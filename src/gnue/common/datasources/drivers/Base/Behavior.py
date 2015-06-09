# GNU Enterprise Common Library - Base database driver - Schema behavior
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
# $Id: Behavior.py 9222 2007-01-08 13:02:49Z johannes $

"""
Generic Behavior class extended by all database driver plugins.
"""

__all__ = ['MissingTypeTransformationError', 'Behavior']

from gnue.common.apps import errors
from gnue.common.datasources import GSchema


# =============================================================================
# Exceptions
# =============================================================================

class MissingTypeTransformationError (errors.SystemError):
	"""
	Cannot transform this type into a native backend type.
	"""

	def __init__ (self, typename):
		msg = u_("No type transformation for '%s' found") % typename
		errors.SystemError.__init__ (self, msg)


# =============================================================================
# Basic schema creation and introspection class
# =============================================================================

class Behavior:
	"""
	Generic class for schema support.

	The Behavior class offers functions for creating new databases, extending the
	database schema and introspecting the schema. All important functions of this
	class are available through the L{Connection.Connection} object, so this
	class is never used directly.

	This class must be subclassed by all database drivers that want to offer
	schema support.

	@cvar _maxIdLength_: maximum length of an identifier or None if no
	  restriction.
	@cvar _type2native_: dictionary mapping field-types to native datatypes.

	@ivar _current: GSchema instance with the connection's current schema. This
	  tree will be set by writeSchema ().
	@ivar _new: GSchema instance with the schema as it should look like after
	  writeSchema ().
	@ivar _diff: GSchema instance containing the difference between _current and
	  _new. All items in this tree have an additional attribute '_action' which
	  determines the item's state within the diff. It can be one of 'add',
	  'change' or 'remove'.
	@ivar _lookups: dictionary where the keys are global identifiers that have
	  already been used in this connection, used to avoid duplicate global
	  identifier names.
	@ivar _elements: dictionary with the keys being table names and values being
	  dictionaries where the keys are local identifiers that have already been
	  used within that table. This is used to avoid duplicate local identifier
	  names.
	"""

	_maxIdLength_ = None                  # Maximum length of an identifier
	_type2native_ = {}                    # Mapping between GSD-Types and natives


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connection):
		"""
		Create a new Behavior instance.

		This is usually done silently when creating a connection instance.

		@param connection: The L{Connection.Connection} instance bound to this
		  Behavior instance.
		"""

		self.__connection = connection

		# Name-conversion mapping for element names
		self._lookups = {}

		# Per table mapping of elements
		self._elements = {}


	# ---------------------------------------------------------------------------
	# Nice string representation
	# ---------------------------------------------------------------------------

	def __repr__ (self):

		return "<Behavior for connection %s at %d>" % \
			(self.__connection.name, id (self))


	# ---------------------------------------------------------------------------
	# Create a new database
	# ---------------------------------------------------------------------------

	def createDatabase (self):
		"""
		Create a new database specified by the associated connection.
		"""

		assert gEnter (8)
		self._createDatabase_ ()
		assert gLeave (8)


	# ---------------------------------------------------------------------------
	# Update the current connection's schema with the given schema
	# ---------------------------------------------------------------------------

	def writeSchema (self, schema, simulation = False):
		"""
		Generate a command sequence to integrate the given schema tree into the
		connection's current schema.

		@param schema: GSchema object tree to be integrated in the connection's
		  current schema.
		@param simulation: if True, do not create the schema. Instead only the code
		  should be generated.
		@return: sequence of statements to be executed on the connection in order
		  to create/update the schema.
		"""

		checktype (schema, GSchema.GSSchema)

		assert gEnter (8)

		self._current = self.readSchema ()
		self._diff    = self._current.diff (schema, self._maxIdLength_)
		self._new     = schema

		self._lookups  = self.__getLookups (self._current)
		self._elements = {}

		assert gDebug (8, "Necessary schema changes:")
		assert gDebug (8, self._diff.dumpXML ())

		result = self._writeSchema_ (self._current, self._new, self._diff,
			simulation)

		assert gLeave (8, result)
		return result


	# ---------------------------------------------------------------------------
	# Read schema information from connection and return it as GSchema tree
	# ---------------------------------------------------------------------------

	def readSchema (self):
		"""
		Retrieve the connection's schema information and return it as L{GSchema}
		object tree.

		@return: current schema as L{GSchema} object tree.
		"""

		assert gEnter (8)

		result = GSchema.GSSchema ()
		author = self.__module__.replace ('gnue.common.datasources.drivers.', '')
		title  = u_("DB-Export of %s") % self.__connection.name
		result.buildAndInitObject (**{'author': author, 'title': title})

		self._readSchema_ (result)

		assert gLeave (8, result)
		return result


	# ---------------------------------------------------------------------------
	# Virtual methods to be implemented by descendants
	# ---------------------------------------------------------------------------

	def _createDatabase_ (self):
		"""
		Create a new database specified by the associated connection.
		"""
		raise NotImplementedError

	# ---------------------------------------------------------------------------

	def _writeSchema_ (self, current, new, diff, simulation = False):
		"""
		Change the schema for the connection. This method must be overwritten by
		descendants.

		@param current: Current state of the backend schema as found out by
		  L{_readSchema_}.
		@param new: New, desired state of the backend schema.
		@param diff: L{GSchema} object tree only containing the elements that have
		  to be added.
		@param simulation: if set to True, the schema should not be changed in the
		  backend, but only the command string should be generated and returned.
		@return: command string to change the schema as desired.
		"""
		raise NotImplementedError

	# ---------------------------------------------------------------------------

	def _readSchema_ (self, parent):
		"""
		Retrieve the connection's schema information and return it as L{GSchema}
		object tree. This method must be overwritten by descendants.

		@param parent: top level L{GSchema.GSSchema} object to be used as root for
		  the created tree.
		"""
		raise NotImplementedError


	# ---------------------------------------------------------------------------
	# Merge two triples of sequences
	# ---------------------------------------------------------------------------

	def _mergeTriple (self, result, source):
		"""
		Merge the sequences in the given triples and return the first one (which
		has been changed as a side effect too).

		This function is useful for descendants to build the command string for
		schema changes.

		@param result: triple of sequences which get extended
		@param source: triple of sequences to extend the result with
		@return: triple of merged sequences
		"""

		if len (result) != len (source):
			raise errors.SystemError, u_("Cannot merge triples of different length")

		for (dest, src) in zip (result, source):
			dest.extend (src)

		return result


	# ---------------------------------------------------------------------------
	# Make sure a given identifier doesn't exceed maximum length
	# ---------------------------------------------------------------------------

	def _shortenName (self, name, stripLast = False):
		"""
		Return the longest usable part of a given identifier.

		This function is useful for descendants to create identifiers when adding
		new objects to the schema.

		@param name: identifier to be checked
		@param stripLast: if True, the last character is cut off if name has at
		  least maximum length. This way one could append another character without
		  violating length restrictions.
		@return: identifier with extra characters cut off
		"""

		if self.__nameTooLong (name):
			result = name [:self._maxIdLength_ - (stripLast and 1 or 0)]
		else:
			result = name

		return result


	# ---------------------------------------------------------------------------
	# Transform a GSField's type attribute into a usable 'native type'
	# ---------------------------------------------------------------------------

	def _getNativetype (self, field):
		"""
		Get the apropriate native datatype for a given GSField's type attribute.
		If there is a method of the same name as the GSField's type this function
		will be called with the GSField as it's argument. If no such method is
		available, but the GSField's type is listed in the '_type2native_'
		dictionary, that value will be used. Otherwise an exception will be raised.

		This function is useful for descendants when adding new fields to the
		schema.

		@param field: GSField to get a native datatype for
		@return: string with the native datatype
		@raise MissingTypeTransformationError: if there is no conversion method
		  for the GSField's type
		"""

		if hasattr (field, 'type'):
			if hasattr (self, field.type):
				return getattr (self, field.type) (field)

			elif field.type in self._type2native_:
				return self._type2native_ [field.type]

			raise MissingTypeTransformationError, field.type

		else:
			return ""


	# ---------------------------------------------------------------------------
	# Create a usable name for a seuquence like object
	# ---------------------------------------------------------------------------

	def _getSequenceName (self, field):
		"""
		Create a name suitable for a sequence like object using the table- and
		fieldname.

		This function is intended to be used by descendants.

		@param field: GSField instance to create a sequence name for
		@return: string with a name for the given sequence
		"""

		table  = field.findParentOfType ('GSTable')
		result = "%s_%s_seq" % (table.name, field.name)

		if self.__nameTooLong (result):
			result = "%s_%s_seq" % (table.name, abs (id (field)))

		if self.__nameTooLong (result):
			result = "%s_seq" % (abs (id (field)))

		return self._shortenName (result)


	# ---------------------------------------------------------------------------
	# Create a unique name using a given lookup table
	# ---------------------------------------------------------------------------

	def _getSafeName (self, name, prefix = None):
		"""
		Return a unique name based on the current lookup-table, which does not
		exceed the maximum identifier length. If the optional prefix argument is
		given it will be used for building lookup-keys.

		This function is intended to be used by descendants.

		@param name: name to get a unique identifier for
		@param prefix: if given use this prefix for lookup-keys

		@return: unique name of at most _maxIdLength_ characters
		"""

		count   = 0
		pattern = prefix and "%s_%%s" % prefix or "%s"
		cname   = self._shortenName (name)

		while count < 10 and (pattern % cname) in self._lookups:
			cname  = "%s%d" % (self._shortenName (name, True), count)
			count += 1

		self._lookups [pattern % cname] = None

		return cname


	# ---------------------------------------------------------------------------
	# Check if a given identifier is too long
	# ---------------------------------------------------------------------------

	def __nameTooLong (self, name):

		return self._maxIdLength_ is not None and len (name) > self._maxIdLength_


	# ---------------------------------------------------------------------------
	# Build a lookup dictionary for all constraints and indices in a schema
	# ---------------------------------------------------------------------------

	def __getLookups (self, schema):

		result = {}.fromkeys (["CONSTRAINT_%s" % c.name for c in \
					schema.findChildrenOfType ('GSForeignKey', False, True)])
		result.update ({}.fromkeys (["INDEX_%s" % i.name for i in \
						schema.findChildrenOfType ('GSIndex', False, True)]))
		return result
