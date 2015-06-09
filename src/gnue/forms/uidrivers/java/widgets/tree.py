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
# $Id: tree.py,v 1.15 2011/12/28 21:46:11 oleg Exp $


import os

from gnue.forms.input.GFKeyMapper import KeyMapper
from _base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import Tree
from gnue import paths

DEBUG=0

	

#
# UITree
#
# Widget set specific function that creates a single instance of a tree
#
class UITree(UIWidget):

	def __init__(self, *args, **kwargs):
		UIWidget.__init__(self, *args, **kwargs)
		self.__menu = None
		self.__editing = False
		self.__nodesChecked = ()

	def _create_widget_(self, event):
		self.widget = Tree(self, self._gfObject.label or "", repr(self._gfObject.getRootId()), map(self.__jsonTreeNodeStyle, self._gfObject.getNodeStyles()))
		self.getParent().addWidget(self)

	################################################################3
	# Events from GFTree (to update ui)
	#
	def _ui_revalidate_(self):
		self.widget.uiRevalidate()

	def _ui_revalidate_node_(self, id, nameChanged, styleChanged):
		"""
		node name or style has been changed
		"""
		if nameChanged or styleChanged:
			self.widget.uiRevalidateIdPath(
				map(repr, self._gfObject.getIdPath(id)), 
				nameChanged, 
				styleChanged, 
				self._gfObject.formatNodeName(id) if nameChanged else '', 
				self._gfObject.getNodeStyleKey(id) if styleChanged else ''
			)

	def _ui_set_focused_node_(self, id):
		self.widget.uiSelectIdPath(map(repr, self._gfObject.getIdPath(id)))

	def _ui_rename_node_(self):
		raise NotImplementedError

	def _ui_cut_node_(self):
		raise NotImplementedError

	def _ui_copy_node_(self):
		raise NotImplementedError

	def _ui_paste_node_(self):
		raise NotImplementedError

	def _ui_delete_node_(self):
		raise NotImplementedError

	def _ui_get_checked_nodes_(self, reduceChildren):
		if reduceChildren:
			ids = self.__nodesChecked
		else:
			ids = set()
			for id in self.__nodesChecked:
				if id not in ids:
					ids.update(self._gfObject.iterChildIdsRecursive(id))
		return ids

	def _ui_check_all_nodes_(self, checked):
		self.widget.uiCheckAllNodes(checked)

	def _ui_get_cutted_node_id_(self, force):
		return None

	def _ui_get_copied_node_id_(self, force):
		return None

	def _ui_expand_(self, idPath, expand):
		# empty id path means to expand/collapse all
		self.widget.uiExpandChildren([] if idPath is None else map(repr, idPath), expand)

	################################################################3
	# Events from ui (ui updated bu user)
	#
	def onGetChildren(self, parentId):
		return [
			{
				'id'         : repr(id),
				'name'       : self._gfObject.formatNodeName(id),
				'childCount' : self._gfObject.getChildCount(id),
				'nodeStyle'  : self._gfObject.getNodeStyleKey(id),
			}
			for id in self._gfObject.iterChildIds(eval(parentId))
		]

	def __jsonTreeNodeStyle(self, style):
		if style:
			style = style.__json__()
			if 'icon' in style:
				path = os.path.join(paths.data, 'share', 'gnue', 'images', 'apps', style['icon'])
				style['icon'] = self._uiDriver.getStaticResourceWebPath(path)
				if self._gfObject.checkable:
					style['button'] = 'checkbox'
			return style
		else:
			return {}
	
	def onGetNodeStyle(self, key):
		return self.__jsonTreeNodeStyle(self._gfObject.getNodeStyles().getStyle(key))
	
	def onSelectionChanged(self, id):
		self._gfObject._event_node_selected(eval(id))

	def onNodeActivated(self):
		self._gfObject._event_node_activated()

	def onSetFocus(self):
		self._gfObject._event_set_focus()

	################################### editing ################################

	def onMenuPopup(self, id):
		self._gfObject._event_menu_popup(eval(id))
		menu = self._gfObject.findChildOfType('GFMenu')
		if menu:
			menu._event_menu_popup()

	##############################################################################

	def _ui_set_context_menu_(self, menu, name):
		self.widget.uiSetPopupMenu(menu)

	# cut-copy-paste commands to GFObject
	#def _moveItem(self, source, target):
	#	self._gfObject._event_move_node(source.GetData(), target.GetData())

	#def _copyItem(self, source, target):
	#	self._gfObject._event_copy_node(source.GetData(), target.GetData())

	def onNodesChecked(self, nodes):
		self.__nodesChecked = map(eval, nodes)
		self._gfObject._event_node_checked()

	# navigable

	def _ui_set_focus_(self):
		self.widget.uiSetFocus()

	def onKeyPressed(self, keycode, shiftDown, ctrlDown, altDown):
		command, args = KeyMapper.getEvent(keycode, shiftDown, ctrlDown, altDown)
		if command:
			self._request(command, triggerName=args)

configuration = {
	'baseClass'  : UITree,
	'provides'   : 'GFTree',
	'container'  : 1,
}
