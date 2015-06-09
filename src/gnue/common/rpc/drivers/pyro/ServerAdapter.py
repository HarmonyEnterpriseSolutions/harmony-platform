# GNU Enterprise Common Library - RPC Interface - Pyro ServerAdapter
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

from gnue.common.rpc import server
from gnue.common.rpc.drivers import Base


# =============================================================================
# Initialization of the plugin
# =============================================================================

def __initplugin__ ():

	try:
		import Pyro.naming
		import Pyro.core
		import Pyro.protocol

	except ImportError:
		raise server.AdapterInitializationError, \
			u_("Unable to load Pyro. To use the Pyro interface, please install " \
				"pyro from http://pyro.sf.net")


# =============================================================================
# ServerAdapter
# =============================================================================

class ServerAdapter (Base.Server):
	"""
	Implementation of an RPC server using the Pyro (Python Remote Objects)
	framework.

	@ivar _ns: the used NameServer to publish services
	@ivar _daemon: the Pyro daemon controlling all incoming requests and doing
	  all the dispatching
	@ivar _pyroService: Pyro.core.ObjBase instance acting as proxy to the served
	  python object
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, service, parameters):
		"""
		@param service: python object to be served
		@param parameters: dictionary of server specific paramters
		"""

		import Pyro.core
		import Pyro.protocol
		import Pyro.naming

		Base.Server.__init__ (self, service, parameters)

		self._pyroGroup = ':GNUeRPC'

		# initialize pyro server
		Pyro.core.initServer (banner = False)
		Pyro.config.PYRO_NS_DEFAULTGROUP = self._pyroGroup
		self._daemon = Pyro.core.Daemon ('PYRO', self._bindto, self._port, True)

		# locate the name server
		locator  = Pyro.naming.NameServerLocator ()
		self._ns = locator.getNS ()

		gDebug (9, "PYRO NameServer found at %s (%s) %s" \
				% (self._ns.URI.address,
				Pyro.protocol.getHostname (self._ns.URI.address) or '??',
				self._ns.URI.port))

		# make sure our namespace group exists
		try:
			self._ns.createGroup (self._pyroGroup)

		except Pyro.core.NamingError:
			pass

		self._daemon.useNameServer (self._ns)

		self._pyroService = Pyro.core.ObjBase ()
		self._pyroService.delegateTo (self.instance)

		uri = self._daemon.connect (self._pyroService, 'GNUeRPCService')


	# ---------------------------------------------------------------------------
	# Start the server
	# ---------------------------------------------------------------------------

	def _serve_ (self):

		try:
			self._daemon.requestLoop ()

		finally:
			self._shutdown_ ()


	# ---------------------------------------------------------------------------
	# Shutdown the adapter
	# ---------------------------------------------------------------------------

	def _shutdown_ (self):
		"""
		Disconnect the registered object from the NameServer and shutdown the
		daemon.
		"""

		print "Shutting down pyro daemon"
		self._daemon.disconnect (self._pyroService)
		self._daemon.shutdown ()


	# ---------------------------------------------------------------------------
	# Nice string representation
	# ---------------------------------------------------------------------------

	def __repr__ (self):
		return "<Pyro RPC server serving '%s' at %d>" % (self.instance, id (self))
