# GNU Enterprise Forms - wx 2.6 UI Driver - MenuItem widget
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
# $Id: menuitem.py,v 1.5 2011/07/01 20:08:23 oleg Exp $

from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import MenuItem

# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================

class UIMenuItem(UIWidget):
	"""
	Implements a menu item object.
	"""

	# -------------------------------------------------------------------------
	# Create a menu item widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new MenuItem widget.
		"""
		if event.container:
			# These are the relevant parameters
			#hotkey = self._gfObject.hotkey

			if self._gfObject.label is not None:

				# it may be (table, tree) or frame
				#uiWidget = self._gfObject.getActionSource().uiWidget

				#if uiWidget._type == 'UIForm':
				#	actionSourceWidget = uiWidget.main_window
				#else:
				#	actionSourceWidget = uiWidget.widget

				#assert actionSourceWidget

				#actionSourceWidget.Bind(wx.EVT_MENU, self.__on_menu, widget)

				widget = MenuItem(self,
					self._gfObject.label, 										# label
					self._uiDriver.getStaticResourceWebPath(
						self._gfObject._get_icon_file(size="16x16", format="png")
					) or '', 	# icon file name
					self._gfObject.action_off is not None,						# is checkbox
				)

				event.container.uiAddMenu(widget)

			else:
				widget = None
				event.container.uiAddSeparator()

			self.widget = widget


	# -------------------------------------------------------------------------
	# Events
	# -------------------------------------------------------------------------

	def onMenu(self, remoteWidget):
		self._gfObject._event_fire()


	# -------------------------------------------------------------------------
	# Check/uncheck menu item
	# -------------------------------------------------------------------------

	def _ui_switch_on_(self):
		if self.widget is not None:	
			self.widget.uiCheck(True)

	# -------------------------------------------------------------------------

	def _ui_switch_off_(self):
		if self.widget is not None:
			self.widget.uiCheck(False)


	# -------------------------------------------------------------------------
	# Enable/disable menu item
	# -------------------------------------------------------------------------

	def _ui_enable_(self, enabled):
		if self.widget is not None:
			self.widget.uiEnable(enabled)

	#def getId(self):
	#	return self.widget.GetId()


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIMenuItem,
	'provides' : 'GFMenuItem',
	'container': False
}
