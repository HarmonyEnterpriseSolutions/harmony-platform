# GNU Enterprise Common Library - Firebird/Interbase database driver plugins
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
# $Id: __init__.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugins for Firebird/Interbase backends.
"""


# =============================================================================
# Define alias for this plugin
# =============================================================================

__pluginalias__ = ['firebird']


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "Firebird/Interbase"

	url = "http://www.firebirdsql.org/"

	description = """
Firebird is a free relational database offering many ANSI SQL-92 features that
runs on GNU/Linux, Windows, and a variety of Unix platforms. Firebird offers
excellent concurrency, high performance, and powerful language support for
stored procedures and triggers. It has been used in production systems,
under a variety of names since 1981.

Interbase is a proprietary database available from Borland.

Firebird and Interbase share a common API, which allows GNUe to use the same
drivers for both.

Firebird is a popular choice of GNUe's Windows-based developers.
"""

	isfree = True
