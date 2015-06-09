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
# $Id: form.py,v 1.27 2012/03/20 13:00:38 oleg Exp $
"""
Implementation of the UI layer for the <form> and <dialog> tag.
"""

import base64

#from gnue.forms.uidrivers.java import dialogs
from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import Frame, Dialog, StatusBar

#from _config import BORDER_SPACE
from toolib.wx.grid.TConfigurable				import TConfigurable

__all__ = ['UIForm']


# =============================================================================
# Interface implementation of a form widget
# =============================================================================

class UIForm(UIWidget, TConfigurable):
	"""
	Interface implementation of form widgets (forms and dialogs)
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):

		UIWidget.__init__(self, event)

		self.__frame = None
		self.__uiContainer = event.uiContainer or self

		self.menuBar = None		# accessed from UIMenu
		self.toolBar = None     # accessed from UIToolbar
		self.__statusBar = None

		# deferred function result consummers
		self.__resultConsumers = {}

		#list of (f, args, kwargs) to call after
		self.__callAfter = []

		# deferred code to execute after modal child finish
		self.__afterModal = None


	def isEmbeded(self):
		return self.__uiContainer is not self

	###########################################################################
	# uiContainer inteface to uiForm
	#
	def getFrame(self):
		assert not self.isEmbeded()
		if self.__frame is None:
			self.__frame = (Dialog if self._gfObject.style == 'dialog' else Frame)(
				self,
				self._gfObject.title,
				self._gfObject.windowStyle,
			)
		return self.__frame

	def getUiForm(self):
		return self

	def getContainer(self, uiForm):
		assert uiForm is self
		return self.getFrame()

	def show(self, uiForm, modal, afterModal):
		assert uiForm is self

		if modal:
			assert self.__afterModal is None, self.__afterModal
			self.__afterModal = afterModal
		
		self.getFrame().uiShow(modal)

	def onAfterModal(self):
		"""
		called by client after modal, only if uiShow had modal=True
		"""
		assert self.__afterModal is not None
		afterModal = self.__afterModal
		self.__afterModal = None
		afterModal()

	def onClose(self):
		"""
		user closing frame on client
		"""
		self._form.close()

	def close(self, uiForm):
		assert uiForm is self
		self.getFrame().uiClose()

	def setTitle(self, uiForm, title):
		assert uiForm is self
		self.getFrame().uiSetTitle(title)

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
		# assume that widget of UIForm is panel because main_window is not allway present
		self.widget = self.__uiContainer.getContainer(self)
		self.__mainFrame = self.__uiContainer.getFrame()

		if self._form.style != 'dialog' and not self._form._features['GUI:STATUSBAR:SUPPRESS']:
			self.__statusBar = StatusBar(self, [-1, 50, 50, 75, 75])
			self.__mainFrame.uiSetStatusBar(self.__statusBar)


	# -------------------------------------------------------------------------
	# Add widgets to the form
	# -------------------------------------------------------------------------

	def addWidget(self, ui_widget):
		"""
		Add a given UI widget to the page.

		@param ui_widget: widget to add to the page
		@param spacer: not used for pages
		"""
		if self.__uiContainer is not self and hasattr(self.__uiContainer, 'addWidget'):
			self.__uiContainer.addWidget(ui_widget)
		else:
			self.widget.uiAdd(ui_widget.widget)


	def onPostInit(self):
		# if not embeded and not maximized
		if self.__uiContainer is self and 'MAXIMIZE' not in self._gfObject.windowStyle:
			self.widget.uiFit()

		if self.menuBar:
			self.__mainFrame.uiSetMenuBar(self.menuBar)

		if self.toolBar:
			self.__mainFrame.uiSetToolBar(self.toolBar)

		super(UIForm, self).onPostInit()

	# -------------------------------------------------------------------------
	# Show the form/dialog
	# -------------------------------------------------------------------------

	def _ui_show_(self, modal, afterModal):
		"""
		If modal is False, afterModal is ignored
		"""
		self._uiDriver.hide_splash()
		if modal:
			self.__uiContainer.show(self, modal, afterModal)
		else:
			self.__uiContainer.show(self, modal, None)
			self.updateBars()

	def updateBars(self):
		if self.toolBar:
			self.__uiContainer.getFrame().uiSetToolBar(self.toolBar)
		else:
			self.__uiContainer.getFrame().uiRemoveToolBar()

		if self.__statusBar:
			self.__uiContainer.getFrame().uiSetStatusBar(self.__statusBar)
		else:
			self.__uiContainer.getFrame().uiRemoveStatusBar()

	# -------------------------------------------------------------------------
	# User feedback functions
	# -------------------------------------------------------------------------

	def _ui_begin_wait_(self):
		"""
		Display the hourglass cursor on all windows of the application.
		"""
		# client does hourglass cursor handling
		pass

	# -------------------------------------------------------------------------

	def _ui_end_wait_(self):
		"""
		Display the normal mouse cursor on all windows of the application.
		"""
		# client does hourglass cursor handling
		pass

	# -------------------------------------------------------------------------

	def _ui_beep_(self):
		"""
		Ring the system bell.
		"""
		self.__mainFrame.uiBeep()

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
				self.__statusBar.uiSetStatusText(tip, 0)

			if record_status is not None:
				self.__statusBar.uiSetStatusText(record_status, 1)

			if insert_status is not None:
				self.__statusBar.uiSetStatusText(insert_status, 2)

			if record_number and record_count:
				self.__statusBar.uiSetStatusText(
					"%s/%s" % (record_number, record_count), 3)

	# -------------------------------------------------------------------------
	# result consumer registry, for deferred invocation
	# -------------------------------------------------------------------------

	def _setResultConsumer(self, name, resultConsumer):
		assert resultConsumer is not None
		#assert name not in self.__resultConsumers
		self.__resultConsumers.setdefault(name, []).append(resultConsumer)

	def _onResult(self, name, result):
		assert name in self.__resultConsumers and self.__resultConsumers[name]
		self.__resultConsumers[name].pop()(result)

	# -------------------------------------------------------------------------
	# Show a message box
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

		@return: True if the Ok-, Close-, or Yes-button was pressed, False if
		        the No-button was pressed or None if the Cancel-button was pressed.

		TODO: no_default to java
		"""
		if self.isEmbeded():
			self.__uiContainer.getUiForm()._ui_show_message_(message, kind, title, cancel, no_default, resultConsumer)
		else:
			if resultConsumer is not None:
				self._setResultConsumer('showMessage', resultConsumer)
			self.getFrame().uiShowMessage(message, kind, title, cancel, bool(resultConsumer))

	def onShowMessage(self, result):
		self._onResult('showMessage', result)

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
		if self.isEmbeded():
			self.__uiContainer.getUiForm()._ui_select_files_(title, defaultDir, defaultFile, wildcard, mode, multiple, overwritePrompt, fileMustExist, readData, resultConsumer, name)
		else:
			self._setResultConsumer('selectFiles', resultConsumer)
			self.getFrame().uiSelectFiles(title, defaultDir, defaultFile, wildcard, mode, multiple, overwritePrompt, fileMustExist, readData)

	def onSelectFiles(self, result):
		if result:
			for i in result:
				if isinstance(i, list):
					i[1] = base64.b64decode(i[1])
		self._onResult('selectFiles', result or None)
	
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
		if self.isEmbeded():
			self.__uiContainer.getUiForm()._ui_select_dir_(title, defaultDir, newDir, resultConsumer, name)
		else:
			self._setResultConsumer('selectDir', resultConsumer)
			self.getFrame().uiSelectDir(title, defaultDir, newDir)

	def onSelectDir(self, result):
		self._onResult('selectDir', result)

	# -------------------------------------------------------------------------

	def _ui_get_shell_folder_(self, shellFolderName, subPath, create, resultConsumer):
		print "* getShellFolder not implemented in java (no way)"
		resultConsumer("")

	# -------------------------------------------------------------------------

	def _ui_set_title_(self, title):
		"""
		Set title of form
		"""
		self.__uiContainer.setTitle(self, title)


	def _ui_show_about_(self, name, version, author, description):
		"""
		Display an about box
		"""
		if version:
			version = _("Version: %s" % version)

		self._ui_show_message_(
			'\n'.join(filter(None, (name, version, author, description))),
			'Info',
			_("About %s") % name,
		)


	def _ui_printout_(self, title, subtitle, user):
		"""
		Print form screenshot
		"""
		self.__mainFrame.uiPrintout(title, subtitle, user)


	# -------------------------------------------------------------------------
	# Close the window (actually only hide it)
	# -------------------------------------------------------------------------

	def _ui_close_(self):
		self.__uiContainer.close(self)

	def _ui_destroy_(self):
		if not self.isEmbeded():
			self.getFrame().uiDestroy()
	
	def _forgetUiContainer(self):
		self.__uiContainer = None

	def _ui_call_after_(self, f, *args, **kwargs):
		if self.isEmbeded():
			self.__uiContainer.getUiForm()._ui_call_after_(f, *args, **kwargs)
		else:
			self.__callAfter.append((f, args, kwargs))
			self.getFrame().uiCallAfter()

	def onCallAfter(self):
		assert self.__callAfter
		f, args, kwargs = self.__callAfter.pop()
		f(*args, **kwargs)
		

	def _ui_download_file_(self, url, path, quiet):
		self.__mainFrame.uiDownloadFile(url, path, quiet)

	def _ui_start_file_(self, url, fileName):
		return self.__mainFrame.uiStartFile(url, fileName)

	def _ui_upload_file_(self, path, url, resultConsumer):
		if self.isEmbeded():
			self.__uiContainer.getUiForm()._ui_upload_file_(path, url, resultConsumer)
		else:
			self._setResultConsumer('uploadFile', resultConsumer)
			return self.__mainFrame.uiUploadFile(path, url)

	def onUploadFile(self, result):
		self._onResult('uploadFile', result)
		

	def _ui_show_exception_(self, group, name, message, detail):
		if self.isEmbeded():
			self.__uiContainer.getUiForm()._ui_show_exception_(group, name, message, detail)
		else:
			self.getFrame().uiShowException(
				group or '', 
				name or '', 
				message or '', 
				detail or ''
			)


# =============================================================================
# Widget configuration
# =============================================================================

configuration = {
	'baseClass': UIForm,
	'provides' : 'GFForm',
}
