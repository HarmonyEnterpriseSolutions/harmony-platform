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
# $Id: adodbapidrv.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for MS-ADO backends using the adodbapi DBSIG2 module.
"""

__all__ = ['Connection']

from gnue.common.datasources.drivers import DBSIG2
from gnue.common.datasources.drivers.sql.msado import Behavior


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		import adodbapi
	except ImportError:
		raise GConnections.DependencyError, ('adodbapi', None)
	try:
		import win32com
	except ImportError:
		raise GConnections.DependencyError, ('win32com', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "msado"

	url = "http://sourceforge.net/projects/adodbapi"

	doc = """
Description
-----------
A Python DB-API 2.0 module that makes it easy to use Microsoft ADO
for connecting with databases and other data sources.

Prerequisites:

  * Mark Hammond's win32all python for windows extensions.


Support
-------
Supported Platforms:

  - MS Windows 98/NT/2000/XP (Installer available)


Connection Properties
----------------------
* oledb_provider   (required)
* data_source      (required)
* initial_catalog  (optional for SQL Server)
* network_library  (optional for SQL Server)
* data_provider    (optional for SQL Server)

You can find more connection strings here:
   http://www.able-consulting.com/MDAC/ADO/Connection/OLEDB_Providers.htm

Examples
--------
  [access]
  comment = MS Access database
  provider = msado
  oledb_provider = Microsoft.Jet.OLEDB.4.0
  data_source = C:\mydb.mdb

  [sqlserver]
  comment = MS SQL Server database
  provider = msado
  oledb_provider = sqloledb
  data_source = myServerName
  initial_catalog = myDatabaseName

Notes
-----
1. This driver is only usable under MS Windows.

2. This driver does not implement schema creation. Index introspection is not
   supported by this driver

3. MS SQL Server has been tested successfully.  MS Access backends need some
   more testing

4. Other than that, the driver is fully functional with no known serious
   problems.
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (DBSIG2.Connection):
	"""
	Connection class for MS ADO backends using the adodbapi DBSIG2 module.
	"""

	_drivername_      = 'adodbapi'
	_defaultBehavior_ = Behavior.Behavior

	_broken_rowcount_ = True


	# ---------------------------------------------------------------------------
	# Build up parameters for connect method
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):

		import adodbapi

		adodbapi.defaultIsolationLevel = adodbapi.adXactSerializable

		# mandatory parameters
		params = {'Provider'   : connectData ['oledb_provider'],
			'Data Source': connectData ['data_source'],
			'User Id'    : connectData ['_username'],
			'Password'   : connectData ['_password']}

		# optional parameters
		for gnueName, oledbName in [('initial_catalog', 'Initial Catalog'),
			('network_library', 'Network Library'),
			('data_provider'  , 'Data Provider'  )]:
			if connectData.has_key (gnueName):
				params [oledbName] = connectData [gnueName]

		p = ["%s=%s" % (k, v) for (k, v) in params.items ()]
		connectstring = ';'.join (p)

		return ([connectstring], {})
