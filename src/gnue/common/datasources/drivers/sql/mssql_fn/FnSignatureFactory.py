import os
import sys
import re
from toolib.util.Cache	import cached_method
from toolib.util		import pydocs
from toolib.util		import strings
from urllib2			import urlparse, urlopen

"""
NOTE:

Cant get function signatures from function description field

SELECT
        pg_catalog.pg_proc.proname,
        pg_catalog.pg_description.description
FROM
        pg_catalog.pg_proc INNER JOIN
        pg_catalog.pg_description ON
        pg_catalog.pg_proc.oid = pg_catalog.pg_description.objoid
WHERE
        pg_catalog.pg_proc.proname = 'f_doc_2_doc'
"""

class FnSignatureFactory(object):

	def __init__(self, connection, encoding):
		self.connection = connection
		self.encoding = encoding

	@cached_method
	def __getitem__(self, table):
		return TableSignature(self, table)


REC_AS = re.compile(r'(?im)\sAS\s')
REC_PARAM = re.compile(r'(?u)\@(\w+)')

class TableSignature(object):

	def __init__(self, factory, table):
		self._connection = factory.connection
		self._encoding   = factory.encoding
		self._table      = table


	def _getParameters(self, sp):
		# "SC.colid = 1" means look first 4000 bytes only
		try:
			text = self._connection.execute("SELECT CAST(SC.text as TEXT) FROM sysobjects SO INNER JOIN syscomments SC ON SC.id=SO.id AND SC.colid = 1 WHERE SO.name = ? AND SO.xtype = 'P'", [sp.encode(self._encoding)]).next()[0]
			text = text.decode(self._encoding)
		except StopIteration:
			return []
		else:
			if text:
				m = REC_AS.search(text)
				if m:
					text = text[:m.start()]
				else:
					print "! stored procedure code has no 'AS':", sp
					return []
				return REC_PARAM.findall(text)
			else:
				return []
	

	@cached_method
	def __getitem__(self, operation):
		
		if operation == 'list':
			sp = self._table
		else:
			sp = "_".join(((self._table[:-5] if self._table.endswith('_list') else self._table), operation))	# 5 == len('_list')
		
		parameters = self._getParameters(sp)
		
		return OperationSignature(sp, parameters)


class OperationSignature(object):

	def __init__(self, sp, parameters):
		self._parameters = parameters
		self._sp = sp
		self._sql = "EXEC %s %s" % (
			sp,
			','.join(("@P=%(P)s".replace('P', parameter) for parameter in parameters))
		)

	def genSql(self, fields):
		#TODO: check only for select
		#assert not set(fields.keys()).difference(self._parameters), "Unknown fields passed to stored procedure '%s': %s" % (self._sp, ', '.join(sorted(set(fields.keys()).difference(self._parameters))))

		#for i in sorted(set(self._parameters).difference(fields.keys())):
		#	print "* parameter '%s' not passed to stored procedure '%s'. NULL will be passed" % (i, self._sp)

		return self._sql, dict(((p, fields.get(p)) for p in self._parameters))

def sorted(s):
	l = list(s)
	l.sort()
	return l
