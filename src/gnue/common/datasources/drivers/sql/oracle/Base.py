# GNU Enterprise Common Library - Generic Oracle database driver
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
# $Id: Base.py 9452 2007-03-29 15:02:51Z jan $

"""
Generic database driver plugin for Oracle backends.
"""

__all__ = ['Connection']

__noplugin__ = True

import os
from gnue.common.apps import errors

from gnue.common.datasources.drivers import DBSIG2
from gnue.common.datasources.drivers.sql.oracle import Behavior


# =============================================================================
# Connection class
# =============================================================================

class Connection (DBSIG2.Connection):
	"""
	Generic Connection class for Oracle databases.
	"""

	_behavior_ = Behavior.Behavior

	# TODO: Test if it would work with the default (True/False), too
	_boolean_false_ = 0
	_boolean_true_  = 1


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections, name, parameters):

		DBSIG2.Connection.__init__ (self, connections, name, parameters)

		if parameters.has_key ('oracle_home'):
			os.environ ['ORACLE_HOME'] = parameters ['oracle_home']
		elif not os.environ.has_key("ORACLE_HOME"):
			raise errors.AdminError('Environment parameter "ORACLE_HOME" is not defined!')


	# ---------------------------------------------------------------------------
	# Get connection parameters
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):

		connectstring = "%s/%s@%s" % (connectData ['_username'],
			connectData ['_password'],
			connectData ['service'])

		return ([connectstring], {})


	# ---------------------------------------------------------------------------
	# Return the current date, according to database
	# ---------------------------------------------------------------------------

	def getTimeStamp (self):

		return self.sql1 ("select sysdate from dual")


	# ---------------------------------------------------------------------------
	# Return a sequence number from sequence 'name'
	# ---------------------------------------------------------------------------

	def getSequence (self, name):

		return self.sql1 ("select %s.nextval from dual" % name)
