# GNU Enterprise Forms - wx 2.6 UI Driver - Box widget
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
# $Id: splitter.py,v 1.2 2009/07/28 17:21:57 oleg Exp $
"""
"""

from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import Splitter

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UISplitter(UIWidget):
	"""
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		UIWidget.__init__(self, event)

	# -------------------------------------------------------------------------
	# Create a wx box widget
	# -------------------------------------------------------------------------

	def _create_widget_ (self, event):
		"""
		@param event: the creation-event instance carrying information like
		        container (parent-widget)

		@returns: wx widget
		"""
		self._container = self.widget = Splitter(self, self._gfObject.align in ('v', 'vertical'))
		self.getParent().addWidget(self)


	def addWidget(self, ui_widget):
		"""
		Add a given UI widget to the splitter.

		@param ui_widget: widget to add to the page
		"""
		self._container.uiAdd(ui_widget.widget)

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UISplitter,
	'provides' : 'GFSplitter',
	'container': 1
}
