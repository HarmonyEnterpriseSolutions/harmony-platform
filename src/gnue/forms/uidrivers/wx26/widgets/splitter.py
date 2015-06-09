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
# $Id: splitter.py,v 1.25 2010/03/18 16:58:01 oleg Exp $
"""
"""

import wx
import wx.grid
from wx.lib.scrolledpanel				     import ScrolledPanel
from gnue.forms.uidrivers.wx26.widgets._base import UIHelper
from toolib.util						     import lang
from toolib.util.Configurable                import Configurable
from toolib.wx.controls.SplitterWindow       import SplitterWindow
from src.gnue.forms.uidrivers.wx26.widgets.mdi_notebook import MdiNotebookClass
from src.gnue.forms.uidrivers.wx26.widgets.notebook import NotebookClass
from src.gnue.forms.uidrivers.wx26.widgets._config import BORDER_SPACE

DEBUG         = 0
MIN_PANE_SIZE = 1
SCROLLERS     = True
BORDER        = False

# =============================================================================
# Interface implementation for a box widget
# =============================================================================

class UISplitter (UIHelper, Configurable):
	"""
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		UIHelper.__init__(self, event)
		self._inits.append(self.__postinit)

	# -------------------------------------------------------------------------
	# Create a wx box widget
	# -------------------------------------------------------------------------

	def _create_widget_ (self, event):
		"""
		@param event: the creation-event instance carrying information like
		        container (parent-widget)

		@returns: wx widget
		"""
		self.__uiWidgets = []
		self._container = self.widget = SplitterWindow(event.container, -1,
			style=lang.iif(BORDER, wx.SP_3D, wx.SP_NOBORDER)
		)
		self.getParent().add_widgets(self)
		self._gfObject._form.associateTrigger('ON-EXIT', self.__on_form_exit)


	def add_widgets(self, ui_widget, border=0):
		"""
		Add a given UI widget to the splitter.

		@param ui_widget: widget to add to the page
		"""
		self.__uiWidgets.append(ui_widget)

	def __postinit(self):

		# have two widgets, can split now
		#if DEBUG:
		#	#rint self._gfObject.align
		#	from toolib.wx.debug.dump import dumpWindowSizes
		#	dumpWindowSizes(self.__uiWidgets[0])
		#	dumpWindowSizes(self.__uiWidgets[1])

		panes = []

		for i, ui_widget in enumerate(self.__uiWidgets):

			if SCROLLERS and not ui_widget._gfObject._type in ('GFTree', 'GFTable', 'GFSplitter', 'GFNotebook', 'GFEntry', 'GFUrlResource', 'GFTreeList') and 'wxGTK' not in wx.PlatformInfo:
				scroll = ScrolledPanel(ui_widget.widget.GetParent(), -1, style=lang.iif(BORDER, 0, wx.STATIC_BORDER))

				ui_widget.widget.Reparent(scroll)

				scroll.SetSizer(wx.GridSizer(1,1))

				if not isinstance(ui_widget.widget, (MdiNotebookClass, NotebookClass)):
					# add border
					scroll.GetSizer().Add(ui_widget.widget, 0, wx.GROW | wx.ALL, BORDER_SPACE)
				else:
					scroll.GetSizer().Add(ui_widget.widget, 0, wx.GROW)

				#scroll.SetAutoLayout(1)
				scroll.SetupScrolling()

				panes.append(scroll)
			else:
				panes.append(ui_widget.widget)

		sashDim = self._gfObject.getAlign()

		#for w in widgets: w.MinSize = -1, w.MinSize[1]
		#for w in widgets: w.MinSize = w.BestSize[0], -1

		if len(panes) < 2:
			# accept also one pane or no panes
			self.widget.Initialize(panes[0] if panes else wx.Panel(self.widget, -1, style=wx.STATIC_BORDER))
		else:
			# if second widget not growable and first growable
			if not self.__uiWidgets[1].is_growable() and self.__uiWidgets[0].is_growable():
				# tie sash to right-bottom
				# +2 is for border, do not know why +3, but it needed to hide splitter
				sashPos = -(self.__getPaneSize(panes[1])[sashDim]+2+3)
				self.widget.SetSashGravity(1)
			else:
				# tie sash to top-left
				# +2 is for border, to hide splitter
				sashPos = self.__getPaneSize(panes[0])[sashDim] + 2
				self.widget.SetSashGravity(0)

			(
				self.widget.SplitVertically,
				self.widget.SplitHorizontally,
			)[sashDim](panes[0], panes[1], sashPos)

			self.widget.SetMinimumPaneSize(MIN_PANE_SIZE)		# to prevent unsplit
			self.applyConfig()

			# set centered if sash still at top
			if self.widget.GetSashPosition() == MIN_PANE_SIZE + 1:
				self.widget.SetSashPosition(self.widget.Size[sashDim] / 2)

	def __on_form_exit(__self, self):
		__self.saveConfig()

	def __getPaneSize(self, pane):
		if pane.GetSizer():
			return pane.GetSizer().GetSize()
		else:
			return pane.BestSize


	# -------------------------------------------------------------------------
	# Indicate whether this box is vertically growable
	# -------------------------------------------------------------------------

	def is_growable(self):
		return True


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
		return { 'SashPosition' : None }

	def applyConfig(self):
		x = self.getSetting('SashPosition')
		if x is not None:
			self.widget.SetSashPosition(x)

	def saveConfig(self):
		try:
			self.setSetting('SashPosition', self.widget.GetSashPosition())
		except wx.PyDeadObjectError:
			print "* UISplitter.saveConfig: PyDeadObjectError, config not saved"
		else:
			# do not save local conf
			return self.saveUserConfig()

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UISplitter,
	'provides' : 'GFSplitter',
	'container': 1
}
