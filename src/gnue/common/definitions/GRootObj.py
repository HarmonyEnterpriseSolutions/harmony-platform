# GNU Enterprise Common Library - GNUe XML object definitions - Root Node
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
# $Id: GRootObj.py 9222 2007-01-08 13:02:49Z johannes $

"""
Provides the base class that can optionally be used by root objects in a GObj
based tree.
"""

__all__ = ['GRootObj']

from gnue.common.logic.NamespaceCore import GObjNamespace
from gnue.common.definitions.GObjects import GObj
from gnue.common.utils.FileUtils import dyn_import

# =============================================================================
# GRootObj
# =============================================================================

class GRootObj (GObj):

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, rootName, xmlElementCallback, xmlParser, *args, **parms):

		GObj.__init__ (self, *args, **parms)

		self._triggerNamespaceTree = None
		self._rname                = rootName

		if isinstance (xmlParser, basestring):
			self._xmlParser = dyn_import (xmlParser)
		else:
			self._xmlParser = xmlParser

		self._xmlnamespaces        = {}
		self._standardnamespaces   = {}
		self._rootComments         = []

		self.__xmlElementCallback  = xmlElementCallback


	# ---------------------------------------------------------------------------
	# Initialize the trigger system
	# ---------------------------------------------------------------------------

	def initTriggerSystem (self):

		self._triggerNamespaceTree = GObjNamespace (self, rootName = self._rname)


	# ---------------------------------------------------------------------------
	# Get the object's XML code tree
	# ---------------------------------------------------------------------------

	def dumpXML (self, lookupDict = {}, treeDump = True, gap = "  ",
		xmlnamespaces= {}, textEncoding = '<locale>', stripPrefixes = None):

		xmlElements = lookupDict
		xmlElements.update (self.__xmlElementCallback ())

		return GObj.dumpXML (self, xmlElements, treeDump, gap,
			xmlnamespaces = self._standardnamespaces, textEncoding = textEncoding,
			stripPrefixes = stripPrefixes)
