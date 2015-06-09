# GNU Enterprise Common Library - Python language adapter plugin
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
# $Id: python.py,v 1.6 2011/07/14 21:07:00 Oleg Exp $
#
# We use * and ** magic on purpose
# pylint: disable-msg=W0142

"""
Language adapter plugin for Python.
"""

import sys
from gnue.common.apps import errors
from gnue.common.logic import language
from gnue.common.logic.adapters import Base

__all__ = ['LanguageAdapter', 'ExecutionContext', 'Function']


# =============================================================================
# Implementation of a language adapter for python
# =============================================================================

class LanguageAdapter(Base.LanguageAdapter):
	"""
	Implementation of a language engine for python
	"""

	# -------------------------------------------------------------------------
	# Create a new execution context
	# -------------------------------------------------------------------------

	def createNewContext(self):
		"""
		Create a python execution context
		"""
		return ExecutionContext("unknown_executioncontext", {}, {}, {})


# =============================================================================
# Python Execution Context
# =============================================================================

class ExecutionContext(Base.ExecutionContext):
	"""
	This class implements an execution context for Python code.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, name, local_namespace, global_namespace,
		builtin_namespace):

		Base.ExecutionContext.__init__(self, name, local_namespace,
			global_namespace, builtin_namespace)

		# TODO: Change this to self.__name with 0.8
		self.shortname = name
		self.__local_namespace = local_namespace
		self.__global_namespace = global_namespace
		self.__builtin_namespace = builtin_namespace


	# -------------------------------------------------------------------------
	# Create a function
	# -------------------------------------------------------------------------

	def _build_function_(self, name, parameters, code):

		# Strip trailing whitespace from code
		lines = [i.rstrip() for i in code.split('\n')]
		indent_char = None
		code_indent = None

		for row, line in enumerate(lines):
			if not line:
				continue

			indent = line[:len(line) - len(line.lstrip('\t '))]

			if line.lstrip().startswith('#'):
				lines[row] = ''
			elif code_indent is None:
				code_indent = indent

			pos = indent.find('\t')
			if pos >= 0:
				if indent_char == ' ':
					raise errors.ApplicationError, u_(
						"Space indented sourcecode contains tab character at row %d position %d") \
						% (row, pos)
				else:
					indent_char = '\t'
			pos = indent.find(' ')
			if pos >= 0:
				if indent_char == '\t':
					raise errors.ApplicationError, u_(
						"Tab indented sourcecode contains space character at row %d position %d") \
						% (row, pos)
				else:
					indent_char = ' '

		code_indent = code_indent or ''

		# replace code indent with 4 spaces
		for row, line in enumerate(lines):
			if line:
				if line.startswith(code_indent):
					lines[row] = '    ' + line[len(code_indent):]
				else:
					raise errors.ApplicationError, u_(
						"Unindent does not match any outer indentation level at row %d") \
						% row

		# The whole code is enclosed into a pseudo function definition. This
		# way, the code can contain "return" statements.
		# Start with the function header
		# Unpack the namepsace dictionary within the function, so the local
		# namespace appears to be local *inside* the function
		# Before calling the function, add the builtins
		# And finally run the function and save the result

		encoding = 'UTF-8'

		revised_code = u"""\
# -*- coding: %s -*-
def %s(__namespace, %s):
    __add = None
    for __add in __namespace.keys():
        exec '%%s = __namespace["%%s"]' %% (__add, __add) in globals(), locals()
    del __add, __namespace

%s

import __builtin__
for (__key, __value) in __builtins.items():
    __builtin__.__dict__[__key] = __value
__result = %s(__namespace, **__parameters)
""" % (encoding, name, ", ".join(parameters), '\n'.join(lines), name)

		try:
			compiled_code = compile(
				revised_code.encode(encoding),
				'<%s>' % self.shortname.encode(encoding),
				'exec'
			)
		except:
			sys.stderr.write("====== ERROR IN CODE =====\n")
			sys.stderr.write('\n'.join(lines))
			sys.stderr.write("\n==========================\n")
			(group, name, message, detail) = errors.getException(1)
			if group == 'system':
				group = 'application'
			raise language.CompileError, (group, name, message, detail)

		# Make sure namespaces are clean
		# TODO: This can be moved to Base.ExecutionContext.__init__() after all
		# the depreciated functions are removed.
		self.__make_safe_namespace(self.__builtin_namespace)
		self.__make_safe_namespace(self.__local_namespace)
		self.__make_safe_namespace(self.__global_namespace)

		return Function(
			compiled_code = compiled_code,
			local_namespace = {
				'__builtins': self.__builtin_namespace,
				'__namespace': self.__local_namespace},
			global_namespace = self.__global_namespace)


	# -------------------------------------------------------------------------
	# Make sure the given Namespace has no invalid identifiers
	# -------------------------------------------------------------------------

	def __make_safe_namespace(self, namespace):
		"""
		This function replaces all invalid keys in the dict. @namespace by
		appropriate identifiers.
		"""
		for key in namespace.keys():
			safe_id = self._identifier_(key)
			if safe_id != key:
				namespace[safe_id] = namespace[key]
				del namespace[key]


	# -------------------------------------------------------------------------
	# Depreciated functions
	# -------------------------------------------------------------------------

	def bindObject(self, name, aObject, asGlobal = False):
		"""
		Add an object to the local or global namespace.
		"""
		if asGlobal:
			self.__global_namespace[name] = aObject
		else:
			self.__local_namespace[name] = aObject

	# -------------------------------------------------------------------------

	def bindFunction(self, name, aFunction, asGlobal = False):
		"""
		Add a function to the local or global namespace.
		"""
		if asGlobal:
			self.__global_namespace[name] = aFunction
		else:
			self.__local_namespace[name] = aFunction

	# -------------------------------------------------------------------------

	def bindBuiltin(self, name, anElement):
		"""
		Bind the given element into the builtin-namespace.
		@param name: name of the element within the builtin-namespace
		@param anElement: element to be bound into the builtin-namespace
		"""
		self.__builtin_namespace[name] = anElement


# =============================================================================
# Class encapsulating user provided Python code in a function
# =============================================================================

class Function:
	"""
	Implementation of a virtual function using Python.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, compiled_code, local_namespace, global_namespace):

		self.__compiled_code = compiled_code
		self.__local_namespace = local_namespace
		self.__global_namespace = global_namespace


	# -------------------------------------------------------------------------
	# Execute the function
	# -------------------------------------------------------------------------

	def __call__(__self, *args, **params):
		"""
		This function creates a local namespace as a copy from the execution
		context's local namespace, adds all parameters to this namespace and
		executes the code.
		"""

		# We call our own self parameter "__self" here so that the user
		# function can have a parameter "self".

		__self.__local_namespace['__parameters'] = params

		# FIXME: This allows the "self" parameter to be passed as a non-keyword
		# argument. DEPRECATED.
		if args:
			__self.__local_namespace['__parameters']['self'] = args[0]

		try:
			exec __self.__compiled_code \
				in __self.__global_namespace, __self.__local_namespace

		except language.AbortRequest:
			# Pass through AbortRequests unchanged
			raise

		except:
			# All others raise a RuntimeError
			(group, name, message, detail) = errors.getException (2)
			if group == 'system':
				group = 'application'
			raise language.RuntimeError, (group, name, message, detail)

		return __self.__local_namespace.get('__result')
