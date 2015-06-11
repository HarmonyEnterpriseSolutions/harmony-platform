# -*- coding: Cp1251 -*-
from harmonylib.webkit.BaseServlet  import BaseServlet

class javaui(BaseServlet):

	def isLoginNotRequired(self):
		return True

	def respondToGet(self, trans):
		trans.response().write("""\
<HTML>
<BODY>
	<h1>Дилерский портал HARMONY переехал на другой сервер<h2>
	<p>
		Попробуйте здесь:
		<ul>
			<li><a href="https://b2b1.harmony.com.ua/">https://b2b1.harmony.com.ua/</a></li>
			<li><a href="https://b2b.harmony.com.ua/">https://b2b.harmony.com.ua/</a></li>
		</ul>
	</p>
</BODY>
</HTML>
""")
