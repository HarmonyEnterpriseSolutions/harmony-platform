# GNU Enterprise Common Library - GNUe XML object definitions - Binary objects
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
# $Id: GBinary.py 9222 2007-01-08 13:02:49Z johannes $

"""
Provides a container object for binary data.
"""

__all__ = ['UnsupportedFormatError', 'GBinary', 'getXMLelements']

import base64

from gnue.common.apps import errors
from gnue.common.definitions.GObjects import GObj


# =============================================================================
# Exceptions
# =============================================================================

class UnsupportedFormatError (errors.ApplicationError):
	def __init__ (self, format):
		msg = u_("Unsupported binary format: '%(format)s'") % {'format': format}
		raise errors.ApplicationError.__init__ (self, msg)


# =============================================================================
# GBinary
# =============================================================================

class GBinary (GObj):
	"""
	Container class for binary data. The only format currently supported is
	'base64'.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, name = "GBinary", parent = None):

		GObj.__init__ (self, name, parent = None)
		self.__data__    = ""
		self.format      = "base64"
		self._phaseInits = [self.init]


	# ---------------------------------------------------------------------------
	# Initialize instance
	# ---------------------------------------------------------------------------

	def init (self):
		"""
		Prepare the __data__ attribute from all the children's contents.

		@raises UnsupportedFormatError: if the format is not supported
		"""

		if self.format == 'base64':
			self.__data__ = base64.decodestring (self.getChildrenAsContent ())
		else:
			raise UnsupportedFormatError, self.format

		self._children = []


	# ---------------------------------------------------------------------------
	# Set the data for the object
	# ---------------------------------------------------------------------------

	def set (self, data):
		"""
		Set the data for the object

		@param data: the data to set
		"""

		self.__data__ = data


	# ---------------------------------------------------------------------------
	# Get the currenlty defined data
	# ---------------------------------------------------------------------------

	def get (self, data):
		"""
		@returns: the data of this object
		"""

		return data


	# ---------------------------------------------------------------------------
	# Dumps an XML representation of the object
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

		xmlEntity = "binary"
		xmlString = "%s<%s" % (gap [:-2],xmlEntity)

		indent = len (xmlString)
		pos    = indent

		for attribute in [a for a in self.__dict__ if a [0] != '_']:
			val = self.__dict__ [attribute]

			if lookupDict [xmlEntity].has_key ('Attributes') and \
				lookupDict [xmlEntity]['Attributes'].has_key (attribute):

				attrDef = lookupDict [xmlEntity]['Attributes'][attribute]

				if val != None and \
					(not 'Default' in attrDef or attrDef ['Default'] != (val)):

					typecast = attrDef ['Typecast']
					if typecast == GTypecast.boolean and val == 1:
						addl = ' %s=""' % (attribute)
					elif typecast == GTypecast.names:
						addl = ' %s="%s"' % (attribute, ','.join (val))
					else:
						addl = ' %s="%s"' % (attribute, saxutils.escape ('%s' % val))

					if len(addl) + pos > 78:
						xmlString += "\n" + " " * indent + addl
						pos = indent
					else:
						xmlString = xmlString + addl
						pos += len (addl)

		xmlString += ">\n"
		if self.format == 'base64':
			xmlString += base64.encodestring (self.__data__)
		else:
			raise UnsupportedFormatError, self.format

		xmlString += "%s</%s>\n" % (gap [:-2], xmlEntity)

		return xmlString


	# ---------------------------------------------------------------------------
	# Virtual methods
	# ---------------------------------------------------------------------------

	def _getAsContents_ (self):
		"""
		@returns: the data of the object
		"""

		return self.__data__


# =============================================================================
# Return any XML elements associated with GBinary
# =============================================================================

def getXMLelements (updates={}):
	"""
	Return any XML elements associated with GBinary
	@returns: dictionary with all elements associated with GBinary
	"""

	xmlElements = {
		'binary': {
			'BaseClass': GBinary,
			'Importable': 1,
			'Attributes': {
				'name': {
					'Unique': 1,
					'Typecast': GTypecast.name },
				'encoding': {
					'Typecast': GTypecast.uppername,
					'ValueSet': {
						#                   'uuencode': {} },  # TODO
						#                   'binhex': {} },    # TODO
						'base64': {} },
					'Default': 'base64' } },
			'MixedContent': 0,
			'KeepWhitespace': 0,
			'UsableBySiblings': 1,
			'ParentTags': None },
	}

	for alteration in updates.keys ():
		xmlElements [alteration].update (updates [alteration])

	return xmlElements
