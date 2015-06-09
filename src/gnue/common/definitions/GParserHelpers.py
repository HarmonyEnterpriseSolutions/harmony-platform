# GNU Enterprise Common Library - GParser - Helper classes
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
# $Id: GParserHelpers.py,v 1.8 2009/03/27 18:57:58 oleg Exp $

"""
Base classes for GNUe objects which can be represented as XML.
"""
import types
import weakref
from xml.sax import saxutils
from gnue.common.apps import errors

NotWeakreffableTypes = (weakref.ProxyType, types.NoneType)

__all__ = ['ParserObj', 'GLeafNode', 'GContent', 'GComment']


# =============================================================================
# Exceptions
# =============================================================================

class AssignmentTypeError (errors.ApplicationError):
	def __init__ (self, dst, source):
		msg = u_("Cannot assign class '%(source)s' to class '%(dest)s'") \
			% {'source': source.__class__, 'dest': dst.__class__}
		errors.ApplicationError.__init__ (self, msg)


# =============================================================================
# Base class for GParser objects
# =============================================================================

class ParserObj(object):
	"""
	Base class for objects handled by a L{gnue.common.definitions.GParser}.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None, type = '_NotSet_'):

		self._type          = type
		self._children      = []     # The objects contained by this object
		self._attributes    = {}
		self._inits         = []     # functions called during phaseInit stage
		self._xmlnamespace  = None   # If the object is namespace-qualified,
		# the namespace
		self._xmlnamespaces = {}     # If attributes are namespace-qualified, a map

		self.setParent (parent)
		if parent:
			parent.addChild (self)


	# ---------------------------------------------------------------------------
	# Return the parent instance of an object in a GObj tree
	# ---------------------------------------------------------------------------

	def getParent (self):
		"""
		Returns the immediate parent of an object instance in a GObj tree.

		@returns: The parent of the object in the GObj tree.
		@rtype: any
		"""

		return self.__parent


	def getTreePath(self):
		path = []
		i = self
		while i:
			path.append(i)
			i = i.getParent()
		path.reverse()
		return path


	# ---------------------------------------------------------------------------
	# Set the parent of an object in a GObj tree
	# ---------------------------------------------------------------------------

	def setParent (self, newParent):
		"""
		Set the immediate parent of an object instance in a GObj tree

		@param newParent: instance to be set as parent
		"""

		if isinstance(newParent, NotWeakreffableTypes):
			self.__parent = newParent
		else:
			self.__parent = weakref.proxy(newParent)



	# ---------------------------------------------------------------------------
	# add an object to the list of children
	# ---------------------------------------------------------------------------

	def addChild (self, child):
		"""
		Add an object to the list of children

		@param child: The object to add.
		@type child: L{ParserObj} derived class
		"""

		self._children.append (child)


	# ---------------------------------------------------------------------------
	# Assign a given set of attributes from another instance
	# ---------------------------------------------------------------------------

	def assign (self, source, recursive = False):
		"""
		Assign all attributes from a given object to this one. If the recursive
		option is given, all of the source's children will be I{duplicated} and
		assigned to this object.

		@param source: the L{ParserObj} instance to assign attributes from
		@param recursive: if True, all children of source will be recursiveley
		  duplicated and assigned to this object

		@raises AssignmentTypeError: if the source object is another class than
		  this object
		"""

		if self.__class__ != source.__class__:
			raise AssignmentTypeError, (self, source)

		# Assign everything except the parent and the children
		for (name, value) in source.__dict__.items ():
			# FIXME: better simply copy all attributes not starting with _? Maybe
			# call buildObject afterwards?
			if name in ['_ParserObj__parent', '_children']:
				continue
			# Do not copy "magic" attributes, they are reserved for Python
			if name.endswith('__'):
				continue
			# Do not copy the list of phaseInit method pointers, they point to the
			# methods of the source object!
			if name == '_inits':
				continue
			# Also do not copy the trigger stuff, it also contains method pointers!
			if name.startswith('_trigger'):
				continue

			self.__dict__ [name] = value

		if recursive:
			self._children = []

			for child in source._children:
				new = child.__class__ (None)
				new.assign (child, recursive)

				self.addChild (new)
				new.setParent (self)


	# ---------------------------------------------------------------------------
	# Merge another object tree with this tree
	# ---------------------------------------------------------------------------

	def merge (self, other, maxIdLength = None, overwrite=False):
		"""
		Merge another object tree into this tree.

		All attributes and child nodes from the other object are merged into this
		object.  If any child node exists in both objects with the same name (id),
		the merge is done recursively.

		@param other: L{ParserObj} tree to be merged into this object tree
		@param maxIdLength: maximum length of the name to compare, useful if any of
		    the objects has the identifier truncated
		@param overwrite: whether attributes and children of the other object
		    should overwrite attributes and children of this object
		"""

		if self.__class__ != other.__class__:
			raise AssignmentTypeError, (self, other)

		# First copy all attributes from the other object.
		if hasattr(other, "_listedAttributes"):
			for attribute in other._listedAttributes:
				if overwrite or (attribute not in self._listedAttributes):
					self.__dict__[attribute] = other.__dict__[attribute]

			self._listedAttributes = list(set(getattr(self, '_listedAttributes', ())).union(other._listedAttributes))

		# We keep a mapping of all our children
		mine = {}
		for mc in self._children:
			mine [mc._id_ (maxIdLength)] = mc

		for otherChild in other._children:
			# ... wether we have to start a recursive merge ...
			if otherChild._id_ (maxIdLength) in mine:
				mine [otherChild._id_ (maxIdLength)].merge (otherChild, maxIdLength,
					overwrite)
			# ... or we can copy the subtree
			else:
				new = otherChild.__class__ (self)
				new.assign (otherChild, True)


	# ---------------------------------------------------------------------------
	# Build a difference-tree from two given object trees
	# ---------------------------------------------------------------------------

	def diff (self, goal, maxIdLength = None):
		"""
		Build an object tree representing the difference between two object trees.

		@param goal: L{ParserObj} tree to compare this object's tree to.
		@param maxIdLength: if defined, use only up to maxIdLength characters of
		  the object name to check for identity.
		@returns: L{ParserObj} tree representing the difference. Every object in
		  this tree has an additional attribute B{_action} which can contain one of
		  the following values:

		  * add: the object is only available in the 'goal' tree
		  * change: the object is avaialable in both trees, but differs
		  * remove: the object is only available in the 'source' tree
		"""

		result = None

		mine   = {}
		others = {}

		# Build a mapping of our children
		for child in self._children:
			mine [child._id_ (maxIdLength)] = child

		# find the counterpart of this instance
		buddy = goal.findChildOfType (self._type, True, True)

		if buddy is not None:
			for child in buddy._children:
				others [child._id_ (maxIdLength)] = child

		# Find out new and changed items
		for (key, item) in others.items ():
			childDiff = None

			if not key in mine:
				if item._children or isinstance (item, GLeafNode):
					childDiff = item.__class__ (None)
					childDiff.assign (item, True)
					childDiff.walk (self._diffActionWalker_, "add")

			else:
				# we need to find out wether the instances are changed then
				childDiff = mine [key].diff (item, maxIdLength)
				if childDiff is not None:
					childDiff._action = "change"

			if childDiff is not None:
				if result is None:
					result = self.__class__ (None)
					result.assign (self)

				result.addChild (childDiff)
				childDiff.setParent (result)

		# Finally find out all 'obsolete' ones
		for (key, item) in mine.items ():
			if not key in others:
				if result is None:
					result = self.__class__ (None)
					result.assign (self)

				child = item.__class__ (None)
				child.assign (item, True)
				child.walk (self._diffActionWalker_, "remove")

				result.addChild (child)
				child.setParent (result)

		if result is not None:
			result._action = "change"

		return result


	# ---------------------------------------------------------------------------
	# Return a XML representation of the object
	# ---------------------------------------------------------------------------

	def dumpXML (self, lookupDict, treeDump = False, gap = "  ",
		xmlnamespaces = {}, textEncoding = '<locale>', stripPrefixes = None,
		escape = True):
		"""
		Return a XML representation of the object.

		@param lookupDict: dictionary describing the XML entities, their
		  attributes and types
		@param treeDump: if True, also include a XML representation of all children
		@param gap: string defining the current indentation level
		@param xmlnamespaces: dictionary with the available XML namespaces
		@param textEncoding: encoding used to transform string-type attributes into
		  unicode. If textEncoding is set to '<locale>' (default) it will be set to
		  the configuration variable 'textEncoding', i.e. from gnue.conf
		@param stripPrefixes: a list of prefixes that will automatically be removed
		  from the objects type.  This can be used to remove the GF from the start
		  of all the gnue-forms objects.  If set to None (the default) then the
		  behaviour will be the old style which removes the first two characters
		  from the type.
		@param escape: if set to True the resulting XML string should be escaped

		@returns: a string with the object's XML representation
		"""

		return self._dumpXML_ (lookupDict, treeDump, gap, xmlnamespaces,
			textEncoding, stripPrefixes, escape)


	# ---------------------------------------------------------------------------
	# Find the first parent instance of a given type
	# ---------------------------------------------------------------------------

	def findParentOfType (self, parentType, includeSelf = True):
		"""
		Moves upward though the parents of an object till it finds the parent of
		the specified type.

		@param parentType: type of the object to be found
		@param includeSelf: if set to True, the search starts with this object
		  instead of the object's parent.

		@returns: the first parent object of the given type or None if no such
		  object was found. Allways returns weakref proxy
		"""

		parentObject = includeSelf and self or self.__parent

		while parentObject is not None:

			# parent of type found or If passed a type of None it finds the top object in the tree
			if parentObject._type == parentType or not parentType and not parentObject.__parent:

				if not isinstance(parentObject, NotWeakreffableTypes):
					if parentObject is not self:
						print "* findParentOfType: %s parent is not weakref: %s" % (self, parentObject)
					parentObject = weakref.proxy(parentObject)

				return parentObject

			parentObject = parentObject.__parent

		return None


	# ---------------------------------------------------------------------------
	# Find the first child object with a given name and type
	# ---------------------------------------------------------------------------

	def findChildNamed (self, name, childType = None, allowAllChildren = False):
		"""
		Moves downward though the children of an object till it finds the child
		with the specified name.

		@param name: The name to search for
		@param childType: The type of object to search for, if None then any type
		  will match.

		@return: The child with the matching name, or None if child not found
		"""

		for child in self._children:
			if name is None or getattr (child, 'name', None) == name:
				if childType is None or child._type == childType:
					return child
			if allowAllChildren:
				o = child.findChildNamed(name, childType, True)
				if o:
					return o
		return None


	# ---------------------------------------------------------------------------
	# Find the first child of a given type
	# ---------------------------------------------------------------------------

	def findChildOfType (self, childType, includeSelf = True,
		allowAllChildren = False):
		"""
		Moves downward through the children of an object till it finds the child of
		the specified type.

		@param childType: type of the child to be searched for
		@param includeSelf: if set to True, the search starts with this instance
		@param allowAllChildren: if set to True, the search will be performed
		  recursive.

		@returns: the first child of the requested type or None if no such object
		  is found.
		"""

		if includeSelf and self._type == childType:
			return self

		for child in self._children:
			if child._type == childType:
				return child

		if allowAllChildren:
			for child in self._children:
				o = child.findChildOfType (childType, False, True)
				if o:
					return o

		return None


	# ---------------------------------------------------------------------------
	# Find children of a given type
	# ---------------------------------------------------------------------------

	def findChildrenOfType (self, childType, includeSelf = True,
		allowAllChildren = False):
		"""
		Find all children of a specific type.

		@param childType: type of the objects to match
		@param includeSelf: if set to True, the search will be started with this
		  instance.
		@param allowAllChildren: if set to True, recursivley step down the object
		  tree and add all children of the requested type

		@returns: sequence with all child objects matching the requested type
		"""

		result = []
		add    = result.append
		extend = result.extend

		if includeSelf and self._type == childType:
			add (self)

		for child in self._children:
			if child._type == childType:
				add (child)

		if allowAllChildren:
			for child in self._children:
				extend (child.findChildrenOfType (childType, False, True))

		return result


	# ---------------------------------------------------------------------------
	# Get a description for an object
	# ---------------------------------------------------------------------------

	def getDescription (self):
		"""
		Return a useful description of the object. Currently used by GNUe Designer.
		"""

		if hasattr (self, '_description'):
			return self._description

		elif hasattr (self, 'name'):
			return "%s (%s)" % (self.name, self._type [2:])

		else:
			return "%s (%s)" % (self._type [2:], self._type [2:])


	# ---------------------------------------------------------------------------
	# Get the contents of all children of type GContent
	# ---------------------------------------------------------------------------

	def getChildrenAsContent (self):
		"""
		Returns the content of any GContent objects that are children of this
		object.

		@returns: The contents of the children
		"""

		result = ""

		for child in self._children:
			result += child._getAsContents_ ()

		return result


	# ===========================================================================
	# Virtual functions
	# ===========================================================================

	def _id_ (self, maxIdLength = None):
		"""
		Return a compareable and identifying id of an object within a tree. Usually
		this is it's name (if available) or it's object type (as given in the
		constructor).

		@param maxIdLength: if not None only return up to maxIdLength characters.
		@return: id for the instance
		"""
		# TODO: remove "and not self.name.startswith(self._type)"
		# make name generation not by random to make names same per startup
		if hasattr (self, 'name') and self.name is not None and not self.name.startswith(self._type):
			result = self.name.lower ()
			if maxIdLength is not None:
				result = result [:maxIdLength]
		else:
			result = self._type

		return result

	def _uid_(self):
		"""
		tree path id - really unique id of an object within a tree
		"""
		return '.'.join(map(lambda node: node._id_(), self.getTreePath()))

	# ---------------------------------------------------------------------------

	def _diffActionWalker_ (self, obj, action):
		"""
		Set the action attribute of a given object to the specified action.

		@param obj: L{ParserObj} to set the action attribute
		@param action: the action to be set
		"""

		obj._action = action


	# ---------------------------------------------------------------------------

	def _dumpXML_ (self, lookupDict, treeDump, gap, xmlnamespaces, textEncoding,
		stripPrefixes, escape):
		"""
		Return a XML representation of the object.

		@param lookupDict: dictionary describing the XML entities, their
		  attributes and types
		@param treeDump: if True, also include a XML representation of all children
		@param gap: string defining the current indentation level
		@param xmlnamespaces: dictionary with the available XML namespaces
		@param textEncoding: encoding used to transform string-type attributes into
		  unicode. If textEncoding is set to '<locale>' (default) it will be set to
		  the configuration variable 'textEncoding', i.e. from gnue.conf
		@param stripPrefixes: a list of prefixes that will automatically be removed
		  from the objects type.  This can be used to remove the GF from the start
		  of all the gnue-forms objects.  If set to None (the default) then the
		  behaviour will be the old style which removes the first two characters
		  from the type.
		@param escape: if set to True the resulting XML string should be escaped

		@returns: a string with the object's XML representation
		"""

		raise NotImplementedError


	# ---------------------------------------------------------------------------

	def _getAsContents_ (self):
		"""
		Get the contents of this object. Usually this will be used by
		getChildrenAsContents ().

		@returns: the contents of the object.
		"""

		return ""


	def _set_initial_attributes_(self, attributes):
		"""
		Set attributes loaded by GParser.

		@param attributes: dictionary of attributes
		"""
		self.__dict__.update(attributes)

	def __json__(self):
		return dict(
			(
				(attr, json(getattr(self, attr)))
				for attr in self._listedAttributes
			)
		)

def json(o):
	if hasattr(o, '__json__'):
		o = o.__json__()
	return o

# =============================================================================
# Mixin-class for leaf node objects
# =============================================================================

class GLeafNode:
	"""
	This is a I{mixin}-class for parser objects which are leaf nodes. This will
	be a relevant information on building difference-trees between two object
	trees. To add this class to another class do something like this::

	  class Foobar (ParserObj, GLeafNode): ...
	  class Barbaz (SomeOtherClass, GLeafNode): ...

	There is nothing more to do if you want to flag a class as leaf node.
	"""

	pass


# =============================================================================
# Base class for xml content
# =============================================================================

class GContent (ParserObj):
	"""
	Class representing XML content.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, content = None):

		ParserObj.__init__ (self, parent, '_content_')
		self._content     = content
		self._description = "(Content)"


	# ---------------------------------------------------------------------------
	# Return the escaped contents
	# ---------------------------------------------------------------------------

	def getEscapedContent (self):
		"""
		@returns: The escaped contents of this object
		"""

		return saxutils.escape (self._content)


	# ---------------------------------------------------------------------------
	# Return the contents
	# ---------------------------------------------------------------------------

	def getContent (self):
		"""
		@returns: The contents of this object
		"""

		return self._content


	# ---------------------------------------------------------------------------
	# Show a contents element within an (indented) tree
	# ---------------------------------------------------------------------------

	def showTree (self, indent = 0):
		"""
		Show a contents element within an indented tree
		"""

		print ' ' * indent + 'GContent ' + `self._content`


	# ---------------------------------------------------------------------------
	# Don't merge contents instances
	# ---------------------------------------------------------------------------

	def merge (self, other, maxIdLength = None, overwrite=False):
		"""
		Content objects cannot be merged together
		"""

		return


	# ---------------------------------------------------------------------------
	# Implementation of virtual methods
	# ---------------------------------------------------------------------------

	def _dumpXML_ (self, lookupDict, treeDump, gap, xmlnamespaces, textEncoding,
		stripPrefixes, escape):
		"""
		Return a XML representation of the contents. If the contents is a plain
		string (non unicode) it will be converted into unicode using the specified
		encoding or (if set to '<locale>') using the encoding as defined by the
		configuration variable 'textEncoding'. If the contents is of any other
		type it will be returned as is.

		@returns: XML representation of the contents
		"""

		if textEncoding == '<locale>':
			textEncoding = gConfig ('textEncoding')

		if isinstance (self._content, str):
			xmlString = '%s' % unicode (self._content, textEncoding)
		else:
			xmlString = self._content

		return escape and saxutils.escape (xmlString) or xmlString


	# ---------------------------------------------------------------------------

	def _getAsContents_ (self):
		"""
		@returns: the object's contents
		"""

		return self._content


# =============================================================================
# Base class for xml comment
# =============================================================================

class GComment (ParserObj):
	"""
	Class representing a comment within a XML tree.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, comment = None):

		ParserObj.__init__ (self, parent, '_comment_')
		self._comment = comment


	# ---------------------------------------------------------------------------
	# Implementation of virtual methods
	# ---------------------------------------------------------------------------

	def _dumpXML_ (self, lookupDict, treeDump, gap, xmlnamespaces, textEncoding,
		stripPrefixes, escape):
		"""
		Return a XML representation of the comment. If the comment is a plain
		string (non unicode) it will be converted into unicode using the specified
		encoding or (if set to '<locale>') using the encoding as defined by the
		configuration variable 'textEncoding'. If the comment is of any other
		type it will be returned as is.

		@returns: XML representation of the contents
		"""

		if textEncoding == '<locale>':
			textEncoding = gConfig ('textEncoding')

		if isinstance (self._comment, str):
			xmlString = '%s' % unicode (self._comment, textEncoding)
		else:
			xmlString = self._comment

		return '<!--%s-->\n' % xmlString
