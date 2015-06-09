# -*- coding: Cp1251 -*-

import os
import sys
import re
import urllib
from urllib2 import urlopen, HTTPError
import locale as locale_module
from simplejson import dumps
import zlib
import base64
from toolib import debug
from toolib.util.Pump import stream2file, stream2stream
from subprocess import Popen
import tempfile

try: u_
except: u_ = lambda x: x

def getReportQuery(
		form,
		query_or_name,			# name is deprecated since accepts multiquery
		parameters  = None,		# deprecated

		format      = None,	    # deprecated
		printer     = None,		# deprecated
		copies      = 1,		# deprecated
		connection  = None,		# deprecated
		accessobject_id = None,	# deprecated
		locale      = None,		# deprecated
	):
	"""
	uses form globals:
		application
		server_url
	
	if locale is none, client default locale is used

	{
		'application' : '?',
		'format'   : 'pdf|xls|html|csv|print',
		'copies'   : 1,
		'printer'  : '',
		'locale'   : 'ru_RU|uk_UA|en_GB',

		'reports'  : [
			{
				'name' : '?',
				'connection' : '?',
				'aoid' : '?',			# used by python proxy to check permission
				
				'parameters' : {
					'name' : 'value',
				}
			}

		],
	}

	"""

	if isinstance(query_or_name, dict):
		# this is query
		query = query_or_name

		# apply old parameters if passed
		if format is not None:
			query['format'] = format
	else:
		# make query from old parameters
		query = {
			'format'   : format or 'pdf',
			'locale'   : locale,
			'reports'  : [
				{
					'name'       : query_or_name,
					'connection' : connection,
					'parameters' : parameters,
					'aoid'       : accessobject_id,
				},
			],
		}
		if format == 'print':
			query['copies'] = copies
			query['printer'] = printer

	if 'application' not in query:
		query['application'] = form.get_global('application')

	if 'locale' not in query:
		query['locale'] = locale_module.getdefaultlocale()[0]

	# TODO: Printers is not Defined here, fix or to work only on windows
	#if query.get('format') == 'print':
	#	query['printer'] = query.get('printer') or Printers.getDefaultPrinterNetworkName()

	# convert parameters to str
	for report in query['reports']:
		report['parameters'] = parameters = (report.get('parameters') or {}).copy()
		for k, v in parameters.iteritems():
			if isinstance(v, list):
				parameters[k] = ','.join(map(unicode, v))
			elif not isinstance(v, basestring):
				parameters[k] = str(v)
	
	return dumps(query)


def getReportUrl(
		form,
		query_or_name,			# name is deprecated since accepts multiquery
		**kwargs				# deprecated
	):

	query = getReportQuery(form, query_or_name, **kwargs)
	
	qsz = urllib.urlencode({
		'zq' : base64.encodestring(zlib.compress(query, 9)),
	})

	url = '%s/report?%s&%s' % (
		form.get_global('server_url'),
		qsz,
		form.get_global('__form_server_query_string__'),
	)

	if len(url) > 1024:
		raise form.error(u_(u"Очень жаль, максимальная длина запроса к серверу отчетов превышена в %.1f раз\nВыберите меньшее количество строк") % (len(url) / 1024.0,))

	return url


def openReportUrl(form, *args, **kwargs):
	url = getReportUrl(form, *args, **kwargs)
	try:
		return urlopen(url)
	except HTTPError, e:
		if e.code == 502:
			raise form.error(u_(u"Сервер отчетов не отвечает\n%s") % e)
		elif e.code == 403:
			raise form.error(str(e))
		else:
			raise


def openReportPost(form, query, timeout=None, max_reports_per_query = 20):
	# webkit stream has timeout
	# http://192.168.2.8/trac/harm/ticket/655
	# to workaround this issue, try connect directly
	
	report_server_direct_url = form.get_global('report_server_direct_url', None)

	if report_server_direct_url:
		print "+ using report server directly"
		url = '%s/report' % report_server_direct_url
	else:
		url = '%s/report?%s' % (
			form.get_global('server_url'),
			form.get_global('__form_server_query_string__'),
		)

	query = dict(query)
	reports = query['reports']

	n = (len(reports) - 1) / max_reports_per_query + 1

	fnames = []

	for i in xrange(n):
		query['reports'] = reports[max_reports_per_query * i: max_reports_per_query * (i + 1)]
	
		f = _openReportPost(url, getReportQuery(form, query), timeout)

		if n == 1:
			return f
		else:
			fname = tempfile.mktemp('.pdf')
			fnames.append(fname)
			stream2file(f, fname, filemode='b')
			             	
	if len(fnames) > 1:
		pdftk = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'bin', 'pdftk.exe')

		command = '%s %s cat output -' % (pdftk, ' '.join(fnames))

		out, err = os.popen3(command, 'b')[1:]

		outfile = tempfile.NamedTemporaryFile(suffix='.pdf')

		stream2stream(out, outfile)
	else:
		file2stream(fname, outfile)

	error = err.read()
	err.close()

	if error:
		raise RuntimeError, error

	out.close()

	for i in fnames:
		try:
			os.remove(i)
		except Exception, e:
			print "* failed to remove %s: %s: %s" % (i, e.__class__.__name__, e)

	outfile.seek(0)
	return outfile



def _openReportPost(url, json_query, timeout):

	try:
		if sys.version[:3] >= '2.6':
			return urlopen(url, urllib.urlencode({ 'q' : json_query, }), timeout)
		else:
			if timeout is not None:
				debug.warning('urlopen timeout not supported in python version < 2.6')
			return urlopen(url, urllib.urlencode({ 'q' : json_query, }))
	except HTTPError, e:
		if e.code == 502:
			raise form.error(u_(u"Сервер отчетов не отвечает\n%s") % e)
		elif e.code == 403:
			raise form.error(str(e))
		else:
			raise




def saveReportPost(
		form,
		query,

		filename = None,
		selectfiles_name = None,
		timeout = None,
		on_success = lambda filename: None,
	):

	assert isinstance(query, dict)

	patterns = []	

	format = query.get('format')
	
	if format:
		formats = (format,)
	else:
		formats = ('pdf', 'csv', 'xls', 'png')

	zip = query.get('zip', False)

	patterns = [((u_('Файлы %s в архиве ZIP') if zip else u_('Файлы %s')) % i.upper(), ('*.%s.zip' if zip else '*.%s') % i.lower()) for i in formats]
	
	def onSelectFiles(files):

		if not files:
			return

		file = files[0]

		if format is None:
			q = dict(query)
			q['format'] = os.path.splitext(file)[1][1:]
		else:
			q = query

		f = openReportPost(form, q, timeout=timeout)
				
		stream2file(f, file, filemode='b')

		on_success(file)

	form.selectFiles(
		u_(u"Выберите файл чтобы сохранить отчет..."),
		'',
		filename,
		patterns,
		'save',
		resultConsumer = onSelectFiles,
		name = selectfiles_name,
	)


try:
	from toolib.win32 import Printers
except ImportError:
	pass
else:

	class PrintReportError(Exception):
		pass
	
	def printReport(
			form, 
			query_or_name,

			parameters = None,		# deprecated
			printer    = None,		# deprecated
			copies     = 1,			# deprecated
			connection = None,		# deprecated
			accessobject_id = None,	# deprecated
			locale     = None,		# deprecated

			verbose    = True,
			clientSide = True,
		):
		if clientSide:
			if isinstance(query_or_name, dict):
				query_or_name = query_or_name.copy()
				query_or_name['format'] = 'pdf'
				printer = query_or_name.get('printer')
				data = openReportUrl(form, query_or_name).read()
			else:
				# DEPRECATED CASE
				data = openReportUrl(
					form, 
					query_or_name,
					format     = 'pdf',			# this is not used if query_or_name is query
					parameters = parameters,
					connection = connection,
					accessobject_id = accessobject_id,
					locale     = locale,
				).read()

			magic = data[:5]
			if magic != '%PDF-':
				message = u_(u"PDF expected from server, got unrecognized text")
				text = data
				if magic.upper() == '<HTML':
					m = re.compile(r'(?is)<!--\[DETAIL\[-->\s*(.*)\s*<!--\]\]-->').search(text)
					if m:
						text = m.groups()[0]
						message = u_(u"Got error on pdf server")
				raise RuntimeError, u"%s[DETAIL[%s]]" % (message, text)

			tempf = tempfile.mktemp('.pdf')
			open(tempf, 'wb').write(data)
			try:
				Printers.printPdf(tempf, printer)
			finally:
				os.remove(tempf)

			if verbose:
				form.show_message(u_(u"Отчет успешно отправлен на печать"), 'info')
		else:
			
			try:
				if isinstance(query_or_name, dict):
					query_or_name = query_or_name.copy()
					query_or_name['format'] = 'print'
					query_or_name['printer'] = query_or_name.get('printer') or Printers.getDefaultPrinterNetworkName()
					response = openReportUrl(form, query_or_name)
				else:
					# DEPRECATED CASE
					response = openReportUrl(
						form, 
						query_or_name,
						format     = 'print',
						printer    = printer,
						copies     = copies,
						parameters = parameters,
						connection = connection,
						accessobject_id = accessobject_id,
						locale     = locale,
					)
				text = response.read()
				response.close()
			except Exception, e:
				raise PrintReportError, u"%s[DETAIL[%s]]" % (u_(u"Ошибка при печати отчета"), u"%s: %s" % (e.__class__.__name__, e))
			else:
				m = re.compile(r'(?is)<!--\[DETAIL\[-->\s*(.*)\s*<!--\]\]-->').search(text)
				if m:
					raise PrintReportError, u"%s[DETAIL[%s]]" % (u_(u"Ошибка при печати отчета"), m.groups()[0])
				elif verbose:
					form.show_message(u_(u"Отчет успешно отправлен на печать"), 'info')


def saveReport(
		form,
		query_or_name,
		parameters = None,

		format     = None,		# deprecated
		verbose    = True,		# deprecated
		connection = None,		# deprecated
		accessobject_id = None,	# deprecated
		locale     = None,		# deprecated

		filename   = None,

		selectfiles_name = 'save_report',

		on_success = lambda filename: None,
		avail_formats = None
	):

	patterns = []	

	if isinstance(query_or_name, dict):
		format = query_or_name.get('format')
	#else deprecated case, format goes from parameters
	
	if avail_formats:
		formats = avail_formats
	else:
		if format:
			formats = (format,)
		else:
			formats = ('pdf', 'csv', 'xls', 'png')

	patterns = [(u_('%s Files') % i.upper(), '*.' + i.lower()) for i in formats]
	
	def onSelectFiles(files):

		if not files:
			return

		file = files[0]

		if isinstance(query_or_name, dict):
			query = query_or_name
			selected_format = os.path.splitext(file)[1][1:].lower()
			if format is None or selected_format != format:
				query = query.copy()
				query['format'] = selected_format
			url = getReportUrl(form, query)
		else:
			# DEPRECATED CASE
			url = getReportUrl(
				form, 
				query_or_name,

				format     = format or os.path.splitext(file)[1][1:],
				parameters = parameters,
				connection = connection,
				accessobject_id = accessobject_id,
				locale     = locale,
			)
				
		form.downloadFile(url, file)

		on_success(file)

	form.selectFiles(
		u_(u"Выберите файл чтобы сохранить отчет..."),
		'',
		filename or (query_or_name if isinstance(query_or_name, basestring) else None),	# or ... is deprecated case
		patterns,
		'save',
		resultConsumer = onSelectFiles,
		name = selectfiles_name,
	)




def runReport(
		form,
		query_or_name,
	
		parameters = None,		# deprecated
		title      = None,		
		connection = None,		# deprecated
		accessobject_id = None,	# deprecated
		locale     = None,		# deprecated
	):

	form.get_global('mdi_parent', form).run_form('common/ReportViewer.gfd', {
		'p_name'       : query_or_name,
		'p_parameters' : parameters,
		'p_title'      : title or (query_or_name if isinstance(query_or_name, basestring) else None),	# or ... is deprecated case
		'p_connection' : connection,
		'p_accessobject_id' : accessobject_id,
		'p_locale'     : locale,
	})
