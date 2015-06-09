# GNU Enterprise Forms - wx 2.6 UI Driver - Menu widget
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
# $Id: dynmenu.py,v 1.11 2010/08/10 12:15:05 oleg Exp $

import wx

from gnue.forms.uidrivers.wx26.widgets._base import UIHelper


# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================




class UIDynMenu(UIHelper):
	"""
	Implements a menu object.
	"""

	# -------------------------------------------------------------------------
	# Create a menu widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new Menu widget.
		"""
		# Submenu
		self.__ids = {}

		widget = wx.Menu()
		self.__parentItemId = None
		self.__parentMenu = None

		if isinstance(event.container, wx.Menu):
			self.__parentItemId = event.container.AppendMenu(wx.ID_ANY, self._gfObject.label, widget).GetId()
			self.__parentMenu = event.container

		elif isinstance(event.container, wx.MenuBar):
			event.container.Append(widget, self._gfObject.label)

		# table tree and button supports _ui_set_context_menu_() interface
		elif hasattr(self._gfObject.getParent().uiWidget, '_ui_set_context_menu_'):
			self._gfObject.getParent().uiWidget._ui_set_context_menu_(widget, self._gfObject.name)

		self._container = widget
		self.__enabled = True

		return widget

	def __fillMenu(self, menu, rootId):

		for id in self._gfObject.iterChildIds(rootId):
			name = self._gfObject.formatNodeName(id)

			if self._gfObject.getChildCount(id) > 0:
				submenu = wx.Menu()
				menu.AppendMenu(-1, name, submenu)
				self.__fillMenu(submenu, id)
			else:
				mi = wx.MenuItem(menu, -1, name) #, description, kind)

				#if icon_file and not check:
				#	image = wx.Image(icon_file, wx.BITMAP_TYPE_PNG)
				#	widget.SetBitmap(image.ConvertToBitmap())

				menu.AppendItem(mi)

				# it may be (table, tree) or frame
				uiWidget = self._gfObject.getActionSource().uiWidget

				if uiWidget._type == 'UIForm':
					actionSourceWidget = uiWidget.getMainFrame()
				else:
					actionSourceWidget = uiWidget.widget

				assert actionSourceWidget

				actionSourceWidget.Bind(wx.EVT_MENU, self.__on_menu, mi)
				self.__ids[mi.GetId()] = id

	def _ui_revalidate_(self):
		# destroy content
		self.__ids.clear()
		items = list(self._container.GetMenuItems())
		items.reverse()
		for item in items:
			self._container.DestroyItem(item)

		# refill menu
		self.__fillMenu(self._container, self._gfObject.getRootId())

		# enable menubar only if child count is > 0
		parent = self._gfObject.getParent().uiWidget._container
		if isinstance(parent, wx.MenuBar):
			for i in xrange(parent.GetMenuCount()):
				if parent.GetMenu(i) == self._container:
					parent.EnableTop(i, self._container.GetMenuItemCount() > 0)

		# restore enabled state
		if not self.__enabled:
			self._ui_enable_(False)

	def _ui_enable_(self, enabled):
		self.__enabled = enabled
		if self.__parentMenu:
			self.__parentMenu.Enable(self.__parentItemId, enabled)
		else:
			for item in self._container.GetMenuItems():
				self._container.Enable(item.GetId(), enabled)

	def __on_menu(self, event):
		self._gfObject._event_node_selected(self.__ids[event.GetId()])
		self._gfObject._event_node_activated()


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIDynMenu,
	'provides' : 'GFDynMenu',
	'container': 1,
}
