# GNU Enterprise Common Library - RPC interface - Un-/Marshalling
#
# Copyright 2001-2007 Free Software Foundation
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
# $Id: typeconv.py 9222 2007-01-08 13:02:49Z johannes $

import datetime
from calendar import timegm

from src.gnue.common.rpc.drivers.hessian import hessianlib


epoch = datetime.datetime.utcfromtimestamp(0)

# -----------------------------------------------------------------------------
# Check wether a given item is an id-dictionary representing a server object
# -----------------------------------------------------------------------------

def is_rpc_object (value):
	"""
	Check wether a given value is a structure representing a server object.

	@param value: the python value to be checked
	@returns: True for a remote server object, False otherwise.
	"""

	if isinstance (value, dict):
		k = value.keys ()
		k.sort ()

		result = (k == ['__id__', '__rpc_datatype__'])
	else:
		result = False

	return result


# -----------------------------------------------------------------------------
# Convert native Python type to hessianrpc's type
# -----------------------------------------------------------------------------

def python_to_rpc (value, wrapObject, *wrapArgs):
	"""
	Convert a value from native python type into a type acceptable to xmlrpc.

	The following type conversions are performed.

	* None           -> None
	* str            -> unicode
	* unicode        -> unicode
	* bool           -> hessianlib.boolean
	* int/long/float -> int/long/float
	* datetime.datetime/.date/.time -> hessianlib.DateTime

	For lists and tuples the conversion will be applied to each element. For
	dictionaries the conversion will be applied to the key as well as the value.

	@param value: the native python value to be converted
	@param wrapObject: if the value is not one of the base types to be converted,
	  this function will be used to wrap the value
	"""

	if value is None:
		return value

	# None or String
	if isinstance (value, str):
		return unicode (value)

	elif isinstance (value, unicode):
		return value

	# Boolean needs to be checked *before* <int>
	elif isinstance (value, bool):
		return hessianlib.boolean (value)

	# Number
	elif isinstance (value, (int, long, float)):
		return value

	# Date/Time
	elif isinstance (value, datetime.datetime):
		return hessianlib.DateTime (timegm (value.utctimetuple ()))

	elif isinstance (value, datetime.date):
		value = epoch.combine (value, epoch.time ())
		return hessianlib.DateTime (timegm (value.utctimetuple ()))

	elif isinstance (value, datetime.time):
		value = epoch.combine (epoch.date (), value)
		return hessianlib.DateTime (timegm (value.utctimetuple ()))

	# List
	elif isinstance (value, list):
		return [python_to_rpc (element, wrapObject, *wrapArgs) for element in value]

	# Tuple
	elif isinstance (value, tuple):
		return tuple ([python_to_rpc (element, wrapObject, *wrapArgs) \
					for element in value])

	# Dictionary
	elif isinstance (value, dict):
		result = {}

		for (key, val) in value.items ():
			if key is None:
				key = ""

			elif not isinstance (key, str):
				key = python_to_rpc (key, wrapObject, *wrapArgs)

			result [key] = python_to_rpc (val, wrapObject, *wrapArgs)

		return result

	elif wrapObject is not None:
		return wrapObject (value, *wrapArgs)

	else:
		raise exception, repr (value)


# -----------------------------------------------------------------------------
# Convert xmlrpc's type to native Python type
# -----------------------------------------------------------------------------

def rpc_to_python (value, wrapObject, exception, *wrapArgs):
	"""
	Convert a value from xmlrpc types into native python types.

	@param value: xmlrpc value
	@param wrapObject: function to be called, if L{is_rpc_object} returns True
	@param exception: exception to be raised if no conversion is available

	The following conversions are performed:

	None               -> None
	str                -> unicode or None (for empty strings)
	unicode            -> unicode or None (for empty strings)
	hessianlib.boolean  -> bool
	int/long/float     -> int/long/float
	hessianlib.DateTime -> datetime.date, time or datetime (dep. on ISO-string)

	For lists and tuples the conversion will be applied to each element. For
	dictionaries the conversion will be applied to the key as well as the value.
	"""

	if value is None:
		return None

	# String (converts to None for empty strings, which will be the case for
	# None-values used in dictionary keys)
	elif isinstance (value, str):
		return value and unicode (value) or None

	elif isinstance (value, unicode):
		return value and value or None

	# Boolean (has to be checked before IntType)
	elif isinstance (value, hessianlib.boolean):
		return value and True or False

	# Number
	elif isinstance (value, (int,long,float)):
		return value

	# Date/Time/DateTime
	elif isinstance (value, hessianlib.DateTime):
		return datetime.datetime.utcfromtimestamp (value.value)

	# List
	elif isinstance (value, list):
		return [rpc_to_python (element, wrapObject, exception, *wrapArgs) \
				for element in value]

	# Tuple
	elif isinstance (value, tuple):
		return tuple ([rpc_to_python (e, wrapObject, exception, *wrapArgs) \
					for e in value])

	# Dictionary
	elif is_rpc_object (value):
		return wrapObject (value, *wrapArgs)

	elif isinstance (value, dict):
		result = {}
		for (key, val) in value.items ():
			result [rpc_to_python (key, wrapObject, exception, *wrapArgs)] = \
				rpc_to_python (val, wrapObject, exception, *wrapArgs)
		return result

	else:
		raise exception, repr (value)
