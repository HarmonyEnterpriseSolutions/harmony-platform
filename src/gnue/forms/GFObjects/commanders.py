# GNU Enterprise Forms - Menus and Toolbars
#
# Copyright 2000-2007 Free Software Foundation
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
# $Id: commanders.py,v 1.9 2013/10/28 13:46:54 oleg Exp $

"""
Classes for all the visible objects that call actions: Menus and Toolbars
"""

import os.path
from gnue import paths
from gnue.forms.GFObjects.GFObj import GFObj
from gnue.common.apps import i18n


__all__ = ['GFMenu', 'GFMenuItem', 'GFToolbar', 'GFToolButton']


# =============================================================================
# Abstract parent class for all objects that can fire an action
# =============================================================================

class GFCommander(GFObj):
	"""
	Any object that is bound to an action.

	A commander can either be linked to a single action, in which case the
	action is executed whenever the commander is fired, or it can be linked to
	an L{action} and an L{action_off}, in which case the commander is a toggle
	and the action is executed when the toggle is switched on and the
	action_off is fired when the toggle is switched off.

	For toggles, the action determines icon, label, and description, rather
	than the action_off.
	"""

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	name        = None
	icon        = None
	label       = None
	description = None
	action      = None
	action_off  = None
	state       = False
	enabled     = True


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent, object_type):
		"""
		Create a GFCommander instance.
		"""
		GFObj.__init__(self, parent, object_type)

		#: L{common.logic.usercode.GAction} object linked to this commander.
		self.__action = None

		#: L{common.logic.usercode.GAction} object linked to the "off"
		#: operation of the commander.
		self.__action_off = None

		#: Whether the UI widget is enabled or not. The UIxxx implementations
		#: read this variable on initialisation; if at some point the UI
		#: widgets are initialized with parameters, this variable can be made
		#: private.
		self._ui_enabled = False

		self._inits.append(self._phase_2_init_)

		# Trigger support
		_triggerProperties = {
			'state': {
				'get': self.__trigger_get_state,
				'set': self.__trigger_set_state},
			'enabled': {
				'get': self.__trigger_get_enabled,
				'set': self.__trigger_set_enabled}}


	# -------------------------------------------------------------------------
	# Phase 2 initialization
	# -------------------------------------------------------------------------

	def _phase_2_init_(self):

		# This must run after phase 1 init because the actions register at the
		# form in phase 1 init, and that must be done when this runs.

		# Link to action object
		if self.action is not None:
			self.__action = self._form._actions[self.action]

			# Register ourselves to the action so we get notified of action
			# enables/disables
			self.__action.register_commander(self)

			# Copy icon, label and description from action object if not set
			# here. We can safely do this here because designer doesn't run
			# this code.
			if self.icon is None:
				self.icon = self.__action.icon
			if self.label is None:
				self.label = i18n.getCatalog('forms').ugettext(self.__action.label)
			if self.description is None:
				self.description = i18n.getCatalog('forms').ugettext(self.__action.description)

			# Set a variable to determine whether the UI widget should be
			# enabled or not.
			if self.action_off is None or not self.state:
				self._ui_enabled = self.enabled and self.__action.enabled

		# Link to action_off object
		if self.action_off is not None:
			self.__action_off = self._form._actions[self.action_off]

			# Register ourselves to the action so we get notified of action
			# enables/disables
			self.__action_off.register_commander(self)

			# Set a variable to determine whether the UI widget should be
			# enabled or not.
			if self.state:
				self._ui_enabled = self.enabled and self.__action_off.enabled


	# -------------------------------------------------------------------------
	# Trigger functions
	# -------------------------------------------------------------------------

	def __trigger_get_state(self):
		return self.state

	# -------------------------------------------------------------------------

	def __trigger_set_state(self, value):
		if value != self.state:
			self.__fire()

	# -------------------------------------------------------------------------

	def __trigger_get_enabled(self):
		return self.enabled

	# -------------------------------------------------------------------------

	def __trigger_set_enabled(self, value):
		self.enabled = value
		self.update_status()


	# -------------------------------------------------------------------------
	# User Events
	# -------------------------------------------------------------------------

	def _event_fire(self):
		"""
		Fire the commander.

		This function is executed when the user clicks on the menu item or the
		toolbar button.

		If the commander is bound to a single action, this action is executed.

		If the commander is bound to two actions (i.e. it is a toggle), the
		state of the toggle is changed, and the corresponding action is
		executed.
		"""

		self._form.event_begin()
		try:
			self.__fire()
		finally:
			self._form.event_end()


	# -------------------------------------------------------------------------
	# Helper functions to be used by the UI implementations
	# -------------------------------------------------------------------------

	def _get_icon_file(self, size="32x32", format="png"):
		"""
		Return the file with the icon bound to this action.

		@param size: Image size, like "16x16" or "24x24".
		@param format: Image format, like "png" or "bmp".
		@return: Filename.
		"""

		if self.icon is None:
			return None

		iconset = gConfigForms('IconSet')
		if iconset == 'auto':
			iconset = forms_ui.default_iconset
		file = "%s-%s.%s" % (self.icon, size, format)

		# First check the directory where this gfd was found.
		dir = os.path.dirname(self._url)
		result = os.path.join(dir, iconset, file)
		if os.path.isfile(result):
			return result
		result = os.path.join(dir, file)
		if os.path.isfile(result):
			return result

		# Then check the standard images directory (for compatibility).
		# FIXME: Move standard icons to share/forms/default/<iconset> and
		# remove this part.
		dir = os.path.join(paths.data, 'share', 'gnue', 'images', 'forms')
		result = os.path.join(dir, iconset, file)
		if os.path.isfile(result):
			return result
		result = os.path.join(dir, file)
		if os.path.isfile(result):
			return result

		return None


	# -------------------------------------------------------------------------
	# Update enabled/disabled status
	# -------------------------------------------------------------------------

	def update_status(self):
		"""
		Update the enabled/disabled status of the commander.

		The attached action calls this function whenever its enabled/disabled
		status changes, so the commander can adjust the status of the user
		interface element.
		"""

		# For toggle commanders, the state can implicitly be changed by
		# enabling one of the actions and disabling the other one.
		if self.__action is not None and self.__action_off is not None:
			if self.__action.enabled and not self.__action_off.enabled:
				if self.state:
					self.state = False
					if self.uiWidget is not None:
						self.uiWidget._ui_switch_off_()
			if self.__action_off.enabled and not self.__action.enabled:
				if not self.state:
					self.state = True
					if self.uiWidget is not None:
						self.uiWidget._ui_switch_on_()

		if self.state and self.__action_off is not None:
			new_ui_enabled = self.enabled and self.__action_off.enabled
		elif self.__action is not None:
			new_ui_enabled = self.enabled and self.__action.enabled
		else:
			new_ui_enabled = False

		if new_ui_enabled != self._ui_enabled:
			if self.uiWidget is not None:
				self.uiWidget._ui_enable_(new_ui_enabled)
			self._ui_enabled = new_ui_enabled


	# -------------------------------------------------------------------------
	# Fire the commander
	# -------------------------------------------------------------------------

	def __fire(self):

		try:
			if self.state and self.__action_off is not None:
				try:
					self.__action_off.run(self.getActionSource().get_namespace_object())
				except Exception:
					self.uiWidget._ui_switch_on_()
					raise
				self.state = False
				if self.uiWidget is not None:
					self.uiWidget._ui_switch_off_()
			elif self.__action is not None:
				try:
					self.__action.run(self.getActionSource().get_namespace_object())
				except:
					if self.__action_off is not None:
						self.uiWidget._ui_switch_off_()
					raise
				if self.__action_off is not None:
					self.state = True
					if self.uiWidget is not None:
						self.uiWidget._ui_switch_on_()
		finally:
			# Do this also in case of exceptions in case the action code has
			# meddled with the enabled/disabled status of the actions.
			self.update_status()

	def getActionSource(self):
		"""
		object this commander is for
		main menu and toolbar commanders is for form object
		context menu commanders is for object context is
		"""
		return self.getParent()

# =============================================================================
# <menu>
# =============================================================================

class GFMenu(GFObj):
	"""
	A Menu that can either be the menu bar, a context menu, or a submenu.
	"""

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	name  = None
	label = None


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent = None, object_type = "GFMenu"):
		"""
		Create a GFMenu instance.
		"""
		GFObj.__init__(self, parent, object_type)

		# Valid triggers
		self._validTriggers = {
			'ON-MENUPOPUP':  'On-MenuPopup',
		}

	def _event_menu_popup(self):
		self.processTrigger('On-MenuPopup')


# =============================================================================
# <menuitem>
# =============================================================================

class GFMenuItem(GFCommander):
	"""
	An item in a menu that fires an action when selected.

	A menu item can also have a hotkey assigned to it.
	"""

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	hotkey = None


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent = None, object_type = "GFMenuItem"):
		"""
		Create a GFMenuItem instance.
		"""
		GFCommander.__init__(self, parent, object_type)

	def getActionSource(self):
		# return parent of most parent menu
		source = self.getParent()
		while isinstance(source, GFMenu):
			source = source.getParent()
		return source


# =============================================================================
# <toolbar>
# =============================================================================

class GFToolbar(GFObj):
	"""
	A Toolbar containing L{GFToolButton} buttons.
	"""

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	name  = None


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent = None, object_type = "GFToolbar"):
		"""
		Create a GFToolbar instance.
		"""
		GFObj.__init__(self, parent, object_type)

		self._triggerFunctions = {
			'get_toolbutton': {'function': self.__trigger_get_toolbutton},
		}

	def __trigger_get_toolbutton(self, name):
		child = self.findChildNamed(name, 'GFToolButton', False)
		if child:
			return child.get_namespace_object()

# =============================================================================
# <toolbutton>
# =============================================================================

class GFToolButton(GFCommander):
	"""
	A button in a toolbar that fires an action when selected.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent = None, object_type = "GFToolButton"):
		"""
		Create a GFToolButton instance.
		"""
		GFCommander.__init__(self, parent, object_type)

		# Trigger support
		self._triggerProperties.update({
			'overtext': {
				'get': self.get_overtext,
				'set': self.__trigger_set_overtext,
			},
		})

		self._overtext = None

	def getActionSource(self):
		return self.getParent().getParent()

	def get_overtext(self):
		return self._overtext

	def __trigger_set_overtext(self, value):
		if self._overtext != value:
			self._overtext = value
			self.uiWidget._ui_set_overtext(self._overtext)


