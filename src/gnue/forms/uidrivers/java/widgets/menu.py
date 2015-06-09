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
# $Id: menu.py,v 1.6 2011/07/01 20:08:23 oleg Exp $

from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import MenuBar, Menu, PopupMenu

# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================

class UIMenu(UIWidget):
	"""
	Implements a menu object.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		UIWidget.__init__(self, event)

	# -------------------------------------------------------------------------
	# Create a menu widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new Menu widget.
		"""
		if self._gfObject.name == '__main_menu__':

			if not self._form._features['GUI:MENUBAR:SUPPRESS'] and not self._uiForm.isEmbeded() and self._form.style != 'dialog':

				assert self._uiForm.menuBar is None
				# We do not set the menubar using main_window.SetMenuBar() here,
				# because on OS X some menu items will get rearranged (like Quit,
				# About, Help-menu ...).  This rearrangement won't work if the
				# menubar is set before the items are created.
				self._container = self._uiForm.menuBar = MenuBar(self)

		elif event.container is not None:

			# Submenu
			self._container = Menu(self, self._gfObject.label or '')

			if isinstance(event.container, (MenuBar, Menu)):
				event.container.uiAddMenu(self._container)


		elif hasattr(self._gfObject.getParent().uiWidget, '_ui_set_context_menu_'):

			self._container = PopupMenu(self, self._gfObject.label or '')

			# table tree and button supports _ui_set_context_menu_() interface
			self._gfObject.getParent().uiWidget._ui_set_context_menu_(self._container, self._gfObject.name)

		return self._container


	#def onPostInit(self):
		"""
		setups key accelerators for context menu
		must run after menuitems created
		"""

		#parentUiWidget = self._gfObject.getParent().uiWidget
		#
		#if hasattr(parentUiWidget, '_ui_set_context_menu_'):
		#
		#	accelerators = []
		#
		#	# for context menu i should connect all accelerators manually @oleg
		#	for mi in self._gfObject.findChildrenOfType('GFMenuItem', includeSelf=False, allowAllChildren=True):
		#		hotkey = getattr(mi, 'hotkey', '')
		#		if hotkey:
		#			accel = wx.GetAccelFromString("dummy\t" + hotkey)
		#			if accel:
		#				accel.Set(accel.GetFlags(), accel.GetKeyCode(), mi.uiWidget.getId())
		#				accelerators.append(accel)

		#	if accelerators:
		#		aTable = wx.AcceleratorTable(accelerators)
		#		if parentUiWidget.widget.GetAcceleratorTable() != aTable:
		#			parentUiWidget.widget.SetAcceleratorTable(aTable)

		#super(UIMenu, self).onPostInit()


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIMenu,
	'provides' : 'GFMenu',
	'container': 1,
}
