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
# Copyright 2000-2007 Free Software Foundation
#
# FILE:
# CommandOption.py
#
# DESCRIPTION:
"""
Command option available to GBaseApp and descendants. Usualy asigned with
the function addCommandOption.
"""

from gnue.common.apps import i18n

class CommandOption:
	def __init__(self, name, shortOption=None, longOption=None,
		acceptsArgument=False, default=None, argumentName=None,
		help="", category="general", action=None, argument=None):
		"""
		 @param name: The key name that will be avaliable  in the self.OPTION
		     dictionary when the application is executing.
		 @param shortOption: Single letter to be assignd to this option.
		 @param longOption: The long option name that is prepended with -- on the
		     command line.
		 @param acceptsArgument: True if the option requires a value to be
		     assigned from the command line.
		 @param default: Default value if the option is not passed in via the
		     command line.
		 @param argumentName: Same as argument, overridden by argument.
		 @param help: Description of the option as displayed in help text.
		 @param category: Used to create groups of command options, where groups
		     "base", "dev", "connections" and "general" are predefined. There is
		     an option --help-dev, --help-connections to give a special help-text
		     for these groups of options.
		 @param action: Function-pointer; if supplied this function will be called
		     automatically if the option is given on command line.
		 @param argument: Option argument as shown in help text. Same as
		     argumentName.
		"""

		self.name = name
		self.shortOption = shortOption
		self.longOption = longOption or name.replace('_','-')
		self.default = default
		self.help = help
		self.category = category
		self.action = action
		if argument:
			self.acceptsArgument=True
			self.argumentName = argument
		else:
			self.acceptsArgument=acceptsArgument
			self.argumentName = argumentName

		# FIXME: only for compatibility, remove in some later version!
		if isinstance (self.help, str):
			self.help = unicode (self.help, i18n.getencoding ())
		if isinstance (self.argumentName, str):
			self.argumentName = unicode (self.argumentName, i18n.getencoding ())
