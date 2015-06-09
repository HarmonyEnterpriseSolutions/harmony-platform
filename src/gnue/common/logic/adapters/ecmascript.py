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
# Copyright 2003-2007 Free Software Foundation
#
#
# FILE:
# ECMAscript/Adapter.py
#
# DESCRIPTION:
# Provides a way to execute python code in a given environment
#
# NOTES:
#
import sys
import types
import string

from gnue.common.apps import GDebug
from gnue.common.apps import errors
from gnue.common.logic import language
from gnue.common.logic.adapters import Base
from gnue.common.logic.NamespaceCore import NamespaceElement

class LanguageAdapter(Base.LanguageAdapter):
	def __init__(self):
		# Import down here so module remains importable (for eypdoc)
		try:
			import spidermonkey
		except ImportError:
			raise errors.AdminError (
				"Spidermonkey python module not installed!\n"
				"http://wwwsearch.sourceforge.net/python-spidermonkey/")
		self._rt = spidermonkey.Runtime()

	def createNewContext(self):
		return ExecutionContext(self._rt)

class ExecutionContext(Base.ExecutionContext):
	def __init__(self, runtime):
		Base.ExecutionContext.__init__(self)
		self._cx = runtime.new_context()
		self._cx.bind_class(NamespaceElement)

	# namespace creation (global namespace)
	#
	def bindObject (self, name, aObject, aClass = None):
		if aClass != None and aClass != False:
			self._cx.bind_class (aClass)
		self._cx.bind_object (name, aObject)

	def bindFunction(self, name, object, asGlobal = False):
		# asGlobal isn't supported at the moment
		self._cx.bind_callable(name, object)

	# script / trigger /
	def buildMethod(self, name, code, parameters={}):
		return ECMAscriptMethod(self, name, code, parameters)

	# script / trigger /
	def buildFunction(self, name, code, parameters={}):
		return ECMAscriptFunction(self, name, code, parameters)

class ECMAscriptMethod (Base.Function):  # a rename to fix it for the moment

	def __init__(self, context, name, code, parameters):
		Base.Function.__init__(self, context, name, code, parameters)
		# Take care of special names
		self._name = string.replace(self._name,'-','_')
		self._cx=context._cx
		self.compile()

	def compile(self):
		# TODO: add error handling

		# build parameter list
		param = ''
		delim =''
		for key in self._parameters.keys():
			value = self._parameters[key]
			param = param + delim + key
			if value==None:
				param = ',%s=%s' % (param, value)
			delim = ','

		# build code
		self._realcode = '\n%s = function (%s) {%s};' % (self._name, param,
			self._code);
		# name of helper function
		self._hname = '__%s' % string.replace(self._name,'.','_')

		# add helper function
		self._realcode = '%s\nfunction %s (%s) { return %s(%s);}; ' % (self._realcode,
			self._hname, param,
			self._name,param)

		assert gDebug(8, "Adding code to ECMAscript namespace :'%s'" % self._realcode)
		# load code into context
		try:
			self._cx.eval_script(self._realcode)

		except:
			(group, name, message, detail) = errors.getException (1)
			if group == 'system':
				group = 'application'
			raise language.CompileError, (group, name, message, detail)


	def execute(self, *args,**params):
		param = ""
		# TODO: find a way to pass parameter
		try:
			#return self._cx.eval_script("x=%s(%s);" % (self._name,param))
			# call function cannot call the function itself, so just simulate it
			# by creating a shortcut function to call like its_me_function to call
			return self._cx.call_fn(self._hname, ()) #args)

		except:
			(group, name, message, detail) = errors.getException (1)
			if group == 'system':
				group = 'application'
			raise language.RuntimeError, (group, name, message, detail)

	def rebind(self, obj, name):
		pass

class ECMAscriptFunction(Base.Function):
	def __init__(self, context, name, code, parameters):
		Base.Function.__init__(self, context, name, code, parameters)
		# Take care of special names
		self._name = string.replace(self._name,'-','_')
		self._cx=context._cx
		self.compile()

	def compile(self):
		# TODO: add error handling

		# build parameter list
		param = ''
		delim =''
		for key in self._parameters.keys():
			value = self._parameters[key]
			param = param + delim + key
			#      if value==None or value == 'None':
			#        param = '%s=%s' % (param, value)
			delim = ','

		# build code
		self._realcode = '%s = function (%s) {%s};' % (self._name, param,
			self._code);

		assert gDebug(8, "Adding code to ECMAscript namespace :'%s'" % self._realcode)
		# load code into context
		try:
			self._cx.eval_script(self._realcode)

		except:
			(group, name, message, detail) = errors.getException (1)
			if group == 'system':
				group = 'application'
			raise language.CompileError, (group, name, message, detail)


	def execute(self, *args,**params):
		# TODO: check args for object instances
		try:
			retval = self._cx.call_fn(self._name, args)
			return retval[0]

		except:
			(group, name, message, detail) = errors.getException (1)
			if group == 'system':
				group = 'application'
			raise language.RuntimeError, (group, name, message, detail)
