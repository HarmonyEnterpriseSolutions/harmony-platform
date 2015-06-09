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
# pylint: disable-msg=W0402,
#   W0402 is disabled as the only obsolete module (as of 4/12/06)
#   is the string module which is used for string.digits
#
# FILE:
# MaskParser
#
# DESCRIPTION:
"""
A parser which takes a text based mask and generates a list of
token class instances that represent that mask.  Any repeaters
found in the mask ({3}) are replaced with the appropriate number
of tokens so that the mask class will not have to deal with
them.

Valid tokens include:

"""
__revision__ = "$Id$"

import string
import StringIO

from gnue.common.external.plex import \
	Scanner, Lexicon, Errors, \
	Str, Begin, State, AnyChar, Rep1, Any
from gnue.common.formatting.masks.Errors import MaskDefinitionError
from gnue.common.formatting.masks import MaskTokens

class MaskTokenizer(Scanner):
	"""
	Custom plex scanner used to contstruct a token list which represents
	an input mask.  This token list is used by the input mask to define
	valid input for each position of the input.

	Takes a file handle containing an input mask and creates a
	list of Tokens which define the input mask
	"""
	def get_type(self):
		"""
		Returns the apparent type of this mask.

		@rtype: string
		@return: The value 'text', 'numeric', or 'date'
		"""
		return self.type

	def get_tokens(self):
		"""
		Returns a list of the tokens after parsing the input mask.

		@rtype: list
		@return: The list of tokens
		"""
		return self.tokens[:]

	# =========================================================================
	# Private stuff
	# =========================================================================

	# -------------------------------------------------------------------------
	# Lexicon action functions
	# -------------------------------------------------------------------------
	def _check_single(self, text):
		"""
		Function to add single instance tokens to the input mask.

		A single instance token is something that can appear only once
		in an input mask.
		"""
		if text in self.__singles:
			raise Errors.UnrecognizedInput(self, \
					'Mask can only have one "%s" token' %text)
		self.__singles.append(text)
		if text == '!':
			self.produce (MaskTokens.RightToLeft(text))
		elif text in '.+,':
			self.produce(MaskTokens.NumberToken(text))
		else:
			self.produce(MaskTokens.TextToken(text))

	def _literal(self, text):
		"""
		A text literal that should appear as is in the mask
		"""
		self.produce(MaskTokens.Literal(text))

	def _literal_2nd(self, text):
		"""
		Closes the literal string
		"""
		return self._literal(text[1:])

	def _escape(self, text):
		"""
		An escaped character such as \$ to display a $
		"""
		self.begin('')
		self.produce(MaskTokens.Literal(text))

	def _repeater(self, text):
		"""
		Action to process an input mask repeater.

		A repeater tells the parser to repeat the previous token a
		specified number of times.

		@param text: The value pulled from between the {} which
		             denotes the number of times to repeat.
		"""
		self.produce(MaskTokens.Repeater(int(text)))

	def _begin_set(self, text):
		"""
		Action to process the start of a set of valid characters.

		The scanner will be placed into set state and the list
		of valid characters will be reset.
		"""
		self.begin('set')
		self._set = ""

	def _add_set(self, text):
		"""
		Action to add a character to the set currently being constructed.

		Only called when the scanner is in state "set".

		The character read will be added to the character sting
		containing the possible valid values.
		"""
		self._set += text

	def _add_set_2nd(self, text):
		"""
		Action to add a special character to a set being built.

		Used when an escaped set character \[ or \] is found
		in the list of valid characters to be added to the set
		"""
		return self._add_set(text[1:])

	def _end_set(self, text):
		"""
		Action to process the end of a set.

		Only called when the scanner is in state "set".

		The list of possible characters that were defined in the set will be used
		to build an instance of a TokenSet class.  As part of this function the
		scanner will set to default state.
		"""
		self.begin('')
		self.produce(MaskTokens.TokenSet(self._set))

	# =========================================================================
	# Lexicon defintions
	# =========================================================================
	#
	# -------------------------------------------------------------------------
	# Base Lexicon definition
	# -------------------------------------------------------------------------
	# This lexicon is the base used by all masks
	#

	_lexicon = [
		# ---------------------------------------------------------------------
		# Default state definitions
		# ---------------------------------------------------------------------
		(Str('\\'),          Begin('escape')),   # found \, set state to escape
		#
		(Str("'"),           Begin('quoted')),   # found ', set state to quoted
		#
		(Str('"'),           Begin('quoted2')),  # found ", set state to qoute2
		#
		(Str('{'),           Begin('repeater')), # found {, set state to
		# repeater
		#
		(Str('['),           _begin_set),        # found [, execute _begin_set
		# the function will set state
		# to set when executed
		#
		(Str(' '),           MaskTokens.Literal),# found a space, return a
		# literal char instance
		#
		(Any('+.,'),         _check_single),     # these characters can appear
		# only once in an input mask
		#
		(Any('_?AaLlCc'),    MaskTokens.TextToken), # found a text character
		# return a text token
		# instance
		#
		(Any('MDYyHISPp:/'), MaskTokens.DateToken), # found a date character
		# return a date token
		# instance
		#
		(Any('#0'),          MaskTokens.NumberToken), # found a number character
		# return a number token
		# instance
		#
		(Any('<>'),          MaskTokens.CaseModifier), # found a case modifier
		# return case modifier
		# instance

		# ---------------------------------------------------------------------
		# Escape State
		# ---------------------------------------------------------------------
		# The escape state is entered whenever a backslash is encountered while
		# in the default state.  It's purpose is to allow the placement of what
		# would normally be reserved characters into the input mask
		#
		State('escape',  [
				(AnyChar,        _escape), # No matter which character is next
			# execute _escape, the function will
			# create a literal instance and set
			# the state back to default
			]),

		# ---------------------------------------------------------------------
		# Quoted state
		# ---------------------------------------------------------------------
		# The quoted state is entered whenever a single quote is encountered
		# thile in the default state.  It's purpose is to allow quoted strings
		# inside the input mask to sent through as their literal value
		#
		State('quoted',  [
				(Str("\\")+Str("'"), _literal_2nd), # Handle \' in the string
				(Str("'"),           Begin('')),    # found ', set state to default
				(AnyChar,            _literal)      # Process as literal character
			]),

		# ---------------------------------------------------------------------
		# quote2 state
		# ---------------------------------------------------------------------
		# This works the exact same way as the quoted state but is used
		# when a double quote is encountered.  ' and " get seperate states
		# so that one type can always enclose the other
		#
		# Example : "Today's date: "
		#
		State('quoted2',  [
				(Str("\\")+Str('"'), _literal_2nd), # Handle \" in the string
				(Str('"'),           Begin('')),    # found ", set state to default
				(AnyChar,            _literal)      # Process as literal character
			]),

		# ---------------------------------------------------------------------
		# repeater state
		# ---------------------------------------------------------------------
		# The repeater state is entered whenever a { is encountered
		# while in the default state.  This state allows an input
		# mask to include a number inside of {} to cause the previous
		# token to repeat
		#
		# Example : A{5} is the same as AAAAA
		#
		State('repeater',  [
				(Str('}'),                 Begin('')),# found }, set state to
				# default
				(Rep1(Any(string.digits)), _repeater) # grab all digits inside
			# the {} execute _repeater,
			# the function will recreate
			# a repeater instance
			# containing the obtained
			# number
			]),

		# ---------------------------------------------------------------------
		# Set state
		# ---------------------------------------------------------------------
		# The set state is entered whenever a [ is encountered while in the
		# default state.  This provides basic regex set support where any
		# character inside the [] is matched.
		#
		# Example : [ABCDEF]
		#
		State('set',  [
				(Str("\\")+Any('[]'),  _add_set_2nd), #
				(Str(']'),             _end_set),     #
				(AnyChar,              _add_set)      #
			]),
	]

	# -------------------------------------------------------------------------
	# Additional lexicon definitions for input masks
	# -------------------------------------------------------------------------
	_extra_lexicon = [
		(Any('!'),        _check_single),
	]

	def __process(self, token):
		"""
		Adds a token class instance to this instances list of tokens.

		As token instances are generated from the input mask they
		are processed and then added to the scanners working list
		of tokens.  Special tokens such as repeater and case modifiers
		are processed during this state.
		"""

		if isinstance(token, MaskTokens.Repeater):
			# If the incoming token is a repeater then replace
			# the repeater with the appropriate number of the
			# previous token.
			for unused in range(0, token.count-1):
				self.__process(self.__last)

		elif isinstance(token, MaskTokens.CaseModifier):
			# If then incomming token is a case modifier
			# then add the modifier token to the list of
			# modifiers stored in the scanner
			self.__modify.append(token)
		else:
			# Standard tokens
			if self.__modify and isinstance(token, MaskTokens.TextToken):
				# If a case modifier is stored and the incoming
				# token is text then force case based upon the
				# modifier
				mod = self.__modify.pop(0)
				if mod.token == '<':
					token.force_upper = True
				elif mod.token == '>':
					token.force_lower = True

			self.tokens.append(token)

		# TODO: Should this be storing modifiers and the like? It is.
		self.__last = token

	def __init__(self, mask_text, name):
		"""
		Input mask scanner constructor.

		The input mask scanner will create a list of class instances
		that describe the input mask.

		@type mask_text: string
		@param mask_text: The text to be used as the mask
		@type name: string
		@param name: The name of the input mask(TODO: ?)
		"""
		self._set = ""
		self.__singles = []
		self.tokens = []
		self.__last = None  # The last token generated from the input mask
		self.__modify = []

		mask = StringIO.StringIO(mask_text)

		# ---------------------------------------------------------------------
		# Read the input mask and convert into instances of Token classes
		# ---------------------------------------------------------------------
		try:
			Scanner.__init__(self,
				Lexicon(self._lexicon + self._extra_lexicon),
				mask, name)

			while True:
				token, unused = self.read()
				if token is None:
					break

				# Process the returned token
				self.__process(token)

		except Errors.PlexError, msg:
			raise MaskDefinitionError, msg

		if self.__modify:
			print "WARNING: Modifier found at end of mask."

		# ---------------------------------------------------------------------
		# Build a count of the various token types created during parsing
		# ---------------------------------------------------------------------
		#
		num_markers   = 0 # Number of numeric token instances found
		date_markers  = 0 # Number of date token instances found
		text_markers  = 0 # Number of text token instances found
		rtl_pos = -1      # Right to left token
		# TODO: Unknown functionality at this time

		for (position, token) in enumerate(self.tokens):
			if isinstance(token, MaskTokens.RightToLeft):
				rtl_pos = position
			if not isinstance(token, MaskTokens.Literal):
				if token.numeric:
					num_markers += 1
				elif token.date:
					date_markers += 1
				else:
					text_markers += 1

		# Check for "!" in non-numeric mask
		if rtl_pos >= 0:
			self.tokens.pop(rtl_pos)
		else:
			rtl_pos = 0

		self.rtl_pos = rtl_pos

		# ---------------------------------------------------------------------
		# Check for errors and mixed marker types
		# ---------------------------------------------------------------------
		#
		# TODO: I'm not sure we should block mixed input types
		#
		#if not (num_markers or date_markers or text_markers):
		#raise MaskDefinitionError, 'Mask has no character tokens'

		#if (num_markers) and (date_markers or text_markers):
		#raise MaskDefinitionError, \
		#'Numeric mask %s has non-numeric tokens' % mask_text

		#if (date_markers) and (num_markers or text_markers):
		#raise MaskDefinitionError, 'Date/Time mask has non-date tokens'

		# ---------------------------------------------------------------------
		# Set the type of parser based upon the marker counts
		# ---------------------------------------------------------------------
		# If any two of these are non-zero, then the mask is a text mask,
		# not date or numeric.
		#
		if (num_markers and date_markers) or text_markers:
			self.type = 'text'
		elif num_markers:
			self.type = 'numeric'
		else:
			self.type = 'date'
