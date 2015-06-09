# GNU Enterprise Common Library - Schema support for PostgreSQL
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
Schema support plugin for PostgreSQL backends.
"""

__all__ = ['Behavior']

import os

from gnue.common.apps import errors
from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers import DBSIG2


# =============================================================================
# Behavior class
# =============================================================================

class Behavior (DBSIG2.Behavior):
	"""
	Behavior class for PostgreSQL backends.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, *args, **kwargs):

		DBSIG2.Behavior.__init__ (self, *args, **kwargs)

		self.__RELKIND = {'v': {'type': 'view',  'name': u_("Views")},
			'r': {'type': 'table', 'name': u_("Tables")}}

		# Build  typemap: {nativetype: (group, fieldtype)}
		self.__TYPEMAP = {'date'  : ('date', 'date'),
			'bool'  : ('boolean', 'boolean'),
			'string': ('string', 'string')}

		for item in ['numeric', 'float4', 'float8', 'money', 'int8',
			'int2', 'int4', 'serial']:
			self.__TYPEMAP [item] = ('number', 'number')

		for item in ['time', 'reltime']:
			self.__TYPEMAP [item] = ('date', 'time')

		for item in ['timestamp', 'abstime']:
			self.__TYPEMAP [item] = ('date', 'datetime')

		self._maxIdLength_   = 31
		self._alterMultiple_ = False
		self._numbers_       = [[(4, 'smallint'), (9, 'integer'), (18, 'bigint')],
			"numeric (%s,0)", "numeric (%(length)s,%(scale)s)"]

		self._type2native_.update ({'boolean' : 'boolean',
				'datetime': 'timestamp without time zone'})


	# ---------------------------------------------------------------------------
	# Create a new database
	# ---------------------------------------------------------------------------

	def _createDatabase_ (self):
		"""
		Create the requested user and database using the tools 'createuser',
		'createdb' and 'dropuser'. Of course this function should better make use
		of the template1 database using a connection object.
		"""

		dbname   = self.__connection.parameters.get ('dbname')
		username = self.__connection.parameters.get ('username', 'gnue')
		password = self.__connection.parameters.get ('password')
		host     = self.__connection.parameters.get ('host')
		port     = self.__connection.parameters.get ('port')
		owner    = self.__connection.parameters.get ('owner', username)
		ownerpwd = self.__connection.parameters.get ('ownerpwd')

		site = ""
		if host is not None:
			site += " --host=%s" % host
		if port is not None:
			site += " --port=%s" % port

		# First, let's connect to template1 using the given username and password
		self.__connection.parameters ['dbname'] = 'template1'
		self.__connection.manager.loginToConnection (self.__connection)

		# Then have a look wether the requested owner is already available
		result = self.__connection.sql ('SELECT usesysid FROM pg_user ' \
				'WHERE usename = %(owner)s', {'owner': owner})
		if not result:
			cmd = 'CREATE USER %s' % owner
			if ownerpwd:
				cmd += " WITH PASSWORD '%s'" % ownerpwd

			self.__connection.sql0 (cmd)
			self.__connection.commit ()

		# Now go and create that new database
		cmd = "ABORT; CREATE DATABASE %s WITH OWNER %s ENCODING = 'UNICODE'; BEGIN"
		self.__connection.sql0 (cmd % (dbname, owner))
		self.__connection.commit ()

		self.__connection.close ()

		# Since the newly created database should be available now, connect to it
		# using the given owner
		self.__connection.parameters ['dbname'] = dbname
		self.__connection.parameters ['username'] = owner

		if ownerpwd:
			self.__connection.parameters ['password'] = ownerpwd
		else:
			if 'password' in self.__connection.parameters:
				del self.__connection.parameters ['password']

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
		fields = self.__readFields (tables)
		self.__readDefaults (fields)
		self.__readKeys (tables)
		self.__readConstraints (tables, fields)


	# ---------------------------------------------------------------------------
	# Read all table-like elements
	# ---------------------------------------------------------------------------

	def __readTables (self, parent):

		mapping = {}    # Maps OIDs to GSTable instances
		tables  = None
		views   = None

		cmd = u"SELECT c.oid, c.relname, c.relkind " \
			"FROM pg_class c, pg_namespace n " \
			"WHERE n.nspname = 'public' AND n.oid = c.relnamespace AND " \
			"      c.relkind in (%s) " \
			"ORDER BY c.relname" \
			% ','.join (["%r" % kind for kind in self.__RELKIND.keys ()])

		cursor = self.__connection.makecursor (cmd)

		try:
			for (oid, relname, relkind) in cursor.fetchall ():

				kind = self.__RELKIND [relkind] ['type']
				properties = {'id': oid, 'name': relname, 'kind': kind}

				if relkind == 'v':
					if views is None:
						views = GSchema.GSTables (parent, **self.__RELKIND [relkind])
					master = views
				else:
					if tables is None:
						tables = GSchema.GSTables (parent, **self.__RELKIND [relkind])
					master = tables

				table = GSchema.GSTable (master, **properties)

				# Maintain a temporary mapping from OID's to GSTable instances so
				# adding fields afterwards runs faster
				mapping [oid] = table

		finally:
			cursor.close ()

		return mapping


	# ---------------------------------------------------------------------------
	# Find all fields
	# ---------------------------------------------------------------------------

	def __readFields (self, tables):

		cmd = u"SELECT attrelid, attname, t.typname, attnotnull, " \
			"       atthasdef, atttypmod, attnum, attlen " \
			"FROM pg_attribute a " \
			"LEFT OUTER JOIN pg_type t ON t.oid = a.atttypid " \
			"WHERE attnum >= 0 AND attisdropped = False " \
			"ORDER BY attrelid, attnum"

		cursor = self.__connection.makecursor (cmd)
		fields = None
		result = {}

		try:
			for rs in cursor.fetchall ():
				(relid, name, typename, notnull, hasdef, typemod, attnum, attlen) = rs

				# only process attributes from tables we've listed before
				if not relid in tables:
					continue

				attrs = {'id'        : "%s.%s" % (relid, attnum),
					'name'      : name,
					'nativetype': typename,
					'nullable'  : hasdef or not notnull}

				if typename.lower () in self.__TYPEMAP:
					(group, attrs ['type']) = self.__TYPEMAP [typename.lower ()]
				else:
					(group, attrs ['type']) = self.__TYPEMAP ['string']

				if group == 'number':
					if typemod != -1:
						value = typemod - 4
						attrs ['length']    = value >> 16
						attrs ['precision'] = value &  0xFFFF

					elif attlen > 0:
						attrs ['length'] = len ("%s" % 2L ** (attlen * 8))

				elif typemod != -1:
					attrs ['length'] = typemod - 4

				# Remove obsolete attributes
				if group in ['date', 'boolean']:
					for item in ['length', 'precision']:
						if item in attrs:
							del attrs [item]

				elif group in ['string']:
					if 'precision' in attrs:
						del attrs ['precision']

				table = tables [relid]
				fields = table.findChildOfType ('GSFields')
				if fields is None:
					fields = GSchema.GSFields (table)

				result [attrs ['id']] = GSchema.GSField (fields, **attrs)

		finally:
			cursor.close ()

		return result


	# ---------------------------------------------------------------------------
	# Read defaults and apply them to the given fields
	# ---------------------------------------------------------------------------

	def __readDefaults (self, fields):

		cmd = u"SELECT adrelid, adnum, adsrc FROM pg_attrdef ORDER BY adrelid"

		cursor = self.__connection.makecursor (cmd)

		try:
			for (relid, fieldnum, source) in cursor.fetchall ():
				field = fields.get ("%s.%s" % (relid, fieldnum))

				# Skip all defaults of not listed fields
				if field is None:
					continue

				if source [:8] == 'nextval(':
					field.defaultwith = 'serial'

				elif source == 'now()':
					field.defaultwith = 'timestamp'

				else:
					field.defaultwith = 'constant'
					field.default = source.split ('::') [0].strip ("'")

		finally:
			cursor.close ()


	# ---------------------------------------------------------------------------
	# Read all indices and associate them with their table/view
	# ---------------------------------------------------------------------------

	def __readKeys (self, tables):

		cmd = u"SELECT indrelid, indkey, indisunique, indisprimary, c.relname " \
			"FROM pg_index i LEFT OUTER JOIN pg_class c ON c.oid = indexrelid"

		cursor = self.__connection.makecursor (cmd)

		try:
			for (relid, fieldvec, isUnique, isPrimary, name) in cursor.fetchall ():

				# Skip functional indices. A functional index is an index that is built
				# upon a fuction manipulating a field upper(userid) vs userid
				fields = [int (i) - 1 for i in fieldvec.split ()]
				if not fields:
					continue

				# only process keys of listed tables
				table = tables.get (relid)
				if table is None:
					continue

				if isPrimary:
					index  = GSchema.GSPrimaryKey (table, name = name)
					fClass = GSchema.GSPKField
				else:
					indices = table.findChildOfType ('GSIndexes')
					if indices is None:
						indices = GSchema.GSIndexes (table)

					index  = GSchema.GSIndex (indices, unique = isUnique, name = name)
					fClass = GSchema.GSIndexField

				fieldList = table.findChildrenOfType ('GSField', False, True)
				for find in fields:
					fClass (index, name = fieldList [find].name)

		finally:
			cursor.close ()


	# ---------------------------------------------------------------------------
	# Read all constraints
	# ---------------------------------------------------------------------------

	def __readConstraints (self, tables, fields):

		cmd = u"SELECT conname, conrelid, confrelid, conkey, confkey, contype " \
			"FROM pg_constraint WHERE contype in ('f', 'u')"

		cursor = self.__connection.makecursor (cmd)
		try:
			for (name, relid, fkrel, key, fkey, ctype) in cursor.fetchall ():
				table   = tables.get (relid)

				if ctype == 'f':
					fktable = tables.get (fkrel)

					# We need both ends of a relation to be a valid constraint
					if table is None or fktable is None:
						continue

					parent = table.findChildOfType ('GSConstraints')
					if parent is None:
						parent = GSchema.GSConstraints (table)

					constr = GSchema.GSForeignKey (parent, name = name,
						references = fktable.name)

					kp  = isinstance (key, basestring) and key [1:-1].split (',') or key
					fkp = isinstance (fkey, basestring) and fkey [1:-1].split(',') or fkey

					k = [fields ["%s.%s" % (relid, i)].name for i in kp]
					f = [fields ["%s.%s" % (fkrel, i)].name for i in fkp]

					for (name, refname) in zip (k, f):
						GSchema.GSFKField (constr, name = name, references = refname)

				# Unique-Constraint
				elif ctype == 'u':
					parent = table.findChildOfType ('GSConstraints') or \
						GSchema.GSConstraints (table)
					constr = GSchema.GSUnique (parent, name = name)
					kp = isinstance (key, basestring) and key [1:-1].split (',') or key

					for name in [fields ["%s.%s" % (relid, i)].name for i in kp]:
						GSchema.GSUQField (constr, name = name)

					# Ok, since we know PostgreSQL automatically creates a unique index
					# of the same name, we drop that index since it would only confuse a
					# later diff
					for ix in table.findChildrenOfType ('GSIndex', False, True):
						if ix.name == constr.name:
							parent = ix.getParent ()
							parent._children.remove (ix)
							ix.setParent (None)

		finally:
			cursor.close ()


	# ---------------------------------------------------------------------------
	# Handle special defaults
	# ---------------------------------------------------------------------------

	def _defaultwith_ (self, code, field):
		"""
		Create a sequence for 'serials' and set the default for 'timestamps'.

		@param code: code-triple to get the result
		@param field: GSField instance of the field having the default
		"""

		if field.defaultwith == 'serial':
			seq = self._getSequenceName (field)
			code [0].append (u"CREATE SEQUENCE %s" % seq)
			field.default = "DEFAULT nextval ('%s')" % seq

		elif field.defaultwith == 'timestamp':
			field.default = "DEFAULT now()"
