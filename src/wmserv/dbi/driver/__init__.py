from toolib.db.simpleconn import Connection
from toolib.util import lang
from weakref import WeakKeyDictionary
from ConfigParser import ConfigParser, NoOptionError
import os
import threading




class DbiDriver(object):


	def __init__(self, app_name, connection_data, after_create_connection=None):
		self._app_name = app_name
		self.__connect_parameters = self.getConnectionParameters(connection_data)
		self.__connections = WeakKeyDictionary()
		self.__after_create_connection = after_create_connection


	def getConnectionParameters(self, connection_data):
		return [], connection_data
	

	def createConnection(self):
		args, kwargs = self.__connect_parameters
		return Connection(self.package, *args, **kwargs)


	def _getConnection(self):
		thread = threading.currentThread()
		return self.__connections.get(thread)

	
	def getConnection(self):
		thread = threading.currentThread()
		connection = self.__connections.get(thread)
		if connection is None:
			connection = self.__connections[thread] = self.createConnection()
			if self.__after_create_connection:
				self.__after_create_connection(self)
		return connection

	
	def closeConnection(self):
		thread = threading.currentThread()
		connection = self.__connections.get(thread)
		if connection is not None:
			del self.__connections[thread]
			try:
				connection.close()
			except Exception, e:
				print "* failed to close connection: %s: %s" % (e.__class__.__name__, e)

	def commit(self):
		connection = self._getConnection()
		if connection:
			connection.commit()
			
	def rollback(self):
		connection = self._getConnection()
		if connection:
			connection.rollback()

			
	def execute(self, function, parameters, rowType=tuple):
		sql, params = self.getExecuteParameters(function, parameters)
		return self.getConnection().execute(sql, params, rowType=rowType)


	def execute_safe(self, function, parameters, rowType=tuple):
		try:
			rs = self.execute(function, parameters, rowType=rowType)
		except:
			try:
				self.rollback()
			except Exception, e:
				print "* failed to rollback connection: %s: %s" % (e.__class__.__name__, e)
			
			# close because connection may be broken after rollback
			self.closeConnection()
			raise
		else:
			return rs
	
	
	def call(self, function, parameters, rowType=tuple):
		rs = self.execute_safe(function, parameters, rowType)
		data = {
			'columns' : [{'name' : i} for i in rs.columns],
			'data'    : list(rs),
		}
		self.commit()
		return data


	def getExecuteParameters(self, function, parameters):
		return function, parameters

	@classmethod
	def getApplicationConfig(cls, application, config):
		path = os.path.abspath(__file__)
		for i in xrange(5):
			path = os.path.split(path)[0]
		return os.path.join(path, 'etc', application, config)

	def getConfig(self, config):
		return self.getApplicationConfig(self._app_name, config)
	
	@classmethod
	def getInstance(cls, application, connection, *args, **kwargs):

		parser = ConfigParser()
		parser.read(cls.getApplicationConfig(application, 'connections.conf'))

		# if alias, resolve alias
		if connection not in parser.sections():
			for section in parser.sections():
				try:
					if connection in (i.strip() for i in parser.get(section, 'aliases').split(',')):
						connection = section
						break
				except NoOptionError:
					pass

		provider = parser.get(connection, 'provider')

		driver = lang.import_module_relative(provider, __name__, 'driver').DbiDriver

		data = {
			'host'       : parser.get(connection, 'host'    ),
			'database'   : parser.get(connection, 'dbname'  ),
			'user'       : parser.get(connection, 'username'),
			'password'   : parser.get(connection, 'password'),
			'_encoding_' : parser.get(connection, 'encoding'),
		}
		try:
			data['port'] = parser.get(connection, 'port')
		except:
			pass

		return driver(application, data, *args, **kwargs)
