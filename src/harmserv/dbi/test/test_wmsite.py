#-*- coding: cp1251 -*-
URL = 'http://192.168.1.2:8000/dbi/'

import os
import simplejson
import sys
import urllib2
from cookielib import CookieJar
from hashlib import md5
from urllib2 import urlopen, HTTPError, Request, quote


def encodePassword(password):
	md = md5()
	md.update((password or u'').encode('UTF8'))
	return md.hexdigest()


class TestClient(object):

	def __init__(self, url):
		self._url = url


	def execute(self, method, *parameters):

		body = simplejson.dumps({
			"version" : "1.1",
			"method" : method,
			"params": parameters,
			"id" : 0,
		})

		headers = {
			'Content-Type'   : 'application/json',
			'Content-Length' : str(len(body)),
		}

		print "----------------------------------"
		print ">>> HTTP POST", self._url
		print "----------------------------------"
		for k, v in headers.items():
			print "%s: %s" % (k, v)
		print 
		print
		print body
		print "----------------------------------"

		try:
			response = urlopen(Request(self._url, body, headers))
		except HTTPError, e:
			result_data = e.read()
			code = e.code		
		else:			
			result_data = response.read()
			code = response.code
		
		print '>>> RESPONSE', code
		print "----------------------------------"
		print result_data
		print "----------------------------------"

		result = simplejson.loads(result_data)
		if 'error' in result:
			raise RuntimeError(result['error'])
		else:
			return result['result']


	def login(self, application='harmsite', username='admin', password='111', connection='db'):
		user_id = self.execute('login', application, username, encodePassword(password))['user_id']

		positions = self.execute('extjs_call', application, connection, 'get_user_position', {'user_id' : user_id})
		if not positions:
			raise RuntimeError, 'user has no positions'
		else:
			print "user has %s positions" % len(positions)
		
		position = positions[0]
		print 'selected position: %(org_name)s, %(org_staff_name)s, %(contact_name)s' % position

		self.execute('extjs_call', application, connection, 'set_user_position', {'org_staff_contact_id' : position['org_staff_contact_id']})
		
	

def test(url):
	urllib2.install_opener(urllib2.build_opener(
		urllib2.HTTPCookieProcessor(CookieJar()),
		urllib2.ProxyHandler({
			"http" : "http://gleb.mironov:123@proxy.local.harm.com.ua:3128",
		}),
	))

	client = TestClient(url)
	client.login()

	print client.execute('call', 'harmsite', 'db', 'ishop_get_contact_price', { 'domain' : 'shop.harm.ua' })



if __name__ == '__main__':
	import sys
	reload(sys)
	sys.setdefaultencoding('Cp1251')
	try:
		test(URL)
	except RuntimeError, e:
		print unicode(e)
