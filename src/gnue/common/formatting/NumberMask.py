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
# Copyright 2001-2007 Free Software Foundation
#
# FILE:
# NumberMask.py
#
# DESCRIPTION:
#
# NOTES:
#
#       \     Next character is a literal
#       a     Abbreviated weekday name (Sun..Sat)
#       b     Abbreviated month name (Jan..Dec)
#       d     day of month (01..31)
#       h     hour (01..12)
#       g     hour (00..23)
#       j     day of year (001..366)
#       m     month (01..12)
#       i     minute (00..59)
#       p     am or pm
#       s     second (00..60)
#       u     week number of year with Sunday  as  first  day  of
#             week (00..53)
#       v     week  number  of  year  with Monday as first day of
#             week (01..52)
#       y     year
#
#     Predefined literals:  "/-.:, "
#
# Example:
#
#  m/d/y		01/01/2001
#  m/y			01/2001
#  h:i p		12:29 pm
#

from src.gnue.common.formatting.BaseMask import MaskSection, Literal
from gnue.common.utils.GDateTime import GDateTime, InvalidDate
from src.gnue.common.formatting.FormatExceptions import *
from src.gnue.common.formatting import BaseMask


class DateLiteral (Literal):
	def addSelfToDate(self, value, date):
		pass

	def isValidEntry(self, value):
		return value == self.literal or value in predefinedDateLiterals

class NumberMask (BaseMask):
	def __init__(self, outputMask, inputMask=None, outputMask2=None):

		self.predefinedLiterals = predefinedDateLiterals

		self.basetype = "date"
		self.literalClass = DateLiteral

		# TODO: Make NumberMask's defaultmask be based on locale settings
		self.defaultmask = "m/d/y"

		self.maskMappings = {
			'a': _aSection,       'A': _ASection,
			'b': _bSection,       'B': _BSection,
			'c': _cSection,       'd': _dSection,
			'D': _DSection,       'h': _hSection,
			'H': _HSection,
			'g': _gSection,       'G': _GSection,
			'j': _jSection,       'J': _JSection,
			'm': _mSection,       'M': _mSection,
			'i': _iSection,       'I': _ISection,
			'p': _pSection,       'P': _PSection,
			's': _sSection,       'S': _SSection,
			'u': _uSection,       'U': _USection,
			'v': _vSection,       'V': _VSection,
			'w': _wSection,
			'x': _xSection,       'X': _XSection,
			'y': _ySection,       'Y': _YSection }

		BaseMask.__init__(self, outputMask, inputMask, outputMask2)

		self.value = GDateTime()
		self.entry = ""
		self.inputMaskPos = []
		self.inputMaskLen = []
		for i in range(len(self.inputHandlers)):
			self.inputMaskPos.append(0)
			self.inputMaskLen.append(0)


	def processEdit (self, str, pos=0, replaces=0):
		nv = self.entry
		if pos == len(nv):
			nv += str
		else:
			nv = "%s%s%s" % (nv[:pos],str,nv[pos+replaces:])

		section = 0
		while section < len(self.inputMaskPos) and \
			self.inputMaskPos[section] < pos:
			section += 1

		i = pos
		while i < len(nv):
			if not self.inputHandlers[section]\
				.isValidEntry(nv[self.inputMaskPos[section]:i+1]):
				if i == self.inputMaskPos[section] and \
					not isinstance(self.inputHandlers[section],Literal):
					self.inputMaskLen[section] = i - self.inputMaskPos[section]
					return 1
				else:
					self.inputMaskLen[section] = i - self.inputMaskPos[section]
					if section == len(self.inputHandlers) - 1:
						if i != len(nv)-1:
							return 1
					else:
						section += 1
						self.inputMaskPos[section] = i
						self.inputMaskLen[section] = 0
			else:
				i += 1

		self.inputMaskLen[section] = i - self.inputMaskPos[section]

		for i in range(section+1, len(self.inputHandlers)):
			self.inputMaskLen[i] = 0


		self.entry = nv
		return 1


	def getFormattedOutput(self, secondary=0):
		rv = ""
		value = self._buildDate(self.entry, 1)
		if secondary:
			handlers = self.output2Handlers
		else:
			handlers = self.outputHandlers

		try:
			for m in self.outputHandlers:
				rv += m.getFormattedValue(value)

			return rv
		except InvalidDate, msg:
			raise InvalidEntry, msg


	def getFormattedDisplay(self):
		rv = ""
		value = self._buildDate(self.entry, 1)

		try:
			for m in self.outputHandlers:
				rv += m.getFormattedValue(value)

			return rv
		except InvalidDate, msg:
			raise InvalidEntry, msg


	def getFormattedInput(self, padding=""):
		rv = ""
		value = self._buildDate(self.entry, 0)

		#    self.lastInputPos =

		print self.inputMaskLen

		for i in range(len(self.inputHandlers)):
			if self.inputMaskLen[i] or isinstance(self.inputHandlers[i],Literal):
				rv += self.inputHandlers[i].getFormattedValue(value)
			elif len(padding):
				rv += padding * self.inputHandlers[i].maxLength

		return rv


	def _buildDate(self, value, mustValidate=0):
		date = GDateTime()

		for i in range(len(self.inputHandlers)):
			if self.inputMaskLen[i] or isinstance(self.inputHandlers[i],Literal):
				self.inputHandlers[i].addSelfToDate(
					value[ self.inputMaskPos[i]: \
							self.inputMaskPos[i] + self.inputMaskLen[i]], date )
			elif mustValidate:
				raise InvalidEntry, u_("Invalid Entry")

		return date



class _baseDateSection (MaskSection):
	def __init__(self):
		pass

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _aSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		return weekdayAbbrevNames[date.getDayOfWeek()]

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _ASection(_aSection):
	def getFormattedValue(self, date):
		return weekdayNames[date.getDayOfWeek()]


class _bSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		return monthAbbrevNames[(date.month or 1) - 1]

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _BSection(_bSection):
	def getFormattedValue(self, date):
		return monthNames[(date.month or 1) - 1]


class _cSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _dSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		return "%02i" % date.day

	def isValidEntry(self, value):
		try:
			v = int(value)
			return (v >= 0 and v <= 31) or (v == 0 and len(value) == 1)
		except ValueError:
			return 0

	def addSelfToDate(self, value, date):
		date.day = int(value or 1)


class _DSection(_dSection):
	def getFormattedValue(self, date):
		return "%i" % date.day


class _hSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		return "%02i" % date.hour

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		date.hour = int(value or 0)


class _HSection(_hSection):
	def getFormattedValue(self, date):
		return "%i" % date.hour


class _gSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _GSection(_gSection):
	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength


class _jSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _JSection(_jSection):
	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength


class _mSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		return "%02i" % date.month

	def isValidEntry(self, value):
		try:
			v = int(value)
			return (v >= 0 and v <= 12) or (v == 0 and len(value) == 1)
		except ValueError:
			return 0

	def addSelfToDate(self, value, date):
		date.month = int(value or 1)


class _MSection(_baseDateSection):
	def getFormattedValue(self, date):
		return "%i" % date.month


class _iSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		return "%02i" % date.minute

	def isValidEntry(self, value):
		try:
			v = int(value)
			return (v >= 0 and v <= 59) or (v == 0 and len(value) == 1)
		except ValueError:
			return 0

	def addSelfToDate(self, value, date):
		date.minute = int(value)


class _ISection(_iSection):
	def getFormattedValue(self, date):
		return "%2i" % date.minute


class _pSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _PSection(_pSection):
	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength


class _sSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		return "%02i" % date.second

	def isValidEntry(self, value):
		try:
			v = int(value)
			return (v >= 0 and v <= 59) or (v == 0 and len(value) == 1)
		except ValueError:
			return 0

	def addSelfToDate(self, value, date):
		date.second = int(value)


class _SSection(_sSection):
	def getFormattedValue(self, date):
		return "%2i" % date.second


class _uSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _USection(_uSection):
	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength


class _vSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _VSection(_vSection):
	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength


class _wSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _xSection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2

	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _XSection(_xSection):
	def getFormattedValue(self, date):
		# TODO: Implement this mask element
		return "*" * self.maxLength


class _ySection(_baseDateSection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 2
		self.maxLength = 2

	def getFormattedValue(self, date):
		return "%02i" % divmod(date.year, 100)[1]

	def isValidEntry(self, value):
		try:
			v = int(value)
			return (v >= 0) and (v <= 99)
		except ValueError:
			return 0

	def addSelfToDate(self, value, date):
		# TODO: Temporary year hack!
		v = int(value)
		if v >= 50:
			date.year = 1900 + v
		else:
			date.year = 2000 + v


class _YSection(_ySection):
	def __init__(self):
		_baseDateSection.__init__(self)
		self.minLength = 2
		self.maxLength = 4

	def getFormattedValue(self, date):
		return "%04i" % date.year

	def isValidEntry(self, value):
		try:
			v = int(value)
			return (v >= 1) and (v <= 9999)
		except ValueError:
			return 0

	def addSelfToDate(self, value, date):
		date.year = int(value)
