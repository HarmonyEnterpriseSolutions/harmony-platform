# GNU Enterprise Forms - GF Object Hierarchy - Box
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
# $Id: GFNotepage.py,v 1.6 2011/10/04 13:22:27 oleg Exp $
"""
NotePage
"""

from gnue.forms.GFObjects.GFContainer import GFContainer as BaseClass

__all__ = ['GFNotepage']

# =============================================================================
# <notepage>
# =============================================================================

class GFNotepage(BaseClass):

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	label = None
	description = None

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		BaseClass.__init__(self, parent, "GFNotepage")

		self._triggerFunctions = {
			'select' : { 'function' : self.select },
		}

		self._triggerProperties = {
			# TODO: all objects attributes must be accessible?
			'name' : {
				'get' : lambda: self.name,
			}
		}

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		BaseClass._phase_1_init_(self)

	def select(self):
		self.uiWidget._ui_select_()
