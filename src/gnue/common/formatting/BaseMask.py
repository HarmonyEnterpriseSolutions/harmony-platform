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
# BaseMask.py
#
# DESCRIPTION:
#
# NOTES:
#

from src.gnue.common.formatting.FormatExceptions import *

# TODO: i18n
#   import locale
#   locale.nl_langinfo(  option)
#
#   Return some locale-specific information as a string. This function is
#   not available on all systems, and the set of possible options might
#   also vary across platforms. The possible argument values are numbers,
#   for which symbolic constants are available in the locale module.
#
#   DAY_1 ... DAY_7
#   Return name of the n-th day of the week.
#
#   ABDAY_1 ... ABDAY_7
#   Return abbreviated name of the n-th day of the week.
#
#   MON_1 ... MON_12
#   Return name of the n-th month.
#
#   ABMON_1 ... ABMON_12
#   Return abbreviated name of the n-th month.


# This is a class for a mask literal element
class Literal:
	def __init__(self, literal):
		self.literal = literal

	def getFormattedValue(self, value):
		return self.literal

	def isValidEntry(self, value):
		return value == self.literal

	def isCompleteEntry(self, value):
		return 0

class BaseMask:
	value = ""
	maskMappings = {}
	inputHandlers = []
	outputHandlers = []
	output2Handlers = []
	predefinedLiterals = ""
	basetype = "base"
	defaultmask = ""
	literalClass = Literal

	def __init__(self, outputMask, inputMask=None, outputMask2=None):

		self.outputHandlers  = self.parseMask(outputMask)
		print "Creating mask handler: %s;%s" % (outputMask,inputMask)
		print self.outputHandlers

		if inputMask != None:
			self.inputHandlers = self.parseMask(inputMask)
		if outputMask2 != None:
			self.output2Handlers = self.parseMask(outputMask2)

		# Calculate our array lengths once to speed up
		# our code. This should always be equivalent to:
		#   len(self.inputHandlers)
		#   len(self.inputMaskPos)
		#   len(self.inputMaskLen)
		#   len(self.inputDisplayLen)
		self.inputCount = len(self.inputHandlers)

		self.reset()


	def reset(self):

		# Holds the starting positions of each element section...
		self.inputMaskPos = [0] * self.inputCount

		# Holds the length of each element section...
		self.inputMaskLen = [0] * self.inputCount

		# Holds the length of each formatted element section...
		self.inputDisplayLen = [0] * self.inputCount
		# .. including padding
		self.inputFormattedLen = [0] * self.inputCount


		self.index = 0
		self.cursor = 0
		self.display = ""
		self.input = ""


	# Take a mask string and break it into its elements and map it to handlers
	def parseMask(self, mask, edit=0):
		assert gDebug(7,'parseMask("%s")' % mask)
		maskHandler = []

		# Load a predefined mask, if that's what user specified
		# TODO: Should predefined masks be pulled from other than gnue.conf?
		if len(mask) > 1 and mask[0] == '&':
			for i in range(edit+1):
				edstr = ('edit','')[i]
				if mask[1:] == self.basetype:
					try:
						mask = gConfig('%s%smask' % (self.basetype, edstr), self.defaultmask)
					except KeyError:
						pass
				else:
					try:
						mask = gConfig('%smask_%s' % (self.basetype, edstr, mask[1:]))
					except KeyError:
						pass
			if not len(mask):
				tmsg =  u_('The requested format mask "%(mask)s" is not defined for '
					'%(type)s fields') \
					% {'mask': mask [1:],
					'type': self.basetype}
				raise PredefinedMaskNotFound, tmsg

		# Process each character in mask at a time
		isLiteral = 0
		for ch in mask:
			if ch == '\\':
				isLiteral = 1
			elif isLiteral or ch in self.predefinedLiterals:
				isLiteral = 0
				maskHandler.append(self.literalClass(ch))
			elif self.maskMappings.has_key(ch):
				maskHandler.append(self.maskMappings[ch])
			else:
				tmsg = u_('Unexpected character "%(char)s" in %(type)s mask.') \
					% {'char': ch,
					'type': self.basetype}
				raise InvalidCharInMask, tmsg

		return maskHandler

	# If secondary is true, then use secondary mask (outputMask2)
	def getFormattedOutput(self, secondary=0):
		pass

	def getFormattedInput(self):
		pass


	def setText(self, text):
		self.input = text
		self.display = text
		self.reset()

	def isValid(self):
		return 1

	# Returns (value, formatted text, cursor)
	def addText(self, value, text, pos, replaces=0, padding="_"):
		shift = 0
		cursor = self.cursor
		for size in self.inputDisplayLen:
			shift -= size

		print "Starting cursor: %s; shift: %s" % (cursor, shift)


		value = self.processEdit(value, text, pos, replaces)
		formatted = self.getFormattedInput(value,padding=padding)

		for size in self.inputDisplayLen:
			shift += size

		self.cursor = cursor + shift
		self.moveCursorRelative(0)

		print "Ending cursor: %s; shift: %s" % (self.cursor, shift)

		return (value, formatted, self.cursor)



	# Returns (value, formatted text, cursor)
	def deleteText(self, text, pos, characters):
		pass



	#
	# Given a display cursor, calculate the index into the string
	#
	def cursorToIndex(self, cursor):
		# TODO
		pos = 0
		index = 0
		i = 0
		while ( i < self.inputCount - 1      ) and \
			( cursor < pos + self.inputDisplayLen[i] ) :
			pos += self.inputDisplayLen[i]
			i += 1


		diff = cursor - pos - self.inputDisplayLen[i]
		if diff > self.inputMaskLen[i]:
			diff = self.inputMaskLen[i]

		return max(self.inputMaskPos[i] + diff,0)


	#
	# Given an index into the string, calculate the display cursor,
	#
	def indexToCursor(self, index):

		i = 0
		while ( i < self.inputCount - 1 ) and \
			( index < self.inputMaskPos[i] ) :
			i += 1

		pos = self.inputMaskPos[i]

		diff = index - pos - self.inputMaskLen[i]

		# TODO
		return max(pos + diff,0)


	#
	# Move cursor using relative units
	#
	# If relative > 0, move cursor to the right <relative> units
	# If relative < 0, move cursor to the left |<relative>| units
	# This takes into account Literals, etc.
	#
	def moveCursorRelative(self, relative):

		print "*** moveCursorRelative(%s)" % relative

		# Direction = -1 (left) or 1 (right).
		direction = relative == 0 or int(relative/abs(relative))

		print "relative=%s" % relative
		print "direction=%s" % direction

		self.cursor = self.cursor + relative

		print "cursor #1: %s" % self.cursor

		if self.cursor <= 0:
			self.cursor = 0
			self.direction = 1
		elif self.cursor > len(self.display):
			self.cursor = len(self.display)
			self.direction = -1

		print "cursor #2: %s" % self.cursor

		pos = 0
		section = 0
		while section < self.inputCount and \
			((pos + self.inputDisplayLen[section]) < self.cursor):

			pos += self.inputDisplayLen[section]
			print "%s; %s" %(section, pos)
			section += 1


		print "pos=%s" % pos
		print "section=%s" % pos

		if pos + self.inputFormattedLen[section] == self.cursor:
			print "cursor #2b: %s" % self.cursor
			section += direction

		print "section=%s" % section

		if section == self.inputCount:
			#      self.cursor = pos + self.inputDisplayLen[-1]
			print "cursor #3: %s" % self.cursor
			section -= 1



		print "section=%s" % section
		if isinstance(self.inputHandlers[section], Literal):
			self.moveCursorRelative(direction)
			print "cursor #4: %s" % self.cursor

		self.index = self.cursorToIndex(self.cursor)

		print "New cursor position: %s" % self.cursor

		return self.cursor


	#
	# Move cursor to the beginning of the field
	#
	def moveCursorToBegin(self):

		# Reset cursor to beginning
		self.cursor = 0
		self.index = 0

		# This will handle if the first character is a literal
		# (e.g., for phone numbers (999) 999-9999, this will move
		# to the first '9', not the '('
		return self.moveCursorRelative(0)


	#
	# Move cursor to the beginning of the field
	#
	def moveCursorToEnd(self):

		# Reset cursor to beginning
		self.cursor = self.indexToCursor(self.lastInputPos)

		return self.moveCursorRelative(0)



	#
	# Edit the value
	#
	def processEdit (self, value, str, pos=0, replaces=0):
		print "-"*50
		assert gDebug(7,'processEdit(%s,%s,%s,%s)' % (value,str,pos,replaces))
		nv = value

		if pos == len(nv):
			nv += str
		else:
			nv = "%s%s%s" % (nv[:pos],str,nv[pos+replaces:])

		assert gDebug(7,"inputMaskPos=%s" % self.inputMaskPos)

		print "pos=%s"%pos

		section = 0
		while section < self.inputCount and \
			self.inputMaskPos[section] < pos and \
			self.inputMaskPos[section] > 0:
			section += 1
		i = pos

		# Debug...
		section = 0
		i = 0

		while i < len(nv):
			if not self.inputHandlers[section]\
				.isValidEntry(nv[self.inputMaskPos[section]:i+1]):
				if i == self.inputMaskPos[section] and \
					not isinstance(self.inputHandlers[section],Literal):
					self.inputMaskLen[section] = i - self.inputMaskPos[section]
					return nv
				else:
					self.inputMaskLen[section] = i - self.inputMaskPos[section]
					if section == self.inputCount - 1:
						if i != len(nv)-1:
							return nv
						else:
							break
					else:
						section += 1
						self.inputMaskPos[section] = i
						self.inputMaskLen[section] = 0
			else:
				i += 1

		self.inputMaskLen[section] = i - self.inputMaskPos[section]

		for i in range(section+1, self.inputCount):
			self.inputMaskLen[i] = 0

		self.index = pos + len(value)
		self.cursor = self.indexToCursor(self.index)
		print "after processEdit, index=%s;cursor=%s" % (self.index, self.cursor)

		assert gDebug(7,"<< %s" % nv)
		return nv



# This is a base class for mask elements
class MaskSection:

	def __init__(self):
		self.minLength = 0
		self.maxLength = 0

		self.intersperse = 0
		self.intersperseString = ","
		self.intersperseRepeat = 1


	def getFormattedValue(self):
		return self.value

	def isValidEntry(self, value):
		return 0

	def isCompleteEntry(self, value):
		return len(value) == self.maxLength
