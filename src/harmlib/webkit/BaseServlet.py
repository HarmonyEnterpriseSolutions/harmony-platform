from WebKit.HTTPServlet	import HTTPServlet
from toolib.web.kit.TransactionInfo	import XTransactionInfo
from toolib.web.kit.XTransaction	import XTransaction
from src.harmonylib.webkit import UserContext


class XBaseServlet(XTransaction, XTransactionInfo):

	def respond(self, trans):
		"""
		check if authorized
		"""
		self.getContext().setTransactionInfo(self.info())
		if self.getContext().userId is not None or self.isLoginNotRequired():
			super(XBaseServlet, self).respond(trans)
		else:
			self.respondForbidden()

	def respondForbidden(self):
		self.response().setHeader('Status', "403 Forbidden")
		self.write('<HTML><BODY><H1>Forbidden</H1></BODY></HTML>')

	def isLoginNotRequired(self):
		return False

	def getContext(self):
		uc = self.session().value('context', None)
		if uc is None:
			uc = self.session()['context'] = UserContext(self.session().identifier())
		return uc
		

class BaseServlet(XBaseServlet, HTTPServlet):
	pass

