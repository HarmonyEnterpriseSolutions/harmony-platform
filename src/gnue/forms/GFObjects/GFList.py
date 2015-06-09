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
# $Id: GFList.py,v 1.1 2009/02/24 17:20:16 oleg Exp $
"""
Logical box support
"""

import re

from src.gnue.forms.GFObjects import GFTabStop

__all__ = ['GFList']

DEBUG=0
BaseClass = GFTabStop
REC_FIELD = re.compile(r"\%(\([A-Za-z_]\w*\))")

# =============================================================================
# <vbox>
# =============================================================================

class GFList(BaseClass):

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	label = None


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		BaseClass.__init__(self, parent, "GFList")

		# filled on event
		self.__rs = None

		self.__itemNameFields   = None
		self.__itemNamePattern = None

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
		}

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		#rint "----------- GFList._phase_1_init_ -------------"

		BaseClass._phase_1_init_(self)

		self.__block = self.get_block()

		assert (self.__block is not None), 'List %s has no block' % self.name

		# substitute %(fieldname)s with %s and add field into list
		self.__itemNameFields = []
		def sub(m):
			self.__itemNameFields.append(m.groups()[0][1:-1])
			return '%'
		self.__itemNamePattern = REC_FIELD.sub(sub, self.itemname)

		# Register event handling functions
		self.__block.getDataSource().registerEventListeners({
				'dsResultSetActivated': self.__ds_resultset_activated,  # from datasources.GDataSource
				'dsResultSetChanged'  : self.__ds_resultset_activated,  # -/-

				'dsCursorMoved'       : self.__ds_cursor_moved,			# from datasources.drivers.Base.ResultSet

				#'dsRecordLoaded'      : self.__ds_record_loaded,		# from datasources.drivers.Base.Record
				#'dsRecordInserted'    : self.__ds_record_inserted,		# -/-
				#'dsRecordTouched'     : self.__ds_record_touched,		# -/-
				'dsRecordChanged'     : self.__ds_record_changed,		# -/-

				#'dsRecordDeleted'     : self.__ds_record_changed,		# -/-. added
				#'dsRecordUndeleted'   : self.__ds_record_changed,		# -/-. added

				#'dsCommitInsert'      : self.__ds_commit_insert,		# -/-
				#'dsCommitUpdate'      : self.__ds_commit_update,		# -/-
				#dsCommitDelete'      : self.__ds_commit_delete,		# -/-
			})

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
		if DEBUG: print 'GFList.resultset_activated', event.resultSet
		self.__rs = event.resultSet
		self.uiWidget._ui_set_values_([self._getValueAt(i) for (i, record) in enumerate(self.__rs) if not record.isEmpty()])

	def __ds_record_changed(self, event):
		if DEBUG: print 'GFList.record_changed', event
		if self.__rs:
			i = self.__rs.getRecordNumber()
			self.uiWidget._ui_set_value_(i, self._getValueAt(i))

	def __ds_cursor_moved(self, event):
		if self.__rs:
			self.uiWidget._ui_select_row_(self.__rs.getRecordNumber())
		
	def _event_item_activated(self):#, row):
		"""
		User cLiked button
		"""
		#self._event_set_focus()
		#self.__block.goto_record(row)
		self.processTrigger('RECORD-ACTIVATED')
		self.__block.processTrigger('RECORD-ACTIVATED')

	def _event_item_focused(self, row):
		self._event_set_focus()
		self.__block.goto_record(row)

	def _event_next_row(self):
		row = self.__rs.getRecordNumber() + 1
		if row < self.__rs.getRecordCount():
			self.__block.goto_record(row)
			return True
		else:
			#self.__block.goto_record(0)
			return False
	
	def _event_prev_row(self):
		row = self.__rs.getRecordNumber() - 1
		if row >= 0:
			self.__block.goto_record(row)
			return True
		else:
			#self.__block.goto_record(self.__rs.getRecordCount()-1)
			return False

	def _getValueAt(self, row):
		return self.__itemNamePattern % tuple([self.__rs[row][self.getBlock().getField(field).field] for field in self.__itemNameFields])

	def getBlock(self):
		return self.__block

	##################################################################
	# GFTabStop implementation
	#
	
	def _is_navigable_(self, mode):
		return self.__block.navigable #and self.navigable
