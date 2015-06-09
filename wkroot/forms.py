import os
import re
from harmlib.webkit.BaseServlet  import BaseServlet
from harmlib.webkit.FormDom      import FormDom
from harmlib.webkit.AccessObject import AccessObject
from toolib import debug

REC_LIBRARY  = re.compile(r"library\s*\=\s*'([^']*)'")

DEBUG = 0
MAGIC_ACCESSOBJECT = 'accessobject/'
REC_ACCESSOBJECT = re.compile(r'\[(\d+)\]')

class forms(BaseServlet):

	def isLoginNotRequired(self):
		"""
		allow to see login form
		"""
		form = self.request().extraURLPath()
		return form.startswith('/login') or form in ('/applications.gfd',) or form.startswith('/test/') or DEBUG

	def respondToGet(self, trans):
		trans.response().setHeader("content-type", 'text/xml')
		try:
			fname = self.request().extraURLPath().replace('/__/', '/../').lstrip('/')
			
			s = REC_ACCESSOBJECT.split(fname, 1)
			if len(s) == 3:
				accessObjectId = int(s[1])
				fname = (s[0] + s[2]).strip('/')

				ao = self.getContext().getAccessObject(accessObjectId)

				access = ao.access
				if access & ao.ACCESS_READ:
					fname = fname or ao.url
				else:
					fname = "common/noaccess.gfd"
				
				print "+ Applying access to %s, %s: %s" % (accessObjectId, fname, access)
			else:
				accessObjectId = None
				access = AccessObject.ACCESS_ALL

			if not self.isLoginNotRequired():
				self.getContext().logEvent(
					'GET_FORM', 
					access_object_id=accessObjectId,
					access=access,
					note = fname,
				)

			base, fname = os.path.split(self.getContext().filePath('forms', fname, exact=False))

			dom = FormDom(fname, get_form_path=lambda fname: os.path.join(base, fname))

			dom.applyAccess(access)

			if not self.getContext().isSuperuser():
				dom.applyFunctionAccess(self.getContext().getFunctionAccess(accessObjectId))

			dom.writexml(self.response())

		except IOError, e:
			debug.error("%s: %s" % (e.__class__.__name__, e))
			if "No such file or directory" in str(e):
				self.response().setHeader('Status', "404 Not Found")
			else:
				raise

