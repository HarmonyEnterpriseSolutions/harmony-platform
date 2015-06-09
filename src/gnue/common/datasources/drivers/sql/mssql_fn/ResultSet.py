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
# $Id: ResultSet.py,v 1.16 2013/03/22 12:42:42 oleg Exp $

"""

"""

__all__ = ['ResultSet']

from gnue.common.datasources.drivers import DBSIG2
from itertools import izip
from gnue.common.apps import errors

# =============================================================================
# Exceptions
# =============================================================================

class ColumnNotFoundError(errors.SystemError):
	"""
	field with specified name not found in query resultset
	"""
	pass


def safe_cmp(v1, v2):
	"""
	fixed TypeError: can't compare datetime.date to NoneType
	"""
	if v1 is None and v2 is not None:
		return -1
	elif v2 is None and v1 is not None:
		return 1
	else:
		return cmp(v1, v2)


def sorter(name=None, descending=False, ignorecase=False):

	def compare(record1, record2):

		v1 = record1[name]
		v2 = record2[name]

		if ignorecase:
			v1 = v1.upper()
			v2 = v2.upper()

		if descending:
			return safe_cmp(v2, v1)
		else:
			return safe_cmp(v1, v2)

	return compare


def sorter_chain(compares):

	def compare(record1, record2):
		for cmp in compares:
			res = cmp(record1, record2)
			if res:
				return res
		return 0

	return compare


# =============================================================================
# ResultSet class
# =============================================================================

class ResultSet(DBSIG2.ResultSet):

	def _query_object_ (self, connection, table, fieldnames, condition, sortorder, distinct, parameters):
		"""
		WARNING: assesses superclass private variables as class names are equal
		"""

#		print "--------------------------------"
#		print """>>> _query_object_
#	table      = %s
#	fieldnames = %s
#	sortorder  = %s
#	distinct   = %s
#	parameters = %s
#""" % (table, fieldnames, sortorder, distinct, parameters)
#		if condition:
#			condition.showTree()

		and_ = condition.findChildOfType('GCand', False)
		if and_:
			for eq in and_.findChildrenOfType('GCeq', False):
				field = eq.findChildOfType('GCCField', False)
				const = eq.findChildOfType('GCCConst', False)
				if field and const:
					parameters[field.name] = const.value

		if hasattr(connection, 'getFnSignatureFactory'):
			query, parameters = connection.getFnSignatureFactory()[table]['list'].genSql(parameters)
		else:	
			# support old pymmsql driver
			query = "EXEC %s %s" % (table, ', '.join(['@%s=%%(%s)s' % (key, key) for key in parameters]))

		#query = "EXEC %s %s" % (table, ', '.join(['@%s=%%(%s)s' % (key, key) for key in parameters]))

		self.__connection = connection
		self.__fieldnames = fieldnames
		self.__cursor = connection.makecursor(query, parameters)
		self.__condition = condition

		if self.__connection._broken_rowcount_:
			self.__count = -1
		else:
			self.__count = self.__cursor.rowcount

		self.__sortorder = sortorder


	# ---------------------------------------------------------------------------
	# Yield data of next record
	# ---------------------------------------------------------------------------

	def __fetchByDescription(self, cachesize):
		#if self.__cursor.description is None:
		#	raise RuntimeError, 'Cursor has no description. ODBC can\'t accept multiple resultsets. If there is INSERT in procedure, have you "SET NOCOUNT ON;"?'

		if self.__cursor.description is not None:
			order = [i[0].decode(self.__connection._encoding) for i in self.__cursor.description]
		else:
			order = []

		unknown = set(self.__fieldnames).difference(order)
		if unknown:
			unknown = list(unknown)
			unknown.sort()
			raise ColumnNotFoundError, 'Column(s) not found: [%s]. Available columns: [%s]' % (', '.join(unknown), ', '.join(order))
			
		fieldIndex = [order.index(fieldname) for fieldname in self.__fieldnames]

		if self.__connection._must_fetchall_:
			if self.__cursor.description:
				rows = self.__cursor.fetchall()
			else:
				# executed something without rows
				rows = []
			self.__cursor.close()
			self.__cursor = None
		else:
			rows = self.__cursor.fetchmany(cachesize)

		while rows:
			# convert String to Unicode and yield a dictionary
			for row in rows:
				result = {}
				for i, fieldname in izip(fieldIndex, self.__fieldnames):
					value = row[i]
					if isinstance(value, str):
						value = unicode(value, self.__connection._encoding)
					result [fieldname] = value
				yield result

			if self.__connection._must_fetchall_:
				rows = ()
			else:
				rows = self.__cursor.fetchmany(cachesize)


	def _fetch_ (self, cachesize):

		g = self.__fetchByDescription(cachesize)

		if self.__connection._broken_rowcount_:
			g = list(g)
			self.__count = len(g)

		# software sort
		if self.__sortorder:
			if not isinstance(g, list):
				g = list(g)

			compares = [sorter(**sortParams) for sortParams in self.__sortorder]

			if len(compares) == 1:
				compare = compares[0]
			else:
				compare = sorter_chain(compares)

			for sortParams in self.__sortorder:
				g.sort(compare)

		if self.__condition:
			g = [row for row in g if self.__condition.evaluate(row)]
			# update row count
			self.__count = len(g)

		if isinstance(g, list):
			g = iter(g)
		
		return g

	# ---------------------------------------------------------------------------
	# Return result count
	# ---------------------------------------------------------------------------

	def _count_(self):
		return self.__count

	def _close_(self):
		if self.__cursor is not None:
			self.__cursor.close()


if __name__ == '__main__':
	import datetime
	l = [datetime.date.today(), None, datetime.date.today() + datetime.timedelta(-1), None]
	print l
	l.sort(safe_cmp)
	print l
