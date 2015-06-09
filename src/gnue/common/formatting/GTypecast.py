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
# Copyright 2000-2007 Free Software Foundation
#
# FILE:
# GTypecast.py
#
# DESCRIPTION:
"""
Methods used to typecast data
"""
#
# NOTES:
# Currently used by Parser, but may be of use to other methods
#
import re
from types import UnicodeType


from gnue.common.apps import errors

# Raised if a value cannot be typecasted
class TypecastError (errors.UserError):
	def __init__(self, msg=u_("Type cast error")):
		errors.UserError.__init__(self, msg)

#######################################################
#
# text
#
# This is for typecasting strings
#
#######################################################
def text (value):
	return value

#######################################################
#
# name
#
# This is for typecasting a string that
# will be used as a name or identifier
# (Characters: A-Z, a-z, 0-9, ['#$_-'])
#
#######################################################

REC_NAME = re.compile('(?i)[_A-Z][_A-Z0-9]*$')

def name (value):
	# TODO: name should make sure the string
	# TODO: containts only valid characters.
	name = value.strip()
	#if not REC_NAME.match(name):
	#    raise TypecastError, 'Invalid name: "%s"' % name
	return name


#######################################################
#
# uppername
#
# This is for typecasting a string that
# will be used as a name or identifier
# it will be automaticly converted to uppercase
# (Characters: A-Z, a-z, 0-9, ['#$_-'])
#
#######################################################
def uppername (value):
	# TODO: name should make sure the string
	# TODO: containts only valid characters.
	return name(value).upper()


#######################################################
#
# names
#
# This is used for typecasting a comma
# separated list of names
#
#######################################################
def names (value):
	return map(name, value.split(','))


#######################################################
#
# boolean
#
# This is for typecasting booleans
#
######################################################
def boolean (value):
	if value in (0,1):
		return value

	rv = value.strip()
	if len(rv):
		return not (rv[0] in ('N','n','F','f','0'))
	else:
		# This may seem counter-intuitive, but if attribute was present
		# without a specified value, then treat as true
		return True


#######################################################
#
# number
#
# This is for typecasting numbers (real)
#
#######################################################
def number (value):
	try:
		return float("%s" % value)
	except ValueError:
		raise TypecastError


#######################################################
#
# integer
#
# This is for typecasting integers
#
#######################################################
def integer (value):
	try:
		return int("%s" % value)
	except ValueError:
		raise TypecastError


#######################################################
#
# whole
#
# This is for typecasting whole numbers (0, 1, 2, ...)
#
#######################################################
def whole (value):
	try:
		v = int("%s" % value)
		if v < 0:
			raise TypecastError, u_("Whole numbers must be positive or 0")
		return v
	except ValueError:
		raise TypecastError


#######################################################
#
# escaped
#
# This "unescapes" a string
# e.g., escape ("\\x40") --> '@'
#
#######################################################
def escaped (value):

	# There should be a python built-in for this :(
	try:
		v = '"%s "' % value.replace('"','\\"')
		return eval(v)[:-1]
	except ValueError, msg:
		raise TypecastError, msg


#######################################################
#
# color
#
#######################################################
def color (value):
	from gnue.common.datatypes.Color import Color, ColorError
	try:
		return Color(value)
	except ColorError, msg:
		raise TypecastError, msg

#######################################################
#
# expression
#
#######################################################
def expression(value):
	try:
		return eval(value, {}, {})
	except Exception, e:
		raise TypecastError, "%s: %s" % (e.__class__.__name__, e)
