import os

from wx.lib.pdfwin   import PDFWindow, get_min_adobe_version
from TempFileMixIn   import TempFileMixIn
from gnue import paths
from src.gnue.forms.uidrivers.wx26.widgets.url_resource import PdfCheckerMixIn


if get_min_adobe_version() is None:
	raise ImportError, 'Adobe Acrobat Reader 5.0, 7.0 or greater is required to be installed'

class PDF(TempFileMixIn, PdfCheckerMixIn, PDFWindow):
	"""
	An implementation of a wx widget used for displaying pdfs
	"""

	def __init__(self, *args, **kwargs):
		PDFWindow.__init__(self, *args, **kwargs)
		TempFileMixIn.__init__(self, self._openFile, self._closeFile, checkFile=self.checkPdfFile, openBusyFile=self._openBusyFile)
		self.__path = os.path.join(paths.data, 'share', 'gnue', 'pdf')

	def _closeFile(self):
		self.LoadFile(os.path.join(self.__path, "blank.pdf"))

	def _openBusyFile(self):
		self.LoadFile(os.path.join(self.__path, "busy.pdf"))
		
	def _openFile(self, url):
		self.LoadFile(url)
