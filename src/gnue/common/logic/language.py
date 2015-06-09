# GNU Enterprise Common Library - Interface to language adapters
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
# $Id: language.py 9222 2007-01-08 13:02:49Z johannes $
#
# We redefine builtin RuntimeError
# pylint: disable-msg=W0622
#
# We use * and ** magic on purpose
# pylint: disable-msg=W0142

"""
Interface to language adapters.

This module contains classes necessary to access the language adapters, which
are used to execute user provided code in GNUe applications.
"""

from gnue.common.apps import errors
from gnue.common.utils.FileUtils import dyn_import

__all__ = ['AdapterNotFoundError', 'ImplementationError', 'CompileError',
	'RuntimeError', 'AbortRequest', 'getLanguageAdapter',
	'create_execution_context']

__plugins = {}                          # Cache for loaded plugins

# for old function "getLanguageAdapter"
__adapters = {}


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class AdapterNotFoundError(errors.AdminError):
	"""
	Language adapter not found.
	"""
	def __init__(self, language):
		errors.AdminError.__init__(self,
			u_("No adapter available for language '%s'") % language)

# -----------------------------------------------------------------------------

class ImplementationError(errors.SystemError):
	"""
	Method not implemented in language adapter.
	"""
	def __init__(self, classname, methodname):
		errors.SystemError.__init__(self,
			u_("The class '%(class)s' has no implementation for "
				"'%(method)s'") \
				% {"class" : classname, "method": methodname})

# -----------------------------------------------------------------------------

class CompileError(errors.RemoteError):
	"""
	Error in user code compilation.

	An error occured when trying to compile user code. Details of the error are
	available through the L{getName}, L{getDetail}, and L{getMessage}
	methods.
	"""
	pass

# -----------------------------------------------------------------------------

class RuntimeError(errors.RemoteError):
	"""
	Error in user code execution.

	An error occured when trying to execute user code. Details of the error are
	available through the L{getName}, L{getDetail}, and L{getMessage}
	methods.
	"""
	pass

# -----------------------------------------------------------------------------

class AbortRequest(errors.UserError):
	"""
	Call to abort().

	User code called the abort() function.
	"""
	pass


# -----------------------------------------------------------------------------
# Create an execution context
# -----------------------------------------------------------------------------

def create_execution_context(language, name, local_namespace, global_namespace,
	builtin_namespace):
	"""
	Create a new execution context.

	An execution context defines the environment in which user provided code
	runs. Most notably, the execution context handles the local and global
	variables that can be accessed by user code.

	@param language: Programming language.
	@type language: string or unicode
	@param name: Name of the execution context. This will be used in error
	    messages.
	@type name: string or unicode
	@param local_namespace: Dictionary with the local namespace. Keys are
	    variable names or function names, values are the objects or the
	    functions respectively. Identifiers defined here will look like locally
	    defined identifiers to the user code.
	@type local_namespace: dict
	@param global_namespace: Dictionary with the global namespace. Keys are
	    variable names or function names, values are the objects or the
	    functions respectively. Identifiers defined here will look like
	    globally defined identifiers to the user code.
	@type global_namespace: dict
	@param builtin_namespace: Dictionary with the builtin namespace. Keys are
	    variable names or function names, values are the objects or the
	    functions respectively. Identifiers defined here will look like
	    builtins to the user code, which means that they can even be accessed
	    from modules that are imported into the user code.
	@type builtin_namespace: dict
	@return: The execution context that can be used to run user defined code.
	@rtype: L{adapters.Base.ExecutionContext}
	"""

	checktype(language, basestring)
	checktype(name, basestring)
	checktype(local_namespace, dict)
	checktype(global_namespace, dict)
	checktype(builtin_namespace, dict)

	lang = str(language.lower())

	if not __plugins.has_key(lang):
		try:
			__plugins[lang] = dyn_import('gnue.common.logic.adapters.%s' % lang)
		except ImportError:
			raise AdapterNotFoundError, language

	return __plugins[lang].ExecutionContext(name, local_namespace,
		global_namespace, builtin_namespace)


# -----------------------------------------------------------------------------
# Get or create an instance of a given language adapter
# -----------------------------------------------------------------------------

def getLanguageAdapter(language):
	"""
	Return a language adapter object for the given language. DEPRECIATED.

	This function returns an execution context factory for the given language.

	This function will be depreciated in 0.7 and removed in 0.8.

	@param language: The language to return the language adapter object for.
	@type language: string or unicode

	@return: Language adapter object
	@rtype: adapters.Base.LanguageAdapter

	@raise AdapterNotFoundError: There is no language adapter available for the
	    given language.
	"""

	lang = str(language.lower())

	if not __adapters.has_key(lang):
		try:
			module = dyn_import('gnue.common.logic.adapters.%s' % lang)
		except ImportError:
			raise AdapterNotFoundError, language
		__adapters[lang] = module.LanguageAdapter()

	return __adapters[lang]


# =============================================================================
# Self test code
# =============================================================================

if __name__ == '__main__':

	code = """
            print "Hello World!"
            print "My name is %s %s." % (my_name, name)
            return value * 2"""

	print "*** Old (depreciated) interface ***"

	print "Creating language adapter for 'python' ..."
	adapter = getLanguageAdapter('python')

	print "Creating new execution environment ..."
	environ = adapter.createNewContext()
	environ.shortname = "testing"

	print "Setting up namespaces ..."
	environ.bindObject('my_name', 'John')

	print "Creating a new virtual code object ..."
	method = environ.buildFunction('myFunctionName', code,
		{'name': "", 'value': 0})

	params = {'name': 'foo', 'value': 'bar'}
	print "Calling function with: %s" % params
	res = method(**params)
	print "   result:", repr(res)

	params = {'name': 'fooBar', 'value': 4}
	print "Calling function with: %s" % params
	res = method(**params)
	print "   result:", repr(res)

	print ""
	print "*** New interface ***"

	print "Creating execution context for Python..."
	execution_context = create_execution_context(
		language = 'Python',
		name = 'test_context',
		local_namespace = {'my_name': 'John'},
		global_namespace = {},
		builtin_namespace = {})

	print "Compiling the code..."
	function = execution_context.build_function(
		name = 'myFunctionName',
		parameters = ['name', 'value'],
		code = code)

	params = {'name': 'foo', 'value': 'bar'}
	print "Calling function with: %s" % params
	res = method(**params)
	print "   result:", repr(res)

	params = {'name': 'fooBar', 'value': 4}
	print "Calling function with: %s" % params
	res = method(**params)
	print "   result:", repr(res)

	print "Thank you for playing."
