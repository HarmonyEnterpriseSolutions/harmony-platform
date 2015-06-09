"""
Remote classes:

Widget			                            has label, tip
	MenuBar                                  
	Menu                                     
	PopupMenu                                
	MenuItem                                 
	ToolBar                                  
	StatusBar                                
	ToolButton                              +
	HBox                                    +
	VBox                                    +
	Panel                                   +
	Label                                   +
	Table                                   text
	Splitter                                 
	EntryButton                             text
	WidgetNavigable                         +
		ButtonAbstract                      text
			Button                          text
		Tree                                +
		Entry                               +
			EntryToggleButton               +
				EntryCheckbox               +
				EntryRadiobutton            +
			EntryAbstractText(Entry):       +
				EntryDefault                +
					EntryLabel              +
					EntryText_with_buttons  +
				EntryMultiline              +
				EntryPassword               +
				EntryDropdown               +
				EntryDatepicker             +
				EntryPicker                 +
					EntryPicker_with_editor +
		URLViewer                           +
			URLViewerPDF                    +
			URLViewerStub                   +
		List
	FrameAbstract                           title
		Frame                               title
		Dialog                              title
		PopupWindow                         title
	Notebook                                +
		NotebookCloseable                   +
"""

from src.gnue.forms.uidrivers.java.widgets._base import Stated
from src.gnue.forms.uidrivers.java.widgets._base import RemoteWidget as Widget
from toolib.util.DateTimePattern import DateTimePattern

# remote stubs

# ----------------------------------------------------------------------

class WidgetNavigable(Widget):
	
	def onSetFocus(self):
		self._uiWidget.onSetFocus()

	def onKeyPressed(self, keycode, shiftDown, ctrlDown, altDown):
		self._uiWidget.onKeyPressed(keycode, shiftDown, ctrlDown, altDown)


class ButtonAbstract(WidgetNavigable):
	def onButton(self):
		self._uiWidget.onButton()

class Button(ButtonAbstract):
    pass

class EntryButton(Widget):

	def onButton(self):
		self._uiWidget.onButton()


class Tree(WidgetNavigable):
	
	def onGetChildren(self, parentId):
		return self._uiWidget.onGetChildren(parentId)

	def onGetNodeStyle(self, key):
		return self._uiWidget.onGetNodeStyle(key)

	def onSelectionChanged(self, id):
		return self._uiWidget.onSelectionChanged(id)

	def onNodeActivated(self):
		self._uiWidget.onNodeActivated()

	def onNodesChecked(self, nodes):
		self._uiWidget.onNodesChecked(nodes)

	def onMenuPopup(self, id):
		self._uiWidget.onMenuPopup(id)

# ----------------------------------------------------------------------

class Entry(WidgetNavigable):
	
	def onStopCellEditing(self, value):
		self._uiWidget.onStopCellEditing(value)

# abstract
class EntryToggleButton(Entry):
	def onChecked(self, value):
		self._uiWidget.onChecked(value)

class EntryCheckbox(EntryToggleButton):
	pass

class EntryRadiobutton(EntryToggleButton):
	pass

class EntryAbstractText(Entry):

	def onTextChanged(self, text, cursorPosition):
		self._uiWidget.onTextChanged(text, cursorPosition)

class EntryDefault(EntryAbstractText):
	pass

class EntryText_with_buttons(EntryDefault):
	pass

class EntryLabel(EntryDefault):
	pass

class EntryMultiline(EntryAbstractText):
	pass

class EntryPassword(EntryAbstractText):
	pass

class EntryDropdown(EntryAbstractText):
	pass

class EntryDatepicker(EntryAbstractText):
	
	def __init__(self, uiWidget, label, tip, align):
		super(EntryDatepicker, self).__init__(
			uiWidget, 
			label, 
			tip, 
			align, 
			DateTimePattern(uiWidget._gfObject._displayHandler._input_mask).getJavaFormat()
		)


class EntryPicker(EntryAbstractText):
	pass

class EntryPicker_with_editor(EntryPicker):
	def onCustomEditor(self):
		self._uiWidget.onCustomEditor()

# ----------------------------------------------------------------------

class FrameAbstract(Widget, Stated):
	
	def onShowMessage(self, result):
		self._uiWidget.onShowMessage(result)

	def onSelectFiles(self, result):
		self._uiWidget.onSelectFiles(result)

	def onSelectDir(self, result):
		self._uiWidget.onSelectDir(result)

	def onUploadFile(self, result):
		self._uiWidget.onUploadFile(result)
	
	def onClose(self):
		self._uiWidget.onClose()

	def onCallAfter(self):
		self._uiWidget.onCallAfter()

	def onAfterModal(self):
		self._uiWidget.onAfterModal()

class Frame(FrameAbstract):
	pass

class Dialog(FrameAbstract):
	pass

class PopupWindow(FrameAbstract):

	def onPopup(self, popup):
		self._uiWidget.onPopup(popup)


# ----------------------------------------------------------------------
class Notebook(Widget):

	def onPageChanged(self, *args, **kwargs):
		self._uiWidget.onPageChanged(*args, **kwargs)

class NotebookCloseable(Notebook):

	def onPageClose(self, *args, **kwargs):
		self._uiWidget.onPageClose(*args, **kwargs)

	def onExit(self, *args, **kwargs):
		self._uiWidget.onExit(*args, **kwargs)


# ----------------------------------------------------------------------

class MenuBar(Widget):
	pass

class Menu(Widget):
	pass

class PopupMenu(Widget):
	pass

class MenuItem(Widget):
	
	def onMenu(self):
		self._uiWidget.onMenu(self)


# ----------------------------------------------------------------------

class ToolBar(Widget):
	pass

class StatusBar(Widget):
	pass

class ToolButton(Widget):
	
	def onButton(self):
		self._uiWidget.onButton()


# ----------------------------------------------------------------------

class HBox(Widget):
	pass

class VBox(Widget):
	pass

# ----------------------------------------------------------------------

class Panel(Widget):
	pass

class Label(Widget):
	pass

class Table(Widget, Stated):
	def onSelectionChange(self, row, col, rows):
		self._uiWidget.onSelectionChange(row, col, rows)

	def onRowActivated(self):
		self._uiWidget.onRowActivated()

	def onMenuPopup(self, *args, **kwargs):
		self._uiWidget.onMenuPopup(*args, **kwargs)
		
	def onKeyPressed(self, keycode, shiftDown, ctrlDown, altDown):
		self._uiWidget.onKeyPressed(keycode, shiftDown, ctrlDown, altDown)

	def onCopy(self, *args, **kwargs):
		return self._uiWidget.onCopy(*args, **kwargs)

	def onErase(self, *args, **kwargs):
		self._uiWidget.onErase(*args, **kwargs)

	def onPaste(self, *args, **kwargs):
		self._uiWidget.onPaste(*args, **kwargs)

class Splitter(Widget, Stated):
	pass


# ----------------------------------------------------------------------

class URLViewer(WidgetNavigable):
	pass

class URLViewerPDF(URLViewer):
	pass

class URLViewerStub(URLViewer):
	pass

class List(WidgetNavigable):
	def onSelectionChanged(self, index):
		return self._uiWidget.onSelectionChanged(index)
