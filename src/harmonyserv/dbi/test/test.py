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


	def raw_execute(self, method, application, connection, table, **parameters):

		body = simplejson.dumps(parameters)

		headers = {
			'Content-Type'   : 'application/json',
			'Content-Length' : len(body),
		}

		url = "%s%s/%s/%s/%s/" % (self._url, method, application, connection, table)

		print "----------------------------------"
		print ">>> HTTP POST", url
		print "----------------------------------"
		for k, v in headers.items():
			print "%s: %s" % (k, v)
		print 
		print
		print body
		print "----------------------------------"

		try:
			response = urlopen(Request(url, body, headers))
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
		if code == 500:
			print simplejson.loads(result_data)['error']
		print "----------------------------------"

		return simplejson.loads(result_data)

	def login(self, application='dp2', username='alibaba1', password='alibaba1', connection='db'):
		user_id = self.execute('login', application, username, encodePassword(password))['user_id']

		positions = self.raw_execute('extjs_call', application, connection, 'get_user_position', parameters={'user_id' : user_id})
		if not positions:
			raise RuntimeError, 'user has no positions'
		else:
			print "user has %s positions" % len(positions)
		
		position = positions[0]
		print 'selected position: %(org_name)s, %(org_staff_name)s, %(contact_name)s' % position

		self.raw_execute('extjs_call', application, connection, 'set_user_position', parameters={'org_staff_contact_id' : position['org_staff_contact_id']})
		
	

def dump_extjs_tree(tree, inset=0):
	for node in tree:
		print '\t' * inset, node['id'], node['text'], '[EXPANDED=%s]' % node.get('expanded'), 'extra_fields =', node.get('extra_fields')
		if 'children' in node:
			dump_extjs_tree(node['children'], inset+1)



def test(url):
	urllib2.install_opener(urllib2.build_opener(
		urllib2.HTTPCookieProcessor(CookieJar()),
		urllib2.ProxyHandler({
			"http" : "http://gleb.mironov:123@proxy.local.harmony.com.ua:3128",
		}),
	))

	client = TestClient(url)
	client.login()

	if 0:
		for row in client.raw_execute('extjs_call', 'dp2', 'db', 'dp_test_user_position', parameters={}):
			print row

	if 0:
		print "############ test exception #############"
		print client.raw_execute('extjs_call', 'dp2', 'db', 'dp_test_exception', parameters={'s' : u'такая'})['error']

	if 0:
		for row in client.raw_execute('extjs_call', 'dp2', 'db', 'dp_doc_sales_pre', parameters={'s_date': '2000-01-01', 'e_date' : '2015-01-01', 'org_id' : 20413}):
			print row

	if 0:
		# test batch dell
		for rs in client.raw_execute('extjs_call', 'dp2', 'db', 'dp_doc_pos_del', parameters=[{'doc_pos_id': 0},{'doc_pos_id': -1},{'doc_pos_id': -2}]):
			for row in rs:
				print row

	if 0:
		for row in client.raw_execute('extjs_call', 'dp2', 'db', 'dp_doc_agreement_sales', parameters={'org_id' : 20413}):
			print row

	if 0:
		for row in client.raw_execute('extjs_call', 'dp2', 'db', 'spr_ei', parameters={}):
			print row

	
	if 0:
		print "############ test tree #############"
		dump_extjs_tree(client.raw_execute('extjs_get_tree', 'dp2', 'db', 'spr_prod_ctg', parameters={'org_id_my' : 3}, tree_parameters={
			'fld_id'     : 'prod_ctg_id',
			'fld_parent' : 'prod_ctg_parent_id',
			'fld_text'   : 'prod_ctg_name',
			'extra_fields' : ['prod_ctg_id'],
			'checked'    : True,
		}))

	if 0:
		for row in client.execute('extjs_call', 'dp', 'db', 'spr_ei', {}):
			print row

	if 0:
		dump_extjs_tree(client.execute('extjs_get_tree', 'dp', 'db', 'spr_prod_ctg', {'org_id_my' : 3}, {
			'fld_id'     : 'prod_ctg_id',
			'fld_parent' : 'prod_ctg_parent_id',
			'fld_text'   : 'prod_ctg_name',
			'checked'    : True,
		}))

	
	if 0:
		print client.execute('extjs_call', 'dp', 'sales', 'sp_DP_status_price_prod_list', {})
	
	if 0:
		print client.execute('extjs_call', 'dp', 'sales', 'sp_DP_status_price_prod_list', {})
	
	if 0:
		print client.execute('call', 'dp', 'sales', 'sp_DP_test_ins', {
			'test_text' : u'запись dbi', 
			'test_int' : 123, 
			'test_datetime' : '20001122 15:55:59',
			'test_float' : '1.2345', 
			'test_decimal' : '1.2345',
		})

	if 0:
		print client.execute('call', 'dp', 'sales', 'sp_DP_test_list', {})


	if 0:
		client.raw_execute('extjs_call', 'dp2', 'db', 'dp_doc_sales_edit', parameters = {
			"doc_id":54976,
			"doc_note":"111",
		})


if __name__ == '__main__':
	import sys
	reload(sys)
	sys.setdefaultencoding('Cp1251')
	try:
		test(URL)
	except RuntimeError, e:
		print unicode(e)
