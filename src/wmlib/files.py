#-*- coding: cp1251 -*-

"""
files client for gnue-forms triggers
"""
import os
import tempfile
from wmlib.webkit.FilesClient import FilesClient

BUF_SIZE = 0x10000

def getFilesClient(form, public):
	return FilesClient('%s/%s?%s' % (
		form.get_global('server_url'),
		'publicfiles' if public else 'files',
		form.get_global('__form_server_query_string__'),
	))

def uploadFile(form, entry, message=None, public=False):
	"""
	returns unique file name

	selectFiles params:

	@param title: Message to show on the dialog
	@param defaultDir: the default directory, or the empty string
	@param defaultFile: the default filename, or the empty string
	@param wildcard: a list of tuples describing the filters used by the
	    dialog.  Such a tuple constists of a description and a fileter.
	    Example: [('PNG Files', '*.png'), ('JPEG Files', '*.jpg')]
	    If no wildcard is given, all files will match (*.*)
	@param mode: Is this dialog an open- or a save-dialog.  If mode is
	    'save' it is a save dialog, everything else would be an
	    open-dialog.
	@param multiple: for open-dialog only: if True, allows selecting
	    multiple files
	@param overwritePrompt: for save-dialog only: if True, prompt for a
	    confirmation if a file will be overwritten
	@param fileMustExist: if True, the user may only select files that
	    actually exist
	"""

	def resultConsumer(files):
		if files:
			filePath = files[0]

			url = getFilesClient(form, public).getCommandUrl('post', os.path.split(filePath)[1])

			def onUploaded(response):

				fileName = response.decode('UTF-8')

				if entry.isCellEditor():
					entry.getParent().cancelEditing()
					entry.getField().set(fileName)
					form.next_entry()
				else:
					form.endEditing()
					try:
						entry.getField().set(fileName)
					finally:
						form.beginEditing()

			form.uploadFile(filePath, url, onUploaded)

	form.selectFiles(message or u_(u'Выберите файл для загрузки...'), '', '', mode='open', fileMustExist=True, resultConsumer=resultConsumer, name='files_client')


def _getEntryText(form, entry):
	if entry.isCellEditor():	# ok
		return entry.getText()
	else:
		form.endEditing()
		try:
			return entry.getField().get()
		finally:
			form.beginEditing()
	return fileName


def downloadFile(form, entry, message=None, public=False):
	fileName = _getEntryText(form, entry)

	if fileName:

		def resultConsumer(files, verbose=True):

			if files:
				filePath = files[0]
				url = getFilesClient(form, public).getCommandUrl('get', fileName)
				form.downloadFile(url, filePath)
		
		ext = os.path.splitext(fileName)[1]
		wildcard = [(u_(u"Файл %s") % ext[1:].upper(), '*' + ext)] if ext else None
		form.selectFiles(message or u_(u"Сохранить файл в..."), '', fileName.lstrip('0123456789_'), wildcard, 'save', resultConsumer = resultConsumer, name='files_client')


def startFile(form, entry, public=False):
	fileName = _getEntryText(form, entry)
	if fileName:
		url = getFilesClient(form, public).getCommandUrl('get', fileName)
		form.startFile(url, fileName)
