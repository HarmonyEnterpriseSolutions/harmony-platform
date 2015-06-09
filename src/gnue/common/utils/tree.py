# GNU Enterprise Common Library - Tree structure classes
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
# $Id: tree.py 9222 2007-01-08 13:02:49Z johannes $

"""
Classes representing a node in a tree structure.

TODO: This module is work in progress.
"""

import locale

from gnue.common.apps import errors
from gnue.common.apps.i18n import utranslate as u_      # for epydoc

__all__ = ['CircularReferenceError', 'DuplicateChildNameError',
	'DuplicateDescendantNameError', 'NodeDictNotAvailableError',
	'Node', 'NamedNode', 'AttribNode']


# =============================================================================
# Exceptions
# =============================================================================

class CircularReferenceError(errors.SystemError):
	"""
	Setting parent would create a circular reference.

	Setting the requested parent for this node would create a circular
	reference in the tree, like A is the parent of B, B is the parent of C, and
	C is the parent of A.
	"""
	def __init__(self):
		message = u_("Setting parent would create a circular reference")
		errors.SystemError.__init__(self, message)


# =============================================================================

class DuplicateChildNameError(errors.SystemError):
	"""
	Duplicate child name.

	Changing the node name or the parent of this node as requested would result
	in the (new) parent having two children with the same node name.

	Note that after this exception has happened, the tree is in an inconsistent
	state.
	"""
	def __init__(self, child_name, parent_node):
		message = u_(
			"Duplicate child name '%(child_name)s' for parent node "
			"'%(parent_node)s'")
		errors.SystemError.__init__(self, message % {
				'child_name': child_name,
				'parent_node': repr(parent_node)})


# =============================================================================

class DuplicateDescendantNameError(errors.SystemError):
	"""
	Duplicate descendant name for node type.

	Changing the node name or the parent of this node as requested would result
	in a (new) ancestor of this node having two descendants of the same type
	with the same name. This is only a problem if this ancestor maintains a
	dictionary of the descendants of this type.

	Note that after this exception has happened, the tree is in an inconsistent
	state.
	"""
	def __init__(self, descendant_name, descendant_type, ancestor_node):
		message = u_(
			"Duplicate node name '%(descendant_name)s' in descendants of "
			"node type %(descendant_type)s of node '%(ancestor_node)s'")
		errors.SystemError.__init__(self, message % {
				'descendant_name': descendant_name,
				'descendant_type': descendant_type,
				'ancestor_node': ancestor_node})


# =============================================================================

class NodeDictNotAvailableError(errors.SystemError):
	"""
	Node Dictionary not available for this type.

	This node class does not maintain a node dictionary for the requested type.
	"""
	def __init__(self, node_name, node_class, node_type):
		message = u_(
			"Node '%(node_name)s' of class '%(node_class)s' does not "
			"maintain a node dictionary for node type '%(node_type)s'")
		errors.SystemError.__init__(self, message % {
				'node_name': node_name,
				'node_class': node_class.__module__ + '.' + node_class.__name__,
				'node_type': node_type})


# =============================================================================
# Node class
# =============================================================================

class Node(object):
	"""
	A node in a n-ary tree.

	Instances of this class represent nodes that make up a tree structure. Each
	node can have one parent (a node with a parent of C{None} is a root node)
	and an arbitary number of children.

	The parent of a node is defined on creation of the node, but can be changed
	later. Nodes keep track of their children automatically, so changing the
	parent of a node from A to B will automatically remove the node from A's
	list of children and add it to B's list of children.

	Children of a node are sorted in the order in which they were attached to
	the parent.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent):
		"""
		Initialize a new node.

		@param parent: Parent node.
		@type parent: Node
		"""

		#: Parent node or C{None} if this is the root node
		self.__parent = None

		#: List of child nodes
		self.__children = []

		self.parent = parent


	# -------------------------------------------------------------------------
	# Property "parent"
	# -------------------------------------------------------------------------

	def __get_parent(self):

		return self.__parent

	# -------------------------------------------------------------------------

	def __set_parent(self, value):

		checktype(value, [Node, None])

		self._set_parent_(value)

	# -------------------------------------------------------------------------

	parent = property(__get_parent, __set_parent, None,
	"""
	Parent node, or C{None} if this is the root of the tree.

	@type: Node or None
	""")


	# -------------------------------------------------------------------------
	# Property "children"
	# -------------------------------------------------------------------------

	# This is a property because we want to make it readonly

	def __get_children(self):

		return self.__children

	# -------------------------------------------------------------------------

	children = property(__get_children, None, None,
	"""
	List of child nodes. (readonly)

	@type: [Node]
	""")


	# -------------------------------------------------------------------------
	# Property "root"
	# -------------------------------------------------------------------------

	def __get_root(self):

		result = self
		while result.__parent is not None:
			result = result.__parent
		return result

	# -------------------------------------------------------------------------

	root = property(__get_root, None, None,
	"""
	Root node of the tree this node is a member of. (readonly)

	@type: Node
	""")


	# -------------------------------------------------------------------------
	# Apply a function to every element in the tree
	# -------------------------------------------------------------------------

	def walk(self, function, *args, **kwargs):
		"""
		Apply a function to all nodes of the (sub)tree rooted at this node.

		The function is first applied to this node, then to the first child
		node, then to all children of the first child node recursively, then to
		the next child node, etc.

		The function is called with the repective node as the first argument,
		followed by the positional arguments and keyword arguments provided in
		the call to C{walk}.

		@param function: Function to call on every node.
		@type function: callable
		@param args: Positional arguments
		@type args: tuple
		@param kwargs: Keyword arguments
		@type kwargs: dict
		"""

		function(self, *args, **kwargs)
		for child in self.__children:
			child.walk(function, *args, **kwargs)


	# -------------------------------------------------------------------------
	# Abstract functions
	# -------------------------------------------------------------------------

	def _set_parent_(self, parent):
		"""
		Hook for subclasses to register a parent change.

		Subclasses can implement this method to execute stuff that has to be
		done whenever a node gets a new parent.
		"""

		# Make sure that we don't create a circular reference
		node = parent
		while node is not None:
			if node is self:
				raise CircularReferenceError
			node = node.__parent

		# Unregister with old parent
		if self.__parent is not None:
			self.__parent.__children.remove(self)

		# Set new parent
		self.__parent = parent

		# Register with new parent
		if self.__parent is not None:
			self.__parent.__children.append(self)


# =============================================================================
# NamedNode class
# =============================================================================

class NamedNode(Node):
	"""
	A node in an n-ary tree with a node type and a name.

	C{NamedNode}s introduce a L{I{node type} <node_type>} and a L{I{node name}
	<node_name>}. While for a given subclass of C{NamedNode}, all instances
	share the same node type, each instance has a different node name.

	Children of C{NamedNode}s that are also C{NamedNode}s can be L{accessed
	with their name <get_child>}.

	Instances of this class support searching ancestors L{for a given node type
	<find_ancestor_of_type>} and searching descendants L{for a given node
	name <find_descendant>} or L{for a given node type
	<find_descendant_of_type>}.

	Every C{NamedNode} instance can define a list of node types it is
	interested in. Descendants of each of these types will be hashed in a
	L{dictionary <get_node_dict>} (a separate dictionary per type).

	@cvar _node_type_: Type of this node. Defined by subclasses.
	@type _node_type_: str

	@cvar _node_dicts_: List of types for which descendants should be hashed.
	    Defined by subclasses.
	@type _node_dicts_: [str]
	"""

	# -------------------------------------------------------------------------
	# Class variables
	# -------------------------------------------------------------------------

	_node_type_ = None
	_node_dicts_ = []


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent):
		"""
		Initialize a new named node.

		@param parent: Parent node.
		@type parent: Node
		"""

		#: Node name
		# Must be set before __init__, because setting the parent already needs
		# this variable.
		self.__node_name = None

		Node.__init__(self, parent)

		#: Dictionary with all named children
		self.__named_children = {}

		#: Dictionaries with descendants of interesting node types
		self.__node_dicts = dict.fromkeys(self._node_dicts_, {})


	# -------------------------------------------------------------------------
	# Nice string representation
	# -------------------------------------------------------------------------

	def __repr__(self):
		"""
		Return a string representation of the node.

		The string representation is either the node name, or, if there is no
		node name defined, a string saying C{"<unnamed I{node_type}>"}.

		If the node name is a unicode string, it is converted to the encoding
		as defined in the current locale.
		"""

		if self.__node_name is None:
			if self._node_type_ is None:
				return "<unnamed untyped node>"
			else:
				return "<unnamed " + self._node_type_ + ">"

		elif isinstance(self.__node_name, unicode):
			return self.__node_name.encode(locale.getlocale()[0], 'replace')

		else:
			return self.__node_name


	# -------------------------------------------------------------------------
	# Property "node_type"
	# -------------------------------------------------------------------------

	def __get_node_type(self):

		return self._node_type_

	# -------------------------------------------------------------------------

	node_type = property(__get_node_type, None, None,
	"""
	Node type.

	The node type is defined in the class definition of descendant
	classes of L{NamedNode}. All nodes of the same class have the same
	type. You can think of the node type as a "nice name for the class
	of the node".

	@type: basestring
	""")

	# -------------------------------------------------------------------------
	# Property "node_name"
	# -------------------------------------------------------------------------

	def __get_node_name(self):

		return self.__node_name

	# -------------------------------------------------------------------------

	def __set_node_name(self, value):

		checktype(value, [basestring, None])

		if self.__node_name is not None:
			self.__unregister()

		self.__node_name = value

		if self.__node_name is not None:
			self.__register()


	# -------------------------------------------------------------------------

	node_name = property(__get_node_name, __set_node_name, None,
	"""
	Name of the node.

	Usually, every node in a tree has a different name. Nodes may also
	be unnamed (meaning a name of None).

	@type: basestring
	""")


	# -------------------------------------------------------------------------
	# Register with parents and ancestors if parent is changed
	# -------------------------------------------------------------------------

	def _set_parent_(self, parent):

		if self.__node_name is not None:
			self.__unregister()

		Node._set_parent_(self, parent)

		if self.__node_name is not None:
			self.__register()


	# -------------------------------------------------------------------------
	# Helper methods to register/unregister with parent and ancestors
	# -------------------------------------------------------------------------

	def __register(self):

		# register with parent
		if isinstance(self.parent, NamedNode):
			child_dict = self.parent.__named_children
			if child_dict.has_key(self.__node_name):
				raise DuplicateChildNameError, (self.__node_name, self.parent)
			child_dict[self.__node_name] = self

		# register with all ancestors that have a node_dict for this node type
		ancestor = self.parent
		while ancestor is not None:
			if isinstance(ancestor, NamedNode):
				if ancestor.__node_dicts.has_key(self._node_type_):
					node_dict = ancestor.__node_dicts[self._node_type_]
					if node_dict.has_key(self.__node_name):
						raise DuplicateDescendantNameError, (self.__node_name,
							self._node_type_, ancestor)
					node_dict[self.__node_name] = self
			ancestor = ancestor.parent

	# -------------------------------------------------------------------------

	def __unregister(self):

		# unregister with parent
		if isinstance(self.parent, NamedNode):
			del self.parent.__named_children[self.__node_name]

		# unregister with all ancestors that have a node_dict for this node type
		ancestor = self.parent
		while ancestor is not None:
			if isinstance(ancestor, NamedNode):
				node_dicts = ancestor.__node_dicts
				if node_dicts.has_key(self._node_type_):
					del ancestor.__node_dicts[self._node_type_]\
						[self.__node_name]
			ancestor = ancestor.parent


	# -------------------------------------------------------------------------
	# Get child with the given node name
	# -------------------------------------------------------------------------

	def get_child(self, node_name):
		"""
		Return the child node with the given node name

		@param node_name: The node name of the desired child
		@type node_name: basestring

		@return: The child node with that node name, or C{None} if there is
		    no such child node.
		@rtype: NamedNode or None
		"""

		return self.__named_children.get(node_name)


	# -------------------------------------------------------------------------
	# Find first parent of a given node type
	# -------------------------------------------------------------------------

	def find_ancestor_of_type(self, node_type):
		"""
		Return the nearest ancestor with the given node type.

		This function searches through all ancestors (parent, parent of the
		parent, etc.) of this node until it finds a node of the given node
		type. If none of the ancestors is of the given type, None is returned.

		If a node isn't an instance of a subclass of L{NamedNode}, it is
		ignored, however the search is continued by its parent.

		@param node_type: Node type to search for.
		@type node_type: str

		@return: Ancestor node of the given node type.
		@rtype: NamedNode or None
		"""

		checktype(node_type, str)

		parent = self.parent
		while parent is not None:
			if isinstance(parent, NamedNode):
				if parent._node_type_ == node_type:
					return parent
			parent = parent.parent
		return None


	# -------------------------------------------------------------------------
	# Find first descendant with a given node name
	# -------------------------------------------------------------------------

	def find_descendant(self, node_name):
		"""
		Return the first descendant with the given node name.

		This function searches through all descendants (children, children of
		children, etc.) of this node until it finds a node with the given node
		name. If none of the descendants has the given type, None is returned.

		If a node isn't an instance of a subclass of L{NamedNode}, it is
		ignored, however the search is continued by its children.

		The search is first applied to the first child node, then to all
		children of the first child node recursively, then to the next child
		node, etc.

		@param node_name: Node name to search for.
		@type node_name: basestring

		@return: Descendant node of the given node type.
		@rtype: NamedNode or None
		"""

		checktype(node_name, basestring)

		# We need a helper function so we can traverse nodes not derived from
		# NamedNode.
		return self.__find_descendant(self, node_name)


	# -------------------------------------------------------------------------
	# Helper function for searching recursively through descendants
	# -------------------------------------------------------------------------

	def __find_descendant(self, node, node_name):

		for child in node.children:
			if isinstance(child, NamedNode):
				if child.__node_name == node_name:
					return child
			found = self.__find_descendant(child, node_name)
			if found is not None:
				return found

	# -------------------------------------------------------------------------
	# Find first descendant of a given node type
	# -------------------------------------------------------------------------

	def find_descendant_of_type(self, node_type):
		"""
		Return the first descendant with the given node type.

		This function searches through all descendants (children, children of
		children, etc.) of this node until it finds a node of the given node
		type. If none of the descendants is of the given type, None is
		returned.

		If a node isn't an instance of a subclass of L{NamedNode}, it is
		ignored, however the search is continued by its children.

		The search is first applied to the first child node, then to all
		children of the first child node recursively, then to the next child
		node, etc.

		@param node_type: Node type to search for.
		@type node_type: str

		@return: Descendant node of the given node type.
		@rtype: NamedNode or None
		"""

		checktype(node_type, str)

		# We need a helper function so we can traverse nodes not derived from
		# NamedNode.
		return self.__find_descendant_of_type(self, node_type)


	# -------------------------------------------------------------------------
	# Helper function for searching recursively through descendants
	# -------------------------------------------------------------------------

	def __find_descendant_of_type(self, node, node_type):

		for child in node.children:
			if isinstance(child, NamedNode):
				if child._node_type_ == node_type:
					return child
			found = self.__find_descendant_of_type(child, node_type)
			if found is not None:
				return found


	# -------------------------------------------------------------------------
	# Get node dictionary with all descendant nodes of a given type
	# -------------------------------------------------------------------------

	def get_node_dict(self, node_type):
		"""
		Return a dictionary with all descendant nodes of the given node type.

		The node names are the keys of the dictionary, and the node objects
		are the values. Nodes without a node name aren't included in the
		dictionary.

		This function only works for node types that have been registered in
		the L{_node_dicts_} list of the class of this node.
		"""

		if node_type not in self.__node_dicts:
			raise NodeDictNotAvailableError, (self.__node_name, self.__class__,
				node_type)
		return self.__node_dicts[node_type]


# =============================================================================
# AttribNode class
# =============================================================================

class AttribNode(NamedNode):
	"""
	A node in an n-ary tree with node attributes.

	Every subclass of this class can define a set of valid attributes that
	nodes of this subclass will have, of what type the attributes are, and what
	default value these attributes will have.

	TODO: document structure of _node_attribs_ dictionary, and give examples
	how to use it (especially how to extend the inherited dictionary in
	subclasses).

	Instances of this class expose their attributes through dictionary access.
	The attribute 'my_attr' of the object instance 'my_node' can be read and
	written as C{my_node['my_attr']}.

	On creation of new instances, attributes are initialized with their default
	value, or with C{None} if no default value is defined.

	Whenever an attribute value is set, it is typecast to the defined type. If
	this typecast fails, the value is not changed, and an exception is raised.

	Attribute types can not only be ordinary data types (like C{unicode},
	C{str}, or C{int}, but they can also be subclasses of L{NamedNode}. In this
	case, both C{my_node['my_attr'] = other_node} and
	C{my_node['my_attr'] = 'other_node_name'} are valid, and will cause
	C{my_node['my_attr']} to evaluate to other_node, provided that other_node
	has a name of 'other_node_name', both my_node and other_node are in the
	same tree, and the type of other_node is registered in the root node's
	C{_node_dicts_} list.
	"""

	# -------------------------------------------------------------------------
	# Class variables
	# -------------------------------------------------------------------------

	_node_attribs_ = {
		'name': {
			'type': str,
			'label': u_("name"),
			'description': u_("Name of this element"),
			'default': None}}


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent):
		"""
		Initialize a new attributed node.

		@param parent: Parent node.
		@type parent: Node
		"""

		NamedNode.__init__(self, parent)

		#: Attributes
		self.__attribs = {}

		for (name, definition) in self._node_attribs_:
			self.__attribs[name] = definition.get('default')


	# -------------------------------------------------------------------------
	# Dictionary style attribute access
	# -------------------------------------------------------------------------

	def __getitem__(self, name):

		try:
			definition = self._node_attribs_[name]
		except KeyError:
			raise InvalidAttributeError(self, name)

		# if this is a reference to another node, look for it in the parent's
		# node dictionary
		target_type = definition['type']

		# TODO: find node type for wanted class, look up name in root's node
		# dictionary.

		return self.__attribs[name]

	# -------------------------------------------------------------------------

	def __setitem__(self, name, value):

		try:
			definition = self._node_attribs_[name]
		except KeyError:
			raise InvalidAttributeError(self, name)

		# typecast if necessary
		target_type = definition['type']

		# if this is a reference to another node, we need to store the name
		if issubclass(target_type, NamedNode):
			target_type = unicode

		if not isinstance(value, target_type):
			try:
				value = target_type(value)
			except Exception, e:
				raise InvalidAttributeValueError(self, name, value, e)

		# TODO: check if value is in list of allowed values if defined in
		# _node_attribs_
		self.__attribs[name] = value


# =============================================================================
# Self test code
# =============================================================================

# -----------------------------------------------------------------------------
# Node class
# -----------------------------------------------------------------------------

def test_node_class():

	# Descendant of Node used in test code
	class TestNode(Node):
		def __init__(self, parent, text):
			Node.__init__(self, parent)
			self.__text = text
		def __str__(self):
			return self.__text

	# Build up our tree
	root = TestNode(None, 'People')
	monty_python = TestNode(root, 'Monty Python')
	john_cleese = TestNode(monty_python, 'John Cleese')
	TestNode(monty_python, 'Michael Palin')
	TestNode(monty_python, 'Graham Chapman')
	TestNode(monty_python, 'Terry Jones')
	TestNode(monty_python, 'Terry Gilliam')
	star_trek = TestNode(root, 'Star Trek')
	TestNode(star_trek, 'James T. Kirk')
	TestNode(star_trek, 'Mr. Spock')
	TestNode(star_trek, 'Leonard McCoy')

	# Test "children" property
	print "The Monty Python group:"
	for child in monty_python.children:
		print "   ", child

	# Test "parent" and "root" property
	print john_cleese, "is a member of", john_cleese.parent
	print "    and all are", john_cleese.root

	# Test "walk" function
	def printout(self, prefix):
		print prefix, self
	print "All nodes:"
	root.walk(printout, "   ")

	# Test "CircularReferenceError" exception
	try:
		monty_python.parent = john_cleese
	except CircularReferenceError, error:
		print "Correctly got an exception:", error
	print monty_python, "has now a parent of", monty_python.parent


# -----------------------------------------------------------------------------
# NamedNode class
# -----------------------------------------------------------------------------

def test_named_node_class():

	# Descendants of NamedNode used in test code
	class TextNode(NamedNode):
		def __init__(self, parent, text):
			NamedNode.__init__(self, parent)
			self.node_name = text
	class GroupNode(TextNode):
		_node_type_ = 'group'
		_node_dicts_ = ['man']
	class ManNode(TextNode):
		_node_type_ = 'man'
	class WomanNode(TextNode):
		_node_type_ = 'woman'

	# Build up our tree
	root = GroupNode(None, 'People')
	monty_python = GroupNode(root, 'Monty Python')
	john_cleese = ManNode(monty_python, 'John Cleese')
	ManNode(monty_python, 'Michael Palin')
	ManNode(monty_python, 'Graham Chapman')
	ManNode(monty_python, 'Terry Jones')
	ManNode(monty_python, 'Terry Gilliam')
	WomanNode(monty_python, None)       # The woman whose name I can't remember
	star_trek = GroupNode(root, 'Star Trek')
	james_kirk = ManNode(star_trek, 'James T. Kirk')
	ManNode(star_trek, 'Mr. Spock')
	ManNode(star_trek, 'Leonard McCoy')
	WomanNode(star_trek, 'Nyota Uhura')
	ManNode(star_trek, None)    # The nameless security officer
	wife = Node(james_kirk)     # Kirk's wife - unnamed node by intention
	peter_kirk = ManNode(wife, 'Peter Kirk')   # Kirk's son

	# Test "node_type" property
	print james_kirk, "is node type", james_kirk.node_type

	# Test "node_name" property
	print james_kirk, "is node name", james_kirk.node_name

	# Test "get_child" method
	print "Terry Jones can be found:", monty_python.get_child('Terry Jones')

	# Test "find_ancestor_of_type" method
	print peter_kirk, "belongs to", peter_kirk.find_ancestor_of_type('group')

	# Test "find_descendant" method
	print "Peter Kirk can be found:", star_trek.find_descendant('Peter Kirk')

	# Test "find_descendant_of_type" method
	print "Nyota Uhura can be found:", \
		star_trek.find_descendant_of_type('woman')

	# Test "get_node_dict" method
	print "All men of the Monty Python group:"
	for (key, value) in monty_python.get_node_dict('man').items():
		print "   ", key, "=", value
	print "All men of the Star Trek group:"
	for (key, value) in star_trek.get_node_dict('man').items():
		print "   ", key, "=", value
	print "All men of all groups:"
	for (key, value) in root.get_node_dict('man').items():
		print "   ", key, "=", value

	# Test changing node name:
	james_kirk.node_name = 'James Tiberius Kirk'
	print "Now Kirk's node name has changed to", james_kirk.node_name
	print "Now he can be found under the new name with get_child:", \
		star_trek.get_child('James Tiberius Kirk')
	print "Now he can be found under the new name with find_descendant:", \
		root.find_descendant('James Tiberius Kirk')
	print "He cannot be found under the old name any more:", \
		star_trek.get_child('James T. Kirk'), "-", \
		root.find_descendant('James T. Kirk')
	print "He is in root's node_dict as 'James Tiberius Kirk':", \
		'James Tiberius Kirk' in root.get_node_dict('man')
	print "He is in root's node_dict as 'James T. Kirk':", \
		'James T. Kirk' in root.get_node_dict('man')

	# Test changing parent: get_child, get_node_dict for old and new
	print "Making John Cleese a son of James Kirk's wife (ugh!)"
	john_cleese.parent = wife
	print "Now he can be found under Star Trek with find_descendant:", \
		star_trek.find_descendant('John Cleese')
	print "He cannot be found under Monty Python any more:", \
		monty_python.get_child('John Cleese'), "-", \
		monty_python.find_descendant('John Cleese')
	print "He is in Star Trek's node_dict:", \
		'John Cleese' in star_trek.get_node_dict('man')
	print "He is in Monty Python's node_dict:", \
		'John Cleese' in monty_python.get_node_dict('man')

	# Test DuplicateChildNameError
	try:
		TextNode(star_trek, 'Nyota Uhura')
	except DuplicateChildNameError, error:
		print "Correctly got an exception:", error
	new_uhura = WomanNode(wife, 'Nyota Uhura')          # this may not fail...
	try:
		new_uhura.parent = star_trek                    # ...but this must fail
	except DuplicateChildNameError, error:
		print "Correctly got an exception:", error

	# Test DuplicateDescendantNameError
	try:
		TextNode(peter_kirk, 'Terry Jones')
	except DuplicateDescendantNameError, error:
		print "Correctly got an exception:", error

	# Test NodeDictNotAvailableError
	try:
		root.get_node_dict('woman')
	except NodeDictNotAvailableError, error:
		print "Correctly got an exception:", error


# -----------------------------------------------------------------------------
# Run tests
# -----------------------------------------------------------------------------

if __name__ == '__main__':

	test_node_class()
	test_named_node_class()
