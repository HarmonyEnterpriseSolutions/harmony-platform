# GNU Enterprise Forms - wx 2.6 UI Driver - Entry widgets
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
# $Id: entry.py,v 1.77 2015/03/12 17:39:28 oleg Exp $
"""
Implementation of the <entry> tag
"""

import wx

from gnue.common.apps import errors
from gnue.forms.uidrivers.wx26.widgets import _base
from gnue.forms.input import GFKeyMapper
from gnue.forms.input.GFKeyMapper import vk
from toolib.wx.controls.RadioBox import RadioBox
from toolib.wx.controls.DateControl import DateControl
from toolib.wx.controls.PopupControl import PopupControl
from toolib.wx.controls.TextCtrlWithButtons import TextCtrlWithButtons

from wx.lib.masked import TextCtrl, BaseMaskedTextCtrl
from toolib.wx.controls.NumCtrl import NumCtrl
from src.gnue.forms.uidrivers.wx26.widgets._controls import RichText

__all__ = ['UIEntry']

# =============================================================================
# Interface class for entry widgets
# =============================================================================

class UIEntry (_base.UIHelper):
	"""
	Interface implementation for entry widgets.
	"""

	# -------------------------------------------------------------------------
	# Create the real wx widget
	# -------------------------------------------------------------------------

	def _create_widget_ (self, event):
		"""
		Create the wx widget. The actual creation will be dispatched to a
		method called '__build_<style>' depending on the object's style.
		"""

		style = self._gfObject.style.lower()
		func = getattr(self, "_UIEntry__build_%s" % style)
		self.__border = 0
		self.label, self.widget = func(event.container)

	    # han have buttons now
		self._container = self.widget

		tip = self._gfObject.getDescription()
		if tip:
			self.widget.SetToolTipString(tip)

		self.getParent().add_widgets(self, self.__border)



	# -------------------------------------------------------------------------
	# Widget construction methods
	# -------------------------------------------------------------------------

	def __build_default(self, parent, password=False, multiline=False, label = False):

		csize = self.get_default_size()

		field = self._gfObject._field

		xFlags = wx.TE_PROCESS_TAB
		if label:
			xFlags |= wx.TE_READONLY # | wx.NO_BORDER

		if field.datatype == 'number':

			xFlags |= wx.TE_PROCESS_ENTER

			minimum = eval(field.min, {})
			maximum = eval(field.max, {})

			ctrl = NumCtrl(parent, -1, size=csize,
				style         = xFlags,

				allowNone     = not field.required,
				fractionWidth = field.scale,
				integerWidth  = (field.length or field.DEFAULT_LENGTH) - field.scale,
				groupDigits   = field.groupDigits,
				min           = minimum,
				max           = maximum,
				allowNegative = minimum is None or minimum < 0, # can't until masked bug with backspace is fixed
				#limited       = True,  # bugs with '-'
			)

		elif self._gfObject.getInputMask() and '#' in self._gfObject.getInputMask():
		 
			xFlags |= wx.TE_PROCESS_ENTER
		 
			ctrl = TextCtrl(parent, -1, size=csize,
				style = xFlags,
				mask  = self._gfObject.getInputMask(),
				raiseOnInvalidPaste = False,
			)

		else:
			if password:
				xFlags |= wx.TE_PASSWORD

			if multiline:
				xFlags |= wx.TE_MULTILINE
			else:
				xFlags |= wx.TE_PROCESS_ENTER

			ctrl = wx.TextCtrl(parent, -1, size=csize, style=xFlags)

		if label:
			colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
			if isinstance(ctrl, BaseMaskedTextCtrl):
				# this sets null value to zero :(
				#ctrl.SetParameters(emptyBackgroundColour = colour, validBackgroundColour = colour)
				# so we hack
				ctrl._emptyBackgroundColour = colour
				ctrl._validBackgroundColour = colour

			ctrl.SetBackgroundColour(colour)

			font = ctrl.Font
			font.Weight = wx.FONTWEIGHT_BOLD
			ctrl.Font = font

		ctrl.Bind(wx.EVT_CHAR, self.__on_keypress)
		ctrl.Bind(wx.EVT_TEXT, self.__on_text_changed)
		ctrl.Bind(wx.EVT_KEY_DOWN, self.__on_key_down)      # fix for ESC in dialogs
		ctrl.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus)

		return [self.__add_entry_label(parent), ctrl]

	# -------------------------------------------------------------------------

	def __build_password(self, parent):

		return self.__build_default(parent, True)

	# -------------------------------------------------------------------------

	def __build_multiline(self, parent):

		return self.__build_default(parent, multiline=True)

	# -------------------------------------------------------------------------

	def __build_label(self, parent):
		return self.__build_default(parent, label=True)

	# -------------------------------------------------------------------------

	def __build_checkbox (self, parent):

		if self._gfObject.isCellEditor():	# ok
			label = ""
		else:
			label = self._gfObject.label or ''

		result = wx.CheckBox (parent, -1, label,
			style=wx.CHK_3STATE | wx.WANTS_CHARS)

		result.Bind (wx.EVT_CHECKBOX, self.__on_toggle_checkbox)

		result.Bind (wx.EVT_CHAR, self.__on_keypress)
		result.Bind (wx.EVT_KEY_DOWN, self.__on_key_down)
		result.Bind (wx.EVT_SET_FOCUS, self.__on_set_focus)

		return [None, result]

	def __build_bitcheckbox (self, parent):
		return self.__build_checkbox(parent)

	# -------------------------------------------------------------------------

	def __build_dropdown(self, parent):

		csize = self.get_default_size()
		result = wx.ComboBox(parent, -1, size=csize, style=wx.CB_DROPDOWN |
			wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER)

		# On wxMac a Combobox is a container holding a TextCtrl and a Choice.
		# We have to bind the Focus- and Char-Events to the TextCtrl widget.
		if 'wxMac' in wx.PlatformInfo:
			for child in result.GetChildren():
				if isinstance(child, wx.TextCtrl):
					textControl = child
				elif isinstance(child, wx.Choice):
					child.Bind(wx.EVT_LEFT_DOWN, self.__on_mac_choice_clicked)
		else:
			textControl = result

		result.Bind(wx.EVT_TEXT, self.__on_text_changed)

		textControl.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus)
		textControl.Bind(wx.EVT_KEY_DOWN, self.__on_combo_keydown)

		#if 'wxMSW' in wx.PlatformInfo:
		#    textControl.Bind(wx.EVT_MOUSEWHEEL, self.__on_cbx_wheel)

		return [self.__add_entry_label(parent), result]

	# -------------------------------------------------------------------------

	def __build_radiobox(self, parent):

		csize = (self.get_default_size()[0], -1)

		#self.__border = self._uiDriver.control_border('default')

		itemCount = self._gfObject.maxitems

		result = RadioBox(parent, -1,
			label = self._gfObject.label or '',
			size = csize,
			choices = [" "] * itemCount,
			majorDimension = self._gfObject.maxitems,
			style = wx.RA_SPECIFY_COLS
		)

		result.Bind(wx.EVT_RADIOBOX, self.__on_item_selected)
		result.Bind(wx.EVT_KEY_DOWN, self.__on_key_down)
		result.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus)

		return [None, result]

	# -------------------------------------------------------------------------

	def __build_radiobutton(self, parent):

		csize = (self.get_default_size()[0], -1)

		#self.__border = self._uiDriver.control_border('default')

		#style = wx.WANTS_CHARS & 0
		#if self._gfObject.radiobutton_group:
		#   style |= wx.RB_GROUP

		if 1:
			result = wx.RadioButton (parent, -1,
				# TODO: NO AFFECT FROM LABEL
				self._gfObject.label or '',
				size = csize,
				style = wx.WANTS_CHARS | wx.RB_SINGLE,
			)
			result.Bind(wx.EVT_RADIOBUTTON, self.__on_radiobutton)
		else:
			result = wx.CheckBox (parent, -1, self._gfObject.label or '',
				style=wx.WANTS_CHARS)

			result.Bind (wx.EVT_CHECKBOX, self.__on_radiobutton)

		result.Bind(wx.EVT_KEY_DOWN, self.__on_key_down)
		result.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus)
		result.Bind(wx.EVT_CHAR, self.__on_keypress)

		return [None, result]

	# -------------------------------------------------------------------------

	def __build_datepicker(self, parent):
		return self.__build_picker(parent,
			DateControl(parent, -1,
				style = wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER,
				format = self._gfObject._displayHandler._input_mask
			)
		)

	# -------------------------------------------------------------------------

	def __build_text_with_buttons(self, parent):
		control = TextCtrlWithButtons(parent, -1,
			style = wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER
		)
		return self.__build_picker(parent, control)

	def add_widgets(self, button):
		self.widget.addButton(button.widget)
		
	# -------------------------------------------------------------------------

	def __build_picker_with_editor(self, parent):
		label, ctrl = self.__build_picker(parent, editor=True)
		ctrl.popupListeners.bind('onEdit', lambda event: self._gfObject._event_on_custom_editor())
		return label, ctrl

	def __build_picker(self, parent, ctrl=None, editor=False):
		#csize = (self.get_default_size()[0], 1)
		if ctrl is None:
			ctrl = GenericPicker(parent, -1,
				#size  = csize,
				style = wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER,
				popupModal = False,
				uiEntry = self,
				editorButton = editor,
			)

		# wrap all events from popup controls embeded
		# text control into DateControl.EventWrapper so GetEventObject()
		# will return PopupControl instead text control
		tc = ctrl.GetTextControl()

		tc.Bind(wx.EVT_TEXT,      lambda event: self.__on_text_changed(ctrl.EventWrapper(event)))
		tc.Bind(wx.EVT_CHAR,      lambda event: self.__on_keypress    (ctrl.EventWrapper(event)))
		tc.Bind(wx.EVT_KEY_DOWN,  lambda event: self.__on_key_down    (ctrl.EventWrapper(event)))
		tc.Bind(wx.EVT_SET_FOCUS, lambda event: self.__on_set_focus   (ctrl.EventWrapper(event)))

		return [self.__add_entry_label(parent), ctrl]

	# -------------------------------------------------------------------------

	def __build_listbox(self, parent):

		# NOTE: please have a look at the note on multiline text edits above
		csize = (self.get_default_size()[0], -1)
		self.__border = self._uiDriver.control_border('default')

		result = wx.ListBox(parent, -1, size=csize, style=wx.LB_SINGLE)

		result.Bind(wx.EVT_LISTBOX, self.__on_item_selected)
		result.Bind(wx.EVT_KEY_DOWN, self.__on_key_down)
		result.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus)

		return [self.__add_entry_label(parent), result]

	# -------------------------------------------------------------------------

	def __build_richedit(self, parent):

		import wx.richtext

		ctrl = RichText(parent)

		ctrl.richtext.Bind(wx.EVT_CHAR, self.__on_keypress)
		ctrl.richtext.Bind(wx.EVT_TEXT, self.__on_richtext_changed)
		ctrl.richtext.Bind(wx.richtext.EVT_RICHTEXT_STYLE_CHANGED, self.__on_richtext_changed)
		ctrl.richtext.Bind(wx.EVT_KEY_DOWN, self.__on_key_down)      # fix for ESC in dialogs
		ctrl.richtext.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus)

		return [self.__add_entry_label(parent), ctrl]

	# -------------------------------------------------------------------------
	def __add_entry_label(self, parent):

		if self._gfObject.label:
			# Replace blanks by non-breaking space to avoid random linebreaks
			# in labels (sometimes done by wx, probably due to rounding errors
			# in size calculations)
			text = self._gfObject.label.replace(u" ", u"\240")
			label = wx.StaticText(parent, -1, text)
		else:
			label = None

		return label


	# -------------------------------------------------------------------------

	def __on_set_focus(self, event):
		self._gfObject._event_set_focus()
		event.Skip()

	# -------------------------------------------------------------------------

	def __on_mac_choice_clicked(self, event):

		for child in event.GetEventObject().GetParent().GetChildren():
			if isinstance(child, wx.TextCtrl):
				child.SetFocus()
				break

		self._gfObject._event_set_focus()
		event.Skip()


	# -------------------------------------------------------------------------

	def __on_toggle_checkbox(self, event):

		if self._gfObject.style == 'bitcheckbox':
			self._request('TOGGLEBIT', activate_value=self._gfObject.activate_value)
		else:
			self._request('TOGGLECHKBOX')

	# -------------------------------------------------------------------------

	def __on_item_selected(self, event):

		self._request('REPLACEVALUE', index=event.GetSelection(),
			text=event.GetString())

	# -------------------------------------------------------------------------

	def __on_radiobutton(self, event):
		if self._gfObject._field.datatype == 'boolean':
			activate_value = self._gfObject._displayHandler.parse_display(self._gfObject.activate_value)
			if activate_value != self._gfObject._field.get_value():
				# CallAfter fixes #465
				wx.CallAfter(self._request, 'TOGGLECHKBOX')
		else:
			wx.CallAfter(self._request, 'REPLACEVALUE', text=self._gfObject.activate_value)

	# -------------------------------------------------------------------------
	def __on_text_changed(self, event):

		widget = event.GetEventObject()

		if isinstance(widget, BaseMaskedTextCtrl):
			if not self._gfObject.isCellEditor():	# ok
				# set value directly, do not use displayHandler
				self._gfObject._field.set_value(self._ui_get_value_() or None)
		else:
			text = widget.GetValue()

			# ComboBox GetSelection is overrided with wxControlWithItems::GetSelection
			# So use GetStringSelection to detect full selection
			# TODO: text must be selected after combobox selection
			if isinstance(widget, wx.ComboBox) and widget.GetStringSelection() == text:
				# all is selected
				position = len(text)
			else:
				position = widget.GetInsertionPoint()
			wx.CallAfter(self._request, 'REPLACEVALUE', text=text, position=position)

	def __on_richtext_changed(self, event):
		# set value directly, do not use displayHandler
		self._gfObject._field.set_value(event.GetEventObject().GetValue() or None)


	def _ui_get_text_(self):
		return self._ui_get_value_()

	def _ui_set_text_(self, text):
		wx.CallAfter(self._request, 'REPLACEVALUE', text=text, position=len(text), force=True)

	# -------------------------------------------------------------------------

	def __on_key_down(self, event):

		# FIXME: Until a button can be flagged as 'Cancel'-Button, which closes
		# a dialog after the user pressed the escape key, we have to 'simulate'
		# that behaviour here.  This event handler can be removed, as soon as
		# such a button is available.  This event cannot be integrated into
		# EVT_CHAR since wxMSW does not generate such an event for WXK_ESCAPE.
		keycode = event.GetKeyCode()

		if keycode == wx.WXK_ESCAPE:
			if isinstance(self._uiForm.getMainFrame(), wx.Dialog):
				self._uiForm.getMainFrame().Close()
				return
			else:
				nd = self._gfObject.getNavigationDelegate()
				if nd and not nd.isNavigationDelegationEnabled():
					if nd.escapeEntry(self._gfObject):
						return
		event.Skip()


	# -------------------------------------------------------------------------

	def __on_keypress(self, event):

		#rint "entry __on_keypress: code=", event.GetKeyCode()

		# disable any key navigation when entry in editor mode
		if self._gfObject.isCellEditor():	# ok
			event.Skip()
			return

		keycode = event.GetKeyCode()

		if keycode == wx.WXK_RETURN and not self._gfObject.isCellEditor():	# ok
			if self._gfObject._event_push_default_button():
				#rint 'default button accepted', self.widget
				return
			else:
				#rint 'default button not found', self.widget
				pass

		if keycode == wx.WXK_RETURN and self._gfObject.style == 'richedit':
			event.Skip()
			return
		
		is_cmd = keycode in [wx.WXK_TAB, wx.WXK_RETURN, wx.WXK_UP, wx.WXK_DOWN, wx.WXK_ESCAPE]
		command = None

		# Prevent up- and down-keys for multiline text controls from being
		# interpreted as record-navigation-keys.
		wxctrl = event.GetEventObject()
		if isinstance(wxctrl, wx.TextCtrl) and wxctrl.IsMultiLine() \
			and (keycode in [wx.WXK_RETURN, wx.WXK_UP, wx.WXK_DOWN]):
			is_cmd = False

		if is_cmd:
			(command, args) = GFKeyMapper.KeyMapper.getEvent(keycode,
				event.ShiftDown(),
				event.CmdDown(),
				event.AltDown())

		# MaskedTextCtrl has its own tab handling
		if isinstance(wxctrl, BaseMaskedTextCtrl) and command in ('NEXTENTRY', 'PREVENTRY'):

			# here is masked ctrl internal members used
			# TODO: find the way with external interface
			field = wxctrl._FindField(wxctrl._GetInsertionPoint())
			if (
				# NEXTENTRY and not standing in last field
				command == 'NEXTENTRY' and field != wxctrl._fields[max(wxctrl._fields.keys())]
				# PREVENTRY and not standing in first field
				or command == 'PREVENTRY' and field != wxctrl._fields[0]
			):
				command = None

		if command:
			if command == 'NEWLINE':
				self._request('KEYPRESS', text='\n')
			else:
				self._request(command, triggerName=args)
		else:
			event.Skip()


	# -------------------------------------------------------------------------

	def __on_combo_keydown(self, event):

		keycode = event.GetKeyCode()
		command = None

		# FIXME: Until a button can be flagged as 'Cancel'-Button, which closes
		# a dialog after the user pressed the escape key, we have to 'simulate'
		# that behaviour here.
		if isinstance(self._uiForm.getMainFrame(), wx.Dialog) and keycode == wx.WXK_ESCAPE:
			self._uiForm.getMainFrame().Close()
			return

		allowed = [wx.WXK_RETURN, wx.WXK_TAB]

		if keycode in allowed:
			(command, args) = GFKeyMapper.KeyMapper.getEvent (keycode,
				event.ShiftDown(),
				event.CmdDown(),
				event.AltDown())

		if command:
			self._request(command, triggerName=args)
		else:
			event.Skip()

	# -------------------------------------------------------------------------

	#def __on_cbx_wheel(self, event):
	#
	#    # On wx.MSW we stop the propagation of a mouse wheel event here, to
	#    # prevent it from changing options in dropdowns
	#    event.StopPropagation()


	# -------------------------------------------------------------------------
	# Enable/disable this entry
	# -------------------------------------------------------------------------

	def _ui_enable_(self, enabled):
		self.widget.Enable(enabled)

	# -------------------------------------------------------------------------
	# Set "editable" status for this widget
	# -------------------------------------------------------------------------

	def _ui_set_editable_(self, editable):
		#rint "_ui_set_editable_", self._gfObject._field.name, editable

		# entries with label style is never editable
		if self._gfObject.style == 'label':
			return

		ctrl = self.widget

		if isinstance(ctrl, (wx.CheckBox, wx.RadioButton, RadioBox)):
			ctrl.Enable(editable)
		else:
			# Simple text controls can be explicitly set to non-editable, so they
			# don't accept keyboard input.
			if isinstance(ctrl, (wx.TextCtrl, wx.ComboBox)):
				ctrl.SetEditable(editable)

			elif isinstance(ctrl, PopupControl):
				ctrl.SetEditable(editable)
				# disable popup button unless popup window have parameter popupReadonly='Y'
				popupWindow = self._gfObject.findChildOfType('GFPopupWindow', includeSelf=False)
				if popupWindow is None or not popupWindow.popupReadonly:
					ctrl.EnableButton(editable, 'popup') #and ctrl.GetButton('popup').IsEnabled()
			
			if editable:
				if 'wxMSW' in wx.PlatformInfo and isinstance(ctrl, wx.ComboBox):
					colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
				else:
					colour = wx.NullColour
			else:
				colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)

			# We set the background color to grey for all kinds of widgets if they
			# are not editable, so the user can see some difference.
			if not 'wxMac' in wx.PlatformInfo:
				if isinstance(ctrl, BaseMaskedTextCtrl):
					# numctrl with decimal point can't hold None :(
					# this sets zero to numctrl :(
					#ctrl.SetCtrlParameters(emptyBackgroundColour = colour, validBackgroundColour = colour)
					# so we need to hack
					# TODO: implement masked control
					ctrl._emptyBackgroundColour = colour
					ctrl._validBackgroundColour = colour

				ctrl.SetBackgroundColour(colour)
				ctrl.Refresh()

	def _ui_set_visible_(self, visible):
		self.widget.Show(visible)

	# -------------------------------------------------------------------------
	# Get the value of a widget
	# -------------------------------------------------------------------------

	def _ui_get_value_(self):
		"""
		returns widget display value
		this value must be able to set with _ui_set_value_
		field.set_value must take it

		not exposed to GF layer, used inside driver
		"""

		if isinstance(self.widget, NumCtrl):
			# to avoid float conversion
			# used lib.masked internal _GetNumValue convertor that produces -###.## value
			return self.widget._GetNumValue(wx.TextCtrl.GetValue(self.widget))
		elif isinstance(self.widget, TextCtrl):  # masked TextCtrl
			#return widget.GetPlainValue()
			return self.widget.GetValue()
		else:
			return self.widget.GetValue()

	# -------------------------------------------------------------------------
	# Set the value of a widget
	# -------------------------------------------------------------------------

	def _ui_set_value_(self, value):
		"""
		This function sets the value of a widget and optionally enables or
		disables the widget.
		"""
		widget = self.widget

		if not widget:
			return

		widget.SetEvtHandlerEnabled(False)

		try:
			if isinstance(widget, wx.StaticText):
				widget.SetLabel(value)

			elif isinstance(widget, wx.ListBox):
				# TODO: We must allow setting the value to None, too, to be
				# able to move the cursor to the empty position at the start.
				# Must be tested under windows and Mac OS X.
				#
				# On wxMSW SetStringSelection() does not work properly with
				# empty values.
				index = widget.FindString(value)
				if index == -1:
					widget.SetSelection(wx.NOT_FOUND)
				else:
					widget.SetSelection(index)

			elif isinstance(widget, (wx.RadioButton, wx.CheckBox)) and self._gfObject.style == 'radiobutton':
				if self._gfObject._field.datatype == 'boolean':
					activate_value = self._gfObject._displayHandler.parse_display(self._gfObject.activate_value)
				else:
					activate_value = self._gfObject.activate_value
				widget.SetValue(value == activate_value)

			elif isinstance(widget, wx.CheckBox):
				if self._gfObject.style == 'bitcheckbox':
					widget.SetValue(int(value or '0', 2) & int(self._gfObject.activate_value, 2))
				else:
					if value is None:
						widget.Set3StateValue(wx.CHK_UNDETERMINED)
					elif value:
						widget.Set3StateValue(wx.CHK_CHECKED)
					else:
						widget.Set3StateValue(wx.CHK_UNCHECKED)


			elif isinstance(widget, wx.ComboBox):
				# We use SetStringSelection to keep the selected index in sync
				# with the string value (e.g. in Choice-Controls on OS X)
				if not widget.SetStringSelection(value):
					widget.SetValue(value)
			elif isinstance(widget, NumCtrl):
				# convert value to format "123456.78", accepted by NumCtrl
				v = self._gfObject._displayHandler.parse_display(value)
				if v is not None:
					v = str(v)

					# truncate value to avoid error that integer value part not fits
					# do it only if field is NEVER editable 
					if self._gfObject._field.editable.upper() == 'N':
						parts = v.split('.')
						n = len(parts[0])
						if n > widget.GetIntegerWidth():
							parts[0] = parts[0][n-widget.GetIntegerWidth():]
							v = '.'.join(parts)
							if widget._foregroundColour != wx.RED:
								widget._foregroundColour = wx.RED
								widget.Refresh()
						else:
							if widget._foregroundColour is not None:
								widget._foregroundColour = None
								widget.Refresh()

				try:
					widget.SetValue(v)
				except ValueError, e:
					if 'exceeds the integer width of the control' in str(e):
						raise errors.UserError(_(u'Value %s exceeds the integer width of the control') % v)
					else:
						raise

			elif isinstance(widget, TextCtrl):
				try:
					widget.SetValue(value)
				except ValueError, e:
					print "! Field %s.%s: Value '%s' not fits into inputmask '%s'" % (self._gfObject._block.name, self._gfObject._field.name, value, self._gfObject.getInputMask())
			else:
				widget.SetValue(value)

			#if self._gfObject.picker_text_minlength >= 0 and self._gfObject.style in ('picker', 'picker_with_editor'):
			#	widget.EnableButton(len(value) > self._gfObject.picker_text_minlength)

		finally:
			widget.SetEvtHandlerEnabled(True)
			widget.Refresh()


	# ------------------------------------------------------------------------
	# Set cursor position and selection inside a widget
	# ------------------------------------------------------------------------

	def _ui_set_selected_area_(self, selectionStart, selectionEnd):
		"""
		Set the cursor position to the selectionEnd inside a capable widget.
		Sets the selection start/end inside a capable widget.

		@param selectionStart: start position of the selection
		@param selectionEnd: end position of the selection
		"""

		widget = self.widget

		if selectionStart == selectionEnd:

			if isinstance (widget, wx.ComboBox):
				widget.SetMark(selectionEnd, selectionEnd)

			elif isinstance (widget, BaseMaskedTextCtrl):
				pass

			elif hasattr (widget, 'SetInsertionPoint'):
				widget.SetInsertionPoint(selectionEnd)

		else:

			if isinstance(widget, wx.ComboBox):
				widget.SetMark(selectionStart, selectionEnd)

			elif isinstance(widget, (wx.ListBox, wx.RadioBox)):
				# listbox and radiobox cant set selection but have method with same name
				pass

			elif isinstance(widget, BaseMaskedTextCtrl):
				self._ui_select_all_()

			elif hasattr(widget, 'SetSelection'):
				if 'wxGTK' in wx.PlatformInfo:
					wx.CallAfter(widget.SetSelection, selectionStart, selectionEnd)
				else:
					# Workaround for wxMSW: if a multiline text entry has more than
					# on line of text, SetSelection() does not work properly.
					if 'wxMSW' in wx.PlatformInfo and selectionStart == 0 \
						and hasattr(widget, 'GetValue') \
						and len(widget.GetValue()) == selectionEnd:
						selectionStart = selectionEnd = -1

					widget.SetSelection(selectionStart, selectionEnd)


	# -------------------------------------------------------------------------
	# Clipboard and selection
	# -------------------------------------------------------------------------

	def _ui_cut_(self):

		widget = self.widget

		if hasattr(widget, 'Cut'):
			widget.Cut()

	# -------------------------------------------------------------------------

	def _ui_copy_(self):

		widget = self.widget

		if hasattr(widget, 'Copy'):
			widget.Copy()

	# -------------------------------------------------------------------------

	def _ui_paste_(self):

		widget = self.widget

		if hasattr(widget, 'Paste'):
			widget.Paste()

	# -------------------------------------------------------------------------

	def _ui_select_all_(self):

		widget = self.widget

		if hasattr(widget, 'SetMark'):
			widget.SetMark(0, len(widget.GetValue()))

		elif isinstance(widget, BaseMaskedTextCtrl):
			wx.CallAfter(widget.SetSelection, *widget._fields[0]._extent)

		elif hasattr(widget, 'SetSelection'):
			widget.SetSelection(-1, -1)


	# -------------------------------------------------------------------------
	# Get the default size
	# -------------------------------------------------------------------------

	def get_default_size(self):
		"""
		Return a wx.Size with the default (starting) size of a widget
		"""
		cellw = self._uiDriver.cellWidth
		cellh = self._uiDriver.cellHeight

		style = self._gfObject.style.lower()
		if style == 'password':
			style = 'default'

		bw, bh = self._uiDriver.best_sizes.get(style, (-1, -1))

		deffield = self.get_field_length()
		# Do not exceed either the maximum allowed or 64 characters
		if (self.def_width or deffield) == 0:
			defw = bw
		else:
			if self.def_width:
				defw = self.def_width * cellw
			else:
				maxw = min(self.max_width or 32, 32)
				defw = min(deffield, maxw) * cellw

		if not self.def_height:
			defh = -1
		else:
			maxh = max((self.max_height or 0) * cellh, bh)
			defh = min(max((self.def_height or 0) * cellh, bh), maxh)

		return wx.Size(defw, defh)


	# -------------------------------------------------------------------------
	# Get the maximum size
	# -------------------------------------------------------------------------

	def get_maximum_size(self):
		"""
		Return a wx.Size with the maximum size of a widget
		"""

		style = self._gfObject.style.lower()
		bw, bh = self._uiDriver.best_sizes.get(style, (-1, -1))
		cellw = self._uiDriver.cellWidth
		cellh = self._uiDriver.cellHeight

		length = self.get_field_length()
		if (self.max_width or length) == 0:
			maxw = -1
		else:
			maxw = ((self.max_width or length) * cellw) or bw

		if not self.max_height:
			maxh = -1
		else:
			maxh = ((self.max_height or 0) * cellh) or bh

		minw, minh = self.get_default_size().Get()
		if maxw != -1:
			maxw = max(maxw, minw)
		if maxh != -1:
			maxh = max(maxh, minh)

		return wx.Size(maxw, maxh)

	# -------------------------------------------------------------------------
	# Update the size hints of a widget
	# -------------------------------------------------------------------------

	def update_size_hints(self):

		minw, minh = self.get_default_size().Get()
		maxw, maxh = self.get_maximum_size().Get()

		if not isinstance(self.widget, BaseMaskedTextCtrl):
			self.widget.SetSizeHints(minw, minh, maxw, maxh)


	# -------------------------------------------------------------------------
	# Indicate whether this entry is vertically growable
	# -------------------------------------------------------------------------

	def is_growable(self):

		return (self._gfObject.style.lower() in ['multiline', 'listbox', 'richedit'])

	# -------------------------------------------------------------------------
	# Indicate whether this entry size is horizontally fixed
	# -------------------------------------------------------------------------

	def is_fixedwidth(self):
		# TODO: second condition is workaround
		# control with style label not shown sinse it is fixedwidth
		return self._gfObject._field.datatype == 'number'# and not self._gfObject.style == 'label'

	def _ui_set_focus_(self):
		"""
		Implemented in GFTabStop
		called when logical focus set to entry to update phisical focus
		"""
		# select all text in masked control
		# to force it to "fix selection"
		# (it will select first field)
		if isinstance(self.widget, BaseMaskedTextCtrl):
			self.widget.SetSelection(-1, -1)

		return super(UIEntry, self)._ui_set_focus_()


class GenericPicker(PopupControl):

	def __init__(self, *args, **kwargs):
		self.__uiEntry = kwargs.pop('uiEntry')
		PopupControl.__init__(self, *args, **kwargs)


# =============================================================================
# Configuration
# =============================================================================

configuration = {
	'baseClass': UIEntry,
	'provides' : 'GFEntry',
	'container': 0
}

# Translate from wx keystrokes to our virtual keystrokes
wxKeyTranslations = {
	vk.C         : 3,
	vk.V         : 22,
	vk.X         : 24,
	vk.A         : 1,
	vk.F1        : wx.WXK_F1,
	vk.F2        : wx.WXK_F2,
	vk.F3        : wx.WXK_F3,
	vk.F4        : wx.WXK_F4,
	vk.F5        : wx.WXK_F5,
	vk.F6        : wx.WXK_F6,
	vk.F7        : wx.WXK_F7,
	vk.F8        : wx.WXK_F8,
	vk.F9        : wx.WXK_F9,
	vk.F10       : wx.WXK_F10,
	vk.F11       : wx.WXK_F11,
	vk.F12       : wx.WXK_F12,
	vk.INSERT    : wx.WXK_INSERT,
	vk.DELETE    : wx.WXK_DELETE,
	vk.HOME      : wx.WXK_HOME,
	vk.END       : wx.WXK_END,
	vk.PAGEUP    : wx.WXK_PRIOR,
	vk.PAGEDOWN  : wx.WXK_NEXT,
	vk.UP        : wx.WXK_UP,
	vk.DOWN      : wx.WXK_DOWN,
	vk.LEFT      : wx.WXK_LEFT,
	vk.RIGHT     : wx.WXK_RIGHT,
	vk.TAB       : wx.WXK_TAB,
	vk.ENTER     : (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER),
	vk.ESC       : wx.WXK_ESCAPE,
	vk.BACKSPACE : wx.WXK_BACK,
	vk.RETURN    : wx.WXK_RETURN,
}

GFKeyMapper.KeyMapper.setUIKeyMap(wxKeyTranslations)
