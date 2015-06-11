from src.harmonylib.webkit import BaseServlet


class Resource(BaseServlet):

	root        = ''
	content     = "text"
	contentType = "plain"

	def respondToGet(self, trans):

		trans.response().setHeader("content-type", '/'.join((self.content, self.contentType)))

		if self.content == 'text':
			mode = 'rt'
		else:
			mode = 'rb'

		try:
			#replace "__" in extra url path path to ".."
			self.writeResource(file(self.getFilePath(self.request().extraURLPath().replace('/__/', '/../').lstrip('/')), mode))
		except IOError, e:
			if "No such file or directory" in str(e):
				self.response().setHeader('Status', "404 Not Found")
			else:
				raise

	def getFilePath(self, extraUrlPath):
		return self.getContext().filePath(self.root, extraUrlPath, exact=False)

	def writeResource(self, f):
		self.write(f.read())

