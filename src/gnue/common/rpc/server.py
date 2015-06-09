# GNU Enterprise Common - RPC - Server Interface
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
# $Id: server.py 9222 2007-01-08 13:02:49Z johannes $

"""
Server side of a GNUe RPC connection
"""

__all__ = ['bind', 'AdapterInitializationError', 'AdapterConfigurationError',
	'ProgrammingError', 'InvalidParameter']

from gnue.common.apps import errors, plugin


# =============================================================================
# Public functions
# =============================================================================

# -----------------------------------------------------------------------------
# Create ServerAdpaters for the given transports
# -----------------------------------------------------------------------------

def bind (transports, service):
	"""
	Build server adapters for the given set of transports publishing the given
	service instance.

	@param transports: A dictionary of server adpaters to create. The dictionary
	  keys are the name of the drivers and the values are dictionaries with
	  parameters passed to the driver. Example: {'xmlrpc': {'loglevel': False,..}}
	@param service: python instance which should be served by the requested
	  adapters

	@returns: a dictionary with the name of the service provider as key and the
	  ServerAdapter instance as value
	"""

	checktype (transports, dict)

	result = {}

	for interface in transports:
		params = transports [interface]
		driver = plugin.find (interface, 'gnue.common.rpc.drivers', 'ServerAdapter')

		result [interface] = driver.ServerAdapter (service, params)

	return result


# =============================================================================
# Exceptions
# =============================================================================

# -----------------------------------------------------------------------------
# The requested adapter could not initialize. Perhaps the
# supplied parameters do not point to a valid server, etc.
# -----------------------------------------------------------------------------

class AdapterInitializationError (errors.AdminError):
	pass

# -----------------------------------------------------------------------------
# The parameters supplied to the adapter are not in the
# correct format, or all the needed parameters were not
# supplied.
# -----------------------------------------------------------------------------

class AdapterConfigurationError (AdapterInitializationError):
	pass

# -----------------------------------------------------------------------------
# Parent for all caller errors
# -----------------------------------------------------------------------------

class ProgrammingError (errors.SystemError):
	pass

# -----------------------------------------------------------------------------
# An invalid parameter was passed to a RPC
# -----------------------------------------------------------------------------

class InvalidParameter (ProgrammingError):
	pass


# =============================================================================
# Self test code
# =============================================================================

if __name__ == '__main__':

	import sys
	import time
	import mx.DateTime

	class TestError (Exception):
		pass

	class subobject:
		def __init__ (self, name = None):
			print "Initializing subobject"
			self.name = name

		def printIt (self):
			print "Current Name is '%s'" % self.name
			return self.name

		def setName (self, name):
			print "Setting new name to:", name
			self.name = name

		def test (self, *args):
			print "Testing subobject:", args

		def argcheck (self, other):
			print "Hi, my name is", self.name
			print "Your name is", other.name
			return other.name

		def dictcheck (self, other, adict):
			print "I am:", self.name
			print "Other is:", other.name
			result = adict ['buddy']
			print "dict [buddy] is:", result.name, id (result)
			return result

		def __del__ (self):
			print "Destroying subobject", id (self)

	class servertest:

		def stringtest (self, s):
			return '"%s" is a string' % s

		def ustringtest (self, u):
			return u'"%s" is a unicode string' % u

		def inttest (self, i):
			return i * 2

		def floattest (self, f):
			return f * 2

		def datetimetest (self):
			return mx.DateTime.now ()

		def booltest (self):
			return True

		def objtest (self, name = None):
			print "Building a subobject ..."
			return subobject (name)

		def roundtrip (self, value):
			print "SERVER:", repr (value), type (value)
			return value

		def exceptiontest (self):
			raise TestError, 'Message string'

		def shutdown (self):
			# Depending on wether the server is forking or threading a sys.exit (0)
			# will affect either a child-process or a child-thread.
			sys.exit (0)

	if len (sys.argv) == 2 and \
		sys.argv [1] in ['pyro', 'xmlrpc', 'socket', 'soap']:
		drivers = {sys.argv [1]: {'port': 8765, 'servertype': 'forking'}}
	else:
		print "GNUe RPC test server\n\nUsage: gcvs server.py <transport>"
		sys.exit (1)

	print "Building adapter(s) for %s ..." % drivers
	servers = bind (drivers, servertest ())

	print 'Starting server ...'
	for server in servers.values ():
		server.serve ()
