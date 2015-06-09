from WebKit.HTTPServlet	import HTTPServlet
from toolib.web.kit.TransactionInfo  import XTransactionInfo
from toolib.web.kit.XTransaction import XTransaction
from toolib.utils import strdict

try: _ 
except: _ = lambda x: x


class info(XTransaction, XTransactionInfo, HTTPServlet):

	def respondToGet(self, trans):

		app = trans.application()

		requestStuff = {}

		for i in [
			'extraURLPath',
			'siteRootFromCurrentServlet',
			'isSecure',
			'isSessionExpired',
			'remoteUser',
			'remoteAddress',
			'remoteName',
			'urlPath',
			'urlPathDir',
			'serverSidePath',
			'serverSideContextPath',
			'contextName',
			'servletURI',
			'uriWebKitRoot',
			'fsPath',
			'serverURL',
			'serverURLDir',
			'serverPath',
			'serverPathDir',
			'siteRoot',
			'siteRootFromCurrentServlet',
			'servletPathFromSiteRoot',
			'adapterName',
			'adapterFileName',
			'servletPath',
			'contextPath',
			'pathInfo',
			'pathTranslated',
			'queryString',
			'uri',
			'method',
			'sessionId',
			]:
			try:
				requestStuff[i] = getattr(self.request(), i)()
			except Exception, e:
				requestStuff[i] = "%s: %s" % (e.__class__.__name__, e)

		self.write('<br><b>Request stuff:</b><br><pre>%s</pre>' % strdict(requestStuff))

		self.write('<br><b>Info:</b><br><pre>%s</pre>' % strdict(self.info().asDict()))

		self.write('<b>Sessions:</b><pre>%s</pre>' % ('\n'.join(app.sessions().keys()),))

		self.write('<br><b>Environment:</b><br><pre>%s</pre>' % strdict(self.request().environ()))
