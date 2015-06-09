import wx

import wx.grid

from gnue.forms.uidrivers.wx26.widgets._base    import UIHelper
from gnue.forms.input import GFKeyMapper

from toolib.wx.grid.editors.AbstractCellEditor  import AbstractCellEditor
from toolib.wx.grid.MGridMessaging				import MGridMessaging
from toolib.wx.grid.MPopupMenu					import MPopupMenu
from toolib.wx.grid.MFindReplace				import MFindReplace
from toolib.wx.grid.TCursor						import TCursor
from toolib.wx.grid.TGridClipboard				import TGridClipboard
from toolib.wx.grid.TSelection					import SelectionError
from toolib.wx.grid.THitTest					import THitTest, GridHitSpace
from toolib.wx.grid.TColumnExtraWidth			import TColumnExtraWidth	# provides getGridWidth

from toolib.wx.grid.TConfigurable				import TConfigurable
from toolib.wx.grid.XEditing					import XEditing
from toolib.wx.grid.XCursorAfterSelection		import XCursorAfterSelection
#from toolib.wx.grid.XSelectCursorLine			import XSelectCursorLine
from toolib.wx.grid.XTips						import XTips

from toolib.wx.grid.renderers.ImageCellRenderer import ImageCellRenderer

from toolib.wx.grid.renderers.BoolRenderer		import BoolRenderer
from toolib.wx.grid.editors.BooleanCellEditor	import BooleanCellEditor

from toolib.wx.grid.table.MTableMessaging       import MTableMessaging
from toolib.wx.grid.table.TAttrCreator          import TAttrCreator
from toolib.wx.grid.table.TTableClipboard		import TTableClipboard

from toolib.wx.event.KeyEventEx					import KeyEventEx
from toolib.wx.controls.PopupControl			import PopupControl
from toolib										import debug

from toolib.event.ListenerList					import ListenerList
from wx.lib.masked								import NumCtrl
from wx.lib.masked                              import NumCtrl, TextCtrl, BaseMaskedTextCtrl
from gnue.forms.GFObjects.GFBlock               import ACCESS

__all__ = ["UITable"]

class ImageCellRenderer(ImageCellRenderer):

	def getBitmap(self, grid, row, col):
		col -= grid.GetTable().getBaseDataCol()
		url = grid._gfTable.getValue(row, col)
		if url:
			bmp = grid._bitmapCache.get(url)
			if not bmp:
				pilimage = grid._gfTable.getFormattedValue(row, col)
				image = wx.EmptyImage(*pilimage.size)
				image.SetData(pilimage.convert("RGB").tostring())
				grid._bitmapCache[url] = bmp = image.ConvertToBitmap()
			return bmp


class Editor(AbstractCellEditor):

	def __init__(self, entry):
		super(Editor, self).__init__()
		self._entry = entry

	def createControl(self, parent, id):

		control = self._entry.uiWidget.widget

		control.SetId(id)

		if control.GetParent() is not parent:
			control.Reparent(parent)

		control.Show()

		return control

	def setControlValue(self, value):
		# do not set if not cancelled (already is)
		if self.isCancelled():
			self._entry.uiWidget._ui_set_value_(value)

	def startEdit(self, grid, row, col):
		c = self.GetControl()
		#rint 'START VALUE:', self._entry.uiWidget._ui_get_value_(), type(self._entry.uiWidget._ui_get_value_())

		# TODO: remove this begin edit
		# it needed only when selecting prod_id via popup
		#self._entry.beginEdit()

		if isinstance(c, wx.CheckBox) and c.IsEnabled():
			c.SetValue(not c.GetValue())

		return self._entry.uiWidget._ui_get_value_()

	def stopEdit(self, grid, row, col):
		#rint "Editor.stopEdit, canceled =", self.isCancelled()

		if isinstance(self.GetControl(), PopupControl):
			self.GetControl().PopDown()

		if self.isCancelled():
			return False
		else:
			# fix for #194
			if self._entry._field.isEditable():
				value = self._entry._displayHandler.parse_display(self._entry.uiWidget._ui_get_value_())
				#rint 'new value', repr(value), ', was', repr(self._entry._field.get_value())

				self._entry._field.set_value(value)
				return True
			else:
				return False

	def StartingKey(self, event):

		# workaround:
		# for not editable NumCtrl entry starting key changes the value
		if not self._entry._field.isEditable():
			return

		tc = self.GetControl()
		code = event.GetKeyCode()
		if code in (wx.WXK_DELETE, wx.WXK_BACK):
			tc.SetValue("")
		else:
			char = KeyEventEx.getChar(event)
			if char is not None:
				#if isinstance(tc, PopupControl):
				#	wx.CallAfter(tc.WriteText, char)
				if isinstance(tc, NumCtrl):
					if char in '0123456789':
						# set integer as a value
						tc.SetValue(int(char))

						# set cursor to the end of first field
						# need to do it after because now not works
						# TODO: not to use internal attrs
						wx.CallAfter(tc.SetInsertionPoint, tc._fields[0]._extent[1])
					elif char in ',.':
						if tc._fields.has_key(1):
							# select fractional part
							wx.CallAfter(tc.SetSelection, *tc._fields[1]._extent)
				#elif char == '-':
				#	# tc is buggy for this (wrong color)
				#	tc.SetValue(-tc.GetValue())
				#	wx.CallAfter(tc.SetSelection, *tc._fields[0]._extent)

				elif isinstance(tc, TextCtrl):	# masked text
					try:
						tc.SetValue(char)
					except ValueError:
						# control throws ValueError if can't insert this char
						pass

				elif hasattr(tc, 'WriteText'):
					# another TextCtrl's
					wx.CallAfter(tc.WriteText, char)

				elif hasattr(tc, 'SetValue') and hasattr(tc, 'SetInsertionPointEnd'):
					# It is probably combobox
					tc.SetValue(char)
					tc.SetInsertionPointEnd()

	def SetSize(self, rect):
		"""
		Called to position/size the edit control within the cell rectangle.
		If you don't fill the cell (the rect) then be sure to override
		PaintBackground and do something meaningful there.
		"""
		c = self.GetControl()
		if isinstance(c, wx.CheckBox) and c.GetLabel() == '':
			w, h = self.GetControl().Size
			self.GetControl().SetDimensions(rect.x + (rect.width - w)/2 + 2, rect.y + (rect.height-h)/2 + 2, w, h)
		else:
			super(Editor, self).SetSize(rect)

FLAG_COLUMN_SIZE = 20
ROW_LABEL_DIGIT_WIDTH = 7
#HSCROLL_HEIGHT = 17
#MAX_MINWIDTH = 600
#BORDER_SIZE = 2
LABEL_EXTRA_HEIGHT = 8
LABEL_FONT_HEIGHT = 12

class Grid(MPopupMenu, MFindReplace,  MGridMessaging, XEditing, XCursorAfterSelection, XTips, wx.grid.Grid, TCursor, TGridClipboard, THitTest, TColumnExtraWidth, TConfigurable):

	def __init__(self, parent, uiTable):

		XEditing.__init__(self, parent, -1, style=wx.WANTS_CHARS | wx.SUNKEN_BORDER)

		MPopupMenu.__init__(self, uiTable._get_context_menu)

		self.__in_revalidate = False

		self._uiTable = uiTable
		self._gfTable = uiTable._gfObject

		self.SetTable(Table(self._gfTable))

		MFindReplace.__init__(self, self.GetTable().getValueAsText)

		# changing until revalidate
		self.GetTable().fireTableStructureChanging()

		self.RegisterDataType(CT_FLAG, BoolRenderer(), BooleanCellEditor())

		for entry in self._gfTable.getEntries():
			renderer = self.GetDefaultRenderer()
			if entry._type == 'GFImage':
				renderer = ImageCellRenderer()
			elif entry._field.datatype == 'boolean':
				renderer = BoolRenderer()
			else:
				renderer = self.GetDefaultRenderer()

			self.RegisterDataType(
				entry._field.name,
				renderer,
				Editor(entry)
			)

		for i in xrange(self.GetTable().getBaseDataCol()):
			self.SetColSize(i, FLAG_COLUMN_SIZE)

		# apply selectionMode GFTable attribute
		selectionMode = getattr(Grid, 'wxGridSelect' + self._gfTable.selectionMode.capitalize())
		self.SetSelectionMode(selectionMode)

		self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
		self.SetColLabelAlignment(wx.ALIGN_LEFT,  wx.ALIGN_CENTRE)

		font = self.GetDefaultCellFont()
		font.SetWeight(wx.FONTWEIGHT_BOLD)
		font.SetPointSize(font.GetPointSize()-1)
		self.SetLabelFont(font)

		# set col label size accounting line count
		lineCounts = [(getattr(entry, 'label', '') or '').count('\n') + 1 for entry in self._gfTable.getEntries()]
		self.SetColLabelSize(LABEL_EXTRA_HEIGHT + LABEL_FONT_HEIGHT * max(lineCounts + [1]))

		self.EnableDragRowSize(False)

		self.SetMargins(0,0)

		# set row height if have sime editors wit defined MinSize.GetHeight
		#wx.CallAfter(lambda: self.SetDefaultRowSize(max([entry.uiWidget.widget.GetMinSize().GetHeight() for entry in self._gfTable.getEntries() if entry.uiWidget.widget] + [self.GetDefaultRowSize()]), True))
		
		# for TConfigurable
		self.applyConfig()

		# if MinSize not set grid allways will be sized to maximum size (no scrollbars)
		self.MinSize = 1, 1

		#w = self.getGridWidth()
		#h = self.GetColLabelSize() + self._uiTable._gfObject.rowCount * self.GetDefaultRowSize() + BORDER_SIZE
		#if w > MAX_MINWIDTH:
		#	w = MAX_MINWIDTH
		#	h += HSCROLL_HEIGHT

		self._bitmapCache = {}

		self.__selectionBackground = self.GetSelectionBackground()

	def tipsAllowed(self):
		return ('collabel',)

	def getTipValue(self, row, col):
		base = self.GetTable().getBaseDataCol()
		if col >= 0:
			if col < base:
				return self._gfTable.getFlagTip(self.GetTable()._flags[col])
			else:
				return self._gfTable.getEntryAt(col-base).getDescription()

	# PopupControl sets focus to it's content
	# redirect method to grid window
	# TODO: must set focus from logical focus
	def SetFocus(self):
		#rint "+ SetFocus in Grid (delegaing to GridWindow)"
		self.GetGridWindow().SetFocus()

	def revalidate(self):
		if not self.__in_revalidate:
			self.__in_revalidate = True

			self.SetEvtHandlerEnabled(False)
			self.GetGridWindow().SetEvtHandlerEnabled(False)
			try:

				#rint
				#rint "--------------------------------"
				#rint "Grid.revalidate"
    
				#row, col = self.GetGridCursorRow(), self.GetGridCursorCol()
    
				self.ClearSelection()
				self.GetTable().fireTableStructureChanged()
    
				self.SetRowLabelSize(ROW_LABEL_DIGIT_WIDTH * (1+len(
							self.GetTable().GetRowLabelValue(self.GetTable().GetNumberRows()-1))))
    
				self._bitmapCache.clear()
    
				# changing until next revalidate
				self.GetTable().fireTableStructureChanging()
				self.GetTable().revalidateRowAttributes()

			finally:
				self.SetEvtHandlerEnabled(True)
				self.GetGridWindow().SetEvtHandlerEnabled(True)
				self.Refresh()
				
			#if row >= 0 and col >= 0:
			#	self.SetGridCursor(row, col)

			self.__in_revalidate = False
		else:
			debug.error('revalidate self entered')


	def setGridFocused(self, focused):
		#rint "Grid.setGridFocused", focused, self._gfTable.getBlock().name
		try:
			if focused:
				self.SetCellHighlightColour(wx.BLACK)
				self.SetSelectionBackground(self.__selectionBackground)
			#self.SetCellHighlightPenWidth(2)
			else:
				self.SetCellHighlightColour(self.GetGridLineColour())
				self.SetSelectionBackground(self.GetGridLineColour())
			#self.SetCellHighlightPenWidth(1)
			self.Refresh()
		except wx.PyDeadObjectError:
			pass


	##########################################
	# for TConfigurable
	#
	def getDomain(self):
		return 'gnue'

	def getConfigName(self):
		"""
		Returns the name of the configuration file.
		This is used on the command-line.
		"""
		return "%s.table_%s" % (self._gfTable.getParent()._uid_(), self._gfTable.getBlock().name)


CT_FLAG = "ct_boolean"

class Table(wx.grid.PyGridTableBase, MTableMessaging, TAttrCreator, TTableClipboard):	#MAttrProviderFix,

	def __init__(self, gfTable):
		#MAttrProviderFix.__init__(self)
		wx.grid.PyGridTableBase.__init__(self)
		MTableMessaging.__init__(self)

		self._gfTable = gfTable

		self._flags  = self._gfTable.getFlags()

		self.__baseDataCol = len(self._flags)

		if self.CanHaveAttributes():
			ap = self.GetAttrProvider()

			for i, f in enumerate(self._flags):
				ap.SetColAttr(self.newAttr(alignment=(wx.ALIGN_LEFT, wx.ALIGN_CENTER)), i)
			#if f == 'M':
			#	ap.SetColAttr(self.newAttr(alignment=(wx.ALIGN_LEFT, wx.ALIGN_CENTER), readOnly = True), i)
			#elif f == 'R':
			#	ap.SetColAttr(self.newAttr(alignment=(wx.ALIGN_LEFT, wx.ALIGN_CENTER)), i)

			for col in xrange(self._gfTable.getFieldCount()):

				attr = None

				if self._gfTable.isFieldReadOnlyAt(col):
					if attr is None: attr = self.newAttr()
					attr.SetReadOnly(True)

				align = self._gfTable.getEntryAt(col).getAlign()
				if align != 7:
					if attr is None: attr = self.newAttr()
					attr.SetAlignment(
						(wx.ALIGN_LEFT,   wx.ALIGN_CENTRE, wx.ALIGN_RIGHT)[(align-1) % 3],
						(wx.ALIGN_BOTTOM, wx.ALIGN_CENTRE, wx.ALIGN_TOP  )[(align-1) / 3],
					)

				if attr:
					ap.SetColAttr(attr, self.__baseDataCol + col)

	def GetNumberRows(self):
		return self._gfTable.getRecordCount()

	def getBaseDataCol(self):
		return self.__baseDataCol

	def GetNumberCols(self):
		return self.__baseDataCol + self._gfTable.getFieldCount()

	def GetTypeName(self, row, col):
		if col < self.__baseDataCol:
			return CT_FLAG
		else:
			return self._gfTable.getFieldAt(col-self.__baseDataCol).name

	def GetColLabelValue(self, col):
		if col < self.__baseDataCol:
			return self._gfTable.getFlagLabel(self._flags[col])
		else:
			col -= self.__baseDataCol
			field = self._gfTable.getFieldAt(col)
			order = field.getSortOrder()
			if order is None:
				arrow = ""
			else:
				arrow = " \\/" if order else " /\\"

			if field.isFiltered():
				arrow = '# ' + arrow

			return (getattr(self._gfTable.getEntryAt(col), 'label', '') or ('Column %s' % (col+1))) + arrow

	def GetRowLabelValue(self, row):
		if self._gfTable.isQuery():
			return _('QRY')
		else:
			return str(row+1)

	def GetValue(self, row, col):
		if col < self.__baseDataCol:
			return self._gfTable.getFlagValue(row, self._flags[col])
		else:
			return self._gfTable.getFormattedValue(row, col-self.__baseDataCol)

	def SetValue(self, row, col, value):
		if col < self.__baseDataCol:
			self._gfTable.setFlagValue(row, self._flags[col], value)

	###################################################################################
	# required for TTableClipboard
	###################################################################################

	def AppendRows(self, rows):
		if rows > 0:
			for i in xrange(rows):
				self._gfTable.appendRecord()

	def getValueAsText(self, row, col):
		if col < self.__baseDataCol:
			return repr(self.GetValue(row, col))
		else:
			return self._gfTable.getClipboardValue(row, col-self.__baseDataCol)

	def setValueAsText(self, row, col, text):
		#rint ">>> setValueAsText", row, col, text
		if col >= self.__baseDataCol:
			self._gfTable.setClipboardValue(row, col-self.__baseDataCol, text)

	###################################################################################

	def getColumnId(self, col):
		"""
		for TConfigurable
		"""
		if col >= self.__baseDataCol:
			return self._gfTable.getFieldAt(col-self.__baseDataCol).name
		else:
			# TConfigurable will not configure this column
			raise IndexError, col

	def revalidateRowAttributes(self):
		if self.CanHaveAttributes():
			ap = self.GetAttrProvider()
			for row in xrange(self.GetNumberRows()):
				style = self._gfTable.getRowStyleAt(row)
				bgcolor = wx.Colour(*style.bgcolor.toRGB()) if style and style.bgcolor else wx.NullColour
				textcolor = wx.Colour(*style.textcolor.toRGB()) if style and style.textcolor else wx.NullColour
				ap.SetRowAttr(self.newAttr(backgroundColour = bgcolor, textColour=textcolor), row)
				pass

# =============================================================================
# Interface implementation for a grid widget
# =============================================================================

class UITable(UIHelper):

	def __init__(self, event):
		UIHelper.__init__(self, event)
		self.__menu = {}
		#self.__focus = False

	def _create_widget_ (self, event):

		self.widget = Grid(event.container, self)

		# use temporary invisible window as widgets parent
		self._container = wx.Window(self.widget)
		self._container.Hide()

		# before add_widgets
		if self._gfObject.label:
			self.label = wx.StaticText(event.container, -1, self._gfObject.label)

		self.getParent().add_widgets(self)

		# self.widget as 3d argument is necessary
		# grid has wrong events from another child grid otherwise
		self.widget.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.__on_select_cell, self.widget)

		self.widget.GetGridWindow().Bind(wx.EVT_SET_FOCUS, self.__on_set_focus, self.widget.GetGridWindow())
		self.widget.GetGridWindow().Bind(wx.EVT_KILL_FOCUS, self.__on_kill_focus, self.widget.GetGridWindow())

		#self.widget.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus, self.widget)
		#self.widget.Bind(wx.EVT_KILL_FOCUS, self.__on_kill_focus, self.widget)

		self.widget.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.__on_cell_left_dclick)		#GetGridWindow().
		self.widget.Bind(wx.grid.EVT_GRID_LABEL_LEFT_DCLICK, self.__on_label_left_dclick)	#

		self.widget.popupListeners.bind('menuPopup', self.__on_menu_popup)

		# GetGridWindow() not used: listens to grid end cell editors
		self.widget.Bind(wx.EVT_KEY_DOWN, self.__on_key_down)

		wx.CallAfter(self.widget.setGridFocused, False)

		self._gfObject._form.associateTrigger('ON-EXIT', self.__on_form_exit)


	def add_widgets(self, ui_widget, border=0):
		# do not need any layout for editor entries
		pass

	def is_growable(self):
		return True

	################################################################
	# Events from GFTable (to update ui)
	#
	def _ui_revalidate_(self):
		self.widget.revalidate()

	def _ui_revalidate_row_(self, row):
		self.widget.revalidate()

	def _ui_set_focused_row_(self, row):
		self.widget.setGridCursor(row)

	def _ui_set_focused_cell_(self, row, col):
		#rint "table: _ui_set_focused_cell_(%s, %s)" % (row, col)

		# do not set focus if widget has PopupControl as parent
		# because grid cell editor shold not lose focus on modeless picker popup

		p = self.widget.GetParent()
		while p is not None and not isinstance(p, PopupControl):
			p = p.GetParent()

		if p is None:
			#rint "+ SetFocus in UITable._ui_set_focused_cell_"
			self.widget.GetGridWindow().SetFocus()

			# force this if was already focused
			# callafter to override callafter in create_widget
			#rint "table: schedule setGridFocused(True)", self._gfObject.getBlock().name
			wx.CallAfter(self.widget.setGridFocused, True)

		self.widget.setGridCursor(row, col + self.widget.GetTable().getBaseDataCol())

	################################################################

	def _ui_focus_out_(self):
		self.widget.HideCellEditControl()
		self.widget.SaveEditControlValue()


	################################################################
	# Events from ui (ui updated by user)
	#

	# TODO: remove __on_kill_focus, __on_select_cell
	# TODO: move __on_select_cell to __on_set_focus

	def __on_set_focus(self, event):
		#rint '--------------------- table: __on_set_focus'
		#self.__focus = True
		wx.CallAfter(self.widget.setGridFocused, True)
		event.Skip()

	def __on_kill_focus(self, event):
		#rint '--------------------- table: __on_kill_focus'
		#self.__focus = False
		wx.CallAfter(self.widget.setGridFocused, False)
		event.Skip()

	def __on_select_cell(self, event):

		#should i move this to Grid?
		assert event.GetEventObject() is self.widget

		#if self.__focus:
		
		#rint 'table: __on_select_cell'

		baseDataCol = self.widget.GetTable().getBaseDataCol()
		col = max(0, event.GetCol() - baseDataCol)

		self._gfObject._event_cell_focused(event.GetRow(), col)
		
		#else:
		#	print 'table: __on_select_cell [skipped]'
		#	assert 0, "can't be here now"
		#	pass

		event.Skip()

	def __on_menu_popup(self, event):
		# set focus to entry from this table
		row, col = self.widget.getGridCursor()
		col -= self.widget.GetTable().getBaseDataCol()
		if row < 0:	row = 0
		if col < 0:	col = 0
		self._gfObject._event_cell_focused(row, col)

		menu = self._gfObject.findChildOfType('GFMenu')
		if menu:
			menu._event_menu_popup()

	def __on_key_down(self, event):
		"""
		go next/previous entry
		"""
		if event.GetKeyCode() in [wx.WXK_TAB, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_ESCAPE]:
			#rint ">>> Event object :", event.GetEventObject()
			#rint ">>> Parent       :", event.GetEventObject().GetParent()
			#rint ">>> ET gridwindow:", self.widget.GetGridWindow()
			#rint ">>> ET grid      :", self.widget

			if event.GetEventObject().GetParent() is not self.widget:
				# finish editing before processing next record command
				self.widget.HideCellEditControl()
				self.widget.SaveEditControlValue()
			elif event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
				attr = self.widget.GetTable().GetAttr(self.widget.GetGridCursorRow(), self.widget.GetGridCursorCol(), 0)
				if attr is not None and attr.IsReadOnly():
					self._gfObject._event_row_activated()
					return

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


	def __on_cell_left_dclick(self, event):
		grid = event.GetEventObject()
		try:
			x, y = event.GetPosition()
			x -= grid.GetRowLabelSize()
			y -= grid.GetColLabelSize()
			row, col = grid.hitTest((x, y))
			attr = grid.GetTable().GetAttr(row, col, 0)
			if attr is not None and attr.IsReadOnly():
				self._gfObject._event_row_activated()
			else:
				event.Skip()
		except GridHitSpace:
			event.Skip()

	def __on_label_left_dclick(self, event):
		if event.GetCol() == -1:
			col = max(self.widget.GetGridCursorCol() - self.widget.GetTable().getBaseDataCol(), 0)
			# set cursor to this row
			self.widget.setGridCursor(
				event.GetRow(),
				col + self.widget.GetTable().getBaseDataCol(),
			)
			self._gfObject._event_cell_focused(event.GetRow(), col)
			self._gfObject._event_row_activated()
		event.Skip()

	################################################################
	# other Interface with GFTable
	#

	def _ui_get_selected_cell_(self):
		#try:
		mode = self.widget.GetSelectionMode()
		if (
			mode == wx.grid.Grid.wxGridSelectRows    and len(self.widget.getRowSelection()) == 1 or 
			mode == wx.grid.Grid.wxGridSelectColumns and len(self.widget.getColSelection()) == 1
		):
			row, col = self.widget.getGridCursor()
			if row < 0 or col < 0:
				raise SelectionError(_("Grid cursor expected"))
		else:
			row, col = self.widget.getCellSelection().getSingleCell()
		return row, col - self.widget.GetTable().getBaseDataCol()
		#except SelectionError, e:
		#	pass

	def _ui_get_selected_col_(self):
		"""
		returns field index selected if single column selected or if single cell selected
		"""
		try:
			return self.widget.getColSelection().getSingleLineOrCell() - self.widget.GetTable().getBaseDataCol()
		except SelectionError:
			pass

	def _ui_get_selected_rows_(self, no_cursor_row=False):
		"""
		returns field index selected if single column selected or if single cell selected
		"""
		rows = None
		try:
			# if returns no rows, set rows to None to check grid cursor later
			rows = self.widget.getRowSelection().getPureLines() or None
		except SelectionError:
			cellSelection = self.widget.getCellSelection()
			if cellSelection:
				try:
					row, col = cellSelection.getSingleCell()
					rows = [row]
				except SelectionError:
					# selection is ambiguous, do not check grid cursor
					rows = []

		if rows is None:
			row = self.widget.GetGridCursorRow()
			if row >= 0 and not no_cursor_row:
				rows = [row]
			else:
				rows = []

		return rows
			

	def _ui_set_context_menu_(self, menu, menuname):
		self.__menu[menuname] = menu

	def _ui_find_(self):
		self.widget.find()

	def _ui_cut_(self):
		try:
			self.widget.cut()
		except SelectionError, e:
			self._form.show_message(str(e), 'error')

	def _ui_copy_(self):
		try:
			self.widget.copy()
		except SelectionError, e:
			self._form.show_message(str(e), 'error')

	def _ui_paste_(self):
		self.widget.paste()

	def _ui_cancel_editing_(self):
		# Thanks XEditing adds python references to current editor
		if self.widget.isEditing():
			self.widget.getCellEditor().Reset()
			self.widget.HideCellEditControl()	
			self.widget.SaveEditControlValue()	# calls EndEdit normally?

	################################################################

	def _get_context_menu(self, hitArea):
		if self.__menu:
			if len(self.__menu) == 1:
				# if one menu use it for all context
				return self.__menu.values()[0]
			else:
				for context in ('rowlabel', 'collabel', 'cell', 'corner', 'space', 'row', 'col', 'any'):
					if self.__menu.has_key(context) and context in hitArea:
						return self.__menu[context]


	def __on_form_exit(__self, self):
		# to prevent crash because of open editor
		try:
			__self.widget.HideCellEditControl()
			__self.widget.SaveEditControlValue()
			__self.widget.saveConfig()
		except wx.PyDeadObjectError:
			print "! grid config not saved because of PyDeadObjectError"


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UITable,
	'provides' : 'GFTable',
	'container': True
}
