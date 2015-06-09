# GNU Enterprise Forms - wx 2.6 UI Driver - base class for UI widgets
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
# $Id: _base.py,v 1.14 2013/12/03 19:58:32 Oleg Exp $
"""
Base classes for all UI widgets building the interface layer to the real wx
widgets.
"""

import wx

from gnue.forms.uidrivers._base.widgets._base import UIWidget
from src.gnue.forms.uidrivers.wx26.widgets._config import BORDER_SPACE

__all__ = ['UIHelper', 'ManagedBox']

# =============================================================================
# This class implements the common behaviour of wx 2.6 widgets
# =============================================================================

class UIHelper(UIWidget):
	"""
	Implements the common behaviour of wx 2.6 widgets

	@ivar label: if not None, this is the wx.StaticText instance representing
	    the label for this widget.
	@ivar widget: if not None, this is the instance of a wx.Window subclass
	    representing the control of this widget
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):

		UIWidget.__init__(self, event)

		self.label = None
		self.widget = None


	# -------------------------------------------------------------------------
	# Get the default size
	# -------------------------------------------------------------------------

	def get_default_size(self):
		"""
		Return a wx.Size with the default (starting) size of a widget
		"""
		return wx.DefaultSize


	# -------------------------------------------------------------------------
	# Get the maximum size
	# -------------------------------------------------------------------------

	def get_maximum_size(self):
		"""
		Return a wx.Size with the maximum size of a widget
		"""
		return wx.DefaultSize

	# -------------------------------------------------------------------------
	# Get the length of a widget according to it's GFField
	# -------------------------------------------------------------------------

	def get_field_length(self):
		"""
		Returns the lenght of the bound GFField
		"""

		datatype = self._gfObject._field.datatype

		if datatype == 'datetime':
			result = 19
		elif datatype == 'date':
			result = 10
		elif datatype == 'time':
			result = 8
		else:
			result = self._gfObject._field.length or 0

		return result


	# -------------------------------------------------------------------------
	# Update the size hints of a widget
	# -------------------------------------------------------------------------

	def update_size_hints(self):
		"""
		Descendants will override this method to update the size hints of all
		it's UI widgets.
		"""
		pass


	# -------------------------------------------------------------------------
	# Focus handling
	# -------------------------------------------------------------------------

	def _ui_set_focus_(self):
		#rint "UIHelper: _ui_set_focus_"

		if isinstance(self.widget, wx.ComboBox) and 'wxMac' in wx.PlatformInfo:
			item = self.widget._entry
		else:
			item = self.widget

		#rint "+ SetFocus in UIHelper._ui_set_focus_"
		item.SetFocus()

	# -------------------------------------------------------------------------

	def _ui_focus_in_(self):
		pass

	# -------------------------------------------------------------------------

	def _ui_focus_out_(self):
		pass


	# -------------------------------------------------------------------------
	# Add a widget into a vertical box sizer
	# -------------------------------------------------------------------------

	def add_to_vbox(self, widget, expand=True, flags=0):
		"""
		Add a widget into a vertical BoxSizer so that the widget is surrounded
		by stretchable spacers of the same proportion.  So the widget will be
		centered.

		@param widget: the wx widget to be 'centered'
		@param expand: if True, the widget will expand it's size to fit the
		    available space
		@param flags: additional flags passed to the Add-Method of the sizer

		@returns: the created BoxSizer
		"""
		return self.__add_to_sizer(wx.VERTICAL, widget, expand, flags)


	# -------------------------------------------------------------------------
	# Add a widget to a horizontal box
	# -------------------------------------------------------------------------

	def add_to_hbox(self, widget, expand=True, flags=0):
		"""
		Add a widget into a horizontal BoxSizer so that the widget is
		surrounded by stretchable spacers of the same proportion.  So the
		widget will be centered.

		@param widget: the wx widget to be 'centered'
		@param expand: if True, the widget will expand it's size to fit the
		    available space
		@param flags: additional flags passed to the Add-Method of the sizer

		@returns: the created BoxSizer
		"""
		return self.__add_to_sizer(wx.HORIZONTAL, widget, expand, flags)

	# -------------------------------------------------------------------------

	def __add_to_sizer(self, direction, widget, expand, flags = 0):

		flags |= expand and wx.EXPAND or 0
		sizer = wx.BoxSizer(direction)
		sizer.AddSpacer((0, 0), 1)
		sizer.Add(widget, 0, expand and wx.EXPAND or 0)
		sizer.AddSpacer((0, 0), 1)
		return sizer


	# -------------------------------------------------------------------------
	# Update the choices of a ComboBox or a Listbox
	# -------------------------------------------------------------------------

	def _ui_set_choices_(self, choices):
		"""
		Update the choices of a combo- or listbox widget with the allowed
		values from the associated GFEntry.  The values are alphabetically
		sorted.

		@param choices: alphabetically sorted list of values
		"""

		widget = self.widget

		if isinstance(widget, wx.RadioBox):
			widget.Freeze()
			try:
				enabled = widget.IsEnabled()
				widget.Clear()
				for i, dsc in enumerate(choices):
					widget.Append(dsc)
					widget.EnableItem(i, enabled)
				widget.Enable(enabled)
			finally:
				widget.Thaw()

		elif isinstance(widget, (wx.ComboBox, wx.ListBox)):
			# @oleg: if combo was empty Freezed combo after Thaw has 1 row list height
			#widget.Freeze()
			#try:
			widget.Clear()
			for dsc in choices:
				widget.Append(dsc)
	#finally:
	#    widget.Thaw()
	#    pass


	# -------------------------------------------------------------------------
	# Widget creation
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Create a real wx widget

		@param event: the creation-event instance carrying information like
		    container (parent-widget)

		@returns: the wx widget which should be added to the widget-collection
		"""

		raise NotImplementedError("No implementation for %s (%s)" \
				% (self.__class__, event.container))


	# -------------------------------------------------------------------------
	# Indicate whether this box is vertically growable
	# -------------------------------------------------------------------------

	def is_growable(self):
		return False

	# -------------------------------------------------------------------------
	# Indicate whether this box has fixed width
	# -------------------------------------------------------------------------

	def is_fixedwidth(self):
		return False


	def getAnchor(self):
		return (
			(wx.ALIGN_BOTTOM, wx.ALIGN_CENTER_VERTICAL  , wx.ALIGN_TOP  )[(self.anchor - 1) / 3] |
			(wx.ALIGN_LEFT  , wx.ALIGN_CENTER_HORIZONTAL, wx.ALIGN_RIGHT)[(self.anchor - 1) % 3]
		)

# =============================================================================
# Base class for managed boxes (vbox/hbox)
# =============================================================================

class ManagedBox(UIHelper):
	"""
	A ManagedBox is the base class for all kinds of managed box containers
	(vbox/hbox).  Such a box contains a GridBagSizer with two columns (vbox) or
	two rows (hbox).  The first row/column always contains the labels and the
	second one the entries.  The first row/column will be left away if a box
	has no child using it.

	@cvar _vertical_: orientation of the managed box is vertical (True) or
	    horizontal (False).
	@ivar last_item: the row- or column-number within the GridBagSizer of the
	    last item added.
	@ivar _entry_pos: the row- or column-number which holds the entries or
	    non-label-style child-widgets in general.
	"""

	_vertical_ = True
	last_item  = 0
	_entry_pos = 0

	# -------------------------------------------------------------------------
	# Create the box widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		@param event: the creation-event instance carrying information like
		    container (parent-widget)

		@returns: the container panel
		"""

		self.last_item = 0

		parent = event.container

		# Build the base panel for the managed box.  This panel will be the
		# parent for container-panel of the box (as well as the StaticBoxSizer
		# if a box-label is requested).
		self._container = wx.Panel(parent, -1, style=wx.WANTS_CHARS)
		# FIXME: Why do we need this sizer? Things seem to work the same at
		# least on gtk2 if we assign the GridBagSizer directly to
		# self._container.
		self._container.SetSizer(wx.BoxSizer(wx.VERTICAL))

		# If the has a block assigned we can bind the mouse wheel event to
		# scroll through the block's records.
		if self._gfObject.get_block() is not None:
			self._container.Bind(wx.EVT_MOUSEWHEEL, self.__on_mousewheel)

		# Space between lines is 6 pixels and between columns is 12 pixel
		# according to GNOME Human Interface Guidlines.
		self._sizer = wx.GridBagSizer(BORDER_SPACE/2, BORDER_SPACE)
		# FIXME: If any element within the GridBagSizer has a span > 1, the
		# requested size of this element is distributed *equally* among the
		# cells it spans. So if, for example, a grid is placed in a <vbox>, the
		# label column becomes half as wide as the grid, even if all the labels
		# were far shorter.
		# Possible solution: don't use the GridBagSizer at all, but use a
		# simple vertical BoxSizer with several horiztontal BoxSizers in it,
		# where all labels get a fixed width taken from the width of the
		# longest label.

		self._entry_pos = self.__use_second_one() and 2 or 1

		if self._vertical_:
			self._sizer.AddGrowableCol(self._entry_pos - 1)
		else:
			self._sizer.AddGrowableRow(self._entry_pos - 1)

		# If a label is requested for the box, we have to wrap the container
		# with a StaticBoxSizer.
		if self._gfObject.hasTitledBorder():
			box_title = wx.StaticBox(self._container, -1, self._gfObject.label)
			box = wx.StaticBoxSizer(box_title, wx.VERTICAL)
			# Border inside the box is 6 pixel according to GNOME Human
			# Interface Guidlines.
			box.Add(self._sizer, 1, wx.EXPAND | wx.ALL, 6)

			add = box

			# Add another 6 pixel above and below the box (additionally to the
			# 6 pixel horizontal gap that exist anyway) according to GNOME
			# Human Interface Guidlines.
			border = 6
		else:
			if self._gfObject.label is not None:
				self.label = wx.StaticText(parent, -1, self._gfObject.label)
			add = self._sizer
			# "Invisible" boxes don't need any border.
			border = 0

		self._container.GetSizer().Add(add, 1, wx.EXPAND | wx.TOP | wx.BOTTOM,
			border)

		self.widget = self._container
		self.getParent().add_widgets(self)

		return self._container


	# -------------------------------------------------------------------------
	# Do we need both rows/columns
	# -------------------------------------------------------------------------

	def __use_second_one(self):

		for item in self._children:
			if item._gfObject.hasLabel():
				return True

		return False

	# -------------------------------------------------------------------------
	# Event-Handler
	# -------------------------------------------------------------------------

	def __on_mousewheel(self, event):

		block = self._gfObject.get_block()

		if event.GetWheelRotation() < 0:
			block.next_record()
		else:
			block.prev_record()
