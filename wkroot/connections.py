from harmonylib.webkit.BaseServlet import BaseServlet

class connections(BaseServlet):

	def respondToGet(self, trans):
		trans.response().setHeader("content-type", "text/plain")
		trans.response().write(open(self.getContext().filePath('etc', 'connections.conf', exact=True), 'rt').read())
