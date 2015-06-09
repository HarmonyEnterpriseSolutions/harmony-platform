# GNU Enterprise Common Library - RPC Interface - XML-RPC client
#
# Copyright 2001-2007 Free Software Foundation
#
# This file is part of GNU Enterprise.
#
# GNU Enterprise is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# GNU Enterprise is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.
#
# $Id: ClientAdapter.py 9431 2007-03-07 10:13:28Z reinhard $

import xmlrpclib
import socket
import weakref

from gnue.common.apps import errors
from gnue.common.rpc import client
from gnue.common.rpc.drivers import Base
from gnue.common.utils import http
from src.gnue.common.rpc.drivers.xmlrpc import typeconv


# =============================================================================
# xml-rpc transport class using a persistent connection
# =============================================================================

class PersistentTransport (xmlrpclib.Transport):
	"""
	Handles a persistent HTTP connection to an XML-RPC server. The connection
	will be established on the first request, and reused by all later requests.
	The XML-RPC server is supposed to grant persistent connections via HTTP.
	"""

	user_agent = "GNUe XML-RPC"

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self):

		self.__connection = None
		# In Python 2.4, xmlrpclib.Transport does not have any __init__ method. In
		# Python 2.5, it does has an __init__ method and it must be called.
		if hasattr(xmlrpclib.Transport, '__init__'):
			xmlrpclib.Transport.__init__(self)


	# ---------------------------------------------------------------------------
	# Send a request to the given host and return it's response
	# ---------------------------------------------------------------------------

	def request (self, host, handler, request_body, verbose = 0):
		"""
		Send an xml-request to the given host and return the server's response. If
		there's no persistent HTTP/1.1 connection available already it will be
		established.

		@param host: target host to be contacted. This host must include a
		  port-number, e.g. foobar.com:4711
		@param handler: target RPC handler, usually '/RPC2'
		@param request_body: XML-RPC request body as created by a xmlrpclib.dumps ()
		@param verbose: if set to 1 the underlying L{http.HTTPConnection} will
		  print additional debug messages

		@returns: tuple with the server's response to the request (as returned by
		  the L{xmlrpclib.Unmarshaller}

		@raises AccessDeniedError: if this client is not allowed to access the
		  RPC services at the given host
		@raises ProtocolError: if the server response was another one than 200 (OK)
		"""

		if not self.__connection:
			self.__connection = http.HTTPConnection (host)

		self.__connection.set_debuglevel (verbose)
		self.__connection.request ('POST', handler, request_body,
			{'Content-Type': 'text/xml'})

		response = self.__connection.getresponse ()
		if response:
			if response.status == 403:
				raise client.AccessDeniedError, host

			elif response.status != 200:
				raise xmlrpclib.ProtocolError (host + handler, response.status,
					response.reason, response.msg)

			data = response.read ()

			p, u = self.getparser ()
			p.feed (data)
			p.close ()

			result = u.close ()
		else:
			result = None

		return result


	# ---------------------------------------------------------------------------
	# Close the HTTP connection
	# ---------------------------------------------------------------------------

	def close (self):
		"""
		Close the transport connection (if still open).
		"""

		if self.__connection:
			self.__connection.close ()
			self.__connection = None



# =============================================================================
# XML-RPC client adapter
# =============================================================================

class ClientAdapter (Base.Client):
	"""
	Implements an XML-RPC client adapter using persistent HTTP connections as
	transport.
	"""

	_default_transport = 'http'
	_default_port      = 8765

	# ---------------------------------------------------------------------------
	# Initialize object
	# ---------------------------------------------------------------------------

	def __init__ (self, params):
		"""
		@param params: parameter dictionary for initialization of the adapter
		"""

		Base.Client.__init__ (self, params)

		self._transport = PersistentTransport ()
		self._verbose   = params.get ('loglevel', 0)
		self.__remote   = "%s:%s" % (self._host, self._port)
		self.__objectProxies = weakref.WeakValueDictionary ()


	# ---------------------------------------------------------------------------
	# Run a procedure on the server
	# ---------------------------------------------------------------------------

	def _callMethod_ (self, method, *args, **params):
		"""
		Execute a method on the XML-RPC server and return it's result.

		@param method: name of the method to be executed
		@param args: tuple with all positional arguments
		@param params: dictionary with all keyword arguments - XML-RPC does B{NOT}
		  support keyword arguments

		@return: result of the remote procedure call

		@raises RemoteError: if an exception occurred while executing the method on
		  the server, this exception will carry that exception
		@raises AdminError: if an exception occurs in the socket-layer
		@raises InvalidParameter: if an argument cannot be converted into a RPC
		  data-type, or a result cannot be converted into a native python type
		"""

		assert gEnter (9)

		checktype (method, basestring)

		if not self._transport:
			assert gLeave (9)
			return

		__args = tuple ([typeconv.python_to_rpc (arg, self.__unwrapProxy) \
					for arg in args])
		try:
			request = xmlrpclib.dumps (__args, method, allow_none = True)
			result = self._transport.request (self.__remote, "/RPC2", request,
				self._verbose)

			# If the result is a tuple with only one item, we're only interessted in
			# that single item
			if len (result) == 1:
				result = result [0]

		except xmlrpclib.Fault, e:
			# If we got a Fault object, transform it into a RemoteError
			(exType, exName, exMessage, exDetail) = e.faultString.split (u'\x91')
			raise errors.RemoteError, (exType, exName, exMessage, exDetail)

		except socket.error:
			raise errors.AdminError, errors.getException () [2]

		result = typeconv.rpc_to_python (result, self.__wrapProxy,
			client.InvalidParameter)
		assert gLeave (9, result)
		return result


	# ---------------------------------------------------------------------------
	# Nice string representation
	# ---------------------------------------------------------------------------

	def __str__ (self):
		return "XML-RPC client adapter for %s" % self.__remote


	# ---------------------------------------------------------------------------
	# Wrap an ObjectProxy instance around a server object
	# ---------------------------------------------------------------------------

	def __wrapProxy (self, item):

		if item ['__id__'] in self.__objectProxies:
			return self.__objectProxies [item ['__id__']]
		else:
			result = ObjectProxy (self, item)
			self.__objectProxies [item ['__id__']] = result
			return result


	# ---------------------------------------------------------------------------
	# Unwrap an ObjectProxy instance so it can be sent through xmlrpc
	# ---------------------------------------------------------------------------

	def __unwrapProxy (self, proxy):

		return proxy._storedItem


	# ---------------------------------------------------------------------------
	# Close the underlying transport connection
	# ---------------------------------------------------------------------------

	def destroy (self):
		"""
		Close the transport connection
		"""

		self._transport.close ()
		self._transport = None


# =============================================================================
# Proxy class for objects living on the server
# =============================================================================

class ObjectProxy (Base.ServerProxy):
	"""
	A proxy class providing an execution context of server side objects.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, adapter, item):

		Base.ServerProxy.__init__ (self, adapter)
		self._storedItem = item


	# ---------------------------------------------------------------------------
	# Remove the object from the server's object store
	# ---------------------------------------------------------------------------

	def __del__ (self):
		"""
		Remove the object from the server's object store. Further access to this
		object will lead to an exception
		"""

		self._adapter._callMethod_ ('_destroy', self._storedItem)


	# ---------------------------------------------------------------------------
	# Attribute access
	# ---------------------------------------------------------------------------

	def __getattr__ (self, name):

		result = ObjectProxyMethod (self._adapter, name, self._storedItem)
		self.__dict__ [name] = result

		return result



# =============================================================================
# Callable environment for object proxies
# =============================================================================

class ObjectProxyMethod (Base.ProxyMethod):
	"""
	Provide a callable environment for an L{ObjectProxy}. This will call the
	"_call" method at the remote server, giving the id-dictionary and the
	method-name as first and second argument.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, adapter, methodname, item):

		Base.ProxyMethod.__init__ (self, adapter, methodname)
		self._storeItem = item


	# ---------------------------------------------------------------------------
	# Call a method
	# ---------------------------------------------------------------------------

	def __call__ (self, *args, **params):

		# Add the id-dictionary and the methodname to the rpc-call
		nargs = tuple ([self._storeItem, self._methodname] + list (args))
		return self._adapter._callMethod_ ('_call', *nargs, **params)

	def __str__ (self):
		return "ObjectProxyMethod '%s' of %s" % (self._methodname, self._storeItem)
