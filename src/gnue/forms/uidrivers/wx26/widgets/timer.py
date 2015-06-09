# GNU Enterprise Forms - wx 2.6 UI Driver - Timer widget
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
# $Id: timer.py,v 1.3 2014/01/29 21:05:44 Oleg Exp $

"""
Implementation of the <Timer> tag
"""

import wx
from gnue.forms.uidrivers.wx26.widgets._base import UIHelper

__all__ = ['UITimer']

# =============================================================================
# Timer
# =============================================================================

class UITimer(UIHelper):
	"""
	Implements a Timer object
	"""
	
	# -------------------------------------------------------------------------
	# Create a Timer widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		self.__timer = wx.Timer(event.container, -1)
		event.container.Bind(wx.EVT_TIMER, self.__on_timer, self.__timer)
		if self._gfObject.autostart:
			self._ui_start_()

	def _ui_start_(self):
		self.__timer.Start(self._gfObject.time, self._gfObject.oneshot)

	def _ui_stop_(self):
		self.__timer.Stop()

	def __on_timer(self, event):
		wx.CallAfter(self._gfObject._event_timer)


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UITimer,
	'provides' : 'GFTimer',
	'container': 0,
}
