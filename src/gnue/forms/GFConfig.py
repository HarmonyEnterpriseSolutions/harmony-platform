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
# $Id: GFConfig.py,v 1.3 2008/11/04 20:14:12 oleg Exp $

"""
Valid configuration options for forms
(appears under [forms] section in gnue.conf)
"""

from gnue.common.formatting import GTypecast

ConfigOptions = (
	{ 'Name'       : 'DefaultUI',
		'Type'       : 'Setting',
		'Comment'    : 'The default user interface driver to use if not specified '
		+ 'on the command line.',
		'Description': 'The default user interface driver to use if not specified '
		+ 'on the command line.',
		'Typecast'   : GTypecast.text,
		'Options'    : ['curses','wx26','gtk2','qt3','html','win32'],
		'Default'    : 'wx26' },

	{ 'Name'       : 'checkboxTrue',
		'Type'       : 'Setting',
		'Comment'    : 'The default value stored in the database for True values.',
		'Description': 'The default value stored in the database for True values '
		+ '(usual values are 1 or Y).',
		'Typecast'   : GTypecast.text,
		'Default'    : 'Y' },

	{ 'Name'       : 'checkboxFalse',
		'Type'       : 'Setting',
		'Comment'    : 'The default value stored in the database for false values.',
		'Description': 'The default value stored in the database for false values '
		+ '(usual values are 0 or N).',
		'Typecast'   : GTypecast.text,
		'Default'    : 'N' },

	{ 'Name'       : 'EnterIsNewLine',
		'Type'       : 'Setting',
		'Comment'    : 'Treat enter as shift-enter in multi-line text boxes.',
		'Description': 'Set to "True" if you want <ENTER> to insert newlines '
		+ 'in multirow entries.\nEven if set to false, '
		+ 'Shift+Enter will insert a newline.',
		'Typecast'   : GTypecast.boolean,
		'Default'    : True },

	{ 'Name'       : 'CacheDetailRecords',
		'Type'       : 'Setting',
		'Comment'    : 'Enable caching of detail data.',
		'Description': 'Enable caching of detail data.\n'
		+ 'If set to True (default), then always cache '
		+ 'detail data in a master/detail set. The benefits '
		+ 'of this method is performance. The downsize to '
		+ 'this method is that records are cached so any '
		+ 'changes made elsewhere are not reflected in the '
		+ 'cached records.\n'
		+ 'If set to false, then only cache detail data if '
		+ 'it has unposted changes. The benefits of this '
		+ 'method are that if another user modifies data '
		+ 'and saves, then it will be available to your '
		+ 'form much quicker.',
		'Typecast'   : GTypecast.boolean,
		'Default'    : True },

	{ 'Name'       : 'DateMask',
		'Type'       : 'Setting',
		'Comment'    : 'Mask for viewing date fields (without quotes).',
		'Description': 'Mask for viewing date fields (without quotes).',
		'Typecast'   : GTypecast.text,
		'Default'    : '%x' },

	{ 'Name'       : 'DateEditMask',
		'Type'       : 'Setting',
		'Comment'    : 'Mask for editing date fields (without qoutes).',
		'Description': 'Mask for editing date fields (without quotes).',
		'Typecast'   : GTypecast.text,
		'Default'    : '%x' },

	{ 'Name'       : 'DateMask_Time',
		'Type'       : 'Setting',
		'Comment'    : 'Mask for viewing time fields (without quotes).',
		'Description': 'Mask for viewing time fields (without quotes).',
		'Typecast'   : GTypecast.text,
		'Default'    : '%X' },

	{ 'Name'       : 'DateEditMask_Time',
		'Type'       : 'Setting',
		'Comment'    : 'Mask for editing time fields (without qoutes).',
		'Description': 'Mask for editing time fields (without quotes).',
		'Typecast'   : GTypecast.text,
		'Default'    : '%X' },

	{ 'Name'       : 'DateMask_Timestamp',
		'Type'       : 'Setting',
		'Comment'    : 'Mask for viewing timestamp fields (without quotes).',
		'Description': 'Mask for viewing timestamp fields (without quotes).',
		'Typecast'   : GTypecast.text,
		'Default'    : '%x %X' },

	{ 'Name'       : 'DateEditMask_Timestamp',
		'Type'       : 'Setting',
		'Comment'    : 'Mask for editing timestamp fields (without qoutes).',
		'Description': 'Mask for editing timestamp fields (without quotes).',
		'Typecast'   : GTypecast.text,
		'Default'    : '%x %X' },

	{ 'Name'       : 'numeric_grouping',
		'Type'       : 'Setting',
		'Comment'    : 'Grouping pattern used for thousands separating and ' \
			'definition of the decimal point. Format: <thousand ' \
			'separator><number of digits><decimal separator>.  ' \
			'The pair <thousand separator><number of ditigs> can ' \
			'be repeated multiple times.  Example: ,3.',
		'Description': 'Grouping pattern used for thousands separating and ' \
			'definition of the decimal point. Format: <thousand ' \
			'separator><number of digits><decimal separator>.  ' \
			'The pair <thousand separator><number of ditigs> can ' \
			'be repeated multiple times. Example: ,3.',
		'Typecast'   : GTypecast.text,
		'Default'    : '' },

	{ 'Name'       : 'SplashScreenPNG',
		'Type'       : 'Setting',
		'Comment'    : 'Location of startup graphic (PNG format)',
		'Description': 'Location of startup graphic (PNG format)',
		'Typecast'   : GTypecast.text,
		'Default'    : 'gnue-splash.png' },

	{ 'Name'       : 'DisableSplash',
		'Type'       : 'Setting',
		'Comment'    : 'Disable the startup splashscreen.',
		'Description': 'Disable the startup splashscreen.',
		'Typecast'   : GTypecast.boolean,
		'Default'    : False },

	{ 'Name'       : 'loginPNG',
		'Type'       : 'Setting',
		'Comment'    : 'Location of GNUe login logo (PNG format).',
		'Description': 'Location of GNUe login logo (PNG format).',
		'Typecast'   : GTypecast.text,
		'Default'    : 'gnue.png' },

	{ 'Name'       : 'loginBMP',
		'Type'       : 'Setting',
		'Comment'    : 'Location of GNUe login logo (BMP format).',
		'Description': 'Location of GNUe login logo (BMP format). '
		+ 'The win32 uidriver accepts only BMP format.',
		'Typecast'   : GTypecast.text,
		'Default'    : 'gnue.bmp' },

	{ 'Name'       : 'widgetHeight',
		'Type'       : 'Setting',
		'Comment'    : 'The default height of widgets for widgets that '
		+ 'don\'t specify height in .gfd file.',
		'Description': 'The default height of widgets for widgets that '
		+ 'don\'t specify height in .gfd file.',
		'Typecast'   : GTypecast.whole,
		'Default'    : 1 },

	{ 'Name'       : 'widgetWidth',
		'Type'       : 'Setting',
		'Comment'    : 'The default width of widgets for widgets that '
		+ 'don\'t specify width in .gfd file.',
		'Description': 'The default width of widgets for widgets that '
		+ 'don\'t specify width in .gfd file.',
		'Typecast'   : GTypecast.whole,
		'Default'    : 10 },

	{ 'Name'       : 'fixedWidthFont',
		'Type'       : 'Setting',
		'Comment'    : 'Set to true if wxWidgets or Win32 clients should use '
		+ 'a fixed width font.',
		'Description': 'The next 3 options are only used by the wxPython and the'
		+ 'Win32 clients.\n'
		+ 'Normally, default font style and size is used, '
		+ 'according to the active theme.\n'
		+ 'Set to true if wxWidgets or Win32 clients should use '
		+ 'a fixed width font.',
		'Typecast'   : GTypecast.boolean,
		'Default'    : False },

	{ 'Name'       : 'pointSize',
		'Type'       : 'Setting',
		'Comment'    : 'If fixedWidthFont is set to true, then this is the '
		+ 'point size used for fonts.',
		'Description': 'If fixedWidthFont is set to true, then this is the '
		+ 'point size used for fonts.',
		'Typecast'   : GTypecast.whole,
		'Default'    : 0 },

	{ 'Name'       : 'faceName',
		'Type'       : 'Setting',
		'Comment'    : 'If fixedWidthFont is set to true, then this is '
		+ 'the face name used for fonts.',
		'Description': 'If fixedWidthFont is set to true, then this is '
		+ 'the face name used for fonts.',
		'Typecast'   : GTypecast.text,
		'Default'    : '' },

	{ 'Name'       : 'focusColor',
		'Type'       : 'Setting',
		'Comment'    : 'The color of a highlighted (ie focused) widget.',
		'Description': 'The color of a highlighted (ie focused) widget. '
		+ 'Leave empty if you don\'t want highlight. '
		+ 'Format is: "RRGGBB", each digit being hexadecimal.',
		'Typecast'   : GTypecast.text,
		'Default'    : '' },

	{ 'Name'       : 'DropdownSeparator',
		'Type'       : 'Setting',
		'Comment'    : 'Text used to concatenation dropdown descriptions',
		'Description': 'Text used to concatenation dropdown descriptions '
		+ '(when multiple description fields are used)',
		'Typecast'   : GTypecast.text,
		'Default'    : ', ' },

	{ 'Name'       : 'IconSet',
		'Type'       : 'Setting',
		'Comment'    : 'The default icon set.',
		'Description': 'The default icon set.',
		'Typecast'   : GTypecast.text,
		'Default'    : 'auto' },

	{ 'Name'       : 'AsteriskWildcard',
		'Type'       : 'Setting',
		'Comment'    : 'Use asterisk (*) for wildcards in addition to percent (%)',
		'Description': 'Use asterisk (*) for wildcards in addition to percent (%)',
		'Typecast'   : GTypecast.boolean,
		'Default'    : True },

	{ 'Name'       : 'fake_ascii_query',
		'Type'       : 'Setting',
		'Comment'    : 'Change all non-ASCII-characters in a query into a "_"',
		'Description': 'Change all non-ASCII-characters in a query into a "_"',
		'Typecast'   : GTypecast.boolean,
		'Default'    : False },

	{ 'Name'       : 'htmlui_include_path',
		'Type'       : 'Setting',
		'Comment'    : 'Set path for include files for HTML UI driver for GNUe Forms',
		'Description': 'Set path for include files for HTML UI driver for GNUe Forms',
		'Typecast'   : GTypecast.text,
		'Default'    : 'Z:X:' },
)
