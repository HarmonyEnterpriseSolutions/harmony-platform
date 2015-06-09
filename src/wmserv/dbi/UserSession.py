import os
import datetime
from ConfigParser import ConfigParser

from src.wmserv.dbi.driver import DbiDriver
import config


class UserSession(object):
	"""
	Persistent core
	"""

	def __init__(self):
		self.application = 'default'
		self.user_id = None
		self.session_id = None
		self.org_staff_contact_id = None
		self.session_key = None

		self._configs = {}
		self._drivers = None

	def __getstate__(self):
		state = dict(self.__dict__)
		state['_drivers'] = None
		#rint ">>> GETSTATE", state
		return state

	def __setstate__(self, state):
		#rint ">>> SETSTATE", state
		self.__dict__.update(state)

	def close(self):
		#rint ">>> SESSION CLOSE!"
		if self._drivers:
			for driver in self._drivers.itervalues():
				driver.closeConnection()
		
	def getDriver(self, connection_name='admin', ignore_user_position_not_set=False):
		key = (self.application, connection_name)

		if self._drivers is None:
			self._drivers = {}

		driver = self._drivers.get(key)

		if driver is None:
			
			def after_create_connection(driver):
				if self.org_staff_contact_id is not None:
					driver.execute('set_user_position', {
						'session_key' : self.session_key,
						'org_staff_contact_id'    : self.org_staff_contact_id,
					}, rowType=dict)
					driver.commit()
				else:
					if not ignore_user_position_not_set:
						raise RuntimeError, "POSITION NOT SET, session_id=%s" % self.session_id

			self._drivers[key] = driver = DbiDriver.getInstance(
				self.application, 
				connection_name, 
				after_create_connection=after_create_connection if connection_name in ('admin', 'db') else None		# TODO: remove hardcode 'db'
			)

		return driver

	def login(self, request, application, user_login, user_password, set_user_position=False):
		
		if application not in config.ALLOWED_APPLICATIONS:
			return None, None
		
		self.application = application
		self.user_id = None
		self.session_id = None
		reject_note = None

		driver = self.getDriver(ignore_user_position_not_set=True)

		user_id, session_id, session_key = driver.execute('_login', {
			'user_login'    : user_login,
			'user_password' : user_password,
			'application'   : application,
			'client_ip'     : request.META['REMOTE_ADDR'],
			'webkit_sid'    : request.session.session_key,
		}).getSingleRecord()

		if user_id is not None:
			driver.commit()	# commit new session created

			reject_note = None

			if set_user_position:

				poss = list(driver.execute('get_user_position', {
					'session_key' : session_key,
					'user_id'     : user_id,
				}, rowType=dict))

				if not poss:
					reject_note = "User has no position"
				elif len(poss) == 1:
					self.set_user_position(poss[0]['org_staff_contact_id'])
				else:
					reject_note = "User must not share multiple contacts"
				
		else:
			reject_note = 'username or password is incorrect'
		
		if reject_note:		
			self.user_id     = None
			self.session_id  = None
			self.session_key = None
			self.logEvent('REJECT_LOGIN', note=reject_note)
		else:
			self.user_id     = user_id
			self.session_id  = session_id
			self.session_key = session_key
			self.logEvent('LOGIN')

		return self.user_id, self.session_id


	def set_user_position(self, org_staff_contact_id):
		"""
		after login user must call get_user_position, choose some record and set org_staff_contact_id here
		"""
		self.org_staff_contact_id = org_staff_contact_id		

	def isLoggedIn(self):
		return self.user_id is not None
			
	
	def logEvent(self, name, access_object_id=None, access=None, note=None):
		driver = self.getDriver(ignore_user_position_not_set=True)
		driver.execute('_event_log_ins', {
			'event_name' : name,
			'event_time' : datetime.datetime.now(),
			#'sid'        : self.sid,
			#'application': self.application,
			#'user_id'    : self.user_id,
			#'ip'         : self.getTransactionInfo().getRemoteAddress(),
			'access_object_id' : access_object_id,
			'access'           : access,
			'event_note'       : note,
			'session_id'       : self.session_id,
		})
		driver.commit()


	def call(self, application, connection_name, function, parameters, rowType=tuple):
		if self.isLoggedIn() and application in config.ALLOWED_APPLICATIONS:
			assert application == self.application, 'dbi client must use application "%s", got "%s"' % (self.application, application)
			driver = self.getDriver(connection_name=connection_name, ignore_user_position_not_set=function in ('get_user_position',))
			
			if isinstance(parameters, dict):
				parameters_list = [parameters]
			else:
				parameters_list = parameters

			try:
				results = []
				for params in parameters_list:
					params = params.copy()
					params['session_key'] = self.session_key
					results.append(driver.call(function, params, rowType=rowType))

				if isinstance(parameters, dict):
					return results[0]
				else:
					return results

			finally:
				# this is not needed since view calls UserSession.close
				driver.closeConnection()
		else:
			return None	# Permission denied error


	def open_resultset(self, application, connection_name, function, parameters):
		if self.isLoggedIn() and application in config.ALLOWED_APPLICATIONS:
			assert application == self.application, 'dbi client must use application "%s", got "%s"' % (self.application, application)
			driver = self.getDriver(connection_name=connection_name, ignore_user_position_not_set=function in ('get_user_position',))
			
			parameters = parameters.copy()
			parameters['session_key'] = self.session_key

			return driver.execute_safe(function, parameters, rowType=tuple)

			# must close all connections before end of http transaction
		else:
			return None	# Permission denied error

			
	#####################################################################
	# wm configs
	#
		
	def filePath(self, path, file, exact=False):
		"""
		returns file absolute path:
			path/<application>/file
		or
			path/file
		if first not exists
		"""
		base = os.path.abspath(__file__) 
		for i in xrange(4):
			base = os.path.split(base)[0]

		abspath = os.path.join(base, path, self.application, file)
		if not exact and (not os.path.exists(abspath) or not os.path.isfile(abspath)):
			abspath = os.path.join(base, path, file)

		return abspath

	
	def getConfig(self, name, exact=False):		
		config = self._configs.get(name)
		if config is None:
			config = ConfigParser()
			config.read(self.filePath('etc', name, exact))
			self._configs[name] = config
		return config
				
	
