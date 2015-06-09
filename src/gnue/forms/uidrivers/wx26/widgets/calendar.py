# -*- coding: Cp1251 -*-
# GNU Enterprise Forms - wx 2.6 UI Driver - Menu widget
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
# $Id: calendar.py,v 1.14 2010/06/16 15:33:42 oleg Exp $

import wx

from src.gnue.forms.uidrivers.wx26.widgets._base import UIHelper
from toolib.wx.controls.calendar.CalendarPanel import CalendarPanel
from toolib.wx.controls.calendar import CalendarModel, CellAttributes
from toolib.wx.controls.calendar.styledtext import StyledTextString
from gnue.forms.input import GFKeyMapper

# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================
class UICalendar(UIHelper):
	"""
	Implements a menu object.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		UIHelper.__init__(self, event)

		self._gfObject._form.associateTrigger('ON-ACTIVATION', self.__on_form_activation)

	# -------------------------------------------------------------------------
	# Create a menu widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new widget.
		"""
		self.widget = CalendarPanel(event.container, -1, style=wx.WANTS_CHARS, model=CalendarModel(getCellFlags=self._getCellFlags, getCellText=self._getCellText, getCellTip=self._getCellTip))
		self.getParent().add_widgets(self)

		self.widget.getCalendar().Bind(wx.EVT_SET_FOCUS, self.__on_set_focus, self.widget.getCalendar())
		self.widget.getCalendar().Bind(wx.EVT_CHAR,      self.__on_char,      self.widget.getCalendar())

		self.widget.getCalendar().Bind(wx.EVT_LEFT_DCLICK, self.__on_left_dclick, self.widget.getCalendar())

		self.widget.getModel().listeners.bind('propertyChanged', self.__onPropertyChanged)

		#wx.CallAfter(lambda: self._gfObject._event_period_changed(self.widget.getModel().getDateStart(), self.widget.getModel().getDateEnd()))
		self.__cellFlags = {}
		
	def __on_form_activation(__self, self):
		# date chane from None to current date
		__self._gfObject._event_period_changed()

	def __onPropertyChanged(self, event):
		if event.propertyName == 'dateStart':
			self._gfObject._event_period_changed()
		elif event.propertyName == 'selection':
			self._gfObject._event_selection_changed()


	def _ui_revalidate_(self, daytype_by_id, daytype_by_date):
		"""
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

		# update calendar attributes
		attributes = self.widget.getCellAttributes()
		for id, daytype in daytype_by_id.iteritems():
			attributes["daytype_%s" % daytype['id']] = CellAttributes(bgColor = daytype['params'].get('bgColor'), textColor=daytype['params'].get('textColor'))

		# update cell flags
		self.__cellFlags.clear()
		for date, daytype in daytype_by_date.iteritems():
			self.__cellFlags[date] = ('daytype_%s' % daytype['id'],)

		# update rules
		self.widget.refresh(full=True)


	def _getCellFlags(self, date):
		return self.__cellFlags.get(date, ())

	def _getCellText(self, date):
		return [str(date.day) + '\n', self._gfObject._event_get_cell_text(date)]

	def _getCellTip(self, date):
		return "%s\n%s" % (date.strftime('%x'), StyledTextString(self._gfObject._event_get_cell_text(date)))

	def _ui_set_date_(self, date):
		self.widget.getModel().setDate(date)

	def _ui_get_date_(self):
		return self.widget.getModel().getDate()

	def _ui_get_period_(self):
		return self.widget.getModel().getDateStart(), self.widget.getModel().getDateEnd()

	def _ui_get_selection_(self):
		return self.widget.getModel().getSelection()

	def is_growable(self):
		return True

	def __on_set_focus(self, event):
		"""
		asquire focus
		"""
		# Let the GF focus follow
		# CallAfter because block not initialized at this time
		wx.CallAfter(self._gfObject._event_set_focus)
		event.Skip()

	def __on_char(self, event):
		"""
		go next/previous entry
		"""
		if event.GetKeyCode() in [wx.WXK_TAB, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
			
			command, args = GFKeyMapper.KeyMapper.getEvent(
				event.GetKeyCode(),
				event.ShiftDown(),
				event.CmdDown(),
				event.AltDown()
			)


			if command:
				if command == 'ENTER':
					self._gfObject._event_day_activated()
				else:
					self._request(command, triggerName=args)
				return	# not skip event

		event.Skip()

	def __on_left_dclick(self, event):
		period, periodType = self.widget.hitTest(event.GetPosition())
		if periodType == 'day':
			date = period[0]
			if date == self.widget.getModel().getDate():
				self._gfObject._event_day_activated()


	def _ui_set_focus_(self):
		self.widget.getCalendar().SetFocus()


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UICalendar,
	'provides' : 'GFCalendar',
	'container': 1,
}
