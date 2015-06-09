# GNU Enterprise Common Library - MySQL database driver using MySQLdb
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
# $Id: mysqldbdrv.py 9398 2007-02-22 14:31:31Z johannes $

"""
Database driver plugin for MySQL backends using the MySQLdb DBSIG2 module.
"""

__all__ = ['Connection']

from gnue.common.datasources.drivers import DBSIG2
from gnue.common.datasources.drivers.sql.mysql import Behavior


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		import MySQLdb
	except ImportError:
		raise GConnections.DependencyError ('mysql-python',
			'http://sourceforge.net/projects/mysql-python')


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "MySQLdb"

	url = "http://sourceforge.net/projects/mysql-python"

	doc = """
Description
-----------
Mysql-python, written by Andy Dustman, supports MySQL 3.22, 3.23, and
4.x.

Support
-------
Supported Platforms:

  - Linux/BSD
  - Solaris
  - MS Windows 98/NT/2000/XP (Installer available)

Connection Properties
----------------------
* host       -- This is the host for your connection (required)
* dbname     -- This is the name of the database to use (required)
* port       -- This is the port where the server is running (optional)
* unicode    -- Enables/disable unicode connection mode (optional, default=true)
* encoding   -- Charset used for the database connection (default="utf-8")
* version    -- Server version of the database server (4 or 5, default is 5)

Examples
--------
 [myconn]
 provider=mysql          # Use the MySQLdb adapter
 host=localhost          # The hostname/IP of the MySQL host
 dbname=mydb             # The name of the MySQL database

Notes
-----
1. Transactions are supported if MySQL is compiled with proper
   transactional support (3.x series does NOT do this by default!).

2. Windows installer available at http://www.cs.fhm.edu/~ifw00065/.

3. Other than that, the driver is fully functional with no known serious
   problems.

If you get an error while connecting to the server which looks like this:
(1193, "Unknown system variable 'NAMES'") please set the connection parameter
'version=4'.
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (DBSIG2.Connection):
	"""
	Connection class for MySQL backends using the MySQLdb DBSIG2 module.
	"""

	_drivername_    = 'MySQLdb'
	_behavior_      = Behavior.Behavior

	_boolean_true_  = 1
	_boolean_false_ = 0
	_std_datetime_  = True


	# ---------------------------------------------------------------------------
	# Get connection parameters
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):

		# mandatory parameters
		kwargs = {'db'    : connectData ['dbname'],
			'user'  : connectData ['_username'],
			'passwd': connectData ['_password'] or '',
			'use_unicode': True}

		# MySQL 4.0* does not support SET NAMES ...
		srv_version = connectData.get('version', 5)

		# optional parameters
		for gnueName, dbName in [('host', 'host'), ('port', 'port'),
			('unicode', 'use_unicode')]:

			if gnueName in connectData:
				if gnueName == 'port':
					kwargs [dbName] = int (connectData[gnueName])
				elif gnueName == 'unicode':
					kwargs [dbName] = not (connectData[gnueName] in ['False','false','0'])
				else:
					kwargs [dbName] = connectData [gnueName]

		if int(srv_version) == 5 and mySQL_encTable.has_key (self._encoding):
			kwargs['charset'] = mySQL_encTable[self._encoding]
		else:
			assert gDebug (1, "Encoding '%s' is not supported by mysql dbdriver. "
				"Using default encoding." % self._encoding)

		return ([], kwargs)


	# ---------------------------------------------------------------------------
	# Start a new transaction
	# ---------------------------------------------------------------------------

	def _beginTransaction_ (self):

		# fix encoding setting of driver
		if mySQL_encTable.has_key (self._encoding):
			self._native.charset = self._encoding

		# only available if MySQL is compiled with transaction support
		try:
			self.sql0("BEGIN")
		# self._native.begin ()
		except:
			pass


	# ---------------------------------------------------------------------------
	# Return the current date, according to database
	# ---------------------------------------------------------------------------

	def getTimeStamp (self):
		return self.sql1 ("select current_timestamp")


# ---------------------------------------------------------------------------
# Return a sequence number from sequence 'name'
# ---------------------------------------------------------------------------

# def getSequence (self, name):
#   (not available in MySQL)



# =============================================================================
# Encoding-Table
# =============================================================================

mySQL_encTable = {
	'ascii'     : 'ascii',         # ASCII
	'big5'      : 'big5',          # Big5 Traditional Chinese
	'gb2312'    : 'gb2312',        # GB2312 Simplified Chinese
	'gbk'       : 'gbk',           # GBK Simplified Chinese
	''          : 'dec8',          # DEC West European
	''          : 'ujis',          # Japanese EUC
	''          : 'sjis',          # Shift-JIS Japanese
	''          : 'euckr',         # Korean EUC
	'utf-8'     : 'utf8',          # Unicode (UTF-8)
	''          : 'ucs2',          # Unicode (UCS-2) <-- not allowed as connection encoding
	'iso8859-1' : 'latin1',        # ISO 8859-1 ECMA-94 Latin Alphabet No.1
	'iso8859-2' : 'latin2',        # ISO 8859-2 ECMA-94 Latin Alphabet No.2
	'iso8859-9' : 'latin5',        # ISO 8859-9 ECMA-128 Latin Alphabet No.5 = ISO 8859-9 Turkishabet No.6
	'iso8859-13': 'latin7',        # ISO 8859-13 Latin Alphabet No.7
	'iso8859-7' : 'greek',         # ECMA-118 Latin/Greek = ISO 8859-7 Greek
	'iso8859-8' : 'hebrew',        # ECMA-121 Latin/Hebrew = ISO 8859-8 Hebrew
	'koi8-r'    : 'koi8r',         # KOI8-R Relcom Russian
	'koi8-u'    : 'koi8u',         # KOI8-U Ukrainian
	'cp1250'    : 'cp1250',        # Windows CP1250 Central European
	'cp1251'    : 'cp1251',        # Windows CP1251 = Windows Cyrillic
	'cp1256'    : 'cp1256',        # Windows CP1256 = Windows Arabic
	'cp1257'    : 'cp1257',        # Windows CP1257 = Windows Baltic
	'cp850'     : 'cp850',         # DOS West European
	'cp852'     : 'cp852',         # DOS Central European
	''          : 'swe7',          # 7bit Swedish
	''          : 'cp932',         # SJIS for Windows Japanese
	''          : 'eucjpms',       # UJIS for Windows Japanese
	''          : 'geostd8',       # GEOSTD8 Georgian
	''          : 'tis620',        # TIS620 Thai
	''          : 'armscii8',      # ARMSCII-8 Armenian
	''          : 'cp866',         # DOS Russian
	''          : 'keybcs2',       # DOS Kamenicky Czech-Slovak
	''          : 'macce',         # Mac Central European
	''          : 'macroman',      # Mac West European
}
