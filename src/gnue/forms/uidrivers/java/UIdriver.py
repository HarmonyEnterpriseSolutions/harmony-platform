#
# This file is part of GNU Enterprise.
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
# Copyright 2000-2007 Free Software Foundation
#
# FILE:
# uidrivers/html/UIdriver.py
#
# DESCRIPTION:
#
# NOTES:
#

# EK TODO: This module is just stub, it does not used by widgets
# at all. How to remove it?

from gnue.forms.uidrivers._base.rpc import staticres
from gnue.forms.uidrivers._base.rpc.RemoteHive import RemoteHive
from gnue.forms.uidrivers._base import Exceptions
from gnue.forms.uidrivers._base.UIdriver import GFUserInterfaceBase

from gnue.common import events
from gnue.common.apps import GConfig, errors
from collections import deque

from gnue.forms.GFForm import *


class MainLoopEntered(Exception):
	pass



class GFUserInterface(GFUserInterfaceBase, RemoteHive):

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, *args, **params):
		GFUserInterfaceBase.__init__(self, *args, **params)

		self.name = "java"

		# this attributes needed by gnue.forms.uidrivers._base.UIdriver

		self.textWidth    = 12  # The pixel width of text inside a widget
		self.textHeight   = 24  # The pixel height of text inside a widget
		self.widgetWidth  = self.textWidth  # The pixel width of a 1 char widget (for things like buttons)
		self.widgetHeight = self.textHeight + 5  # The pixel height of a 1 char widget (for things like button
		self.__mainLoopEntered = False

		self._instance = None

	def __getstate__(self):
		dict = self.__dict__.copy()
		dict['_getUserContextBySid'] = None
		return dict
	
	def setGetUserContextBySid(self, getUserContextBySid):
		self._getUserContextBySid = getUserContextBySid

	def getStaticResourceWebPath(self, path):
		"""
		redirects to GFClient because applet gets static resource without hive id
		"""
		return staticres.getStaticResourceWebPath(path)

	def initRemoteHive(self, hiveId):
		RemoteHive.__init__(self, hiveId)

	def mainLoop(self):
		# should break GFInstance.__run execution at this point
		if not self.__mainLoopEntered:
			self.__mainLoopEntered = True
			raise MainLoopEntered(self)

	# ---------------------------------------------------------------------------
	# create a modal dialog box, asking for user input
	# ---------------------------------------------------------------------------

	def _getInput (self, title, fields, cancel):
		raise NotImplementedError, "input not implemented and deprecated"

	# ---------------------------------------------------------------------------
	# create a modal message box
	# ---------------------------------------------------------------------------

	def _ui_show_error_(self, message):
		if self._uiForm() is not None:
			self._uiForm()._ui_show_message_(message, "error", _("Error"), True)
		else:
			# This will be displayed by Desktop as Remote error
			raise RuntimeError, "Can't show error because no form. Original error message:\n%s" % (message,)


	# ---------------------------------------------------------------------------
	# Show an exception dialog
	# ---------------------------------------------------------------------------

	def _ui_show_exception_(self, group, name, message, detail):
		if self._uiForm() is not None:
			self._uiForm()._ui_show_exception_(group, name, message, detail)
		else:
			# This will be displayed by Desktop as Remote error
			raise RuntimeError, "Can't show exception because no form. Original exception:\n%s: %s\n%s" % (name, message, detail)
			

	# ---------------------------------------------------------------------------
	# Exit the application
	# ---------------------------------------------------------------------------

	def _ui_exit_(self):
		"""
		Exit the application.
		"""
		pass


	def hide_splash(self):
		pass


	def handleError(self, etype, value, traceback):
		self._instance.show_exception(*errors.getException(None, etype, value, traceback))


	def _setInstance(self, instance):
		self._instance = instance

	
	def _uiForm(self):
		# TODO: desktop should be remote object too

		forms = self._instance._GFInstance__loaded_forms
		if forms:
			return tuple(forms)[0].uiWidget


	def getUserContext(self):
		# retrieve user context for session with session id
		# sid will be deprecated, only user_id is used with django javaui server
		sid = self._instance.getGlobal('sid', None)
		user_id = self._instance.getGlobal('user_id', None)
		if sid and user_id is not None:
			return self._getUserContextBySid(sid, user_id)
