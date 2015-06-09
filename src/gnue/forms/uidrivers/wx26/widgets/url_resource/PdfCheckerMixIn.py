from toolib._ import *
import re

class PdfResourceError(Exception):
	pass


class PdfCheckerMixIn(object):

	def checkPdfFile(self, file):
		magic = open(file, 'rb').read(5)
		if magic != '%PDF-':
			message = _("PDF expected from server, got unrecognized text")
			text = open(file, 'rt').read()
			if magic.upper() == '<HTML':
				m = re.compile(r'(?is)<!--\[DETAIL\[-->\s*(.*)\s*<!--\]\]-->').search(text)
				if m:
					text = m.groups()[0]
					message = _("Got error on pdf server")
			raise PdfResourceError, "%s[DETAIL[%s]]" % (message, text)
