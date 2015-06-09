# GNU Enterprise Common Library - Base exception classes
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
# $Id: errors.py,v 1.8 2014/01/16 17:05:57 Oleg Exp $

"""
General exception classes.
"""

import sys
import traceback
import types
import string
import exceptions

from gnue.common.apps import i18n

# =============================================================================
# New basic exception class. Python's standard exception class cannot handle
# unicode messages.
# =============================================================================

class gException (Exception):
	"""
	The same as the builtin python Exception, but can handle messages that are
	unicode strings.  This exception is available as the builtin class
	"gException".  All other user-defined exceptions should be derived from this
	class.

	@ivar message: The error message.
	@type message: Unicode
	@ivar group: The group or category of the exception. Can be one of 'system',
	  'admin', 'application', or 'user'.
	@ivar name: The name of the exception. If set, this will be returned by
	  L{getName} and L{getException} instead of the class name of the exception.
	@ivar detail: The detail information to the exception. If set, this will be
	  returned by L{getDetail} and L{getException} instead of the traceback.
	"""
	def __init__ (self, message, group = 'system'):
		self.message = message
		self.group   = group
		self.name    = None
		self.detail  = None
		exceptions.Exception.__init__ (self, message)

	# ---------------------------------------------------------------------------
	# Get the type of the exception
	# ---------------------------------------------------------------------------

	def getGroup (self):
		"""
		Return the group of the exception.

		@return: Group of the exception, one of 'system', 'admin', 'application',
		  or 'user'.
		"""
		return self.group


	# ---------------------------------------------------------------------------
	# Return the name of the exception
	# ---------------------------------------------------------------------------

	def getName (self):
		"""
		Return the exception's name, which is the classname of the exception class
		unless overwritten with L{name}.

		@return: Name of the exception.
		@rtype: Unicode
		"""
		return self._fmtUnicode(self.name or self.__class__.__name__)


	# ---------------------------------------------------------------------------
	# Get the detail of an exception
	# ---------------------------------------------------------------------------

	def getDetail (self, count = None, type = None, value = None, trace = None):
		"""
		Return the exception's detail, which is the traceback unless overwritten
		with L{detail}.

		Optionally, a number of lines can be skipped at the beginning of the
		traceback (if the detail I{is} the traceback).

		@param count: Number of lines to skip at the beginning of the traceback.
		@return: Detail information for the exception.
		@rtype: Unicode
		"""
		if self.detail is not None:
			return self._fmtUnicode (self.detail, i18n.getencoding ())

		if sys.exc_info () == (None, None, None):
			tStack = traceback.format_exception (type, value, trace)
		else:
			tStack = traceback.format_exception (*sys.exc_info ())
		if count is not None:
			del tStack [1:count + 1]
		return self._fmtUnicode ("%s" % string.join (tStack), i18n.getencoding ())


	# ---------------------------------------------------------------------------
	# Get the message of an exception
	# ---------------------------------------------------------------------------

	def getMessage (self):
		"""
		Return the message of an exception.
		@return: Message of the exception.
		@rtype: Unicode
		"""
		return self._fmtUnicode (self.message)


	# ---------------------------------------------------------------------------
	# Make sure a given text is a unicode string
	# ---------------------------------------------------------------------------

	def _fmtUnicode (self, text, encoding = None):
		"""
		Return a given text as unicode string using an optional encoding or the
		system's default encoding.

		@param text: String to be encoded. If this string is already unicode no
		  modification will take place.
		@param encoding: Encoding to use (if None, system default encoding will
		  take place)
		@return: Unicode representation of the text parameter.
		"""
		if isinstance (text, types.UnicodeType):
			return text
		else:
			if encoding is not None:
				return unicode (text, encoding, 'replace')
			else:
				return unicode (text, errors = 'replace')

	def __str__(self):
		return "%s error: %s\n%s" % (self.group, self.message, self.detail)

# =============================================================================
# System Error
# =============================================================================

class SystemError (gException):
	"""
	This exception class should be used for exceptions indicating a bug in GNUe.
	Whenever such an exception is raised, one have found such a bug :)
	"""
	def __init__ (self, message):
		gException.__init__ (self, message, 'system')


# =============================================================================
# Administrative Errors
# =============================================================================

class AdminError (gException):
	"""
	This exception class should be used for exceptions indicating a
	misconfiguration in a widest sense. This could be a missing module for a
	dbdriver as well as an 'out of disk space' error.
	"""
	def __init__ (self, message):
		gException.__init__ (self, message, 'admin')


# =============================================================================
# Application Errors
# =============================================================================

class ApplicationError (gException):
	"""
	This class should be used for errors caused by applications like a corrupt
	trigger code, or a misformed xml-file and so on.
	"""
	def __init__ (self, message):
		gException.__init__ (self, message, 'application')


# =============================================================================
# User Errors
# =============================================================================

class UserError (gException):
	"""
	This class should be used for exceptions where a user did something wrong, or
	a situation has occured which isn't dramatic, but the user has to be informed
	of. Example: wrong password or the user has entered non-numeric data into a
	numeric field, and so on.
	"""
	def __init__ (self, message):
		gException.__init__ (self, message, 'user')


# =============================================================================
# Exceptions raised on a remote site/process
# =============================================================================

class RemoteError (gException):
	"""
	This class is used for transporting an exception raised at a remote point.
	Once it has been created it never changes it's contents. A remote error
	usually contains System-, Admin- or User-Errors.
	"""
	def __init__ (self, group, name, message, detail):
		gException.__init__ (self, message)
		self.group  = group
		self.name   = name
		self.detail = detail


# -----------------------------------------------------------------------------
# Get a tuple (type, name, message, detail) for the last exception raised
# -----------------------------------------------------------------------------

def getException (count = None, aType = None, aValue = None, aTrace = None):
	"""
	Return textual information about an exception.

	This function creates a tuple (group, name, message, detail) for the last
	exception raised. The optional parameter determines the number of lines
	skipped from the detail traceback.

	The intended use of this function is to get the text to be displayed in error
	messages.

	@param count: number of lines to skip in the traceback
	@return: tuple with group, name, message and detail of the last exception.
	"""
	(sType, sValue, sTrace) = sys.exc_info ()
	aType  = aType  or sType
	aValue = aValue or sValue
	aTrace = aTrace or sTrace

	if isinstance (aValue, gException):
		return (aValue.getGroup (), aValue.getName (), aValue.getMessage (),
			aValue.getDetail (count, aType, aValue, aTrace))
	else:
		# Exception was not a descendant of gException, so we construct the tuple
		# from the exception information
		lines = traceback.format_exception (aType, aValue, aTrace)
		if count is not None:
			del lines [1:count + 1]

		name = getattr(aType, '__name__', None) or ("%s" % aType)
		name = unicode (name, i18n.getencoding (), 'replace')
		name = name.split ('.') [-1]
		message = "%s" % aValue
		if isinstance (message, types.StringType):
			message = unicode (message, i18n.getencoding (), 'replace')
		detail  = string.join (lines)
		if isinstance (detail, types.StringType):
			detail = unicode (detail, i18n.getencoding (), 'replace')

		# add html to detail in exceptions with stream
		if hasattr(aValue, 'read'):
			try:
				detail = '\n'.join((detail, aValue.read().decode('UTF-8', 'replace')))
			except:
				pass
		
		return ('system', name, message, detail)
