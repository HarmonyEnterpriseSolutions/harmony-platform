import wx

class StubViewer(wx.StaticText):
	def __init__(self, parent, id):
		wx.StaticText.__init__(self, parent, id, label='Content not supported')

	def setUrl(self, url):
		pass
