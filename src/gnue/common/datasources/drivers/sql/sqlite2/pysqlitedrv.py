# GNU Enterprise Common Library - SQLite database driver using pysqlite
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
# $Id: pysqlitedrv.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for SQLite backends using the pysqlite DBSIG2 module.
"""

__all__ = ['Connection']

from gnue.common.datasources.drivers import DBSIG2
from gnue.common.datasources.drivers.sql.sqlite2 import Behavior


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		import sqlite

		# This is a workaround for a bug in PySQLite. All the following mebers are
		# not imported from main.py in __init__.py
		if not hasattr (sqlite, 'Timestamp') and sqlite.main.have_datetime:
			sqlite.Date               = sqlite.main.Date
			sqlite.Time               = sqlite.main.Time
			sqlite.Timestamp          = sqlite.main.Timestamp
			sqlite.DateFromTicks      = sqlite.main.DateFromTicks
			sqlite.TimeFromTicks      = sqlite.main.TimeFromTicks
			sqlite.TimestampFromTicks = sqlite.main.TimestampFromTicks

			sqlite.DateTimeType       = sqlite.main.DateTimeType
			sqlite.DateTimeDeltaType  = sqlite.main.DateTimeDeltaType

	except ImportError:
		raise GConnections.DependencyError, ('SQLitedbapi', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "pysqlite"

	url = "http://pysqlite.sourceforge.net/"

	doc = """
Description
-----------
PySQLite is a Python extension for SQLite that conforms to the Python
Database API Specification 2.0. The source is released under the
Python license.

Support
-------
Supported Platforms:

  - Linux/BSD
  - Solaris
  - MS Windows 98/NT/2000/XP

Connection Properties
---------------------
* dbname     -- This is the file name of the sqlite database (required)

Examples
--------
[myconn]
provider=sqlite2        # Use the SQLite adapter
dbname=/usr/db/testdb   # The filename for the SQLite database

Notes
-----
1. The database engine stores all data in string format. Many
   SQL statements won't work. Comparison of date types won't work
   correctly, etc.

2. Other than that, this driver is fully functional without any serious
   known problems.
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (DBSIG2.Connection):
	"""
	Connection class for SQLite backends using the pysqlite DBSIG2 module.
	"""

	_drivername_ = 'sqlite'
	_behavior_   = Behavior.Behavior

	# SQLite doesn't like boolean type in SQL parameters
	_boolean_true_  = 1
	_boolean_false_ = 0
	_rowidField_    = u'oid'


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections, name, parameters):

		DBSIG2.Connection.__init__ (self, connections, name, parameters)

		# If autocommit is False, sqlite2 opens the database file with an exclusive
		# lock. If autocommit is True, no exclusive lock is made, but every
		# statement is sent to the database. Since appserver is able to handle
		# transactions on it's own, we turn on autocommit.
		self.__noTransactions = parameters.get ('appserver', False)


	# ---------------------------------------------------------------------------
	# Return a sequence of required login fields
	# ---------------------------------------------------------------------------

	def _getLoginFields_ (self):
		"""
		This function returns an empty sequence since SQLite doesn't use any user
		authentication.
		"""
		return []


	# ---------------------------------------------------------------------------
	# Get connection parameters
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):

		# mandatory parameters
		kwargs = {'db'        : connectData ['dbname'],
			'encoding'  : self._encoding,
			'autocommit': self.__noTransactions}

		return ([], kwargs)


	# ---------------------------------------------------------------------------
	# Commit a pending transactiona pending transaction
	# ---------------------------------------------------------------------------

	def _commit_ (self):
		"""
		This function performs a commit depending on the current transaction-flag.
		"""
		if not self.__noTransactions:
			DBSIG2.Connection._commit_ (self)
