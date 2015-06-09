# GNU Enterprise Forms - GF Object Hierarchy - Static text objects
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
# $Id: GFLabel.py,v 1.4 2015/03/25 14:41:09 oleg Exp $
"""
A class wrapping static text objects
"""

from gnue.forms.GFObjects.GFObj import GFObj

# =============================================================================
# A generic text class
# =============================================================================

class GFLabel(GFObj):

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):

		GFObj.__init__(self, parent, 'GFLabel')

		# Default attributes (these may be replaced by parser)
		self.alignment = "left"

		self._triggerProperties = {
			'text': {
				'get': lambda: self.text,
				'set': self.set_text,
			},
		}


	def set_text(self, text):
		if self.text != text:
			self.text = text
			self.uiWidget._ui_set_text_(text)
