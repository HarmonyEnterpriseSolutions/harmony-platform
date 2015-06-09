"""
Acrobat reader 5.0 ActiveX support
Note: not displays russian fonts from Jasper reports generated pdfs
"""

import win32com.client.gencache
from wx.lib.activexwrapper import MakeActiveXClass
from src.gnue.forms.uidrivers.wx26.widgets.url_resource import PdfCheckerMixIn, TempFileMixIn

acrobat = win32com.client.gencache.EnsureModule('{CA8A9783-280D-11CF-A24D-444553540000}', 0x0, 1, 3)

if not acrobat:
	raise ImportError, 'Acrobat Reader 5.0 is not installed'


Base = MakeActiveXClass(acrobat.Pdf)


class AcrobatReader5(TempFileMixIn, PdfCheckerMixIn, Base):
	"""
	An implementation of a wx widget used for displaying pdfs
	"""

	def __init__(self, *args, **kwargs):
		Base.__init__(self, *args, **kwargs)
		TempFileMixIn.__init__(self, self.LoadFile, checkFile=self.checkPdfFile)
