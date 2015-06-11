from harmonylib.webkit.HttpProxyServlet import HttpProxyServlet

DEBUG = 1

class publicfiles(HttpProxyServlet):

	def getTargetUrl(self):
		return self.getContext().getConfig('servers.conf').get('files', 'publicfiles')

	def isLoginNotRequired(self):
		return DEBUG
