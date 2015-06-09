# GNU Enterprise Common Library - Utilities - CSV writer
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
# $Id: ucsv.py 9222 2007-01-08 13:02:49Z johannes $
"""
This module provides a csv.DictWriter class which is able to handle unicode
values.  Additionally floats will be converted using the proper decimal-point
character according to locale.
"""

__all__ = ['UDictWriter']

import csv
import locale
import gnue


# =============================================================================
# A dialect using a semicolon as delimiter
# =============================================================================

class ExcelSemicolon(csv.excel):
	"""
	Use a semicolon as delimiter instead of the colon.
	"""
	delimiter = ';'

csv.register_dialect("ExcelSemicolon", ExcelSemicolon)

# =============================================================================
# Unicode-capabel DictWriter
# =============================================================================

class UDictWriter(csv.DictWriter):
	"""
	Descendant of the DictWriter which is able to handle unicode values.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, fileobject, fieldnames, dialect="ExcelSemicolon",
		encoding="utf-8", encode_errors="replace"):

		self.encoding = encoding
		self.encode_errors = encode_errors
		csv.DictWriter.__init__(self, fileobject, fieldnames, "", "ignore",
			dialect)


	# -------------------------------------------------------------------------
	# Convert a row dictionary into a sequence to write
	# -------------------------------------------------------------------------

	def _dict_to_list(self, rowdict):
		"""
		Convert the given row dictionary into a list of values to be sent to
		the writer object.
		"""

		ndict = {}
		for (key, value) in rowdict.items():
			if isinstance(value, unicode):
				value = value.encode(self.encoding, self.encode_errors)
			if isinstance(value, float):
				value = locale.str(value)

			ndict[key] = value

		return csv.DictWriter._dict_to_list(self, ndict)


# =============================================================================
# Shorthand for creating a CSV file from a dictionary
# =============================================================================

def write_file(fieldnames, data, filename, dialect="ExcelSemicolon",
	encoding="utf-8", encode_errors="replace", caption=None):
	"""
	Create a CSV file using the given fieldnames and data
	@param fieldnames: list of fields to export
	@param data: list of dictionaries with the data to export
	@param filename: name of the file to export the data to
	@param dialect: name of a registered dialect (as used by the csv module)
	@param encoding: an encoding used for unicode values
	@param encode_errors: error handling schema for encoding
	@param caption: dictionary giving a nice caption per column.  If no such
	    mapping is provided the fieldnames will be used as header line
	"""
	fhd = open(filename, 'wb')
	try:
		writer = UDictWriter(fhd, fieldnames, dialect, encoding, encode_errors)

		if not caption:
			caption = {}
			for field in fieldnames:
				caption[field] = field
		writer.writerow(caption)
		writer.writerows(data)

	finally:
		fhd.close()


# =============================================================================
# Selftest
# =============================================================================

if __name__ == '__main__':

	import datetime

	xk = u'bar\xf6xy'
	test = [{'foo': u'Bl\xf6di', xk: None, 'sepp': 7.41, 'noo': 100},
		{'foo': u'Bl\xf6di und so', xk: None, 'sepp':
			datetime.date.today(), 'noo': 100},
		{'foo': u'Bl\xf6di, und;so', xk: None, 'sepp':
			datetime.date.today(), 'noo': 100},
	]

	write_file(test[0].keys(), test, 'out.csv', encoding="cp1250")
