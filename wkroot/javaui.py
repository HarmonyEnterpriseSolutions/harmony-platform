# -*- coding: Cp1251 -*-
from wmlib.webkit.BaseServlet  import BaseServlet

class javaui(BaseServlet):

	def isLoginNotRequired(self):
		return True

	def respondToGet(self, trans):
		trans.response().write("""\
<HTML>
<BODY>
	<h1>��������� ������ WWM �������� �� ������ ������<h2>
	<p>
		���������� �����:
		<ul>
			<li><a href="https://b2b1.wwm.com.ua/">https://b2b1.wwm.com.ua/</a></li>
			<li><a href="https://b2b.wwm.com.ua/">https://b2b.wwm.com.ua/</a></li>
		</ul>
	</p>
</BODY>
</HTML>
""")
