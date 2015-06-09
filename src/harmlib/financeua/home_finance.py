import simplejson
import urllib
import urllib2
import datetime

"""
client for home finance on finance.ua
unused since it is payed service
"""

DEFAULT_URL = 'http://home.finance.ua/services/index.php'


class RemoteException(Exception):
	pass


class HomeFinanceUaClient(object):

	def __init__(self, url=DEFAULT_URL):
		self._url = url
		self._current_id = 0

	def get_params(self, params):
		return [params]


	def call(self, service, method, **params):

		self._current_id += 1
		data = simplejson.dumps({
			'id' : self._current_id,
			'service' : service,
			'method' : method,
			'params' : self.get_params(params),
		})

		print data

		headers = {
			'Content-Type' : 'application/json',
		}

		response = urllib2.urlopen(urllib2.Request(self._url, data, headers))

		print response.code, response.msg
		print response.headers

		result = simplejson.loads(response.read())

		if 'error' in result:
			raise RemoteException, "[%(code)s] %(message)s" % result['error']

		else:
			return result['result']


	def login(self, email, password):

		self.call()



class HomeFinanceUaConnection(HomeFinanceUaClient):
	def __init__(self, url, context):
		super(HomeFinanceUaConnection, self).__init__(url)
		self._context = context
		self._role = self._context.pop('role')
		
	def get_params(self, params):
		return [self._context, params]
          

if __name__ == '__main__':
	client = HomeFinanceUaClient()
	#print client.call('sauth', 'auth', email='nogus@mail.ru', password='noguss')

	connection = HomeFinanceUaConnection(DEFAULT_URL, {
		'idUser': 38262, 
		'idAccount': 38262,
		'token': '4a3248aefdfa531d27dcf0aefa73d6b8', 
		'role': 1, 
	})


	print connection.call('soperations', 'read', fromdate = '2012-06-13', todate = '2012-06-13', today = '2012-06-13')
