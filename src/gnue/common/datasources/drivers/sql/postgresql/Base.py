# GNU Enterprise Common Library - Generic PostgreSQL database driver
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
# $Id: Base.py 9222 2007-01-08 13:02:49Z johannes $

"""
Generic database driver plugin for PostgreSQL backends.
"""
from src.gnue.common.datasources.drivers.sql.postgresql import ErrorDecorators

__all__ = ['Connection']

__noplugin__ = True

from gnue.common.datasources.drivers import DBSIG2
from gnue.common.datasources.drivers.sql.postgresql import Behavior

# =============================================================================
# Connection class
# =============================================================================

class Connection(ErrorDecorators, DBSIG2.Connection):
	"""
	Generic Connection class for PostgreSQL backends.
	"""

	_behavior_ = Behavior.Behavior

	# The oid column is not created by default with Postgres >= 8.0, so don't use
	# it by default.
	# _rowidField_ = 'oid'

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections, name, parameters):

		DBSIG2.Connection.__init__ (self, connections, name, parameters)

		# Optionally the oid can be used as a rowid field.
		if 'use_oid' in parameters:
			self._rowidField_ = 'oid'

		# Find out encoding for Postgres
		if pg_encTable.has_key (self._encoding):
			self._pg_encoding = pg_encTable [self._encoding]
		else:
			self._pg_encoding = ''
			assert gDebug (1, "Encoding '%s' is not supported by postgresql dbdriver. "
				"Using default encoding." % self._encoding)


	# ---------------------------------------------------------------------------
	# Get connection parameters
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):

		# mandatory parameters
		kwargs = {'database': connectData ['dbname'],
			'user'    : connectData ['_username'],
			'password': connectData ['_password']}

		# optional parameters
		for gnueName, pgName in [('host', 'host'),
			('port', 'port')]:
			if connectData.has_key (gnueName):
				kwargs [pgName] = connectData [gnueName]

		return ([], kwargs)

	# ---------------------------------------------------------------------------

	def _getNativeConnection(self):
		nc = super(Connection, self)._getNativeConnection()
		nc['decorate_error'] = self.decorateError
		return nc

	# ---------------------------------------------------------------------------
	# Done at the start of each transaction
	# ---------------------------------------------------------------------------

	def _beginTransaction_ (self):

		# Must set CLIENT_ENCODING per transaction as it is reset on COMMIT or
		# ROLLBACK.

		if self._pg_encoding not in ['', 'DEFAULT']:
			# django setups psycopg2 to return unicode
			# it does "psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)"
			# SET CLIENT ENCOING does not work in this case, leads to UnicodeDecodeError as connection does not know about real encoding
			# TODO: do not set client encoding at all, use database. Must check about sql encoding hovever
			self._native.set_client_encoding(self._pg_encoding)
			#self.sql0 ("SET CLIENT_ENCODING TO '%s'" % self._pg_encoding)


	# ---------------------------------------------------------------------------
	# Return the current date, according to database
	# ---------------------------------------------------------------------------

	def getTimeStamp (self):

		return self.sql1 ("select current_timestamp")


	# ---------------------------------------------------------------------------
	# Return a sequence number from sequence 'name'
	# ---------------------------------------------------------------------------

	def getSequence (self, name):

		return self.sql1 ("select nextval('%s')" % name)



# =============================================================================
# Encoding-Table
# =============================================================================

pg_encTable = {
	'ascii'     : 'SQL_ASCII',     # ASCII
	''          : 'EUC_JP',        # Japanese EUC
	''          : 'EUC_CN',        # Chinese EUC
	''          : 'EUC_KR',        # Korean EUC
	''          : 'JOHAB',         # Korean EUC (Hangle base)
	''          : 'EUC_TW',        # Taiwan EUC
	'utf-8'     : 'UNICODE',       # Unicode (UTF-8)
	''          : 'MULE_INTERNAL', # Mule internal code
	'iso8859-1' : 'LATIN1',        # ISO 8859-1 ECMA-94 Latin Alphabet No.1
	'iso8859-2' : 'LATIN2',        # ISO 8859-2 ECMA-94 Latin Alphabet No.2
	'iso8859-3' : 'LATIN3',        # ISO 8859-3 ECMA-94 Latin Alphabet No.3
	'iso8859-4' : 'LATIN4',        # ISO 8859-4 ECMA-94 Latin Alphabet No.4
	'iso8859-9' : 'LATIN5',        # ISO 8859-9 ECMA-128 Latin Alphabet No.5
	'iso8859-10': 'LATIN6',        # ISO 8859-10 ECMA-144 Latin Alphabet No.6
	'iso8859-13': 'LATIN7',        # ISO 8859-13 Latin Alphabet No.7
	'iso8859-14': 'LATIN8',        # ISO 8859-14 Latin Alphabet No.8
	'iso8859-15': 'LATIN9',        # ISO 8859-15 Latin Alphabet No.9
	'iso8859-16': 'LATIN10',       # ISO 8859-16 ASRO SR 14111 Latin Alph. No.10
	'iso8859-5' : 'ISO-8859-5',    # ECMA-113 Latin/Cyrillic
	'iso8859-6' : 'ISO-8859-6',    # ECMA-114 Latin/Arabic
	'iso8859-7' : 'ISO-8859-7',    # ECMA-118 Latin/Greek
	'iso8859-8' : 'ISO-8859-8',    # ECMA-121 Latin/Hebrew
	'koi8-r'    : 'KOI8',          # KOI8-R(U)
	'cp1251'    : 'WIN',           # Windows CP1251
	''          : 'ALT',           # Windows CP866
	''          : 'WIN1256',       # Arabic Windows CP1256
	''          : 'TCVN',          # Vietnamese TCVN-5712 (Windows CP1258)
	''          : 'WIN874',        # Thai Windows CP874
}
