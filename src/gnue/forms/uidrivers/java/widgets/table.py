
from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import Table
from gnue.forms.input.GFKeyMapper import KeyMapper

__all__ = ["UITable"]


# =============================================================================
# Interface implementation for a grid widget
# =============================================================================

SORT_ORDER = {
	None  : 0,
	True  : 1,
	False : -1,
}

class UITable(UIWidget):

	def __init__(self, event):
		UIWidget.__init__(self, event)
		self.__selectedRows = ()
		self.__selectedCol  = None
		self.__findForm = None

	def _create_widget_ (self, event):
		self.widget = Table(self, self._gfObject.label or "", self._gfObject.selectionMode)
		self.getParent().addWidget(self)

	def onPostInit(self):
		self.__flags = self._gfObject.getFlags()
		columns = [
			{
				'editable' : False,
				'label'    : self._gfObject.getFlagLabel(flag),
				'tip'      : self._gfObject.getFlagTip(flag),
			}
			for flag in self.__flags
		] + [
			{
				'editable' : not self._gfObject.isFieldReadOnlyAt(i),
				'label'    : getattr(entry, 'label', ''),
				'tip'      : entry.getDescription(),
				'id'       : entry._field.name,
				'order'    : SORT_ORDER[entry._field.getSortOrder()],
			}
			for (i, entry) in enumerate(self._gfObject.getEntries())
		]
		self.widget.uiSetColumns(self.__flags, columns)

		super(UITable, self).onPostInit()
	

	def addWidget(self, ui_widget):
		self.widget.uiAdd(ui_widget.widget)
		

	################################################################
	# Events from GFTable (to update ui)
	#
	def _ui_revalidate_(self):
		self.widget.uiSetData(
			[self.__getRowData(row) for row in xrange(self._gfObject.getRecordCount())],
			[{} for flag in self.__flags] + [
				{
					'order'    : SORT_ORDER[entry._field.getSortOrder()],
				}
				for entry in self._gfObject.getEntries()
			]
		)

	def _ui_revalidate_row_(self, row):
		self.widget.uiSetRowData(row, self.__getRowData(row))

	def __getRowData(self, row):
		return [
			self._gfObject.getFlagValue(row, flag)
			for flag  in self.__flags
		] + [
			self._gfObject.getFormattedValue(row, col)
			for col in xrange(self._gfObject.getFieldCount())
		]

	def _ui_set_focused_row_(self, row):
		self.widget.uiSetFocusedRow(row)

	def _ui_set_focused_cell_(self, row, col):
		self.widget.uiSetFocusedCell(row, col)

	################################################################

	def _ui_focus_out_(self):
		self.widget.uiStopEditing()


	################################################################
	# Events from ui (ui updated by user)
	#

	def onSelectionChange(self, row, col, rows):
		self.__selectedRows = rows
		self._gfObject._event_cell_focused(row, col)

	def onRowActivated(self):
		self._gfObject._event_row_activated()

	def onMenuPopup(self, rows, col):
		# called before menu popup
		# set focus to entry from this table
		self.__selectedRows = rows
		self.__selectedCol = col
		menu = self._gfObject.findChildOfType('GFMenu')
		if menu:
			menu._event_menu_popup()

	def onCopy(self, baseRow, baseCol, rowCount, colCount):
		text = []
		baseDataCol = len(self.__flags)
		for i, row in enumerate(xrange(baseRow, baseRow + rowCount)):
			if i > 0:
				text.append('\n')
			for j, col in enumerate(xrange(baseCol, baseCol + colCount)):
				if j > 0:
					text.append('\t')
				if col >= baseDataCol:
					value = self._gfObject.getClipboardValue(row, col-baseDataCol)
				else:
					value = repr(self._gfObject.getFlagValue(row, self.__flags[col]))
				text.append(value)
		return ''.join(text)
	
	def onErase(self, baseRow, baseCol, rowCount, colCount):
		baseCol = max(baseCol, len(self.__flags)) - len(self.__flags)
		for row in xrange(baseRow, baseRow + rowCount):
			for col in xrange(baseCol, baseCol + colCount):
				try:
					self._gfObject.setClipboardValue(row, col, "")
				except ValueError:
					pass

	def onPaste(self, text):
		data = [line.split('\t') for line in text.rstrip('\n').split('\n')]

		if not data:
			raise self._form.error(_("Nothing to paste"))

		if not self.__selectedRows:
			raise self._form.error(_("Row not selected"))

		if self.__selectedCol is None:
			raise self._form.error(_("Column not selected"))

		baseRow = min(self.__selectedRows)
		baseCol = self.__selectedCol - len(self.__flags)

		if baseCol < 0:
			raise self._form.error(_("Can't paste flags"))

		for i, row in enumerate(xrange(baseRow, baseRow + len(data))):
			for j, col in enumerate(xrange(baseCol, baseCol + len(data[i]))):

				if row == self._gfObject.getRecordCount():
					self._gfObject.appendRecord()

				try:
					self._gfObject.setClipboardValue(row, col, data[i][j])
				except ValueError:
					pass

	# navigable
	def onKeyPressed(self, keycode, shiftDown, ctrlDown, altDown):
		command, args = KeyMapper.getEvent(keycode, shiftDown, ctrlDown, altDown)
		if command:
			self._request(command, triggerName=args)

	################################################################
	# other Interface with GFTable
	#

	def _ui_get_selected_cell_(self):
		if len(self.__selectedRows) != 1:
			raise ValueError, "Not a single cell selection"

		return self.__selectedRows[0], self._ui_get_selected_col_()

	def _ui_get_selected_col_(self):
		"""
		returns field index selected if single column selected or if single cell selected
		"""
		return self.__selectedCol - len(self.__flags)

	def _ui_get_selected_rows_(self, no_cursor_row=False):
		"""
		returns rows selected
		no_cursor_row ignored
		"""
		return self.__selectedRows

	def _ui_set_context_menu_(self, menu, menuname):
		self.widget.uiSetPopupMenu(menu)

	def _ui_find_(self):
		if not self.__findForm:
			
			self.__findForm = self._gfObject._form.run_form(
				"common/FindDialog.gfd",
				{
					'p_table' : self._gfObject,
				},
			)
			
			this = self
			
			def on_parent_exit(self):
				if this.__findForm:
					this.__findForm.close()
			self._gfObject._form.associateTrigger('ON-EXIT', on_parent_exit)
			
			def on_exit(self):
				this.__findForm = None
			self.__findForm.associateTrigger('ON-EXIT', on_exit)
		
	def _ui_cut_(self):
		self.widget.uiCut()

	def _ui_copy_(self):
		self.widget.uiCopy()

	def _ui_paste_(self):
		self.widget.uiPaste()

	def _ui_cancel_editing_(self):
		self.widget.uiCancelEditing()



# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UITable,
	'provides' : 'GFTable',
	'container': True
}
