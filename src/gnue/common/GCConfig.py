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
# $Id: GCConfig.py 9222 2007-01-08 13:02:49Z johannes $

"""
Valid configuration options that apply to all GNUe tools
(appears under [common] section in gnue.conf or
can appear in each individual tool section)
"""

import locale

from gnue.common.formatting import GTypecast

ConfigOptions = (
	{ 'Name'       : 'textEncoding',
		'Type'       : 'Setting',
		'Comment'    : 'Encoding for XML headers and for fonts in forms. '
		+ 'Like iso8859-1, iso8859-13.',
		'Description': 'Encoding for XML headers and for fonts in forms. '
		+ 'Like iso8859-1, iso8859-13.',
		'Typecast'   : GTypecast.text,
		'Default'    : locale.getpreferredencoding ()},

	{ 'Name'       : 'ImportPath',
		'Type'       : 'Setting',
		'Comment'    : 'Locations added to the python search path',
		'Description': 'A comma-separated list of directories to be added '
		+ 'to the python search path to add custom functionality.',
		'Typecast'   : GTypecast.text,
		'Default'    : "" },

	{ 'Name'       : 'StoreTriggersAsCDATA',
		'Type'       : 'Setting',
		'Comment'    : 'If set to true, then store trigger definitions in '
		+ '<![CDATA[ .. ]]> blocks, instead of encoding with &lt; etc.',
		'Description': 'If set to true, then store trigger definitions in '
		+ '<![CDATA[ .. ]]> blocks, instead of encoding with &lt; etc.',
		'Typecast'   : GTypecast.boolean,
		'Default'    : True },
)
