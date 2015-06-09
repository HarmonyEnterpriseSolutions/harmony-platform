#
# Copyright 2001-2007 Free Software Foundation
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
# FILE:
# RuntimeSettings.py
#
# DESCRIPTION:
# Saves the state of designer between runs. Saves such data as
# window positions, size, visibility, etc.
#
# NOTES:

import sys, os, ConfigParser


# TODO: Should this save into the Win32 registry if its available?????
# TODO: This is, after all, session-specific information and not
# TODO: user-settable configuration data.

if not globals().has_key('location'):
	location = None

def init(configFilename="default.ini", homeConfigDir=".gnue"):
	global location, config
	if os.environ.has_key('HOME'):
		try:
			os.makedirs(os.path.join(os.environ['HOME'], homeConfigDir))
		except:
			pass
		location = os.path.join(os.environ['HOME'], homeConfigDir ,configFilename)
	elif sys.platform[:3] in ('win','mac'):
		location = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])),configFilename)
	else:
		location = configFilename

	try:
		config = ConfigParser.ConfigParser()
		config.read(location)
	except:
		config = None

def registerInstance(instance):
	instance._runtimes = []


def get(section, setting, default):
	# Backwards compatability
	if location == None:
		init()
	try:
		return config.get(section, setting)
	except:
		return default


def getint(section, setting, default):
	# Backwards compatability
	if location == None:
		init()
	try:
		return config.getint(section, setting)
	except:
		return default

#
# Save the runtime settings
#
def saveRuntimeSettings(instance):
	from gnue.common.apps.GDebug import _DEBUG_LEVELS
	if location:
		try:
			fh = open(location,'w')
			for h in instance._runtimes:
				try:
					section, hash = h.saveRuntimeSettings()
				except:
					print o(u_("Warning: Unable to save all session data to %s") %
						location)
					if _DEBUG_LEVELS != [0]:
						raise
				if len(hash.keys()):
					if not config.has_section(section):
						config.add_section(section)
					for key in hash.keys():
						config.set(section, key, "%s" % hash[key])

			config.write(fh)
			fh.close()
		except:
			print o(u_("\nWarning: Unable to save session data to %s\n") % location)
			if _DEBUG_LEVELS != [0]:
				raise

#
# Any object (class) that has settings it wants saved should
# register with this method.  The object should define a
# getRuntimeSettings() method.
#
def registerRuntimeSettingHandler(instance, object):
	instance._runtimes.append(object)
