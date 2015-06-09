"""
Acrobat reader 7.0, 8.0... ActiveX support
"""

import win32com.client.gencache
from wx.lib.activexwrapper import MakeActiveXClass
from src.gnue.forms.uidrivers.wx26.widgets.url_resource import PdfCheckerMixIn, TempFileMixIn

acrobat = win32com.client.gencache.EnsureModule('{05BFD3F1-6319-4F30-B752-C7A22889BCC4}', 0x0, 1, 0)

if not acrobat:
	raise ImportError, 'Acrobat Reader 7.0 or greater is not installed'


Base = MakeActiveXClass(acrobat.AcroPDF)


class AcrobatReader7(TempFileMixIn, PdfCheckerMixIn, Base):
	"""
	An implementation of a wx widget used for displaying pdfs
	"""

	def __init__(self, *args, **kwargs):
		Base.__init__(self, *args, **kwargs)
		TempFileMixIn.__init__(self, self.LoadFile, checkFile=self.checkPdfFile)
