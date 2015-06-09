# -*- coding: Cp1251 -*-
from wmlib.webkit.BaseServlet  import BaseServlet

class javaui(BaseServlet):

	def isLoginNotRequired(self):
		return True

	def respondToGet(self, trans):
		trans.response().write("""\
<HTML>
<BODY>
	<h1>Дилерский портал HARM переехал на другой сервер<h2>
	<p>
		Попробуйте здесь:
		<ul>
			<li><a href="https://b2b1.harm.com.ua/">https://b2b1.harm.com.ua/</a></li>
			<li><a href="https://b2b.harm.com.ua/">https://b2b.harm.com.ua/</a></li>
		</ul>
	</p>
</BODY>
</HTML>
""")
