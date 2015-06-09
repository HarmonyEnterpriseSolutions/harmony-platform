# Create your views here.
import datetime
import sys
import traceback
import urllib
import urllib2

import simplejson as json
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse

from toolib.web.cookies import CookieJar
from toolib.web.djangoutils.jsonrpc import JSONRPCService, jsonremote, RPCServiceError, Transaction
from toolib.text.json.json_coerce import json_coerce
import config
from UserSession import UserSession
from src.harmserv.dbi import fetch_metadata


jsonservice = JSONRPCService()
forms = None
time = None

class PermissionDeniedError(RPCServiceError):
	pass

def service(request):
	if request.method == 'POST':
		return jsonservice(request)
	elif request.method == 'GET':
		global forms, time
		
		if 'refresh' in request.GET:
			forms = None
			return HttpResponseRedirect(reverse('service'))
	
		if forms is None:
			forms = fetch_metadata.Fetcher(config.APPLICATION).fetchFormsMetadata(config.FORMS)
			time = datetime.datetime.now()
		
		return HttpResponse(loader.get_template('dbi/forms.html').render(RequestContext(request, { 
			'forms' : forms,
			'time' : time,
			'application' : config.APPLICATION,
		})))
	else:
		raise Http404()

@jsonremote(jsonservice)
def call(transaction, application, connection, function, parameters):
	session = get_session(transaction.request)
	try:
		result = session.call(application, connection, function, parameters)
		if result:
			return json_coerce(result)
		else:
			raise PermissionDeniedError
	finally:
		session.close()

@jsonremote(jsonservice)
def login(transaction, application, user_login, user_password, set_user_position=False):
	transaction.request.session['dbi_session'] = None
	session = get_session(transaction.request)
	try:
		user_id, session_id = session.login(transaction.request, application, user_login, user_password, set_user_position)
		return {
			'user_id'    : user_id,
			'session_id' : session_id,
		}
	finally:
		session.close()


def execute(request):
	"""
	POST DATA is json
	{
		'application' : 'harm',
		'connection' : 'db',
		'function' : 'harmsite_attribute',
		'parameters' : {
		}
	}

	result is multiple lines of json
	first line is always list of column descriptions, json encoded

	[{ 'name' : 'id' }, { 'name' : 'column1' }, { 'name' : 'column2' }]

	then lines with json encoded rows

	[1, 'column1 row0 value', 'column2 row0 value']
	[2, 'column1 row1 value', 'column2 row1 value']
	[3, 'column1 row2 value', 'column2 row2 value']
	...
	[N, 'column1 rowN value', 'column2 rowN value']

	in case of error returns json

	{'error' : '...'}


	"""
	parameters = json.loads(get_request_body(request))

	session = get_session(request)
	try:
		try:

			rs = session.open_resultset(
				parameters['application'], 
				parameters['connection'], 
				parameters['function'], 
				parameters['parameters'],
			)

			if not rs:
				raise PermissionDeniedError
		except RPCServiceError, e:
			return HttpResponse(json.dumps({'error' : u'%s: %s' % (e.__class__.__name__, e.message)}))
		except:
			return HttpResponse(json.dumps({'error' : ''.join(traceback.format_exception(*sys.exc_info()))}))
		else:		
			def generate_response():

				yield json.dumps([{'name' : i} for i in rs.columns])
				yield '\n'

				for row in rs:
					yield json.dumps(json_coerce(row))
					yield '\n'
			
			return HttpResponseWithAfter(generate_response(), after_response = lambda: get_session(request).close())
	except:
		# of no exception, HttpResponseWithAfter will close session
		session.close()
		raise
		
def test_streamed_response(request):

	def generate_response():
		#rint ">> generate"
		for i in xrange(10):
			#rint ">> step", i
			yield '%s<br>%s\n' % (i+1, ' ' * 100000)
			import time
			time.sleep(1)			
			
	#rint ">> return"
	return HttpResponse(content=generate_response())


def get_session(request):
	session = request.session.get('dbi_session')
	if session is None:
		session = request.session['dbi_session'] = UserSession()
	return session

def str_keys(d):
	return dict([(str(k), v) for k, v in d.iteritems()])



def report(request):

	session = get_session(request)
	try:

		if request.method == 'GET':
			q = json.loads(request.GET['q'])
		elif request.method == 'POST':
			q = json.loads(get_request_body(request))
		else:
			raise Http404()

		if q['application'] not in config.ALLOWED_APPLICATIONS:
			return HttpResponse(status = 403)
	
		for report in q.get('reports', ()):
			if 'parameters' not in report: report['parameters'] = {}

			# allways try to pass session_key and org_staff_contact_id
			report['parameters']['session_key']          = session.session_key
			report['parameters']['org_staff_contact_id'] = session.org_staff_contact_id
		
		# get reports server url for application
		report_server = session.getConfig('servers.conf').get('reports', 'report_server')
		servlet = report_server + ('report' if report_server.endswith('/') else '/report')

		cookie_jar = request.session.get('report_cookie_jar')
		if cookie_jar is None:
			request.session['report_cookie_jar'] = cookie_jar = CookieJar()

		# force cookie jar to save
		request.session.modified = True

		# post q parameter
		res = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar)).open(servlet, urllib.urlencode({'q' : json.dumps(q)}))

		data = res.read()
		
		headers = res.info()

		response = None

		if headers.get('Content-Type') == 'text/html':
			try:
				# detect error	
				tb_begin = '<!--[DETAIL[-->'
				tb_end = '<!--]]-->'
				p1 = data.index(tb_begin) + len(tb_begin)
				p2 = data.index(tb_end)
			except ValueError:
				pass
			else:
				# cut traceback from html
				data = data[p1:p2]

				response = HttpResponse(status = 500)
				response['Content-Type']  = 'text/plain'

		if response is None:
			response = HttpResponse(status = res.code)
		
			# copy some headers if any
			for i in ('Content-Type', 'Content-Disposition'):
				if i in headers:
					response[i] = headers[i]

		response.write(data)

		return response

	finally:
		session.close()

#############################
# STUFF for ext client
#

def raw_service(request, method, application, connection, function):
	"""
	alternative of json-rpc, made exclusively for Andrey
	POST data is json with parameters
	response is like json-rpc
	"""
	transaction = Transaction(request, HttpResponse())	
	params = json.loads(get_request_body(request))
	params = str_keys(params)
	method = jsonservice.method_map[method]
	try:
		rc = method(transaction, application, connection, function, **params)
	except:
		#transaction.response = HttpResponse(status_code = 500)
		transaction.response.status_code = 500
		rc = {'error' : ''.join(traceback.format_exception(*sys.exc_info()))}

	transaction.response.write(json.dumps(rc))
	return transaction.response

@jsonremote(jsonservice)
def extjs_call(transaction, application, connection, function, parameters, **ignore):
	session = get_session(transaction.request)
	if function == 'set_user_position':
		session.set_user_position(parameters['org_staff_contact_id'])
		transaction.request.session.modified = True
		return []
	else:
		result = session.call(application, connection, function, parameters, rowType=dict)
		if result:
			if isinstance(result, dict):
				return json_coerce(result['data'])
			else:
				return [json_coerce(i['data']) for i in result]
		else:
			raise PermissionDeniedError

@jsonremote(jsonservice)
def extjs_get_tree(transaction, application, connection, function, parameters, tree_parameters, **ignore):
    
	if not isinstance(parameters, dict):
		raise TypeError, 'extjs_get_tree parameters must be dict'
	
	fld_id       = tree_parameters['fld_id']
	fld_parent   = tree_parameters['fld_parent']
	fld_text     = tree_parameters['fld_text']
	check        = tree_parameters.get('checked')
	rootid       = tree_parameters.get('rootid', 0)
	extra_fields = tree_parameters.get('extra_fields')

	session = get_session(transaction.request)
	result = session.call(application, connection, function, parameters, rowType=dict)

	if not result:
		raise PermissionDeniedError

	rows_by_parent_id = {}
	for row in result['data']:
		rows_by_parent_id.setdefault(row[fld_parent], []).append(row)

	def make_children(id, level=0):
		return [make_node(i, level) for i in list(rows_by_parent_id.get(id, ()))]

	def make_node(row, level):
		node = {
			'id'       : row[fld_id],
			'text'     : row[fld_text],
		}
		
		if check is not None:
			node['checked'] = check

		children = make_children(row[fld_id], level+1)
		if children:
			node['children'] = children
			node['cls'] = 'folder'
			node['expanded'] = level == 0  # expand only first level
		else:
			node['leaf'] = True

		if extra_fields:
			node['extra_fields'] = dict([(f, row[f]) for f in extra_fields])
		
		return node
		
	return make_children(rootid)


class HttpResponseWithAfter(HttpResponse):

	def __init__(self, *args, **kwargs):
		self.__after_response = kwargs.pop('after_response')
		super(HttpResponseWithAfter, self).__init__(*args, **kwargs)
	
	def close(self):
		super(HttpResponseWithAfter, self).close()
		if self.__after_response:
			self.__after_response()
		self.__after_response = None
	

def get_request_body(request):
	try:
		return request.body
	except AttributeError:
		# django 1.3 support
		return request.raw_post_data
