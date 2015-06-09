import wx

from toolib.wx.controls.ButtonList              import ButtonList
from gnue.forms.uidrivers.wx26.widgets._base    import UIHelper

from gnue.forms.input import GFKeyMapper
from toolib.wx.mixin.TWindowUtils import getTopLevelParent
from src.gnue.forms.uidrivers.wx26.widgets._config import BORDER_SPACE

_all__ = ["UIList"]

class Tabs(wx.Notebook):

	def __init__(self, parent, uiObject):	
		wx.Notebook.__init__(self, parent, -1, style=wx.WANTS_CHARS)
		self._uiObject = uiObject
		self._gfObject = uiObject._gfObject

		self.Bind(wx.EVT_KEY_DOWN, self._uiObject._on_char, self)
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__on_page_changed, self)
		self.__container = wx.Panel(self, -1)
		self.__container.SetSizer(wx.GridSizer(1, 1))

		self.__eventsEnabled = True

	def _ui_set_values_(self, values):
		#rint '_ui_set_values_', values
		#self.SetEvtHandlerEnabled(False)	# This is buggy (control does not paint content after this)
		self.__eventsEnabled = False
		self.Freeze()
		
		for i in range(self.GetPageCount()-1,-1,-1):
			self.RemovePage(i)
		
		for text in values:
			self.AddPage(self.__container, text, True)
		
		# True in previous AddPage and SetSelection(0) after is workaround to paint content
		if values:
			self.SetSelection(0)

		self.Thaw()
		self.__eventsEnabled = True

	def _ui_set_value_(self, index, value):
		self.SetPageText(index, value)

	def _ui_select_row_(self, index):
		#rint '_ui_select_row_', index
		self.__eventsEnabled = False
		focusOwner = wx.Window.FindFocus()
		self.SetSelection(index)
		
		# WORKAROUND: SetSelection sets focus to selected notepage so return focus to owner
		if focusOwner:
			focusOwner2 = wx.Window.FindFocus()
			if focusOwner is not focusOwner2:
				focusOwner.SetFocus()
		self.__eventsEnabled = True

	def add_widgets(self, uiWidget):
		self.__container.GetSizer().Add(
			uiWidget.widget, 
			0, 
			wx.GROW | wx.ALL, 
			0 if uiWidget._gfObject._type in ('GFTree', 'GFTable', 'GFSplitter', 'GFNotebook', 'GFUrlResource', 'GFList') else BORDER_SPACE
		)

	def getContainer(self):	
		"""
		used to set UIWidget._container in _create_widget_
		"""
		return self.__container

	def __on_page_changed(self, event):
		if self.__eventsEnabled:
			#from toolib.debug import stack
			#rint stack()
			self._gfObject._event_item_focused(event.GetSelection())
		event.Skip()


class Buttons(ButtonList):

	def __init__(self, parent, uiObject):
		ButtonList.__init__(self, parent, -1, style=wx.WANTS_CHARS)
		self._uiObject = uiObject
		self._gfObject = uiObject._gfObject
		self.Bind(wx.EVT_BUTTON, self.__on_button)		#GetGridWindow().

	def _ui_set_values_(self, values):
		for b in self.getButtons():
			b.Unbind(wx.EVT_CHAR, b)
			b.Unbind(wx.EVT_SET_FOCUS, b)

		self.SetItems(values)

		for b in self.getButtons():
			b.Bind(wx.EVT_CHAR, self._uiObject._on_char, b)
			b.Bind(wx.EVT_SET_FOCUS, self.__on_set_focus, b)
	
		parent = getTopLevelParent(self)
		if isinstance(parent, wx.Dialog):
			parent.Fit()
			parent.CenterOnScreen()

	def _ui_set_value_(self, index, value):
		self.SetString(index, value)

	def _ui_select_row_(self, index):
		self.getButtonAt(index).SetFocus()

	def __on_button(self, event):
		self._gfObject._event_item_activated()

	def __on_set_focus(self, event):
		self._gfObject._event_item_focused(self.getButtonIndex(event.GetEventObject()))

	def getContainer(self):
		return None

# =============================================================================
# Interface implementation for a grid widget
# =============================================================================

class UIList(UIHelper):

	def __init__(self, event):
		UIHelper.__init__(self, event)

	def _create_widget_ (self, event):

		self.widget = eval(self._gfObject.style.capitalize())(event.container, self)
		self._container = self.widget.getContainer()

		self.getParent().add_widgets(self)

	def is_growable(self):
		return self._gfObject.style in ('tabs',)
	
	def __getattr__(self, name):
		return getattr(self.widget, name)

	def _on_char(self, event):

		#rint "char"

		keycode = event.GetKeyCode()

		is_cmd = keycode in [wx.WXK_TAB, wx.WXK_RETURN, wx.WXK_UP, wx.WXK_DOWN, wx.WXK_ESCAPE]
		command = None

		if is_cmd:
			(command, args) = GFKeyMapper.KeyMapper.getEvent(keycode,
				event.ShiftDown(),
				event.CmdDown(),
				event.AltDown())

			if command is 'NEXTENTRY':
				if self._gfObject._event_next_row():
					command = None
			elif command is 'PREVENTRY':
				if self._gfObject._event_prev_row():
					command = None
			elif command is 'ENTER':
				self._gfObject._event_item_activated()
				command = None

		if command:
			self._request(command, triggerName=args)
		else:
			event.Skip()


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIList,
	'provides' : 'GFList',
	'container': True
}
