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
# InputMask.py
#
# DESCRIPTION:
"""
Input masks for GNUe Forms, et al

Based on lex/yacc parsing (via Plex)
"""

__revision__ = "$Id$"

from cStringIO import StringIO
import pprint

from src.gnue.common.formatting.masks.Errors import *
import MaskTokenizer
import MaskTokens
import InputTokens


class InputMask:
	"""
	All functions return a tuple containing
	(displayed representation, cursor position)
	or can raise InvalidInputCharacter
	"""

	# Handle via gConfig?
	placeholder = "_"


	####################################################################
	#
	#  Editing calls
	#
	def begin(self, value=None):
		"""
		Resets the mask processor.

		@type value: string
		@param value: Not used
		"""
		self.text = ""
		self.cursor = 0
		self.waitingForRTL = self.rtl_pos
		components = [None]*len(self.tokens)
		self._parseInput(self.text)
		return self._adjustCursor(0)

	def add(self, text, replace=0):
		"""
		Insert text character
		"""
		disp = ""
		emptyDisplay = self.emptyDisplay
		inputted = self.inputted
		tokens = self.tokens
		last_token = len(tokens) - 1
		i = 0
		##    print
		##    print "Cursor=%s" % self.cursor
		while i <= last_token:
			if isinstance(self.tokens[i], InputTokens.LitTok):
				if len(disp) < self.cursor:
					disp += emptyDisplay[i]
			else:
				if self.inputted[i]:
					disp += inputted[i]
			i += 1

		##    print "DISP=%s" % disp
		newtxt = disp[:self.cursor] + text + disp[self.cursor + replace:]
		##    print "NEW=%s" % newtxt
		##    print newtxt
		self._parseInput(newtxt)
		##    print self.cursor + len(text) - replace
		if text:
			return self._adjustCursor(self.cursor + len(text) - replace)
		else:
			return (self.display, self.cursor)

	def delete(self):
		"""
		Delete forwards
		"""
		return self.add("", 1)

	def backspace(self):
		"""
		Delete backwards
		"""
		cursor = self.cursor
		display, cursor2 = self._adjustCursor(self.cursor-1, True)
		if cursor != cursor2:
			return self.add("", 1)

	def _parseInput(self, newtext=""):
		"""
		Parses an input string into its components
		and sets the resultant display

		@type newtext:  string
		@param newtext: The text to add via the input mask
		"""

		cursor = self.cursor

		tokens = self.tokens
		inputted = [""] * len(self.tokens)
		inputted_states = []
		for f in range(len(self.tokens)):
			inputted_states.append([])

		first_state = 0
		last_state = -1
		if newtext:
			scanner = Scanner(self.lexicon, StringIO(newtext), newtext)
			try:
				while True:
					parsed, extra = scanner.read()
					print parsed, extra
					if parsed is None:
						last_state = self.eof_nextstate[0]
						break
					else:
						state, char = parsed
						mstate = state[0]
						inputted_states[mstate].append(state)
						inputted[mstate] += char
						if first_state is None:
							first_state = mstate

			except Errors.PlexError, msg:
				import sys
				mesg = u_("input error:\n%(exType)s\n%(exMessage)s") \
					% {'exType'   : sys.exc_info ()[0],
					'exMessage': sys.exc_info ()[1]}
				print mesg
				raise InvalidInputCharacter, msg


		# Calculate the last token's position (including any literals)
		numtokens = len(self.tokens)
		last_token = numtokens - 1
		last_pos = last_token

		while last_pos > 0 and not inputted[last_pos]:
			last_pos -= 1

		if last_pos < last_token and isinstance(tokens[last_pos+1], InputTokens.LitTok):
			last_pos += 1
			while last_pos < last_token and \
				isinstance(tokens[last_pos], InputTokens.LitTok):
				last_pos += 1


		# Wait until after any exceptions are raised
		# before storing state variables (in case input
		# was invalid, we still have the old, valid input
		# to refer to for future cursor movement.
		self.inputted = inputted
		self.last_state = last_state
		self.first_state = first_state
		self.last_pos = last_pos

		#
		# Calculate the displayed text, with any placeholders
		#
		disp = ""
		emptyDisplay = self.emptyDisplay
		actualDisplay = self.actualDisplay = []
		for i in range(len(self.tokens)):
			if isinstance(tokens, InputTokens.LitTok):
				actualDisplay.append(emptyDisplay[i])
				inputted[i] = ""
			else:
				if not inputted[i]:
					actualDisplay.append(emptyDisplay[i])
				else:
					if i == last_state:
						# The last input token may not be complete,
						# so add any extra _ placeholders.
						actualDisplay.append(inputted[i] + emptyDisplay[i][len(inputted[i]):])
					else:
						oi = inputted[i]
						ni = tokens[i].getProperDisplay(inputted[i])
						self.cursor += len(ni) - len(oi)
						inputted[i] = ni
						actualDisplay.append(inputted[i])

		self.display = "".join(actualDisplay)

		return (self.display, self.cursor)

	# ---------------------------------------------------------------------------
	# Cursor positioning functions
	# ---------------------------------------------------------------------------
	def move(self, pos):
		"""
		Move the cursor to a new position.
		Usually results from a mouse click.
		pos is a physical cursor position; the
		internal code calculates the logical
		position and, hence, the actual new
		physical position.
		"""
		return self._adjustCursor(pos)

	def moveLeft(self):
		"""
		Move the cursor left one character. The
		internal code calculates the logical
		position and, hence, the actual new
		physical position.
		"""
		return self._adjustCursor(self.cursor-1, True)

	def moveRight(self):
		"""
		Move the cursor right one character. The
		internal code calculates the logical
		position and, hence, the actual new
		physical position.
		"""
		return self._adjustCursor(self.cursor+1)

	def moveHome(self):
		"""
		Move the cursor to the beginning of
		the text. The internal code calculates
		the logical position and, hence, the
		actual new physical position.
		"""
		return self._adjustCursor(0)

	def moveEnd(self):
		"""
		Move the cursor to the end of the
		text. The internal code calculates
		the logical position and, hence,
		the actual new physical position.
		"""
		return self._adjustCursor(len(self.display))


	def _adjustCursor(self, pos, left=False):
		"""
		Moves the cursor to a new position.
		"""

		if pos < 0:
			pos = 0

		##    print "Pos=%s" % pos
		##    print "Adjusting cursor to %s" % pos

		rpos = 0
		token_at = 0
		tokens = self.tokens
		last_token = len(tokens) - 1
		while rpos < pos and token_at < last_token:
			rpos += len(self.actualDisplay[token_at])
			token_at += 1

		if rpos > pos:
			# This can happen if a token is partially complete
			token_at -= 1
		elif rpos + len(self.inputted[token_at]) < pos:
			# This can happen at the end of the string
			pos = rpos + len(self.inputted[token_at])

		##    print "Token at %s, pos=%s, rpos=%s" % (token_at, pos, rpos)

		if left:
			while token_at > 0 and isinstance(self.tokens[token_at], InputTokens.LitTok):
				pos -= len(self.emptyDisplay[token_at])
				token_at -= 1
		else:
			while token_at < last_token and \
				isinstance(self.tokens[token_at], InputTokens.LitTok):
				pos += len(self.emptyDisplay[token_at])
				token_at += 1


		##    print "Deciding on %s" % pos
		self.cursor = pos
		return (self.display, pos)


	def _generateInputTokens(self, maskTokens):
		"""
		Creates an input token list from a mask token list.

		Input tokens represent

		@param maskTokens: The list of mask tokens used to build the
		                   input token list
		@type maskTokens: List of InputToken instances
		"""
		i = 0
		inputTokens = []

		while i < len(maskTokens):
			ptoken=maskTokens[i]
			if isinstance(ptoken , MaskTokens.Literal):
				chars = ""
				# Merge consecutive literals into one rule to simplify logic
				while i < len(maskTokens) and \
					isinstance(maskTokens[i], MaskTokens.Literal):
					chars += maskTokens[i].token
					i += 1
				token = InputTokens.tLiteral(chars)
				i -= 1 # Because we add one later...
			elif isinstance(ptoken , MaskTokens.TokenSet):
				if ptoken.numeric:
					token = InputTokens.tCustomNum(ptoken.token)
				else:
					token = InputTokens.tCustom(ptoken.token)
			else:
				token = InputTokens.tokenMap[ptoken.token]()

			# Honor force_upper/lower
			try:
				if ptoken.force_upper:
					token.force_upper = True
				elif ptoken.force_lower:
					token.force_lower = True
			except AttributeError:
				pass

			# Save token
			inputTokens.append(token)

			# Calculate "empty" displayed value
			if token.maskchar:
				self.emptyDisplay.append(token.maskchar)
			elif token.autochar:
				self.emptyDisplay.append(token.autochar)
			else:
				self.emptyDisplay.append(self.placeholder*token.maxchars)

			i += 1

		return inputTokens

	def _generateLexicon(self, tokens):
		"""
		Build a lexicon from a list of input tokens
		"""
		# We start at the end of the mask and work backwards, as
		# any optional mask tokens will need to reference the
		# next token's initial grammar elements.
		#
		# Each position in the input mask gets it's own lexicon state
		#
		# First each rules are created in with state name format of
		# (position #, path #, rule #)
		# Then they are merged into a single entry per position
		#
		# Each path represents one text string which would
		# pass the lexicons test.

		tokenIndex = len(tokens)

		lexicon = [
			# The first rule will always be Bol (to init stuff)
			State("", [(Bol, Begin((0,0,0))) ]),
			# The final rule prevents any trailing characters
			# The Eof is just a dummy rule that won't ever be matched.
			State((tokenIndex,0,0), [(Eof, IGNORE)])
		]

		leadin = []
		last_leadin = []

		while tokenIndex > 0:
			# Iterate backward through the tokens in the input mask
			tokenIndex -= 1
			currentToken = tokens[tokenIndex]
			if not currentToken.optional:
				leadin = []

			# Iterate forward through each token's path lists (ruleset) =======

			lexiconStateCount = 0 # used in the naming of the next
			# valid lexicon state

			for ruleset in currentToken.paths:
				ks = 0
				possibly_completed = False  # Once a ruleset encounters an object
				# of class forcible then it is possible
				# that the ruleset may possibly be complete

				# Iterate forward through the ruleset and define a (pattern, action)
				# tuple (rule) for the lexicon we are constructing
				for rulesetIndex in range(len(ruleset)):
					path = ruleset[rulesetIndex]
					lexi = []

					# See if the current rule may be the last one needed
					# to complete the ruleset
					try:
						possibly_completed = possibly_completed or \
							ruleset[rulesetIndex+1]== InputTokens.forcible
					except IndexError:
						pass

					# Add the rule, skipping any class foricble items
					# as they are not actually tokens
					if not path == InputTokens.forcible:

						if (rulesetIndex < len(ruleset) - 1):
							# There are additional items in this ruleset so
							# set the next state to point to the next rule in the
							# set
							next_state = (tokenIndex, lexiconStateCount, ks+1)
						else:
							# There are no additional rules in this ruleset so
							# set the next state to the next character's tokens
							next_state = (tokenIndex+1,0,0)

						# Construct the lexicon pattern (rule) and store with a
						# lambda based action function.  Note that the lambda
						# isn't executed at this time so p and t arguments below
						# are the scanner(parser), text arguments that plex will pass to
						# the action function
						rule = (path,
							lambda p, t, st=(tokenIndex, lexiconStateCount, ks), ns=next_state:
							self._tokenFound(p, t, st, ns))

						# Store the first rule of each path list
						if rulesetIndex == 0:
							leadin.append(rule)

						# Add the rule to the list of rules to be inserted into
						# our generated lexicon
						lexi.append(rule)

						# If no more characters are required then
						# add in the start points from the previous token's
						# paths (rulesets)
						if possibly_completed:
							lexi += last_leadin

						# I
						if lexiconStateCount or ks:
							lexicon.append((State((tokenIndex, lexiconStateCount, ks), lexi)))
						ks += 1
				lexiconStateCount += 1

			# Append the created state to the main lexicon
			# we are creating
			lexicon.append(State((tokenIndex,0,0), leadin[:]))
			last_leadin = leadin # Assign the current leadin to previous leadin
		# this will be used in the next iteration to
		return lexicon

	# ===========================================================================
	#  Internal lexicon init crap
	# ===========================================================================

	def __init__(self, mask, numeric=False, date=False):
		"""
		InputMask constructor

		InputMasks can be of 3 differnt types (text, numeric, and date).  The type of
		input mask is determined by the boolean values of the numeric and date
		arguments to the constructor.  The default mask type is text but if either
		of the two booleans are set then the mask type switchs to that.

		When building an input mask 2 token lists are built.  The initial token list
		is created from the mask text passed into the constructor.  This mask token
		list is then used to create a list of input tokens.  Input tokens contain
		the lexicon rules required to

		@param mask: The input mask the initialized instance of the class should
		             support
		@param numeric: Is this input mask numeric input only?
		@param date: Is this input mask date input only?
		"""

		# -------------------------------------------------------------------------
		# Generate a list of parser tokens that define the input mask
		# -------------------------------------------------------------------------
		#
		parser = MaskTokenizer.MaskTokenizer(mask,'inline')

		self.pp = pprint.PrettyPrinter(indent=4)
		self.isnumeric = numeric
		self.isdate = date

		# If non-zero, position of the right-to-left token
		rtl_pos = self.rtl_pos = parser.rtl_pos

		# Set the type of input mask based upon
		# the parser text, numeric, or date
		self.type = parser.type

		validationRule = None

		# This contains a list of each token's "empty" marker,
		# which will usually be '_' or, if a literal, the literal's
		# value.
		self.emptyDisplay = []

		# List of all tokens. Note that all {#}
		# expansions have already happened.
		self.tokens = tokens = self._generateInputTokens(parser.tokens)
		lexicon = self._generateLexicon(tokens)

		InputTokens.printLexiconTree(lexicon)

		# Create a consolidated validation rule so we
		# can test if inputted string is "complete".  This
		# creates the single rule for each position.
		self.validationRule = InputTokens.buildValidationRule(tokens)

		# Pre-compile the lexicon for this mask
		DEBUG=StringIO()
		self.lexicon = Lexicon(lexicon, DEBUG)
		DEBUG.seek(0)
	##    print DEBUG.read()

	def _tokenFound(self, parser, text, curstate, nextstate):
		"""
		Function called when an input character matches a token.
		It is defined as the action for every pattern in the
		lexicon.

		I believe this function returns the current state that
		matched as well as the text.  It then sets the plex
		scanner to the next valid state.

		My current thinking is the input mask system changes state
		based upon every character input into the system.
		"""
		parser.produce((curstate,text))
		parser.begin(nextstate)
		self.eof_nextstate = nextstate


class EOF:
	"""
	Internal class used to return an EOF to our input loop.
	"""
	def __init__(self, state):
		self.state = state
