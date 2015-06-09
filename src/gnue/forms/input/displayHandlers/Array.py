
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
# Copyright 2002-2007 Free Software Foundation
#
# FILE:
# GFDisplayHandler.py
#
# $Id: Array.py,v 1.1 2009/04/29 14:20:21 oleg Exp $
"""
Text display handler
"""
__revision__ = "$Id: Array.py,v 1.1 2009/04/29 14:20:21 oleg Exp $"

from gnue.forms.input.displayHandlers.Cursor import BaseCursor
import datetime

class fakeSubEventHandler:
	@staticmethod
	def registerEventListeners(events):
		pass

class Array(BaseCursor):
	"""
	Class to handle the display and entry of array fields.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, entry, eventHandler, subEventHandler, display_mask, input_mask):
		BaseCursor.__init__(self, entry, eventHandler, subEventHandler, display_mask, input_mask)
	
		itemtype = entry._field.itemtype

		assert itemtype, 'itemtype not defined for datatype'



		from __init__ import factory
		self.__itemhandler = factory(entry, eventHandler, fakeSubEventHandler, display_mask, input_mask, datatype=itemtype)


	# -------------------------------------------------------------------------
	# Try to guess what value is meant by a given string
	# -------------------------------------------------------------------------

	def parse_display(self, display):
		"""
		Try to convert the given display string into a number
		"""

		print "parse_display", display

		if not display:
			return None

		#res = [self.__convert(self.__itemhandler.parse_display(i.strip())) for i in display.split(',')]
		res = [self.__itemhandler.parse_display(i.strip()) for i in display.split(',')]

		print "RESULT:", res

		return res

	# -------------------------------------------------------------------------
	# Create a display string for the current value
	# -------------------------------------------------------------------------

	def build_display(self, value, editing):
		"""
		Create a display string for the current value
		"""
		print "format_display", value

		if value is None:
			return ''
		return ', '.join([self.__itemhandler.build_display(i, editing) for i in value])

	#def __convert(self, value):
	#	if isinstance(value, datetime.date):
	#		return datetime.datetime(value.year, value.month, value.day)
	#	else:
	#		return value

