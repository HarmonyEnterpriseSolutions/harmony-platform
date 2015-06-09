# GNU Enterprise Common Library - Trigger handling classes
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
# $Id: GTrigger.py 9390 2007-02-21 13:43:05Z reinhard $

from gnue.common.apps import errors
from gnue.common.formatting import GTypecast

from gnue.common.logic.usercode import UserCode
from gnue.common.logic import language

__all__ = ['InvalidTriggerTypeError', 'InvalidTriggerFiredError', 'GTrigger',
	'GTriggerExtension']


# =============================================================================
# Exceptions
# =============================================================================

class InvalidTriggerTypeError(errors.ApplicationError):
	"""
	Invalid trigger type associated with object.

	A trigger is defined with a type not allowed for the associated object.
	"""
	def __init__(self, trigger_type):
		errors.ApplicationError.__init__(self, u_(
				"Invalid trigger type '%s'") % trigger_type)

# -----------------------------------------------------------------------------

class InvalidTriggerFiredError(errors.SystemError):
	"""
	Invalid trigger type fired.

	A trigger has been fired with a type not allowed for the object that fired
	it.
	"""
	def __init__(self, trigger_type, xml_object):
		errors.SystemError.__init__(self, u_(
				"Invalid trigger type '%s' fired by %s") \
				% (trigger_type, repr(xml_object)))


# =============================================================================
# <trigger>
# =============================================================================

class GTrigger(UserCode):

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	type = None
	src = None


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):

		UserCode.__init__(self, parent, 'GCTrigger')


	# -------------------------------------------------------------------------
	# Nice string representation
	# -------------------------------------------------------------------------

	def __repr__(self):

		return repr(self.getParent()) + '.' + self.getDescription()


	# -------------------------------------------------------------------------
	# Phase 1 initialization
	# -------------------------------------------------------------------------

	def _initialize_(self):

		UserCode._initialize_(self)

		if not self.type:
			raise RuntimeError, "Trigger named '%s' has no 'type' attribute defined" % (self.name,)
		
		if self.type != "NAMED":
			if self.getParent():
				self.getParent().associateTrigger(self.type, self)
		else:
			self._root._triggerDictionary[self.name] = self

		if self.src is None:
			self.compile(['self'])


	# -------------------------------------------------------------------------
	# Run the trigger code
	# -------------------------------------------------------------------------

	def __call__(__self, *args, **params):

		# We call our own self parameter "__self" here so that the user
		# function can have a parameter "self".

		if __self.src is not None:
			action = __self._root._actions.get(__self.src)
			if action is not None:
				if action.enabled:
					return action.run(*args, **params)
			else:
				return __self._root._triggerDictionary[__self.src](*args, **params)
		else:
			return __self.run(*args, **params)


	# -------------------------------------------------------------------------
	# Return a nice description of this object for designer
	# -------------------------------------------------------------------------

	def getDescription(self):
		"""
		Return a useful description of this object for use by designer
		"""
		if self.type == 'NAMED':
			return self.name
		else:
			return self.type.upper()


# =============================================================================
# Base class for all objects that can have triggers associated
# =============================================================================

# FIXME: Should actually be a descendant of GTriggerCore, because the calling
# object itself is visible in the trigger namespace as "self", so it must
# obviously be trigger namespace visible.

class GTriggerExtension:
	"""
	Base class for all objects that can fire triggers.

	Descendants of this class maintain a list of trigger names and attached
	L{GTrigger} objects. Each trigger name can have several L{GTrigger} objects
	attached, in which case the code of all of them is executed sequentially.

	@cvar _validTriggers: Dictionary with valid trigger names as keys.
	"""

	# -------------------------------------------------------------------------
	# Class variables
	# -------------------------------------------------------------------------

	_validTriggers = {}


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self):

		self.__triggers = {}


	# -------------------------------------------------------------------------
	# Associate a function with a trigger
	# -------------------------------------------------------------------------

	def associateTrigger(self, key, function):
		"""
		Associate a trigger with this object.

		More than one trigger of a specific type can be associated with an
		object. This function is typically automatically called during tree
		construction from xml source.

		@param key: Trigger name
		@type key: str
		@param function: User provided code to call
		@type function: callable
		"""

		key = key.upper()

		if not key in self._validTriggers.keys():
			raise InvalidTriggerTypeError, key

		if not self.__triggers.has_key(key):
			self.__triggers[key] = []
		self.__triggers[key].append(function)


	# -------------------------------------------------------------------------
	# Fire a trigger
	# -------------------------------------------------------------------------

	def processTrigger(self, key, ignoreAbort=True):
		"""
		Fire the requested trigger if a trigger of that type has been
		associated with this object.

		@param key: The name of the trigger.
		@type key: str
		@param ignoreAbort: If True (the default), then
		    L{language.AbortRequest} exceptions from the trigger are ignored.
		@type ignoreAbort: bool
		"""

		key = key.upper()

		if not key in self._validTriggers.keys():
			raise InvalidTriggerFiredError, (key, self)

		assert gDebug (9, 'Trigger %s on %s' % (key, repr(self)))
		result = None
		if self.__triggers.has_key(key):
			for function in self.__triggers[key]:
				try:
					new_result = function(self = self.get_namespace_object())
					if new_result is not None:
						result = new_result
				except language.AbortRequest:
					if not ignoreAbort:
						raise
		return result


# =============================================================================
# XML Element dictionary
# =============================================================================

def getXMLelements(updates=None):
	"""
	Return the XML Element dictionary for the objects defined in this module.
	"""

	xml_elements = {
		'trigger': {
			'Description'     : u_(
				"A piece of code that can be bound to a specific event."),
			'BaseClass'       : GTrigger,
			'ParentTags'      : None,
			'Importable'      : True,
			'MixedContent'    : True,
			'KeepWhitespace'  : True,
			'UsableBySiblings': True,
			'Attributes': {
				'name': {
					'Label'      : u_("Name"),
					'Description': u_("Name of this element"),
					'Typecast'   : GTypecast.name,
					'Unique'     : True},
				'type': {
					'Label'      : u_("Type"),
					'Description': u_(
						"Type of the trigger. Can be either the name of "
						"the event that should fire this trigger, or "
						"'NAMED' for named triggers"),
					'Typecast'   : GTypecast.uppername},
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
				'src': {
					'Label'      : u_("Source Trigger"),
					'Description': u_(
						"Name of a named trigger that contains the "
						"program code"),
					'References' : 'trigger.name',
					'Typecast'   : GTypecast.name}}}}

	if updates is not None:
		for alteration in updates.keys():
			xml_elements[alteration].update(updates[alteration])

	return xml_elements
