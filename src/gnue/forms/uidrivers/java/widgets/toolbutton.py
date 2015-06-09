# GNU Enterprise Forms - wx 2.6 UI Driver - ToolButton widget
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
# $Id: toolbutton.py,v 1.3 2009/07/28 17:21:57 oleg Exp $

from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import ToolButton


# =============================================================================
# UIToolButton
# =============================================================================

class UIToolButton(UIWidget):
	"""
	Implements a toolbar button object.
	"""

	# -------------------------------------------------------------------------
	# Create a menu item widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new toolbar button widget.
		"""

		# TODO: helpString = self._gfObject.description
		
		self.__widget = None

		if event.container is not None:	# was not supressed
			if self._gfObject.label is not None:
				self.__widget = ToolButton(self,
					self._gfObject.label,
					self._uiDriver.getStaticResourceWebPath(
						self._gfObject._get_icon_file(size="24x24", format="png")
					),
					self._gfObject.action_off is not None,  # bool toggle
				)
				event.container.uiAddToolButton(self.__widget)
			else:
				event.container.uiAddSeparator()
		
		return self.__widget


	# -------------------------------------------------------------------------
	# Events
	# -------------------------------------------------------------------------

	def onButton(self):
		self._gfObject._event_fire()

	# -------------------------------------------------------------------------
	# Check/uncheck menu item
	# -------------------------------------------------------------------------

	def _ui_switch_on_(self):
		if self.__widget is not None:
			self.__widget.uiCheck(True)

	# -------------------------------------------------------------------------

	def _ui_switch_off_(self):
		if self.__widget is not None:
			self.__widget.uiCheck(False)

	# -------------------------------------------------------------------------
	# Enable/disable menu item
	# -------------------------------------------------------------------------

	def _ui_enable_(self, enabled):
		if self.__widget is not None:
			self.__widget.uiEnable(enabled)


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIToolButton,
	'provides' : 'GFToolButton',
	'container': False
}
