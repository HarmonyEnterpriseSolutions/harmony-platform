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
# $Id: GConfig.py 9222 2007-01-08 13:02:49Z johannes $
#
# DESCRIPTION:
# Class that loads the configuration files so gnue apps can get
# default settings.
#
# NOTES:
#

from ConfigParser import *
import os
import string
import sys
import textwrap

from gnue import paths
from gnue.common.apps import i18n, errors, GDebug
from gnue.common.utils.FileUtils import openResource
from gnue.common import GCConfig
import copy

# -----------------------------------------------------------------------------
# Configuration file cannot be parsed
# -----------------------------------------------------------------------------

class InvalidFormatError (errors.AdminError):
	pass


class GConfig:
	def __init__(self, section, defaults=None, configFilename="gnue.conf", homeConfigDir=".gnue"):

		self._defaultConfigFilename = configFilename
		self._defaultSection = section
		self._loadedConfigs = {}
		self.loadApplicationConfig(configFilename,homeConfigDir,section, defaults)

		# Add global gConfig function to application namespace
		import __builtin__
		__builtin__.__dict__['gConfig'] = self.gConfig
		__builtin__.__dict__['gConfigDict'] =  self.gConfigDict

	def registerAlias(self, name, section):
		alias = GConfigAlias(self.gConfig, section)
		import __builtin__
		__builtin__.__dict__[name] = alias.gConfig


	#
	# loadApplicationConfig
	#
	# Loads the specified file only once.
	# Subsequent calls setup the defaults for any missing values
	#
	def loadApplicationConfig(self, configFilename="gnue.conf", homeConfigDir=".gnue", section="DEFAULT", defaults = None):

		assert gDebug(2,'Reading configuration info from %s section %s' % (configFilename, section))

		#
		# Create parser and populate it if it doesn't exist
		#
		if not self._loadedConfigs.has_key(configFilename):
			if defaults is None:
				parser = GConfigParser(GCConfig.ConfigOptions)
			else:
				parser = GConfigParser(defaults + GCConfig.ConfigOptions)
			self._loadedConfigs[configFilename]=parser


			# Build valid file list
			fileLocations = []
			etc_base = getInstalledBase('%s_etc' % section, 'common_etc')

			# system config file
			if etc_base:
				fileLocations.append(os.path.join(etc_base,configFilename))

			# user config file
			try:
				fileLocations.append(os.path.join(os.environ['HOME'], homeConfigDir ,configFilename))
			except KeyError:
				pass

			# system fixed config file
			if etc_base:
				fileLocations.append(os.path.join(etc_base,configFilename+'.fixed'))

			#
			# Load the values from the files specified
			#
			try:
				parser.read(fileLocations)
				assert gDebug(2,'Configuration files were read in this order:  %s' % \
						(fileLocations) )
			except DuplicateSectionError:
				raise InvalidFormatError, \
					u_('Configuration file has duplicate sections.')
			except MissingSectionHeaderError:
				raise InvalidFormatError, \
					u_('Configuration file has no sections.')
			except:
				raise InvalidFormatError, \
					u_('Configuration file cannot be parsed:\n%s') % sys.exc_value

			#
			# Common only needs checked once
			#
			# Load any [common] defaults
			self._integrateDefaultDict(configFilename,'common',
				self._buildDefaults(GCConfig.ConfigOptions))

		#
		# Load anything set in the DEFAULT section
		#
		self._integrateDefaultDict(configFilename,section,
			self._loadedConfigs[configFilename].defaults())

		#
		# If any values are still blank after loading from file's
		# specific section and then the default section then load the
		# defaults specified by the application itself.
		#
		self._integrateDefaultDict(configFilename,section,self._buildDefaults(defaults))


	def _integrateDefaultDict(self,filename, section,defaults):
		try:
			self._loadedConfigs[filename].add_section(section)
		except DuplicateSectionError:
			pass
		for key in defaults.keys():
			# Only set the value to the default if config file didn't contain
			# custom setting.
			try:
				self._loadedConfigs[filename].get(section,key)
			except NoOptionError:
				self._loadedConfigs[filename].set(section,key,defaults[key])


	def gConfig(self, varName, configFilename=None, section=None):
		if not configFilename: configFilename = self._defaultConfigFilename
		if not section: section = self._defaultSection
		try:
			return self._loadedConfigs[configFilename].get(section,varName)
		except NoSectionError:
			self._loadedConfigs[configFilename].add_section(section)
			return self._loadedConfigs[configFilename].get(section,varName)
		except NoOptionError:
			section = 'common'
			try:
				return self._loadedConfigs[configFilename].get(section,varName)
			except NoSectionError:
				self._loadedConfigs[configFilename].add_section(section)
				return self._loadedConfigs[configFilename].get(section,varName)

	def gConfigDict(self, configFilename=None, section=None):
		if not configFilename: configFilename = self._defaultConfigFilename
		if not section:      section = self._defaultSection

		c = self._loadedConfigs[configFilename]
		if c.has_section(section):
			options = {}
			for option in c.options(section):
				options[option] = c.get(section,string.lower(option))
			return options
		else:
			return {}

	def _buildDefaults(self, defaultDefinitions):
		defaults = {}
		if defaultDefinitions:
			for definition in defaultDefinitions:
				defaults[string.lower(definition['Name'])]=str(definition['Default'])
		return defaults


class GConfigParser(ConfigParser):
	"""
	Add support for our GTypecast systems to the generic ConfigParser
	"""
	def __init__(self, defaults):
		self.__defaults = defaults
		ConfigParser.__init__(self)
		typecasts = self.__typecasts = {}
		# FIXME: I don't know what kind of elements are stored in 'defaults'.
		#        add a correct iteration over the "defaults-dictionary"!
		if defaults and (len (defaults) > 0):
			for f in defaults:
				try:
					typecasts[f['Name'].lower()] = f['Typecast']
				except KeyError:
					typecasts[f['Name'].lower()] = str

	def get(self, section, field):
		try:
			val = ConfigParser.get(self, section, field)
			return self.__typecasts[field.lower()](val)
		except KeyError:
			return val
		except ValueError:
			raise ValueError, u_("Config option %(field)s is of wrong type in "
				"[%(section)s]") \
				% {'field': field, 'section': section}


class GConfigAlias:
	def __init__(self, gconfig, name):
		self._gConfig = gconfig
		self._section = name

	def gConfig(self, varName, configFilename=None, section=None):
		if not section:
			section = self._section
		return self._gConfig(varName, configFilename=configFilename, section = section)


def getInstalledBase(*parameters):
	for param in parameters:
		try:
			return _site_config[param]
		except KeyError:
			pass

	return None

def printableConfigOptions(options, outputWidth=60):
	output = "Valid config file options.....\n"
	if options:
		for option in options:
			output += '='*outputWidth+"\n"
			nameString = "Name:%s" % option['Name']
			defaultString = "Default Value:%s" % option['Default']
			output += "%s%s%s\n" %(nameString, ' ' * (outputWidth - len(nameString + defaultString)), defaultString)
			# FIXME: This allows for non-unicode descriptions. Remove at some point.
			description = option['Description']
			if isinstance(description, str):
				description = unicode(description, i18n.getencoding())
			output += "%s\n" % textwrap.fill(description, outputWidth)
	else:
		output += "No options defined"
	return output

############################
#
# Site configuration stuff
#
############################

_site_config = {}

# highest priority: site_config.cfg (depreciated -- will be removed)

if os.environ.has_key('GNUE_INSTALLED_SITE_CFG'):
	input = open(os.environ['GNUE_INSTALLED_SITE_CFG'],'r')
	text = input.read()
	input.close()

	# This evaluates the text file as a python script (hope you secured it)
	# The resulting namespace is stored as a dict in _site_config.
	eval (compile(text, '<string>', 'exec'), _site_config)

# second priority: INSTALL_PREFIX environment variable (depreciated -- will be
# removed)

elif os.environ.has_key('INSTALL_PREFIX'):

	install_prefix = os.environ['INSTALL_PREFIX']
	_site_config = {
		'install_prefix': install_prefix,
		'common_etc': os.path.join(install_prefix,'etc'),
		'common_images': os.path.join(install_prefix,'shared','images'),
		'common_appbase': install_prefix,
		'common_shared': os.path.join(install_prefix,'shared')
	}

else:
	_site_config = {
		"install_prefix": paths.data,
		"common_etc": paths.config,
		"common_images": os.path.join (paths.data, "share", "gnue", "images"),
		"common_appbase": paths.data,
		"common_shared": os.path.join (paths.data, "share", "gnue")}
