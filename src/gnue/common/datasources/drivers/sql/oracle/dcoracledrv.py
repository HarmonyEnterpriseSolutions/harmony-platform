# GNU Enterprise Common Library - Oracle database driver using DCOracle
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
# $Id: dcoracledrv.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for Oracle backends using the DCOracle DBSIG2 module.
"""

__all__ = ['Connection']

__pluginalias__ = ['dcoracle']

from gnue.common.datasources.drivers.sql.oracle import Base


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		import DCOracle2
	except ImportError:
		raise GConnections.DependencyError ('DCOracle2', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "DCOracle2 OCI Driver"

	url = "http://www.zope.org/Members/matt/dco2/"

	doc = """
Description
-----------
An Oracle driver from Digital Creations (Zope).  Works with Oracle
7.3, 8.x, 9i via Oracle's SQL-Net OCI interface.

The "Oracle Database Bindings for Python" are packaged with the
"Zope Oracle Database Adapter". GNUe does not use the Zope
Adapter, so you can safely ignore any installation instructions
referring to Zope.

DCOracle is not actively maintained by its upstream developers 
any longer. You may wish to use the cx_Oracle driver instead. 

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
provider=oracle         # Use the DCOracle2 adapter
service=mytnsname       # The TNS connection string of the database

Notes
-----
1. Requires Oracle Client Libraries.

2. Does not recognize the TWO_TASK environment setting.

3. Creation of new databases with "gnue-schema --createdb" does not
   work with this driver. Index introspection is not supported

4. Other than that, the driver is fully functional with no known serious
   problems.
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Connection class for Oracle backends using the DCOracle DBSIG2 module.
	"""

	_drivername_ = 'DCOracle2'
