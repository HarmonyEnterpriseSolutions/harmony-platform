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
# FILE:
# TextUtils.py
#
# NOTES:
"""
Common text-related utilities
"""
__revision__ = "$Id"

import formatter, htmllib, StringIO

ALIGN_LEFT   = 0
ALIGN_RIGHT  = 1
ALIGN_CENTER = 2

# very simple lineWrap
# TODO: Deprecate in favor of Python 2.3's textwrap module
def lineWrap(message, maxWidth, preserveNewlines=1,
	alignment=ALIGN_LEFT, eol=1):
	"""
	A simple linewrap function.

	@param message:   The string to wrap
	@param maxWidth:  The maximum string width allowed.
	@param preserveNewlines: If true then newlines are left in the string
	                         otherwise they are removed.
	@param alignment: The alignment of the returned string based upon
	                  a width of maxWidth.

	                  Possible values (ALIGN_LEFT, ALIGN_RIGHT, ALIGN_CENTER)

	@param eol: If true then the last character of the return value
	            will be a newline

	@return: The properly wrapped text string.
	@rtype: string
	"""

	text = ""

	temptext = str(message).strip()
	if preserveNewlines:
		buff = temptext.split("\n")
	else:
		buff = (temptext, )

	for strings in buff:
		while len(strings) > maxWidth:
			index = 0

			for sep in [' ', ',', ':', '.', ';']:
				ind = strings.rfind(sep, 0, maxWidth-1)+1
				index = max(ind, index)

			if index > maxWidth or index == 0:
				index = maxWidth-1

			line = strings[:index]
			if alignment == ALIGN_CENTER:
				line = ' ' * ( (maxWidth - len(line)) /2 ) + line
			elif alignment == ALIGN_RIGHT:
				line = ' ' * ( (maxWidth - len(line)) ) + line
			text += "%s\n" % line
			strings = strings[index:]

		line = strings
		if alignment == ALIGN_CENTER:
			line = ' ' * ( (maxWidth - len(line)) /2 ) + line
		elif alignment == ALIGN_RIGHT:
			line = ' ' * ( (maxWidth - len(line)) ) + line
		text += "%s\n" % line

	if not eol:
		return text[:-1]
	else:
		return text


def textToMeasurement(text, multiplier=1):
	"""
	Converts most standard measurements to inches.

	Sample Usage:

	>>> textToMeasurement('72pt')
	1.0
	>>> # convert to 72 point output
	... textToMeasurement('1.27cm',72)
	36.0

	@param text: A string containing the measurement to convert
	             The following measurements are accepted
	             (pt, cm, mm, in)
	@type text: string
	@param multiplier: A multiplier used to adjust the output
	                   to values other inches.
	@type multiplier: number

	@return: The converted value
	@rtype: number
	"""
	if text[-1].isdigit():
		value = float(text) / 72 * multiplier
	else:
		unit = text[-2:]
		text = text[:-2]
		value = float(text) / {'pt':72, 'in':1, 'cm':2.54,
			'mm': 25.4}[unit.lower()] * multiplier

	return value


def intToRoman(num):
	"""
	Convert an integer to a roman numeral.

	Sample Usage:

	>>> intToRoman(1999)
	'MCMXCIX'

	@param num: The number to convert
	@type num: integer

	@return: The roman numeral equivalent.
	@rtype: string
	"""
	number = int(num) # just in case
	output = ""
	for dec, roman in (
		(1000, 'M'), (900, 'CM', ),
		(500, 'D'), (400, 'CD'), (100, 'C'),
		(90, 'XC'),(50, 'L'), (40, 'XL'),
		(10, 'X'), (9, 'IX'), (5, 'V'),
		(4, 'IV'), (1, 'I') ):
		while (number >= dec):
			number -= dec;
			output += roman;
	return output


def dollarToText(num):
	"""
	Convert a number to "dollar" notation (suitable for use on checks)
	e.g., 123.24 --> "One Hundred Twenty Three and 24/100"

	Sample Usage:

	>>> dollarToText(1120.15)
	'One Thousand One Hundred Twenty and 15/100'

	@param num: The numeric amount
	@type num: number

	@return: The full text equivalent of the number.
	@rtype: string
	"""
	whole = int(num)
	cents = round((num-whole)*100)
	output = 'and %02d/100' % cents
	if whole:
		thirdRange = 0
		while whole:
			whole, segment = divmod(whole, 1000)
			hundreds, tens = divmod(segment, 100)
			try:
				output = _smallDollarMap[tens] + _thirdDollarMap[thirdRange] + output
			except IndexError:
				ten, ones = divmod(tens, 10)
				output = _tenDollarMap[ten] + _smallDollarMap[ones] + \
					_thirdDollarMap[thirdRange] + output
			if hundreds:
				output = _smallDollarMap[hundreds] + 'Hundred ' + output
			thirdRange += 1
	else:
		output = 'Zero ' + output

	return output


_smallDollarMap = ('', 'One ', 'Two ', 'Three ', 'Four ', 'Five ',
	'Six ', 'Seven ', 'Eight ', 'Nine ', 'Ten ',
	'Eleven ', 'Twelve ', 'Thirteen ', 'Fourteen ',
	'Fifteen ', 'Sixteen ', 'Seventeen ', 'Eighteen ',
	'Nineteen ' )
_tenDollarMap = ('', '', 'Twenty ', 'Thirty ', 'Forty ', 'Fifty ',
	'Sixty ', 'Seventy ', 'Eighty ', 'Ninety ')
_thirdDollarMap = ('', 'Thousand ', 'Million ', 'Billion ', 'Trillion ')



# Comify a number
def comify(num, decimals=2, parenthesis=False):
	"""
	Comify a number (e.g., print -9900 as -9,900.00)

	Sample Usage:

	>>> comify(-9999.934, 2)
	'-9,999.93'
	>>> comify(-9999.934, 2, 1)
	'(9,999.93)'

	@param num: The number to reformat
	@type num: number
	@param decimals: The number of decimal places to retain
	@type decimals: number
	@param parenthesis: If true then negative numbers will be returned inside parenthesis
	@type  parenthesis: boolean

	@return: A properly formatted number
	@rtype: string
	"""
	neg = num < 0
	num = abs(num)
	whole, dec = ( ( ( ("%%12.%sf" % decimals) % abs(num)).strip()).split('.') +
		[""])[:2]
	if len(dec):
		dec = "." + dec

	output = ""

	for i in range(divmod(len(whole), 3)[0]+1):
		j = len(whole) - i*3
		output = "," + whole[j > 3 and j-3 or 0:j] + output

	output += dec

	while output[:1] == ',':
		output = output[1:]

	if neg:
		if parenthesis:
			output = "(%s)" % output
		else:
			output = "-" + output
	elif parenthesis:
		output += " "

	return output


def stripHTML(htmlString):
	"""
	Removes all html mark-up from a text string.

	@param htmlString: The text containing the html mark up
	@type htmlString: String
	@return: The string minus any html markup
	@rtype: String
	"""
	# This is based upon code found at
	# http://online.effbot.org/2003_08_01_archive.htm#20030811
	#
	# It looks as if the original code is in the public domain
	# per http://effbot.org/zone/copyright.htm
	#
	class Parser(htmllib.HTMLParser):
		"""
		Private class for strip HTML
		"""
		def anchor_end(self):
			self.anchor = None

	class Formatter(formatter.AbstractFormatter):
		"""
		Private class for strip HTML
		"""
		pass

	class Writer(formatter.DumbWriter):
		"""
		Private class for strip HTML
		"""
		def send_label_data(self, data):
			"""
			"""
			self.send_flowing_data(data)
			self.send_flowing_data(" ")

	output = StringIO.StringIO()
	parser = Parser(Formatter(Writer(output)))
	parser.feed(htmlString)
	parser.close()

	return output.getvalue()
