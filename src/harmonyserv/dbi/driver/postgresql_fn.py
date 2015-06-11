import __init__ as base
import psycopg2
import re
from gnue.common.datasources.drivers.sql.postgresql_fn.FnSignatureFactory import FnSignatureFactory

REC_FUNCTION = re.compile('(\w+)(_ins|_edit|_del)')
OPER_BY_SUFFIX = {
	''      : 'select',
	'_edit' : 'update',
	'_ins'  : 'insert',
	'_del'  : 'delete',
}


class DbiDriver(base.DbiDriver):

	package = psycopg2

	def __init__(self, app_name, connection_data, *args, **kwargs):
		super(DbiDriver, self).__init__(app_name, connection_data, *args, **kwargs)

		self._sig_factory = FnSignatureFactory.getInstance(self.getConfig('fn_signatures.conf.py'))


	def getExecuteParameters(self, function, parameters):
	
		m = REC_FUNCTION.match(function)
		if  m:
			table, suffix = m.groups()
			oper = OPER_BY_SUFFIX[suffix]
		else:
			table = function
			oper = 'select'

		session_key = parameters.get('session_key', None)

		statement, parameters = self._sig_factory[table][oper].genSql(parameters, session_key)

		if oper in ('select', 'insert'):
			statement = "SELECT * FROM " + statement
		else:
			statement = "SELECT " + statement
	
		return statement, parameters
