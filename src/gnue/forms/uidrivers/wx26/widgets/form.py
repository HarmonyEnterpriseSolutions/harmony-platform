# GNU Enterprise Forms - wx 2.6 UI Driver - Form widget
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
# $Id: form.py,v 1.49 2013/07/26 15:42:36 oleg Exp $
"""
Implementation of the UI layer for the <form> and <dialog> tag.
"""

import time
import os.path

import wx
from gnue.common.apps import GConfig
from gnue.forms import VERSION
from gnue.forms.uidrivers.wx26 import dialogs
from gnue.forms.uidrivers.wx26.widgets._base import UIHelper
from gnue.common.apps import errors
from src.gnue.forms.uidrivers.wx26.widgets._config import BORDER_SPACE
from gnue.forms.GFObjects.GFBox import GFBox
from toolib.util.Configurable                import Configurable


__all__ = ['UIForm']

_MBOX_KIND = {
	'info'    : {
		'type'   : wx.ICON_INFORMATION,
		'buttons': wx.OK,
		'title'  : u_("Information")
	},
	'warning' : {
		'type'   : wx.ICON_EXCLAMATION,
		'buttons': wx.OK,
		'title'  : u_("Warning")
	},
	'question': {
		'type'   : wx.ICON_QUESTION,
		'buttons': wx.YES_NO,
		'title'  : u_("Question")
	},
	'error' : {
		'type'   : wx.ICON_ERROR,
		'buttons': wx.OK,
		'title'  : u_("Error")
	}
}

_RESPONSE = {wx.ID_OK    : True,
	wx.ID_YES   : True,
	wx.ID_NO    : False,
	wx.ID_CANCEL: None }


# =============================================================================
# Interface implementation of a form widget
# =============================================================================

busyCursorSuppressed = 0

class UIForm(UIHelper, Configurable):
	"""
	Interface implementation of form widgets (forms and dialogs)
	"""

	_TAB_STYLE = {'left': wx.NB_LEFT,
		'right': wx.NB_RIGHT,
		'bottom': wx.NB_BOTTOM,
		'top': wx.NB_TOP}

	_WINDOW_STYLE = {
		'MINIMIZE_BOX'      : wx.MINIMIZE_BOX,
		'MAXIMIZE_BOX'      : wx.MAXIMIZE_BOX,
		'CLOSE_BOX'         : wx.CLOSE_BOX,
		'RESIZEABLE'        : wx.RESIZE_BORDER,
		'CAPTION'           : wx.CAPTION,
		'MAXIMIZE'          : wx.MAXIMIZE,
	}

	_DEFAULT_WINDOW_STYLE = {
		'normal' : wx.DEFAULT_FRAME_STYLE,
		'dialog' : wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
	}

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):

		UIHelper.__init__(self, event)

		self._inits.append(self.__postinit)

		self.__mainFrame = None
		self.__frame = None
		self.__uiContainer = event.uiContainer or self

		self.menuBar = None		# accessed from UIMenu
		self.toolBar = None     # accessed from UIToolbar
		self.__statusBar = None


	def isEmbeded(self):
		return self.__uiContainer is not self

	def getMainFrame(self):
		"""the wx.Frame or wx.Dialog instance representing this form"""
		return self.__mainFrame
	
	###########################################################################
	# uiContainer inteface to uiForm
	#
	def getFrame(self):
		if self.__frame is None:

			# convert gnue windowStyle to wx style
			style = self._DEFAULT_WINDOW_STYLE[self._form.style]
			for s in self._gfObject.windowStyle:
				s = s.upper()
				if s:
					negative = s.startswith('-')
					if negative:
						s = s[1:].lstrip()
					try:
						wxStyle = self._WINDOW_STYLE[s]
						if negative:
							style &= ~wxStyle
						else:
							style |= wxStyle
					except KeyError:
						raise errors.AdminError, 'Unknown windowStyle: "%s"' % s

			if self._form.style == 'dialog':
				parent = wx.Window.FindFocus()
				print "new dialog %s parent is %s" % (self._form.name, parent)
				frame = wx.Dialog(None, -1, style = style)
			else:
				frame = wx.Frame(None, -1, style = style, size=(1024-50, 768-50))
				# workaround bug: window not maximized
				# can't understand why
				if style & wx.MAXIMIZE:
					frame.Maximize()

			frame.SetTitle(self._form.title)
			frame.SetIcons(self.__load_icons())
			frame.SetSizer(wx.BoxSizer(wx.VERTICAL))

			frame.Bind(wx.EVT_CLOSE, self.__on_close, frame)

			frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))

			self.__frame = frame
		return self.__frame


	def getContainer(self, uiForm):
		assert uiForm is self
		return self.getFrame()


	def show(self, uiForm, modal):
		global busyCursorSuppressed

		assert uiForm is self

		frame = self.getFrame()
		frame.Raise()

		if modal and isinstance(frame, wx.Dialog):
			# disable busy cursor when modal dialog shown 
			# solves bug when no resize cursors
			if wx.IsBusy():
				wx.EndBusyCursor()
				busyCursorSuppressed += 1
			frame.ShowModal()
		else:
			frame.Show()


	def close(self, uiForm):
		global busyCursorSuppressed
		assert uiForm is self

		frame = self.getFrame()

		if isinstance(frame, wx.Dialog) and frame.IsModal():
			frame.EndModal(0)
			# restore busy cursor if was
			if busyCursorSuppressed > 0:
				busyCursorSuppressed -= 1
				wx.BeginBusyCursor()
		else:
			frame.Hide()


	def setTitle(self, uiForm, title):
		assert uiForm is self

		self.getFrame().SetTitle(title)

	#
	###########################################################################

	# -------------------------------------------------------------------------
	# Create a new wx frame widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Create the real wx.Frame or wx.Dialog.

		@param event: the creation-event instance carrying information like
		        container (parent-widget)

		@returns: the wx.Frame or wx.Dialog instance for this form
		"""

		self.__mainFrame = self.__uiContainer.getFrame()
		self._container  = self.__uiContainer.getContainer(self)

		# assume that widget of UIForm is panel because __mainFrame is not allways present
		self.widget = self._container

		
		if self._form.style != 'dialog' and not self._form._features['GUI:STATUSBAR:SUPPRESS']:
			self.__statusBar = wx.StatusBar(self.__mainFrame)
			self.__statusBar.SetFieldsCount(5)
			self.__statusBar.SetStatusWidths([-1, 50, 50, 75, 75])

	# -------------------------------------------------------------------------
	# Add widgets to the form
	# -------------------------------------------------------------------------

	def add_widgets(self, ui_widget, border=0):
		"""
		Add a given UI widget to the page.

		@param ui_widget: widget to add to the page
		@param spacer: not used for pages
		"""
		if self.__uiContainer is not self and hasattr(self.__uiContainer, 'add_widgets'):
			self.__uiContainer.add_widgets(ui_widget, border)
		else:
			self._container.GetSizer().Add(
				ui_widget.widget,
				ui_widget.stretch,
				wx.EXPAND | wx.ALL,
				# The border between the edge of the page
				# add no border if item is not GFBox widget
				isinstance(ui_widget._gfObject, GFBox) and BORDER_SPACE or 0
			)

	# -------------------------------------------------------------------------
	# Load an icon bundle for this form
	# -------------------------------------------------------------------------

	def __load_icons(self):

		idir = GConfig.getInstalledBase('forms_images', 'common_images')
		iconBundle = wx.IconBundle()

		for size in [16, 32, 64]:
			fname = os.path.join(idir, 'forms', 'default',
				'gnue-%sx%s.png' % (size, size))
			if os.path.exists(fname):
				# On wxMSW loading an icon directly from a file doesn't work, so
				# we need to copy the icons from a bitmap on the fly
				icon = wx.Icon(fname, wx.BITMAP_TYPE_PNG)
				icon.CopyFromBitmap(wx.Image(fname).ConvertToBitmap())

				iconBundle.AddIcon(icon)

		return iconBundle


	def __isFitable(self):
		for i in ('GFTable', 'GFTree', 'GFSplitter', 'GFNotebook', 'GFMDINotebook'):
			if self._gfObject._layout.findChildNamed(None, i, allowAllChildren=True):
				return False
		return True

	def __postinit (self):
		# specify the size hints and fit all child controls

		# If a menubar has been created, it will be set for the main window.
		# This 'deferred' method is needed so OS X can rearrange some
		# items according to it's HIG.
		if self.menuBar:
			self.__mainFrame.SetMenuBar(self.menuBar)

		self.walk(self.__update_size_hints_walker)

		# if not embeded
		if self.__uiContainer is self:

			# if not maximized
			if not self.__mainFrame.GetWindowStyle() & wx.MAXIMIZE:

				fitable = self.__isFitable()		

				# try read size from configurable
				w = self.getSetting('width')
				h = self.getSetting('height')
				if w and h:
					if fitable:
						# avoid size smaller than fit size
						self.__mainFrame.Fit()
						w = max(w, self.__mainFrame.Size[0])
						h = max(h, self.__mainFrame.Size[1])

					# read last size
					self.__mainFrame.Size = (w, h)
					self.__mainFrame.CenterOnScreen()
				else:
					if fitable:
						self.__mainFrame.Fit()
						self.__mainFrame.CenterOnScreen()
					else:
						# make window size as screen size if it can't be packed
						w = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
						h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y) - wx.SystemSettings.GetMetric(wx.SYS_CAPTION_Y) * 2
						
						self.__mainFrame.Size = (w, h)
						self.__mainFrame.CenterOnScreen()
        
						y = self.__mainFrame.Position[1]
						if y < 0:
							h += y
							self.__mainFrame.Size = (w, h)
							self.__mainFrame.CenterOnScreen()
    


	# -------------------------------------------------------------------------
	# Update the size hints of all UI widgets
	# -------------------------------------------------------------------------

	def __update_size_hints_walker(self, item):

		if item != self:
			item.update_size_hints()


	def updateBars(self):
		if not isinstance(self.__mainFrame, wx.Dialog):

			self.__mainFrame.Freeze()

			oldToolBar = self.__mainFrame.GetToolBar()
			if self.toolBar is not oldToolBar:

				if self.toolBar:
					self.__mainFrame.SetToolBar(self.toolBar)
					self.toolBar.Show()

				if oldToolBar:
					oldToolBar.Hide()

			oldStatusBar = self.__mainFrame.GetStatusBar()
			if self.__statusBar is not oldStatusBar:

				if self.__statusBar:
					self.__mainFrame.SetStatusBar(self.__statusBar)
					self.__statusBar.Show()

				if oldStatusBar:
					oldStatusBar.Hide()

			self.__mainFrame.Thaw()


	# -------------------------------------------------------------------------
	# Show the form/dialog
	# -------------------------------------------------------------------------

	def _ui_show_(self, modal, afterModal):
		"""
		If modal is False, afterModal is ignored
		"""
		self._uiDriver.hide_splash()
		self.__uiContainer.show(self, modal)
		if modal:
			afterModal()
		else:
			self.updateBars()

	# -------------------------------------------------------------------------
	# Event-handler
	# -------------------------------------------------------------------------

	def __on_close(self, event):
		#rint ">>> %s.__on_close(canVeto=%s)" % (self._form.name, event.CanVeto())
		if event.CanVeto():
			self._form.close()
			event.Veto()
		else:
			# Actually, event.Skip() should call the standard event handler for
			# this event, meaning the form is being destroyed. For some reason,
			# this doesn't work, so we destroy the form manually.
			#event.Skip()
			event.GetEventObject().Destroy()

	# -------------------------------------------------------------------------
	# User feedback functions
	# -------------------------------------------------------------------------

	def _ui_begin_wait_(self):
		"""
		Display the hourglass cursor on all windows of the application.
		"""
		wx.BeginBusyCursor()

	# -------------------------------------------------------------------------

	def _ui_end_wait_(self):
		"""
		Display the normal mouse cursor on all windows of the application.
		"""
		# workaround for #881 (_ui_end_wait_ before EndModal?)
		if wx.IsBusy():
			wx.EndBusyCursor()
		else:
			# must be busy cursor but not, may be it supressed but not unsupressed, fix the state
			global busyCursorSuppressed
			busyCursorSuppressed = 0

	# -------------------------------------------------------------------------

	def _ui_beep_(self):
		"""
		Ring the system bell.
		"""
		wx.Bell()

	# -------------------------------------------------------------------------

	def _ui_update_status_(self, tip, record_status, insert_status,
		record_number, record_count):
		"""
		Update the apropriate section of the status bar with the given
		information.

		@param tip: message to be shown in the first section
		@param record_status: message for the second section
		@param insert_status: message for the third section
		@param record_number: number of the current record
		@param record_count: number of available records.  Together with
		        record_number this will be set into the 4th section
		@param page_number: number of the current page
		@param page_count: number of available pages.  Together with the
		        page_number this will be set into the 5th section
		"""
		if self.__statusBar:

			if tip is not None:
				self.__statusBar.SetStatusText(tip, 0)

			if record_status is not None:
				self.__statusBar.SetStatusText(record_status, 1)

			if insert_status is not None:
				self.__statusBar.SetStatusText(insert_status, 2)

			if record_number and record_count:
				self.__statusBar.SetStatusText(
					"%s/%s" % (record_number, record_count), 3)


	# -------------------------------------------------------------------------

	def _ui_show_message_(self, message, kind, title, cancel=False, no_default=False, resultConsumer=lambda x: x):
		"""
		This function creates a message box of a given kind and returns True,
		False or None depending on the button pressed.

		@param message: the text of the messagebox
		@param kind: type of the message box. Valid types are 'Info',
		        'Warning', 'Question', 'Error'
		@param title: title of the message box
		@param cancel: If True a cancel button will be added to the dialog
		@param resultConsumer: function to call to handle result

		@return: True if the Ok-, Close-, or Yes-button was pressed, False if
		        the No-button was pressed or None if the Cancel-button was pressed.
		"""

		mbRec  = _MBOX_KIND.get(kind.lower())
		flags  = mbRec['type'] | mbRec['buttons']
		
		if cancel:
			flags |= wx.CANCEL
		
		if no_default:
			flags |= wx.NO_DEFAULT 
		
		title  = title and title or mbRec['title']

		p = self.__mainFrame
		while not p.IsShown() and p.GetParent():
			p = p.GetParent()

		dialog = wx.MessageDialog(p, message, title, flags)
		try:
			result = dialog.ShowModal()
		finally:
			dialog.Destroy()

		return resultConsumer(_RESPONSE[result])

	# -------------------------------------------------------------------------
	# Show a file selection dialog
	# -------------------------------------------------------------------------

	def _ui_select_files_(self, title, defaultDir, defaultFile, wildcard,
		mode, multiple, overwritePrompt, fileMustExist, readData, resultConsumer, name):
		"""
		Bring up a dialog for selecting filenames.

		@param title: Message to show on the dialog
		@param defaultDir: the default directory, or the empty string
		@param defaultFile: the default filename, or the empty string
		@param wildcard: a list of tuples describing the filters used by the
		        dialog.  Such a tuple constists of a description and a fileter.
		        Example: [('PNG Files', '*.png'), ('JPEG Files', '*.jpg')]
		        If no wildcard is given, all files will match (*.*)
		@param mode: Is this dialog an open- or a save-dialog.  If mode is
		        'save' it is a save dialog, everything else would be an
		        open-dialog.
		@param multiple: for open-dialog only: if True, allows selecting
		        multiple files
		@param overwritePrompt: for save-dialog only: if True, prompt for a
		        confirmation if a file will be overwritten
		@param fileMustExist: if True, the user may only select files that
		        actually exist

		@returns: a sequence of filenames or None if the dialog has been
		        cancelled.
		"""

		wst = '|'.join(['%s|%s' % (descr, filt) for (descr, filt) in wildcard])
		if not wst:
			wst = '%s (*.*)|*.*' % u_('All files')

		if mode.lower().startswith('save'):
			flags = wx.SAVE
			if overwritePrompt:
				flags |= wx.OVERWRITE_PROMPT
		else:
			flags = wx.OPEN
			if multiple:
				flags |= wx.MULTIPLE

		if fileMustExist:
			flags |= wx.FILE_MUST_EXIST

		path_key = 'selectfiles.' + name + '.path'
		#file_key = 'selectfiles.' + name + '.file'

		#rint '>>>>', repr(defaultFile), repr(self.getSetting(file_key, defaultFile))

		dlg = wx.FileDialog(
			self.__mainFrame, 
			title, 
			self.getSetting(path_key, defaultDir),
			defaultFile, #self.getSetting(file_key, defaultFile) or defaultFile,	# TODO: getSetting must not return None
			wst, 
			flags
		)

		try:
			result = None
			mres = dlg.ShowModal()
			if mres == wx.ID_OK:
				if multiple:
					result = dlg.GetPaths()
				else:
					result = [dlg.GetPath()]
				
				# remember state for the next time
				path, file = os.path.split(result[0])
				self.setSetting(path_key, path)
				#self.setSetting(file_key, file)
				#if flags & wx.MULTIPLE:
				#	self.setSetting(file_key, None)	# TODO: this will set None and future getSetting will return None
				
				if readData:
					result = [(i, open(i, 'rb').read()) for i in result]
		finally:
			dlg.Destroy()

		return resultConsumer(result)

	# -------------------------------------------------------------------------
	# Select a directory
	# -------------------------------------------------------------------------

	def _ui_select_dir_(self, title, defaultDir, newDir, resultConsumer, name):
		"""
		Bring up a dialog for selecting a directory path.

		@param title: Message to show on the dialog
		@param defaultDir: the default directory, or the empty string
		@param newDir: If true, add "Create new directory" button and allow
		        directory names to be editable. On Windows the new directory button
		        is only available with recent versions of the common dialogs.

		@returns: a path or None if the dialog has been cancelled.
		"""

		style = wx.DD_DEFAULT_STYLE 
		if not newDir:
			style = style | wx.DD_DIR_MUST_EXIST 

		path_key = 'selectdir.' + name + '.path'
		dlg = wx.DirDialog(self.__mainFrame, title, self.getSetting(path_key, defaultDir), style)
		try:
			result = None
			mres = dlg.ShowModal()
			if mres == wx.ID_OK:
				result = dlg.GetPath()
				self.setSetting(path_key, result)

		finally:
			dlg.Destroy()

		return resultConsumer(result)


	# -------------------------------------------------------------------------
	# Set title of form
	# -------------------------------------------------------------------------

	def _ui_set_title_(self, title):
		self.__uiContainer.setTitle(self, title)

	# -------------------------------------------------------------------------
	# Display an about box
	# -------------------------------------------------------------------------

	def _ui_show_about_(self, name, version, author, description):

		idir = GConfig.getInstalledBase('forms_images', 'common_images')
		icon = os.path.join(idir, 'gnue-icon.png')

		dlg = dialogs.AboutBox(self.__mainFrame, name, version, author,
			description, icon)
		try:
			dlg.ShowModal()
		finally:
			dlg.Destroy()


	# -------------------------------------------------------------------------
	# Print form screenshot
	# -------------------------------------------------------------------------

	def _ui_printout_(self, title, subtitle, user):

		# Store the content of the form in a bitmap DC, because later parts of
		# the form are hidden behind the print dialog, which breaks the form
		# DC.
		window_dc = wx.ClientDC(self.__mainFrame)
		w, h = self.__mainFrame.GetClientSizeTuple()
		# We have to take the different origin of the client area into account.
		# On wxMSW the ClientDC contains the ToolBar.
		(offsx, offsy) = self.__mainFrame.GetClientAreaOrigin()

		bitmap = wx.EmptyBitmap(w, h)
		form_dc = wx.MemoryDC()
		form_dc.SelectObject(bitmap)
		form_dc.Blit(0,0, w, h, window_dc, offsx, offsy)

		printout = _Printout(title, subtitle, user, bitmap)
		wx.Printer().Print(self.__mainFrame, printout)


	# -------------------------------------------------------------------------
	# Close the window
	# -------------------------------------------------------------------------

	def _ui_close_(self):
		self.saveConfig()
		self.__uiContainer.close(self)

	def _ui_destroy_(self):
		"""
		called to dispose frame when form closed forever
		"""
		if not self.isEmbeded():
			self.getFrame().Destroy()


	def _forgetUiContainer(self):
		self.__uiContainer = None

	def _ui_call_after_(self, f, *args, **kwargs):
		wx.CallAfter(f, *args, **kwargs)

	##########################################
	# for Configurable
	#
	def getDomain(self):
		return 'gnue'

	def getConfigName(self):
		"""
		Returns the name of the configuration file.
		This is used on the command-line.
		"""
		return self._gfObject._uid_()

	def getDefaultUserConfig(self):
		return {
			'width' : None,
			'height' : None,
		}

	def applyConfig(self):
		w = self.getSetting('width')
		h = self.getSetting('height')
		if w and h:
			self.widget.Size = (w, h)

	def saveConfig(self):
		# if not embeded
		if self.__uiContainer is self:# and not self.__isFitable():

			w, h = self.__mainFrame.Size
			self.setSetting('width', w)
			self.setSetting('height', h)
			
			# do not save local conf
			return self.saveUserConfig()

# =============================================================================
# Helper class for screen dump printing
# =============================================================================

class _Printout(wx.Printout):

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, title, subtitle, login, bitmap):
		self.__title = title
		self.__subtitle = subtitle or ''
		self.__login = login
		self.__bitmap = bitmap
		wx.Printout.__init__(self, title)


	# -------------------------------------------------------------------------
	# Return info about number of pages in the document (always 1 here)
	# -------------------------------------------------------------------------

	def GetPageInfo(self):

		return (1, 1, 1, 1)


	# -------------------------------------------------------------------------
	# Print the page
	# -------------------------------------------------------------------------

	def OnPrintPage(self, page):

		# Prepare DC to paint on
		dc = self.GetDC()
		# dc.SetFont(wx.NORMAL_FONT)
		dc.SetPen(wx.BLACK_PEN)
		dc.SetBrush(wx.TRANSPARENT_BRUSH)

		# Scale from screen to printer
		screen_ppi_x, screen_ppi_y = self.GetPPIScreen()
		printer_ppi_x, printer_ppi_y = self.GetPPIPrinter()
		scale_x = float(printer_ppi_x) / screen_ppi_x
		scale_y = float(printer_ppi_y) / screen_ppi_y

		# Calculate page margins
		page_width, page_height = self.GetPageSizePixels()
		page_margin_left = page_margin_right  = int(printer_ppi_x*.75+.5)
		page_margin_top  = page_margin_bottom = int(printer_ppi_y*.75+.5)
		page_left   = page_margin_left
		page_top    = page_margin_top
		page_right  = page_width - page_margin_right
		page_bottom = page_height - page_margin_bottom

		# Page header, left
		y = self.draw_text(dc, page_left, page_top, self.__title)
		y = self.draw_text(dc, page_left, y, self.__subtitle)

		# Page header, right
		timestamp = time.strftime(
			"%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
		y = self.draw_text(dc, page_right, page_top, timestamp,
			align_right=True)
		y = self.draw_text(dc, page_right, y, u_('Login: ') + self.__login,
			align_right=True)

		# Page header, line
		dc.DrawLine(page_left, y, page_right, y)
		canvas_top = y + int(printer_ppi_y * 0.25 + 0.5)

		# Page footer, left
		y = self.draw_text(dc, page_left, page_bottom,
			'GNUe Forms %s' % VERSION, align_bottom=True)

		# Page footer, line
		dc.DrawLine(page_left, y, page_right, y)
		canvas_bottom = y - int(printer_ppi_y * 0.25 + 0.5)

		# Space where we can paint the screenshot
		canvas_w = page_right - page_left
		canvas_h = canvas_bottom - canvas_top

		# If necessary, adjust scale factor to fit on page
		w = self.__bitmap.GetWidth()
		h = self.__bitmap.GetHeight()
		if w * scale_x > canvas_w:
			scale_y = float(scale_y) / (w * scale_x / canvas_w)
			scale_x = float(canvas_w) / w
		if h * scale_y > canvas_h:
			scale_x = float(scale_x) / (h * scale_y / canvas_h)
			scale_y = float(canvas_h) / h

		# the actual screenshot with border
		dc.SetUserScale(scale_x, scale_y)
		x = (page_left + canvas_w / 2) / scale_x - w / 2
		y = (canvas_top + canvas_h / 2) / scale_y - h / 2
		dc.DrawBitmap(self.__bitmap, x, y)
		dc.DrawRectangle(x, y, w, h)
		dc.SetUserScale(1, 1)


	# -------------------------------------------------------------------------
	# Draw text and calculate new y position
	# -------------------------------------------------------------------------

	def draw_text(self, dc, x, y, text, align_right=False, align_bottom=False):

		w, h = dc.GetTextExtent(text)

		_x = x
		_y = y

		if align_right:
			_x -= w
		if align_bottom:
			_y -= h

		dc.DrawText(text, _x, _y)

		if align_bottom:
			new_y = y - h * 1.3
		else:
			new_y = y + h * 1.3

		return new_y


# =============================================================================
# Widget configuration
# =============================================================================

configuration = {
	'baseClass': UIForm,
	'provides' : 'GFForm',
	'container': 1,
}
