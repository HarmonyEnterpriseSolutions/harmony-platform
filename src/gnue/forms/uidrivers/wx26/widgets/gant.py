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
# $Id: gant.py,v 1.5 2009/08/06 15:23:40 oleg Exp $

import wx

from src.gnue.forms.uidrivers.wx26.widgets._base import UIHelper
from toolib.wx.controls.gant import GantView, GantModel

# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================




class UIGant(UIHelper):
	"""
	Implements a menu object.
	"""

	# -------------------------------------------------------------------------
	# Create a menu widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new Menu widget.
		"""
		# Submenu

		self._model = GantModel()
		self.widget = GantView.createScrolledView(event.container, self._model)
		self.getParent().add_widgets(self)

		self.__activities = {}

		self._model.listeners.bind('propertyChanged', self.__onPropertyChanged)

		event.container.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus, self.widget)
		event.container.Bind(wx.EVT_CHAR,      self.__on_char,      self.widget)

	def _ui_set_activities_(self, activities):
		# remove all activities
		#x = 0
		for activity in tuple(self._model):
			activity.remove()
		#	x = 1

		self.__activities.clear()	

		#if x == 1:
		#	return 

		for activity in activities:
			id = activity.pop('id')
			self.__activities[id] = self._model.addActivity(**activity)
			#rint "add activity", self.__activities[id]

		self.widget.Refresh()

	def _ui_set_links_(self, links):
		#def f():
		# remove all links
		for activity in self._model:
			for link in activity.getLinksTo():
				link.remove()
			for link in activity.getLinksFrom():
				link.remove()
		
		#rint 'links', links
		for link in links:
			try:
				activityIdTo   = link.pop('activityTo')
				activityIdFrom = link.pop('activityFrom')
				#rint "add link", self.__activities[activityIdFrom], '-->', self.__activities[activityIdTo]
				self.__activities[activityIdTo].addPredecessor(self.__activities[activityIdFrom], **link)
			except KeyError, e:
				print "! activity not found", e

		self.widget.Refresh()

		#wx.CallAfter(f)

	def is_growable(self):
		return True

	def __onPropertyChanged(self, event):
		if event.propertyName == 'selected' and event.value:
			activity = event.getSource()
			for id, a in self.__activities.iteritems():
				if a == activity:
					self._gfObject._event_activity_selected(id)

	def _ui_select_activity_(self, id):
		if id in self.__activities:
			self.__activities[id].setSelected(True)
		
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
		if event.GetKeyCode() in [wx.WXK_TAB]:
			command, args = GFKeyMapper.KeyMapper.getEvent(
				event.GetKeyCode(),
				event.ShiftDown(),
				event.CmdDown(),
				event.AltDown()
			)

			if command:
				self._request(command, triggerName=args)
				return	# not skip event

		event.Skip()
					

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIGant,
	'provides' : 'GFGant',
	'container': 1,
}
