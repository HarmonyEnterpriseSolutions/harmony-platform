import os
import sys
import traceback
import datetime
from ConfigParser import ConfigParser
import threading
from weakref import WeakKeyDictionary

from gnue.common.datasources.GConnections import GConnections
from gnue.common.datasources.GConditions import buildConditionFromDict
from src.wmlib.webkit import AccessObject


_gConnections_by_thread = WeakKeyDictionary()


class UserContext(object):
	"""
	Persistent core
	"""

	def __init__(self, sid):
		self.sid = sid
		self.application = 'default'
		self.userId = None
		self.sessionId = None

		self.__sessionKey = 0

		self.__configs = {}
		self.__transactionInfo = None


	def getTransactionInfo(self):
		return self.__transactionInfo

	def setTransactionInfo(self, transactionInfo):
		self.__transactionInfo = transactionInfo

	def __getstate__(self):
		dict = self.__dict__.copy()
		# drop caches
		dict['_UserContext__gConnection'] = None
		dict['_UserContext__configs'] = {}
		dict['_UserContext__transactionInfo'] = None
		return dict

	def filePath(self, path, file, exact=False):
		"""
		returns file absolute path:
			path/<application>/file
		or
			path/file
		if first not exists
		"""
		#base = os.path.split(self.request().serverSideContextPath())[0]

		base = os.path.abspath(__file__) 
		for i in xrange(4):
			base = os.path.split(base)[0]

		abspath = os.path.join(base, path, self.application, file)
		if not exact and (not os.path.exists(abspath) or not os.path.isfile(abspath)):
			abspath = os.path.join(base, path, file)

		#assert os.path.exists(abspath) and os.path.isfile(abspath), abspath
		
		return abspath


	def getConfig(self, name, exact=False):
		"""
		return python config
		uses filePath to find file
		"""

		config = self.__configs.get(name)

		if config is None:
			file = self.filePath('etc', name, exact)
			try:
				config = {}
				execfile(file, {}, config)
			except SyntaxError:
				config = ConfigParser()
				config.read(file)
			
			self.__configs[name] = config

		return config				


	def login(self, application, user_login, user_password):
		
		self.application = application
		self.userId = None
		self.sessionId = None
		self.__sessionKey = None
		self.__userGroups = None

		if self.hasConnection():

			res = tuple(self.query(
				'_login', 
				[
					'_user_id', 
					'_session_id',
					'_session_key', 
				],
				parameters = { 
					'user_login'    : user_login,
					'user_password' : user_password,
					'application'   : application,
					'client_ip'     : self.getTransactionInfo().getRemoteAddress(),
					'webkit_sid'    : self.sid,
				},
			
			))
			if res:
				self.userId       = res[0]['_user_id']
				self.sessionId    = res[0]['_session_id']
				self.__sessionKey = res[0]['_session_key']

			if self.userId is not None:
				self.logEvent('LOGIN')
			else:
				self.logEvent('REJECT_LOGIN', note=user_login)
		else:
			# working without database security
			self.userId = 0
			self.sessionId = 0
			self.__sessionKey = -1

		return (self.userId, self.__sessionKey, self.sid)

	def isLoggedIn(self):
		return self.userId is not None
			
	def logEvent(self, name, access_object_id=None, access=None, note=None):
		if self.hasConnection():
			c = self.getConnection()
			c.insert('_event_log', {
				'event_name' : name,
				'event_time' : datetime.datetime.now(),
				#'sid'        : self.sid,
				#'application': self.application,
				#'user_id'    : self.userId,
				#'ip'         : self.getTransactionInfo().getRemoteAddress(),
				'access_object_id' : access_object_id,
				'access'           : access,
				'event_note'       : note,
				'session_id'       : self.sessionId,
			})
			c.commit()

	def getUserGroups(self):
		if self.isLoggedIn() and self.hasConnection():
			return tuple((row['group_sysname'] for row in self.query('_group_actual', ['group_sysname'])))
		else:
			return ()

	def isSuperuser(self):
		return 'ADMINISTRATOR' in self.getUserGroups()

	def getAccessObject(self, accessObjectId):
		assert accessObjectId is not None

		try:
			ao = self.query('_spr_object',
					[
						'object_id',
						#'object_parent_id',
						'object_type_id',
						'object_name',
						'object_url',
						#'object_params',
					],
					{
						'object_id' : accessObjectId,
					},
					parameters = {
						'user_id' : self.userId,
					}, 
				).next()
		except StopIteration:
			return None
		else:
			return AccessObject(
				ao,
				self.query(
					'get_objectaccess', 
					[	
						'objectaccess_is_view', 
						'objectaccess_is_edit',
						'objectaccess_is_ins',
						'objectaccess_is_del',
						'objectaccess_is_print',
					],
					parameters = { 
						'object_id' : accessObjectId,
						'user_id' : self.userId,
					},
				)
			)


	def getFunctionAccess(self, object_id):
		d = {}
		if self.isLoggedIn() and self.hasConnection():
			for row in self.query(
				'session_func', 
				[
					'func_key',
					'is_ins',
					'is_upd',
					'is_del',
				],
				parameters = {
					'object_id' : object_id,
				}
			):
				d[row['func_key']] = (row['is_ins'], row['is_upd'], row['is_del'])
		return d
		

	def hasConnection(self):
		return bool(self.getConfig('servers.conf').get('auth', 'connection'))


	def getConnection(self):
		filePath = self.filePath('etc', 'connections.conf', exact=True)
		connName = self.getConfig('servers.conf').get('auth', 'connection')
		thread = threading.currentThread()

		key = (filePath, connName)

		gConnection = _gConnections_by_thread.get(thread, {}).get(key)

		if gConnection is not None:
			# test if usable
			try:
				c = gConnection._getNativeConnection()['connection'].cursor()
				c.execute('SELECT NULL')
				c.close()
			except:
				print '* connection from cache is unusable. Problem was:'
				print ''.join(traceback.format_exception(*sys.exc_info()))
				gConnection = None
		
		if gConnection is None:
			_gConnections_by_thread.setdefault(thread, {})[key] = gConnection = GConnections(filePath).getConnection(connName, login=True)
	
		# TODO: maybe set session key to connection, not to manager every time
		gConnection.manager.setSessionKey(self.__sessionKey)

		return gConnection

	
	def query(self, table, fieldnames, condition=None, sortorder=None, distinct=False, parameters=None):
		"""
		TODO: his method must be reduced into GConnection
		"""
		c = self.getConnection()
		rs = c._resultSetClass_(
			defaultData      = {},
			connection       = c,
			tablename        = table,
			rowidField       = None,
			primarykeyFields = None,
			primarykeySeq    = None,
			boundFields      = (),
			requery          = False,
			access           = ACCESS.FULL,
			details          = {},
			eventController  = None
		)
		rs._query_object_(c, 
			table, 
			fieldnames, 
			buildConditionFromDict(condition or {}), 
			sortorder or [], 
			distinct, 
			parameters or {}
		)
		c.commit()
		return rs._fetch_(5)

	
	def getUserConfigValue(self, key):
		"""
		returns user specific value by key
		used e.g. for ui layout persistence
		"""
		if self.isLoggedIn() and self.hasConnection():
			res = tuple(self.query('_spr_userconfig',
				[
					'userconfig_value',
				],
				parameters = {
					'user_id'        : self.userId,
					'userconfig_key' : key,
				},
			))
			if res:
				return eval(res[0]['userconfig_value'], {}, {})


	def setUserConfigValue(self, key, value):
		"""
		saves user specific value of any pythonic simple type by key
		used e.g. for ui layout persistence
		"""
		if self.isLoggedIn() and self.hasConnection():
			c = self.getConnection()
			c.insert('_spr_userconfig', {
				'user_id'          : self.userId,
				'userconfig_key'   : key,
				'userconfig_value' : repr(value),
			})
			c.commit()
