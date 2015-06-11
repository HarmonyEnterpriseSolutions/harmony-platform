# -*- coding: Cp1251 -*-
from harmonylib.webkit.BaseServlet  import BaseServlet

class javauiws(BaseServlet):

	def isLoginNotRequired(self):
		return True

	def respondToGet(self, trans):
		self.response().sendRedirect(self.info().getAppContextUri() + '/javaui/')
