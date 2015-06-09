from wx.lib.iewin import IEHtmlWindow

class IE(IEHtmlWindow):
	"""
	Internet broser
	"""

	def setUrl(self, url):
		try:
			self.Navigate2(url or 'about:blank')
		except AttributeError:
			self.Navigate(url or 'about:blank')
