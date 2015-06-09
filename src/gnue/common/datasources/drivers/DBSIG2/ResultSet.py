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
# $Id: ResultSet.py 9550 2007-05-05 17:59:06Z johannes $

"""
Generic ResultSet class for DBSIG2 based database driver plugins.
"""

__all__ = ['ResultSet']

from gnue.common.apps import errors
from gnue.common.datasources.drivers import Base


# =============================================================================
# Exceptions
# =============================================================================

class InvalidRowCountError (errors.SystemError):
	"""
	DBSIG2 module returned invalid row count. Probably _broken_rowcount_ should
	be set in this driver.
	"""

	def __init__ (self, drivername, value):
		msg = u_("The driver '%(driver)s' returned an invalid row " \
				"count '%(count)s'") \
			% {'driver': drivername, 'count': value}
		errors.SystemError.__init__ (self, msg)


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

	def _query_object_ (self, connection, table, fieldnames, condition,
		sortorder, distinct, parameters = None):

		params = parameters or {}
		what = ', '.join(fieldnames) or 'null'
		if distinct:
			what = 'DISTINCT ' + what
		where = condition.asSQL (params)

		# If the connection has a broken row count, query for the number of records
		# first. This avoids conflicts with some drivers not supporting multiple
		# open cursors (like adodbapi).
		if connection._broken_rowcount_:
			if distinct:
				self.__count = 0
			else:
				query = self.__buildQueryCount (table, where)
				self.__count = connection.sql1 (query, params)

		query = self.__buildQuery (table, what, where, sortorder)

		self.__cursor = connection.makecursor (query, params)

		if not connection._broken_rowcount_:
			self.__count = self.__cursor.rowcount

		# If the driver has a broken rowcount, but does not report it as broken,
		# protect clients from behaving very strange
		if self.__count is None or self.__count < 0:
			raise InvalidRowCountError, (connection._drivername_, self.__count)

		self.__connection = connection
		self.__fieldnames = fieldnames


	# ---------------------------------------------------------------------------
	# Build the query string
	# ---------------------------------------------------------------------------

	def __buildQuery (self, table, what, where, sortorder):
		assert what

		query = 'SELECT ' + what + ' FROM ' + table

		if where:
			query += ' WHERE ' + where

		if sortorder:
			order = []
			for item in sortorder:
				field      = item ['name']
				descending = item.get ('descending') or False
				ignorecase = item.get ('ignorecase') or False

				fmt = ignorecase and "UPPER(%s)%s" or "%s%s"
				order.append (fmt % (field, descending and ' DESC' or ''))

			query += ' ORDER BY ' + ', '.join (order)

		return query


	# ---------------------------------------------------------------------------
	# Build the query string for the count
	# ---------------------------------------------------------------------------

	def __buildQueryCount (self, table, where):

		query = 'SELECT COUNT (*) FROM ' + table

		if where:
			query += ' WHERE ' + where

		return query


	# ---------------------------------------------------------------------------
	# Execute query for SQL type datasources
	# ---------------------------------------------------------------------------

	def _query_sql_ (self, connection, sql):

		self.__cursor = connection.makecursor (sql)

		if connection._broken_rowcount_:
			self.__count = 0                  # No chance to find it out
		else:
			self.__count = self.__cursor.rowcount

		self.__connection = connection

		# get field names from cursor description
		self.__fieldnames = [(unicode (d [0], connection._encoding)).lower () \
				for d in self.__cursor.description]


	# ---------------------------------------------------------------------------
	# Return result count
	# ---------------------------------------------------------------------------

	def _count_ (self):

		return self.__count


	# ---------------------------------------------------------------------------
	# Yield data of next record
	# ---------------------------------------------------------------------------

	def _fetch_ (self, cachesize):

		while True:

			# fetch next records from the backend
			if self.__connection._must_fetchall_:
				rows = self.__cursor.fetchall ()
			elif self.__connection._broken_fetchmany_:
				try:
					rows = self.__cursor.fetchmany (cachesize)
				except:
					break
			else:
				rows = self.__cursor.fetchmany (cachesize)

			# did we receive any?
			if not rows:
				break

			# convert String to Unicode and yield a dictionary
			for row in rows:
				result = {}
				for (fieldname, value) in zip (self.__fieldnames, row):
					if isinstance (value, str):
						value = unicode (value, self.__connection._encoding)
					result [fieldname] = value
				yield result


	# ---------------------------------------------------------------------------
	# Close cursor
	# ---------------------------------------------------------------------------

	def _close_ (self):

		self.__cursor.close ()
