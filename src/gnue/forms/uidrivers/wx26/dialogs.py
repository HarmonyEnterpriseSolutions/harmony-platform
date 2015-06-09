# GNU Enterprise Forms - wx 2.6 UI Driver - UI specific dialogs
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
# $Id: dialogs.py,v 1.7 2013/11/25 12:37:32 Oleg Exp $

import wx
import os
import sys

from gnue.forms import VERSION
from gnue.common.apps import GConfig


# =============================================================================
# This class implements an about dialog for the wx UI driver
# =============================================================================

class AboutBox (wx.Dialog):
	"""
	Displays an about dialog for the current application as defined by the given
	arguments.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, parent, name, version, author, descr, icon):
		"""
		@param parent: wx object to be the parent of the dialog
		@param name: name of the application
		@param version: version of the application
		@param author: author of the application
		@param description: text describing the form
		@param icon: path to the appication's icon
		"""

		wx.Dialog.__init__ (self, parent, wx.ID_ANY, u_("About %s") % name)

		dlgSz = wx.BoxSizer (wx.VERTICAL)
		sizer = wx.BoxSizer (wx.VERTICAL)

		dlgSz.Add (sizer, 1, wx.ALIGN_CENTER | wx.ALL, 12)

		if icon is not None and os.path.exists (icon):
			sizer.Add (wx.StaticBitmap (self, wx.ID_STATIC,
					wx.Image (icon).ConvertToBitmap ()), 0, wx.ALIGN_CENTER | wx.BOTTOM, 6)

		bold = wx.SystemSettings.GetFont (wx.SYS_DEFAULT_GUI_FONT)
		bold.SetWeight (wx.FONTWEIGHT_BOLD)

		# On Windows the SMALL_FONT is really too small
		if 'wxMSW' in wx.PlatformInfo:
			small = wx.NORMAL_FONT
		else:
			small = wx.SMALL_FONT

		# Application name
		s = wx.StaticText (self, -1, name)
		s.SetFont (bold)
		sizer.Add (s, 0, wx.ALIGN_CENTER)

		# Application version
		if version:
			s = wx.StaticText (self, -1, u_("Version: %s") % version)
			s.SetFont (small)
			sizer.Add (s, 0, wx.ALIGN_CENTER)

		# Author of the application
		if author:
			sizer.Add (wx.StaticText (self, -1, author), 0,
				wx.ALIGN_CENTER | wx.TOP, 6)

		# Description of the application
		if descr:
			sizer.Add (wx.StaticText (self, -1, descr, wx.DefaultPosition,
					wx.DefaultSize, wx.ALIGN_CENTRE), 0, wx.ALIGN_CENTER | wx.TOP, 6)

		# The GNUe Forms version
		sizer.Add (wx.StaticLine (self, -1, wx.DefaultPosition, wx.DefaultSize,
				wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 6)

		s = wx.StaticText (self, -1, "GNU Enterprise Forms")
		s.SetFont(bold)
		sizer.Add(s, 0, wx.ALIGN_CENTER)

		wxv = ".".join (["%s" % e for e in wx.VERSION])
		uni = 'unicode' in wx.PlatformInfo and 'Unicode' or 'Ansi'

		s = wx.StaticText (self, -1, "Version %s / %s %s - %s" % (VERSION, wx.PlatformInfo [1], wxv, uni))
		s.SetFont(small)
		sizer.Add(s, 0, wx.ALIGN_CENTER)

		s = wx.StaticText (self, -1, "python %s" % (sys.version,))
		s.SetFont(small)
		sizer.Add(s, 0, wx.ALIGN_CENTER)

		# Ok button
		sizer.Add (self.CreateButtonSizer (wx.OK), 0, wx.ALIGN_CENTER | wx.TOP, 12)

		self.SetSizerAndFit (dlgSz)
		self.CenterOnScreen ()


# =============================================================================
# Class implementing a versatile input dialog
# =============================================================================

class InputDialog (wx.Dialog):
	"""
	Dialog class prompting the user for a given number of fields. These field
	definitions are specified as follows:

	A field definition is a tuple having these elements:
	- fieldlabel: This text will be used as label in the left column
	- fieldname: This is the key in the result-dictionary to contain the value
	    entered by the user
	- fieldtype: Currently these types are supported:
	    - label: The contents of 'fieldlabel' as static text
	    - warning: The contents of 'fieldlabel' as static text, formatted as
	        warning
	    - string: A text entry control
	    - password: A text entry control with obscured characters
	    - dropdown: Foreach element given in 'elements' a separate ComboBox
	        control will be created, where each one has it's own dictionary of
	        allowed values. If a value is selected in one control, all others are
	        synchronized to represent the same key-value.
	- default: Default value to use
	- masterfield: Used for 'dropdowns'. This item specifies another field
	    definition acting as master field. If this master field is changed, the
	    allowedValues of this dropdown will be changed accordingly. If a
	    masterfield is specified the 'allowedValues' dictionaries are built like
	    {master1: {key: value, key: value, ...}, master2: {key: value, ...}}
	- elements: sequence of input element tuples (label, allowedValues). This is
	    used for dropdowns only. 'label' will be used as ToolTip for the control
	    and 'allowedValues' gives a dictionary with all valid keys to be selected
	    in the dropdown.

	@return: If closed by 'Ok' the result is a dictionary with all values entered
	  by the user, where the "fieldname"s will be used as keys. If the user has
	  not selected a value from a dropdown (i.e. it has no values to select)
	  there will be no such key in the result dictionary. If the dialog is
	  canceled ('Cancel'-Button) the result will be None.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, title, fields, cancel=True, on_top=False):
		"""
		Create a new input dialog

		@param title: Dialog title
		@param fields: sequence of field definition tuples
		@param cancel: If True add a Cancel button to the dialog
		"""

		flags = wx.DEFAULT_DIALOG_STYLE
		if on_top:
			flags |= wx.STAY_ON_TOP

		wx.Dialog.__init__ (self, None, wx.ID_ANY, title, style=flags)

		self.SetIcon (wx.ArtProvider.GetIcon (wx.ART_QUESTION, wx.ART_FRAME_ICON))

		topSizer = wx.BoxSizer (wx.VERTICAL)
		self.gbs = gbs = wx.GridBagSizer (2, 12)

		self.inputData   = {}
		self.__dropdowns = {}
		self.__lastEntry = None

		row = 0
		for (label, name, fieldtype, default, master, elements) in fields:
			ftp = fieldtype.lower ()

			if ftp in ['label', 'warning']:
				self.__addText (row, label, ftp == 'warning')

			elif ftp == 'image':
				self.__addImage (row, name)

			elif ftp in ['string', 'password']:
				self.__addString (row, label, name, default, elements, ftp != 'string')

			elif ftp == 'dropdown':
				self.__addChoice (row, label, name, default, master, elements)

			row += 1

		gbs.AddGrowableCol (1)
		topSizer.Add (gbs, 1, wx.EXPAND | wx.ALL, 6)

		topSizer.Add (wx.StaticLine (self, wx.ID_STATIC, style = wx.LI_HORIZONTAL),
			0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		buttonSizer = self.CreateButtonSizer (wx.OK | (cancel and wx.CANCEL or 0) |
			wx.NO_DEFAULT)
		topSizer.Add (buttonSizer, 0, wx.EXPAND | wx.ALIGN_RIGHT | wx.ALL, 8)

		self.SetSizerAndFit (topSizer)

		self.CenterOnScreen ()


	# ---------------------------------------------------------------------------
	# Add a centered, static label or warning
	# ---------------------------------------------------------------------------

	def __addText (self, row, label, warning = False):

		text = wx.StaticText (self, -1, label, style = wx.ALIGN_CENTRE)

		if warning:
			text.SetForegroundColour (wx.RED)

		self.gbs.Add (text, (row, 0), (1, 2), wx.EXPAND |
			wx.ALIGN_CENTER_HORIZONTAL)


	# ---------------------------------------------------------------------------
	# Add a text control for a string or a password
	# ---------------------------------------------------------------------------

	def __addString (self, row, label, name, default, elements, pwd = False):

		text = wx.StaticText (self, wx.ID_ANY, label)
		self.gbs.Add (text, (row, 0), flag = wx.ALIGN_CENTER_VERTICAL)

		self.inputData [name] = default or ''

		eStyle = wx.TE_PROCESS_ENTER
		if pwd:
			eStyle |= wx.TE_PASSWORD

		entry = wx.TextCtrl (self, wx.ID_ANY, default or '', style = eStyle)
		entry._field = name

		if elements and elements [0][0]:
			entry.SetToolTip (wx.ToolTip (elements [0][0]))

		self.Bind (wx.EVT_TEXT, self.OnEntryChanged, entry)
		self.Bind (wx.EVT_TEXT_ENTER, self.OnEnter, entry)

		self.gbs.Add (entry, (row, 1), flag = wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
		self.__lastEntry = entry


	# ---------------------------------------------------------------------------
	# Add a series of dropdowns into a single row
	# ---------------------------------------------------------------------------

	def __addChoice (self, row, label, name, default, master, elements):

		self.gbs.Add (wx.StaticText (self, wx.ID_ANY, label), (row, 0),
			flag = wx.ALIGN_CENTER_VERTICAL)

		rowSizer = wx.BoxSizer (wx.HORIZONTAL)

		perMaster = self.__dropdowns.setdefault (master, {})
		perRow    = perMaster.setdefault (name, [])

		border = 0
		for (tip, allowedValues) in elements:
			widget = wx.Choice (self, -1)
			widget._master  = master
			widget._name    = name
			widget._allowed = allowedValues
			widget._default = default

			self.__updateWidget (widget)

			if tip:
				widget.SetToolTip (wx.ToolTip (tip))

			self.Bind (wx.EVT_CHOICE, self.OnChoiceChanged, widget)
			perRow.append (widget)

			rowSizer.Add (widget, 1, wx.EXPAND | wx.LEFT, border)
			border = 4
			self.__lastEntry = widget

		self.gbs.Add (rowSizer, (row, 1), flag = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)


	# ---------------------------------------------------------------------------
	# Add a centered image to the dialog
	# ---------------------------------------------------------------------------

	def __addImage (self, row, imageURL):

		sizer = wx.BoxSizer (wx.HORIZONTAL)

		sizer.Add ((0, 0), 1)
		sizer.Add (wx.StaticBitmap (self, wx.ID_ANY,
				wx.Image (imageURL).ConvertToBitmap ()), 0)
		sizer.Add ((0, 0), 1)

		self.gbs.Add (sizer, (row, 0), (1, 2),
			wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)


	# ---------------------------------------------------------------------------
	# Whenever an entry will be changed, keep inputData in snyc
	# ---------------------------------------------------------------------------

	def OnEntryChanged (self, event):

		entry = event.GetEventObject ()
		self.inputData [entry._field] = entry.GetValue ()


	# ---------------------------------------------------------------------------
	# If <Enter> is pressed within a text control, move the focus
	# ---------------------------------------------------------------------------

	def OnEnter (self, event):

		entry = event.GetEventObject ()

		if entry == self.__lastEntry:
			self.EndModal (wx.ID_OK)
		else:
			entry.Navigate (wx.NavigationKeyEvent.IsForward)


	# ---------------------------------------------------------------------------
	# After the selection of a choice has change, keep all others in sync
	# ---------------------------------------------------------------------------

	def OnChoiceChanged (self, event):

		widget = event.GetEventObject ()
		newKey = widget.GetClientData (event.GetSelection ())
		self.inputData [widget._name] = newKey

		# Make sure all controls stay in sync
		for item in self.__dropdowns [widget._master][widget._name]:
			item.SetSelection (event.GetSelection ())

		# Keep all depending controls in sync
		self.__updateDepending (widget._name)


	# ---------------------------------------------------------------------------
	# Update all depending choice widgets
	# ---------------------------------------------------------------------------

	def __updateDepending (self, master):

		if master in self.__dropdowns:
			for name in self.__dropdowns [master].keys ():
				drops = self.__dropdowns [master] [name]
				for i in drops:
					self.__updateWidget (i)

				self.__updateDepending (name)


	# ---------------------------------------------------------------------------
	# Update the choices of a given choice widget
	# ---------------------------------------------------------------------------

	def __updateWidget (self, widget):

		widget.Freeze ()
		widget.Clear ()

		if widget._master:
			values = widget._allowed.get (self.inputData.get (widget._master), {})
		else:
			values = widget._allowed

		if values:
			for (k, v) in values.items ():
				widget.Append (unicode(v), k)

			if widget._default in values:
				widget.SetStringSelection(unicode(values[widget._default]))
				self.inputData [widget._name] = widget._default
			else:
				self.inputData [widget._name] = widget.GetClientData (0)
				widget.SetSelection (0)

		else:
			if widget._name in self.inputData:
				del self.inputData [widget._name]

		widget.Enable (len (values))
		widget.Thaw ()
		widget.Refresh ()


	# ---------------------------------------------------------------------------
	# Show the modal dialog and clear inputData on cancelling
	# ---------------------------------------------------------------------------

	def ShowModal (self):
		"""
		Starts the modal dialog. If it get's cancelled inputData will be cleared.
		"""

		result = wx.Dialog.ShowModal (self)
		if result == wx.ID_CANCEL:
			self.inputData = None


# =============================================================================
# Exception display dialog
# =============================================================================

class ExceptionDialog (wx.Dialog):

	_TITLE = {'system'     : _("GNUe Internal System Error"),
		'admin'      : _("GNUe Unexpected Error"),
		'application': _("GNUe Application Error")}

	_FORMAT = {
		'system': u_("An unexpected internal error has occured:\n%s.\n"
			"This means you have found a bug in GNU Enterprise. "
			"Please report it to gnue-dev@gnu.org"),
		'admin': u_("An unexpected error has occured:\n%s.\n"
			"Please contact your system administrator."),
		'application': u_("An unexpected error has occured:\n%s.\n"
			"Please contact your system administrator.")}

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, group, name, message, detail):

		wx.Dialog.__init__ (self, None, wx.ID_ANY,
			name or self._TITLE.get (group, _('Error')), wx.DefaultPosition,
			wx.DefaultSize, wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

		self.dls = dls = wx.BoxSizer (wx.VERTICAL)
		self.gbs = gbs = wx.GridBagSizer (6, 6)

		self.SetIcon (wx.ArtProvider.GetIcon (wx.ART_ERROR, wx.ART_FRAME_ICON))

		# ---- Message panel
		icon = wx.StaticBitmap (self, wx.ID_ANY,
			wx.ArtProvider.GetBitmap (wx.ART_ERROR, wx.ART_MESSAGE_BOX),
			wx.DefaultPosition)
		gbs.Add (icon, (0, 0))

		msg =wx.StaticText (self, wx.ID_STATIC,
			self._FORMAT.get (group, "%s") % message, wx.DefaultPosition,
			wx.DefaultSize, 0)
		gbs.Add (msg, (0, 1), flag = wx.EXPAND | wx.ALIGN_LEFT)

		(mxW, mxH) = self.GetMaxSize ()
		h = (len (detail.splitlines ()) + 1) * (self.GetCharHeight () + 2)
		w = max ([len (i) for i in detail.splitlines ()]) * self.GetCharWidth ()
		size = (min (w, int (mxW * 0.9)), min (h, int (mxH * 0.8)))

		detail = '\n'.join((name, message, detail))
		
		self.detailText = wx.TextCtrl (self, wx.ID_ANY, detail, wx.DefaultPosition,
			size, wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)

		# Don't forget to put an empty item into the 'empty' cells. This prevents a
		# crason on win32 and mac os x
		gbs.Add ((0, 0), (1, 0))
		gbs.Add (self.detailText, (1, 1), flag = wx.EXPAND | wx.ALIGN_LEFT)


		self.detailText.MinSize = (800, min(detail.count('\n') + 3, 33) * 13)
		#gbs.Hide (self.detailText)

		gbs.AddGrowableCol (1)
		gbs.AddGrowableRow (1)

		dls.Add (gbs, 1, wx.EXPAND | wx.ALIGN_TOP | wx.ALL, 6)

		# ---- Static line

		line = wx.StaticLine (self, wx.ID_STATIC, wx.DefaultPosition,
			wx.DefaultSize, wx.LI_HORIZONTAL)
		dls.Add (line, 0, wx.EXPAND | wx.ALIGN_TOP | wx.LEFT | wx.RIGHT, 6)

		# ---- Button box
		buttonBox = wx.BoxSizer (wx.HORIZONTAL)
		close  = wx.Button (self, wx.ID_CLOSE)
		detail = wx.Button (self, wx.ID_ANY, _("<< Details"))

		self.Bind (wx.EVT_BUTTON, self.__closeButton , close)
		self.Bind (wx.EVT_BUTTON, self.__detailButton, detail)

		buttonBox.Add (close , 1, wx.ALIGN_LEFT)
		buttonBox.Add (detail, 1, wx.ALIGN_LEFT | wx.LEFT, 6)

		dls.Add (buttonBox, 0, wx.ALIGN_RIGHT | wx.ALL, 6)
		self.__showDetail  = True
		self.__changedFont = False

		self.SetSizerAndFit (dls)

		self.CenterOnScreen ()
		self.Raise ()


	# ---------------------------------------------------------------------------
	# Detail button click
	# ---------------------------------------------------------------------------

	def __detailButton (self, event):

		self.__showDetail = not self.__showDetail

		if not self.__changedFont:
			cur = self.detailText.GetFont ()
			fix = wx.Font (cur.GetPointSize (), wx.MODERN, wx.NORMAL, wx.NORMAL)
			if fix.Ok ():
				self.detailText.SetFont (fix)
				self.detailText.SetInsertionPoint (0)

			self.__changedFont = True

		btn = event.GetEventObject ()
		if self.__showDetail:
			btn.SetLabel (_('<< Details'))
			self.gbs.Show (self.detailText)
		else:
			btn.SetLabel (_('>> Details'))
			self.gbs.Hide (self.detailText)

		self.gbs.Layout ()
		self.Fit ()
		self.CenterOnScreen ()
		self.Refresh ()


	# ---------------------------------------------------------------------------
	# Close the dialog
	# ---------------------------------------------------------------------------

	def __closeButton (self, event):

		self.EndModal (wx.ID_CLOSE)



# =============================================================================
# Module self test
# =============================================================================

if __name__ == '__main__':
	app = wx.PySimpleApp ()

	desc = "This is a quite long description of the application.\n" \
		"It also contains newlines as well as a lot of text. This text " \
		"get's continued in the third line too.\n"

	dialog = AboutBox (None, 'FooBar', '1.0.3', 'BarBaz', desc, None)
	try:
		dialog.ShowModal ()
	finally:
		dialog.Destroy ()

	# ---------------------------------------------------------------------------

	cname = {'c1': 'demoa', 'c2': 'demob'}
	ckey  = {'c1': 'ck-A' , 'c2': 'ck-B'}

	wija = {'c1': {'04': 2004, '05': 2005},
		'c2': {'24': 2024, '25': 2025, '26': 2026}}

	codes = {'24': {'241': 'c-24-1', '242': 'c-24-2'},
		'25': {'251': 'c-25-1'}}

	fields = [#('Foo!', '/home/johannes/gnue/share/gnue/images/gnue.png', 'image',
		# None, None, []),
		('Username', '_username', 'string', 'frodo', None, \
				[('Name of the user', None)]),
		('Password', '_password', 'password', 'foo', None, [('yeah',1)]),
		('Foobar', '_foobar', 'dropdown', 'frob', None, \
				[('single', {'trash': 'Da Trash', 'frob': 'Frob'})]),
		('Multi', '_multi', 'dropdown', '100', None, \
				[('name', {'50': 'A 50', '100': 'B 100', '9': 'C 9'}),
				('sepp', {'50': 'se 50', '100': 'se 100', '9': 'se 9'})]),
		('Noe', '_depp', 'label', 'furz', None, []),
		('Das ist jetzt ein Fehler', None, 'warning', None, None, []),

		('Firma', 'company', 'dropdown', 'c1', None,
			[('Name', cname), ('Code', ckey)]),
		('Wirtschaftsjahr', 'wija', 'dropdown', '05', 'company',
			[('Jahr', wija)]),
		('Codes', 'codes', 'dropdown', None, 'wija',
			[('Code', codes)])]

	dialog = InputDialog ('Foobar', fields)
	try:
		dialog.ShowModal ()
		print "Result:", dialog.inputData

	finally:
		dialog.Destroy ()

	app.MainLoop ()
