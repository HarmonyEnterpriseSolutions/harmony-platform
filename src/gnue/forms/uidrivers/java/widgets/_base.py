# GNU Enterprise Forms - HTML UI Driver - base class for UI widgets
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
# $Id: _base.py,v 1.5 2011/07/14 20:16:12 oleg Exp $

from gnue.forms.uidrivers._base.widgets._base import UIWidget as UIBaseWidget
from gnue.forms.GFObjects import GFEntry

import os
import weakref
		
# =============================================================================
# This class implements the common behaviour of java widgets
# =============================================================================

class UIWidget(UIBaseWidget):

	"""
	Implements the common behaviour of java widgets
	"""

	def __init__(self, event):
		assert event.parent
		UIBaseWidget.__init__(self, event)

		self._inits.append(self.onPostInit)


	def getRemoteHive(self):
		return self._uiDriver

	# -------------------------------------------------------------------------
	# Widget creation
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Create a real RemoteWidget

		@param event: the creation-event instance carrying information like
		    container (parent-widget)

		@returns: RemoteWidget
		"""
		raise NotImplementedError("No implementation for %s (%s)" % (self.__class__, event.container))

	# ---------------------------------------------------------------------------

	def _ui_focus_in_(self):
		# Used only in grid: just ignore it
		pass

	# ---------------------------------------------------------------------------

	def _ui_focus_out_(self):
		# Used only in grid: just ignore it
		pass

	# ---------------------------------------------------------------------------
	# state
	# ---------------------------------------------------------------------------

	def onPostInit(self):
		if isinstance(getattr(self, 'widget', None), Stated):
			self._gfObject._form.associateTrigger('ON-EXIT', self.__on_save_state)
			context = self._uiDriver.getUserContext()
			if context:
				state = context.getUserConfigValue(self._gfObject._uid_())
				if state:
					self.widget.uiSetState(state)

	def __on_save_state(__self, self):
		__self.widget.uiGetState()

	def onGetState(self, state):
		context = self._uiDriver.getUserContext()
		if context:
			try:
				context.setUserConfigValue(self._gfObject._uid_(), state)
			except weakref.ReferenceError:
				# if form closed in On-Activation
				pass

	# ---------------------------------------------------------------------------

from gnue.forms.uidrivers._base.rpc.RemoteObject import RemoteObject

class RemoteWidget(RemoteObject):

	def __init__(self, uiWidget, *args, **kwargs):
		self._uiWidget = uiWidget
		RemoteObject.__init__(self, uiWidget.getRemoteHive(), None, *args, **kwargs)

	def getUiWidget(self):
		return self._uiWidget

class Stated(object):

	def onGetState(self, state):
		self.getUiWidget().onGetState(state)

