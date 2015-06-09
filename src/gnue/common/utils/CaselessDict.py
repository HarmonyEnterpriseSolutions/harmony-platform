# GNU Enterprise Common - Utilities - Caseinsensitive Dictionary
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
# $Id: CaselessDict.py 9222 2007-01-08 13:02:49Z johannes $

import operator
import sys


# =============================================================================
# Class implementing a dictionary with case-insenitive keys
# =============================================================================

class CaselessDict:
	"""
	This class is a wrapper around a dictionary, where all keys are treated lower
	case (where applicable). If a 'notFoundError' exception is passed in the
	classes' constructor this exception will be raised on access to a
	non-existing key. The first argument of the exception is the key, followed by
	all arguments described by 'exceptionArgs' of the constructor.
	"""

	# ---------------------------------------------------------------------------
	# Create a new instance of the dictionary
	# ---------------------------------------------------------------------------

	def __init__ (self, notFoundError = None, *exceptionArgs):
		"""
		@param notFoundError: exception raised instead of a KeyError
		@param exceptionArgs: arguments for the notFoundError exception
		"""

		self._items = {}
		self.__notFoundError = notFoundError
		self.__exceptionArgs = exceptionArgs

	# ---------------------------------------------------------------------------
	# Return all keys of the dictionary
	# ---------------------------------------------------------------------------

	def keys (self):
		"""
		@return: sequence with all keys of the dictionary
		"""

		return self._items.keys ()


	# ---------------------------------------------------------------------------
	# Return all values of the dictionary
	# ---------------------------------------------------------------------------

	def values (self):
		"""
		@return: sequence with all values of the dictionary
		"""

		return self._items.values ()


	# ---------------------------------------------------------------------------
	# Return a sequence of all key-value pairs
	# ---------------------------------------------------------------------------

	def items (self):
		"""
		@return: sequence with all key-value pairs of the dictionary
		"""

		return self._items.items ()


	# ---------------------------------------------------------------------------
	# Check if a given key exists in the dictionary
	# ---------------------------------------------------------------------------

	def has_key (self, key):
		"""
		This function returns True if a given key exists in the dictionary, False
		otherwise.

		@param key: key to be looked for
		@return: True if key is in the dictionary, False otherwise
		"""

		dkey = hasattr (key, 'lower') and key.lower () or key
		return self._items.has_key (dkey)


	# ---------------------------------------------------------------------------
	# Return the number of elements in the dictionary
	# ---------------------------------------------------------------------------

	def __len__ (self):
		"""
		@return: number of items in the dictionary
		"""

		return len (self._items)


	# ---------------------------------------------------------------------------
	# Return the item with the given key
	# ---------------------------------------------------------------------------

	def __getitem__ (self, key):
		"""
		This function returns the item of the dictionary with the given key. If no
		such key exists, a 'notFoundError' or a KeyError will be raised.

		@param key: the key to look for
		@return: the dictionary element with the given key
		"""

		dkey = hasattr (key, 'lower') and key.lower () or key

		try:
			return self._items [dkey]

		except KeyError:
			if self.__notFoundError is not None:
				raise self.__notFoundError, tuple ([dkey] + list (self.__exceptionArgs))

			else:
				raise


	# ---------------------------------------------------------------------------
	# Set the value of a dictionary element
	# ---------------------------------------------------------------------------

	def __setitem__ (self, key, value):
		"""
		This function sets or adds a key with a given value to the dictionary.

		@param key: key to be set
		@param value: the value to be set for the key
		"""

		dkey = hasattr (key, 'lower') and key.lower () or key
		self._items [dkey] = value


	# ---------------------------------------------------------------------------
	# Remove a given element from the dictionary
	# ---------------------------------------------------------------------------

	def __delitem__ (self, key):
		"""
		This function removes a given element from the dictionary.

		@param key: the key of the element to be removed
		"""

		dkey = hasattr (key, 'lower') and key.lower () or key

		try:
			del self._items [dkey]

		except KeyError:

			if self.__notFoundError is not None:
				raise self.__notFoundError, tuple ([dkey] + list (self.__exceptionArgs))

			else:
				raise


	# ---------------------------------------------------------------------------
	# Return a string representation of the wrapped dictionary
	# ---------------------------------------------------------------------------

	def __repr__ (self):
		"""
		This function returns a string representation of the dictionary
		@return: the wrapped dictionary as string
		"""

		return repr (self._items)


	# ---------------------------------------------------------------------------
	# Clear the dictionary
	# ---------------------------------------------------------------------------

	def clear (self):
		"""
		This function clears the wrapped dictionary.
		"""

		self._items.clear ()


	# ---------------------------------------------------------------------------
	# Update the wrapped dictionary
	# ---------------------------------------------------------------------------

	def update (self, data):
		"""
		This function updates the wrapped dictionary with the given dictionary

		@param data: dictionary to update from
		"""

		for (key, value) in data.items ():
			self.__setitem__ (key, value)


	# ---------------------------------------------------------------------------
	# Get a given key from the dictionary, optionally setting a default value
	# ---------------------------------------------------------------------------

	def setdefault (self, key, default = None):
		"""
		This function returns the current value of the given key. If the dictionary
		has no such key, it will be added using the given default value.

		@param key: the key to return the value from
		@param default: value to set for the key if it's not available in the
		    dictionary already

		@return: current value of the given key
		"""

		if hasattr (key, 'lower'):
			key = key.lower ()

		return self._items.setdefault (key, default)


	# ---------------------------------------------------------------------------
	# Get an item from the dictionary
	# ---------------------------------------------------------------------------

	def get (self, key, default = None):

		return self._items.get (key.lower (), default)


	# ---------------------------------------------------------------------------
	# Return the value of a key or a default and remove it
	# ---------------------------------------------------------------------------

	def pop (self, key, *default):
		"""
		This function returns the value for a given key and if it exists removes it
		from the dictionary. If the key does not exist and a default is given, this
		default will be returned. If no default is given a KeyError or a
		notFoundError will be raised.

		@param key: the key to return the value for (will be removed afterwards)
		@param default: default value to return if the key does not exist

		@return: value for key or default (if given)
		"""

		key = hasattr (key, 'lower') and key.lower () or key

		try:
			return self._items.pop (key, *default)

		except KeyError:
			if self.__notFoundError is not None:
				raise self.__notFoundError, tuple ([key] + list (self.__exceptionArgs))

			else:
				raise


	# ---------------------------------------------------------------------------
	# remove and return an arbitrary (key, value) pair
	# ---------------------------------------------------------------------------

	def popitem (self):
		"""
		This function returns an arbitrary (key, value) pair and removes it from
		the dictionary. This is useful to destructively iterate over the
		dictionary. If called on an empty dictionary a KeyError will be raised.

		@return: arbitrary (key, value) pair
		"""

		return self._items.popitem ()


	# ---------------------------------------------------------------------------
	# Create a new dictionary having a given set of keys with an optional value
	# ---------------------------------------------------------------------------

	def fromkeys (self, keys, value = None):
		"""
		This function is a class method taht returns a new dictionary, having all
		keys listed in the given sequence. If a value is given, all keys will have
		this value.

		@param keys: sequence of keys of the new dictionary
		@param value: value of all keys in the new dictionary

		@return: new dictionary wrapper instance with the same notFoundError
		"""

		result = CaselessDict (self.__notFoundError, *self.__exceptionArgs)
		# Using a map statement here looks a bit freaky, but it's much faster than
		# using a simple for-loop iterating over all keys
		map (operator.setitem, [result] * len (keys), keys, [value] * len (keys))

		return result


	# ---------------------------------------------------------------------------
	# Return an iterator over (key, value) pairs
	# ---------------------------------------------------------------------------

	def iteritems (self):
		"""
		This function returns an iterator over (key, value) pairs. If Python
		version is below 2.2 this function raises a NotImplementedError.

		@return: iterator object for (key, value) pairs
		"""

		if sys.version_info [:2] >= (2, 2):
			return self._items.iteritems ()

		else:
			raise NotImplementedError


	# ---------------------------------------------------------------------------
	# Return an iterator over the mapping's keys
	# ---------------------------------------------------------------------------

	def iterkeys (self):
		"""
		This function returns an iterator over the mapping's keys. If Python
		version is below 2.2 this function raises a NotImplementedError.

		@return: iterator object for keys
		"""

		if sys.version_info [:2] >= (2, 2):
			return self._items.iterkeys ()

		else:
			raise NotImplementedError


	# ---------------------------------------------------------------------------
	# Return an iterator over the mapping's values
	# ---------------------------------------------------------------------------

	def itervalues (self):
		"""
		This function returns an iterator over the mapping's values. If Python
		version is below 2.2 this function raises a NotImplementedError.

		@return: iterator object for values
		"""

		if sys.version_info [:2] >= (2, 2):
			return self._items.itervalues ()

		else:
			raise NotImplementedError
