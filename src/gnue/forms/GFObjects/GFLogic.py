# GNU Enterprise Forms - GF Object Hierarchy - Logic tag
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
# $Id: GFLogic.py,v 1.6 2012/01/24 14:05:03 oleg Exp $
"""
Handles the <logic> tag.
"""

from gnue.forms.GFObjects.GFObj import GFObj, UnresolvedNameError
from gnue.forms.GFObjects.GFBlock import GFBlock

__all__ = ['GFLogic', 'BlockNotFoundError']

# =============================================================================
# Exceptions
# =============================================================================

class BlockNotFoundError(UnresolvedNameError):
	def __init__(self, source, name, referer=None):
		UnresolvedNameError.__init__(self, source, 'Block', name, referer)


# =============================================================================
# Wrapper for the logic tag
# =============================================================================

class GFLogic(GFObj):
	"""
	The logic tag is a container for all business logic elements like, blocks,
	fields, block-level and field-level triggers.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		GFObj.__init__(self, parent, "GFLogic")
		self._blockMap = {}
		self._blockList = []

		self._triggerFunctions = {
			'getBlock' : {'function': self.__trigger_getBlock},
		}

	def _phase_1_init_(self):
		# add child blocks into logic
		self.walk(self.__init_rows_walker)

	def __init_rows_walker(self, item):
		if isinstance(item, GFBlock):
			self._blockList.append(item)
			self._blockMap[item.name] = item

	def getBlock(self, name, referer=None):
		try:
			return self._blockMap[name]
		except KeyError:
			raise BlockNotFoundError(self, name, referer)

	def __trigger_getBlock(self, name):
		return self.getBlock(name).get_namespace_object()
