#-*- coding: cp1251 -*-
import os
import sys
from urllib2 import urlopen, HTTPError, Request, quote
#from toolib.web.mime import MimeMultipart

class FilesClient(object):

	def __init__(self, serviceUrl):
		self._serviceUrl = serviceUrl

	def uploadFile(self, filePath, fileName=None):
		"""
		returns unique file name
		"""
		#headers, body = MimeMultipart.encode((), (('file', fileName, open(filePath, 'rb').read()),))
		#request = Request(self._serviceUrl, body, headers)
		#return urlopen(request).read()
		
		url = self.getCommandUrl('post', fileName or os.path.split(filePath)[1])
		body = open(filePath, 'rb').read()
		headers = {
			'Content-Type'   : 'application/octet-stream',
			'Content-Length' : len(body),
		}
		return urlopen(Request(url, body, headers)).read().decode('UTF-8')

	def getCommandUrl(self, command, uniqueFileName):
		# encode unicode filename to UTF-8
		return self._serviceUrl + '%scommand=%s&file=%s' % ('&' if '?' in self._serviceUrl else '?', command, quote(uniqueFileName.encode('UTF-8')))

	def downloadFile(self, uniqueFileName):
		"""
		returns file like object to read file data
		"""
		return urlopen(self.getCommandUrl('get', uniqueFileName))

	def deleteFile(self, uniqueFileName):
		"""
		removes file on server
		"""
		urlopen(self.getCommandUrl('delete', uniqueFileName))

if __name__ == '__main__':
	from toolib import startup
	startup.startup()

	fc = FilesClient('http://localhost:82/wm/wk.cgi/wm/files')

	fname = fc.uploadFile(u'C:\\автоекзек.bat')#'F:\photos\me.psd')

	print "UPLOADED:", fname
	print "----------"
	print fc.downloadFile(fname).read()
	print "----------"
	fc.deleteFile(fname)


