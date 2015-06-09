# GNU Enterprise Common Library - GNUe XML object definitions
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
# $Id: GObjects.py 9222 2007-01-08 13:02:49Z johannes $

"""
Base class for GNUe objects which can be represented as XML
"""

__all__ = ['GObj', 'GUndividedCollection']

from xml.sax import saxutils
from gnue.common.definitions.GParserHelpers import GContent, ParserObj
from gnue.common.formatting import GTypecast
from gnue.common.logic.GTriggerCore import GTriggerCore


# =============================================================================
# Base class for GNUe object which can be represented by XML tags
# =============================================================================

class GObj (GTriggerCore, ParserObj):
	"""
	The base class for almost all GNUe objects. GObj based objects can be
	represented by XML tags in a GParser based setup. This class introduces the
	concept of phased initialization as well as dictionary style access.

	This is the method of attribute access used by Designer and Reports.
	For example. if foo is a GObject, then the following are equivalent::
	  foo.required = 'Y'
	  foo['required'] = 'Y'

	The advantage of this method, however, is when namespaces are used
	in the GObj XML document (i.e., reports). e.g., ::
	  foo['Char:x'] = 1
	  foo['Char:y'] = 2

	These don't have a clean equivalent using the .attribute method.
	(Though, technically, a tool could access foo.Char__x, but that
	should be considered bad style.)

	Eventually,  .attribute style access should probably be deprecated,
	so we can clean up the python namespaces of GObjects. (i.e., we could
	keep all XML-storable attributes in one dict instead of in the
	namespace __dict__.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, *args, **parms):

		GTriggerCore.__init__ (self)
		ParserObj.__init__ (self, *args, **parms)

		self._inits = []

		# Descendants can set this to True if they want their content to be saved
		# within <![CDATA[...]]>
		self._xml_content_as_cdata_ = False


	# ---------------------------------------------------------------------------
	# Dictionary style attribute access
	# ---------------------------------------------------------------------------

	def __getitem__ (self, key):

		return self.__dict__ [key.replace (':', '__')]


	# ---------------------------------------------------------------------------

	def __setitem__ (self, key, value):

		return self._setItemHook (key.replace (':', '__'), value)


	# ---------------------------------------------------------------------------
	# Build an object using attributes given as keyword arguments
	# ---------------------------------------------------------------------------

	def buildObject (self, **params):
		"""
		A convenience function for applications NOT using GParser to load an object
		tree.
		"""

		self.__dict__.update (params)
		return self._buildObject ()


	# ---------------------------------------------------------------------------
	# Build and initialize an object using attributes given as keyword arguments
	# ---------------------------------------------------------------------------

	def buildAndInitObject (self, **params):
		"""
		This is a convenience function for applications NOT using GParser to load
		an object tree.
		"""

		self.phaseInit (self.buildObject (**params))


	# ---------------------------------------------------------------------------
	# phaseInit
	# ---------------------------------------------------------------------------

	def phaseInit (self, iterations = 0):
		"""
		Starts GNUe's phased initialization system from this object down.

		Typically called from within a GParser instance.  phaseInit interates
		thru the GObj tree as many times as necessary to fully initialize the
		tree.  It determines the number of iterations to perform during it's
		first pass down the tree.

		phaseInit looks for a private list variable called _inits that
		contains a list of functions to execute.  Here is an example from
		gnue-forms GFForm object.

		C{self._inits = [self.primaryInit, None, self.secondaryInit]}

		This list tells phase init to execute the self.primaryInit function
		during the first iteration of the initialization process. During
		the seconds pass through it does nothing on these objects.  During the
		third pass through it executes self.secondaryInit.

		Some may question why we don't do all initialization logic inside the
		python objects __init__ functions.  Frequently you may find that a parent
		object may need specific infomation from some of its children to properly
		initialize itself.  This type of logic cannot be places into an __init__
		as the children may not be loaded yet or may not yet have the needed
		information.

		@param iterations: Limits the number of passes to the specified number.
		"""

		if iterations == 0:
			iterations = self.maxInits ()

		for phase in range (iterations):
			self._phaseInit (phase)


	# ---------------------------------------------------------------------------
	# Get the maximium size of all the _inits lists
	# ---------------------------------------------------------------------------

	def maxInits (self):
		"""
		maxInits returns the maximum size of all the _inits list from this object
		or it's children
		"""

		self._initCount = 0
		self.walk (self.__maxInitsWalker)
		return self._initCount

	# ---------------------------------------------------------------------------

	def __maxInitsWalker (self, object):
		"""
		The function passed to the tree walker to extract the length of the _inits
		list.

		@param object: L{GObj} to the get the length of it's _inits sequence
		"""
		if hasattr (object, '_inits'):
			self._initCount = max (self._initCount, len (object._inits))


	# ---------------------------------------------------------------------------
	# Show the XML tree of an object
	# ---------------------------------------------------------------------------

	def showTree (self, indent = 0):
		"""
		A recusive function to print an indented text representation of the GObj
		tree from this object down. This is usefull for debugging purposes.

		@param indent: Sets the level of indention.  Used during recursion to
		  properly indent the tree.
		@type indent: int
		"""

		print ' ' * indent + `self._type`, self

		for child in self._children:
			child.showTree (indent + 2)


	# ---------------------------------------------------------------------------
	# Get the XML tag used to represent the object
	# ---------------------------------------------------------------------------

	def getXmlTag (self, stripPrefixes = None):
		"""
		Returns the xml tag to be used to represent the object.

		@param stripPrefixes: A list of prefixes that will automatically be removed
		  from the objects type.  This can be used to remove the gf from the start
		  of all the gnue-forms objects.  If set to None (the default) then the
		  behaviour will be the old style which removes the first two characters
		  from the type.

		@returns: The XML tag to use
		@rtype: string
		"""

		if stripPrefixes is None:
			return self._type [2:].replace ('_', '-').lower ()

		for prefix in stripPrefixes:
			if prefix == self._type [:len (prefix)]:
				return self._type [len (prefix):].replace ('_', '-').lower ()

		return self._type.replace ('_', '-').lower ()


	# ---------------------------------------------------------------------------
	# Function for traversing an object tree
	# ---------------------------------------------------------------------------

	def walk (self, function, *args, **parms):
		"""
		Function that recursively walks down through a tree of L{ParserObj}
		instances and applies a function to them.

		@param function: the function to call for every element found in the tree
		"""

		function (self, *args, **parms)
		for child in self._children:
			if isinstance (child, GObj):
				child.walk (function, *args, **parms)


	# ---------------------------------------------------------------------------
	# Get an iterator for child objects
	# ---------------------------------------------------------------------------

	def iterator (self, test = None, types = (), includeSelf = True):
		"""
		Return a python iterator of child objects.

		@param test: A function that should return true or false to
		       indicate whether a GObject should be included in the
		       iterator. This method will be passed a GObj instance.
		       e.g., test=lambda obj: obj._type in ('GFField,'GFEntry')
		@type test: method

		@param types: A list of valid child types to return.
		       E.g., types=('GFField','GFEntry')
		@type types: list

		@param includeSelf: Should the current object be included in the tests?
		@type includeSelf: boolean

		@return: An iterator of matching objects

		"""
		if includeSelf:
			objects = [self]
		else:
			objects = self._children
		set = []

		def _includable (object):
			include = True
			if test:
				include = include and test (object)
			if types:
				include = include and object._type in types
			if include:
				set.append (object)

		for child in objects:
			child.walk (_includable)

		return _GObjectIterator (set)


	# ---------------------------------------------------------------------------
	# Worker function to perform an initialization
	# ---------------------------------------------------------------------------

	def _phaseInit (self, phase):
		"""
		Used internally by phaseInit to walk through the object tree initializing
		objects.
		"""

		## TODO: Below is a call-less recursive version of
		## TODO: phaseInit.  Needs to be profiled both ways.
		## TODO: Profile tests have shown this to be .001
		## TODO: cpu seconds faster per call
		##    stack = [self]
		##    while stack:
		##      object = stack.pop()
		##      for child in object._children:
		##        stack.insert(0,child)
		##      try:
		##        init = object._inits[phase]
		##      except IndexError:
		##        continue
		##      try:
		##        init()
		##      except TypeError:
		##        continue

		inits = self._inits
		if (len (inits) > phase) and inits [phase]:
			assert gDebug (7,"%s: Init Phase %s" % (self._type, phase+1))
			inits [phase] ()

		for child in self._children:
			try:
				initter = child._phaseInit
			except AttributeError:
				continue

			initter (phase)


	# ---------------------------------------------------------------------------
	# Get the number of phaseInit iterations needed by the object
	# ---------------------------------------------------------------------------

	def _buildObject (self):
		"""
		This function is called after the parsers have completely constructed. All
		children should be in place and attributes and content should be set at
		this point.  Return the number of phaseInit iterations your object will
		need.

		NOTE: Do not initialize datasources, etc at this point. This is only so
		content can be set, etc, after loading from XML.

		@returns: number of the phaseInit iterations needed by this object
		"""

		return len (self._inits)


	# ---------------------------------------------------------------------------
	# callback function called when an item has been changed
	# ---------------------------------------------------------------------------

	def _setItemHook (self, key, value):
		"""
		This bit of nastiness is here to let GNUe Designer capture the setting of
		GObject properties. This is primarily used in the wizard system so Designer
		can act in real time as a wizard sets a document's properties.

		I.e., if a wizard sets::
		  field['width'] = 10

		Designer can immediately changed the visual width of the field as displayed
		on screen.
		"""
		self.__dict__ [key] = value


	# ---------------------------------------------------------------------------
	# Implementation of virtual methods
	# ---------------------------------------------------------------------------

	def _dumpXML_ (self, lookupDict, treeDump, gap, xmlnamespaces, textEncoding,
		stripPrefixes, escape):
		"""
		Dumps an XML representation of the object
		"""

		xmlns    = ""
		xmlnsdef = ""

		if textEncoding == '<locale>':
			textEncoding = gConfig('textEncoding')

		try:
			if self._xmlnamespace:
				try:
					xmlns = xmlnamespaces [self._xmlnamespace] + ":"

				except KeyError:
					i     = 0
					xmlns = "out"

					while xmlns in xmlnamespaces.values ():
						i    += 1
						xmlns = "out%s" % i

					xmlnamespaces [self._xmlnamespace] = xmlns
					xmlnsdef = ' xmlns:%s="%s"' % (xmlns, self._xmlnamespace)
					xmlns   += ":"

		except AttributeError:
			try:
				if self._xmlchildnamespace:
					if not xmlnamespaces.has_key (self._xmlchildnamespace):
						i  = 0
						ns = "out"

						while ns in xmlnamespaces.values ():
							i += 1
							ns = "out%s" % i

						xmlnamespaces [self._xmlnamespace] = ns
						xmlnsdef = ' xmlns:%s="%s"' % (ns, self._xmlchildnamespace)

			except AttributeError:
				pass

		try:
			if self._xmlchildnamespaces:
				for abbrev in self._xmlchildnamespaces.keys ():
					xmlnsdef += ' xmlns:%s="%s"' % \
						(abbrev, self._xmlchildnamespaces [abbrev])

		except AttributeError:
			pass

		xmlEntity = self.getXmlTag (stripPrefixes)
		xmlString = "%s<%s%s%s" % (gap[:-2], xmlns, xmlEntity, xmlnsdef)

		indent = len (xmlString)
		pos    = indent
		attrs  = self.__dict__.keys ()
		attrs.sort ()

		# Make 'name' first
		if 'name' in attrs:
			attrs.pop (attrs.index ('name'))
			attrs.insert (0, 'name')

		# Iterate over all attributes which do not start with an underscore
		for attribute in [a for a in attrs if a [0] != "_"]:
			val = self.__dict__ [attribute]

			if (xmlns and attribute in self._listedAttributes) or \
				(not xmlns and lookupDict [xmlEntity].has_key ('Attributes') and \
					lookupDict [xmlEntity]['Attributes'].has_key (attribute)):

				try:
					attrDef = lookupDict [xmlEntity]['Attributes'][attribute]
				except KeyError:
					attrDef = {}

				if val != None and \
					(xmlns or (not 'Default' in attrDef or \
							(attrDef ['Default']) != (val))):

					typecast = attrDef.get ('Typecast', GTypecast.text)

					if typecast == GTypecast.boolean:
						addl = ' %s="%s"' % (attribute, ['N', 'Y'][bool (val)])

					elif typecast == GTypecast.names:
						if isinstance (val, (list, tuple)):
							addl = ' %s="%s"' % (attribute, ','.join (val))
						elif isinstance (val, string):
							addl = ' %s="%s"' % (attribute, unicode (val, textEncoding))
						else:
							addl = ' %s="%s"' % (attribute, val)

					else:
						cont = '%s' % val
						if isinstance (val, str):
							cont = unicode (val, textEncoding)

						addl = ' %s="%s"' % (attribute, saxutils.escape (cont))

					if len (addl) + pos > 78:
						xmlString += "\n" + " " * indent + addl
						pos        = indent
					else:
						xmlString += addl
						pos       += len (addl)

			if attribute.find ('__') > 0 and \
				attribute.split ('__') [0] in xmlnamespaces:

				if val != None:
					attrName  = attribute.replace ('__', ':')
					attrValue = val

					if isinstance (val, str):
						attrValue = unicode (val, textEncoding)
					else:
						try:
							if val == int (val):
								attrValue = int (val)

						except:
							pass

					addl = ' %s="%s"' % (attrName, saxutils.escape ('%s' % attrValue))

					if len (addl) + pos > 78:
						xmlString += "\n" + " " * indent + addl
						pos = indent
					else:
						xmlString += addl
						pos += len (addl)

		if len (self._children):
			hasContent = 0
			for child in self._children:
				hasContent = hasContent or isinstance (child, GContent)
			if hasContent:
				xmlString += ">"
			else:
				xmlString += ">\n"

			if treeDump:
				if hasContent and self._xml_content_as_cdata_:
					xmlString += "<![CDATA["
				for child in self._children:
					xmlString += child.dumpXML (lookupDict, True, gap + "  ",
						xmlnamespaces, textEncoding, stripPrefixes,
						(not self._xml_content_as_cdata_) and escape)
				if hasContent and self._xml_content_as_cdata_:
					xmlString += "]]>"

			if hasContent:
				xmlString += "</%s%s>\n" % (xmlns, xmlEntity)
			else:
				xmlString += "%s</%s%s>\n" % (gap [:-2], xmlns, xmlEntity)

		else:
			xmlString += "/>\n"

		return xmlString


# =============================================================================
# Collection class where the children in a diff won't get divided
# =============================================================================

class GUndividedCollection (GObj):
	"""
	GUndividedCollection implements a collection class where the children in a
	diff () won't get divided. Example: A primary key definition can contain
	multiple primary key fields. If a primary key definition differs from another
	one, it's fields must be kept as a union.
	"""

	# ----------------------------------------------------------------------------
	# Constructor
	# ----------------------------------------------------------------------------

	def __init__ (self, *args, **kwargs):

		GObj.__init__ (self, *args)
		self.buildObject (**kwargs)


	# ----------------------------------------------------------------------------
	# Build a difference-tree to the given object tree
	# ----------------------------------------------------------------------------

	def diff (self, goal, maxIdLength=None):
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

		result = ParserObj.diff (self, goal, maxIdLength)

		if result is not None:
			for item in result._children [:]:
				# We cannot change a child of an immutable collection directly, instead
				# we remove the original and add the changed one.
				if item._action == 'change':
					result._children.remove (item)

					# Add a copy of the 'old' item to be 'removed'
					for old in self._children:
						if old._id_ (maxIdLength) == item._id_ (maxIdLength):
							add = old.__class__ (result)
							add.assign (old, True)
							add.walk (self._diffActionWalker_, "remove")
							break

					# and one copy of the 'new' item to be 'added'
					for new in goal._children:
						if new._id_ (maxIdLength) == item._id_ (maxIdLength):
							add = new.__class__ (result)
							add.assign (new, True)
							add.walk (self._diffActionWalker_, "add")
							break

		return result



# =============================================================================
# Convenience class for the GObject .iterator () method
# =============================================================================

class _GObjectIterator:
	"""
	Convenience class for L{GObj.iterator} method providing an iterator over a
	given set of L{GObj} instances (children).
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, set):

		self.stack = set [:]


	# ---------------------------------------------------------------------------
	# Return the iterator object
	# ---------------------------------------------------------------------------

	def __iter__ (self):
		"""
		@returns: the iterator object itself.
		"""

		return self


	# ---------------------------------------------------------------------------
	# Get the next item
	# ---------------------------------------------------------------------------

	def next (self):
		"""
		Return the next item from the container.
		@returns: the next item from the container
		@raises StopIteration: If no more items are available in the container.
		"""

		if self.stack:
			return self.stack.pop (0)
		else:
			raise StopIteration
