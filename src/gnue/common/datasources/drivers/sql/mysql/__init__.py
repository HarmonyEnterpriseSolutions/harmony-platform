# GNU Enterprise Common Library - MySQL database driver plugins
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
Database driver plugins for MySQL backends.
"""


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "MySQL (4.x+)"

	url = "http://www.mysql.org/"

	description = """
MySQL is a fast database that runs on numerous platforms. It is one of the
most popular free databases available.

Given the transactional nature of GNUe, we recommend using MySQL 4.x+ with
transaction support compiled in.

Not all features of GNUe are usable under MySQL, such as auto-populating fields
with serials/sequences and query-by-detail.
"""

	isfree = True
