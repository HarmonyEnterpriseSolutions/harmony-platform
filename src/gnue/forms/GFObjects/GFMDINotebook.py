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
# $Id: GFMDINotebook.py,v 1.15 2012/04/10 17:46:27 oleg Exp $
"""
NoteBook
"""

from gnue.forms.GFObjects.GFContainer import GFContainer
BaseClass = GFContainer

__all__ = ['GFMDINotebook']

# =============================================================================
# <notebook>
# =============================================================================

class GFMDINotebook(BaseClass):

	# -------------------------------------------------------------------------
	# Attributes
	# -------------------------------------------------------------------------

	label = None
	max_title_length = None
	closable = True

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		BaseClass.__init__(self, parent, "GFMDINotebook")

		# triggers
		self._validTriggers = {
			'ON-SELECTFORM' : 'On-SelectForm',
		}

		self._triggerFunctions = {
			'run_form'        : { 'function' : self.run_form },
			'run_form_lazy'   : { 'function' : self.run_form_lazy },
			'selectForm'      : { 'function' : self.__trigger_selectForm },
			'getSelectedForm' : { 'function' : self.__trigger_getCurrentForm },
		}

		# form url to form name mapping
		self.__formUrl2Name = {}

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		BaseClass._phase_1_init_(self)

	def run_form(self, url, parameters=None):
		self._form.event_begin()
		try:
			form = self._form.run_form(url, parameters, gfContainer = self)
			self.__formUrl2Name[url] = form.name
		finally:
			self._form.event_end()

	def run_form_lazy(self, title, url, parameters=None):
		self.uiWidget._ui_add_lazy_page_(title, lambda: self.run_form(url, parameters))

	def getCurrentForm(self):
		return self.uiWidget._ui_get_current_form_()

	def __trigger_getCurrentForm(self):
		form = self.getCurrentForm()
		if form:
			return form.get_namespace_object()

	def __trigger_selectForm(self, url):
		if url in self.__formUrl2Name:
			return self.uiWidget._ui_select_form_(self.__formUrl2Name[url])
		else:
			return False

	def _event_form_selected(self):
		self.processTrigger('ON-SELECTFORM')
