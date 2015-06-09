# GNU Enterprise Forms - GF Object Hierarchy - Navigable Objects
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
# $Id: GFTabStop.py,v 1.14 2011/07/14 20:14:54 oleg Exp $

"""
Base class for all objects that can receive the keyboard focus on the UI.
"""

from gnue.common import events
from gnue.forms.input import displayHandlers
from gnue.forms.GFObjects.GFObj import GFObj
from gnue.forms.GFObjects.GFField import InvalidFieldValueError
from toolib import debug

__all__ = ['GFTabStop']

# =============================================================================
# Base class for navigable controls
# =============================================================================

class GFTabStop (GFObj):
	"""
	A base class for all GFObjects that can receive focus on the UI.

	@cvar _navigableInQuery_: If True the object can recieve the keyboard focus
	  in query mode, otherwise not
	"""

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	navigable = None

	# -------------------------------------------------------------------------
	# Class variables
	# -------------------------------------------------------------------------

	_navigableInQuery_ = True


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent, object_type):

		GFObj.__init__(self, parent, object_type)

		# The sub-event handler handles the events that are passed from the
		# GFInstance. This is the event handler that display handlers
		self.subEventHandler = events.EventController()

		self.__first_visible_record = 0
		self.__current_row_enabled = True

		# Trigger exposure
		self._validTriggers = {
			'PRE-FOCUSOUT'     : 'Pre-FocusOut',
			'POST-FOCUSOUT'    : 'Post-FocusOut',
			'PRE-FOCUSIN'      : 'Pre-FocusIn',
			'POST-FOCUSIN'     : 'Post-FocusIn',
			'ON-NEXT-ENTRY'    : 'On-Next-Entry',
			'ON-PREVIOUS-ENTRY': 'On-Previous-Entry',
		}

	# -------------------------------------------------------------------------
	# Implementation of virtual methods
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		"""
		"""

		GFObj._phase_1_init_(self)

		self._form._entryList.append(self)


	# -------------------------------------------------------------------------

	def _is_navigable_ (self, mode):
		"""
		In general an object is navigable if it is not hidden and it's
		navigable xml-attribute is set. If mode is 'query' it additionally
		depends wether an object is 'queryable' or not. If mode is 'edit' or
		'new' only objects are navigable which are not 'readonly'.
		"""

		if self.hidden:
			return False

		else:
			if mode == 'query':
				return self.navigable and self._navigableInQuery_
			else:
				return self.navigable


	# -------------------------------------------------------------------------
	# UI events (called from UIEntry/UIButton)
	# -------------------------------------------------------------------------

	def _event_set_focus(self):
		"""
		Notify the object that the user has set the focus to this object with a
		mouse click.

		This method makes sure that the logical focus follows the physical
		focus.

		In case the current focus widget vetoes the focus loss, this method
		beats the focus back to the old widget.

		In fact, this method only calls GFForm._event_focus_changed() with a
		target of this object.
		"""

		self._form._event_focus_changed(self)


	# -------------------------------------------------------------------------
	# Recalculate the visible index of an object
	# -------------------------------------------------------------------------

	def recalculate_visible(self, cur_record):
		"""
		Process a record pointer movement or a result set change for this
		entry.

		This function sets the C{_visibleIndex} property of this entry. It also
		takes care of disabling rows of this entry that are outside the actual
		number of available records, and it redisplays the contents of the
		entry as needed.

		@param cur_record: the currently active record, or -1 if there is no
		    record active currently.
		"""

		if self.hidden:
			return

		if self._form.get_focus_object() is self:
			self.ui_focus_out()

		try:
			if self.uiWidget is not None:

				if isinstance(self, GFFieldBound):
					
					# Disable current row if current record is -1
					if hasattr(self.uiWidget, '_ui_enable_'):
						self.uiWidget._ui_enable_(cur_record != -1)
					else:
						debug.error("%s has no _ui_enable_ method" % self.uiWidget)
					
					self.refresh_ui()

					# Set widgets to editable or non-editable
					self.uiWidget._ui_set_editable_(self._field.isEditable())

		finally:
			# If this was the currently focused widget, move the focus along
			if self._form.get_focus_object() is self:
				self.ui_focus_in()
				self.ui_set_focus()
				if hasattr(self, '_displayHandler') and self._displayHandler.editing:
					self._displayHandler.generateRefreshEvent()

	# -------------------------------------------------------------------------
	# Focus handling
	# -------------------------------------------------------------------------

	def focus_in(self):
		"""
		Notify the object that it has received the focus.
		"""

		self.ui_focus_in()

		self.processTrigger('PRE-FOCUSIN')
		self.processTrigger('POST-FOCUSIN')

		# Update tip
		if self.get_option('tip'):
			tip = self.get_option('tip')
		elif isinstance(self, GFFieldBound) and self._field.get_option('tip'):
			tip = self._field.get_option('tip')
		elif hasattr(self, "_displayHandler"):
			tip = self._displayHandler.get_tip()
		else:
			tip = ""

		self._form.update_tip(tip)

	# -------------------------------------------------------------------------

	def validate(self):
		"""
		Validate the object to decide whether the focus can be moved away from
		it.

		This function can raise an exception, in which case the focus change
		will be prevented.
		"""

		self.processTrigger('PRE-FOCUSOUT', ignoreAbort=False)

	# -------------------------------------------------------------------------

	def focus_out(self):
		"""
		Notify the object that it is going to lose the focus.

		The focus change is already decided at this moment, there is no way to
		stop the focus from changing now.
		"""

		self.processTrigger('POST-FOCUSOUT')

		self.ui_focus_out()


	# -------------------------------------------------------------------------
	# UI focus movement
	# -------------------------------------------------------------------------

	def ui_set_focus(self):
		"""
		Set the focus to this widget on the UI layer.

		This function is only called when the focus is set from the GF layer.
		If the user changes the focus with a mouse click, this function is not
		called because the UI focus already is on the target widget.

		So the purpose of this function is to make the UI focus follow the GF
		focus.
		"""
		#rint "ui_set_focus: Focus requested from logic", self._field
		self.uiWidget._ui_set_focus_()


	# -------------------------------------------------------------------------

	def ui_focus_in(self):
		"""
		Notify the UI widget that is is going to receive the focus.

		This function is always called, no matter whether the user requested
		the focus change via mouse click, keypress, or trigger function.

		The purpose of this function is to allow the UI widget to do things
		that always must be done when it gets the focus, like changing the
		color of the current widget, or activating the current entry in the
		grid.
		"""

		self.uiWidget._ui_focus_in_()

		# if have parent notepages, select them
		parent = self
		while parent:
			if parent._type == 'GFNotepage':
				parent.select()
			parent = parent.getParent()

	# -------------------------------------------------------------------------

	def ui_focus_out(self):
		"""
		Notify the UI widget that it has lost the focus.

		This function is always called, no matter whether the user requested
		the focus change via mouse click, keypress, or trigger function.

		The purpose of this function is to allow the UI widget to do things
		that always must be done when it loses the focus, like changing the
		color of the formerly current widget back to normal, or deactivating
		the no-longer-current entry in the grid.

		This function works better than the KILL-FOCUS event of the UI, because
		KILL-FOCUS runs too often, for example also when the dropdown is opened
		(and the focus moves from the dropdown entry to the dropdown list).
		"""

		self.uiWidget._ui_focus_out_()

		# GFTable has this method to listen when entry looses focus to end editing
		if hasattr(self.getParent(), 'ui_focus_out'):
			self.getParent().ui_focus_out()


# =============================================================================
# Base class for all widgets bound to a field
# =============================================================================

class GFFieldBound(GFTabStop):

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent, object_type):

		GFTabStop.__init__(self, parent, object_type)

		self._block = None
		self._field = None


	# -------------------------------------------------------------------------
	# Phase 1 init
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):

		GFTabStop._phase_1_init_(self)

		self._block = self.get_block()
		assert (self._block is not None), '%s has no block' % self.name

		self._block._entryList.append(self)

		self._field = self.get_field()
		self._field._entryList.append(self)

		self._formatmask  = ""
		self._inputmask   = getattr(self, 'inputmask', '')
		self._displaymask = getattr(self, 'displaymask', '')

		# Associate a display handler with this instance
		self._displayHandler = displayHandlers.factory(self,
			self._form._instance.eventController,
			self.subEventHandler,
			self._displaymask,
			self._inputmask)


	# -------------------------------------------------------------------------
	# Clipboard and selection
	# -------------------------------------------------------------------------

	def cut(self):

		if self.uiWidget is not None:
			self.uiWidget._ui_cut_()

	# -------------------------------------------------------------------------

	def copy(self):

		if self.uiWidget is not None:
			self.uiWidget._ui_copy_()

	# -------------------------------------------------------------------------

	def paste(self):

		if self.uiWidget is not None:
			self.uiWidget._ui_paste_()

	# -------------------------------------------------------------------------

	def select_all(self):

		if self.uiWidget is not None:
			self.uiWidget._ui_select_all_()

	# -------------------------------------------------------------------------
	# Refresh the user interface with the current field data
	# -------------------------------------------------------------------------

	def refresh_ui(self):

		if not self.hidden:

			# Do not execute if we were editing - would overwrite unsaved change
			if not self._displayHandler.editing:

				try:
					value = self._field.get_value()
				except InvalidFieldValueError:                   # invalid value
					value = None

				display = self._displayHandler.build_display(value, False)

				assert isinstance(display, (unicode, bool)), self._displayHandler

				self.uiWidget._ui_set_value_(display)


	def refresh_ui_editable(self):
		if not self.hidden:
			self.uiWidget._ui_set_editable_(self._field.isEditable())

	# -------------------------------------------------------------------------
	# Update the available list of choices for all uiWidgets
	# -------------------------------------------------------------------------

	def refresh_ui_choices(self, choices):
		self.uiWidget._ui_set_choices_(choices)
