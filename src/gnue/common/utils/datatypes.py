# GNU Enterprise Common Library - Utilities - Datatype conversion
#
# Copyright 2001-2007 Free Software Foundation
#
# This file is part of GNU Enterprise
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
# $Id: datatypes.py,v 1.7 2009/04/29 14:18:16 oleg Exp $
"""
Helper functions for datatype conversion.
"""

__all__ = ['convert', 'InvalidValueType', 'ConversionError']

import datetime
from decimal import Decimal

from gnue.common.utils import GDateTime


# =============================================================================
# Convert a value to a given target datatype
# =============================================================================

def convert(value, datatype, length, scale):
	"""
	Convert a value to a given target datatype.

	@param value: The value to convert.
	@param datatype: Can be "text", "number", "date", "time", "datetime",
	    "boolean", or "raw".
	@param length: Length for "text" and "number" datatypes. C{None} means
	    "unlimited" number of digits.
	@param scale: Scale for "number" datatype. C{None} means "unlimited" number
	    of fractional digits.
	"""

	# It might be better style to have separate functions "convert_text",
	# "convert_number", etc., however I strongly believe that keeping
	# everything in a single function helps improving the performance.
	#   -- Reinhard

	if value is None:
		# "None" is always valid, independent of data type
		result = None

	elif isinstance(value, InvalidValueType):
		result = value

	elif datatype == "raw":
		result = value

	elif datatype == "text":
		if isinstance(value, unicode):
			result = value
		elif isinstance(value, str):
			result = unicode(value)
		else:
			result = unicode(str(value))

	elif datatype == "number":
		if scale is None or scale > 0:
			if isinstance(value, Decimal):
				result = value
			else:
				result = Decimal(str(value))
		else:
			result = int(value)

	elif datatype == "date":
		if isinstance(value, basestring):
			try:
				value = GDateTime.parseISO(value)
			except GDateTime.InvalidDateError:
				raise ConversionError(value, datatype)

		if isinstance(value, datetime.datetime):
			result = value.date()

		elif isinstance(value, datetime.date):
			result = value

		else:
			raise ConversionError(value, datatype)

	elif datatype == "time":
		if isinstance(value, basestring):
			try:
				value = GDateTime.parseISO(value)
			except GDateTime.InvalidDateError:
				raise ConversionError(value, datatype)

		if isinstance(value, datetime.datetime):
			result = value.time()

		elif isinstance(value, datetime.time):
			result = value

		elif isinstance(value, datetime.timedelta):
			result = (datetime.datetime(1, 1, 1) + value).time()

		else:
			raise ConversionError(value, datatype)

	elif datatype == "datetime":
		if isinstance(value, basestring):
			try:
				value = GDateTime.parseISO(value)
			except GDateTime.InvalidDateError:
				raise ConversionError(value, datatype)

		if isinstance(value, datetime.datetime):
			result = value

		elif isinstance(value, datetime.date):
			result = datetime.datetime(value.year, value.month, value.day)

		elif isinstance(value, datetime.time):
			# FIXME: remove with next release of gnue-common when generated
			# forms in gnue-appserver have been fixed to use the correct
			# datatype.
			gDebug(1, "WARNING: converting time to datetime")
			result = datetime.datetime(1900, 1, 1, value.hour, value.minute,
				value.second, value.microsecond)

		else:
			raise ConversionError(value, datatype)

	elif datatype == "boolean":
		if value in [0, "0", "f", "F", "false", "FALSE", "n", "N", "no", "NO",
			False]:
			result = False
		elif value in [1, "1", "t", "T", "true", "TRUE", "y", "Y", "yes", "YES",
			True]:
			result = True
		else:
			raise ConversionError(value, datatype)

	elif datatype == "array":
		result = value

	else:
		# Unknown datatype
		raise ConversionError(value, datatype)

	return result


# =============================================================================
# Singleton to represent an invalid value
# =============================================================================

class InvalidValueType(object):
	"""
	An invalid value, connected with an exception that defines why it is
	invalid.

	An instance of this class represents an invalid value. Like None, it is
	passed unchanged through type conversion.
	"""
	def __init__(self, exception):
		#: The exception that explains why this value is invalid.
		self.exception = exception
	def __str__(self):
		return "InvalidValue (%s)" % type(self.exception)
	def __unicode__(self):
		return u"InvalidValue (%s)" % type(self.exception)
	def __repr__(self):
		return "InvalidValue (%s)" % type(self.exception)


# =============================================================================
# Exceptions
# =============================================================================

class ConversionError(ValueError):
	"""
	Unable to convert the given value to the requested datatype.
	"""

	def __init__(self, value, datatype):
		ValueError.__init__(self,
			"Unable to convert %(value)r to datatype %(datatype)s" % {
				'value': value,
				'datatype': datatype})


# =============================================================================
# Self test code
# =============================================================================

if __name__ == '__main__':
	print repr(convert('abc', 'text', 0, 0))
	print repr(convert('123', 'number', 0, 0))
	print repr(convert(123, 'number', 10, 2))
	print repr(convert('2006-11-29', 'date', 0, 0))
	print repr(convert('17:18:19', 'time', 0, 0))
	print repr(convert(1, 'boolean', 0, 0))
