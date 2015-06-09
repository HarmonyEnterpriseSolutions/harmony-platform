
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
# Boolean.py
#
# $Id: Boolean.py,v 1.2 2009/08/25 15:33:13 oleg Exp $
"""
Display handler for entries of type Boolean
"""
__revision__ = "$Id: Boolean.py,v 1.2 2009/08/25 15:33:13 oleg Exp $"

from gnue.forms.input.displayHandlers.Cursor import BaseCursor

#############################################################################
#
# Handler for Boolean types
#
class Boolean(BaseCursor):

	def __init__(self, entry, eventHandler, subEventHandler, displayMask,
		inputMask):

		self.trueValue = gConfigForms("checkboxTrue")
		self.falseValue = gConfigForms("checkboxFalse")

		self.trueValues =  ('Y', 'y', 'T', 't', '1', 'x', 'X', self.trueValue)
		self.falseValues = ('N', 'n', 'F', 'f', '0', '', ' ', self.falseValue)

		BaseCursor.__init__(self, entry, eventHandler, subEventHandler,
			displayMask, inputMask)

		# My events...
		self.subEventHandler.registerEventListeners( {
				'requestTOGGLECHKBOX' : self.handleToggleChkbox} )


	# What should a CheckBox do on a movement of the cursor ?

	def _moveCursor(self, event, selecting=False):
		pass

	def _moveCursorRight(self, selecting=False):
		pass

	def _moveCursorLeft(self, selecting=False):
		pass

	def _moveCursorToEnd(self, event, selecting=False):
		pass

	def _moveCursorToBegin(self, event, selecting=False):
		pass

	def __sanitize_value(self, value):
		if self.field._block.mode == 'query' and (value in [None, '']):
			return None

		if ("%s" % value)[:1] in self.trueValues:
			return True
		elif ("%s" % value)[:1] in self.falseValues:
			return False
		else:
			return value and True or False


	# Helpers for user events:

	# Set checkbox to boolean value
	def __set (self, value):
		if value != self.display:
			# Don't allow any changes if we aren't editing.
			if not self.editing:
				self.generateRefreshEvent()   # Reset old value on UI
				return
			self.display = value
			self.modified = True
			self.generateRefreshEvent()
			self.updateFieldValue()

	# Toggle value of checkbox
	def __toggle (self):
		allowed = [True, False]
		if self.field._block.mode == 'query':
			allowed.append(None)
		next = allowed.index(self.display) + 1
		if next == len(allowed):
			next = 0
		self.__set(allowed[next])


	# Handle requestTOGGLECHKBOX event
	def handleToggleChkbox (self, event):
		self.__toggle()


	def beginEdit(self):

		self.editing = self.field.isEditable()
		self.display = self.build_display(self.field.get_value(), self.editing)
		self.modified = False
		self._cursor = 0


	# Correctly handle requestKEYPRESS event
	def _addText(self, event):
		if event.text == ' ':
			self.__toggle ()
		elif event.text in ['0', '-']:      # TODO: add "Y" for current language
			self.__set (False)
		elif event.text in ['1', '+']:      # TODO: add "N" for current language
			self.__set (True)
		return


	def build_display(self, value, editing):
		return self.__sanitize_value(value)

	def parse_display(self, display):
		return self.__sanitize_value(display)
