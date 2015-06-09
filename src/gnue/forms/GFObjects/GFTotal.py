# GNU Enterprise Forms - GF Object Hierarchy - Box
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
# $Id: GFTotal.py,v 1.9 2008/11/04 20:14:16 oleg Exp $
"""
Splitter
"""

import operator
#from GFObj import GFObj as BaseClass
from gnue.common.logic.usercode import UserCode as BaseClass


__all__ = ['GFTotal']

# =============================================================================
# <total>
# =============================================================================

class GFTotal(BaseClass):

	OPERATIONS = {
		#          reduce function          filter function           start value
		#          -----------------------  ------------------------  -----------
		'sum'   : (lambda r, x: r + x,      lambda x: x is not None,  0          ),
		'count' : (lambda r, x: r + 1,      lambda x: True,           0          ),
		'min'   : (lambda r, x: min(r, x),  lambda x: x is not None,  None       ),
		'max'   : (lambda r, x: max(r, x),  lambda x: x is not None,  None       ),

	# assume start value to be first value if start value is None
	}

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		BaseClass.__init__(self, parent, "GFTotal")

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	#def _phase_1_init_(self):
	#	BaseClass._phase_1_init_(self)

	def _initialize_(self):
		BaseClass._initialize_(self)
		self.compile([])

		self.__resultSet = None
		self.__field = None

		for source in self.source.split(','):
			blockName, fieldName = source.strip().split('.')
			block = self.getParent()._form._logic.getBlock(blockName)

			block.getDataSource().registerEventListeners({
					'dsResultSetActivated': self.__ds_resultset_activated,  # from datasources.GDataSource
					'dsResultSetChanged'  : self.__ds_resultset_activated,  # -/-
				})

			assert self.__field is None or self.function == 'usercode', "multiple source in totals requires function='usercode'"
			self.__field = block.getField(fieldName)
			self.__field.associateTrigger('POST-CHANGE', self.__on_field_change)

	def __ds_resultset_activated(self, event):
		self.__resultSet = event.resultSet
		self.__refresh()

	def __on_field_change(__self, *args, **kwargs):
		# 'self' is trigger namespace field object
		if __self.__resultSet:
			__self.__refresh()

	def __calculate(self):
		reduceFn, filterFn, startValue = self.OPERATIONS[self.function]

		columnName = self.__field.field

		values   = (row[columnName] for row in self.__resultSet if not row.isEmpty())
		filtered = (i for i in values if filterFn(i))

		try:
			if startValue is None:
				startValue = filtered.next()
				assert not isinstance(startValue, float), 'must be decimal!'
		except StopIteration:
			return None
		else:
			return reduce(reduceFn, filtered, startValue)

	def __refresh(self):
		if self.function == 'usercode':
			total = self.run()
		else:
			total = self.__calculate()

		try:
			self.getParent().set_value(total)
		except AttributeError:
			#block has no rs associated yet
			pass
