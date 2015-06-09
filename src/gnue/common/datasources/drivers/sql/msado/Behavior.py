# GNU Enterprise Common Library - Schema support for MS-ADO
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
Schema support plugin for MS-ADO backends.
"""

__all__ = ['Behavior']

from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers import Base


# =============================================================================
# Behavior class
# =============================================================================

class Behavior (Base.Behavior):
	"""
	Behavior class for MS-ADO backends.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connection):

		Base.Behavior.__init__ (self, connection)

		self.__RELKIND = {'TABLE': {'type': 'table', 'name': u_('Tables')},
			'VIEW' : {'type': 'view', 'name': u_('Views')}}


	# ---------------------------------------------------------------------------
	# Read the current connection's schema
	# ---------------------------------------------------------------------------

	def _readSchema_ (self, parent):

		self._TYPEMAP = self.__buildTypeMap ()
		tables = self.__readTables (parent)
		self.__readFields (tables)
		self.__readPrimaryKeys (tables)


	# ---------------------------------------------------------------------------
	# Read all tables and views
	# ---------------------------------------------------------------------------

	def __readTables (self, parent):

		result  = {}
		masters = {}

		rs = self.__connection._native.adoConn.OpenSchema (20)

		for rec in self.__iterateRS (rs):
			(name, rtype) = [rec.get (i) for i in ['TABLE_NAME', 'TABLE_TYPE']]

			if not rtype in self.__RELKIND:
				continue

			if not rtype in masters:
				masters [rtype] = GSchema.GSTables (parent, **self.__RELKIND [rtype])

			result [name] = GSchema.GSTable (masters [rtype], name = name)

		return result


	# ---------------------------------------------------------------------------
	# Read all fields for the given tables
	# ---------------------------------------------------------------------------

	def __readFields (self, tables):

		result = {}
		rs = self.__connection._native.adoConn.openSchema (4)

		for rec in self.__iterateRS (rs):
			table = tables.get (rec ['TABLE_NAME'])
			if table is None:
				continue

			(group, datatype) = self._TYPEMAP.get (rec ['DATA_TYPE'],
				self._TYPEMAP ['string'])

			parent = table.findChildOfType ('GSFields') or GSchema.GSFields (table)
			attrs = {'id': '%s.%s' % (table.name, rec ['COLUMN_NAME']),
				'name': rec ['COLUMN_NAME'],
				'nativetype': rec ['DATA_TYPE'],
				'nullable': rec ['IS_NULLABLE'],
				'type': datatype}

			if group == 'string':
				attrs ['length'] = int (rec ['CHARACTER_MAXIMUM_LENGTH'] or 0)

			elif group == 'number':
				attrs ['length'] = rec ['NUMERIC_PRECISION']
				if attrs ['nativetype'] == self.__connection._driver.adCurrency:
					attrs ['precision'] = 4
				else:
					attrs ['precision'] = rec ['NUMERIC_SCALE']

			result [attrs ['id']] = GSchema.GSField (parent, **attrs)

		return result


	# ---------------------------------------------------------------------------
	# Read all primary keys for the given tables
	# ---------------------------------------------------------------------------

	def __readPrimaryKeys (self, tables):

		keys = {}

		rs = self.__connection._native.adoConn.OpenSchema (28)
		for rec in self.__iterateRS (rs):
			table = tables.get (rec ['TABLE_NAME'])
			if table is None:
				continue

			entry = keys.setdefault (table.name, {})
			entry ['name'] = rec.get ('PK_NAME') or 'pk_%s' % table.name
			fields = entry.setdefault ('fields', [])
			fields.append ((rec ['ORDINAL'], rec ['COLUMN_NAME']))

		for (tname, keydef) in keys.items ():
			table = tables [tname]
			pk = GSchema.GSPrimaryKey (table, name = keydef ['name'])
			fields = keydef ['fields']
			fields.sort ()

			for (ix, name) in fields:
				GSchema.GSPKField (pk, name = name)


	# ---------------------------------------------------------------------------
	# Iterate over a ResultSet and return every record as dictionary
	# ---------------------------------------------------------------------------

	def __iterateRS (self, rs):

		if rs.BOF or rs.EOF:
			return

		rs.MoveFirst ()

		while not rs.EOF:
			fld = rs.Fields
			yield dict ([(fld (i).Name, fld (i).Value) for i in range (fld.Count)])

			rs.MoveNext ()


	# ---------------------------------------------------------------------------
	# Build a mapping for the supported datatypes
	# ---------------------------------------------------------------------------

	def __buildTypeMap (self):

		dbm = self.__connection._driver
		result = {'string': ('string', 'string'),
			dbm.adBoolean: ('booelan', 'boolean'),
			dbm.adDBTime: ('date', 'time')}

		for item in [dbm.adBigInt, dbm.adChapter, dbm.adCurrency, dbm.adDecimal,
			dbm.adDouble, dbm.adInteger, dbm.adNumeric, dbm.adSingle,
			dbm.adSmallInt, dbm.adTinyInt, dbm.adUnsignedBigInt,
			dbm.adUnsignedInt, dbm.adUnsignedSmallInt,
			dbm.adUnsignedTinyInt, dbm.adVarNumeric]:
			result [item] = ('number', 'number')

		for item in [dbm.adDBDate, dbm.adDate]:
			result [item] = ('date', 'date')

		for item in [dbm.adDBTimeStamp, dbm.adFileTime]:
			result [item] = ('date', 'datetime'),

		return result
