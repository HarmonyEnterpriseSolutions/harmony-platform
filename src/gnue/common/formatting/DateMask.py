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
# DateMask.py
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
#  m/d/y                01/23/01
#  m/Y                  01/2001
#  h:i p                12:29 pm
#
#####################################################################


from src.gnue.common.formatting.BaseMask import MaskSection, Literal
from gnue.common.apps import GDebug
from gnue.common.utils.GDateTime import GDateTime, InvalidDate
from src.gnue.common.formatting.FormatExceptions import *


# TODO: This is obviously not Internationalized!
from src.gnue.common.formatting import BaseMask

monthNames = ['January','February','March','April','May','June',
	'July','August','September','October','November','December']

monthAbbrevNames = ['Jan','Feb','Mar','Apr','May','Jun',
	'Jul','Aug','Sep','Oct','Nov','Dec']

weekdayNames = ['Sunday','Monday','Tuesday','Wednesday',
	'Thursday','Friday','Saturday']

weekdayAbbrevNames = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']


predefinedDateLiterals = "-./: ,"


class DateLiteral (Literal):
	def addSelfToDate(self, value, date):
		pass

	def isValidEntry(self, value):
		return value == self.literal or len(value) == 1 and value in predefinedDateLiterals


class DateMask (BaseMask):
	def __init__(self, outputMask, inputMask=None, outputMask2=None):

		self.predefinedLiterals = predefinedDateLiterals

		self.basetype = "date"
		self.literalClass = DateLiteral

		# TODO: Make DateMask's defaultmask be based on locale settings
		self.defaultmask = "m/d/y"

		# Reference the module-level mask mappings
		# These should never change from the values created
		# at init time.
		self.maskMappings = maskMappings

		BaseMask.__init__(self, outputMask, inputMask, outputMask2)

		self.value = GDateTime()
		self.entry = ""


	def getFormattedOutput(self, value, secondary=0):
		if value in (None,''):
			return ""

		rv = ""
		val = self._buildDate(value, 1)
		if secondary:
			handlers = self.output2Handlers
		else:
			handlers = self.outputHandlers

		try:
			for m in self.outputHandlers:
				rv += m.getFormattedValue(val)

			return rv
		except InvalidDate, msg:
			raise InvalidEntry, msg


	def getFormattedInput(self, value, padding=""):

		assert gDebug(7,'getFormattedInput(%s,%s)' % (value,padding))
		print "**** Formattin dis puppy!"

		val = self._buildDate(value, 0)

		self.display = ""
		self.lastInputPos = 0
		lastElement = self.inputCount - 1

		print o(u_("inputMaskPos=%s") % self.inputMaskLen)
		print o(u_("inputMaskLen=%s") % self.inputMaskLen)


		for i in range(self.inputCount):

			# Keep track of the last valid position
			if self.inputMaskLen[i]:
				self.lastInputPos = i + self.inputMaskLen[i] - 1

			piece = ""
			pad = ""
			partial = value[self.inputMaskPos[i]: \
					self.inputMaskPos[i]+self.inputMaskLen[i]]

			# If this is a "literal" print it as is
			if isinstance(self.inputHandlers[i],Literal):
				piece = self.inputHandlers[i].getFormattedValue(val)

			else:

				# If this is the very last (partial) section, add it unformatted
				if  self.inputMaskLen[i] and \
					( (i == lastElement) or \
						( ( i < lastElement) and \
							not self.inputMaskLen[i+1] and \
							not self.inputHandlers[i].isCompleteEntry(partial)) ) :


					piece = partial

					# Pad any extra space in this section
					if len(padding):
						pad = padding * (self.inputHandlers[i].maxLength - len(piece))

				# .. or if we have data to output, format it appropriately
				elif self.inputMaskLen[i]:
					piece = self.inputHandlers[i].getFormattedValue(val)

				# .. or if we have no data but are padding, pad appropriately
				elif len(padding):
					pad = padding * self.inputHandlers[i].maxLength

			self.inputDisplayLen[i] = len(piece)
			self.inputFormattedLen[i] = len(piece+pad)
			self.display += piece + pad

		return self.display


	def _buildDate(self, value, mustValidate=0):
		date = GDateTime()

		for i in range(self.inputCount):
			if (self.inputMaskLen[i] or isinstance(self.inputHandlers[i],Literal)):
				#        if self.inputHandlers[i].isValidEntry(value[ self.inputMaskPos[i]: \
				#                   self.inputMaskPos[i] + self.inputMaskLen[i]]):
				self.inputHandlers[i].addSelfToDate(
					value[ self.inputMaskPos[i]: \
							self.inputMaskPos[i] + self.inputMaskLen[i]], date )
		#        else:
		#          raise InvalidEntry, "Invalid Entry"

		return date




#####################################################################
#
# Mask elements
#
#####################################################################

class _baseDateSection (MaskSection):
	def __init__(self):
		pass

	def isValidEntry(self, value):
		return 0

	def addSelfToDate(self, value, date):
		pass


class _numberRangeSection (_baseDateSection):

	minLength = 0
	maxLength = 0
	valueRange = (0,0)

	def isValidEntry(self, value):
		try:
			v = int(value)
			return (v >= self.valueRange[0] and v <= self.valueRange[1] \
					and len(value) <= self.maxLength) or \
				(v <= self.valueRange[1] and len(value) < self.maxLength)
		except ValueError:
			return 0

	def isCompleteEntry(self, value):
		v = int(value)
		return      v >= self.valueRange[0] \
			and v <= self.valueRange[1] \
			and (len(value) == self.maxLength or
			v * 10 > self.valueRange[1])



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


class _dSection(_numberRangeSection):
	def __init__(self):
		_numberRangeSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2
		self.valueRange = (0,31)

	def getFormattedValue(self, date):
		return "%02i" % date.day

	def addSelfToDate(self, value, date):
		date.day = int(value or 1)


class _DSection(_dSection):
	def getFormattedValue(self, date):
		return "%i" % date.day


class _hSection(_numberRangeSection):
	def __init__(self):
		_numberRangeSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2
		self.valueRange = (0,24)

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


class _mSection(_numberRangeSection):
	def __init__(self):
		_numberRangeSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2
		self.valueRange = (1,12)

	def getFormattedValue(self, date):
		return "%02i" % date.month

	def isValidEntry(self, value):
		try:
			v = int(value)
			return (v >= 0 and v <= 12 and len(value) <= 2) or \
				(v == 0 and len(value) == 1)
		except ValueError:
			return 0

	def addSelfToDate(self, value, date):
		date.month = int(value or 1)


class _MSection(_baseDateSection):
	def getFormattedValue(self, date):
		return "%i" % date.month


class _iSection(_numberRangeSection):
	def __init__(self):
		_numberRangeSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2
		self.valueRange = (0,59)

	def getFormattedValue(self, date):
		return "%02i" % date.minute

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
		return date.hour >= 12 and 'pm' or 'am'

	def isValidEntry(self, value):
		return string.upper(string.replace(string.replace(value,' ',''),'.','')) \
			in ('A','AM','P','PM')

	def addSelfToDate(self, value, date):
		pass


class _PSection(_pSection):
	def getFormattedValue(self, date):
		return date.hour >= 12 and 'PM' or 'AM'


class _sSection(_numberRangeSection):
	def __init__(self):
		_numberRangeSection.__init__(self)
		self.minLength = 1
		self.maxLength = 2
		self.valueRange = (0,59)

	def getFormattedValue(self, date):
		return "%02i" % date.second

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


class _ySection(_numberRangeSection):
	def __init__(self):
		_numberRangeSection.__init__(self)
		self.minLength = 2
		self.maxLength = 2
		self.valueRange = (0,99)

	def getFormattedValue(self, date):
		return "%02i" % divmod(date.year, 100)[1]

	def addSelfToDate(self, value, date):
		# TODO: Temporary year hack!
		v = int(value)
		if v >= 50:
			date.year = 1900 + v
		else:
			date.year = 2000 + v


class _YSection(_numberRangeSection):
	def __init__(self):
		_numberRangeSection.__init__(self)
		self.minLength = 2
		self.maxLength = 4
		self.valueRange = (0,9999)

	def getFormattedValue(self, date):
		return "%04i" % date.year

	def addSelfToDate(self, value, date):
		date.year = int(value)



#####################################################################
#
# Mask mappings
#
#####################################################################


# Map the mask characters to their corresponding classes...
# Since these can be reused, we will create one instance at
# the module level... this will add a *little* overhead at
# module load time, but will save significant time when many
# masks are used by the app.
maskMappings = {
	'a': _aSection(),       'A': _ASection(),
	'b': _bSection(),       'B': _BSection(),
	'c': _cSection(),       'd': _dSection(),
	'D': _DSection(),
	'h': _hSection(),       'H': _HSection(),
	'g': _gSection(),       'G': _GSection(),
	'j': _jSection(),       'J': _JSection(),
	'm': _mSection(),       'M': _mSection(),
	'i': _iSection(),       'I': _ISection(),
	'p': _pSection(),       'P': _PSection(),
	's': _sSection(),       'S': _SSection(),
	'u': _uSection(),       'U': _USection(),
	'v': _vSection(),       'V': _VSection(),
	'w': _wSection(),
	'x': _xSection(),       'X': _XSection(),
	'y': _ySection(),       'Y': _YSection() }





#####################################################################
#
# Debugging stuff
#
#####################################################################

if __name__ == '__main__':
	GDebug.setDebug(20)
	val = ""
	dates = DateMask(r'\D\a\t\e: A, B d, Y  \T\i\m\e: h:i:s','m.d.y')

	#  val = dates.processEdit(val, '07/161',0,0)
	#  print "processEdit <= %s" % val
	#  print dates.getFormattedInput(val, "_")

	val = dates.processEdit(val, '1',0,0)
	print "processEdit <= %s" % val
	print dates.getFormattedInput(val, "_")

	val = dates.processEdit(val, '2',1,0)
	print "processEdit <= %s" % val
	print dates.getFormattedInput(val, "_")

	val = dates.processEdit(val, '091',1,1)
	print "processEdit <= %s" % val
	print dates.getFormattedInput(val, "_")

	val = dates.processEdit(val, '',1,1)
	print "processEdit <= %s" % val
	print dates.getFormattedInput(val, "_")
