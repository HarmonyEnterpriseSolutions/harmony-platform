from harmonylib.webkit.BaseServlet import BaseServlet

class fn_signatures(BaseServlet):

	def respondToGet(self, trans):
		trans.response().setHeader("content-type", "text/plain")
		# unix server reads this config with \r\n
		# and client exec have SyntaxError on \r character
		# reading binary and replacing
		trans.response().write(file(self.getContext().filePath('etc', 'fn_signatures.conf.py', exact=True), 'rb').read().replace('\r\n', '\n'))
