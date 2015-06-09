# GNU Enterprise Forms - GF Object Hierarchy - Datasources
#
# Copyright 2001-2007 Free Software Foundation
#
# This file is part of GNU Enterprise
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
# $Id: GFDataSource.py,v 1.4 2008/12/25 16:16:59 oleg Exp $
"""
Logical datasource support
"""

from gnue.common.datasources.GDataSource import GDataSource

# =============================================================================
# Wrapper class for datasources used in GF object trees
# =============================================================================

class GFDataSource(GDataSource):
	"""
	A GFDataSource wrapps a L{gnue.common.datasources.GDataSource} object
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent):

		GDataSource.__init__(self, parent, 'GFDataSource')

		self._toplevelParent = 'GFForm'
		self._form = self.findParentOfType('GFForm')
