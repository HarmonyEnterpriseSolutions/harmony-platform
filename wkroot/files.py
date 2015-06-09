from harmlib.webkit.BaseServlet import BaseServlet
from toolib._ import *
from toolib.util import randoms
from urllib2 import quote
import os


BUF_SIZE = 0x10000

UID_N     = 10
UID_CHARS = '0123456789'

UNIQUE_STRING_TRIES_COUNT = 1000

class files(BaseServlet):
	"""
	java gnue.forms.Desktop.wrapUrl redirects here

	used in PDFViewer and Frame.uiSaveUrl
	"""

	def isLoginNotRequired(self):
		return False

	def getFilePath(self, fileName):
		path = self.getContext().getConfig('servers.conf').get('files', 'path')
		if not os.path.exists(path):
			os.makedirs(path)
		path = os.path.join(path, fileName)

		# Under unix, os.path gets LANG envorinment variable to get filesystem encoding
		# Webkit has no LANG variable so path tried to be encoded with sys.getdefaultencoding() and fails for non-ascii strings
		if not os.path.supports_unicode_filenames:
			path = path.encode('UTF-8')
		
		return path

	#def respondToPost(self, trans):
	#	"""
	#	accept file sent as multipart/form-data, 
	#	save it to unique place, 
	#	return user unique file name in response
	#	"""
	#	fs = trans.request().fields()['file']	# type is cgi.FieldStorage
	#
	#	for i in xrange(UNIQUE_STRING_TRIES_COUNT):
	#		uniqueFileName = '_'.join((randoms.getRandomString(UID_N, UID_CHARS), fs.filename))
	#		uniquePath = self.getFilePath(uniqueFileName)
	#		if not os.path.exists(uniquePath):
	#			open(uniquePath, 'wb').write(fs.value)
	#			break
	#	else:
	#		raise RuntimeError, "Can't generate unique file name"
	#
	#	trans.response().setHeader("content-type", 'text/plain')
	#	trans.response().write(uniqueFileName)

	def respondToPost(self, trans):
		"""
		accept file sent as application/octet-stream, 
		save it to unique place, 
		return user unique file name in response
		"""
		fileName = trans.request().fields()['file'].decode('UTF-8')
		rawInput = trans.request().rawInput(True)
		
		for i in xrange(UNIQUE_STRING_TRIES_COUNT):
			uniqueFileName = u'_'.join((randoms.getRandomString(UID_N, UID_CHARS), fileName))
			uniquePath = self.getFilePath(uniqueFileName)
			if not os.path.exists(uniquePath):
				f = open(uniquePath, 'wb')
				while True:
					buf = rawInput.read(BUF_SIZE)
					if not buf: break
					f.write(buf)
				f.close()
				break
		else:
			raise RuntimeError, "Can't generate unique file name"

		trans.response().setHeader("content-type", 'text/plain')
		trans.response().write(uniqueFileName.encode('UTF-8'))

	def respondToGet(self, trans):
		uniqueFileName = self.request().fields()['file'].decode('UTF-8')
		command = self.request().fields()['command']

		uniquePath = self.getFilePath(uniqueFileName)
		if os.path.exists(uniquePath):
			if command == 'get':
				trans.response().setHeader("content-type", 'application/octet-stream')
				f = open(uniquePath, 'rb')
				try:
					while True:
						buf = f.read(BUF_SIZE)
						if not buf:
							break
						trans.response().write(buf)
				finally:
					f.close()
			elif command == 'delete':
				os.remove(uniquePath)
		else:
			trans.response().setHeader('Status', "404 %s" % _('File not found'))
