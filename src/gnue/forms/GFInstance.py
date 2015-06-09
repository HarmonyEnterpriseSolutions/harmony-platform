# GNU Enterprise Forms - Forms Instance Management
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
# $Id: GFInstance.py,v 1.25 2014/03/17 17:26:21 Oleg Exp $

"""
Classes that manage a running instance of GNUe Forms.
"""

import os
import re
import gc
from urllib2 import HTTPError

from gnue import paths
from gnue.common import events
from gnue.common.apps import i18n, errors
from gnue.common.datasources.GDataSource import getAppserverResource
from gnue.common.utils import FileUtils
from gnue.forms import GFForm
from gnue.forms.GFParser import loadFile
from gnue.forms.input import GFKeyMapper
from src.gnue.forms.GFExceptionDecorator import decorate_exception


__all__ = ['GFInstance']


class NoDefault: pass

# =============================================================================
# Forms instance manager class
# =============================================================================

class GFInstance(events.EventAware):
	"""
	A running GNUe Forms instance.

	This class handles loading of the forms definitions, building up the object
	tree for the forms, and starting the main form, as well as ending the
	application when the last form is closed.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, manager, connections, ui, disableSplash=False,
		parameters=None, parentContainer=None, moduleName=None):
		# moduleName is here only for Designer to be able to pass it in
		#when debugging a form.

		assert gEnter(4)

		# Configure event handling
		assert gDebug(4, "Initializing event handling")

		self.eventController = events.EventController()
		events.EventAware.__init__(self, self.eventController)
		self.registerEventListeners({
				# First, all events are passed to the focus widget
				'__before__'          : self.__before_event,

				# Focus-related events
				'requestENTER'        : self.__execute_next_entry,
				'requestNEXTENTRY'    : self.__execute_next_entry,
				'requestPREVENTRY'    : self.__execute_previous_entry,
				'requestNEXTBLOCK'    : self.__execute_next_block,
				'requestPREVBLOCK'    : self.__execute_previous_block,

				# Clipboard and selection
				'requestCUT'          : self.__execute_cut,
				'requestCOPY'         : self.__execute_copy,
				'requestPASTE'        : self.__execute_paste,
				'requestSELECTALL'    : self.__execute_select_all,

				# Record navigation
				'requestFIRSTRECORD'  : self.__execute_first_record,
				'requestPREVRECORD'   : self.__execute_prev_record,
				'requestNEXTRECORD'   : self.__execute_next_record,
				'requestLASTRECORD'   : self.__execute_last_record,
				'requestJUMPPROMPT'   : self.__execute_jump_prompt,

				# Record insertion/deletion
				'requestNEWRECORD'    : self.__execute_new_record,
				'requestMARKFORDELETE': self.__execute_mark_for_delete,
				'requestUNDELETE'     : self.__execute_undelete_record,

				# unmodify record and field
				'requestUNMODIFYFIELD'  : self.__execute_umodify_field,
				'requestUNMODIFYRECORD' : self.__execute_umodify_record,

				# Queries
				'requestENTERQUERY'   : self.__execute_enter_query,
				'requestCOPYQUERY'    : self.__execute_copy_query,
				'requestCANCELQUERY'  : self.__execute_cancel_query,
				'requestEXECQUERY'    : self.__execute_exec_query,

				# Transactions
				'requestCOMMIT'       : self.__execute_commit,
				'requestROLLBACK'     : self.__execute_rollback,

				# Miscellaneous stuff
				'requestMODETOGGLE'   : self.__execute_mode_toggle,
				'requestABOUT'        : self.__execute_about,
				'requestPRINTOUT'     : self.__execute_printout,
				'requestUSERCOMMAND'  : self.__execute_user_command,
				'requestEXIT'         : self.__execute_exit})

		self.connections = connections  # Link to the GBaseApp's GConnections

		self.manager = manager          # Link to the GBaseApp Instance that
		#   created this GFInstance
		self._uimodule = ui             # The UI created in the GBaseApp
		self._disableSplash = disableSplash  # Disable splashscreen

		# The parameters passed to the GBaseApp instance
		self.__parameters = parameters

		self.__loaded_forms = set()		# All loaded forms

		self.__globals = {}

		self.__keepalive = False

		self._parentContainer = parentContainer

		# Load user customized key mappings
		options = gConfigDict()
		mapping = {}

		for key in options.keys():
			if key.lower().startswith('key_'):
				gDebug(1, ("DEPRECATED: %s option in gnue.conf.  " \
							+ "Please add a menu item to default.gfd instead.") \
						% key)
				mapping[key[4:]] = options[key]

		GFKeyMapper.KeyMapper.loadUserKeyMap(mapping)

		# Construct an instance of the UI driver if an UI module is available
		if self._uimodule is not None:
			assert gDebug(4, "Initializing user interface driver")
			self._uiinstance = self._uimodule.GFUserInterface(
				self.eventController, disableSplash=self._disableSplash,
				parentContainer=self._parentContainer,
				moduleName=moduleName)

		assert gLeave(4)


	def createDefaultForm(self):

		assert gDebug(4, "Loading default form")

		dirnames = [os.path.join(paths.data, "share","gnue","forms","defaults")]
		dirnames.append(paths.config)
		if os.environ.has_key("HOME"):
			dirnames.append(os.path.join(os.environ["HOME"], ".gnue"))

		default_form = GFForm.GFForm()
		for dirname in dirnames:
			filename = os.path.join(dirname, "default.gfd")
			if os.path.isfile(filename):
				default_form.merge(
					self.__load_file_with_translations(filename, False),
					overwrite=True)

		return default_form


	# -------------------------------------------------------------------------
	# Decide whether to keep the GFInstance alive even if no windows are open
	# any more
	# -------------------------------------------------------------------------

	def keepalive(self, setting):
		"""
		Decide whether the main loop should automatically be ended when the
		last window is closed.

		GNUe-Navigator uses this to keep the application alive even if no form
		is open any more.

		@param setting: True to keep the application running, False to end it.
		"""

		self.__keepalive = setting


	# -------------------------------------------------------------------------
	# Load and run a form
	# -------------------------------------------------------------------------

	def run_from_file(self, filename, parameters, gfContainer=None):
		"""
		Load a form definition from a file and open the form.

		@param filename: Filename to load
		@param parameters: Parameter dictionary to pass to the form.
		@param gfContainer: GFObject that want to be uiParent of this form
		"""

		form = self.__load_file_with_translations(filename, True)
		self.__loaded_forms.add(form)
		if form.isEmpty():
			form.close()
			if form.title:
				raise errors.UserError(form.title)
		else:
			self.__run(form, parameters, gfContainer)
		return form


	# -------------------------------------------------------------------------
	# Helper functions, can be merged into main functions when depreciated
	# functions are removed.
	# -------------------------------------------------------------------------

	def __load_file_with_translations(self, filename, check_required):

		# Load base form
		form = self.__load_file(filename, check_required)

		(base, ext) = os.path.splitext(filename)

		# Find out about the languages to load.
		lang = i18n.getlanguage()
		filenames = []
		if lang != "C":
			filenames.append(base + os.path.extsep + lang[:2] + ext)
			filenames.append(os.path.join(base, lang[:2] + ext))
			if len(lang) > 2:
				filenames.append(base + os.path.extsep + lang + ext)
				filenames.append(os.path.join(base, lang + ext))

		# Merge language specific versions
		for fn in filenames:
			if os.path.isfile(fn):
				form.merge(self.__load_file(fn, False), overwrite=True)

		return form

	# -------------------------------------------------------------------------

	def __make_absolute_url(self, url):
		if self.__globals.get('__form_server_url__') and not re.match(r'(?i)[a-z]+://|/|[a-z]:', url):
			url = '%s/%s' % (self.__globals.get('__form_server_url__'), url)
		if self.__globals.get('__form_server_query_string__') and re.match(r'(?i)[a-z]+://', url):
			if re.search(r'(?i)\?[a-z]+\=', url):
				url += '&'
			else:
				url += '?'
			url += self.__globals.get('__form_server_query_string__')
		return url

	def __load_file(self, filename, check_required):
		try:
			if filename.startswith('appserver://'):
				param = {'language': i18n.language, 'formwidth': 80,
					'formheight': 20}
				filehandle = getAppserverResource(filename, param,
					self.connections)
				form = self.__load(filehandle, filename, check_required)
				filehandle.close()
			else:
				filehandle = FileUtils.openResource(self.__make_absolute_url(filename))
				form = self.__load(filehandle, filename, check_required)
				filehandle.close()

			return form

		except HTTPError, e:
			if e.code == 403:
				raise errors.UserError(u_(u"Your login session has expired, please, restart application"))
			else:
				raise
		except IOError, e:
				raise errors.UserError(u_("Unable to open file: %s") % errors.getException()[2])

	# -------------------------------------------------------------------------

	def __load(self, filehandle, url, check_required):

		# Load the file bypassing the initialization We bypass the
		# initialization because <dialog>s are really <form>s and they don't
		# like being children of another form
		return loadFile(filehandle, self, initialize=0, url=url,
			check_required=check_required)

	# -------------------------------------------------------------------------

	def __run(self, form, parameters, gfContainer=None):

		# Initialize all the forms loaded into memory
		assert gDebug(4, "Initializing form objects")

		# Set the parameters for the main form now so they are available in the
		# ON-STARTUP trigger, which is called in phaseInit.
		if parameters is not None:
			form.set_parameters(parameters)

		form.initialize(self.createDefaultForm(), gfContainer)

		def afterOpen():
			# Get the parameters back from the form.
			if parameters is not None:
				parameters.clear()
				parameters.update(form.get_parameters())
		
		# Bring up the main form
		if form.style == 'dialog':
			# we assume a dialog to be modal by definition and that program
			# execution stops here until the dialog get's closed. So do *not*
			# enter another main loop
			assert gDebug(4, "Activating main form as dialog")
			form.execute_open(True, afterOpen)
		else:
			assert gDebug(4, "Activating main form")
			form.execute_open(False, None)
			assert gDebug(4, "Startup complete")
			assert gDebug(4, "Entering main loop")
			self._uiinstance.mainLoop()
			assert gDebug(4, "Returning from main loop")
			afterOpen()


	# -------------------------------------------------------------------------
	# Show an exception
	# -------------------------------------------------------------------------

	def show_exception(self, group=None, name=None, message=None, detail=None):
		"""
		This function shows the last exception raised.

		The exact way of showing the message depends on the exception group.
		"""
		if (group, name, message, detail) == (None, None, None, None):
			(group, name, message, detail) = errors.getException()

		#rint "--------------- before"
		#rint 'group  :', repr(group)
		#rint 'name   :', repr(name)
		#rint 'message:', repr(message)
		#rint 'detail :', repr(detail)

		for key in ('group', 'name', 'detail', 'message'):
			m = re.compile(r'(?is)\[%s\[([^\]]*)\]\]' % key).search(message)
			if m:
				exec(key + '= m.groups()[0]')
				if key == 'message':
					message = message.rstrip()
				else:
					message = message[:m.start()] + message[m.end():]

		group, name, message, detail = decorate_exception(group, name, message, detail)

		#rint "--------------- after"
		#rint 'group  :', repr(group)
		#rint 'name   :', repr(name)
		#rint 'message:', repr(message)
		#rint 'detail :', repr(detail)

		if group == 'user':
			if message:
				self._uiinstance._ui_show_error_(message)
		else:
			self._uiinstance._ui_show_exception_(group, name, message, detail)

	# -------------------------------------------------------------------------
	# Exit the application if the last form has been closed
	# -------------------------------------------------------------------------

	def maybe_exit(self, closedForm):
		"""
		Exit the application if the last form has been closed

		This function is called by each form when it is closed.
		"""

		# dialogs defined inside of form is reused after close
		# thay are not in self.__loaded_forms
		if closedForm in self.__loaded_forms:

			# anyway, remove closed form from list
			self.__loaded_forms.remove(closedForm)

			# GFUserInterface has UIForm as children
			if closedForm.uiWidget is not None:
				closedForm.uiWidget.getParent()._children.remove(closedForm.uiWidget)

			gc.collect()

		if not self.__keepalive:
			any_form_open = False
			for form in self.__loaded_forms:
				if form.is_visible():
					any_form_open = True
					break
			if not any_form_open:
				self._uiinstance._ui_exit_()


	def setGlobal(self, key, value):
		self.__globals[key] = value

	def getGlobal(self, key, default=NoDefault):
		if default is NoDefault:
			try:
				return self.__globals[key]
			except KeyError:
				raise NameError, u_('Global variable "%s" is not defined') % key
		else:
			return self.__globals.get(key, default)

	def getGlobals(self):
		return self.__globals

	def set_clientproperty(self, key, value):
		if not hasattr(self.manager, 'get_clientproperty_storage'):
			raise NotImplementedError, 'clientproperty is not implemented in current driver'
		self.manager.get_clientproperty_storage()[key] = value

	def get_clientproperty(self, key, default=None):
		if not hasattr(self.manager, 'get_clientproperty_storage'):
			raise NotImplementedError, 'clientproperty is not implemented in current driver'
		try:
			return self.manager.get_clientproperty_storage()[key]
		except KeyError:
			return default
	
	# =========================================================================
	# EVENT FUNCTIONS
	# =========================================================================

	# -------------------------------------------------------------------------
	# Handle an event before it's sent to usual event processing
	# -------------------------------------------------------------------------

	def __before_event(self, event):
		"""
		This is called before any normal event processing is done. This method
		passes the event to the current focus widget and sees if that widget
		wants to handle that event.

		@param event: The event currently being processed.
		"""

		if not hasattr(event, '_form'):
			return

		entry = event._form._currentEntry
		if entry is None:
			return

		# Pass off the event to the current entry's event handler
		entry.subEventHandler.dispatchEvent(event)

		# If the entry needs an error message displayed, then the proxied event
		# should set this to the message text
		if event.__errortext__:
			event._form.show_message(event.__errortext__, 'Error')


	# -------------------------------------------------------------------------
	# Focus movement
	# -------------------------------------------------------------------------

	def __execute_next_entry(self, event):

		event._form.next_entry()

	# -------------------------------------------------------------------------

	def __execute_previous_entry(self, event):

		event._form.previous_entry()

	# -------------------------------------------------------------------------

	def __execute_next_block(self, event):

		event._form.next_block()

	# -------------------------------------------------------------------------

	def __execute_previous_block(self, event):

		event._form.previous_block()

	# -------------------------------------------------------------------------
	# Clipboard and selection
	# -------------------------------------------------------------------------

	def __execute_cut(self, event):

		event._form.cut()

	# -------------------------------------------------------------------------

	def __execute_copy(self, event):

		event._form.copy()

	# -------------------------------------------------------------------------

	def __execute_paste(self, event):

		event._form.paste()

	# -------------------------------------------------------------------------

	def __execute_select_all(self, event):

		event._form.select_all()

	# -------------------------------------------------------------------------
	# Record navigation
	# -------------------------------------------------------------------------

	def __execute_first_record(self, event):

		event._form.first_record()

	# -------------------------------------------------------------------------

	def __execute_prev_record(self, event):

		event._form.prev_record()

	# -------------------------------------------------------------------------

	def __execute_next_record(self, event):

		event._form.next_record()

	# -------------------------------------------------------------------------

	def __execute_last_record(self, event):

		event._form.last_record()

	# -------------------------------------------------------------------------

	def __execute_jump_prompt(self, event):

		event._form.ask_record()

	# -------------------------------------------------------------------------
	# Record insertion/deletion
	# -------------------------------------------------------------------------

	def __execute_new_record(self, event):

		event._form.new_record()

	# -------------------------------------------------------------------------

	def __execute_mark_for_delete(self, event):

		event._form.delete_record()

	# -------------------------------------------------------------------------

	def __execute_undelete_record(self, event):

		event._form.undelete_record()


	# -------------------------------------------------------------------------
	# Queries
	# -------------------------------------------------------------------------

	def __execute_enter_query(self, event):

		event._form.init_filter()

	# -------------------------------------------------------------------------

	def __execute_copy_query(self, event):

		event._form.change_filter()

	# -------------------------------------------------------------------------

	def __execute_cancel_query(self, event):

		event._form.discard_filter()

	# -------------------------------------------------------------------------

	def __execute_exec_query(self, event):

		event._form.apply_filter()


	# -------------------------------------------------------------------------
	# Transactions
	# -------------------------------------------------------------------------

	def __execute_commit(self, event):

		event._form.commit()

	# -------------------------------------------------------------------------

	def __execute_rollback(self, event):

		event._form.rollback()


	# -------------------------------------------------------------------------
	# Toggle insert mode
	# -------------------------------------------------------------------------

	def __execute_mode_toggle(self, event):

		event._form.toggle_insert_mode()


	# -------------------------------------------------------------------------
	# Display the about dialog
	# -------------------------------------------------------------------------

	def __execute_about(self, event):

		event._form.show_about()


	# -------------------------------------------------------------------------
	# Fire a trigger named 'process-printout' (if it exists)
	# -------------------------------------------------------------------------

	def __execute_printout(self, event):

		event._form.printout()


	# -------------------------------------------------------------------------
	# Execute user command
	# -------------------------------------------------------------------------

	def __execute_user_command(self, event):

		try:
			event._form.fire_trigger("KEY-%s" % event.triggerName.upper())
		except KeyError:
			pass


	# -------------------------------------------------------------------------
	# Verify state of data and exit form
	# -------------------------------------------------------------------------

	def __execute_exit(self, event):

		event._form.close()

	# -------------------------------------------------------------------------
	# unmodify current field and current record
	# -------------------------------------------------------------------------

	def __execute_umodify_field(self, event):
		event._form.umodify_field()

	def __execute_umodify_record(self, event):
		event._form.umodify_record()


