# GNU Enterprise Common Library - Connection object wrapper for triggers
#
# Copyright 2000-2007 Free Software Foundation
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
# $Id: ConnectionTriggerObj.py 9222 2007-01-08 13:02:49Z johannes $
"""
Wrapper object for connections to be used in trigger namespace.
"""

__all__ = ['ConnectionTriggerObj', 'add_connections_to_tree']

import types

from gnue.common.apps import GDebug
from gnue.common.definitions import GObjects


# =============================================================================
# Connection wrapper object
# =============================================================================

class ConnectionTriggerObj (GObjects.GObj):
	"""
	Class that allows us to insert Connection objects into trigger namespaces
	"""

	_blockedMethods = ('connect','close','getLoginFields')


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connection, name):

		self.__connection = connection
		self.name         = name
		GObjects.GObj.__init__ (self, type = "GCConnection")

		self._triggerGlobal = True
		self._triggerFunctions = {}

		for method in dir (connection):
			function = getattr (connection,method)
			if method [0] != '_' and method not in self._blockedMethods \
				and type (function) == types.MethodType:
				self._triggerFunctions [method] = {'function': function}

		self._triggerProperties = {'login': {'get': self.__getLogin}}


	# ---------------------------------------------------------------------------
	# Find out who connected
	# ---------------------------------------------------------------------------

	def __getLogin(self):

		return self.__connection.manager.getAuthenticatedUser (self.name)


# =============================================================================
# Add all connections to the namespace
# =============================================================================

def add_connections_to_tree (connections, root_object):
	"""
	Adds a L{ConnectionTriggerObj} object for each connection as a child to the
	root object.

	This causes all connections to become visible in the global trigger
	namespace, because they will be handled like XML elements defined within
	the root element.
	"""
	for name in connections.getConnectionNames():
		try:
			conn = connections.getConnection(name)
		except:
			assert gDebug (1, "Cannot add connection %s to object tree" % name)
			continue
		root_object.addChild(ConnectionTriggerObj(conn, name))
