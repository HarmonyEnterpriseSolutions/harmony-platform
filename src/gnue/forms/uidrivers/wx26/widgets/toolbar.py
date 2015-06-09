# GNU Enterprise Forms - wx 2.6 UI Driver - Toolbar widget
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
# $Id: toolbar.py,v 1.5 2013/10/28 13:47:03 oleg Exp $

import wx

from gnue.forms.uidrivers.wx26.widgets._base import UIHelper


# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================
class MyToolBar(wx.ToolBar):

	def OnPaint(self, event=None):
		print 'PAINT'


class UIToolbar(UIHelper):
	"""
	Implements a toolbar object.
	"""

	def __init__(self, event):
		UIHelper.__init__(self, event)
		self._inits.append(self.__postinit)

	# -------------------------------------------------------------------------
	# Create a menu widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new toolbar widget.
		"""

		if self._gfObject.name == '__main_toolbar__' \
			and not self._form._features['GUI:TOOLBAR:SUPPRESS']:

			# Make sure to disable the color-remapping in windows
			wx.SystemOptions.SetOption ('msw.remap', '0')

			# Toolbar of the form
			if isinstance(self._uiForm.getMainFrame(), wx.Frame):
				self._container = self.widget = wx.ToolBar(self._uiForm.getMainFrame(), -1, style=wx.TB_FLAT)

				self._container.Bind(wx.EVT_PAINT, self.on_paint)
				self.widget.Hide()
				self.widget.SetToolBitmapSize((24, 24))

				# set to uiForm
				self._uiForm.toolBar = self.widget


	def __postinit(self):
		if self.widget:
			# This function should be called after I have added tools.
			self.widget.Realize()

	def _ui_set_overtext(self, button, text):
		print self.widget.__class__


	def on_paint(self, event):
		wx.CallAfter(self._do_paint)
		event.Skip()

	def _do_paint(self):

		dc = wx.ClientDC(self.widget)
		font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		dc.SetFont(font)

		x = 0

		buttons = [i for i in self._gfObject._children if i._type == 'GFToolButton']

		for i in xrange(self.widget.GetToolsCount()):

			tool = buttons[i].uiWidget.widget
			#tool_id = tool.GetId() if tool else None

			w = h = self.widget.GetSize()[1]
			text = buttons[i].get_overtext()
			if text:

				tw, th = dc.GetTextExtent(text)
				dc.DrawText(
					text, 
					x + (w-tw)/2,  
					(h-th)/2
				)

			x += self.widget.GetToolSize()[0] if tool else 8


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIToolbar,
	'provides' : 'GFToolbar',
	'container': 1,
}
