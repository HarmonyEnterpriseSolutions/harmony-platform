"""
Foxit reader ActiveX (foxitreader_ax.ocx) support

Note: Foxit reader ActiveX is not free, evaluation version only
      run bin/foxitreader_register.cmd to evaluate
      run bin/foxitreader_unregister.cmd to uninstall activex

Note: IE driver may work with free foxit reader if no adobe acrobat installed
"""

import win32com.client.gencache
from wx.lib.activexwrapper import MakeActiveXClass
from src.gnue.forms.uidrivers.wx26.widgets.url_resource import PdfCheckerMixIn, TempFileMixIn

foxit = win32com.client.gencache.EnsureModule('{388F9F25-E145-4CCE-8E44-D808AC984081}', 0x0, 1, 0)

if not foxit:
	raise ImportError, 'Foxit Reader SDK ActiveX is not installed'

Base = MakeActiveXClass(foxit.FoxitReaderSDK)

class FoxitReader(TempFileMixIn, PdfCheckerMixIn, Base):
	"""
	An implementation of a wx widget used for displaying pdfs
	"""

	def __init__(self, *args, **kwargs):
		Base.__init__(self, *args, **kwargs)

		TempFileMixIn.__init__(self,
			lambda filename: self.OpenFile(filename, ''),
			self.CloseFile,
			checkFile=self.checkPdfFile,
		)
