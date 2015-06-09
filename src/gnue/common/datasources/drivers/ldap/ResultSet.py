# GNU Enterprise Common Library - Generic DBSIG2 database driver - Result set
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
# $Id: ResultSet.py,v 1.3 2008/11/04 20:14:03 oleg Exp $

"""
Generic ResultSet class for DBSIG2 based database driver plugins.
"""

__all__ = ['ResultSet']

from gnue.common.apps import errors
from gnue.common.datasources.drivers import Base
import ldap


def _internalize(value):
	if isinstance(value, str):
		value = value.decode('UTF-8')
	return value

# =============================================================================
# ResultSet class
# =============================================================================

class ResultSet (Base.ResultSet):
	"""
	Generic ResultSet class for SQL based backends using a DBSIG2 compatible
	Python module.
	"""

	# ---------------------------------------------------------------------------
	# Execute query for object type datasources
	# ---------------------------------------------------------------------------

	def _query_object_ (self, connection, table, fieldnames, condition, sortorder, distinct, parameters = None):
		print '_query_object_:\n\ttable %s\n\tfieldnames %s\n\tcondition %s\n\tsortorder %s\n\tdistinct %s\n\tparameters %s' % (table, fieldnames, condition, sortorder, distinct, parameters)
		connection._ldapObject
		#raise NotImplementedError
		self.__fieldnames = fieldnames
		self.__data = [i for i in connection._ldapObject.search_s(
				table,
				ldap.SCOPE_SUBTREE,
				'(&(objectClass=person)(!(objectClass=computer)))',
				map(str, fieldnames),
			) if i[0] is not None]

		for i in sortorder:
			self.__data.sort(self.__sorter(**i))


	def __sorter(self, name=None, descending=False, ignorecase=False):
		if descending:
			return lambda a, b: cmp(b[1].get(str(name)), a[1].get(str(name)))
		else:
			return lambda a, b: cmp(a[1].get(str(name)), b[1].get(str(name)))


	# ---------------------------------------------------------------------------
	# Execute query for SQL type datasources
	# ---------------------------------------------------------------------------

	def _query_sql_ (self, connection, sql):
		raise NotImplementedError


	# ---------------------------------------------------------------------------
	# Return result count
	# ---------------------------------------------------------------------------

	def _count_ (self):
		return len(self.__data)


	# ---------------------------------------------------------------------------
	# Yield data of next record
	# ---------------------------------------------------------------------------

	def _fetch_ (self, cachesize):
		for key, row in self.__data:
			result = {}
			for fn in self.__fieldnames:
				value = row.get(fn)
				if isinstance(value, list):
					value = u', '.join(map(unicode, map(_internalize, value)))
				else:
					value = _internalize(value)
				result[fn] = value
			yield result


	# ---------------------------------------------------------------------------
	# Close cursor
	# ---------------------------------------------------------------------------

	def _close_ (self):
		raise NotImplementedError
