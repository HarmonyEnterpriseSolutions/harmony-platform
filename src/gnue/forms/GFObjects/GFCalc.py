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
# $Id: GFCalc.py,v 1.11 2012/10/10 06:26:15 oleg Exp $
"""
Calculated field
"""

import re
from gnue.common.logic.usercode import UserCode
from gnue.forms.GFObjects.GFObj import UnresolvedNameError

__all__ = ['GFCalc']

# =============================================================================
# <total>
# =============================================================================

class GFCalc(UserCode):

	REC_FIELD = re.compile('(?i)([_A-Z][_A-Z0-9]*)\.([_A-Z][_A-Z0-9]*)')

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		UserCode.__init__(self, parent, "GFCalc")
		self._inits.append(self.__postinit)

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _initialize_(self):
		UserCode._initialize_(self)
		self.compile(['self'])

		# here to listen to all fields in user code
		self.__blocks = {} # used in __postinit
		self.__fields = {}

		fields = set()
		code = self.getChildrenAsContent()
		for m in self.REC_FIELD.finditer(code):
			fields.add(m.groups())

		logic = self.getParent()._form._logic
		for blockName, fieldName in fields:
			try:
				if blockName == 'self':
					block = self.getParent().getBlock()
				else:
					block = logic.getBlock(blockName)
				field = block.getField(fieldName)
			except UnresolvedNameError:
				pass
			else:
				#field.associateTrigger('POST-CHANGE',  self.__on_field_change__post_change)
				#field.associateTrigger('POST-REFRESH', self.__on_field_change__post_refresh)

				# used in __postinit
				self.__blocks[block.name] = block

				fs = self.__fields.get(block.name)
				if fs is None:
					self.__fields[block.name] = fs = []

				fs.append(field.name)

		self.getParent().getBlock().associateTrigger('ON-RECORDLOADED', self.__on_recordloaded)
		self.getParent().getBlock().associateTrigger('ON-NEWRECORD', self.__on_recordloaded)


	def __postinit(self):
		# do this in postinit because have no datasource in _initialize_
		
		for block in self.__blocks.itervalues():
			block.getDataSource().registerEventListeners({ 'dsRecordChanged' : self.__on_recordchange }, user_data=(block.name, self.__fields[block.name]))

		del self.__blocks
		del self.__fields

	def __on_recordloaded(__self, *args, **kwargs):
		#rint"CALC on %s because of ON-RECORDLOADED" % __self.getParent().name, args, kwargs
		# self for calc is block
		result = __self.run(__self.getParent().getParent().get_namespace_object())
		try:
			__self.getParent().set_value(result, enable_change_event=False)
		except AttributeError:
			#block has no rs associated yet
			pass

	def __on_recordchange(__self, event):
		#rint"MAYBE CALC on %s because of dsRecordChanged" % __self.getParent().name, event.record, event.fields, event.user_data

		this_field = __self.getParent()
		this_block = this_field.getParent()

		depend_block_name, depend_field_names = event.user_data

		depend_block = this_block._form._logic.getBlock(depend_block_name)

		# event.fields - field.field that has been changed
		# depend_field_names - field.name that this calc DEPENDS on

		depend_field_fnames = set([depend_block.getField(i).field for i in depend_field_names])

		# check that at list one from event.field are in depend_field_names
		#if not depend_field_fnames.isdisjoint(event.fields):
		if depend_field_fnames.intersection(event.fields):

			#rint"CALC on %s because of dsRecordChanged" % __self.getParent().name, event.record, event.fields, event.user_data

			# self for calc is block
			result = __self.run(this_block.get_namespace_object())
			try:
				this_field.set_value(result, enable_change_event=False)
			except AttributeError:
				#block has no rs associated yet
				#rint"! block has no rs associated yet"
				pass

