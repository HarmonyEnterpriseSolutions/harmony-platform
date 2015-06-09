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
# Copyright 2000-2007 Free Software Foundation
#
# FILE:
# GMenu.py
#
# DESCRIPTION:
# Class that implements a basic menu system
#
# NOTES:
#
# HISTORY:
#

from gnue.common.definitions import GObjects
import sys, string
from gnue.common.datasources import GConnections
from gnue.common.formatting import GTypecast
from gnue.common.datasources import GConditions

# Depreciated. Will be removed with 0.7


########################################################################
#
# Class that handles Menus.  This is a subclass of GObj, which
# means this class can be created from XML markup and stored in an
# Object tree (e.g., a Forms tree).
#
########################################################################

class GMenu(GObjects.GObj):
	#TODO: Designer expects types of GXtype and strips the first
	#TODO: 2 chars.  So we have to add a placeholer G to the type :(
	def __init__(self, parent=None, type="GGMenu"):
		GObjects.GObj.__init__(self, parent, type)

		#
		# trigger support
		#
		self._triggerProperties = {'enabled':{'set':self.setEnabled,
				'get':self.getEnabled
			},
		}
		self._triggerFunctions = {'fire':{'function':self.fireMenuItem,
			},
		}
	def setEnabled(self, value):
		self._enabled = value

	def getEnabled(self):
		return self._enabled

	def fireMenuItem(self):
		print "You're fired!"

######
#
# Used by client GParsers to automatically pull supported xml tags
#
######

#
# Return any XML elements associated with
# GDataSources.  Bases is a dictionary of tags
# whose values are update dictionaries.
# For example: bases={'datasource': {'BaseClass':myDataSource}}
# sets xmlElements['datasource']['BaseClass'] = myDataSource
#
def getXMLelements(updates={}):

	xmlElements = {
		'menu': {
			'BaseClass': GMenu,
			'Attributes': {
				'name':        {
					'Required': 1,
					'Unique':   1,
					'Typecast': GTypecast.name },
				'label':        {
					'Typecast': GTypecast.name},
				'trigger':      {
					'Typecast': GTypecast.name },
				'type':      {
					'Typecast': GTypecast.name },
				'leader':      {
					'Typecast': GTypecast.text },
				'event':      {
					'Typecast': GTypecast.text },
				'location':      {
					'Typecast': GTypecast.text },
				'enabled': {
					'Typecast': GTypecast.boolean,
					'Default': 0 } },
			'ParentTags': None ,
		}}

	for alteration in updates.keys():
		xmlElements[alteration].update(updates[alteration])

	return xmlElements
