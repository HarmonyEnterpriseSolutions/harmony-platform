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
# Copyright 2000-2007 Free Software Foundation
#
# FILE:
# GClientApp.py
#
# DESCRIPTION:
# Class that provides a basis for GNUe client applications.
#
# NOTES:
# This will eventually have features only needed by "client"
# applications, such as abstracted client RPC calls via
# CORBA, RPC-XML, SOAP, etc.
#

from gnue.common.apps.GBaseApp import GBaseApp
from gnue.common.apps import errors

class StartupError (errors.UserError):
	pass

class GClientApp(GBaseApp):
	"""
	A class designed to be the basis of client type
	applications.

	GBaseApp Provides the following features
	  - Connection login handler
	"""

	#
	#  Set the login handler for this session
	#
	def setLoginHandler(self, loginHandler):
		if self.connections:
			self.connections.loginHandler = loginHandler


	#
	#  Get the login handler for this session
	#
	def getLoginHandler(self):
		if self.connections and self.connections.loginHandler:
			return self.connections.loginHandler
		else:
			return None


	#
	#  Set the connection manager for this session
	#
	def getConnectionManager(self):
		return self.connections
