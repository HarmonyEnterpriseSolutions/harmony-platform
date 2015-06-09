# GNU Enterprise Common Library - Schema support for SQLite
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
Schema support plugin for SQLite.
"""

__all__ = ['Behavior']

import re

from gnue.common.apps import errors
from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers import DBSIG2


# ===========================================================================
# Regular expressions and constants
# ===========================================================================

_REPCOMMAS   = re.compile ('\(\s*(\d+)\s*,\s*(\d+)\s*\)')
_ALIGN       = re.compile ('\s*\(\s*(.*?)\s*\)')
_LEN_SCALE   = re.compile ('^\s*(\w+)\s*\((\d+)[;]{0,1}(\d*)\)\s*')
_TEXTTYPE    = re.compile ('.*(BLOB|CHAR|CLOB|TEXT){1}.*')
_BLANKS      = re.compile ('\s+')
_NOTNULL     = re.compile ('(.*)(NOT NULL)(.*)', re.I)
_CONSTRAINTS = re.compile ('.*?((UNIQUE|CHECK|PRIMARY KEY)\s*\(.*?\)).*', re.I)
_PRIMARYKEY  = re.compile ('.*?PRIMARY KEY\s*\((.*?)\).*', re.I)
_PKFIELD     = re.compile ('.*?PRIMARY\s+KEY\s*', re.I)
_INDEX       = re.compile ('CREATE\s*(\w+){0,1}\s*INDEX\s*(\w+)\s*ON\s*\w+\s*'\
		'\((.*?)\).*', re.I)
_VIEWCODE    = re.compile ('^\s*CREATE\s+VIEW\s+\w+\s+AS\s+(.*)\s*$', re.I)
_DEFAULT     = re.compile ('.*\s+DEFAULT\s+(.*)', re.I)
_SQLCODE     = re.compile ('\s*SELECT\s+(.*)\s+FROM\s+(\w+).*', re.I)
_CMD         = re.compile ('(.*?)\((.*)\)(.*)')


# =============================================================================
# Excpetions
# =============================================================================

class MissingTableError (errors.AdminError):
	"""
	Table should be altered but original table cannot be found.
	"""
	def __init__ (self, table):
		msg = u_("Cannot find table '%s' anymore") % table
		errors.AdminError.__init__ (self, msg)

class InvalidSQLCommand (errors.SystemError):
	"""
	SQL command used to create the table cannot be parsed.
	"""
	def __init__ (self, sql):
		msg = u_("Cannot split SQL command: '%s'") % sql
		errors.SystemError.__init__ (self, msg)


# =============================================================================
# Behavior class
# =============================================================================

class Behavior (DBSIG2.Behavior):
	"""
	Behavior class for SQLite backends.

	Limitations:
	  - Since SQLite is typeless we cannot derive a 'length' for columns
	    specified as 'integer' or 'text' without any further information.
	  - SQLite does not support referential constraints
	  - SQLite has no real concept of a serial
	  - SQLite has no concept of a 'default with timestamp'
	  - Name of Primary Keys is not available
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connection):

		DBSIG2.Behavior.__init__ (self, connection)

		self.__RELTYPE = {'table': {'type': 'table', 'name': u_("Tables")},
			'view' : {'type': 'view',  'name': u_("Views")}}

		self._maxIdLength_   = 31
		self._alterMultiple_ = False
		self._numbers_       = [[(None, 'integer')],
			"",
			"numeric (%(length)s,%(scale)s)"]

		self._type2native_.update ({'boolean' : 'integer',
				'datetime': 'timestamp'})

		self._passThroughTypes = ['date', 'datetime', 'time']


	# ---------------------------------------------------------------------------
	# Create a new database
	# ---------------------------------------------------------------------------

	def _createDatabase_ (self):
		"""
		Create a new SQLite database for the associated connection.
		"""

		dbname = self.__connection.parameters.get ('dbname')
		self.__connection.manager.loginToConnection (self.__connection)


	# ---------------------------------------------------------------------------
	# Read the current connection's schema
	# ---------------------------------------------------------------------------

	def _readSchema_ (self, parent):
		"""
		Read the connection's schema and build a GSchema object tree connected to
		the given parent object (which is of type GSSchema).
		"""

		tables = self.__readTables (parent)
		self.__readIndices (tables)


	# ---------------------------------------------------------------------------
	# Read all tables
	# ---------------------------------------------------------------------------

	def __readTables (self, parent):

		cmd = u"SELECT type, name, sql FROM sqlite_master ORDER BY lower (name)"

		result  = {}
		masters = {}
		views   = {}
		cursor  = self.__connection.makecursor (cmd)

		try:
			for (reltype, name, sql) in cursor.fetchall ():
				if not reltype in self.__RELTYPE:
					continue

				if not reltype in masters:
					masters [reltype] = GSchema.GSTables (parent,
						**self.__RELTYPE [reltype])

				key = name.lower ()
				result [key] = GSchema.GSTable (masters [reltype], name = name,
					sql = sql)

				if reltype == 'table':
					self.__parseFields (result [key], sql)

					pkm = _PRIMARYKEY.match (sql)
					if pkm is not None:
						pk = GSchema.GSPrimaryKey (result [key], name = 'pk_%s' % name)

						for field in [f.strip () for f in pkm.groups () [0].split (',')]:
							GSchema.GSPKField (pk, name = field)

				else:
					views [key] = sql

		finally:
			cursor.close ()

		self.__parseViews (result, views)

		return result


	# ---------------------------------------------------------------------------
	# Parse all fields from a given SQL code
	# ---------------------------------------------------------------------------

	def __parseFields (self, table, sql):

		result = {}

		# Replace all newlines by a single whitespace and take all the code in
		# between the first and last bracket
		code = ' '.join (sql.splitlines ())
		code = code [code.find ('(') + 1:code.rfind (')')]

		# Reduce multiple blanks to a single blank
		code = _BLANKS.sub (' ', code)
		# Make sure to have numeric arugments like '( 5 , 2)' given as '(5;2)'
		code = _REPCOMMAS.sub (r'(\1;\2)', code)
		# Realign arguments in parenthesis, i.e. from 'char(  7 )' to 'char (7)'
		code = _ALIGN.sub (r' (\1)', code)

		# we currently skip all constraints (primary key, unique, check)
		cma = _CONSTRAINTS.match (code)
		while cma is not None:
			constraint = cma.groups () [0]
			code = code.replace (constraint, '')
			cma = _CONSTRAINTS.match (code)

		for item in [i.strip () for i in code.split (',')]:
			if not len (item):
				continue

			parts = item.split ()

			if _PKFIELD.match (item) is not None:
				pk = table.findChildOfType ('GSPrimaryKey') or \
					GSchema.GSPrimaryKey (table, name = 'pk_%s' % table.name)
				GSchema.GSPKField (pk, name = parts [0])

			attrs = {'id'  : "%s.%s" % (table.name, parts [0]),
				'name': parts [0]}

			datatype = ' '.join (parts [1:])

			lsmatch = _LEN_SCALE.match (datatype)
			if lsmatch is not None:
				(typename, length, scale) = lsmatch.groups ()
			else:
				typename = parts [1]
				length   = 0
				scale    = 0

			nativetype = typename
			add = filter (None, [length, scale])
			nativetype += add and "(%s)" % ','.join (add) or ''

			attrs ['nativetype'] = nativetype

			if length:
				attrs ['length'] = int (length)
			if scale:
				attrs ['precision'] = int (scale)

			attrs ['nullable']   = _NOTNULL.match (item) is None

			if _TEXTTYPE.match (typename.upper ()):
				attrs ['type'] = 'string'

			elif typename.lower () == 'timestamp':
				attrs ['type'] = 'datetime'

			elif typename.lower () in self._passThroughTypes:
				attrs ['type'] = typename.lower ()

			else:
				attrs ['type'] = 'number'

			fields = table.findChildOfType ('GSFields') or GSchema.GSFields (table)
			result [attrs ['id']] = GSchema.GSField (fields, **attrs)

			match = _DEFAULT.match (item)
			if match is not None:
				text = match.groups () [0].strip ()
				if text [0] in ["'", '"']:
					default = text [1:text.find (text [0], 1)]
				else:
					default = text.split () [0]

				result [attrs ['id']].defaultwith = 'constant'
				result [attrs ['id']].default     = default

		return result


	# ---------------------------------------------------------------------------
	# Read all indices for the given tables
	# ---------------------------------------------------------------------------

	def __readIndices (self, tables):

		cmd = u"SELECT lower (tbl_name), name, sql FROM sqlite_master " \
			"WHERE type = 'index' AND sql IS NOT NULL"

		cursor = self.__connection.makecursor (cmd)

		try:
			for (tname, name, sql) in cursor.fetchall ():
				table = tables [tname]

				ixm = _INDEX.match (sql)
				if ixm is not None:
					(unique, name, fields) = ixm.groups ()

					top = table.findChildOfType ('GSIndexes') or GSchema.GSIndexes (table)
					index = GSchema.GSIndex (top, name = name,
						unique = unique is not None and unique.lower () == 'unique')

					for field in [f.strip () for f in fields.split (',')]:
						GSchema.GSIndexField (index, name = field)

		finally:
			cursor.close ()


	# ---------------------------------------------------------------------------
	# Populate the view objects
	# ---------------------------------------------------------------------------

	def __parseViews (self, tables, views):

		for (viewname, sql) in views.items ():
			code = ' '.join (sql.splitlines ())
			code = _VIEWCODE.match (code)
			if not code:
				continue

			match = _SQLCODE.match (code.groups () [0])
			if match:
				(fieldseq, relname) = match.groups ()
				tablename = relname.lower ()
				if not viewname in tables or not tablename in tables:
					continue

				view    = tables [viewname]
				table   = tables [tablename]
				tfields = table.findChildrenOfType ('GSField', False, True)
				vfields = view.findChildOfType ('GSFields') or GSchema.GSFields (view)

				for item in [f.strip ().lower () for f in fieldseq.split (',')]:
					tf = None
					for f in tfields:
						if f.name.lower () == item:
							tf = f
							break

					if tf is None: continue

					vf = GSchema.GSField (vfields, name = tf.name, type = tf.type)
					for key in ['length', 'precision', 'nullable', 'default',
						'defaultwith']:
						if hasattr (tf, key):
							setattr (vf, key, getattr (tf, key))


	# ---------------------------------------------------------------------------
	# Create constraint definition
	# ---------------------------------------------------------------------------

	def _createConstraint_ (self, constraint):
		"""
		SQLite does not support referential constraints, so this function returns
		an empty code-triple.
		"""

		return ([], [], [])


	# ---------------------------------------------------------------------------
	# Drop a given constraint
	# ---------------------------------------------------------------------------

	def _dropConstraint_ (self, constraint):
		"""
		SQLite does not support referential constraints, so this function returns
		an empty code-triple.
		"""
		return ([], [], [])


	# ---------------------------------------------------------------------------
	# Create a primary key definition
	# ---------------------------------------------------------------------------

	def _createPrimaryKey_ (self, pkey):
		"""
		Create a code-triple for the given primary key

		@param pkey: GSPrimaryKey instance to create a code-sequence for
		@return: code-triple for the primary key
		"""

		fields = pkey.findChildrenOfType ('GSPKField', False, True)
		code   = u"PRIMARY KEY (%s)" % ", ".join ([f.name for f in fields])

		return ([], [code], [])


	# ---------------------------------------------------------------------------
	# Create a command sequence for creating/modifying tables
	# ---------------------------------------------------------------------------

	def _createTable_ (self, table):

		# We need to know if the diff contains new fields. If not, we can use the
		# DBSIG2 way for code-generation
		newFields = [f.name for f in table.fields ('add')]

		# DBSIG2 behavior can handle new or removed tables well
		if table._action != 'change' or not newFields:
			result = DBSIG2.Behavior._createTable_ (self, table)
			return result

		# But since SQLite does not support ALTER TABLE statements we've to handle
		# that situation here
		else:
			result   = (pre, body, post) = ([], [], [])
			original = None

			# First find the original table
			for item in self._current.findChildrenOfType ('GSTable', False, True):
				if item._id_ (self._maxIdLength_) == table._id_ (self._maxIdLength_):
					original = item
					break

			if original is None:
				raise MissingTableError, table.name

			parts = _CMD.match (original.sql)
			if not parts:
				raise InvalidSQLCommand, original.sql

			fields  = [f.name for f in original.fields ()]
			nfields = ["NULL" for f in table.fields ()]
			nfields.extend (fields)

			# Build the temporary table, populate it with all rows and finally
			# drop the table. This will drop all indices too.
			body.append (u"CREATE TEMPORARY TABLE t1_backup (%s)" % ",".join (fields))
			body.append (u"INSERT INTO t1_backup SELECT %(fields)s FROM %(table)s" \
					% {'fields': ", ".join (fields),
					'table' : self._shortenName (table.name)})
			body.append (u"DROP TABLE %s" % self._shortenName (table.name))

			# Build the new table using all new fields concatenated with the old
			# SQL-command.
			fcode = self._createFields_ (table)
			self._mergeTriple (result, (fcode [0], [], fcode [2]))

			oldSQL  = parts.groups ()
			newBody = [", ".join (fcode [1])]
			if len (oldSQL [1]):
				newBody.append (oldSQL [1])

			cmd = u"%s (%s)%s" % (oldSQL [0], ", ".join (newBody), oldSQL [2])

			body.append (cmd)
			body.append (u"INSERT INTO %(table)s SELECT %(fields)s FROM t1_backup" \
					% {'table' : self._shortenName (table.name),
					'fields': ",".join (nfields)})
			body.append (u"DROP TABLE t1_backup")

			# Finally create all indices as given by the new table
			for item in self._new.findChildrenOfType ('GSTable', False, True):
				if item._id_ (self._maxIdLength_) == table._id_ (self._maxIdLength_):
					for index in item.findChildrenOfType ('GSIndex', False, True):
						self._mergeTriple (result, self._createIndex_ (index))

					break

			return result
