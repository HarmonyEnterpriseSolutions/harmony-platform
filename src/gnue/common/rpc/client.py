# GNU Enterprise Common Library - RPC interface - Client adapter
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
# $Id: client.py 9222 2007-01-08 13:02:49Z johannes $

"""
Client side of a GNUe RPC connection
"""

__all__ = ['attach', 'InvalidAdapter', 'AdapterInitializationError',
	'AdapterConfigurationError', 'ProgrammingError', 'AccessDeniedError']

from gnue.common.apps import errors, plugin

# =============================================================================
# Public functions
# =============================================================================

# -----------------------------------------------------------------------------
# Attach to a client driver
# -----------------------------------------------------------------------------

def attach (interface, params):
	"""
	Create a new ClientAdapter of a given rpc driver.

	@param interface: name of the driver to create a L{drivers.Base.Client}
	instance for
	@param params: dictionary of parameters to pass to the ClientAdapter

	@return: a L{drivers.Base.ServerProxy} instance ready for accessing the
	  remote RPC server.
	"""

	checktype (interface, basestring)
	checktype (params, dict)

	driver = plugin.find (interface, 'gnue.common.rpc.drivers', 'ClientAdapter')
	return driver.ClientAdapter (params).getServerProxy ()


# =============================================================================
# Exceptions
# =============================================================================

# -----------------------------------------------------------------------------
# Requested adapter does not exist
# -----------------------------------------------------------------------------

class InvalidAdapter (errors.AdminError):
	pass

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
# A client application requested a service that is not
# exposed by the server.
# -----------------------------------------------------------------------------

class InvalidService (ProgrammingError):
	pass

# -----------------------------------------------------------------------------
# An invalid parameter was passed to a RPC
# -----------------------------------------------------------------------------

class InvalidParameter (ProgrammingError):
	pass

class AccessDeniedError (errors.AdminError):
	def __init__ (self, host):
		msg = u_("Access to services at '%s' denied") % host
		errors.AdminError.__init__ (self, msg)


# =============================================================================
# Self test code - requires server.py running
# =============================================================================

if __name__ == '__main__':

	import traceback
	import sys
	from gnue.common.apps import errors
	import datetime
	import mx.DateTime

	if len (sys.argv) >= 2 and \
		sys.argv [1] in ['pyro', 'xmlrpc', 'socket', 'soap']:
		host = len (sys.argv) > 2 and sys.argv [2] or 'localhost'
		port = len (sys.argv) > 3 and sys.argv [3] or 8765

		obj  = attach (sys.argv [1], {'host': host, 'port': port})
	else:
		print "GNUe RPC test client\n\nUsage: gcvs client.py <transport>"
		sys.exit (1)


	print 'stringtest:', repr (obj.stringtest ('This'))

	try:
		print 'ustringtest:', \
			(obj.ustringtest (u'\xe0\xe2\xe1\xe4')).encode ('utf-8')
	except:
		print "UnicodeStringtest failed"

	print 'inttest: 21 * 2 =', repr (obj.inttest (21))
	print 'floattest: 123.45 * 2 =', repr (obj.floattest (123.45))
	print 'datetimetest:', repr (obj.datetimetest ())
	print 'booltest:', repr (obj.booltest ())

	subobj = obj.objtest ()
	print 'objtest:', repr (subobj)
	print 'subobj.test', subobj.test ()

	subobj.setName ('Foobar')
	print "Subobj.printIt () ==", subobj.printIt ()

	print 'testing exception ...'

	try:
		obj.exceptiontest ()

	except Exception, e:
		print "-" * 70
		if isinstance (e, errors.gException):
			print "Exception Group:", e.getGroup ()
			print "Exception Name :", e.getName ()
			print "Message        :", e.getMessage ()
		else:
			print "Exception:", e

		print "-" * 70
		print "local traceback:"
		traceback.print_exc ()

		if isinstance (e, errors.gException):
			print "-" * 70
			print "remote exception detail:", e.getDetail ()
			print "-" * 70

	print "-" * 70
	o = None
	print "Sending %r (%s) to a roundtrip ..." % (o, type (o))
	v = obj.roundtrip (o)
	print "Result:", repr (v), type (v)

	o = {None: 'foobar', u'Unicode-Key': 2,
		'int': 2, 'long': 3L, 'float': 2.34, 'False': False,
		'True': True, 'None': None, 'tuple': ('a', 2), 'list': ['b', 3],
		'date': datetime.date.today (),
		'time': datetime.datetime.today ().time (),
		'datetime': datetime.datetime.today (),
		'mx.DateTime': mx.DateTime.now (),
		'mx.DateTimeDelta': mx.DateTime.DateTimeDelta (0, 1, 2, 3.456)}
	print "Sending %r (%s) to a roundtrip ..." % (o, type (o))
	v = obj.roundtrip (o)
	print "Result:", repr (v), type (v)

	other = obj.objtest ('barbaz')
	print "Other object:", other.printIt ()

	res = subobj.argcheck (other)
	print "subobj.argcheck (other)", res

	print "<enter>"
	raw_input ()

	res = subobj.dictcheck (other, {'buddy': other})
	print "Result-Object (buddy)=", res.printIt ()

	print "removing result", res
	del res
	raw_input ()

	print "removing subobj", subobj
	del subobj
	raw_input ()

	print "removing other:", other
	del other
	raw_input ()

	print 'shutting down server ...'
	try:
		# This will raise an exception because the server will not even answer any
		# more. Need to find a better way to shutdown the server.
		obj.shutdown ()
	except:
		pass

	del obj
