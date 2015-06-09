# GNU Enterprise Common Library - SQLite3 database driver using pysqlite2
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
# $Id: pysqlite2drv.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for SQLite3 backends using the pysqlite2 DBSIG2 module.
"""

__all__ = ['Connection']

import datetime
import locale

from gnue.common.datasources.drivers import DBSIG2
from gnue.common.datasources.drivers.sql.sqlite3 import Behavior


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		from pysqlite2 import dbapi2

	except ImportError:
		raise GConnections.DependencyError, ('pysqlite2.dbapi2', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "pysqlite2"

	url = "http://initd.org"

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
* timeout    -- When a database is accessed by multiple connections, and one of
                the processes modifies the database, the SQLite database is
                locked until that transaction is committed. The timeout
                parameter specifies how long the connection should wait for the
                lock to go away until raising an exception

Examples
--------
[myconn]
provider=sqlite3         # Use the SQLite adapter
dbname=/usr/db/testdb    # The filename for the SQLite database

Notes
-----
1. The database engine stores all data in string format. Many
   SQL statements won't work.

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

	_drivername_ = 'pysqlite2.dbapi2'
	_behavior_   = Behavior.Behavior

	_std_datetime_    = True
	_rowidField_      = u'oid'
	_broken_rowcount_ = True
	_must_fetchall_   = True


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

		from pysqlite2 import dbapi2

		# Register the missing converter and adapater for time values
		dbapi2.register_adapter (datetime.time, adapt_time)
		dbapi2.register_converter ('time', convert_time)
		# Register the missing converter and adapter for boolean values
		dbapi2.register_adapter (bool, adapt_boolean)
		dbapi2.register_converter ('boolean', convert_boolean)
		# NOTE: gnue-forms allways creates datetime values, even for dates. This is
		# why we have to define our own converter. Please remove as soon as
		# gnue-forms is fixed.
		dbapi2.register_converter ('date', convert_date)

		# mandatory parameters
		kwargs = {'database'    : connectData ['dbname'],
			'detect_types': dbapi2.PARSE_DECLTYPES}

		if 'timeout' in connectData:
			kwargs ['timeout'] = connectData ['timeout']

		return ([], kwargs)

	# ---------------------------------------------------------------------------

	def _connect_ (self, connectData):

		DBSIG2.Connection._connect_ (self, connectData)

		# With pysqlite2 version 2.2+ we could override the default collation
		# function to use the current locales' one
		if hasattr (self._native, 'create_collation'):
			self._native.create_collation ('BINARY', collateByLocale)



# =============================================================================
# The following functions should go into pysqlite2.dbapi2 !
# =============================================================================

# -----------------------------------------------------------------------------

def collateByLocale (value1, value2):

	return locale.strcoll (value1, value2)

# -----------------------------------------------------------------------------

def convert_time (value):

	# Be nice to datetime values passed in and take only the timepart
	parts    = value.split (' ', 1)
	timepart = len (parts) > 1 and parts [1] or parts [0]

	timepart_full = timepart.split(".")
	hours, minutes, seconds = map(int, timepart_full[0].split(":"))
	if len(timepart_full) == 2:
		microseconds = int(float("0." + timepart_full[1]) * 1000000)
	else:
		microseconds = 0

	return datetime.time (hours, minutes, seconds, microseconds)

# -----------------------------------------------------------------------------

def convert_date (value):

	datepart = value.split (' ', 1) [0]
	return datetime.date (*map (int, datepart.split ('-')))

# -----------------------------------------------------------------------------

def adapt_time (value):

	if isinstance (value, datetime.datetime):
		value = value.time ()

	return value.isoformat ()

# -----------------------------------------------------------------------------

def convert_boolean (value):

	value = "%s" % value
	return value.strip ().lower () in ['y', 't', '1', 'true', 'yes']

# -----------------------------------------------------------------------------

def adapt_boolean (value):

	return value and '1' or '0'
