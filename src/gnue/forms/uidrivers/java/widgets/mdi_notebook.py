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
# $Id: mdi_notebook.py,v 1.13 2012/04/10 18:02:17 oleg Exp $
"""
"""


from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import NotebookCloseable, Panel
from gnue.common.logic.language import AbortRequest



# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UIMDINotebook(UIWidget):
	"""

	Exit chain:
		P __on_form_pre_exit								# if not self.__allClosed call uiExit and abort exit
		J	uiExit
		P		onPageClose(container, exiting=True)		# self.__exiting = True, if no pages left, self.__allClosed = True
		P			close(uiForm)
	 -> J				uiRemovePage(container, exiting=True)	# calls onExit(newCurrent=None)
	|	P					onExit(container)					# call container form.close() or this form.close()
	 -- P						close(uiForm)

	# method 2, buggy
		P __on_form_pre_exit								# if not self.__allClosed call uiExit and abort exit
		P	selected form.close()							# set self.__exiting = True, close current form, abort exit; if no pages left, self.__exiting = False and do not abort
		P		close(uiForm)
	 -> J			uiRemovePage(container, exiting=True)	# calls onExit(newCurrent=None)
	|	P				onExit(container)					# call container form.close() or this form.close()
	 -- P					close(uiForm)

	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		UIWidget.__init__(self, event)

		self.__containers = {}			# { uiForm    : container }
		self.__uiForms = {}				# { container : uiForm    }
		self.__prevContainers = {}		
		self.__selectedContainer = None
		self.__selectedUiForm = None
		
		# implies onPageClosed behaviour
		self.__exiting = False

		# implies exit trigger behaviour
		self.__allClosed = False

	# -------------------------------------------------------------------------
	# Create a wx box widget
	# -------------------------------------------------------------------------

	def _create_widget_ (self, event):
		"""
		@param event: the creation-event instance carrying information like
		        container (parent-widget)

		@returns: wx widget
		"""
		self._container = self.widget = NotebookCloseable(self, self._gfObject.closable)
		self.getParent().addWidget(self)

		self._gfObject._form.associateTrigger('PRE-EXIT', self.__on_form_pre_exit)


	###########################################################################
	# uicontainer interface implementation
	def getFrame(self):
		return self._form.uiWidget.getFrame()

	def getUiForm(self):
		return self._form.uiWidget

	def _get_selected_panel(self):
		return self.__selectedContainer
	
	def getContainer(self, uiForm):
		"""
		returns container for uiForm
		"""
		panel = self._get_selected_panel()
		if panel and panel._lazy_:
			self.__uiForms[panel] = uiForm
			self.__containers[uiForm] = panel
			return panel
		else:

			#rint "getContainer"
			container = Panel(self)
			container._lazy_ = False
			self.__uiForms[container] = uiForm
			self.__containers[uiForm] = container
			return container

	def show(self, uiForm, modal, afterModal):
		"""
		modal must be False and afterModal must be None
		"""
		#rint "show"

		assert not modal, "mdi notebook can't show modal dialogs"
		assert afterModal is None

		container = self.__containers[uiForm]

		# know previous page to select if this closed
		#index = self.widget.GetSelection()
		#if index >= 0:
		#	self.__prevContainers[] = self.widget.GetPage(index)
		#else:
		#	container._prev_ = None

		panel = self._get_selected_panel()
		if panel and panel._lazy_:
			panel._lazy_ = False
		else:
			self.widget.uiAddPage(container, uiForm._gfObject.title, uiForm._gfObject.description or '')
			self.widget.uiSelectPage(container)

	def close(self, uiForm):

		container = self.__containers.pop(uiForm)	# forget about container
		del self.__uiForms[container]    # just to break reference

		# select previous page
		#prev = container._prev_
		#while prev:
		#	index = self.widget.GetPageIndex(prev)
		#	if index >= 0:
		#		self.widget.SetSelection(index)
		#		break
		#	else:
		#		prev = prev._prev_

		# remove this
		self.widget.uiRemovePage(container, self.__exiting)

		uiForm._forgetUiContainer()


	def setTitle(self, uiForm, title):
		container = self.__containers[uiForm]
		self.widget.uiSetPageText(container, title)

	#
	###########################################################################


	def __on_form_pre_exit(__self, self):
		self = __self

		if not self.__allClosed:
			self.widget.uiExit()
			# allways abort, will exith then
			raise AbortRequest(None)		# empty and None message means stop exiting with no error raised


	# callback from client uiRemovePage
	def onExit(self, container):
		if container:
			if not container._lazy_:
				self.__uiForms[container]._gfObject.close()
		else:
			# no pages left, exit application
			self._form.close()


	def onPageClose(self, container, exiting):
		"""button pressed to close page"""
		#rint "__on_page_close", event.GetEventObject().GetPage(event.GetInt())._uiForm_._gfObject
		# call logic
		if container:
			self.__exiting = exiting
			self.__uiForms[container]._gfObject.close()
		elif exiting:
			self.__exiting = False
			self.__allClosed = True
			self._form.close()


	def onPageChanged(self, container):
		assert isinstance(container, (Panel, type(None))), 'Container has bad type: %s' % (type(container),)
		self.__selectedContainer = container

		if container and container._lazy_:
			if self.__exiting:
				container._on_page_selected_ = None
				self.widget.uiRemovePage(container, self.__exiting)
			else:
				on_page_selected = container._on_page_selected_
				container._on_page_selected_ = None
				if on_page_selected:
					on_page_selected()
				
		else:
			uiForm = self.__uiForms.get(container)
			if self.__selectedUiForm is not uiForm:
				(uiForm or self._form.uiWidget).updateBars()
				self.__selectedUiForm = uiForm



	###########################################################################
	# Interface to GFMDINotebook
	#

	def _ui_get_current_form_(self):
		if self.widget.GetPageCount():
			return self.widget.GetPage(self.widget.GetSelection())._uiForm_._gfObject

	def _ui_select_form_(self, name):
		for uiForm, container in self.__containers.iteritems():
			if uiForm._gfObject.name == name:
				self.widget.uiSelectPage(container)
				return True
		return False
		
	def _ui_add_lazy_page_(self, title, on_page_selected):
		panel = Panel(self)
		panel._lazy_ = True
		panel._on_page_selected_ = on_page_selected
		self.widget.uiAddPage(panel, title, '')

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIMDINotebook,
	'provides' : 'GFMDINotebook',
	'container': 0,
}
