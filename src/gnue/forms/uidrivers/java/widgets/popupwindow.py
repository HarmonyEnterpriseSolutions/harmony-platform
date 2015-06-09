# GNU Enterprise Forms - wx 2.6 UI Driver - Box widget
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
# $Id: popupwindow.py,v 1.8 2011/07/14 14:09:12 oleg Exp $
"""
"""
from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import EntryPicker, PopupWindow

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UIPopupWindow(UIWidget):
	"""
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		UIWidget.__init__(self, event)
		self.__popupForm = None
		self.__callAfter = None

	# -------------------------------------------------------------------------
	# Create a wx box widget
	# -------------------------------------------------------------------------

	def _popupControl(self):
		return self._gfObject.getParent().uiWidget.widget

	def _create_widget_ (self, event):
		"""
		@param event: the creation-event instance carrying information like
		        container (parent-widget)
		@returns: wx widget
		"""
		parent = self._popupControl()

		assert isinstance(parent, EntryPicker), "popupwindow parent must be entry with 'picker' style"

		self._container = self.widget = PopupWindow(self, parent)

		#if self._gfObject.title is not None:
		#	self.widget.SetTitle(self._gfObject.title)
		#else:
		#	self.widget.SetWindowStyleFlag(self.widget.GetWindowStyleFlag() & ~wx.CAPTION)

		self.widget.uiSetModal(self._gfObject.modal)

		#if hasattr(self._gfObject, 'form'):
		#	# called once to create popup form
		#	parent.popupListeners.bind('beforePopup', self.__onBeforePopup_createForm)

		#parent.popupListeners.bind('beforePopup',   lambda event: self._gfObject._event_pre_popup())
		#parent.popupListeners.bind('afterPopup',    lambda event: self._gfObject._event_post_popup())
		#parent.popupListeners.bind('beforePopdown', lambda event: self._gfObject._event_pre_popdown())
		#parent.popupListeners.bind('afterPopdown',  lambda event: self._gfObject._event_post_popdown())


	###########################################################################
	# uicontainer interface implementation
	def getFrame(self):
		return self.widget

	def getUiForm(self):
		return self

	def getContainer(self, uiForm):
		return self.widget

	def show(self, uiForm, modal, afterModal):
		pass

	def close(self, uiForm):
		self.widget.uiClose()

	def setTitle(self, uiForm, title):
		self.widget.uiSetTitle(title)

	#
	###########################################################################

	def addWidget(self, ui_widget):
		"""
		Add a given UI widget to the popupwindow.

		@param ui_widget: widget to add to the page
		"""
		self._container.uiAdd(ui_widget.widget)

	def _ui_popup_(self):
		self.widget.uiPopup()

	def _ui_popdown_(self):
		self.widget.uiPopdown()

	def _ui_call_after_(self, f, *args, **kwargs):
		assert self.__callAfter is None
		self.__callAfter = f, args, kwargs
		self.getFrame().uiCallAfter()

	def onCallAfter(self):
		assert self.__callAfter is not None
		try:
			f, args, kwargs = self.__callAfter
			f(*args, **kwargs)
		finally:
			self.__callAfter = None

	def onPopup(self, popup):
		if popup:
			self._gfObject._event_pre_popup()
			if self.__popupForm is None:

				parameters = self._gfObject.getParameters()

				parameters['p_parentform'] = self._form.get_namespace_object()
				parameters['p_popupwindow'] = self._gfObject.get_namespace_object()

				self.__popupForm = self._form.run_form(self._gfObject.form, parameters,	gfContainer = self._gfObject)
        
				if self._gfObject.title is not None:
					self.__popupForm.set_title(self._gfObject.title)
        
				self._gfObject._event_form_loaded(self.__popupForm)
        
				# Popup control loses focus when new form popups so bring focus back
				#rint "+ SetFocus in UIPopupWindow.__onBeforePopup_createForm"
				#self._popupControl().SetFocus()
        
				# should fix text selection after focus lose
				#p = self._popupControl().GetSelection()[1]
				#self._popupControl().SetSelection(p,p)
        
				self._form.associateTrigger('ON-EXIT', self.__on_exit)
			
			self._gfObject._event_post_popup()
		else:
			self._gfObject._event_pre_popdown()
			self._gfObject._event_post_popdown()

	def __on_exit(__self, self):
		"""
		application exits. close popup form
		"""
		#__self.saveConfig()
		__self.__popupForm.close()


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIPopupWindow,
	'provides' : 'GFPopupWindow',
	'container': 1
}
