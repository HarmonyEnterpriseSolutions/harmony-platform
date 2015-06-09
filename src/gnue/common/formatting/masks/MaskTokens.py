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
# MaskTokens.py
#
# DESCRIPTION:
"""
Tokens returned by the mask tokenizer.

These tokens are used by an input mask to create a set of InputTokens.
"""
__revision__ = "$Id$"

class BaseToken:
	"""
	Basic parser token class.

	Not used directly,  but inherited by the other defined tokens
	Literal, Token, etc.
	"""
	numeric = False
	date    = False
	text    = False
	literal = False
	token   = False

	def __init__(self, base_token, override_token=None): # , *args):
		"""
		Token construtor
		"""
		if override_token is not None:
			self.token = override_token
		else:
			self.token = base_token

# -----------------------------------------------------------------------------
# Standard token classes
# -----------------------------------------------------------------------------
class Token(BaseToken):
	"""
	Class typically used to create normal tokens as
	opposed to special tokens like literal.

	It sets the standard options so that each individual
	token class doesn't need to.
	"""
	force_lower = False
	force_upper = False
	token = True

class NumberToken(Token):
	"""
	Numeric token (#9-,.)
	"""
	numeric = True

class DateToken(Token):
	"""
	Date token (MDYyHIS:/)
	"""
	date = True

class TextToken(Token):
	"""
	Text token

	A test token represents 1 standard alphanumeric character.
	"""
	text = True

class TokenSet(Token):
	"""
	Token defined by user with [] notation.
	Can behave like a  NumberToken or TextToken,
	depending on contents of [].
	"""
	def __init__(self, token): # , *args):

		Token.__init__(self, token) #, *args)

		# Are we all-numeric?
		self.numeric = token.isdigit()
		self.token = token

		if not self.numeric:
			self.text = True

# -----------------------------------------------------------------------------
# Special token classes
# -----------------------------------------------------------------------------
class Literal(BaseToken):
	"""
	A literal string that the developer wants in the string.
	Note that for our purposes, the basic "literals" aren't
	really Literals(), but special cases of Token classes.
	So all literals represented by this class are denoted
	with \ or "" syntaxes.
	"""
	literal = True

class RightToLeft(BaseToken):
	"""
	Temporary token class used to note the
	position of ! modifiers
	"""
	numeric = True

class CaseModifier:
	"""
	Temporary token class used to record > and <
	markers. These cause the modified token to have
	either force_upper or force_lower set, so the
	other classes won't ever see CaseModifier
	instances.
	"""
	def __init__(self):
		pass

class Repeater:
	"""
	Temporary token class used to record {#}
	markers. These are replaced with the actual
	represented tokens before being passed out
	of MaskParser (i.e., 0{3} would be returned
	as 000, so the other classes won't ever see
	Repeater instances.
	"""
	def __init__(self, count):
		self.count = count
