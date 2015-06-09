# GNU Enterprise Forms - Display handler - Numeric values
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
# $Id: Numeric.py,v 1.8 2012/10/10 10:15:31 oleg Exp $
"""
DisplayHandler classes for Forms input validation
"""
__revision__ = "$Id: Numeric.py,v 1.8 2012/10/10 10:15:31 oleg Exp $"

import re

from gnue.forms.input.displayHandlers.Cursor import BaseCursor
from decimal import Decimal
import locale

# =============================================================================
# Display handler for numeric values
# =============================================================================


REC_NUMBER = re.compile('^(\D*)(\d*)(\D*)(\d*)$')

class Numeric(BaseCursor):
	"""
	Class to handle the display and entry of numeric fields.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, entry, eventHandler, subEventHandler, display_mask,
		input_mask):

		BaseCursor.__init__(self, entry, eventHandler, subEventHandler,
			display_mask, input_mask)
		if display_mask:
			self._display_mask = display_mask
		else:
			if self.field.scale:
				self._display_mask = '%%.%sf' % self.field.scale
			else:
				self._display_mask = '%d'
		#elif self.field.length:
		#    self._display_mask = '%d'
		#else:
		#    self._display_mask = '%s'

		self.__grouping = gConfigForms('numeric_grouping') or None

		# encoding used to encode locale.format result
		self.__locale_encoding = locale.getlocale()[1] or 'ascii'
		self.__locale_thousands_sep = locale.localeconv()['thousands_sep']


	# -------------------------------------------------------------------------
	# Try to guess what value is meant by a given string
	# -------------------------------------------------------------------------

	def parse_display(self, display):
		"""
		Try to convert the given display string into a number
		"""

		if not display:
			return None

		# space as thousands separator is forced in build_display
		display = display.replace(' ', '').replace("'", '')

		match = REC_NUMBER.match(display)
		if match:
			(sign, whole, dec, frac) = match.groups()
			display = sign + whole
			if frac:
				display += "." + frac

		if self.field.scale == 0:
			return int(display)
		else:
			return Decimal(display)

	# -------------------------------------------------------------------------
	# Create a display string for the current value
	# -------------------------------------------------------------------------

	def build_display(self, value, editing):
		"""
		Create a display string for the current value
		"""
		if value is None:
			return u''

		if editing:
			result = unicode(self._display_mask % value)
		else:
			result = locale.format(self._display_mask, float(value), grouping=self.__grouping)
			if self.__locale_thousands_sep:
				result = result.replace(self.__locale_thousands_sep, ' ')
			result = result.decode(self.__locale_encoding)
		return result
