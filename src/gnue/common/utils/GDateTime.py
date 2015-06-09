# GNU Enterprise Common Library - Utilities - Datetime support
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
# $Id: GDateTime.py 9222 2007-01-08 13:02:49Z johannes $

import datetime
import calendar
import re

from gnue.common.apps import errors


# =============================================================================
# Exceptions
# =============================================================================

class InvalidDateError (errors.ApplicationError):
	def __init__ (self, datestring):
		msg = "'%s' is not valid literal for a date" % datestring
		errors.ApplicationError.__init__ (self, msg)

class InvalidTimeError (errors.ApplicationError):
	def __init__ (self, timestring):
		msg = "'%s' is not valid literal for a time" % timestring
		errors.ApplicationError.__init__ (self, msg)

class NotSupportedError (errors.ApplicationError):
	pass

# =============================================================================
# tzinfo implementation for timezones with a fixed offset
# =============================================================================

class FixedOffsetZone (datetime.tzinfo):

	# ---------------------------------------------------------------------------
	# Create a new tzinfo instance with the given offset and an optional name
	# ---------------------------------------------------------------------------

	def __init__ (self, offset = 0, name = None):

		self.__offset = datetime.timedelta (minutes = offset)
		self.__name   = name

		# A timezone with a zero offset is always 'UTC'
		if not offset and name is None:
			self.__name = 'UTC'

	# ---------------------------------------------------------------------------
	# return the offset of this timezone to UTC
	# ---------------------------------------------------------------------------

	def utcoffset (self, dt):
		"""
		Return offset of local time from UTC, in minutes east of UTC. If local time
		is west of UTC, this should be negative.
		"""
		return self.__offset


	# ---------------------------------------------------------------------------
	# Return the name of the timezone
	# ---------------------------------------------------------------------------

	def tzname (self, dt):
		return self.__name


	# ---------------------------------------------------------------------------
	# Return the daylight saving time adjustment
	# ---------------------------------------------------------------------------

	def dst (self, dt):
		"""
		Return the daylight saving time (DST) adjustment, in minutes east of UTC,
		or None if DST information isn't known.
		"""
		return datetime.timedelta (0)


# =============================================================================
# Parse a string in ISO 8601 format into a date-, time- or datetime instance
# =============================================================================

def parseISO (isostring):
	"""
	Parse a given string with an ISO-date, -time or -datetime and create an
	apropriate datetime.* type. The ISO string migth be given in the extended
	format (including separators) or the basic format as well.

	@param isostring: string with the date, time or datetime to be parsed
	@return: datetime.date/time/datetime instance representing the given string

	@raises InvalidDateError: if the given string cannot be parsed
	"""

	match = re.match ('^(.*?)[ T](.*)$', isostring.strip ())
	if match is not None:
		(datepart, timepart) = match.groups ()
		date = parseISODate (datepart)
		(time, date) = parseISOTime (timepart, date)
		return datetime.datetime.combine (date, time)

	else:
		try:
			return parseISOTime (isostring.strip ())

		except InvalidTimeError:
			return parseISODate (isostring.strip ())


# =============================================================================
# Parse a date given as ISO string into a datetime.date instance
# =============================================================================

def parseISODate (datestring):
	"""
	Parse a date given as string in ISO 8601 format into a datetime.date
	instance. The date might be given in the basic- or extended format.
	Possible forms are: ordinal dates (1981-095, 1981095), weeks (1981-W14-7,
	1981W147) or full dates (1981-05-03, 19810503). If a week is given without a
	day of the week, Monday of that week will be used (see L{parseISOWeek}).
	NOTE: datetime library does not support dates earlier than 1st January 1 AD

	@param datestring: string conforming to ISO 8601 date format
	@return: datetime.date instance with the given date

	@raises NotSupportedError: if the given string represents a date before 1st
	  january 1 AD.
	@raises InvalidDateError: if the given datestring cannot be transformed into
	  a datetime.date instance
	"""

	result = None

	if datestring [0] == '-':
		raise NotSupportedError, \
			u_("Dates before 0001/01/01 are not supported by datetime library")

	if "W" in datestring:
		result = parseISOWeek (datestring)

	elif "-" in datestring:
		parts = datestring.split ('-')
		year  = int (parts [0])

		if len (parts) == 2 and len (parts [1]) == 3:
			result = parseOrdinal (year, int (parts [1]))
		else:
			month = int (parts [1])
			day   = len (parts) > 2 and int (parts [2]) or 1

			result = datetime.date (year, month, day)

	elif len (datestring) == 7:
		result = parseOrdinal (int (datestring [:4]), int (datestring [4:7]))

	elif len (datestring) == 8:
		parts = map (int, [datestring [:4], datestring [4:6], datestring [6:8]])
		result = datetime.date (*parts)

	if result is None:
		raise InvalidDateError, datestring

	return result


# =============================================================================
# Parse an ISO string representing a week
# =============================================================================

def parseISOWeek (weekstring):
	"""
	Parses an ISO week string given as 'YYYY-Www-d' (extended) or 'YYYYWwwd'
	(basic) into a datetime.date instance reflecting the given date. The day of
	the week part is optional and defaults to Monday of the week if omitted. The
	ISO week day is defined as 1 for Monday and 7 for Sunday.

	@param weekstring: ISO string with the week to be parsed
	@returns: datetime.date instance reflecting the given date
	"""

	if '-' in weekstring:
		parts = weekstring.split ('-')
		parts [1] = parts [1][1:]
	else:
		parts = weekstring [:4], weekstring [5:7], weekstring [7:]

	parts = map (int, filter (None, parts))
	year, week, day = parts [0], parts [1], len (parts) > 2 and parts [2] or 1

	# First create a date for the first day in the given year ...
	january = datetime.date (year, 1, 1)

	# ... and calculate an offset depending on wether the first january is within
	# the same year or not
	if january.isocalendar () [0] == year:
		offset = -january.isoweekday () + 7 * (week - 1) + day

	else:
		offset = 7 - january.isoweekday () + 7 * (week - 1) + day

	return january + datetime.timedelta (offset)


# =============================================================================
# Build a date instance for a given date within a given year
# =============================================================================

def parseOrdinal (year, day):
	"""
	Return a datetime.date instance for the given date within the given year,
	where day 1 is the first of January, day 32 is the first of February and so
	on.

	@param year: the year
	@param day: the day within the year to create a datetime.date instance for
	@return: datetime.date reflecting the requested day within the year
	"""

	return datetime.date (year, 1, 1) + datetime.timedelta (day - 1)


# =============================================================================
# Parse a time given as ISO string into a datetime.time instance
# =============================================================================

def parseISOTime (timestring, date = None):
	"""
	Return a datetime.time instance for the given string in ISO 8601 format. The
	timestring could be given in basic- or extended format and might contain a
	timezone. Examples: 14:30:21Z, 14:30:21+02:00, 13:20:12.1234-0130, 14.3+02

	@param timestring: string in ISO 8601 format to parse
	@param date: datetime.date instance for which the timestring should be
	  parsed. This argument is optional. If the time is '24:00:00' one day will
	  be added to this date.
	@return: If not date arguemnt is given the result is a datetime.time
	  reflecting the given string. If a date is given, the result is a tuple
	  (datetime.time, datetime.date) reflecting the requested time and the given
	  date (optionally incremented by one day)

	@raises InvalidTimeError: if the given timestring cannot be transformed into
	  a datetime.time instance
	"""

	timezone = None

	parts = re.match ('^(.*?)(?:([Z+-])(.*)){0,1}$', timestring)
	if parts is None:
		raise InvalidTimeError, timestring

	(timepart, zone, offset) = parts.groups ()

	# Make sure to have the timepart in basic format
	if ':' in timepart:
		items = timepart.split (':')
		for (ix, i) in enumerate (items):
			if '.' in i:
				full, frac = i.split ('.')
				items [ix] = "%02d.%s" % (int (full), frac)
			else:
				items [ix] = "%02d" % int (i)

		timepart = ''.join (items)

	# Use UTC timezone if the string contains a Z (=Zulu time)
	if zone == 'Z':
		timezone = FixedOffsetZone (0, 'UTC')

	# otherwise if a timezone offset is defined, transform it into a tzinfo
	# instance
	if offset:
		zoneMatch = re.match ('(\d\d)?:?(\d\d)$', offset)
		if zoneMatch is None:
			raise InvalidTimeError, timestring

		items = filter (None, zoneMatch.groups ())
		zhour = int (items [0])
		zmin  = len (items) > 1 and int (items [1]) or 0
		mult  = zone == '-' and -1 or 1

		timezone = FixedOffsetZone (mult * (zhour * 60 + zmin))

	# If the timestring contains a fractional part (e.g. 14.3 which means 14
	# hours and 20 minutes) split the string into the full and the fractional
	# part
	match = re.match ('^(\d+)(?:[\.,](\d+)){0,1}$', timepart)
	if match is None:
		raise InvalidTimeError, timepart

	# The full part cannot contain more than 6 characters (=HHMMSS)
	(full, fractions) = match.groups ()
	if len (full) > 6:
		raise InvalidTimeError, timestring

	elements = []
	while len (full):
		elements.append (int (full [:2]))
		full = full [2:]

	# Get an apropriate factor for the given fractions, which is 60 for hours,
	# and minutes, and 1000000 (microseconds) for seconds.
	if fractions:
		factor = len (elements) < 3 and 60 or 1000000
		elements.append (int (float ("0.%s" % fractions) * factor))

	# Finally make sure to have 4 elements (where missing items are 0)
	while len (elements) < 4:
		elements.append (0)

	(hour, minute, second, micro) = elements
	if hour > 24 or minute > 59 or second > 60:
		raise InvalidTimeError, timestring

	# 24 in an hour is only valid as 24:00:00
	if hour == 24 and (minute + second + micro) != 0:
		raise InvalidTimeError, timestring

	# 24:00:00 is the same as 00:00:00 of the next day
	if hour == 24:
		hour = minute = second = micro = 0
		if date is not None:
			date += datetime.timedelta (days = 1)

	result = datetime.time (hour, minute, second, micro, tzinfo = timezone)

	if date is not None:
		return (result, date)
	else:
		return result


#
def isLeapYear (year):
	return calendar.isleap (year)

class InvalidDate (errors.UserError):
	pass

class GDateTime:
	def __init__(self):
		self.month = 0
		self.day = 0
		self.year = 0
		self.hour = 0
		self.minute = 0
		self.second = 0

	def __repr__(self):
		return "%04d/%02d/%02d %02d:%02d:%02d" % \
			(self.year, self.month, self.day, self.hour, self.minute, self.second)

	def getDayOfWeek(self):
		# from the Calendar FAQ (http://www.pauahtun.org/CalendarFAQ/)
		# 0 = Sunday
		a = int((14 - self.month) / 12)
		y = self.year - a
		m = self.month + 12*a - 2
		return divmod(self.day + y + int(y/4) - int(y/100) + int(y/400) + (31*m)/12,7)[1]


	def validate(self):
		if not (\
				self.month >= 1 and self.month <= 12 and \
				self.year >= 0 and \
				self.day >= 1 and self.day <= ( \
					(self.month in (1,3,5,7,8,10,12) and 31) or \
					(self.month == 2 and (28 + isLeapYear(self.year))) \
					or 30) and \
				self.hour >= 0 and self.hour <= 23 and \
				self.minute >= 0 and self.minute <= 59 and \
				self.second >= 0 and self.second <= 59 ):
			raise InvalidDate, u_("Not a valid date")



# =============================================================================
# Module self test code
# =============================================================================

def check (value):
	print "%-20s: %s" % (value, parseISO (value).isoformat ())

if __name__ == '__main__':

	check ('14230301')           # 1st March 1423
	check ('1423-03-01')           # 1st March 1423
	check ('1981-04-05')
	check ('14:23:21.233')
	check ('19810405 17:23:15')
	check ('1981-W14-7 17:23:15')
	check ('1981-W14')
	check ('1981W147')
	check ('1981W14')
	check ('2005-W01-1')
	check ('2005-W53-6')
	check ('1981-095 121314Z')
	check ('1321')
	check ('1321.5')
	check ('1321.3+0312')
	check ('1321-12:34')
	check ('2005-07-27 24:00+02')
	check ('6:2:1.233')
