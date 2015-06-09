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
# Copyright 2002-2007 Free Software Foundation
#
# FILE:
# GFDisplayHandler.py
#
# $Id: Cursor.py,v 1.16 2010/03/03 23:22:35 oleg Exp $
#
#
"""
The base display handler for entries that deal with cursor based
input (aka text).

This class should not be used directly.  Other handlers should
inherit from this one.
"""

__revision__ = "$Id: Cursor.py,v 1.16 2010/03/03 23:22:35 oleg Exp $"

import sys
from gnue.common import events
from gnue.common.utils import datatypes


class BaseCursor(events.EventAware):
	"""
	The base display handler for entries that deal with cursor based
	input (aka text).

	This class should not be used directly.  Other handlers should
	inherit from this one.
	"""

	def __init__(self, entry, eventHandler, subEventHandler, displayMask,
		inputMask):
		"""
		Constructor

		@param entry: The GFEntry instance associated with this handler
		@param eventHandler: The
		@param subEventHandler: The event handler this display helper will
		                        user to register it's listeners.
		"""
		events.EventAware.__init__(self, eventHandler)

		self.entry = entry            # The GFEntry that this instance will
		# support
		self.field = entry._field     # The GFField associated with that GFEntry
		self.editing = False          # Is handler in edit mode
		self.modified = False         # Have we been modified??
		self.__updating = False       # Is an updateFieldValue already running
		self.display = u""            # The current display-formatted value
		self.subEventHandler = subEventHandler

		# Cursor based vars
		self.__selection1 = None        # Start of highlight
		self.__selection2 = None        # End of highlight

		self._cursor = 0               # Cursor position

		# TODO: replace w/an event that asks the
		# TODO: UIdriver if this should happen!
		self.handleCR = sys.platform == "win32"

		self.subEventHandler.registerEventListeners( {

				# "Entry" events
				'requestKEYPRESS'     : self._addText,
				'requestCURSORLEFT'   : self._moveCursorLeft,
				'requestCURSORRIGHT'  : self._moveCursorRight,
				'requestCURSOREND'    : self._moveCursorToEnd,
				'requestCURSORHOME'   : self._moveCursorToBegin,
				'requestCURSORMOVE'   : self._moveCursor,
				'requestBACKSPACE'    : self._backspace,
				'requestDELETE'       : self._delete,
				'requestENTER'        : self.__handleENTER,
				'requestREPLACEVALUE' : self._replace_text,
				'requestTOGGLEBIT'    : self._toggle_bit,

				# Selection
				'requestSELECTWITHMOUSE' : self._selectWithMouse,
				'requestSELECTTOHOME'    : self._selectToBegin,
				'requestSELECTTOEND'     : self._selectToEnd,
				'requestSELECTLEFT'      : self._selectLeft,
				'requestSELECTRIGHT'     : self._selectRight,

				# Request for direct buffer manipulation
				'requestINSERTAT'     : self._insertTextAt,
				'requestDELETERANGE'  : self._deleteRange,
			})


	def _set_selection1(self, x):
		#rint "_set_selection1", x
		self.__selection1 = x

	def _set_selection2(self, x):
		#rint "_set_selection2", x
		self.__selection2 = x

	_selection1 = property(lambda self: self.__selection1, _set_selection1)
	_selection2 = property(lambda self: self.__selection2, _set_selection2)

	#####################
	#
	# General methods
	#

	def generateRefreshEvent(self):
		"""
		Function to emit an event that will cause forms
		to update the UI.
		"""
		assert gDebug (5, "generateRefreshEvent on %s '%s' %s" % \
				(self, self.display, self.entry))

		if (self.handleCR and type(self.display)=='str'):
			cursor=self._cursor + len(self.display[:self._cursor+1].split('\n'))-1
		else:
			cursor=self._cursor

		self.entry.uiWidget._ui_set_value_(self.display)
		self.entry.uiWidget._ui_set_selected_area_(*(self.getSelectionArea() or (cursor, cursor)))

	#####################
	#
	# Editing methods
	#

	def beginEdit(self):
		"""
		Notifies the handler that it will be doing edits.

		Called when a widget first gets focus. It places the display handler
		into edit mode, syncs the current value with the GFField associated
		with this display handler, and creates the string to display in the
		form.
		"""
		self.editing = self.field.isEditable()
		self.modified = False
		self.display = self.build_display(self.field.get_value(), self.editing)

		# multiline entries should not be selected on cirsor
		if self.entry.style != 'multiline':
			self._cursor = len(self.display)
			self.setSelectionArea(0, self._cursor)
			self.generateRefreshEvent()


	def endEdit(self):
		"""
		Called when a widget loses focus or when ENTER is hit.
		"""
		if not self.editing:
			return

		self.__updateFieldValue()

		self._selection1 = None
		self.editing = False

		if not self.entry.isCellEditor():	# ok
			# Refresh display to switch from editing format to display format.
			self.display = self.build_display(self.field.get_value(), self.editing)
			self._cursor = 0
			self._selection1 = self._selection2 = None
			self.generateRefreshEvent()


	# -------------------------------------------------------------------------
	# Return a tip displayed in the statusbar
	# -------------------------------------------------------------------------

	def get_tip(self):
		"""
		Descendands can override this method to return a tip which will be
		displayed in the statusbar if neither the entry nor the field provide
		such a tip.
		"""
		return u''



	# -------------------------------------------------------------------------
	# Text manipulation
	# -------------------------------------------------------------------------

	def _addText(self, event):

		if self._selection1 is not None:
			# If text is selected, then we will replace
			(start, end) = self.getSelectionArea()
		else:
			# Otherwise just graft the new text in place
			(start, end) = (self._cursor, self._cursor)

		self.__change_text(start, end, event.text, start + len(event.text))

	# -------------------------------------------------------------------------

	def _replace_text(self, event):
		if hasattr(event, 'position'):
			new_cursor = event.position
		else:
			new_cursor = len(event.text)

		self.__change_text(0, len(self.display), event.text, new_cursor, getattr(event, 'force', False))


	def _toggle_bit(self, event):
		assert event.activate_value
		self.__change_text(
			0,
			len(self.display),
			tobin(
				int(event.activate_value, 2) ^ int(self.display or '0', 2),
				len(event.activate_value),
			),
			len(self.display),
		)

	# -------------------------------------------------------------------------

	def _insertTextAt(self, event):

		self.__change_text(event.position, event.position, event.text,
			event.position + len(event.text))

	# -------------------------------------------------------------------------

	def _deleteRange(self, event):

		self.__change_text(event.start_pos, event.end_pos, u"",
			event.start_pos)

	# -------------------------------------------------------------------------

	def __handleENTER(self, event):

		isNewLine = gConfigForms ('EnterIsNewLine')

		if isNewLine and self.entry.style == 'multiline':
			event.text = '\n'
			self._addText(event)
			event.drop()

	# -------------------------------------------------------------------------

	def _backspace(self, event):

		# If there is a selection, delete the selected portion.
		if self._selection1 is not None:
			(start, end) = self.getSelectionArea()
			self.__change_text(start, end, u"", start)
			return

		# Can't backspace if at the beginning.
		if self._cursor == 0:
			return

		# Delete character left to the cursor.
		self.__change_text(self._cursor - 1, self._cursor, u"",
			self._cursor - 1)

		# On win32, also delete the \r along with the \n.
		if sys.platform == "win32":
			if self._cursor > 0 and self.display[self._cursor-1] == "\r":
				self.__change_text(self._cursor - 1, self._cursor, u"",
					self._cursor - 1)

	# -------------------------------------------------------------------------

	def _delete(self, event):

		# If there is a selection, delete the selected portion.
		if self._selection1 is not None:
			(start, end) = self.getSelectionArea()
			self.__change_text(start, end, u"", start)
			return

		if self._cursor == len(self.display):
			return

		# Delete character right to the cursor.
		self.__change_text(self._cursor, self._cursor + 1, u"", self._cursor)

		# On win32, also delete the \n along with the \r.
		if sys.platform == "win32":
			if self._cursor < len(self.display) \
				and self.display[self._cursor] == "\n":
				self.__change_text(self._cursor, self._cursor + 1, u"",
					self._cursor)

	# -------------------------------------------------------------------------

	def __change_text(self, start, end, text, new_cursor, force=False):
		"""
		force used only when GFEntry.setText
		"""

		# Don't accept any changes if we aren't editing.
		if not self.editing and not force:
			self.__error(u_("This field can not be changed"))
			return

		# Get the text to be added forcing to specific case if necessary.
		if self.field._lowercase:
			text = text.lower()
		elif self.field._uppercase:
			text = text.upper()

		# Check if the text is numeric if need to.
		if (self.field._numeric and self.field._block.mode == 'normal' and self.entry.style != 'dropdown'):
			for char in text:
				if not (char.isdigit() or char in ',.-'):
					self.__error(u_("This field allows numeric input only"))
					return

		# Now, assemble the new text.
		new_text = self.display[:start] + text + self.display[end:]

		# Check if max length isn't exceeded.
		if not self.field.isLookup():
			if self.field.length is not None and \
				len(new_text) > self.field.length:
				self.__error(u_("Maximum input length reached"))
				return

		# If text was added at the end, do autocompletion.
		ende = len(self.display)
		if self._selection1 or self._selection2:
			ende = min(self._selection1, self._selection2)

		if new_text.startswith(self.display[:ende]) and len(new_text) > ende:
			new_text, start_sel = self._autocomplete_(new_text, len(new_text))
			if len(new_text) > start_sel:
				new_selection = (start_sel, len(new_text))
				new_cursor = start_sel
			else:
				new_selection = (None, None)
		else:
			new_selection = (None, None)

		self.display = new_text
		self._cursor = new_cursor
		self._selection1, self._selection2 = new_selection
		self.modified = True
		self.generateRefreshEvent()

		# can be used in table to run trigger on changes before commit to field
		#self.entry.processTrigger('PRE-CHANGE')

		# Update the field. This means PRE-CHANGE and POST-CHANGE will get
		# fired now.
		self.updateFieldValue()

		# can be used in table to run trigger on changes before commit to field
		self.entry.processTrigger('POST-CHANGE')

	# -------------------------------------------------------------------------
	# Do autocompletion
	# -------------------------------------------------------------------------

	def _autocomplete_(self, new_value, new_cursor):
		"""
		Descandants can override this method to introduce autocompletion.  This
		method get's called from __change_text() if the current cursor is at
		the end of the display-string

		@returns: the new (autocompleted) value to use
		"""
		return self.field.autocomplete(new_value, new_cursor)

	# =========================================================================
	# Cursor movement functions
	# =========================================================================

	def __move_cursor(self, position, selecting=False):
		"""
		Move the cursor to the specified position optionally selecting the
		text.  After moving the cursor a refresh event will be generated.

		@param position: the position to set the cursor to
		@param selecting: boolean indicating if the text should be selected.
		"""

		if selecting:
			if self._selection1 is None:
				self._selection1 = self._cursor
		else:
			self._selection1 = None

		self._cursor = min(position, len(self.display))

		if selecting:
			self._selection2 = self._cursor

		self.generateRefreshEvent()


	# -------------------------------------------------------------------------

	def _moveCursor(self, event, selecting=False):
		"""
		Moves the cursor to the specified position optionally selecting the
		text.

		@param event: The GFEvent making the request
		@param selecting: Boolean indicating if text should be selected
		                  as part of the cursor move
		"""
		self.__move_cursor(event.position, selecting)

	# -------------------------------------------------------------------------

	def _moveCursorLeft(self, event, selecting=False):
		"""
		Moves the cursor to the left optionally selecting the text.

		@param event: The GFEvent making the request
		@param selecting: Boolean indicating if text should be selected
		                  as part of the cursor move
		"""

		if self._cursor > 0:
			self.__move_cursor(self._cursor - 1, selecting)

	# -------------------------------------------------------------------------

	def _moveCursorRight(self, event, selecting=False):
		"""
		Moves the cursor to the right optionally selecting the text.

		@param event: The GFEvent making the request
		@param selecting: Boolean indicating if text should be selected
		                  as part of the cursor move
		"""
		if self._cursor < len(self.display):
			self.__move_cursor(self._cursor + 1, selecting)

	# -------------------------------------------------------------------------

	def _moveCursorToEnd(self, event, selecting=False):
		"""
		Moves the cursor to the end optionally selecting the text.

		@param event: The GFEvent making the request
		@param selecting: Boolean indicating if text should be selected
		                  as part of the cursor move
		"""

		self.__move_cursor(len(self.display), selecting)

	# -------------------------------------------------------------------------

	def _moveCursorToBegin(self, event, selecting=False):
		"""
		Moves the cursor to the beginning optionally selecting the text.

		@param event: The GFEvent making the request
		@param selecting: Boolean indicating if text should be selected
		                  as part of the cursor move
		"""
		self.__move_cursor(0, selecting)


	# -------------------------------------------------------------------------
	# Selection Support
	# -------------------------------------------------------------------------

	def setSelectionArea(self, cursor1, cursor2):
		"""
		Set the selection area

		Starting and ending position can be passed in an any order.

		@param cursor1: A starting or ending position for the selection
		@param cursor2: A starting or ending position for the selection
		"""
		self._selection1 = min(cursor1, cursor2)
		self._selection2 = max(cursor1, cursor2)


	# -------------------------------------------------------------------------
	# Get the currently selected area
	# -------------------------------------------------------------------------

	def getSelectionArea(self):
		"""
		Return the selected area

		@return: The selected area as a tuple or None if no selection
		"""
		#rint "getSelectionArea", self._selection1, self._selection2
		if self._selection1 is None:
			return None
		else:
			return ( min(self._selection1, self._selection2),
				max(self._selection1, self._selection2) )


	# -------------------------------------------------------------------------

	def _selectWithMouse(self, event):
		"""
		Select an area of text based upon the mouse

		@param event: The GFEvent making the request
		"""
		self._selection1 = event.position1
		self._selection2 = event.position2
		if self._cursor == self._selection2:
			event.position = self._selection1
		else:
			event.position = self._selection2
		self._moveCursor(event, True)

	# -------------------------------------------------------------------------

	def _selectAll (self, event):
		"""
		Select the entire text of the entry and move the cursor to the end

		@param event: The GFEvent making the request
		"""
		self._selection1 = 0
		self._moveCursorToEnd(event, True)

	# -------------------------------------------------------------------------

	def _selectLeft(self, event):
		"""
		Move the selection cursor to the left one unit

		@param event: The GFEvent making the request
		"""
		self._moveCursorLeft(event, True)

	# -------------------------------------------------------------------------

	def _selectRight(self, event):
		"""
		Move the selection cursor to the right one unit

		@param event: The GFEvent making the request
		"""
		self._moveCursorRight(event, True)

	# -------------------------------------------------------------------------

	def _selectToBegin(self, event):
		"""
		Select from the current curson position to the beginning of the entry

		@param event: The GFEvent making the request
		"""
		self._moveCursorToBegin(event, True)

	# -------------------------------------------------------------------------

	def _selectToEnd(self, event):
		"""
		Select from the current curson position to the end of the entry

		@param event: The GFEvent making the request
		"""
		self._moveCursorToEnd(event, True)


	# -------------------------------------------------------------------------
	# Parse the display string
	# -------------------------------------------------------------------------

	def parse_display(self, display):

		if display == u"":
			return None
		else:
			return display


	# -------------------------------------------------------------------------
	# Build the display string
	# -------------------------------------------------------------------------

	def build_display(self, value, editing):
		"""
		Build the display string from the user value.
		"""

		if value is None:
			return u""
		else:
			return unicode(value)


	def updateFieldValue (self):
		"""
		Update the associated field with the current value of the display
		handler. Exceptions are ignored. This function is used to update the
		underlying field while the entry remains in editing mode (so the user
		still can correct errors).
		"""
		try:
			self.__updateFieldValue()
		except Exception, exception:
			# We don't want to raise the exception now as the user is still
			# typing. However, we archive the exception in an InvalidValueType
			# object and store that as the current field value. If any trigger
			# code now tries to access the field, the GFField.get_value will
			# raise the exception.
			self.field.set_value(datatypes.InvalidValueType(exception))


	def __updateFieldValue(self):

		# if entry in table this means not to update field value, just update ui value
		if self.entry.isCellEditor():	# ok
			return

		if not self.__updating and self.modified:
			# Make sure that this function isn't called twice recursively. This
			# would happen when the field is autoquery, so the
			# field.set_value() would cause a query to run, which in turns
			# causes an endEdit.
			self.__updating = True
			try:
				value = self.parse_display(self.display)
				self.field.set_value(value)
				self.modified = False
			finally:
				self.__updating = False


	# -------------------------------------------------------------------------
	# Helper function to display error message in status bar and beep
	# -------------------------------------------------------------------------

	def __error(self, message):

		self.entry._form.alert_message(message)
		self.generateRefreshEvent()


def tobin(x, count=8):
	"""
	Integer to binary
	Count is number of bits
	"""
	return "".join(map(lambda y: str((x>>y)&1), range(count-1, -1, -1)))
