# GNU Enterprise Common Library - Generic DBSIG2 database driver - Connection
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
# $Id: Connection.py,v 1.2 2008/11/04 20:14:03 oleg Exp $

"""
Generic Connection class for DBSIG2 based database driver plugins.
"""
from src.gnue.common.datasources.drivers.ldap import ResultSet

__all__ = ['Connection']

import ldap

from gnue.common.datasources import Exceptions
from gnue.common.datasources.drivers import Base


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	"""

	_resultSetClass_    = ResultSet


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections, name, parameters):
		Base.Connection.__init__ (self, connections, name, parameters)


	# ---------------------------------------------------------------------------
	# Implementations of virtual methods
	# ---------------------------------------------------------------------------

	def _getLoginFields_ (self):
		return [(u_('User Name'), '_username', 'string', None, None, []),
			(u_('Password'), '_password', 'password', None, None, [])]

	# ---------------------------------------------------------------------------

	def _connect_ (self, connectData):
		print "_connect_", connectData
		try:
			self._ldapObject = ldap.open(connectData['host'], int(connectData.get('port', 389)))
			self._ldapObject.simple_bind_s(connectData['_username'], connectData['_password'])
		except ldap.LDAPError, e:
			raise self.decorateError(
				Exceptions.LoginError("%s: %s" % tuple(errors.getException()[1:3]))
			)

	# ---------------------------------------------------------------------------

	def _insert_ (self, table, newfields):
		raise NotImplementedError

	# ---------------------------------------------------------------------------

	def _update_ (self, table, oldfields, newfields):
		raise NotImplementedError

	# ---------------------------------------------------------------------------

	def _delete_ (self, table, oldfields):
		raise NotImplementedError

	# ---------------------------------------------------------------------------

	def _requery_ (self, table, oldfields, fields, parameters):
		raise NotImplementedError

	# ---------------------------------------------------------------------------

	def _commit_ (self):
		pass

	# ---------------------------------------------------------------------------

	def _rollback_ (self):
		pass

	# ---------------------------------------------------------------------------

	def _close_ (self):
		pass


	# ---------------------------------------------------------------------------
	# Virtual methods to be implemented by descendants
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):
		"""
		Return a tuple with a list and a dictionary, being the parameters and
		keyword arguments to be passed to the connection function of the DBSIG2
		driver.

		This method must be overwritten by all descendants.
		"""
		return ([], {})

	# ---------------------------------------------------------------------------

	def _createTimestamp_ (self, year, month, day, hour, minute, secs, msec = 0):
		"""
		Create a timestamp object for the given point in time.

		This function doesn't have to be overwritten unless the handling of time
		values is weird.

		@param year: Year number
		@param month: Month number (1 - 12)
		@param day: Day of the month (1 - 31)
		@param hour: Hour (0 - 23)
		@param minute: Minute (0 - 59)
		@param secs: Whole seconds (integer)
		@param msec: Microseconds (integer)

		returns: a timestamp object created by the driver's Timestamp constructor
		"""
		raise NotImplementedError


	# ---------------------------------------------------------------------------
	# Create an apropriate time object for the given values
	# ---------------------------------------------------------------------------

	def _createTime_ (self, hour, minute, second, msec = 0):
		"""
		Create a time object for the given point in time.

		This function doesn't have to be overwritten unless the handling of time
		values is weird.

		@param hour: Hour (0 - 23)
		@param minute: Minute (0 - 59)
		@param second: Whole seconds (integer)
		@param msec: Microseconds (integer)

		returns: a time object created by the driver's Time constructor
		"""
		raise NotImplementedError

	def decorateError(self, error):
		"""
		This function used to make database related error user frielndly
		"""
		return error
