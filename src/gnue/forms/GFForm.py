# GNU Enterprise Forms - GF Object Hierarchy - Form
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
# $Id: GFForm.py,v 1.73 2014/10/20 15:00:17 Oleg Exp $
"""
Class that contains the internal python object representation of a GNUe Form
built from GFObjects
"""

import os
import sys
import tempfile
import thread
from urllib2 import urlopen, HTTPError, Request

from gnue.common.apps import i18n, errors
from gnue.common import events
from gnue.common.datasources.Exceptions import ConnectionError as DBError
from gnue.common.definitions.GRootObj import GRootObj
from gnue.common.definitions.GObjects import GObj
from gnue.common.datasources import ConnectionTriggerObj
from gnue.forms.GFObjects.GFTabStop import GFFieldBound
from gnue.forms.GFObjects import *
from gnue.forms.GFObjects.GFObj import UnresolvedNameError
from gnue.forms import GFParser
from gnue.common.utils import CaselessDict
from gnue.common.datasources.access import ACCESS
from gnue.common.logic.language import AbortRequest
from toolib.db import simpleconn

IO_BUF_SIZE = 65536

# =============================================================================
# Exceptions
# =============================================================================

class DataSourceNotFoundError(UnresolvedNameError):
	def __init__(self, source, name, referer=None):
		UnresolvedNameError.__init__(self, source, 'Datasource', name, referer)

# =============================================================================

class UndefinedParameterError(errors.ApplicationError):
	"""
	A parameter that is assigned a value is not defined.
	"""
	def __init__(self, name):
		errors.ApplicationError.__init__(self, u_(
				"Parameter '%(name)s' not defined in the form") % {'name': name})

# =============================================================================
# Implementation of the form tag
# =============================================================================

class GFForm(GRootObj, GFObj, events.EventAware):
	"""
	Contains the internal python object representation of a GNUe Form built
	from GFObjects.
	"""

	description = None

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):

		GRootObj.__init__(self, 'form', GFParser.getXMLelements, GFParser)
		GFObj.__init__(self, parent, 'GFForm')

		self.name = "__main__"

		# Datasources referced by this form
		self._datasourceDictionary = {}

		# Dictionary to locate named triggers
		self._triggerDictionary = {}

		# Dictionary to locate actions
		self._actions = {}

		# Dictionary with all the subforms
		self.__subforms = {}

		# Dictionary to locate parameters
		self.__parameter_dict = {}

		# Insert/Overwrite mode
		self.__insert_mode = True

		# Focus information
		self._currentBlock = None
		self._currentEntry = None

		# Is the form in filter mode?
		self.__in_filter_mode = False

		# Set to true while focus is moving so a record change in
		# focusin/focusout triggers doesn't run endEditing and beginEditing
		self.__editing_blocked = False

		self._instance = None

		# Hackery until proper layout support is added
		self._standardnamespaces = {'Char': 'GNUe:Forms:Char'}

		# Is this form currently open?
		self.__visible = False

		# Is this form still opening
		self.__opening = False

		# not None means initialize later with this args
		self.__lazyInitializeArgs = None
		self.__subform = False

		# helper cache used only in __return_if_changed
		self.__return_if_changed_cache = {}

		# The "None" init gives datasources time to setup master/detail
		self._inits.extend([self.phase_2_init, self.phase_3_init])

		# Trigger support
		self._triggerns = {}
		self._triggerGlobal = True

		self._entryList = []

		self._validTriggers = {
			'ON-STARTUP':      'On-Startup',
			'ON-ACTIVATION':   'On-Activation',
			'ON-POPUP':        'On-Popup',
			'ON-STATUSCHANGE': 'On-StatusChange',
			'PRE-EXIT':        'Pre-Exit',
			'ON-EXIT':         'On-Exit',
			'PRE-COMMIT':      'Pre-Commit',
			'POST-COMMIT':     'Post-Commit'}

		self._triggerFunctions = {
			# User feedback and interaction
			'beep': {'function': self.beep, 'global': True},
			'status_message': {'function': self.status_message},
			'show_message': {'function': self.show_message},
			'error' : { 'function': self.error, 'global': True },
			'selectFiles': {'function': self.selectFiles},
			'selectDir': {'function': self.selectDir},
			'show_about': {'function': self.show_about},
			'show_dialog': {'function': self.show_dialog, 'global' : True },

			'downloadFile' : {'function' : self.__trigger_downloadFile},
			'startFile' : {'function' : self.__trigger_startFile},
			'uploadFile' : {'function' : self.__trigger_uploadFile},
			'getShellFolder' : {'function' : self.__trigger_getShellFolder},

			# Clipboard and selection
			'cut': {'function': self.cut},
			'copy': {'function': self.copy},
			'paste': {'function': self.paste},
			'select_all': {'function': self.select_all},

			# Focus movement
			'next_entry': {'function': self.next_entry},
			'previous_entry': {'function': self.previous_entry},
			'next_block': {'function': self.next_block},
			'previous_block': {'function': self.previous_block},
			'get_focus_block': {'function': self.__trigger_get_focus_block},

			# Record navigation
			'first_record': {'function': self.first_record},
			'prev_record': {'function': self.prev_record},
			'next_record': {'function': self.next_record},
			'last_record': {'function': self.last_record},
			'ask_record': {'function': self.ask_record},

			# Record insertion and deletion
			'new_record': {'function': self.new_record},
			'delete_record': {'function': self.delete_record},
			'undelete_record': {'function': self.undelete_record},

			# Filter
			'init_filter': {'function': self.init_filter},
			'change_filter': {'function': self.change_filter},
			'discard_filter': {'function': self.discard_filter},
			'apply_filter': {'function': self.apply_filter},
			'in_filter_mode': {'function': self.in_filter_mode},

			# raw connection
			'raw_connection' : {'function': self.__trigger_raw_connection, 'global': True},

			# Transactions
			'commit': {'function': self.commit, 'global': True},
			'rollback': {'function': self.rollback, 'global': True},
			'is_saved': {'function': self.is_saved},
			'refresh': {'function': self.refresh},

			# Other stuff
			'fire_trigger': {'function': self.fire_trigger},
			'run_form': {'function': self.__trigger_run_form},

			'run_report': {'function': self.run_report},
			'toggle_insert_mode': {'function': self.toggle_insert_mode},
			'get_username': {'function': self.get_username},
			'get_uidriver_name': {'function': self.get_uidriver_name, 'global': True},
			'printout': {'function': self.printout},
			'close': {'function': self.close, 'global': True},

			'set_global': {'function': self.__trigger_setGlobal, 'global': True},
			'get_global': {'function': self.__trigger_getGlobal, 'global': True},

			'set_clientproperty': {'function': self.__trigger_set_clientproperty, 'global': True},
			'get_clientproperty': {'function': self.__trigger_get_clientproperty, 'global': True},

			'call_after': {'function': self.call_after, 'global': True},

			'endEditing': {'function': self.endEditing, 'global': True},
			'beginEditing': {'function': self.beginEditing, 'global': True},

			'run_job': {'function': self.run_job, 'global': True},

			'test': {'function': self.__test},

			# Deprecated functions

			'activateTrigger': {
				'function': self.fire_trigger,
				'global': True},
			'runForm': {
				'function': self.run_form,
				'global': True},
			'runReport': {
				'function': self.run_report,
				'global': True},

			'init_query': {'function': self.init_filter},
			'copy_query': {'function': self.change_filter},
			'cancel_query': {'function': self.discard_filter},
			'execute_query': {'function': self.apply_filter},
			'in_query_mode': {'function': self.in_filter_mode},

			'getAuthenticatedUser': {
				'function': self.get_username,
				'global'  : True},
			'getFeature': {
				'function': self.__trigger_get_feature,
				'global': True},
			'setFeature': {
				'function': self.__trigger_set_feature,
				'global': True},
			'getParameter': {
				'function': self.__trigger_get_parameter,
				'global'  : True},
			'setParameter': {
				'function': self.__trigger_set_parameter,
				'global'  : True},
			'setFocus': {
				'function': self.__trigger_set_focus,
				'global'  : True}}

		self._triggerProperties = {
			'name': {
				'get': lambda: self.name,
			},
			'title': {
				'get': lambda: self.title,
				'set': self.set_title,
			},
			'logic': {
				'get': lambda: self._logic.get_namespace_object(),
			},
			'toolbar': {
				'get': lambda: self._toolbar.get_namespace_object(),
			},
			'globals': {
				'get': lambda: self._instance.getGlobals(),
			},
		}

		self._features = {
			'GUI:MENUBAR:SUPPRESS': False,
			'GUI:TOOLBAR:SUPPRESS': False,
			'GUI:STATUSBAR:SUPPRESS': False,
		}

		self._in_trigger_lock = False


	# -------------------------------------------------------------------------
	# Object initialization
	# -------------------------------------------------------------------------

	def _buildObject(self):

		# Find the logic and layout controllers
		for child in self._children:
			if child._type == 'GFLogic':
				self._logic = child
			elif child._type == 'GFLayout':
				self._layout = child
			elif child._type == 'GFToolbar':
				self._toolbar = child

		# Build parameter dictionary
		for child in self._children:
			if child._type == 'GFParameter':
				self.__parameter_dict[child.name] = child

		return GFObj._buildObject(self)


	# -------------------------------------------------------------------------
	# Initialize the form and merge default form into this form
	# -------------------------------------------------------------------------

	def initialize(self, default_form, gfContainer):
		"""
		Initialize the form and all its dialogs.

		@param gfContainer: GFObject that want to be ui container for this form
		"""

		# Extract dialogs contained in this form tree, so later in phaseInit,
		# each object really sees the correct root object.
		# Note that we can't do this in _buildObject, since it may not run for
		# imported gfd's.
		for child in self._children[:]:
			if isinstance(child, GFForm):
				child.setParent(None)
				self.__subforms[child.name] = child
				self._children.remove(child)

		# Merge in default menu and toolbar.
		self.merge(default_form)

		# Merge extras and help menus into the main menu.
		main_menu = self.findChildNamed('__main_menu__', 'GFMenu')
		extra_menu = self.findChildNamed('__extra_menu__', 'GFMenu')
		help_menu = self.findChildNamed('__help_menu__', 'GFMenu')
		if extra_menu:
			main_menu.merge(extra_menu)
			extra_menu.setParent(None)
			self._children.remove(extra_menu)
		if help_menu:
			main_menu.merge(help_menu)
			help_menu.setParent(None)
			self._children.remove(help_menu)

		self.__gfContainer = gfContainer
		self.phaseInit()

		for subform in self.__subforms.itervalues():
			subform._instance = self._instance
			subform._connections = self._connections

			# call initialize later
			# 1. fixes problem with wx.Dialog:
			# wx.Dialog returns focus on component that had focus when wx.Dialog was created
			# 2. subform may be never initialized (optimization)
			subform.subformLazyInitialize(default_form, None)

	def subformLazyInitialize(self, *args):
		"""
		remember that it is subform
		defer initialize call until execute_open
		"""
		self.__subform = True
		self.__lazyInitializeArgs = args

	# -------------------------------------------------------------------------
	# Phase 1 initialization
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		"""
		Called automatically during phaseInit() startup of GParser.
		"""
		GFObj._phase_1_init_(self)

		events.EventAware.__init__(self, self._instance.eventController)

		# Add all connections as children, so they are accessible in the
		# action/trigger namespace.
		ConnectionTriggerObj.add_connections_to_tree(
			self._instance.connections, self)


	# -------------------------------------------------------------------------
	# Phase 2 initialization
	# -------------------------------------------------------------------------

	def phase_2_init(self):
		"""
		Called automatically during phaseInit() startup of GParser.
		"""

		# Trigger system may not be initialized earlier, because imported
		# elements (e.g. <import-block>) are moved into the form tree in phase
		# 1 init.
		self.initTriggerSystem()
		self._triggerns.update(self._triggerNamespaceTree._globalNamespace)

		# support gettext in triggers
		self._triggerns['u_'] = self._triggerns['_'] = lambda text: i18n.getCatalog('forms').ugettext(unicode(text, 'UTF-8'))

	# -------------------------------------------------------------------------
	# Phase 3 initialization
	# -------------------------------------------------------------------------

	def phase_3_init(self):
		"""
		Called automatically during phaseInit().  It must happen after all
		children have init'ed.
		"""

		# First of all, run the On-Startup trigger so it can suppress the tool
		# bar, menu bar or status line. This of course means that the blocks
		# are not yet populated while this trigger runs.
		self.processTrigger('On-Startup')

		# build the UI form, _uiinstance is UIDriver instance
		self._instance._uiinstance.buildForm(self, self.__gfContainer)

		# populate the blocks
		for block in self._logic._blockList:
			block.populate()

		self.update_insert_status()


	# -------------------------------------------------------------------------
	# Set and get parameters for the form
	# -------------------------------------------------------------------------

	def set_parameters(self, parameters):
		"""
		Set the parameters for this form.

		@param parameters: Dictionary with name/value pairs.
		"""

		for (name, value) in parameters.iteritems():
			if name in self.__parameter_dict:
				self.__parameter_dict[name].value = value
			else:
				raise UndefinedParameterError(name)

	# -------------------------------------------------------------------------

	def get_parameters(self):
		"""
		Return the current parameter values of the form.

		@return: Current parameter values.
		@rtype: dict
		"""

		result = {}
		for parameter in self.__parameter_dict.itervalues():
			result[parameter.name] = parameter.value
		return result


	# -------------------------------------------------------------------------
	# Open (activate) the form
	# -------------------------------------------------------------------------

	def execute_open(self, modal, afterOpen):
		
		if self.__lazyInitializeArgs:
			self.initialize(*self.__lazyInitializeArgs)
			self.__lazyInitializeArgs = None

		self.initFocus()

		assert gDebug(4, "Processing activation trigger")
		# Switch off editing mode so the On-Activation trigger can cleanly
		# change the field value even of the first field in the form. Usually,
		# changing the value of a field while an associated entry is in editing
		# mode doesn't work.

		self.__opening = True

		self.endEditing()
		self.processTrigger('On-Activation')
		self.beginEditing()

		self.__visible = True

		# ON-ACTIVATION trigger may close the form, this will set __opening to False
		if self.__opening:
		
			assert gDebug(4, "Activating form")
			if modal:
				self.uiWidget._ui_show_(True, afterOpen)
			else:
				self.uiWidget._ui_show_(False, None)
				if afterOpen is not None:
					afterOpen()
		else:
			# still execute after modal
			if afterOpen is not None:
				afterOpen()

	def initFocus(self):
		# Set initial focus
		self.__find_and_change_focus([self._layout], False)
	#rint "initial focus set to", self._currentBlock, self._currentEntry

	# -------------------------------------------------------------------------
	# UI events (called from UIForm)
	# -------------------------------------------------------------------------

	def _event_focus_changed(self, target):
		"""
		Notify the form that the user has moved the focus with a mouse click.

		This method makes sure that the logical focus follows the physical
		focus.

		In case the current focus widget vetoes the focus loss, this method
		beats the focus back to the old widget.
		"""
		#rint "GFForm: _event_focus_changed", target._field

		# Most UIs issue a SET_FOCUS event also when the focus moves from
		# another window to this one. We don't need to do anything in this
		# case.
		if self.get_focus_object() is not target:
			try:
				self.endEditing()
				try:
					self.__move_focus(target, 0)
				finally:
					self.beginEditing()
			except:
				# Old focus entry has invalid value: beat the UI focus back, so we
				# are captured until the value is corrected.
				# FIXME: if there is a way (on some UIs) to veto the focus change
				# on UI layer, this should be the prefered method
				if self._currentEntry is not None:
					self._currentEntry.ui_set_focus()
				raise

	# =========================================================================
	# Events
	# =========================================================================

	# -------------------------------------------------------------------------
	# Function to be called at the begin of event handling code
	# -------------------------------------------------------------------------

	def event_begin (self):
		"""
		Start handling of a user event.

		This function has to be called at the beginning of each user event
		being handled. At the end of handling the user event, L{event_end} has
		to be called.

		Currently, these functions only turn on and off the hourglass mouse
		cursor.
		"""

		if self.uiWidget is not None:
			self.uiWidget._ui_begin_wait_()


	# -------------------------------------------------------------------------
	# Function to be called at the end of event handling code
	# -------------------------------------------------------------------------

	def event_end (self):
		"""
		End handling of a user event.

		This function has to be called at the end of each user event being
		handled, just like L{event_begin} is called at the beginning.

		Currently, these functions only turn on and off the hourglass mouse
		cursor.
		"""

		if self.uiWidget is not None:
			self.uiWidget._ui_end_wait_()


	# =========================================================================
	# User feedback
	# =========================================================================

	def set_title(self, title):
		"""
		Sets and displays the title of the form.

		@param title: new title
		"""
		self.title = title
		self.__ui_update_title()

	# -------------------------------------------------------------------------

	def alert_message(self, message):

		self.status_message(message)
		self.beep()

	# -------------------------------------------------------------------------

	def beep(self):
		"""
		Makes a noise.
		"""
		if self.uiWidget is not None:
			self.uiWidget._ui_beep_()

	# -------------------------------------------------------------------------

	def status_message(self, message):
		"""
		Displays a custom message on the form's status bar.
		@param message: message to be displayed
		"""

		self.__update_status(tip=message)

	# -------------------------------------------------------------------------

	def show_message(self, message, kind='Info', title=None, cancel=False, no_default=False, resultConsumer=lambda x: x):
		"""
		This function brings up a message box of a given kind.
		@param message: text to be displayed
		@param kind: 'Question', 'Info', 'Warning', or 'Error'
		@param cancel: Boolean flag indicating wether a cancel button will be
		    included or not.
		@return: True for <Yes> or <Ok> button, False for <No> button, None for
		    <Cancel> button.
		"""
		if self.uiWidget is not None:
			if title is None:
				title = self.title
			return self.uiWidget._ui_show_message_(message, kind, title, cancel, no_default, resultConsumer)

	def error(self, message):
		return errors.UserError(message)

	# -------------------------------------------------------------------------

	def selectFiles(self, title, defaultDir, defaultFile, wildcard=[],
		mode='open', multiple=False, overwritePrompt=True,
		fileMustExist=False, readData=False, resultConsumer=lambda x: x, name=None):
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
		@param readData: if True, returns the sequence of tuples (filename, data)
		@param name: name used to save last directory at client local storage

		@returns: a sequence of filenames or None if the dialog has been
		    cancelled.
		"""
		if self.uiWidget is not None:
			return self.uiWidget._ui_select_files_(title, defaultDir,
				defaultFile, wildcard, mode, multiple, overwritePrompt,
				fileMustExist, readData, resultConsumer, name or 'default')

	# -------------------------------------------------------------------------

	def selectDir(self, title, defaultDir, newDir=False, resultConsumer=lambda x: x, name=None):
		"""
		Bring up a dialog for selecting a directory path.

		@param title: Message to show on the dialog
		@param defaultDir: the default directory, or the empty string
		@param newDir: If true, add "Create new directory" button and allow
		    directory names to be editable. On Windows the new directory button
		    is only available with recent versions of the common dialogs.

		@returns: a path or None if the dialog has been cancelled.
		"""
		if self.uiWidget is not None:
			return self.uiWidget._ui_select_dir_(title, defaultDir, newDir, resultConsumer, name or 'default')

	# -------------------------------------------------------------------------

	def show_about(self):

		if self.uiWidget is not None:
			self.uiWidget._ui_show_about_(
				self.title or "Unknown",
				self.get_option('version') or "Unknown",
				self.get_option('author') or "Unknown",
				self.get_option('description') or "Unknown")

	# -------------------------------------------------------------------------

	def show_dialog (self, name, parameters=None, modal=False, resultConsumer=lambda x: None):
		"""
		Launches a standard or a custom dialog.
		@param name: name of the dialog to be displayed
		@param parameters: dictionary of parameters used to pass values
		                    back and forth
		@param modal: whether the dialog should be modal or not
		@return: None
		"""
		form = self.__subforms[name]
		if parameters is not None:
			form.set_parameters(parameters)
		
		def afterOpen():
			
			if parameters is not None:
				parameters.update(form.get_parameters())
			
			resultConsumer(parameters)

		if modal:
			form.execute_open(modal, afterOpen)
		else:
			form.execute_open(modal, None)
			afterOpen()
			
		

	def __trigger_downloadFile(self, url, path, quiet=False):
		if hasattr(self.uiWidget, '_ui_download_file_'):
			# remote clients must define this method
			self.uiWidget._ui_download_file_(url, path, quiet)
		else:
			try:
				response = urlopen(url)
				if response:
					f = open(path, 'wb')
					try:
						while True:
							buf = response.read(IO_BUF_SIZE)
							if not buf:
								break
							f.write(buf)
					finally:
						response.close()
						f.close()
						if not quiet:
							self.call_after(self.show_message, _("File saved: %s") % (path,), 'info')
				else:
					raise self.error(_("Empty response from server"))
			except HTTPError, e:
				if e.code == 502:
					raise self.error(_("No response from server\n%s") % e)
				elif e.code == 403:
					raise self.error(str(e))
				else:
					raise

	def __trigger_startFile(self, url, fileName):
		if hasattr(self.uiWidget, '_ui_start_file_'):
			# remote clients must define this method
			self.uiWidget._ui_start_file_(url, fileName)
		else:
			path = tempfile.mktemp(fileName)
			self.__trigger_downloadFile(url, path, quiet=True)
			os.startfile(path)

	def __trigger_uploadFile(self, path, url, resultConsumer=lambda x: x):
		if hasattr(self.uiWidget, '_ui_upload_file_'):
			# remote clients must define this method
			self.uiWidget._ui_upload_file_(path, url, resultConsumer)
		else:
			try:
				body = open(path, 'rb').read()
				headers = {
					'Content-Type'   : 'application/octet-stream',
					'Content-Length' : len(body),
				}
				response = urlopen(Request(url, body, headers))
				if response:
					return resultConsumer(response.read())
				else:
					raise self.error(_("Empty response from server"))
			except HTTPError, e:
				if e.code == 502:
					raise self.error(_("No response from server\n%s") % e)
				elif e.code == 403:
					raise self.error(str(e))
				else:
					raise
		

	def __trigger_getShellFolder(self, shellFolderName='PERSONAL', subPath=(), create=False, resultConsumer=lambda x: x):
		"""
		shellFolderName is like "PERSONAL" from  CSIDL_PERSONAL
		"""
		if hasattr(self.uiWidget, '_ui_get_shell_folder_'):
			# remote clients must define this method
			self.uiWidget._ui_get_shell_folder_(shellFolderName, subPath, create, resultConsumer)
		else:
			path = None
			try:
				from toolib.win32 import shell
				path = shell.getSpecialFolderPath(shellFolderName)
			except:
				print "* shell folders supported only on windows"

			if path:
				if os.path.exists(path):
					path = os.path.join(path, *subPath)
					if create and not os.path.exists(path):
						os.makedirs(path)
				else:
					path = None
					print "* shell folder '%s' not exist: %s" % (shellFolderName, path)

			return resultConsumer(path)

	# =========================================================================
	# Clipboard and selection
	# =========================================================================

	# -------------------------------------------------------------------------
	# Clipboard
	# -------------------------------------------------------------------------

	def cut(self):
		"""
		Cut the selected portion of the current entry into the clipboard.
		"""

		if isinstance(self._currentEntry, GFFieldBound):
			self._currentEntry.cut()

	# -------------------------------------------------------------------------

	def copy(self):
		"""
		Copy the selected portion of the current entry into the clipboard
		"""

		if isinstance(self._currentEntry, GFFieldBound):
			self._currentEntry.copy()

	# -------------------------------------------------------------------------

	def paste(self):
		"""
		Paste the content of the clipboard into the current entry.
		"""

		if isinstance(self._currentEntry, GFFieldBound):
			self._currentEntry.paste()

	# -------------------------------------------------------------------------
	# Selection
	# -------------------------------------------------------------------------

	def select_all(self):
		"""
		Select all text on the current entry.
		"""

		if isinstance(self._currentEntry, GFFieldBound):
			self._currentEntry.select_all()

	# =========================================================================
	# Focus functions
	# =========================================================================

	# -------------------------------------------------------------------------
	# Next/previous entry
	# -------------------------------------------------------------------------

	def next_entry(self, reverse=False):
		"""
		Called whenever an event source has requested that the focus change
		to the next data entry object.
		@param reverse: boolean, step focus in reverse direction?
		"""

		origEntry = self._currentEntry

		#rint '>>> origEntry', origEntry

		if self._currentEntry is not None:
			if reverse:
				self._currentEntry.processTrigger('ON-PREVIOUS-ENTRY', ignoreAbort = False)
			else:
				self._currentEntry.processTrigger('ON-NEXT-ENTRY',     ignoreAbort = False)

		# If the trigger changed focus, no need in us doing it too...
		if self._currentEntry != origEntry:
			return

		currentBlock = self._currentBlock

		#rint ">>> currentBlock", currentBlock

		mode = self.getCurrentMode()

		if currentBlock is None or (
				currentBlock.transparent and not (
					currentBlock.autoNextRecord and not (
						currentBlock.get_record_status() in [None, 'empty'] or
						(not reverse and currentBlock.is_last_record() and
							not (currentBlock.autoCreate and
								currentBlock.hasAccess(ACCESS.INSERT)) or
							(reverse and currentBlock.is_first_record())
						)))):
			source = self._layout.get_focus_order()
			stayInBlock = False
		else:
			source = currentBlock.get_focus_order()
			stayInBlock = True

		#rint ">>> source", source
		#rint ">>> stayInBlock", stayInBlock

		# If we want the previous entry, then reverse the focusorder we're using
		if reverse:
			source.reverse()

		nextEntry = None
		firstEntry = None
		keepNext = False

		for object in source:

			if object.is_navigable(mode):
				if stayInBlock and \
					(currentBlock.name != object.block):
					continue

				# Put the first field as the next to rollover
				if nextEntry == None:
					nextEntry = object
					firstEntry = object

				# If we're at the current focused entry,
				# then the next entry will be what we want
				if object == self._currentEntry or self._currentEntry is None:
					keepNext = True

				# If we've already passed the current entry
				# Then this is the entry to return
				elif keepNext:
					nextEntry = object
					break

		#rint ">>> nextEntry firstEntry", nextEntry, firstEntry

		# If we've cycled back around to the first entry, then do special checks
		if nextEntry == firstEntry:

			# If we should navigate to the next record, do it...
			if currentBlock is not None \
				and reverse and currentBlock.autoNextRecord \
				and not currentBlock.is_first_record():
				self.change_focus(nextEntry, -1)
			elif currentBlock is not None and not reverse and \
				currentBlock.autoNextRecord and \
				not currentBlock.get_record_status() in [None, 'empty'] and \
				not (not currentBlock.autoCreate and \
					currentBlock.is_last_record()):
				self.change_focus(nextEntry, +1)

			else:
				self.change_focus(nextEntry, 0)

		else:
			self.change_focus(nextEntry, 0)

	# -------------------------------------------------------------------------

	def previous_entry(self):
		"""
		Called whenever an event source has requested that the focus change
		to the previous data entry object.
		"""

		self.next_entry(reverse=True)


	# ------------------------------------------------------------------------
	# Next/previous block
	# -------------------------------------------------------------------------

	def next_block(self):
		"""
		Change focus to the next data entry block.
		@return: None
		"""

		if self._currentBlock is not None:
			# Find next block with navigable entries.
			blocks = self._logic._blockList
			current_index = blocks.index(self._currentBlock)
			list = blocks[current_index+1:] + blocks[:current_index]
			self.__find_and_change_focus(list, False)

	# -------------------------------------------------------------------------

	def previous_block(self):
		"""
		Change focus to the previous data entry block.
		@return: None
		"""

		if self._currentBlock is not None:
			# Find next block with navigable entries.
			blocks = self._logic._blockList
			current_index = blocks.index(self._currentBlock)
			list = blocks[current_index+1:] + blocks[:current_index]
			list.reverse()
			self.__find_and_change_focus(list, False)


	# -------------------------------------------------------------------------
	# Move the focus to a new object
	# -------------------------------------------------------------------------

	def __find_and_change_focus(self, list, last):
		entry = self.__find_focus(list, last)
		if entry:
			self.change_focus(entry, 0)


	# -------------------------------------------------------------------------
	# Find the next focusable item within a list of objects
	# -------------------------------------------------------------------------

	def __find_focus(self, list, last):
		if last:
			list = list[:]              # Don't mess with the parameter!
			list.reverse()

		for object in list:
			if isinstance(object, GFTabStop):
				# Trivial case: the focus object itself.
				if object.is_navigable(self.getCurrentMode()):
					return object
				else:
					continue

			elif isinstance(object, GFContainer):
				# Container: search for the first focusable object.
				new_list = object.get_focus_order()

			elif isinstance(object, GFField):
				# Field: search for the first focusable entry attached to it.
				new_list = object._entryList

			else:
				new_list = []

			new_focus = self.__find_focus(new_list, last)
			if new_focus:
				return new_focus
			elif isinstance(object, GFLayout):
				# Allow empty layoout to be focused
				return object

		# Nothing found.
		return None


	# -------------------------------------------------------------------------
	# Return the editing mode of the current record
	# -------------------------------------------------------------------------

	def getCurrentMode(self):
		"""
		Returns the editing mode of the current record
		@return: 'query', 'new' or 'edit'
		"""
		if self.__in_filter_mode:
			return 'query'
		elif self._currentBlock is not None \
			and self._currentBlock.get_record_status() \
			not in [None, 'empty', 'new']:
			return 'edit'
		else:
			return 'new'


	# -------------------------------------------------------------------------
	# Changes to the requested entry object requested by an event source
	# -------------------------------------------------------------------------

	def change_focus(self, widget, row_offset):
		"""
		Changes focus to the requested entry object on GF and UI layer.

		@param widget: entry or page to put focus on. If it is a page, the form
		    changes to that page and does not focus any widget. This is useful
		    to activate a page without a focusable widget on it.
		"""

		self.endEditing()
		try:
			self.__move_focus(widget, row_offset)
		finally:
			if self._currentEntry is not None:
				self._currentEntry.ui_set_focus()
			self.beginEditing()


	# -------------------------------------------------------------------------
	# Changes to the requested entry object requested by an event source
	# -------------------------------------------------------------------------

	def __move_focus(self, widget, row_offset):
		"""
		Changes focus to the requested entry object on GF layer.

		@param widget: entry to put focus on
		@param row_offset: number of rows to jump up or down in new widget
		"""
		assert gDebug(5, "Change focus: %s->%s" % (self._currentEntry, widget))

		if isinstance(widget, GFTabStop):
			new_entry = widget
			new_block = widget.get_block()
		else:
			new_entry = None
			new_block = None

		# if we move the record pointer, we also want to run the block-level
		# focus in and focus out triggers
		blockChange = (new_block != self._currentBlock) or row_offset != 0

		self.__editing_blocked = True

		try:
			if self._currentEntry:
				# Validation triggers
				self._currentEntry.validate()
				field = self._currentEntry.get_field()
				if field is not None:
					field.validate()
				if blockChange:
					if self._currentBlock is not None:
						self._currentBlock.validate()

				# Focus-Out triggers
				self._currentEntry.focus_out()
				field = self._currentEntry.get_field()
				if field is not None:
					field.focus_out()
				if blockChange:
					if self._currentBlock is not None:
						self._currentBlock.focus_out()

			# Set Focus to nowhere while we move the record pointer, so no focus
			# magic will happen now.
			self._currentEntry = None
			self._currentBlock = None

			if row_offset == 1:
				# Special case: next_record() can also trigger a new_record()
				new_block.next_record()
			elif row_offset != 0:
				new_block.jump_records(row_offset)

			self._currentEntry = new_entry
			self._currentBlock = new_block

			# Focus-In triggers
			if self._currentEntry is not None:
				if blockChange:
					if self._currentBlock is not None:
						self._currentBlock.focus_in()
				field = self._currentEntry.get_field()
				if field is not None:
					field.focus_in()
				self._currentEntry.focus_in()
		finally:
			self.__editing_blocked = False

		# The Focus-In trigger of the block has already refreshed the toolbar,
		# except for the case where the new entry has no block.
		if self._currentBlock is None:
			self.status_changed()


	# -------------------------------------------------------------------------
	# Info about focus position
	# -------------------------------------------------------------------------

	def get_focus_block(self):
		"""
		Return the block that currently has the focus.
		"""
		return self._currentBlock

	# -------------------------------------------------------------------------

	def __trigger_get_focus_block(self):
		if self._currentBlock is not None:
			return self._currentBlock.get_namespace_object()
		else:
			return None

	# -------------------------------------------------------------------------

	def get_focus_object(self):
		"""
		Return the block that currently has the focus.
		"""
		return self._currentEntry


	# =========================================================================
	# Data navigation and manipulation
	# =========================================================================

	# -------------------------------------------------------------------------
	# Record navigation
	# -------------------------------------------------------------------------

	def first_record(self):
		"""
		Jumps to the first record in the current block.
		"""
		if self._currentBlock is not None:
			self._currentBlock.first_record()

	# -------------------------------------------------------------------------

	def prev_record(self):
		"""
		Steps to the previous record in the current block.
		"""
		if self._currentBlock is not None:
			self._currentBlock.prev_record()

	# -------------------------------------------------------------------------

	def next_record(self):
		"""
		Steps to the next record in the current block.
		"""
		if self._currentBlock is not None:
			self._currentBlock.next_record()

	# -------------------------------------------------------------------------

	def last_record(self):
		"""
		Jumps to the last record in the current block.
		"""
		if self._currentBlock is not None:
			self._currentBlock.last_record()

	# -------------------------------------------------------------------------

	def ask_record(self):
		"""
		Ask the user for a record number to jump to in the current block.
		"""

		if self._currentBlock is None:
			return

		fields = [(u_("Recordnumber"), 'record', 'string',
				str(self._currentBlock._currentRecord + 1), None, [])]

		while True:
			result = self._instance._uiinstance.getInput(u_("Jump to record"),
				fields)
			if result is None:
				return
			try:
				count = int(result['record'])
				# Positive start to count by zero
				if count > 0: count -= 1
				break
			except ValueError:
				fields = [
					(u_("Invalid numeric value entered."), None, 'warning',
						None, None, []),
					(u_("Recordnumber"), 'record', 'string',
						result['record'], None, [])]

		self._currentBlock.goto_record(count)

	# -------------------------------------------------------------------------

	def jump_records(self, count):
		"""
		Jumps to a given record in the current block.
		@param count: number of records to move
		"""
		if self._currentBlock is not None:
			self._currentBlock.jump_records(count)


	# -------------------------------------------------------------------------
	# Record insertion and deletion
	# -------------------------------------------------------------------------

	def new_record(self):
		"""
		Create a new, empty record in the current block.
		"""

		if self._currentBlock is not None:
			self._currentBlock.new_record()

	# -------------------------------------------------------------------------

	def delete_record(self):
		"""
		Deletes the current record.
		"""

		if self._currentBlock is not None:
			self._currentBlock.delete_record()

	# -------------------------------------------------------------------------

	def undelete_record(self):
		"""
		Undeletes the current record.
		"""

		if self._currentBlock is not None:
			self._currentBlock.undelete_record()


	# -------------------------------------------------------------------------
	# Queries
	# -------------------------------------------------------------------------

	def init_filter(self):
		"""
		Enters the form into Query mode.
		"""

		# self.endEditing()         # happens via _focus_out()

		# We *must* run _focus_out() here: letting the user leave an entry
		# with an invalid value here would make it possible to enter an
		# invalid value, switch to filter mode, move the focus somewhere
		# else, cancel the filter (and so getting back the original result
		# set) and then saving the unchecked data.
		# The _focus_out() can run outside the try-except block because it
		# already does the beginEditing in case of an exception.
		if self._currentBlock is not None:
			self._currentBlock._focus_out()

		try:
			if not self._must_save():
				# We must refresh the UI events now as otherwise the "init
				# filter" button will stick in.
				self.status_changed()
				self.beginEditing()
				return

			self.__in_filter_mode = True

			for block in self._logic._blockList:
				block.init_filter()

			self.status_message(u_('Enter your filter criteria.'))
		finally:
			self.beginEditing()

	# -------------------------------------------------------------------------

	def change_filter(self):
		"""
		Copies the Query, ie brings back conditions from the last filter.
		"""

		# self.endEditing()         # happens via focus_out()

		if self._currentBlock is not None:
			self._currentBlock._focus_out()

		try:
			if not self._must_save():
				self.status_changed()
				self.beginEditing()
				return

			self.__in_filter_mode = True

			for block in self._logic._blockList:
				block.change_filter()

			self.status_message(u_('Enter your filter criteria.'))
		finally:
			self.beginEditing()

	# -------------------------------------------------------------------------

	def discard_filter(self):
		"""
		Cancels Query mode.
		"""

		self.endEditing()

		try:
			self.__in_filter_mode = False

			for block in self._logic._blockList:
				block.discard_filter()

			self.status_message(u_('Query canceled.'))
		finally:
			if self._currentBlock is not None:
				self._currentBlock._focus_in()

	# self.beginEditing()         # happens via _focus_in()


	# -------------------------------------------------------------------------

	def apply_filter(self):
		"""
		Applies the filter.
		"""

		self.endEditing()

		try:
			# Do a rollback on all connections so the query starts a new
			# transaction.
			self.__rollback_all_connections()

			try:
				for block in self._logic._blockList:
					block.processTrigger('PRE-QUERY')
					for field in block.iterFields():
						field.processTrigger('PRE-QUERY')

				self.__in_filter_mode = False

				# We have to reset all blocks to mode normal *before* we apply
				# the filter for any block, to make sure detail blocks are in
				# "normal" mode before they get queried.
				for block in self._logic._blockList:
					block.mode = "normal"

				for block in self._logic._blockList:
					block.apply_filter()

				for block in self._logic._blockList:
					block.processTrigger('POST-QUERY')
					for field in block.iterFields():
						field.processTrigger('POST-QUERY')

			except Exception:
				self.__rollback_all_connections()
				self.__reset_all_blocks()
				raise

		finally:
			if self._currentBlock is not None \
				and self._currentBlock.get_record_status() == 'empty':
				self.status_message (u_('Query returned no results.'))
			else:
				self.status_message (u_('Query successful.'))

			if self._currentBlock is not None:
				self._currentBlock._focus_in()
			else:
				# The Focus-In trigger of the block has already refreshed the
				# toolbar, unless there is no current block.
				self.status_changed()

	# self.beginEditing()             # happens via _focus_in()

	# -------------------------------------------------------------------------

	def in_filter_mode(self):
		"""
		Return True if the form is in filter mode.
		"""
		return self.__in_filter_mode


	# -------------------------------------------------------------------------
	# refresh all master bound blocks
	# -------------------------------------------------------------------------

	def refresh(self, canCancel = True, message = None):
		"""
		refresh all master bound blocks unless cancelled
		"""
		for block in self._logic._blockList:
			ds = block.getDataSource()
			if not ds.hasMaster() and ds.type != 'unbound':
				if block.refresh(canCancel, message) is None:   # canceled
					return

	def __trigger_raw_connection(self, connectionName):
		"""
		returns tuple: (<simpleconn>, <context dict>)
		session key stored in context dict for postgresql_fn driver
		"""
		gnueConn = self.__get_connections()[connectionName]

		if hasattr(gnueConn, '_getNativeConnection'):
			native = gnueConn._getNativeConnection()
			raw_connection = simpleconn.Connection(
				native['driver'],
				_connection_ = native['connection'],
				_encoding_ = native['encoding'],
				_decorate_error_ = native.get('decorate_error'),
			)
		else:
			raw_connection = None

		if hasattr(gnueConn, '_getNativeConnectionContext'):
			context = gnueConn._getNativeConnectionContext()
		else:
			context = None

		return raw_connection, context
	
	# -------------------------------------------------------------------------
	# Commit all pending changes
	# -------------------------------------------------------------------------

	def commit(self):
		"""
		Commit all pending changes.
		"""

		if self._currentBlock is not None:
			self._currentBlock._focus_out()

		# suppress all FOCUS-IN/FOCUS-OUT magic while committing
		current_block = self._currentBlock
		self._currentBlock = None

		try:
			# Do the actual work
			self.execute_commit()

			self._currentBlock = current_block
		finally:
			if self._currentBlock is not None:
				self._currentBlock._focus_in()

	# -------------------------------------------------------------------------

	def execute_commit(self):

		# Save all current records, since they get lost in the Pre-Commit
		# trigger code
		for block in self._logic._blockList:
			block._precommitRecord = block._currentRecord

		# Form level pre-commit triggers
		self.processTrigger('Pre-Commit', ignoreAbort=False)

		# Block level pre-commit triggers
		for block in self._logic._blockList:
			block.processTrigger('Pre-Commit')

		# FIXME: Is this a GoodThing(tm)? Maybe we would really *want* to move
		# the record pointer at commit time in the trigger?
		for block in self._logic._blockList:
			block.goto_record(block._precommitRecord)

		# Set the mode to commit on all blocks
		for block in self._logic._blockList:
			block.mode = 'commit'

		try:
			# Process the commit on all blocks
			for block in self._logic._blockList:
				assert gDebug(5, "Saving %s" % block.name)
				try:
					block.post()
				except Exception:
					# jump to offending block
					# FIXME: does not work with master/detail, always moves the
					# focus to master record.
					if block != self._currentBlock:
						self.__find_and_change_focus([block], False)
					raise
		finally:
			for block in self._logic._blockList:
				block.mode = 'normal'

		try:
			# Now do the real commit() on the backend connections (only
			# once per connection, if multiple blocks are sharing the same
			# connection)
			for connection in self.__get_connections().itervalues():
				connection.commit()
		except:
			# Make sure the block is in consistent state again; this has to
			# be done in any case if the processCommit was successful, even
			# if the connection commit failed!
			try:
				for block in self._logic._blockList:
					block.requery(False)
			except:
				# Ignore exceptions happening in requery so they don't
				# obfuscate the original exception that happened in commit.
				pass
			# FIXME: We have to think more about the question what's the right
			# way to act when an exception happenend in the COMMIT.
			raise

		for block in self._logic._blockList:
			block.requery(True)

		# Execute Post-Commit-Trigger for each block
		for block in self._logic._blockList:
			block.processTrigger('Post-Commit')

		for block in self._logic._blockList:
			if block.autoClear:
				block.clear()

		# Execute Post-Commit-Trigger for the form
		self.processTrigger('Post-Commit')


	# -------------------------------------------------------------------------
	# Roll back any uncommitted transaction
	# -------------------------------------------------------------------------

	def rollback(self):
		"""
		Roll back any uncommitted transaction.
		"""

		try:
			self.endEditing()
		except:
			# Ignore errors, as we're discarding the changes anyway
			pass

		# We purposedly don't call focus-out here, we want to be able to clean
		# blocks that have invalid stuff entered.
		# FIXME: probably we would want to call the POST-FOCUSOUT triggers,
		# though.

		# Suppress all FOCUS-IN/FOCUS-OUT magic while clearing the blocks
		# (focus_in() and focus_out() would happen via dsResultSetChanged)
		current_block = self._currentBlock
		self._currentBlock = None

		try:
			# Call rollback only once per connection (if multiple blocks are
			# sharing the same connection)
			self.__rollback_all_connections()
			self.__reset_all_blocks()
		finally:
			self._currentBlock = current_block
			if self._currentBlock is not None:
				self._currentBlock._focus_in()
	# self.beginEditing()               # happens via _focus_in()

	# -------------------------------------------------------------------------

	def __rollback_all_connections(self):

		for connection in self.__get_connections().itervalues():
			connection.rollback()

	# -------------------------------------------------------------------------

	def __reset_all_blocks(self):

		for block in self._logic._blockList:
			block.populate()


	# -------------------------------------------------------------------------
	# Check all blocks in the form whether they are saved (committed) or not.
	# -------------------------------------------------------------------------

	def is_saved(self):
		"""
		Checks all block in the form whether they are saved (committed) or not.
		@return: boolean, True if all the blocks are committed.
		"""

		# Are there any not yet posted changes in any of the blocks?
		for block in self._logic._blockList:
			if block.is_pending():
				return False

		# Does a connection have any pending (already posted but not yet
		# committed) changes?
		for connection in (self.__get_connections()).itervalues():
			if connection.isPending():
				return False

		return True


	# =========================================================================
	# Misc stuff
	# =========================================================================

	# -------------------------------------------------------------------------
	# Launch a trigger
	# -------------------------------------------------------------------------

	def fire_trigger(self, name):
		"""
		Launches a trigger.

		@param name: name of the trigger to be launched.
		"""

		self._triggerDictionary[name](self=self)


	# -------------------------------------------------------------------------
	# Run a form from another GFD
	# -------------------------------------------------------------------------

	def run_form(self, filename, parameters=None, gfContainer=None):
		"""
		Loads and activates a new form from a file.

		@param fileName: the name of the .gfd file to be displayed
		@param parameters: dictionary of parameters to be passed to the newly
		    run form
		"""

		result = self._instance.run_from_file(filename, parameters, gfContainer)
		# htmlex specific
		if hasattr(self.uiWidget, '_ui_run_form_'):
			self.uiWidget._ui_run_form_(result)
		return result

	def __trigger_run_form(self, *args, **kwargs):
		return self.run_form(*args, **kwargs).get_namespace_object()

	# -------------------------------------------------------------------------
	# Run a report
	# -------------------------------------------------------------------------

	def run_report(self, reportFile, parameters={}, **parms):
		"""
		Launches a new instance of GNUe-Reports, running a new report.
		@param reportFile: the name of the .grd file to be processed
		@param parameters: dictionary of parameters to be passed
		                    to the newly run report
		@param **params:
		  These roughly correspond to the ./gnue-reports options
		          destination
		          destinationType
		          destinationOptions (dict)
		          filter
		          filterOptions (dict)
		          sortoption
		          includeStructuralComments
		          omitGNUeXML
		@return: None
		"""

		from gnue.reports.base.GREngine import GREngine
		from gnue.reports.base import GRFilters, GRExceptions
		rep_engine = GREngine(self._instance.connections)
		rep_engine.processReport(reportFile, parameters=parameters, **parms)


	# -------------------------------------------------------------------------
	# Get the currently logged in username
	# -------------------------------------------------------------------------

	def get_username(self, connection=None):
		"""
		Return the authenticated user.
		"""
		return self._instance.connections.getAuthenticatedUser(connection)


	# -------------------------------------------------------------------------
	# Get the name of current ui driver
	# -------------------------------------------------------------------------

	def get_uidriver_name(self):
		"""
		Return the driver name
		"""
		return self._instance._uiinstance.name


	# -------------------------------------------------------------------------
	# Toggles insert mode
	# -------------------------------------------------------------------------

	def toggle_insert_mode(self):
		"""
		Toggles insert mode.
		"""
		self.__insert_mode = not self.__insert_mode
		self.update_insert_status()
	# FIXME: This does not have any effect


	# -------------------------------------------------------------------------
	# Print form
	# -------------------------------------------------------------------------

	def printout(self):
		"""
		Print the form.

		If the form has a trigger named "process-printout", fire it. Otherwise,
		print a screen dump of the form.
		"""

		if self._triggerDictionary.has_key('process-printout'):
			self.fire_trigger('process-printout')
		else:
			if self.uiWidget is not None:
				self.uiWidget._ui_printout_(self.title, "",
					self._instance.connections.getAuthenticatedUser(None) \
						or 'Anonymous')


	# -------------------------------------------------------------------------
	# Close this window
	# -------------------------------------------------------------------------

	def close(self):
		#rint ">>> %s.close()" % (self.name,)

		# FIXME: Changes in the current entry are not yet saved in the field if
		# this was caused by a click on the close button of the window,
		# because...
		try:
			self.processTrigger('Pre-Exit', ignoreAbort = False)
		except AbortRequest, e:
			if e.args[0]:
				raise
			else:
				# if abortRequest without message, stay calm
				return
		except:
			# if we have some connection-dependent error, show it once and close form
			sys.excepthook(*sys.exc_info())
			self.show_message(_("Trigger fails: %s\nThis may cause unproper cleanup or data loss") % 'PRE-EXIT', 'Warning')

		# deferred function
		def resultConsumer(result):
			
			# ... we would want to be able to exit here without saving even if the
			# current entry contains an invalid value.
			
			if result:
				try:
					self.processTrigger('On-Exit')
				except:
					# if we have some connection-dependent error, show it once and close form
					sys.excepthook(*sys.exc_info())

				if self.uiWidget is not None:
					self.uiWidget._ui_close_()

					# destroy if not reusable subform
					if not self.__subform:

						#destroy all subforms
						for subform in self.__subforms.itervalues():
							if subform.uiWidget is not None:
								subform.uiWidget._ui_destroy_()
							
						self.uiWidget._ui_destroy_()

				self.__visible = False
				self.__opening = False

				self._instance.maybe_exit(self)
			
			return result

		self._must_save(resultConsumer)

	# =========================================================================
	# trigger globals
	# =========================================================================

	def __trigger_getGlobal(self, *args, **kwargs):
		return self._instance.getGlobal(*args, **kwargs)

	def __trigger_setGlobal(self, *args, **kwargs):
		return self._instance.setGlobal(*args, **kwargs)

	def __trigger_get_clientproperty(self, *args, **kwargs):
		return self._instance.get_clientproperty(*args, **kwargs)

	def __trigger_set_clientproperty(self, *args, **kwargs):
		return self._instance.set_clientproperty(*args, **kwargs)

	
	# =========================================================================
	# Various helper functions
	# =========================================================================

	# -------------------------------------------------------------------------
	# Get all connections used by the form
	# -------------------------------------------------------------------------

	def __get_connections(self):
		"""
		This function creates a dictionary of all connections referenced by the
		form, where the connection-name is the key and the connection instance
		is the value.

		@return: dictionary with all connections used by the form
		"""

		result = {}
		for d_link in self._datasourceDictionary.values():
			try:
				if d_link._connection is not None:
					result[d_link.connection] = d_link._connection
			except AttributeError:
				pass

		return result


	# -------------------------------------------------------------------------
	# Signal the UI Drivers of navigation button relevance
	# -------------------------------------------------------------------------

	def status_changed(self):
		"""
		Notify the form of a record status change.

		This function must be called whenever the status of the current block
		has changed, or the focus has moved to another block (meaning that a
		different block has now become the current block).
		It calls the ON-STATUSCHANGE trigger, allowing the form to
		enable/disable menu items and toolbar buttons depending on the current
		status.
		"""
		self.processTrigger('On-StatusChange')


	# -------------------------------------------------------------------------
	# Update the status bar in the form
	# -------------------------------------------------------------------------

	def update_tip(self, tip):

		self.__update_status(tip=tip)

	# -------------------------------------------------------------------------

	def update_record_status(self, record_status):

		self.__update_status(record_status=record_status)

	# -------------------------------------------------------------------------

	def update_insert_status(self):

		if self.__insert_mode:
			self.__update_status(insert_status='INS')
		else:
			self.__update_status(insert_status='OVR')

	# -------------------------------------------------------------------------

	def update_record_counter(self, record_number, record_count):

		self.__update_status(record_number=record_number,
			record_count=record_count)

	# -------------------------------------------------------------------------

	def __update_status(self, tip=None, record_status=None, insert_status=None,
		record_number=None, record_count=None):
		"""
		Updates the complete status bar of the form.

		Parameters that are not given are not changed in the status bar.
		"""

		# This can be called before the UI is built.
		if self.uiWidget is not None:

			# avoid superfluous updates
			record_number, record_count = self.__return_if_changed((record_number, record_count), 'record_number_count') or (None, None)
			
			self.uiWidget._ui_update_status_(
				self.__return_if_changed(tip, 'tip'), 
				self.__return_if_changed(record_status, 'record_status'), 
				self.__return_if_changed(insert_status, 'insert_status'),	
				record_number, 
				record_count
			)

		self.__ui_update_title()


	def __ui_update_title(self):
		title = self.title
		if not self.is_saved():
			title += ' *'

		# avoid superfluous updates
		title = self.__return_if_changed(title, 'title')
		if title is not None:
			self.uiWidget._ui_set_title_(title)


	def __return_if_changed(self, value, name):
		if value is not None:
			old_value = self.__return_if_changed_cache.get(name)
			if old_value != value:
				self.__return_if_changed_cache[name] = value
				return value
				
	# -------------------------------------------------------------------------
	# Signal to the current Entry to stop editing
	# mode and save it's value to the virtual form
	# -------------------------------------------------------------------------

	def endEditing(self):
		"""
		Signals the current entry to stop editing mode and
		save it's value to the virtual form.
		@return: Boolean, True if succeeded, False if failed.
		"""
		if not self.__editing_blocked \
			and isinstance(self._currentEntry, GFEntry):
			# Block beginEditing and endEditing for everything that happens in
			# endEdit, especially autoquery.
			self.__editing_blocked = True
			try:
				self._currentEntry.endEdit()
			finally:
				self.__editing_blocked = False


	# -------------------------------------------------------------------------
	# Start editing mode of the current entry
	# -------------------------------------------------------------------------

	def beginEditing(self):
		if not self.__editing_blocked \
			and isinstance(self._currentEntry, GFEntry):
			self._currentEntry.beginEdit()


	# -------------------------------------------------------------------------
	# Is this form or any subform visible?
	# -------------------------------------------------------------------------

	def is_visible(self):

		if self.__visible:
			return True
		for subform in self.__subforms.itervalues():
			if subform.is_visible():
				return True
		return False


	# -------------------------------------------------------------------------
	# Ask the user whether to save or to discard changes if there are any
	# -------------------------------------------------------------------------


	def _must_save(self, resultConsumer=lambda result: result):

		if self.is_saved():
			return resultConsumer(True)
		else:
			def mustSaveResultConsumer(result):
				if result is None:
					# Cancel
					return resultConsumer(False)

				if result:
					self.commit()

				return resultConsumer(True)

			return self.show_message(message=u_("Save changes?"), kind='Question', title=self.title, cancel=True, resultConsumer=mustSaveResultConsumer)



		


	# =========================================================================
	# Deprecated trigger functions
	# =========================================================================

	def __trigger_get_feature(self, feature):
		"""
		Gets feature values.
		Features are things like toolbars, menubars and statusbar.
		@param feature: 'GUI:MENUBAR:SUPPRESS' or 'GUI:TOOLBAR:SUPPRESS' or
		                    'GUI:STATUSBAR:SUPPRESS'
		@return:    Boolean
		"""
		try:
			return self._features[feature]
		except KeyError:
			raise KeyError, "Trigger attempted to get unknown feature %s" % feature

	# -------------------------------------------------------------------------

	def __trigger_set_feature(self, feature, value):
		"""
		Sets feature values.
		Features are things like toolbars, menubars and statusbar.
		@param feature: 'GUI:MENUBAR:SUPPRESS' or 'GUI:TOOLBAR:SUPPRESS' or
		                    'GUI:STATUSBAR:SUPPRESS'
		@param value: True or False
		@return: None
		"""
		if not self._features.has_key(feature):
			raise KeyError, "Trigger attempted to set unknown feature %s" % feature
		else:
			self._features[feature] = value

	# -------------------------------------------------------------------------

	def __trigger_get_parameter(self, parameter):

		assert gDebug(1, "DEPRECATED: getParameter trigger function")
		if parameter in self.__parameter_dict:
			return self.__parameter_dict[parameter].value
		else:
			raise UndefinedParameterError(parameter)

	# -------------------------------------------------------------------------

	def __trigger_set_parameter(self, parameter, value):

		assert gDebug(1, "DEPRECATED: setParameter trigger function")
		if parameter in self.__parameter_dict:
			self.__parameter_dict[parameter].value = value
		else:
			raise UndefinedParameterError(parameter)

	# -------------------------------------------------------------------------

	def __trigger_set_focus(self, object):
		"""
		Switch input focus to a specific widget.

		@param object: the widget that should get the focus
		"""
		# add global focus locking
		if self._in_trigger_lock:
			gDebug(1, "Already called by a trigger")
			return

		self._in_trigger_lock = True

		try:
			self.__find_and_change_focus([object._object], False)
		finally:
			self._in_trigger_lock = False

	# -------------------------------------------------------------------------

	def getDataSource(self, name, referer=None):
		try:
			return self._datasourceDictionary[name.lower()]
		except KeyError:
			raise DataSourceNotFoundError(self, name, referer)

	def call_after(self, f, *args, **kwargs):
		if hasattr(self.uiWidget, '_ui_call_after_'):
			self.uiWidget._ui_call_after_(f, *args, **kwargs)
		else:
			f(*args, **kwargs)


	def umodify_field(self):
		if self._currentBlock:
			self._currentBlock.unmodify_field()

	def umodify_record(self):
		if self._currentBlock:
			self._currentBlock.unmodify_record()

	def isEmpty(self):
		return not self._layout._children


	###################################################################
	# jobs
	#

	def run_job(self, job, *args, **kwargs):
		"""
		Starts a thread, job(*args, **kwargs) 
		job can use call_after to update gui
		"""
		# error dialog stalls when invoked from another thread
		# TODO: gnue excepthook must use form.call_after to show error
		def safeJob():
			try:
				job(*args, **kwargs)
			except:
				self.call_after(sys.excepthook, *sys.exc_info())
				
		thread.start_new_thread(safeJob, args, kwargs)
		
	###################################################################

	def __test(self):

		import sys, gc, inspect
		from toolib.dbg import objgraph

		#import pdb
		#pdb.set_trace()
		#return

		#from gnue.forms.GFInstance import GFInstance
		#testForm = GFInstance.testForm
		try:
			del GFInstance.testForm
		except:
			pass

		#from gnue.forms.GFInstance import GFInstance
		from gnue.common.datasources.drivers.Base import ResultSet
		testForm = ResultSet.testRS
		print repr(testForm)
		try:
			del ResultSet.testRS
		except:
			pass

		gc.collect()

		print "Test form", testForm

		if 0:
			print "looking for chain to instance"
			to_instance = lambda x: x is self._instance
			to_app = lambda x: x is self.testApp
			to_table = lambda x: x.__class__.__name__ == 'Table'

			chain = objgraph.find_backref_chain(testForm, to_table, max_depth=50)
			if chain:
				print "chain found!", len(chain)
				ids = set(map(id, chain))
				in_chain = lambda x: id(x) in ids
				objgraph.show_backrefs(chain[-1], len(chain), filter=in_chain)
			else:
				print "chain NOT FOUND"

		else:
			objgraph.show_backrefs(testForm, max_depth=3000)#, filter=lambda x: not (inspect.isfunction(x) or inspect.ismethod(x)))
