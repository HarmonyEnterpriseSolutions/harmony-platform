# GNU Enterprise Forms - The Forms Client
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
# $Id: GFClient.py,v 1.2 2008/11/04 20:14:12 oleg Exp $

"""
Command line client startup file that parses args, imports the required UI,
configures the controling GFInstance and passes control to it.
"""
__revision__ = "$Id: GFClient.py,v 1.2 2008/11/04 20:14:12 oleg Exp $"

import os, sys

from gnue.common.apps import GConfig
from gnue.common.apps.i18n import utranslate as u_      # for epydoc
from gnue.common.apps.GClientApp import GClientApp, StartupError
from gnue.common.utils.FileUtils import dyn_import
from gnue.common.utils import CaselessDict

from gnue.forms import VERSION
from gnue.forms.GFInstance import GFInstance
from gnue.forms.GFConfig import ConfigOptions
from gnue.forms.uidrivers._base import Exceptions

try:
	from gnue.reports.base.GRConfig import ConfigOptions as ReportsConfigOptions

	REPORTS_SUPPORT = True

except:
	REPORTS_SUPPORT = False


# =============================================================================
# GNU Enterprise Forms Client
# =============================================================================

class GFClient (GClientApp):

	VERSION = VERSION
	COMMAND = "gnue-forms"
	NAME    = "GNUe Forms"
	USAGE   = "%s file" % GClientApp.USAGE
	SUMMARY = u_(
		"GNUe Forms is the primary user interface to the GNU Enterprise "
		"system.")
	USE_DATABASE_OPTIONS = True


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections = None):

		self.addCommandOption ('user_interface', 'u', 'interface', argument = "ui",
			category = "ui",
			help = _("The name of the user interface to use to display your form. "
				"For a list of interfaces, use the --help-ui options."))

		self.addCommandOption ('help-ui', action = self.__listUIs, category = "ui",
			help = _("Prints a list of user interfaces that forms supports."))

		self.addCommandOption ('no-splash', 's', category = "ui",
			help = _('Disables the splash screen'))

		GClientApp.__init__(self, connections, 'forms', ConfigOptions)
		self.configurationManager.registerAlias ('gConfigForms', 'forms')

		if REPORTS_SUPPORT:
			self.configurationManager.loadApplicationConfig (section = "reports",
				defaults = ReportsConfigOptions)
			self.configurationManager.registerAlias ('gConfigReports', 'reports')

		# Load default configuration options
		self._ui = None
		self.ui_type = gConfigForms ('DefaultUI')
		self.disableSplash = self.OPTIONS['no-splash']

	# ---------------------------------------------------------------------------
	# Run the client application
	# ---------------------------------------------------------------------------

	def run (self):
		"""
		Main method of GFClient

		Responsible for setting up the desired UI driver, parsing command line
		arguments, loading the desired form, and passing control to the GFInstance
		that will control the application.

		"""
		assert gEnter (4)

		# -------------------------------------------------------------------------
		# User interface setup
		# -------------------------------------------------------------------------
		if gConfigForms ('disableSplash') == True:
			self.disableSplash = True

		assert gDebug (4, "Loading user interface driver")

		SPECIFIC_UI = bool(self.OPTIONS ['user_interface'])
		if SPECIFIC_UI:
			self.ui_type = self.OPTIONS ['user_interface']

		while 1:
			try:
				self._ui = dyn_import ("gnue.forms.uidrivers.%s" % self.ui_type)
				break

			except ImportError, err:
				assert gDebug (1, "Unknown UI Driver: %s" % self.ui_type)
				assert gDebug (1, err)

				raise StartupError, \
					u_("Unknown UI driver specified: %s") % self.ui_type

			except Exceptions.UIException, err:
				if not SPECIFIC_UI and self.ui_type.lower () != 'curses':
					self.ui_type = 'curses'

				else:
					raise StartupError, u_("Unable to load UI driver: %s") % err

		# start webserver for HTML UI driver
		if hasattr(self._ui,"start_server"):
			self._ui.start_server(self)
			return

		# -------------------------------------------------------------------------
		# Get the user supplied parameters
		# -------------------------------------------------------------------------
		# User supplied parameters are a way of passing initial values into form
		# variables from the command line
		#
		assert gDebug (4, "Parsing command line parameters")

		userParameters = CaselessDict.CaselessDict ()
		for (k, v) in  (self.getCommandLineParameters (self.ARGUMENTS [1:])).items():
			userParameters [k] = v



		# Create the instance that will control the loaded form(s)
		assert gDebug (4, "Creating GFInstance object")

		instance = GFInstance (self, self.connections, self._ui,
			self.disableSplash, userParameters)

		# UI is now loaded and in a usable state, so use better exception display
		self._showException = instance.show_exception

		# Assign the proper login handler based upon the user interface choice
		# FIXME: IMHO, it would be much better if the login handler would be just a
		# function, which could be a method of the GFUserInterfae object - much
		# like _showException.  -- Reinhard
		loginHandler = self._ui.UILoginHandler ()
		loginHandler.uiDriver = instance._uiinstance
		self.getConnectionManager ().setLoginHandler (loginHandler)

		# assign form file from 1st free argument
		if len (self.ARGUMENTS):
			formfile = self.ARGUMENTS [0]

		else:
			basename = os.path.basename (sys.argv [0])

			# If no form specified, then see if this is a symlinked form definition
			if not basename.lower ().split ('.') [0] in ('gnue-forms', 'gfclient'):
				formfile = os.path.join (
					GConfig.getInstalledBase ('forms_appbase', 'common_appbase',
						'install_prefix'),
					gConfigForms ('FormDir'), basename + ".gfd")
			else:
				raise StartupError, u_("No Forms Definition File Specified.")

		assert gDebug (4, "Parsing form definition")
		instance.run_from_file(formfile, userParameters)

		assert gDebug (4, "Closing all connections")
		self.getConnectionManager ().closeAll ()

		assert gLeave (4)


	# ---------------------------------------------------------------------------
	# List all available user interfaces
	# ---------------------------------------------------------------------------

	def __listUIs (self):
		"""
		Helper function to print a list of user interfaces that forms supports

		If this functoin is called then it will print out the help text and then
		force exit of the program.
		"""
		self.printHelpHeader ()
		print _("The following interfaces are supported by GNUe Forms. "
			"You can select an\ninterface via the --interface option.")
		print
		print _("To view general help, run this command with the --help option.")
		print
		print _('User interface command line options:')
		print self.buildHelpOptions ("ui")

		# TODO: This should be automated
		print "Available user interfaces:"
		print "   wx       wxPython-based graphical interface"
		print "   gtk2     GTK2-based graphical interface"
		print "   qt3      QT3-based graphical interface"
		print "   win32    Native Windows graphical interface"
		print "   curses   Text-based interface that uses ncurses"
		self.printHelpFooter ()
		sys.exit ()

# =============================================================================
# Main program
# =============================================================================

if __name__ == '__main__':
	GFClient ().run ()
