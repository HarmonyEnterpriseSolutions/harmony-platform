# GNU Enterprise Common Library - Application Services - Base Application Class
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
# $Id: GBaseApp.py,v 1.3 2008/11/04 20:14:00 oleg Exp $
"""
Class that provides a basis for GNUe applications.

Typically, this class will not be called; rather, a tool will be a GClientApp
or GServerApp.
"""
from src.gnue.common.apps import manpage

__revision__ = "$Id"

import sys
import os
import getopt
import types
import ConfigParser
import gc
import signal
import locale

from gnue import paths

from gnue.common.datasources import GConnections
from gnue.common.apps.CommandOption import CommandOption


# =============================================================================
# Exceptions
# =============================================================================

class StartupError (errors.UserError):
	"""
	Error raised when a gnue application fails during initial startup prior to
	initializing to the point that better error handlers are available.
	"""
	pass


# =============================================================================
# Base class for GNUe Applications
# =============================================================================

class GBaseApp:
	"""
	The base class of the various GNUe application classes.

	GBaseApp Provides the following features
	  - Command line argument parsing
	  - Run time debug output levels
	  - An integrated profiler
	  - An integrated debugger
	"""

	# Attributes to be overwritten by subclasses
	VERSION = "0.0.0"
	NAME    = "GNUe Application"
	COMMAND_OPTIONS = []      # Should be in same format as _base_options below
	SUMMARY = "A brief summary of the program goes here."
	COMMAND = "app"
	USAGE   = "[options]"
	USE_CONNECTIONS      = 1  # Set to 1 if the program uses dbdrivers
	USE_DATABASE_OPTIONS = 0  # Also implies USE_CONNECTIONS = 1
	USE_RPC_OPTIONS      = 0


	# More options, but won't be changed unless this is a non-GNUe app using
	# GNUe-Common
	AUTHOR         = "GNU Enterprise Project"
	EMAIL          = "info@gnue.org"
	REPORT_BUGS_TO = "Please report any bugs to info@gnue.org."
	CONFIGFILE     = "gnue.conf"


	# Attributes that will be set by GClientApp after __init__ has run
	OPTIONS     = {}    # Will contain a hash containing command line options
	ARGUMENTS   = []    # Will contain an array of command line arguments
	connections = None  # Will contain a GConnection object

	# ---------------------------------------------------------------------------
	# Create a new GNUe Application
	# ---------------------------------------------------------------------------

	def __init__ (self, connections = None, application = 'common',
		defaults = None):
		"""
		@param connections:
		@param application:
		@param defaults:
		"""

		self.configDefaults = defaults

		sys.excepthook = self.excepthook

		# Basic options
		self._base_options = [
			##
			## Base options
			##
			CommandOption ('version', category = "base", action = self.doVersion,
				help = u_('Displays the version information for this program.')),

			CommandOption ('debug-level', category = "base", default = 0,
				argument = u_("level"),
				help = u_('Enables debugging messages.  Argument specifies the '
					'level of messages to display (e.g., "--debug-level 5" '
					'displays all debugging messages at level 5 or below.)')),

			CommandOption ('debug-file', category = "base", argument = u_("filename"),
				help = u_('Sends all debugging messages to a specified file '
					'(e.g., "--debug-file trace.log" sends all output to '
					'"trace.log")')),

			# This is actually handled during the initial GDebug import but is added
			# here so that applications won't abort with an unknown option.
			CommandOption ('debug-imports', category = "dev",
				help = u_('All python imports are logged to stdout')),

			CommandOption ('silent', category = "base",
				help = u_('Displays no output at all.')),

			CommandOption ('help', category = "base", action = self.printHelp,
				help = u_('Displays this help screen.')),

			CommandOption ('help-config', category = "base",
				action = self.doHelpConfig,
				help = u_('Displays a list of valid configuration file entries, their '
					'purpose, and their default values.')),

			##
			## Developer options
			##

			CommandOption ('help-dev', category = "base", action = self.printHelpDev,
				help = u_('Display all options of interest to core developers. ')),

			CommandOption ('selfdoc', category = "dev", action = self.doSelfDoc,
				argument = u_("type[,subtype]"),
				help = u_('Generates self-documentation.')),

			CommandOption ('selfdoc-format', category = "dev",
				argument = u_("format"),
				help = u_('Format to output the self-documentation in. Supported '
					'formats are dependent on the type of selfdoc being '
					'created.')),

			CommandOption ('selfdoc-file', category = "dev",
				argument = u_("filename"),
				help = u_('Specifies the filename that selfdoc should write to. If not '
					'provided, output is sent to stdout.')),

			CommandOption ('selfdoc-options', category = "dev",
				argument = u_("options"),
				help = u_('Options specific to individual selfdoc types.')),

			CommandOption ('profile', category = "dev",
				help = u_("Run Python's built-in profiler and display the resulting "
					"run statistics.")),

			CommandOption ('interactive-debugger', category = "dev",
				help = u_("Run the app inside Python's built-in debugger ")),

			CommandOption ('debug-gc', 'g', 'debug-gc', True, None, "logfile",
				category = "dev", action = self.__installGCHandler,
				help = u_("Debug Python's garbage collection on a SIGUSR1. If the "
					"argument is empty 'garbage.log' will be used as "
					"logfile.")),

		#CommandOption ('garbagelog', 'l'
		]

		if self.USE_DATABASE_OPTIONS:
			self.USE_CONNECTIONS = 1
			self._base_options.extend ([ \
						CommandOption ('username', category = "connections", default = '',
						argument = u_('name'),
						help = u_('Username used to log into the database.  Note that if '
							'specified, this will be used for all databases.  If not '
							'supplied, the program will prompt for username.')),

					CommandOption ('password', category = "connections", default = '',
						argument = u_('passwd'),
						help = u_('Password used to log into the database.  Note that if '
							'specified, this will be used for all databases.  If not '
							'supplied, the program will prompt for password if needed.'
							'\nNOTE: SUPPLYING A PASSWORD VIA THE COMMAND LINE MAY BE '
							'CONSIDERED A SECURITY RISK AND IS NOT RECOMMENDED.'))])

		if self.USE_CONNECTIONS:
			self._base_options += [
				CommandOption ('help-connections', category = "base",
					action = self.printHelpConn,
					help = u_('Display help information related to database '
						'connections, including a list of available drivers.')),

				CommandOption ('connections', category = "connections",
					argument = u_("location"),
					help = u_('Specifies the location of the connection definition file. '
						'<location> may specify a file name '
						'(/usr/local/gnue/etc/connections.conf),'
						'or a URL location '
						'(http://localhost/connections.conf).'
						'If this option is not specified, the environent variable '
						'GNUE_CONNECTIONS is checked.'
						'If neither of them is set, "%s" is used as a default.') %
					os.path.join (paths.config, "connections.conf")) ]

		# Python version check
		if not hasattr (sys, 'hexversion') or sys.hexversion < 0x02030000:
			msg = u_("This application requires Python 2.3 or greater.")
			if hasattr (sys, 'version'):
				msg = u_("This application requires Python 2.3 or greater. "
					"You are running Python %s") % sys.version [:5]

			raise errors.AdminError, msg


		#
		# Get all command line options and arguments
		#
		shortoptions = ""
		longoptions  = []
		lookup       = {}
		actions      = {}

		# Convert old-style options to new-style
		if self.COMMAND_OPTIONS and \
			isinstance (self.COMMAND_OPTIONS [0], types.ListType):
			options = self.COMMAND_OPTIONS
			self.COMMAND_OPTIONS = []
			for option in options:
				self.COMMAND_OPTIONS.append (CommandOption (*option))

		for optionset in [self._base_options, self.COMMAND_OPTIONS]:
			for option in optionset:
				self.OPTIONS[option.name] = option.default
				if option.shortOption:
					shortoptions += option.shortOption
					lookup["-" + option.shortOption] = option.name
				lookup["--" + option.longOption] = option.name
				if option.action:
					actions["--" + option.longOption] = option.action
				lo = option.longOption
				if option.acceptsArgument:
					lo += '='
					shortoptions += ':'
				longoptions.append(lo)


		# mod_python apps don't have an argv
		# so create an empty one.
		# TODO: This class needs adjusted to
		#       be more efficent in mod_python cases
		#       But not this close to a release :)
		if not sys.__dict__.has_key('argv'):
			sys.argv = []

		try:
			opt, self.ARGUMENTS = getopt.getopt (sys.argv[1:], shortoptions,
				longoptions)
		except getopt.error, msg:
			raise StartupError, "%s" % msg

		pendingActions = []
		for o in opt:
			if len(o[1]):
				self.OPTIONS[lookup[o[0]]] = o[1]
			else:
				self.OPTIONS[lookup[o[0]]] = True

			# Add any actions to our list
			try:
				pendingActions.append(actions[o[0]])
			except KeyError:
				pass

		for task in pendingActions:
			task()

		self._run = self.run

		# Are we silent?
		if self.OPTIONS['silent']:
			# our file objects (/dev/null and nul) has no encoding, unlike stdout...
			import __builtin__
			__builtin__.__dict__['u_'] = __builtin__.__dict__['_']
			if os.name == 'posix':
				sout = open('/dev/null','w')
				serr = open('/dev/null','w')
			elif os.name == 'nt':
				sout = open('nul', 'w')
				serr = open('nul', 'w')

			try:
				sys.stdout.close()
				sys.stdout = sout
				sys.stderr.close()
				sys.stderr = serr
			except:
				pass

		# Should we profile?
		if self.OPTIONS['profile']:
			self.run = self._profile

		# Setup debugging
		# Should we run in debugger?
		elif self.OPTIONS['interactive-debugger']:
			self.run = self._debugger

		try:
			GDebug.setDebug ("%s" % self.OPTIONS ['debug-level'],
				self.OPTIONS ['debug-file'])
		except ValueError:
			raise StartupError, \
				u_('The debug_level option ("-d") expects numerical values.')

		assert gDebug (2, "Python %s" % sys.version)
		assert gDebug (2, "Run Options: %s" % opt)
		assert gDebug (2, "Run Arguments: %s" % self.ARGUMENTS)

		# Read the config files
		if application:
			try:
				self.configurationManager = GConfig.GConfig (application,
					self.configDefaults, configFilename = self.CONFIGFILE)

			except ConfigParser.NoSectionError, msg:
				raise errors.AdminError, \
					u_("The gnue.conf file is incomplete:\n   %s") % msg

		# Add custom import to python's namespace
		try:
			extrapaths = gConfig('ImportPath')
		except:
			extrapaths = ""
		if extrapaths:
			for path in extrapaths.split(','):
				p = path.strip()
				if not p in sys.path:
					sys.path.append(p)

		# Get the connection definitions
		if connections != None:
			assert gDebug(7,"Reusing connections instance")
			self.connections = connections
		elif self.USE_CONNECTIONS:

			# Check for default username/password
			lhOptions = {}
			if self.USE_DATABASE_OPTIONS:
				if self.OPTIONS['username']:
					lhOptions['_username'] = self.OPTIONS['username']
				if self.OPTIONS['password']:
					lhOptions['_password'] = self.OPTIONS['password']

			if self.OPTIONS['connections']:
				self.connections_file = self.OPTIONS['connections']
			elif os.environ.has_key('GNUE_CONNECTIONS'):
				self.connections_file = os.environ['GNUE_CONNECTIONS']
			else:
				self.connections_file = os.path.join (paths.config, "connections.conf")
				# assume connection file is empty if default location file not exist
				if not os.path.exists(self.connections_file):
					self.connections_file = ''

			assert gDebug(2, 'Connection Definition: "%s"' % self.connections_file)

			try:
				self.connections = GConnections.GConnections (self.connections_file,
					loginOptions = lhOptions)
			except GConnections.InvalidFormatError, msg:
				raise errors.AdminError, \
					u_("Unable to load the connections definition file.\n\n"
					"The connections file is in an invalid format.\n%s") % msg

			except IOError:
				raise StartupError, \
					u_("Unable to load the connections definition file: %s.") \
					% self.connections_file


	# ---------------------------------------------------------------------------
	# Run the program
	# ---------------------------------------------------------------------------

	def run(self):
		"""
		Run the program. This function will be overriden by a descendant.
		"""

		pass


	# ---------------------------------------------------------------------------
	# Add a new option to the program
	# ---------------------------------------------------------------------------

	def addCommandOption(self, *args, **parms):
		"""
		Create a new command option and add it to the options sequence.

		@param args: positional arguments for the command option's constructor
		@param parms: keyword arguments for the command option's constructor
		"""

		self.COMMAND_OPTIONS.append (CommandOption (*args, **parms))


	# ---------------------------------------------------------------------------
	# Display version information for this application
	# ---------------------------------------------------------------------------

	def printVersion (self):
		"""
		Display version information for this application
		"""

		from gnue.common import VERSION as commonVersion
		print o(u_("\n%(name)s\nVersion %(version)s\n") \
				% {'name': self.NAME, 'version': self.VERSION})
		print o(u_("GNUe Common Version %s\n") % commonVersion)


	# ---------------------------------------------------------------------------
	# Build help options
	# ---------------------------------------------------------------------------

	def buildHelpOptions (self, category = None):
		"""
		Build 'help text' for all options of the given category. If no category is
		given all options except the 'dev' options will be included.

		@param category: if not None only options of this category will be included.

		@return: string with the help text for all matching options.
		"""

		allOptions  = {}
		descriptors = {}
		maxLength   = 0

		for optionset in [self._base_options, self.COMMAND_OPTIONS]:
			for option in optionset:
				# Limit this to the correct category. A category of None implies all
				# options except "dev".
				if not (  ( category is None and \
							option.category != "dev" ) or \
						( category == option.category ) ):
					continue

				allOptions [option.longOption.upper ()] = option

				if option.acceptsArgument:
					descr = '--%s <%s>' % (option.longOption, option.argumentName)
				else:
					descr = '--%s' % (option.longOption)
				if option.shortOption:
					descr += ', -%s' % option.shortOption

				descriptors [option.longOption.upper()] = descr

				maxLength = max(len (descr), maxLength)

		maxLength = min(10, maxLength)

		sorted = allOptions.keys ()
		sorted.sort ()

		dispOptions = u""

		for optionKey in sorted:
			margin = maxLength + 4
			width  = 78 - margin
			pos    = 0

			if len (descriptors [optionKey]) > maxLength:
				dispOptions += "\n  %s\n%s" % (descriptors [optionKey], " " * margin)
			else:
				dispOptions += "\n  %s  %s" % (descriptors [optionKey],
					" " * (maxLength - len (descriptors [optionKey])))

			for word in allOptions [optionKey].help.split():
				if (len (word) + pos) > width:
					pos = 0
					dispOptions += "\n" + " " * margin

				pos = pos + len (word) + 1

				dispOptions += word + " "

			dispOptions +=  "\n"

		return dispOptions


	# ---------------------------------------------------------------------------
	# Print a usage header
	# ---------------------------------------------------------------------------

	def printHelpHeader(self):
		"""
		Print version information and the usage header
		"""

		self.printVersion ()
		print o(u_("Usage:  ") + self.COMMAND + ' ' + self.USAGE)
		print


	# ---------------------------------------------------------------------------
	# Print help footer
	# ---------------------------------------------------------------------------

	def printHelpFooter(self):
		"""
		Print the help footer including the address for bug reports.
		"""

		print
		print o("%s\n" % self.REPORT_BUGS_TO)


	# ---------------------------------------------------------------------------
	# Display help information for this program
	# ---------------------------------------------------------------------------

	def printHelp (self):
		"""
		Print help information for this application and quit the program. This
		includes the version, the usage, the application's summary and all
		available command options (without the 'developer' options).
		"""

		self.printHelpHeader ()
		print o("\n" + self.SUMMARY + '\n')

		print o(u_('Available command line options:'))
		print o(self.buildHelpOptions ())
		self.printHelpFooter ()

		sys.exit ()


	# ---------------------------------------------------------------------------
	# Display dev help information for this program
	# ---------------------------------------------------------------------------

	def printHelpDev (self):
		"""
		Print help information for this application and quit the program. This
		includes the version, usage and all available developer's command options.
		"""

		self.printHelpHeader ()

		print o(u_("The following options are mainly of interest to GNUe "
				"developers."))
		print o(u_("To view general help, run this command with the --help "
				"option."))
		print
		print o(u_('Developer-specific command line options:'))
		print o(self.buildHelpOptions ("dev"))
		self.printHelpFooter ()

		sys.exit ()


	# ---------------------------------------------------------------------------
	# Print connection-specific help information
	# ---------------------------------------------------------------------------

	def printHelpConn (self):
		"""
		Print connection/database-related help information and quit the program.
		"""

		self.printHelpHeader ()

		print o(u_("The following connection/database-related options are "
				"available."))
		print o(u_("To view general help, run this command with the --help "
				"option."))
		print
		print o(u_('Database/connection command line options:'))
		print o(self.buildHelpOptions ("connections"))
		print
		print o(u_('The following database drivers are installed on your system:'))
		print "   TODO\n"
		# print self.connections.getAvailableDrivers()
		self.printHelpFooter ()

		sys.exit ()


	# ---------------------------------------------------------------------------
	# Run the self-documentation for a program
	# ---------------------------------------------------------------------------

	def selfdoc (self, command, handle, format = None, options = {}):
		"""
		Run the self-documentation for an application. Currently only the command
		'manpage' is supported.

		@param command: can be 'manpage' only atm
		@param handle: file-like object to write the documentation contents to.
		    This file handle must be already opened for writing.
		@param format: not used in the current version
		@param options: not used in the current version
		"""

		if command == 'manpage':
			manpage.ManPage (self, handle, format, options)


	# ---------------------------------------------------------------------------
	#
	# ---------------------------------------------------------------------------

	def getCommandLineParameters (self, paramList):
		"""
		Convert a sequence of parameters (i.e. '--foo=bar') into a parameter
		dictionary, where the paramter ('--foo') is the key and it's argument
		('bar') is the value.

		@param paramList: sequence of parameters (usually from self.ARGUMENTS)
		@return: dictionary of parameters, splitted by the first '='

		@raises StartupError: if a parameter has no value assigned
		"""

		parameters = {}
		for param in [unicode(p, locale.getpreferredencoding()) for p in paramList]:
			psplit = param.split('=', 1)
			if len (psplit) == 1:
				raise StartupError, \
					'Parameter "%s" specified, but no value supplied.' % psplit [0]
			parameters [psplit [0].lower()] = psplit [1]

			assert gDebug (2,'Param "%s"="%s" ' % (psplit [0].lower(), psplit [1]))

		return parameters


	# ---------------------------------------------------------------------------
	# Display a startup error and exit gracefully
	# ---------------------------------------------------------------------------

	def handleStartupError (self, msg):
		"""
		Display a startup error and exit gracefully. This function is depreciated.
		Descendants should use the concpet of exceptions instead, which will be
		handled by the exception hook installed by this class.
		"""

		self.printVersion ()

		# if msg is multiline, then surround with dashes to set it apart
		if ("%s" % msg).find("\n") + 1:
			print '-' * 60

		print o(u_("Error: %s") % msg)
		if ("%s" % msg).find("\n") + 1:
			print '-' * 60

		print o(u_("\nFor help, type:\n   %s --help\n") % self.COMMAND)

		sys.exit ()


	# ---------------------------------------------------------------------------
	# Display version information
	# ---------------------------------------------------------------------------

	def doVersion (self):
		"""
		Display the version information and quit the program.
		"""

		self.printVersion ()
		sys.exit ()


	# ---------------------------------------------------------------------------
	# Run the self documentation
	# ---------------------------------------------------------------------------

	def doSelfDoc (self):
		"""
		Run the self documentation. If a documentation file is specified the
		contents will be written to that file, otherwise it will be printed to
		stdout.
		"""

		if self.OPTIONS ['selfdoc-file']:
			doprint = False
			handle  = open (self.OPTIONS ['selfdoc-file'], 'w')
		else:
			doprint = True
			import StringIO
			handle = StringIO.StringIO

		try:
			self.selfdoc (self.OPTIONS ['selfdoc'], handle,
				self.OPTIONS ['selfdoc-format'],
				self.OPTIONS ['selfdoc-options'])
			if doprint:
				handle.seek (0)
				print o(handle.read ())

		finally:
			handle.close ()

		sys.exit ()


	# ---------------------------------------------------------------------------
	# Display information about the configuration settings
	# ---------------------------------------------------------------------------

	def doHelpConfig (self):
		"""
		Display all configuration settings and their default values and quit the
		program.
		"""

		self.printHelpHeader ()
		print o(GConfig.printableConfigOptions (self.configDefaults))

		sys.exit ()


	# ---------------------------------------------------------------------------
	# Catch an exception
	# ---------------------------------------------------------------------------

	def excepthook (self, etype, value, traceback):
		"""
		This function catches an exception and evaluates it using getException ().
		The exception-tuple is then passed to showException (), which might get
		overriden by a descendant.
		"""
		sys.excepthook = sys.__excepthook__
		self._showException (*errors.getException (None, etype, value, traceback))
		sys.excepthook = self.excepthook


	# ---------------------------------------------------------------------------
	# Used when interactive debugger in use
	# ---------------------------------------------------------------------------

	def _debugger (self):
		"""
		Run the application in the python debugger.
		"""

		import pdb

		debugger = pdb.Pdb ()
		GDebug.setDebugger (debugger)
		debugger.runctx ('self._run ()', globals (), locals ())


	# ---------------------------------------------------------------------------
	# Used when profiling
	# ---------------------------------------------------------------------------

	def _profile (self):
		"""
		Run the application through the python profiler and print some statistics
		afterwards.
		"""

		import profile
		prof = profile.Profile ()
		prof.runctx ('self._run ()', globals (), locals ())

		import pstats
		p = pstats.Stats (prof)
		p.sort_stats ('time').print_stats (50)
		p.sort_stats ('cumulative').print_stats (50)
		p.sort_stats ('calls').print_stats (50)


	# ---------------------------------------------------------------------------
	# Show an exception
	# ---------------------------------------------------------------------------

	def _showException (self, group, name, message, detail):
		"""
		This function shows an exception specified by the given parameters.
		@param group: Exception group ('system', 'admin', 'application', 'user')
		@param name: Name of the exception
		@param message: Message of the exception
		@param detail: Detail of the exception (usually holding a traceback)
		"""

		if group in ['user', 'admin']:
			sys.__stderr__.write ("%s: %s\n" % (self.COMMAND, o(message)))
			sys.__stderr__.write ("%s\n" % \
					o(u_("For help, type: %s --help") % self.COMMAND))
		else:
			sys.stderr.write ("%s\n" % o(detail))


	# ---------------------------------------------------------------------------
	# Install a signal handler for SIGUSR1
	# ---------------------------------------------------------------------------

	def __installGCHandler (self):
		"""
		Install a signal handler for SIGUSR1, which actually performs the debugging.
		"""

		signal.signal (signal.SIGUSR1, self.debugGarbageCollection)


	# ---------------------------------------------------------------------------
	# Debug Python's garbage collection
	# ---------------------------------------------------------------------------

	def debugGarbageCollection (self, signal, frame):
		"""
		Debug Python's garbage collection.

		@param signal: signal number caught by this handler (=SIGUSR1)
		@param frame: the current stack frame or None
		"""

		filename = "garbage.log"
		if isinstance (self.OPTIONS ['debug-gc'], basestring):
			filename = self.OPTIONS ['debug-gc']

		log = open (filename, 'w')
		try:
			# If we are interested in the objects collected by the garbage collection
			# set the debug level to gc.DEBUG_LEAK. In this case gc.garbage contains
			# all objects, collectable and uncollectable as well and we are able to
			# inspect those cycles and objects.
			gc.collect ()

			self.__gcLog (log, "Number of unreachable objects: %d" % len (gc.garbage))
			if not gc.garbage:
				return

			try:
				self.__gcLog (log, "Dump of gc.garbage sequence:")
				self.__gcLog (log, "-" * 70)

				for item in gc.garbage:
					try:
						itemrep = "%s: %s" % (type (item), repr (item))
					except:
						itemrep = "No representation available for object (weakref/proxy?)"

					self.__gcLog (log, "%s" % itemrep)

				for item in gc.garbage:
					cycle = self.findCycle (item, item, None, [], {})

					if cycle:
						self.__gcLog (log, "-" * 70)

						for line in self.analyzeCycle (cycle):
							self.__gcLog (log, line)

				self.__gcLog (log, "-" * 70)

			finally:
				del gc.garbage [:]

		finally:
			log.close ()


	# ---------------------------------------------------------------------------

	def __gcLog (self, filehandle, message):

		filehandle.write ("%s%s" % (message, os.linesep))
		print o(message)


	# ---------------------------------------------------------------------------
	# Find a reference cycle starting from a given object
	# ---------------------------------------------------------------------------

	def findCycle (self, search, current, last, path, seen):
		"""
		Find a reference cycle starting from a given object (current) and ending
		with a given object (search). The result is either None if no such cycle
		exists, or a sequence of tuples (repr, propertyname) describing the
		reference cycle. 'repr' is either a string representation of an object
		holding the reference or None. 'propertyname' could be one of the
		following:
		  - 'name':   name of the property within 'repr' holding the reference
		  - '[n]':    the reference is the n-th element of a sequence
		  - '[name]': the reference is the value of key 'name' in a dictionary
		  - '{}':     the reference is a key in a dictionary

		The latter three variants could be cumulative (i.e. [1][3]['foo']) and the
		corresponding propertyname is the last one encountered.

		@return: None or sequence of tuples (repr, propertyname)
		"""

		if last is not None:
			path = path + [last]

		currentId = id (current)

		# If we have already visited this object, no need to do further processing
		if seen.has_key (currentId):
			return None

		seen [currentId] = path

		# If the current object has a __dict__ property, iterate over all it's
		# properties
		if hasattr (current, '__dict__'):
			for (name, attr) in current.__dict__.items ():
				prop = (repr (current), name)

				if attr == search:
					return path + [prop]

				else:
					newpath = self.findCycle (search, attr, prop, path, seen)
					if newpath:
						return newpath

		# A bound method has a reference to self
		elif isinstance (current, types.MethodType):
			if current.im_self == search:
				return path + [(repr (current), "im_self")]

		# For Sequences or Tuples iterate over all elements
		elif isinstance (current, types.ListType) or \
			isinstance (current, types.TupleType):

			for (index, element) in enumerate (current):
				prop = (None, "[%d]" % index)
				if element == search:
					return path + [prop]

				else:
					newpath = self.findCycle (search, element, prop, path, seen)
					if newpath:
						return newpath

		# For dictionaries iterate over all items
		elif isinstance (current, types.DictType):
			for (key, element) in current.items ():
				prop = (None, "[%s]" % repr (key))

				if element == search:
					return path + [prop]

				elif  key == search:
					return path + [(None, "{}")]

				else:
					newpath = self.findCycle (search, element, prop, path, seen)
					if newpath:
						return newpath

		# a generator keeps has always reference to self, so we have to iterate
		# it's local namespace
		elif isinstance (current, types.GeneratorType):
			for (key, element) in current.gi_frame.f_locals.items ():
				prop = (None, "[%s]" % key)
				if element == search:
					return path + [prop]

				elif key == search:
					return path + [(None, "{}")]

				else:
					newpath = self.findCycle (search, element, prop, path, seen)
					if newpath:
						return newpath

		return None


	# ---------------------------------------------------------------------------
	# Analyze a given reference cycle
	# ---------------------------------------------------------------------------

	def analyzeCycle (self, cycle):
		"""
		Return a generator for iterating a given reference cycle.

		@param cycle: None or a sequence of tuples (repr, propertyname)
		@return: iterator
		"""

		if cycle:
			for (index, (rep, name)) in enumerate (cycle):
				if index == 0:
					yield 'self = %s' % rep
					lastname = 'self.%s' % name
				else:
					if rep is not None:
						yield '%s = %s' % (lastname, rep)
						jsymb = '.'
					else:
						jsymb = ' '

					lastname = jsymb.join ([lastname, name])

			yield '%s = self' % lastname
