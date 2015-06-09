import os

from gnue.common.datasources.drivers.sql.postgresql_fn.FnSignatureFactory import FnSignatureFactory
from harmlib.scripts.utils.harmApplication import harmApplication
from harmlib.webkit.FormDom import FormDom
from toolib.db.simpleconn import NoRecordError
from src.harmserv.dbi import config


"""
metadata = {
	'form1' : [
		{
			'function' : 'foo_list',
			'parameters' : [
				{
					'name' : 'param1',
					'type' : 'integer',
				},
			],
			'columns' : [
				{
					'name' : 'field1',
					'type' : 'integer',
					'scale' : 0,
					'editable' : 'Y',
				},
			],
		},
	],
}



"""


TYPE_ALIACES = {
	'bool'          : 'boolean', 
	'decimal'       : 'numeric', 
	'int'           : 'integer',
	'int4'          : 'integer',
	'int8'          : 'bigint',
	'number'        : 'numeric',
	'smalldatetime' : 'datetime',
	'varchar'       : 'string',
	'char'          : 'string',
	'text'          : 'string',
}

def normal_type(s):
	return TYPE_ALIACES.get(str(s), str(s))


OPER_SUFFIX = {
	'insert' : 'ins',
	'update' : 'edit',
	'delete' : 'del',
}

class FormFunctions(object):

	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)
		if 'functions' not in kwargs:
			self.functions = []


class Parameter(object):

	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)


class Column(object):

	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)
		

class Function(object):

	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)
		if 'columns' not in kwargs:
			self.columns = []
		if 'parameters' not in kwargs:
			self.parameters = []



class Block(object):

	def __init__(self, form, block):
		self._block = block

	def getColumns(self):
		columns = []

		for field in self._block.getElementsByTagName('field'):

			field_name = field.getAttribute('field')

			if field:
				column = Column(name=field_name)
				if field.getAttribute('datatype'): column.type = normal_type(field.getAttribute('datatype'))
				if field.getAttribute('scale'): column.numeric_scale = field.getAttribute('scale')

				columns.append(column)

		return columns


class Signatures_psycopg2(object):

	def __init__(self, datasource):
		self._datasource = datasource

	def getFunctions(self):
		
		if self._datasource._table == 'dummy':
			return {}

		app = self._datasource._form._app
		table_sig = app._signature_factory[self._datasource._table]

		result = {}

		for oper in ('select', 'insert', 'update', 'delete'):
			
			try:
				oper_sig = table_sig[oper]
			except KeyError:
				pass
			else:
				#rint '------------', self._datasource._table, oper
				function_name = oper_sig.getFunctionName()

				oper_result = result[oper] = Function(
					connection = self._datasource.getConnection(),
					name = "f_%s_%s" % (self._datasource._table, OPER_SUFFIX[oper]) if oper != 'select' else 'f_' + self._datasource._table,
				)
				
				param_count = len(oper_sig)
				if table_sig._secure:
					param_count += 1

				try:
					specific_name, data_type, type_udt_name = self._datasource._conn.execute("""
						SELECT
							R.specific_name, R.data_type, R.type_udt_name
						FROM information_schema.routines R
						LEFT JOIN information_schema.parameters P ON P.specific_name = R.specific_name
						WHERE 
							routine_schema = 'public' 
							AND (parameter_mode is NULL OR parameter_mode <> 'OUT')
							AND routine_name = %(function_name)s
						GROUP BY R.specific_name, R.routine_name, R.data_type, R.type_udt_name
						HAVING count(P.ordinal_position) = %(param_count)s
					""", locals()).getSingleRow()
				except NoRecordError:
					print "! function not exist", self._datasource._table, oper
					continue

				param_names = [i.name for i in oper_sig]
				if table_sig._secure:
					param_names.insert(0, 'session_key')

				parameters = map(remove_null_values, self._datasource._conn.execute("""
					SELECT
						P.udt_name AS type,
						P.character_maximum_length,
						P.numeric_precision,
						P.numeric_scale
					FROM information_schema.parameters P
					WHERE 
						P.specific_name = %(specific_name)s
						AND (P.parameter_mode is NULL OR P.parameter_mode <> 'OUT') 
					ORDER BY P.ordinal_position
				""", locals(), rowType=dict))
			
				for i, row in enumerate(parameters):
					row['name'] = param_names[i]
					row['type'] = normal_type(row['type'])

				if table_sig._secure:
					parameters = parameters[1:]

				oper_result.parameters.extend([Parameter(**p) for p in parameters])
					
				if data_type != 'void':
					columns = oper_result.columns
					if data_type == "USER-DEFINED":
						# type_udt_name is type or table
						#rint ">>>", type_udt_name

						for row in self._datasource._conn.execute("""
							SELECT
								A.attname AS name,
								AT.typname AS type,
								CASE WHEN (AT.typname = 'varchar' OR AT.typname = 'bpchar') AND a.atttypmod != -1 THEN (A.atttypmod - 4) & 65535 ELSE NULL END AS character_maximum_length,
								CASE WHEN AT.typname = 'numeric' AND a.atttypmod != -1 THEN ((A.atttypmod - 4) >> 16) & 65535 ELSE NULL END AS numeric_precision,
								CASE WHEN AT.typname = 'numeric' AND a.atttypmod != -1 THEN (A.atttypmod - 4) & 65535 ELSE NULL END AS numeric_scale
							from pg_type T
							INNER JOIN pg_class C on (C.reltype = t.oid)
							INNER JOIN pg_attribute A on (A.attrelid = C.oid)
							INNER JOIN pg_type AT on (A.atttypid = AT.oid)
							WHERE T.typname = %(type_udt_name)s AND A.attnum > 0
							ORDER BY A.attnum
						""", locals(), rowType = dict):
							row['type'] = normal_type(row['type'])
							columns.append(Parameter(**remove_null_values(row)))
					elif data_type == 'record':
						
						for row in self._datasource._conn.execute("""
							SELECT
								P.parameter_name AS name,
								P.udt_name AS type,
								P.character_maximum_length,
								P.numeric_precision,
								P.numeric_scale
							FROM information_schema.parameters P
							WHERE 
								P.specific_name = %(specific_name)s
								AND (P.parameter_mode = 'OUT') 
							ORDER BY P.ordinal_position
						""", locals(), rowType = dict):
							row['type'] = normal_type(row['type'])
							columns.append(Column(**remove_null_values(row)))

					else:
						columns.append(Column(
							name = function_name,
							type = normal_type(type_udt_name),
						))

		
		return result

def remove_null_values(d):
	return dict(((k, v) for (k, v) in d.iteritems() if v is not None))

class Signatures_pyodbc(object):
	
	def __init__(self, datasource):
		self._datasource = datasource


	def getFunctions(self):
		result = {}
		
		for oper, suffix in (('select', ''), ('insert', '_ins'), ('update', '_edit'), ('delete', '_del')):
			function = self._datasource._table
			if suffix:
				if function.endswith('_list'):
					function = function[:-5]
				function = function + suffix
			
			parameters = []
			for row in self._datasource._conn.execute("""
				SELECT 
					SUBSTRING(P.parameter_name, 2, 4000) AS name,
					P.data_type AS type,
					P.character_maximum_length AS character_maximum_length,
					CASE WHEN P.data_type = 'decimal' THEN P.numeric_precision ELSE NULL END AS numeric_precision,
					CASE WHEN P.data_type = 'decimal' THEN P.numeric_scale ELSE NULL END AS numeric_scale
				FROM information_schema.routines R
				INNER JOIN information_schema.parameters P ON P.specific_name = R.specific_name
				WHERE R.specific_name = %(function)s
				ORDER BY ordinal_position
			""", locals(), rowType=dict):
				row['type'] = normal_type(row['type'])
				parameters.append(Parameter(**remove_null_values(row)))

			if parameters:
				oper_result = result[oper] = Function(
					connection = self._datasource.getConnection(),
					name = function,
					parameters = parameters,
				)
		
		return result


class Datasource(object):

	def __init__(self, form, datasource):
		self._form = form
		self._datasource = datasource
		self._table = datasource.getAttribute('table')

		self._connection = datasource.getAttribute('connection')

		assert self._connection, datasource.getAttribute('name')

		self._conn = form._app.getConnection(self._connection)
		self._signatures = eval('Signatures_' + form._app.getConnectionArgs(self._connection)[0].__name__)(self)

	def getConnection(self):
		return self._connection


	def getFunctions(self):
		functions = self._signatures.getFunctions()

		if 'select' in functions and not functions['select'].columns and self.getBlock():
			columns = functions['select'].columns.extend(self.getBlock().getColumns())

		if 'insert' in functions and not functions['insert'].columns:
			assert self._datasource.getAttribute('rowid')
			columns = functions['insert'].columns.append(Column(
				name = self._datasource.getAttribute('rowid'),
				type = 'integer',
			))

		return functions.values()

		
	def getBlock(self):
		return self._form.getBlock(self._datasource.getAttribute('name'))


		

class Form(FormDom):

	def __init__(self, app, form_path):
		os.chdir(os.path.dirname(form_path))
		FormDom.__init__(self, form_path)

		self._app = app
		self._block_by_ds = {}

		logics = self.dom.getElementsByTagName('logic')
		if logics:
			for block in logics[0].getElementsByTagName('block'):
				ds = block.getAttribute('datasource')
				if ds:
					self._block_by_ds[ds] = block


	def getDatasources(self):
		for ds in self.dom.getElementsByTagName('datasource'):
			if ds.getAttribute('connection'):
				yield Datasource(self, ds)
		

	def getBlock(self, datasource_name):
		block = self._block_by_ds.get(datasource_name)
		if block:
			return Block(self, block)


	def getFunctions(self):
		functions = []
		for ds in self.getDatasources():
			functions.extend(ds.getFunctions())
		return functions






class Fetcher(harmApplication):

	def __init__(self, app_name):
		harmApplication.__init__(self, app_name)
		self._signature_factory = FnSignatureFactory.getInstance(self.getConfigPath('fn_signatures.conf.py'))


	def fetchFormsMetadata(self, forms):
		"""
		returns list of FormFunctions
		"""
		result = []

		for form in forms:
			form_path = self.getPath('forms', self.name, form)

			functions = Form(self, form_path).getFunctions()
			
			result.append(FormFunctions(name=form, functions=functions))

		return result




def main():

	app_name = config.APPLICATION
	forms = Fetcher(app_name).fetchFormsMetadata(config.FORMS)

	for form in forms:
		print
		print form.name
		print
		for f in form.functions:
			print f
			for p in f.parameters:
				print '\t', p
			for c in f.columns:
				print '\t', c
					


if __name__ == '__main__':
	main()
