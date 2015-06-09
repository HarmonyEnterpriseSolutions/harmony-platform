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
# $Id: menu.py,v 1.11 2009/08/06 16:04:45 oleg Exp $

import wx

from gnue.forms.uidrivers.wx26.widgets._base import UIHelper


# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================

class UIMenu(UIHelper):
	"""
	Implements a menu object.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		UIHelper.__init__(self, event)
		self._inits.append(self.__postinit)

	# -------------------------------------------------------------------------
	# Create a menu widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new Menu widget.
		"""
		if self._gfObject.name == '__main_menu__':

			if not self._form._features['GUI:MENUBAR:SUPPRESS'] \
				and not self._uiForm.isEmbeded() \
				and isinstance(self._uiForm.getMainFrame(), wx.Frame):

				assert self._uiForm.menuBar is None
				# We do not set the menubar using getMainFrame().SetMenuBar() here,
				# because on OS X some menu items will get rearranged (like Quit,
				# About, Help-menu ...).  This rearrangement won't work if the
				# menubar is set before the items are created.
				self._container = self._uiForm.menuBar = wx.MenuBar()

		elif event.container is not None or hasattr(self._gfObject.getParent().uiWidget, '_ui_set_context_menu_'):

			# Submenu or popup menu
			self._container = wx.Menu()

			# On OS X the 'Help' and 'Window' menus will be added automatically
			# to the menubar.  To avoid having two 'Help' menus we have to name
			# the help-menu '&Help'.  This will be translated to the current
			# language automatically then.
			if self._gfObject.name == '__help__' and 'wxMac' in wx.PlatformInfo:
				lb = '&Help'
			else:
				lb = self._gfObject.label

			if isinstance(event.container, wx.Menu):
				event.container.AppendMenu(wx.ID_ANY, lb, self._container)

			elif isinstance(event.container, wx.MenuBar):
				event.container.Append(self._container, lb)

			# table tree and button supports _ui_set_context_menu_() interface
			elif hasattr(self._gfObject.getParent().uiWidget, '_ui_set_context_menu_'):
				self._gfObject.getParent().uiWidget._ui_set_context_menu_(self._container, self._gfObject.name)

		return self._container


	def __postinit(self):
		"""
		setups key accelerators for context menu
		must run after menuitems created
		"""

		parentUiWidget = self._gfObject.getParent().uiWidget

		if hasattr(parentUiWidget, '_ui_set_context_menu_'):

			accelerators = []

			# for context menu i should connect all accelerators manually @oleg
			for mi in self._gfObject.findChildrenOfType('GFMenuItem', includeSelf=False, allowAllChildren=True):
				hotkey = getattr(mi, 'hotkey', '')
				if hotkey:
					accel = wx.GetAccelFromString("dummy\t" + hotkey)
					if accel:
						accel.Set(accel.GetFlags(), accel.GetKeyCode(), mi.uiWidget.getId())
						accelerators.append(accel)

			if accelerators:
				aTable = wx.AcceleratorTable(accelerators)
				if parentUiWidget.widget.GetAcceleratorTable() != aTable:
					parentUiWidget.widget.SetAcceleratorTable(aTable)


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIMenu,
	'provides' : 'GFMenu',
	'container': 1,
}
