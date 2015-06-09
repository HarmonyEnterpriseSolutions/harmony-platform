
from gnue.forms.input.GFKeyMapper import KeyMapper
from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import List

_all__ = ["UIList"]
		

# =============================================================================
# Interface implementation for a grid widget
# =============================================================================

class UIList(UIWidget):

	def _create_widget_ (self, event):
		self.widget = List(self, self._gfObject.label or "", self._gfObject.style)
		self.getParent().addWidget(self)

	def is_growable(self):
		return True
	
	def _ui_set_values_(self, values):
		self.widget.uiSetValues(values)

	def _ui_set_value_(self, index, value):
		self.widget.uiSetValue(index, value)

	def _ui_select_row_(self, index):
		self.widget.uiSelectRow(index)
		
	def addWidget(self, ui_widget):
		"""
		Add a given UI widget to the Notebook.

		@param ui_widget: widget to add to the page
		"""
		self.widget.uiAdd(ui_widget.widget)

	def onSelectionChanged(self, index):
		self._gfObject._event_item_focused(index)

	def onSetFocus(self):
		self._gfObject._event_set_focus()

	# navigable

	def _ui_set_focus_(self):
		self.widget.uiSetFocus()

	def onKeyPressed(self, keycode, shiftDown, ctrlDown, altDown):
		command, args = KeyMapper.getEvent(keycode, shiftDown, ctrlDown, altDown)
		if command:
			self._request(command, triggerName=args)


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIList,
	'provides' : 'GFList',
	'container': True
}
