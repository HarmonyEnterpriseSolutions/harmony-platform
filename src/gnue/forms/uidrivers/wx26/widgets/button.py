# GNU Enterprise Forms - wx 2.6 UI Driver - Button widget
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
# $Id: button.py,v 1.19 2011/08/25 13:13:20 oleg Exp $

"""
Implementation of the <button> tag
"""

import wx
import os

from gnue.forms.input.GFKeyMapper import KeyMapper
from gnue.forms.uidrivers.wx26.widgets._base import UIHelper
from gnue.common.datatypes.Color import Color

__all__ = ['UIButton']

# =============================================================================
# Wrap an UI layer around a wxButton widget
# =============================================================================

class UIButton(UIHelper):
	"""
	Implements a button object
	"""

	# -------------------------------------------------------------------------
	# Create a button widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new Button widget.
		"""
		owner = self.getParent()

		parent = event.container

		csize = wx.DefaultSize

		# added WANTS_CHARS to accept tab character

		if hasattr(self._gfObject, 'image'):
			path = self._gfObject.image
			if not os.path.isabs(path):
				path = os.path.join(os.path.split(os.path.abspath(self._gfObject._url))[0], path)
			if os.path.exists(path):
				bmp = wx.Image(path).ConvertToBitmap()
				if hasattr(self._gfObject, 'imagemask'):
					bmp.SetMask(wx.Mask(bmp, wx.Colour(*self._gfObject.imagemask.toRGB())))
				self.widget = wx.BitmapButton(parent, -1, bmp, size=csize, style= 4 | wx.WANTS_CHARS)
			else:
				self.widget = wx.Button(parent, -1, "File not found: '%s'" % path, size=csize, style=wx.WANTS_CHARS)
		else:
			self.widget = wx.Button(parent, -1, self._gfObject.label, size=csize, style=wx.WANTS_CHARS)

		tip = self._gfObject.description
		if tip:
			self.widget.SetToolTipString(tip)
		
		self._container = self.widget
		self.widget.Enable(self._gfObject.enabled)

		# caused problem: false press on enter in any editor in block, event table editor
		#if self._gfObject.default:
		#    # can't have more 1 default button on the frame
		#    # so SetDefault is prtialy suitable
		#    self.widget.SetDefault()

		self.__menu = None
		self.__id_to_action = {}

		self.widget.Bind(wx.EVT_BUTTON   , self.__on_button,    self.widget)
		self.widget.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus, self.widget)
		self.widget.Bind(wx.EVT_KEY_DOWN , self.__on_key_down,  self.widget)
		self.widget.Bind(wx.EVT_CHAR     , self.__on_char,      self.widget)

		owner.add_widgets(self)


	# -------------------------------------------------------------------------

	def __on_char (self, event):

		keycode = event.GetKeyCode()

		if keycode == wx.WXK_RETURN:
			self.__on_button(event)
		else:
			# For all other keys ask the keymapper if he could do something
			# usefull
			(command, args) = KeyMapper.getEvent(keycode, event.ShiftDown(), event.CmdDown(), event.AltDown())

			if command:
				self._request(command, triggerName=args)

			else:
				event.Skip()

	# -------------------------------------------------------------------------

	def __on_key_down(self, event):

		# FIXME: Until a button can be flagged as 'Cancel'-Button, which closes
		# a dialog after the user pressed the escape key, we have to 'simulate'
		# that behaviour here.  This event handler can be removed, as soon as
		# such a button is available.  This handler cannot be integrated into
		# EVT_CHAR, since wxMSW does not generate such an event for WXK_ESCAPE
		keycode = event.GetKeyCode()

		if isinstance(self._uiForm.getMainFrame(), wx.Dialog) and keycode == wx.WXK_ESCAPE:
			self._uiForm.getMainFrame().Close()
		else:
			event.Skip()

	# -------------------------------------------------------------------------

	def __on_button (self, event):
		if 'wxMac' in wx.PlatformInfo:
			self._gfObject._event_set_focus()

		self._gfObject._event_fire()

		if self.__menu:
			# show menu
			event.GetEventObject().PopupMenu(self.__menu, (event.GetEventObject().Size[0]-1, 0))

	# -------------------------------------------------------------------------

	def __on_set_focus (self, event):

		self._gfObject._event_set_focus()
		event.Skip()


	# -------------------------------------------------------------------------
	# Enable/disable this button
	# -------------------------------------------------------------------------

	def _ui_enable_(self, enabled):
		self.widget.Enable(enabled)

	def _ui_is_enabled_(self):
		return self.widget.IsEnabled()

	def _ui_set_context_menu_(self, menu, name):
		self.__menu = menu

	def _ui_set_visible_(self, visible):
		self.widget.Show(visible)

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIButton,
	'provides' : 'GFButton',
	'container': 0,
}
