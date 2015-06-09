# GNU Enterprise Common Library - Schema support for MaxDB/SAP-DB
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
Schema support plugin for MaxDB/SAP-DB backends.
"""

__all__ = ['Behavior']

from gnue.common.apps import errors
from gnue.common.datasources import GLoginHandler, GSchema
from gnue.common.datasources.drivers import DBSIG2


# =============================================================================
# Behavior class
# =============================================================================

class Behavior (DBSIG2.Behavior):
	"""
	Behavior class for MaxDB/SAP-DB backends.

	Limitations:
	  - MaxDB has no named primary keys, so we build them from "pk_<tablename>"
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connection):

		DBSIG2.Behavior.__init__ (self, connection)

		self.__RELKIND   = {'TABLE'  : {'type': 'table'  , 'name': u_('Tables')},
			'VIEW'   : {'type': 'view'   , 'name': u_('Views')},
		# 'SYNONYM': {'type': 'synonym', 'name': u_('Synonyms')},
		# 'RESULT' : {'type': 'result' ,
		#             'name': u_('Result Table')}
		}
		self.__maxVarchar = 3999

		self._maxIdLength_ = 32
		self._numbers_     = [[(5, 'SMALLINT'), (10, 'INTEGER')],
			"FIXED (%s)",
			"FIXED (%(length)s,%(scale)s)"]

		self._type2native_.update ({'boolean' : 'BOOLEAN',
				'datetime': 'TIMESTAMP'})


	# ---------------------------------------------------------------------------
	# Create a new database instance
	# ---------------------------------------------------------------------------

	def _createDatabase_ (self):
		"""
		Create a new database instance as defined by the connection's parameters.
		The user will be asked for a username and password who is member of the
		SDBA group on the backend system and theirfore allowed to create new
		instances. If the database already exists no action takes place.
		"""

		# Import here so epydoc can import this module even if sapdb is not
		# installed
		import sapdb.dbm

		host     = self.__connection.parameters.get ('host', 'localhost')
		dbname   = self.__connection.parameters.get ('dbname', None)
		username = self.__connection.parameters.get ('username', 'gnue')
		password = self.__connection.parameters.get ('password', 'gnue')

		title  = u_("OS User for host %s") % host
		fields = [(u_("User Name"), '_username', 'string', None, None, []),
			(u_("Password"), '_password', 'password', None, None, [])]
		res    = GLoginHandler.BasicLoginHandler ().askLogin (title, fields, {})

		try:
			session = sapdb.dbm.DBM (host, '', '',
				"%s,%s" % (res ['_username'], res ['_password']))

		except sapdb.dbm.CommunicationError, err:
			raise errors.AdminError, \
				u_("Unable to establish session: %s") % errors.getException () [2]

		try:
			result = session.cmd ('db_enum')

			for entry in result.split ('\n'):
				if entry.split ('\t') [0] == dbname.upper ():
					return

			print o(u_("Creating database instance %s") % dbname)
			session.cmd ("db_create %s %s,%s" % (dbname, res ['_username'],
					res ['_password']))

			print o(u_("Setting up parameters ..."))
			session.cmd ("param_startsession")
			session.cmd ("param_init OLTP")
			session.cmd ("param_put MAXUSERTASKS 10")
			session.cmd ("param_put CACHE_SIZE 20000")
			session.cmd ("param_put _UNICODE YES")
			session.cmd ("param_checkall")
			session.cmd ("param_commitsession")

			print o(u_("Adding log- and data-volumes ..."))
			session.cmd ("param_adddevspace 1 LOG  LOG_001 F 1000")
			session.cmd ("param_adddevspace 1 DATA DAT_001 F 2500")

			print o(u_("Entering administration mode"))
			session.cmd ("db_admin")

			print o(u_("Activating instance with initial user %s") % (username))
			session.cmd ("db_activate %s,%s" % (username, password))

			print o(u_("Loading system tables ..."))
			session.cmd ("load_systab -ud domp")

			print o(u_("Database instance created."))

		finally:
			session.release ()


	# ---------------------------------------------------------------------------
	# Read the current connection's schema
	# ---------------------------------------------------------------------------

	def _readSchema_ (self, parent):
		"""
		Read the connection's schema and build a GSchema object tree connected to
		the given parent object (which is of type GSSchema).
		"""

		tables = self.__readTables (parent)
		self.__readFields (tables)
		self.__readIndices (tables)
		self.__readConstraints (tables)


	# ---------------------------------------------------------------------------
	# Read all relations of the types listed in __RELKIND
	# ---------------------------------------------------------------------------

	def __readTables (self, parent):

		result  = {}
		masters = {}

		cmd = u"SELECT tableid, tablename, tabletype, owner FROM DOMAIN.TABLES " \
			"WHERE TYPE <> 'SYSTEM' ORDER BY tablename"

		cursor = self.__connection.makecursor (cmd)
		try:
			for (relid, name, kind, owner) in cursor.fetchall ():
				if not kind in self.__RELKIND:
					continue
				if not kind in masters:
					masters [kind] = GSchema.GSTables (parent, **self.__RELKIND [kind])

				attrs = {'id'   : relid,
					'name' : name,
					'type' : kind,
					'owner': owner}
				result [name] = GSchema.GSTable (masters [kind], **attrs)

		finally:
			cursor.close ()

		return result


	# ---------------------------------------------------------------------------
	# Read all fields for the given tables
	# ---------------------------------------------------------------------------

	def __readFields (self, tables):

		cmd = u'SELECT tablename, columnname, mode, datatype, len, dec, ' \
			'  nullable, "DEFAULT", "DEFAULTFUNCTION", pos, keypos ' \
			'FROM DOMAIN.COLUMNS ' \
			'ORDER BY tablename, pos'

		result = {}
		cursor = self.__connection.makecursor (cmd)

		try:
			for rs in cursor.fetchall ():
				(tname, cname, mode, nativetype, length, decimal, nullable,
					default, defaultfunc, pos, keypos) = rs

				table = tables.get (tname)
				if table is None:
					continue

				attrs = {'id'        : "%s.%s" % (tname, cname),
					'name'      : cname,
					'nativetype': nativetype,
					'nullable'  : nullable == 'YES',
					'pos'       : pos,
					'keypos'    : keypos}

				if nativetype in ['DATE', 'TIME', 'TIMESTAMP']:
					attrs ['type'] = nativetype == 'TIMESTAMP' and 'datetime' or \
						nativetype.lower ()

				elif nativetype in ['FIXED', 'FLOAT', 'INTEGER', 'SMALLINT']:
					attrs ['type']   = 'number'
					attrs ['length'] = length

					if nativetype == 'FIXED':
						attrs ['precision'] = decimal

				elif nativetype in ['BOOLEAN']:
					attrs ['type'] = 'boolean'

				else:
					attrs ['type']   = 'string'
					attrs ['length'] = length

				if default is not None:
					attrs ['defaultwith'] = 'constant'
					attrs ['default']     = default

				elif defaultfunc is not None:
					if defaultfunc in ['DATE', 'TIME', 'TIMESTAMP']:
						dkind = 'timestamp'
					else:
						dkind = 'constant'
					attrs ['defaultwith'] = dkind
					attrs ['defaultval']  = defaultfunc

				parent = table.findChildOfType ('GSFields') or GSchema.GSFields (table)
				result [attrs ['id']] = GSchema.GSField (parent, **attrs)

		finally:
			cursor.close ()

		# Finally iterate over all tables added and build up their primary keys
		for table in tables.values ():
			fields = [(f.keypos, f.name) for f in \
					table.findChildrenOfType ('GSField', False, True) \
					if f.keypos is not None]
			if fields:
				fields.sort ()
				pk = GSchema.GSPrimaryKey (table, name = "pk_%s" % table.name)
				for (p, name) in fields:
					GSchema.GSPKField (pk, name = name)

		return result


	# ---------------------------------------------------------------------------
	# Read all indices defined for the given tables
	# ---------------------------------------------------------------------------

	def __readIndices (self, tables):

		cmd = u"SELECT tablename, indexname, columnname, type " \
			"FROM DOMAIN.INDEXCOLUMNS " \
			"WHERE disabled = 'NO' " \
			"ORDER BY tablename, indexname, columnno"

		cursor = self.__connection.makecursor (cmd)
		try:
			for (tname, iname, cname, itype) in cursor.fetchall ():
				#print "TN:", tname, "IN:", iname, "CN:", cname, "IT:", itype
				table = tables.get (tname)
				if table is None:
					continue

				indices = table.findChildOfType ('GSIndexes') or \
					GSchema.GSIndexes (table)

				index = None
				for ix in indices.findChildrenOfType ('GSIndex', False, True):
					if ix.name == iname:
						index = ix
						break

				if index is None:
					index = GSchema.GSIndex (indices, name = iname,
						unique = itype == 'UNIQUE')
				GSchema.GSIndexField (index, name = cname)

		finally:
			cursor.close ()


	# ---------------------------------------------------------------------------
	# Read all referential constraints for the tables given
	# ---------------------------------------------------------------------------

	def __readConstraints (self, tables):

		cmd = u"SELECT tablename, columnname, fkeyname, reftablename, " \
			"  refcolumnname " \
			"FROM DOMAIN.FOREIGNKEYCOLUMNS " \
			"ORDER BY tablename, fkeyname"

		cursor = self.__connection.makecursor (cmd)

		try:
			for (tname, cname, fkname, reftable, refcol) in cursor.fetchall ():
				table = tables.get (tname)
				if table is None:
					continue

				master = table.findChildOfType ('GSConstraints') or \
					GSchema.GSConstraints (table)
				cs = None
				for item in master.findChildrenOfType ('GSForeignKey', False, True):
					if item.name == fkname:
						cs = item
						break

				if cs is None:
					cs = GSchema.GSForeignKey (master, name = fkname,
						references = reftable)

				GSchema.GSFKField (cs, name = cname, references = refcol)

		finally:
			cursor.close ()


	# ---------------------------------------------------------------------------
	# Handle special defaults
	# ---------------------------------------------------------------------------

	def _defaultwith_ (self, code, field):
		"""
		Handle special defaults like 'serial' and 'timestamp'.

		@param code: code-triple to merge the result in
		@param field: GSField instance with the default definition
		"""

		if field.defaultwith == 'serial':
			field.default = 'DEFAULT SERIAL'

		elif field.defaultwith == 'timestamp':
			field.default = 'DEFAULT TIMESTAMP'


	# ---------------------------------------------------------------------------
	# Get an apropriate type for strings
	# ---------------------------------------------------------------------------

	def string (self, field):
		"""
		Return the native datatype for string fields

		@param field: GSField instance to get a native datatype for
		@return: 'VARCHAR (?)' or 'LONG'
		"""

		length = hasattr (field, 'length') and field.length or self.__maxVarchar

		if length <= self.__maxVarchar:
			return "VARCHAR (%d)" % length

		else:
			return "LONG"
