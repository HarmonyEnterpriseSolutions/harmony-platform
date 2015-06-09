# GNU Enterprise Common Library - PostgreSQL database driver plugins
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
Database driver plugins for PostgreSQL backends.
"""


# =============================================================================
# Define aliases for this plugin
# =============================================================================

__pluginalias__ = ['pgsql', 'postgres']


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "PostgreSQL (7.x+)"

	url = "http://www.postgresql.org/"

	description = """
PostgreSQL is an free object-relational database, which supports a large part
of SQL-99.  It is under continuous development and each release implements
more of the SQL standard, to the extent that it is now probably more compliant
than most commercial databases.  It also supports some object-oriented
features. PostgreSQL is a full-featured, multi-user RDBMS that scales well
from a few users to an entire organization.

PostgreSQL is the primary database used by GNUe developers.
"""

	isfree = True
