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
# Copyright 2000-2007 Free Software Foundation
#
# FILE:
#
# DESCRIPTION:
"""
"""

from src.gnue.forms.input.displayHandlers.datehandler import Date, Time, DateTime
from src.gnue.forms.input.displayHandlers import Image, Text, Numeric, Dropdown, Listbox, Password, Component, Boolean, \
	Array

_classConstructors = {
	'boolean'  : Boolean,
	'date'     : Date,
	'time'     : Time,
	'datetime' : DateTime,
	'dropdown' : Dropdown,
	'listbox'  : Listbox,
	'password' : Password,
	'number'   : Numeric,
	'array'    : Array,
}

def factory(entry, eventHandler, subEventHandler, displayMask, inputMask, datatype=None):
	"""
	Function to act as a display handler factory.

	@returns: An instance of a display handler that is appropriate for the entry
	            type passed in.
	"""
	if entry._type == 'GFImage':
		# Only import the Image handler if used in the form
		key = 'image'
		if key not in _classConstructors:
			_classConstructors[key] = Image

	elif entry._field.isLookup():
		key = 'dropdown'

	elif (datatype or entry._field.datatype) in ['date', 'time', 'datetime', 'number', 'boolean', 'array']:
		key = datatype or entry._field.datatype

	else:
		key = entry.style

	assert gDebug(6, "Creating display handler for entry key %s" % key)

	#rint "Creating display handler for entry key %s" % key

	return _classConstructors.get(key, Text)(
		entry,
		eventHandler,
		subEventHandler,
		displayMask,
		inputMask
	)
