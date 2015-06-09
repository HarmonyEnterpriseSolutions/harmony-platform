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
# Copyright 2000-2006 Free Software Foundation
#
#
# FILE:
# GFTreeList.py
#
# DESCRIPTION:
"""
"""

#import sys
#from toolib.dbg.CatchOutput import CatchOutput
#sys.stdout = CatchOutput(sys.stdout, "wx.lib.agw.hypertreelist.TreeListItem")

from src.gnue.forms.GFObjects.GFTabStop import GFFieldBound
from gnue.common.datasources.access  import ACCESS
from src.gnue.forms.GFObjects import GFTreeMixInNodeNamePattern, XNavigationDelegate, GFContainer

DEBUG = 0

#
# GFTreeList
#
class GFTreeList(GFTreeMixInNodeNamePattern, GFContainer, XNavigationDelegate):

	label = ""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		GFContainer.__init__(self, parent, self.__class__.__name__)
		GFTreeMixInNodeNamePattern.__init__(self)

		self._triggerFunctions.update({
			'newNode'          : { 'function': self.newNode    },

			'cutNode'          : { 'function': self.cutNode    },
			'copyNode'         : { 'function': self.copyNode   },
			'pasteNode'        : { 'function': self.pasteNode  },

			'deleteNode'       : { 'function': self.deleteNode },

			'getNewNodeParentId'    : { 'function': self.__trigger_getNewNodeParentId },
			'getPossibleOperations' : { 'function': self.__trigger_getPossibleOperations },

			'getCuttedNodeId'  : { 'function': self.getCuttedNodeId },
			'getCopiedNodeId'  : { 'function': self.getCopiedNodeId },

			'expand'           : {'function': self.__trigger_expand},

		})

		self.__freeze = False

		# state
		self.__lastPopupId = None
		self.__recordCount = None

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		#rint "----------- GFTable._phase_1_init_ -------------"

		super(GFTreeList, self)._phase_1_init_()

		self.__entries = []
		for entry in iterGFObjectChildrenOfClass(self, GFFieldBound):
			self.__entries.append(entry)

		self._block.getDataSource().registerEventListeners({
				'dsResultSetActivated': self.__ds_resultset_activated,  # from datasources.GDataSource
				'dsResultSetChanged'  : self.__ds_resultset_activated,  # -/-

				'dsCursorMoved'       : self.__ds_cursor_moved,			# from datasources.drivers.Base.ResultSet

				'dsRecordInserted2'   : self.__ds_record_inserted,		# -/-
				'dsRecordDeleted'     : self.__ds_record_deleted,
				'dsRecordUndeleted'   : self.__ds_record_undeleted,
			})

		self._block.associateTrigger('ON-NEWRECORD', self.__on_newrecord)
		self._block.associateTrigger('PRE-REFRESH', self.__pre_refresh)

		self.__lastId = self._rootId


	#####################################################
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
		# this handler must be called after mixins one
		#print "GFTreeList.resultset_activated"
		self.uiWidget._ui_set_focused_node_(self._getIdAt(self._rs.getRecordNumber()))

		# remember current record id to set parent if new record created
		#print "set last id to", self._rs.current[self._fldId]
		self.__lastId = self._rs.current[self._fldId]

		# this is for __ds_cursor_moved to detect empty record remove
		self.__recordCount = self._rs.getRecordCount()

	def __ds_cursor_moved(self, event):
		"""
		dsCursorMoved (parameters: none) whenever the cursor in the current
		ResultSet is moved, i.e. a different record becomes the current record.
		"""
		if DEBUG: print 'GFTreeList.cursor_moved', event

		if self._rs is None:
			if DEBUG: print "GFTreeList.cursor_moved and NO RESULTSET YET!"
			return 

		if self.__freeze:
			return
		
		# AFTER LEAVE OF NEWLY CREATED RECORD
		# revalidate if only record count changed since last time
		if self.__recordCount != self._rs.getRecordCount():
			if DEBUG: print "cursor moved and record count changed, was %s and now %s" % (self.__recordCount,self._rs.getRecordCount())
			self._revalidate()
			self.__recordCount = self._rs.getRecordCount()

		
		#print "current id:", self._getIdAt(self._rs.getRecordNumber())
		self.uiWidget._ui_set_focused_node_(self._getIdAt(self._rs.getRecordNumber()))

		# remember current record id to set parent if new record created
		#print "set last id to", self._rs.current[self._fldId]
		self.__lastId = self._rs.current[self._fldId]


	def __pre_refresh(__self, self):
		#print "PRE-REFRESH"
		__self.__lastId = __self._rootId

	def __on_newrecord(__self, self):

		if __self.__freeze:
			return

		#print "ON-NEWRECORD"
		#print "last id:", __self.__lastId

		#print "rs: ---------------------"
		#for row, record in enumerate(__self._rs or ()):
		#	print row, record[__self._fldId], record
		#print "-------------------------"

		__self._block.getField(__self.fld_parent).set_value(__self.__lastId)
		if __self.__lastId != __self._rootId:
			__self.uiWidget._ui_set_editor_visible_(True)

	def __ds_record_inserted(self, event):
		if DEBUG: print "GFTreeList.record_inserted"

		if self.__freeze:
			return

		if self._rs is None:
			if DEBUG: print "GFTreeList.record_inserted and NO RESULTSET YET!"
			return 

		#if self._block.save():
		#	self._revalidate()

		#if self.__freezed:
		#	return 
		if DEBUG: print 'GFTreeList.record_inserted', event
		self._revalidate()
		self.uiWidget._ui_set_focused_node_(self._getIdAt(self._rs.getRecordNumber()))
		#self._dump()

	def __ds_record_deleted(self, event):
		# mark deleted all child records
		pass

	def __ds_record_undeleted(self, event):
		# remove mark deleted on all child records and parent record
		pass

	def ui_set_focused_entry(self, entry):
		"""
		ui_set_focus is blocked for entries in GFTable
		ui_set_focused_entry used instead
		"""
		self.uiWidget._ui_set_focused_cell_(self._getIdAt(self._rs.getRecordNumber()), self.__entries.index(entry))


	def ui_focus_out(self):
		"""
		called from child GFTabStop
		"""
		pass

	#####################################################
	# Mixin required implementation
	#
	def formatNodeNameAt(self, row, col):
		if col == 0:
			return super(GFTreeList, self).formatNodeNameAt(row, col)
		else:
			return self.getFormattedValue(row, col)

	def getNodeNameFields(self):
		return [self.getFieldAt(i).name for i in range(self.getFieldCount())]

	def isNodeNameChanging(self):
		return False

	#####################################################
	# response to events from UITreeList
	#

	def _event_cell_focused(self, id, col):
		#rint 'GFTable: _event_cell_focused', row, col

		if not self.hasIdRow(id):
			print "! _event_cell_focused: id missed from model"
			return

		# set logical focus to entry
		# this must be before (else have issue with logical focus)
		# (goto_record makes SetFocus to previous entry, grid looses focus)
		self.__entries[col]._event_set_focus()

		# this must be after (else have issue with logical focus)
		self._block.goto_record(self.getIdRow(id))

	def _event_node_checked(self):
		self.processTrigger('RECORD-CHECKED')

	def _event_node_activated(self):
		"""
		User doubleckiked node, or pressed enter on node
		"""
		self.uiWidget._ui_set_editor_visible_(True)
		super(GFTreeList, self)._event_node_activated()

	def _event_menu_popup(self, id):
		"""
		call when menu popups and pass node id menu popupped on
		or None if menu popped up on empty space
		"""
		self.__lastPopupId = id

	def _event_move_node(self, targetId, sourceId):
		"""
		set targetId node parent field to sourceId
		"""
		self._rs[self.getIdRow(sourceId)][self._fldParent] = targetId
		self._revalidate()
		self._block.goto_record(self.getIdRow(sourceId))
		return True

	def _event_copy_node(self, targetId, sourceId):
		#print '_event_copy_node', targetId, sourceId

		# this done to avoid tree focus
		self.__freeze = True

		#print "vvvvvvvvvvvvvvvvvv"
		self._rs.setRecord(self.getIdRow(sourceId))
		record = self._rs.duplicateRecord(exclude=(self._fldId,))
		record[self._fldParent] = targetId

		#print "------------------"
		#for row, record in enumerate(self._rs or ()):
		#	print row, record[self._fldId], record
		# 
		#print "^^^^^^^^^^^^^^^^^^"

		self.__freeze = False

		self._revalidate()

		try:
			if self._block.autoCommit:
				self._form.commit()
			else:
				self._block.refresh(False, message=_('Node copied'))
		except:	# server error
			raise
		else:
			self._rs.setRecord(self.getIdRow(targetId))
			return True

	#####################################################
	# Interface to entries
	#
	def getEntries(self):
		return self.__entries

	def getFieldColumnIndex(self, fieldName):
		for i, entry in enumerate(self.__entries):
			if entry._field.name == fieldName:
				return i

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
	# UI 
	#
	def isNavigationDelegationEnabled(self):
	    # if row editor is not visible, no navigation delegation performed
		return not self.uiWidget._ui_is_row_editor_visible_()

	def isCellEditable(self):
		# dows not support cell editing
		return False

	def escapeEntry(self, entry):
		self.uiWidget._ui_set_editor_visible_(False)
		return True

	#####################################################
	# Interface to data
	#
	def getValue(self, row, col):
		record = self._rs.getRecord(row)
		if record is None:
			return None
		else:
			return record[self.__entries[col]._field.field]

	def getFormattedValue(self, row, col):
		value = self.getValue(row, col)
		entry = self.__entries[col]
		
		if value is None:
			return ""
		else:
			value = entry._displayHandler.build_display(entry._field.lookup(value), False)
				
			if entry.style == 'bitcheckbox':
				value = bool(int(value or '0', 2) & int(entry.activate_value, 2))

			return value


	def getFieldFormattedValueAt(self, row, field):
		"""
		This is GFTreeMixInNodeNamePattern required overrided method
		formatting using entry display handler
		"""
		col = self.getFieldColumnIndex(field)
		assert col is not None
		value = self.getFormattedValue(row, col)
		if isinstance(value, bool) and col == 0:
			value = _('Yes') if value else _('No')
		return value
	
	
	#####################################################
	# Trigger methods
	#
	def __trigger_getNewNodeParentId(self):
		if self.__lastPopupId is None:
			return self._rootId
		else:
			return self.__lastPopupId

	def __trigger_getPossibleOperations(self):
		operations = set()

		inContext = self.__lastPopupId is not None

		uiDriverCanModify = self._form.get_uidriver_name() != 'java'

		# TODO: when access will work ok with trees can set this from block.getAccess()
		canInsert = True and uiDriverCanModify
		canUpdate = True and uiDriverCanModify
		canDelete = True and uiDriverCanModify

		nodeInClipboard = self.getCuttedNodeId() is not None or self.getCopiedNodeId() is not None

		if inContext and canUpdate:
			operations.add('cutNode' )

		#if inContext and canInsert:
		#	operations.add('copyNode')

		if inContext and (canInsert or canUpdate) and nodeInClipboard:
			operations.add('pasteNode')

		operations.add('expand')
		operations.add('collapse')

		return operations

	def getCuttedNodeId(self, force=False):
		return self.uiWidget._ui_get_cutted_node_id_(force)

	def getCopiedNodeId(self, force=False):
		return self.uiWidget._ui_get_copied_node_id_(force)

	def __trigger_expand(self, expand=True):
		self.uiWidget._ui_expand_(self.getIdPath(self.__lastPopupId) if self.__lastPopupId is not None else None, expand)

	##########################################################
	# actions
	#
	def newNode(self):
		if self.__lastPopupId is None:
			id = self._rootId
			if self._rs.current.isEmpty():
				record = self._rs.current
			else:
				record = self._rs.appendRecord()
		else:
			id = self.__lastPopupId
			record = self._rs.appendRecord()
		record[self._fldParent] = id
		self._revalidate()
		self._rs.setRecord(self._rs.getRecordCount()-1)
		self.uiWidget._ui_rename_node_()

	def cutNode(self):
		if self.__lastPopupId is not None:
			if self.__lastPopupId != self._rootId:
				self.uiWidget._ui_cut_node_()
			else:
				self._form.show_message(_("Can't cut root"), 'Error')
		else:
			self._form.show_message(_("Nothing to cut"), 'Error')

	def copyNode(self):
		if self.__lastPopupId is not None:
			if self.__lastPopupId != self._rootId:
				self.uiWidget._ui_copy_node_()
			else:
				self._form.show_message(_("Can't copy root"), 'Error')
		else:
			self._form.show_message(_("Nothing to copy"), 'Error')

	def pasteNode(self):
		self.uiWidget._ui_paste_node_()

	def _getNearestRow(self, currentRow):
		"""
		returns parent node row
		        or next sibling row
		        or previous sibling row
		        or KeyError
		"""
		parentId = self._rs[currentRow][self._fldParent]
		try:
			return self.getIdRow(parentId)
		except KeyError:
			# currentRow is root node, try to go to next root, then to previous root
			rootRows = [row for row in (self.getIdRow(id) for id in self.iterChildIds(self._rootId)) if not self._rs[row].isDeleted() or row == currentRow]

			try:
				i = rootRows.index(currentRow)
			except ValueError:
				# currentRow is not root node, strange, return first root at list
				i = 0
			else:
				del rootRows[i]

			if rootRows:
				return rootRows[min(i, len(rootRows)-1)]
			else:
				raise KeyError, 'no other nodes'

	def deleteNode(self):
		if self.__lastPopupId == self._rootId:
			self._form.show_message(u_(u"Can't remove root node"), 'Error')
			return

		if not self._rs.current.isEmpty():
			rows = list(self._iterRowsRecursive(self._rs.getRecordNumber()))

			if self._block.autoCommit or self._form.show_message('\n'.join(filter(None, (u_("Are you sure want to delete %s record(s)?") % len(rows), self.deleteMessage))), 'Question'):
			
				if self._block.deleteRecords(rows, True, bypassDeletable=True):
					self.uiWidget._ui_delete_node_()
					try:
						self._rs.setRecord(self._getNearestRow(self._rs.getRecordNumber()))
					except KeyError:
						pass
		else:
			self._form.show_message(u_(u"Nothing to delete"), 'Error')

def iterGFObjectChildrenOfClass(gfObject, cls):
	for i in gfObject._children:
		if isinstance(i, cls):
			yield i
		for j in iterGFObjectChildrenOfClass(i, cls):
			yield j
