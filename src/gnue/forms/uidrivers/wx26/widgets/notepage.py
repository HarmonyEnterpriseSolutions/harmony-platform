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
# $Id: notepage.py,v 1.22 2012/03/13 16:36:45 oleg Exp $
"""
"""

import wx

from gnue.forms.uidrivers.wx26.widgets import _base
from src.gnue.forms.uidrivers.wx26.widgets._config import BORDER_SPACE

__all__ = ["UINotepage"]

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UINotepage (_base.UIHelper):
	"""
	"""

	def __init__(self, event):
		_base.UIHelper.__init__(self, event)
		self.widget = None
		#self._inits.append(self.__tretiaryInit)


	def _create_widget_ (self, event):
		"""
		@param event: the creation-event instance carrying information like
		        container (parent-widget)

		@returns: wx widget
		"""
		self._has_border = True
		for t in ('GFTree', 'GFTable', 'GFSplitter', 'GFNotebook', 'GFUrlResource', 'GFList'):
			if self._gfObject.findChildOfType(t, includeSelf=False, allowAllChildren=False):
				self._has_border = False
				break

		self._container = wx.Panel(event.container, -1)
		self._container.SetSizer(wx.BoxSizer())
		self.widget = self._container

		return None

	def add_widgets(self, ui_widget, border=0):
		"""
		Add a given UI widget to the notepage

		@param ui_widget: widget to add to the page
		"""
		self._container.GetSizer().Add(ui_widget.widget, 1, wx.GROW | wx.ALL, BORDER_SPACE if self._has_border else 0)
		self.getParent().add_widgets(self)

	#def __tretiaryInit(self):
	#	if self.__widget:
	#		bind_recursive(self.__widget, wx.EVT_SET_FOCUS, self.__on_set_docus)
	#	pass

	#def __on_set_docus(self, event):
	#	if self.__index is not None:
	#		if self._container.GetSelection() != self.__index:
	#			self._container.ChangeSelection(self.__index)
	#			# page header changes focus to itself so oeverride focus
	#			event.GetEventObject().SetFocus()
	#	event.Skip()

	def _ui_select_(self):
		self.getParent()._selectPage(self)
		

#def bind_recursive(window, evt, handler):
#	window.Bind(evt, handler, window)
#	for i in window.GetChildren():
#		bind_recursive(i, evt, handler)

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UINotepage,
	'provides' : 'GFNotepage',
	'container': 1
}
