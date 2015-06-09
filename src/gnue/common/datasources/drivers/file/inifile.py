# GNU Enterprise Common Library - INI file database driver
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
# $Id: inifile.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for INI style configuration file backends.
"""

__all__ = ['Connection']

import ConfigParser

from gnue.common.apps import errors
from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers.file import Base


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "INI style configuration files"

	description = """
INI files are configuration files in the style of Samba's "smb.conf". Sections
(introduced by a line enclosed in brackets) are considered records, and the
parameters in this section are considered the fields of the record.

The INI file driver is primarly provided to make it possible to use GNUe-Forms
to edit configuration files (like connections.conf).
"""

	doc = """
Description
-----------
The GNUe INI file driver uses Python's built-in configfile module. It does not
depend on any external module.

Connection Properties
---------------------
* filename -- File name of the INI file. Can contain %(home)s, %(configdir)s,
  and %(table)s placeholders.

Examples
--------
  [myconn]
  provider = inifile
  filename = %(configdir)s/connections.conf

Notes
-----
1. This driver is not intended to be used with real data.
"""


# =============================================================================
# Exceptions
# =============================================================================

class DuplicateSectionError (errors.UserError):
	"""
	Duplicate section name on insert or update.
	"""
	def __init__ (self, section):
		errors.UserError.__init__ (self, u_("Duplicate section name %s") % section)

class MissingSectionError (errors.UserError):
	"""
	Section name not given on insert or update.
	"""
	def __init__ (self):
		errors.UserError.__init__ (self, u_("Missing section name"))


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Connection class for INI style configuration file backends.
	"""

	_primarykeyFields_ = ['_section_name']


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, *params, **kwargs):

		Base.Connection.__init__ (self, *params, **kwargs)

		self.__parsers = {}                 # ConfigParser objects per table
		self.__dirty = {}                   # Dirty status per table


	# ---------------------------------------------------------------------------
	# Iterate through the list of field names
	# ---------------------------------------------------------------------------

	def _listFields_ (self, table):

		result = GSchema.GSFields (None)
		parser = self.__getParser (table.filename, table.name)

		fields = {}

		for section in parser.sections ():
			for fieldname in parser.options (section):
				fields [fieldname] = {'id':         fieldname,
					'name':       fieldname,
					'type':       'field',
					'nativetype': 'text',
					'datatype':   'text',
					'required':    False}

		for item in fields.values ():
			GSchema.GSField (result, **item)

		return result


	# ---------------------------------------------------------------------------
	# Load the file
	# ---------------------------------------------------------------------------

	def _loadFile_ (self, filename, table):

		parser = self.__getParser (filename, table)

		return [dict ([('_section_name', section)] + parser.items (section)) \
				for section in parser.sections ()]


	# ---------------------------------------------------------------------------
	# Prepare the file
	# ---------------------------------------------------------------------------

	def __getParser (self, filename, table):

		if not self.__parsers.has_key (table):
			parser = ConfigParser.RawConfigParser ()
			parser.read (filename)
			self.__parsers [table] = parser
		return self.__parsers [table]


	# ---------------------------------------------------------------------------
	# Insert new record
	# ---------------------------------------------------------------------------

	def _insert_ (self, table, newfields):

		parser = self.__getParser (self._getFilename (table), table)

		section = newfields.get ('_section_name')

		if section in parser.sections ():
			raise DuplicateSectionError

		if not section:
			raise MissingSectionError

		parser.add_section (section)

		self.__setFields (parser, section, newfields)

		self.__dirty [table] = True


	# ---------------------------------------------------------------------------
	# Update existing record
	# ---------------------------------------------------------------------------

	def _update_ (self, table, oldfields, newfields):

		parser = self.__getParser (self._getFilename (table), table)

		section = oldfields.get ('_section_name')

		# Handle section name change
		if "_section_name" in newfields and newfields ["_section_name"] != section:

			oldsection = section

			section = newfields ['_section_name']

			if section in parser.sections ():
				raise DuplicateSectionError

			if not section:
				raise MissingSectionError

			parser.add_section (section)

			for option in parser.options (oldsection):
				parser.set (section, option, parser.get (oldsection, option))

			parser.remove_section (oldsection)

		self.__setFields (parser, section, newfields)

		self.__dirty [table] = True


	# ---------------------------------------------------------------------------
	# Set fields (used by _insert_ and _update_)
	# ---------------------------------------------------------------------------

	def __setFields (self, parser, section, fields):

		for (field, value) in fields.items ():
			if field != '_section_name':
				if value == '' or value is None:
					parser.remove_option (section, field)
				else:
					parser.set (section, field, value)


	# ---------------------------------------------------------------------------
	# Delete record
	# ---------------------------------------------------------------------------

	def _delete_ (self, table, oldfields):

		parser = self.__getParser (self._getFilename (table), table)

		section = oldfields.get ('_section_name')

		dataCon.remove_section (section)

		self.__dirty [table] = True


	# ---------------------------------------------------------------------------
	# Write changes back to the file
	# ---------------------------------------------------------------------------

	def _commit_ (self):

		for table in self.__dirty.keys ():
			f = open (self._getFilename (table), "w+")
			(self.__parsers [table]).write (f)
			f.close ()

		self.__dirty = {}


	# ---------------------------------------------------------------------------
	# Undo changes
	# ---------------------------------------------------------------------------

	def _rollback_ (self):

		# Just clean the cache; will cause each file to be re-read on next access
		self.__parsers = {}
		self.__dirty = {}
