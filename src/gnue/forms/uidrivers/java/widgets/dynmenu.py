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
# $Id: dynmenu.py,v 1.6 2011/07/01 20:08:23 oleg Exp $

from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import Menu, MenuBar, MenuItem, PopupMenu

# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================


class UIDynMenu(UIWidget):
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

		if isinstance(event.container, (Menu, MenuBar, PopupMenu)):
			self._container = Menu(self, self._gfObject.label)
			event.container.uiAddMenu(self._container)

		# table tree and button supports _ui_set_context_menu_() interface
		elif hasattr(self._gfObject.getParent().uiWidget, '_ui_set_context_menu_'):
			self._container = PopupMenu(self, self._gfObject.label)
			self._gfObject.getParent().uiWidget._ui_set_context_menu_(self._container, self._gfObject.name)

		return self._container


	def __fillMenu(self, menu, rootId):

		for id in self._gfObject.iterChildIds(rootId):
			name = self._gfObject.formatNodeName(id)

			if self._gfObject.getChildCount(id) > 0:
				submenu = Menu(self, name)
				menu.uiAddMenu(submenu)
				self.__fillMenu(submenu, id)
			else:
				mi = MenuItem(self, name, '', False)

				menu.uiAddMenu(mi)

				# it may be (table, tree) or frame
				#uiWidget = self._gfObject.getActionSource().uiWidget

				#if uiWidget._type == 'UIForm':
				#	actionSourceWidget = uiWidget.main_window
				#else:
				#	actionSourceWidget = uiWidget.widget

				#assert actionSourceWidget

				#actionSourceWidget.Bind(wx.EVT_MENU, self.__on_menu, mi)
				self.__ids[mi.__roid__()] = id

	def _ui_revalidate_(self):
		# destroy content
		self.__ids.clear()

		self._container.uiRemoveAll()

		# refill menu
		self.__fillMenu(self._container, self._gfObject.getRootId())

		# enable menubar only if child count is > 0
		#parent = self._gfObject.getParent().uiWidget._container
		#if isinstance(parent, wx.MenuBar):
		#	for i in xrange(parent.GetMenuCount()):
		#		if parent.GetMenu(i) == self._container:
		#			parent.EnableTop(i, self._container.GetMenuItemCount() > 0)


	def _ui_enable_(self, enabled):
		self._container.uiEnable(enabled)
	
	def onMenu(self, remoteWidget):
		self._gfObject._event_node_selected(self.__ids[remoteWidget.__roid__()])
		self._gfObject._event_node_activated()


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIDynMenu,
	'provides' : 'GFDynMenu',
	'container': 1,
}
