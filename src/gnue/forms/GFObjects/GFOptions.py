# GNU Enterprise Forms - GF Object Hierarchy - Options container
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
# $Id: GFOptions.py,v 1.2 2008/11/04 20:14:16 oleg Exp $
"""
Options container support
"""

from gnue.common.definitions.GObjects import GObj

# =============================================================================
# Collection of options
# =============================================================================

class GFOptions(GObj):

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):

		GObj.__init__(self, parent, 'GFOptions')
