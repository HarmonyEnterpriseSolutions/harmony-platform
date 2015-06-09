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
# $Id: notebook.py,v 1.10 2011/10/05 10:01:19 oleg Exp $
"""
"""

import wx

from gnue.forms.uidrivers.wx26.widgets import _base
from gnue.common.logic.language        import AbortRequest
from toolib.wx.mixin.XNotebookTips import XNotebookTips
from toolib import debug

__all__ = ["UINotebook"]


class NotebookWidget(XNotebookTips, wx.Notebook):

	def __init__(self, *args, **kwargs):
		super(NotebookWidget, self).__init__(*args, **kwargs)
		self._tips = []
	
	def AddPage(self, *args, **kwargs):
		tip = kwargs.pop('tip', None)
		rc = super(NotebookWidget, self).AddPage(*args, **kwargs)
		self._tips.append(tip)
		return rc
		
	def getTipValue(self, index):
		return self._tips[index]

NotebookClass = NotebookWidget

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UINotebook (_base.UIHelper):
	"""
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		_base.UIHelper.__init__(self, event)
		self.__selection = -1

	# -------------------------------------------------------------------------
	# Create a wx box widget
	# -------------------------------------------------------------------------

	def _create_widget_ (self, event):
		"""
		@param event: the creation-event instance carrying information like
		        container (parent-widget)

		@returns: wx widget
		"""
		self.__pages = []
		self._container = self.widget = NotebookWidget(event.container, -1)
		self.getParent().add_widgets(self)

		self.widget.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.__on_notebook_page_changing)
		self.widget.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__on_notebook_page_changed)

	def add_widgets(self, ui_widget):
		if self._container.AddPage(ui_widget.widget, ui_widget._gfObject.caption, tip=ui_widget._gfObject.description):
			self.__pages.append(ui_widget)
		else:
			debug.error("Failed to AddPage")

	# -------------------------------------------------------------------------
	# Indicate whether this box is vertically growable
	# -------------------------------------------------------------------------

	def is_growable(self):
		return True

	def _ui_get_selected_page_(self):
		"""
		Returns the currently selected page, or -1 if none was selected.
		"""
		return self.__pages[self.__selection] if self.__selection >= 0 else None

	def _selectPage(self, uiPage):
		self._container.ChangeSelection(self.__pages.index(uiPage))

	def __on_notebook_page_changing(self, event):
		if self.__selection != -1:
			try:
				self._gfObject._event_pre_page_change_()
			except AbortRequest:
				event.Veto()
				raise
			else:
				event.Skip()

	def __on_notebook_page_changed(self, event):
		self.__selection = event.GetSelection()
		self._gfObject._event_post_page_change_()
		event.Skip()


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UINotebook,
	'provides' : 'GFNotebook',
	'container': 1
}
