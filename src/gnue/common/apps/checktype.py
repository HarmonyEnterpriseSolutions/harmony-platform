# GNU Enterprise Common Library - checktype support
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
# Copyright 2001-2007 Free Software Foundation
#
# $Id: checktype.py 9222 2007-01-08 13:02:49Z johannes $

"""
Support for checking the type of variables.
"""

from types import *

import string
import sys

from gnue.common.apps import errors, i18n


# -----------------------------------------------------------------------------
# Exception definition
# -----------------------------------------------------------------------------

class TypeError (errors.SystemError):
	"""
	Raised when L{checktype} detects a wrong type.

	Do not raise this exception manually.
	"""

	# -----------------------------------------------------------------------------

	def __stringify (self, atype):
		if isinstance (atype, ListType):
			return string.join ([self.__stringify (t) for t in atype], ' / ')
		elif isinstance (atype, TypeType):
			return str (atype)
		elif isinstance (atype, ClassType):
			return '<class %s>' % str (atype)
		else:
			return '<type %s>' % str (atype)

	# -----------------------------------------------------------------------------

	def __init__ (self, variable, expected):

		self.varname = '<?>'
		for (k, v) in (sys._getframe (2)).f_locals.items ():
			if variable is v:
				self.varname = k

		self.expected = expected            # Expected type of variable

		if isinstance (variable, InstanceType):
			self.actual = variable.__class__
		else:
			self.actual = type (variable)     # Actual type of variable

		self.value = variable               # Value of variable

		message = u_('"%(varname)s" is expected to be of %(expected)s but is of '
			'%(actual)s and has value %(value)s') \
			% {'varname' : self.varname,
			'expected': self.__stringify (self.expected),
			'actual'  : self.__stringify (self.actual),
			'value'   : repr (self.value)}
		errors.SystemError.__init__ (self, message)


# -----------------------------------------------------------------------------
# Check type of a variable
# -----------------------------------------------------------------------------

def checktype (variable, validtype):
	"""
	Check a varaible (for example a parameter to a function) for a correct type.

	This function is available as builtin function.

	@param variable: Variable to check.
	@param validtype: Type, class, or a list of types and classes that are valid.
	@raise TypeError: The variable has a type not listed in the valid types.
	"""
	if isinstance (validtype, ListType):
		for t in validtype:
			if t is None:
				if variable is None:
					return
			else:
				if isinstance (variable, t):
					return
	else:
		if isinstance (variable, validtype):
			return
	raise TypeError, (variable, validtype)


# -----------------------------------------------------------------------------
# Module initialization
# -----------------------------------------------------------------------------

import __builtin__
__builtin__.__dict__['checktype'] = checktype


# -----------------------------------------------------------------------------
# Self test code
# -----------------------------------------------------------------------------

if __name__ == '__main__':

	import sys

	def mustfail (testvar, validtype):
		try:
			checktype (testvar, validtype)
		except TypeError, message:
			print message
			return
		raise Error ("checking %s as %s hasn't failed!" % (repr (variable),
				repr (validtype)))

	n = None
	s = 'this is a string'
	u = u'this is a unicode string'
	i = 100
	f = 17.85
	class p:
		pass
	class c (p):
		pass
	o = c ()

	print 'Single type, success ...'
	checktype (n, NoneType)
	checktype (s, StringType)
	checktype (u, UnicodeType)
	checktype (i, IntType)
	checktype (f, FloatType)
	checktype (c, ClassType)
	checktype (o, InstanceType)
	checktype (o, c)
	checktype (o, p)

	print 'Multiple types, success ...'
	checktype (n, [StringType, NoneType])
	checktype (s, [StringType, UnicodeType])
	checktype (u, [StringType, UnicodeType])
	checktype (o, [NoneType, c])

	print 'Single type, failure ...'
	mustfail (n, StringType)
	mustfail (s, UnicodeType)
	mustfail (u, StringType)
	mustfail (i, FloatType)
	mustfail (o, IntType)
	mustfail (c, c)

	print 'Multiple types, failure ...'
	mustfail (n, [StringType, UnicodeType])
	mustfail (s, [IntType, FloatType])

	print 'All test passed.'
