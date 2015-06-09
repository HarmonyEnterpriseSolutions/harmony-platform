# GNU Enterprise Common Library - Base Login Handler
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
# $Id: GLoginHandler.py 9222 2007-01-08 13:02:49Z johannes $
"""
Classes for login handlers.
"""

__all__ = ['UserCanceledLogin', 'LoginHandler', 'BasicLoginHandler']

import getpass

from gnue.common.apps import errors


# =============================================================================
# Exceptions
# =============================================================================

class UserCanceledLogin (errors.UserError):
	"""
	User cancelled login request (by pressing <Esc>, hitting the <Abort> button
	etc.).
	"""
	def __init__ (self):
		msg = u_("User canceled the login request.")
		errors.UserError.__init__ (self, msg)


# =============================================================================
# Base class for all login handler
# =============================================================================

class LoginHandler:
	"""
	Abstract base class for all login handlers.

	A login handler is an object that asks the user for login data. Different
	user interfaces (e.g. gtk2, curses, qt3...) implement different login
	handlers.
	"""

	# ---------------------------------------------------------------------------
	# Get login information (depreciated)
	# ---------------------------------------------------------------------------

	def getLogin (self, requiredFields, errortext = None):
		"""
		DEPRECIATED: get information for the given fields and return a dictionary

		@param requiredFields: sequence of [connection name, description, sequence
		    of fields (name, label, is password)]
		@param errortext: message of the last error occured

		@raises UserCanceledLogin: if the user canceled the login request
		"""
		pass


	# ---------------------------------------------------------------------------
	# Called when the app no longer needs the login handler
	# ---------------------------------------------------------------------------

	def destroyLoginDialog (self):
		"""
		DEPRECIATED
		"""
		pass


	# ---------------------------------------------------------------------------
	# Ask for all fields given by the field definitions
	# ---------------------------------------------------------------------------

	def askLogin (self, title, fielddefs, defaultData, lastError = None):
		"""
		Ask for login information as specified by the given field definitions using
		the given default data.

		@param title: title for the login dialog
		@param fielddefs: sequence of field definitions for InputDialogs
		@param defaultData: dictionary with default values
		@param lastError: last error message or None

		@raises UserCanceledLogin: if the user canceled the login request

		@return: dictionary of all keys/values the user has entered.
		"""

		fields = []
		for (label, name, ftype, default, master, elements) in fielddefs:
			default = defaultData.get (name, default)
			if not ftype in ['label', 'warning', 'image']:
				label = "%s:" % label

			fields.append ((label, name, ftype, default, master, elements))

		if lastError:
			errorField = (lastError, None, 'warning', None, None, [])
			added = False
			for (ix, field) in enumerate (fields):
				if not field [2] in ['label', 'warning', 'image']:
					fields.insert (ix, errorField)
					added = True
					break

			if not added:
				fields.append (errorField)

		result = self._askLogin_ (title, fields)
		if result is None:
			raise UserCanceledLogin

		return result


	# ---------------------------------------------------------------------------
	# Do the dirty work for askLogin
	# ---------------------------------------------------------------------------

	def _askLogin_ (self, title, fields):
		"""
		Descendants override this method to do all the dirty work for askLogin ().

		This class converts the given field definition sequence into an old style
		format as required by getLogin () and finally calls getLogin. This process
		will fade out as soon as getLogin is obsolete.
		"""

		# flatten the blown-up sequence till all support the new style definitions
		data   = []
		labels = []
		error  = None

		for (label, name, ftype, default, master, elements) in fields:
			if ftype in ['image']:
				continue

			elif ftype == 'label':
				labels.append (label)

			elif ftype == 'warning':
				error = label

			else:
				data.append ((name, label, ftype == 'password'))

		try:
			name = len (labels) and labels [0] or ''
			desc = len (labels) > 1 and labels [1] or ''
			result = self.getLogin ([name, desc, data], error)
		finally:
			self.destroyLoginDialog ()

		return result


# =============================================================================
# Class implementing a basic login handler using raw_input and getpass
# =============================================================================

class BasicLoginHandler (LoginHandler):
	"""
	Class implementing a basic login handler using raw_input () and getpass ()
	as input methods.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, useDefaults = False, silent = False):
		"""
		@param useDefaults: if True, does not ask for a field if it has a default
		  other than None, but uses that default directly
		@param silent: if True, no output occurs and it implicitly sets useDefaults
		  to True.
		"""

		self.__silent      = silent
		self.__useDefaults = silent and True or useDefaults


	# ---------------------------------------------------------------------------
	# Ask for all fields requestd
	# ---------------------------------------------------------------------------

	def _askLogin_ (self, title, fields):

		result = {}

		if not self.__silent:
			print "*" * 60
			print o(title)
			print

		try:
			for (label, name, ftype, default, master, elements) in fields:
				if ftype in ['label', 'warning']:
					if not self.__silent:
						print "  %s" % o(label)

				elif ftype in ['string', 'password']:
					if self.__useDefaults and default is not None:
						result [name] = default
					else:
						if ftype == 'password':
							value = getpass.getpass ("  %s " % o(label))
						else:
							# raw_input print's it's argument to stderr, so we have to print
							# the label manually here since stderr might be redirected
							print "  %s" % o(label),
							value = raw_input ()

						result [name] = [value, default][value is None]

				elif ftype in ['dropdown']:
					# TODO: sort all fields according to master-detail dependencies and
					# then validate the input values using the 'allowedValues' dicts
					if self.__useDefaults and default is not None:
						result [name] = default
					else:
						print "  %s" % o(label),
						result [name] = raw_input ()

		except KeyboardInterrupt:
			raise UserCanceledLogin

		return result


# =============================================================================
# Class implementing a 'silent' login handler
# =============================================================================

class SilentLoginHandler (LoginHandler):
	"""
	Implementation of a login handler that gets all data preset via parameter and
	doesn't communicate with the user at all.
	"""

	# ---------------------------------------------------------------------------
	# Create a new instance
	# ---------------------------------------------------------------------------

	def __init__ (self, **keywords):
		"""
		Provides all given keywords as login data.
		@param keywords: all keys and values given by this dictionary are available
		  as 'login data' and will be returned if requested by askLogin ()
		"""

		self.__loginData = keywords


	# ---------------------------------------------------------------------------
	# Ask for the given fields
	# ---------------------------------------------------------------------------

	def _askLogin_ (self, title, fields):

		result = {}
		for (label, name, ftype, default, master, elements) in fields:
			if not ftype in ['label', 'warning', 'image']:
				value = self.__loginData.get (name, default)
				if value is None:
					value = default

				result [name] = value

		return result
