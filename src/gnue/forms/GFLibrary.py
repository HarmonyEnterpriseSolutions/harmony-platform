#
# This file is part of GNU Enterprise.
#
# GNU Enterprise is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or(at your option) any later version.
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
# GFLibrary
#
# DESCRIPTION:
"""
Adds support for importing of "library" items
"""
#
# NOTES:
#

import string

from gnue.common.definitions.GObjects import GObj
from src.gnue.forms import GFParser


class GFImport(GObj):
	def __init__(self, parent=None):
		GObj.__init__(self, parent, type="GFImport")
		self.library = ""
		self._form = None


class GFImportItem(GObj):
	def __init__(self, parent=None, type="GFImport-Item"):
		GObj.__init__(self, parent, type=type)
		self._loadedxmlattrs = {} # Set by parser

	def _buildObject(self):
		if hasattr(self,'_xmltag'):
			self._type = 'GF%s' % self._xmltag
		if not hasattr(self,'_importclass'):
			self._importclass = GFParser \
				.getXMLelements()[string.lower(self._type[9:])]['BaseClass']

		print self._type, self._importclass
		return GObj._buildObject(self)
