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
# $Id: _aui_mdi_notebook.py,v 1.3 2008/11/04 20:14:19 oleg Exp $
"""
"""

import wx
import wx.aui

from gnue.forms.uidrivers.wx26.widgets import _base
from toolib.wx.mixin.TWindowUtils      import getTopLevelParent
from gnue.common.logic.language        import AbortRequest

__all__ = ["UIMDINotebook"]

MdiNotebookClass = wx.aui.AuiNotebook

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UIMDINotebook (_base.UIHelper):
	"""
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		_base.UIHelper.__init__(self, event)

		self.__containers = {}
		self.__titles = {}
		self.__selectedUiForm = None

	# -------------------------------------------------------------------------
	# Create a wx box widget
	# -------------------------------------------------------------------------

	def _create_widget_ (self, event):
		"""
		@param event: the creation-event instance carrying information like
		        container (parent-widget)

		@returns: wx widget
		"""
		self._container = self.widget = wx.aui.AuiNotebook(event.container,
			style = (
				wx.NO_BORDER
				| wx.aui.AUI_NB_TOP
				| wx.aui.AUI_NB_TAB_SPLIT
				| wx.aui.AUI_NB_TAB_MOVE
				| wx.aui.AUI_NB_SCROLL_BUTTONS
				| wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
			)
		)
		self.getParent().add_widgets(self)

		self.widget.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.__on_page_close, self.widget)
		self.widget.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.__on_page_changed, self.widget)

		self._gfObject._form.associateTrigger('PRE-EXIT', self.__on_form_pre_exit)


	###########################################################################
	# uicontainer interface implementation
	def getFrame(self):
		return self._form.uiWidget.getFrame()

	def getContainer(self, uiForm):
		#rint "getContainer"
		panel = wx.Panel(self.widget, -1)
		panel.Hide()
		panel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		panel._uiForm_ = uiForm
		self.__containers[uiForm] = panel
		return panel

	def show(self, uiForm, modal=False):
		#rint "show"
		self.widget

		container = self.__containers[uiForm]

		# know previous page to select if this closed
		index = self.widget.GetSelection()
		if index >= 0:
			container._prev_ = self.widget.GetPage(index)
		else:
			container._prev_ = None

		self.widget.AddPage(container, self.__titles.get(uiForm, uiForm._gfObject.title))
		self.widget.SetSelection(self.widget.GetPageCount()-1)

	def close(self, uiForm):

		container = self.__containers.pop(uiForm)	# forget about container
		container._uiForm_ =  None	# just to break reference

		# break reference for gc
		self.__titles.pop(uiForm, None)

		# select previous page
		prev = container._prev_
		while prev:
			index = self.widget.GetPageIndex(prev)
			if index >= 0:
				self.widget.SetSelection(index)
				break
			else:
				prev = prev._prev_

		# remove this
		self.widget.RemovePage(self.widget.GetPageIndex(container))
		container.Destroy()

		if self.widget.GetPageCount() == 0:
			self.__ui_form_selected(None)

		uiForm._forgetUiContainer()


	def setTitle(self, uiForm, title):
		index = self.widget.GetPageIndex(self.__containers[uiForm])
		if index >= 0:
			self.widget.SetPageText(index, title)
		else:
			# called before show
			self.__titles[uiForm] = title

	#
	###########################################################################


	def __on_form_pre_exit(__self, self):
		# close current page until no pages left or user cancel
		while __self.widget.GetPageCount():
			form =  __self.widget.GetPage(__self.widget.GetSelection())._uiForm_._gfObject
			form.close()
			if form.is_visible():
				# form close cancelled
				raise AbortRequest(u_('Exit cancelled, changes not saved'))


	def __on_page_close(self, event):
		#rint "__on_page_close", event.GetEventObject().GetPage(event.GetInt())._uiForm_._gfObject
		# call logic
		event.GetEventObject().GetPage(event.GetInt())._uiForm_._gfObject.close()
		# page will be closed via close method
		event.Veto()


	def __on_page_changed(self, event):
		# TODO: set bars

		#event.GetEventObject().GetPage(event.GetInt())._uiForm_.setTool

		self.__ui_form_selected(self.widget.GetPage(event.GetInt())._uiForm_)
		event.Skip()

	def __ui_form_selected(self, uiForm):
		#rint '__ui_form_selected', uiForm
		if self.__selectedUiForm is not uiForm:
			(uiForm or self._form.uiWidget).updateBars()
			self.__selectedUiForm = uiForm

	# -------------------------------------------------------------------------
	# Indicate whether this box is vertically growable
	# -------------------------------------------------------------------------

	def is_growable(self):
		return True

	###########################################################################
	# Interface to GFMDINotebook
	#
	def _ui_add_form(self, url, parameters):

		try:
			wx.BeginBusyCursor()
			form = self._form.run_form(url, parameters, gfContainer = self._gfObject)
		finally:
			wx.EndBusyCursor()

	def _ui_get_current_form_(self):
		if self.widget.GetPageCount():
			return self.widget.GetPage(self.widget.GetSelection())._uiForm_._gfObject



# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIMDINotebook,
	'provides' : 'GFMDINotebook',
	'container': 0,
}
