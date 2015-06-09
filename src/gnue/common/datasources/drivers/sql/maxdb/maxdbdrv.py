# GNU Enterprise Common Library - MaxDB database driver
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
# $Id: maxdbdrv.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for MaxDB/SAP-DB backends.
"""

__all__ = ['Connection']

import datetime

from gnue.common.datasources.drivers import DBSIG2
from gnue.common.datasources.drivers.sql.maxdb import Behavior


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		import sapdb.dbapi

	except ImportError:
		raise GConnections.DependencyError, ('sapdb', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "MySQL's MaxDB driver"

	url = "http://www.mysql.com/products/maxdb/sapdbapi.html"

	doc = """
Description
-----------
Python driver for MaxDB/SAPDB version 7.x+.

Support
-------
Supported Platforms:

  - Linux/BSD
  - MS Windows 98/NT/2000/XP

Connection Properties
---------------------
* host       -- This is the MaxDB host for your connection (optional)
* dbname     -- This is the MaxDB database to use (required)
* timeout    -- Command timeout in seconds (optional)
* isolation  -- Isolation level (optional) (0, 1 [default], 10, 15, 2, 20, 3, 30)
* sqlmode    -- INTERNAL (default) or ORACLE (optional)
* sqlsubmode -- ODBC or empty (optional)

Examples
--------
# This connection uses the SAP DB  driver
# We will be connecting to the SAP DB server on
# "localhost" to a database called "TST".
[sapdb]
comment = XYZ Development Database
provider = sapdb
host=dbs.mydomain.com
dbname = TST
timeout = 900

Notes
-----
1.  The driver is fully functional
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (DBSIG2.Connection):
	"""
	Connection class for MaxDB backends.
	"""

	_drivername_ = 'sapdb.dbapi'
	_behavior_   = Behavior.Behavior

	_named_as_sequence_ = True
	_broken_rowcount_   = True
	_std_datetime_      = True


	# ---------------------------------------------------------------------------
	# Get connection parameters
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):

		# mandatory parameters
		# FIXME: would it be possible to use kwargs for these parameters, too?
		params = [(connectData ['_username']).upper(),
			connectData ['_password'],
			connectData ['dbname'],
			connectData.get ('host', '')]

		# keyword arguments
		kwargs = {}

		for gnueName, sapdbName in [('sqlmode'   , 'sqlmode'),
			('timeout'   , 'timeout'),
			('isolation' , 'isolation'),
			('sqlsubmode', 'component')]:
			if connectData.has_key (gnueName):
				kwargs [sapdbName] = connectData [gnueName]

		return (params, kwargs)

	# ---------------------------------------------------------------------------

	def _connect_ (self, connectData):

		DBSIG2.Connection._connect_ (self, connectData)
		self._native.typeTranslations = {'Date': self.__toDate,
			'Time': self.__toTime,
			'Timestamp': self.__toDateTime}

	# ---------------------------------------------------------------------------

	def __toDate (self, internal):
		(year, month, day) = (internal [:4], internal [4:6], internal [6:8])
		return datetime.date (int (year), int (month), int (day))

	# ---------------------------------------------------------------------------

	def __toTime (self, internal):
		(hour, minute, second) = map (int, (internal [:4], internal [4:6],
				internal [6:8]))
		return datetime.time (hour, minute, second)

	# ---------------------------------------------------------------------------

	def __toDateTime (self, ival):
		(year, month, day, hour, minute, second, micros) = \
			map (int, (ival [:4], ival [4:6], ival [6:8], ival [8:10], ival [10:12],
				ival [12:14], ival [14:] or '0'))
		return datetime.datetime (year, month, day, hour, minute, second, micros)

	# ---------------------------------------------------------------------------

	def _createTime_ (self, hour, minute, second, msecs = 0):

		return self._driver.Time (hour, minute, second)
