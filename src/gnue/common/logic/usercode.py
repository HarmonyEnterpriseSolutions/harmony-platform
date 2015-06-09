# GNU Enterprise Common Library - Actions and Triggers
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
# $Id: usercode.py 9222 2007-01-08 13:02:49Z johannes $

"""
Classes for all the object trees that handle user code: Actions and Triggers.

Triggers are still in the GTrigger module.
"""

from gnue.common.definitions import GObjects, GRootObj
from gnue.common.formatting import GTypecast

from gnue.common.logic import language

__all__ = ['GAction']


# =============================================================================
# Abstract parent class for action and trigger
# =============================================================================

class UserCode(GObjects.GObj):
	"""
	A Piece of user defined code.

	This class is the abstract base class for L{GAction} and
	L{GTrigger.GTrigger} and implements most of the things related to compiling
	and executing code that was provided in a form/report/whatever definition.
	"""

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	name = None
	language = None
	file = None


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None, object_type=None):
		"""
		Initialize a UserCode instance.
		"""

		GObjects.GObj.__init__(self, parent, object_type)

		self._xml_content_as_cdata_ = gConfig('StoreTriggersAsCDATA')

		self.__function = None

		self._inits = [self._initialize_]


	# -------------------------------------------------------------------------
	# Phase 1 init
	# -------------------------------------------------------------------------

	def _initialize_(self):

		# Find the next GRootObj. This can be, for example, either a <form> or
		# a <dialog> within a <form>. This must be done because every dialog
		# has its own global trigger namespace and its own trigger dictionary.
		# This cannot be done in __init__ or _buildObject, because for imported
		# objects (or for their children), the parent changes between __init__
		# and the phaseInit.
		parent = self.getParent()
		while not isinstance(parent, GRootObj.GRootObj) \
			and parent.getParent() is not None:
			parent = parent.getParent()
		self._root = parent             # also used by GTrigger

		return GObjects.GObj._buildObject(self)


	# -------------------------------------------------------------------------
	# Compile program code
	# -------------------------------------------------------------------------

	def compile(self, parameters):
		"""
		Compile the code.
		"""

		execution_context = language.create_execution_context(
			language = self.language,
			name = repr(self),
			local_namespace = {},
			global_namespace = self._root._triggerns,
			builtin_namespace = {})

		self.__function = execution_context.build_function(
			name = self.getDescription(),
			parameters = parameters,
			code = self.getChildrenAsContent())


	# -------------------------------------------------------------------------
	# Run program code
	# -------------------------------------------------------------------------

	def run(__self, *args, **params):
		"""
		Run the code.
		"""

		# We call our own self parameter "__self" here so that the user
		# function can have a parameter "self".

		if __self.__function is not None:
			return __self.__function(*args, **params)


# =============================================================================
# <action>
# =============================================================================

class GAction(UserCode):
	"""
	A piece of code that can be run by the user.

	Actions are pieces of code that can be arbitarily run by the user.

	Actions can be bound to a button, a toolbar button, a menu item, or a
	trigger.  Each action is available in the global namespace in all
	action/trigger code and can be run explicitly by calling its L{run} method.

	It is possible to assign an icon, a label and a description to an action,
	which will then be used for all attached buttons, menu items, and toolbar
	buttons, unless these elements override that information.

	It is possible to enable/disable an action, which will automatically
	enable/disable all attached buttons, menu items, and toolbar buttons.
	"""

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	icon        = None
	label       = None
	description = None
	enabled     = True


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent = None, object_type = "GCAction"):
		"""
		Create a GAction instance.
		"""
		UserCode.__init__(self, parent, object_type)

		#: Commanders attached to this action
		self.__commanders = []

		# Trigger support
		self._triggerGlobal = True
		self._triggerFunctions = {
			'run': {
				'function': self.__trigger_run}}
		self._triggerProperties = {
			'enabled': {
				'get': self.__trigger_get_enabled,
				'set': self.__trigger_set_enabled}}


	# -------------------------------------------------------------------------
	# Phase 1 initialization
	# -------------------------------------------------------------------------

	def _initialize_(self):

		UserCode._initialize_(self)
		self._root._actions[self.name] = self
		self.compile(['self'])


	# -------------------------------------------------------------------------
	# Trigger functions
	# -------------------------------------------------------------------------

	def __trigger_run(__self, *args, **params):
		# action must accept self as first arg
		# it is action source object
		__self.run(*args, **params)

	# -------------------------------------------------------------------------

	def __trigger_get_enabled(self):
		return self.enabled

	# -------------------------------------------------------------------------

	def __trigger_set_enabled(self, value):
		self.enabled = value
		for commander in self.__commanders:
			commander.update_status()


	# -------------------------------------------------------------------------
	# Register commander attached to this action
	# -------------------------------------------------------------------------

	def register_commander(self, commander):
		"""
		Registers a commander that is attached to this action.

		Whenever this action is enabled or disabled, it will automatically
		enable/disable all commanders attached to it.
		"""

		self.__commanders.append(commander)


# =============================================================================
# XML Element dictionary
# =============================================================================

def get_xml_elements(updates):
	"""
	Return the XML Element dictionary for the objects defined in this module.
	"""

	checktype(updates, dict)

	xml_elements = {
		'action': {
			'Description'   : u_(
				"A piece of code that can be bound to a button, a menu "
				"item, a toolbar button or a trigger."),
			'BaseClass'     : GAction,
			'ParentTags'    : None,
			'Importable'    : True,
			'MixedContent'  : True,
			'KeepWhitespace': True,
			'Attributes' : {
				'name': {
					'Label'      : u_("Name"),
					'Description': u_("Name of this element"),
					'Typecast'   : GTypecast.name,
					'Required'   : True,
					'Unique'     : True},
				'icon': {
					'Label'      : u_("Icon"),
					'Description': u_("Icon assigned with this action"),
					'Typecast'   : GTypecast.name},
				'label': {
					'Label'      : u_("Label"),
					'Description': u_("Short text to use for this action"),
					'Typecast'   : GTypecast.text},
				'description': {
					'Label'      : u_("Description"),
					'Description': u_("Long text to use for this action"),
					'Typecast'   : GTypecast.text},
				'language': {
					'Label'      : u_("Language"),
					'Description': u_(
						"Programming language the code is written in"),
					'Typecast'   : GTypecast.name,
					'ValueSet'   : {
						'python': {'Label': "Python"}},
					'Default'    : 'python'},
				'file': {
					'Label'      : u_("Source file"),
					'Description': u_(
						"External file containing the source code"),
					'Typecast'   : GTypecast.text},
				'enabled': {
					'Label'      : u_("Enabled"),
					'Description': u_(
						"Determines whether this action can be run"),
					'Typecast'   : GTypecast.boolean,
					'Default'    : True}}}}

	for alteration in updates.keys():
		xml_elements[alteration].update(updates[alteration])

	return xml_elements
