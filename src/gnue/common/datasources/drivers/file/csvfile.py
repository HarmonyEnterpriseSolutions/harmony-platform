# GNU Enterprise Common Library - CSV file database driver
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
# $Id: csvfile.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for CSV file backends.
"""

__all__ = ['Connection']

import csv

from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers.file import Base


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "CSV files"

	description = """
CSV files are flat ASCII files where records are separated by newlines and
fields are separated by a special character, like a comma or a semicolon.

The CSV file driver is primarly provided to help with migration of legacy data.
"""

	doc = """
Description
-----------
The GNUe CSV file driver uses Python's built-in csv module. It supports
auto-guessing of the field separator and the quoting character.

Connection Properties
---------------------
* filename -- File name of the CSV file. Can contain %(home)s, %(configdir)s,
  and %(table)s placeholders. Using the %(table)s placeholder, this driver
  can be used to emulate a database with several tables.

Examples
--------
  [myconn]
  provider = csvfile
  filename = %(home)s/data/%(table)s.csv

Notes
-----
1. This driver does not support write access.
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Connection class for CSV file backends.
	"""

	# ---------------------------------------------------------------------------
	# Iterate through the list of field names
	# ---------------------------------------------------------------------------

	def _listFields_ (self, table):

		result = GSchema.GSFields (None)
		(f, dialect, fieldnames) = self.__prepareFile (table.filename)

		for fieldname in fieldnames:
			GSchema.GSField (result, id = fieldname,
				name = fieldname,
				type = 'string',
				nativetype = 'string',
				nullable = True)

		return result


	# ---------------------------------------------------------------------------
	# Load the file
	# ---------------------------------------------------------------------------

	def _loadFile_ (self, filename, table):

		(f, dialect, fieldnames) = self.__prepareFile (filename)

		reader = csv.DictReader (f, fieldnames, dialect = dialect)

		# Make a real list of dictionaries
		return [row for row in reader]


	# ---------------------------------------------------------------------------
	# Prepare the file
	# ---------------------------------------------------------------------------

	def __prepareFile (self, filename):

		f = file (filename, 'rb')

		# Let the sniffer determine the file format
		sniffer = csv.Sniffer ()
		dialect = sniffer.sniff (f.readline ())

		# Rewind file
		f.seek (0)

		# Read the first row to get the field names
		fieldnames = (csv.reader (f, dialect)).next ()

		return (f, dialect, fieldnames)
