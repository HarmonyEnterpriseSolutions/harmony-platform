# GNU Enterprise Forms - wx 2.6 UI Driver - ToolButton widget
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
# $Id: toolbutton.py,v 1.6 2013/10/28 13:47:03 oleg Exp $

import wx

from gnue.forms.uidrivers.wx26.widgets._base import UIHelper


# =============================================================================
# UIToolButton
# =============================================================================

class UIToolButton(UIHelper):
	"""
	Implements a toolbar button object.
	"""

	# -------------------------------------------------------------------------
	# Create a menu item widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new toolbar button widget.
		"""

		# These are the relevant parameters
		icon_file = self._gfObject._get_icon_file(size="24x24", format="png")
		label = self._gfObject.label
		description = self._gfObject.description
		check = (self._gfObject.action_off is not None)

		if event.container is not None:
			if label is not None:
				if check:
					kind = wx.ITEM_CHECK
				else:
					kind = wx.ITEM_NORMAL

				if icon_file:
					image = wx.Image(icon_file, wx.BITMAP_TYPE_PNG)
				else:
					assert 0, 'No icon found: %s' % self._gfObject.icon
				try:
					widget = event.container.AddLabelTool(wx.ID_ANY, label, image.ConvertToBitmap(), kind=kind, shortHelp=label, longHelp=(description or u""))

					wx.EVT_TOOL(event.container, widget.GetId(), self.__on_tool)
				except:
					print "! failed to load image:", icon_file
					raise
			else:
				widget = None
				event.container.AddSeparator()
		else:
			# TOOLBAR:SUPPRESS was set
			widget = None

		self.widget = widget

		return widget


	# -------------------------------------------------------------------------
	# Events
	# -------------------------------------------------------------------------

	def __on_tool(self, event):
		self._gfObject._event_fire()


	# -------------------------------------------------------------------------
	# Check/uncheck menu item
	# -------------------------------------------------------------------------

	def _ui_switch_on_(self):
		if self.widget is not None:
			# FIXME: why doesn't the next line work?
			# self.widget.SetToggle(True)
			self.widget.GetToolBar().ToggleTool(self.widget.GetId(), True)

	# -------------------------------------------------------------------------

	def _ui_switch_off_(self):
		if self.widget is not None:
			# FIXME: why doesn't the next line work?
			# self.widget.SetToggle(False)
			self.widget.GetToolBar().ToggleTool(self.widget.GetId(), False)


	# -------------------------------------------------------------------------
	# Enable/disable menu item
	# -------------------------------------------------------------------------

	def _ui_enable_(self, enabled):
		if self.widget is not None:
			# FIXME: why doesn't the next line work?
			# self.widget.Enable(True)
			self.widget.GetToolBar().EnableTool(self.widget.GetId(), enabled)

	def _ui_set_overtext(self, text):
		self._gfObject.getParent().uiWidget.widget.Refresh()
		

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIToolButton,
	'provides' : 'GFToolButton',
	'container': False
}
