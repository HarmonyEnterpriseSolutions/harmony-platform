# GNU Enterprise Forms - GF Object Hierarchy - Layout
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
# pylint: disable-msg=W0704
#
# $Id: GFLayout.py,v 1.5 2008/11/04 20:14:16 oleg Exp $
"""
Handles the <layout> tag.
"""

from src.gnue.forms.GFObjects import GFContainer

__all__ = ['GFLayout', 'LayoutConceptError']


# =============================================================================
# Class implementing the layout tag
# =============================================================================

class GFLayout(GFContainer):
	"""
	Implementation of the <layout> tag
	"""

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	tabbed = 'none'
	name   = 'layout'


	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):

		GFContainer.__init__(self, parent, "GFLayout")

		self._triggerGlobal = 1
		self._xmlchildnamespaces = {}

		self._triggerFunctions = {
			'find_child': {'function': self.__trigger_find_child},
		}

	def __trigger_find_child(self, name, childType = None, recursive = True):
		child = self.findChildNamed(name, childType, recursive)
		if child:
			return child.get_namespace_object()

	# -------------------------------------------------------------------------
	# Implementation of virtual methods
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		"""
		Build a dictionary of all XML namespaces used by the layouts children
		"""

		GFContainer._phase_1_init_(self)
		self._xmlchildnamespaces = self.__find_namespaces(self)


	# -------------------------------------------------------------------------
	# Find the XML namespace in use by any child objects
	# -------------------------------------------------------------------------

	def __find_namespaces(self, gf_object):

		result = {}
		for child in gf_object._children:
			try:
				if child._xmlnamespaces:
					result.update(child._xmlnamespaces)
				else:
					result.update(self.__find_namespaces(child))

			except AttributeError:
				pass

		return result
