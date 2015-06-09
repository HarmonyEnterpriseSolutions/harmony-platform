# GNU Enterprise Forms - GF Object Hierarchy - Button
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
# $Id: GFButton.py,v 1.16 2013/12/18 22:13:02 Oleg Exp $
"""
Logical button support
"""

# =============================================================================
# Class implementing a button
# =============================================================================
from src.gnue.forms.GFObjects import GFTabStop


class GFButton(GFTabStop):

	_navigableInQuery_ = False          # Buttons don't get focus in query mode

	description = None
	visible = True

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):

		GFTabStop.__init__(self, parent, 'GFButton')

		self.label = ""
		self.action = None

		self._validTriggers = {
			'ON-ACTION'        : 'On-Action',
			'PRE-FOCUSOUT'     : 'Pre-FocusOut',
			'POST-FOCUSOUT'    : 'Post-FocusOut',
			'PRE-FOCUSIN'      : 'Pre-FocusIn',
			'POST-FOCUSIN'     : 'Post-FocusIn',
			'ON-NEXT-ENTRY'    : 'On-Next-Entry',
			'ON-PREVIOUS-ENTRY': 'On-Previous-Entry'}

		self._triggerProperties = {
			'enabled': {
				'set': self.setEnabled,
				'get': self.isEnabled,
			},
			'visible':   {
				'set': self.triggerSetVisible, 
				'get': self.triggerGetVisible
			},
		}

	# -------------------------------------------------------------------------
	# Implementation of virtual methods
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		GFTabStop._phase_1_init_(self)

		self._block = self.get_block()
		if self._block:
			self._block._entryList.append(self)

		if self.action is not None:
			
			action = self._form._actions[self.action]
			action.register_commander(self)
			
			if not self.label:
				self.label = action.label or ''

			if not self.description:
				self.description = action.description or ''

	# -------------------------------------------------------------------------
	# Fire the trigger associated with the button from outside GF
	# -------------------------------------------------------------------------

	def _event_fire(self):
		"""
		Update the value of the current entry and execute the trigger
		associated with the button. Use this function to fire a button from the
		UI layer.
		"""

		self._form.event_begin()

		try:
			# Fire the ON-ACTION trigger
			self.processTrigger('On-Action', False)

			# Fire the action
			if self.action is not None:
				self._form._actions[self.action].run(self.get_namespace_object())
		finally:
			self._form.event_end()

	def push_default_button(self):
		if self.default:
			if self.isEnabled():
				self._form.call_after(self._event_fire)
			return True
		else:
			return False

	def setEnabled(self, enabled):
		self.uiWidget._ui_enable_(enabled)

	def isEnabled(self):
		return self.uiWidget._ui_is_enabled_()

	def update_status(self):
		"""
		called from GAction for all objects registered in action with register_commander
		"""
		self.uiWidget._ui_enable_(self._form._actions[self.action].enabled)

	# -------------------------------------------------------------------------

	def triggerSetVisible(self, visible):
		if self.visible != bool(visible):
			self.visible = bool(visible)
			self.uiWidget._ui_set_visible_(self.visible)
			
	def triggerGetVisible(self):
		return self.visible
