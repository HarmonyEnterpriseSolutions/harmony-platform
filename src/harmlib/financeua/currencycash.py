# -*- coding: Cp1251 -*-

import urllib2
from lxml import etree
import decimal
import datetime


DEFAULT_URL = 'http://resources.finance.ua/ua/public/currency-cash.xml'
ZERO = decimal.Decimal(0)
DEFAULT_TZ_DELTA = datetime.timedelta(hours=2)
DEFAULT_CITY = u'Київ'

def round(d, count):

	i = 0

	d2 = d

	while d2 < 1:
		d2 *= 10
		i += 1

	return d.quantize(decimal.Decimal('1.' + '0' * (count + i - 1)))


class CurrencyCash(object):

	def __init__(self, url=DEFAULT_URL, tz_delta=None):
		self._url = url
		self._tz_delta = tz_delta or DEFAULT_TZ_DELTA


	def parse_date(self, d):
		"""
		2012-06-14T12:10:00+03:00
		+03:00 is a finance.ua bug
		"""
		d, tz = d.split('+')
		#h, m = tz.split(':')
		return datetime.datetime.strptime(d, '%Y-%m-%dT%H:%M:%S') #- datetime.timedelta(hours=int(h), minutes=int(m)) + self._tz_delta


	def getRates(self, currencies=(), city=DEFAULT_CITY):
		"""
		return {
			'USD' : {
				'avg' : ...
			}
			'GBP' : {
				'avg' : ...
			}
		}
		"""

		f = urllib2.urlopen(self._url)
		#f = open('currency-cash.xml', 'rb')
		tree = etree.parse(f)

		city_id = tree.xpath(u"//cities/city[@title='%s']" % city)[0].attrib['id']

		sums_avg = {}
		counts = {}

		for c in tree.xpath("//organization/city[@id='%s']/..//c" % city_id):
			currency = c.attrib['id']
			if currency in currencies:
				avg = (decimal.Decimal(c.attrib['ar']) + decimal.Decimal(c.attrib['br'])) / 2

				sums_avg[currency] = sums_avg.get(currency, ZERO) + avg
				counts[currency] = counts.get(currency, 0) + 1

		rates = {}

		for currency in counts.keys():
			rates[currency] = { 
				'avg' : sums_avg[currency] / counts[currency],
			}

		return self.parse_date(tree.xpath("/source")[0].attrib['date']), rates


	@classmethod
	def calcRatesTo(self, rates, currency_to, key='avg'):
		
		print rates

		rates = dict(rates)
		rates['UAH'] = { 'avg' : decimal.Decimal(1) }

		usd = rates[currency_to]['avg']

		res = {}

		for currency, conf in rates.iteritems():
			if currency != currency_to:
				res[currency] = usd / conf[key]

		return res		


if __name__ == '__main__':

	print CurrencyCash().getRates()#['rates']['USD']
