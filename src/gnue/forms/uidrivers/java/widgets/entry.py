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
# uidrivers/html/widgets/entry.py
#
# DESCRIPTION:
#
# NOTES:
#
import weakref

from gnue.forms.input.GFKeyMapper import KeyMapper
from gnue.common.datasources.access import ACCESS
from _base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import (
	EntryToggleButton,	# abstract, for isinstance
	EntryCheckbox
)


EntryBitcheckbox = EntryCheckbox


class UIEntry(UIWidget):

	def _create_widget_(self, event):
		self.__text = None

		klass = eval("Entry" + self._gfObject.style.capitalize())

		self.widget = klass(self, self._gfObject.label or "", self._gfObject.getDescription(), self._gfObject.getAlign())

		self.getParent().addWidget(self)

	def addWidget(self, entryButton):
		self.widget.uiAddWidget(entryButton.widget)

	# ---------------------------------------------------------------------------
	# Enable/disable this entry
	# ---------------------------------------------------------------------------

	def _ui_enable_(self, enabled):
		self.widget.uiEnable(enabled)

	# ---------------------------------------------------------------------------
	# Set the value of a widget
	# ---------------------------------------------------------------------------

	def _ui_set_value_(self, value):
		if isinstance(value, basestring):
			self.__text = value

		if self._gfObject.style == 'bitcheckbox':
			value = bool(int(value or '0', 2) & int(self._gfObject.activate_value, 2))
		if self._gfObject.style == 'radiobutton':
			if self._gfObject._field.datatype == 'boolean':
				activate_value = self._gfObject._displayHandler.parse_display(self._gfObject.activate_value)
			else:
				activate_value = self._gfObject.activate_value
			value = (value == activate_value)

		if isinstance(self.widget, EntryToggleButton):
			self.widget.uiSetText('1' if value else '0')
		else:
			self.widget.uiSetText(value)

	# ---------------------------------------------------------------------------
	# Set "editable" status for this widget
	# ---------------------------------------------------------------------------

	def _ui_set_editable_(self, editable):
		"""
		grey out entry, make readonly but copyable
		"""
		self.widget.uiSetEditable(editable)

	def _ui_set_visible_(self, visible):
		self.widget.uiSetVisible(visible)

	# ---------------------------------------------------------------------------
	# set the selected area
	# ---------------------------------------------------------------------------

	def _ui_set_selected_area_(self, selection1, selection2):
		# TODO: avoid if
		if not isinstance(self.widget, EntryToggleButton):
			self.widget.uiSetSelectedArea(selection1, selection2)

	# ---------------------------------------------------------------------------
	# Update the list of allowed values on a combo or list widget
	# ---------------------------------------------------------------------------

	def _ui_set_choices_(self, choices):
		self.widget.uiSetChoices(choices)

	# ---------------------------------------------------------------------------
	# Focus
	# ---------------------------------------------------------------------------

	def _ui_set_focus_(self):
		self.widget.uiSetFocus()

	# ---------------------------------------------------------------------------
	# CALLBACK EVENTS
	#

	def onKeyPressed(self, keycode, shiftDown, ctrlDown, altDown):
		#rint "entry __on_keypress: code=", event.GetKeyCode()

		# disable any key navigation when entry in editor mode
		# do it on client
		#if self._gfObject.isCellEditor():	# ok, TODO: not send this event to server at all
		#	return

		command, args = KeyMapper.getEvent(keycode, shiftDown, ctrlDown, altDown)
		#rint "COMMAND:", command, args

		if command == 'ENTER':
			if self._gfObject._event_push_default_button():
				#rint 'default button accepted', self.widget
				return
			else:
				#rint 'default button not found', self.widget
				pass

		# accept only [wx.WXK_TAB, wx.WXK_RETURN, wx.WXK_UP, wx.WXK_DOWN, wx.WXK_ESCAPE]
		# for multiline accept only [wx.WXK_TAB, wx.WXK_ESCAPE] 

		if command:
			#rint "PROCESS COMMAND", command
			if command == 'NEWLINE':
				self._request('KEYPRESS', text='\n')
			else:
				self._request(command, triggerName=args)

	def onTextChanged(self, text, position):
		self._request('REPLACEVALUE', text=text, position=position)
		
	def onChecked(self, value):
		if self._gfObject.style == 'bitcheckbox':
			self._request('TOGGLEBIT', activate_value=self._gfObject.activate_value)
		elif self._gfObject.style == 'radiobutton':
			# allways true, client does not send false
			if value:
				if self._gfObject._field.datatype == 'boolean':
					activate_value = self._gfObject._displayHandler.parse_display(self._gfObject.activate_value)
					if activate_value != self._gfObject._field.get_value():
						self._request('TOGGLECHKBOX')
				else:
					self._request('REPLACEVALUE', text=self._gfObject.activate_value)

		else:
			self._request('TOGGLECHKBOX')

	def onSetFocus(self):
		try:
			self._gfObject._event_set_focus()
		except weakref.ReferenceError:
			# WORKAROUND FOR #89. Weakly referenced object does not exists.
			pass

	def onStopCellEditing(self, value):
		# this check fixes not editable boolean table entry swith from null to False
		if self._gfObject._field.hasAccess(ACCESS.WRITE):

			if isinstance(self.widget, EntryToggleButton):
				value = bool(int(value))

			#if self._gfObject.style == 'bitcheckbox':
			#	value = bool(int(value or '0', 2) & int(self._gfObject.activate_value, 2))
			#if self._gfObject.style == 'radiobutton':
			#	value = (value == self._gfObject.activate_value)

			value = self._gfObject._displayHandler.parse_display(value)
			#rint '>>> new value', repr(value), ', was', repr(self._gfObject._field.get_value())
			self._gfObject._field.set_value(value)

	def onCustomEditor(self):
		self._gfObject._event_on_custom_editor()
		
	# ---------------------------------------------------------------------------

	def _ui_get_text_(self):
		return self.__text

	def _ui_set_text_(self, text):
		self._request('REPLACEVALUE', text=text, position=len(text), force=True)

	# ---------------------------------------------------------------------------
	# DEPRECATED
	#

	def _ui_copy_(self):
		pass

	def _ui_paste_(self):
		pass

	def _ui_select_all_(self):
		pass


configuration = {
	'baseClass'  : UIEntry,
	'provides'   : 'GFEntry',
}



