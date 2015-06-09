# -*- coding: Cp1251 -*-
from wmlib.webkit.BaseServlet  import BaseServlet

class javaui(BaseServlet):

	def isLoginNotRequired(self):
		return True

	def respondToGet(self, trans):
		trans.response().write("""\
<HTML>
<BODY>
	<h1>Дилерский портал WWM переехал на другой сервер<h2>
	<p>
		Попробуйте здесь:
		<ul>
			<li><a href="https://b2b1.wwm.com.ua/">https://b2b1.wwm.com.ua/</a></li>
			<li><a href="https://b2b.wwm.com.ua/">https://b2b.wwm.com.ua/</a></li>
		</ul>
	</p>
</BODY>
</HTML>
""")
