# GNU Enterprise Common Library - Utilities - locale extensions
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
# $Id: xlocale.py 9547 2007-05-03 06:53:01Z reinhard $
"""
Helper functions which we think are missing in python's locale module.
"""

import locale
import re

__all__ = ['format_numeric']

# =============================================================================
# Format a numeric value according to LC_NUMERIC or the given pattern
# =============================================================================

def format_numeric(fmt_string, value, pattern=None):
	"""
	Format a numeric value using a conversion specifier (fmt_string) and apply
	grouping (thousands separating, decimal point) according to a given pattern
	or as defined by the current locale.

	The grouping-pattern used for thousands separating and definition of the
	decimal point.  The format of this string is <thousand-separator><number of
	digits><decimal separator> where the pair <thousand-separator><number of
	digits> can be repeated.

	Examples: assume a call of format_numeric('%.2f', 1234567.89, pat) with
	    - pat =   ',3.'   result is 1,234,567.89
	    - pat = ',3.3,'   result is 1,234.567,89
	    - pat = '#2.1;'   result is 1#23.4#56.7;89

	In the last example you can see that the grouping pattern will be repeated
	as a whole.

	@param fmt_string: conversion specifier as used by pythons string
	    formatting, i.e. %.2f or %d
	@param value: numeric value to be formatted.  This value will be converted
	    using @L{fmt_string} and that result get's processed according to
	    either the grouping-pattern or the locales default.
	@param pattern: the grouping-pattern used for thousands separating and
	    definition of the decimal point.  If no pattern is given (None),
	    thousands separating and decimal point replacement is done by the
	    locale.

	@returns: a formatted string according to the given conversion specifier as
	    well as thousands-separating and decimal point replacement as defined
	    by the pattern or locale.
	"""

	# If we don't have a pattern for grouping we pass the job back to the
	# locales format method.
	if pattern is None:
		result = locale.format(fmt_string, value, True)
	else:
		# Catch the decimal separator
		dec_sep = pattern[-1]
		pattern = pattern[:-1]

		# Break the given pattern into separator groups
		pat = re.compile('.*?(\D+)(\d+)$')
		match = pat.match(pattern)
		groups = []
		while match:
			sep, offs = match.groups()
			groups.append((sep, int(offs)))
			off = len(sep) + len(offs)
			pattern = pattern[:-off]
			match = pat.match(pattern)

		# Build the raw string according to the conversion string
		result = fmt_string % value

		# Store the sign
		if result[0].isdigit():
			sign = ''
		else:
			sign = result[0]
			result = result[1:]

		# Take away the fractional part since it is not needed for grouping
		match = re.match('(.*?)\.(\d*)$', result)
		if match:
			result, fractional = match.groups()
			fractional = dec_sep + fractional
		else:
			fractional = ''

		# Now perform the grouping from right to left
		if groups:
			rest = result
			result = ''

			while rest:
				for (sep, pos) in groups:
					if len(rest) <= pos:
						result = rest + result
						rest = ''
						break

					result = sep + rest[-pos:] + result
					rest = rest[:-pos]

		# And finally stick all parts together again
		result = sign + result + fractional

	return result


# =============================================================================
# Modules self test code
# =============================================================================

if __name__ == '__main__':

	locale.setlocale(locale.LC_ALL, '')

	def check(fmt, val, group=None):
		""" show and run a test for format_numeric() """
		print "Fmt: %s Group: %s Value: %s = %s" % \
			(fmt, group, val, format_numeric(fmt, val, group))

	val1 = 1234567891234567.236
	check('%.2f', val1)
	check('%.2f', val1, ',4.3,')
	check('%.2f', val1, ',3.3,')
	check('%.3f', 12, ',3.3,')
	check('%.4f', 1234.52, 'x2;')
	check('%d', 1234, ',3.')
	check('%.2f', 1234567.89, ',3.')
	check('%.2f', 1234567.89, ',3.3,')
	check('%.2f', 1234567.89, '#2.1;')
