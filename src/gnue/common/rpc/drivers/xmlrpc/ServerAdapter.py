# GNU Enterprise Common Library - RPC Interface - xmlrpc ServerAdpater
#
# Copyright 2001-2007 Free Software Foundation
#
# This file is part of GNU Enterprise
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
# $Id: ServerAdapter.py 9222 2007-01-08 13:02:49Z johannes $

import os
import xmlrpclib
import SocketServer
from SimpleXMLRPCServer import SimpleXMLRPCServer

from src.gnue.common.rpc.drivers.xmlrpc import typeconv
from gnue.common.rpc import server
from gnue.common.rpc.drivers import Base
from gnue.common.apps import errors
from gnue.common.utils import http



# =============================================================================
# Exceptions
# =============================================================================

class ObjectNotFoundError (errors.SystemError):
	def __init__ (self, item):
		msg = u_("Element of type '%(type)s' with id '%(id)s' not found in store")\
			% {'type': item ['__rpc_datatype__'], 'id': item ['__id__']}
		errors.SystemError.__init__ (self, msg)


# =============================================================================
# Class implementing an XML-RPC server adapter
# =============================================================================

class ServerAdapter (Base.Server):
	"""
	Implementation of a XML-RPC server supporting HTTP/1.1 persistent
	connections. It supports both forking and threading per connection and one
	can use the 'servertype' parameter set to 'forking' or 'threading' to select
	this behavior. NOTE: 'forking' is not supported by all platforms; in this
	case a threading server will be selected automatically.

	@ivar _tpcServer: the TCPServer of the XML-RPC-Server
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, service, parameters):
		"""
		@param service: python object to be served
		@param parameters: dictionary of server specific parameters
		"""

		Base.Server.__init__ (self, service, parameters)

		stype = parameters.get ('servertype', 'forking')

		# In order to use a forking server make sure it's supported by the OS
		if stype == 'forking' and hasattr (os, 'fork'):
			serverClass = ForkingXMLRPCServer
			self.__type = 'forking'
		else:
			serverClass = ThreadingXMLRPCServer
			self.__type = 'threading'

		self._tcpServer = serverClass ((self._bindto, self._port),
			logRequests = parameters.get ('loglevel', 0), adapter = self)

		# Store with all valid objects created by the server
		self._clientPerObject = {}
		self._objectPerClient = {}

		# Register the python object to be served as well as the introspection
		# functions (system.list_methods,system.list_help, system.list_signatures)
		self._tcpServer.register_instance (self.instance)
		self._tcpServer.register_introspection_functions ()

		# Register functions for object support: calling and removing
		self._tcpServer.register_function (self._call)
		self._tcpServer.register_function (self._destroy)


	# ---------------------------------------------------------------------------
	# Dispatch a method with the given parameters
	# ---------------------------------------------------------------------------

	def call (self, client, method, parameters):
		"""
		Dispatch a method with a given set of parameters

		@param method: method to be dispatched
		@param parameters: tuple of parameters to call method with. These
		  parameters are given in RPC types.

		@returns: result of the method given in RPC types
		"""

		assert gEnter (9)

		checktype (method, basestring)
		checktype (parameters, tuple)

		params = typeconv.rpc_to_python (parameters, self._fetchFromStore,
			server.InvalidParameter, client)
		result = self._tcpServer._dispatch (method, params)

		result = typeconv.python_to_rpc (result, self._updateStore, client)
		assert gLeave (9, result)
		return result


	# ---------------------------------------------------------------------------
	# Call a procedure of a given stored object
	# ---------------------------------------------------------------------------

	def _call (self, storedObject, method, *parameters):

		assert gEnter (9)
		result = getattr (storedObject, method) (*parameters)
		assert gLeave (9, result)
		return result


	# ---------------------------------------------------------------------------
	# Remove an object from the object store
	# ---------------------------------------------------------------------------

	def _destroy (self, item):

		assert gEnter (9)

		if hasattr (item, '_destroy'):
			item._destroy ()

		itemId = str (id (item))
		client = self._clientPerObject.get (itemId)

		if itemId in self._clientPerObject:
			del self._clientPerObject [itemId]

		if client in self._objectPerClient:
			if itemId in self._objectPerClient [client]:
				del self._objectPerClient [client][itemId]

		assert gLeave (9)


	# ---------------------------------------------------------------------------
	# Add an object to the store or update it's reference
	# ---------------------------------------------------------------------------

	def _updateStore (self, item, client):

		gEnter (9)

		# The itemId must be stored as string, because 64 bit numbers cannot be
		# transported with xmlrpc
		itemId = str (id (item))
		result = {'__id__': itemId, '__rpc_datatype__': 'object'}
		self._objectPerClient.setdefault (client, {}) [itemId] = item
		self._clientPerObject [itemId] = client

		assert gLeave (9, result)

		return result


	# ---------------------------------------------------------------------------
	# Fetch a real object from the store, identified by it's id-dictionary
	# ---------------------------------------------------------------------------

	def _fetchFromStore (self, item, client):

		try:
			itemId = item ['__id__']
			return self._objectPerClient [client][itemId]

		except KeyError:
			raise ObjectNotFoundError, item


	# ---------------------------------------------------------------------------
	# Clear all object of a given client
	# ---------------------------------------------------------------------------

	def _clearClientObjects (self, client):

		assert gEnter (9)

		for item in self._objectPerClient.get (client, {}).values ():
			self._destroy (item)

		assert gLeave (9)


	# ---------------------------------------------------------------------------
	# Nice string representation
	# ---------------------------------------------------------------------------

	def __repr__ (self):
		return "<%s XML-RPC server serving '%s' at %d>" % \
			(self.__type, self.instance, id (self))


	# ---------------------------------------------------------------------------
	# Start the server
	# ---------------------------------------------------------------------------

	def _serve_ (self):

		self._tcpServer.serve_forever ()



# =============================================================================
# XML-RPC Request handler
# =============================================================================

class XMLRPCRequestHandler (http.HTTPRequestHandler):
	"""
	Handle XML-RPC requests sent via HTTP connections.

	@cvar protocol_version: Set to 'HTTP/1.1' so we do have persistent
	  connections.
	"""

	# Make sure to support persistent connections
	protocol_version = "HTTP/1.1"


	# ---------------------------------------------------------------------------
	# log all requests at debug level 9
	# ---------------------------------------------------------------------------

	def log_request (self, code = '-', size = '-'):
		"""
		Log all requests at debug level 9.
		"""

		assert gDebug (9, '"%s" %s %s' % (self.requestline, code, size))


	# ---------------------------------------------------------------------------
	# Process a POST request
	# ---------------------------------------------------------------------------

	def do_POST (self):
		"""
		Process a XML-RPC request. Exceptions are reported by L{xmlrpclib.Fault}
		instances. Such an instance carries a string consisting of the group, name,
		message and traceback of the exception, separated by the unicode character
		u'0x91' (see L{errors.getException}). The underlying connection will be
		closed only if stated by the headers (e.g. 'Connection: close')
		"""

		try:
			data = self.rfile.read (int (self.headers ["content-length"]))

			params, method = xmlrpclib.loads (data)

			response = self.server.serverAdapter.call (self.client_address, method,
				params)
			response = (response,)

			response = xmlrpclib.dumps (response, methodresponse = 1, allow_none = 1)

		except:
			stack  = u'\x91'.join (errors.getException ())
			response = xmlrpclib.Fault (1, stack)
			response = xmlrpclib.dumps (response, methodresponse = 1)

		# Add the following data to the send-queue, but don't write it to the
		# socket
		self.send_response (200, flush = False)
		self.send_header ("Content-type", "text/xml", flush = False)
		self.send_header ("Content-length", str (len (response)), flush = False)
		self.end_headers (flush = False)

		# Add the response to the send-queue and finally flush everything to the
		# socket.
		self.write (response, flush = True)

		# If a shutdown of the connection is requested do so, although we assume to
		# have a persistent connection.
		if self.close_connection:
			self.connection.shutdown (1)



# =============================================================================
# XML-RPC TCP server
# =============================================================================

class XMLRPCServer (SimpleXMLRPCServer):
	"""
	A TCP server implementing a XML-RPC server. This class verifies each
	connection against a list of 'allowed hosts' and if it is not listed, an
	error 403 (Forbidden) is returned to the client. If the owning
	L{ServerAdapter} does not provide such a list, all clients are accepted.
	These verification takes place *before* a new process for the connection is
	forked or a new thread is started.

	@ivar allow_reuse_address: if True, the port can be reused even if it's in
	  TIME_WAIT state
	"""

	allow_reuse_address = True

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, addr, requestHandler = XMLRPCRequestHandler,
		logRequests = False, allow_none = 1, adapter = None):

		SimpleXMLRPCServer.__init__ (self, addr, requestHandler, logRequests)
		self.allow_none    = allow_none
		self.serverAdapter = adapter


	# ---------------------------------------------------------------------------
	# Verify a given request
	# ---------------------------------------------------------------------------

	def verify_request (self, request, client_address):
		"""
		Verify if the given client connection is allowed to use the services.

		@param request: the already opened socket object
		@param client_address: tuple with the address and port of the client

		@returns: True, if the client is accepted, False if it is not allowed to
		  use the services. In the latter case a '403' error response will be sent
		  to the socket.
		"""

		assert gEnter (9)

		allowed = self.serverAdapter and self.serverAdapter.allowed_hosts
		for host in allowed:
			if client_address [0][:len (host)] == host:
				assert gLeave (9, True)
				return True

		request.send ('HTTP/1.1 403 Forbidden\r\n\r\n')
		self.close_request (request)

		assert gLeave (9, False)
		return False


	# ---------------------------------------------------------------------------
	# A connection to a given socket has been closed
	# ---------------------------------------------------------------------------

	def close_request (self, request):

		if self.serverAdapter:
			self.serverAdapter._clearClientObjects (request.getpeername ())

		SimpleXMLRPCServer.close_request (self, request)



# =============================================================================
# A forking XML-RPC server
# =============================================================================

class ForkingXMLRPCServer (SocketServer.ForkingMixIn, XMLRPCServer):
	"""
	A XML-RPC server which forks a new process per connection.
	"""
	pass


# =============================================================================
# A threading XML-RPC server
# =============================================================================

class ThreadingXMLRPCServer (SocketServer.ThreadingMixIn, XMLRPCServer):
	"""
	A XML-RPC server which starts a new thread per connection.
	"""
	pass
