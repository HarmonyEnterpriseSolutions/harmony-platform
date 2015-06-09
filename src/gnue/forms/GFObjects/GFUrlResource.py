# GNU Enterprise Forms - GF Object Hierarchy - Images
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
# $Id: GFUrlResource.py,v 1.3 2009/07/24 15:00:54 oleg Exp $
"""
Wrapper class for image objects
"""

from gnue.forms.GFObjects.GFTabStop import GFFieldBound


# =============================================================================
# Image objects
# =============================================================================

class GFUrlResource(GFFieldBound):

	label = None
	
	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None, value=None):
		GFFieldBound.__init__(self, parent, 'GFUrlResource')

		# to calm display handler constructor down
		self.style = 'text'

		self._triggerFunctions = {
			'getData':            {'function': self.getData},
		}

	def hasLabel(self):
		return self.label is not None

	# -------------------------------------------------------------------------
	# Get the current value
	# -------------------------------------------------------------------------

	#def getValue(self, *args, **kwargs):
	#    return self._field.getValue(*args, **kwargs)


	# -------------------------------------------------------------------------
	# Implementation of virtual methods
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):

		GFFieldBound._phase_1_init_(self)

		if not hasattr(self, 'Char__height'):
			self.Char__height = int(gConfigForms('widgetHeight'))

	# -------------------------------------------------------------------------

	def _is_navigable_(self, mode):

		return False

	def getData(self):
		return self.uiWidget._ui_get_data_()

