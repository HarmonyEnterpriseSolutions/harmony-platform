# Credits: SimpleHessianServer.py was inspired by and based on
# SimpleXMLRPCServer.py written by Brian Quinlan (brian@sweetapp.com)

import SocketServer
import BaseHTTPServer
import sys
import os

from src.gnue.common.rpc.drivers.hessian.hessianlib import Fault
from src.gnue.common.rpc.drivers.hessian import hessianlib


__version__ = "0.2"


def resolve_dotted_attribute(obj, attr, allow_dotted_names=True):
	"""resolve_dotted_attribute(a, 'b.c.d') => a.b.c.d

	Resolves a dotted attribute name to an object.  Raises
	an AttributeError if any attribute in the chain starts with a '_'.

	If the optional allow_dotted_names argument is false, dots are not
	supported and this function operates similar to getattr(obj, attr).
	"""

	if allow_dotted_names:
		attrs = attr.split(".")
	else:
		attrs = [attr]

	for i in attrs:
		if i.startswith("_"):
			raise AttributeError(
				"attempt to access private attribute '%s'" % i
			)
		else:
			obj = getattr(obj,i)
	return obj

def list_public_methods(obj):
	"""Returns a list of attribute strings, found in the specified
	object, which represent callable attributes"""

	return [member for member in dir(obj)
		if not member.startswith("_") and
		callable(getattr(obj, member))]

def remove_duplicates(lst):
	"""remove_duplicates([2,2,2,1,3,3]) => [3,1,2]

	Returns a copy of a list without duplicates. Every list
	item must be hashable and the order of the items in the
	resulting list is not defined.
	"""
	u = {}
	for x in lst:
		u[x] = 1

	return u.keys()

class SimpleHessianDispatcher:
	"""
	Mix-in class that dispatches Hessian requests.

	This class is used to register Hessian method handlers
	and then to dispatch them. There should never be any
	reason to instantiate this class directly.
	"""

	def __init__(self):
		self.funcs = {}
		self.instance = None

	def register_instance(self, instance, allow_dotted_names=False):
		"""
		Registers an instance to respond to Hessian requests.

		Only one instance can be installed at a time.

		If the registered instance has a _dispatch method then that
		method will be called with the name of the Hessian method and
		its parameters as a tuple
		e.g. instance._dispatch('add',(2,3))

		If the registered instance does not have a _dispatch method
		then the instance will be searched to find a matching method
		and, if found, will be called. Methods beginning with an '_'
		are considered private and will not be called by
		SimpleHessianServer.

		If a registered function matches a Hessian request, then it
		will be called instead of the registered instance.

		If the optional allow_dotted_names argument is true and the
		instance does not have a _dispatch method, method names
		containing dots are supported and resolved, as long as none of
		the name segments start with an '_'.

		*** SECURITY WARNING: ***

		Enabling the allow_dotted_names options allows intruders
		to access your module's global variables and may allow
		intruders to execute arbitrary code on your machine.  Only
		use this option on a secure, closed network.
		"""

		self.instance = instance
		self.allow_dotted_names = allow_dotted_names

	def register_function(self, function, name = None):
		"""Registers a function to respond to Hessian requests.

		The optional name argument can be used to set a Unicode name
		for the function.
		"""

		if name is None:
			name = function.__name__
		self.funcs[name] = function

	def register_introspection_functions(self):
		"""Registers the Hessian introspection methods in the system
		namespace.
		"""

		self.funcs.update({"system.listMethods": self.system_listMethods,
				"system.methodSignature": self.system_methodSignature,
				"system.methodHelp": self.system_methodHelp})

	def register_multicall_functions(self):
		"""Registers the Hessian multicall method in the system
		namespace."""

		self.funcs.update({"system.multicall": self.system_multicall})

	def _marshaled_dispatch(self, data, dispatch_method = None):
		"""Dispatches an Hessian method from marshalled (Hessian) data.

		Hessian methods are dispatched from the marshalled (Hessian) data
		using the _dispatch method and the result is returned as
		marshalled data. For backwards compatibility, a dispatch
		function can be provided as an argument (see comment in
		SimpleHessianRequestHandler.do_POST) but overriding the
		existing method through subclassing is the prefered means
		of changing method dispatch behavior.
		"""

		params, method = hessianlib.loads(data)

		# generate response
		try:
			if dispatch_method is not None:
				response = dispatch_method(method, params)
			else:
				response = self._dispatch(method, params)
			# wrap response in a singleton tuple
			response = (response,)
			response = hessianlib.dumps(response, methodresponse=1)
		except Fault, fault:
			response = hessianlib.dumps(fault)
		except:
			# report exception back to server
			response = hessianlib.dumps(
				hessianlib.Fault(1, "%s:%s" % (sys.exc_type, sys.exc_value))
			)

		return response

	def system_listMethods(self):
		"""system.listMethods() => ['add', 'subtract', 'multiple']

		Returns a list of the methods supported by the server."""

		methods = self.funcs.keys()
		if self.instance is not None:
			# Instance can implement _listMethod to return a list of
			# methods
			if hasattr(self.instance, "_listMethods"):
				methods = remove_duplicates(
					methods + self.instance._listMethods()
				)
			# if the instance has a _dispatch method then we
			# don't have enough information to provide a list
			# of methods
			elif not hasattr(self.instance, "_dispatch"):
				methods = remove_duplicates(
					methods + list_public_methods(self.instance)
				)
		methods.sort()
		return methods

	def system_methodSignature(self, method_name):
		"""system.methodSignature('add') => [double, int, int]

		Returns a list describing the signature of the method. In the
		above example, the add method takes two integers as arguments
		and returns a double result.

		This server does NOT support system.methodSignature."""

		return "signatures not supported"

	def system_methodHelp(self, method_name):
		"""system.methodHelp('add') => "Adds two integers together"

		Returns a string containing documentation for the specified method."""

		method = None
		if self.funcs.has_key(method_name):
			method = self.funcs[method_name]
		elif self.instance is not None:
			# Instance can implement _methodHelp to return help for a method
			if hasattr(self.instance, "_methodHelp"):
				return self.instance._methodHelp(method_name)
			# if the instance has a _dispatch method then we
			# don't have enough information to provide help
			elif not hasattr(self.instance, "_dispatch"):
				try:
					method = resolve_dotted_attribute(
						self.instance,
						method_name,
						self.allow_dotted_names
					)
				except AttributeError:
					pass

		# Note that we aren't checking that the method actually
		# be a callable object of some kind
		if method is None:
			return ""
		else:
			import pydoc
			return pydoc.getdoc(method)

	def system_multicall(self, call_list):
		"""system.multicall([{'methodName': 'add', 'params': [2, 2]}, ...]) => \
		[[4], ...]

		        Allows the caller to package multiple Hessian calls into a single
		        request.
		        """

		results = []
		for call in call_list:
			method_name = call["methodName"]
			params = call["params"]

			try:
				# XXX A marshalling error in any response will fail the entire
				# multicall. If someone cares they should fix this.
				results.append([self._dispatch(method_name, params)])
			except Fault, fault:
				results.append(
					{"code": fault.code,
						"message": fault.message}
				)
			except:
				results.append(
					{"code": 1,
						"message": "%s:%s" % (sys.exc_type, sys.exc_value)}
				)
		return results

	def _dispatch(self, method, params):
		"""Dispatches the Hessian method.

		Hessian calls are forwarded to a registered function that
		matches the called Hessian method name. If no such function
		exists then the call is forwarded to the registered instance,
		if available.

		If the registered instance has a _dispatch method then that
		method will be called with the name of the Hessian method and
		its parameters as a tuple
		e.g. instance._dispatch('add',(2,3))

		If the registered instance does not have a _dispatch method
		then the instance will be searched to find a matching method
		and, if found, will be called.

		Methods beginning with an '_' are considered private and will
		not be called.
		"""

		func = None
		try:
			# check to see if a matching function has been registered
			func = self.funcs[method]
		except KeyError:
			if self.instance is not None:
				# check for a _dispatch method
				if hasattr(self.instance, "_dispatch"):
					return self.instance._dispatch(method, params)
				else:
					# call instance method directly
					try:
						func = resolve_dotted_attribute(
							self.instance,
							method,
							self.allow_dotted_names
						)
					except AttributeError:
						pass

		if func is not None:
			return func(*params)
		else:
			raise Exception("method '%s' is not supported" % method)

class SimpleHessianRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	"""Simple Hessian request handler class.

	Handles all HTTP POST requests and attempts to decode them as
	Hessian requests.
	"""
	server_version = "SimpleHessian/%s" % __version__

	def do_POST(self):
		"""Handles the HTTP POST request.

		Attempts to interpret all HTTP POST requests as Hessian calls,
		which are forwarded to the server's _dispatch method for handling.
		"""

		try:
			# get arguments
			data = self.rfile.read(int(self.headers["content-length"]))
			# In previous versions of SimpleHessianServer, _dispatch
			# could be overridden in this class, instead of in
			# SimpleHessianDispatcher. To maintain backwards compatibility,
			# check to see if a subclass implements _dispatch and dispatch
			# using that method if present.
			response = self.server._marshaled_dispatch(
				data, getattr(self, "_dispatch", None)
			)
		except: # This should only happen if the module is buggy
			# internal error, report as HTTP server error
			self.send_response(500)
			self.end_headers()
		else:
			# got a valid Hessian RPC response
			self.send_response(200)
			self.send_header("Content-length", str(len(response)))
			self.end_headers()
			self.wfile.write(response)

			# shut down the connection
			self.wfile.flush()
			self.connection.shutdown(1)

	def log_request(self, code="-", size="-"):
		"""Selectively log an accepted request."""

		if self.server.logRequests:
			BaseHTTPServer.BaseHTTPRequestHandler.log_request(self, code, size)

class SimpleHessianServer(SocketServer.TCPServer, SimpleHessianDispatcher):
	"""Simple Hessian server.

	Simple Hessian server that allows functions and a single instance
	to be installed to handle requests. The default implementation
	attempts to dispatch Hessian calls to the functions or instance
	installed in the server. Override the _dispatch method inhereted
	from SimpleHessianDispatcher to change this behavior.
	"""

	def __init__(self, addr, requestHandler=SimpleHessianRequestHandler,
		logRequests=0):
		self.logRequests = logRequests

		SimpleHessianDispatcher.__init__(self)
		SocketServer.TCPServer.__init__(self, addr, requestHandler)

class CGIHessianRequestHandler(SimpleHessianDispatcher):
	"""Simple handler for Hessian data passed through CGI."""

	def __init__(self):
		SimpleHessianDispatcher.__init__(self)

	def handle_hessian(self, request_text):
		"""Handle a single Hessian request"""

		response = self._marshaled_dispatch(request_text)

		print "Content-Length: %d" % len(response)
		print
		sys.stdout.write(response)

	def handle_get(self):
		"""Handle a single HTTP GET request.

		Default implementation indicates an error because
		Hessian uses the POST method.
		"""

		code = 400
		message, explain = \
			BaseHTTPServer.BaseHTTPRequestHandler.responses[code]

		response = BaseHTTPServer.DEFAULT_ERROR_MESSAGE % \
			{
			"code": code,
			"message": message,
			"explain": explain
		}
		print "Status: %d %s" % (code, message)
		print "Content-Type: text/html"
		print "Content-Length: %d" % len(response)
		print
		sys.stdout.write(response)

	def handle_request(self, request_text = None):
		"""Handle a single Hessian request passed through a CGI post method.

		If no Hessian data is given then it is read from stdin. The resulting
		Hessian response is printed to stdout along with the correct HTTP
		headers.
		"""

		if request_text is None and \
			os.environ.get("REQUEST_METHOD", None) == "GET":
			self.handle_get()
		else:
			# POST data is normally available through stdin
			if request_text is None:
				request_text = sys.stdin.read()

			self.handle_hessian(request_text)

if __name__ == '__main__':

	def raiseErr(code, message):
		raise hessianlib.Fault(code, message)

	def echo(param):
		return param

	server = SimpleHessianServer(("", 7000), logRequests=1)
	server.register_function(pow)
	server.register_function(lambda x,y: x+y, 'add')
	server.register_function(lambda: "Hello, World", 'hello')
	server.register_function(echo)
	server.register_function(raiseErr)
	server.register_introspection_functions()
	server.serve_forever()
