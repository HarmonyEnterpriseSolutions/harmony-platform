# -*- coding: iso-8859-1 -*-
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
# Copyright 2001-2007 Free Software Foundation
#
# FILE:
# FileUtils.py
#
# DESCRIPTION:
# Common file/url/resource related utilities
#
# NOTES:
# TODO: Deprecate


import os
import urllib
import urlparse
import sys
import cStringIO


# For backwards compatability
from gnue.common.utils.importing import import_string as dyn_import
from gnue.common.utils.file import to_uri as urlize, \
	open_uri as openResource, \
	to_buffer as openBuffer
