# GNU Enterprise Common Library - Generic DBSIG2 database driver - Behavior
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
Generic Behavior class for DBSIG2 based database driver plugins.
"""

all = ['Behavior']

from gnue.common.datasources import GSchema
from gnue.common.datasources.drivers import Base


# =============================================================================
# Behavior class
# =============================================================================

class Behavior (Base.Behavior):
	"""
	Generic Behavior class for SQL based backends using a DBSIG2 compatible
	Python module.

	As schema creation is pretty well standardized among SQL based backends and
	schema introspection works differently for each database, this class
	implements pretty much of the dirty work for _writeSchema_ but leaves
	_readSchema_ completely unimplemented.

	@cvar _writeableTypes_: list of GSTables-types to be handled by
	  writeSchema ().  GSTables instances of other types (ie. views) are ignored.
	@cvar _alterMultiple_: boolean flag indicating wether an 'alter table'
	  statement can contain multiple fields or not.
	@cvar _extraPrimaryKey_: boolean flag indicating wether primary keys must be
	  added with an extra command (ie. alter table) or not.
	@cvar _numbers_: triple specifying rules for datatype transformation of
	  numeric types. The first element is a sequence of tuples (maxlen, type). If
	  the numeric field has no precision (it's a whole number) this sequence will
	  be iterated in an ascending order using the first suitable (length <=
	  maxlen) item. The second element of the triple is a fallback-type for whole
	  numbers if the requested length exceeds all tuples in the previous
	  sequence. This type must take a single argument (ie. 'numeric(%s)') which
	  will be set to the requested length. The last element of the triple is a
	  format string used for numeric types with precision (floats). It must
	  contain a '%(length)s' and a '%(scale)s' placeholder, i.e.
	  "numeric (%(length)s,%(scale)s)".
	"""

	_writeableTypes_  = ['table']
	_alterMultiple_   = True
	_extraPrimaryKey_ = False
	_numbers_         = ([], None, None)
	_type2native_     = {'datetime': 'datetime',
		'time'    : 'time',
		'date'    : 'date'}

	# ---------------------------------------------------------------------------
	# Generate a code sequence to match the requested schema
	# ---------------------------------------------------------------------------

	def _writeSchema_ (self, current, new, diff, simulation = False):
		"""
		Integrate the given schema into the current connection's schema and return
		the commands used to achive this. Optionally a simulation for the
		integration is possible. In that case no real change will take place in the
		backend.

		@param current: GSchema tree with the current schema at the backend
		@param new: GSchema tree with the schema to be achieved
		@param diff: GSchema tree with the differences between current and new
		@param simulation: if True, only create the command sequence

		@return: sequence of commands to be executed for changing the current
		    schema into the new one
		"""

		if diff is None:
			return []

		result = (prolog, main, epilog) = ([], [], [])

		for block in diff.findChildrenOfType ('GSTables', False, True):
			if not block.type in self._writeableTypes_:
				continue

			for table in block.findChildrenOfType ('GSTable', False, True):
				# We do not drop tables
				if table._action in ['add', 'change']:
					self._mergeTriple (result, self._createTable_ (table))

		code = prolog + main + epilog

		if not simulation:
			for command in code:
				self.__connection.sql0 (command)

			self.__connection.commit ()

		return code


	# ---------------------------------------------------------------------------
	# Create the command sequence for table creation or modification
	# ---------------------------------------------------------------------------

	def _createTable_ (self, table):
		"""
		Generate a code-triple to create or change the given table. Note:
		writeSchema () does *not* remove (drop) tables. GSTable instances with a
		'remove' action are skipped.

		@param table: GSTable instance to be processed
		@return: code-triple with the needed commands
		"""

		result = (pre, body, post) = ([], [], [])

		# We don't want to drop relations, do we ?!
		if table._action == 'remove':
			return result

		# Do we have some constraints or indices to be dropped ?
		for constraint in table.findChildrenOfType ('GSForeignKey', False, True):
			if constraint._action == "remove":
				csKey = "CONSTRAINT_%s" % constraint.name
				if csKey in self._lookups:
					del self._lookups [csKey]

				pre.extend (self._dropConstraint_ (constraint))

		for constraint in table.findChildrenOfType ('GSUnique', False, True):
			if constraint._action == "remove":
				csKey = "CONSTRAINT_%s" % constraint.name
				if csKey in self._lookups:
					del self._lookups [csKey]

		for index in table.findChildrenOfType ('GSIndex', False, True):
			if index._action == "remove":
				ixKey = "INDEX_%s" % index.name
				if ixKey in self._lookups:
					del self._lookups [ixKey]

				pre.extend (self._dropIndex_ (index))

		# Create an 'ALTER TABLE' sequence for changed tables
		if table._action == 'change':
			fields = [f for f in table.findChildrenOfType ('GSField', False, True) \
					if f._action in ['add', 'change']]

			if len (fields):
				if self._alterMultiple_:
					fcode = self._createFields_ (table)
					code = u"ALTER TABLE %s ADD (%s)" % (table.name, ", ".join (fcode[1]))
					self._mergeTriple (result, (fcode [0], [code], fcode [2]))

				else:
					for field in fields:
						fcode = self._createFields_ (field)
						code  = u"ALTER TABLE %s ADD %s" \
							% (table.name, ", ".join (fcode [1]))

						self._mergeTriple (result, (fcode [0], [code], fcode [2]))

		# Create a new table
		else:
			fcode = self._createFields_ (table)

			pkey = table.findChildOfType ('GSPrimaryKey')
			if pkey is not None:
				triple = self._extraPrimaryKey_ and result or fcode
				self._mergeTriple (triple, self._createPrimaryKey_ (pkey))

			code = u"CREATE TABLE %s (%s)" % (table.name, ", ".join (fcode [1]))
			self._mergeTriple (result, (fcode [0], [code], fcode [2]))

		# build all indices
		for index in table.findChildrenOfType ('GSIndex', False, True):
			if index._action == 'add':
				self._mergeTriple (result, self._createIndex_ (index))

		# build all constraints
		for constraint in table.findChildrenOfType ('GSUnique', False, True):
			if constraint._action == 'add':
				self._mergeTriple (result, self._createConstraint_ (constraint))

		for constraint in table.findChildrenOfType ('GSForeignKey', False, True):
			if constraint._action == 'add':
				self._mergeTriple (result, self._createConstraint_ (constraint))

		return result


	# ---------------------------------------------------------------------------
	# Create a fields sequence for the given item
	# ---------------------------------------------------------------------------

	def _createFields_ (self, item):
		"""
		Create a code-triple for the given GSTable or GSField.

		@param item: GSTable or GSField instance. For a GSTable instance this
		    method must add all fields to the result, otherwise only the given
		    field.
		@return: code-triple for the fields in question
		"""

		result = (pre, body, post) = ([], [], [])

		if isinstance (item, GSchema.GSTable):
			for field in item.findChildrenOfType ('GSField', False, True):
				self._mergeTriple (result, self._processField_ (field))

		elif isinstance (item, GSchema.GSField):
			self._mergeTriple (result, self._processField_ (item))

		return result


	# ---------------------------------------------------------------------------
	# Process a given field
	# ---------------------------------------------------------------------------

	def _processField_ (self, field):
		"""
		Create a code-triple for a single field. This function handles defaults and
		nullable flags too.

		@param field: GSField instance to create code for
		@return: code-triple for the field
		"""

		result = (pre, body, post) = ([], [], [])
		if field._action == 'remove':
			return result

		body.append ("%s %s" % (field.name, self._getNativetype (field)))

		if hasattr (field, 'defaultwith'):
			self._defaultwith_ (result, field)

		if hasattr (field, 'default') and field.default:
			default = field.default
			if default [:8].upper () != 'DEFAULT ':
				default = "DEFAULT '%s'" % default

			self._setColumnDefault_ (result, field, default)

		self._integrateNullable_ (result, field)

		return result


	# ---------------------------------------------------------------------------
	# Set a default value for a given column
	# ---------------------------------------------------------------------------

	def _setColumnDefault_ (self, code, field, default):
		"""
		Set a default value for a given column. If it is called for a table
		modification the epilogue of the code-block will be modified. On a table
		creation, this function assumes the field's code is in the last line of the
		code-block's body sequence.

		@param code: code-triple to get the result
		@param field: the GSField instance defining the default value
		@param default: string with the default value for the column
		"""

		table = field.findParentOfType ('GSTable')
		if table._action == 'change':
			code [2].append (u"ALTER TABLE %s ALTER COLUMN %s SET %s" % \
					(table.name, field.name, default))
		else:
			code [1][-1] += " %s" % default


	# ---------------------------------------------------------------------------
	# Handle the nullable flag of a field
	# ---------------------------------------------------------------------------

	def _integrateNullable_ (self, code, field):
		"""
		Handle the nullable-flag of a given field.  If the field is not
		nullable the last line of the code's body sequence will be modified on a
		create-action, or an 'alter table'-statement is added to the code's
		epilogue. @see: _setColumnDefault ()

		@param code: code-triple to get the result.
		@param field: the GSField instance defining the nullable-flag
		"""

		if hasattr (field, 'nullable') and not field.nullable:
			self._setColumnDefault_ (code, field, "NOT NULL")


	# ---------------------------------------------------------------------------
	# Handle special kinds of default values (like functions, sequences, ...)
	# ---------------------------------------------------------------------------

	def _defaultwith_ (self, code, field):
		"""
		Process special kinds of default values like sequences, functions and so
		on. Defaults of type 'constant' are already handled by '_processFields_'.

		@param code: code-triple of the current field as built by _processFields_
		@param field: GSField instance to process the default for
		"""

		pass


	# ---------------------------------------------------------------------------
	# Create a code sequence for a primary key
	# ---------------------------------------------------------------------------

	def _createPrimaryKey_ (self, pkey):
		"""
		Create a code triple for the given primary key. If _extraPrimaryKey_ is set
		to True the result's epilogue will contain an 'ALTER TABLE' statement,
		otherwise the result's body sequence will contain the constraint code.

		@param pkey: GSPrimaryKey instance defining the primary key
		@return: code-triple with the resulting code
		"""

		result  = (pre, body, post) = ([], [], [])
		keyName = self._getSafeName (pkey.name, "PK")
		fields  = ", ".join ([field.name for field in \
					pkey.findChildrenOfType ('GSPKField', False, True)])

		code = u"CONSTRAINT %s PRIMARY KEY (%s)" % (keyName, fields)

		if self._extraPrimaryKey_:
			table = pkey.findParentOfType ('GSTable')
			post.append (u"ALTER TABLE %s ADD %s" % (table.name, code))
		else:
			body.append (code)

		return result


	# ---------------------------------------------------------------------------
	# Create a code triple for a given index
	# ---------------------------------------------------------------------------

	def _createIndex_ (self, index):
		"""
		Create a code triple for the given index. If another GSTable instance
		wrapping the same table already created the index no code will be
		generated.

		@param index: GSIndex instance of index to be processed
		@return: code triple for the index
		"""

		result = (pre, body, post) = ([], [], [])

		table    = index.findParentOfType ('GSTable')
		elements = self._elements.setdefault (table.name, {})
		ixKey    = "INDEX_%s" % index.name

		# If the index was already processed by another GSTable instance of the
		# same table, just skip it
		if ixKey in elements:
			return result
		else:
			elements [ixKey] = None

		unique = hasattr (index, 'unique') and index.unique or False
		ixName = self._getSafeName (index.name, "INDEX")
		fields = index.findChildrenOfType ('GSIndexField', False, True)

		body.append (u"CREATE %sINDEX %s ON %s (%s)" % \
				(unique and "UNIQUE " or "", ixName, table.name,
				", ".join ([f.name for f in fields])))

		return result


	# ---------------------------------------------------------------------------
	# Create a constraint
	# ---------------------------------------------------------------------------

	def _createConstraint_ (self, constraint):
		"""
		Create a code triple for the given constraint. By adding all code to the
		epilogue, the order of processing related tables does not matter, since all
		new tables are created in the body-part of the code-triples.

		@param constraint: GSForeignKey instance to be processed
		@return: code triple with the command sequences
		"""

		result   = (pre, body, post) = ([], [], [])

		table    = constraint.findParentOfType ('GSTable')
		elements = self._elements.setdefault (table.name, {})
		csKey    = "CONSTRAINT_%s" % constraint.name

		# If the constraint was already processed by another GSTable instance of
		# the same table, just skip it
		if csKey in elements:
			return result
		else:
			elements [csKey] = None

		csName  = self._getSafeName (constraint.name, "CONSTRAINT")

		if isinstance (constraint, GSchema.GSForeignKey):
			rfName  = self._shortenName (constraint.references)
			fields  = constraint.findChildrenOfType ('GSFKField', False, True)

			code = u"ALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY (%s) " \
				"REFERENCES %s (%s)" \
				% (table.name, csName, ", ".join ([f.name for f in fields]),
				rfName, ", ".join ([f.references for f in fields]))

		elif isinstance (constraint, GSchema.GSUnique):
			fields = constraint.findChildrenOfType ('GSUQField')
			code   = u"ALTER TABLE %s ADD CONSTRAINT %s UNIQUE (%s)" \
				% (table.name, csName, ", ".join ([f.name for f in fields]))

		post.append (code)

		return result


	# ---------------------------------------------------------------------------
	# Drop a constraint
	# ---------------------------------------------------------------------------

	def _dropConstraint_ (self, constraint):
		"""
		Create a command sequence for dropping the given constraint.

		@param constraint: GSForeignKey instance to be dropped
		@return: command sequence
		"""

		table = constraint.findParentOfType ('GSTable').name
		return [u"ALTER TABLE %s DROP CONSTRAINT %s" % (table, constraint.name)]


	# ---------------------------------------------------------------------------
	# Drop an index
	# ---------------------------------------------------------------------------

	def _dropIndex_ (self, index):
		"""
		Create a command sequence for dropping the given index.

		@param index: GSIndex instance to be dropped
		@return: command sequence
		"""

		return [u"DROP INDEX %s" % index.name]


	# ---------------------------------------------------------------------------
	# A string becomes either varchar or text
	# ---------------------------------------------------------------------------

	def string (self, field):
		"""
		Return the native datatype for a string field.  If a length is defined it
		results in a 'varchar'- otherwise in a 'text'-field.

		@param field: GSField instance to get a native datatype for
		@return: varchar (length) or text
		"""

		if hasattr (field, 'length') and field.length:
			return "varchar (%s)" % field.length
		else:
			return "text"


	# ---------------------------------------------------------------------------
	# Numeric type transformation
	# ---------------------------------------------------------------------------

	def number (self, field):
		"""
		Return the native datatye for a numeric field.

		@param field: GSField instance to get the native datatype for
		@return: string with the native datatype
		"""

		length = hasattr (field, 'length') and field.length or 0
		scale  = hasattr (field, 'precision') and field.precision or 0

		if not scale:
			self._numbers_ [0].sort ()

			for (maxlen, ftype) in self._numbers_ [0]:
				if maxlen is None:
					return ftype

				elif length <= maxlen:
					return ftype

			if self._numbers_ [1]:
				return self._numbers_ [1] % length

		else:
			return self._numbers_ [2] % {'length': length, 'scale': scale}
