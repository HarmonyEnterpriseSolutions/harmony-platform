# GNU Enterprise Common Library - XML elements for schema support
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
# $Id: GSchema.py 9394 2007-02-21 19:35:10Z johannes $
"""
Classes for the schema object tree.
"""

from gnue.common.definitions import GObjects, GParser, GParserHelpers, GRootObj
from gnue.common.formatting import GTypecast


xmlElements = None

# =============================================================================
# The base class for GNUe Schema Definitions
# =============================================================================

class GSObject (GObjects.GObj):
	"""
	Abstract base class for all objects of a schema tree.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, objType, **kwargs):

		GObjects.GObj.__init__ (self, parent, objType)
		self.buildObject (**kwargs)


# =============================================================================
# <schema>
# =============================================================================

class GSSchema (GRootObj.GRootObj, GSObject):
	"""
	Database schema, the root of any schema tree.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, parent = None):

		GRootObj.GRootObj.__init__(self, 'schema', getXMLelements, __name__)
		GSObject.__init__(self, parent, 'GSSchema')


# =============================================================================
# <tables>
# =============================================================================

class GSTables (GSObject):
	"""
	Collection of table definitions.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, parent, **params):

		GSObject.__init__(self, parent, 'GSTables', **params)


	# ---------------------------------------------------------------------------
	# Make sure that different types of table-collections aren't mixed up
	# ---------------------------------------------------------------------------

	def _id_ (self, maxIdLength = None):

		return "%s" % self.type


# =============================================================================
# <table>
# =============================================================================

class GSTable (GSObject):
	"""
	Definition of a single database table.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, parent, **params):

		GSObject.__init__(self, parent, 'GSTable', **params)


	# ---------------------------------------------------------------------------
	# Return a list of all fields
	# ---------------------------------------------------------------------------

	def fields (self, action = None):
		"""
		Returns a list of all fields of this table.

		@param action: if given, only returns the fields where the property
		  "action" is set to the value of this parameter.
		@return: iterater over the requested fields.
		"""

		for field in self.findChildrenOfType ('GSField', False, True):
			if action is not None and field._action != action:
				continue
			else:
				yield field


# =============================================================================
# <fields>
# =============================================================================

class GSFields (GSObject):
	"""
	Collection of fields of a table.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, parent, **params):

		GSObject.__init__(self, parent, 'GSFields', **params)

# =============================================================================
# <field>
# =============================================================================

class GSField (GSObject, GParserHelpers.GLeafNode):
	"""
	Definition of a single database field.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, parent, **params):

		GSObject.__init__(self, parent, 'GSField', **params)


# =============================================================================
# <primarykey>
# =============================================================================

class GSPrimaryKey (GObjects.GUndividedCollection):
	"""
	Definition of a primary key of a database table.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GObjects.GUndividedCollection.__init__ (self, parent, 'GSPrimaryKey',
			**params)


# =============================================================================
# <pkfield>
# =============================================================================

class GSPKField (GSObject, GParserHelpers.GLeafNode):
	"""
	Definition of a primary key field.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__(self, parent, 'GSPKField', **params)


# =============================================================================
# <constraints>
# =============================================================================

class GSConstraints (GObjects.GUndividedCollection):
	"""
	Collection of constraint definitions.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GObjects.GUndividedCollection.__init__ (self, parent, 'GSConstraints',
			**params)


# =============================================================================
# <foreignkey>
# =============================================================================

class GSForeignKey (GSObject):
	"""
	Definition of a foreign key constraint.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__ (self, parent, 'GSForeignKey', **params)


# =============================================================================
# <fkfield>
# =============================================================================

class GSFKField (GSObject, GParserHelpers.GLeafNode):
	"""
	Definition of a foreign key field.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__(self, parent, 'GSFKField', **params)


# =============================================================================
# <unique>
# =============================================================================

class GSUnique (GSObject):
	"""
	Definition of an unique constraint.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__ (self, parent, 'GSUnique', **params)


# =============================================================================
# <uqfield>
# =============================================================================

class GSUQField (GSObject, GParserHelpers.GLeafNode):
	"""
	Definition of an unique constraint field.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__(self, parent, 'GSUQField', **params)


# =============================================================================
# <indexes>
# =============================================================================

class GSIndexes (GObjects.GUndividedCollection):
	"""
	Collection of index definitions.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GObjects.GUndividedCollection.__init__ (self, parent, 'GSIndexes',
			**params)


# =============================================================================
# <index>
# =============================================================================

class GSIndex (GSObject):
	"""
	Definition of an index on a database table.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):
		GSObject.__init__(self, parent, 'GSIndex', **params)


# =============================================================================
# <indexfield>
# =============================================================================

class GSIndexField (GSObject, GParserHelpers.GLeafNode):
	"""
	Definition of an index field.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):
		GSObject.__init__(self, parent, 'GSIndexField', **params)


# =============================================================================
# <data>
# =============================================================================

class GSData (GSObject):
	"""
	Collection of tabledata to be included in a schema definition (e.g. for
	initial loading of a table).
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__ (self, parent, 'GSData', **params)


# =============================================================================
# <tabledata>
# =============================================================================

class GSTableData (GSObject):
	"""
	Data for one table.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__ (self, parent, 'GSTableData', **params)


# =============================================================================
# <rows>
# =============================================================================

class GSRows (GSObject):
	"""
	Collection of data rows.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__ (self, parent, 'GSRows', **params)

	# ---------------------------------------------------------------------------
	# Merge a rows collection with another one
	# ---------------------------------------------------------------------------

	def merge (self, other, maxIdLength = None, overwrite=False):
		"""
		Merge all rows of another rows collection into this one. Since we cannot
		determine a primary key here we have no chance to detect duplicate rows.
		That's why we just copy all of the others' rows.
		"""

		for row in other.findChildrenOfType ('GSRow', False, True):
			new = GSRow (self)
			new.assign (row, True)


# =============================================================================
# <row>
# =============================================================================

class GSRow (GSObject):
	"""
	Definition of a single data row.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__ (self, parent, 'GSRow', **params)


# =============================================================================
# <value>
# =============================================================================

class GSValue (GSObject, GParserHelpers.GLeafNode):
	"""
	Definition for a value in a row.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):
		GSObject.__init__ (self, parent, 'GSValue', **params)


# =============================================================================
# <description>
# =============================================================================

class GSDescription (GSObject, GParserHelpers.GLeafNode):
	"""
	Clear text description of the schema.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, **params):

		GSObject.__init__ (self, parent, 'GSDescription', **params)


# =============================================================================
# load an XML object tree from a given stream and return it's root object
# =============================================================================

def loadFile (buffer, app = None, initialize = True):
	"""
	This function loads an XML object tree from a given stream and return it's
	root object.
	"""

	return GParser.loadXMLObject (buffer, xmlSchemaHandler, 'GSSchema', 'schema',
		initialize, attributes = {'_app': app})


# =============================================================================
# Build a dictionary tree with all available XML elements
# =============================================================================

def getXMLelements ():
	"""
	Create a dictionary tree with all valid xml elements. This dictionary tree is
	available via global variable 'xmlElements'
	"""

	global xmlElements

	if xmlElements is None:
		xmlElements = {
			'schema': {
				'BaseClass'       : GSSchema,
				'Required'        : True,
				'SingleInstance'  : True,
				'Attributes'      : {'title'      : {'Typecast': GTypecast.text},
					'author'     : {'Typecast': GTypecast.text},
					'version'    : {'Typecast': GTypecast.text},
					'description': {'Typecast': GTypecast.text}},
				'ParentTags'      : None },
			'tables': {
				'BaseClass'       : GSTables,
				'SingleInstance'  : False,
				'Attributes'      : {'type': {'Typecast': GTypecast.name,
						'Default' : 'table'},
					'name': {'Typecast': GTypecast.name,
						'Default' : 'tables'}},
				'ParentTags'      : ('schema',)},
			'table': {
				'BaseClass'       : GSTable,
				'Importable'      : True,
				'Attributes'      : {'name'       : {'Required': True,
						'Unique'  : True,
						'Typecast': GTypecast.name},
					'description': {'Typecast': GTypecast.text},
					'type'       : {'Typecast': GTypecast.name},
					'action'     : {'Typecast': GTypecast.text,
						'ValueSet': {'create': {},
							'extend': {}},
						'Default' : 'create'}},
				'ParentTags'      : ('tables',)},
			'fields': {
				'BaseClass'       : GSFields,
				'Importable'      : True,
				'SingleInstance'  : True,
				'ParentTags'      : ('table',)},
			'field': {
				'BaseClass'       : GSField,
				'Importable'      : True,
				'Attributes'      : {'name'       : {'Required': True,
						'Unique'  : True,
						'Typecast': GTypecast.name},
					'description': {'Typecast': GTypecast.text},
					'type'       : {'Required': True,
						'Typecast': GTypecast.name},
					'length'     : {'Typecast': GTypecast.whole},
					'precision'  : {'Typecast': GTypecast.whole,
						'Default' : 0},
					'nullable'   : {'Typecast': GTypecast.boolean,
						'Default' : True},
					'default'    : {'Typecast': GTypecast.text},
					'defaultwith': {'Typecast': GTypecast.text,
						'ValueSet': {'constant' : {},
							'timestamp': {},
							'serial'   : {}},
						'Default': 'constant'}},
				'ParentTags'      : ('fields',)},
			'primarykey': {
				'BaseClass'       : GSPrimaryKey,
				'SingleInstance'  : True,
				'Attributes'      : {'name': {'Required': True,
						'Typecast': GTypecast.name}},
				'ParentTags'      : ('table', 'tabledata')},
			'pkfield': {
				'BaseClass'       : GSPKField,
				'Attributes'      : {'name': {'Required': True,
						'Typecast': GTypecast.name}},
				'ParentTags'      : ('primarykey',)},
			'constraints': {
				'BaseClass'       : GSConstraints,
				'SingleInstance'  : True,
				'ParentTags'      : ('table',)},
			'foreignkey': {
				'BaseClass'       : GSForeignKey,
				'Attributes'      : {'name'      : {'Required': True,
						'Typecast': GTypecast.name},
					'references': {'Typecast': GTypecast.name}},
				'ParentTags'      : ('constraints',)},
			'fkfield': {
				'BaseClass'       : GSFKField,
				'Attributes'      : {'name'      : {'Required': True,
						'Typecast': GTypecast.name},
					'references': {'Required': True,
						'Typecast': GTypecast.name}},
				'ParentTags'      : ('foreignkey',)},
			'unique': {
				'BaseClass'       : GSUnique,
				'Attributes'      : {'name': {'Required': True,
						'Typecast': GTypecast.name}},
				'ParentTags'      : ('constraints',)},
			'uqfield': {
				'BaseClass'       : GSUQField,
				'Attributes'      : {'name': {'Required': True,
						'Typecast': GTypecast.name}},
				'ParentTags'      : ('unique',)},
			'indexes': {
				'BaseClass'       : GSIndexes,
				'SingleInstance'  : True,
				'ParentTags'      : ('table',)},
			'index': {
				'BaseClass'       : GSIndex,
				'Attributes'      : {'name'  : {'Required': True,
						'Typecast': GTypecast.name},
					'unique': {'Typecast': GTypecast.boolean,
						'Default' : False}},
				'ParentTags'      : ('indexes',)},

			'indexfield': {
				'BaseClass'       : GSIndexField,
				'Attributes'      : {'name': {'Required': True,
						'Typecast': GTypecast.name}},
				'ParentTags'      : ('index',)},
			'data': {
				'BaseClass'       : GSData,
				'SingleInstance'  : True,
				'ParentTags'      : ('schema',)},
			'tabledata': {
				'BaseClass'       : GSTableData,
				'Importable'      : True,
				'Attributes'      : {'name'     : {'Required': True,
						'Typecast': GTypecast.name},
					'tablename': {'Required': True,
						'Typecast': GTypecast.name}},
				'ParentTags'      : ('data',)},
			'rows': {
				'BaseClass'       : GSRows,
				'SingleInstance'  : True,
				'ParentTags'      : ('tabledata',)},
			'row': {
				'BaseClass'       : GSRow,
				'ParentTags'      : ('rows',)},
			'value': {
				'BaseClass'       : GSValue,
				'Attributes'      : {'field': {'Required': False,
						'Typecast': GTypecast.name},
					'type' : {'Required': False,
						'Typecast': GTypecast.name,
						'Default' : 'text' }},
				'ParentTags'      : ('row',),
				'MixedContent'    : True,
				'KeepWhitespace'  : True},
			'description': {
				'BaseClass'       : GSDescription,
				'SingleInstance'  : True,
				'MixedContent'    : True,
				'UsableBySiblings': True,
				'ParentTags'      : ('schema',)}}

	return GParser.buildImportableTags ('schema', xmlElements)


# =============================================================================
# Class called by the XML parser to process the XML file
# =============================================================================

class xmlSchemaHandler (GParser.xmlHandler):

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self):

		GParser.xmlHandler.__init__(self)
		self.xmlElements = getXMLelements ()
