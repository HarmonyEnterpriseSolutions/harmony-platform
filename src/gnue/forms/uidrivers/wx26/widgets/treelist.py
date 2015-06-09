#
# This file is part of GNU Enterprise.
#
# GNU Enterprise is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or(at your option) any later version.
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
# Copyright 2000-2006 Free Software Foundation
#
# FILE:
# UIwxpython.py
#
# DESCRIPTION:
# A wxPython based user interface driver for GNUe forms.
#
# NOTES:
#
# $Id: treelist.py,v 1.10 2010/06/08 13:09:45 oleg Exp $

import os

import wx
from toolib.wx.controls.CustomTreeCtrl       import CustomTreeCtrl, GenericTreeItem, TR_AUTO_CHECK_CHILD, TR_AUTO_CHECK_PARENT, EVT_TREE_ITEM_CHECKED, TR_FULL_ROW_HIGHLIGHT
from wx.lib.agw.hypertreelist                import HyperTreeList as CustomTreeCtrl, _DEFAULT_COL_WIDTH
from toolib.wx.tree.MTreePopupMenu           import MTreePopupMenu
from toolib.wx.tree.MManageCustomTree        import MManageCustomTree
from toolib.wx.tree.XCustomTreeColumns       import XCustomTreeColumns
from toolib.wx.tree.XCustomTreeColumnsTips   import XCustomTreeColumnsTips
from toolib.wx.imagecaches                   import CachedImageList, CachedImageListStub
from toolib.util.Configurable                import Configurable
from toolib import debug
from toolib.wx.controls.PopupControl         import PopupControl
from gnue.forms.uidrivers.wx26.widgets._base import UIHelper
from gnue.forms.input                        import GFKeyMapper
from gnue import paths
from src.gnue.forms.uidrivers.wx26.widgets._config import BORDER_SPACE
from gnue.forms.GFObjects.GFBox import GFBox


try: _
except: _ = lambda x: x

DEBUG=0


class Tree(ExpansionState, XCustomTreeColumnsTips, XCustomTreeColumns, CustomTreeCtrl, MTreePopupMenu, MManageCustomTree, Configurable):		#DragAndDrop,

	def __init__(self, parent, uiObject):

		style = wx.TR_DEFAULT_STYLE | wx.WANTS_CHARS | wx.SUNKEN_BORDER | wx.TR_HIDE_ROOT | TR_AUTO_CHECK_CHILD | TR_AUTO_CHECK_PARENT | TR_FULL_ROW_HIGHLIGHT

		super(Tree, self).__init__(parent, -1, style = style)
		MTreePopupMenu.__init__(self, uiObject._get_context_menu, popupNowhere=uiObject._gfObject.getRootId() is not NotImplemented)
		MManageCustomTree.__init__(self, uiObject._moveItem, uiObject._copyItem)

		# if at list one treenodestyle has icon create CachedImageList
		self.cachedImageList = CachedImageListStub()
		if uiObject._gfObject.getNodeStyles().hasStyle(lambda style: style.icon is not None):
			self.cachedImageList = CachedImageList(os.path.join(paths.data, 'share', 'gnue', 'images', 'apps'))
			self.SetImageList(self.cachedImageList)

		self._uiObject = uiObject
		self._gfObject = uiObject._gfObject
		self.GetMainWindow().Bind(wx.EVT_KEY_DOWN, self.__on_key_down)

	def OnMouse(self, event):
		"""
		customtreectrl bugfix: node selection if rightclick to right of node
		"""
		if event.RightDown() :
			item, flags = self.HitTest(event.GetPosition())
			if not flags & (wx.TREE_HITTEST_ONITEMICON | wx.TREE_HITTEST_ONITEMLABEL):
				event.Skip()
				return
		return super(Tree, self).OnMouse(event)
	
	############################################################################################
	# select id path

	def _findItem(self, parentItem, id):
		item, cookie = self.GetFirstChild(parentItem)
		while item:
			if item.GetData() == id:
				return item
			item = self.GetNextSibling(item)
		return None

	def _expandPath(self, parentItem, idPath):
		#rint 'expandPath', parentItem.GetData(), idPath

		if not idPath:
			return parentItem

		item = self._findItem(parentItem, idPath[0])
		if item:
			if parentItem != self.GetRootItem():
				#rint 'expand:', parentItem.GetData()
				self.Expand(parentItem)
			return self._expandPath(item, idPath[1:])
		else:
			return parentItem

	def expandChildren(self, idPath, expand):
		parentItem = self.getItemByIdPath(idPath) if idPath else None
		items = self.iterItemsRecursive(parentItem)
		if expand:
			for item in items:
				item.Expand()
		else:
			for item in items:
				item.Collapse()

		self.GetMainWindow().CalculatePositions()

		if parentItem:
			self.GetMainWindow().RefreshSubtree(parentItem)
		else:
			self.Refresh()

	def selectIdPath(self, idPath):
		#rint 'selectIdPath', idPath
		item = self._expandPath(self.GetRootItem(), idPath)

		# do not select hidden root
		if item == self.GetRootItem():
			item, cookie = self.GetFirstChild(self.GetRootItem())

		self.Refresh()
		if item:
			self.SelectItem(item)
			# WORKAROUND: if do it now, have bug in treelist after refresh after empty record removed from tree
			#wx.CallAfter(self.SelectItem, item)

	#def OnDrop(self, dropItem, dragItem):
	#	dropId = dropItem.GetData()
	#	dragId = dragItem.GetData()
	#	self._gfObject._event_move_node(dropId, dragId)
	#	self.revalidate()
	#	self.selectIdPath(self._gfObject.getIdPath(dragId))

	############################################################################################
	# revalidate
	#
	def GetItemIdentity(self, item):
		""" needed for expansion state """
		return item.GetData()

	def _appendItems(self, parentItem, parentId):

		for id in self._gfObject.getChildIds(parentId):

			style = self._gfObject.getNodeStyle(id)

			item = self.AppendItem(
				parentItem,
				self._gfObject.formatNodeName(id),
				image = self.cachedImageList.getImageIndex(style and style.icon or None),
				data  = id,
				ct_type = {'checkbox' : 1, 'radiobox' : 2}.get(style and style.button or None, 0)
			)

			for col in range(1, self._gfObject.getFieldCount()):

				text = self._gfObject.formatNodeName(id, col)
				if isinstance(text, bool):
					self.SetItemImage(item, self.cachedImageList.getImageIndex("../forms/" + str(text) + ".gif"), column=col)
					text = ""

				self.SetItemText(item, text, col)

			if style:
				self.__revalidateItemTextFormatAndColors(item, style)
				if style.checked is not None and style.button == 'checkbox':
					item.Check(style.checked)

			if style and style.expanded:
				# expand this and all parents
				i = item
				while i is not None and i.IsOk():
					i.Expand()
					i = i.GetParent()

			elif self._gfObject.expanded:
				# expand this
				item.Expand()

			self._appendItems(item, id)


	def iterCheckedItems(self, reduceChildren=False):
		return (
			item
			for item in self.iterItemsRecursive(
				stopFn = (
					reduceChildren
					and GenericTreeItem.IsChecked
					or  (lambda item: False)
				)
			)
			if item.IsChecked()
		)

	def getCheckedState(self, reduceChildren=False):
		state = {}
		for item in self.iterItemsRecursive():
			state[item.GetData()] = item.IsChecked()
		return state

	def setCheckedState(self, state):
		for item in self.iterItemsRecursive():
			id = item.GetData()
			if state.has_key(id):
				item.Check(state[id])

	def revalidate(self):
		self.SetEvtHandlerEnabled(False)
		self.Freeze()

		es = self.GetExpansionState()
		cs = self.getCheckedState()

		#if self.GetSelection() and self.GetSelection().GetData():
		#	idPath = self._gfObject.getIdPath(self.GetSelection().GetData())
		#else:
		#	idPath = None

		self.DeleteChildren(self.GetRootItem())
		self._appendItems(self.GetRootItem(), self._gfObject.getRootId())

		self.SetExpansionState(es)
		self.setCheckedState(cs)

		# expand root nodes
		item, cookie = self.GetFirstChild(self.GetRootItem())
		while item:
			self.Expand(item)
			item = self.GetNextSibling(item)

		#idPath = self._gfObject.getSelectionIdPath()
		#if idPath:
		#	self.selectIdPath(idPath)

		self.Thaw()
		self.SetEvtHandlerEnabled(True)

	def _revalidateItemName(self, item):
		"""
		updates item text
		"""
		for col in xrange(self._gfObject.getFieldCount()):
			text = self._gfObject.formatNodeName(item.GetData(), col)
			if isinstance(text, bool):
				self.SetItemImage(item, self.cachedImageList.getImageIndex("../forms/" + str(text) + ".gif"), column=col)
				text = ""
			self.SetItemText(item, text, col)
		
		
	def _revalidateItemStyle(self, item):
		style = self._gfObject.getNodeStyle(item.GetData())
		self.SetItemImage(item, self.cachedImageList.getImageIndex(style and style.icon or None), column=0)
		self.__revalidateItemTextFormatAndColors(item, style)
		
	def __revalidateItemTextFormatAndColors(self, item, style):
		self.SetItemBold  (item, style.bold   if style else False)
		self.SetItemItalic(item, style.italic if style else False)
		self.SetItemTextColour      (item, wx.Colour(*style.textcolor.toRGB()) if style and style.textcolor else wx.NullColour)
		self.SetItemBackgroundColour(item, wx.Colour(*style.bgcolor  .toRGB()) if style and style.bgcolor   else wx.NullColour)
	
	def getItemByIdPath(self, idPath):
		item = self.GetRootItem()
		for id in idPath:
			item = self._findItem(item, id)
			if item is None:
				break
		return item

	def revalidateIdPath(self, idPath, nameChanged, styleChanged):
		item = self.getItemByIdPath(idPath)
		if item:
			if nameChanged:
				self._revalidateItemName(item)
			if styleChanged:
				self._revalidateItemStyle(item)
		else:
			debug.error('item not found to revalidate, idPath = %s' % (idPath,))


	############################################################################################

	def getColumnCount(self):
		return len(self._gfObject.getColumns())

	def getColumnWidth(self, col):
		return self._gfObject.getColumns()[col].width

	def getTipValue(self, item, hit, column, treeListColumn=None):
		if item is not None and column is not None:
			column = self._gfObject.getColumns()[column]
			style = self._gfObject.getNodeStyle(item.GetData())
			return (
				column.icon_description
				if
				style and column.name in (style.flags or ())
				else
				column.icon_off_description
			)
		else:
			return ""

	def paintCell(self, dc, item, col, rect):
		#dc.SetBrush(wx.TRANSPARENT_BRUSH)
		#dc.SetPen(wx.Pen(wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT), 1, wx.SOLID))
		#dc.DrawRectangleRect(rect)

		column = self._gfObject.getColumns()[col]
		style = self._gfObject.getNodeStyle(item.GetData())

		imageIndex = self.cachedImageList.getImageIndex(
			column.icon
			if
			style and column.name in (style.flags or ())
			else
			column.icon_off
		)

		if imageIndex >= 0:
			icon = self.cachedImageList.GetIcon(imageIndex)
			if icon.IsOk():
				dc.DrawIcon(
					icon,
					rect.X + (rect.Width  - icon.Width ) / 2,
					rect.Y + (rect.Height - icon.Height) / 2,
				)

	def checkAllNodes(self, checked):
		for item in self.iterItemsRecursive():	#stopFn = lambda item: item.IsChecked()):
			item.Check(checked)


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
		d = {}
		for i in xrange(self.GetColumnCount()):
			try:
				d['col[%s].size' % self.__getColumnId(i)] = _DEFAULT_COL_WIDTH
			except IndexError:
				pass
		return d

	def applyConfig(self):
		for i in xrange(self.GetColumnCount()):
			try:
				self.SetColumnWidth(i, self.getSetting('col[%s].size' % self.__getColumnId(i), _DEFAULT_COL_WIDTH))
			except IndexError:
				pass


	def saveConfig(self):
		for i in xrange(self.GetColumnCount()):
			try:
				self.setSetting('col[%s].size' % self.__getColumnId(i), self.GetColumnWidth(i))
			except IndexError:
				pass
		# do not save local conf
		return self.saveUserConfig()

	def __getColumnId(self, index):
		return self._gfObject.getFieldAt(index).name

	##########################################

	def __on_key_down(self, event):
		"""
		prevent node activation on SPACE
		"""
		if event.GetKeyCode() == wx.WXK_SPACE:
			item = self.GetSelection()
			if item and self.GetItemType(item) > 0:
				self.CheckItem(item, not self.IsItemChecked(item))
			return
		event.Skip()

#
# UITree
#
# Widget set specific function that creates a single instance of a tree
#
class UITreeList(UIHelper):

	def __init__(self, *args, **kwargs):
		UIHelper.__init__(self, *args, **kwargs)
		self.__menu = None
		self.__editing = False
		self._inits.append(self.__postinit)
		self._ignoreSelectionEvent = False
		self._gfObject._form.associateTrigger('ON-EXIT', self.__on_form_exit)

	def _create_widget_(self, event):
		self.widget = Tree(event.container, self)

		# before add_widgets
		#if not hasattr(self.widget, 'AddColumn') and self._gfObject.label:
		#	self.label = wx.StaticText(event.container, -1, self._gfObject.label)
		
		# use Dialog as widgets parent
		self._container = wx.Dialog(self.widget, -1, self._gfObject.label or "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self._container.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self._container.Bind(wx.EVT_ACTIVATE, self.__on_row_editor_activate)

		self.getParent().add_widgets(self)
		
		window = self.widget.GetMainWindow()
		
		window.Bind(wx.EVT_TREE_SEL_CHANGED,      self.__on_selection_changed, window)
		window.Bind(wx.EVT_SET_FOCUS,             self.__on_set_focus,         window)
		window.Bind(wx.EVT_CHAR,                  self.__on_char,              window)
		self.widget.Bind(wx.EVT_TREE_ITEM_ACTIVATED,   self.__on_node_activated)
		window.Bind(EVT_TREE_ITEM_CHECKED,        self.__on_node_checked,      window)

		self.widget.popupListeners.bind('menuPopup', self.__on_menu_popup)

	def __on_row_editor_activate(self, event):
		if not event.GetActive():
			#if not self.widget.IsShown():
			wx.CallAfter(self._container.Show, False)
			
		event.Skip()

	def add_widgets(self, ui_widget, border=0):
		# do not need any layout for editor entries
		self._container.GetSizer().Add(
			ui_widget.widget,
			ui_widget.stretch,
			wx.EXPAND | wx.ALL,
			# The border between the edge of the page
			# add no border if item is not GFBox widget
			isinstance(ui_widget._gfObject, GFBox) and BORDER_SPACE or 0
		)

	def __postinit(self):
		for entry in self._gfObject.getEntries():
			self.widget.AddColumn(entry.label or "")
			index = self.widget.GetColumnCount()-1
			if index > 0:
				align = entry.getAlign()
				wxalign = (wx.ALIGN_LEFT, wx.ALIGN_CENTRE, wx.ALIGN_RIGHT)[(align-1) % 3] #| (wx.ALIGN_BOTTOM, wx.ALIGN_CENTRE, wx.ALIGN_TOP)[(align-1) / 3]
				self.widget.SetColumnAlignment(index, wxalign)
		self.widget.AddRoot('HIDDEN ROOT')
		self.widget.applyConfig()
		self._container.Fit()

	def is_growable(self):
		return True

	################################################################3
	# Events from GFTree (to update ui)
	#
	def _ui_revalidate_(self):
		# self.SetEvtHandlerEnabled(False) in not enough
		self._ignoreSelectionEvent = True
		self.widget.revalidate()
		self._ignoreSelectionEvent = False

	def _ui_revalidate_node_(self, id, nameChanged, styleChanged):
		"""
		node name or style has been changed
		"""
		self.widget.revalidateIdPath(self._gfObject.getIdPath(id), nameChanged, styleChanged)

	def _ui_set_focused_node_(self, id):
		self._ignoreSelectionEvent = True
		self.widget.selectIdPath(self._gfObject.getIdPath(id))
		self._ignoreSelectionEvent = False
	
	def _ui_set_focused_cell_(self, id, col):
		#rint "table: _ui_set_focused_cell_(%s, %s)" % (row, col)

		# do not set focus if widget has PopupControl as parent
		# because grid cell editor shold not lose focus on modeless picker popup

		p = self.widget.GetParent()
		while p is not None and not isinstance(p, PopupControl):
			p = p.GetParent()

		if p is None:
			#rint "+ SetFocus in UITable._ui_set_focused_cell_"
			self.widget.GetMainWindow().SetFocus()

		self.widget.selectIdPath(self._gfObject.getIdPath(id))

	def _ui_rename_node_(self):
		item = self.widget.GetSelection()
		if item:
			self.widget.GetMainWindow().CalculatePositions()	# fix for misplaced editor bug
			self.widget.EditLabel(item)

	def _ui_cut_node_(self):
		self.widget.onCutItem()

	def _ui_copy_node_(self):
		self.widget.onCopyItem()

	def _ui_paste_node_(self):
		self.widget.onPasteItem()

	def _ui_delete_node_(self):
		item = self.widget.GetSelection()
		if item:
			self.widget.Delete(item)

	def _ui_get_checked_nodes_(self, reduceChildren):
		return [item.GetData() for item in self.widget.iterCheckedItems(reduceChildren)]

	def _ui_check_all_nodes_(self, checked):
		self.widget.checkAllNodes(checked)

	def _ui_get_cutted_node_id_(self, force):
		return self.widget.getCuttedItemData(force)

	def _ui_get_copied_node_id_(self, force):
		return self.widget.getCopiedItemData(force)

	def _ui_expand_(self, idPath, expand):
		self.widget.expandChildren(idPath, expand)

	def _ui_set_editor_visible_(self, visible):
		if visible:
			self._container.CenterOnParent()
		self._container.Show(visible)

	def _ui_is_row_editor_visible_(self):
		return self._container.IsShown()

	################################################################3
	# Events from ui (ui updated bu user)
	#
	def __on_selection_changed(self, event):
		item = event.GetItem()
		# Tree internaly at idle selects hidden root item if no nodes in tree, ignore this event
		if not self._ignoreSelectionEvent and item.IsOk() and item is not self.widget.GetRootItem():
			self._gfObject._event_cell_focused(self.widget.GetPyData(event.GetItem()), 0)
		event.Skip()

	def __on_node_activated(self, event):
		self._gfObject._event_node_activated()

	def __on_node_checked(self, event):
		self._gfObject._event_node_checked()
		event.Skip()

	def __on_set_focus(self, event):
		"""
		asquire focus
		"""
		# Let the GF focus follow
		# CallAfter because block not initialized at this time
		#wx.CallAfter(self._gfObject._event_set_focus)
		event.Skip()

	def __on_char(self, event):
		"""
		go next/previous entry
		"""
		if event.GetKeyCode() in [wx.WXK_TAB]:
			command, args = GFKeyMapper.KeyMapper.getEvent(
				event.GetKeyCode(),
				event.ShiftDown(),
				event.CmdDown(),
				event.AltDown()
			)

			if command:
				self._request(command, triggerName=args)
				return	# not skip event

		event.Skip()

		
	################################### editing ################################

	def __on_menu_popup(self, event):
		self._gfObject._event_menu_popup(event.data)
		menu = self._gfObject.findChildOfType('GFMenu')
		if menu:
			menu._event_menu_popup()

	##############################################################################

	def _ui_set_context_menu_(self, menu, name):
		self.__menu = menu

	def _get_context_menu(self):
		return self.__menu

	# cut-copy-paste commands to GFObject
	def _moveItem(self, source, target):
		self._gfObject._event_move_node(source.GetData(), target.GetData())

	def _copyItem(self, source, target):
		self._gfObject._event_copy_node(source.GetData(), target.GetData())

	##############################################################################

	def __on_form_exit(__self, self):
		# to prevent crash because of open editor
		try:
			__self.widget.saveConfig()
		except wx.PyDeadObjectError:
			print "! treelist config not saved because of PyDeadObjectError"

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UITreeList,
	'provides' : 'GFTreeList',
	'container': True
}
