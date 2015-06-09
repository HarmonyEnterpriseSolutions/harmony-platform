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
# $Id: hbox.py,v 1.6 2009/09/07 15:31:38 oleg Exp $
"""
A <hbox> is a visual container in a managed layout.  Children of a hbox are
organized in a horizontal table with two rows, where the first row holds
optional labels and the second one the widgets (or other (v/h)boxes).
"""

import wx

from gnue.forms.uidrivers.wx26.widgets import _base, button

__all__ = ['UIHBox']

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UIHBox (_base.ManagedBox):
	"""
	Implementation of the hbox tag.
	"""

	_vertical_ = False

	# -------------------------------------------------------------------------
	# Add new widgets for a givin UI* instance to the HBox container
	# -------------------------------------------------------------------------

	def add_widgets(self, ui_widget, border=0):
		"""
		Add a given UI widget to the hbox.

		@param ui_widget: widget to add to the page
		"""

		pos = (0, self.last_item)
		span = (1, 1)
		add = False

		if ui_widget.label:
			add = True
			self._sizer.Add(ui_widget.label, pos, span)

		if ui_widget.widget:
			add = True
			pos = (self._entry_pos - 1, self.last_item)
			span = (1, 1)

			item = ui_widget.widget

			flags = wx.EXPAND

			# For (vertically) growable widgets, let them expand.
			if not ui_widget.is_growable():
				# If this is a single-line hbox (with label to the left), align
				# all widgets (vertically) centered, this looks better.
				# We want to expand horizontally, but align vertically. Since
				# wx.EXPAND makes the widget expand to both directions, we must
				# introduce another sizer.
				box = wx.BoxSizer(wx.HORIZONTAL)

				box.Add(item, 1, ui_widget.getAnchor())

				# Otherwise, align widgets on top.
				#box.Add(item, 1, wx.ALIGN_TOP if self._gfObject.hasLabel() else wx.ALIGN_TOP)


				item = box

			#if isinstance(ui_widget, button.UIButton):
			#    item = self.add_to_hbox(item, False)

			self._sizer.Add(item, pos, span, flags)

		# Only columns having a stretch greater than zero require a growable
		# column.  Setting a stretch of 0 breaks the size calculation anyway.
		if add and ui_widget.stretch:
			# FIXME: If a stretch factor is used, the *whole* newly calculated
			# size is distributed according to this stretch factor, instead of
			# only the extra space.
			# self._sizer.AddGrowableCol(self.last_item, ui_widget.stretch)
			self._sizer.AddGrowableCol(self.last_item)

		self.last_item += add


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
	'baseClass': UIHBox,
	'provides' : 'GFHBox',
	'container': 0
}
