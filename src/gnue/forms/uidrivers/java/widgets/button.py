#
# This file is part of GNU Enterprise.
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
# Copyright 2000-2007 Free Software Foundation
#
# FILE:
# uidrivers/html/widgets/box.py
#
# DESCRIPTION:
#
# NOTES:
#

from gnue.forms.input.GFKeyMapper import KeyMapper
from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import Button

class UIButton(UIWidget):

	def _create_widget_(self, event):
		self.widget = Button(self, self._gfObject.label, self._gfObject.description or "")
		self.getParent().addWidget(self)
		self.__menu = None
		self.__enabled = True

	def _ui_enable_(self, enabled):
		self.__enabled = enabled
		self.widget.uiEnable(enabled)

	def _ui_is_enabled_(self):
		return self.__enabled

	def _ui_set_context_menu_(self, menu, name):
		self.__menu = menu

	def onButton(self):
		self._gfObject._event_fire()

		if self.__menu:
			# show menu
			self.widget.uiPopupMenu(self.__menu)

	def onSetFocus(self):
		self._gfObject._event_set_focus()

	# navigable

	def _ui_set_focus_(self):
		self.widget.uiSetFocus()

	def onKeyPressed(self, keycode, shiftDown, ctrlDown, altDown):
		command, args = KeyMapper.getEvent(keycode, shiftDown, ctrlDown, altDown)
		if command:
			if command == 'ENTER':
				self.onButton()
			else:
				self._request(command, triggerName=args)
		
	def _ui_set_visible_(self, visible):
		self.widget.uiSetVisible(visible)

#
# Configuration data
#
configuration = {
	'baseClass'  : UIButton,
	'provides'   : 'GFButton',
}
