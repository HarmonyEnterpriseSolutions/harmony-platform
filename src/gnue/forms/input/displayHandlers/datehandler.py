# GNU Enterprise Forms - Display handler - Date related display handlers
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
# $Id: datehandler.py,v 1.8 2012/04/26 07:57:04 oleg Exp $
"""
DisplayHandler classes for input validation of date, time and datetime values
"""
__revision__ = "$Id: datehandler.py,v 1.8 2012/04/26 07:57:04 oleg Exp $"

import sys
import time
import datetime
import re

from gnue.common.apps import errors
from gnue.forms.input.displayHandlers.Cursor import BaseCursor

# =============================================================================
# Exceptions
# =============================================================================

class InvalidDateLiteral(errors.UserError):
	def __init__(self, value):
		msg = u_("'%(value)s' is not a valid date-literal") % {'value': value}
		errors.UserError.__init__ (self, msg)

class InvalidTimeLiteral(errors.UserError):
	def __init__(self, value):
		msg = u_("'%(value)s' is not a valid time-literal") % {'value': value}
		errors.UserError.__init__ (self, msg)


# =============================================================================
# Base class for date related handlers
# =============================================================================

class DateRelated(BaseCursor):
	"""
	Base class for all date- and time-related displayhandler

	@cvar _config_display_mask_: name of the configuration setting for the
	    display mask in gnue.conf
	@cvar _config_input_mask_: name of the configuration setting for the input
	    mask in gnue.conf
	"""

	_config_display_mask_ = ''
	_config_input_mask_ = ''

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, entry, eventHandler, subEventHandler, display_mask,
		input_mask):

		BaseCursor.__init__(self, entry, eventHandler, subEventHandler,
			display_mask, input_mask)

		self._input_mask = input_mask or gConfigForms(self._config_input_mask_)
		self._display_mask = display_mask or \
			gConfigForms(self._config_display_mask_)

		self._order = []
		self._inter = []

		self._get_ordering_()


	# -------------------------------------------------------------------------
	# Create a display string for the current value
	# -------------------------------------------------------------------------

	def build_display(self, value, editing):
		"""
		Create a display string for the given date-, time- or datetime-value.

		@param value: the value to create a display string for
		@param editing: True if the display-string is for edit mode, False
		     otherwise

		@returns: the display string for the given value
		@rtype: string
		"""

		if editing:
			mask = self._input_mask
		else:
			mask = self._display_mask

		if value in (None, ""):
			return u""

		try:
			return unicode(value.strftime(str(mask)))

		except AttributeError:
			return unicode(value)

		except ValueError:
			return unicode(value)


	# -------------------------------------------------------------------------
	# Get the tip for this kind of date/time field
	# -------------------------------------------------------------------------

	def get_tip(self):
		"""
		Derive the apropriate tip from the sample date.
		"""
		sample = datetime.datetime(1978, 3, 21, 13, 24, 56)
		result = sample.strftime(str(self._input_mask))
		result = result.replace('13', u_('H') * 2)
		result = result.replace('01', u_('H') * 2)
		result = result.replace('24', u_('M') * 2)
		result = result.replace('56', u_('S') * 2)
		result = result.replace('21', u_('D') * 2)
		result = result.replace('03', u_('M') * 2)
		result = result.replace('3', u_('M'))
		result = result.replace('78', u_('Y') * 2)
		result = result.replace('19', u_('Y') * 2)

		return result

	# -------------------------------------------------------------------------
	# Get the order of the date/time components
	# -------------------------------------------------------------------------

	def _get_ordering_(self):
		pass

	# -------------------------------------------------------------------------
	# Split a given text into the date components
	# -------------------------------------------------------------------------

	def _split_apart(self, text):
		"""
		Split the given string into the components according to the order as
		given by C{self._order}.

		@param text: the string to be split into it's components
		@returns: dictionary with the components using the item of self._order
		    as keys and the splitted part as value
		"""

		result = {}

		if text.isdigit():
			components = []
			while text:
				if len(text) > 2:
					components.append(text[:2])
					text = text[2:]
				else:
					components.append(text)
					text = ''

			for index, value in enumerate(components):
				result[self._order[index]] = value
		else:
			for index in range(len(self._order)):
				if index < len(self._inter):
					parts = text.split(self._inter[index], 1)
					if len(parts) == 2:
						cut = parts[0] + self._inter[index]
					else:
						cut = parts[0]
				else:
					parts = [text]
					cut = text

				result[self._order[index]] = parts[0]
				text = text[len(cut):]
				if not text:
					break

		return result


# =============================================================================
# Display handler for date fields
# =============================================================================

class Date(DateRelated):
	"""
	Display handler for date values.
	"""

	_config_display_mask_ = 'DateMask'
	_config_input_mask_   = 'DateEditMask'


	# -------------------------------------------------------------------------
	# Get the order of the date's components (as defined by the given mask)
	# -------------------------------------------------------------------------

	def _get_ordering_(self):

		sample = datetime.date(1978, 3, 21)
		text = sample.strftime(str(self._input_mask))
		self._order = []
		self._inter = []
		pat = re.compile('^(\d+)(\D*)')

		match = pat.match(text)
		while match:
			part, rest = match.groups()
			if part in ['1978', '78']:
				self._order.append('year')
			elif part in ['03', '3']:
				self._order.append('month')
			elif part == '21':
				self._order.append('day')
			else:
				self._order.append('?')

			if rest:
				self._inter.append(rest)

			text = text[len(part + rest):]
			if not text:
				break

			match = pat.match(text)


	# -------------------------------------------------------------------------
	# Try to figure out which date the user meant
	# -------------------------------------------------------------------------

	def parse_display(self, display):
		date = self.__parse_display(display)

		# check year to be >= 1900 because strftime can't format this
		if date is not None and date.year < 1900:
			raise InvalidDateLiteral, display

		return date

	def __parse_display(self, display):
		"""
		Try to figure out which date is meant by the given string.

		@param display: string with a (maybe incomplete) date
		@returns: date matching the given string
		@raises InvalidDateLiteral: if the given string is no valid date
		"""

		if not display:
			return None

		try:
			# First have a look wether the input follows the requested format
			temp = time.strptime(display, self._input_mask)
			return datetime.date(*temp[0:3])

		except ValueError:
			pass

		today = datetime.date.today()

		# Ok, now let's do some guessing.

		# If the input is a number of length 2 we treat it as day
		if display.isdigit() and len(display) <= 2:
			try:
				return today.replace(day=int(display))

			except ValueError:
				raise InvalidDateLiteral, display

		# If the input is a 4-digit number or a string with two numbers
		# separated by a non-digit string we treat it as "day and month"
		# according to the order of the original input mask
		match = re.match('^(\d+)\D+(\d+)\s*$', display)
		if (display.isdigit() and len(display) == 4) or match is not None:
			if match:
				(val1, val2) = match.groups()
			else:
				val1, val2 = display[:2], display[2:]

			if self._order.index('day') < self._order.index('month'):
				day = int(val1)
				month = int(val2)
			else:
				day = int(val2)
				month = int(val1)

			try:
				return today.replace(day=day, month=month)

			except ValueError:
				raise InvalidDateLiteral, display

		# If the input is a 6-digit number or a triple of numeric values
		# separated by non-digit characters it is likely a complete date
		match = re.match('^(\d+)\D+(\d+)\D+(\d+).*$', display)
		if (display.isdigit() and len(display) == 6) or match is not None:
			if match:
				values = match.groups()
			else:
				values = display[:2], display[2:4], display[4:]

			kw = {}
			for index, item in enumerate(values):
				value = int(item)
				part = self._order[index]

				# If the year is given without a century we will figure out
				# which one to use.
				if part == 'year' and value < 100:
					if value % 100 >= 50:
						value += 1900
					else:
						value += 2000

				kw[part] = value

			try:
				return datetime.date(**kw)

			except ValueError:
				raise InvalidDateLiteral, display

		# If the input is a 8-digit number it should be a complete date.  We
		# derive the order of the elements from the order as given in the input
		# mask.
		if display.isdigit() and len(display) == 8:
			for item in self._order:
				if item == 'year':
					year = int(display[:4])
					display = display[4:]
				elif item == 'month':
					month = int(display[:2])
					display = display[2:]
				elif item == 'day':
					day = int(display[:2])
					display = display[2:]

			try:
				return datetime.date(day=day, month=month, year=year)

			except ValueError:
				raise InvalidDateLiteral, display

		raise InvalidDateLiteral, display


	# -------------------------------------------------------------------------
	# Autocomplete a user input
	# -------------------------------------------------------------------------

	def _autocomplete_(self, new_text, new_cursor):

		# We do not autocomplete dates starting with the year
		if self._order[0] == 'year':
			return new_text, new_cursor

		today = datetime.date.today()

		parts = self._split_apart(new_text)
		result = ''
		ncursor = None
		for index, item in enumerate(self._order):
			if item in parts:
				value = parts[item]
				if item in ['day', 'month'] and len(value) > 2:
					parts[item] = value[:2]
					parts[self._order[index+1]] = value[2:]

				if not value.isdigit():
					return new_text, new_cursor

				if (index > 0):
					result += self._inter[index-1]

					# bugfix: 11111 leads to 11.11.|1]
					ncursor = new_cursor + len(self._inter[index-1])

				result += parts[item]
			else:
				if ncursor is None:
					ncursor = len(result)
					if new_text.endswith(self._inter[index-1]):
						ncursor += len(self._inter[index-1])

				result += self._inter[index-1]

				result += "%s" % getattr(today, item)

		if ncursor is not None:
			new_cursor = ncursor

		return result, new_cursor


# =============================================================================
# Display handler for time fields
# =============================================================================

class Time(DateRelated):
	"""
	Display handler for time values.
	"""

	_config_display_mask_ = 'DateMask_Time'
	_config_input_mask_   = 'DateEditMask_Time'


	# -------------------------------------------------------------------------
	# Get the ordering of the time components according to the given format
	# -------------------------------------------------------------------------

	def _get_ordering_(self):
		"""
		Get the ordering of the time components according to the input mask
		"""
		text = datetime.time(13, 24, 56).strftime(str(self._input_mask))
		pat = re.compile('^(\d+)(\D*)')

		match = pat.match(text)
		while match:
			part, rest = match.groups()
			if part in ['13', '01']:
				self._order.append('hour')
			elif part == '24':
				self._order.append('minute')
			elif part == '56':
				self._order.append('second')
			else:
				self._order += '?'

			if rest:
				self._inter.append(rest)

			text = text[len(part + rest):]
			if not text:
				break

			match = pat.match(text)



	# -------------------------------------------------------------------------
	# Parsing a (maybe partial) value
	# -------------------------------------------------------------------------

	def parse_display(self, display):
		"""
		Try to figure out which datetime.time value is meant by the given
		display string.
		"""

		if not display:
			return None

		try:
			# First have a look wether the input follows the requested format
			temp = time.strptime(display, self._input_mask)
			return datetime.time(*temp[3:3+len(self._order)])

		except ValueError:
			pass

		kw = {}
		# If the input is a number of length 2 we treat it as the lowest part
		if display.isdigit() and len(display) <= 2:
			try:
				kw[self._order[-1]] = int(display)
				return datetime.time(**kw)

			except ValueError:
				raise InvalidTimeLiteral, display


		# If the input is a 4-digit number or a string with two numbers
		# separated by a non-digit string we treat it as the least significant
		# two components according to the order of the original input mask
		match = re.match('^(\d+)\D+(\d+)\s*$', display)
		if (display.isdigit() and len(display) == 4) or match is not None:
			if match:
				(val1, val2) = match.groups()
			else:
				val1, val2 = display[:2], display[2:]

			if len(self._order) >= 2:
				kw[self._order[-2]] = int(val1)
				kw[self._order[-1]] = int(val2)
			else:
				kw[self._order[-1]] = int(val1)

			try:
				return datetime.time(**kw)

			except ValueError:
				raise InvalidTimeLiteral, display

		# If the input is a 6-digit number or a string with three numbers
		# separated by a non-digit string we treat it as the least significant
		# three components according to the order of the original input mask
		match = re.match('^(\d+)\D+(\d+)\D+(\d+)\s*$', display)
		if (display.isdigit() and len(display) == 6) or match is not None:
			if match:
				(val1, val2, val3) = match.groups()
			else:
				val1, val2, val3 = display[:2], display[2:4], display[4:]

			if len(self._order) >= 3:
				kw[self._order[-3]] = int(val1)
				kw[self._order[-2]] = int(val2)
				kw[self._order[-1]] = int(val3)
			elif len(self._order) == 2:
				kw[self._order[-2]] = int(val1)
				kw[self._order[-1]] = int(val2)
			else:
				kw[self._order[-1]] = int(val1)

			try:
				return datetime.time(**kw)

			except ValueError:
				raise InvalidTimeLiteral, display

		# Does not seem to fit any pattern
		raise InvalidTimeLiteral, display


# =============================================================================
# Displayhandler for date- and time-values
# =============================================================================

class DateTime(DateRelated):
	"""
	Class to handle the display and entry of date based fields.
	"""

	_config_display_mask_ = 'DateMask_Timestamp'
	_config_input_mask_   = 'DateEditMask_Timestamp'


	# -------------------------------------------------------------------------
	# Get the ordering for the components
	# -------------------------------------------------------------------------

	def _get_ordering_(self):

		sample = datetime.datetime(1978, 3, 21, 13, 24, 56)
		text = sample.strftime(str(self._input_mask))

		self._order = []
		self._inter = []
		pat = re.compile('^(\d+)(\D*)')

		match = pat.match(text)
		while match:
			part, rest = match.groups()
			if part in ['1978', '78']:
				self._order.append('year')
			elif part in ['03', '3']:
				self._order.append('month')
			elif part == '21':
				self._order.append('day')
			elif part in ['13', '01']:
				self._order.append('hour')
			elif part == '24':
				self._order.append('minute')
			elif part == '56':
				self._order.append('second')
			else:
				self._order.append('?')

			if rest:
				self._inter.append(rest)

			text = text[len(part + rest):]
			if not text:
				break

			match = pat.match(text)


	# -------------------------------------------------------------------------
	# Try to get an apropriate datetime value from a string
	# -------------------------------------------------------------------------

	def parse_display(self, display):

		if not len(display):
			return None

		try:
			# First have a look wether the input follows the requested format
			temp = time.strptime(display, self._input_mask)
			return datetime.datetime(*temp[0:6])

		except ValueError:
			pass


		today = datetime.datetime.today().replace(hour=0, minute=0, second=0,
			microsecond=0)

		# If the input is a number of length 2 we treat it as day
		if display.isdigit() and len(display) <= 2:
			try:
				return today.replace(day=int(display))

			except ValueError:
				raise InvalidDateLiteral, display

		# If the input is a 4-digit number or a string with two numbers
		# separated by a non-digit string we treat it as "day and month"
		# according to the order of the original input mask
		match = re.match('^(\d+)\D+(\d+)\s*$', display)
		if (display.isdigit() and len(display) == 4) or match is not None:
			if match:
				(val1, val2) = match.groups()
			else:
				val1, val2 = display[:2], display[2:]

			if self._order.index('day') < self._order.index('month'):
				day = int(val1)
				month = int(val2)
			else:
				day = int(val2)
				month = int(val1)

			try:
				return today.replace(day=day, month=month)

			except ValueError:
				raise InvalidDateLiteral, display

		# If the input is a 6-digit number or a triple of numeric values
		# separated by non-digit characters it is likely a complete date
		match = re.match('^(\d+)\D+(\d+)\D+(\d+)$', display)
		if (display.isdigit() and len(display) == 6) or match is not None:
			if match:
				values = match.groups()
			else:
				values = display[:2], display[2:4], display[4:]

			kw = {}
			for index, item in enumerate(values):
				value = int(item)
				part = self._order[index]

				# If the year is given without a century we will figure out
				# which one to use.
				if part == 'year' and value < 100:
					if value % 100 >= 50:
						value += 1900
					else:
						value += 2000

				kw[part] = value

			try:
				return datetime.datetime(**kw)

			except ValueError:
				raise InvalidDateLiteral, display

		# If the input is a 8-digit number it should be a complete date.  We
		# derive the order of the elements from the order as given in the input
		# mask.
		if display.isdigit() and len(display) == 8:
			for item in self._order:
				if item == 'year':
					year = int(display[:4])
					display = display[4:]
				elif item == 'month':
					month = int(display[:2])
					display = display[2:]
				elif item == 'day':
					day = int(display[:2])
					display = display[2:]

			try:
				return datetime.datetime(day=day, month=month, year=year)

			except ValueError:
				raise InvalidDateLiteral, display


		# If the input is a triple of numeric values separated by non-digit
		# characters followed by non-digit characters and something else it is
		# likely a complete date with a time-part
		match = re.match('^(\d+)\D+(\d+)\D+(\d+)\D+(.*)$', display)
		if match is not None:
			values = list(match.groups())
			timepart = values.pop()

			kw = {}
			for index, item in enumerate(values):
				value = int(item)
				part = self._order[index]

				# If the year is given without a century we will figure out
				# which one to use.
				if part == 'year' and value < 100:
					if value % 100 >= 50:
						value += 1900
					else:
						value += 2000

				kw[part] = value

			# now try to guess what the timepart means
			timeres = self.__parse_time(timepart)

			try:
				return datetime.datetime.combine(datetime.date(**kw), timeres)

			except ValueError:
				raise InvalidDateLiteral, display
		raise InvalidDateLiteral, display


	# -------------------------------------------------------------------------
	# Try to figure out which time is meant by a given string
	# -------------------------------------------------------------------------

	def __parse_time(self, display):

		# Catch the ordering of the time components
		order = [i for i in self._order if i in ['hour', 'minute', 'second']]

		kw = {'hour': 0, 'minute': 0, 'second': 0}

		# If the input is a number of length 2 we treat it as the first
		# component
		if display.isdigit() and len(display) <= 2:
			try:
				kw[order[0]] = int(display)
				return datetime.time(**kw)

			except ValueError:
				raise InvalidTimeLiteral, display


		# If the input is a 4-digit number or a string with two numbers
		# separated by a non-digit string we treat it as the first two
		# components according to the order of the original input mask
		match = re.match('^(\d+)\D+(\d+)\s*$', display)
		if (display.isdigit() and len(display) == 4) or match is not None:
			if match:
				(val1, val2) = match.groups()
			else:
				val1, val2 = display[:2], display[2:]

			kw[order[0]] = int(val1)
			kw[order[1]] = int(val2)

			try:
				return datetime.time(**kw)

			except ValueError:
				raise InvalidTimeLiteral, display

		# If the input is a 6-digit number or a string with three numbers
		# separated by a non-digit string we treat it as complete time part
		# according to the order of the original input mask
		match = re.match('^(\d+)\D+(\d+)\D+(\d+)\s*$', display)
		if (display.isdigit() and len(display) == 6) or match is not None:
			if match:
				(val1, val2, val3) = match.groups()
			else:
				val1, val2, val3 = display[:2], display[2:4], display[4:]

			kw[order[0]] = int(val1)
			kw[order[1]] = int(val2)
			kw[order[2]] = int(val3)

			try:
				return datetime.time(**kw)

			except ValueError:
				raise InvalidTimeLiteral, display

		# Does not seem to fit any pattern
		raise InvalidTimeLiteral, display

	# -------------------------------------------------------------------------
	# Autocompletion of a datetime value
	# -------------------------------------------------------------------------

	def _autocomplete_(self, new_text, new_cursor):

		# We do not autocomplete dates starting with the year
		if self._order[0] == 'year':
			return new_text, new_cursor

		today = datetime.datetime.today().replace(hour=0, minute=0, second=0,
			microsecond=0)

		parts = self._split_apart(new_text)
		result = ''
		ncursor = None
		for index, item in enumerate(self._order):
			if item in parts:
				value = parts[item]
				if item in ['day', 'month'] and len(value) > 2:
					parts[item] = value[:2]
					parts[self._order[index+1]] = value[2:]

				if not value.isdigit():
					return new_text, new_cursor

				if (index > 0):
					result += self._inter[index-1]

				result += parts[item]
			else:
				if ncursor is None:
					ncursor = len(result)
					if new_text.endswith(self._inter[index-1]):
						ncursor += len(self._inter[index-1])

				result += self._inter[index-1]

				result += "%s" % getattr(today, item)

		if ncursor is not None:
			new_cursor = ncursor

		return result, new_cursor
