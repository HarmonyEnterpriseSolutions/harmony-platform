# GNU Enterprise Common Library - Firebird database driver using KinterbasDB
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
# $Id: kinterbasdbdrv.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for Firebird/Interbase backends using the KinterbasDB
DBSIG2 module.
"""

__all__ = ['Connection']

from gnue.common.datasources.drivers import DBSIG2
from gnue.common.datasources.drivers.sql.interbase import Behavior


# =============================================================================
# Test if plugin is functional
# =============================================================================

def __initplugin__ ():
	from gnue.common.datasources import GConnections
	try:
		import kinterbasdb

	except ImportError:
		raise GConnections.DependencyError, ('kinterbasdb', None)


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "kinterbasdb Firebird/Interbase Driver"

	url = "http://kinterbasdb.sourceforge.net"

	doc = """
Description
-----------
Written by Alexander Kuznetsov, kinterbasdb provides support for
Firebird and Interbase.

Support
-------
Supported Platforms:

  - Linux/BSD
  - MS Windows 98/NT/2000/XP (Installer available)


Connection Properties
---------------------
* host       -- This is the hostname running your database server (optional)
* dbname     -- This is the name of the database to use (required)

Examples
--------
  [myconn]
  provider=firebird       # Use the kinterbasdb adapter
  host=localhost          # The hostname/IP of the Firebird host
  dbname=mydb             # The name of the Firebird database

  [myconn2]
  provider=interbase      # Use the kinterbasdb adapter
  host=localhost          # The hostname/IP of the Interbase host
  dbname=mydb             # The name of the Interbase database

Notes
-----
1. This driver is fully fuctional and has no serious known problems.


To build the driver on a Ubuntu Breezy (and below) you need at least these
packages:

  * build-essentials
  * python-dev
  * firebird2-dev
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (DBSIG2.Connection):
	"""
	Connection class for Interbase backends using the KinterbasDB DBSIG2 module.
	"""

	_drivername_ = 'kinterbasdb'
	_behavior_   = Behavior.Behavior

	_broken_rowcount_ = True
	_must_fetchall_   = True


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections, name, parameters):

		DBSIG2.Connection.__init__ (self, connections, name, parameters)

		# Find out encoding for Interbase
		if ib_encTable.has_key (self._encoding):
			self._ib_encoding = ib_encTable [self._encoding]
		else:
			self._ib_encoding = ''
			assert gDebug (1, "Encoding '%s' is not supported by interbase dbdriver. "
				"Using default encoding." % self._encoding)


	# ---------------------------------------------------------------------------
	# Connect to the backend and establish type conversions
	# ---------------------------------------------------------------------------

	def _connect_ (self, connectData):

		DBSIG2.Connection._connect_ (self, connectData)

		# We could do a kinterbasdb.init (100) in __initplugin__ () instead, but
		# then there is another dependency to a FixedPoint module which is not
		# included in the kinterbasdb package
		import kinterbasdb.typeconv_datetime_stdlib as tc_dt

		# Install type conversions
		self._native.set_type_trans_in({
				'DATE':      tc_dt.date_conv_in,
				'TIME':      tc_dt.time_conv_in,
				'TIMESTAMP': tc_dt.timestamp_conv_in})

		self._native.set_type_trans_out({
				'DATE':      tc_dt.date_conv_out,
				'TIME':      tc_dt.time_conv_out,
				'TIMESTAMP': tc_dt.timestamp_conv_out})

		# Map the constructors and singeltons
		for i in ['Date', 'Time', 'Timestamp', 'DateFromTicks', 'TimeFromTicks',
			'TimestampFromTicks']:
			setattr (self._driver, i, getattr (tc_dt, i))


	# ---------------------------------------------------------------------------
	# Get connection parameters
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):

		# mandatory parameters
		kwargs = {'database': connectData ['dbname'],
			'user'    : connectData ['_username'],
			'password': connectData ['_password']}

		# optional parameters
		for gnueName, ibName in [('host', 'host')]:
			if connectData.has_key (gnueName):
				kwargs [ibName] = connectData [gnueName]

		# character set
		if self._ib_encoding:
			kwargs ['charset'] = self._ib_encoding

		return ([], kwargs)


	# ---------------------------------------------------------------------------
	# Start a new transaction
	# ---------------------------------------------------------------------------

	def _beginTransaction_ (self):
		self._native.begin ()


	# ---------------------------------------------------------------------------
	# Return the current date, according to database
	# ---------------------------------------------------------------------------

	def getTimeStamp (self):
		return self.sql1 ("SELECT CAST('now' AS DATE) FROM rdb$database")


	# ---------------------------------------------------------------------------
	# Return a sequence number from sequence 'name'
	# ---------------------------------------------------------------------------

	def getSequence (self, name):
		return self.sql1 ("SELECT gen_id(%s,1) FROM rdb$database" % name)


# =============================================================================
# Encoding-Table
# =============================================================================

# RDB$CHARACTER_SETS.RDB$CHARACTER_SET_NAME
ib_encTable =  {'ascii'     :  'ASCII',
	''          :  'BIG_5',
	''          :  'CYRL',
	'cp437'     :  'DOS437',
	'cp850'     :  'DOS850',
	'cp852'     :  'DOS852',
	'cp857'     :  'DOS857',
	'cp860'     :  'DOS860',
	'cp861'     :  'DOS861',
	'cp863'     :  'DOS863',
	'cp865'     :  'DOS865',
	''          :  'EUCJ_0208',
	''          :  'GB_2312',
	'iso8859-1' :  'ISO8859_1',
	'iso8859-2' :  'ISO8859_2',
	'iso8859-3' :  'ISO8859_3',
	'iso8859-4' :  'ISO8859_4',
	'iso8859-5' :  'ISO8859_5',
	'iso8859-6' :  'ISO8859_6',
	'iso8859-7' :  'ISO8859_7',
	'iso8859-8' :  'ISO8859_8',
	'iso8859-9' :  'ISO8859_9',
	'iso8859-13':  'ISO8859_13',
	''          :  'KSC_5601',
	''          :  'NEXT',
	''          :  'NONE',
	''          :  'OCTETS',
	''          :  'SJIS_0208',
	'utf-8'     :  'UNICODE_FSS',
	'cp1250'    :  'WIN1250',
	'cp1251'    :  'WIN1251',
	'cp1252'    :  'WIN1252',
	'cp1253'    :  'WIN1253',
	'cp1254'    :  'WIN1254',
	'cp1255'    :  'WIN1255',
	'cp1256'    :  'WIN1256',
	'cp1257'    :  'WIN1257'}
