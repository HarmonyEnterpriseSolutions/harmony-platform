#-*- coding: cp1251 -*-
import urllib2
from cookielib import CookieJar

import simplejson as json

from src.harmonyserv.dbi.test.test import TestClient


URL = 'http://192.168.1.2:8888/dbi/'
#  Parameter: org_id of class class java.lang.Integer = 12937
#  Parameter: doc_agreement_id of class class java.lang.Integer = null

QUERY = {
	'application' : 'dp2', 
	'format'      : 'xls',
	'zip'         : True,
	'reports'     : [
		{
			'name' : 'rep_org_agreement_price',
			'connection' : 'db',
			'parameters' : {
				'org_id': 12937, 
				#'doc_agreement_id': None, 
			},
		},
	],
	'filter' : 'group_xls.py --base_data_row=2 --group_base=1 - -',
}


if __name__ == '__main__':
	
	urllib2.install_opener(urllib2.build_opener(
		urllib2.HTTPCookieProcessor(CookieJar()),
		urllib2.ProxyHandler({
			"http" : "http://gleb.mironov:123@proxy.local.harmony.com.ua:3128",
		}),
	))

	client = TestClient(URL)
	client.login()

	try:
		#response = urllib2.urlopen(URL + 'report/', json.dumps(QUERY))
		url = URL + 'report/?q=' + urllib2.quote(json.dumps(QUERY))
		print 'GET', url
		response = urllib2.urlopen(url)
	except urllib2.HTTPError, e:
		print "ERROR: HTTP", e.code
		print e.read()
	else:
		text = response.read()

		f = open('test-report.xls.zip', 'wb')
		f.write(text)
		f.close()
		print "OK"

		#os.system('test-report.xls')
