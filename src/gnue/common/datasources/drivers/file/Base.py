# GNU Enterprise Common Library - Generic file based database driver
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
# $Id: Base.py 9222 2007-01-08 13:02:49Z johannes $

"""
Generic database driver plugin for file based backends.
"""

__all__ = ['Behavior', 'ResultSet', 'Connection']

__noplugin__ = True

import glob
import os

from gnue import paths
from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers import Base


# =============================================================================
# Schema support class
# =============================================================================

class Behavior (Base.Behavior):
	"""
	Generic Behavior class for file based backends.
	"""

	# ---------------------------------------------------------------------------
	# Read the connection's schema
	# ---------------------------------------------------------------------------

	def _readSchema_ (self, parent):
		"""
		Read the connection's schema and build a GSchema object tree connected to
		the given parent object (which is of type GSSchema).
		"""

		filename = self.__connection._getFilename ('*')

		for fname in glob.glob (filename):
			tables = self.__connection._listTables_ (fname)
			if tables is not None:
				master = parent.findChildOfType ('GSTables')
				if master is None:
					parent.addChild (tables)
					tables.setParent (parent)
				else:
					for table in tables.findChildrenOfType ('GSTable', False, True):
						master.addChild (table)
						table.setParent (master)

		# Add all fields, indices and constraints to the tables
		for table in parent.findChildrenOfType ('GSTable', False, True):
			for item in [self.__connection._listFields_ (table),
				self.__connection._listPrimaryKey_ (table),
				self.__connection._listIndices_ (table),
				self.__connection._listConstraints_ (table)]:
				if item is not None:
					table.addChild (item)
					item.setParent (table)



# =============================================================================
# ResultSet class
# =============================================================================

class ResultSet (Base.ResultSet):
	"""
	Generic ResultSet class for file based backends.
	"""

	# ---------------------------------------------------------------------------
	# Implementation of virtual methods
	# ---------------------------------------------------------------------------

	def _query_object_ (self, connection, table, fieldnames, condition, sortorder,
		distinct):
		self.__data = connection._getFile (table)
		self.__fieldnames = fieldnames
		self.__condition  = condition       # currently not honored
		self.__sortorder  = sortorder       # currently not honored
		self.__distinct   = distinct        # currently not honored

	# ---------------------------------------------------------------------------

	def _count_ (self):
		return len (self.__data)

	# ---------------------------------------------------------------------------

	def _fetch_ (self, cachesize):
		for row in self.__data:
			result = {}
			for fn in self.__fieldnames:
				result [fn] = row.get (fn)
			yield result


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Generic Connection class for file based backends.
	"""

	_resultSetClass_ = ResultSet
	_behavior_       = Behavior


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections, name, parameters):

		Base.Connection.__init__ (self, connections, name, parameters)

		if parameters.has_key ("filename"):
			self.__filename = parameters ['filename']
		elif parameters.has_key ("file"):
			self.__filename = parameters ['file']
		else:
			self.__filename = parameters ['dbname']

		# We can replace some of the parameters right away
		self.__filename = self.__filename % {'home'     : os.environ.get('HOME', ""),
			'configdir': paths.config,
			'table'    : '%(table)s'}


	# ---------------------------------------------------------------------------
	# Implementation of (some) virtual methods
	# ---------------------------------------------------------------------------

	def _requery_ (self, table, oldfields, fields, parameters):
		for row in self._getFile (table):
			found = True
			for (fieldname, value) in oldfields:
				if row.get (fieldname) != value:
					found = False
			if found:
				result = {}
				for fieldname in fields:
					result [fieldname] = row.get (fieldname)
				return result


	# ---------------------------------------------------------------------------
	# Get the filename for a given table
	# ---------------------------------------------------------------------------

	def _getFilename (self, table):
		"""
		Return the filename to be used for a given table.

		@param table: Table name.
		@return: Filename.
		"""

		return self.__filename % {'table': table}


	# ---------------------------------------------------------------------------
	# Get the data of a file
	# ---------------------------------------------------------------------------

	def _getFile (self, table):
		"""
		Return data from the file.

		@param table: Table name.
		@return: iterable object of fieldname/value dictionaries containing the
		    records of the file.
		"""

		return self._loadFile_ (self._getFilename (table), table)


	# ---------------------------------------------------------------------------
	# Virtual methods (to be implemented by descendants)
	# ---------------------------------------------------------------------------

	def _listTables_ (self, filename):
		"""
		List all the table names contained in the given file.

		This function must return either None if there are no tables or a GSTables
		instance containing all tables available.

		Table names can be mixed case.

		The default behaviour of this function is to extract the table name from
		the file name (if the filename parameter of the connection contains a
		'%(table)s') and return 'data' otherwise.

		Descendants only have to overwrite this function if a file can contain more
		than one table.

		This method is used for introspection.

		@param filename: Filename
		@return: GSTables instance or None
		"""

		f = self._getFilename ('\n')
		if '\n' in f:
			(prefix, postfix) = f.split ('\n', 1)
			if filename [:len (prefix)] == prefix and \
				filename [-len (postfix):] == postfix:
				table = filename [len (prefix):-len (postfix)]
			else:
				table = filename
		else:
			table = 'data'

		result = GSchema.GSTables (None, type = 'table', name = u_('Tables'))
		GSchema.GSTable (result, id = table, name = table, filename = filename)

		return result

	# ---------------------------------------------------------------------------

	def _listFields_ (self, table):
		"""
		List all the field names available for a table.

		This function must return either None if there are no fields available, or
		a GSFields instance containing all fields. The GSFields instance must *not*
		have a parent.

		Field names can be mixed case.

		This method is used for introspection.

		@param table: GSTable instance to get the fields for
		@return: GSFields instance or None
		"""

		return None

	# ---------------------------------------------------------------------------

	def _listIndices_ (self, table):
		"""
		List all available indices for a table.

		This function must return a GSIndexes instance with all available indices
		or None if there are no indices at all. The GSIndexes instance must *not*
		have a parent.

		This method is used for introspection.

		@param table: GSTable instance to get the fields for
		@return: GSIndexes instance or None
		"""

		return None

	# ---------------------------------------------------------------------------

	def _listPrimaryKey_ (self, table):
		"""
		List the primary key for a table.

		This function must return a GSPrimaryKey instance holding the primary key
		definition for the table or None if it has no such key. The GSPrimaryKey
		instance must *not* have a parent.

		This method is used for introspection.

		@param table: GSTable instance to get the fields for
		@return: GSPrimaryKey instance or None
		"""

		return None

	# ---------------------------------------------------------------------------

	def _listConstraints_ (self, table):
		"""
		List all available constraints for a table.

		This function must return a GSConstraints instance with all available
		constraints or None if there are no constraints at all. The GSConstraints
		instance must *not* have a parent.

		This method is used for introspection.

		@param table: GSTable instance to get the fields for
		@return: GSConstraints instance or None
		"""

		return None

	# ---------------------------------------------------------------------------

	def _loadFile_ (self, filename, table):
		"""
		Load data from a file.

		@param filename: Filename
		@param table: Table name (only useful if a file can contain more than one
		  table)
		@return: iterable object of fieldname/value dictionaries containing the
		    records of the file. This object must implement __len__ ().
		"""
		return []
