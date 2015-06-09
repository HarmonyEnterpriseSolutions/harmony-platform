# GNU Enterprise Common Library - XML elements for datasources
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
# $Id: GDataSource.py,v 1.24 2014/12/24 13:36:26 oleg Exp $
"""
Classes for the datasource object tree.
"""

import cStringIO

from gnue.common.apps import errors
from gnue.common.definitions import GObjects, GParser, GParserHelpers
from gnue.common import events
from gnue.common.formatting import GTypecast
from src.gnue.common.datasources.access import ACCESS


# =============================================================================
# <datasource>
# =============================================================================

class GDataSource (GObjects.GObj):
	"""
	Class that handles DataSources.  This is a subclass of GObj, which
	means this class can be created from XML markup and stored in an
	Object tree (e.g., a Forms tree).

	Each GDataSource object maintains its own event controller and issues the
	following events:
	  - dsResultSetActivated (parameters: resultSet) whenever the current
	    ResultSet of this datasource changes; this happens when a query is
	    executed or when the master of this datasource moves to another record.
	  - dsResultSetChanged (parameters: resultSet) whenever the current ResultSet
	    has been reloaded from the backend; this happens after each commit if the
	    "requery" option of this datasource is in use.
	  - dsCursorMoved (parameters: none) whenever the cursor in the current
	    ResultSet is moved, i.e. a different record becomes the current record.
	  - dsRecordLoaded whenever a record has been loaded from the backend.
	  - dsRecordInserted
	  - dsRecordTouched whenever a record is modified for the first time since
	    it was loaded from the backend or last saved.
	  - dsCommitInsert whenever a record is about to be inserted in the backend
	    due to a commit operation. The record in question will be the current
	    record of the datasource at the time this trigger is run.
	  - dsCommitUpdate whenever a record is about to be updated in the backend
	    due to a commit operation. The record in question will be the current
	    record of the datasource at the time this trigger is run.
	  - dsCommitDelete whenever a record is about to be deleted in the backend
	    due to a commit operation. The record in question will be the current
	    record of the datasource at the time this trigger is run.
	  - dsPostCommitInsert
	  - dsPostCommitUpdate
	  - dsPostCommitDelete
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None, type = "GDataSource"):

		GObjects.GObj.__init__ (self, parent, type)

		# Manually set a few defaults for properties in case the datasource was not
		# created with XML, but with e.g. DataSourceWrapper.
		self.type = "object"
		self.connection = None
		self.table = None
		self.cache = 200
		self.distinct = False
		self.primarykeyseq = None
		self.requery = True

		# GConnections object (connection manager). GDataSource must have a
		# _connections because it can be a top level object (when used with
		# DataSourceWrapper)
		self._connections = None

		self._toplevelParent = None # Needs to be set by subclass
		# so that _topObject gets set
		self._topObject = None

		# GConnection object. Forms accesses this variable :(
		self._connection = None

		# Master DataSource object
		self.__master = None

		# Master/detail link fields in the master table
		self.__masterPkFields = []

		# Master/detail link fields in the detail table
		self.__masterFkFields = []

		# Primary key fields of this table
		self.__primarykeyFields = []

		# Rowid field name
		self.__rowidField = None
		self.__exp_rowid = None

		# Condition from <conditions> child
		self.__staticCondition = None

		# Sort order definition from <sortorder> child
		self.__sortorder = []

		# Refenrenced fields (fields bound to a database column)
		self.__fieldReferences = {}

		# Default data for new records per field
		self.__defaultData = {}

		# Dictionary with the keys being GDataSource objects and the values being
		# (pk_fields, fk_fields) tuples.
		self.__details = {}

		# The current result set
		self.__currentResultSet = None

		# additional parameters we will pass to ResultSet.query function
		# parameters can be set from triggers with setParameter
		self._parameters = {}

		# We maintain our own event controller, so an object interested in *our*
		# events doesn't get the events of other datasources
		self.__eventController = events.EventController ()
		self.registerEventListeners = self.__eventController.registerEventListeners

		# Initialization steps
		self._inits = [self.__primaryInit, self.__secondaryInit,
			self.__tertiaryInit]

		# Definitions for triggers
		self._triggerGlobal = True
		self._triggerFunctions = {
			'createResultSet': {'function': self.__trigger_createResultSet},
			'simpleQuery'    : {'function': self.__trigger_simpleQuery},
			'update'         : {'function': self.__trigger_update},
			'delete'         : {'function': self.__trigger_delete},
			'call'           : {'function': self.__trigger_call},
			'getCondition'   : {'function': self.getCondition},
			'setCondition'   : {'function': self.setCondition},
			'count'          : {'function': self.__trigger_get_recordCount},

			'getParameter' : {'function': self.getParameter},
			'setParameter' : {'function': self.setParameter},
			'removeParameter' : {'function': self.removeParameter},
		}

		self._triggerProperties = {
			'extensions' : {
				'get'    : self.__trigger_get_extensions,
				'direct' : 1
			},
			'recordCount': {
				'get'    : self.__trigger_get_recordCount,
				'direct' : 1
			},
			'order_by'   : {
				'get'    : self.__trigger_get_order_by,
				'set'    : self.__trigger_set_order_by,
				'direct' : 1
			},
			'table': {
				'get'    : lambda: getattr(self, 'table', None),
			},
			'rowid': {
				'get'    : lambda: getattr(self, 'rowid', None),
			},
		}

	def getParameter(self, name, default=NotImplemented):
		if default is NotImplemented:
			return self._parameters[name]
		else:
			return self._parameters.get(name, default)

	def setParameter(self, name, value):
		oldValue = self._parameters.get(name)
		self._parameters[name] = value
		return oldValue != value

	def removeParameter(self, name):
		try:
			del self._parameters[name]
		except:
			pass

	# ---------------------------------------------------------------------------
	# Functions and properties available in triggers
	# ---------------------------------------------------------------------------

	def __trigger_createResultSet (self, conditions = {}, access = ACCESS.FULL,
		query = False):
		if query:
			return self.createResultSet (conditions, access)
		else:
			return self.createEmptyResultSet(access=access)

	# ---------------------------------------------------------------------------

	def __trigger_simpleQuery (self, maskDict):
		conditions = GConditions.buildConditionFromDict (
			maskDict, GConditions.GClike)
		resultSet = self.createResultSet (conditions)
		return [record.getFieldsAsDict () for record in resultSet]

	# ---------------------------------------------------------------------------

	def __trigger_update (self):
		# The update function is not available for backends that need a rollback
		# after a post have failed. Reason: we do an uncommmitted post here, and a
		# rollback in a later post would also roll back this post, and all changes
		# in this post would get lost.
		if self._connection._need_rollback_after_exception_:
			raise Exceptions.FunctionNotAvailableError
		self.postAll ()
		self.requeryAll (False)

	# ---------------------------------------------------------------------------

	def __trigger_delete (self):
		self.__currentResultSet.current.delete ()

	# ---------------------------------------------------------------------------

	def __trigger_call (self, name, params):
		# The call function is not available for backends that need a rollback
		# after a post have failed. Reason: we do an uncommmitted post here, and a
		# rollback in a later post would also roll back this post, and all changes
		# in this post would get lost.
		if self._connection._need_rollback_after_exception_:
			raise Exceptions.FunctionNotAvailable
		# Remember current record; record pointer is not reliable between postAll
		# and requeryAll!
		current = self.__currentResultSet.current
		self.postAll ()
		try:
			result = current.call (name, params)
		finally:
			self.requeryAll (False)
		return result

	# ---------------------------------------------------------------------------

	def __trigger_get_extensions (self):
		return self.extensions

	# ---------------------------------------------------------------------------

	def __trigger_get_recordCount (self):
		if self.__currentResultSet:
			return len (self.__currentResultSet)
		else:
			return 0

	# ---------------------------------------------------------------------------

	def __trigger_get_order_by (self):
		return self.__sortorder

	# ---------------------------------------------------------------------------

	def __trigger_set_order_by (self, value):
		self.__sortorder = self.__convertOrderBy (value)

	# ---------------------------------------------------------------------------
	# new order by
	# ---------------------------------------------------------------------------

	def addOrderBy(self, name, descending=False, ignorecase=False):
		"""
		returns True if something affected
		"""
		for order in self.__sortorder:
			if order['name'] == name:
				break
		else:
			order = { 'name' : name }
			self.__sortorder.append(order)

		# if just created, None -> True or False, elsewhere True to False or vice versa
		change = order.get('descending') != descending or order.get('ignorecase') != ignorecase
		order['descending'] = descending
		order['ignorecase'] = ignorecase
		return change

	def removeOrderBy(self, name):
		"""
		returns True if something affected
		"""
		change = False
		for i in xrange(len(self.__sortorder)-1, -1, -1):
			if self.__sortorder[i]['name'] == name:
				del self.__sortorder[i]
				change = True
		return change

	def getOrderBy(self, name):
		"""
		returns { name : ..., descending : ..., ignorecase : ... } or None
		throws KeyError if no sort order
		"""
		for order in self.__sortorder or ():
			if order['name'] == name:
				return order
		raise KeyError, name

	# ---------------------------------------------------------------------------
	# Initialize object after parsing from XML
	# ---------------------------------------------------------------------------

	def _buildObject (self):

		# Added 0.5.0 -- Delete before 1.0
		if hasattr (self, 'database'):
			self.connection = self.database
			del self.database

		# order_by attribute: set self.__sortorder
		if hasattr (self, 'order_by'):
			self.__sortorder = self.__convertOrderBy (self.order_by)

		# explicitfields attribute: reference them
		if hasattr (self, 'explicitfields'):
			if len (self.explicitfields):
				for field in self.explicitfields.split (','):
					self.referenceField (field.strip ())

		# primarykey attribute: remember them and reference them
		if hasattr (self, 'primarykey'):
			self.__primarykeyFields = self.primarykey.split (',')
			# Make sure the primary key is included in the field references
			self.referenceFields (self.__primarykeyFields)

		if hasattr(self, 'rowid'):
			self.__exp_rowid = self.rowid

		# <condition> child: set self.__staticCondition
		self.__staticCondition = self.findChildOfType ('GCCondition')

		# <sortorder> child: set self.__sortorder
		sortorder = self.findChildOfType ('GCSortOrder')
		if sortorder:
			self.__sortorder = sortorder.sorting

		# <staticset> child: set self._staticSet
		self._staticSet = self.findChildOfType ('GDStaticSet')

		# <sql> child: set self._rawSQL
		self._rawSQL = self.findChildOfType ('GDSql')

		return GObjects.GObj._buildObject (self)


	# ---------------------------------------------------------------------------
	# Phase 1 init: Find connection manager and open connection
	# ---------------------------------------------------------------------------

	def __primaryInit (self):

		self._topObject = self.findParentOfType (self._toplevelParent)
		self.setConnectionManager (self._topObject._connections)

		if self.connection is None:
			# For connectionless (unbound or static) datasources, the base driver is
			# enough
			from gnue.common.datasources.drivers import Base
			self.__resultSetClass = Base.ResultSet
		else:
			# Get Connection object and log in
			self._connection = self._connections.getConnection (self.connection,
				login = True)

			# Remember the result set class to use
			self.__resultSetClass = self._connection._resultSetClass_

			# Check if the connection has a fixed primary key name
			primarykeyFields = self._connection._primarykeyFields_
			if primarykeyFields:
				self.__primarykeyFields = primarykeyFields
				self.referenceFields (self.__primarykeyFields)

			# Include the rowid in list of field references
			rowidField = self._connection._rowidField_ or self.__exp_rowid
			if rowidField:
				# TODO: checks if the rowid is available and should be used go here:
				# 1. if primary key should be prefered, don't set self.__rowidField
				# 2. try if rowidField is available in current table/view
				if not self.__primarykeyFields:
					self.__rowidField = rowidField
					self.referenceField (self.__rowidField)

		# Add ourselves into the "global" datasource dictionary
		self._topObject._datasourceDictionary [self.name.lower ()] = self

		# Check whether the type matches the used tags
		if self.type == "sql" and self._rawSQL is None:
			raise Exceptions.MissingSqlDefinitionError, self.name
		elif not self.type == "sql" and self._rawSQL is not None:
			raise Exceptions.NotSqlTypeError, self.name

		# compatibility
		self.extensions = self._connection


	# ---------------------------------------------------------------------------
	# Phase 2 init: Link with master
	# ---------------------------------------------------------------------------

	# TODO: Merged into GDataSource per the TODOs in reports and forms however
	# TODO: self._topObject._datasourceDictionary implies that the top object
	# TODO: always has a specifc structure.  This is a bad thing :(  Maybe
	# TODO: GRootObj should contain a getDatasourceDict()?
	#
	def __secondaryInit (self):

		# Master/Detail handling
		# FIXME: Could this be merged with primary init, and done before connect?
		# So bugs in the datasource definition would be reported before asking for
		# connection login.
		# Hmmm... No, because primary init registers the datasource in the toplevel
		# datasourceDictionary, and the master must already be registered here.
		# Maybe a _topObject.findChildByName would help and be more clean?
		if hasattr (self, 'master') and self.master:

			# Find the master datasource by name
			self.__master = self._topObject._datasourceDictionary.get (
				self.master.lower ())

			if self.__master is None:
				raise Exceptions.MasterNotFoundError (self.name, self.master)

			# Get the primary key fields from the "masterlink" attribute
			if not hasattr (self, 'masterlink'):
				raise Exceptions.MissingMasterlinkError (self.name)
			self.__masterPkFields = [s.strip () for s in self.masterlink.split (',')]
			self.__master.referenceFields (self.__masterPkFields)

			# Get the foreign key fields from the "detaillink" attribute
			if not hasattr (self, 'detaillink'):
				raise Exceptions.MissingDetaillinkError (self.name)
			self.__masterFkFields = [s.strip () for s in self.detaillink.split (',')]
			self.referenceFields (self.__masterFkFields)

			# Check if the number of fields matches
			if len (self.__masterPkFields) != len (self.__masterFkFields):
				raise Exceptions.MasterDetailFieldMismatch (self.name)

			self.__master._addDetail (self, self.__masterPkFields,
				self.__masterFkFields)


	# ---------------------------------------------------------------------------
	# Phase 3 init: do prequery
	# ---------------------------------------------------------------------------

	def __tertiaryInit (self):

		if hasattr(self, 'prequery'):
			if not self.hasMaster() and self.prequery:
				self.createResultSet()


	# ---------------------------------------------------------------------------
	# Set the Connection Manager for this DataSource
	# ---------------------------------------------------------------------------

	def setConnectionManager (self, connectionManager):
		"""
		Set the connection manager (L{GConnections.GConnections} instance for this
		datasource.

		@param connectionManager: the connection manager instance.
		"""

		self._connections = connectionManager


	# ---------------------------------------------------------------------------
	# Set the static condition for this datasource
	# ---------------------------------------------------------------------------

	def setCondition (self, mycondition):
		"""
		Set the static condition for this datasource. This condition is used in any
		query, additionally to the condition given in L{createResultSet}.

		@param mycondition: condition in prefix notation, dictionary notation or as
		  a L{GConditions} object tree.
		"""

		self.__staticCondition = mycondition


	# ---------------------------------------------------------------------------
	# Return the static condition for this datasource
	# ---------------------------------------------------------------------------

	def getCondition (self):
		"""
		Returns the static condition for this datasource, as set in setCondition or
		as defined in XML.
		"""

		return self.__staticCondition


	# ---------------------------------------------------------------------------
	# Get the master datasource of this datasource
	# ---------------------------------------------------------------------------

	def getMaster (self):
		"""
		Return the master datasource of this datasource.
		"""

		return self.__master


	# ---------------------------------------------------------------------------
	# Return True if this datasource is a detail
	# ---------------------------------------------------------------------------

	def hasMaster (self):
		"""
		Return True if this datasource is a detail of another datasource.
		"""

		return self.__master is not None

	def iterDetailDatasources(self, fields=None):
		"""
		returns tuple of details datasources
		optionally datasources connected with fields
		"""
		if fields is not None:
			fields = set(fields)
		for ds, (pkFields, fkFields) in self.__details.iteritems():
			if fields is None or set(pkFields) == fields:
				yield ds

	# ---------------------------------------------------------------------------
	# Add a detail datasource where this datasource is a master
	# ---------------------------------------------------------------------------

	def _addDetail (self, dataSource, pkFields, fkFields):
		"""
		Add a detail datasource where this datasource is the master.

		This method is called by the detail datasource to register itself at the
		master.

		@param dataSource: detail datasource.
		@param pkFields: list of field names of the primary key fields in the
		  detail datasource.
		@param fkFields: list of field names of the foreign kei fields in the
		  master datasource (i.e. in this datasource).
		"""

		self.__details [dataSource] = (pkFields, fkFields)


	# ---------------------------------------------------------------------------
	# Reference a bound field
	# ---------------------------------------------------------------------------

	def referenceField (self, field, defaultValue = None):
		"""
		Reference a bound field (i.e. bind it to a database column with the same
		name).

		@param field: Field name.
		@param defaultValue: optional default value for newly inserted records.
		"""

		if self.type == 'unbound':
			assert gDebug (1, "Trying to bind field %s to unbound DataSource" % field)
			return

		self.__fieldReferences [field] = True

		if defaultValue != None:
			self.__defaultData [field] = defaultValue


	# ---------------------------------------------------------------------------
	# Reference several bound fields
	# ---------------------------------------------------------------------------

	def referenceFields (self, fields):
		"""
		Reference several bound fields at once (i.e. bind them to database columns
		with the same names).

		@param fields: List of field names.
		"""

		for field in fields:
			if isinstance (field, basestring):
				self.referenceField (field)
			else:
				self.referenceField (*field)


	# ---------------------------------------------------------------------------
	# Reference an unbound field
	# ---------------------------------------------------------------------------

	def referenceUnboundField(self, field, defaultValue=None):
		"""
		Reference an unbound field.

		Unbound fields are not bound to a database column. Values stored in unbound
		fields are not persistent.

		It is only necessary to explicitly reference an unbound field if a default
		value should be set.

		@param field: Field name.
		@param defaultValue: optional default value for newly inserted records.
		"""

		assert gDebug (7,'Unbound Field %s implicitly referenced' % field)

		if defaultValue != None:
			self.__defaultData [field] = defaultValue


	# ---------------------------------------------------------------------------
	# Create and activate a new result set
	# ---------------------------------------------------------------------------

	def createResultSet (self, conditions = {}, access = ACCESS.FULL,
		masterRecord = None):
		"""
		Execute a query on the backend and create a result set.

		The result set generated by the query will become the active result set of
		this datasource.

		@param conditions: Conditions to be applied additionally to the static
		  condition of the datasource (defined with setCondition or with
		  <conditions> XML tags).
		@param access: bit integer, see ACCESS.* masks
		@param masterRecord: Master Record object for the ResultSet to be
		  generated if the datasource is a detail datasource.
		@return: The new active ResultSet object.
		"""
		assert self.__exp_rowid or access & ACCESS.UPDATE == 0, "rowid is required for datasource '%s'" % self.name
		assert masterRecord or not self.__masterPkFields and not self.__masterFkFields, 'Must provide masterRecord'

		resultSet = self.__createResultSet (conditions, access, masterRecord)
		self._activateResultSet (resultSet)
		return resultSet


	# ---------------------------------------------------------------------------
	# Requery an existing result set
	# ---------------------------------------------------------------------------

	def _requeryResultSet (self, masterRecord, resultSet):
		"""
		Requery data for an existing result set from the backend.

		This function queries the data for an existing result set again from the
		backend and merges everything that has changed meanwhile into the existing
		result set.

		The Record object uses this function to update all it's detail result
		sets after its changes have been posted to the database.

		The resultSet is passed as a parameter and need not be the current result
		set of the datasource.

		@param masterRecord: The master record for which the detail should be
		  requeried.
		@param resultSet: The existing result set into which the changes should be
		  merged.
		"""

		if self.__rowidField or self.__primarykeyFields:
			newResultSet = self.__createResultSet (masterRecord = masterRecord)
			resultSet._merge (newResultSet)
			newResultSet.close ()
		else:
			# We can't merge the resultsets without a key, so no use requerying at
			# all. The call to resultSet.requery will just reset the status for all
			# records and remove the deleted records from the cache.
			# We can pretend there has been a commit in any case: The requery isn't
			# done against the database anyway.
			resultSet.requery (True, self._parameters)

		# If this is the current result set, then the UI has to follow the changes.
		if resultSet == self.__currentResultSet:
			self.__eventController.dispatchEvent ('dsResultSetChanged',
				resultSet = resultSet)


	# ---------------------------------------------------------------------------
	# Create a result set
	# ---------------------------------------------------------------------------

	def __createResultSet (self, conditions = {}, access = ACCESS.FULL,
		masterRecord = None):

		assert masterRecord or not self.__masterPkFields and not self.__masterFkFields, 'Must provide masterRecord'

		cond = GConditions.combineConditions (conditions, self.__staticCondition)

		# Add condition from master record
		mastercond = {}
		for (masterfield, detailfield) in zip(self.__masterPkFields, self.__masterFkFields):
			mastercond [detailfield] = masterRecord.getField (masterfield)

		cond = GConditions.combineConditions (cond, mastercond)

		resultset =  self.__newResultSet (access, masterRecord)

		if self.type == 'object':
			resultset.query ('object', self.cache,
				table      = self.table,
				fieldnames = self.__fieldReferences.keys (),
				condition  = cond,
				sortorder  = self.__sortorder and self.__sortorder or [],
				distinct   = self.distinct,
				parameters = self._parameters)

		elif self.type == 'static':
			resultset.query ('static', self.cache, data = self._staticSet.data)

		elif self.type == 'sql':
			resultset.query ('sql', self.cache, sql = self._rawSQL.getChildrenAsContent ())

		return resultset


	# ---------------------------------------------------------------------------
	# Create and activate an empty result set
	# ---------------------------------------------------------------------------

	def createEmptyResultSet (self, masterRecord = None, access = ACCESS.FULL):
		"""
		Create an empty result set.

		The result set generated will become the active result set of this
		datasource.

		@param masterRecord: Master Record object for the ResultSet to be
		  generated if the datasource is a detail datasource (this will become
		  important once new records are inserted in this result set).
		@return: The new active (empty) ResultSet object.
		"""

		resultSet = self.__newResultSet (access, masterRecord)
		self._activateResultSet (resultSet)
		return resultSet


	# ---------------------------------------------------------------------------
	# Create a new ResultSet object instance
	# ---------------------------------------------------------------------------

	def __newResultSet (self, access, masterRecord):

		# Merge the correct foreign key values into the default data dictionary
		defaultData = self.__defaultData.copy ()
		if masterRecord is not None:
			for (masterfield, detailfield) in zip (
				self.__masterPkFields, self.__masterFkFields):
				defaultData [detailfield] = masterRecord.getField (masterfield)

		# Create the ResultSet instance
		return self.__resultSetClass (
			defaultData      = defaultData,
			connection       = self._connection,
			tablename        = self.table,
			rowidField       = self.__rowidField,
			primarykeyFields = self.__primarykeyFields,
			primarykeySeq    = self.primarykeyseq,
			boundFields      = self.__fieldReferences.keys (),
			requery          = self.requery,
			access           = access,
			details          = self.__details,
			eventController  = self.__eventController)


	# ---------------------------------------------------------------------------
	# Activate a result set
	# ---------------------------------------------------------------------------

	def _activateResultSet (self, resultSet):
		"""
		Make the given result set the active result set for this datasource.

		The master calls this to activate the correct detail result sets for its
		detail datasources.
		"""
		
		index = self.__currentResultSet.getRecordNumber() if self.__currentResultSet is not None else -1
		if index >= 0:
			resultSet.setRecord(index)
		self.__currentResultSet = resultSet
		# Let our details follow
		if self.__currentResultSet.current is not None:
			self.__currentResultSet.current._activate()
		self.__eventController.dispatchEvent('dsResultSetActivated', resultSet = resultSet)


	# ---------------------------------------------------------------------------
	# Post all changes in this datasource to the backend
	# ---------------------------------------------------------------------------

	def postAll (self):
		"""
		Post all changes to the backend.

		This function posts the top level master datasource of this datasource and
		all of that datasource's children.

		After calling postAll, L{requeryAll} must be called.
		"""

		if self.__master:
			self.__master.postAll ()
		else:
			try:
				self.__currentResultSet.post (parameters=self._parameters)
			except:
				if self._connection._need_rollback_after_exception_:
					# we have to rollback now, all changes to the backend get lost, so we
					# don't requery
					self._connection.rollback ()
				else:
					# we don't have to rollback, the changes done so far to the backend
					# are preserved, we requery so we have the the frontend updated
					self.__currentResultSet.requery (False, self._parameters)
				raise


	# ---------------------------------------------------------------------------
	# Requery data from the backend
	# ---------------------------------------------------------------------------

	def requeryAll (self, commit):
		"""
		Requery data from the backend.

		This must be called after L{postAll} to synchronize the datasource with
		changes that happened in the backend (through backend triggers). It
		requeries the top level master datasource of this datasource and all of
		that datasource's children.

		Note that this method also updates the record status for all added,
		modified and deleted records, so it has to be called even if the requery
		feature of the datasource is not used.

		@param commit: indicate whether a commit was done since the call to
		  L{postAll}.
		"""

		if self.__master:
			self.__master.requeryAll (commit)
		else:
			self.__currentResultSet.requery (commit, self._parameters)
			# Many records can have changed through backend triggers. The UI has to
			# follow the changes.
			self.__eventController.dispatchEvent ('dsResultSetChanged',
				resultSet = self.__currentResultSet)


	# ---------------------------------------------------------------------------
	# convert an order_by rule into the new 'sorting' format
	# ---------------------------------------------------------------------------

	def __convertOrderBy (self, order_by):
		"""
		This function transforms an order_by rule into a proper 'sorting' sequence,
		made of dictionaries with the keys 'name', 'descending' and 'ignorecase'.

		@param order_by: string, unicode-string, sequence with sort-order
		@return: sequence of dictionaries (name, descending, ignorecase)
		"""

		result = []

		# If it's a string or a unicode string, we transform it into a tuple
		# sequence, where all items are treated to be in 'ascending' order
		if isinstance (order_by, basestring):
			assert gDebug (1, "DEPRECIATION WARNING: use of 'order_by' attribute is " \
					"depreciated. Please use <sortorder> instead.")
			for field in order_by.split (','):
				(item, desc) = (field, field [-5:].lower () == ' desc')
				if desc:
					item = item [:-5].strip ()

				# Since the old 'order_by' format does *not* support 'ignorecase' we
				# will use 'False' as default
				result.append ({'name': item, 'descending': desc})

		# Well, order_by is already a sequence. So we've to make sure it's a
		# sequence of tuples with fieldname and direction.
		elif isinstance (order_by, list):
			for item in order_by:
				if isinstance (item, basestring):
					result.append ({'name':item})

				elif isinstance (item, dict):
					result.append (item)

				else:
					element = {'name': item [0]}
					if len (item) > 1: element ['descending'] = item [1]
					if len (item) > 2: element ['ignorecase'] = item [2]

		else:
			raise GParser.MarkupError, \
				(u_("Unknown type/format of 'order-by' attribute"), self._url,
				self._lineNumber)

		return result


# =============================================================================
# <sortorder>
# =============================================================================

class GCSortOrder (GObjects.GObj):
	"""
	The sort order definition for a datasource.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None):

		GObjects.GObj.__init__ (self, parent, type = 'GCSortOrder')


	# ---------------------------------------------------------------------------
	# Build Object
	# ---------------------------------------------------------------------------

	def _buildObject (self):

		self.sorting = []
		for item in self.findChildrenOfType ('GCSortField'):
			self.sorting.append ({'name': item.name,
					'descending': item.descending,
					'ignorecase': item.ignorecase})

		return GObjects.GObj._buildObject (self)


# =============================================================================
# <sortfield>
# =============================================================================

class GCSortField (GObjects.GObj):
	"""
	A field within a sort order definition.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None):

		GObjects.GObj.__init__ (self, parent, type = 'GCSortField')


# =============================================================================
# <sql>
# =============================================================================

class GSql (GObjects.GObj):
	"""
	The definition of a raw SQL query string.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None):

		GObjects.GObj.__init__ (self, parent, type = 'GDSql')


# =============================================================================
# <staticset>
# =============================================================================

class GStaticSet (GObjects.GObj):
	"""
	A set of static data.

	Static data is used whenever the values are predefined in the XML instead of
	read from a database.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None):

		GObjects.GObj.__init__ (self, parent, type = "GDStaticSet")


	# ---------------------------------------------------------------------------
	# Build Object
	# ---------------------------------------------------------------------------

	def _buildObject (self):

		self.data = [staticsetrow.data for staticsetrow in self._children if staticsetrow._type == "GDStaticSetRow" ]

		return GObjects.GObj._buildObject (self)


# =============================================================================
# <staticsetrow>
# =============================================================================

class GStaticSetRow (GObjects.GObj):
	"""
	A row of static data.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None):

		GObjects.GObj.__init__ (self, parent, type = "GDStaticSetRow")


	# ---------------------------------------------------------------------------
	# Build Object
	# ---------------------------------------------------------------------------

	def _buildObject (self):
		self.data = {}
		for staticsetfield in self._children:
			v = staticsetfield.value
			# allow pythonic constants evaluation
			try:
				v = eval(v, {})
			except StandardError: # NameError or SyntaxError -> unquoted string constant
				pass
			self.data[staticsetfield.name] = v
		return GObjects.GObj._buildObject (self)


# =============================================================================
# <staticsetfield>
# =============================================================================

class GStaticSetField (GObjects.GObj):
	"""
	A field in a static data row.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None):

		GObjects.GObj.__init__ (self, parent, type = "GDStaticSetField")


# =============================================================================
# <connection>
# =============================================================================

class GConnection(GObjects.GObj):
	"""
	A connection defined in the XML instead of in connections.conf.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent = None):

		GObjects.GObj.__init__ (self, parent, "GCConnection")

		self.comment = ""
		self.name    = ""
		self._inits  = [self.__initialize]


	# ---------------------------------------------------------------------------
	# Build Object
	# ---------------------------------------------------------------------------

	def _buildObject (self):

		self.name = self.name.lower ()

		return GObjects.GObj._buildObject (self)


	# ---------------------------------------------------------------------------
	# Build Object
	# ---------------------------------------------------------------------------

	def __initialize (self):

		# Add our database connection information to the connections
		# manager, then let it handle everything from there.
		root = self.findParentOfType (None)
		root._instance.connections.addConnectionSpecification (self.name, {
				'name': self.name,
				'provider': self.provider,
				'dbname': self.dbname,
				'host': self.host })


# =============================================================================
# List of XML Elements
# =============================================================================

def getXMLelements (updates = {}):

	xmlElements = {
		'datasource': {
			'BaseClass': GDataSource,
			'Importable': True,
			'Description': u_('A datasource provides a link to a database table '
				'or some similar data store.'),
			'Attributes': {
				'name':        {
					'Required': True,
					'Unique':   True,
					'Typecast': GTypecast.name,
					'Description': u_('Unique name of the datasource.')},
				'type':        {
					'Label': u_('Data Object Type'),
					'Typecast': GTypecast.name,
					'Default':  "object" },
				'connection':    {
					'Label': u_('Connection Name'),
					'Typecast': GTypecast.name,
					'Description': u_('The name of the connection as in '
						'connections.conf that points to '
						'a valid database.')},
				'database':    {
					'Typecast': GTypecast.name,
					'Deprecated': 'Use {connection} attribute instead' },
				'table':       {
					'Label': u_('Table Name'),
					'Typecast': GTypecast.name,
					'Default':  '',
					'Description': u_('The table in the database this datasource '
						'will point to.')},
				'cache':       {
					'Label': u_('Cache Size'),
					'Description': u_('Cache this number of records'),
					'Typecast': GTypecast.whole,
					'Default':  5 },
				'prequery':    {
					'Label': u_('Query on Startup'),
					'Description': u_('If true, the datasource is populated on '
						'form startup. If false (default), the form '
						'starts out with an empty record until the '
						'user or a trigger queries the database.'),
					'Typecast': GTypecast.boolean},
				'distinct':    {
					'Typecast': GTypecast.boolean,
					'Default':  False,
					'Description': 'TODO' },
				'order_by':    {
					'Typecast': GTypecast.text ,
					'Deprecated': 'Use {sortorder} tag instead' },
				'master':      {
					'Label': u_('M/D Master DataSource'),
					'Description': u_('If this datasource is the child in a '
						'master/detail relationship, this property '
						'contains the name of the master datasource.'),
					'Typecast': GTypecast.name },
				'masterlink':  {
					'Label': u_('M/D Master Field(s)'),
					'Description': u_('If this datasource is the child in a '
						'master/detail relationship, this property '
						'contains a comma-separated list of the '
						'master datasource\'s field(s) used for '
						'linking.'),
					'Typecast': GTypecast.text },
				'detaillink':  {
					'Label': u_('M/D Detail Field(s)'),
					'Description': u_('If this datasource is the child in a '
						'master/detail relationship, this property '
						'contains a comma-separated list of the '
						'this (child\'s) datasource\'s field(s) used '
						'for linking.'),
					'Typecast': GTypecast.text },
				# TODO: Short-term hack
				'explicitfields': {
					'Label': u_('Explicit Fields'),
					'Typecast': GTypecast.text,
					'Description': 'TODO' },
				'primarykey': {
					'Label': u_('Primary Key Field(s)'),
					'Description': u_('Comma-separated list of the fields that '
						'make up the primary key.'),
					'Typecast': GTypecast.text },
				'primarykeyseq': {
					'Label': u_('Primary Key Sequence'),
					'Description': u_('Name of the sequence used to populate a '
						'primary key (only applies to relational '
						'backends that support sequences; requires '
						'a single {primarykey} value.'),
					'Typecast': GTypecast.text },
				'rowid': {
					#'Required': True,
					'Label': u_('Row-ID field'),
					'Description': u_('Name of the field to use as Row-ID if the '
						'connection does not support row ids.'),
					'Typecast': GTypecast.text },
				'requery': {
					'Label': u_('Re-query on commit?'),
					'Default': True,
					'Description': u_('Requery a record after posting it; requires '
						'{primarykey} support and a non-null primary '
						'key value at the time of update (whether '
						'via a trigger or by the use of '
						'{primarykeyseq}.'),
					'Typecast': GTypecast.boolean }
			},
			'ParentTags': None },

		'sortorder': {
			'BaseClass': GCSortOrder,
			'Attributes': {},
			'ParentTags': ('datasource',),
		},
		'sortfield': {
			'BaseClass': GCSortField,
			'Attributes': {
				'name': {
					'Required': True,
					'Unique'  : True,
					'Description': u_('The name of the field by which the datasource '
						'will be ordered.'),
					'Typecast': GTypecast.name,
				},
				'descending': {
					'Description': u_('Selects if the ordering is done in ascending '
						'(default) or in descending order.'),
					'Default' : False,
					'Typecast': GTypecast.boolean,
				},
				'ignorecase': {
					'Default' : False,
					'Typecast': GTypecast.boolean,
					'Description': u_('Selects wether the ordering is case-sensitive '
						'or not.'),
				},
			},
			'ParentTags': ('sortorder',),
		},

		'staticset': {
			'BaseClass': GStaticSet,
			#  TODO: This should be replaced by a SingleInstanceInParentObject
			#        instead of SingleInstance (in the whole file)
			#         'SingleInstance': True,
			'Attributes': {
				'fields':        {
					'Typecast': GTypecast.text,
					'Required': True } },
			'ParentTags': ('datasource',) },
		'staticsetrow': {
			'BaseClass': GStaticSetRow,
			'ParentTags': ('staticset',) },
		'staticsetfield': {
			'BaseClass': GStaticSetField,
			'Attributes': {
				'name':        {
					'Typecast': GTypecast.text,
					'Required': True },
				'value':        {
					'Typecast': GTypecast.text,
					'Required': True } },
			'ParentTags': ('staticsetrow',) },
		'sql': {
			'BaseClass': GSql,
			'MixedContent': True,
			'KeepWhitespace': True,
			'ParentTags': ('datasource',) },
		'connection': {
			'BaseClass': GConnection,
			'Attributes': {
				'name': {
					'Required': True,
					'Unique': True,
					'Typecast': GTypecast.name,
					'Description': 'TODO' },
				'provider': {
					'Required': True,
					'Typecast': GTypecast.name,
					'Description': 'TODO' },
				'dbname': {
					'Required': False,
					'Typecast': GTypecast.text,
					'Description': 'TODO' },
				'service': {
					'Required': False,
					'Typecast': GTypecast.text,
					'Description': 'TODO' },
				'comment': {
					'Required': False,
					'Typecast': GTypecast.text,
					'Description': 'TODO' },
				'host': {
					'Required': False,
					'Typecast': GTypecast.text,
					'Description': 'TODO' } },
			'ParentTags': None,
			'Description': 'TODO' },
	}

	# Add conditional elements
	xmlElements.update (GConditions.getXMLelements (
			{'condition': {'ParentTags': ('datasource',)}}))

	for alteration in updates.keys ():
		xmlElements [alteration].update (updates [alteration])

	# Connections will have the same parent as datasources
	xmlElements ['connection']['ParentTags'] = \
		xmlElements ['datasource']['ParentTags']

	return xmlElements


# =============================================================================
# Wrapper for standalone DataSources (i.e., not in context of a GObj tree)
# =============================================================================

def DataSourceWrapper (connections = None, fields = [], attributes = {},
	init = True, sql = ""):
	"""
	Wrapper function to use datasources outside an XML tree.

	@param connections: Connection manager (L{GConnections.GConnections}
	  instance).
	@param fields: List of field names to bind to the database.
	@param attributes: Dictionary of attributes to set for the datasource (all
	  XML attributes can be used).
	@param init: If set to False, does not initialize the datasource object.
	@param sql: Optional raw SQL.
	"""

	source = _DataSourceWrapper ()

	if sql:
		s = GSql (source)
		GParserHelpers.GContent (s,sql)
		attributes ['type'] = 'sql'


	if connections:
		source.setConnectionManager (connections)

	if init:
		source.buildAndInitObject (**attributes)
	else:
		source.buildObject (**attributes)

	if fields:
		source.referenceFields (fields)

	return source

# -----------------------------------------------------------------------------

class _DataSourceWrapper (GDataSource):
	def __init__ (self, *args, **parms):
		GDataSource.__init__ (self, *args, **parms)
		self._datasourceDictionary= {}
		self._toplevelParent = self._type


# =============================================================================
# Load AppServer specific resources
# =============================================================================

class AppServerResourceError (errors.AdminError):
	"""
	Abstract base class for errors when loading appserver resources.
	"""
	pass

# -----------------------------------------------------------------------------

class InvalidURLError (AppServerResourceError):
	"""
	Invalid URL for an appserver resource.
	"""
	def __init__ (self, url):
		msg = u_("The URL '%s' is not a valid application server resource "
			"locator") % url
		AppServerResourceError.__init__ (self, msg)

# -----------------------------------------------------------------------------

class InvalidResourceTypeError (AppServerResourceError):
	"""
	Invalid resource type for an appserver resource.
	"""
	def __init__ (self, resourceType):
		msg = u_("Resource type '%s' is not supported") % resourceType
		AppServerResourceError.__init__ (self, msg)

# -----------------------------------------------------------------------------

class ResourceNotFoundError (AppServerResourceError):
	"""
	Requested appserver resource not found.
	"""
	def __init__ (self, resType, resName):
		msg = u_("Resource '%(name)s' of type '%(type)s' not found") \
			% {'type': resType,
			'name': resName}
		AppServerResourceError.__init__ (self, msg)


# -----------------------------------------------------------------------------
# Load a resource from appserver and return it as a file-like object
# -----------------------------------------------------------------------------

def getAppserverResource (url, paramDict, connections):
	"""
	Load an appserver resource.

	Appserver resources are XML definitions that are generated by appserver.

	@param url: Resource URL. Must be in format
	  appserver://<connection>/<resourcetype>/<resourcename>
	@param paramDict: Parameters to provide when requesting the resource. Valid
	  parameters depend on the resource type.
	@param connections: Connection manager that can be used to connect to the
	  appserver backend.
	"""
	if url [:12].lower () != 'appserver://':
		raise InvalidURLError, url

	if '?' in url:
		(appUrl, options) = url [12:].split ('?')
	else:
		appUrl  = url [12:]
		options = None

	parts = appUrl.split ('/')
	if len (parts) != 3:
		raise InvalidURLError, url
	(connection, element, elementName) = parts [:3]

	if not len (connection) or not len (element) or not len (elementName):
		raise InvalidURLError, url

	if not element in ['form']:
		raise InvalidResourceTypeError, element

	elementParams = {}

	if options:
		for part in options.split (';'):
			(item, value) = part.split ('=')
			elementParams [item] = value

	debugFileName = None
	if elementParams.has_key ('debug-file'):
		debugFileName = elementParams ['debug-file']
		del elementParams ['debug-file']

	paramDict.update (elementParams)

	attrs = {'name'    : 'dtsClass',
		'database': connection,
		'table'   : 'gnue_class'}
	fieldList = ['gnue_id', 'gnue_name', 'gnue_module']

	dts = DataSourceWrapper (
		connections = connections,
		attributes  = attrs,
		fields      = fieldList)

	parts = elementName.split ('_')
	if len (parts) != 2:
		raise ResourceNotFoundError, (element, elementName)

	moduleName = (parts [0]).upper ()
	className  = (parts [1]).upper ()
	cond = ['and', ['eq', ['upper', ['field', 'gnue_name']],
			['const', className]],
		['eq', ['upper', ['field', 'gnue_module.gnue_name']],
			['const', moduleName]]]
	mc = GConditions.buildConditionFromPrefix (cond)

	rs = dts.createResultSet (mc)
	if rs.firstRecord ():
		paramDict ['connection'] = connection

		res = rs.current.call ("gnue_%s" % element, paramDict)

		if debugFileName is not None:
			dfile = open (debugFileName, 'w')
			dfile.write (res.encode ('utf-8'))
			dfile.close ()

		return cStringIO.StringIO (res.encode ('utf-8'))

	else:
		raise ResourceNotFoundError, (element, elementName)
