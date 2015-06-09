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
# masks.py
#
# DESCRIPTION:
"""
Input masks for GNUe Forms, et al
Based on lex/yacc parsing (via Plex)

Programs should use InputMask() or FormatMask()
to create masks.  Then, the internal library manager
will reuse existing masks if possible.
"""
# NOTES:
#
from src.gnue.common.formatting.masks import InputMask as _InputMask

__all__ = ['InputMask', 'FormatMask']


class MaskLibrary:
	"""
	Convenience class that keeps track of any existing mask definitions,
	so we don't have to duplicate mask instances if we've already
	encountered one before.
	"""
	def __init__(self):
		self._inputMaskMap = {}
		self._maskMap = {}

	def getInputMask(self, mask, style="default", numeric=False, date=False):
		key = (numeric, date, mask)
		try:
			handler = self._inputMaskMap[key]
			assert gDebug(7,'Reusing existing mask for %s' % mask)
		except KeyError:
			assert gDebug(7,'Creating mask handler for %s' % mask)
			handler = self._inputMaskMap[key] = _InputMask(mask, numeric, date)
		return handler

	def getFormatMask(self, mask, style="default", ):
		try:
			handler = self._maskMap[mask]
			assert gDebug(7,'Reusing existing mask for %s' % mask)
		except KeyError:
			assert gDebug(7,'Creating mask handler for %s' % mask)
			handler = self._maskMap[mask] = None
		return handler

	def getValidationMask(self, mask, style="default", ):
		try:
			handler = self._maskMap[mask]
			assert gDebug(7,'Reusing existing mask for %s' % mask)
		except KeyError:
			assert gDebug(7,'Creating mask handler for %s' % mask)
			handler = self._maskMap[mask] = None
		return handler


#
# Create an internal cache of initialized masks, so we can reuse them.
#
library = MaskLibrary()
InputMask = library.getInputMask
FormatMask = library.getFormatMask
ValidationMask = library.getValidationMask
