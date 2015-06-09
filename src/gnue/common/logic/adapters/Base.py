# GNU Enterprise Common Library - Base classes for language adapter plugins
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
# $Id: Base.py 9222 2007-01-08 13:02:49Z johannes $
#
# We use * and ** magic on purpose
# pylint: disable-msg=W0142

"""
Base classes for language adapter plugins.

Language adapters are python modules that allow external, user provided code in
a given language to be executed within Python. In GNU Enterprise, language
adapters are used to execute L{usercode.GAction} actions, L{GTrigger.GTrigger}
triggers, and server side methods in GNUe-AppServer.

Each language adapter implements this feature for a specific language. An
implementation of a language adapter consists of three classes that are derived
from the three base classes in this module.
"""

import re
import types

from gnue.common.logic.language import ImplementationError, AbortRequest

__all__ = ['LanguageAdapter', 'ExecutionContext']


# =============================================================================
# Base class for LanguageAdapters
# =============================================================================

class LanguageAdapter:
	"""
	Base class for language adapters. DEPRECIATED.

	This class will be depreciated in 0.7 and removed in 0.8.
	Depreciated. Use L{language.create_execution_context} instead.
	"""

	# -------------------------------------------------------------------------
	# Create and return a new execution context
	# -------------------------------------------------------------------------

	def createNewContext(self):
		"""
		Create a new execution context in which user provided code can run.
		DEPRECIATED.

		This function will be depreciated in 0.7 and removed in 0.8.
		Use L{language.create_execution_context} instead.

		@return: Execution context object.
		@rtype: ExecutionContext
		"""
		raise ImplementationError, (self.__class__, 'createNewContext()')


# =============================================================================
# Helper function to raise an AbortRequest exception
# =============================================================================

def _abort(message):
	"""
	Raise an L{language.AbortRequest} exception.

	This function will be available for user code under the name "abort".
	"""
	raise AbortRequest, message


# =============================================================================
# Base class for execution contexts
# =============================================================================

class ExecutionContext:
	"""
	An environment in which user defined code can be compiled and executed.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, name, local_namespace, global_namespace,
		builtin_namespace):
		"""
		Initialize an execution context object.

		Descendants must overwrite the constructor and do something useful with
		the parameters.

		@param name: Name of the execution context. This will be used in error
		    messages.
		@type name: string or unicode
		@param local_namespace: Dictionary with the local namespace. Keys are
		    variable names or function names, values are the objects or the
		    functions respectively. Identifiers defined here will look like
		    locally defined identifiers to the user code.
		@type local_namespace: dict
		@param global_namespace: Dictionary with the global namespace. Keys are
		    variable names or function names, values are the objects or the
		    functions respectively. Identifiers defined here will look like
		    globally defined identifiers to the user code.
		@type global_namespace: dict
		@param builtin_namespace: Dictionary with the builtin namespace. Keys
		    are variable names or function names, values are the objects or the
		    functions respectively. Identifiers defined here will look like
		    builtins to the user code, which means that they can even be
		    accessed from modules that are imported into the user code.
		@type builtin_namespace: dict
		"""

		builtin_namespace['abort'] = _abort


	# -------------------------------------------------------------------------
	# Build a function
	# -------------------------------------------------------------------------

	def build_function(self, name, parameters, code):
		"""
		Create an executable object containing the user provided code.

		@param name: Function name
		@type name: string or unicode
		@param parameters: List of paramete names
		@type parameters: list of strings or unicodes
		@param code: Function code
		@type code: string or unicode
		"""

		checktype(name, basestring)
		checktype(parameters, list)
		for parameters_item in parameters:
			checktype(parameters_item, basestring)
		checktype(code, basestring)

		# Make sure name is not empty
		if not name:
			name = "unnamed"

		# Make sure the function name and the parameter names are clean
		# identifiers
		name = self._identifier_(name)
		parameters = [self._identifier_(param) for param in parameters]

		return self._build_function_(name, parameters, code)


	# -------------------------------------------------------------------------
	# Virtual methods
	# -------------------------------------------------------------------------

	def _build_function_(self, name, parameters, code):
		"""
		Create an executable object containing the user provided code.

		Descendants must implement this function.
		"""
		raise ImplementationError, (self.__class__, '_build_function_()')

	# -------------------------------------------------------------------------

	def _identifier_(self, name):
		"""
		Convert any name into an identifier valid for this programming
		language.

		By default, this function changes all non-alphanumeric characters into
		an underscore and adds an underscore at the beginning if the name
		starts with a number. Descendants can overwrite or extend this.
		"""
		result = re.sub('[^a-zA-Z0-9]', '_', name)
		if re.match('[0-9]', result):
			result = '_' + result
		return result


	# -------------------------------------------------------------------------
	# Depreciated methods
	# -------------------------------------------------------------------------

	def defineNamespace(self, addNS, asGlobal = False):
		"""
		Define the namespace for this execution context. DEPRECIATED.

		This function will be depreciated in 0.7 and removed in 0.8.
		Use L{language.create_execution_context} instead to define all
		namespaces in one single step.

		Merge the given namespace into the execution context. This function
		is doing this using L{bindFunction} and L{bindObject} methods depeding
		on the namespace elements type.
		"""
		for (name, value) in addNS.items():
			if name is not None:
				if isinstance(value, types.MethodType):
					self.bindFunction(name, value, asGlobal)
				else:
					self.bindObject(name, value, asGlobal)

	# -------------------------------------------------------------------------

	def bindObject(self, name, aObject, asGlobal = False):
		"""
		Bind an object into the namespace. DEPRECIATED.

		This function will be depreciated in 0.7 and removed in 0.8.
		Use L{language.create_execution_context} instead to define all
		namespaces in one single step.

		A descendant overrides this function to bind a given object into the
		local or global namespace.
		"""
		raise ImplementationError, (self.__class__, 'bindObject()')

	# -------------------------------------------------------------------------

	def bindFunction(self, name, aFunction, asGlobal = False):
		"""
		Bind a function into the namespace. DEPRECIATED.

		This function will be depreciated in 0.7 and removed in 0.8.
		Use L{language.create_execution_context} instead to define all
		namespaces in one single step.

		A descendant overrides this function to bind a given function into the
		local or global namespace.
		"""
		raise ImplementationError, (self.__class__, 'bindFunction()')

	# -------------------------------------------------------------------------

	def bindBuiltin(self, name, anElement):
		"""
		Bind a builtin function into the namespace. DEPRECIATED.

		This function will be depreciated in 0.7 and removed in 0.8.
		Use L{language.create_execution_context} instead to define all
		namespaces in one single step.

		A descendant overrides this function to bind a given element into the
		builtin-namespace of the context.
		"""
		raise ImplementationError, (self.__class__, 'bindBuiltin()')

	# -------------------------------------------------------------------------

	def buildFunction(self, name, code, parameters = None):
		"""
		Build a Function and compile its code.
		"""
		if parameters is None:
			params = []
		else:
			params = parameters.keys()
		return self._build_function_(name, params, code)

	# -------------------------------------------------------------------------

	def release (self):
		"""
		Release an execution context: remove references in the namespace and
		the like. DEPRECIATED.

		This function is not necessary any more.
		"""
		pass
