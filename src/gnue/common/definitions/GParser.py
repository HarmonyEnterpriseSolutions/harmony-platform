# GNU Enterprise Common Library - GNUe XML object definitions - XML Parser
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
# $Id: GParser.py,v 1.9 2009/09/05 15:28:57 oleg Exp $

"""
Class that contains a SAX2-based XML processor for GNUe
"""

__all__ = ['MarkupError', 'loadXMLObject', 'normalise_whitespace',
	'xmlHandler', 'GImportItem', 'GImport']

import sys, copy, types
from gnue.common.definitions.GObjects import GObj
from gnue.common.definitions.GRootObj import GRootObj
from gnue.common.utils.FileUtils import openResource, dyn_import

try:
	from xml.sax.handler import property_lexical_handler
	from xml.sax import saxutils
	import xml.sax

except ImportError:
	print """
   This GNUe tool requires pythons XML module be installed.
   Typically this is the case, however some GNU/Linux distro's
   like Debian distribute this as a seperate package

   To install this package...
     On Debian: apt-get install python-xml

"""


import os

from gnue.common.apps import errors
from gnue.common.formatting import GTypecast
from gnue.common.definitions.GParserHelpers import GContent, GComment


# =============================================================================
# Exceptions
# =============================================================================

class MarkupError (errors.ApplicationError):
	def __init__ (self, message, url = None, line = None):
		errors.ApplicationError.__init__ (self, message)
		text = [message]
		if url is not None:
			if line is not None:
				msg = u_("XML markup error in '%(url)s' at line %(line)s:") \
					% {'url': url, 'line': line}
			else:
				msg = u_("XML markup error in '%(url)s':") % {'url': url}

			text.insert (0, msg)

		self.detail = os.linesep.join (text)

# =============================================================================

class InvalidValueSetError (MarkupError):
	def __init__ (self, attr, obj, vals):
		msg = u_("'%(value)s' is not valid for %(attr)s-attribute which allows "
			"these values only: %(allowed)s") \
			% {'attr': attr,
			'allowed': ",".join (["'%s'" % i for i in vals]),
			'value': getattr(obj, attr)}
		MarkupError.__init__ (self, msg, obj._url, obj._lineNumber)


# -----------------------------------------------------------------------------
# Build an object from a XML stream
# -----------------------------------------------------------------------------

def loadXMLObject (stream, handler, rootType, xmlFileType,
	initialize = True, attributes = {}, initParameters = {}, url = None,
	checkRequired = True):
	"""
	This method loads an object from a XML stream and returns that object.  If
	initialize is True (default), then the object is initialized and ready to go.
	Setting initialize to 0 is useful for a design environment where the object
	is not actually being used, but simply loaded as a document.

	"attributes" is a dictionary containing extra attributes that should be
	attached to this object.

	e.g., if attributes={myproperty:[0,1,2]}, then before the object is
	initialized or returned, object.myproperty == [0,1,2].
	"""

	# Create a parser
	parser = xml.sax.make_parser ()


	# Set up some namespace-related stuff for the parsers
	parser.setFeature (xml.sax.handler.feature_namespaces, 1)


	# Allow for parameter external entities
	## Does not work with expat!!! ##
	##parser.setFeature(xml.sax.handler.feature_external_pes, 1)

	# Create a stack for the parsing routine
	object = None

	# Create the handler
	dh = handler ()

	# pass the url of the stream and a pointer to the parser instance down to the
	# handler, so it's able to do better error reporting
	if url is None:
		url = hasattr (stream, 'url') and stream.url or '[unknown]'

	dh.url = url
	dh.checkRequired = checkRequired
	dh.parser = parser
	dh.root_attributes = attributes

	dh.initValidation ()

	# Tell the parser to use our handler
	parser.setContentHandler (dh)

	try:
		parser.setProperty (property_lexical_handler, dh)
	except Exception, e:
		print e

	try:
		parser.parse (stream)

	except xml.sax.SAXParseException, e:
		raise MarkupError, (errors.getException () [2], url, e.getLineNumber ())

	object = dh.getRoot ()

	if not object:
		tmsg = u_("Error loading %s: empty definition file") % (xmlFileType)
		raise MarkupError, (tmsg, url)

	elif rootType and object._type != rootType:
		tmsg = u_("Error loading %(filetype)s: not a valid %(filetype)s definition "
			"(expected: %(expected)s, got: %(got)s)") \
			% {'filetype': xmlFileType,
			'expected': rootType,
			'got'     : object._type}
		raise MarkupError, (tmsg, url)

	object._rootComments = dh.getRootComments ()

	dh.finalValidation ()

	if initialize:
		assert gDebug (7, "Initializing the object tree starting at %s" % (object))
		object.phaseInit (dh._phaseInitCount)

	# Break the cyclic reference in the content handler, so garbage collection is
	# able to collect it
	dh.parser = None

	return object


# ---------------------------------------------------------------------------
# Remove redundant whitespace characters from a string
# ---------------------------------------------------------------------------

def normalise_whitespace (text):
	"""
	Remove redundant whitespace characters from a string.

	@param text: string to remove redundant whitespaces (space, tabs, ...)
	@returns: normalized string
	"""

	return ' '.join (text.split ())


# =============================================================================
# XML Content handler
# =============================================================================

class xmlHandler (xml.sax.ContentHandler):
	"""
	This class is used by the XML parser to process the XML file.

	@cvar default_namespace: The default namespace (which would be dropped), i.e.
	  if the default namespace is 'Foo', then <Foo:test> would just be processed
	  as <test>.
	@cvar ignore_unknown_namespaces: If set to True, any elements that have an
	  unknown namespace will be dropped.
	"""

	default_namespace         = None
	ignore_unknown_namespaces = False


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	xmlElements = {}
	# This is a hack, currently used only by GRPassThru
	xmlMasqueradeNamespaceElements = None

	# Use namespace as a prefix in GObjects
	xmlNamespaceAttributesAsPrefixes = False

	def __init__ (self):


		# Internal stuff
		self.xmlStack        = []
		self.nameStack       = []
		self.bootstrapflag   = False
		self.uniqueIDs       = {}
		self.root            = None
		self.url             = None
		self.doImportLayoutParser = True
		self.checkRequired   = True

		self._phaseInitCount     = 0
		self._requiredTags       = []
		self._singleInstanceTags = []
		self._tagCounts          = {}
		self._rootComments       = []


	# ---------------------------------------------------------------------------
	# Called by client code to get the "root" node
	# ---------------------------------------------------------------------------

	def getRoot (self):
		"""
		@returns: the root node of the object tree
		"""

		return self.root


	# ---------------------------------------------------------------------------
	# Builds structures need to verify requirements in the file
	# ---------------------------------------------------------------------------

	def initValidation (self):
		"""
		Update some statistics about the elements in use. All 'required' elements
		will be added to the sequence _requiredTags and all elements having
		a True value set for 'SingleInstance' will be added to the sequence
		_singleInstanceTags. Additionally the tag-counter dictionary will
		be reset.
		"""

		for element in self.xmlElements:
			self._tagCounts [element] = 0
			try:
				if self.xmlElements [element]['Required']:
					self._requiredTags.append (element)

			except KeyError:
				pass

			try:
				if self.xmlElements [element]['SingleInstance']:
					self._singleInstanceTags.append (element)

			except KeyError:
				pass


	# ---------------------------------------------------------------------------
	# Final validation
	# ---------------------------------------------------------------------------

	def finalValidation (self):
		"""
		Perform a final validation of the tags. Checks if all required tags are
		really defined (via tag-counter dictionary).
		"""

		# TODO: too simple a validation need to be per object instance
		#for element in self._singleInstanceTags:
		#  if self._tagCounts[element] > 1:
		#    raise MarkupError, \
		#      u_("File has multiple instances of <%s> when only one allowed") \
		#      % (element)

		for element in self._requiredTags:
			if self._tagCounts [element] < 1:
				raise MarkupError, \
					(u_("File is missing required tag <%s>") % element, self.url)


	# ---------------------------------------------------------------------------
	# Start of a XML element
	# ---------------------------------------------------------------------------

	def startElementNS (self, name, qname, attrs):
		"""
		Signals the start of an element in namespace mode.

		The name parameter contains the name of the element type as a (uri,
		localname) tuple, the qname parameter the raw XML 1.0 name used in the
		source document, and the attrs parameter holds an instance of the
		Attributes class containing the attributes of the element.

		The uri part of the name tuple is None for elements which have no
		namespace.
		"""

		ns, tname      = name
		lattrs         = {}
		loadedxmlattrs = {}
		baseAttrs      = {}

		# Updating self.xmlElements with namespace specific parser definitions
		# to let designer handle layout tags.
		if self.default_namespace is None and self.doImportLayoutParser and ns:
			try:
				gnue, tool, toolNS = ns.split (':')
				layoutParser = dyn_import ('gnue.%s.adapters.filters.%s.LayoutParser' \
						% (tool.lower (), toolNS))
				self.xmlElements.update (layoutParser.getXMLelements ())
				self.default_namespace = ns

			except:
				self.doImportLayoutParser = False
				assert gDebug (7, "No parser defined for namespace %s, " \
						"using PassThru objects." % ns)

		if not ns or ns == self.default_namespace:
			#
			# No namespace qualifier
			#
			assert gDebug (7, "<%s>" % tname)

			# Check whether this tag is valid at all
			if not self.xmlElements.has_key (tname):
				raise MarkupError, \
					(u_("Error processing <%(tagname)s> tag [I do not know what a "
						"<%(tagname)s> tag does]") % {'tagname': tname},
					self.url,
					self.parser.getLineNumber ())

			# The definition for this tag
			elementDefinition = self.xmlElements [tname]

			# Check whether this tag is valid for the current parent
			# TEMP HACK for reports 'and not ns',
			# this check is not needed if tags are root in namespace
			if self.nameStack and not ns:
				ok = False
				if self.nameStack [0] in elementDefinition.get ('ParentTags', []):
					ok = True
				elif elementDefinition.get ('UsableBySiblings', False):
					for ancestor in self.nameStack:
						if ancestor in elementDefinition.get ('ParentTags', []):
							ok = True
							break
				if not ok:
					raise MarkupError, \
						(u_("Error processing <%(tagname)s> tag [tag not allowed at "
							"this position]") % {'tagname': tname},
						self.url,
						self.parser.getLineNumber ())

			baseAttrs = elementDefinition.get ('Attributes', {})

			xmlns = {}

			for qattr, qattr_data in attrs.items():
				attrns, attr = qattr

				if attrns:
					if not self.xmlNamespaceAttributesAsPrefixes:
						tmsg = u_("Unexpected namespace on attribute")
						raise MarkupError, (tmsg, self.url, self.parser.getLineNumber ())
					prefix = attrns.split (':') [-1]
					lattrs[prefix + '__' + attr] = qattr_data
					xmlns[prefix] = attrns

					loadedxmlattrs [attr] = qattr_data

				else:
					# Typecasting, anyone?  If attribute should be int, make it an int
					try:
						typecast = baseAttrs[attr].get('Typecast', GTypecast.text)
						lattrs[attr] = attrvalue = typecast(qattr_data)
						loadedxmlattrs[attr] = attrvalue

					except KeyError:
						raise MarkupError, \
							(u_('Error processing <%(tagname)s> tag [I do not '
								'recognize the "%(attribute)s" attribute]') \
								% {'tagname': tname, 'attribute': attr},
							self.url, self.parser.getLineNumber ())


					valueset = baseAttrs[attr].get('ValueSet', {})
					if valueset and not valueset.has_key(attrvalue):
						# FIXME: This should raise an exception. Only issue a warning
						# for now to stay compatible with earlier versions that didn't
						# check this at all.
						assert gDebug(1,
							"DEPRECATION WARNING: %s not a valid value for %s.%s" \
								% (attrvalue, tname, attr))
					#raise InvalidValueSetError (item, object,
					#        data ['ValueSet'].keys ())


					# If this attribute must be unique, check for duplicates
					if baseAttrs[attr].get ('Unique', False):
						if self.uniqueIDs.has_key ('%s' % (qattr_data)):
							tmsg = u_('Error processing <%(tag)s> tag ["%(attribute)s" '
								'attribute should be unique; duplicate value is '
								'"%(duplicate)s"]') \
								% {'tag'      : tname,
								'attribute': attr,
								'duplicate': attrvalue}
							raise MarkupError, (tmsg, self.url, self.parser.getLineNumber ())

			# If we would really want to ensure uniqueness, we'd like to
			# uncomment the following lines. But as this seems to break forms
			# keep it (for now)
			# self.uniqueIDs ["%s" % qattr_data] = True


			for attr, attrdata in baseAttrs.iteritems():
				try:
					if not attr in lattrs:
						# Pull default values for missing attributes
						if baseAttrs[attr].get('Default', None) is not None:
							typecast = attrdata.get ('Typecast', GTypecast.text)
							lattrs[attr] = typecast (attrdata['Default'])

						# Check for missing required attributes
						elif self.checkRequired and attrdata.get('Required', False):
							tm = u_('Error processing <%(tagname)s> tag [required attribute '
								'"%(attribute)s" not present]') \
								% {'tagname': tname, 'attribute': attr}
							raise MarkupError, (tm, self.url, self.parser.getLineNumber ())

				except (AttributeError, KeyError), msg:
					raise errors.SystemError, \
						u_("Error in GParser xmlElement definition for %(tag)s/%(attr)s"
						"\n%(message)s") \
						% {'tag': tname, 'attr': attr, 'message': msg}

			lattrs ['_xmlnamespaces'] = xmlns

			if self.bootstrapflag:
				if self.xmlStack[0] is not None:
					object = elementDefinition ['BaseClass'] (self.xmlStack [0])
			else:
				object = elementDefinition ['BaseClass'] ()
				self.root = object
				self.bootstrapflag = 1

			try:
				self._tagCounts [tname] += 1

			except KeyError:
				pass

			object._xmltag           = tname
			object._xmlnamespace     = ns
			object._listedAttributes = loadedxmlattrs.keys ()

		elif self.xmlMasqueradeNamespaceElements:
			#
			# namespace qualifier and we are masquerading
			#
			assert gDebug (7, "<%s:%s>" % (ns, tname))

			for qattr in attrs.keys ():
				attrns, attr  = qattr
				lattrs [attr] = attrs [qattr]
				loadedxmlattrs [attr] = attrs [qattr]

			try:
				object = self.xmlMasqueradeNamespaceElements (self.xmlStack [0])

			except IndexError:
				tmsg = u_("Error processing <%(namespace)s:%(name)s> tag: root "
					"element needs to be in default namespace") \
					% {'namespace': ns,
					'name'     : tname}
				raise MarkupError, (tmsg, self.url, self.parser.getLineNumber ())

			object._xmltag           = tname
			object._xmlnamespace     = ns
			object._listedAttributes = loadedxmlattrs.keys ()

		elif self.ignore_unknown_namespaces:
			self.xmlStack.insert (0, None)
			self.nameStack.insert (0, None)

			return

		else:
			#
			# namespace qualifier and we are not masquerading
			#
			tmsg = u_("WARNING: Markup includes unsupported namespace '%s'.") % ns
			raise MarkupError, (tmsg, self.url, self.parser.getLineNumber ())


		# Save the attributes loaded from XML file (i.e., attributes that were not
		# defaulted)
		object._loadedxmlattrs = loadedxmlattrs

		# We make the url of the xml-stream and the line number of the element
		# available to the instance (for later error handling)
		object._lineNumber = self.parser.getLineNumber ()
		object._url        = self.url

		# Set the attributes
		object._set_initial_attributes_(lattrs)

		# If it is an import, replace the placeholder with the actual object
		if isinstance(object, GImportItem):
			object = object.get_imported_item()
			self.xmlStack[0].addChild(object)
			object.setParent(self.xmlStack[0])

		if isinstance(object, GRootObj):
			object.__dict__.update(self.root_attributes)

		self.xmlStack.insert (0, object)
		self.nameStack.insert (0, tname)

		# processing trigger/procedure code from external files
		for qattr in attrs.keys ():
			attrns, attr = qattr

			if baseAttrs.has_key ('file') and attr == 'file':
				# FIXME: find a better way to handle encoding of external resources
				textEncoding = gConfig('textEncoding')
				handle = openResource (lattrs [attr])
				text = handle.read ().decode (textEncoding)
				handle.close ()

				if self.xmlStack [0] != None:
					GContent (self.xmlStack [0], text)

		# Let any subclasses know that the object was created
		self._object_created_(object)


	# ---------------------------------------------------------------------------
	# Process text which is not part of a tag (=contents)
	# ---------------------------------------------------------------------------

	def characters (self, content):
		"""
		Called by the internal SAX parser whenever text (not part of a tag) is
		encountered.
		"""

		if self.xmlStack [0] != None:
			# Masqueraging namespace elements, then keep content
			xmlns = self.xmlMasqueradeNamespaceElements and \
				isinstance (self.xmlStack [0], self.xmlMasqueradeNamespaceElements)

			# Should we keep the text?
			if xmlns or self.xmlElements [self.nameStack [0]].get('MixedContent', 0):
				if xmlns or self.xmlElements[self.nameStack[0]].get('KeepWhitespace',0):
					GContent (self.xmlStack [0], content)
				else:
					# Normalize
					if len (content.strip ()):
						content = normalise_whitespace (content)
					else:
						content = ""

					if len (content):
						GContent (self.xmlStack [0], content)


	# ---------------------------------------------------------------------------
	# End of a XML tag encountered
	# ---------------------------------------------------------------------------

	def endElementNS (self, name, qname):
		"""
		Called by the internal SAX parser whenever an ending XML tag/element is
		encountered.
		"""

		ns, tname = name
		self.nameStack.pop (0)
		child = self.xmlStack.pop (0)

		if not child:
			return

		if hasattr(child, '_buildObject'):
			inits = child._buildObject()
			self._phaseInitCount = (inits != None and inits > self._phaseInitCount \
					and inits or self._phaseInitCount)

		assert gDebug (7, "</%s>" % tname)

	# ---------------------------------------------------------------------------
	# Virtual functions
	# ---------------------------------------------------------------------------
	def _object_created_(self, obj):
		pass


	# ---------------------------------------------------------------------------
	# Get the root comments sequence
	# ---------------------------------------------------------------------------

	def getRootComments (self):
		"""
		@returns: sequence of comment tags given before the root node
		"""

		return self._rootComments


	# ---------------------------------------------------------------------------
	# Lexical handler stuff
	# ---------------------------------------------------------------------------

	def comment (self, text):

		if self.root is None:
			self._rootComments.append (text)
		else:
			if self.xmlStack [0] != None:
				GComment (self.xmlStack [0], text)

	# ---------------------------------------------------------------------------

	def startCDATA (self):
		pass

	# ---------------------------------------------------------------------------

	def endCDATA (self):
		pass

	# ---------------------------------------------------------------------------

	def startDTD (self, name, public_id, system_id):
		pass

	# ---------------------------------------------------------------------------

	def endDTD (self):
		pass

	# ---------------------------------------------------------------------------

	def startEntity (self, name):
		pass

	# ---------------------------------------------------------------------------

	def endEntity (self, name):
		pass



# =============================================================================
# Base class for importable items
# =============================================================================

class GImportItem (GObj):
	"""
	This class is used for loading importable items from external resources.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None, type = "GCImport-Item"):

		GObj.__init__ (self, parent, type = type)

		self._loadedxmlattrs = {} # Set by parser
		self._xmlParser      = self.findParentOfType (None)._xmlParser


	# ---------------------------------------------------------------------------
	# Do the actual importing
	# ---------------------------------------------------------------------------

	def get_imported_item(self):

		if hasattr (self, '_xmltag'):
			self._type = 'GC%s' % self._xmltag

		if not hasattr (self, '_importclass'):
			item = self._type [9:].lower ()
			self._importclass = self._xmlParser.getXMLelements () [item]['BaseClass']

		# Open the library and convert it into objects
		handle = openResource (self.library)
		parent = self.findParentOfType (None)

		# Let the parent provide it's instance either as _app or _instance
		if hasattr (parent, '_instance'):
			instance = parent._instance
		elif hasattr (parent, '_app'):
			instance = parent._app
		else:
			instance = None

		form = self._xmlParser.loadFile (handle, instance, initialize = 0)
		handle.close ()

		id = hasattr(self, 'name') and 'name' or 'id'

		# Configure the imported object, assign as a child of self
		rv = self.__findImportItem (self, form, id)
		if rv is not None:
			rv._IMPORTED = True

			# transfer attributes reassigned during the import
			for key in [k for k in self._loadedxmlattrs.keys () if k [0] != '_']:
				rv.__dict__ [key] = self._loadedxmlattrs [key]
				assert gDebug (7, ">>> Moving %s" % key)


			if hasattr(self, 'as'):
				rv.name = getattr(self, 'as')

			return rv

		else:
			raise MarkupError, \
				(u_("Unable to find an importable object named %(name)s in "
					"%(library)s") % {'name'   : self.name, 'library': self.library},
				self._url, self._lineNumber)


	# ---------------------------------------------------------------------------
	# find an item of a given name and type
	# ---------------------------------------------------------------------------

	def __findImportItem (self, find, object, id):

		if isinstance (object, find._importclass) and \
			hasattr (object, id) and \
			object.__dict__.get(id) == find.__dict__ [id]:
			return object

		elif hasattr (object,'_children'):
			rv = None
			for child in object._children:
				rv = self.__findImportItem (find, child, id)
				if rv:
					break

			return rv

		else:
			return None


# =============================================================================
# Generic class for importable objects
# =============================================================================

# This works like this:
# <import trigger="trigger1,trigger2" entry="entry1,entry2">
# which is horrible, doesn't make much sense (give the deep nesting of things
# in forms) and should most probably be removed completely. -- Reinhard

class GImport (GObj):

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, parent = None):

		GObj.__init__ (self, parent, type = "GCImport")
		self.library    = ""
		self._form      = None
		self._inits     = [self.__primaryInit]
		self._xmlParser = self.findParentOfType (None)._xmlParser


	# ---------------------------------------------------------------------------
	# Phase I initialization
	# ---------------------------------------------------------------------------

	def __primaryInit (self):

		handle = openResource (self.library)
		form   = self._xmlParser.loadFile (handle,
			self.findParentOfType (None)._app, initialize = False)
		handle.close ()

		for attribute in self._loadedxmlattrs.keys ():
			if attribute not in ('library', 'as'):
				attr        = self._loadedxmlattrs [attribute]
				importAll   = attr == "*"
				importNames = attr.replace (' ', '').split (',')

				elements     = self._xmlParser.getXMLelements ()
				instanceType = elements [attribute.lower ()]['BaseClass']

				if importAll or len (importNames):
					for child in form._children:
						if isinstance (child, instanceType) and \
							(importAll or child.name in importNames):
							child.setParent (self)
							child._IMPORTED = 1
							self.addChild (child)
							child._buildObject ()


# -----------------------------------------------------------------------------
# build importable tags
# -----------------------------------------------------------------------------

def buildImportableTags (rootTag, elements):
	"""
	Scans XML elements and looks for 'Importable' items. If an object needs to be
	importable, simply add its tag name to the tuple below and make sure it has a
	"name" attribute (otherwise we don't know how to reference it in the imported
	file).
	"""

	importElement = {'BaseClass' : GImport,
		'Attributes' : {
			'library' : {
				'Required' : True,
				'Typecast' : GTypecast.name,
			},
		},
		'ParentTags': (rootTag,),
	}

	importable = set()

	for key in elements.keys ():
		if elements [key].get ('Importable', False):

			importable.add(key)

			name = "import-%s" % key

			copy._deepcopy_dispatch [types.FunctionType] = copy._deepcopy_atomic
			copy._deepcopy_dispatch [types.ClassType] = copy._deepcopy_atomic
			copy._deepcopy_dispatch [type (int)] = copy._deepcopy_atomic

			p = copy.deepcopy (elements [key])
			p ['BaseClass'] = GImportItem

			if not p.has_key ('Attributes'):
				p ['Attributes'] = {}

			p ['Attributes']['library'] = {
				'Required': True,
				'Typecast': GTypecast.name,
			}

			p ['Attributes']['as'] = {
				'Typecast': GTypecast.name,
			}

			p ['MixedContent'] = False
			p ['Required'] = False

			elements [name] = p

			importElement ['Attributes'][key] = {'Typecast': GTypecast.name,
				'Default' : ""}

	if importElement ['Attributes']:
		elements ['import'] = importElement

	# if tag is child of another tag
	# allow it to be a child if corresponding import-tag
	for element in elements.itervalues():
		assert isinstance(element.get('ParentTags'), (type(None), list, tuple)), 'Invalid ParentTags in %s' % element.name
		parents = element['ParentTags'] = list(element.get('ParentTags') or ())
		for i in tuple(parents):
			if i in importable:
				parents.append('import-' + i)

	return elements
