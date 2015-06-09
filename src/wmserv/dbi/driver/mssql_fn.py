import __init__ as base
import pyodbc
from toolib.db import pyodbcs
from gnue.common.datasources.drivers.sql.mssql_fn.FnSignatureFactory import FnSignatureFactory
import re

REC_FUNCTION = re.compile('\w+(:?_(ins|edit|del))?')

class DbiDriver(base.DbiDriver):

	package = pyodbc

	def __init__(self, app_name, connection_data, *args, **kwargs):
		super(DbiDriver, self).__init__(app_name, connection_data, *args, **kwargs)
		self._encoding = connection_data.get('_encoding_')
		assert self._encoding
	
	
	def getConnectionParameters(self, connection_data):
		kwargs = {}
		if '_encoding_' in connection_data:
			kwargs['_encoding_'] = connection_data['_encoding_']
		return [pyodbcs.get_mssql_connect_string(connection_data)], kwargs


	def getExecuteParameters(self, function, parameters):
	
		sig_factory = FnSignatureFactory(self.getConnection(), self._encoding)

		m = REC_FUNCTION.match(function)

		oper = m.groups()[0] or 'list'

		statement, parameters = sig_factory[function][oper].genSql(parameters)

		return statement, parameters
