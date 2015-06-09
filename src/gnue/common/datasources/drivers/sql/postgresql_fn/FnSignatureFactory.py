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

	_instances = {}

	def __init__(self, fn_signatures, fn_names):
		self._signatures = fn_signatures
		self._names = fn_names

	@classmethod
	def getInstance(cls, connectionsUrl):
		"""
		Looks for config in connectionsUrl
		"""
		instance = cls._instances.get(connectionsUrl)
		if instance is None:
			# http://localhost/harm/wk.cgi/harm/connections?_SID_=20080208162931-2e6444a8371cf04261e43057f4b1a071
			loc = {}
			if re.match('(?i)[A-Z]+://', connectionsUrl):
				#'/harm/wk.cgi/harm/connections' -> '/harm/wk.cgi/harm/fn_signatures'
				scheme, netloc, path, params, query, fragment = urlparse.urlparse(connectionsUrl)
				path = path.rsplit('/', 1)[0] + '/fn_signatures'
				url = urlparse.urlunparse((scheme, netloc, path, params, query, fragment))
				script = urlopen(url).read()
				exec(script, {}, loc)
			else:
				path = os.path.join(os.path.split(connectionsUrl)[0], 'fn_signatures.conf.py')
				execfile(path, {}, loc)
			cls._instances[connectionsUrl] = instance = FnSignatureFactory(loc['fn_signatures'], loc['fn_names'])
		return instance

	@cached_method
	def __getitem__(self, table):
		names = self._names['*'].copy()
		names.update(self._names.get(table, {}))
		return TableSignature(table, self._signatures[table], names)

	@cached_method
	def keys(self):
		keys = self._signatures.keys()
		keys.sort()
		return keys

	def __iter__(self):
		return iter(self.keys())

	def dump(self):
		import re
		keys = self._signatures.keys()
		keys.sort()
		for i in keys:
			sys.stdout.write(i+'\n')
			REC_VAR = re.compile('(?i)\%\(([_A-Z0-9]+)\)s')
			for op in ('select', 'update', 'insert', 'delete'):
				try:
					sys.stdout.write('    %s: %s\n' % (op,
							REC_VAR.sub(
								lambda m: m.groups()[0],
								self[i][op].genSql({})[0],
							)
						))
				except KeyError:
					sys.stdout.write('    %s:\n' % (op,))


class TableSignature(object):

	def __init__(self, table, signatures, names):
		self._table   = table
		self._signatures = signatures
		self._names = names
		self._secure = signatures['__secure__'] if '__secure__' in signatures else names.get('__secure__', True)

	@cached_method
	def __getitem__(self, operation):
		sigText = self._signatures.get(operation)
		if sigText is None:
			sigText = self._signatures.get('default')
			if sigText is None:
				raise KeyError, operation
			# insert is default without primary
			if operation == 'insert':
				filterfn = lambda attrSig: not attrSig.primary
			# delete signature is only primary from default
			elif operation == 'delete':
				filterfn = lambda attrSig: attrSig.primary
			# select signature has no parameters by default
			elif operation == 'select':
				filterfn = lambda attrSig: False
			# else pass all parameters
			else:
				filterfn = lambda attrSig: True
		else:
			filterfn = lambda attrSig: True
		sigFn = self._signatures.get('fn_' + operation)
		if sigFn is None:
			sigFn = self._names[operation]
		assert sigFn
		return OperationSignature(operation, self._table, sigFn, sigText, filterfn, self._secure)


class OperationSignature(object):

	def __init__(self, operation, table, fnNamePattern, sigText, filterfn, secure):
		assert sigText is not None
		self._operation = operation
		self._table     = table
		self._secure    = secure
		self._signatures = filter(filterfn, map(AttrSignature, filter(None, strings.splitEx(sigText, ','))))
		self._primary = None

		ids = [i.name for i in self._signatures if i.primary]

		if operation == 'insert':
			assert len(ids) <= 1, "Insert can't have more than one primary keys: %s" % self
			if ids:
				self._primary = ids[0]

		if operation != 'select' and ids:
			assert len(ids) == 1, "Signature must have one primary key: %s (%s). Found %s" % (self, sigText, len(ids))
			self._primary = ids[0]

		self._pattern = fnNamePattern.replace('%s', table) + "(%s)"

	#rint "SIGNATURE CREATED: %s %s (%s)" % (table, operation, ', '.join([i['name'] for i in signature]))

	def __iter__(self):
		return iter(self._signatures)

	def __len__(self):
		return len(self._signatures)

	def getFunctionName(self):
		assert self._pattern.endswith('(%s)')
		return self._pattern[:-4]

	def genSql(self, fields, sessionKey=0):
		"""
		iter signature
		        skip parameters with default value if default value == newField(oldField)
		"""
		#assert self._primary is None or not newfields.has_key(self._primary), "Can't update primary key: %s" % self

		sql = []
		parameters = {}
		
		if self._secure:
			sql.append('%(_session_key)s')
			parameters['_session_key'] = sessionKey

		for sig in self._signatures:
			name    = sig.name

			#if not fields.has_key(name):
			#	rint "+ Field %s not provided. %s, fields: %s" % (name, self, fields)

			value = fields.get(name)
			if value != sig.defaultValue:
				sql.append("%%(%s)s" % name)
				parameters[name] = value

		return self._pattern % ", ".join(sql), parameters

	def __str__(self):
		return self._pattern % ', '.join(map(str, self))


class AttrSignature(pydocs.AttrSignature):

	def __init__(self, sigText):
		pydocs.AttrSignature.__init__(self, sigText)

		assert self.type in (None, 'primary'), 'Invalid modifier: %s' % self

		self.primary = (self.type == 'primary')

		if self.default:
			self.defaultValue = eval(self.default, {})
		else:
			self.defaultValue = NotImplemented
