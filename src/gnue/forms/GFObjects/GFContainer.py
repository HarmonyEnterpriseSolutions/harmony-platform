# GNU Enterprise Forms - GF Object Hierarchy - Container Objects
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
# $Id: GFContainer.py,v 1.2 2008/11/04 20:14:15 oleg Exp $
"""
A base class for all GFObjects that can be containers
"""

from gnue.forms.GFObjects.GFObj import GFObj
from gnue.forms.GFObjects.GFTabStop import GFTabStop

# =============================================================================
# Base class for container objects
# =============================================================================

class GFContainer (GFObj):
	"""
	A base class for all GFObjects that can be containers
	"""

	# -------------------------------------------------------------------------
	# Determine the focus order of a given list of entries
	# -------------------------------------------------------------------------

	def get_focus_order(self, list=None):
		"""
		Builds a list of objects ordered in the way in which they should receive
		focus.

		@param list: An optional list of objects to scan for focus
		@return: A list of objects in the order that they should receive focus
		"""

		# A list of tab stops in the form that do not have a focus order.
		missingFocusOrder = []

		# A list of tab stops in the form that have a focus order.  Stored in
		# the format [focusOrder, [tabstops]]
		hasFocusOrder = []

		# If no list passed then use the instances built in children list
		if list is None:
			list = self._children

		# Build the missing and has focus lists
		for child in list:
			if isinstance(child, GFContainer):
				tabStops = child.get_focus_order()
			elif isinstance(child, GFTabStop):
				tabStops = [child]
			else:
				tabStops = None  # Things like labels

			if bool(tabStops):
				try:
					index = child.focusorder - 1
					hasFocusOrder.append([index, tabStops])
				except AttributeError:
					missingFocusOrder.append(tabStops)

		# Sort the focus stops on items that had defined focus order
		hasFocusOrder.sort()

		# Create a None filled list that will contain all the tab stops
		maxFocusIndex = hasFocusOrder and hasFocusOrder[-1][0] or 0
		totalLength = len(hasFocusOrder) + len(missingFocusOrder)
		workingList = [None] * max(maxFocusIndex + 1, totalLength)

		# Merge in the items with defined focus orders
		for index, tabStop in hasFocusOrder:
			workingList[index] = tabStop

		# Merge in the items missing defined focus orders where ever there is a
		# gap.
		while bool(missingFocusOrder):
			tabStop = missingFocusOrder.pop(0)
			workingList[workingList.index(None)] = tabStop

		# Remove any None entries in the list. This would happen if the
		# focusorder settings skipped numbers.
		returnValue = []
		for tabStop in workingList:
			if tabStop is not None:
				returnValue.extend(tabStop)

		return returnValue
