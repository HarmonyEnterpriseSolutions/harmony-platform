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
# $Id: GFNotebook.py,v 1.3 2009/12/07 14:59:35 oleg Exp $
"""
NoteBook
"""

from gnue.forms.GFObjects.GFContainer import GFContainer
BaseClass = GFContainer

__all__ = ['GFNotebook']

# =============================================================================
# <notebook>
# =============================================================================

class GFNotebook(BaseClass):

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	label = None

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		BaseClass.__init__(self, parent, "GFNotebook")

		self._validTriggers = {
			'PRE-PAGECHANGE'  : 'Pre-PageChange',
			'POST-PAGECHANGE' : 'Post-PageChange',
		}

		self._triggerFunctions = {
			'getSelectedPage' : { 'function' : self.__trigger_getSelectedPage },
		}

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		BaseClass._phase_1_init_(self)

	def getSelectedPage(self):
		uiPage = self.uiWidget._ui_get_selected_page_()
		if uiPage:
			return uiPage._gfObject

	def __trigger_getSelectedPage(self):
		page = self.getSelectedPage()
		if page:
			return page.get_namespace_object()

	def _event_pre_page_change_(self):
		self.processTrigger('PRE-PAGECHANGE', ignoreAbort=False)

	def _event_post_page_change_(self):
		self.processTrigger('POST-PAGECHANGE')
