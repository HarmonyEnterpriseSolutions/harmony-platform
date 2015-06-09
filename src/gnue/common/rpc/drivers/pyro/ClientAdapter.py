# GNU Enterprise Common Library - RPC Interface - Pyro ClientAdapter
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
# $Id: ClientAdapter.py 9222 2007-01-08 13:02:49Z johannes $

from gnue.common.rpc import client
from gnue.common.rpc.drivers import Base


# =============================================================================
# Plugin initialization
# =============================================================================

def __initplugin__ ():
	try:
		import Pyro.core

	except ImportError:
		raise client.AdapterInitializationError, \
			u_("Unable to load Pyro. To use the Pyro interface, please install " \
				"pyro from http://pyro.sf.net")



# =============================================================================
# Proxy class from server objects
# =============================================================================

class ServerProxy (Base.ServerProxy):
	"""
	A proxy class for Pyro RPC service objects. This class is needed to supply a
	'_destroy' method to the proxy object.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, adapter, delegate):

		Base.ServerProxy.__init__ (self, adapter)
		self.__delegate = delegate


	# ---------------------------------------------------------------------------
	# Attribute access
	# ---------------------------------------------------------------------------

	def __getattr__ (self, name):
		"""
		Attribute access will be delegated to the encapsulated Pyro-Proxy object
		"""

		return getattr (self.__delegate, name)



# =============================================================================
# ClientAdapter
# =============================================================================

class ClientAdapter (Base.Client):
	"""
	Implementation of a RPC client using the Pyro framework.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, params):
		"""
		@param params: parameter dictionary for adapter initialization
		"""

		import Pyro.core
		Base.Client.__init__ (self, params)

		# initialize the client and set the default namespace group
		self._pyroGroup = ':GNUeRPC'

		Pyro.core.initClient ()
		Pyro.config.PYRO_NS_DEFAULTGROUP = self._pyroGroup

		self.__getPyroProxy = Pyro.core.getProxyForURI


	# ---------------------------------------------------------------------------
	# Return a proxy object to the service at the remote site
	# ---------------------------------------------------------------------------

	def _getServerProxy_ (self):
		"""
		Return a proxy object to the hosted service at the RPC server.

		@returns: Proxy object
		"""

		return ServerProxy (self, self.__getPyroProxy ("PYRONAME://GNUeRPCService"))
