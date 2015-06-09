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
# $Id: mdi_notebook.py,v 1.31 2013/12/03 19:58:32 Oleg Exp $
"""
"""

import wx
import wx.aui

from gnue.forms.uidrivers.wx26.widgets import _base
from toolib.wx.mixin.TWindowUtils      import getTopLevelParent
from gnue.common.logic.language        import AbortRequest
from toolib.util import strings

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
		self.__selectedUiForm = None
		self.__exiting = False

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
				| (wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB if self._gfObject.closable else 0)
				| wx.WANTS_CHARS
			)
		)
		
		self.getParent().add_widgets(self)

		self.widget.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.__on_page_close, self.widget)
		self.widget.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.__on_page_changed, self.widget)

		self._gfObject._form.associateTrigger('PRE-EXIT', self.__on_form_pre_exit)


	def _get_selected_panel(self):
		selection = self.widget.GetSelection()
		if selection >= 0:
			return self.widget.GetPage(selection)


	###########################################################################
	# uicontainer interface implementation
	def getFrame(self):
		return self._form.uiWidget.getFrame()

	def getContainer(self, uiForm):
		panel = self._get_selected_panel()
		if panel and panel._lazy_:
			panel._uiForm_ = uiForm
			self.__containers[uiForm] = panel
			return panel
		else:
			#rint "getContainer"
			panel = wx.Panel(self.widget, -1, style=wx.WANTS_CHARS)
			panel.Hide()
			panel.SetSizer(wx.BoxSizer(wx.VERTICAL))
			panel._uiForm_ = uiForm
			panel._lazy_ = False
			self.__containers[uiForm] = panel
			return panel

	def show(self, uiForm, modal=False):
		#rint "show"
		container = self.__containers[uiForm]

		# know previous page to select if this closed
		index = self.widget.GetSelection()
		if index >= 0:
			container._prev_ = self.widget.GetPage(index)
		else:
			container._prev_ = None

		panel = self._get_selected_panel()
		if panel and panel._lazy_:
			panel._lazy_ = False
			panel.Layout()
		else:
			self.widget.AddPage(container, strings.shorten(uiForm._gfObject.title, self._gfObject.max_title_length))
			self.widget.SetSelection(self.widget.GetPageCount()-1)

	def close(self, uiForm):

		container = self.__containers.pop(uiForm)	# forget about container
		container._uiForm_ =  None	# just to break reference

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
			self.widget.SetPageText(index, strings.shorten(title, self._gfObject.max_title_length))

	#
	###########################################################################


	def __on_form_pre_exit(__self, self):
		# close current page until no pages left or user cancels
		self = __self
		self.__exiting = True
		try:
			while self.widget.GetPageCount():
				container = self.widget.GetPage(self.widget.GetSelection())
				if container._lazy_:
					self.widget.RemovePage(self.widget.GetPageIndex(container))
					container.Destroy()
				else:
					form = container._uiForm_._gfObject
					form.close()
					if form.is_visible():
						# form close canceled
						raise AbortRequest(u_('Exit cancelled, changes not saved'))
		finally:
			self.__exiting = False

	def __on_page_close(self, event):
		#rint "__on_page_close", event.GetEventObject().GetPage(event.GetInt())._uiForm_._gfObject
		# call logic
		try:
			event.GetEventObject().GetPage(event.GetInt())._uiForm_._gfObject.close()
		finally:
			# page will be closed via close method
			event.Veto()


	def __on_page_changed(self, event):
		# TODO: set bars

		#event.GetEventObject().GetPage(event.GetInt())._uiForm_.setTool

		panel = self.widget.GetPage(event.GetInt())
		if panel._lazy_:
			if self.__exiting:
				panel._on_page_selected_ = None
			else:
				on_page_selected = panel._on_page_selected_
				panel._on_page_selected_ = None
				if on_page_selected:
					on_page_selected()
		else:
			self.__ui_form_selected(panel._uiForm_)
		event.Skip()

	def __ui_form_selected(self, uiForm):
		#rint '__ui_form_selected', uiForm
		if self.__selectedUiForm is not uiForm:
			(uiForm or self._form.uiWidget).updateBars()
			self.__selectedUiForm = uiForm
			self._gfObject._event_form_selected()

	# -------------------------------------------------------------------------
	# Indicate whether this box is vertically growable
	# -------------------------------------------------------------------------

	def is_growable(self):
		return True

	###########################################################################
	# Interface to GFMDINotebook
	#

	def _ui_get_current_form_(self):
		selection = self.widget.GetSelection()
		if selection >= 0:
			uiForm = self.widget.GetPage(selection)._uiForm_
			# check to workaround #466
			if uiForm is not None:
				return uiForm._gfObject

	def _ui_select_form_(self, name):
		"""
		name is form name
		"""
		for i in xrange(self.widget.GetPageCount()):
			page = self.widget.GetPage(i)
			for uiForm, container in self.__containers.iteritems():
				if page is container and uiForm._gfObject.name == name:
					self.widget.SetSelection(i)
					return True
		return False

	def _ui_add_lazy_page_(self, title, on_page_selected):
		panel = wx.Panel(self.widget, -1)
		panel.Hide()
		panel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		panel._lazy_ = True
		panel._on_page_selected_ = on_page_selected
		self.widget.AddPage(panel, strings.shorten(title, self._gfObject.max_title_length))
		

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIMDINotebook,
	'provides' : 'GFMDINotebook',
	'container': 0,
}
