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
# $Id: GFTimer.py,v 1.2 2012/05/28 15:00:20 oleg Exp $
"""
Timerulated field
"""

import re
from gnue.common.logic.usercode import UserCode
from gnue.forms.GFObjects.GFObj import UnresolvedNameError

__all__ = ['GFTimer']

# =============================================================================
# <total>
# =============================================================================

class GFTimer(UserCode):

	REC_FIELD = re.compile('(?i)([_A-Z][_A-Z0-9]*)\.([_A-Z][_A-Z0-9]*)')

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		UserCode.__init__(self, parent, "GFTimer")
		self._triggerFunctions = {
			'start': {'function': self.start},
			'stop':  {'function': self.stop},
			'run':   {'function': self.run},	# run timer function now
		}
		parent.associateTrigger('ON-EXIT', self.__on_exit)

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _initialize_(self):
		UserCode._initialize_(self)
		self.compile([])

	def __on_exit(__self, self):
		__self.stop()

	def start(self):
		self.uiWidget._ui_start_()
	
	def stop(self):
		self.uiWidget._ui_stop_()

	def _event_timer(self):
		self.run()

