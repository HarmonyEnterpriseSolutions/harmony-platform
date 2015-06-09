import os
import tempfile
import urllib2
#from toolib.util.Pump import stream2stream
from toolib import debug
import wx
import wx.lib.delayedresult as delayedresult
from urllib2 import HTTPError
from gnue.common.apps.errors import UserError

class TempFileMixIn(object):
	"""
	downloads url resourceee to temp file
	uses provided openFile and closeFile methods thrue temp file
	"""

	def __init__(self, openFile, closeFile=None, checkFile=None, getData=None, openBusyFile=None):
		self.__tempFile     = None
		self.__openFile     = openFile
		self.__openBusyFile = openBusyFile
		self.__closeFile    = closeFile
		self.__checkFile    = checkFile	# checks if file is ok
		self.__getData      = getData
		self.__filesToRemove = set()

		self.__abortEvent = delayedresult.AbortEvent()
		self.__workerThread = None

	def __close(self):
		#rint "+ close"

		# abort previous job if any
		self.handleAbort()

		if self.__closeFile is not None:
			#rint "+ closeFile"
			try:
				self.__closeFile()
			except Exception, e:
				debug.error("failed to close file")
				pass

		#rint "+ cleanup after close"
		self.__cleanup()


	def __open(self, url):
		if self.__openBusyFile:
			self.__openBusyFile()
		self.__workerThread = delayedresult.startWorker(
			self.__resultConsumer,
			self.__resultProducer,
			wargs = (url, self.__abortEvent),
		)


	def handleAbort(self):
		"""Abort the result computation."""
		if self.__workerThread is not None and self.__workerThread.isAlive():
			#rint "aborting url download..."
			self.__abortEvent.set()
			self.__workerThread.join()
			self.__workerThread = None
		#rint "aborted ok"
		self.__abortEvent.clear()

	def __resultProducer(self, url, abortEvent):
		self.__data = None
		res = urllib2.urlopen(url)

		fd, fname = self.__tempFile = tempfile.mkstemp()
		self.__filesToRemove.add(fname)
		f = os.fdopen(fd, 'wb')
		try:
			n = 4086
			data = []
			while True:
				try:
					abortEvent()
				except delayedresult.AbortedException:
					#rint "abort requested!"
					f.close()
					f = None
					self.__cleanup()
					raise
				else:
					s = res.read(n)
					#rint "downloaded", len(s), "bytes"
					if s:
						f.write(s)
						data.append(s)
					else:
						break
			self.__data = ''.join(data)
			return fname
		finally:
			res.close()
			if f:
				f.close()

	def __resultConsumer(self, delayedResult):
		try:
			try:
				fname = delayedResult.get()
			except:
				if self.__openBusyFile and self.__closeFile:
					self.__closeFile()
				raise
		except HTTPError, e:
			if e.code == 502:
				raise UserError(_("No response from server:\n%s") % e)
			elif e.code == 403:
				raise UserError(_("Access denied"))
			else:
				raise
		else:
			try:
				if self.__checkFile: self.__checkFile(fname)
				self.__openFile(fname)
			finally:
				# if close is defined do not try to remove temp file until close
				if self.__closeFile is None:
					self.__cleanup()


	def __cleanup(self):
		#rint "+ cleanup:"
		for name in tuple(self.__filesToRemove):
			try:
				os.remove(name)
			except:
				debug.error('failed to remove temporary file:', name)
				pass
			else:
				#rint '+ temp file removed:', name
				self.__filesToRemove.remove(name)

	def setUrl(self, url):
		self.__close()
		if url:
			self.__open(url)

	def getData(self):
		if self.__getData:
			return self.__getData()
		elif self.__tempFile:
			#return open(self.__tempFile[1], 'rb').read()
			#os.fdopen(self.__tempFile[0], 'rb').read()
			return self.__data
