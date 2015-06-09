# GNU Enterprise Forms - GF Object Hierarchy - Box
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
# $Id: GFBox.py,v 1.8 2009/07/24 14:59:58 oleg Exp $
"""
Logical box support
"""

# =============================================================================
# Box widget
# =============================================================================
from src.gnue.forms.GFObjects import GFContainer


class GFBox(GFContainer):

	label = None

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None, name="GFBox"):
		GFContainer.__init__(self, parent, name)

	def _event_push_default_button(self):
		"""
		some child GFObject notifies about user requested to push default button
		"""
		# search default button in this box and push if found
		return self.push_default_button()

	def push_default_button(self):
		"""
		if have some children can push_default_button do it
		"""
		for i in self._children:
			if hasattr(i, 'push_default_button'):
				return i.push_default_button()
		return False

	def hasTitledBorder(self):
		"""
		returns True if the box has TitledBorder
		"""
		return self.label is not None and not self.hasLabel()
