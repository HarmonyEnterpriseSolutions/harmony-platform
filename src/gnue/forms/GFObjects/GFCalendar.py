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
Calendar diagram
"""

import re

from src.gnue.forms.GFObjects import GFTabStop

REC_FIELD = re.compile(r"\%(\([A-Za-z_]\w*\))")
DEBUG=0



class GFCalendar(GFTabStop):
	"""
	"""


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		"""
		"""

		GFTabStop.__init__(self, parent, self.__class__.__name__)

		self._block = None

		# triggers
		self._validTriggers = {
			'PRE-FOCUSOUT'     : 'Pre-FocusOut',
			'POST-FOCUSOUT'    : 'Post-FocusOut',
			'PRE-FOCUSIN'      : 'Pre-FocusIn',
			'POST-FOCUSIN'     : 'Post-FocusIn',
			'ON-NEXT-ENTRY'    : 'On-Next-Entry',
			'ON-PREVIOUS-ENTRY': 'On-Previous-Entry',

			'PERIOD-CHANGED'    : 'Period-Changed',
			'SELECTION-CHANGED' : 'Selection-Changed',
			'GET-CELL-TEXT'     : 'Get-Cell-Text',
			'DAY-ACTIVATED'     : 'Day-Activated',
		}

		self._triggerFunctions = {
			'getBlock'         : {'function': self.__trigger_getBlock},
			'setDate'          : {'function': self.setDate},
			'getSelection'     : {'function': self.getSelection},

			'getDate'          : {'function': self.getDate},
			'getPeriod'        : {'function': self.getPeriod},

			# functions to communicate with trigger generating cell text
			'getCellParameters'   : {'function': self.__trigger_getCellParameters},
			'setCellText'      : {'function': self.__trigger_setCellText},
		}

		self._triggerProperties = {
		}

		self.__cellParameters = None
		self.__cellText = None

		self.__rules_by_date = {}
		self.__daytype_by_date = {}


	def __trigger_getBlock(self):
		return self._block.get_namespace_object()

	def __trigger_getCellParameters(self):
		return self.__cellParameters

	def __trigger_setCellText(self, cellText):
		self.__cellText = cellText

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		super(GFCalendar, self)._phase_1_init_()

		# calendar is not GFFieldBound
		self._block = self._form._logic.getBlock(self.block)

		# Register event handling functions
		self._block.getDataSource().registerEventListeners({
			'dsResultSetActivated': self.__ds_resultset_activated,  # from datasources.GDataSource
			'dsResultSetChanged'  : self.__ds_resultset_activated,  # -/-

			#'dsRecordLoaded'      : self.__ds_record_loaded,		# from datasources.drivers.Base.Record
			#'dsRecordInserted'    : self.__ds_record_inserted,		# -/-
			#'dsRecordTouched'     : self.__ds_record_touched,		# -/-
			'dsRecordChanged'     : self.__ds_record_changed,		# -/-

			#'dsCommitInsert'      : self.__ds_commit_insert,		# -/-
			#'dsCommitUpdate'      : self.__ds_commit_update,		# -/-
			#'dsCommitDelete'      : self.__ds_commit_delete,		# -/-
		})


	##################################################################
	# Validation
	#
	def _revalidate(self):
		"""
		rules_by_date is {
			date : [<rule>, ...]
		}

		where <rule> is {
			'_daytype_' : <daytype>,
			<all other data from block row iterator>
		}

		daytype_by_id is {
			id : <daytype>,
		}

		daytype_by_date is {
			date : <daytype>,
		}

		where <daytype> is {
			'id'          : <daytype id>,
			'description' : <daytype description>,
			'params'      : <evaludated params>,
		}
		"""

		daytype_by_id = {}

		self.__rules_by_date.clear()
		self.__daytype_by_date.clear()

		for row in self._block.iterRecords():

			date       = row[self.fld_date]
			daytype_id = row[self.fld_daytype_id]
			
			if daytype_id is not None:

				if daytype_id not in daytype_by_id:
					daytype_by_id[daytype_id] = daytype = {}
					daytype['id']          = daytype_id
					daytype['description'] = row[self.fld_daytype_description]
					try:
						daytype['params'] = eval(row[self.fld_daytype_params])
					except:
						daytype['params'] = {}

				self.__daytype_by_date[date] = daytype_by_id[daytype_id]

				#rule['_daytype_'] = daytype_by_id[daytype_id]
			else:
				if date not in self.__rules_by_date:
					self.__rules_by_date[date] = []
				self.__rules_by_date[date].append(row.copy())

		self.uiWidget._ui_revalidate_(daytype_by_id, self.__daytype_by_date)


	#####################################################
	# response to events from cal_by_date DataSource
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
		if DEBUG: print 'day_type_resultset_activated', event.resultSet
		self._revalidate()

	def __ds_record_changed(self, event):
		self._revalidate()


	#####################################################
	# response to events from UICalendar
	#
	def _event_day_activated(self):
		"""
		User doubleckiked day_type, or pressed enter on day_type
		"""
		self.processTrigger('DAY-ACTIVATED')
		self._block.processTrigger('RECORD-ACTIVATED')

	def setDate(self, date):
		self.uiWidget._ui_set_date_(date)

	def _is_navigable_(self, mode):
		# TODO: navigable? hidden?
		return True

	def _event_period_changed(self):
		self.processTrigger('PERIOD-CHANGED')

	def _event_selection_changed(self):
		self.processTrigger('SELECTION-CHANGED')

	def getDate(self):
		return self.uiWidget._ui_get_date_()

	def getPeriod(self):
		return self.uiWidget._ui_get_period_()

	def getSelection(self):
		return self.uiWidget._ui_get_selection_()

	def _event_get_cell_text(self, date):
		try:
			self.__cellParameters = self.__rules_by_date.get(date, ()), self.__daytype_by_date.get(date)
			self.processTrigger('GET-CELL-TEXT')
			return self.__cellText
		finally:
			self.__cellText = None
			self.__cellParameters = None
