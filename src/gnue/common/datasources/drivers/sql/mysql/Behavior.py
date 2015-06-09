# GNU Enterprise Common Library - Schema support for MySQL
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
# $Id: Behavior.py 9410 2007-02-26 08:21:54Z johannes $

"""
Schema support plugin for MySQL backends.
"""

__all__ = ['Behavior']

import os

from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers import DBSIG2


# =============================================================================
# Behavior class
# =============================================================================

class Behavior (DBSIG2.Behavior):
	"""
	Behavior class for MySQL backends.

	Limitations
	  - MySQL does not support booleans, nor does it have column checks. So a
	    'boolean' column will be transformed into a 'number' silently.
	  - MySQL does not give us a chance to find out anything about foreign key
	    constraints. (Even with InnoDB it's quite hard to parse it from SHOW
	    CREATE TABLE or SHOW TABLE STATUS)
	  - MySQL does *not* store the name of a primary key, instead this is always
	    'PRIMARY'. That's why we lose the original primary key's names.
	  - You cannot set the value of an AUTO_INCREMENT field to 0 using an INSERT
	    statement.  To do this you'd have to insert first and the use an UPDATE
	    afterwards using the last serial value as key.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, *args, **kwargs):

		DBSIG2.Behavior.__init__ (self, *args, **kwargs)

		self.__TYPEMAP = {'string'   : ('string', 'string'),
			'date'     : ('date', 'date'),
			'time'     : ('date', 'time'),
			'timestamp': ('date', 'timestamp'),
			'datetime' : ('date', 'datetime')}

		# Update the typemap with numeric types
		for t in ['int','integer','bigint','mediumint',
			'smallint','tinyint','float','real', 'double','decimal']:
			self.__TYPEMAP [t] = ('number', 'number')

		self._maxIdLength_ = 64
		self._numbers_     = [[(4, 'smallint'), (9, 'int'), (18, 'bigint')],
			"decimal (%s,0)", "decimal (%(length)s,%(scale)s)"]

		self._type2native_ ['boolean'] = "tinyint (1) unsigned"


	# ---------------------------------------------------------------------------
	# Create a new database
	# ---------------------------------------------------------------------------

	def _createDatabase_ (self):
		"""
		Create a new database for the associated connection. In order to be
		successfull the current account must have enough privileges to create new
		databases.
		"""

		dbname   = self.__connection.parameters.get ('dbname')
		username = self.__connection.parameters.get ('username', 'gnue')
		password = self.__connection.parameters.get ('password')
		host     = self.__connection.parameters.get ('host')
		port     = self.__connection.parameters.get ('port')
		owner    = self.__connection.parameters.get ('owner', username)
		ownerpwd = self.__connection.parameters.get ('ownerpwd')

		createdb = u"mysqladmin %(site)s%(port)s%(user)s%(pwd)s create %(db)s" \
			% {'db'  : dbname,
			'site': host and "--host=%s " % host or '',
			'port': port and "--port=%s " % port or '',
			'user': owner and "--user=%s " % owner or '',
			'pwd' : ownerpwd and "--password=%s " % ownerpwd or ''}

		os.system (createdb)

		sql = u"GRANT ALL PRIVILEGES ON %(db)s.* TO '%(user)s'@'%%' %(pass)s" \
			% {'db'  : dbname,
			'user': username,
			'pass': password and "IDENTIFIED BY '%s'" % password or ""}

		grant = 'mysql %(host)s%(port)s%(user)s%(pass)s -e "%(sql)s" -s %(db)s' \
			% {'sql' : sql,
			'host': host and "--host=%s " % host or '',
			'port': port and "--port=%s " % port or '',
			'user': owner and "--user=%s " % owner or '',
			'pass': ownerpwd and "--password=%s " % ownerpwd or '',
			'db'  : dbname}

		os.system (grant)

		sql = u"GRANT ALL PRIVILEGES ON %(db)s.* TO '%(user)s'@'localhost' " \
			"%(pass)s" \
			% {'db': dbname,
			'user': username,
			'pass': password and "IDENTIFIED BY '%s'" % password or ""}

		grant = 'mysql %(host)s%(port)s%(user)s%(pass)s -e "%(sql)s" -s %(db)s' \
			% {'sql' : sql,
			'host': host and "--host=%s " % host or '',
			'port': port and "--port=%s " % port or '',
			'user': owner and "--user=%s " % owner or '',
			'pass': ownerpwd and "--password=%s " % ownerpwd or '',
			'db'  : dbname}

		os.system (grant)


	# ---------------------------------------------------------------------------
	# Read the current connection's schema
	# ---------------------------------------------------------------------------

	def _readSchema_ (self, parent):
		"""
		Read the connection's schema and build a GSchema object tree connected to
		the given parent object (which is of type GSSchema).
		"""

		tables = self.__readTables (parent)
		fields = self.__readFields (tables)
		self.__readIndices (tables)


	# ---------------------------------------------------------------------------
	# Read all tables available
	# ---------------------------------------------------------------------------

	def __readTables (self, parent):

		tables = None
		result = {}

		cursor = self.__connection.makecursor (u"SHOW TABLES")
		try:
			for (tablename,) in cursor.fetchall ():
				if tables is None:
					tables = GSchema.GSTables (parent, type = 'table', name = u_("Tables"))

				result [tablename] = GSchema.GSTable (tables, name = tablename)

		finally:
			cursor.close ()

		return result


	# ---------------------------------------------------------------------------
	# Read all fields for the given tables
	# ---------------------------------------------------------------------------

	def __readFields (self, tables):

		result = {}

		for (tablename, table) in tables.items ():
			fields = table.findChildOfType ('GSFields')
			if fields is None:
				fields = GSchema.GSFields (table)

			cmd = u"SHOW COLUMNS FROM %s" % tablename
			cursor = self.__connection.makecursor (cmd)

			try:
				for (name, ftype, null, key, default, extra) in cursor.fetchall ():
					nativetype = ftype.replace (')', '').split ('(')
					properties = {'id'        : "%s.%s" % (tablename, name),
						'name'      : name,
						'nativetype': ftype,
						'nullable'  : null == 'YES',
						'type'      : 'string'}

					if nativetype [0] in self.__TYPEMAP:
						(group, properties ['type']) = self.__TYPEMAP [nativetype [0]]
					else:
						group = 'string'

					if len (nativetype) == 2:
						parts = []
						for item in nativetype [1].split (','):
							parts.extend (item.split ())

						if parts [0].strip ().isdigit ():
							properties ['length'] = int (parts [0].strip ())

						if len (parts) > 1 and parts [1].strip ().isdigit ():
							properties ['precision'] = int (parts [1].strip ())

					if default not in ('NULL', '0000-00-00 00:00:00', '', None):
						properties ['defaultwith'] = 'constant'
						properties ['default']     = default

					if extra == 'auto_increment':
						properties ['defaultwith'] = 'serial'

					elif nativetype [0] == 'timestamp':
						properties ['defaultwith'] = 'timestamp'

					result [properties ['id']] = GSchema.GSField (fields, **properties)

			finally:
				cursor.close ()

		return result


	# ---------------------------------------------------------------------------
	# Read all indices per table given
	# ---------------------------------------------------------------------------

	def __readIndices (self, tables):

		for (tablename, table) in tables.items ():
			indices = {}
			cursor  = self.__connection.makecursor (u"SHOW INDEX FROM %s" % tablename)

			try:
				for rs in cursor.fetchall ():
					(nonUnique, name, seq, column) = rs [1:5]

					index = indices.setdefault (name, [])
					index.append ((seq, column, nonUnique))

			finally:
				cursor.close ()

			for (name, parts) in indices.items ():
				parts.sort ()

				if name == 'PRIMARY':
					fClass = GSchema.GSPKField
					index = table.findChildOfType ('GSPrimaryKey')
					if index is None:
						index = GSchema.GSPrimaryKey (table, name = "pk_%s" % table.name)
				else:
					fClass = GSchema.GSIndexField
					parent = table.findChildOfType ('GSIndexes')
					if parent is None:
						parent = GSchema.GSIndexes (table)

					index = GSchema.GSIndex (parent, name = name,
						unique = not parts [0][2])

				for (seq, column, nonUnique) in parts:
					fClass (index, name = column)


	# ---------------------------------------------------------------------------
	# Handle special defaults
	# ---------------------------------------------------------------------------

	def _defaultwith_ (self, code, field):
		"""
		This function adds 'auto_increment' for 'serials' and checks for the proper
		fieldtype on 'timestamps'

		@param code: code-tuple to merge the result in
		@param field: GSField instance to process the default for
		"""

		if field.defaultwith == 'serial':
			code [1] [-1] += " AUTO_INCREMENT"

		elif field.defaultwith == 'timestamp':
			if field.type != 'timestamp':
				field.type = 'timestamp'

				code [1].pop ()
				code [1].append ("%s timestamp" % field.name)

				print u_("WARNING: changing column type of '%(table)s.%(column)s' "
					"to 'timestamp'") \
					% {'table': field.findParentOfType ('GSTable').name,
					'column': field.name}


	# ---------------------------------------------------------------------------
	# Drop an old index
	# ---------------------------------------------------------------------------

	def _dropIndex_ (self, index):
		"""
		Drop the given index

		@param index: name of the table to drop an index from
		"""

		table = index.findParentOfType ('GSTable')
		return [u"DROP INDEX %s ON %s" % (index.name, table.name)]


	# ---------------------------------------------------------------------------
	# Translate a string into an apropriate native type
	# ---------------------------------------------------------------------------

	def string (self, field):
		"""
		Return the native type for a string. If the length is given and below 255
		character the result is a varchar, otherwist text.

		@param field: GSField instance to get a native datatype for
		@return: string with the native datatype
		"""

		if hasattr (field, 'length') and field.length <= 255:
			return "varchar (%s)" % field.length
		else:
			return "text"


	# ---------------------------------------------------------------------------
	# MySQL has a timestamp, which is needed for 'defaultwith timestamp'
	# ---------------------------------------------------------------------------

	def timestamp (self, field):
		"""
		In MySQL timestamps are used for default values, otherwise we map to
		'datetime'

		@param field: GSField instance to get a native datatype for
		@return: string with the native datatype
		"""

		if hasattr (field, 'defaultwith') and field.defaultwith == 'timestamp':
			return "timestamp"
		else:
			return "datetime"
