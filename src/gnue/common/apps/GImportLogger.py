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
# $Id: GImportLogger.py 9222 2007-01-08 13:02:49Z johannes $
#
"""
Importing this module causes all modules imported after this
to be printed to stdout
"""
import os, ihooks, sys
_import_indent = 0

class MyHooks(ihooks.Hooks):
	pass

class GImportLogger(ihooks.ModuleLoader):

	def load_module(self, name, stuff):
		global _import_indent
		print "." * _import_indent + "Importing %s..." % name
		_import_indent += 1

		module = ihooks.ModuleLoader.load_module(self, name, stuff)

		_import_indent -= 1
		return module

ihooks.ModuleImporter(GImportLogger(MyHooks())).install()
