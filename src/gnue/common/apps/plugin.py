# GNU Enterprise Common Library - Plugin support
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
# Copyright 2001-2007 Free Software Foundation
#
# $Id: plugin.py 9222 2007-01-08 13:02:49Z johannes $

"""
Functions to list and load avaliable plugins dynamically.

Plugins are Python modules that implement a defined API and are loaded on
demand.  Usually, there are several plugins of the same type (that means they
implement the same API) that can be used interchangeable.  The user can select
which plugin he wants to use.

All plugins of a specific type must be Python modules in a defined package.
For example, all database drivers must be modules in the
gnue.common.datasources.drivers package.

Any plugin must define a specific symbol (usually a class definition like
LanguageAdapter, ClientAdapter or Connection) to qualify itself as valid.

Any plugin must immediately check whether it is functional (especially whether
all dependencies are installed), and import must fail with a meaningful
exception otherwise.  Optionally, a module can also define a function with the
name __initplugin__ that initializes the module and raises an exception if the
plugin cannot be initialized.

Plugins can be organized in a tree structure.  To load a plugin, any point in
the tree may be specified.  For example, consider there are three plugins named
base.group.foo, base.group.bar and base.group.baz.  "foo" will specify the foo
plugin, as well as "group.foo".  Loading the plugin "group" means to load the
first available functional plugin in the group.

Modules and packages located within the plugin tree but not being valid plugins
can define a symbol with the name __noplugin__ to indicate that they are no
valid plugin.  Note that the module defining the __noplugin__ symbol is still
imported, but no submodules of it. This is useful to exclude, for example,
abstract base drivers.
"""

from types import *

import os
import string
import sys
import traceback

from gnue.common.apps import errors, i18n


# =============================================================================
# Exceptions
# =============================================================================

# -----------------------------------------------------------------------------
# Module loading error
# -----------------------------------------------------------------------------

class LoadError (errors.AdminError):
	"""
	Indicates a failure to load a given module.  Raised by L{find}.

	If e is an Exception of this class, e.exceptions gives a dictionary with
	the keys being the modules that were trying to be imported and the values
	being the exception info tuples for the exception that happened trying, and
	e.detail is a string containing basically the same info.
	"""
	def __init__ (self, name, exceptions):

		self.name = name
		self.exceptions = exceptions

		if self.exceptions:
			message = u_("Cannot load plugin '%s'") % self.name
			detail = u_("The following plugins failed:\n")
			for (name, exc) in self.exceptions.items ():
				list = traceback.format_exception_only (exc [0], exc [1])
				del list [1:2]
				msg = unicode (string.join (list, ''), i18n.getencoding ())
				detail += "* %s: %s" % (name, msg)
		else:
			message = u_("Cannot find plugin '%s'") % self.name
			detail = None

		errors.AdminError.__init__ (self, message)

		if detail:
			self.detail = detail


# -----------------------------------------------------------------------------
# List all available plugins
# -----------------------------------------------------------------------------

def list (base, identifier, try_to_init = True):
	"""
	List all available plugins.

	@param base: Name of the package that contains the plugins.
	@param identifier: Identifier that a plugin must define to qualify as module.
	@param try_to_init: If set to False, __initplugin__ is not called.
	@return: A dictionary with the available plugin module names as keys and
	    either the loaded module or the exception info tuple of the exception
	    raised when trying to import the module as values.
	"""
	checktype (base, [StringType, UnicodeType])
	checktype (identifier, [StringType, UnicodeType])

	# Make sure everything is a string. Non-ASCII characters are not allowed in
	# Python module names anyway.
	_base = base.encode ()
	_identifier = identifier.encode ()

	# Now recursively list the plugins
	return __list (_base, _identifier, try_to_init, True)


# -----------------------------------------------------------------------------
# Find a plugin
# -----------------------------------------------------------------------------

def find (name, base, identifier):
	"""
	Find a plugin by name. If no plugin is functional, a LoadError is raised.

	@param name: Name of the plugin to find.  If the plugin is foo.bar, name can
	    be bar, or foo.bar, or foo, where the last one returns the first
	    functional plugin in the foo group.
	@param base: Name of the package that contains the plugins.
	@param identifier: Identifier that a plugin must define to qualify as module.
	@return: The loaded module of the plugin.
	"""
	checktype (name, [StringType, UnicodeType])
	checktype (base, [StringType, UnicodeType])
	checktype (identifier, [StringType, UnicodeType])

	# Make sure everything is a string. Non-ASCII characters are not allowed in
	# Python module names anyway.
	_name = name.encode ()
	_base = base.encode ()
	_identifier = identifier.encode ()

	# First, see if we've already found this module previously
	global __findCache
	try:
		result = __findCache[(_base, _name)]
	except KeyError:
		# If not, search for the plugin
		result = __findCache[(_base, _name)] = __find (_base, _name, _identifier)

	if isinstance (result, ModuleType):
		return result
	else:
		raise LoadError, (name, result)


# -----------------------------------------------------------------------------
# A list of all previously failed modules
# -----------------------------------------------------------------------------

# This dictionary remembers all previous failure of module imports/inits. That
# is necessary because module initialization code is only run at first import
# attempt.
__failed = {}


# -----------------------------------------------------------------------------
# Mapping of previously found plugins
# -----------------------------------------------------------------------------

__findCache = {}


# -----------------------------------------------------------------------------
# Find all modules and subpackages in a package
# -----------------------------------------------------------------------------

def __modules (package, want_packages):

	# package.__file__ is a directory if GImportLogger is in use. This makes it
	# necessary to 'simulate' a package, otherwise stepping down subpackages
	# won't work.
	if os.path.isdir (package.__file__):
		(basedir, basefile) = (package.__file__, '__init__.py')
	else:
		(basedir, basefile) = os.path.split (package.__file__)

	(basename, baseext) = os.path.splitext (basefile)

	if basename != '__init__':
		# This is not a package, so no need to go deeper
		return []

	# Find all submodules
	result = {}
	for subfile in os.listdir (basedir):
		(subname, subext) = os.path.splitext (subfile)
		subpath = os.path.join (basedir, subfile)
		# We are only interested in Python modules or packages
		if (not want_packages and subext in ['.py', '.pyc', '.pyo'] and \
				subname != '__init__') or \
			(os.path.isdir (subpath) and \
				os.path.isfile (os.path.join (subpath, '__init__.py')) or \
				os.path.isfile (os.path.join (subpath, '__init__.pyc')) or \
				os.path.isfile (os.path.join (subpath, '__init__.pyo'))):
			result [subname] = True

	return result.keys ()


# -----------------------------------------------------------------------------
# Recursively list all plugins
# -----------------------------------------------------------------------------

def __list (base, identifier, try_to_init, top):

	global __failed

	if __failed.has_key (base):
		# This has already failed in previous attempt
		return {base: __failed [base]}

	try:
		m = __import__ (base, None, None, '*')
	except:
		__failed [base] = sys.exc_info ()
		return {base: __failed [base]}

	if hasattr (m, '__noplugin__'):
		# This is not a plugin, ignore it
		return {}

	if not top:
		if hasattr (m, identifier):
			# This is already a plugin, no need to go deeper
			if try_to_init and hasattr (m, '__initplugin__'):
				try:
					m.__initplugin__ ()
				except:
					__failed [base] = sys.exc_info ()
					return {base: __failed [base]}
			return {base: m}

	# List all submodules
	result = {}
	for sub in __modules (m, False):
		result.update (__list (base + '.' + sub, identifier, try_to_init, False))
	return result


# -----------------------------------------------------------------------------
# Recursively find first available plugin and return the module or a dictionary
# with the exceptions that occured
# -----------------------------------------------------------------------------

def __first (base, identifier):

	global __failed

	if __failed.has_key (base):
		# This has already failed in previous attempt
		return {base: __failed [base]}

	try:
		m = __import__ (base, None, None, '*')
	except:
		__failed [base] = sys.exc_info ()
		return {base: __failed [base]}

	if hasattr (m, '__noplugin__'):
		# This is not a plugin, ignore it
		return {}

	if hasattr (m, identifier):
		# This is already a plugin, no need to go deeper
		if hasattr (m, '__initplugin__'):
			try:
				m.__initplugin__ ()
			except:
				__failed [base] = sys.exc_info ()
				return {base: __failed [base]}
		return m

	# Search all submodules
	exceptions = {}
	for sub in __modules (m, False):
		result = __first (base + '.' + sub, identifier)
		if isinstance (result, ModuleType):
			return result
		exceptions.update (result)
	return exceptions


# -----------------------------------------------------------------------------
# Recursively search for a plugin and return the module or the exceptions that
# occured
# -----------------------------------------------------------------------------

def __find (base, name, identifier):

	if __failed.has_key (base):
		# This has already failed in previous attempt
		return {base: __failed [base]}

	try:
		m = __import__ (base, None, None, '*')
	except:
		__failed [base] = sys.exc_info ()
		return {base: __failed [base]}

	if hasattr (m, '__noplugin__'):
		# This is not a plugin, ignore it
		return {}

	# Is the searched driver an alias of this module?
	if hasattr (m, '__pluginalias__'):
		if name in m.__pluginalias__:
			return __first (base, identifier)

	if __failed.has_key (base + '.' + name):
		# This has already failed in previous attempt
		return {base + '.' + name: __failed [base + '.' + name]}

	try:
		m = __import__ (base + '.' + name, None, None, '*')
	except ImportError:
		pass
	except:
		__failed [base + '.' + name] = sys.exc_info ()
		return {base + '.' + name: __failed [base + '.' + name]}
	else:
		return __first (base + '.' + name, identifier)

	# Search all submodules
	exceptions = {}
	for sub in __modules (m, False):
		result = __find (base + '.' + sub, name, identifier)
		if isinstance (result, ModuleType):
			return result
		exceptions.update (result)

	return exceptions


# =============================================================================
# Self test code
# =============================================================================

if __name__ == '__main__':

	base = 'gnue.common.datasources.drivers'

	if len (sys.argv) == 1:

		# List all modules
		for (name, result) in (list (base, 'Connection')).items ():
			print name [len(base)+1:]  + ":",
			if isinstance (result, ModuleType):
				print "ok"
			else:
				list = traceback.format_exception_only (result [0], result [1])
				print string.join (list, ''),

	elif sys.argv [1] == 'test':

		try:
			print 'find "postgresql.popy":',
			m = find ('postgresql.popy', base, 'Connection')
			print m.__name__
		except LoadError, e:
			print e
			print "Detail:"
			print o(e.detail),

		print

		try:
			print 'find "pygresql":',
			m = find ('pygresql', base, 'Connection')
			print m.__name__
		except LoadError, e:
			print e
			print "Detail:"
			print o(e.detail),

		print

		try:
			print 'find "mysql":',
			m = find ('mysql', base, 'Connection')
			print m.__name__
		except LoadError, e:
			print e
			print "Detail:"
			print o(e.detail),

		print

		try:
			print 'find "oracle":',
			m = find ('oracle', base, 'Connection')
			print m.__name__
		except LoadError, e:
			print e
			print "Detail:"
			print o(e.detail),

		print

		try:
			print 'find "nonexistent":',
			m = find ('nonexistent', base, 'Connection')
			print m.__name__
		except LoadError, e:
			print e
			print "Detail:"
			print o(e.detail),

	else:

		try:
			print 'find %s:' % sys.argv [1],
			m = find (sys.argv [1], base, 'Connection')
			print m.__name__
		except LoadError, e:
			print e
			print "Detail:"
			print o(e.detail),
