import simplejson
import base64
import zlib

from harmlib.webkit.HttpProxyServlet import HttpProxyServlet

DEBUG = 0

class report(HttpProxyServlet):

	def __init__(self):
		super(report, self).__init__(timeout=8*60*60)

	def getTargetUrl(self):
		return self.getContext().getConfig('servers.conf').get('reports', 'report_server') + "/report"

	def isLoginNotRequired(self):
		return DEBUG

	def respondToAny(self, trans):
		try:
			zq = base64.decodestring(trans.request().fields()['zq'])
		except KeyError:
			jq = trans.request().fields()['q']
		else:
			jq = zlib.decompress(zq)
		
		query = simplejson.loads(jq)

		for rep in query['reports']:
			aoid = rep.get('aoid')
			if aoid is not None:
				ao = self.getContext().getAccessObject(aoid)
				if ao is None or not bool(ao.access & ao.ACCESS_PRINT):
					#trans.response().setHeader('Status', "403 %s" % _('You have no permission to generate this report'))	# at list one of reports
					trans.response().setHeader('Status', "403 Access Denied")	# at list one of reports
					return

		super(report, self).respondToAny(trans)

		self.getContext().logEvent('GET_REPORT', note = str(query))

		#raw = trans.request().rawInput(True)
		#if raw:
		#	data = raw.read()
		#else:
		#	data = urllib.urlencode(trans.request().fields())

