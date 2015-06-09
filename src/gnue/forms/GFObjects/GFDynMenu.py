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
# Copyright 2000-2006 Free Software Foundation
#
#
# FILE:
# GFDynMenu.py
#
# DESCRIPTION:
"""
Menu like GFTree, loads from block
"""

from src.gnue.forms.GFObjects.GFTree import GFTreeMixIn
from src.gnue.forms.GFObjects.commanders import GFMenu

#
# GFDynMenu
#
from src.gnue.forms.GFObjects import GFObj


class GFDynMenu(GFTreeMixIn, GFObj):

	label = ""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		GFObj.__init__(self, parent, self.__class__.__name__)
		GFTreeMixIn.__init__(self)

		self._triggerProperties = {
			'enabled': {
				'set': self.setEnabled,
				'get': self.isEnabled,
			},
		}

		self.enabled = True

	def getActionSource(self):
		# return parent of most parent menu
		source = self.getParent()
		while isinstance(source, GFMenu):
			source = source.getParent()
		return source

	def setEnabled(self, enabled):
		if self.enabled != enabled:
			self.enabled = enabled
			self.uiWidget._ui_enable_(enabled)

	def isEnabled(self):
		return self.enabled
