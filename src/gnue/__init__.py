# GNU Enterprise Common Library - Base Module
#
# Copyright 2001-2006 Free Software Foundation
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
# $Id: __init__.py,v 1.1 2007/10/04 18:20:41 oleg Exp $

"""
GNUe base module.  All gnue.* modules depend on gnue.common, so import
gnue.<whatever>" will cause gnue.common.apps to be loaded. This sets up a GNUe
environment.
"""

# Init stuff like _()
import gnue.common.apps as _init
