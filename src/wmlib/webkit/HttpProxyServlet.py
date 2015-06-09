from toolib.web.kit.MHttpProxyServlet import MHttpProxyServlet
from wmlib.webkit.BaseServlet import BaseServlet

class HttpProxyServlet(MHttpProxyServlet, BaseServlet):

	def __init__(self, *args, **kwargs):
		timeout = kwargs.pop('timeout', None)
		BaseServlet.__init__(self, *args, **kwargs)
		MHttpProxyServlet.__init__(self, timeout=timeout)

	def createAdditionalUrlHandlers(self, trans):
		handlers = super(HttpProxyServlet, self).createAdditionalUrlHandlers(trans)

		config = self.getContext().getConfig('urllib2.conf.py')	

		if 'PROXY_HANDLER' in config:
			handlers += (config['PROXY_HANDLER'],)

		return handlers
