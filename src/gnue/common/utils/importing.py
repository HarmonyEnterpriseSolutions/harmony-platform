# GNU Enterprise Common - Utilities - Importing
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
# $Id: importing.py 9404 2007-02-23 01:29:03Z jcater $
#
"""
This module implements a dynamic module importer.
"""

import sys


__all__ = ['import_string']

# ===================================================================
# Dynamically import a python module
# ===================================================================
_global_dict = globals()
def import_string(name):
	"""
	Import a module/item using a string name.

	This is adapted from PEAK's peak.utils.importString, licensed
	under the Python license.
	"""
	parts = filter(None,name.split('.'))
	item = __import__(parts.pop(0), _global_dict, _global_dict, ['__name__'])

	# Fast path for the common case, where everything is imported already
	for attr in parts:
		try:
			item = getattr(item, attr)
		except AttributeError:
			break   # either there's an error, or something needs importing
	else:
		return item

	# We couldn't get there with just getattrs from the base import.  So now
	# we loop *backwards* trying to import longer names, then shorter, until
	# we find the longest possible name that can be handled with __import__,
	# then loop forward again with getattr.  This lets us give more meaningful
	# error messages than if we only went forwards.
	attrs = []
	exc = None

	try:
		while True:
			try:
				# Exit as soon as we find a prefix of the original `name`
				# that's an importable *module* or package
				item = __import__(name, _global_dict, _global_dict, ['__name__'])
				break
			except ImportError:
				if not exc:
					# Save the first ImportError, as it's usually the most
					# informative, especially w/Python < 2.4
					exc = sys.exc_info()

				if '.' not in name:
					# We've backed up all the way to the beginning, so reraise
					# the first ImportError we got
					raise exc[0],exc[1],exc[2]

				# Otherwise back up one position and try again
				parts = name.split('.')
				attrs.append(parts[-1])
				name = '.'.join(parts[:-1])
	finally:
		exc = None

	# Okay, the module object is now in 'item', so we can just loop forward
	# to retrieving the desired attribute.
	#
	while attrs:
		attr = attrs.pop()
		try:
			item = getattr(item,attr)
		except AttributeError:
			raise ImportError("%r has no %r attribute" % (item,attr))

	return item
