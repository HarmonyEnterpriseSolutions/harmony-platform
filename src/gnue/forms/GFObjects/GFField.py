# GNU Enterprise Forms - GF Object Hierarchy - Field of a block
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
# $Id: GFField.py,v 1.48 2012/09/27 21:59:30 oleg Exp $

"""
Fields of a block, representing database columns.
"""

import re
import types
from gnue.common.apps               import errors
from gnue.common.definitions        import GParser
from gnue.common.utils              import datatypes
from gnue.common.datasources.access import *
from gnue.forms.GFObjects.GFObj     import GFObj


__all__ = ['GFField', 'FKeyMissingError',
	'InvalidDBValueError', 'InvalidFieldValueError',
	'InvalidDefaultValueError']


# =============================================================================
# <field>
# =============================================================================

class GFField(GFObj):
	"""
	A field manages a database column, possibly with foreign key lookup.

	A field has two different values. The DB value, which is the value read
	from/written into the database backend, and the user value, which is the
	value displayed in a form. Those values are different when the field uses
	foreign key lookup.
	"""

	DEFAULT_LENGTH = 15

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):

		GFObj.__init__(self, parent, 'GFField')

		# Defaults for object attributes.
		self.length = None

		# These 3 attributes are used by displayHandler to decide which kinds
		# of keypresses to accept.
		self._uppercase = False
		self._lowercase = False
		self._numeric = False

		# Lookup info for foreign key lookup fields
		self.__is_lookup = False                # True for lookup fields
		self.__lookup_list = []                 # all valid user values
		self.__lookup_dict = {}                 # {db_value: user_value}
		self.__lookup_dict_reverse = {}         # {user_value: db_value}
		self.__fkReset = False                 # set to True at first fk datasorce refresh

		# Autoquery support
		self.__autoquery_value = None
		self.__in_autoquery = False

		# This will be populated by GFEntry's initialize.
		self._entryList = []

		# Valid triggers
		self._validTriggers = {
			'PRE-FOCUSOUT':  'Pre-FocusOut',
			'POST-FOCUSOUT': 'Post-FocusOut',
			'PRE-FOCUSIN':   'Pre-FocusIn',
			'POST-FOCUSIN':  'Post-FocusIn',
			'PRE-COMMIT':    'Pre-Commit',
			'POST-COMMIT':   'Post-Commit',
			'PRE-QUERY':     'Pre-Query',
			'POST-QUERY':    'Post-Query',
			'PRE-INSERT':    'Pre-Insert',
			'PRE-DELETE':    'Pre-Delete',
			'PRE-UPDATE':    'Pre-Update',
			'PRE-CHANGE':    'Pre-Change',
			'POST-CHANGE':   'Post-Change',

			'POST-REFRESH':  'Post-Refresh',         # resultset-activated
			'ON-CUSTOMEDITOR':  'On-CustomEditor',
		}

		# Trigger functions
		self._triggerFunctions = {
			# Possibly all of them should be deprecated sooner or later.

			# This is a ugly hack anyway and should not be necessary any more
			# since now primary keys set by database triggers work nicely.
			'autofillBySequence': {'function': self.triggerAutofillBySequence},

			# This can be achieved by "field.value is None".
			'isEmpty'           : {'function': self.isEmpty},

			# This will become obsolete as soon as the lookup datasource can be
			# a block.
			'resetForeignKey'   : {'function': self.resetForeignKey},

			# This gets and sets the DB value instead of the user value. For
			# consistency, a different field that isn't a lookup should be used
			# for that.
			'get'               : {'function': self.__get_value},
			'set'               : {'function': self.__set_value},
			'get_resolved'      : {'function': self.get_value},
			'set_resolved'      : {'function': self.set_value},
			'setColumnValue'    : {'function': self.setColumnValue},

			# Hmm... I'm not sure what this is useful for...
			'clear'             : {'function': self.resetToDefault},

			# Use "value" property instead.
			'getFKDescription'  : {'function': self.get_value},
			'setFKDescription'  : {'function': self.set_value},

			'getBlock'          : {'function': lambda: self.getBlock().get_namespace_object()},
			'isValueValid'      : {'function': self.isValueValid},
			'addLookupPair'     : {'function': self.__trigger_addLookupPair},

			'fkFirstRecord'     : {'function': self.__trigger_fkFirstRecord},
			'getFkRecordCount'  : {'function': self.__trigger_getFkRecordCount},

			# sort order
			'setSortOrder'      : {'function': self.setSortOrder},
			'applySortOrder'    : {'function': self.applySortOrder},
			'getSortOrder'      : {'function': self.getSortOrder},
		}

		self._triggerProperties = {
			'value': {
				'get': self.get_value,
				'set': self.set_value
			},

			'field': {
				'get': lambda: self.field,
			},
			'name': {
				'get': lambda: self.name,
			},
			
			'editable' : {
				'set' : lambda v: self.setAccess(editableToAccess(v), ACCESS.WRITE),
				'get' : lambda: accessToEditable(self.getAccess()),
			},
		}

		self._triggerGet = self.__get_value
		self._triggerSet = self.__set_value

		# this is access from form definition
		self.__access = None

		# this is access set by user
		# resulting access is self.__access & self.__userAccess & block.getAccess()
		self.__userAccess = ACCESS.FULL

	# -------------------------------------------------------------------------
	# Initialization
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):

		GFObj._phase_1_init_(self)

		self._block = self.findParentOfType ('GFBlock')

		# Convert depreciated "typecast" attribute to new "type" attribute
		if hasattr(self, 'typecast'):
			if self.typecast == 'text':
				self.datatype = 'text'
			elif self.typecast == 'number':
				self.datatype = 'number'
			elif self.typecast == 'date':
				self.datatype = 'datetime'
			elif self.typecast == 'boolean':
				self.datatype = 'boolean'

		# Convert depreciated "maxLength" attribute to new "length" attribute
		if hasattr(self, 'maxLength'):
			self.length = self.maxLength

		if self.datatype == 'number':
			self._numeric = True

		if self.case == 'upper':
			self._uppercase = True
		elif self.case == 'lower':
			self._lowercase = True

		try:
			default = datatypes.convert(self.__get_default(), self.datatype,
				self.length, self.scale)
		except ValueError:
			raise InvalidDefaultValueError(self, self.__get_default())

		if not hasattr(self, 'field') or not len(self.field):
			self.field = "__GNUe__%s" % self.name
			self._block.getDataSource().referenceUnboundField(self.field,
				default)
			self._bound = False
		else:
			self._block.getDataSource().referenceField(self.field, default)
			self._bound = True

		# Initialize the foreign key lookup (if necessary)
		if getattr(self, 'fk_source', None):
			if not getattr (self, 'fk_key', None):
				raise FKeyMissingError (self)

			if not hasattr (self, 'fk_description'):
				self.fk_description = self.fk_key

			self.__fk_descr = self.fk_description.split (',')
			self.__fk_datasource = self._block._form.getDataSource(self.fk_source)

			# Reference the foreign keys to their datasources (so they are
			# selected).
			for field in [self.fk_key] + self.__fk_descr:
				self.__fk_datasource.referenceField(field, None)

			# Register event handling functions
			self.__fk_datasource.registerEventListeners ({
					'dsResultSetActivated': self.__dsResultSetActivated,
					'dsResultSetChanged'  : self.__dsResultSetActivated, # sic!
					'dsCursorMoved'       : self.__dsCursorMoved})

			self.__is_lookup = True

		elif hasattr(self, 'fk_source'):
			# has empty fk_source, this means that field is lookup
			self.__is_lookup = True

		if hasattr(self, 'fk_resolved_description'):
			self.__is_lookup = True

		# Check if "length" attribute is allowed.
		if self.length is not None \
			and (self.datatype not in ['text', 'number', 'raw']):
			raise AttributeNotAllowedError(self, 'length')

		# Check if "minLength" attribute is allowed.
		if self.minLength > 0 \
			and (self.datatype != 'text' or self.__is_lookup):
			raise AttributeNotAllowedError(self, 'minLength')

		if hasattr(self, 'queryDefault') and self.queryDefault != None and \
			self._bound and len(self.queryDefault):
			try:
				self._block._queryDefaults[self] = datatypes.convert(
					self.queryDefault, self.datatype, self.length,
					self.scale)
			except ValueError:
				raise InvalidDefaultValueError(self, self.queryDefault)

		# access defined in gfd
		self.__access = editableToAccess(self.editable)

	# -------------------------------------------------------------------------
	# ACCESS
	# -------------------------------------------------------------------------

	def getAccess(self):
		return self.__access & self.__userAccess & self._block.getAccess()

	def hasAccess(self, access):
		return bool(self.getAccess() & access)

	def setAccess(self, access, mask = None):
		oldAccess = self.getAccess()
		
		if mask is None:
			self.__userAccess = access
		else:
			self.__userAccess = self.__userAccess & ~mask | access & mask

		if oldAccess != self.getAccess():
			self._refresh_ui_editable()
			self._block._GFBlock__update_record_status()

	# -------------------------------------------------------------------------
	# Determine wether a field currently is editable or not
	# -------------------------------------------------------------------------

	def isEditable(self):
		if self._block.mode == 'query':
			return self._block.queryable
		else:
			new = self._block.get_record_status() in ['empty', 'inserted', 'void']
			#if self.editable == 'null' and self.__get_value(offset) is not None:
			#	return False
			return self.hasAccess(ACCESS.INSERT	if new else ACCESS.UPDATE)

	# -------------------------------------------------------------------------
	# Autocomplete a value for this field
	# -------------------------------------------------------------------------

	def autocomplete(self, value, cursor):
		"""
		Return the first valid user value that starts with the provided part.

		The entry can use this function to implement autocompletion.

		@param value: User entered string.
		@type value: unicode
		@param cursor: Position of the current insertion point
		@type cursor: integer
		@returns: tuple of autocompleted string and the new position of the
		    insertion point
		@rtype: tuple of (unicode, integer)
		"""

		if not self.__is_lookup or getattr(self, 'disableAutoCompletion', False):
			return (value, cursor)

		for allowed in self.__lookup_list:
			if allowed.upper().startswith(value.upper()):
				return (allowed, cursor)

		# Nothing found, return original user input.
		return (value, cursor)


	# -------------------------------------------------------------------------
	# lookup
	# -------------------------------------------------------------------------

	def lookup(self, key):
		if self.__is_lookup:
			return self.__lookup_dict[key] if key in self.__lookup_dict else _('(! unresolved: %s)') % key
		else:
			return key

	# -------------------------------------------------------------------------
	# Get DB value for a given user value
	# -------------------------------------------------------------------------

	def reverse_lookup(self, value):
		"""
		Return the DB value for a given user value.

		@param value: A valid lookup value for this field.
		@returns: The corresponding DB value.
		"""
		if not self.__is_lookup:
			return value

		# can't lookup string because dictionary has unicode keys
		if isinstance(value, str):
			value = unicode(value)

		if value is None:
			return None
		elif isinstance(value, datatypes.InvalidValueType):
			return value
		elif self._block.mode == 'query' and value.lower() == u_("(all)"):
			return ''
		elif self._block.mode == 'query' and value.lower() == u_("(empty)"):
			return chr(0)
		elif value in self.__lookup_dict_reverse:
			return self.__lookup_dict_reverse[value]
		else:
			raise InvalidFieldValueError(self.name, value)


	REC_ID_NAME = re.compile("""\[([^\]]+)\]\ (.*)$""")
	def reverseLookupFormattedKeyDescription(self, value):
		"""
		if value like '[id] name' returns id
		else reverse_lookup
		"""
		if self.__is_lookup and value is not None:
			m = self.REC_ID_NAME.match(value)
			if m:
				key, description = m.groups()
				key = eval(key, {}, {})
				if key not in self.__lookup_dict:
					self._addLookupPair(key, description)
				self._refreshLookup()
				return key
			else:
				return self.reverse_lookup(value)
		else:
			return value
		
	def formatKeyDescription(self, key, description):
		if isinstance(key, basestring) and key == description:
			return description
		else:
			return "[%s] %s" % (repr(key), description)

	# -------------------------------------------------------------------------
	# Reading and writing the user value of the field
	# -------------------------------------------------------------------------

	def get_value(self, offset=0):
		"""
		Return the current user value of the field. For lookup fields, this is
		the foreign key description.
		"""

		if not self.__is_lookup:
			return self.__get_value(offset)

		db_value = self.__get_value(offset)

		if self._block.mode == 'query' and db_value == chr(0):
			return u_("(empty)")
		elif self._block.mode == 'query' and db_value is None:
			return u_("(all)")

		if not self.__lookup_dict:
			return None
		elif db_value in self.__lookup_dict:
			return self.__lookup_dict[db_value]
		elif not isinstance(db_value, basestring) \
			and str(db_value) in self.__lookup_dict:
			# This is a workaround to allow lookups of boolean or numeric
			# values in static lookup datasources.
			return self.__lookup_dict[str(db_value)]
		elif db_value is None:
			# This is *after* the other checks so somebody can add "None"
			# explicitly to the lookup source.
			return None
		else:
			# db returned value that is actually not allowed
			return u"(invalid %s)" % db_value

	# -------------------------------------------------------------------------

	def set_value(self, value, enable_change_event=True):
		"""
		Set the current user value of the field. For lookup fields, this is the
		foreign key description.
		"""

		self.__set_value(self.reverse_lookup(value), enable_change_event)

	# -------------------------------------------------------------------------

	def isValueValid(self, offset=0):
		try:
			self.__get_value(offset)
		except InvalidFieldValueError:
			return False
		except Exception, e:
			#rint "! isValueValid: unexpected error: %s: %s" % (e.__class__.__name__, e)
			return False
		else:
			return True

	# -------------------------------------------------------------------------
	# Reading and writing the DB value of a field
	# -------------------------------------------------------------------------

	def __get_value(self, offset=0):
		"""
		Return the current value of the field, depending on the state of the
		form and the block.

		@param offset: offset from the current record (to get values of records
		    other than the current record).
		"""

		value = self._block.get_value(self, offset)

		if isinstance(value, datatypes.InvalidValueType):
			raise value.exception

		# Do not convert if it is a lookup, because the datatype refers to the
		# (lookup) user value, not to the DB value.
		if hasattr(self, '_GFField__fk_resultSet'):
			return value

		# FIXME: This conversion should be in gnue-common.
		try:
			value = datatypes.convert(value, self.datatype, self.length,
				self.scale)
		except ValueError:
			raise InvalidDBValueError(self.name, value)

		if isinstance(value, basestring):
			if self.rtrim:
				value = value.rstrip()
			if self.ltrim:
				value = value.lstrip()

		return value

	# -------------------------------------------------------------------------

	def __set_value(self, value, enable_change_event=True):
		"""
		Set the current value of the field, depending on the state of the form
		and the block.
		"""

		# Don't convert when in query mode, so :operator: magic works.
		# Also, do not convert if it is a lookup, because the datatype refers
		# to the (lookup) user value, not to the DB value.
		#rint "field.__set_value", self.field, value
		if self._block.mode != 'query' \
			and not hasattr(self, '_GFField__fk_resultSet'):
			# FIXME: This conversion should be in gnue-common.
			try:
				value = datatypes.convert(value, self.datatype, self.length,
					self.scale)
			except ValueError:
				raise InvalidFieldValueError(self.name, value)

			if isinstance(value, basestring):
				if self.rtrim:
					value = value.rstrip()
				if self.ltrim:
					value = value.lstrip()

			if self.minLength and isinstance(value, basestring) \
				and len(value) < self.minLength:
				raise MinimumLengthError(self.name, value, self.minLength)

		# If this is an autoquery field, don't pass the value to the block, but
		# save it for later.
		if (self.autoquery == 'Y') \
			or (self.autoquery == 'new' \
				and self._block.get_record_status() == 'empty'):
			if not self.__in_autoquery:
				self.__autoquery_value = value
				return

		self._block.set_value(self, value, enable_change_event)

	def setColumnValue(self, value):
		self._block.setColumnValue(self, value)

	# -------------------------------------------------------------------------
	# Notification of value change
	# -------------------------------------------------------------------------

	def value_changed(self, new_value):
		"""
		Notify the field that the db or query value behind it has changed.

		This function gets called whenever the user interface has to be
		updated.

		@param new_value: the new value for this field.
		"""

		# If the field is a foreign key, move the result set to the
		# selected value.
		if hasattr(self, '_GFField__fk_resultSet'):
			#rint '>>> move rs', new_value
			self.__fk_resultSet.findRecord({self.fk_key: new_value})
		# This will cause __refresh_ui() to be called via
		# __dsCursorMoved
		else:
			self.__refresh_ui()


	# -------------------------------------------------------------------------
	# Get a default value
	# -------------------------------------------------------------------------

	def __get_default (self):

		if hasattr(self, 'default') and self.default is not None \
			and self.default:
			default = self.default
		else:
			default = None

		return default


	# -------------------------------------------------------------------------
	# Focus handling
	# -------------------------------------------------------------------------

	def focus_in(self):
		"""
		Notify the field that it has received the focus.
		"""

		if self._block.mode == 'normal':
			self.processTrigger('PRE-FOCUSIN')
			self.processTrigger('POST-FOCUSIN')

	# -------------------------------------------------------------------------

	def validate(self):
		"""
		Validate the field to decide whether the focus can be moved away from
		it.

		This function can raise an exception, in which case the focus change
		will be prevented.
		"""

		if self._block.mode == 'normal':
			self.processTrigger('PRE-FOCUSOUT', ignoreAbort=False)

			if self.__autoquery_value is not None and not self.__in_autoquery:
				if (self.autoquery == 'Y') \
					or (self.autoquery == 'new' \
						and self._block.get_record_status() == 'empty'):
					self.__in_autoquery = True
					try:
						self._block.set_filter({self.field: self.__autoquery_value})
						if self._block.get_record_status() == 'empty':
							# Query returned no result, so set the field value
							self.__set_value(self.__autoquery_value)
						self.__autoquery_value = None
					finally:
						self.__in_autoquery = False

	# -------------------------------------------------------------------------

	def focus_out(self):
		"""
		Notify the field that it is going to lose the focus.

		The focus change is already decided at this moment, there is no way to
		stop the focus from changing now.
		"""

		if self._block.mode == 'normal':
			self.processTrigger('POST-FOCUSOUT')

	# -------------------------------------------------------------------------
	# Event handling functions for datasource events
	# -------------------------------------------------------------------------

	def __dsResultSetActivated(self, event):

		#load allowed values
		self.clearLookup()

		dpSep = gConfigForms('DropdownSeparator')
		if dpSep.startswith('"') and dpSep.endswith('"') and len(dpSep) > 2:
			dpSep = dpSep[1:-1]

		array = event.resultSet.getArray([self.fk_key] + self.__fk_descr)
		if not array and self.required:
			gDebug(1, "WARNING: empty item added the choices of a required " \
					"field")
			self.__lookup_list.append(u"")

		for line in array:
			key = line[0]
			descr = dpSep.join(["%s" % i for i in line[1:]])

			self._addLookupPair(key, descr, sortLookupList=False)

		self.__lookup_list.sort()

		# And now, position the resultSet to the correct record according to
		# the current field content.
		event.resultSet.findRecord({self.fk_key: self.__get_value()})

		# Remember the resultSet for later
		self.__fk_resultSet = event.resultSet

		# Update the list of choices in all entries bound to this field
		self.__refresh_ui_choices()

		# Update the UI to also for other rows
		self.__refresh_ui()
	
	# -------------------------------------------------------------------------

	def __dsCursorMoved(self, event):
		#rint '>>> __dsCursorMoved', self.field

		# This is called when the cursor of the *foreign key* result set moved.
		# Example: two dropdowns are bound to the same database field, when
		# changing the value of one dropdown, the other dropdown follows
		# through this method.
		# The entry causing the fk record change has already posted a set_value
		# for this field; our current record already contians the correct data.
		# All we have to do is tell our UI to update.
		self.__refresh_ui()


	def isLookup(self):
		return self.__is_lookup


	def clearLookup(self):
		del self.__lookup_list[:]
		if not self.required:
			self.__lookup_list.append(u"")
		self.__lookup_dict.clear()
		self.__lookup_dict_reverse.clear()

	def __trigger_addLookupPair(self, key, descr):
		self._addLookupPair(key, unicode(descr))
		self._refreshLookup()

	def _addLookupPair(self, key, descr, sortLookupList=True):
		self.__lookup_list.append(descr)
		if sortLookupList:
			self.__lookup_list.sort()
		self.__lookup_dict[key] = descr
		self.__lookup_dict_reverse[descr] = key

	def _refreshLookup(self):
		# Update the list of choices in all entries bound to this field
		self.__refresh_ui_choices()
		# Update the UI to also for other rows
		self.__refresh_ui()

	# -------------------------------------------------------------------------
	# Keep the fk resultset in sync
	# -------------------------------------------------------------------------

	def _event_new_current_record (self):
		"""
		The current record of our own ResultSet has changed. So make sure the
		fk ResultSet follows.
		"""

		if hasattr(self, '_GFField__fk_resultSet'):
			self.__fk_resultSet.findRecord({self.fk_key: self.__get_value()})


	# -------------------------------------------------------------------------
	# Refresh the user interface with a changed field value
	# -------------------------------------------------------------------------

	def __refresh_ui(self):

		for entry in self._entryList:
			entry.refresh_ui()

	def _refresh_ui_editable(self):

		for entry in self._entryList:
			entry.refresh_ui_editable()

	# -------------------------------------------------------------------------

	def __refresh_ui_choices(self):

		if self._block.mode == 'query':
			lookup = [u_("(all)"), u_("(empty)")] + self.__lookup_list
			if '' in lookup:
				lookup.remove('')
		else:
			lookup = self.__lookup_list

		for entry in self._entryList:
			entry.refresh_ui_choices(lookup)


	# -------------------------------------------------------------------------
	# Update the list of choices for all bound entries
	# -------------------------------------------------------------------------

	def refresh_choices(self):

		if self.__is_lookup:
			self.__refresh_ui_choices()


	# -------------------------------------------------------------------------
	# Trigger functions
	# -------------------------------------------------------------------------

	def isEmpty(self):

		return self.__get_value() in ("", None)

	# -------------------------------------------------------------------------

	def resetToDefault(self):
		"""
		Reset the current field to the default value.
		"""

		if self.field in self._block._lastValues:
			default = self._block._lastValues[self.field]
		else:
			default = self.__get_default()

		self.__set_value(default)

	# -------------------------------------------------------------------------

	def resetForeignKey(self, once=False):
		"""
		Reload the allowed values of the field. If a ResultSet is provided the
		values will be retrieved from it, otherwise a new ResultSet will be
		created (using the fk_source).
		"""

		# Added so forms triggers could set after init/execute queries
		# which allows filtering of dropdown's in trigger code

		# fk_source can be empty meaning that there is no __fk_datasource
		if self.fk_source and (not once or not self.__fkReset):
			self.__fk_datasource.createResultSet(access=ACCESS.NONE)
			self.__fkReset = True

	def __trigger_fkFirstRecord(self):
		"""
		sets fk to first record
		"""
		assert self.fk_key, 'requires fk_key to be defined'
		try:
			value = self.__fk_resultSet[0][self.fk_key]
		except IndexError:
			pass
		else:
			self.__set_value(value)

	def __trigger_getFkRecordCount(self):
		"""
		fk record count
		"""
		return self.__fk_resultSet.getRecordCount()

	# -------------------------------------------------------------------------

	def triggerAutofillBySequence(self, sequenceName):

		if (not self.__get_value()) or self.__get_value() == "":
			con = self._block.getDataSource()._connection
			self.__set_value(con.getSequence(sequenceName))

	# -------------------------------------------------------------------------

	def getBlock(self):
		return self._block

	# -------------------------------------------------------------------------
	
	def setSortOrder(self, ascending=True):
		"""
		do not applies sort order
		returns if sort order changed
		"""
		if self._bound:
			if self.__is_lookup:
				if getattr(self, 'fk_resolved_description', None):
					field = self.fk_resolved_description
				else:
					field = self.field
					if ascending is not None and not hasattr(self, '_warned_wrong_sort_order_'):
						self._form.show_message(_("Sort order will be wrong because this field is client side resolved.\nPlease, make a request to developers if Your really need this feature"), kind='warning')
						self._warned_wrong_sort_order_ = True
			else:
				field = self.field

			if ascending is None:
				return self.getBlock().getDataSource().removeOrderBy(field)
			else:
				return self.getBlock().getDataSource().addOrderBy(field, not ascending)
		elif ascending is not None:
			raise errors.UserError(_("Can't apply sort order because this field is client side calculated.\nPlease, make a request to developers if Your really need this feature"))

	def applySortOrder(self, ascending=True):
		oldAscending = self.getSortOrder()
		if self.setSortOrder(ascending):
			def onRefresh(result):	
				if result is None:
					self.setSortOrder(oldAscending)
			self.getBlock().refresh(resultConsumer=onRefresh)

	def getSortOrder(self):
		if self._bound:
			if self.__is_lookup and getattr(self, 'fk_resolved_description', None):
				field = self.fk_resolved_description
			else:
				field = self.field
			try:
				return not self.getBlock().getDataSource().getOrderBy(field).get('descending', False)
			except KeyError:
				return None
		else:
			return None

	# -------------------------------------------------------------------------
	# Deprecated functions (temporary until displayHandler is cleaned up)
	# -------------------------------------------------------------------------

	getValue = __get_value
	setValue = __set_value

	def isFiltered(self):
		return findField(self._block.getDataSource().getCondition(), self.field)


def findField(condition, field):
	if isinstance(condition, list):
		if condition[0] == 'field' and condition[1] == field:
			return True
		else:
			for cond in condition[1:]:
				if findField(cond, field):
					return True

# =============================================================================
# Exceptions
# =============================================================================

class FKeyMissingError(GParser.MarkupError):
	def __init__(self, field):
		GParser.MarkupError.__init__(self, u_(
				"Field '%(name)s' has a fk_source specified, but no fk_key"
			) % {
				'name': field.name},
			field._url, field._lineNumber)

# =============================================================================

class AttributeNotAllowedError(GParser.MarkupError):
	def __init__(self, field, name):
		GParser.MarkupError.__init__(self, u_(
				"'%(name)s' attribute not allowed for field '%(field)s'"
			) % {
				'name': name,
				'field': field.name,
			},
			field._url, field._lineNumber)

# =============================================================================

class InvalidDBValueError(errors.ApplicationError):
	"""
	The database has returned an invalid value for a field.

	The most probable reason for this is that the database column in the
	backend does not match the datatype from the field definition.
	"""
	def __init__(self, field, value):
		errors.ApplicationError.__init__(self, u_(
				"Invalid database value '%(value)s' for field '%(field)s'"
			) % {
				'value': value,
				'field': field})

# =============================================================================

class MinimumLengthError(errors.UserError):
	def __init__(self, field, value, min_length):
		errors.UserError.__init__(self, u_(
				"Value '%(value)s' for field '%(field)s' does not reach "
				"minimum length of %(min_length)s"
			) % {
				'field': field,
				'value': value,
				'min_length': min_length})

# =============================================================================

class InvalidFieldValueError(errors.UserError):
	"""
	The user has provided an invalid value for a field.
	"""
	def __init__(self, field, value):
		errors.UserError.__init__(self, u_(
				"Invalid value '%(value)s' for field '%(field)s'"
			) % {
				'value': value,
				'field': field})
		self.value = value

# =============================================================================

class InvalidDefaultValueError(GParser.MarkupError):
	"""
	The field definition contains an invalid default value or default query
	value for a field.
	"""
	def __init__(self, field, value):
		GParser.MarkupError.__init__(self, u_(
				"Invalid default value '%(value)s' for field '%(name)s'"
			) % {
				'value': value,
				'name': field.name}, field._url, field._lineNumber)
