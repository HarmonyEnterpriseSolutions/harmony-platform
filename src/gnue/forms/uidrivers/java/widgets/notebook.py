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
# $Id: notebook.py,v 1.6 2011/10/04 13:22:51 oleg Exp $
"""
"""

from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import Notebook, Panel

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UINotebook(UIWidget):
	"""
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		UIWidget.__init__(self, event)
		self._selectedPage = None

	# -------------------------------------------------------------------------
	# Create a wx box widget
	# -------------------------------------------------------------------------

	def _create_widget_ (self, event):
		"""
		@param event: the creation-event instance carrying information like
		        container (parent-widget)

		@returns: wx widget
		"""
		self._container = self.widget = Notebook(self)
		self.getParent().addWidget(self)


	def addWidget(self, ui_widget):
		"""
		Add a given UI widget to the Notebook.

		@param ui_widget: widget to add to the page
		"""
		self._container.uiAddPage(ui_widget.widget, ui_widget._gfObject.caption, ui_widget._gfObject.description or '')


	def onPageChanged(self, container):
		assert isinstance(container, Panel), 'Container has bad type: %s' % (type(container),)
		self._selectedPage = container._uiNotePage_
		try:
			self._gfObject._event_pre_page_change_()
		finally:
			self._gfObject._event_post_page_change_()

	def _ui_get_selected_page_(self):
		return self._selectedPage

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UINotebook,
	'provides' : 'GFNotebook',
	'container': 1
}
