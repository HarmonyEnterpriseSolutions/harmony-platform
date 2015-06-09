# GNU Enterprise Forms - GF Object Hierarchy - Entry Objects
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
# $Id: GFEntry.py,v 1.40 2015/03/12 17:39:28 oleg Exp $

"""
The primary data entry widget in forms
"""
from src.gnue.forms.GFObjects import XNavigationDelegate

from src.gnue.forms.GFObjects.GFTabStop import GFFieldBound

# =============================================================================
# Class for data entry widgets
# =============================================================================

class GFEntry(GFFieldBound):

	visible = True
	
	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):

		GFFieldBound.__init__(self, parent, 'GFEntry')

		# Default attributes (these may be replaced by parser)
		self.style = "default"
		self.label = None

		# Trigger exposure
		self._validTriggers.update({
			'ON-PICKER'        : 'On-Picker',
			'POST-CHANGE'      : 'Post-Change', # in table change not goes to logic until editing finished
			'ON-CUSTOMEDITOR'  : 'On-CustomEditor',
		})

		self._triggerFunctions = {
			'set': {'function': self.triggerSetValue},
			'get': {'function': self.getValue},

			'getField'  : { 'function' : lambda: self._field.get_namespace_object() },
			'getText'   : { 'function' : self.getText },
			'setText'   : { 'function' : self.setText },
			'isCellEditor' : { 'function' : self.isCellEditor },
		}

		self._triggerSet = self.triggerSetValue
		self._triggerGet = self.getValue

		self._triggerProperties = {
			'value':    {'set': self.triggerSetValue,
				'get': self.getValue},
			'visible':   {'set': self.triggerSetVisible,
				'get': self.triggerGetVisible},
			'navigable':{'set': self.triggerSetNavigable,
				'get': self.triggerGetNavigable},
		}


	# -------------------------------------------------------------------------
	# Phase I init
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		"""
		On Phase 1 initialization add the entry to the owning blocks' entry
		list as well as to the pages' field list.
		"""

		GFFieldBound._phase_1_init_(self)

		# Select "auto" style
		if self.style == 'auto':
			if self._field.isLookup():
				self.style = 'dropdown'
			elif self._field.datatype == 'boolean':
				self.style = 'checkbox'
			elif self._field.datatype in ('date', 'datetime'):
				self.style = 'datepicker'
			else:
				self.style = 'default'

		# Have a look wether the entry will be navigable or not
		#if self.style == 'label':
		#    self.navigable = False

		if self.picker_text_minlength >= 0:
			self.associateTrigger('POST-CHANGE', self.__on_trigger_picker_post_change)

	def __on_trigger_picker_post_change(__self, self):
		popup = __self.findChildOfType("GFPopupWindow")
		if popup:
			if __self._field.isLookup() and not self.isCellEditor() and self.getField().isValueValid():
				popup.popdown()
			else:
				if self.isCellEditor():
					text = self.getText()
				else:			
					# get user value
					if self.getField().isValueValid():
						text = __self._field.get_value()
					else:
						#assert 0, "TODO: get invalid value as text"
						text = self.getText()

				if text and len(text) > __self.picker_text_minlength:
					popup.popup()
				else:
					popup.popdown()
					
	# -------------------------------------------------------------------------
	# Implementation of virtual methods
	# -------------------------------------------------------------------------

	def _is_navigable_(self, mode):
		return self.navigable and self._block.navigable and self.visible


	# -------------------------------------------------------------------------
	# Indicate whether this widget makes use of the separate label column
	# -------------------------------------------------------------------------

	def hasLabel(self):
		return self.label is not None and self.style not in ('checkbox', 'bitcheckbox', 'radiobutton')

	# =========================================================================
	# Trigger functions
	# =========================================================================

	def getValue(self, *args, **parms):

		return self._field.getValue(*args, **parms)

	# -------------------------------------------------------------------------

	def triggerSetValue(self, *args, **parms):

		return self._field.triggerSetValue(*args, **parms)

	# -------------------------------------------------------------------------

	def triggerSetVisible(self, visible):
		if self.visible != bool(visible):
			self.visible = bool(visible)
			self.uiWidget._ui_set_visible_(self.visible)

	# -------------------------------------------------------------------------

	def triggerGetVisible(self):

		return self.visible

	# -------------------------------------------------------------------------

	def triggerSetNavigable(self, value):

		self.navigable = bool(value)

	# -------------------------------------------------------------------------

	def triggerGetNavigable(self):

		return self.navigable


	# -------------------------------------------------------------------------
	# Begin/end editing mode for this entry
	# -------------------------------------------------------------------------

	def beginEdit(self):
		#rint "beginEdit:", self
		self._displayHandler.beginEdit()

	# -------------------------------------------------------------------------

	def endEdit(self):
		#rint "endEdit:", self
		self._displayHandler.endEdit()
		# TODO: fix workaround to end editing in table
		if self.isCellEditor():					# ok
			nd = self.getNavigationDelegate()
			if nd and nd.isNavigationDelegationEnabled():
				nd.ui_focus_out()

	def isCellEditor(self):
		"""
		return parent object is navigation delegate and it is cell editable
		assuming than if object cell editable it has entried as direct children, e.g. GFTable
		"""
		parent = self.getParent()
		return parent.isCellEditable() if isinstance(parent, XNavigationDelegate) else False

	def getNavigationDelegate(self):
		"""
		if entry has navigation delegate
		"""
		parent = self.getParent()
		while parent:
			if isinstance(parent, XNavigationDelegate):
				return parent
			parent = parent.getParent()
		return None

	def getInputMask(self):
		return getattr(self, 'inputmask', None) or getattr(self._field, 'inputmask', None)

	def _event_popup(self):
		self._field._block._focus_out()
		self.processTrigger('ON-PICKER')
		self._field._block.focus_in()

	def _event_push_default_button(self):
		"""
		returns False if no default button
		"""
		if hasattr(self.getParent(), '_event_push_default_button'):
			return self.getParent()._event_push_default_button()
		else:
			return False

	def _event_on_custom_editor(self):
		self.processTrigger('ON-CUSTOMEDITOR')
		self._field.processTrigger('ON-CUSTOMEDITOR')

	def getText(self):
		"""
		returns text directly from displayHandler from currently edited entry
		"""
		return self.uiWidget._ui_get_text_()

	def setText(self, text):
		"""
		sets text to currently edited entry
		"""
		return self.uiWidget._ui_set_text_(text)

	# =========================================================================
	# GFTabStop overrided
	# =========================================================================
	def ui_set_focus(self):
		"""
		If isCellEditor, redirect to GFTable.ui_set_selected_entry
		"""
		nd = self.getNavigationDelegate()
		if nd and nd.isNavigationDelegationEnabled():
			nd.ui_set_focused_entry(self)
		else:
			super(GFEntry, self).ui_set_focus()

	def getDescription(self):
		"""
		return entry description or field description or entry label
		"""
		return (
			getattr(self, 'description', '')
			or getattr(self._field, 'description','')
			#or getattr(self, 'label', None)
			or ''
		)

	# align like in numpad, default is 4
	ALIGN = {
		'date'		: 5,
		'datetime'	: 5,
		'time'		: 5,
		'number'	: 6,
		'boolean'	: 5,
	}
	
	def getAlign(self):
		if self._field.isLookup():
			return 4
		else:
			return self.ALIGN.get(self._field.datatype, 4)
