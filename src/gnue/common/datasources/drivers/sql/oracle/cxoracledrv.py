# GNU Enterprise Common Library - Oracle database driver using cxOracle
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
# $Id: cxoracledrv.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for Oracle backends using the cxOracle DBSIG2 module.
"""

__all__ = ['Connection']

__pluginalias__ = ['cxoracle']

from gnue.common.datasources.drivers.sql.oracle import Base


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		import cx_Oracle
	except ImportError:
		raise GConnections.DependencyError, ('cx_Oracle', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "cx_Oracle SQLNet Driver"

	url = "http://www.cxtools.net/"

	doc = """
Description
-----------
An Oracle driver from Computronix. Works with Oracle 8.1.x thru 10.x  via
Oracle's SQL-Net OCI interface.

Support
-------
Supported Platforms:

  - Linux/BSD
  - Solaris
  - MS Windows 98/NT/2000/XP (Installer available)


Connection Properties
----------------------
* service  -- This is the Oracle TNS connection name

Examples
--------
[myconn]
provider=cxoracle       # Use the CX Oracle adapter
service=mytnsname       # The TNS connection string of the database

Notes
-----
1. Requires Oracle Client Libraries.

2. Does not recognize the TWO_TASK environment setting.

3. Creation of new databases with "gnue-schema --createdb" does not
   work with this driver. Index introspection is not supported.

4. Other than that, the driver is fully functional with no known serious
   problems.
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Connection class for Oracle backends using the cxOracle DBSIG2 module.
	"""

	_drivername_ = 'cx_Oracle'
