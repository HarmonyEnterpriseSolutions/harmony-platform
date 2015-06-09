# GNU Enterprise Forms - wx 2.6 UI Driver - MenuItem widget
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
# $Id: menuitem.py,v 1.8 2009/08/06 16:04:46 oleg Exp $

import wx

from gnue.forms.uidrivers.wx26.widgets._base import UIHelper


# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================

class UIMenuItem(UIHelper):
	"""
	Implements a menu item object.
	"""

	# -------------------------------------------------------------------------
	# Create a menu item widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new MenuItem widget.
		"""
		if event.container:
			# These are the relevant parameters
			icon_file = self._gfObject._get_icon_file(size="16x16", format="png")
			label = self._gfObject.label
			description = self._gfObject.description
			hotkey = self._gfObject.hotkey
			check = (self._gfObject.action_off is not None)

			if check:
				kind = wx.ITEM_CHECK
			else:
				kind = wx.ITEM_NORMAL

			if label is not None:
				if hotkey is not None:
					text = label + u"\t" + hotkey
				else:
					text = label

				# On OS X the menu items with the special IDs wx.ID_ABOUT,
				# wx.ID_EXIT and wx.ID_PREFERENCES will get rearranged into the
				# Application menu (according to Apples HIG).  On all other
				# platforms it does nothing special with these menu items.
				if self._gfObject.name == '__show_about__':
					mid = wx.ID_ABOUT

				elif self._gfObject.name == '__close__':
					mid = wx.ID_EXIT
				else:
					mid = wx.ID_ANY

				widget = wx.MenuItem(event.container, mid, text,
					description or u"", kind)

				if icon_file and not check:
					image = wx.Image(icon_file, wx.BITMAP_TYPE_PNG)
					widget.SetBitmap(image.ConvertToBitmap())

				# it may be (table, tree) or frame
				uiWidget = self._gfObject.getActionSource().uiWidget

				if uiWidget._type == 'UIForm':
					actionSourceWidget = uiWidget.getMainFrame()
				else:
					actionSourceWidget = uiWidget.widget

				assert actionSourceWidget

				actionSourceWidget.Bind(wx.EVT_MENU, self.__on_menu, widget)

				event.container.AppendItem(widget)
			else:
				widget = None
				event.container.AppendSeparator()

			self.widget = widget


	# -------------------------------------------------------------------------
	# Events
	# -------------------------------------------------------------------------

	def __on_menu(self, event):
		self._gfObject._event_fire()


	# -------------------------------------------------------------------------
	# Check/uncheck menu item
	# -------------------------------------------------------------------------

	def _ui_switch_on_(self):
		if self.widget is not None and self.widget.IsCheckable():
			self.widget.Check(True)

	# -------------------------------------------------------------------------

	def _ui_switch_off_(self):
		if self.widget is not None and self.widget.IsCheckable():
			self.widget.Check(False)


	# -------------------------------------------------------------------------
	# Enable/disable menu item
	# -------------------------------------------------------------------------

	def _ui_enable_(self, enabled):
		if self.widget is not None:
			self.widget.Enable(enabled)

	def getId(self):
		return self.widget.GetId()


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIMenuItem,
	'provides' : 'GFMenuItem',
	'container': False
}
