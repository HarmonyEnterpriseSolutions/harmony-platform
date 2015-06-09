# GNU Enterprise Forms - UI Driver - Base class for user interfaces
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
# $Id: UIdriver.py,v 1.10 2008/12/08 21:22:29 oleg Exp $

import sys, os, dircache
import traceback
import weakref

from gnue.common import events
from gnue.common.definitions.GObjects import *
from gnue.common.definitions.GRootObj import GRootObj
from gnue.common.utils.FileUtils import dyn_import
from gnue.common.apps import errors

from gnue.forms.GFForm import *
from gnue.forms import VERSION

# =============================================================================
# Exceptions
# =============================================================================

class ImplementationError (errors.SystemError):
	def __init__ (self, drivername, method):
		msg = u_("The UI-Driver %(name)s has no implementation of %(method)s") \
			% {'name': drivername,
			'method': method}
		errors.SystemError.__init__ (self, msg)


# -----------------------------------------------------------------------------
# Guess a default iconset for the current environment
# -----------------------------------------------------------------------------

def guessDefaultIconset ():
	"""
	Guess the default iconset to use in this environment
	"""

	# TODO: This is *very* crude logic
	try:
		import mac
		return 'macosx'
	except ImportError:
		try:
			winver = sys.getwindowsversion()
			if winver[0]>5 or (winver[0]==5 and winver[1]>=1 and winver[3]==2):
				# TODO: we have no winxp iconset yet
				# return 'winxp'
				return 'default'
			else:
				return 'default'
		except AttributeError:
			try:
				import posix
				if os.environ.get('KDE_FULL_SESSION',''):
					return 'kde3'
				ds = os.environ.get('DESKTOP_SESSION','')
				if ds[:3] == 'kde':
					return 'kde3'
				elif ds[:5] == 'gnome':
					return 'gnome'
				else:
					return 'default'
			except ImportError:
				return 'default'



# =============================================================================
# Base class for UI drivers
# =============================================================================

class GFUserInterfaceBase (GRootObj, events.EventAware):

	default_iconset = guessDefaultIconset ()

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__(self, eventHandler, name = "Undefined", disableSplash = None,
		parentContainer = None, moduleName = None):
		"""
		"""
		# moduleName is here only for Designer to be able to pass it in
		#when debugging a form.

		GRootObj.__init__(self, 'uiDriver', None, None)

		self.name           = name
		self._type          = 'UIDriver'
		self._disableSplash = disableSplash

		# Used when forms are embedded in navigator. What parentContainer is
		# depends on the individual UIdriver and Navigator.
		self._parentContainer = parentContainer

		events.EventAware.__init__(self, eventHandler)

		# So other modules can get to the ui
		__builtins__ ['forms_ui']  = self

		# Import and register supported widgets in UI driver
		self._supportedWidgets = {}

		if moduleName:  #We are within Designer, running a form
			basedir = os.path.dirname(sys.modules[moduleName].__file__)
		else:   #Normal case
			basedir  = os.path.dirname (sys.modules [self.__module__].__file__)

		uiDriver = os.path.basename (basedir)
		basedir = os.path.join(basedir, 'widgets')
		ignored = set(['CVS'])
		for fname in dircache.listdir(basedir):
			widgetName, ext = os.path.splitext(fname)
			if widgetName and widgetName[0] != '_' and '.' not in widgetName and widgetName not in ignored:
				ignored.add(widgetName)
				try:
					widget = dyn_import('gnue.forms.uidrivers.%s.widgets.%s' % (uiDriver, widgetName))
				except:
					print >> sys.stderr, "* Error while importing ui widget '%s'" % widgetName
					print >> sys.stderr, ''.join(traceback.format_exception(*sys.exc_info()))
				else:
					self._supportedWidgets[widget.configuration['provides']] = widget

	# ---------------------------------------------------------------------------
	# Build the user interface
	# ---------------------------------------------------------------------------

	def _buildUI (self, gfObject, gfForm, gfContainer):
		try:
			supported = self._supportedWidgets[gfObject._type]
		except KeyError:
			assert gDebug(4, "No UI Widget provided for type '%s' in _buildUI" % gfObject._type)
		else:

			parent = gfObject.getParent()

			# find the ui widget that corrosponds with that parent
			if gfObject._type == 'GFForm':
				uiParent = self
			elif parent._type == 'GFLayout':
				uiParent = parent.getParent().uiWidget
			else:
				uiParent = parent.uiWidget

			assert uiParent, "Can't get uiParent for %s (parent=%s)" % (gfObject, parent)

			# all references passed to UIWidget are weak
			# to avoid backrefs from driver as it can be gc unsafe

			# Build widget
			event = events.Event ('CreateUIWidget',
				eventHandler = weakref.proxy(self.dispatchEvent),
				object       = weakref.proxy(gfObject),
				parent       = weakref.proxy(uiParent),
				#container   = self.currentWidget[0],
				textWidth    = self.textWidth,
				textHeight   = self.textHeight,
				widgetWidth  = self.widgetWidth,
				widgetHeight = self.widgetHeight,
				interface    = weakref.proxy(self),
				initialize   = 1,

				gfForm       = weakref.proxy(gfForm),				# GFForm containing this object
				uiContainer  = (gfContainer or gfForm).uiWidget,	# uiobject containing this form
			)

			uiWidget  = supported.configuration ['baseClass'] (event)

			# Store UIWidget reference with GFObj based object that created it
			gfObject.uiWidget = uiWidget



	#############################################################################
	#
	# Public Interface
	#
	# The interface exposed to the forms backend
	#
	#


	# ---------------------------------------------------------------------------
	# Build a form from a GObj tree
	# ---------------------------------------------------------------------------

	def buildForm (self, gfForm, gfContainer):

		# Create the UI from the GFForm passed in
		gfForm.walk (self._buildUI, gfForm, gfContainer)
		gfForm.uiWidget.phaseInit()


	#############################################################################
	#
	# Optional Functions
	#
	# UIDrivers can override the following functions
	#


	# ---------------------------------------------------------------------------
	# Get an input dialog for a given set of fields
	# ---------------------------------------------------------------------------

	def getInput (self, title, fields, cancel = True):
		"""
		Prompt the user for a given number of fields and return the result as
		dictionary.

		@param title: title of the input dialog
		@param fields: field definition as described below
		@param cancel: if True the dialog has a cancel button, otherwise not

		These field definitions are specified as follows:

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
		        allowed values. If a value is selected in one control, all others
		        are synchronized to represent the same key-value.
		- default: Default value to use
		- masterfield: Used for 'dropdowns'. This item specifies another field
		    definition acting as master field. If this master field is changed, the
		    allowedValues of this dropdown will be changed accordingly. If a
		    masterfield is specified the 'allowedValues' dictionaries are built like
		    {master1: {key: value, key: value, ...}, master2: {key: value, ...}}
		- elements: sequence of input element tuples (label, allowedValues). This
		    is used for dropdowns only. 'label' will be used as ToolTip for the
		    control and 'allowedValues' gives a dictionary with all valid keys to
		    be selected in the dropdown.

		@return: If closed by 'Ok' the result is a dictionary with all values
		  entered by the user, where the "fieldname"s will be used as keys. If the
		  user has not selected a value from a dropdown (i.e. it has no values to
		  select) there will be no such key in the result dictionary. If the dialog
		  is canceled ('Cancel'-Button) the result will be None.
		"""

		return self._getInput (title, fields, cancel)


	# ---------------------------------------------------------------------------

	def _getInput (self, title, fields, cancel):

		raise ImplementationError, (self.name, '_getInput')
