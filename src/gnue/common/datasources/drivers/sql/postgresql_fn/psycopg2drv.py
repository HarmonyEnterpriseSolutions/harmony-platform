# GNU Enterprise Common Library - PostgreSQL database driver using psycopg
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
# $Id: psycopg2drv.py,v 1.7 2011/11/10 16:34:34 oleg Exp $

"""
Database driver plugin for PostgreSQL backends using the psycopg2 DBSIG2 module.
"""
from src.gnue.common.datasources.drivers.sql.postgresql_fn import FnSignatureFactory, ResultSet

__all__ = ['Connection']

# =============================================================================
# Driver info
# =============================================================================

class DriverInfo(DriverInfo):
	name = "postgresql_fn"

# =============================================================================
# Connection class
# =============================================================================

class Connection(Connection):
	"""
	PostgreSQL with stored procedures backend
	"""

	_resultSetClass_ = ResultSet

	def _getSessionKey(self):
		return self.manager._getSessionKey()

	def getFnSignatureFactory(self):
		return FnSignatureFactory.getInstance(self.manager._location)

	def _update_ (self, table, oldfields, newfields):
		fs = oldfields.copy()
		fs.update(newfields)
		statement, parameters = self.getFnSignatureFactory()[table]['update'].genSql(fs, self._getSessionKey())
		self.sql0("SELECT " + statement, parameters)

	def _insert_ (self, table, newfields):
		"""
		Every insert function must return curval
		"""
		statement, parameters = self.getFnSignatureFactory()[table]['insert'].genSql(newfields, self._getSessionKey())
		id = self.sql1("SELECT " + statement, parameters)
		if id == '':
			id = None
		return id

	def _delete_ (self, table, oldfields):
		statement, parameters = self.getFnSignatureFactory()[table]['delete'].genSql(oldfields, sessionKey = self._getSessionKey())
		self.sql0("SELECT " + statement, parameters)

	def _requery_ (self, table, oldfields, fields, parameters):
		"""
		"""
		if set(fields).issubset(oldfields.keys()):
			# bypass primary key requery
			return oldfields
		else:
			fs = oldfields.copy()
			if parameters:
				fs.update(parameters)

			# if oldfields has some field from signature and parameters has no such value
			# this old field will be passed to signature
			sql, params = self.getFnSignatureFactory()[table]['select'].genSql(fs, self._getSessionKey())

			return super(Connection, self)._requery_(sql, oldfields, fields, params)

	def _getNativeConnectionContext(self):
		return { 'session_key' : self.manager._getSessionKey() }
