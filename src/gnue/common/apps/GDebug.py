# GNU Enterprise Common Library - Application Services - Debugging support
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
# $Id: GDebug.py,v 1.11 2013/02/27 13:22:17 oleg Exp $

"""
Support for debugging messages with independent debug levels and redirection of
messages to a file.
"""

import sys, os
if '--debug-imports' in sys.argv or os.environ.has_key('GNUE_DEBUG_IMPORT'):
	from gnue.common.apps import GImportLogger

import __builtin__
import inspect
import os
import string
import sys
import time
import traceback
import types


# -----------------------------------------------------------------------------
# Internal global variables
# -----------------------------------------------------------------------------

_fh = sys.stderr                        # Filehandle to write debug msgs to
_DEBUG_LEVELS = []                      # Debug levels requested
_DEBUGGER = None                        # Interactive debugger


# =============================================================================
# Support for redirecting error messages to a file
# =============================================================================

# -----------------------------------------------------------------------------
# Class to catch the stderr stream
# -----------------------------------------------------------------------------

class __stderrcatcher:
	"""
	Output stream for error message.

	sys.stderr is redirected to this class. It prepends "DB000: " in front of
	each line and writes everything to the debug file or stderr.
	"""

	def __init__ (self, filehandle):
		self.filehandle = filehandle

	def write (self, str):
		lines = string.split (str, "\n")
		while len(lines) and lines [-1] == "":             # remove empty lines at the end
			del (lines [-1])
		self.filehandle.write (string.join (["DB000: " + s for s in lines], "\n"))
		self.filehandle.write ("\n")
		try:
			self.filehandle.flush ()
		except:
			pass

	def writelines (self, list):
		for line in list:
			self.write (str)

	def flush(self):
		try:
			self.filehandle.flush ()
		except:
			pass

# -----------------------------------------------------------------------------
# redirect stderr and all debugging output to the given filehandle
# -----------------------------------------------------------------------------

def __catchStderr (filehandle):

	global _fh
	_fh = filehandle
	sys.stderr = __stderrcatcher (filehandle)


# =============================================================================
# Support for debugging messages
# =============================================================================

# -----------------------------------------------------------------------------
# Placeholders for gDebug/gEnter/gLeave if no debug output is desired at all
# -----------------------------------------------------------------------------

def __noDebug (level, message, dropToDebugger = False):
	return True


def __noEnter (level = 1):
	return True

def __noLeave (level = 1, *result):
	return True

# Initialize builtin dictionary with placeholders until setDebug is called
__builtin__.__dict__ ['gDebug'] = __noDebug
__builtin__.__dict__ ['gEnter'] = __noEnter
__builtin__.__dict__ ['gLeave'] = __noLeave


# -----------------------------------------------------------------------------
# Set the debugger
# -----------------------------------------------------------------------------

def setDebugger (debugger):
	"""
	This function informs the debug system about the use of Python's interactive
	debugger. If this is called, subsequent calls to gDebug with the parameter
	dropToDebugger set will switch the interactive debugger to trace mode.
	"""

	global _DEBUGGER
	_DEBUGGER = debugger


# -----------------------------------------------------------------------------
# Dump a message to the debug-output
# -----------------------------------------------------------------------------

def __dumpMessage (level, filename, message, dropToDebugger = False):
	"""
	Write a message to the debug-output.

	@param level: the debug-level the message will be logged in
	@param filename: the filename the message originated from
	@param message: the message to be logged
	@param dropToDebugger: if set to True, Python's interactive debugger will be
	  switched to trace mode. This requires that setDebugger has been called
	  before.
	"""
	encoding = getattr(sys.stdout, 'encoding', None) or 'UTF8'

	global _fh, _DEBUGGER

	s = time.time ()
	msecs = (s - long (s)) * 1000
	t = time.strftime ('%Y-%m-%d %H:%M:%S', time.localtime (s))
	stamp = "%s.%03d" % (t, msecs)
	
	print ("%s [%s]: %s" % (stamp, level, message)).encode(encoding, 'replace')
	return

	lines = "%s" % message
	for line in lines.splitlines ():
		try:
			ilevel = int(level)
			_fh.write ("DB%03d: %s %s%s%s" % (ilevel, stamp, filename, line, os.linesep))
		except:
			_fh.write ("DB%s: %s %s%s%s" % (level, stamp, filename, line, os.linesep))
		_fh.flush ()

	if dropToDebugger and _DEBUGGER:
		_DEBUGGER.set_trace ()


# -----------------------------------------------------------------------------
# Write debug message
# -----------------------------------------------------------------------------

def gDebug (level, message, dropToDebugger = False):
	"""
	Write a message to the debug-output. This function is available in the
	global namespace.

	@param level: the debug-level the message will be logged in
	@param message: the message to be logged
	@param dropToDebugger: if set to True, Python's interactive debugger will be
	  switched to trace mode. This requires that setDebugger has been called
	  before.
	@return: Always true so it can be filtered out via assert
	"""

	if level in _DEBUG_LEVELS :

		# Just to be sure...
		#if isinstance (message, types.UnicodeType):
		#	message = message.encode ('utf-8')

		# Find out the file from where we were called
		caller = traceback.extract_stack()[-2]
		try:
			if caller[0][-3:] == '.py':
				file = "[%s:%s] " % (string.split(caller[0][:-3],'/')[-1], caller[1])
			else:
				file = "[%s:%s] " % (string.split(caller[0],'/')[-1], caller[1])
		except:
			file = ""

		__dumpMessage (level, file, message, dropToDebugger)

	return True

# -----------------------------------------------------------------------------
# Add a function-signature to the debug output
# -----------------------------------------------------------------------------

def gEnter (level = 1):
	"""
	Write information about the current function and its parameters to
	debug-output. This function is available in the global namespace.

	assert gEnter is intended to be called at the begin of a function.

	@param level: the debug-level the message will be logged in
	@return: Always true so it can be filtered out via assert
	"""

	if not level in _DEBUG_LEVELS:
		return True

	# Get the caller's frame
	frame = sys._getframe (1)

	try:
		(args, vargs, vkw, flocals) = inspect.getargvalues (frame)

		# If the function has a 'self' argument we add the class referenced by self
		# to the name of the function
		funcName = frame.f_code.co_name
		if 'self' in args:
			funcName = "%s.%s" % (flocals ['self'].__class__, funcName)

		params = []

		# First add all 'normal' arguments
		params = [repr (flocals [item]) for item in args]

		# Next, add all variable arguments (*arg)
		if vargs:
			params.extend ([repr (i) for i in flocals [vargs]])

		# and finally add all keyword arguments (**kwarg)
		if vkw is not None:
			params.extend (["%s = %s" % (repr (k), repr (v)) \
						for (k, v) in flocals [vkw].items ()])

		message  = "Entering function %s (%s)" % (funcName,
			string.join (params, ", "))

		path = frame.f_code.co_filename
		if path [-3:] == '.py':
			path = string.split (path [:-3], '/') [-1]
		else:
			path = string.split (path, '/') [-1]

		filename = "[%s:%s] " % (path, frame.f_code.co_firstlineno)

		__dumpMessage (level, filename, message)

	finally:
		# Make sure to release the reference to the frame object. This keeps
		# garbage collection doing a fine job :)
		del frame

	return True


# -----------------------------------------------------------------------------
# Add a line to debug-output describing the end of a function call
# -----------------------------------------------------------------------------

def gLeave (level = 1, *result):
	"""
	Write information about the current function and its return value to
	debug-output. This function is available in the global namespace.

	gLeave is intended to be called at the end of a function.

	@param level: debug-level to send the message to
	@param result: the function's result (if any)
	@return: True
	"""

	if not level in _DEBUG_LEVELS:
		return True

	# Get the caller's frame
	frame = sys._getframe (1)

	try:
		(args, vargs, vkw, flocals) = inspect.getargvalues (frame)

		# If the function has a 'self' argument we add the class referenced by self
		# to the name of the function
		fName = frame.f_code.co_name
		hId   = ''
		if 'self' in args:
			fName = "%s.%s" % (flocals ['self'].__class__, fName)
			hId   = repr (hex (id (flocals ['self'])))

		resStr  = len (result) and ' == %s' % repr (result [0]) or ''
		message = "Leaving function %s (%s)%s" % (fName, hId, resStr)

		path = frame.f_code.co_filename
		if path [-3:] == '.py':
			path = string.split (path [:-3], '/') [-1]
		else:
			path = string.split (path, '/') [-1]

		filename = "[%s:%s] " % (path, frame.f_code.co_firstlineno)

		__dumpMessage (level, filename, message)

	finally:
		# Make sure to release the reference to the frame object. This keeps
		# garbage collection doing a fine job :)
		del frame
		return True


# -----------------------------------------------------------------------------
# Set debug levels to use and initialize debugging
# -----------------------------------------------------------------------------

def setDebug (level, file = None):
	"""
	Initialize and configure the debug message system

	@param level: A string with the debug levels to output, e.g. "0-3,5,7"
	@param file: Filename to output debug messages to (instead of stderr)
	"""

	global _DEBUG_LEVELS

	# Find out debug levels
	levels = []
	for entry in level.split(','):
		values=entry.split('-')
		if len(values) > 1:
			levels+=range(int(values[0]),int(values[1])+1)
		else:
			levels+=[entry]

	_DEBUG_LEVELS=levels

	# If debug levels are given, we must replace the empty placeholder functions
	# with a function that actually does something
	if _DEBUG_LEVELS != []:
		__builtin__.__dict__ ['gDebug'] = gDebug
		__builtin__.__dict__ ['gEnter'] = gEnter
		__builtin__.__dict__ ['gLeave'] = gLeave

	# Redirect debugging and error output to a file if requested
	if (file):
		__catchStderr (open (file, 'a'))
	else:
		__catchStderr (sys.stderr)


# -----------------------------------------------------------------------------
# Deprecated, for compatibility
# -----------------------------------------------------------------------------

def printMesg (level, message, dropToDebugger = False):
	"""
	This function is deprecated - use gDebug instead
	"""
	__builtin__.__dict__ ['gDebug'] (level, message, dropToDebugger)


# -----------------------------------------------------------------------------
# FIXME: is it save to remove the following stuff?
# -----------------------------------------------------------------------------

class GETrace(Exception):
	#
	#Exception class representing a debug message
	#not yet used for anything and probably won't be :)
	#
	def __init__(self, level=0, message="Trace Message"):
		Exception.__init__(self)
		self.level = level
		self.message = message

def handleException(exc_info):
	#
	# Not used at present
	#
	type, exception, traceback = exc_info
	if (isinstance(exception, GETrace) ):
		printMesg( exception.level, exception.message)
	elif (not isinstance(exception, SystemExit)):
		strings = traceback.format_exception(type, exception, traceback)
		text = string.join(strings, '')
		printMesg(0, text)
