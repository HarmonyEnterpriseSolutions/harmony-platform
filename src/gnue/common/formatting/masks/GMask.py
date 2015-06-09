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
# GDataSource.py
#
# DESCRIPTION:
"""
Class that implements a provider-independent DataSource object
"""
# NOTES:
#
# HISTORY:
#

from gnue.common.apps import i18n, errors
from gnue.common.definitions import GObjects
from gnue.common.definitions.GParserHelpers import GContent

class GMask(GObjects.GObj):
	"""
	Class that handles masks in a GObject tree
	"""
	def __init__(self, parent=None, type="GMask"):
		pass


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
		'mask': {
			'BaseClass': GMask,
			'Importable': True,
			'Attributes': {
				'type':        {
					'Label': u_('Mask Type'),
					'Typecast': GTypecast.name,
					'ValueSet': {
						'display':    {'Label': u_('Display/Output')},
						'input':      {'Label': u_('Input Validation/Reformatting')},
						'storage':    {'Label': u_('Storage')},
						'validation': {'Label': u_('Validation')} },
					'Default': 'display' },
				'ParentTags': None,
				'MixedContent': True,
				'Description': 'TODO' },
		} }

	for alteration in updates.keys():
		xmlElements[alteration].update(updates[alteration])


	return xmlElements
