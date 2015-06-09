from hashlib import md5
import urllib
import urllib2
from urlparse import urlparse, urlunparse
import socket

def login(server_url, application, login, user_password):
	"""
	returns	tuple: (user id, session key)
	"""

	response = urllib2.urlopen(server_url + '/login', urllib.urlencode({
		'application'   : application.encode('UTF8'),
		'user_login'    : login.encode('UTF8'),
		'user_password' : encodePassword(user_password),
	}))

	return eval(response.read(), {})

	# this works with httplib
	#if response.code == 200:
	#	return eval(response.read(), {})
	#elif response.code == 403:
	#	raise SecurityError
	#else:
	#	raise IOError, '%s %s' % (response.code, response.msg)


def encodePassword(password):
	md = md5()
	md.update((password or u'').encode('UTF8'))
	return md.hexdigest()
	
if __name__ == '__main__':
	print login('http://localhost:82/harm/wk.cgi/harm', 'harm', 'admin', '111')
