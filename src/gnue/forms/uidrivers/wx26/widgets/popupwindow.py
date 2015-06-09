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
# $Id: popupwindow.py,v 1.15 2010/02/17 17:24:49 oleg Exp $
"""
"""
import wx
from gnue.forms.uidrivers.wx26.widgets._base import UIHelper
from toolib.wx.controls.PopupControl import PopupControl
from toolib.wx.mixin.TWindowUtils      import getTopLevelParent
from toolib.util.Configurable                import Configurable
from toolib import debug

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UIPopupWindow(UIHelper, Configurable):
	"""
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		UIHelper.__init__(self, event)
	#self._inits.append(self.__tretiaryInit)

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

		assert isinstance(parent, PopupControl), "popupwindow parent must be entry with 'picker' style"

		self._container = self.widget = parent.GetPopupWindow()
		self.widget.SetSizer(wx.BoxSizer(wx.VERTICAL))

		if self._gfObject.title is not None:
			self.widget.SetTitle(self._gfObject.title)
		else:
			self.widget.SetWindowStyleFlag(self.widget.GetWindowStyleFlag() & ~wx.CAPTION)

		parent.SetPopupModal(self._gfObject.modal)

		if hasattr(self._gfObject, 'form'):
			# called once to create popup form
			parent.popupListeners.bind('beforePopup', self.__onBeforePopup_createForm)
		else:
			assert 0, "do we have popupwindow without form?"

		parent.popupListeners.bind('beforePopup',   lambda event: self._gfObject._event_pre_popup())
		parent.popupListeners.bind('afterPopup',    lambda event: self._gfObject._event_post_popup())
		parent.popupListeners.bind('beforePopdown', lambda event: self._gfObject._event_pre_popdown())
		parent.popupListeners.bind('afterPopdown',  lambda event: self._gfObject._event_post_popdown())


	###########################################################################
	# uicontainer interface implementation
	def getFrame(self):
		return self.widget

	def getContainer(self, uiForm):
		return self.widget

	def show(self, uiForm, modal):
		pass

	def close(self, uiForm):
		#uiForm.getMainFrame().Destroy()
		pass

	def setTitle(self, uiForm, title):
		self.getFrame().SetTitle(title)

	#
	###########################################################################

	def add_widgets(self, ui_widget, border=0):
		"""
		Add a given UI widget to the popupwindow.

		@param ui_widget: widget to add to the page
		"""
		self._container.SetContent(ui_widget.widget)

	def _ui_popup_(self):
		self._popupControl().PopUp()

	def _ui_popdown_(self):
		self._popupControl().PopDown()

	def __onBeforePopup_createForm(self, event):
		wx.BeginBusyCursor()
		try:
			parameters = self._gfObject.getParameters()
			
			parameters['p_parentform'] = self._form.get_namespace_object()
			parameters['p_popupwindow'] = self._gfObject.get_namespace_object()

			self.__popupForm = self._form.run_form(self._gfObject.form,	parameters,	gfContainer = self._gfObject)

			if self._gfObject.title is not None:
				self.__popupForm.set_title(self._gfObject.title)

			self._gfObject._event_form_loaded(self.__popupForm)

			# Popup control loses focus when new form popups so bring focus back
			#rint "+ SetFocus in UIPopupWindow.__onBeforePopup_createForm"
			self._popupControl().SetFocus()

			# should fix text selection after focus lose
			p = self._popupControl().GetSelection()[1]
			self._popupControl().SetSelection(p,p)

			self._form.associateTrigger('ON-EXIT', self.__on_exit)

			self.applyConfig()

		finally:
			wx.EndBusyCursor()
			# did it once, so unbind
			self._popupControl().popupListeners.unbind('beforePopup', self.__onBeforePopup_createForm)

	def __on_exit(__self, self):
		__self.saveConfig()
		__self.__popupForm.close()

	##########################################
	# for Configurable
	#
	def getDomain(self):
		return 'gnue'

	def getConfigName(self):
		"""
		Returns the name of the configuration file.
		This is used on the command-line.
		"""
		return self._gfObject._uid_()

	def getDefaultUserConfig(self):
		return {
			'width' : None,
			'height' : None,
		}

	def applyConfig(self):
		w = self.getSetting('width')
		h = self.getSetting('height')
		if w and h:
			self.widget.Size = (w, h)
		else:
			self.widget.Size = (200, 200)

	def saveConfig(self):
		w, h = self.widget.Size
		self.setSetting('width', w)
		self.setSetting('height', h)
		# do not save local conf
		return self.saveUserConfig()

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIPopupWindow,
	'provides' : 'GFPopupWindow',
	'container': 1
}
