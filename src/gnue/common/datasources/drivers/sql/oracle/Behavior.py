# GNU Enterprise Common Library - Schema support for Oracle
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
# $Id: Behavior.py 9453 2007-03-29 17:36:19Z johannes $

"""
Schema support plugin for Oracle backends.
"""

from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers import DBSIG2

# =============================================================================
# Behavior class
# =============================================================================

class Behavior (DBSIG2.Behavior):
	"""
	Behavior class for Oracle backends.

	Limitations:
	  - does not detect primary keys, indices and constraints
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, *args, **kwargs):

		DBSIG2.Behavior.__init__ (self, *args, **kwargs)

		self.__RELKIND = {
			'user_table'  : {'type': 'usertable',   'name': u_("User Tables")},
			'user_view'   : {'type': 'userview',    'name': u_("User Views")},
			'user_synonym': {'type': 'usersynonym', 'name': u_("User Synonyms")},
			'all_table'   : {'type': 'alltable',    'name': u_('System Tables')},
			'all_view'    : {'type': 'allview',     'name': u_('System Views')},
			'all_synonym' : {'type': 'allsynonym',  'name': u_('System Synonyms')}}
		self.__pkPrecision = 10

		self._maxIdLength_   = 31
		self._alterMultiple_ = False
		self._numbers_       = [[], "number (%s)", "number (%(length)s,%(scale)s)"]

		self._type2native_.update ({'datetime': 'date', 'time': 'date'})


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


	# ---------------------------------------------------------------------------
	# Read all relations available
	# ---------------------------------------------------------------------------

	def __readTables (self, parent):

		masters = {}
		result  = {}

		where_type = self.__RELKIND.keys()

		# TODO: exclude system tables to increase performance
		cmd = \
			"select owner||'.'||table_name||'.'||table_type full_name, \n" + \
			"  decode(owner,user,null,owner||'.')||table_name table_name, \n" + \
			"  decode(owner,user,'user_','all_')||lower(table_type) table_type \n" + \
			"  from all_catalog \n" + \
			"  where decode(owner,user,'user_','all_')||lower(table_type) in ('%s') \n" \
			% ','.join(where_type) + \
			"  order by table_name "

		cursor = self.__connection.makecursor (cmd)
		try:
			for (fullname, name, kind) in cursor.fetchall ():
				if not kind in masters:
					masters [kind] = GSchema.GSTables (parent, **self.__RELKIND [kind])

				properties = {'id': fullname, 'name': name.lower (), 'kind': kind}
				result [fullname] = GSchema.GSTable (masters [kind], **properties)

		finally:
			cursor.close ()

		return result


	# ---------------------------------------------------------------------------
	# Read fields
	# ---------------------------------------------------------------------------

	def __readFields (self, tables):

		for (key, table) in tables.items ():

			(owner, name, type) = key.split ('.')

			if type == 'SYNONYM':
				cmd = "select table_owner, table_name, " + \
					"decode(db_link,null,'','@'||db_link) name " + \
					"from all_synonyms " + \
					"where owner = '%s' and synonym_name='%s'" % (owner, name)

				cursor = self.__connection.makecursor (cmd)
				try:
					(owner, name, link) = cursor.fetchone ()
					if link is None:
						link = ""

				finally:
					cursor.close()
			else:
				link = ""

			cmd = "SELECT owner||'.'||table_name||'.'||column_name||'.%s', " \
				"  column_name, data_type, nullable, data_length, data_scale, " \
				"  data_precision "  \
				"FROM all_tab_columns%s " \
				"WHERE owner = '%s' AND table_name = '%s' " \
				"ORDER BY column_id" % (link, link, owner, name)

			cursor = self.__connection.makecursor (cmd)

			try:
				for rs in cursor.fetchall ():
					(fullname, name, nativetype, nullable, length, scale, prec) = rs

					attrs = {'id'        : fullname,
						'name'      : name.lower (),
						'nativetype': nativetype,
						'nullable'  : nullable != 'N'}

					if nativetype == 'NUMBER':
						attrs ['precision'] = int (scale or 0)
						attrs ['type']      = 'number'
						attrs ['length']    = int (prec or 38)
					# 38 is the default decimal precision according to
					# Oracle(c) Database SQL Reference 10g Release 2 (10.2)

					elif nativetype == 'DATE':
						attrs ['type'] = 'date'

					else:
						attrs ['type'] = 'string'
						if int (length):
							attrs ['length'] = int (length)

					parent = table.findChildOfType ('GSFields') or GSchema.GSFields (table)
					GSchema.GSField (parent, **attrs)

			finally:
				cursor.close ()


	# ---------------------------------------------------------------------------
	# Create a new database
	# ---------------------------------------------------------------------------

	def _createDatabase_ (self):
		"""
		There's no support for creating databases atm, so a NotImplementedError
		will be raised.
		"""

		raise NotImplementedError


	# ---------------------------------------------------------------------------
	# Handle sepcial defaults
	# ---------------------------------------------------------------------------

	def _defaultwith_ (self, code, field):
		"""
		Creates a sequence for 'serials' and set the default for 'timestamps' to
		'now ()'

		@param code: code-triple to get the result
		@param field: GSField instance of the field having the default
		"""

		tablename = field.findParentOfType ('GSTable').name
		if field.defaultwith == 'serial':
			seq = self._getSequenceName (field)
			code [0].append (u"CREATE SEQUENCE %s MAXVALUE %s NOCYCLE" \
					% (seq, "9" * self.__pkPrecision))

			body = u"IF :new.%(field)s IS NULL THEN" \
				" SELECT %(seq)s.nextval INTO :new.%(field)s FROM dual;" \
				"END IF;" \
				% {'field': field.name, 'seq': seq}

			self.__addTrigger (tablename, field.name, code, body)


		elif field.defaultwith == 'timestamp':
			if field.type == 'date':
				sysdate = "TRUNC (sysdate)"
			else:
				sysdate = "sysdate"

			body = u"IF :new.%(field)s IS NULL THEN" \
				" :new.%(field)s := %(date)s;" \
				"END IF;" \
				% {'field': field.name,
				'date' : sysdate}

			self.__addTrigger (tablename, field.name, code, body)


	# ---------------------------------------------------------------------------
	# Create a trigger code and add it to the epilogue of the given code
	# ---------------------------------------------------------------------------

	def __addTrigger (self, tablename, fieldname, code, body):

		code [2].append (u"CREATE OR REPLACE TRIGGER t__%(table)s_%(field)s_pre"
			"  BEFORE INSERT ON %(table)s"
			"  FOR EACH ROW WHEN (new.%(field)s IS NULL)"
			"  BEGIN %(body)s END; /"
			% {'table': tablename,
				'field': fieldname,
				'body': body})


	# ---------------------------------------------------------------------------
	# String becomes varchar2
	# ---------------------------------------------------------------------------

	def string (self, field):
		"""
		Return the native type for a string-field.

		@param field: GSField instance to get a native type for
		@return: string with the native datatype
		"""

		length = hasattr (field, 'length') and field.length or 99999
		if length <= 2000:
			return "varchar2 (%s)" % length
		else:
			return "blob"


	# ---------------------------------------------------------------------------
	# There's no native boolean type
	# ---------------------------------------------------------------------------

	def boolean (self, field):
		"""
		Return a native data type for a boolean

		@param field: GSField instance to get a native type for
		@return: string with the native datatype
		"""

		nullable = hasattr (field, 'nullable') and field.nullable or True

		if nullable:
			return "number (1) CHECK (%(field)s IS NULL OR %(field)s IN (0,1))" \
				% {'field': field.name}
		else:
			return "number (1) CHECK (%s IN (0,1))" % field.name
