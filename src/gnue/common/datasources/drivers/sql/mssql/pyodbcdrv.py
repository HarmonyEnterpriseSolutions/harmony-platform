# GNU Enterprise Common Library - MS-ADO database driver using adodbapi
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
# $Id: pyodbcdrv.py,v 1.6 2013/12/17 14:48:14 Oleg Exp $

"""
Database driver plugin for MS-SQL backends using the adodbapi DBSIG2 module.
"""
from src.gnue.common.datasources.drivers.sql.mssql import ErrorDecorators, Behavior

__all__ = ['Connection']

import time

from gnue.common.datasources.drivers import DBSIG2


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		import pyodbc
	except ImportError:
		raise GConnections.DependencyError, ('pyodbc', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo(object):
	name = "mssql"
	url = "http://pyodbc.sourceforge.net/"


# =============================================================================
# Connection class
# =============================================================================

class Connection (ErrorDecorators, DBSIG2.Connection):
	"""
	Connection class for MS SQL backends using the adodbapi DBSIG2 module.
	"""
	_drivername_      = 'pyodbc'
	_behavior_        = Behavior
	_must_fetchall_   = True
	_broken_rowcount_ = True
	_std_datetime_ = True

	# ---------------------------------------------------------------------------
	# Get connection parameters
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):
		from toolib.db import pyodbcs
		return [
			pyodbcs.get_mssql_connect_string({
				'host'     : connectData['host'],
				'database' : connectData['dbname'],
				'user'     : connectData['_username'],
				'password' : connectData['_password'],
			})
		], {}

	def _commit_(self):
		assert gDebug('sql', 'commit started')
		t = time.time()
		self._native.commit ()
		assert gDebug('sql', "commit finished in %.3f sec." % (time.time() - t,))

	def _rollback_ (self):
		assert gDebug('sql', 'rollback started')
		t = time.time()
		self._native.rollback()
		assert gDebug('sql', "rollback finished in %.3f sec." % (time.time() - t,))
	
	def _getNativeConnection(self):
		nc = super(Connection, self)._getNativeConnection()
		nc['decorate_error'] = self.decorateError
		return nc
	
	'''
	def _createTimestamp_ (self, year, month, day, hour, minute, secs, msec = 0):
		"""
		Create a timestamp object for the given point in time.

		This function doesn't have to be overwritten unless the handling of time
		values is weird.

		@param year: Year number
		@param month: Month number (1 - 12)
		@param day: Day of the month (1 - 31)
		@param hour: Hour (0 - 23)
		@param minute: Minute (0 - 59)
		@param secs: Whole seconds (integer)
		@param msec: Microseconds (integer)

		returns: a timestamp object created by the driver's Timestamp constructor
		"""
		import datetime
		return datetime.datetime(year, month, day, hour, minute, secs, msec)
	'''