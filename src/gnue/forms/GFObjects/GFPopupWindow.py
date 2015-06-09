# GNU Enterprise Forms - GF Object Hierarchy - Parameters
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
# $Id: GFPopupWindow.py,v 1.11 2010/03/03 15:01:09 oleg Exp $


"""
part of form to be inside popup window
TODO: move form loading here from uiwidget
"""

from gnue.forms.GFObjects.GFContainer import GFContainer
BaseClass = GFContainer


class GFPopupWindow(GFContainer):

	# default attributes
	title = None
	parameters = {}

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None, name="GFPopupWindow"):
		GFContainer.__init__(self, parent, name)

		self._validTriggers = {
			'PRE-POPUP'     : 'Pre-Popup',
			'POST-POPUP'    : 'Post-Popup',

			'PRE-POPDOWN'   : 'Pre-Popdown',
			'POST-POPDOWN'  : 'Post-Popdown',
		}

		self._triggerFunctions = {
			'popup': {'function': self.popup},
			'popdown': {'function': self.popdown},

			'setParameter' : {'function': self.__trigger_setParameter},
		}

		self._triggerProperties = {
			'form': {
				'get': lambda self: self.form,
				'set': self.__trigger_setForm,
			},
		}

		self.__form = None

		# holds parameter values before popup form created
		# after form creation this dict is useless
		self.__parameters = {}

	def popup(self):
		self.uiWidget._ui_popup_()

	def popdown(self):
		self.uiWidget._ui_popdown_()

	#def __trigger_getForm(self):
	#	if self.getForm() is not None:
	#		return self.getForm().get_namespace_object()

	def __trigger_setForm(self, form):
		self.form = form

	def getForm(self):
		return self.__form

	def _event_form_loaded(self, form):
		"""
		popupwindow ui has been loaded form
		"""
		self.__form = form

	# uiwidget popup/popdown
	def _event_pre_popup(self):
		self.processTrigger('PRE-POPUP')

	def _event_post_popup(self):
		#self.getForm().initFocus()
		self.__form.processTrigger('On-Popup')
		self.processTrigger('POST-POPUP')

	def _event_pre_popdown(self):
		self.processTrigger('PRE-POPDOWN')

	def _event_post_popdown(self):
		self.processTrigger('POST-POPDOWN')

	def __trigger_setParameter(self, name, value):
		if self.__form:
			self.__form.set_parameters({name : value})
		else:
			self.__parameters[name] = value

	def getParameters(self):
		"""
		called once when popup form creating to obtain static parameters and parameters set before first popup
		"""
		assert self.__form is None, 'getParameters is not actual after popup form created'
		parameters = dict(self.parameters)
		parameters.update(self.__parameters)
		return parameters
