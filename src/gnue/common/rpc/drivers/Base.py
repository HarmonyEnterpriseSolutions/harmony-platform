# GNU Enterprise Common Library - RPC interface - Base for all drivers
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
# $Id: Base.py 9222 2007-01-08 13:02:49Z johannes $

"""
Generic base classes for GNUe RPC server- and client-drivers
"""

__all__ = ['ServerProxy', 'Client', 'ProxyMethod', 'Server']

import sys
import traceback
import urlparse
import types

from gnue.common.apps import i18n
from gnue.common.rpc import server

# Indicate that this is not a valid plugin
__noplugin__ = True


# =============================================================================
# Server Proxy
# =============================================================================

class ServerProxy:
	"""
	A ServerProxy provides access to the RPC server, where each attribute is
	encapsulated by a L{ProxyMethod} instance. Such an instance executes the
	encapsulated method (the former attribute) on the RPC server.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, adapter):
		"""
		Create a new proxy for the given adapter

		@param adapter: L{Server} instance to send all requests to
		"""

		self._adapter = adapter


	# ---------------------------------------------------------------------------
	# attribute access
	# ---------------------------------------------------------------------------

	def __getattr__ (self, name):
		"""
		Wrap a L{ProxyMethod} around the requested attribute name.

		@param name: (method)-name to be wrapped within a ProxyMethod
		"""

		if name [0] == '_':
			raise AttributeError, name

		result = ProxyMethod (self._adapter, name)
		self.__dict__ [name] = result

		return result


	# ---------------------------------------------------------------------------
	# Nice string represenation
	# ---------------------------------------------------------------------------

	def __repr__ (self):
		return "<%s>" % self

	def __str__ (self):
		return "ServerProxy for %s" % self._adapter._url


	# ---------------------------------------------------------------------------
	# Close the connection to the remote service
	# ---------------------------------------------------------------------------

	def _destroy (self):

		self._adapter.destroy ()


# =============================================================================
# Client adapter
# =============================================================================

class Client:
	"""
	Basic client adapter
	"""

	_default_transport_ = None
	_default_host_      = 'localhost'
	_default_port_      = None
	_default_path_      = '/'

	_serverProxyClass_  = ServerProxy


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, params):

		checktype (params, dict)

		self._url       = None
		self._transport = None
		self._host      = None
		self._port      = None
		self._path      = None

		if params.has_key ('url'):

			# Connection defined as URL
			(self._transport, netloc, self._path, params, query, fragment) \
				= urlparse.urlparse (params ['url'])
			(self._host, self._port) = netloc.split (':', 1)

		else:
			# Connection defined as transport/host/port/path info
			self._transport = params.get ('transport')
			self._host      = params.get ('host')
			self._port      = params.get ('port')
			self._path      = params.get ('path')

		# If some info isn't given, fall back to default values
		if not self._transport: self._transport = self._default_transport_
		if not self._host:      self._host      = self._default_host_
		if not self._port:      self._port      = self._default_port_
		if not self._path:      self._path      = self._default_path_

		# Make sure port is an integer
		self._port = int (self._port)

		# Now build the full URL
		self._url = '%s://%s:%d%s' % (self._transport, self._host, self._port,
			self._path)
		self._timeout = params.get ('timeout', 1.0)


	# ---------------------------------------------------------------------------
	# Nice string representation
	# ---------------------------------------------------------------------------

	def __repr__ (self):
		return "<%s>" % self

	def __str__ (self):
		return "RPC-CLientAdapter for %s" % self._url


	# ---------------------------------------------------------------------------
	# Set timeout
	# ---------------------------------------------------------------------------

	def setTimeout (self, timeout):

		self._timeout = timeout


	# ---------------------------------------------------------------------------
	# Request a proxy object
	# ---------------------------------------------------------------------------

	def getServerProxy (self):
		"""
		Create a new proxy object to the remote server.

		@returns: L{ServerProxy} instance handling attribute access and method calls
		"""

		assert gEnter (8)
		result = self._getServerProxy_ ()
		assert gLeave (8, result)
		return result


	# ---------------------------------------------------------------------------
	# Destroy a client adapter's connection
	# ---------------------------------------------------------------------------

	def destroy (self):

		pass


	# ===========================================================================
	# Virtual functions
	# ===========================================================================

	# ---------------------------------------------------------------------------
	# Create a new server proxy object
	# ---------------------------------------------------------------------------

	def _getServerProxy_ (self):
		"""
		Create a new proxy object to the remote server.

		@returns: server proxy object, handling attribute access and method calls
		"""

		return self._serverProxyClass_ (self)


	# ---------------------------------------------------------------------------
	# perform a remote procedure call
	# ---------------------------------------------------------------------------

	def _callMethod_ (self, method, *args, **params):
		"""
		Call a method with the given arguments on the remote side. Descendants
		override this function to do the actual remote procedure call.

		@param method: name of the method to call
		@param args: tuple with all positional arguments
		@param params: dictionary with all keyword arguments

		@return: result of the remote procedure call
		"""

		raise NotImplementedError


# =============================================================================
# Proxy method for clients
# =============================================================================

class ProxyMethod:
	"""
	A ProxyMethod provides a callable for a method in a RPC server. This method
	will be executed by the given L{Client} adapter.
	"""

	# ---------------------------------------------------------------------------
	# Initialize proxy method
	# ---------------------------------------------------------------------------

	def __init__ (self, adapter, methodname):
		"""
		@param adapter: L{Client} instance implementing a C{_callMethod_} function
		@param methodname: name of the method be called
		"""

		self._adapter    = adapter
		self._methodname = methodname


	# ---------------------------------------------------------------------------
	# Run the method
	# ---------------------------------------------------------------------------

	def __call__ (self, *args, **params):
		"""
		Execute the wrapped RPC-Method via L{Client} adapter using the given
		positional and keyword-arguments.

		Note: not all RPC adapter can handle keyword arguments, so take care.
		"""

		assert gEnter (8)
		result = self._adapter._callMethod_ (self._methodname, *args, **params)
		assert gLeave (8, result)
		return result


	# ---------------------------------------------------------------------------
	# Attribute access
	# ---------------------------------------------------------------------------

	def __getattr__ (self, name):
		"""
		Support for nested methods, e.g. system.listMethods.
		@param name: name of the attribute in question

		@returns: L{ProxyMethod} instance pointing to the nested method
		"""

		return ProxyMethod (self._adapter, "%s.%s" % (self._methodname, name))


	# ---------------------------------------------------------------------------
	# Nice string representation
	# ---------------------------------------------------------------------------

	def __repr__ (self):
		return "<%s>" % self

	def __str__ (self):
		return "ProxyMethod '%s' of %s" % (self._methodname, self._adapter)



# =============================================================================
# Base class for server adapters
# =============================================================================

class Server:
	"""
	Basic server adapter.

	@cvar _default_transport_: default transport to use if no transport parameter
	  is given.
	@cvar _default_port_: default port to use if no port parameter is given

	@ivar instance: the python instance to be served by this server
	@ivar allowed_hosts: a sequence of hosts (name/ip-addresses) which are
	  allowed to connect to this server. An empty sequence means 'no restriction'
	"""

	_default_transport_ = None
	_default_port_      = None


	# ---------------------------------------------------------------------------
	# Initialize server object
	# ---------------------------------------------------------------------------

	def __init__ (self, service, parameters):
		"""
		Create a new server adapter serving a given python object.

		@param service: python object to be served
		@param parameters: dictionary of parameters for the server adapter
		"""

		checktype (service, types.InstanceType)
		checktype (parameters, dict)

		self.instance   = service

		self._transport = parameters.get ('transport', self._default_transport_)
		self._port      = parameters.get ('port', self._default_port_)

		if not self._port:
			raise server.AdapterConfigurationError, \
				u_("Required parameter 'port' not supplied")

		self._port   = int (self._port)
		self._bindto = parameters.get ('bindto', '')

		self.allowed_hosts = parameters.get ('allowed_hosts', '').split (',')


	# ---------------------------------------------------------------------------
	# Nice string representation
	# ---------------------------------------------------------------------------

	def __repr__ (self):

		return "<RPC-Server serving '%r' at %x>" % (self.instance, id (self))


	# ---------------------------------------------------------------------------
	# Start server
	# ---------------------------------------------------------------------------

	def serve (self):
		"""
		Start the server.
		"""

		assert gEnter (8)
		result = self._serve_ ()
		assert gLeave (8, result)
		return result


	# ---------------------------------------------------------------------------
	# Shut down the server
	# ---------------------------------------------------------------------------

	def shutdown (self):
		"""
		"""

		assert gEnter (8)
		self._shutdown_ ()
		assert gLeave (8)


	# ---------------------------------------------------------------------------
	# Virtual methods to be implemented by descendants
	# ---------------------------------------------------------------------------

	def _serve_ (self):
		"""
		Start serving the instance.
		"""

		pass


	# ---------------------------------------------------------------------------

	def _shutdown_ (self):

		pass
