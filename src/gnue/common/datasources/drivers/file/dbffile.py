# GNU Enterprise Common Library - DBF file database driver
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
# $Id: dbffile.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for DBF file backends.
"""

__all__ = ['Connection']

from gnue.common.utils import dbf
from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers.file import Base


# =============================================================================
# Driver Info
# =============================================================================

class DriverInfo:

	name = "DBF files (DBase, XBase etc.)"

	description = """
DBF files are a file format often used in old DOS applications. Each DBF file
contains data for a single table.

The DBF file driver is primarly provided to help with migration of legacy data.
"""

	doc = """
Description
-----------
The GNUe DBF file driver comes with its own file parsing routines and does not
depend on any external module.

Connection Properties
---------------------
* filename -- File name of the DBF file. Can contain %(home)s, %(configdir)s,
  and %(table)s placeholders. Using the %(table)s placeholder, this driver
  can be used to emulate a database with several tables.

Examples
--------
  [myconn]
  provider = dbffile
  filename = %(home)s/data/%(table)s.dbf

Notes
-----
1. This driver does not support write access.
"""


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Connection class for DBF file backends.
	"""

	__datatypes = {'C': 'string',
		'N': 'number',
		'D': 'date',
		'L': 'boolean'}


	# ---------------------------------------------------------------------------
	# Iterate through the list of field names
	# ---------------------------------------------------------------------------

	def _listFields_ (self, table):

		result = GSchema.GSFields (None)

		f = dbf.dbf (table.filename)

		for (name, ftype, length, scale, index) in f.fields:
			field = GSchema.GSField (result, id = name,
				name = name,
				nativetype = ftype,
				type = self.__datatypes [ftype],
				nullable = True)
			# Date  and boolean types have no length and scale
			if not ftype in ['D', 'L']:
				if length:
					field.length = length
				if scale:
					field.precision = scale

		return result


	# ---------------------------------------------------------------------------
	# Load the file
	# ---------------------------------------------------------------------------

	def _loadFile_ (self, filename, table):

		return dbf.dbf (filename)
