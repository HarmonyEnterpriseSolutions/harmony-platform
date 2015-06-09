# GNU Enterprise Forms - wx 2.6 UI Driver - Box widget
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
# $Id: vbox.py,v 1.9 2009/09/07 15:31:38 oleg Exp $
"""
A <vbox> is a visual container in a managed layout.  Children of a vbox are
organized in a virtual table with two columns, where the first column holds
optional labels and the second one the widgets (or other (v/h)boxes).
"""

import wx

from gnue.forms.uidrivers.wx26.widgets import _base, hbox, button

__all__ = ['UIVBox']

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UIVBox (_base.ManagedBox):
	"""
	Implementation of the vbox tag
	"""

	# -------------------------------------------------------------------------
	# Add an UI widget to the VBox container
	# -------------------------------------------------------------------------

	def add_widgets(self, ui_widget, border=0):
		"""
		Add a given UI widget to the vbox.  The following widgets span both
		columns: vbox, hbox and checkbox-entries.

		@param ui_widget: widget to add to the page
		"""

		if ui_widget.label:

			# For growable widgets (like listboxes and multiline entries), it
			# looks better if the label is aligned to the top.
			if ui_widget.is_growable():
				flags = wx.ALIGN_TOP
			else:
				## workaround to make labels align same as text in readonly entry
				#if getattr(ui_widget._gfObject, 'style', None) == 'label':
				#    flags = wx.ALIGN_TOP
				#else:
				flags = wx.ALIGN_CENTER_VERTICAL
			self._sizer.Add(ui_widget.label, (self.last_item, 0), (1, 1), flags)

		if ui_widget.widget:

			if isinstance(ui_widget, button.UIButton):
				self.add_to_hbox(ui_widget.widget)

			if ui_widget.label:
				pos = (self.last_item, self._entry_pos - 1)
				span = (1, 1)
			else:
				pos = (self.last_item, 0)
				span = (1, 2)

			flags = ui_widget.getAnchor()

			if not ui_widget.is_fixedwidth() and ui_widget.stretch:
				flags |= wx.EXPAND

			if 'wxMac' in wx.PlatformInfo:
				# On OSX we need a little extra space around the widgets to
				# see the shiny focus properly.
				if pos[0] == 0:
					flags |= wx.TOP | wx.RIGHT
				else:
					flags |= wx.RIGHT
				self._sizer.Add(ui_widget.widget, pos, span, flags, 3)
			else:
				self._sizer.Add(ui_widget.widget, pos, span, flags)

		if ui_widget.label or ui_widget.widget:

			if ui_widget.is_growable():
				# FIXME: If a stretch factor is used, the *whole* newly calculated
				# size is distributed according to this stretch factor, instead of
				# only the extra space.
				# self._sizer.AddGrowableRow(self.last_item, ui_widget.stretch)
				self._sizer.AddGrowableRow(self.last_item)

			self.last_item += 1


	# -------------------------------------------------------------------------
	# Indicate whether this box is vertically growable
	# -------------------------------------------------------------------------

	def is_growable(self):

		for child in self._children:
			if child.is_growable():
				return True
		return False


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIVBox,
	'provides' : 'GFVBox',
	'container': 0
}
