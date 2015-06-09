# GNU Enterprise Common Library - Schema support for Firebird/Interbase
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
# $Id: Behavior.py 9222 2007-01-08 13:02:49Z johannes $

"""
Schema support plugin for Firebird/Interbase backends.
"""

__all__ = ['Behavior']

import re

from gnue.common.datasources import GLoginHandler, GSchema
from gnue.common.datasources.drivers import DBSIG2


# =============================================================================
# Behavior class
# =============================================================================

class Behavior (DBSIG2.Behavior):
	"""
	Behavior class for Firebird/Interbase backends.

	Limitations:
	  - Interbase/Firebird has no native boolean datatype. That's why this
	    introspection module treats the domain 'BOOLEAN' as boolean data types.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connection):

		DBSIG2.Behavior.__init__ (self, connection)

		self.__RELTYPE    = {False: {'type': 'table', 'name': u_('Tables')},
			True : {'type': 'view' , 'name': u_('Views')}}
		self.__TYPEMAP    = {'DATE'     : 'date',
			'TIME'     : 'time',
			'TIMESTAMP': 'datetime'}
		self.__NOW        = re.compile ("'(NOW\s*\(\)\s*)'", re.IGNORECASE)
		self.__GENFIELD   = re.compile ('^.*NEW\.(\w+)\s*=\s*GEN_ID\s*\(.*\)',
			re.IGNORECASE)
		self.__maxVarchar = 10921

		self._maxIdLength_   = 31
		self._alterMultiple_ = False
		self._numbers_       = [[(4, 'SMALLINT'), (9, 'INTEGER')], "NUMERIC(%s)",
			"NUMERIC (%(length)s,%(scale)s)"]

		self._type2native_ ['datetime'] = 'timestamp'
		self._type2native_ ['boolean']  = 'boolean'


	# ---------------------------------------------------------------------------
	# Create a new database
	# ---------------------------------------------------------------------------

	def _createDatabase_ (self):
		"""
		Create a new database for the associated connection. The password for the
		SYSDBA will be queried.
		"""

		dbname   = self.__connection.parameters.get ('dbname', None)
		username = self.__connection.parameters.get ('username', 'gnue')
		password = self.__connection.parameters.get ('password', 'gnue')
		host     = self.__connection.parameters.get ('host', None)
		gsecbin  = self.__connection.parameters.get ('gsecbin', 'gsec')

		loginHandler = GLoginHandler.BasicLoginHandler ()
		fields       = [(u_("Password"), '_password', 'password', None, None, [])]
		title        = u_("Logon for SYSDBA into Security Database")

		error = None
		res   = {'_password': ''}
		while not res ['_password']:
			res = loginHandler.askLogin (title, fields, {}, error)
			if not res ['_password']:
				error = u_("Please specify a password")

		syspw = res ['_password']

		if host:
			dburl = "%s:%s" % (host, dbname)
		else:
			dburl = dbname

		code = u"%s -user sysdba -password %s -delete %s" % \
			(gsecbin, syspw, username)

		try:
			os.system (code)
		except:
			pass

		code = u"%s -user sysdba -password %s -add %s -pw %s" % \
			(gsecbin, syspw, username, password)

		try:
			# if creating the user fails we try to create the db anyway. Maybe this
			# is done from a remote system where no gsec is available, but the given
			# credentials are valid on the given server.
			os.system (code)
		except:
			pass

		self.__connection._driver.create_database (\
				u"create database '%s' user '%s' password '%s' " \
				"default character set UNICODE_FSS" % (dburl, username, password))

		self.__connection.manager.loginToConnection (self.__connection)

		code = u"CREATE DOMAIN boolean AS smallint " \
			"CHECK (value IN (0,1) OR value IS NULL);"
		self.__connection.makecursor (code)

		code = u"DECLARE EXTERNAL FUNCTION lower CSTRING(255) " \
			"RETURNS CSTRING(255) FREE_IT " \
			"ENTRY_POINT 'IB_UDF_lower' MODULE_NAME 'ib_udf';"
		self.__connection.makecursor (code)
		self.__connection.commit ()

	# ---------------------------------------------------------------------------
	# Read the current connection's schema
	# ---------------------------------------------------------------------------

	def _readSchema_ (self, parent):
		"""
		"""

		tables = self.__readTables (parent)
		fields = self.__readFields (tables)
		constr = self.__readConstraints (tables)
		self.__readKeys (tables, constr)
		self.__readSerials (tables)


	# --------------------------------------------------------------------------
	# Read all tables and views
	# --------------------------------------------------------------------------

	def __readTables (self, parent):

		cmd = u"SELECT rdb$relation_name, rdb$view_source FROM RDB$RELATIONS " \
			"WHERE rdb$system_flag = 0 ORDER BY rdb$relation_name"

		result  = {}
		masters = {}
		cursor  = self.__connection.makecursor (cmd)

		for rs in cursor.fetchall ():
			(name, source) = self.__stripStrings (rs)
			reltype = self.__RELTYPE [source is not None]
			if not reltype ['type'] in masters:
				masters [reltype ['type']] = GSchema.GSTables (parent, **reltype)

			result [name] = GSchema.GSTable (masters [reltype ['type']], name = name)

		return result


	# ---------------------------------------------------------------------------
	# Read all fields of the given tables
	# ---------------------------------------------------------------------------

	def __readFields (self, tables):

		result = {}

		cmd = u"SELECT rf.rdb$relation_name, rf.rdb$field_name, tp.rdb$type_name," \
			"  rf.rdb$null_flag, rf.rdb$default_source, fs.rdb$field_length, " \
			"  fs.rdb$field_scale, fs.rdb$field_precision, " \
			"  fs.rdb$character_length, rf.rdb$field_source " \
			"FROM rdb$relation_fields rf, rdb$fields fs, rdb$types tp " \
			"WHERE " \
			"fs.rdb$field_name = rf.rdb$field_source AND " \
			"tp.rdb$type = fs.rdb$field_type AND " \
			"tp.rdb$field_name = 'RDB$FIELD_TYPE'" \
			"ORDER BY rf.rdb$relation_name, rf.rdb$field_position"

		cursor = self.__connection.makecursor (cmd)
		try:
			for rs in cursor.fetchall ():
				(table, name, ftype, null, default, flen, scale, prec, clen, fsrc) = \
					self.__stripStrings (rs)

				if not table in tables:
					continue

				nativetype = ftype
				attrs = {'id'        : "%s.%s" % (table, name),
					'name'      : name,
					'nativetype': nativetype,
					'nullable'  : not null}

				if fsrc == 'BOOLEAN':
					attrs ['type'] = 'boolean'

				elif nativetype in self.__TYPEMAP:
					attrs ['type'] = self.__TYPEMAP [nativetype]

				elif nativetype in ['DOUBLE', 'FLOAT', 'INT64', 'LONG', 'QUAD', \
						'SHORT']:
					attrs ['type']      = 'number'
					if prec == 0 and scale == 0:
						attrs ['length'] = len ("%s" % 2L ** (flen * 8))
					else:
						attrs ['length']    = prec
						attrs ['precision'] = abs (scale)

				else:
					attrs ['type']   = 'string'
					attrs ['length'] = clen

				if default is not None:
					if self.__NOW.search (default) is not None:
						attrs ['defaultwith'] = 'timestamp'
					else:
						attrs ['defaultwith'] = 'constant'
						attrs ['defaultl']    = default [8:]

				fields = tables [table].findChildOfType ('GSFields') or \
					GSchema.GSFields (tables [table])

				result [attrs ['id']] = GSchema.GSField (fields, **attrs)

		finally:
			cursor.close ()

		return result


	# ---------------------------------------------------------------------------
	# Read all relation constraints (pk/fk only)
	# ---------------------------------------------------------------------------

	def __readConstraints (self, tables):

		cmd = u"SELECT rdb$relation_name, rdb$constraint_name, " \
			"   rdb$constraint_type, rdb$index_name " \
			"FROM rdb$relation_constraints " \
			"WHERE rdb$constraint_type IN " \
			"      ('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE')"

		result = {}
		cursor = self.__connection.makecursor (cmd)
		try:
			for rs in cursor.fetchall ():
				(tname, name, ctype, index) = self.__stripStrings (rs)

				table = tables.get (tname)
				if table is None:
					continue

				if ctype == 'PRIMARY KEY':
					item = GSchema.GSPrimaryKey (table, name = name)
				else:
					cons = table.findChildOfType ('GSConstraints') or \
						GSchema.GSConstraints (table)
					if ctype == 'UNIQUE':
						item = GSchema.GSUnique (cons, name = name)
					else:
						item = GSchema.GSForeignKey (cons, name = name)

				result ["%s.%s" % (tname, index)] = item

		finally:
			cursor.close ()

		return result


	# ---------------------------------------------------------------------------
	# Read indices and populate constraints
	# ---------------------------------------------------------------------------

	def __readKeys (self, tables, constraints):

		fields = {}    # Map index to fields
		relmap = {}    # Map index to relations
		update = {}    # Map FK-Relations to be updated after the first run

		# First build a mapping of all index fields
		cmd = u"SELECT rdb$index_name, rdb$field_name FROM rdb$index_segments " \
			"ORDER BY rdb$index_name, rdb$field_position"

		cursor = self.__connection.makecursor (cmd)

		try:
			for (index, field) in cursor.fetchall ():
				seq = fields.setdefault (index.strip (), [])
				seq.append (field.strip ())

		finally:
			cursor.close ()

		# Now build up the indices and populate the constraints
		cmd = u"SELECT rdb$index_name, rdb$relation_name, rdb$unique_flag, " \
			"  rdb$foreign_key " \
			"FROM rdb$indices " \
			"WHERE (rdb$index_inactive IS NULL or rdb$index_inactive = 0) " \
			"ORDER BY rdb$relation_name, rdb$index_id"

		cursor = self.__connection.makecursor (cmd)
		try:
			for rs in cursor.fetchall ():
				(iname, tname, unique, fkey) = self.__stripStrings (rs)
				if not tname in tables:
					continue

				relmap [iname] = tname
				table = tables [tname]

				constraint = constraints.get ("%s.%s" % (tname, iname))
				if constraint is None:
					ind = table.findChildOfType ('GSIndexes') or GSchema.GSIndexes (table)
					index = GSchema.GSIndex (ind, name = iname, unique = unique == 1)

					for field in fields [iname]:
						GSchema.GSIndexField (index, name = field)
				else:
					if isinstance (constraint, GSchema.GSPrimaryKey):
						for field in fields [iname]:
							GSchema.GSPKField (constraint, name = field)

					elif isinstance (constraint, GSchema.GSUnique):
						for field in fields [iname]:
							GSchema.GSUQField (constraint, name = field)

					else:
						for (field, reffield) in zip (fields [iname], fields [fkey]):
							GSchema.GSFKField (constraint, name = field,
								references = reffield)
						update.setdefault (fkey, []).append (constraint)

			for (fkey, constraints) in update.items ():
				for item in constraints:
					item.references = relmap [fkey]

		finally:
			cursor.close ()


	# ---------------------------------------------------------------------------
	# Read all 'before insert'-triggers to discover Generator based fields
	# ---------------------------------------------------------------------------

	def __readSerials (self, tables):

		cmd = u"SELECT rdb$relation_name, rdb$trigger_source " \
			"FROM rdb$triggers " \
			"WHERE rdb$trigger_type = 1 " \
			"ORDER BY rdb$trigger_sequence"
		cursor = self.__connection.makecursor (cmd)

		try:
			for rs in cursor.fetchall ():
				(relname, source) = self.__stripStrings (rs)
				if not relname in tables:
					continue

				match = self.__GENFIELD.match (source)
				if match is not None:
					fieldname = match.groups () [0].upper ()
					fields = tables [relname].findChildrenOfType ('GSField', False, True)
					for item in fields:
						if item.name == fieldname:
							item.defaultwith = 'serial'

		finally:
			cursor.close ()


	# ---------------------------------------------------------------------------
	# Strip all 'stripable' elements in a given sequence
	# ---------------------------------------------------------------------------

	def __stripStrings (self, seq):

		result = []
		append = result.append

		for item in seq:
			if hasattr (item, 'strip'):
				append (item.strip ())
			else:
				append (item)

		return result


	# ---------------------------------------------------------------------------
	# Process a defaultwith attribute
	# ---------------------------------------------------------------------------

	def _defaultwith_ (self, code, field):
		"""
		Process special kinds of default values like sequences, functions and so
		on. Defaults of type 'constant' are already handled by '_processFields_'.

		@param code: code-triple of the current field as built by _processFields_
		@param field: GSField instance to process the default for
		"""

		if field.defaultwith == 'serial':
			table = field.findParentOfType ('GSTable')
			seq   = self._getSequenceName (field)

			code [0].append (u"CREATE GENERATOR %s" % seq)
			code [2].append ( \
					u"CREATE TRIGGER trg_%s FOR %s ACTIVE BEFORE INSERT POSITION 0 AS " \
					"BEGIN IF (NEW.%s IS NULL) THEN NEW.%s = GEN_ID (%s,1); END" \
					% (field.name, table.name, field.name, field.name, seq))

		elif field.defaultwith == 'timestamp':
			field.default = "NOW"


	# ---------------------------------------------------------------------------
	# Create a native type representation for strings
	# ---------------------------------------------------------------------------

	def string (self, field):
		"""
		Return the native datatype for a string-field.

		@param field: GSField instance to get the native datatype for
		@return: string with the native datatype
		"""

		if hasattr (field, 'length') and field.length <= self.__maxVarchar:
			return "varchar (%s)" % field.length

		elif not hasattr (field, 'length'):
			return "varchar (%s)" % self.__maxVarchar

		else:
			return "blob"
