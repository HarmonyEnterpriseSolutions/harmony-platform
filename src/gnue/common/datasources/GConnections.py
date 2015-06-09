# GNU Enterprise Common Library - Connection Manager
#
# Copyright 2000-2007 Free Software Foundation
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
# $Id: GConnections.py 9222 2007-01-08 13:02:49Z johannes $
"""
Connection manager system.
"""

from ConfigParser import *
from ConfigParser import RawConfigParser # is not in __all__

import copy, netrc

from gnue.common.apps import plugin, errors, i18n
from gnue.common.utils.FileUtils import openResource, dyn_import
from gnue.common.datasources import Exceptions, GLoginHandler

import warnings

# =============================================================================
# Exceptions
# =============================================================================

class NotFoundError (errors.AdminError):
	"""
	Connection name not found in connections.conf.
	"""
	def __init__ (self, name, file):
		msg = u_("The connections file does not contain a definition "
			"for \"%(connection)s\".\n\nFile: %(file)s") \
			% {'connection': name,
			'file'      : file}
		errors.AdminError.__init__ (self, msg)

# -----------------------------------------------------------------------------

class DependencyError (errors.AdminError):
	"""
	Cannot load database driver plugin due to a missing dependency.

	This exception is raised by the database drivers.
	"""
	def __init__ (self, modulename, url):
		self.modulename = modulename
		self.url = url
		message = u_("Module '%s' is not installed.") % self.modulename
		if self.url:
			message += u_("  You can download it from %s.") % self.url
		errors.AdminError.__init__ (self, message)

# -----------------------------------------------------------------------------

class InvalidFormatError (errors.AdminError):
	"""
	Cannot parse connections.conf file.
	"""
	pass


# =============================================================================
# Connection manager class
# =============================================================================

class GConnections:
	"""
	Class that loads connection definition files and maintains
	database connections.

	If you pass GConnections an "eventHandler" instance, it will generate a
	Connections:Connect(name, base) when a new connection is created.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, location, loginHandler = None, loginOptions = {},
		eventhandler = None):
		"""
		Create a new GConnections instance.

		@param location: Filename of the connections.conf file.
		@param loginHandler: Instance of a L{GLoginHandler.LoginHandler}
		  descendant to ask the user for login data.
		@param loginOptions: Default data for the login handler.
		@param eventhandler: Event handler to notify about new connections.
		"""

		# These 4 may not be private as they are used by appserver to clone the
		# connection manager.
		self._location     = location
		self._loginHandler = loginHandler
		self._loginOptions = loginOptions
		self._eventHandler = eventhandler

		# Alias connection names and their parameters
		self.__aliases = {}

		# All connection names and their parameters
		self.__definitions = {}

		# Dictionary of authenticated users per connection name.
		self.__authenticatedUsers = {}

		# Dictionary of open connections (GConnection objects) per connection name.
		self.__openConnections = {}

		# Parse the connections.conf file
		parser = RawConfigParser ()

		if len (self._location):
			fileHandle = openResource (self._location)

			try:
				parser.readfp (fileHandle)

			except DuplicateSectionError:
				tmsg =  u_("The connections file has duplicate source definitions."
					"\n\nFile: %s") % location
				raise InvalidFormatError, tmsg
			except MissingSectionHeaderError:
				tmsg = u_("The connections file has no source definitions."
					"\n\nFile: %s") % location
				raise InvalidFormatError, tmsg
			except Exception:
				tmsg =  u_("The connections file cannot be parsed."
					"\n\nFile: %s") % location
				raise InvalidFormatError, tmsg

		# Read all the sections into a dict
		# and make a note of all alias names
		for section in parser.sections ():
			self.__definitions[section] = {}
			for att in parser.options (section):
				if att == 'aliases':
					for alias in parser.get(section, att).lower().split():
						self.__aliases[alias] = section
				else:
					self.__definitions[section][att] = parser.get(section, att)

		self.__sessionKey = 0

	# ---------------------------------------------------------------------------
	# session key
	# ---------------------------------------------------------------------------

	# postgresql_fn connection needs session key to authentificate calls
	def setSessionKey(self, sessionKey):
		self.__sessionKey = sessionKey

	def _getSessionKey(self):
		return self.__sessionKey

	# ---------------------------------------------------------------------------
	# Set the login handler for opening connections
	# ---------------------------------------------------------------------------

	def setLoginHandler (self, loginHandler):
		"""
		Set the login handler to use to ask the user for login data.
		"""

		self._loginHandler = loginHandler


	# ---------------------------------------------------------------------------
	# Get a parameter for a connection
	# ---------------------------------------------------------------------------

	def __getConnectionParameter (self, connection_name, attribute, default = None):
		"""
		Read a parameter from the connections.conf file.
		"""

		try:
			definition = self.__definitions [connection_name]
			try:
				return definition [attribute]
			except:
				return default
		except KeyError:
			raise NotFoundError, (connection_name, self._location)


	# ---------------------------------------------------------------------------
	# Returns a list of connection names
	# ---------------------------------------------------------------------------

	def getConnectionNames (self, includeAliases = True):
		"""
		Return a list of all connections from the connections.conf file.

		@param includeAliases: Whether or not to include connection aliases.
		@return: List with all connection names.
		"""

		if includeAliases:
			return self.__definitions.keys() + self.__aliases.keys()
		else:
			return self.__definitions.keys()


	# ---------------------------------------------------------------------------
	# Returns a dictionary describing a connection
	# ---------------------------------------------------------------------------

	def getConnectionParameters (self, connection_name):
		"""
		Return the parameter dictionary for a given connection.

		@return: Dictionary with parameter name and parameter value.
		"""

		try:
			return copy.deepcopy (self.__definitions [connection_name])
		except KeyError:
			raise NotFoundError, (connection_name, self._location)


	# ---------------------------------------------------------------------------
	# Add a connection entry (session specific; i.e., doesn't add
	# to the connections.conf file, but to the current instance's
	# list of available connections.
	# ---------------------------------------------------------------------------

	def addConnectionSpecification (self, name, parameters):
		"""
		Add a session specific connection entry.

		With this function, a temporary connection definition can be inserted
		without having to change the connections.conf file.

		@param name: Connection name.
		@param parameters: Connection parameters as a dictionary.
		"""

		self.__definitions [name.lower ()] = copy.copy (parameters)


	# ---------------------------------------------------------------------------
	# get a connection instance and optionally log into it
	# ---------------------------------------------------------------------------

	def getConnection (self, connection_name, login = False):
		"""
		Return an instance of the requested connection and optionally log into it.

		If there's an already opened connection for the requested connectionname
		this instance will be returned.

		@param connection_name: name of the connection to be returned
		@param login: if TRUE, this function automatically tries to open the
		    connection.
		@return: connection instance
		@raise GConnection.NotFoundError: if connection_name does not exist
		"""

		connection_name = connection_name.lower ()

		# resolve alias if it is alias
		connection_name = self.__aliases.get(connection_name, connection_name)

		if self.__openConnections.has_key (connection_name):
			conn = self.__openConnections [connection_name]
		else:
			# Support for multiple open connections to the same database.
			# Specify as 'gnue:1', 'gnue:2', etc, to open two actual connections to
			# 'gnue', each with their own transactions, etc.
			connection_base = connection_name.split (':') [0]

			# This will throw a GConnections.NotFoundError if an unknown connection
			# name is specified. The calling method should catch this exception and
			# handle it properly (exit w/message)
			parameters = self.getConnectionParameters (connection_base)

			driver   = parameters ['provider'].lower ().replace ('/', '.')
			dbdriver = plugin.find (driver, 'gnue.common.datasources.drivers',
				'Connection')
			conn = dbdriver.Connection (self, connection_name, parameters)

			self.__openConnections [connection_name] = conn

		if login:
			self.loginToConnection (conn)

		return conn


	# ---------------------------------------------------------------------------
	# Has a connection been initialized/established?
	# ---------------------------------------------------------------------------

	def isConnectionActive (self, connection):
		"""
		Return True if there is an open connection for the given connection name.

		@param connection: Connection name.
		@return: True if this connection is open, False otherwise.
		"""

		return self.__openConnections.has_key (connection.lower ())


	# ---------------------------------------------------------------------------
	# login to a connection
	# ---------------------------------------------------------------------------

	def loginToConnection (self, connection):
		"""
		Log into a connection.

		This is called automatically at the end of L{getConnection} if the login
		parameter is set to True.

		@param connection: Connection name.
		"""

		connection_name = connection.name
		connection_base = connection_name.split (':') [0]

		if not self._loginHandler:
			self.setLoginHandler (GLoginHandler.BasicLoginHandler ())

		try:
			connected = connection.__connected

		except AttributeError:
			connected = 0

		if not connected:
			loginData = connection.parameters
			loginData ['_language'] = i18n.getuserlocale ()

			try:
				# load the user's netrc file:
				# a sample .netrc could look like:
				# <.netrc begin>
				# machine 'gnue://my_connection/'
				# login 'mylogin'
				# password 'mypassword'
				# EOF
				# (Remark: if .netrc should work under Win32 you have to
				#  set the HOME environement variable [SET HOME=...])

				netrcData = netrc.netrc ().authenticators ("'gnue://%s/'" \
						% connection_base)
				if netrcData is not None:
					assert gDebug (7, 'Read the user\'s .netrc file')
					loginData ['_username'] = netrcData [0][1:-1]
					loginData ['_password'] = netrcData [2][1:-1]

					assert gDebug (7, "Found useful stuff for connection %s in "
						"the user\'s .netrc file" % connection_name)

			except (IOError, netrc.NetrcParseError, KeyError):
				pass

			if (loginData.has_key ('username')):
				loginData ['_username'] = loginData ['username']
				del loginData ['username']

			if (loginData.has_key ('password')):
				loginData ['_password'] = loginData ['password']
				del loginData ['password']

			# Override with data provided on command line so this has highest
			# priority.
			loginData.update (self._loginOptions)

			# Load authenticator if needed
			if loginData.has_key ('custom_auth'):
				authenticator = dyn_import (loginData ['custom_auth']).Authenticator ()
				checkFields   = authenticator.getLoginFields ( \
						connection.getLoginFields ())
			else:
				checkFields   = connection.getLoginFields ()
				authenticator = None

			haveAllInformation  = True
			needFieldConversion = False

			for item in checkFields:
				if len (item) == 3:
					needFieldConversion = True
					fieldname = item [0]
				elif len (item) == 6:
					fieldname = item [1]
				else:
					raise InvalidLoginFieldsError, checkFields

				if not (fieldname in loginData and loginData [fieldname] is not None):
					haveAllInformation = False
					break

			if haveAllInformation:
				if authenticator:
					connection.connect (authenticator.login (loginData))
				else:
					connection.connect (loginData)

			else:
				if needFieldConversion:
					fields = []
					for (name, label, password) in checkFields:
						fields.append ((label, name, password and 'password' or 'string',
								None, None, []))

					checkFields = fields
					needFieldConversion = False

				descr = self.__getConnectionParameter (connection_base, 'comment', '')
				text  = u_('Login required for %(newline)s"%(description)s"') \
					% {'newline': len (descr) and '\n' or '',
					'description': descr or connection_base}

				title  = u_("GNU Enterprise: Login to %s") % connection_base
				header = [(text, None, 'label', None, None, []),
					('', None, 'label', None, None, [])]

				attempts = 4

				assert gDebug (7, 'Getting new data connection to %s' % connection_name)

				errortext = None

				while attempts:
					try:
						fields = header + checkFields

						# Ask the UI to prompt for our login data
						result = self._loginHandler.askLogin (title, fields, loginData,
							errortext)
						loginData.update (result)

						# Ask the data object to connect to the database
						if authenticator:
							connection.connect (authenticator.login (loginData))
						else:
							connection.connect (loginData)

						# We're done!
						attempts = 0

					except Exceptions.LoginError:
						attempts  -= 1
						errortext  = errors.getException () [2]

						if not attempts:
							# Four times is plenty...
							raise Exceptions.LoginError, \
								u_("Unable to log in after 4 attempts.\n\nError: %s") \
								% errortext

			# Add to authenticated user list
			try:
				self.__authenticatedUsers [connection] = loginData ['_username']

			except KeyError:
				self.__authenticatedUsers [connection] = None

			# Ok, since everything worked fine, add the connection to the dictionary
			# of open connections
			self.__openConnections [connection_name] = connection

			if self._eventHandler:
				self._eventHandler.dispatchEvent ('Connections:Connect',
					name = connection_name, base = connection_base)

		# Done
		connection.__connected = True


	# ---------------------------------------------------------------------------
	# Get the user name that has logged into a connection
	# ---------------------------------------------------------------------------

	def getAuthenticatedUser (self, connection = None):
		"""
		Return the user name that has been used to log into the give connection.
		"""

		try:
			if connection is None:
				return self.__authenticatedUsers [self.__authenticatedUsers.keys () [0]]
			else:
				return self.__authenticatedUsers [connection]
		except (KeyError, IndexError):
			return None


	# ---------------------------------------------------------------------------
	# Close all connections
	# ---------------------------------------------------------------------------

	def closeAll(self):
		"""
		This function closes all open connections.
		"""

		for connection in self.__openConnections.values ():
			connection.close ()


	# ---------------------------------------------------------------------------
	# After a connection has been closed, remove all references to it
	# ---------------------------------------------------------------------------

	def _connectionClosed (self, connection):

		if connection in self.__authenticatedUsers:
			del self.__authenticatedUsers [connection]

		for (key, value) in self.__openConnections.items ():
			if value == connection:
				del self.__openConnections [key]

		connection.__connected = False
