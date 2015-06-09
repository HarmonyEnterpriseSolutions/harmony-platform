# GNU Enterprise Forms - GF Object Hierarchy - Block
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
# $Id: GFBlock.py,v 1.91 2015/01/27 21:19:18 oleg Exp $

"""
Classes making up the Block object.
"""

import types
from gnue.common.datasources           import GConditions
from gnue.common                       import events
from gnue.forms.GFObjects.GFContainer  import GFContainer
from gnue.forms.GFObjects.GFDataSource import GFDataSource
from gnue.common.datasources.access    import *
from gnue.forms.GFObjects.GFObj        import UnresolvedNameError
from gnue.common.logic.language        import AbortRequest

__all__ = ['GFBlock', 'FieldNotFoundError']


DEBUG = False

# =============================================================================
# Exceptions
# =============================================================================

class FieldNotFoundError(UnresolvedNameError):
	def __init__(self, source, name, referer=None):
		UnresolvedNameError.__init__(self, source, 'Field', name, referer)



class TriggerRecord(object):
	"""
	flyweight trigger object passed to trigger by iterRecords and representing record
	"""
	def __init__(self, block):
		self.__block = block
		self.__record = None

	def _setRecord(self, record):
		self.__record = record

	def copy(self):
		r = self.__class__(self.__block)
		assert self.__record
		r._setRecord(self.__record)
		return r

	def __getitem__(self, fieldName):
		return self.__record[self.__block._fieldMap[fieldName].field]

	def __setitem__(self, fieldName, value):
		self.__record[self.__block._fieldMap[fieldName].field] = value

	def __iter__(self):
		for key in self.__block._fieldMap.keys():
			yield key, self[key]

	def get(self, fieldName, default=None):
		try:
			field = self.__block._fieldMap[fieldName].field
		except KeyError:
			return default
		else:
			return self.__record[field]
		

# =============================================================================
# <block>
# =============================================================================

class GFBlock(GFContainer, events.EventAware):
	"""
	A block in a form definition.

	A block covers all aspects of a form's connection to a data source.

	Blocks can be filled with data by using the L{init_filter},
	L{change_filter}, and L{apply_filter} methods or in a single step with the
	L{set_filter} method.  The L{clear} method populates the block with a
	single empty record.

	Within the result set, blocks maintain a pointer to a current record which
	can be moved around with the L{first_record}, L{prev_record},
	L{next_record}, L{last_record}, L{goto_record}, L{jump_records}, and
	L{search_record} methods.

	Read and write access to the data of the current record (and the
	surrounding records) is possible with the L{get_value} and L{set_value}
	methods. New records can be inserted with the L{new_record} and
	L{duplicate_record} methods. Records can be marked for deletion at next
	commit with the L{delete_record} method and this mark can be undone with
	L{undelete_record}.

	The L{post} and L{requery} methods are available to write the block's
	changes back to the datasource.

	In case the block is connected to an active datasource (especially the GNUe
	AppServer), the L{update} method can be used to write the block's changes
	to the backend without committing them, in order to run trigger functions
	on the backend, while L{call} directly calls a backend function for the
	block's current record.

	The status of the current record can be determined by L{get_record_status},
	while L{is_pending} can be used to determine the status of the whole block.
	The method L{get_possible_operations} lists all operations that are
	possible for the block in its current status.

	The block keeps track of all user interface elements that are connected to
	it and keeps the user interface up to date on all its operations. It should
	always be kept in mind that this might result in bad performance for mass
	operations on the data, so the method L{get_data} is available to access
	the raw data behind the block for high speed operations.

	Whenever the user interface focus enters or leaves the block, it must be
	notified via the L{focus_in}, L{validate}, and L{focus_out} methods.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent):
		"""
		Create a new block instance.

		@param parent: Parent object.
		"""

		GFContainer.__init__(self, parent, 'GFBlock')

		# Current mode of the block. Can be 'normal', 'commit' (during commit
		# triggers), 'init' (during record initialization triggers), or 'query'
		# (if the form is in filter mode).
		self.__mode = 'normal'

		# The underlying resultset.
		self.__rs = None

		# The attached data source.
		self.__ds = None

		# The current record number.
		self._currentRecord = 0         # FIXME: make private!

		# The total number of records.
		self.__record_count = 0

		# The default filter criteria, defined through the fields.
		self._queryDefaults = {}        # FIXME: make private!

		# The current filter criteria.
		self.__query_values = {}

		# The criteria of the last filter that was executed.
		self.__last_query_values = {}

		# Flag set to True while a query is running.
		self.__in_query = False

		# List of all entries bound to this block, populated by GFEntry's
		# initialize
		self._entryList = []            # FIXME: make private!

		# All fields of this block by name.
		# TODO: when all clients 2.7, set _fieldMap to OrderedDict and remove __fieldOrder
		self._fieldMap = {}             # FIXME: make private!
		self.__fieldOrder = []

		# If this is true, notifying attached objects of current record changes
		# is temporarily blocked
		self.__scrolling_blocked = False

		# __autoCommitBlocked needed to disable commit for autoCommit blocks in focus_out routine
		self.__autoCommitBlocked = False

		# this is access from form definition
		self.__access = None

		# this is access set by user
		# resulting access is self.__access & self.__userAccess
		self.__userAccess = ACCESS.FULL

		# this is access from gnue
		# used for detail block to avoid enter details if parent block is set to empty record
		self.__dynamicAccess = ACCESS.FULL

		# if freeze = True, record change is ignored by block and update_record_status too
		self.__freeze = False

		# Trigger exposure
		self._validTriggers = {
			'ON-NEWRECORD':   'On-NewRecord',
			'ON-RECORDLOADED':'On-RecordLoaded',
			'PRE-COMMIT':     'Pre-Commit',
			'POST-COMMIT':    'Post-Commit',
			'PRE-QUERY':      'Pre-Query',
			'POST-QUERY':     'Post-Query',
			'PRE-MODIFY':     'Pre-Modify',
			
			'PRE-INSERT':     'Pre-Insert',
			'PRE-DELETE':     'Pre-Delete',
			'PRE-UPDATE':     'Pre-Update',

			'POST-INSERT':    'Post-Insert',
			'POST-DELETE':    'Post-Delete',
			'POST-UPDATE':    'Post-Update',
			
			'PRE-FOCUSIN':    'Pre-FocusIn',
			'POST-FOCUSIN':   'Post-FocusIn',
			'PRE-FOCUSOUT':   'Pre-FocusOut',
			'POST-FOCUSOUT':  'Post-FocusOut',
			'PRE-CHANGE':     'Pre-Change',
			'POST-CHANGE':    'Post-Change',

			'RECORD-ACTIVATED' : 'Record-Activated',    # user double-clicked on record
			'PRE-REFRESH'      : 'Pre-Refresh',         # block just accepted resultset
			'POST-REFRESH'     : 'Post-Refresh',        # resultset-activated
			'POST-ROWCHANGE'   : 'Post-RowChange',		# = POST-FOCUSIN + POST-REFRESH, means that row may be changed
		}

		self._triggerGlobal = True
		self._triggerFunctions = {
			# Query
			'set_filter': {'function': self.set_filter},
			'add_filter': {'function': self.add_filter},
			'query': {'function': self.set_filter},         # Deprecated!
			'clear': {'function': self.clear},

			# Record navigation
			'first_record': {'function': self.first_record},
			'prev_record': {'function': self.prev_record},
			'next_record': {'function': self.next_record},
			'last_record': {'function': self.last_record},
			'goto_record': {'function': self.goto_record},
			'jump_records': {'function': self.jump_records},
			'search_record': {'function': self.search_record},

			# Record status
			'get_record_status': {'function': self.get_record_status},
			'get_record_count': {'function': self.get_record_count},
			'is_pending': {'function': self.is_pending},
			'get_possible_operations': {'function': self.get_possible_operations},

			# Record insertion and deletion
			'new_record': {'function': self.new_record},
			'duplicate_record': {'function': self.duplicate_record},
			'delete_record': {'function': self.delete_record},
			'undelete_record': {'function': self.undelete_record},

			# Record insertion and deletion (olegs stuff)
			'append_record': {'function': self.append_record},

			# Record activation (olegs stuff)
			'activate_record': {'function': self.activate_record},

			# Other stuff
			'call': {'function': self.call},
			'update': {'function': self.update},
			'get_data': {'function': self.get_data},
			'get_user_data': {'function': self.get_user_data},

			#direct access to underlying data
			'iterRecords'     : {'function': self.iterRecords},
			'getRecordCount'  : {'function': self.getRecordCount},
			'hasRecords'      : {'function': self.hasRecords},
			'getRecords'      : {'function': self.getRecords},
			'iterValues'      : {'function': self.iterValues},
			
			# Deprecated functions
			'isPending': {'function': self.is_pending},
			'isSaved': {'function': self.is_saved},
			'isEmpty': {'function': self.is_empty},
			'firstRecord': {'function': self.first_record},
			'prevRecord': {'function': self.prev_record},
			'nextRecord': {'function': self.next_record},
			'lastRecord': {'function': self.last_record},
			'gotoRecord': {'function': self.goto_record},
			'jumpRecords': {'function': self.jump_records},
			'newRecord': {'function': self.new_record},
			'duplicateRecord': {'function': self.duplicate_record},
			'deleteRecord': {'function': self.delete_record},
			'undeleteRecord': {'function': self.undelete_record},
			'getResultSet': {'function': self.get_resultset},

			# olegs stuff
			'getDataSource' : {'function': self.__trigger_getDataSource},
			'getField'      : {'function': lambda field: self.getField(field).get_namespace_object()},
			'getFields'     : {'function': lambda: map(lambda field: field.get_namespace_object(), self.iterFields())},
			'getMasterBlock': {'function': self.__trigger_get_master_block},
			'iterDetailBlocks': {'function': self.__trigger_iterDetailBlocks},
			'getFieldByDataSourceField' : {'function': self.__trigger_get_field_by_ds_field},
			
			'refresh'       : {'function': self.refresh},
			'save'          : {'function': self.save},
			'discard'       : {'function': self.discard},

			'find_record'   : {'function': self.find_record},
			'unmodify_record' : {'function': self.unmodify_record},

			'setAccess' : {'function': self.setAccess},
			'hasAccess' : {'function': self.hasAccess},
		}

		self._triggerProperties = {
			'editable' : {
				'set' : lambda v: self.setAccess(editableToAccess(v), ACCESS.WRITE),
				'get' : lambda: accessToEditable(self.getAccess()),
			},

			'deletable' : {
				'set' : lambda v: self.setAccess(deletableToAccess(v), ACCESS.DELETE),
				'get' : lambda: accessToDeletable(self.getAccess()),
			},
		}

	def _setMode(self, mode):
		oldMode = self.__mode
		if mode != oldMode:
			self.__mode = mode
			# this is only for gftable, supress init, commit mode switches
			if mode == 'query' or oldMode == 'query':
				self.dispatchEvent('blockModeChanged', source=self, mode=mode, oldMode=oldMode)

	def freeze(self):
		self.__freeze = True
		self.__scrolling_blocked = True
		self.dispatchEvent('freeze', source=self)

	def thaw(self):
		self.__freeze = False
		self.__scrolling_blocked = False
		self.dispatchEvent('thaw', source=self)

		# adjust scrolling
		self.__current_record_changed()
		self.__update_record_status()

	def _getMode(self):
		return self.__mode

	mode = property(_getMode, _setMode)

	def __trigger_getDataSource(self):
		# WORKAROUND BUG: if stub unbound datasource has no namespace_object created for it
		if self.__ds.type != 'unbound':
			return self.__ds.get_namespace_object()

	def getDataSource(self):
		if self.__ds is not None:
			return self.__ds
		else:
			raise ValueError, "Block '%s' has no datasource" % self.name

	############################################################################################
	# refresh = save or discard
	# 
	def save(self, canCancel=True, message = None, resultConsumer=lambda x: x):
		"""
		canCancel is DEPRECATED and ignored
		"""
		# check the master block is saved
		if self.__get_top_master_block().is_pending():
			return self.__save(False, message, resultConsumer)
		else:
			return resultConsumer(True)

	def __save(self, canSkipSave, message, resultConsumer):
		"""
		called only if master block is_pending
		"""
		m = _("Save changes?") if canSkipSave else _("Save changes and continue?")
		if message:
			m = "%s. %s" % (message, m)

		# this called after show_message gets result
		def saveResultConsumer(rc):
			if rc is None:
				return resultConsumer(None)  # cancel refresh
			elif rc:
				self._form.commit()
				# ds.createResultSet not called because commit already did block update
				return resultConsumer(True)
			else:
				return resultConsumer(False if canSkipSave else None)

		rc = self._form.show_message(m, 'Question', cancel = canSkipSave, resultConsumer=saveResultConsumer)

		# DEPRECATED return since using resultConsumer
		return rc if canSkipSave else rc or None 


	def refresh(self, canCancel=True, message = None, resultConsumer=lambda x: x):
		"""
		canCancel is DEPRECATED and ignored
		"""
		if self.__get_top_master_block().is_pending():
			def refreshResultConsumer(result):
				if result is False:
					self.discard()
				return resultConsumer(result)
			return self.__save(True, message, resultConsumer=refreshResultConsumer)
		else:
			self.discard()
			return resultConsumer(True)


	def getPrimaryField(self):
		if self.__ds:
			rowid = getattr(self.__ds, 'rowid', None)
			if rowid:		
				for field in self._fieldMap.itervalues():
					if field.field == rowid:
						return field

	def discard(self):
		"""
		discards master block and all slave blocks data
		"""
		block = self.__get_top_master_block()
		ds = block.getDataSource()

		# remember id
		pf = block.getPrimaryField()
		if pf:
			id = self.get_value(pf)

		# __autoCommitBlocked needed to disable commit for autoCommit blocks in focus_out routine
		self.__autoCommitBlocked = True
		ds.createResultSet(access=block.getAccess())
		self.__autoCommitBlocked = False

		# try to restore id if changed
		if pf and id is not None and id != self.get_value(pf):
			block.search_record(**{str(pf.name) : id})


	############################################################################################

	def iterFields(self):
		assert len(self.__fieldOrder) == len(self._fieldMap)
		return iter(self.__fieldOrder)

	def getField(self, name, referer=None):
		try:
			return self._fieldMap[name]
		except KeyError:
			raise FieldNotFoundError(self, name, referer)

	# -------------------------------------------------------------------------
	# Object construction from xml
	# -------------------------------------------------------------------------

	def _buildObject(self):

		if hasattr(self,'datasource'):
			self.datasource = self.datasource.lower()

		# Build a list and a dictionary of all fields in this block
		for field in self.findChildrenOfType('GFField', includeSelf=False):
			if field.name not in self._fieldMap:
				self.__fieldOrder.append(field)
			self._fieldMap[field.name] = field

		return GFContainer._buildObject(self)


	# -------------------------------------------------------------------------
	# Implementation of virtual methods
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):

		GFContainer._phase_1_init_(self)

		self._convertAsterisksToPercent = gConfigForms('AsteriskWildcard')

		self._logic = self.findParentOfType('GFLogic')

		self._lastValues = {}

		# Initialize our events system
		events.EventAware.__init__(self, events.EventController())

		# Create a stub/non-bound datasource if we aren't bound to one
		if not hasattr(self, 'datasource') or not self.datasource:
			datasource = GFDataSource(self._form)
			datasource.type = 'unbound'
			self.datasource = datasource.name = "__dts_%s" % id(self)
			self._form._datasourceDictionary[datasource.name] = datasource
			datasource._buildObject()
			datasource.phaseInit()

		self.__ds = self._form.getDataSource(self.datasource)

		self.__access = editableToAccess(self.editable) | deletableToAccess(self.deletable)
		if self.__ds.type == 'unbound':
			self.__access = self.__access & ACCESS.WRITE

		# Register event handling functions
		self.__ds.registerEventListeners({
				'dsResultSetActivated': self.__ds_resultset_activated,
				'dsResultSetChanged'  : self.__ds_resultset_activated, # sic!
				'dsCursorMoved'       : self.__ds_cursor_moved,
				'dsRecordInserted'    : self.__ds_record_inserted,
				'dsRecordLoaded'      : self.__ds_record_loaded,
				'dsRecordTouched'     : self.__ds_record_touched,
				'dsCommitInsert'      : self.__ds_commit_insert,
				'dsCommitUpdate'      : self.__ds_commit_update,
				'dsCommitDelete'      : self.__ds_commit_delete,
				'dsPostCommitInsert'  : self.__ds_post_commit_insert,
				'dsPostCommitUpdate'  : self.__ds_post_commit_update,
				'dsPostCommitDelete'  : self.__ds_post_commit_delete,
		})

	# -------------------------------------------------------------------------
	# Get an ordered list of focus-controls
	# -------------------------------------------------------------------------

	def get_focus_order(self):

		ctrlList = []
		for field in self._children:
			ctrlList += getattr(field, '_entryList', [])

		return GFContainer.get_focus_order(self, ctrlList)


	# -------------------------------------------------------------------------
	# Event handling functions for datasource events
	# -------------------------------------------------------------------------

	def __ds_resultset_activated(self, event):
		if DEBUG and self.name == DEBUG: print "GFBlock.__ds_resultset_activated"

		# Don't let the user interface follow while we iterating through the
		# detail resultsets for the commit triggers
		if self.mode == 'commit':
			return

		# FIXME: If an exception appears here, we have a problem: it is probably
		# too late to cancel the operation.
		if not self.__in_query:
			self._focus_out()

		self.__rs = event.resultSet

		self.processTrigger('PRE-REFRESH')

		recno = self.__rs.getRecordNumber()
		if recno == -1:
			self.__scrolling_blocked = True
			try:
				if not self.__rs.firstRecord():
					self.__rs.insertRecord(self._lastValues)
			finally:
				self.__scrolling_blocked = False

		self.__current_record_changed()

		# update fk fields with resolved descriptions
		for field in self.iterFields():
			# if field have no fk datasource, get lookup pairs from fk_resolved_description
			if hasattr(field, 'fk_resolved_description') and not hasattr(field, 'fk_source'):
				field.clearLookup()
				descFieldName = self.getField(field.fk_resolved_description).field
				
				for row in self.__rs:
					key = row[field.field]
					if key is not None:
						field._addLookupPair(key, row[descFieldName] or _('(! unresolved: %s)') % key)

				field._refreshLookup()

			elif field.isLookup() and field.fk_refresh != 'never':
				field.resetForeignKey(once=(field.fk_refresh == 'startup'))

		if not self.__in_query:
			self._focus_in()

		self.processTrigger('POST-REFRESH')
		self.processTrigger('POST-ROWCHANGE')

		for f in self.iterFields():
			f.processTrigger('POST-REFRESH')

	# -------------------------------------------------------------------------

	def __ds_cursor_moved(self, event):
		if DEBUG and self.name == DEBUG: print "GFBlock.__ds_cursor_moved"

		# Don't let the user interface follow while we iterating through the
		# records for the commit triggers
		if self.mode == 'commit':
			return

		if self.__scrolling_blocked:
			return

		self.__current_record_changed()

		#rint ">>> CURSOR MOVED", self.name
		#updating recursive because when grandfather cursor moved, chind have no events to update grandchildren
		self._updateDetailsDynamicAccess(event.record, recursive=True)

	# -------------------------------------------------------------------------

	def __ds_record_inserted(self, event):
		if DEBUG and self.name == DEBUG: print "GFBlock.__ds_record_inserted"
		oldmode = self.mode
		self.mode = 'init'
		self.__initializing_record = event.record
		self.processTrigger('ON-NEWRECORD')
		self.mode = oldmode
		del self.__initializing_record

		#rint ">>> RECORD INSERTED!", self.name
		self._updateDetailsDynamicAccess(event.record)
				
	# -------------------------------------------------------------------------

	def __ds_record_touched(self, event):
		#rint ">>> RECORD TOUCHED!", self.name
		self._updateDetailsDynamicAccess()
		
	# -------------------------------------------------------------------------

	def __ds_record_loaded(self, event):
		oldmode = self.mode
		self.mode = 'init'
		self.__initializing_record = event.record
		self.processTrigger('ON-RECORDLOADED')
		self.mode = oldmode
		del self.__initializing_record

	# -------------------------------------------------------------------------

	def __ds_commit_insert(self, event):
		self.__fire_record_trigger('PRE-INSERT')
		# removed since it is called already from GFForm
		#self.__fire_record_trigger('PRE-COMMIT')

	# -------------------------------------------------------------------------

	def __ds_commit_update(self, event):
		self.__fire_record_trigger('PRE-UPDATE')
		# removed since it is called already from GFForm
		#self.__fire_record_trigger('PRE-COMMIT')

	# -------------------------------------------------------------------------

	def __ds_commit_delete(self, event):
		self.__fire_record_trigger('PRE-DELETE')
		# removed since it is called already from GFForm
		#self.__fire_record_trigger('PRE-COMMIT')

	# -------------------------------------------------------------------------

	def __ds_post_commit_insert(self, event):
		self.processTrigger('POST-INSERT')

	def __ds_post_commit_update(self, event):
		self.processTrigger('POST-UPDATE')

	def __ds_post_commit_delete(self, event):
		self.processTrigger('POST-DELETE')

	# -------------------------------------------------------------------------

	def __fire_record_trigger(self, trigger):
		self.processTrigger(trigger)
		for field in self._fieldMap.itervalues():
			field.processTrigger(trigger)

	# -------------------------------------------------------------------------
	# Queries
	# -------------------------------------------------------------------------

	def populate(self):
		"""
		Populate the block with data at startup.

		Depending on the properties of the block, it is populated either with a
		single empty record or the result of a full query.
		"""
		#rint "populate block", self.name, self.startup

		if self.__get_master_block() is not None:
			# Population will happen through the master
			return

		if self.startup == 'full':
			self.__query()
		elif self.startup == 'empty':
			self.clear()

	# -------------------------------------------------------------------------

	def init_filter(self):
		"""
		Set the block into filter mode.

		From this point on, changes to fields within this block will be
		understood as filter criteria. Use L{apply_filter} to apply the filter
		and populate the block with all records matching the criteria.
		"""

		self.mode = 'query'
		self.__query_values = {}
		self.__query_values.update(self._queryDefaults)
		self.__refresh_choices()
		self.__current_record_changed()
		if self._form.get_focus_block() is self:
			self.__update_record_status()

	# -------------------------------------------------------------------------

	def change_filter(self):
		"""
		Set the block into filter mode and initialize the filter criteria with
		the last executed filter.

		From this point on, changes to fields within this block will be
		understood as filter criteria. Use L{apply_filter} to apply the filter
		and populate the block with all records matching the criteria.
		"""

		self.mode = 'query'
		self.__query_values = {}
		self.__query_values.update(self.__last_query_values)
		self.__refresh_choices()
		self.__current_record_changed()
		if self._form.get_focus_block() is self:
			self.__update_record_status()

	# -------------------------------------------------------------------------

	def discard_filter(self):
		"""
		Reset the block from filter mode back to data browsing mode without
		applying the new filter.

		The result set that was active before switching to filter mode remains
		active.
		"""

		self.mode = 'normal'
		self.__refresh_choices()
		self.__current_record_changed()

	# -------------------------------------------------------------------------

	def apply_filter(self):
		"""
		Apply the filter defined through the field values.

		The block switches back from filter mode to data browsing mode and is
		populated with all records that match the filter criteria.
		"""

		# Store block states
		self.__last_query_values = self.__query_values.copy()

		if self.__get_master_block() is None:
			# Condition for the master block
			conditions = self.__generate_condition_tree()

			self.__in_query = True
			try:
				self.__ds.createResultSet(conditions, access=self.getAccess())
			finally:
				self.__in_query = False

		# Update list of allowed values
		self.__refresh_choices()
		# This seems redundant at first sight, but we must make sure to update
		# the UI after we have changed the available choices, otherwise the UI
		# will get confused. Doing this here makes sure it even is done for
		# detail blocks that were queried before through the master.
		self.__current_record_changed()

	# -------------------------------------------------------------------------

	def set_filter(self, *args, **params):
		"""
		Set new filter criteria for this block.

		@param args: zero, one or more condition trees, can be in dictionary
		    format, in prefix notation, or GCondition object trees. Field names
		    in these conditions are passed directly to the backend, i.e. they
		    are database column names. This is useful to create queries of
		    arbitary complexity.
		@param params: simple filter values in the notation C{fieldname=value}
		    where the fieldname is the name of a GFField. This is useful to
		    create straightforward simple filters where the database columns
		    included in the condition have their GFField assigned. This also
		    works for lookup fields.
		@returns: True if the filter was applied, False if the user aborted
		    when being asked whether or not to save changes.
		"""

		self._focus_out()
		try:
			# We only have to save if the queried block or one of its details has
			# pending changes, not if any other unrelated block is dirty.
			if self.is_pending() and not self._form._must_save():
				return False
			
			# First, convert the fieldname/value pairs to column/value pairs.
			cond = {}
			for (fieldname, value) in params.iteritems():
				field = self._fieldMap[fieldname]
				cond[field.field] = field.reverse_lookup(value)
    
			# Then, mix in the conditions given in args.
			for arg in args:
				cond = GConditions.combineConditions(cond, arg)

			self.__ds.setCondition(cond or None)
			self.__query()
		finally:
			self._focus_in()
		return True

	def add_filter(self, cond):
		self._focus_out()
		try:
			# We only have to save if the queried block or one of its details has
			# pending changes, not if any other unrelated block is dirty.
			if self.is_pending() and not self._form._must_save():
				return False

			if self.__ds.getCondition():
				cond = ['and', self.__ds.getCondition(), cond]

			self.__ds.setCondition(cond or None)

			self.__query()
		finally:
			self._focus_in()
		return True

	# -------------------------------------------------------------------------

	def __query(self):
		# Now, do the query.
		self.__in_query = True
		try:
			mb = self.__get_master_block()
			if mb:
				masterRecord = mb.get_resultset().current
			else:
				masterRecord = None
			self.__ds.createResultSet(access=self.getAccess(), masterRecord=masterRecord)
		finally:
			self.__in_query = False

	# -------------------------------------------------------------------------

	def clear(self):
		"""
		Discard changes in this block and populate it with a single empty
		record.
		"""

		# Detail blocks cannot be cleared - they follow their master blindly.
		if self.__get_master_block() is not None:
			return

		self.__ds.createEmptyResultSet(access = self.getAccess())


	# -------------------------------------------------------------------------
	# Record Navigation
	# -------------------------------------------------------------------------

	def first_record(self):
		"""
		Move the record pointer to the first record of the block.
		"""

		if self.mode == 'query':
			return

		if self.__rs.isFirstRecord():
			return

		self._focus_out()

		self.__rs.firstRecord()

		self._focus_in()

	# -------------------------------------------------------------------------

	def prev_record(self):
		"""
		Move the record pointer to the previous record in the block.

		@returns: True if the record pointer was moved, False if it was already
		    the first record.
		"""

		if self.mode == 'query':
			return False

		if self.__rs.isFirstRecord():
			return False

		self._focus_out()

		self.__rs.prevRecord()

		self._focus_in()

		return True

	# -------------------------------------------------------------------------

	def next_record(self):
		"""
		Move the record pointer to the next record in the block.

		If the record is already the last one, a new record will be created if
		the "autoCreate" attribute of the block is set.

		@returns: True if the record pointer was moved, False if it was already
		    the last record and no new record was inserted.
		"""

		if self.mode == 'query':
			return False

		if self.__rs.isLastRecord():
			if self.autoCreate and self.get_record_status() != 'empty' and self.hasAccess(ACCESS.INSERT):
				self.new_record()
				return True
			return False

		self._focus_out()

		self.__rs.nextRecord()

		self._focus_in()

		return True

	# -------------------------------------------------------------------------

	def last_record(self):
		"""
		Move the record pointer to the last record of the block.
		"""

		if self.mode == 'query':
			return

		if self.__rs.isLastRecord():
			return

		self._focus_out()

		self.__rs.lastRecord()

		self._focus_in()

	# -------------------------------------------------------------------------

	def goto_record(self, record_number):
		"""
		Move the record pointer to a specific record number in the block.

		@param record_number: Record number to jump to. If this is a negative
		    value, move relative to the last record.
		"""

		if self.mode == 'query':
			return

		# If record_number is negative, move relative to last record
		if record_number < 0:
			record_number += self.__rs.getRecordCount()
		if record_number < 0:
			record_number = 0

		if record_number == self.__rs.getRecordNumber():
			return

		self._focus_out()

		if not self.__rs.setRecord(record_number):
			self.__rs.lastRecord()

		self._focus_in()

	# -------------------------------------------------------------------------

	def activate_record(self):
		self.processTrigger('RECORD-ACTIVATED')

	# -------------------------------------------------------------------------

	def jump_records(self, count):
		"""
		Move the record pointer by a given adjustment relative to the current
		record.

		@param count: the number of records to move from the current record.
		"""

		record_number = self.__rs.getRecordNumber() + count

		record_number = max(record_number, 0)
		record_number = min(record_number, self.__rs.getRecordCount())

		self.goto_record(record_number)

	# -------------------------------------------------------------------------

	def search_record(self, **params):
		"""
		Search for (and jump to) the first record matching a set of field
		values.

		@param params: search conditions in the notation C{fieldname=value}
		    where the fieldname is the name of a GFField.
		@returns: True if a record was found, False otherwise.
		"""

		if self.mode == 'query':
			return False

		# First, convert the fieldname/value pairs to column/value pairs.
		cond = {}
		for (fieldname, value) in params.iteritems():
			field = self._fieldMap[fieldname]
			cond[field.field] = field.reverse_lookup(value)

		self._focus_out()

		result = (self.__rs.findRecord(cond, moveIfNotFound=False) is not None)

		self._focus_in()

		return result


	def find_record(self, params, lookup=False):
		"""
		Search for (and jump to) the first record matching a set of field
		values.

		Without lookup.

		@param params: search conditions in the notation C{fieldname=value}
		    where the fieldname is the name of a GFField.
		@param lookup: to perform reverse lookup of values
		@returns: True if a record was found, False otherwise.
		"""

		if self.mode == 'query':
			return False

		# First, convert the fieldname/value pairs to column/value pairs.
		cond = {}
		for (fieldname, value) in params.iteritems():
			field = self._fieldMap[fieldname]
			if lookup:
				cond[field.field] = field.reverse_lookup(value)
			else:
				cond[field.field] = value

		self._focus_out()

		result = (self.__rs.findRecord(cond, moveIfNotFound=False) is not None)

		self._focus_in()

		return result

	# -------------------------------------------------------------------------
	# Status information
	# -------------------------------------------------------------------------

	def get_record_status(self):
		"""
		Find out about the status of the record.

		The status can be one of 'empty', 'inserted', 'void', 'clean',
		'modified', or 'deleted', or C{None} if there is no current record.
		"""

		if self.mode == 'query':
			return None

		if self.__rs is None:
			return None

		record_number = self.__rs.getRecordNumber()
		if record_number < 0 or \
			record_number >= self.__rs.getRecordCount():
			return None
		else:
			rec = self.__rs[record_number]

		# try functions that do not depend on detail records first, because
		# they are faster
		if rec.isVoid():
			return 'void'
		elif rec.isDeleted():
			return 'deleted'
		elif rec.isEmpty():
			return 'empty'
		elif rec.isInserted():
			return 'inserted'
		elif rec.isModified():
			return 'modified'
		else:
			return 'clean'

	# -------------------------------------------------------------------------

	def get_record_count(self):
		"""
		Return the number of records in this block.
		"""

		return self.__rs.getRecordCount()

	# -------------------------------------------------------------------------

	def get_possible_operations(self):
		"""
		Return a list of possible operations for this block.

		The form can use this function to enable or disable commanders (menu
		items or toolbar buttons) that are bound to the respective action.

		The return value is basically a list of method names that can be called
		for this block in the current state.
		"""
		result = []

		if self.mode == 'query':
			result.append('discard_filter')
			result.append('apply_filter')
		else:
			result.append('init_filter')
			result.append('change_filter')

			if self.__ds.type != 'unbound':
				result.append('refresh')
				rs = self.__rs
				if rs is not None:
					rec = rs.current
					status = self.get_record_status()

					if rec is not None:
						if not rs.isFirstRecord():
							result.append('first_record')
							result.append('prev_record')
						if not rs.isLastRecord():
							result.append('next_record')
							result.append('last_record')
						result.append('goto_record')
						if rec.isModified() or rec.isInserted():
							result.append('unmodify_record')

					if self.hasAccess(ACCESS.INSERT) and status != 'empty':
						result.append('new_record')
						result.append('duplicate_record')
						if self.autoCreate and rs.isLastRecord():
							result.append('next_record')

					if self.hasAccess(ACCESS.DELETE):
						if status not in ('void', 'deleted'):
							result.append('delete_record')
						else:
							result.append('undelete_record')

		return result

	# -------------------------------------------------------------------------
	# ACCESS
	# -------------------------------------------------------------------------

	def getAccess(self):
		return self.__access & self.__userAccess & self.__dynamicAccess

	def hasAccess(self, access):
		return bool(self.__access & self.__userAccess & self.__dynamicAccess & access)

	def setAccess(self, access, mask = None):
		oldAccess = self.getAccess()
		
		if mask is None:
			self.__userAccess = access
		else:
			self.__userAccess = self.__userAccess & ~mask | access & mask

		if oldAccess != self.getAccess():
			for field in self.iterFields():
				field._refresh_ui_editable()
			self.__update_record_status()

	def _setDynamicAccess(self, access):
		oldAccess = self.getAccess()
		
		self.__dynamicAccess = access

		if oldAccess != self.getAccess():
			for field in self.iterFields():
				field._refresh_ui_editable()
			# TODO: maybe comment it out
			#self.__update_record_status()

	def _updateDetailsDynamicAccess(self, record = None, recursive=False):
		record = record if record is not None else self.__rs.current
		access = ACCESS.NONE if record.isVoid() or record.isEmpty() else ACCESS.FULL
		#rint "    >>> set access to block details", self.name, access
		for block in self._iterDetailBlocks():
			block._setDynamicAccess(access)
			if recursive:
				block._updateDetailsDynamicAccess()

	# -------------------------------------------------------------------------

	def is_saved(self):
		"""
		Return True if the block is not pending any uncommited changes.

		This method is depreciated. Please use block.is_pending() instead !
		"""

		assert gDebug(1, "DEPRECATED: <block>.isSaved trigger function")
		return not self.is_pending()

	# -------------------------------------------------------------------------

	def is_pending(self):
		"""
		Return True if the block is pending any uncommited changes.
		"""

		return self.__rs is not None and self.__rs.isPending()

	# -------------------------------------------------------------------------

	def is_empty(self):
		"""
		Return True if the current record is empty.

		Empty means that it has been newly inserted, but neither has any field
		been changed nor has a detail for this record been inserted with a
		status other than empty.
		"""

		assert gDebug(1, "DEPRECATED: <block>.isEmpty trigger function")
		return self.get_record_status() in [None, 'empty']

	# -------------------------------------------------------------------------

	def is_first_record(self):
		"""
		Return True if the current record is the first one in the result set.
		"""

		return self.__rs.isFirstRecord()

	# -------------------------------------------------------------------------

	def is_last_record(self):
		"""
		Return True if the current record is the last one in the result set.
		"""

		return self.__rs.isLastRecord()


	# -------------------------------------------------------------------------
	# Field access
	# -------------------------------------------------------------------------

	def get_value(self, field, offset=0):
		"""
		Return the value of the given field, depending on the block's state.

		@param field: the GFField object.
		@param offset: the offset from the current record (to get data for
		    records other than the current one).
		"""

		if offset == 0:
			if self.mode == 'query':
				value = self.__query_values.get(field)

			elif self.mode == 'init':
				value = self.__initializing_record[field.field]

			else:
				if self.__rs and self.__rs.current:
					value = self.__rs.current[field.field]
				else:
					value = None
		else:
			if self.mode in ['query', 'init'] or self.__rs is None:
				value = None
			else:
				record_number = self.__rs.getRecordNumber() + offset
				if record_number < 0 or \
					record_number >= self.__rs.getRecordCount():
					value = None
				else:
					value = self.__rs[record_number][field.field]

		return value

	# -------------------------------------------------------------------------

	def set_value(self, field, value, enable_change_event=True):
		"""
		Set the value of the given field, depending on the block's state.

		@param field: the GFField object.
		"""

		if self.mode == 'query':
			if value is None:
				if field in self.__query_values:
					del self.__query_values[field]
			else:
				self.__query_values[field] = value
			field.value_changed(value)

		elif self.mode == 'init':
			self.__initializing_record[field.field] = value

		else:
			try:
				if enable_change_event:
					self.processTrigger('Pre-Change', ignoreAbort=False)
					field.processTrigger('Pre-Change', ignoreAbort=False)
			except AbortRequest:
				self._form.endEditing()
				try:
					field._GFField__refresh_ui()
				finally:
					self._form.beginEditing()
			else:
				self.__rs.current[field.field] = value
				if field.defaultToLast:
					self._lastValues[field.field] = value
				field.value_changed(value)

				if enable_change_event:
					field.processTrigger('Post-Change')
					self.processTrigger('Post-Change')

				# Status could have changed from clean to modified
				if self._form.get_focus_block() is self:
					self.__update_record_status()


	def setColumnValue(self, field, value):
		assert self.mode != 'query'
		if self.mode != 'init':
			try:
				self.processTrigger('Pre-Change', ignoreAbort=False)
			except AbortRequest:
				self._form.endEditing()
				try:
					field._GFField__refresh_ui()
				finally:
					self._form.beginEditing()
			else:

				self.freeze()

				for record in self.__rs:
					if not record.isVoid():
						record[field.field] = value

				self.thaw()
				
				self.processTrigger('Post-Change')

				# Status could have changed from clean to modified
				if self._form.get_focus_block() is self:
					self.__update_record_status()
			

	# -------------------------------------------------------------------------
	# Insertion and Deletion of Records
	# -------------------------------------------------------------------------

	def new_record(self):
		"""
		Add a new record to the block.
		"""
		if self.hasAccess(ACCESS.INSERT):
			self._focus_out()
			self.__rs.insertRecord(self._lastValues)
			self._focus_in()

	def append_record(self):
		"""
		Append a new record to the block.
		"""
		if self.hasAccess(ACCESS.INSERT):
			self._focus_out()
			self.__rs.appendRecord(self._lastValues)
			self._focus_in()

	# -------------------------------------------------------------------------

	def duplicate_record(self, exclude=(), include=()):
		"""
		Create a new record and initialize it with field values from the
		current record.

		@param exclude: list of fields not to copy.
		@param include: list of fields to copy. An empty list means to copy all
		    fields except primary key fields and rowid fields, which are never
		    copied anyway.
		"""

		if self.hasAccess(ACCESS.INSERT):
			self._focus_out()
			self.__rs.duplicateRecord(exclude=exclude, include=include)
			self._focus_in()

	# -------------------------------------------------------------------------

	def delete_record(self, delete=True, resultConsumer=lambda x: x):
		"""
		Mark the current record for deletion. The acutal deletion will be done
		on the next commit, call or update.
		"""
		self.deleteRecords((self.__rs.getRecordNumber(),), delete, resultConsumer)

	# -------------------------------------------------------------------------

	def undelete_record(self, resultConsumer=lambda x: x):
		"""
		Remove the deletion mark from the current record.
		"""
		self.delete_record(False, resultConsumer)

	# -------------------------------------------------------------------------

	def deleteRecords(self, rows, delete=True, bypassDeletable=False, resultConsumer=lambda x: x):
		"""
		Mark the record listed for deletion. The acutal deletion will be done
		on the next commit, call or update.
		"""
		def deleteRecordsResultConsumer(rc):
			if rc:
				for row in rows:
					self.__rs[row].delete(delete)

				if self._form.get_focus_block() is self:
					self.__update_record_status()

			return resultConsumer(rc)

		if bypassDeletable or self.hasAccess(ACCESS.DELETE):
			if not self.autoCommit or not delete:
				return deleteRecordsResultConsumer(True)
			else:
				if len(rows) == 1 and self.__rs[rows[0]].isEmpty():
					deleteRecordsResultConsumer(True)
				else:
					return self._form.show_message(u_("Are you sure want to delete %s record(s)?") % len(rows), 'Question', resultConsumer=deleteRecordsResultConsumer)
		else:
			return resultConsumer(False)

	def undeleteRecords(self, rows, resultConsumer=lambda x: x):
		"""
		Remove the deletion mark from the records listed
		"""
		return self.deleteRecords(rows, False, resultConsumer)

	# -------------------------------------------------------------------------
	# Saving and Discarding
	# -------------------------------------------------------------------------

	def post(self):
		"""
		Post all pending changes of the block and all its detail blocks to the
		database backend.

		If this function has been run successfully, L{requery} must be called.
		"""

		assert gDebug(4, "processing commit on block %s" % self.name, 1)

		try:
			if self.__get_master_block() is None:
				self.__ds.postAll()
		except:
			# if an exception happened, the record pointer keeps sticking at
			# the offending record, so we must update the UI
			self.__current_record_changed()
			raise

	# -------------------------------------------------------------------------

	def requery(self, commit):
		"""
		Finalize storing the values of the block in the database.

		This method must be called after L{post} has run successfully. It
		restores the block into a consistent state.

		@param commit: True if a commit has been run on the backend connection
		    between post and requery.
		"""

		if self.__get_master_block() is None:
			self.__ds.requeryAll(commit)


	# -------------------------------------------------------------------------
	# Function and Update
	# -------------------------------------------------------------------------

	def call(self, name, parameters):
		"""
		Call a server side function.

		Currently, the only backend to support server side function calls is
		gnue-appserver.

		@param name: Function name.
		@param parameters: Function parameter dictionary.
		"""

		# Remember the current record; the record pointer is not reliable
		# between postAll and requeryAll!
		current = self.__rs.current
		self.__ds.postAll()

		try:
			res = current.call(name, parameters)
		finally:
			self.__ds.requeryAll(False)

		return res

	# -------------------------------------------------------------------------

	def update(self):
		"""
		Update the backend with changes to this block without finally
		commmitting them.

		This can be useful to make the backend react to changes entered by the
		user, for example to make gnue-appserver recalculate calculated fields.
		"""

		self.__ds.postAll()
		self.__ds.requeryAll(False)


	# -------------------------------------------------------------------------
	# Raw data access
	# -------------------------------------------------------------------------

	def get_resultset(self):
		"""
		Return the current ResultSet of the block.
		"""

		gDebug(1, "DEPRECATED: <block>.getResultSet trigger function")
		return self.__rs

	# -------------------------------------------------------------------------

	def get_data(self, fieldnames=None):
		"""
		Build a list of dictionaries of the current resultset using the fields
		defined by fieldnames.

		@param fieldnames: list of fieldnames to export per record
		@returns: list of dictionaries (one per record)
		"""

		result = []
		if self.__rs is not None:

			for recno in xrange(0, self.__rs.getRecordCount()):
				record = self.__rs[recno]
				if not record.isEmpty() and not record.isVoid():
					offset = recno - self.__rs.getRecordNumber()
					add = {}
					for field in self.__getFields(fieldnames):
						add[field.name] = field._GFField__get_value(offset)
					result.append(add)

		return result

	def get_user_data(self, fieldnames=None):
		"""
		Build a list of dictionaries of the current resultset using the fields
		defined by fieldnames.

		@param fieldnames: list of fieldnames to export per record
		@returns: list of dictionaries (one per record)
		"""

		result = []
		if self.__rs is not None:

			for recno in xrange(0, self.__rs.getRecordCount()):
				record = self.__rs[recno]
				if not record.isEmpty() and not record.isVoid():
					offset = recno - self.__rs.getRecordNumber()
					add = {}
					for field in self.__getFields(fieldnames):
						add[field.name] = field.get_value(offset)
					result.append(add)

		return result

	# -------------------------------------------------------------------------
	# Direct access to underlying data
	# TODO: Tree, table, gant must work thrue this
	# TODO: make get_data, get_user_data deprecated
	# -------------------------------------------------------------------------

	def iterRecords(self):
		"""
		returns iterator of dicts
		"""
		r = TriggerRecord(self)
		for record in self.__rs or ():
			if not record.isEmpty() and not record.isVoid():
				r._setRecord(record)
				yield r

	def getRecordCount(self):
		"""
		returns new list of records (not flyweight)
		"""
		c = 0
		for record in self.__rs or ():
			if not record.isEmpty() and not record.isVoid():
				c += 1
		return c

	def hasRecords(self):
		for record in self.__rs or ():
			if not record.isEmpty() and not record.isVoid():
				return True
		else:
			return False
	
	def getRecords(self, filterFn=lambda triggerRecord: True):
		"""
		returns new list of records (not flyweight)
		"""
		return [tr.copy() for tr in self.iterRecords() if filterFn(tr)]

	def iterValues(self, fieldName):
		"""
		returns iterator of values
		"""
		columnName = self._fieldMap[fieldName].field
		for record in self.__rs or ():
			if not record.isEmpty() and not record.isVoid():
				yield record[columnName]

	def __getFields(self, fieldNames):
		if fieldNames is None:
			return self._fieldMap.values()
		else:
			return [self._fieldMap[i] for i in fieldNames]

	# -------------------------------------------------------------------------
	# Shared code called whenever focus enters or leaves a record
	# -------------------------------------------------------------------------

	def _focus_in(self):

		if self._form.get_focus_block() is self:
			self.focus_in()
			field = self._form.get_focus_object().get_field()
			if field is not None:
				field.focus_in()

			self._form.beginEditing()

	# -------------------------------------------------------------------------

	def _focus_out(self):

		if self._form.get_focus_block() is self:

			self._form.endEditing()

			try:
				field = self._form.get_focus_object().get_field()
				if field is not None:
					field.validate()
					self.validate() # @oleg TODO: maybe this must be shited one tab left?
				if field is not None:
					field.focus_out()
				self.focus_out()
			except Exception:
				self._form.beginEditing()
				raise


	# -------------------------------------------------------------------------
	# Focus handling
	# -------------------------------------------------------------------------

	def focus_in(self):
		"""
		Notify the block that it has received the focus.
		"""

		if self.mode == 'normal':
			self.processTrigger('PRE-FOCUSIN')
			self.processTrigger('POST-FOCUSIN')
			self.processTrigger('POST-ROWCHANGE')

		self.__update_record_status()

	# -------------------------------------------------------------------------

	def validate(self):
		"""
		Validate the block to decide whether the focus can be moved away from
		it.

		This function can raise an exception, in which case the focus change
		will be prevented.
		"""

		if self.mode == 'normal':
			self.processTrigger('PRE-FOCUSOUT', ignoreAbort=False)

			# self.__autoCommitBlocked is set to True only when refresh rollbak
			if self.autoCommit and self.is_pending() and not self.__autoCommitBlocked:

				# WORKAROUND BUG: autocommit block steels focus
				focus = self._form._currentBlock, self._form._currentEntry
				self._form._currentBlock = self._form._currentEntry = None

				self._form.execute_commit()

				self._form._currentBlock, self._form._currentEntry = focus

	# -------------------------------------------------------------------------

	def focus_out(self):
		"""
		Notify the block that it is going to lose the focus.

		The focus change is already decided at this moment, there is no way to
		stop the focus from changing now.
		"""

		if self.mode == 'normal':
			self.processTrigger('POST-FOCUSOUT')


	# -------------------------------------------------------------------------
	# Current record has changed
	# -------------------------------------------------------------------------

	def __current_record_changed(self):

		if self.mode == 'query':
			newRecord = 0
		else:
			newRecord = self.__rs.getRecordNumber()

		self._currentRecord = newRecord

		for entry in self._entryList:
			entry.recalculate_visible(self._currentRecord)

		# Things that have to be done if a new current record is activated
		for field in self._fieldMap.itervalues():
			field._event_new_current_record()


	# -------------------------------------------------------------------------
	# Update the list of choices in all fields of the block
	# -------------------------------------------------------------------------

	def __refresh_choices(self):

		for field in self._fieldMap.itervalues():
			field.refresh_choices()

	# -------------------------------------------------------------------------
	# Update the record status
	# -------------------------------------------------------------------------

	def __update_record_status(self):

		# do not update for freezed block
		if self.__freeze:
			return
		
		# resultset is None here
		# when using url_resource with foxit pdf ActiveX @oleg
		if not self.__rs:
			return

		if self.mode == 'query':
			record_number = 1
			record_count = 1
			record_status = 'QRY'
		else:
			record_number = self.__rs.getRecordNumber()+1
			record_count = self.__rs.getRecordCount()
			record_status = {
				None:       '',
				'empty':    'NEW',
				'inserted': 'MOD',
				'void':     'DEL',
				'clean':    'OK',
				'modified': 'MOD',
				'deleted':  'DEL'}[self.get_record_status()]

		self._form.update_record_counter(record_number=record_number,
			record_count=record_count)

		self._form.update_record_status(record_status)
		self._form.status_changed()


	# -------------------------------------------------------------------------
	# Return the top level master block of this block
	# -------------------------------------------------------------------------

	def __get_top_master_block(self):

		result = self
		master = result.__get_master_block()
		while master is not None:
			result = master
			master = result.__get_master_block()
		return result


	# -------------------------------------------------------------------------
	# Return the master block of this block
	# -------------------------------------------------------------------------

	def __get_master_block(self):

		if self.__ds.hasMaster():
			ds = self.__ds.getMaster()
			for block in self._logic._blockList:
				if block.__ds == ds:
					return block
			# return None in case our master is not bound to a block; e.g. if
			# our master is a dropdown
			return None
		else:
			return None

	def __trigger_get_master_block(self):
		block = self.__get_master_block()
		if block is not None:
			return block.get_namespace_object()

	# -------------------------------------------------------------------------
	# Return list of details blocks of this block
	# -------------------------------------------------------------------------

	def _iterDetailBlocks(self, fields=None, recursive=False):
		"""
		"""
		for ds in self.__ds.iterDetailDatasources(fields):
			for block in self._logic._blockList:
				if block.__ds is ds:
					yield block
					if recursive:
						for b in block._iterDetailBlocks(recursive=True):
							yield b

	def __trigger_iterDetailBlocks(self, fields=None, recursive=False):
		for b in self._iterDetailBlocks(fields, recursive):
			yield b.get_namespace_object()
					
	# -------------------------------------------------------------------------
	
	def __trigger_get_field_by_ds_field(self, dsField):
		for field in self.iterFields():
			if field.field == dsField:
				return field.get_namespace_object()

	# -------------------------------------------------------------------------
	# Create a condition tree
	# -------------------------------------------------------------------------

	def __generate_condition_tree(self):
		"""
		Create a condition tree based upon the values currently stored in the
		form.

		@return: GCondition instance with the condition to use or an empty
		    dictionary if no condition is needed.
		"""

		# 'user input': [GCondition, pass value?]
		baseComparisons = {
			'>': ['gt', True],
			'>=': ['ge', True],
			'<': ['lt', True],
			'<=': ['le', True],
			'=': ['eq', True],
			'!=': ['ne', True],
			'like': ['like', True],
			'empty': ['null', False],
			'notempty': ['notnull', False]}
		comparisonDelimiter = ":"

		condLike = {}
		condEq   = {}
		conditions = []
		# Get all the user-supplied parameters from the entry widgets
		for entry, val in self.__query_values.items():
			if entry._bound and len(("%s" % val)):

				# New : operator support
				match = False
				for comparison in baseComparisons.keys():
					if isinstance(val, basestring) and \
						val[:2+len(comparison)].lower() == "%s%s%s" % \
						(comparisonDelimiter, comparison, comparisonDelimiter):
						value = val[2 + len(comparison):]

						if baseComparisons[comparison][1]:
							field = ['field', entry.field]
							const = ['const', value]

							if not entry.query_casesensitive:
								field = ['upper', field]
								const = ['upper', const]

							conditions.append([
									baseComparisons[comparison][0],
									field,
									const])
						else:
							conditions.append([
									baseComparisons[comparison][0],
									['field', entry.field]])
						match = True
						break

				if not match and isinstance(val, bool) and not val:
					conditions.append(['or', \
								['eq', ['field', entry.field], ['const', val]],
							['null', ['field', entry.field]]])
					match = True

				# Falls through to old behaviour if no : condition given or
				# the : condition is unknown
				if not match:
					if isinstance(val, basestring):
						if self._convertAsterisksToPercent:
							try:
								val = ("%s" % val).replace('*', '%')
							except ValueError:
								pass

						val = cond_value(val)
						# a Null-Character means a dropdown with '(empty)'
						# selected.
						if val == chr(0):
							conditions.append(['null', ['field', entry.field]])

						else:
							if (val.find('%') >= 0 or val.find('_') >= 0):
								condLike[entry] = val
							else:
								condEq[entry] = val
					else:
						condEq[entry] = val

		epf = []
		for (entry, value) in condEq.items():
			field = ['field', entry.field]
			const = ['const', value]

			if not entry.query_casesensitive and isinstance(value, basestring):
				field = ['upper', field]
				const = ['upper', const]

			epf.append(['eq', field, const])

		lpf = []
		for (entry, value) in condLike.items():
			field = ['field', entry.field]
			const = ['const', value]

			if not entry.query_casesensitive and isinstance(value, basestring):
				field = ['upper', field]
				const = ['upper', const]

			epf.append(['like', field, const])

		if epf or lpf or conditions:
			result = GConditions.buildConditionFromPrefix(
				['and'] + epf + lpf + conditions)
		else:
			result = {}

		if result and self.__get_master_block() is not None:
			exist = GConditions.GCexist()
			exist.table = self.__ds.table
			exist.masterlink = self.__ds.masterlink
			exist.detaillink = self.__ds.detaillink
			exist._children = [result]
			result = exist

		for detail in self._logic._blockList:
			if detail.__get_master_block() != self:
				continue
			result = GConditions.combineConditions(result,
				detail.__generate_condition_tree())

		return result

	def unmodify_field(self):
		pass

	def unmodify_record(self):
		if self.__rs:
			self.__autoCommitBlocked = True
			self._focus_out()
			self.__rs[self.__rs.getRecordNumber()].unmodify()
			self._focus_in()
			self.__autoCommitBlocked = False

			# TODO: do it thrue ResultSet events
			for entry in self._entryList:
				entry.recalculate_visible(self.__rs.getRecordNumber())

# -----------------------------------------------------------------------------
# Change a condition value as needed
# -----------------------------------------------------------------------------

def cond_value(value):
	"""
	Change a given condition value as needed.  If it is a string and the option
	'fake_ascii_query' is set, all characters above 127 are changed into an
	underscore.
	"""

	if isinstance(value, basestring) and gConfigForms('fake_ascii_query'):
		result = ''
		for char in value:
			if ord(char) > 127:
				char = '_'
			result += char

		value = result

	return value
