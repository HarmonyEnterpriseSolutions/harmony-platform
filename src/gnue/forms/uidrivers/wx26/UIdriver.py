# GNU Enterprise Forms - wx 2.6 UI Driver - User Interface
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
# $Id: UIdriver.py,v 1.8 2013/11/25 12:40:49 Oleg Exp $

import sys
import os.path

from gnue.forms.uidrivers._base import Exceptions
from gnue.forms.uidrivers._base.UIdriver import GFUserInterfaceBase

#try:
#	if sys.platform == 'darwin':
#		minimal = '2.8'
#	else:
#		minimal = '2.6'
#
#	# On Mac OS X we provide GNUe Forms as semi-standalone application.  Since
#	# sys.frozen is set there and the default version installed on OS X 10.3+
#	# is wx 2.5 we have to require 2.8 even if sys.frozen is set.
#	if not hasattr(sys, 'frozen') or sys.platform == 'darwin':
#		import wxversion
#		wxversion.ensureMinimal(minimal)
#
#except ImportError:
#	raise Exceptions.DriverNotSupported, \
#		_("This GNUe-Forms UI Driver requires at least wx %s.") % minimal

import toolib.wx.event.CallAfterSafe # installs PyDeadObjectError safe CallAfter
import wx.lib.colourdb

from gnue.forms.uidrivers.wx26 import dialogs, UISplashScreen
from gnue.common.apps import GConfig


# =============================================================================
# This class implements a User Interface for wx 2.6
# =============================================================================

class GFUserInterface (GFUserInterfaceBase):
	"""
	An implementation of the common GUI toolkit interface using wx 2.6+.

	@cvar __rearrange_boxes__: if True the bounding boxes of widgets will be
	     checked.  Additionally all widgets having a position within a box-tag
	     will get a child of that box (in the xml-object-tree).
	"""

	__rearrange_boxes__ = True

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, eventHandler, name="Undefined", disableSplash=None,
		parentContainer=None, moduleName=None):
		GFUserInterfaceBase.__init__(self, eventHandler, name,
			disableSplash, parentContainer, moduleName)

		self.name = "wx 2.6"
		self.app  = wx.GetApp() or wx.PySimpleApp()   #or wx.App()
		wx.InitAllImageHandlers()
		wx.lib.colourdb.updateColourDB()

		(self.best_sizes, self.cellWidth, self.cellHeight) = self.__getSizes()

		self.textWidth  = self.widgetWidth  = self.cellWidth
		self.textHeight = self.widgetHeight = self.cellHeight

		if not self._disableSplash:
			self.__splash = UISplashScreen.SplashScreen()
			self.__splash.Show()
		else:
			self.__splash = None


	# -------------------------------------------------------------------------
	# Get the widget sizes and the dimension of a form cell
	# -------------------------------------------------------------------------

	def __getSizes(self):

		frame  = wx.Frame(None)
		result = {}

		try:
			# First of all find out the preferred size of all widgets needed
			text = wx.TextCtrl(frame, wx.ID_ANY)
			result['default'] = text.GetBestSize()

			combo = wx.ComboBox(frame, wx.ID_ANY)
			result['dropdown'] = combo.GetBestSize()

			label = wx.StaticText(frame, wx.ID_ANY)
			result['label'] = label.GetBestSize()

			# Get the height and width of a form-cell for which we use the
			# tallest control and the avarage character width of the
			# application font
			cellHeight = max([i[1] for i in result.values()]) + 2
			cellWidth  = frame.GetCharWidth() + 1

			# Add the button after calculating the cellHeight.  This is because
			# a button is too big on GTK.
			button = wx.Button(frame, wx.ID_ANY)
			result['button'] = button.GetBestSize()

			multi = wx.TextCtrl(frame, -1, style=wx.TE_MULTILINE)
			result['multiline'] = multi.GetBestSize()

		finally:
			frame.Destroy()

		return (result, cellWidth, cellHeight)


	# -------------------------------------------------------------------------
	# Get the border for a given type of control
	# -------------------------------------------------------------------------

	def control_border(self, control):

		return (self.cellHeight - self.best_sizes.get(control, [0,0])[1]) / 2


	# -------------------------------------------------------------------------
	# Hide the splash screen
	# -------------------------------------------------------------------------

	def hide_splash(self):
		"""
		Hide the Splash-Screen (if it is visible).
		"""

		if self.__splash is not None:
			try:
				self.__splash.Close()
			finally:
				self.__splash = None


	# -------------------------------------------------------------------------
	# Start the application's main loop
	# -------------------------------------------------------------------------

	def mainLoop(self):
		"""
		Start the main loop of the current application instance (wx.App())
		"""

		assert gEnter(6)

		# Main loop might already be running if this has been called with
		# runForm()
		if not self.app.IsMainLoopRunning():
			self.app.MainLoop()

		assert gLeave(6)


	# -------------------------------------------------------------------------
	# Create and run an input dialog
	# -------------------------------------------------------------------------

	def _getInput(self, title, fields, cancel = True):

		dialog = dialogs.InputDialog(title, fields, cancel)

		try:
			dialog.ShowModal()
			return dialog.inputData

		finally:
			dialog.Destroy()


	# -------------------------------------------------------------------------
	# Show a simple error message
	# -------------------------------------------------------------------------

	def _ui_show_error_(self, message):

		if self.__splash:
			self.__splash.Close()

		dialog = wx.MessageDialog(None, message, "GNU Enterprise",
			wx.ICON_ERROR | wx.OK)
		try:
			result = dialog.ShowModal()
		finally:
			dialog.Destroy()


	# -------------------------------------------------------------------------
	# Show an exception dialog
	# -------------------------------------------------------------------------

	def _ui_show_exception_(self, group, name, message, detail):

		if self.__splash:
			self.__splash.Close()

		dlg = dialogs.ExceptionDialog(group, name, message, detail)
		try:
			dlg.ShowModal()

		finally:
			dlg.Destroy()


	# -------------------------------------------------------------------------
	# Exit the application
	# -------------------------------------------------------------------------

	def _ui_exit_(self):
		"""
		Exit the application.
		"""
		pass
