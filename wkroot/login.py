from wmlib.webkit.BaseServlet import BaseServlet
from WebKit.HTTPServlet	import HTTPServlet
from toolib._ import *

class login(BaseServlet):

	def isLoginNotRequired(self):
		return True

	def respondToPost(self, trans):
		userId, sessionKey, sid = self.getContext().login(
			self.request().field('application'           ), 
			self.request().field('user_login',    'guest'), 
			self.request().field('user_password', ''     ),
		)
		if userId is not None:
			self.write(repr((userId, sessionKey, sid)))
		else:
			trans.response().setHeader('Status', "401 Unauthorized")
