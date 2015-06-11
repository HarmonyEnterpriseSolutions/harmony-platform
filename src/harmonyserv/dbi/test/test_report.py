#-*- coding: cp1251 -*-
import urllib2
import os
from cookielib import CookieJar

import simplejson as json

from src.harmonyserv.dbi.test.test import TestClient


URL = 'http://192.168.1.2:8000/dbi/'

QUERY = {
	#'locale': 'ru_RU', 
	'application': 'dp2', 
	'format': 'pdf',
	'reports': [
		{
			'name': 'rep_dp_org_balance', 
			'parameters': {
				's_date': '2013-12-01', 
				'e_date': '2013-12-31', 
				'org_id': 10853, 
				'is_f1': False, 
				'is_f2': True,
			}
		}
	], 
}

QUERY = {
	'application': 'dp2', 
	'format': 'pdf',
	'reports': [
		{
			'name': 'dp_erp_doc_generic', 
			'parameters': {
				'doc_id': 54970, 
				'doc_type_report_key': 'REP_DT_SALES_AGREE',
			}
		}
	], 
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

		if text.startswith('%PDF'):
			f = open('test-report.pdf', 'wb')
			f.write(text)
			f.close()
			print "OK"

			os.system('test-report.pdf')

		else:
			print text
		
