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
# $Id: psycopgdrv.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for PostgreSQL backends using the psycopg DBSIG2 module.
"""

__all__ = ['Connection']

__pluginalias__ = ['psycopg']

from gnue.common.datasources.drivers.sql.postgresql import Base


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		import psycopg
	except:
		raise GConnections.DependencyError, ('psycopg', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "psycopg"

	url = "http://initd.org/software/initd/psycopg/"

	doc = """
Description
-----------
From the Psycopg website: "It was written from scratch with the aim of
being very small and fast, and stable as a rock."  Written by initd.org
volunteers.

Support
-------
Supported Platforms:

  - Linux/BSD
  - MS Windows 98/NT/2000/XP (Installer available)

Connection Properties
---------------------
* dbname -- This is the database to use (required)
* host  -- This is the name of the database host, or, on Linux,
    directory containing the network socket (optional)
* port -- Port that PostgreSQL is running on (defaults to 5432) (optional)
* use_oid -- if set to any value, the driver uses Postgres' OID field as an
    implicit primary key for all tables. OID fields were generated by default
    for all tables for Postgres 7.x and are not generated by default for
    Postgres 8.x.

Examples
--------
  [myconn]
  provider=psycopg        # Use the psycopg adapter
  host=localhost          # The hostname/IP of the postgresql host
  dbname=mydb             # The name of the pg database

Notes
-----
1. This is the driver of choice for PostgreSQL.

2. Available in Debian as: "apt-get install python-psycopg".

3. Windows installer available at: http://stickpeople.com/projects/python/win-psycopg/.

4. This driver is fully functional with no known serious problems.
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Connection class for PostgreSQL backends using the psycopg DBISG2 module.
	"""

	_drivername_ = 'psycopg'
	_need_rollback_after_exception_ = True
