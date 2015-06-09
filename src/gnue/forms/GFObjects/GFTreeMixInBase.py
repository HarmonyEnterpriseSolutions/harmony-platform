from toolib                          import debug
from src.gnue.forms.GFObjects import GFStyles

DEBUG=1

class GFTreeMixInBase(object):
	"""
	Required:
		def formatNodeNameAt(self, row)
		def isNodeNameChanging(self)
		def getNodeNameFields(self)
	"""


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self):

		# default attribute values
		self.rootname = None

		# will be definded in phase 1 init
		self._rootId          = None

		# filled in phase 1 init
		self._fldId     = None
		self._fldParent = None

		# filled on event
		self._rs = None

		# tree data
		self.__childIds = {}
		self.__idRow = {}
		self.__invalid = True

		# triggers
		self._validTriggers.update({
			'RECORD-ACTIVATED' : 'Record-Activated',
			'RECORD-CHECKED'   : 'Record-Checked',

			'POST-REFRESH'     : 'Post-Refresh',
		})

		self._triggerFunctions = {
			'getBlock':            {'function': lambda: self._block.get_namespace_object()},
			'getCheckedNodesData': {'function': self.__trigger_getCheckedNodesData},
			#'isVirtualRootChecked': {'function': self.__trigger_isVirtualRootChecked},
			#'getChildNodesData'  : {'function': self.__trigger_getChildNodesData},
			#'setChildNodesData'  : {'function': self.__trigger_setChildNodesData},
			'checkAllNodes'      : {'function': self.__trigger_checkAllNodes },
			
			# expose tree model
			'getRootId'          : {'function': self.getRootId},
			'getChildIds'        : {'function': self.getChildIds},
			'getParentId'        : {'function': self.__trigger_getParentId},
			'getValue'           : {'function': self.__trigger_getValue},
			'setValue'           : {'function': self.__trigger_setValue},
		}

		self._triggerProperties = {
		}

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		super(GFTreeMixInBase, self)._phase_1_init_()

		self._rootId = eval(self.rootid, {})


		# tree is not GFFieldBound
		self._block = self.get_block()

		#translate to resultset field
		self._fldId     = self._rsField(self.fld_id)
		self._fldParent = self._rsField(self.fld_parent)
		self._fldStyle  = self._rsField(self.fld_style) if getattr(self, 'fld_style', None) else None


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
	def validate(self):
		if self.__invalid:
			self._revalidate()

	def invalidate(self):
		self.__invalid = True

	def _revalidate(self):
		"""
		generates new __childIds and __idRow
		"""
		#######################################
		# internal data validation
		# self.__childIds is { rowId : [childId1, childId2...]}
		# self.__idRow     is { rowId : row }
		#
		self.__childIds.clear()
		self.__idRow.clear()

		# if we have virtual root
		if self.rootname is not None:
			# root id (virtual) row has index -1
			self.__idRow[self._rootId] = -1

			# children of NotImplemented parent is Virtual Root (row -1)
			self.__childIds[NotImplemented] = [self._rootId]

		for row, record in enumerate(self._rs or ()):
			print row, record[self._fldId], record
			id = record[self._fldId]
			self.__idRow[id] = row
			parentId = record[self._fldParent]
			if id != parentId:
				self.__childIds.setdefault(parentId, []).append(id)
			else:
				debug.error("! Cyclic tree node reference removed", id)

		#######################################
		if 1:
			self._dump()

		self.__invalid = False

		self.processTrigger('POST-REFRESH')
		self.uiWidget._ui_revalidate_()

	# the only three accessors to model
	def getIdRow(self, id):
		self.validate()
		return self.__idRow[id]

	def hasIdRow(self, id):
		self.validate()
		return id in self.__idRow

	def getChildIds(self, nodeId):
		self.validate()
		return self.__childIds.get(nodeId, ())

	##################################################################

	def _dump(self):
		print "model %svalid" % ('NOT ' if self.__invalid else '')
		print "------------------------------------"
		for k, v in self.__childIds.iteritems():
			print k, v
		print "------------------------------------"
		print self.__idRow
		print "------------------------------------"
	
	def _iterRowsRecursive(self, row, includeSelf=True):

		if row >= 0 and includeSelf:
			yield row

		for id in self.getChildIds(self._getIdAt(row)):
			for i in self._iterRowsRecursive(self.getIdRow(id)):
				yield i

	##################################################################
	# Interface for uiWidget model creation
	#

	def getRootId(self):
		if self.rootname is not None:
			return NotImplemented
		else:
			return self._rootId

	def iterChildIdsRecursive(self, nodeId, includeSelf=True):
		if includeSelf:
			yield nodeId
		for i in self.getChildIds(nodeId):
			for j in self.iterChildIdsRecursive(i, True):
				yield j

	def getChildCount(self, id):
		return len(self.getChildIds(id))

	def formatNodeName(self, id, col=0):
		if id != self._rootId:
			row = self.getIdRow(id)
			return self.formatNodeNameAt(row, col)
		else:
			return self.rootname

	def setNodeName(self, id, text):
		"""
		tries to unparse text as in nodeNamePattern and set to fields
		works only for text fields
		"""
		if id is not NotImplemented:
			return self.setNodeNameAt(self.getIdRow(id), text)
		return False

	#def getSelectionIdPath(self):
	#	return self.getIdPath(self._rs.current[self._fldId])

	def getIdPath(self, id):
		#rint 'getIdPath', id
		idPath = []
		while id != self.getRootId():
			idPath.append(id)
			#rint 'appended', id
			try:
				row = self.getIdRow(id)
			except KeyError:
				#raise
				break
			else:
				if row == -1:
					id = NotImplemented
				else:
					id = self._rs[row][self._fldParent]
		idPath.reverse()
		#rint "getIdPath:", idPath
		return idPath

	#####################################################
	# node styles
	#

	def getNodeStyles(self):
		return self.__nodeStyles

	def getNodeStyleKey(self, id):
		if self._fldStyle:
			row = self.getIdRow(id)
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
		if DEBUG: print 'GFTreeMixInBase.commit_insert'
		self.invalidate()

	def __ds_commit_delete(self, event):
		if DEBUG: print 'GFTreeMixInBase.commit_delete'
		self.invalidate()

	def __ds_resultset_activated(self, event):
		"""
		- dsResultSetActivated (parameters: resultSet) whenever the current
		  ResultSet of this datasource changes; this happens when a query is
		  executed or when the master of this datasource moves to another record.
		- dsResultSetChanged (parameters: resultSet) whenever the current ResultSet
		  has been reloaded from the backend; this happens after each commit if the
		  "requery" option of this datasource is in use.
		"""
		if DEBUG: print 'GFTreeMixInBase.resultset_activated', event.resultSet
		self._rs = event.resultSet
		self._revalidate()

	def __ds_resultset_changed(self, event):
		if DEBUG: print 'GFTreeMixInBase.resultset_changed, invalid =', self.__invalid
		self.validate()

	def __ds_record_changed(self, event):
		fields = set(event.fields)
		styleChanged = self._fldStyle is not None and self._fldStyle in fields
		fields.intersection_update(map(self._rsField, self.getNodeNameFields()))
		nameChanged = not self.isNodeNameChanging() and fields
		if nameChanged or styleChanged:
			id = event.record[self._fldId]
			#if id is not None:
			self.uiWidget._ui_revalidate_node_(id, nameChanged, styleChanged)

	#####################################################
	# response to events from uiTree
	#
	def _event_node_selected(self, id):
		"""
		node selected with cursor
		"""
		try:
			row = self.getIdRow(id)
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


	#################################################################################################
	# triggers
	#

	def __trigger_getCheckedNodesData(self, fieldnames, reduceChildren=False, style=NotImplemented):
		data = self._block.get_data(fieldnames)
		return [
			data[self.getIdRow(id)] 
			for id in self.uiWidget._ui_get_checked_nodes_(reduceChildren)
			# TODO: style == self.getNodeStyle(id).name is not good for multiple styles
			if id is not NotImplemented and self.hasIdRow(id) and (style is NotImplemented or style == self.getNodeStyle(id).name)
		]

	#def __trigger_isVirtualRootChecked(self):
	#	"""
	#	returns True if virtualRoot checked
	#	"""
	#	nodes = self.uiWidget._ui_get_checked_nodes_(reduceChildren=True)
	#	return None in nodes

	def __trigger_checkAllNodes(self, checked=True):
		self.uiWidget._ui_check_all_nodes_(checked)
	
	#def __trigger_getChildNodesData(self, fieldnames, id=None, includeSelf=False):
	#	data = self._block.get_data(fieldnames)
	#	return [data[i] for i in self._iterRowsRecursive(
	#		self.getIdRow(id) if id is not None else self._rs.getRecordNumber(),
	#		includeSelf=False
	#	)]

	#def __trigger_setChildNodesData(self, data, id=None, includeSelf=False):
	#	"""
	#	@param data: { fieldname : valkue, }
	#	@param id: parent id, focused node if None
	#	@param includeSelf: set parent node data
	#	"""
	#	data = data.items()
	#	for row in self._iterRowsRecursive(
	#		self.getIdRow(id) if id is not None else self._rs.getRecordNumber(),
	#		includeSelf=False
	#	):
	#		for field, value in data:
	#			self._setFieldValueAt(row, field, value)
			

	#################################################################################################
	# tree model exposed to POST-REFRESH TRIGGER
	#

	def __trigger_getParentId(self, id):
		try:
			row = self.getIdRow(id)
		except KeyError:
			pass
		else:
			if row >= 0:
				return self._rs[row][self._fldParent]

	def __trigger_getValue(self, id, fieldName):
		return self._rs[self.getIdRow(id)][self._rsField(fieldName)]

	def __trigger_setValue(self, id, fieldName, value):
		self._rs[self.getIdRow(id)][self._rsField(fieldName)] = value


