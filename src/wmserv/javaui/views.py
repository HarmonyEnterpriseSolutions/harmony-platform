# Create your views here.
from urllib2 import urlopen, Request
import datetime

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import RequestContext, loader
from django.utils.translation import get_language
from django.contrib.sessions.models import Session
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from toolib.web.djangoutils.jsonrpc import JSONRPCService, jsonremote, RPCServiceError
from gnue.forms.uidrivers.java.GFClient import GFClient, InstanceNotFoundError
from gnue.forms.uidrivers._base.rpc.outconv import outconv
from gnue.forms.uidrivers.java.config import DEBUG
from src.wmserv.javaui.models import UserContext
from wmserv.clientproperty.models import Storage


javaui_service = JSONRPCService()


_clients = {}


class SessionNotFoundError(RPCServiceError):
	pass


@jsonremote(javaui_service)
def process(transaction, hiveId, calls):

	request = transaction.request
	response = transaction.response

	request.session.set_expiry(settings.SESSION_EXPIRY)

	alive_session_keys = set((row['session_key'] for row in Session.objects.filter(expire_date__gte=datetime.datetime.now()).values('session_key')))

	for key in _clients.keys():
		if key not in alive_session_keys:
			# TODO: maybe try to close forms?
			_clients[key].closeAllConnections()
			del _clients[key]

	#rint "PROCESS", calls

	sid = request.session.session_key

	try:
		client = _clients[sid]
	except KeyError:
		#rint ">>> CREATE CLIENT (%s)" % sid
		client = _clients[sid] = GFClient(
			settings.GNUE_SERVER_URL,
			debug = bool(DEBUG),
		)
	
	# used by uidriver to get user context to store gui state
	# TODO
	client.setGetUserContextBySid(lambda sid, user_id: UserContext(user_id))
	client.set_get_clientproperty_storage(lambda: Storage.objects.get_storage(request, response))

	try:
		rc = client.processCalls(hiveId, calls)
	except InstanceNotFoundError:
		raise SessionNotFoundError, unicode(_("""Sorry, Your session has not been found. Possible reasons:
			- session expired (session inactivity timeout is %.f minutes)
			- cookies is disabled on Yours web browser (appears when just typing login)
			- server restarted
		Application will be reset to login""" % (settings.SESSION_EXPIRY / 60.)))

	# to free request, response reference
	client.set_get_clientproperty_storage(None)

	return outconv(rc)


def index(request):
	return HttpResponse(loader.get_template('javaui/index.html').render(RequestContext(request, {})))


def applet(request):
	if request.method == 'POST':
		return javaui_service(request)

	elif request.method == 'GET':
		return HttpResponse(loader.get_template('javaui/applet.html').render(RequestContext(request, {
			'debug'    : int(DEBUG),
			'language' : get_language()[:2].lower(),
		})))
	else:
		raise Http404()


from gnue.forms.uidrivers._base.rpc.staticres import getStaticResourceFilePath


def staticres(request, path):
	response = HttpResponse(content_type='application/octet-stream')
	path = path.replace('/__/', '/../')
	path = getStaticResourceFilePath(path)
	response.write(open(path, 'rb').read())
	return response



BUF_SIZE = 0x10000
from src.wmserv.javaui.utils import is_hop_by_hop

def dynamicres(request):
	"""
	java gnue.forms.Desktop.wrapUrl redirects here

	used in PDFViewer and Frame.uiSaveUrl
	"""
	response = HttpResponse()

	if request.method == 'GET':

		# applet asks resource by url
		ins = urlopen(request.GET['URL'])


		for name, value in ins.headers.items():
			if name.lower() != 'set-cookie' and not is_hop_by_hop(name):
				response[name] = value

		while True:
			buf = ins.read(BUF_SIZE)
			if not buf:
				break
			response.write(buf)

	elif request.method == 'POST':
		
		url = request.POST['URL']

		ins = urlopen(Request(url, get_request_body(request), {
			'Content-Type'   : 'application/octet-stream',
			'Content-Length' : len(body),
		}))

		for name, value in ins.headers.items():
			if name.lower() != 'set-cookie' and not is_hop_by_hop(name):
				response[name] = value

		while True:
			buf = ins.read(BUF_SIZE)
			if not buf:
				break
			response.write(buf)
	else:
		raise Http404()

	return response


def webstart(request):
	url = request.build_absolute_uri()
	response = HttpResponse(loader.get_template('javaui/javaui.jnlp').render(RequestContext(request, {
		'codebase'            : request.build_absolute_uri(settings.STATIC_URL),
		'href'                : url,
		'gnue_forms_codebase' : url.rstrip('/').rsplit('/', 1)[0] + '/', # remove webstart/ at end
		'gnue_forms_debug'    : int(DEBUG),
	})), content_type='application/x-java-jnlp-file')
	response['Content-Disposition'] = 'inline; filename="javaui.jnlp"'
	return response


def test_cookies(request):
	request.session.set_test_cookie()	
	return HttpResponseRedirect('../test_cookies_result/')

def test_cookies_result(request):
	if request.session.test_cookie_worked():
		request.session.delete_test_cookie()
		return HttpResponse("Cookies OK")
	else:
		return HttpResponse("Cookies FAILED")		


def get_request_body(request):
	try:
		return request.body
	except AttributeError:
		# django 1.3 support
		return request.raw_post_data
