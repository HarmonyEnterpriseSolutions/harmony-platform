# GNU Enterprise Common Library - PostgreSQL database driver using pyPgSQL
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
# $Id: pypgsqldrv.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for PostgreSQL backends using the pyPgSQL DBSIG2 module.
"""

__all__ = ['Connection']

__pluginalias__ = ['pypgsql']

from gnue.common.datasources.drivers.sql.postgresql import Base


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		from pyPgSQL import PgSQL
	except:
		raise GConnections.DependencyError, ('pyPgSQL', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "pyPgSQL"

	url = "http://pypgsql.sf.net/"

	doc = """
Description
-----------
Written by Billy Allie, pyPgSQL is a database interface for PostgreSQL 7.x.

Support
-------
Supported Platforms:

  - Linux/BSD
  - MS Windows 98/NT/2000/XP (Installer available)

Platforms Tested:

 - GNU/Linux [Debian 2.x, 3.x, Slackware 8.0, RedHat ]
 - Windows 98/2000/XP

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
  provider=pypgsql        # Use the pypgsql adapter
  host=localhost          # The hostname/IP of the postgresql host
  dbname=mydb             # The name of the pg database

Notes
-----
1. pyPgSQL is available in Debian as python-pgsql.

2. This driver is fully functional with no known serious problems.
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Connection class for PostgreSQL backends using the pyPgSQL DBSIG2 module.
	"""

	_drivername_ = 'pyPgSQL.PgSQL'

	_rowidField_       = None             # PyPgSQL doesn't support rowid's!!
	_broken_fetchmany_ = True
	_broken_rowcount_  = True
	_need_rollback_after_exception_ = True