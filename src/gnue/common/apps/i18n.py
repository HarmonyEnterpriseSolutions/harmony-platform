# GNU Enterprise Common Library - i18n support
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
# $Id: i18n.py 9614 2007-05-24 08:46:51Z johannes $

"""
Internationalization support.

@var language: Language of the current locale
@var encoding: Encoding of the current locale
"""

import gettext
import locale
import os
import os.path
import sys

from gnue import paths

__all__ = ['language', 'encoding', 'outconv', 'utranslate', 'translate',
	'getlanguage', 'getencoding', 'getuserlocale', 'setcurrentlocale']


# -----------------------------------------------------------------------------
# Global variables
# -----------------------------------------------------------------------------

__modules = {}                          # Modules by filename
__catalogs = {}                         # Message catalogs by domain:language

language = None
encoding = None

# languages to try to load for specified language
LANGUAGES = {
	'uk_UA' : ['uk_UA', 'ru_RU'],
}

DEFAULT_LANGUAGES = ['ru_RU']

# -----------------------------------------------------------------------------
# Convert Unicode to String, let everything else untouched. This is o().
# -----------------------------------------------------------------------------

def outconv (message):
	"""
	Encodes a message to L{encoding} (the current locale's encoding).  This
	function is available as the builtin function "o()".
	"""
	if isinstance (message, unicode):
		return message.encode (encoding, 'replace')
	else:
		return message


# -----------------------------------------------------------------------------
# Find a module from filename
# -----------------------------------------------------------------------------

def __find_module (filename):
	if __modules.has_key (filename):
		return __modules [filename]
	for mod in sys.modules.values ():
		if hasattr (mod, '__file__'):
			# mod.__file__ can be .pyc if the module is already compiled
			mod_filename = mod.__file__
			if mod_filename.endswith('c'):
				mod_filename = mod_filename [:-1]
			if os.path.normcase (mod_filename) == os.path.normcase (filename):
				__modules [filename] = mod
				return mod


# -----------------------------------------------------------------------------
# Find the correct translation catalog
# -----------------------------------------------------------------------------

def __find_catalog ():

	# find out the filename of the calling function
	caller_file = (sys._getframe (2)).f_code.co_filename

	# find out the module name
	caller_module = __find_module (caller_file)

	if caller_module is None:
		return None

	domain = caller_module.__name__

	# make 'gnue-common' from 'gnue.common.foo.bar'
	if domain.startswith('gnue.'):
		domain = domain.replace('.', '-', 1)

	domain = domain [:domain.find('.')]

	return getCatalog(domain)


def getCatalog(domain):

	catalog = __catalogs.get((domain, language), NotImplemented)
	if catalog is NotImplemented:
		try:
			catalog = gettext.translation(domain, paths.data + '/share/locale', LANGUAGES.get(language, DEFAULT_LANGUAGES))
		except Exception, e:
			assert gDebug('i18n', '! %s: %s' % (e.__class__.__name__, e))
			catalog = None

		__catalogs [(domain, language)] = catalog

	return catalog


# -----------------------------------------------------------------------------
# Translate a message and return unicode
# -----------------------------------------------------------------------------

def utranslate (message):
	"""
	Translates a message and returns a unicode string.  This function is
	available as the builtin function "u_()".
	"""
	catalog = __find_catalog ()

	if catalog is None:
		return message

	return catalog.ugettext (message)


# -----------------------------------------------------------------------------
# Translate a message and return local encoding
# -----------------------------------------------------------------------------

def translate (message):
	"""
	Translates a message and returns an 8 bit string, encoded with L{encoding}
	(the current locale's encoding).  This function is available as the builtin
	function "_()".
	"""
	catalog = __find_catalog ()

	if catalog is None:
		return message

	return outconv (catalog.ugettext (message))


# -----------------------------------------------------------------------------
# Get the current language
# -----------------------------------------------------------------------------

def getlanguage ():
	"""
	Returns the language of the currently acitve locale. This can be changed with
	L{setcurrentlocale}.

	@return: language of the current locale.
	"""
	return language


# -----------------------------------------------------------------------------
# Get the current encoding
# -----------------------------------------------------------------------------

def getencoding ():
	"""
	Returns the encoding of the currently active locale. This can be changed with
	L{setcurrentlocale}.

	@return: encoding of the current locale.
	"""
	return encoding


# -----------------------------------------------------------------------------
# Get the locale string of the current user
# -----------------------------------------------------------------------------

def getuserlocale ():
	"""
	Try to find out which locale the user is using.  This is always the locale of
	the user running the program and is not touched by setcurrentlocale.

	@return: localestring of the user's locale, i.e. de_AT@euro.
	"""

	# *Actually* the following is very much what locale.getdefaultlocale should
	# do anyway.  However, that function is broken for $LANGUAGE containing a
	# list of locales, separated with ":". So we have to manually rebuild it...
	items = ['LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG']
	for key in items:
		if os.environ.has_key (key):
			# Some systems (most notably Debian...) set $LANGUAGE to a *list* of
			# locales, separated by a ":".
			env_lang = (os.environ [key]).split (':') [0]
			return locale.locale_alias.get (env_lang, env_lang)

	# Now this should only happen on Windows, where getdefaultlocale seems to
	# work ok.
	try:
		result = locale.getdefaultlocale () [0]
	except locale.Error:
		result = ''

	return result or 'C'


# -----------------------------------------------------------------------------
# Update global variables
# -----------------------------------------------------------------------------

def __updateglobals ():

	global language, encoding

	# On win32, getlocale is broken - it returns strings like Hungarian_Hungary
	# instead of hu_HU.
	if sys.platform in ['win32', 'Pocket PC']:
		language = locale.getdefaultlocale()[0]
		# if default encoding was not set by sys.setdefaultencoding, use UTF8
		encoding = 'UTF8' if sys.getdefaultencoding() == 'ascii' else sys.getdefaultencoding()
	else:
		(language, encoding) = locale.getlocale ()

	# Make sure language and encoding are not None
	if not language:
		language = 'C'
	if not encoding:
		encoding = 'ascii'

# -----------------------------------------------------------------------------
# Change the current locale
# -----------------------------------------------------------------------------

def setcurrentlocale (new_locale):
	"""
	Set the current locale.

	If it fails it tries to succeed using a more general form of the requested
	locale, i.e. if 'de_AT@euro' fails, 'de_AT' will be tried next. If that fails
	too, 'de' will be tried.

	@param new_locale: string of the locale to be set, e.g. de_AT.ISO88591@euro
	  (full blown) or 'de_AT' or 'en_AU'
	"""
	# Setting a locale different than the current locale doesn't work on Windows.
	if sys.platform == 'win32':
		return

	if new_locale is None:
		new_locale = ''

	new_locale = new_locale.encode ()

	parts  = []
	add    = []
	normal = locale.normalize (new_locale)         # lc_CC.ENCODING@variant
	next   = normal.split ('@') [0]               # lc_CC.ENCODING
	lang   = next.split ('.') [0]                 # lc_CC

	alias  = locale.locale_alias.get (lang.split ('_') [0].lower ())
	if alias:
		add = [alias.split ('@') [0]]
		add.append (add [-1].split ('.') [0])
		add.append (locale.locale_alias.get (add [-1].split ('_') [0].lower ()))

	for item in [normal, next, lang] + add:
		if item is not None and item not in parts:
			parts.append (item)

	for item in parts:
		try:
			locale.setlocale (locale.LC_ALL, item)

		except locale.Error:
			pass

		else:
			break

	__updateglobals ()


# -----------------------------------------------------------------------------
# Module initialization
# -----------------------------------------------------------------------------

# set locale if yet not set by host application
if locale.getlocale() == (None, None):

	# Initialize locale.  On Mac locale.setlocale() does not return the default
	# locale.  Instead we have to query the system preferences for the AppleLocale
	if sys.platform == 'darwin':
		pipe = os.popen('defaults read -g AppleLocale')
		deflc = pipe.read().strip() + '.UTF-8'
		pipe.close()
	else:
		deflc = ''

	try:
		locale.setlocale (locale.LC_ALL, deflc)
	except:
		pass
	else:
		if os.name == 'nt':
			# under windows
			try:
				import WebKit
			except:
				# not under webkit
				try:
					from django.conf import settings
					settings.SITE_ID
				except:
					# not under django or webkit
					encoding = locale.getpreferredencoding()
					if encoding:
						from toolib.util.streams import Rewriter
						if sys.stdout.encoding and sys.stdout.encoding != encoding: sys.stdout = Rewriter(sys.stdout, sys.stdout.encoding, encoding)
						if sys.stderr.encoding and sys.stderr.encoding != encoding: sys.stderr = Rewriter(sys.stderr, sys.stderr.encoding, encoding)


__updateglobals ()

# Now define the new builtin stuff
import __builtin__
__builtin__.__dict__['o'] = outconv
__builtin__.__dict__['u_'] = utranslate
__builtin__.__dict__['_'] = utranslate		# utranslate too
