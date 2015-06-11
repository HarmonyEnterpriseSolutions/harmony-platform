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
# $Id: pyodbcdrv.py,v 1.11 2013/04/01 12:43:49 oleg Exp $

"""
Database driver plugin for PostgreSQL backends using the psycopg2 DBSIG2 module.
"""
from src.gnue.common.datasources.drivers.sql.mssql_fn import FnSignatureFactory, ResultSet

__all__ = ['Connection']

from gnue.common.datasources import Exceptions
import decimal
import datetime

# =============================================================================
# Driver info
# =============================================================================

class DriverInfo(DriverInfo):
	name = "mssql_fn"

# =============================================================================
# Connection class
# =============================================================================

class Connection(BaseConnection):
	"""
	PostgreSQL with stored procedures backend
	"""
	_resultSetClass_ = ResultSet

	def getFnSignatureFactory(self):
		if not hasattr(self, '_fnSignatureFactory'):
			self._fnSignatureFactory = FnSignatureFactory(self._getNativeConnection()['connection'], self._encoding)
		return self._fnSignatureFactory
	
	def _update_ (self, table, oldfields, newfields):
		fields = oldfields.copy()
		fields.update(newfields)

		statement, parameters = self.getFnSignatureFactory()[table]['edit'].genSql(fields)
		self.sql0(statement, parameters)

	def _insert_ (self, table, newfields):
		"""
		Every insert function must return curval
		"""
		sql, parameters = self.getFnSignatureFactory()[table]['ins'].genSql(newfields)
		cursor = self.makecursor(sql, parameters)
		rows = cursor.fetchall()
		cursor.close()
		assert len(rows) == 1 and len(rows[0]) == 1, "_ins function for %s must return one row with single value (primary key id)"
		id = rows[0][0]
		if id == '':
			id = None
		return id

	def _delete_ (self, table, oldfields):
		statement, parameters = self.getFnSignatureFactory()[table]['del'].genSql(oldfields)
		self.sql0(statement, parameters)

	def _requery_ (self, table, oldfields, fields, parameters):
		"""
		"""
		if set(fields).issubset(oldfields.keys()):
			# bypass primary key requery
			return oldfields
		else:
			if parameters:
				# if oldfields has some field from signature and parameters has no such value
				# this old field will be passed to signature
				oldfields = oldfields.copy()
				oldfields.update(parameters)

			sql, parameters = self.getFnSignatureFactory()[table]['list'].genSql(oldfields)
			cursor = self.makecursor(sql, parameters)
			rows = cursor.fetchall()

			# ignore fields passed in, because can't rule fields order
			fields = [i[0] for i in cursor.description]
			
			cursor.close()
			
			if rows:
				assert len(rows) == 1, "requery returned more than one rows. Does %s accepting primary key?" % table
				row = rows[0]
				result = {}
				for i, field in enumerate(fields):
					value = row[i]
					if isinstance(value, str):
						value = value.decode(self._encoding)
					result[field] = value
				return result
			else:
				raise Exceptions.RecordNotFoundError

	def make_parameter(self, value):
		"""
		overrided DBSIG2 Connection.make_parameter
		"""

		# Cant find out why decimal does not work here
		# harmonylib/test/dbapi/test_pyodbc_decimal_insert.py works ok but here same code does not work:
		# DataError: ('22018', '[22018] [Microsoft][ODBC SQL Server Driver]Invalid character value for cast specification (0) (SQLExecDirectW)').
		if isinstance(value, decimal.Decimal):
			value = str(value)
		# under ubuntu pyodbc returns sql decimal type as float, http://stackoverflow.com/questions/3371795/freetds-translating-ms-sql-money-type-to-python-float-not-decimal
		# if passing float as parameter, have strange error on ubuntu
		# ConnectionError: ProgrammingError: ('42000', "[42000] [FreeTDS][SQL Server]Must pass parameter number 6 and subsequent parameters as '@name = value'. After the form '@name = value' has been used, all subsequent parameters must be passed in the form '@name = value'. (119) (SQLExecDirectW)")
		# hovever, can't reproduce it in the minimal script harmonylib/test/dbapi/test_pyodbc_paramater_6.py
		elif isinstance(value, float):
			value = repr(value)
			# SCOPE_IDENTITY() returns Decimal for _ins functions, have  error since value converted to str before row requery
			if value.endswith('.0'):
				value = value[:-2]
		# when sending datetime, have
		# Error: ('HYC00', '[HYC00] [Microsoft][ODBC SQL Server Driver]Optional feature not implemented (0) (SQLBindParameter)')
		elif isinstance(value, datetime.datetime):
			value = value.strftime('%Y%m%d %H:%M:%S')
		elif isinstance(value, datetime.date):
			value = value.strftime('%Y%m%d')
		elif isinstance(value, datetime.time):
			value = value.strftime('%H:%M:%S')
		else:
			value = super(Connection, self).make_parameter(value)

		return value
