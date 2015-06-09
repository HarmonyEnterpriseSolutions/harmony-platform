# GNU Enterprise Common Library - XML elements for conditions
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
# $Id: GConditions.py 9244 2007-01-09 19:25:54Z reinhard $
"""
Classes for the condition object tree.
"""

import re
import sys
import datetime
if sys.hexversion >= 0x02040000:
	import decimal

from gnue.common.apps import errors
from gnue.common.definitions import GObjects
from gnue.common.formatting import GTypecast
from gnue.common.utils import GDateTime


# =============================================================================
# Exceptions
# =============================================================================

# -----------------------------------------------------------------------------
# Abstract base class
# -----------------------------------------------------------------------------

class ConditionError (errors.ApplicationError):
	"""
	Abstract base class for all errors in condition definitions.
	"""
	pass


# -----------------------------------------------------------------------------
# Malformed condition tree
# -----------------------------------------------------------------------------

class MalformedConditionTreeError (ConditionError):
	"""
	Abstract base class for all errors in the structure of the condition tree.
	"""
	pass

# -----------------------------------------------------------------------------

class ArgumentCountError (MalformedConditionTreeError):
	"""
	Number of child elements is incorrect.
	"""
	def __init__ (self, element, wanted):
		msg = u_("Conditionelement '%(element)s' was expected to have '%(wanted)d'"
			"arguments, but only has %(real)d'") \
			% {'element': element._type,
			'wanted' : wanted,
			'real'   : len (element._children)}
		MalformedConditionTreeError.__init__ (self, msg)


# -----------------------------------------------------------------------------
# Field value not in lookup dictionary
# -----------------------------------------------------------------------------

class MissingFieldError (ConditionError):
	"""
	Cannot find field value on attempt to evaluate a condition.
	"""

	def __init__ (self, field):
		msg = u_("The field '%(field)s' has no entry in the given lookup-table") \
			% {'field': field }
		ConditionError.__init__ (self, msg)


# -----------------------------------------------------------------------------
# Errors on unifying of different types
# -----------------------------------------------------------------------------

class UnificationError (errors.ApplicationError):
	"""
	Abstract base class for all errors on unifying different data types.
	"""
	pass

# -----------------------------------------------------------------------------

class ConversionRuleError (UnificationError):
	"""
	Cannot convert both data types into a common compatible type.
	"""
	def __init__ (self, value1, value2):
		msg = u_("No unification rule for combination '%(type1)s' and "
			"'%(type2)s'") \
			% {'type1': type (value1).__name__,
			'type2': type (value2).__name__}
		UnificationError.__init__ (self, msg)

# -----------------------------------------------------------------------------

class ConversionError (UnificationError):
	"""
	Cannot convert a value.
	"""
	def __init__ (self, value1, value2):
		msg = u_("Value '%(value1)s' of type '%(type1)s' cannot be converted "
			"into type '%(type2)s'") \
			% {'value1': value1,
			'type1' : type (value1).__name__,
			'type2' : type (value2).__name__}
		UnificationError.__init__ (self, msg)


# =============================================================================
# Base condition class; this is class is the root node of condition trees
# =============================================================================

class GCondition (GObjects.GObj):
	"""
	A GCondition instance is allways the root node of a condition tree. All
	children of a GCondition node are evaluated and combined using an AND
	condition if not otherwise stated.

	@ivar _maxChildren_: if not None specifies the maximum number of children
	  allowed for a condition element.
	@ivar _operator_: unicode string defining the operator used for SQL
	  transformation of a condition element.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, parent = None, type = "GCCondition", prefixList = None):
		"""
		@param parent: Parent instance in the GObj tree owning this instance
		@param type: type of this instance (usually 'GCCondition')
		@param prefixList: a condition in prefix notation; if this sequence is not
		  None, a condition tree according to this sequence will be built. This
		  instance is the root element of the newly created condition tree.
		"""

		GObjects.GObj.__init__ (self, parent, type = type)
		self._maxChildren_ = None
		self._operator_    = u""

		if prefixList is not None:
			self.buildFromList (prefixList)

		self.validate ()


	# ---------------------------------------------------------------------------
	# Make sure an element of the tree has the requested number of children
	# ---------------------------------------------------------------------------

	def _needChildren (self):
		"""
		Ensure that the requested number of children is available.

		@raise ArgumentCountError: raised if the number of children does not match
		  _maxChildren_.
		"""

		if self._maxChildren_ is not None and \
			len (self._children) != self._maxChildren_:
			raise ArgumentCountError, (self, self._maxChildren_)


	# ---------------------------------------------------------------------------
	# Evaluate a condition tree using the given lookup dictionary
	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		"""
		Evaluate a condition tree using a given lookup dictionary for field- and
		parameter-values. Evaluation stops on the first False result.

		@param lookup: dictionary used for lookups of field- and parameter-values.
		@return: True or False

		@raise ArgumentCountError: if the number of child elements somewhere in the
		  tree is incorrect.
		@raise MissingFieldError: if not all fields appearing in the condition tree
		  are assigned a value in the lookup dictionary.
		@raise ConversionRuleError: if any operation is given two incompatible
		  arguments.
		@raise ConversionError: if the type conversion needed to make arguments of
		  an operation comatible fails.
		"""

		self.validate ()

		for child in self._children:
			if not child.evaluate (lookup):
				return False

		return True


	# ---------------------------------------------------------------------------
	# Validate an element of a condition tree
	# ---------------------------------------------------------------------------

	def validate (self):
		"""
		This function calls validate () on all it's children. Descendants might
		override this function to do integrity checks and things like that.

		@raise ArgumentCountError: if the number of child elements somewhere in the
		  tree is incorrect.
		"""

		self._needChildren ()

		for child in self._children:
			child.validate ()


	# ---------------------------------------------------------------------------
	# Convert an element into prefix notation
	# ---------------------------------------------------------------------------

	def prefixNotation (self):
		"""
		This function returns the prefix notation of an element and all it's
		children.
		"""

		result = []
		append = result.extend

		if isinstance (self, GConditionElement):
			result.append (self._type [2:])
			append = result.append

		for child in self._children:
			append (child.prefixNotation ())

		return result


	# ---------------------------------------------------------------------------
	# Build an element and all it's children from a prefix notation list
	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		Return the condition tree as SQL string in python-format using placeholders
		and a given parameter dictionary.

		Example::
		  condition = ['eq', ['field', 'foobar'], ['const', 'barbaz']]
		  result = condition.asSQL (pDict)

		  result = 'foobar = %(p0)s'
		  pDcit  = {'p0': 'barbaz'}

		@param paramDict: dictionary with all parameter values. this dictionary
		  will be populated with all placeholders used in the SQL string.

		@return: SQL string representing the current condition
		"""

		f = isinstance (self.getParent (), GConditionElement) and u'(%s)' or u'%s'
		op = u' %s ' % self._operator_
		return f % op.join ([c.asSQL (paramDict) for c in self._children])


	# ---------------------------------------------------------------------------
	# Build an element and all it's children from a prefix notation list
	# ---------------------------------------------------------------------------

	def buildFromList (self, prefixList):
		"""
		This function creates a (partial) condition tree from a prefix notation
		list.

		@param prefixList: condition element sequence in prefix notation
		@return: GCondition tree
		"""

		checktype (prefixList, list)

		if len (prefixList):
			item = prefixList [0]

			# be nice if there's a condition part missing
			offset = 1
			if isinstance (item, list):
				self.buildFromList (item)
				element = self
			else:
				# automatically map 'field' to 'Field' and 'const' to 'Const'
				if item in ['field', 'const']:
					item = item.title ()

				element = getattr (sys.modules [__name__], "GC%s" % item) (self)

				if item == 'exist':
					(table, masterlink, detaillink) = prefixList [1:4]
					element.table      = table
					element.masterlink = masterlink
					element.detaillink = detaillink
					offset = 4

			for subitem in prefixList [offset:]:
				element.buildFromList (subitem)


# =============================================================================
# Parent class for all condition elements
# =============================================================================

class GConditionElement (GCondition) :
	"""
	Abstract base class for all condition elements.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, parent=None, type="GConditionElement"):
		GCondition.__init__ (self, parent, type = type)


# =============================================================================
# A Field element in the condition tree
# =============================================================================

class GCField (GConditionElement):
	"""
	Field value from a database table.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, parent, name = None, datatype = "char"):
		GConditionElement.__init__ (self, parent, 'GCCField')
		self.type = datatype
		self.name = name


	# ---------------------------------------------------------------------------
	# Evaluate a field element
	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		"""
		Return the value of the field in the given lookup dictionary.

		@param lookup: dictionary used for lookups
		@return: value of the field

		@raise MissingFieldError: raised if the lookup dictionary does not contain
		    a key for this field
		"""
		if not lookup.has_key (self.name):
			raise MissingFieldError, (self.name)

		return lookup [self.name]


	# ---------------------------------------------------------------------------
	# A field in prefix notation is a tuple of 'field' and fieldname
	# ---------------------------------------------------------------------------

	def prefixNotation (self):
		"""
		The prefix notation of a field element is a tuple of the identifier 'field'
		(acting as operator) and the field's name.

		@return: ['Field', name]
		"""

		return ['Field', self.name]


	# ---------------------------------------------------------------------------
	# to complete a field element from a prefix notation set the fieldname
	# ---------------------------------------------------------------------------

	def buildFromList (self, prefixList):
		"""
		The single argument to a field 'operator' could be it's name, so this
		method set's the fieldname.
		"""

		checktype (prefixList, basestring)
		self.name = prefixList


	# ---------------------------------------------------------------------------
	# SQL represenation of a field is it's field name
	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		The SQL representation of a field is it's name.

		@param paramDict: current parameter dictionary
		@return: the name of the field
		"""

		return self.name


# =============================================================================
# A constant definition in a condition tree
# =============================================================================

class GCConst (GConditionElement):
	"""
	Constant value of a specific type.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, value = None, datatype = "char"):
		GConditionElement.__init__ (self, parent, 'GCCConst')
		self.type   = datatype
		self.value  = value
		self._inits = [self.__typecast]

		if self.value is not None:
			self.__typecast ()


	# ---------------------------------------------------------------------------
	# Evaluate a constant
	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		"""
		This function returns the constants value

		@param lookup: dictionary with lookup values
		@return: value of the constant definition
		"""

		return self.value


	# ---------------------------------------------------------------------------
	# The prefix notation of a constant is a tuple of identifier and value
	# ---------------------------------------------------------------------------

	def prefixNotation (self):
		"""
		The prefix notation of a constant is a tuple of the identifier 'Const' and
		the constant's value.

		@return: ['Const', value]
		"""
		return ['Const', self.value]


	# ---------------------------------------------------------------------------
	# Recreate a constant from a prefix notation
	# ---------------------------------------------------------------------------

	def buildFromList (self, prefixList):
		"""
		The single argument of a constant 'operator' could be it's value, so this
		function set the constant's value.

		@param prefixList: element sequence in prefix notation. For a constant
		    definition this sequence must be the constant's value.
		"""

		self.value = prefixList


	# ---------------------------------------------------------------------------
	# Return an SQL representation of a constant
	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		Add another key to the parameter dictionary holding the constant's value
		and return an apropriate place holder for it.

		@param paramDict: parameter dictionary which will be extended
		@return: placeholder for the constant, i.e. '%(p0)s'
		"""

		if self.value is None:
			# Some backends don't like NULL to be a parameter
			return u'NULL'
		else:
			pKey = "p%d" % len (paramDict)
			paramDict [pKey] = self.value
			return u'%%(%s)s' % pKey


	# ---------------------------------------------------------------------------
	# Create a native python type for the constant value
	# ---------------------------------------------------------------------------

	def __typecast (self):

		dtype = self.type.lower ()

		if dtype == 'boolean':
			self.value = self.value.upper () in ['TRUE', 'Y', '1']

		elif dtype == 'number':
			# NOTE: what about the decimal separator depending on the locale?
			if "." in self.value:
				self.value = float (self.value)
			else:
				self.value = int (self.value)

		elif dtype == 'date':
			self.value = GDateTime.parseISODate (self.value)

		elif dtype == 'time':
			self.value = GDateTime.parseISOTime (self.value)

		elif dtype == 'datetime':
			self.value = GDateTime.parseISO (self.value)


# =============================================================================
# Base class for parameter elements in a condition tree
# =============================================================================

class GCParam (GConditionElement):
	"""
	Abstract class for parameters. Must be overridden by a descendant to handle
	actual parameter values.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, name = None, datatype = "char"):
		GConditionElement.__init__ (self, parent, 'GCCParam')
		self.type = datatype
		self.name = name


	# ---------------------------------------------------------------------------
	# Return the value of a parameter
	# ---------------------------------------------------------------------------

	def getValue(self):
		"""
		Descendants override this function to return the value of the parameter.
		"""

		return ""


	# ---------------------------------------------------------------------------
	# Evaluate the parameter object
	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		"""
		A parameter element evaluates to it's value.

		@param lookup: dictionary used for lookups
		@return: the parameter's value
		"""

		return self.getValue ()


	# ---------------------------------------------------------------------------
	# Return a parameter object in prefix notation
	# ---------------------------------------------------------------------------

	def prefixNotation (self):
		"""
		The prefix notation of a parameter object is a 'constant' with the
		parameters' value

		@return: ['Const', value]
		"""
		return ['Const', self.getValue ()]


	# ---------------------------------------------------------------------------
	# Return a SQL representation of a parameter instance
	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		Add another key to the parameter dictionary holding the parameter's value
		and return an apropriate place holder for it.

		@param paramDict: parameter dictionary which will be extended
		@return: placeholder for the parameter, i.e. '%(p0)s'
		"""

		pKey = "p%d" % len (paramDict)
		paramDict [pKey] = self.getValue ()
		return u'%%(%s)s' % pKey


# =============================================================================
# Base classes for unary operations
# =============================================================================

class GUnaryConditionElement (GConditionElement):
	"""
	Abstract base class for all unary condition elements.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None, elementType = ''):
		GConditionElement.__init__ (self, parent, elementType)
		self._maxChildren_ = 1


	# ---------------------------------------------------------------------------
	# Return a SQL representation of a unary operation
	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		Return a SQL code snippet for a unary operation.

		@param paramDict: parameter dictionary which will be extended
		@return: SQL code (in python-format) for the operation
		"""

		return self._operator_ % self._children [0].asSQL (paramDict)


# =============================================================================
# Base class for binary operations
# =============================================================================

class GBinaryConditionElement (GConditionElement):
	"""
	Abstract base class for all binary condition elements.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None, elementType = ''):
		GConditionElement.__init__ (self, parent, elementType)
		self._maxChildren_ = 2
		self.values       = []


	# ---------------------------------------------------------------------------
	# Evaluating a binary element means evaluation of both children
	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		"""
		This function evaluates both children of a binary element storing their
		values in the property 'values'. Descendants can use these values for
		further evaluations.

		@raise ArgumentCountError: if the number of child elements somewhere in the
		  tree is incorrect.
		"""

		self._needChildren ()
		self.values = unify ([child.evaluate (lookup) for child in self._children])


# =============================================================================
# Logical operators
# =============================================================================

# -----------------------------------------------------------------------------
# n-ary operation: AND
# -----------------------------------------------------------------------------

class GCand (GConditionElement):
	"""
	Logical AND.
	"""
	def __init__ (self, parent = None):
		GConditionElement.__init__ (self, parent, 'GCand')
		self._operator_ = u"AND"


# -----------------------------------------------------------------------------
# n-ary operation: OR
# -----------------------------------------------------------------------------

class GCor (GConditionElement):
	"""
	Logical OR.
	"""
	def __init__ (self, parent = None):
		GConditionElement.__init__ (self, parent, 'GCor')
		self._operator_ = u"OR"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		"""
		This function concatenates all children of this element by a logical OR.
		The iteration stops on the first 'true' result.
		"""

		for child in self._children:
			if child.evaluate (lookup):
				return True

		return False


# -----------------------------------------------------------------------------
# unary operation: NOT
# -----------------------------------------------------------------------------

class GCnot (GUnaryConditionElement):
	"""
	Logical NOT.
	"""
	def __init__ (self, parent = None):
		GUnaryConditionElement.__init__ (self, parent, 'GCnot')
		self._operator_ = u"NOT %s"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		"""
		This function logically inverts the child's evaluation
		"""

		self._needChildren ()
		return not self._children [0].evaluate (lookup)


# =============================================================================
# Numeric operations
# =============================================================================

# ---------------------------------------------------------------------------
# n-ary operation: Addition
# ---------------------------------------------------------------------------

class GCadd (GConditionElement):
	"""
	Numeric addition.
	"""
	def __init__ (self, parent = None):
		GConditionElement.__init__ (self, parent, 'GCadd')
		self._operator_ = u"+"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		"""
		This function creates the sum of all it's children. A unify is used to
		ensure all children evaluate to a numeric type.
		"""

		result = 0
		for child in self._children:
			result += unify ([child.evaluation (lookup), 0]) [0]
		return result


# -----------------------------------------------------------------------------
# n-ary operation: Subtraction
# -----------------------------------------------------------------------------

class GCsub (GConditionElement):
	"""
	Numeric subtraction.
	"""
	def __init__ (self, parent = None):
		GConditionElement.__init__ (self, parent, 'GCsub')
		self._operator_ = u"-"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		result = None

		for child in self._children:
			value = unify ([child.evaluation (lookup), 0]) [0]
			if result is None:
				result = value
			else:
				result -= value

		return result


# -----------------------------------------------------------------------------
# n-ary operation: Multiplication
# -----------------------------------------------------------------------------

class GCmul (GConditionElement):
	"""
	Numeric multiplication.
	"""
	def __init__ (self, parent = None):
		GConditionElement.__init__ (self, parent, 'GCmul')
		self._operator_ = u"*"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		result = None

		for child in self._children:
			value = unify ([child.evaluate (lookup), 0]) [0]
			if result is None:
				result = value
			else:
				result *= value

		return result


# -----------------------------------------------------------------------------
# n-ary operation: Division
# -----------------------------------------------------------------------------

class GCdiv (GConditionElement):
	"""
	Numeric division.
	"""
	def __init__ (self, parent = None):
		GConditionElement.__init__ (self, parent, 'GCdiv')
		self._operator_ = u"/"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		result = None

		for child in self._children:
			value = unify ([child.evaluate (lookup), 0]) [0]
			if result is None:
				result = value
			else:
				result /= value

		return result


# -----------------------------------------------------------------------------
# unary operation: numeric negation
# -----------------------------------------------------------------------------

class GCnegate (GUnaryConditionElement):
	"""
	Numeric negation.
	"""
	def __init__ (self, parent = None):
		GUnaryConditionElement.__init__ (self, parent, 'GCnegate')
		self._operator_ = u"-%s"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		"""
		This function does a numeric negation on the child's evaluation result.
		"""
		self._needChildren ()
		return -unify ([self._children [0].evaluate (lookup), 0]) [0]


# =============================================================================
# Relational operations
# =============================================================================

# -----------------------------------------------------------------------------
# Equality
# -----------------------------------------------------------------------------

class GCeq (GBinaryConditionElement):
	"""
	Test for equality.
	"""
	def __init__ (self, parent = None):
		GBinaryConditionElement.__init__ (self, parent, 'GCeq')
		self._operator_ = u"="

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		GBinaryConditionElement.evaluate (self, lookup)
		return self.values [0] == self.values [1]

	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		Return a SQL code snippet for this equal relation. If the right hand
		element of the relation is a constant with a value of None, the operator
		will be changed to the keyword 'IS'.

		@param paramDict: parameter dictionary which will be extended
		@return: SQL code for the condition element
		"""

		if isinstance (self._children [1], GCConst) and \
			self._children [1].value is None:
			self._operator_ = u"IS"

		return GBinaryConditionElement.asSQL (self, paramDict)


# -----------------------------------------------------------------------------
# Inequality
# -----------------------------------------------------------------------------

class GCne (GBinaryConditionElement):
	"""
	Test for inequality.
	"""
	def __init__ (self, parent = None):
		GBinaryConditionElement.__init__ (self, parent, 'GCne')
		self._operator_ = u"!="

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		GBinaryConditionElement.evaluate (self, lookup)
		return self.values [0] != self.values [1]

	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		Return a SQL code snippet for this inequal relation. If the right hand
		element of the relation is a constant with a value of None, the operator
		will be changed to the keyword 'IS NOT'.

		@param paramDict: parameter dictionary which will be extended
		@return: SQL code for the condition element
		"""

		if isinstance (self._children [1], GCConst) and \
			self._children [1].value is None:
			self._operator_ = u"IS NOT"

		return GBinaryConditionElement.asSQL (self, paramDict)


# -----------------------------------------------------------------------------
# Greater Than
# -----------------------------------------------------------------------------

class GCgt (GBinaryConditionElement):
	"""
	Test for greater than.
	"""
	def __init__ (self, parent = None):
		GBinaryConditionElement.__init__ (self, parent, 'GCgt')
		self._operator_ = u">"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		GBinaryConditionElement.evaluate (self, lookup)
		return self.values [0] > self.values [1]


# -----------------------------------------------------------------------------
# Greater or Equal
# -----------------------------------------------------------------------------

class GCge (GBinaryConditionElement):
	"""
	Test for greater or equal.
	"""
	def __init__ (self, parent = None):
		GBinaryConditionElement.__init__ (self, parent, 'GCge')
		self._operator_ = u">="

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		GBinaryConditionElement.evaluate (self, lookup)
		return self.values [0] >= self.values [1]


# -----------------------------------------------------------------------------
# Less Than
# -----------------------------------------------------------------------------

class GClt (GBinaryConditionElement):
	"""
	Test for lower than.
	"""
	def __init__ (self, parent = None):
		GBinaryConditionElement.__init__ (self, parent, 'GClt')
		self._operator_ = u"<"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		GBinaryConditionElement.evaluate (self, lookup)
		return self.values [0] < self.values [1]


# -----------------------------------------------------------------------------
# Less or Equal
# -----------------------------------------------------------------------------

class GCle (GBinaryConditionElement):
	"""
	Test for lower or equal.
	"""
	def __init__ (self, parent = None):
		GBinaryConditionElement.__init__ (self, parent, 'GCle')
		self._operator_ = u"<="

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		GBinaryConditionElement.evaluate (self, lookup)
		return self.values [0] <= self.values [1]


# -----------------------------------------------------------------------------
# Like
# -----------------------------------------------------------------------------

class GClike (GBinaryConditionElement):
	"""
	Test for SQL LIKE.
	"""
	def __init__ (self, parent = None):
		GBinaryConditionElement.__init__ (self, parent, 'GClike')
		self._operator_ = u"LIKE"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		GBinaryConditionElement.evaluate (self, lookup)
		# None cannot be like something else. You should use 'NULL' or 'NOT NULL'
		# instead
		if self.values [0] is None:
			return False

		strpat = "^%s" % self.values [1]
		strpat = strpat.replace ('?', '.').replace ('%', '.*')
		pattern = re.compile (strpat)
		return pattern.match (self.values [0]) is not None


# -----------------------------------------------------------------------------
# Not Like
# -----------------------------------------------------------------------------

class GCnotlike (GBinaryConditionElement):
	"""
	Test for SQL NOT LIKE.
	"""
	def __init__ (self, parent = None):
		GBinaryConditionElement.__init__ (self, parent, 'GCnotlike')
		self._operator_ = u"NOT LIKE"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		GBinaryConditionElement.evaluate (self, lookup)
		strpat = "^%s" % self.values [1]
		strpat = strpat.replace ('?', '.').replace ('%', '.*')
		pattern = re.compile (strpat)
		return pattern.match (self.values [0]) is None


# -----------------------------------------------------------------------------
# Between
# -----------------------------------------------------------------------------

class GCbetween (GConditionElement):
	"""
	Test for SQL BETWEEN.
	"""
	def __init__ (self, parent = None):
		GConditionElement.__init__ (self, parent, 'GCbetween')
		self._maxChildren_ = 3
		self._operator_ = u"BETWEEN"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		self._needChildren ()
		values = unify ([v.evaluate (lookup) for v in self._children])
		return values [1] <= values [0] <= values [2]

	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		Return a SQL code snippet for this condition element.

		@param paramDict: parameter dictionary which will be extended
		@return: SQL code for the condition element
		"""

		f = isinstance (self.getParent (), GConditionElement) and u'(%s)' or u'%s'
		return f % ('%s BETWEEN %s AND %s' \
				% tuple ([item.asSQL (paramDict) for item in self._children]))


# -----------------------------------------------------------------------------
# Not Between
# -----------------------------------------------------------------------------

class GCnotbetween (GConditionElement):
	"""
	Test for SQL NOT BETWEEN.
	"""
	def __init__ (self, parent = None):
		GConditionElement.__init__ (self, parent, 'GCnotbetween')
		self._maxChildren_ = 3
		self._operator_ = u"NOT BETWEEN"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		self._needChildren ()
		values = unify ([v.evaluate (lookup) for v in self._children])
		return not (values [1] <= values [0] <= values [2])

	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		Return a SQL code snippet for this condition element.

		@param paramDict: parameter dictionary which will be extended
		@return: SQL code for the condition element
		"""

		f = isinstance (self.getParent (), GConditionElement) and u'(%s)' or u'%s'
		return f % ('%s NOT BETWEEN %s AND %s' \
				% tuple ([item.asSQL (paramDict) for item in self._children]))


# -----------------------------------------------------------------------------
# is NULL
# -----------------------------------------------------------------------------

class GCnull (GUnaryConditionElement):
	"""
	Test for SQL IS NULL
	"""
	def __init__ (self, parent = None):
		GUnaryConditionElement.__init__ (self, parent, 'GCnull')
		self._operator_ = u"(%s IS NULL)"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		self._needChildren ()
		return self._children [0].evaluate (lookup) is None


# -----------------------------------------------------------------------------
# is Not NULL
# -----------------------------------------------------------------------------

class GCnotnull (GUnaryConditionElement):
	"""
	Test for SQL IS NOT NULL
	"""
	def __init__ (self, parent = None):
		GUnaryConditionElement.__init__ (self, parent, 'GCnotnull')
		self._operator_ = u"(%s IS NOT NULL)"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		self._needChildren ()
		return self._children [0].evaluate (lookup) is not None


# -----------------------------------------------------------------------------
# upper
# -----------------------------------------------------------------------------

class GCupper (GUnaryConditionElement):
	"""
	String conversion to uppercase.
	"""
	def __init__ (self, parent = None):
		GUnaryConditionElement.__init__ (self, parent, 'GCupper')
		self._operator_ = u"UPPER(%s)"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		self._needChildren ()
		return (self._children [0].evaluate (lookup)).upper ()


# -----------------------------------------------------------------------------
# lower
# -----------------------------------------------------------------------------

class GClower (GUnaryConditionElement):
	"""
	String conversion to lowercase.
	"""
	def __init__ (self, parent = None):
		GUnaryConditionElement.__init__ (self, parent, 'GClower')
		self._operator_ = u"LOWER(%s)"

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):
		self._needChildren ()
		return (self._children [0].evaluate (lookup)).lower ()


# -----------------------------------------------------------------------------
# exist
# -----------------------------------------------------------------------------

class GCexist (GConditionElement):
	"""
	Test if a record fulfilling a given condition exists in another table.
	"""
	def __init__ (self, parent = None):
		GConditionElement.__init__ (self, parent, 'GCexist')
		self.callback = None

	# ---------------------------------------------------------------------------

	def evaluate (self, lookup):

		if self.callback is None:
			raise NotImplementedError

		return self.callback (self, lookup)

	# ---------------------------------------------------------------------------

	def prefixNotation (self):
		"""
		This function returns the prefix notation of an exist element and all it's
		children.
		"""
		result = ['exist', self.table, self.masterlink, self.detaillink]

		for child in self._children:
			result.append (child.prefixNotation ())

		return result

	# ---------------------------------------------------------------------------

	def asSQL (self, paramDict):
		"""
		Return the SQL statement for this condition, using a subselect.
		"""

		sql = '%s IN (SELECT %s FROM %s WHERE %s)' % (
			self.masterlink, self.detaillink, self.table,
			' AND '.join ([c.asSQL (paramDict) for c in self._children]))
		return sql


# =============================================================================
# Return a dictionary of all XML elements available
# =============================================================================

def getXMLelements (updates = {}):
	xmlElements = {
		'condition': {
			'BaseClass'  : GCondition,
			'ParentTags' : ()},
		'cfield': {
			'BaseClass'  : GCField,
			'Description': 'Defines a database table\'s field in a condition.',
			'Attributes' : {'name': {'Required': True,
					'Typecast': GTypecast.name }},
			'ParentTags' : ('eq','ne','lt','le','gt','ge','add','sub','mul',
				'div','negate','like','notlike','between',
				'notbetween','upper','lower','null','notnull')},
		'cconst': {
			'BaseClass'  : GCConst,
			'Description': 'Defines a constant value in a condition.',
			'Attributes' : {'value': {'Required': True,
					'Typecast': GTypecast.text},
				'type' : {'Typecast': GTypecast.text }},
			'ParentTags' : ('eq','ne','lt','le','gt','ge','add','sub','mul',
				'div','negate','like','notlike','between',
				'notbetween')},
		'cparam': {
			'BaseClass'  : GCParam,
			'Description': 'Defines a parameter value in a condition.',
			'Attributes' : {'name': {'Required': True,
					'Unique':   True,
					'Typecast': GTypecast.name }},
			'ParentTags' : ('eq','ne','lt','le','gt','ge','add','sub','mul',
				'div','negate','like','notlike','between',
				'notbetween')},
		'and': {
			'BaseClass'  : GCand,
			'Description': 'Implements logical AND relation.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'or': {
			'BaseClass'  : GCor,
			'Description': 'Implements logical OR relation.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'not': {
			'BaseClass'  : GCnot,
			'Description': 'Implements logical NOT relation.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'add': {
			'BaseClass'  : GCadd,
			'Description': 'Implements addition.',
			'ParentTags' : ('eq','ne','lt','le','gt','ge','add','sub','mul',
				'div','negate','between','notbetween')},
		'sub': {
			'BaseClass'  : GCsub,
			'Description': 'Implements subtraction.',
			'ParentTags' : ('eq','ne','lt','le','gt','ge','add','sub','mul',
				'div','negate','between','notbetween')},
		'mul': {
			'BaseClass'  : GCmul,
			'Description': 'Implements multiplication.',
			'ParentTags' : ('eq','ne','lt','le','gt','ge','add','sub','mul',
				'div','negate','between','notbetween')},
		'div': {
			'BaseClass'  : GCdiv,
			'Description': 'Implements division.',
			'ParentTags' : ('eq','ne','lt','le','gt','ge','add','sub','mul',
				'div','negate','between','notbetween')},
		'negate': {
			'BaseClass'  : GCnegate,
			'Description': 'Implements numerical negation.',
			'ParentTags' : ('eq','ne','lt','le','gt','ge','add','sub','mul',
				'div','between','notbetween')},
		'eq': {
			'BaseClass'  : GCeq,
			'Description': 'Implements a {field} = {value} condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'ne': {
			'BaseClass'  : GCne,
			'Description': 'Implements a {field} <> {value} condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'gt': {
			'BaseClass'  : GCgt,
			'Description': 'Implements a {field} > {value} condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'ge': {
			'BaseClass'  : GCge,
			'Description': 'Implements a {field} >= {value} condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'lt': {
			'BaseClass'  : GClt,
			'Description': 'Implements a {field} < {value} condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'le': {
			'BaseClass'  : GCle,
			'Description': 'Implements a {field} <= {value} condition.',
			'ParentTags' :  ('condition','and','or','not','exist')},
		'like': {
			'BaseClass'  : GClike,
			'Description': 'Implements a {field} LIKE {value} condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'notlike': {
			'BaseClass'  : GCnotlike,
			'Description': 'Implements a {field} NOT LIKE {value} condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'between': {
			'BaseClass'  : GCbetween,
			'Description': 'Implements a {field} BETWEEN {value1} {value2} '
			'condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'notbetween': {
			'BaseClass'  : GCnotbetween,
			'Description': 'Implements a {field} NOT BETWEEN {value1} {value2} '
			'condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'null': {
			'BaseClass'  : GCnull,
			'Description': 'Implements a {field} IS NULL condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'notnull': {
			'BaseClass'  : GCnotnull,
			'Description': 'Implements a {field} IS NOT NULL condition.',
			'ParentTags' : ('condition','and','or','not','exist')},
		'upper': {
			'BaseClass'  : GCupper,
			'Description': 'Implements upper({value}).',
			'ParentTags' : ('eq','ne','lt','le','gt','ge',
				'like','notlike','between','notbetween')},
		'lower': {
			'BaseClass'  : GClower,
			'Description': 'Implements lower({value}).',
			'ParentTags' : ('eq','ne','lt','le','gt','ge',
				'like','notlike','between','notbetween')},
		'exist': {
			'BaseClass'  : GCexist,
			'Description': 'Implements an exist condition.',
			'Attributes' : {'table'     : {'Required': True,
					'Typecast': GTypecast.name},
				'masterlink': {'Required': True,
					'Typecast': GTypecast.text},
				'detaillink': {'Required': True,
					'Typecast': GTypecast.text}},
			'ParentTags' : ('condition','and','or','not','exist')}}

	for alteration in updates.keys ():
		xmlElements [alteration].update (updates [alteration])

	return xmlElements


# =============================================================================
# Convenience methods
# =============================================================================

# -----------------------------------------------------------------------------
# Create a condition tree either from a prefix list or a dictionary
# -----------------------------------------------------------------------------

def buildCondition (condition, comparison = GCeq, logic = GCand):
	"""
	Create a condition tree either from a sequence in prefix notation or a
	dictionary. In the latter case an optional comparison- and logic-operator
	class might be specified.

	@param condition: sequence in prefix notation or a dictionary with the
	    condition to be converted
	@param comparison: (operator) class used to compare keys and values
	@param logic: (operator) class used to concatenate multiple comparisons

	@return: GCondition tree
	"""

	checktype (condition, [list, dict, GCondition, None])

	if isinstance (condition, list):
		return GCondition (prefixList = condition)

	elif isinstance (condition, dict):
		return buildConditionFromDict (condition, comparison, logic)

	elif isinstance (condition, GCondition):
		return condition

	else: # None
		return GCondition ()


# -----------------------------------------------------------------------------
# Create a condition tree from an element sequence in prefix notation
# -----------------------------------------------------------------------------

def buildConditionFromPrefix (prefixList):
	"""
	This function creates a new condition tree from the given element sequence,
	which must be in prefix notation.

	@param prefixList: sequence of condition elements in prefix notation
	@return: GCondition tree
	"""

	checktype (prefixList, list)

	return GCondition (prefixList = prefixList)


# -----------------------------------------------------------------------------
# Create a condition tree from a dictionary
# -----------------------------------------------------------------------------

def buildConditionFromDict (dictionary, comparison = GCeq, logic = GCand):
	"""
	This function creates a new condition tree using the given comparison as
	operation between keys and values and a given logic as concatenation for all
	keys.

	@param dictionary: dictionary with (key, value) pairs to convert into a
	    condition tree
	@param comparison: (operator) class used to compare keys and values
	@param logic: (operator) class used to concatenate multiple comparisons

	@return: GCondition tree
	"""

	checktype (dictionary, dict)

	c     = comparison ()._type [2:]
	pList = [[c, ['field', f], ['const', v]] for (f, v) in dictionary.items ()]

	if pList:
		pList.insert (0, logic ()._type [2:])

	return GCondition (prefixList = pList)


# -----------------------------------------------------------------------------
# Combine two conditions with an AND clause
# -----------------------------------------------------------------------------

def combineConditions (cond1, cond2):
	"""
	Combine two conditions using an AND operator. Both arguments can be given as
	condition trees (GCondition), dictionaries or prefix sequences. The resulting
	combination is a *new* condition tree. None of the arguments will be changed.

	@param cond1: condition-tree, -dictionary or -sequence (prefix list)
	@param cond2: condition-tree, -dictionary or -sequence (prefix list)
	@return: new GCondition instance with an AND-combination of both conditions
	"""

	# First check for the trivial cases. If there is only one part defined we can
	# return a *copy* of that condition
	if not cond1:
		return buildCondition (buildCondition (cond2).prefixNotation ())

	elif not cond2:
		return buildCondition (buildCondition (cond1).prefixNotation ())

	# otherwise make sure to have GCondition instances on both sides
	cond1 = buildCondition (cond1)
	cond2 = buildCondition (cond2)

	# If the condition starts with an AND operator we start at that point,
	# otherwise use the condition as it is
	top1 = (cond1.findChildOfType ('GCand') or cond1).prefixNotation ()
	top2 = (cond2.findChildOfType ('GCand') or cond2).prefixNotation ()

	if top1 and top1 [0] == 'and': top1 = top1 [1:]
	if top2 and top2 [0] == 'and': top2 = top2 [1:]

	ncond = ['and']
	if top1: ncond.append (top1)
	if top2: ncond.append (top2)

	return buildCondition (ncond)


# -----------------------------------------------------------------------------
# Unify all elements in values to the same type
# -----------------------------------------------------------------------------

def unify (values):
	"""
	Convert all items in a given sequence to the same types.

	@param values: sequence of items to be converted to a common type
	@return: sequence of converted items having all the same datatype.
	"""

	checktype (values, list)

	result = []
	__unify (values, result)

	return result

# -----------------------------------------------------------------------------

def __unify (values, result):

	if not len (values):
		return

	elif len (values) == 1:
		result.append (values [0])
		return

	if isinstance (values [0], str):
		values [0] = unicode (values [0])
	if isinstance (values [1], str):
		values [1] = unicode (values [1])

	v1 = values [0]
	v2 = values [1]

	if v1 is None or v2 is None:
		result.append (None)
		values.remove (None)
		__unify (values, result)

	elif type (v1) == type (v2):
		result.append (v1)
		values.remove (v1)
		__unify (values, result)

	else:
		# String-Conversions
		if isinstance (v1, unicode) or isinstance (v2, unicode):
			if isinstance (v1, unicode):
				oldValue = v1
				chkValue = v2
			else:
				oldValue = v2
				chkValue = v1

			# String to Boolean
			if isinstance (chkValue, bool):
				if oldValue.upper () in ['TRUE', 'T']:
					newValue = True
				elif oldValue.upper () in ['FALSE', 'F']:
					newValue = False
				else:
					raise ConversionError, (oldValue, chkValue)

			# String to Integer, Long or Float
			elif isinstance (chkValue, int) or \
				isinstance (chkValue, long) or \
				isinstance (chkValue, float):
				try:
					if oldValue.upper () in ['TRUE', 'T']:
						newValue = 1
					elif oldValue.upper () in ['FALSE', 'F']:
						newValue = 0
					else:
						newValue = int (oldValue)

				except ValueError:

					try:
						newValue = float (oldValue)

					except ValueError:
						raise ConversionError, (oldValue, chkValue)

			# String to DateTime
			elif isinstance (chkValue, datetime.datetime) or \
				isinstance (chkValue, datetime.time) or \
				isinstance (chkValue, datetime.date):

				try:
					new = GDateTime.parseISO (oldValue)

					if isinstance (chkValue, datetime.time):
						newValue = datetime.time (new.hour, new.minute, new.second,
							new.microsecond)

					elif isinstance (chkValue, datetime.date):
						newValue = datetime.date (new.year, new.month, new.day)

					elif isinstance (chkValue, datetime.datetime):
						newValue = datetime.datetime (new.year, new.month, new.day,
							new.hour, new.minute, new.second, new.microsecond)

					else:
						newValue = new

				except ValueError:
					raise ConversionError, (oldValue, chkValue)

			else:
				raise ConversionRuleError, (oldValue, chkValue)

		# Boolean conversions
		elif isinstance (v1, bool) or isinstance (v2, bool):
			if isinstance (v1, bool):
				oldValue = v1
				chkValue = v2
			else:
				oldValue = v2
				chkValue = v1

			# Boolean to Integer
			if isinstance (chkValue, int):
				if oldValue:
					newValue = 1
				else:
					newValue = 0

			# Boolean to Long
			elif isinstance (chkValue, long):
				if oldValue:
					newValue = 1L
				else:
					newValue = 0L

			# Boolean to Decimal
			elif sys.hexversion >= 0x02040000 \
				and isinstance (chkValue, decimal.Decimal):
				if oldValue:
					newValue = decimal.Decimal(1)
				else:
					newValue = decimal.Decimal(0)

			else:
				raise ConversionRuleError, (oldValue, chkValue)

		# Integer conversions
		elif isinstance (v1, int) or isinstance (v2, int):
			if isinstance (v1, int):
				oldValue = v1
				chkValue = v2
			else:
				oldValue = v2
				chkValue = v1

			# Integer to Float
			if isinstance (chkValue, float):
				newValue = float (oldValue)

			# Integer to Long
			elif isinstance (chkValue, long):
				newValue = long (oldValue)

			# Integer to Decimal
			elif sys.hexversion >= 0x02040000 \
				and isinstance (chkValue, decimal.Decimal):
				newValue = decimal.Decimal (oldValue)
			else:
				raise ConversionRuleError, (oldValue, chkValue)

		# Long conversions
		elif isinstance (v1, long) or isinstance (v2, long):
			if isinstance (v1, long):
				oldValue = v1
				chkValue = v2
			else:
				oldValue = v2
				chkValue = v1

			# Long to Float
			if isinstance (chkValue, float):
				newValue = float (oldValue)

			# Long to Decimal
			elif sys.hexversion >= 0x02040000 \
				and isinstance (chkValue, decimal.Decimal):
				newValue = decimal.Decimal (oldValue)
			else:
				raise ConversionRuleError, (oldValue, chkValue)

		# Decimal conversion (Python 2.4 or later)
		elif sys.hexversion >= 0x02040000 \
			and (isinstance (v1, decimal.Decimal) \
				or isinstance (v2, decimal.Decimal)):

			if isinstance (v1, decimal.Decimal):
				oldValue = v1
				chkValue = v2
			else:
				oldValue = v2
				chkValue = v1

			# Decimal into Float
			if isinstance (chkValue, float):
				newValue = float (oldValue)
			else:
				raise ConversionRuleError, (oldValue, chkValue)

		elif isinstance (v1, datetime.datetime) or \
			isinstance (v2, datetime.datetime):

			if isinstance (v1, datetime.datetime):
				oldValue = v1
				chkValue = v2
			else:
				oldValue = v2
				chkValue = v1

			if isinstance (chkValue, datetime.date):
				newValue = oldValue.date ()

			else:
				raise ConversionRuleError, (v1, v2)

		elif isinstance (v1, datetime.timedelta) or \
			isinstance (v2, datetime.timedelta):
			if isinstance (v1, datetime.timedelta):
				oldValue = v1
				chkValue = v2
			else:
				oldValue = v2
				chkValue = v1

			if isinstance (chkValue, datetime.time):
				newValue = datetime.time (oldValue.seconds / 3600,
					oldValue.seconds % 3600 / 60, oldValue.seconds % 60,
					oldValue.microseconds)
			else:
				raise ConversionRuleError, (v1, v2)
		else:
			raise ConversionRuleError, (v1, v2)

		values [oldValue == v2] = newValue
		__unify (values, result)
