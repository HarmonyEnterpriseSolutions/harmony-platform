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
# GFTree.py
#
# DESCRIPTION:
"""
Logical tree support

TODO: completely remove row from uiObject interface, replace with id
"""

import re
import datetime

from GFTabStop                      import GFTabStop
from toolib                         import debug
from gnue.common.datasources.access import ACCESS
from src.gnue.forms.GFObjects import GFStyles


REC_FIELD = re.compile(r"\%(\([A-Za-z_]\w*\))")
DEBUG=0



class GFTreeMixIn(object):
	"""
	"""


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self):

		# default attribute values
		self.rootname = None

		# will be definded in phase 1 init
		self._rootId          = None
		self.__nodeNameFields   = None
		self.__nodeNamePattern = None

		# filled in phase 1 init
		self._fldId     = None
		self._fldParent = None

		# filled on event
		self._rs = None

		# tree data
		self.__childIds = {}
		self._idRow = {}
		self._structureChanged = False

		self.__nodeStyles = None

		# state fix
		self.__disableRevalidateOnNodeNameFieldsChange = False

		# triggers
		self._validTriggers = {
			'PRE-FOCUSOUT'     : 'Pre-FocusOut',
			'POST-FOCUSOUT'    : 'Post-FocusOut',
			'PRE-FOCUSIN'      : 'Pre-FocusIn',
			'POST-FOCUSIN'     : 'Post-FocusIn',
			'ON-NEXT-ENTRY'    : 'On-Next-Entry',
			'ON-PREVIOUS-ENTRY': 'On-Previous-Entry',

			'RECORD-ACTIVATED' : 'Record-Activated',
			'RECORD-CHECKED'   : 'Record-Checked',

			'POST-REFRESH'     : 'Post-Refresh',
		}

		self._triggerFunctions = {
			'getBlock':            {'function': lambda: self._block.get_namespace_object()},
			'getCheckedNodesData': {'function': self.__trigger_getCheckedNodesData},
			#'isVirtualRootChecked': {'function': self.__trigger_isVirtualRootChecked},
			'getChildNodesData'  : {'function': self.__trigger_getChildNodesData},
			'setChildNodesData'  : {'function': self.__trigger_setChildNodesData},
			'checkAllNodes'      : {'function': self.__trigger_checkAllNodes },
			
			# expose tree model
			'getRootId'          : {'function': self.getRootId},
			'getChildIds'        : {'function': self.iterChildIds},
			'getParentId'        : {'function': self.__trigger_getParentId},
			'getValue'           : {'function': self.__trigger_getValue},
			'setValue'           : {'function': self.__trigger_setValue},
			'isLeaf'             : {'function': self.__trigger_isLeaf},
		}

		self._triggerProperties = {
		}

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		super(GFTreeMixIn, self)._phase_1_init_()

		self._rootId = eval(self.rootid, {})

		# nodename -> create __nodeNameFields, __nodeNamePattern
		# substitute %(fieldname)s with %s and add field into list
		self.__nodeNameFields = []
		def sub(m):
			self.__nodeNameFields.append(m.groups()[0][1:-1])
			return '%'
		self.__nodeNamePattern = REC_FIELD.sub(sub, self.nodename)

		#rint "nodename fields:", self.__nodeNameFields
		#rint "nodename pattern:", self.__nodeNamePattern

		# tree is not GFFieldBound
		self._block = self.get_block()

		assert not self._block.autoNextRecord, "Tree block '%s' can't have autoNextRecord='Y'" % self._block.name

		#translate to resultset field
		self._fldId     = self._rsField(self.fld_id)
		self._fldParent = self._rsField(self.fld_parent)
		self._fldStyle  = self._rsField(self.fld_style) if getattr(self, 'fld_style', None) else None

		self._fldsNodeName = map(self._rsField, self.__nodeNameFields)

		assert self._fldId, 'id field has no field atribute'
		assert self._fldParent, 'parent field has no field atribute'

		# Register event handling functions
		self._block.getDataSource().registerEventListeners({
				'dsResultSetActivated': self.__ds_resultset_activated,  # from datasources.GDataSource
				'dsResultSetChanged'  : self.__ds_resultset_changed,    # -/-

				#'dsRecordLoaded'      : self.__ds_record_loaded,		# from datasources.drivers.Base.Record
				#'dsRecordInserted'    : self.__ds_record_inserted,		# -/-
				#'dsRecordTouched'     : self.__ds_record_touched,		# -/-
				'dsRecordChanged'     : self.__ds_record_changed,		# -/-

				'dsCommitInsert'      : self.__ds_commit_insert,		# -/-
				#'dsCommitUpdate'      : self.__ds_commit_update,		# -/-
				'dsCommitDelete'      : self.__ds_commit_delete,		# -/-
			})

		self.__nodeStyles = self.findChildOfType('GFStyles') or GFStyles(self)


	##################################################################
	# Validation
	#
	def _revalidate(self):
		#######################################
		# internal data validation
		# self.__childIds is { rowId : [childId1, childId2...]}
		# self._idRow     is { rowId : row }
		#
		self.__childIds.clear()
		self._idRow.clear()

		# if we have virtual root
		if self.rootname is not None:
			# root id (virtual) row has index -1
			self._idRow[self._rootId] = -1

			# children of NotImplemented parent is Virtual Root (row -1)
			self.__childIds[NotImplemented] = [self._rootId]

		for row, record in enumerate(self._rs or ()):
			if not record.isDeleted() and not record.isEmpty():
				id = record[self._fldId]
				self._idRow[id] = row
				parentId = record[self._fldParent]
				if id != parentId:
					self.__childIds.setdefault(parentId, []).append(id)
				else:
					debug.error("! Cyclic tree node reference removed", id)

		#######################################
		if 0:
			self._dump()

		self.processTrigger('POST-REFRESH')
		self.uiWidget._ui_revalidate_()


	def _dump(self):
		print "------------------------------------"
		for k, v in self.__childIds.iteritems():
			print k, v
		print "------------------------------------"
		print self._idRow
		print "------------------------------------"
	
	def _iterRowsRecursive(self, row, includeSelf=True):

		if row >= 0 and includeSelf:
			yield row

		for id in self.__childIds.get(self._getIdAt(row), ()):
			for i in self._iterRowsRecursive(self._idRow[id]):
				yield i

	##################################################################
	# Interface for uiWidget model creation
	#

	def getRootId(self):
		if self.rootname is not None:
			return NotImplemented
		else:
			return self._rootId

	def iterChildIds(self, nodeId):
		return self.__childIds.get(nodeId, ())

	def iterChildIdsRecursive(self, nodeId, includeSelf=True):
		if includeSelf:
			yield nodeId
		for i in self.__childIds.get(nodeId, ()):
			for j in self.iterChildIdsRecursive(i, True):
				yield j

	def getChildCount(self, id):
		return len(self.__childIds.get(id, ()))

	def formatNodeName(self, id):
		if id != self._rootId:
			row = self._idRow[id]
			return (self.__nodeNamePattern % tuple([self._getFieldFormattedValueAt(row, field) for field in self.__nodeNameFields])).replace('\n', ' ').strip()
		else:
			return self.rootname

	def setNodeName(self, id, text):
		"""
		tries to unparse text as in nodeNamePattern and set to fields
		works only for text fields
		"""
		if id is not NotImplemented:
			row = self._idRow[id]
			pattern = re.sub(r'(?i)\\\%[^a-z]*[a-z]', lambda m: '(.+)', re.escape(self.__nodeNamePattern)) + '$'
			m = re.match(pattern, text)
			if m:
				for i, text in enumerate(m.groups()):
					text = text.rstrip()
					field = self.__nodeNameFields[i]
					# do not allow to edit primary key
					if field != self.fld_id:
						# avoid node revalidation when changing tree label text
						self.__disableRevalidateOnNodeNameFieldsChange = True
						self._setFieldFormattedValueAt(row, field, text)
						self.__disableRevalidateOnNodeNameFieldsChange = False
				return True
		return False

	def isNodeNameEditable(self):
		"""
		if tree node name can be updated on existent or new node
		"""
		if self.labelEdit:
			for i in self.__nodeNameFields:
				if not self._block.getField(i).hasAccess(ACCESS.WRITE):
					return False
			return True
		else:
			return False

	def getIdPath(self, id):
		#rint 'getIdPath', id
		idPath = []
		while id != self.getRootId():
			idPath.append(id)
			#rint 'appended', id
			try:
				row = self._idRow[id]
			except KeyError:
				#rint "stop via KeyError"
				break
			else:
				if row == -1:
					id = NotImplemented
				else:
					id = self._rs[row][self._fldParent]
		idPath.reverse()
		#rint "getIdPath:", idPath
		return idPath

	def getNodeStyles(self):
		return self.__nodeStyles

	def getNodeStyleKey(self, id):
		if self._fldStyle:
			row = self._idRow[id]
			if row >=0:
				return self._rs[row][self._fldStyle]
			else:
				# virtual root has default style
				return 'default'
		else:
			return 'default'

	def getNodeStyle(self, id):
		return self.__nodeStyles.getStyle(self.getNodeStyleKey(id))

	#####################################################
	# response to events from DataSource
	#

	def __ds_commit_insert(self, event):
		if DEBUG: print 'GFTree.commit_insert'
		self._structureChanged = True

	def __ds_commit_delete(self, event):
		if DEBUG: print 'GFTree.commit_delete'
		self._structureChanged = True

	def __ds_resultset_activated(self, event):
		"""
		- dsResultSetActivated (parameters: resultSet) whenever the current
		  ResultSet of this datasource changes; this happens when a query is
		  executed or when the master of this datasource moves to another record.
		- dsResultSetChanged (parameters: resultSet) whenever the current ResultSet
		  has been reloaded from the backend; this happens after each commit if the
		  "requery" option of this datasource is in use.
		"""
		if DEBUG: print 'GFTree.resultset_activated', event.resultSet
		self._rs = event.resultSet
		self._revalidate()

	def __ds_resultset_changed(self, event):
		if DEBUG: print 'GFTree.resultset_changed', self._structureChanged
		if self._structureChanged:
			self._revalidate()
			self._structureChanged = False

	def __ds_record_changed(self, event):
		fields = set(event.fields)
		styleChanged = self._fldStyle is not None and self._fldStyle in fields
		fields.intersection_update(self._fldsNodeName)
		nameChanged = not self.__disableRevalidateOnNodeNameFieldsChange and bool(fields)
		if nameChanged or styleChanged:
			id = event.record[self._fldId]
			if id is not None:
				self.uiWidget._ui_revalidate_node_(id, nameChanged, styleChanged)

	#####################################################
	# response to events from uiTree
	#
	def _event_node_selected(self, id):
		"""
		node selected with cursor
		"""
		try:
			row = self._idRow[id]
		except KeyError:
			debug.error('No row for id: %s' % id)
		else:
			# do not select -1 row, it is virtual root
			#if row >= 0:
			if row == -1:
				# usually tree block is editable 'update' so can't do so
				#self.__block.append_record()
				#self.__block.last_record()
				#rint "_event_node_selected, row -1, GO FIRST RECORD"
				self._block.first_record()
			else:
				#rint "_event_node_selected, row", row
				self._block.goto_record(row)

	def _event_node_activated(self):
		"""
		User doubleckiked node, or pressed enter on node
		"""
		self.processTrigger('RECORD-ACTIVATED')
		self._block.processTrigger('RECORD-ACTIVATED')


	#####################################################
	# internal interface to data
	#
	def _rsField(self, field):
		"""returns resultset field name by logical field name"""
		return self._block.getField(field).field

	def _getIdAt(self, row):
		if row >= 0:
			return self._rs[row][self._fldId]
		else:
			return self._rootId

	def _getFieldValueAt(self, row, field):
		return self._rs[row][self._rsField(field)]

	def _setFieldValueAt(self, row, field, value):
		self._rs[row][self._rsField(field)] = value

	def _getFieldFormattedValueAt(self, row, field):

		# NOTE: tree has no entries so displayparser is not accessible
		# TODO: extract display parsing and formatting to GFField
		# unless can't set values to notext fields

		value = self._getFieldValueAt(row, field)
		if value is None:
			return ""
		else:
			field = self._block.getField(field)
			value = field.lookup(value)

			# WORKAROUND: since displayHandler in entry we ca't use it for formatting
			# TODO: formatter must be at field level
			if field.datatype == 'date' and hasattr(value, 'strftime') or isinstance(value, datetime.date):
				return value.strftime('%x')
			elif field.datatype == 'datetime' and hasattr(value, 'strftime') or isinstance(value, datetime.datetime):
				return value.strftime('%c')
			else:
				return unicode(value)

	def _setFieldFormattedValueAt(self, row, field, text):
		"""
		used when setting from clipboard
		"""

		# NOTE: tree has no entries so displayparser is not accessible
		# TODO: extract display parsing and formatting to GFField
		# unless can't set values to notext fields

		text = self._block.getField(field).reverse_lookup(text)
		self._setFieldValueAt(row, field, text or None)


	#################################################################################################
	# triggers
	#

	def __trigger_getCheckedNodesData(self, fieldnames, reduceChildren=False, style=NotImplemented):
		data = self._block.get_data(fieldnames)
		return [
			data[self._idRow[id]] 
			for id in self.uiWidget._ui_get_checked_nodes_(reduceChildren)
			# TODO: style == self.getNodeStyle(id).name is not good for multiple styles
			if id is not NotImplemented and id in self._idRow and (style is NotImplemented or style == self.getNodeStyle(id).name)
		]

	#def __trigger_isVirtualRootChecked(self):
	#	"""
	#	returns True if virtualRoot checked
	#	"""
	#	nodes = self.uiWidget._ui_get_checked_nodes_(reduceChildren=True)
	#	return None in nodes

	def __trigger_checkAllNodes(self, checked=True):
		self.uiWidget._ui_check_all_nodes_(checked)
	
	def __trigger_getChildNodesData(self, fieldnames, id=None, includeSelf=False):
		data = self._block.get_data(fieldnames)
		return [data[i] for i in self._iterRowsRecursive(
			self._idRow[id] if id is not None else self._rs.getRecordNumber(),
			includeSelf=False
		)]

	def __trigger_setChildNodesData(self, data, id=None, includeSelf=False):
		"""
		@param data: { fieldname : valkue, }
		@param id: parent id, focused node if None
		@param includeSelf: set parent node data
		"""
		data = data.items()
		for row in self._iterRowsRecursive(
			self._idRow[id] if id is not None else self._rs.getRecordNumber(),
			includeSelf=False
		):
			for field, value in data:
				self._setFieldValueAt(row, field, value)
			

	#################################################################################################
	# interface to tree model
	#

	def __trigger_getParentId(self, id):
		try:
			row = self._idRow[id]
		except KeyError:
			pass
		else:
			if row >= 0:
				return self._rs[row][self._fldParent]

	def __trigger_getValue(self, id, fieldName):
		return self._rs[self._idRow[id]][self._rsField(fieldName)]

	def __trigger_setValue(self, id, fieldName, value):
		self._rs[self._idRow[id]][self._rsField(fieldName)] = value

	def __trigger_isLeaf(self, nodeId=None):
		if nodeId is None:
			nodeId = self._rs.current[self._fldId]
		return len(self.__childIds.get(nodeId, ())) == 0


#
# GFTree
#
class GFTree(GFTreeMixIn, GFTabStop):

	label = None

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		GFTabStop.__init__(self, parent, self.__class__.__name__)
		GFTreeMixIn.__init__(self)

		self._triggerFunctions.update({
			'renameNode'       : { 'function': self.renameNode },
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

		self.__columns = None
		self.__freeze = False

		# state
		self.__lastPopupId = None

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		super(GFTree, self)._phase_1_init_()

		self._block.getDataSource().registerEventListeners({
				'dsResultSetActivated': self.__ds_resultset_activated,  # from datasources.GDataSource
				'dsResultSetChanged'  : self.__ds_resultset_activated,  # -/-

				'dsCursorMoved'       : self.__ds_cursor_moved,			# from datasources.drivers.Base.ResultSet
			})

		self.__columns = self.findChildrenOfType('GFTreeColumn', includeSelf=False, allowAllChildren=True)


	def hasLabel(self):
		return self.label is not None

	
	##################################################################
	# interface with uiWidget
	#

	def getColumns(self):
		return self.__columns

	##################################################################
	# GFTabStop implementation
	#
	def _is_navigable_(self, mode):
		# TODO: navigable? hidden?
		return self._block.navigable and self.navigable

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
		try:
			self.uiWidget._ui_set_focused_node_(self._getIdAt(self._rs.getRecordNumber()))
		except IndexError:
			print "! reproduced #228"
			import sys
			sys.excepthook(*sys.exc_info())

	def __ds_cursor_moved(self, event):
		"""
		dsCursorMoved (parameters: none) whenever the cursor in the current
		ResultSet is moved, i.e. a different record becomes the current record.
		"""
		if DEBUG: print 'GFTree.cursor_moved', event
		if not self.__freeze:
			if self._rs is not None:
				self.uiWidget._ui_set_focused_node_(self._getIdAt(self._rs.getRecordNumber()))
			else:
				if DEBUG: print "GFTree.cursor_moved and NO RESULTSET YET!"


	#####################################################
	# response to commands from uiTree
	#

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
		self._rs[self._idRow[sourceId]][self._fldParent] = targetId
		self._revalidate()
		self._block.goto_record(self._idRow[sourceId])
		return True

	def _event_copy_node(self, targetId, sourceId):
		#rint '_event_copy_node', targetId, sourceId

		# this done to avoid tree focus
		self.__freeze = True

		self._rs.setRecord(self._idRow[sourceId])
		record = self._rs.duplicateRecord(exclude=(self._fldId,))
		record[self._fldParent] = targetId

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
			self._rs.setRecord(self._idRow[targetId])
			return True


	def _event_new_node_created(self):

		# go to parent record
		#rs = self._rs
		#self._block.goto_record(self._idRow[self._rs.current[self._fldParent]])

		try:
			if self._block.autoCommit:
				self._form.commit()
			else:
				# new node created, need to save
				self._block.refresh(False, message = _("New node created"))
		except: # server error
			# here to cleanup
			if self._block.autoCommit:
				# rollback
				self._block.getDataSource().createResultSet(access=self._block.getAccess())

			raise


	def _event_new_node_cancelled(self):
		try:
			nearestId = self._getIdAt(self._getNearestRow(self._rs.getRecordNumber()))
		except KeyError:
			nearestId = None
		self._rs.current.unmodify()
		self._revalidate()
		if nearestId is not None:
			self._rs.setRecord(self._idRow[nearestId])

	def _event_node_checked(self):
		self.processTrigger('RECORD-CHECKED')

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

		if canInsert:
			operations.add('newNode')

		if inContext and canUpdate:
			operations.add('renameNode')

		if inContext and canUpdate:
			operations.add('cutNode' )

		if inContext and canInsert:
			operations.add('copyNode')

		if inContext and (canInsert or canUpdate) and nodeInClipboard:
			operations.add('pasteNode')

		if inContext and canDelete:
			operations.add('deleteNode')

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
		# if rs has one just created record, previous setRecord will do nothing so force tree select root node
		# else _ui_rename_node_ will not work because tree has no selection
		self.uiWidget._ui_set_focused_node_(self._getIdAt(self._rs.getRecordNumber()))
		self.uiWidget._ui_rename_node_()

	def renameNode(self):
		if self.__lastPopupId not in (None, self._rootId):
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
			return self._idRow[parentId]
		except KeyError:
			# currentRow is root node, try to go to next root, then to previous root
			rootRows = [row for row in (self._idRow[id] for id in self.iterChildIds(self._rootId)) if not self._rs[row].isDeleted() or row == currentRow]

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
