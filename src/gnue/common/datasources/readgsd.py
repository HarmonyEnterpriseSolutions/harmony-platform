# GNU Enterprise Common Library - Read and import gsd-files
#
# Copyright 2000-2007 Free Software Foundation
#
# This file is part of GNU Enterprise.
#
# GNU Enterprise is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# GNU Enterprise is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.
#
# $Id: readgsd.py 9454 2007-03-30 06:55:31Z johannes $
"""
Program to import gsd files.
"""

import os
import re
import sets
import datetime

from gnue.common.apps import errors, GBaseApp, GClientApp
from gnue.common.datasources import GSchema, GDataSource, GConditions
from gnue.common.utils.FileUtils import openResource
from gnue.common.utils import GDateTime
from gnue.common.apps.i18n import utranslate as u_          # for epydoc


# =============================================================================
# Exceptions
# =============================================================================

class MissingTableError(errors.ApplicationError):
	def __init__(self, name):
		msg = u_("Table '%(table)s' not found in the schema") % {'table': name}
		errors.ApplicationError.__init__(self, msg)

class MissingKeyFieldError(errors.ApplicationError):
	def __init__(self, table, row, keySet, rowSet):
		msg = u_("Key field(s) '%(fields)s' missing in row '%(row)s' of " \
				"table '%(table)s'") \
			% {'table' : table, 'row': row,
			'fields': ", ".join(keySet.difference(rowSet))}
		errors.ApplicationError.__init__(self, msg)

class InvalidFieldsError(errors.ApplicationError):
	def __init__(self, table, row, fields):
		msg = u_("Table '%(table)s' has no field '%(fields)s'") \
			% {'table': table, 'fields': ", ".join(fields)}
		errors.ApplicationError.__init__(self, msg)

class CircularReferenceError(errors.ApplicationError):
	def __init__(self):
		msg = u_("Tables have circular or unresolveable references")
		errors.ApplicationError.__init__(self, msg)

class CircularDataReferences(errors.ApplicationError):
	def __init__(self, table):
		msg = u_("Table '%s' contains circular/unresolvable record references")\
			% table
		errors.ApplicationError.__init__(self, msg)

class InvalidNumberError(errors.ApplicationError):
	def __init__(self, value, length, scale):
		msg = u_("The value '%(value)s' is not a valid " \
				"number (%(length)s.%(scale)s)") \
			% {'value': value, 'length': length, 'scale': scale}
		errors.ApplicationError.__init__(self, msg)

class OutOfRangeError(errors.ApplicationError):
	def __init__(self, value, length, scale):
		msg = u_("The value '%(value)s' is out of range " \
				"(%(length)s.%(scale)s)") \
			% {'value': value, 'length': length, 'scale': scale}
		errors.ApplicationError.__init__(self, msg)

class InvalidBooleanError(errors.ApplicationError):
	def __init__(self, value):
		msg = u_("'%(value)s' is not a valid boolean value") % {'value': value}
		errors.ApplicationError.__init__(self, msg)

class InvalidDateError(errors.ApplicationError):
	def __init__(self, value):
		msg = u_("'%s' is not a vaild date, use 'YYYY-MM-DD' (ISO)") % value
		errors.ApplicationError.__init__(self, msg)

class InvalidTimeError(errors.ApplicationError):
	def __init__(self, value):
		msg = u_("'%s' is not a vaild time, use 'HH[:MM[:SS[.ss]]]' (ISO)") \
			% value
		errors.ApplicationError.__init__(self, msg)

class InvalidDateTimeError(errors.ApplicationError):
	def __init__(self, value):
		msg = u_("'%s' is not a vaild date/time, use 'YYYY-MM-DD " \
				"HH[:MM[:SS[.ss]]]' (ISO)") % value
		errors.ApplicationError.__init__(self, msg)

class InvalidTypeError(errors.ApplicationError):
	def __init__(self, ftype):
		msg = u_("'%s' is not a recognized field type") % ftype
		errors.ApplicationError.__init__(self, msg)


# =============================================================================
# Client application reading and importing GNUe Schema Definition files
# =============================================================================

class gsdClient(GClientApp.GClientApp):
	"""
	Client application for reading and importing gsd files.
	"""

	NAME    = "gnue-schema"
	COMMAND = "gnue-schema"
	VERSION = "0.1.0"
	USAGE   = "%s file [, file, ...]" % GClientApp.GClientApp.USAGE
	SUMMARY = u_("Import GNUe Schema Definition files into a given connection")


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, connections=None):

		self.addCommandOption('connection', 'c', argument=u_('connectionname'),
			default = "gnue",
			help = u_("Use the connection <connectionname> for creating the "
				"schema"))

		self.addCommandOption('output','o', argument=u_('filename'),
			help = u_("Also send the code for creating the schema to "
				"this file."))

		self.addCommandOption('file-only', 'f', default = False,
			help = u_("If this flag is set, only code is sent to the output "
				"file and the schema is not created automatically."))

		self.addCommandOption('mode', 'm', argument='both|schema|data',
			default = 'both',
			help = u_("Mode of operation. If mode is 'schema', only schema "
				"creation is done. If mode is 'data' only data "
				"integration is done."))

		self.addCommandOption('username', 'u', argument = u_("user"),
			help = u_("Set the username to connect to the database. If the "
				"database is to be created and no owner (--owner) is "
				"specified, this username will be it's owner."))

		self.addCommandOption('password', 'p', argument = u_("password"),
			help = u_("Set the password to connect to the database."))

		self.addCommandOption('owner', 'O', argument = u_("owner"),
			help = u_("If the database is to be created this will be its "
				"owner."))

		self.addCommandOption('ownerpassword', 'P', argument = u_("ownerpwd"),
			help = u_("If the database is to be created this will be the "
				"password used for the database owner."))

		self.addCommandOption('createdb', 'd', default = False,
			help = u_("If this option is set, the database will be created "
				"before any schema creation is done. There must be an "
				"owner or a username either from the given "
				"connection-configuration or from the command line. "
				"This user becomes the owner of the database and will "
				"be implicitly created."))

		self.addCommandOption('yes', 'y', default = False,
			help = u_("If this option is set, the program runs in batch-mode, "
				"which means all questions are answered with 'yes' "
				"automatically."))

		GClientApp.GClientApp.__init__(self, connections, 'schema', ())


	# -------------------------------------------------------------------------
	# Run the import
	# -------------------------------------------------------------------------

	def run(self):
		"""
		Check the options given on the command line, load all gsd files and
		import their schema/data according to the command line options.
		"""

		self.__check_options()
		self.__load_input_files()

		proceed = True

		if self.__do_schema:
			proceed = self.__import_schema()

		if proceed and self.__do_data:
			self.__import_data()


	# -------------------------------------------------------------------------
	# Check the command line arguments
	# -------------------------------------------------------------------------

	def __check_options(self):
		"""
		Process the command line arguments.

		Builds a list of file handles to process and validates that the command
		line option combinations are valid.
		"""

		if not self.ARGUMENTS:
			raise GBaseApp.StartupError, u_("No input file specified.")

		# --- Build file handle list ------------------------------------------
		try:
			self._files = []

			for filename in self.ARGUMENTS:
				self._files.append(openResource(filename))

		except IOError:
			raise GBaseApp.StartupError, \
				u_("Unable to open input file: %s") % errors.getException()[2]


		# --- Setup ouput file if requested -----------------------------------
		self.outfile = self.OPTIONS['output']

		if self.OPTIONS['file-only'] and self.outfile is None:
			raise GBaseApp.StartupError, \
				u_("Output to file only requested, but no filename specified.")

		# --- Determine which processing steps are executed -------------------

		mode = self.OPTIONS['mode'].lower()
		self.__do_schema = mode in ['both', 'schema']
		self.__do_data   = mode in ['both', 'data'] and \
			not self.OPTIONS['file-only']

		if not (self.__do_schema or self.__do_data):
			raise GBaseApp.StartupError, \
				u_("Mode of operation must be one of 'both', 'schema' " \
					"or 'data'.")

		# --- Setup the connection --------------------------------------------
		cName = self.OPTIONS['connection']
		self.connection = self.connections.getConnection(cName)

		# --- Authentication --------------------------------------------------
		# If a username is given on the command line we pass both username and
		# password to the connection parameters.  If the password is not set,
		# it defaults to 'gnue'.
		username = self.connection.parameters.get('username', 'gnue')
		password = self.connection.parameters.get('password', 'gnue')

		if self.OPTIONS['username'] is not None:
			username = self.OPTIONS['username']

		if self.OPTIONS['password'] is not None:
			password = self.OPTIONS['password']

		self.connection.parameters['username'] = username
		self.connection.parameters['password'] = password

		owner = self.OPTIONS.get('owner',
			self.connection.parameters.get('owner'))
		if not owner:
			owner = username

		self.connection.parameters['owner'] = owner
		if self.OPTIONS.get('ownerpassword'):
			self.connection.parameters['ownerpwd'] = \
				self.OPTIONS['ownerpassword']


	# -------------------------------------------------------------------------
	# Load input files
	# -------------------------------------------------------------------------

	def __load_input_files(self):
		"""
		Builds a schema from the list of input filehandles stored in self._files
		"""
		self._schema = None

		for stream in self._files:
			xmltree = GSchema.loadFile(stream)
			if self._schema is None:
				self._schema = xmltree
			else:
				self._schema.merge(xmltree)


	# -------------------------------------------------------------------------
	# Import the given GSD files into the connection
	# -------------------------------------------------------------------------

	def __import_schema(self):

		if self.OPTIONS['createdb']:
			# Create a new database
			if self.__ask(u_("You are about to create the new database '%s'. " \
						"Continue") % self.connection.name,
				[u_("y"), u_("n")], "n") == u_("n"):
				return False

			self.connection.createDatabase()

		# Process schema information (if requested)
		simulation = self.OPTIONS['file-only']
		if not simulation:
			if self.__ask(u_("You are about to change the database '%s'. " \
						"Continue") % self.connection.name,
				[u_("y"), u_("n")], u_("n")) == u_("n"):
				return False

		self.connections.loginToConnection(self.connection)

		print o(u_("Updating schema ..."))
		commands = self.connection.writeSchema(self._schema, simulation)

		# Dump the commands to the output file (if requested)
		if self.outfile is not None:
			dest = open(self.outfile, 'w')
			try:
				for line in commands:
					dest.write("%s%s" % (line, os.linesep))

			finally:
				dest.close()

		return True


	# -------------------------------------------------------------------------
	# Import the given <data>
	# -------------------------------------------------------------------------

	def __import_data(self):

		# remember to login if not updating schema
		if not self.__do_schema:
			self.connections.loginToConnection(self.connection)

		print o(u_("Updating data ..."))

		# First fetch the current schema from the backend
		self._current = self.connection.readSchema()
		self._schema.merge(self._current)

		tables = {}
		pkeys  = {}
		fields = {}

		# Then make sure to have valid key information for all tables
		for tdata in self._schema.findChildrenOfType('GSTableData',False,True):
			table = self.__findTable(tdata.tablename)
			tables[table.name.lower()] = (table, tdata)
			fields[table.name.lower()] = sets.Set([f.name.lower() for f in \
						table.findChildrenOfType('GSField', False, True)])

			key = tdata.findChildOfType('GSPrimaryKey')
			if key is None:
				key = self.__get_key_from_table(table)
				if key is not None:
					GSchema.GSPrimaryKey(tdata).assign(key, True)

				else:
					q = u_("The table '%s' has no key defined. Shall i " \
							"insert all rows") % table.name
					if self.__ask(q, [u_("y"), u_("n")], u_("n")) == u_("n"):
						tdata.getParent()._children.remove(tdata)
						del tables[table.name.lower()]

			if key is not None:
				pkeys[table.name.lower()] = sets.Set([f.name.lower() for f in \
							key.findChildrenOfType('GSPKField', False, True)])

		# Since we have all key information available now, double check the
		# rows
		for item in self._schema.findChildrenOfType('GSTableData',False,True):
			keySet = pkeys.get(item.tablename.lower())

			for (n, r) in enumerate(item.findChildrenOfType('GSRow', False,
					True)):
				rowfields = sets.Set([value.field.lower() \
							for value in r.findChildrenOfType('GSValue', False, True)])

				# If the table has a key, are all keyfields available in the
				# row
				if keySet is not None and not keySet.issubset(rowfields):
					raise MissingKeyFieldError, (item.tablename, n, keySet,
						rowfields)

				# Are all fields in the row defined by the table
				if not rowfields.issubset(fields[item.tablename.lower()]):
					raise InvalidFieldsError, (item.tablename, n,
						rowfields.difference(fields[item.tablename]))

		# Order the tables so the do not violate constraints
		references = {}
		fishhooks  = {}

		for (table, tdata) in tables.values():
			deps = references.setdefault(table.name.lower(), [])

			for fk in table.findChildrenOfType('GSForeignKey', False, True):
				fkname = fk.references.lower()

				if fkname == table.name.lower():
					fishhooks.setdefault(table.name.lower(), []).append(fk)

				# Only add a dependency for a constraint, if we plan to add
				# data for that table too
				elif fkname in tables:
					if not fkname in deps:
						deps.append(fkname)

		needCommit = False
		for name in self.__order_by_dependency(references):
			(table, tdata) = tables[name]
			if not name in pkeys:
				needCommit |= self.__import_all_inserts(table, tdata)
			else:
				needCommit |= self.__import_table(table, tdata,
					fishhooks.get(name))

		if needCommit:
			self.connection.commit()


	# --------------------------------------------------------------------------
	# Import a table having a primary key
	# --------------------------------------------------------------------------

	def __import_table(self, table, tabledata, fishes):

		fields = {}
		for field in table.findChildrenOfType('GSField', False, True):
			fields[field.name.lower()] = field

		pkf = [f.name.lower() for f in \
				tabledata.findChildrenOfType('GSPKField', False, True)]
		rows       = {}
		rowFields  = {}
		fishLookup = {}

		for row in tabledata.findChildrenOfType('GSRow', False, True):
			record = {}
			for value in row.findChildrenOfType('GSValue'):
				fname = value.field.lower()
				rowFields[fname] = True
				record[fname] = self.__getValue(value, fields[fname])

			pkey = tuple([record[k] for k in pkf])
			rows[pkey] = record

			if fishes is not None:
				for fkey in fishes:
					ref = []
					for fkfield in fkey.findChildrenOfType('GSFKField'):
						ref.append(record.get(fkfield.references.lower()))

					fishLookup.setdefault(fkey.name, {})[tuple(ref)] = pkey


		if fishes is not None:
			sortdict = {}

			for (key, data) in rows.items():
				deps = sortdict.setdefault(key, [])

				for fkey in fishes:
					k = tuple([data.get(f.name.lower()) for f in \
								fkey.findChildrenOfType('GSFKField')])
					rkey = fishLookup[fkey.name].get(k)

					if rkey is not None:
						deps.append(rkey)

			recOrder = self.__order_by_dependency(sortdict,
				CircularDataReferences, table.name)
		else:
			recOrder = rows.keys()

		# Build a datasource and insert the data
		source = GDataSource.DataSourceWrapper(connections = self.connections,
			attributes = {'name'      : "dts_%s" % table.name,
				'connection': self.connection.name,
				'table'     : table.name,
				'primarykey': ",".join(pkf)},
			fields = rowFields.keys())

		# Build a mapping for the existing table, based on the primary key
		existing  = {}
		resultSet = source.createResultSet()

		rec = resultSet.firstRecord()
		while rec is not None:
			recKey = tuple([rec[f] for f in pkf])
			existing[recKey] = rec

			rec = resultSet.nextRecord()

		# Now run over all datarows in the previously determined order
		print o(u_("  updating table '%s' ...") % table.name)
		doPost = False
		new = 0
		upd = 0

		for key in recOrder:
			if key in existing:
				rs = existing[key]
				changed = 0

				for (field, value) in rows[key].items():
					(ov, nv) = GConditions.unify([rs.getField(field), value])
					if ov != nv:
						rs.setField(field, value)
						changed = 1

				upd += changed

			else:
				new   += 1
				newRec = resultSet.insertRecord()
				for (field, value) in rows[key].items():
					newRec.setField(field, value)

		if new or upd:
			resultSet.post()

		print o(u_("    Rows: %(ins)d inserted, %(upd)d updated, %(kept)d "
				"unchanged.") \
				% {'ins': new, 'upd': upd, 'kept': len(rows) - upd - new})

		return (new + upd) > 0


	# -------------------------------------------------------------------------
	# Import a table by inserting all it's rows
	# -------------------------------------------------------------------------

	def __import_all_inserts(self, table, tabledata):

		fields = {}
		for field in table.findChildrenOfType('GSField', False, True):
			fields[field.name.lower()] = field

		rows = []
		rowFields = {}

		for row in tabledata.findChildrenOfType('GSRow', False, True):
			record = {}
			for value in row.findChildrenOfType('GSValue'):
				fname = value.field.lower()
				rowFields[fname] = True
				record[fname] = self.__getValue(value, fields[fname])

			rows.append(record)

		if not rows:
			return False

		# Build a datasource and insert the data
		source = GDataSource.DataSourceWrapper(connections = self.connections,
			attributes = {'name'      : "dts_%s" % table.name,
				'connection': self.connection.name,
				'table'     : table.name},
			fields = rowFields.keys())

		print o(u_("  inserting into table '%s' ...") % table.name)

		resultSet = source.createEmptyResultSet()
		for record in rows:
			new = resultSet.insertRecord()
			for (field, value) in record.items():
				new.setField(field, value)

		resultSet.post()

		print o(u_("    Rows: %(ins)d inserted") % {'ins': len(rows)})

		return True


	# -------------------------------------------------------------------------
	# Order a given dependency tree
	# -------------------------------------------------------------------------

	def __order_by_dependency(self, depTree, error=CircularReferenceError, *ea):

		result = []

		while depTree:
			addition = []

			for (key, deps) in depTree.items():
				# If a key has no dependencies, add it to the result
				if not len(deps):
					addition.append(key)

					# and remove that key from all other dependency sequences
					for otherDeps in depTree.values():
						if key in otherDeps:
							otherDeps.remove(key)

					# finally remove it from the dictionary
					del depTree[key]

			# If no key without a dependency was found, but there are still
			# entries in the tree, they *must* have circular references
			if not addition and depTree:
				raise error, ea

			result.extend(addition)

		return result


	# -------------------------------------------------------------------------
	# Get a native python value from a GSValue instance using a given GSField
	# -------------------------------------------------------------------------

	def __getValue(self, value, field):

		ftype    = field.type.lower()
		contents = value.getChildrenAsContent()

		# unquote the contents if it is quoted
		if len(contents) > 1 and contents[0] in ["'", '"']:
			if contents[-1] == contents[0]:
				contents = contents[1:-1]

		# If no value is given, just return None
		if not len(contents):
			return None

		length = hasattr(field, 'length') and field.length or 0
		scale  = hasattr(field, 'precision') and field.precision or 0

		# return string type fields with an optional length restriction
		if ftype == 'string':
			maxlen = length and length or len(contents)
			return contents[:maxlen]

		# Try to convert a numeric field according to length and scale
		elif ftype == 'number':
			value = contents.strip()

			if value in [u'TRUE', u'FALSE']:
				return int(value == u'TRUE')

			elif length or scale:
				vmatch = re.compile('^([+-]{0,1})(\d+)[\.]{0,1}(\d*)$').match(\
						value)
				if vmatch is None:
					raise InvalidNumberError, (value, length, scale)

				(sign, pre, frac) = vmatch.groups()
				if len(pre) > (length - scale) or len(frac) > scale:
					OutOfRangeError, (value, length, scale)

				if len(frac):
					return float("%s%s.%s" % (sign, pre, frac))

				else:
					return int("%s%s" % (sign, pre))

			# we don't know anything about precision
			else:
				if '.' in value or ',' in value:
					return float(value)

				else:
					return int(value)

		# booleans must be 'TRUE' or 'FALSE', otherwise they're None
		elif ftype == 'boolean':
			bool = contents.upper().strip()
			if bool in ['TRUE', 'FALSE']:
				return bool == 'TRUE'
			else:
				raise InvalidBooleanError, bool

		# Dates must conform with the ISO spec: YYYY-MM-DD
		elif ftype == 'date':
			try:
				return GDateTime.parseISODate(contents.strip())

			except ValueError:
				raise InvalidDateError, contents.strip()

		# Times must conform with the ISO spec: HH:[MM:[:SS[.ss]]]
		elif ftype == 'time':
			try:
				return GDateTime.parseISOTime(contents.strip())

			except ValueError:
				raise InvalidTimeError, contents.strip()

		elif ftype == 'datetime':
			try:
				return GDateTime.parseISO(contents.strip())

			except ValueError:
				raise InvalidDateTimeError, contents.strip()

		else:
			raise InvalidTypeError, ftype


	# --------------------------------------------------------------------------
	# Find a given GSTable instance in the current schema
	# --------------------------------------------------------------------------

	def __findTable(self, name):

		for item in self._current.findChildrenOfType('GSTable', False, True):
			if item.name.lower() == name.lower():
				return item

		raise MissingTableError, (name)


	# --------------------------------------------------------------------------
	# Get a usable key from the given table
	# --------------------------------------------------------------------------

	def __get_key_from_table(self, table):

		# Is there a PK defined in the backend schema ?
		pk = table.findChildOfType('GSPrimaryKey')
		if pk is not None:
			return pk

		# Maybe we could use a 'unique index' to as key, since it has the same
		# nature as a primary key. But then we have to check wether all <rows>
		# have all fields used by the index available. This is left for a future
		# version though :)

		return None


	# -------------------------------------------------------------------------
	# Ask a question with a set of valid options and a default
	# -------------------------------------------------------------------------

	def __ask(self, question, options, default):
		"""
		Ask for a question, allowing a set of answers, using a default-value if
		the user just presses <Enter>.

		@param question: string with the question to ask
		@param options: sequence of allowed options, i.e. ['y', 'n']
		@param default: string with the default option

		@return: string with the option selected
		"""

		if self.OPTIONS['yes']:
			return u_("y")

		answer  = None
		default = default.lower()
		lopts   = [opt.lower() for opt in options]

		dopts   = []
		for item in lopts:
			dopts.append(item == default and item.upper() or item)

		while True:
			print o(question), o("[%s]:" % ",".join(dopts)),
			answer = raw_input().lower() or default

			if answer in lopts:
				break

		return answer


# =============================================================================
# Main program
# =============================================================================

if __name__ == '__main__':
	gsdClient().run()
