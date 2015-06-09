#-*- coding: Cp1251 -*-
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
Gantt diagram
"""

import re

from toolib.util					import dicts
from src.gnue.forms.GFObjects import GFTabStop

REC_FIELD = re.compile(r"\%(\([A-Za-z_]\w*\))")
DEBUG=1



class GFGant(GFTabStop):
	"""
	"""


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		"""
		активность

		spr_activity
				activity_id serial
				no integer                      -- номер по порядку, в какой
												-- строке отображать
				name                            -- наименование
				duration integer                -- продолжительность
				start_min integer, default 0    -- не раньше чем


		у активности может быть одна или более предшествующих активностей

		spr_activity_predecessor
				activity_predecessor_id serial
				activity_id   
				predecessor_id
		"""

		GFTabStop.__init__(self, parent, self.__class__.__name__)

		self._block_act = None
		self._block_link = None

		# triggers
		self._validTriggers = {
			'PRE-FOCUSOUT'     : 'Pre-FocusOut',
			'POST-FOCUSOUT'    : 'Post-FocusOut',
			'PRE-FOCUSIN'      : 'Pre-FocusIn',
			'POST-FOCUSIN'     : 'Post-FocusIn',
			'ON-NEXT-ENTRY'    : 'On-Next-Entry',
			'ON-PREVIOUS-ENTRY': 'On-Previous-Entry',

			'RECORD-ACTIVATED' : 'Record-Activated',
		}

		self._triggerFunctions = {
		}

		self._triggerProperties = {
		}

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		super(GFGant, self)._phase_1_init_()

		self.__key_trans_act = (
			(self.fld_id,        'id'),
			(self.fld_duration,  'duration'),
			(self.fld_name,      'name'),
			(self.fld_row,       'row'),
			(self.fld_start_min, 'startMin'),
		)

		self.__conv_act = (
			('duration',  float),
			('startMin',  float),
		)

		self.__key_trans_link = (
			(self.fld_activity_from, 'activityFrom'),
			(self.fld_activity_to,   'activityTo'),
			(self.fld_lag,           'lag'),
		)

		self.__conv_link = (
			('lag',  float),
		)

		# gant is not GFFieldBound
		self._block_act  = self._form._logic.getBlock(self.block_activity)
		self._block_link = self._form._logic.getBlock(self.block_precedence)

		# Register event handling functions
		self._block_act.getDataSource().registerEventListeners({
				'dsResultSetActivated': self.__ds_activity_resultset_activated,  # from datasources.GDataSource
				'dsResultSetChanged'  : self.__ds_activity_resultset_activated,  # -/-

				#'dsRecordLoaded'      : self.__ds_activity_record_loaded,		# from datasources.drivers.Base.Record
				#'dsRecordInserted'    : self.__ds_activity_record_inserted,		# -/-
				#'dsRecordTouched'     : self.__ds_activity_record_touched,		# -/-
				'dsRecordChanged'     : self.__ds_activity_record_changed,		# -/-

				#'dsCommitInsert'      : self.__ds_activity_commit_insert,		# -/-
				#'dsCommitUpdate'      : self.__ds_activity_commit_update,		# -/-
				#'dsCommitDelete'      : self.__ds_activity_commit_delete,		# -/-
			})

		# Register event handling functions
		if 1:
			self._block_link.getDataSource().registerEventListeners({
					'dsResultSetActivated': self.__ds_link_resultset_activated,  # from datasources.GDataSource
					'dsResultSetChanged'  : self.__ds_link_resultset_activated,  # -/-

					#'dsRecordLoaded'      : self.__ds_link_record_loaded,		# from datasources.drivers.Base.Record
					#'dsRecordInserted'    : self.__ds_link_record_inserted,		# -/-
					#'dsRecordTouched'     : self.__ds_link_record_touched,		# -/-
					'dsRecordChanged'     : self.__ds_link_record_changed,		# -/-

					#'dsCommitInsert'      : self.__ds_link_commit_insert,		# -/-
					#'dsCommitUpdate'      : self.__ds_link_commit_update,		# -/-
					#'dsCommitDelete'      : self.__ds_link_commit_delete,		# -/-
				})

		self._block_act.associateTrigger('POST-FOCUSIN', self.__on_block_act_post_focusin)

	##################################################################
	# Validation
	#
	def _revalidate_activities(self):
		self.uiWidget._ui_set_activities_(
			[
				self._translateDict(row, self.__key_trans_act, self.__conv_act) 
				for row in self._block_act.iterRecords()
			]
		)

	def _revalidate_links(self):
		links = [
			self._translateDict(row, self.__key_trans_link, self.__conv_link) 
			for row in self._block_link.iterRecords()
			if row[self.fld_activity_from] is not None and row[self.fld_activity_to] is not None
		]
		self.uiWidget._ui_set_links_(links)


	def _translateDict(self, d, translation, conv):
		d = dicts.translateKeys(d, translation)
		for k, f in conv:
			d[k] = f(d[k])
		return d

	#####################################################
	# response to events from activity DataSource
	#

	def __ds_activity_resultset_activated(self, event):
		"""
		- dsResultSetActivated (parameters: resultSet) whenever the current
		  ResultSet of this datasource changes; this happens when a query is
		  executed or when the master of this datasource moves to another record.
		- dsResultSetChanged (parameters: resultSet) whenever the current ResultSet
		  has been reloaded from the backend; this happens after each commit if the
		  "requery" option of this datasource is in use.
		"""
		if DEBUG: print 'activity_resultset_activated', event.resultSet
		self._revalidate_activities()
		self._revalidate_links()

	def __ds_activity_record_changed(self, event):
		self._revalidate_activities()
		self._revalidate_links()


	#####################################################
	# response to events from DataSource
	#

	def __ds_link_resultset_activated(self, event):
		"""
		- dsResultSetActivated (parameters: resultSet) whenever the current
		  ResultSet of this datasource changes; this happens when a query is
		  executed or when the master of this datasource moves to another record.
		- dsResultSetChanged (parameters: resultSet) whenever the current ResultSet
		  has been reloaded from the backend; this happens after each commit if the
		  "requery" option of this datasource is in use.
		"""
		if DEBUG: print 'link_resultset_activated', event.resultSet
		self._revalidate_links()

	def __ds_link_record_changed(self, event):
		self._revalidate_links()


	#####################################################
	# response to events from UIGant
	#
	def _event_activity_activated(self):
		"""
		User doubleckiked activity, or pressed enter on activity
		"""
		self.processTrigger('RECORD-ACTIVATED')
		self._block_act.processTrigger('RECORD-ACTIVATED')

	def _event_activity_selected(self, id):
		if self._block_act.getField(self.fld_id).get_value() != id:
			self._block_act.find_record({str(self.fld_id) : id})
			pass

	def _rsField(self, field):
		"""returns resultset field name by logical field name"""
		return self._block_act.getField(field).field

	def __on_block_act_post_focusin(__self, self):
		__self.uiWidget._ui_select_activity_(__self._block_act.getField(__self.fld_id).get_value())

	def _is_navigable_(self, mode):
		# TODO: navigable? hidden?
		return True
