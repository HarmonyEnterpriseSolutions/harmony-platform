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
# $Id: GFSplitter.py,v 1.6 2008/11/04 20:14:16 oleg Exp $
"""
Splitter
"""

from gnue.forms.GFObjects.GFContainer import GFContainer
BaseClass = GFContainer

__all__ = ['GFSplitter']

# =============================================================================
# <vbox>
# =============================================================================

class GFSplitter(BaseClass):

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	ALIGN_VERTICAL = 0
	ALIGN_HORIZONTAL = 1

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		BaseClass.__init__(self, parent, "GFSplitter")

		self.align = 'vertical'	# default value

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		BaseClass._phase_1_init_(self)

	def getAlign(self):
		return ['vertical', 'horizontal', 'v', 'h'].index(self.align) % 2
