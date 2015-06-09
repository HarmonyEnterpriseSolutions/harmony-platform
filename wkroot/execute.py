import os
import urllib
import urllib2
import thread


if __name__ == '__main__':
	URL = 'http://localhost:82/wm/wk.cgi/wm/execute'
	FIELDS = {
		'command' : 'wmsite3_sync_price',
	}

	response = urllib2.urlopen(URL, urllib.urlencode(FIELDS))

	print response.code, response.msg
	print response.headers
	print response.read()
	import sys
	sys.exit(0)


from toolib._ import *
from wmlib.webkit.BaseServlet import BaseServlet


class execute(BaseServlet):
	"""
	executes scripts
	"""

	def isLoginNotRequired(self):
		return False

	def respondToPost(self, trans):
		"""
		accept file sent as application/octet-stream, 
		save it to unique place, 
		return user unique file name in response
		"""
		section = trans.request().fields()['command']
		email = trans.request().fields().get('email', '')

		command = self.getContext().getConfig('execute.conf').get(section, 'command')
		command = command.replace('{{ email }}', email)

		print '>>> command =', repr(command)

		thread.start_new_thread(os.system, (command,))
				
		trans.response().setHeader("content-type", 'text/plain')
		trans.response().write('started')
