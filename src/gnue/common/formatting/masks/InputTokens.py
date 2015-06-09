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
# pylint: disable-msg=R0903,
#  R0903 disabled as these classes represent placeholders and
#  as such don't have public methods
#
# FILE:
# Tokens.py
#
# DESCRIPTION:
"""
Tokens used to define the components that make up an input mask.

These tokens are used to define the final lexicon used by the
mask.
"""
__revision__ = "$Id$"

from gnue.common.external.plex \
	import Str, State, AnyChar, Rep1, Any, Range, NoCase, Bol, Eol, Opt

import string
import locale

FORCE_UPPER = True
FORCE_LOWER = False

digit = Any(string.digits)
letter = Any(string.letters)

# =============================================================================
# Base tokens
#
# These are inherited be other tokens that are actually
# used in the input mask.  Instances of these classes should not
# be used directly.
# =============================================================================
class Tok:
	"""
	Base token containing all the flags and values that an
	input token may require.
	"""

	# True if this character is optional
	optional = False

	# If set, the character to auto-fill the string with
	autochar = None

	# If set, the mask char to fill the display with
	# (Note: autochar takes precedence; default is _)
	maskchar = None

	# A list of partial grammar rules to
	# build our character-at-a-time parser
	# This list should itself contain lists
	paths = []

	# Number of characters this space takes up
	maxchars = 1

	# Left pad with zeros
	# (only makes sense if maxchars > 1)
	zero_pad = False

	# As implied...
	force_upper = False
	force_lower = False

	def __repr__(self):
		return "%s(%s)" % (self.__class__.__name__, self.symbol)

	def getProperDisplay(self, text):
		if self.zero_pad and self.maxchars == 2 and len(text) == 1:
			return "0" + text
		else:
			return text

class TextTok(Tok):
	"""
	Base text token
	"""

class DateTok(Tok):
	"""
	Base date token
	"""

class NumTok(Tok):
	"""
	Base numeric token
	"""

class LitTok(Tok):
	"""
	Base literal token
	"""
	optional = True
	def __repr__(self):
		"""
		Force the class to return a custom string representation of itself.
		Not sure why yet.
		"""
		return "%s(%s)" % (self.__class__.__name__, self.autochar)


class forcible:
	"""
	This is a placeholder for the paths=[]
	that denotes when a mask can be considered complete
	*if* a forced marker is provided.
	"""

# =============================================================================
# Base tokens
# =============================================================================
class tChar(TextTok):
	"""
	Any character, required
	"""
	symbol = '_'
	paths = [[Any(string.letters + string.digits + ' ' + string.punctuation)]]

class tCharOpt(tChar):
	"""
	Any character, optional
	"""
	symbol = '?'
	optional = True

class tA(TextTok):
	"""
	Any alphanumeric, required
	"""
	symbol = 'A'
	paths = [[Any(string.letters + string.digits)]]

class ta(tA):
	"""
	Any alphanumeric, optional
	"""
	symbol = 'a'
	optional = True

class tL(TextTok):
	"""
	Any letter, required
	"""
	symbol = 'L'
	paths = [[letter]]

class tl(tL):
	"""
	Any letter, optional
	"""
	symbol = 'l'
	optional = True

class tC(TextTok):
	"""
	Any character (alphanum) or space, required
	"""
	symbol = 'C'
	paths = [[Any(string.letters + string.digits + ' ')]]

class tc(tC):
	"""
	Any character (alphanum) or space, optional
	"""
	symbol = 'c'
	optional = True

class tsign(NumTok):
	"""
	Positive or negative sign (one per mask) (literal)
	"""
	symbol = '-'
	optional = True
	paths = [[Any('+-')]]

class tDigit(NumTok):
	"""
	Any digit, required
	"""
	symbol = '0'
	paths = [[digit]]
#  optional=True  # For input masks, this is largely true?

class tDigitOpt(tDigit):
	"""
	Any digit, optional
	"""
	symbol = '#'
	optional = True

class tM(DateTok):
	"""
	Month, with zero padding
	"""
	symbol = 'M'
	maxchars = 2
	zero_pad = True
	paths = [ [ Str('1'), forcible, Any('012') ], # months 1, 10 - 12
		[ Str('0'), Range('19') ],          # months 01 - 09
		[ Range('29') ] ]                   # months 2 - 9

class tm(tM):
	"""
	Month, no zero padding
	"""
	symbol = 'm'

class tD(DateTok):
	"""
	Day
	"""
	symbol = 'D'
	zero_pad = True
	maxchars = 2
	paths = [ [ Str('3'), forcible, Any('01') ], # days 3, 30 - 31
		[ Any('12'), forcible, digit ],    # days 1, 2, 10 - 29
		[ Str('0'), Range('19')],          # days 01 - 09
		[ Range('49') ] ]                  # days 4 - 9

class td(tD):
	"""
	Day, no zero padding
	"""
	symbol = 'd'

class tY(DateTok):
	"""
	Year - 4 digits
	"""
	symbol = 'Y'
	maxchars = 4
	paths = [ [ digit ]*4 ]

class ty(DateTok):
	"""
	Year - 2 digits
	"""
	symbol = 'y'
	maxchars = 2
	paths = [ [ digit ]*2 ]

class tH(DateTok):
	"""
	Hour
	"""
	symbol = 'H'
	maxchars = 2
	paths = [ [ Str('2'), forcible, Any('0123') ], # Hour 2, 20-23
		[ Any('01'), forcible, digit ],     # Hour 00 - 19
		[ Range('39') ] ]                   # Hour 3 - 9

class tI(DateTok):
	"""
	Minute
	"""
	symbol = 'I'
	maxchars = 2
	paths = [ [Any('012345'), digit ] ]

class tS(DateTok):
	"""
	Seconds
	"""
	symbol = 'S'
	maxchars = 2
	paths = [ [ Any('012345'), digit ] ]

class tP(DateTok):
	"""
	PM AM token
	"""
	symbol = 'P'
	maxchars = 2
	paths = [ [ NoCase(Str('p','a')), NoCase(Str('m')) ] ]
	force_upper = True

class tp(tP):
	"""
	pm am token
	"""
	symbol = 'p'
	maxchars = 2
	force_lower = True

class tLiteral(LitTok):
	def __init__(self, char):
		path = []

		for ch in char:
			path.append(Str(ch))
		if len(char) == 1:
			self.symbol = "\\%s" % char
		else:
			self.symbol = '"' + char.replace('\\','\\\\').replace('"','\\"') + '"'
		self.paths = [path]
		self.autochar = char

class tDecSep(LitTok):
	"""
	Decimal separator
	"""
	symbol = '.'
	autochar = locale.localeconv()['decimal_point'] or '.'
	paths = [[Str(autochar)]]

class tThouSep(LitTok):
	"""
	Thousands separator
	"""
	symbol = ','
	autochar = locale.localeconv()['thousands_sep'] or ','
	paths = [[Str(autochar)]]

class tTimeSep(LitTok):
	"""
	Time Separator
	"""
	symbol = ':'
	autochar = ':'  # TODO: *Where* is this in locale?!?!?
	#       >>> locale.nl_langinfo(locale.T_FMT) ?
	paths = [[Str(autochar)]]


class tDateSep(LitTok):
	"""
	Date Separator
	"""
	symbol = '/'
	autochar = '/' # TODO: *Where* is this in locale?!?!?
	# >>> locale.nl_langinfo(locale.D_FMT) ?
	paths=[[Str(autochar)]]

class tCustom(TextTok):
	"""
	Custom text token
	(Passed in a set of valid characters)
	"""
	def __init__(self, chars):
		self.paths = [[Any(chars)]]

class tCustomNum(NumTok):
	"""
	Custom numeric token
	(Passed in a set of valid digits)
	"""
	def __init__(self, chars):
		self.paths = [[Any(chars)]]
		self.symbol = '[%s]' % chars.replace('\\','\\\\').replace(']','\\]').replace('-','\\-')

# ---------------------------------------------------------------------------
# Map of tokens to classes
# ---------------------------------------------------------------------------
tokenMap = {
	# Input/output tokens
	'_':  tChar,    # Any character, required
	'?':  tCharOpt, # Any character, optional
	'A':  tA,       # Any alphanumeric, required
	'a':  ta,       # Any alphanumeric, optional
	'L':  tL,       # Any letter, required
	'l':  tl,       # Any letter, optional
	'C':  tC,       # Any character (alphanum) or space, required
	'c':  tc,       # Any character (alphanum) or space, optional
	'+':  tsign,    # Positive or negative sign (one per mask)
	'0':  tDigit,   # Any digit, required
	'#':  tDigitOpt, # Any digit, optional
	'M':  tM,       # Month, zero padding
	'D':  tD,       # Day, zero padding
	'Y':  tY,       # Year - 4 digits
	'y':  ty,       # Year - 2 digits
	'H':  tH,       # Hour
	'I':  tI,       # Minute
	'S':  tS,       # Seconds
	'P':  tP,       # PM AM token
	'p':  tp,       # pm am token
	'.':  tDecSep,  # Decimal separator
	',':  tThouSep, # Thousands separator
	':':  tTimeSep, # Time Separator
	'/':  tDateSep, # Date Separator
	# Output-only
	'm':  tm,       # Month, no zero padding
	'd':  td,       # Day, no zero padding
}

# =============================================================================
# Module level functions
# =============================================================================
def buildSingleValidationRule(token, honorOptional = True):
	"""
	Build a validation rule for a specific token
	"""
	val = None
	for ruleset in token.paths:
		v2 = v3 = None
		startoptional = False
		for rule in ruleset:
			if rule == forcible:
				startoptional = True
				continue
			if startoptional:
				if v3 is None:
					v3 = rule
				else:
					v3 = v3 + rule
			else:
				if v2 is None:
					v2 = rule
				else:
					v2 = v2 + rule
		if v3 is not None:
			v2 = v2 + v3
		if val is None:
			val = v2
		else:
			val = val | v2
	if honorOptional and token.optional:
		return Opt(val)
	else:
		return val

def buildValidationRule(tokens):
	"""
	Take a list of tokens and combine all their rule paths
	into a single rule that validates whether a string is
	"complete" wrt the input mask or not.
	"""
	val = Bol
	for token in tokens:
		val = val + buildSingleValidationRule(token)
	if not tokens:
		val = val + Rep1(AnyChar)
	return val + Eol


# =============================================================================
# Debugging functions
# =============================================================================
def printLexiconTree(lexicon, indent = 0):
	"""
	Function useful for debuging.
	"""
	for foo in lexicon:
		if isinstance(foo, State):
			print (" "*indent) + ("State: %s" % str((foo.name)))
			printLexiconTree(foo.tokens, indent + 2)
		elif type(foo) == type(()) and len(foo) == 2:
			print " "*indent + str(foo[0])
		else:
			print " "*indent + str(foo)
