# GNU Enterprise Forms - GF Object Hierarchy - Box
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
# $Id: GFTable.py,v 1.68 2013/09/09 14:24:02 oleg Exp $
"""
Logical box support
"""

import re

from GFContainer                    import GFContainer
from GFTabStop                      import GFFieldBound
from XNavigationDelegate            import XNavigationDelegate
from gnue.common.apps               import errors
from gnue.common.datasources.access import ACCESS
from src.gnue.forms.GFObjects import GFStyles


__all__ = ['GFTable']

DEBUG=0
BaseClass = GFContainer

FLAGS  = ["M", "R"]		# system
FLAG_LABEL = {
	'M' : "M",
	'R' : "R",
}
FLAG_TIP = {
	'M' : u_("Modified"),
	'R' : u_("Marked to remove"),
}


# =============================================================================
# <table>
# =============================================================================

class GFTable(BaseClass, XNavigationDelegate):

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	label = None

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		BaseClass.__init__(self, parent, "GFTable")

		# filled on event
		self.__resultSet = None
		self.__recordCount = None
		self.__query = False

		self.__rowStyles = None
		self.__freezed = False

		# triggers
		self._validTriggers = {
			'PRE-FOCUSOUT'     : 'Pre-FocusOut',      # TODO: REMOVE THIS
			'POST-FOCUSOUT'    : 'Post-FocusOut',	  # TODO: REMOVE THIS
			'PRE-FOCUSIN'      : 'Pre-FocusIn',       # TODO: REMOVE THIS
			'POST-FOCUSIN'     : 'Post-FocusIn',      # TODO: REMOVE THIS
			'ON-NEXT-ENTRY'    : 'On-Next-Entry',     # TODO: REMOVE THIS
			'ON-PREVIOUS-ENTRY': 'On-Previous-Entry', # TODO: REMOVE THIS

			'RECORD-ACTIVATED' : 'Record-Activated',
		}

		self._triggerFunctions = {
			'getBlock':          {'function': lambda: self.getBlock().get_namespace_object()},

			# Query
			'find':              {'function': self.find},
			'findText':          {'function': self.findText},
			'filterIncludeCell': {'function': self.filterIncludeCell},
			'filterExcludeCell': {'function': self.filterExcludeCell},
			'cancelFilters':     {'function': self.cancelFilters},

			'getSelectedField':    {'function': self.__trigger_getSelectedField},
			'getSelectedRowsData': {'function': self.getSelectedRowsData},

			'cut':               {'function': self.cut},
			'copy':              {'function': self.copy},
			'paste':             {'function': self.paste},

			'deleteRecords':     {'function': self.deleteRecords},

			'cancelEditing':     {'function': self.cancelEditing},

			'getPossibleOperations' : { 'function': self.__trigger_getPossibleOperations },
		}

		self._triggerProperties = {
			# exposed to set in on-startup trigger (color/not color)
			'fld_style' : {
				'set' : lambda v: setattr(self, 'fld_style', v),
				'get' : lambda: self.fld_style,
			},
		}

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		#rint "----------- GFTable._phase_1_init_ -------------"

		BaseClass._phase_1_init_(self)

		self.__block = self.get_block()

		assert (self.__block is not None), 'Table %s has no block' % self.name

		self.__entries = []

		#rint "GFTable: bound to block", self.__block

		for entry in self._children:
			if isinstance(entry, GFFieldBound):
				self.__entries.append(entry)

		# Register event handling functions
		self.__block.getDataSource().registerEventListeners({
			'dsResultSetActivated': self.__ds_resultset_activated,  # from datasources.GDataSource
			'dsResultSetChanged'  : self.__ds_resultset_activated,  # -/-

			'dsCursorMoved'       : self.__ds_cursor_moved,			# from datasources.drivers.Base.ResultSet

			'dsRecordLoaded'      : self.__ds_record_loaded,		# from datasources.drivers.Base.Record
			'dsRecordInserted'    : self.__ds_record_inserted,		# -/-
			#'dsRecordTouched'     : self.__ds_record_touched,		# -/-
			'dsRecordChanged'     : self.__ds_record_changed,		# -/-

			'dsRecordDeleted'     : self.__ds_record_changed,		# -/-. added
			'dsRecordUndeleted'   : self.__ds_record_changed,		# -/-. added

			'dsCommitInsert'      : self.__ds_commit_insert,		# -/-
			'dsCommitUpdate'      : self.__ds_commit_update,		# -/-
			'dsCommitDelete'      : self.__ds_commit_delete,		# -/-
		})

		self.__block.registerEventListeners({
				'blockModeChanged' : self.__blockModeChanged,
				'freeze'           : self.__freeze,
				'thaw'             : self.__thaw,
			})

		self.__rowStyles = self.findChildOfType('GFStyles') or GFStyles(self)

	def __freeze(self, event):
		self.__freezed = True
		
	def __thaw(self, event):
		self._resultSetActivated()
		self.__freezed = False
	
	def hasLabel(self):
		return self.label is not None

	def getRowStyles(self):
		return self.__rowStyles

	def getRowStyleAt(self, row):
		if not self.__query and getattr(self, 'fld_style', None):
			try:
				key = self.__resultSet[row][self.__block.getField(self.fld_style).field]
			except IndexError:
				# table asks for value before resultset initializes new row
				key = None
		else:
			key = None
		return self.__rowStyles.getStyle(key)

	###################################################################
	# response to events from DataSource
	#

	def __ds_resultset_activated(self, event):
		"""
		- dsResultSetActivated (parameters: resultSet) whenever the current
		  ResultSet of this datasource changes; this happens when a query is
		  executed or when the master of this datasource moves to another record.
		- dsResultSetChanged (parameters: resultSet) whenever the current ResultSet
		  has been reloaded from the backend; this happens after each commit if the
		  "requery" option of this datasource is in use.
		"""
		if self.__freezed:
			return 

		if DEBUG: print 'GFTable.resultset_activated', event.resultSet
		self._resultSetActivated(event.resultSet)

	def _resultSetActivated(self, resultSet=None):
		
		if resultSet:
			self.__resultSet = resultSet

		self.uiWidget._ui_revalidate_()
		self.uiWidget._ui_set_focused_row_(self.__resultSet.getRecordNumber())

		# this is for __ds_cursor_moved
		self.__recordCount = self.__resultSet.getRecordCount()

	def __ds_cursor_moved(self, event):
		"""
		dsCursorMoved (parameters: none) whenever the cursor in the current
		ResultSet is moved, i.e. a different record becomes the current record.
		"""
		if self.__freezed:
			return 

		if self.__resultSet:
			self.uiWidget._ui_set_focused_row_(self.__resultSet.getRecordNumber())

			# AFTER LEAVE OF NEWLY CREATED RECORD
			# revalidate if only record count changed since last time
			if self.__recordCount != self.__resultSet.getRecordCount():
				if DEBUG: print "cursor moved and record count changed, was %s and now %s" % (self.__recordCount,self.__resultSet.getRecordCount())
				self.uiWidget._ui_revalidate_()
				self.__recordCount = self.__resultSet.getRecordCount()
		else:
			if DEBUG: print "GFTable.cursor_moved and NO RESULTSET YET!"


	def __ds_record_loaded(self, event):
		"""
		- dsRecordLoaded whenever a record has been loaded from the backend.
		- dsRecordTouchend whenever a record is modified for the first time since
		  it was loaded from the backend or last saved.
		"""
		if self.__freezed:
			return 
		#if DEBUG: print 'GFTable.record_loaded', event
		pass

	def __ds_record_inserted(self, event):
		if self.__freezed:
			return 
		if DEBUG: print 'GFTable.record_inserted', event
		self.uiWidget._ui_revalidate_()

	def __ds_record_changed(self, event):
		if self.__freezed:
			return 
		if DEBUG: print 'GFTable.record_changed', event
		if self.__resultSet:
			# TODO: why calculated field does record_changed in empty record
			if not event.record.isEmpty():
				self.uiWidget._ui_revalidate_row_(self.__resultSet.getRecordIndex(event.record))

	def __ds_commit_insert(self, event):
		"""
		dsCommitInsert whenever a record is about to be inserted in the backend
		due to a commit operation. The record in question will be the current
		record of the datasource at the time this trigger is run.
		"""
		if self.__freezed:
			return 
		if DEBUG: print 'GFTable.commit_insert', event
		pass

	def __ds_commit_update(self, event):
		"""
		dsCommitUpdate whenever a record is about to be updated in the backend
		due to a commit operation. The record in question will be the current
		record of the datasource at the time this trigger is run.
		"""
		if self.__freezed:
			return 
		if DEBUG: print 'GFTable.commit_update', event
		pass

	def __ds_commit_delete(self, event):
		"""
		dsCommitDelete whenever a record is about to be deleted in the backend
		due to a commit operation. The record in question will be the current
		record of the datasource at the time this trigger is run.
		"""
		if self.__freezed:
			return 
		if DEBUG: print 'GFTable.commit_delete', event
		pass

	###################################################################
	# response to events from Blocks
	#
	def __blockModeChanged(self, event):
		if event.source is self.__block:
			if event.mode in ('query', 'normal'):
				query = (event.mode == 'query')
				if self.__query != query:
					self.__query = query
					self.uiWidget._ui_revalidate_()

	#####################################################
	# response to events from UITable
	#

	def _event_cell_focused(self, row, col):
		#rint 'GFTable: _event_cell_focused', row, col

		# set logical focus to entry
		# this must be before (else have issue with logical focus)
		# (goto_record makes SetFocus to previous entry, grid looses focus)
		self.__entries[col]._event_set_focus()

		# this must be after (else have issue with logical focus)
		self.__block.goto_record(row)



	def _event_row_activated(self):
		"""
		User doubleckiked node, or pressed enter on node
		"""
		self.processTrigger('RECORD-ACTIVATED')
		self.__block.processTrigger('RECORD-ACTIVATED')

	#####################################################
	# Interface to entries
	#
	def getEntries(self):
		return self.__entries

	def getEntryAt(self, i):
		return self.__entries[i]

	#####################################################
	# Interface to fields
	#
	def getFieldAt(self, i):
		return self.__entries[i]._field

	def getFieldCount(self):
		return len(self.__entries)

	def isFieldReadOnlyAt(self, col):
		entry = self.__entries[col]
		return not entry._field.hasAccess(ACCESS.WRITE) and not entry.findChildNamed(None, 'GFEntryButton') or getattr(entry, 'style') == 'label'

	#####################################################
	# Interface to data
	#
	def getValue(self, row, col):
		record = self.__resultSet.getRecord(row)
		if record is None:
			return None
		else:
			return record[self.__entries[col]._field.field]

	def getFormattedValue(self, row, col):
		"""
		used to render
		"""
		if self.__query:
			return self.__entries[col]._field.get_value() or ""
		else:
			value = self.getValue(row, col)
			entry = self.__entries[col]
			if value is None:
				if entry._field.datatype == 'boolean':
					# can't return string instead of boolean
					return False
				else:	
					return ""
			else:
				value = entry._displayHandler.build_display(entry._field.lookup(value), False)
				if entry._field.datatype == 'text':
					# show only first line if multiline text
					value = value.split('\n', 1)[0]
				return value

	def getClipboardValue(self, row, col):
		value = self.getValue(row, col)
		if value is None:
			return ""
		else:
			entry = self.__entries[col]
			text = entry._displayHandler.build_display(entry._field.lookup(value), False)

			# boolean is not formatted by display handler
			if isinstance(text, bool):
				text = repr(text)

			if entry._field.isLookup():
				text = entry._field.formatKeyDescription(value, text)

			assert isinstance(text, basestring), 'getClipboardValue at %s, %s returns wrong value: %s %s' % (row, col, repr(text), type(text))

			text = text.replace(u'\xa0', u' ')		# excel does not understand this

			return text

	def setClipboardValue(self, row, col, text):
		"""
		used when setting from clipboard
		"""
		if self.__query:
			pass
		else:
			text = unicode(text).strip()
			entry = self.getEntryAt(col)

			if entry._field._lowercase:
				text = text.lower()
			elif entry._field._uppercase:
				text = text.upper()

			if entry._field.isEditable():
				self.__resultSet.getRecord(row)[
					self.__entries[col]._field.field
				] = entry._field.reverseLookupFormattedKeyDescription(
					entry._displayHandler.parse_display(text)
				)
			else:
				raise ValueError, "Can't set non-editable cell value"

	def isRecordDeleted(self, row):
		if self.__query:
			return False
		else:
			try:
				rec = self.__resultSet[row]
				return rec.isDeleted() or rec.isVoid()
			# TODO: fix this workaround
			except IndexError:
				return False

	def isRecordModified(self, row):
		if self.__query:
			return False
		else:
			try:
				rec = self.__resultSet[row]
				return (rec.isModified() or rec.isInserted()) and not rec.isVoid()
			# TODO: fix this workaround
			except IndexError:
				return False


	# -------------------------------------------------------------------------
	# flags at the left of data
	#

	def getFlags(self):
		flags  = list(FLAGS)

		if not self.__block.hasAccess(ACCESS.UPDATE) or self.__block.autoCommit:
			flags.remove("M")

		if not self.__block.hasAccess(ACCESS.DELETE):
			flags.remove("R")

		return flags

	def getFlagValue(self, row, flag):
		if flag == 'M':
			return self.isRecordModified(row)
		elif flag == 'R':
			return self.isRecordDeleted(row)
		else:
			assert 0, 'Unknown flag: %s' % flag

	def setFlagValue(self, row, flag, value):
		if flag == 'R':
			self.deleteRecord(row, value)
		elif flag == 'M':
			self.modifyRecord(row, value)
		else:
			assert 0, 'Unknown flag: %s' % flag
		
	def getFlagLabel(self, flag):
		return FLAG_LABEL[flag]

	def getFlagTip(self, flag):
		return FLAG_TIP[flag]

	# -------------------------------------------------------------------------

	def getRecordCount(self):
		if self.__query:
			return 1
		else:
			if self.__resultSet is not None:
				return self.__resultSet.getRecordCount()
			else:
				return 0

	def appendRecord(self):
		self.__block.append_record()

	def modifyRecord(self, row, modify):
		if not modify and self.__resultSet[row].isModified():
			self.__block.focus_out()
			self.__resultSet[row].unmodify()
			# aim is to call Block.__update_record_status
			self.__block.focus_in()

	def deleteRecord(self, row, delete=True):
		"""
		delete specified record
		"""
		self.__block.deleteRecords((row,), delete)

	def deleteRecords(self, delete=True):
		"""
		delete selected records
		"""
		self.__block.deleteRecords(self.uiWidget._ui_get_selected_rows_() or (), delete)

	def isQuery(self):
		return self.__query

	#######################################################################
	# actions
	def find(self):
		self.uiWidget._ui_find_()

	def findText(self, text, wholeCell, searchSelection, reverse, prevPos=None):

		positions = (ReverseCellIterator if reverse else CellIterator)(self, prevPos, prevPos is not None)

		if searchSelection:
			rows = self.uiWidget._ui_get_selected_rows_()
		else:
			rows = None

		if wholeCell:
			match = re.compile(re.escape(text) + u'$', re.LOCALE | re.IGNORECASE).match
		else:
			match = re.compile(
				u'.*'.join(
					map(
						re.escape,
						filter(None, text.split(u' '))
					)
				),
				re.LOCALE | re.IGNORECASE,
			).search

		if searchSelection:
			for p in positions:
				if p[0] in rows and match(unicode(self.getFormattedValue(*p))):
					self._event_cell_focused(*p)
					return p
		else:
			for p in positions:
				if match(unicode(self.getFormattedValue(*p))):
					self._event_cell_focused(*p)
					return p

		return None

	def __filterByCell(self, compOper, noneCompOper):
		try:
			row, col = self.uiWidget._ui_get_selected_cell_()
		except:
			pass
		else:
			if row >= 0 and col >= 0:
				value = self.getValue(row, col)

				field = self.getFieldAt(col)

				if field._bound:
					condField = [ 'field', field.field ]

					if value is None:
						cond = [noneCompOper,	condField]
					else:
						cond = [compOper,		condField,		[ 'const', value ]]

					self.__block.add_filter(cond)
				else:
					self._form.show_message(_("Can't filter by calculated field"), 'Error')

	def filterIncludeCell(self):
		self.__filterByCell('eq', 'null')

	def filterExcludeCell(self):
		self.__filterByCell('ne', 'notnull')

	def cancelFilters(self):
		self.__block.set_filter()

	def __trigger_getSelectedField(self):
		col = self.uiWidget._ui_get_selected_col_()
		if col >= 0:	# None is not >= 0
			return self.getFieldAt(col).get_namespace_object()

	def getSelectedRowsData(self, fieldnames, no_cursor_row=False):
		data = self.getBlock().get_data(fieldnames)
		rows = self.uiWidget._ui_get_selected_rows_(no_cursor_row=no_cursor_row)
		for row in rows:
			if self.isRecordDeleted(row):
				raise errors.UserError, u_("You can't select rows marked for deletion")

		return [data[i] for i in rows if i < len(data)]

	def cancelEditing(self):
		self.uiWidget._ui_cancel_editing_()

	def getBlock(self):
		return self.__block

	##########################################################################

	def cut(self):
		self.__block._focus_out()
		try:
			self.uiWidget._ui_cut_()
		finally:
			self.__block._focus_in()

	def copy(self):
		self.uiWidget._ui_copy_()

	def paste(self):
		self.__block._focus_out()
		self.__block.freeze()
		try:
			#import cProfile
			#cProfile.runctx("self.uiWidget._ui_paste_()", globals(), locals(), 'paste.stats')
			self.uiWidget._ui_paste_()
		finally:
			self.__block.thaw()
			self.__block._focus_in()

	##########################################################################

	def ui_set_focused_entry(self, entry):
		"""
		ui_set_focus is blocked for entries in GFTable
		ui_set_focused_entry used instead
		"""
		self.uiWidget._ui_set_focused_cell_(self.__resultSet.getRecordNumber(), self.__entries.index(entry))

	##########################################################################

	def ui_focus_out(self):
		# called from child GFTabStop
		self.uiWidget._ui_focus_out_()

	def __trigger_getPossibleOperations(self):
		operations = set()

		if self.__block.hasAccess(ACCESS.DELETE):
			operations.add('deleteRecords')
			operations.add('undeleteRecords')
		                       
		operations.add('find')

		operations.add('filterIncludeCell')
		operations.add('filterExcludeCell')
		operations.add('cancelFilters')
		                       
		operations.add('orderAscending')
		operations.add('orderDescending')
		operations.add('orderNone')
		operations.add('disableOrders')
		                       
		operations.add('cut')
		operations.add('copy')
		operations.add('paste')

		return operations


class CellIterator(object):

	def __init__(self, gfTable, pos=None, skipFirst=False):
		self.gfTable = gfTable
		self.row, self.col = pos or self._firstCell()
		if not skipFirst:
			self._noskip()

	def __iter__(self):
		return self

	def _noskip(self):
		self.col -= 1

	def _firstCell(self):
		return (0,0)

	def next(self):
		self.col += 1
		if self.col >= self.gfTable.getFieldCount():
			self.col = 0
			self.row += 1
		if self.row >= self.gfTable.getRecordCount():
			raise StopIteration
		return self.row, self.col


class ReverseCellIterator(CellIterator):

	def _noskip(self):
		self.col += 1

	def _firstCell(self):
		return (self.gfTable.getRecordCount()-1,self.gfTable.getFieldCount()-1)

	def next(self):
		self.col -= 1
		if self.col < 0:
			self.col = self.gfTable.getFieldCount()-1
			self.row -= 1
		if self.row < 0:
			raise StopIteration
		return self.row, self.col
