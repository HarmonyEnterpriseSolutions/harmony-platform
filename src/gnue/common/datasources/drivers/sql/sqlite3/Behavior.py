# GNU Enterprise Common Library - Schema support for SQLite3
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
# $Id: Behavior.py 9222 2007-01-08 13:02:49Z johannes $

"""
Schema support plugin for SQLite3.
"""

from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers.sql.sqlite2 import Behavior as Base


# =============================================================================
# Behavior class
# =============================================================================

class Behavior (Base.Behavior):
	"""
	Behavior class for SQLite3 backends.

	Limitations:
	  - Since SQLite3 is typeless we cannot derive a 'length' for columns
	    specified as 'integer' or 'text' without any further information.
	  - SQLite3 does not support referential constraints
	  - SQLite3 has no real concept of a serial
	  - SQLite3 has no concept of a 'default with timestamp'
	  - Name of Primary Keys is not available
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connection):

		Base.Behavior.__init__ (self, connection)

		self._type2native_.update ({'boolean' : 'boolean',
				'datetime': 'timestamp'})

		self._passThroughTypes.append ('boolean')
