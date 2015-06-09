# GNU Enterprise Common Library - Namespace Handling
#
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
# $Id: NamespaceCore.py 9222 2007-01-08 13:02:49Z johannes $
"""
Classes to build up a namespace object tree from an XML object tree.

Namespace objects are available within action and trigger code. They mirror the
XML object tree of the document, but the namespace objects are limited to the
functions and properties that the objects explicitly want to provide.
"""

from gnue.common.definitions.GObjects import GObj

__all__ = ['GObjNamespace']


# =============================================================================
# GObjNamespace
# =============================================================================

class GObjNamespace:
	"""
	Helper object to build up a tree of namespace objects. For internal use of
	the trigger system only.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, xml_object, rootName = "root"):
		"""
		Initialize a GObjNamespace instance.
		"""

		# FIXME: This should rather check for GRootObj, but that causes a
		# circular import
		checktype (xml_object, GObj)

		self.__root_name = rootName

		self._globalNamespace = {}

		self._globalNamespace[rootName] = xml_object.create_namespace_object(self._globalNamespace, self.__root_name)