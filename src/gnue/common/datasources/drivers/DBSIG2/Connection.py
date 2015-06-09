# GNU Enterprise Common Library - Generic DBSIG2 database driver - Connection
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
# $Id: Connection.py,v 1.31 2012/08/09 11:16:48 oleg Exp $

"""
Generic Connection class for DBSIG2 based database driver plugins.
"""
from src.gnue.common.datasources.drivers.DBSIG2 import ResultSet

__all__ = ['Connection']

import sys
import datetime
import decimal
import time

from gnue.common.datasources import Exceptions
from gnue.common.datasources.drivers import Base


# =============================================================================
# Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Generic Connection class for SQL based backends using a DBSIG2 compatible
	Python module.

	Driver plugins derived from this driver must subclass this class and
	overwrite at least the L{_drivername_} class variable and implement the
	L{_getConnectParams_} method.

	@cvar _drivername_: The Python module name of the DBSIG2 driver. Must be
	  overwritten by descendants.
	@cvar _boolean_false_: Value to post to the database for boolean FALSE
	  (defaults to False). Can be overwritten by descendants.
	@cvar _boolean_true_: Value to post to the database for boolean TRUE
	  (defaults to True). Can be overwritten by descendants.
	@cvar _broken_fetchmany_: Can be set to True by descendants if the DBSIG2
	  module raises an exception if fetchmany() is called when no records are
	  left.
	@cvar _broken_rowcount_: Can be set to True by descendants if the DBSIG2
	  module does not return a correct value for cursor.rowcount.
	@cvar _named_as_sequence_: If paramstyle = 'named' pass parameters as
	  sequence (True) or as mapping (False). Can be overwritten by descendants.
	@cvar _std_datetime_: If True, the driver will use python's (2.3+) datetime
	  types for time and timestamp values. If so, the constructors Timestamp and
	  Time will be called with an extra argument for microseconds.
	"""

	_resultSetClass_    = ResultSet

	_drivername_        = None            # DBSIG2 compatible driver module
	_boolean_false_     = False           # value to pass for boolean FALSE
	_boolean_true_      = True            # value to pass for boolean TRUE
	_broken_fetchmany_  = False           # Does fetchmany () raise an exception
	# when no records are left?
	_broken_rowcount_   = False           # Is cursor.rowcount unusable?
	_must_fetchall_     = False           # Do we have to use fetchall () instead
	# of fetchmany () because the open
	# cursor will not survive a commit?
	_named_as_sequence_ = False           # Pass 'named' parameters as sequence
	_std_datetime_      = False


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections, name, parameters):

		Base.Connection.__init__ (self, connections, name, parameters)

		self._driver = __import__ (self._drivername_, None, None, '*')

		# Encoding used to communicate with the database (not used by all drivers)
		if parameters.has_key ('encoding'):
			self._encoding = parameters ['encoding']
		else:
			self._encoding = 'utf-8'

		self._native = None


	# ---------------------------------------------------------------------------
	# Implementations of virtual methods
	# ---------------------------------------------------------------------------

	def _getLoginFields_ (self):
		return [(u_('User Name'), '_username', 'string', None, None, []),
			(u_('Password'), '_password', 'password', None, None, [])]

	# ---------------------------------------------------------------------------

	def _connect_ (self, connectData):
		(params, kwargs) = self._getConnectParams_ (connectData)
		assert gDebug (3, 'DBSIG2 Connect')
		try:
			self._native = self._driver.connect (*params, **kwargs)
		except self._driver.DatabaseError:
			raise self.decorateError(
				Exceptions.LoginError(self._getExceptionMessage())
			)

	# ---------------------------------------------------------------------------

	def _insert_ (self, table, newfields):
		fields = []
		values = []
		parameters = {}
		for (field, value) in newfields.items ():
			key = 'new_' + field
			fields.append (field)
			values.append ('%%(%s)s' % key)
			parameters [key] = value
		statement = "INSERT INTO %s (%s) VALUES (%s)" % (table, ', '.join (fields),
			', '.join (values))
		return self.sql0 (statement, parameters)

	# ---------------------------------------------------------------------------

	def _update_ (self, table, oldfields, newfields):
		(where, parameters) = self.__where (oldfields)
		updates = []
		for (field, value) in newfields.items ():
			key = 'new_' + field
			updates.append ("%s=%%(%s)s" % (field, key))
			parameters [key] = value
		statement = "UPDATE %s SET %s WHERE %s" % (table, ', '.join (updates),
			where)
		self.sql0 (statement, parameters)

	# ---------------------------------------------------------------------------

	def _delete_ (self, table, oldfields):
		(where, parameters) = self.__where (oldfields)
		statement = 'DELETE FROM %s WHERE %s' % (table, where)
		self.sql0 (statement, parameters)

	# ---------------------------------------------------------------------------

	def _requery_ (self, table, oldfields, fields, parameters):
		(where, parameters) = self.__where (oldfields, parameters)
		statement = "SELECT %s FROM %s WHERE %s" % (', '.join (fields), table,
			where)
		rows = self.sql (statement, parameters)
		if len (rows):
			row = rows [0]
			result = {}
			for i in range (len (fields)):
				if isinstance (row [i], str):
					result [fields [i]] = unicode (row [i], self._encoding)
				else:
					result [fields [i]] = row [i]
			return result
		else:
			raise Exceptions.RecordNotFoundError

	# ---------------------------------------------------------------------------

	def _commit_ (self):
		assert gDebug (3, 'DBSIG2 Commit')
		while True:
			try:
				self._native.commit ()
			except self._driver.DatabaseError:
				error = self.decorateError(
					Exceptions.ConnectionError(self._getExceptionMessage(), 'COMMIT', None)
				)
				if error is None:
					continue # retry
				else:
					raise error
			else:
				break

	# ---------------------------------------------------------------------------

	def _rollback_ (self):
		assert gDebug (3, 'DBSIG2 Rollback')
		if hasattr (self._native, 'rollback'):
			self._native.rollback ()

	# ---------------------------------------------------------------------------

	def _close_ (self):
		assert gDebug (3, 'DBSIG2 Close')
		if self._native:
			self._native.close ()


	# ---------------------------------------------------------------------------
	# Build WHERE-Clause based on a dictionary of fieldname/value pairs
	# ---------------------------------------------------------------------------

	def __where (self, oldfields, parameters=None):

		where = []
		if parameters is None:
			parameters = {}
		for (field, value) in oldfields.items ():
			if value is None:
				where.append ("%s IS NULL" % field)
			else:
				key = 'old_' + field
				where.append ("%s=%%(%s)s" % (field, key))
				parameters [key] = value

		return (' AND '.join (where), parameters)


	# ---------------------------------------------------------------------------
	# Execute the given SQL statement and return the result matrix
	# ---------------------------------------------------------------------------

	def sql (self, statement, parameters = None):
		"""
		Execute the given SQL statement and return the result matrix.

		@param statement: The SQL statement as either 8-bit or unicode string. Can
		  contain %(name)s style placeholders for parameters.
		@param parameters: A dictionary with the parameter values. The values of
		  the dictionary can be 8-bit strings, unicode strings, integer or floating
		  point numbers, booleans or datetime values.
		@return: A 2-dimensional matrix holding the complete result of the query.
		"""

		cursor = self.makecursor (statement, parameters)
		try:
			result = cursor.fetchall ()
		finally:
			cursor.close ()
		return result


	# ---------------------------------------------------------------------------
	# Execute the given SQL statement that is expected to return a single value
	# ---------------------------------------------------------------------------

	def sql1 (self, statement, parameters = None):
		"""
		Execute the given SQL statement that is expected to return a single value.

		If the query returns nothing, None is returned.

		@param statement: The SQL statement as either 8-bit or unicode string. Can
		  contain %(name)s style placeholders for parameters.
		@param parameters: A dictionary with the parameter values. The values of
		  the dictionary can be 8-bit strings, unicode strings, integer or floating
		  point numbers, booleans or datetime values.
		@return: The value returned by the query. If the query returns more than a
		  single value, the first column of the first row is returned.
		"""

		cursor = self.makecursor (statement, parameters)
		try:
			result = cursor.fetchone()
		finally:
			cursor.close()
		
		if result is None:
			raise RuntimeError, "Expecting one record, have none"

		value = result[0]
		
		if isinstance(value, str):
		    value = value.decode(self._encoding)

		return value


	# ---------------------------------------------------------------------------
	# Execute the given SQL statement that is expected to return nothing
	# ---------------------------------------------------------------------------

	def sql0 (self, statement, parameters = None):
		"""
		Execute the given SQL statement and return the rowid of the affected row
		(in case the statement was an insert).

		@param statement: The SQL statement as either 8-bit or unicode string. Can
		  contain %(name)s style placeholders for parameters.
		@param parameters: A dictionary with the parameter values. The values of
		  the dictionary can be 8-bit strings, unicode strings, integer or floating
		  point numbers, booleans or datetime values.
		@return: For INSERT statements, the rowid of the newly inserted record, if
		  the database supports rowids and the DBSIG2 module supports the
		  cursor.lastrowid extension, and None otherwise. For other statements,
		  undefined.
		"""

		cursor = self.makecursor (statement, parameters)
		if hasattr (cursor, 'lastrowid'):
			result = cursor.lastrowid
		else:
			result = None
		cursor.close ()
		return result


	# ---------------------------------------------------------------------------
	# Create a new DBSIG2 cursor object and execute the given SQL statement
	# ---------------------------------------------------------------------------

	def makecursor (self, statement, parameters = None):
		"""
		Create a new DBSIG2 cursor object and execute the given SQL statement.

		@param statement: The SQL statement as either 8-bit or unicode string. Can
		  contain %(name)s style placeholders for parameters.
		@param parameters: A dictionary with the parameter values. The values of
		  the dictionary can be 8-bit strings, unicode strings, integer or floating
		  point numbers, booleans or datetime values.
		@return: A DBSIG2 cursor object holding the result of the query.
		"""
		assert gDebug('sql', statement % dict(((k, pythonConstToSql(v)) for k, v in (parameters or {}).iteritems())))

		checktype (statement, basestring)
		checktype (parameters, [dict, None])

		if parameters:
			for (parameters_key, parameters_value) in parameters.items ():
				checktype (parameters_key, basestring)
		# checktype (parameters_value, .....) -- too many valid types :-)

		# Convert to encoded string for database
		if isinstance (statement, unicode):
			s = statement.encode (self._encoding)
		else:
			s = statement

		if parameters:
			assert gDebug('sql', "query parameters:\n" + '\n'.join(("\t%-24s = %s" % (k, pythonConstToSql(parameters[k])) for k in sorted(parameters.keys()))))

			# convert parameter dictionary to encoded strings
			p = {}
			for (key, value) in parameters.items ():
				if isinstance (key, unicode):
					k = key.encode (self._encoding)
				else:
					k = key
				p [k] = self.make_parameter (value)

			# assert gDebug('sql', "ENCODED query parameters:\n" + '\n'.join(("\t%-24s = %s (%s)" % (k, repr(p[k]), type(p[k])) for k in sorted(p.keys()))))

			# Convert parameters into correct style
			paramstyle = self._driver.paramstyle
			if paramstyle != 'pyformat':
				(s, p) = getattr (self, '_Connection__param_' + paramstyle) (s, p)

		else:
			p = None

		assert gDebug (3, "DBSIG2 Statement: %s" % s)
		assert gDebug (3, "DBSIG2 Parameters: %s" % p)

		t = time.time()

		while True:
			# Create DBSIG2 cursor and execute statement
			cursor = self._native.cursor ()
			try:
				if p is not None:
					cursor.execute (s, p)
				else:
					cursor.execute (s)
			except self._driver.DatabaseError:
				error = self.decorateError(Exceptions.ConnectionError(self._getExceptionMessage(), statement, parameters))
				if error is None:
					continue # retry
				else:
					try:
						raise error
					finally:
						try:
							cursor.close()
						except Exception, e:
							print "* Have DatabaseError, failed to close cursor: %s: %s" % (e.__class__.__name__, e)
			except:
				try:
					raise
				finally:
					try:
						cursor.close()
					except Exception, e:
						print "* Have error, failed to close cursor: %s: %s" % (e.__class__.__name__, e)
			else:
				break

		assert gDebug('sql', "-------------------------- cursor returned in %.3f sec." % (time.time() - t,))

		return cursor


	# ---------------------------------------------------------------------------
	# Convert type into what the DBSIG2 driver wants as parameter
	# ---------------------------------------------------------------------------

	def make_parameter (self, value):
		"""
		Convert any given value into the datatype that must be passed as parameter
		to the DBSIG2 cursor.execute() function.

		Descendants may override this function to to different type conversions.
		"""
		if isinstance (value, unicode):
			# Unicode: return encoded string
			return value.encode (self._encoding)

		elif isinstance (value, bool):
			# Booleans
			if value:
				return self._boolean_true_
			else:
				return self._boolean_false_

		elif isinstance (value, datetime.datetime):

			second = value.second
			microsecond = hasattr (value, 'microsecond') and value.microsecond or 0

			if isinstance (second, float):
				microsecond = int ((second - int (second)) * 1000000)
				second = int (second)

			return self._createTimestamp_ (value.year, value.month, value.day,
				value.hour, value.minute, second,
				microsecond)

		elif isinstance (value, datetime.time):

			second = value.second
			microsecond = hasattr (value, 'microsecond') and value.microsecond or 0

			if isinstance (second, float):
				microsecond = int ((second - int (second)) * 1000000)
				second = int (second)

			return self._createTime_ (value.hour, value.minute, second, microsecond)

		elif isinstance (value, datetime.date):
			if hasattr(self._driver, 'Date'):
				return self._driver.Date (value.year, value.month, value.day)
			else:
				# assume that driver accepts datetime
				return value

		elif isinstance(value, list):
			# psycopg2 driver treats [empty?] list type as text[] so format sql to force 'unknown' type
			return pythonConstToSql(value)
		else:
			# Strings, Integers
			return value


	# ---------------------------------------------------------------------------
	# Change SQL statement and parameters to different paramstyles
	# ---------------------------------------------------------------------------

	# All these functions receive the statement and the params in pyformat style
	# and convert to whatever style is needed (according to function name).
	# One of these functions get called in makecursor.

	def __param_qmark (self, statement, parameters):
		s = statement
		l = []
		while True:
			start = s.find ('%(')
			if start == -1:
				break
			end = s.find (')s', start)
			if end == -1:
				break
			key = s [start+2:end]
			s = s [:start] + '?' + s [end+2:]
			l.append (parameters [key])
		return (s, l)

	# ---------------------------------------------------------------------------

	def __param_numeric (self, statement, parameters):
		s = statement
		l = []
		i = 0
		while True:
			start = s.find ('%(')
			if start == -1:
				break
			end = s.find (')s', start)
			if end == -1:
				break
			i += 1
			key = s [start+2:end]
			s = s [:start] + (':%d' % i) + s [end+2:]
			l.append (parameters [key])
		return (s, l)

	# ---------------------------------------------------------------------------

	def __param_named (self, statement, parameters):
		s = statement
		values = []
		while True:
			start = s.find ('%(')
			if start == -1:
				break
			end = s.find (')s', start)
			if end == -1:
				break
			key = s [start+2:end]
			s = s [:start] + (':%s' % key) + s [end+2:]
			values.append (parameters [key])

		return (s, self._named_as_sequence_ and values or parameters)

	# ---------------------------------------------------------------------------

	def __param_format (self, statement, parameters):
		s = statement
		l = []
		while True:
			start = s.find ('%(')
			if start == -1:
				break
			end = s.find (')s', start)
			if end == -1:
				break
			key = s [start+2:end]
			s = s [:start] + '%s' + s [end+2:]
			l.append (parameters [key])
		return (s, l)


	# ---------------------------------------------------------------------------
	# Virtual methods to be implemented by descendants
	# ---------------------------------------------------------------------------

	def _getConnectParams_ (self, connectData):
		"""
		Return a tuple with a list and a dictionary, being the parameters and
		keyword arguments to be passed to the connection function of the DBSIG2
		driver.

		This method must be overwritten by all descendants.
		"""
		return ([], {})

	# ---------------------------------------------------------------------------

	def _createTimestamp_ (self, year, month, day, hour, minute, secs, msec = 0):
		"""
		Create a timestamp object for the given point in time.

		This function doesn't have to be overwritten unless the handling of time
		values is weird.

		@param year: Year number
		@param month: Month number (1 - 12)
		@param day: Day of the month (1 - 31)
		@param hour: Hour (0 - 23)
		@param minute: Minute (0 - 59)
		@param secs: Whole seconds (integer)
		@param msec: Microseconds (integer)

		returns: a timestamp object created by the driver's Timestamp constructor
		"""

		psec = secs + float (msec) / 1000000

		if self._std_datetime_:
			return self._driver.Timestamp (year, month, day, hour, minute, secs, msec)

		else:
			return self._driver.Timestamp (year, month, day, hour, minute, psec)


	# ---------------------------------------------------------------------------
	# Create an apropriate time object for the given values
	# ---------------------------------------------------------------------------

	def _createTime_ (self, hour, minute, second, msec = 0):
		"""
		Create a time object for the given point in time.

		This function doesn't have to be overwritten unless the handling of time
		values is weird.

		@param hour: Hour (0 - 23)
		@param minute: Minute (0 - 59)
		@param second: Whole seconds (integer)
		@param msec: Microseconds (integer)

		returns: a time object created by the driver's Time constructor
		"""

		psec = second + float (msec) / 1000000

		if self._std_datetime_:
			return self._driver.Time (hour, minute, second, msec)

		else:
			return self._driver.Time (hour, minute, psec)

	def decorateError(self, error):
		"""
		This function used to make database related error user frielndly
		"""
		return error


	def _getNativeConnection(self):
		"""
		Used by GFForm to provide raw connection as toolib.simpleconn
		"""
		return {
			'driver'     : self._driver,
			'connection' : self._native,
			'encoding'   : self._encoding,
		}

	def _getNativeConnectionContext(self):
		return {}


	def _getExceptionMessage(self):
		"""
		Returns message based on native exception information
		"""
		# was: "%s: %s" % tuple(errors.getException()[1:3])
		ec, e, tb = sys.exc_info()
		return u"%s: %s" % (ec.__name__, str(e).decode(self._encoding, 'replace'))
		
	    

PYTYPE2SQLCONV = {
	type(None)        : lambda x: 'null',
	bool              : lambda x: 'true' if x else 'false',
	str               : lambda x: "'%s'" % x.replace("\\", "\\\\").replace("'", "\\'").replace("\t", "\\t").replace("\n", "\\n"),
	list              : lambda x: "{%s}" % ','.join(map(pythonListConstToSql, x)),
	datetime.date     : lambda x: x.strftime("'%Y-%m-%d'"),
	datetime.datetime : lambda x: x.strftime("'%Y-%m-%d %H:%M:%S'"),
	datetime.time     : lambda x: x.strftime(         "'%H:%M:%S'"),
	decimal.Decimal   : str,
	long              : lambda x: repr(x).rstrip('L'),
}

PYTYPE2SQLCONV[unicode] = PYTYPE2SQLCONV[str]

def pythonConstToSql(v):
	return PYTYPE2SQLCONV.get(type(v), repr)(v)

def pythonListConstToSql(v):
	if isinstance(v, basestring):
		# remove parentheses for string contants
		return pythonConstToSql(v)[1:-1]
	else:
		return pythonConstToSql(v)


def sorted(l):
	l = list(l)
	l.sort()
	return l


if __name__ == '__main__':
	print pythonConstToSql(['zzz', 'qqq'])
	print pythonConstToSql([1,2,3L])

