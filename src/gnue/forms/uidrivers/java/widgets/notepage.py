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
# $Id: notepage.py,v 1.4 2011/07/01 20:08:23 oleg Exp $
"""
"""

from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import Panel

__all__ = ["UINotepage"]

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UINotepage(UIWidget):
	"""
	"""

	def __init__(self, event):
		UIWidget.__init__(self, event)


	def _create_widget_ (self, event):
		"""
		@param event: the creation-event instance carrying information like
		        container (parent-widget)

		@returns: wx widget
		"""
		self._container = self.widget = Panel(self)
		self._container._uiNotePage_ = self
		self.getParent().addWidget(self)

	def addWidget(self, ui_widget):
		"""
		Add a given UI widget to the notepage

		@param ui_widget: widget to add to the page
		"""
		self.widget.uiAdd(ui_widget.widget)

	def _ui_select_(self):
		pass

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UINotepage,
	'provides' : 'GFNotepage',
	'container': 1
}
