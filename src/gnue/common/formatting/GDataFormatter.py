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
# GRLayout.py
#
# DESCRIPTION:
# Class
#
# NOTES:
#
# HISTORY:
#

from types import *
from gnue.common.external.fixedpoint import FixedPoint, addHalfAndChop
FixedPoint.round = addHalfAndChop


def applyFormatting (value, mask):
	# This obviously doesn't do anything with the mask yet
	# Just returns a string
	if value == None:
		return ""
	elif mask:

		# TODO: This whole section should be using FormatMasks
		# TODO: This is all a gross hack!!!!
		try:
			return value.strftime(str(mask))
		except AttributeError:
			pass

		# TODO: As said above, this is a bad hack w/a lot of assumptions
		if type(value) == FloatType:
			v = mask.split('.',1)
			try:
				dec = len(v[1])
			except:
				dec = 0
			comma = mask.find(',') + 1

			if v[0][:1] == '$':
				rv = "$"
			else:
				rv = ""

			value = FixedPoint(value,dec)
			fract = "%s" % value.frac()
			fract = fract.split('.')[1]
			whole = int(value)
			wstr = str(abs(whole))

			if comma:
				commas, leading = divmod(len(wstr),3)
				if not leading and commas:
					commas -= 1
					leading += 3
				if leading:
					rv += wstr[:leading]

				wstr = wstr[leading:]
				for i in range(commas):
					rv += ',' + wstr[:3]
					wstr = wstr[3:]

			if dec:
				rv += ".%s" % fract
			if value < 0:
				rv = '-' + rv
			return rv

	return "%s" % value


if __name__ == '__main__':
	print applyFormatting(1.444,'#,##0.00')
	print applyFormatting(12.444,'#,##0.00')
	print applyFormatting(123.444,'#,##0.00')
	print applyFormatting(1234.444,'#,##0.00')
	print applyFormatting(12345.444,'#,##0.00')
	print applyFormatting(123456.444,'#,##0.00')
