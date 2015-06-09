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
# $Id: GFEntryButton.py,v 1.1 2009/08/28 19:04:29 oleg Exp $
"""
Logical button support
"""

# =============================================================================
# Class implementing a button
# =============================================================================
from src.gnue.forms.GFObjects import GFObj


class GFEntryButton(GFObj):

	_navigableInQuery_ = False          # Buttons don't get focus in query mode

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):

		GFObj.__init__(self, parent, 'GFEntryButton')

		self.label = ""
		self.action = None

		self._validTriggers = {
			'ON-ACTION'        : 'On-Action',
		}

		self._triggerProperties = {
			'enabled': {
				'set': self.setEnabled,
				'get': self.isEnabled,
			},
		}

	# -------------------------------------------------------------------------
	# Implementation of virtual methods
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		GFObj._phase_1_init_(self)

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

	def setEnabled(self, enabled):
		self.uiWidget._ui_enable_(enabled)

	def isEnabled(self):
		return self.uiWidget._ui_is_enabled_()
