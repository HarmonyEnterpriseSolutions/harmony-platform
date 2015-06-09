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
# Copyright 2001-2007 Free Software Foundation
#
# FILE:
# RpcDoc.py
#
# DESCRIPTION:
# Frontend to GnuRpc documentation commands.
#
# SYNTAX:
#
#  grpcdoc <module> <command> [ <grpc-file> [<output-file>] ]
#  grpcdoc <module> help
#  grpcdoc help
#


import sys, string
from gnue.common.utils.FileUtils import dyn_import

def run (interface, command, *arguments):
	try:
		commdriver = dyn_import("gnue.common.rpc.drivers.%s.RpcDoc" % (interface))
		commdriver.doc(sys.stdout,command, *arguments)
	except ImportError, err:
		print o(u_("GNUe RPC Documentation Generator"))
		print ""
		print o(u_("Error: the module %s does not exist or cannot be loaded") % \
				(interface))
		print ""

	return ""


def help():
	print """
GNUe RPC Documentation Generator

Description:
  grpcdoc generates documentation and IDLs based on an XML-based
  .grpc markup.

Syntax:
  grpcdoc <module> <command> [ <grpc-file> [<output-file>] ]
  grpcdoc <module> help
  grpcdoc help

Examples:

  1. To generate documentation on the exposed XML-RPC services, run:
        grpcdoc xmlrpc doc myapp.grpc

  2. To generate a CORBA IDL definition, run:
        grpcdoc corba idl myapp.grpc

  3. To see what commands are available for the soap module, run:
        grpcdoc soap help

"""



if __name__ == '__main__':

	if   len(sys.argv) < 2 or \
		string.lower(sys.argv[1]) == 'help' or \
		len(sys.argv) < 3:

		help()

	else:

		run(*sys.argv[1:])
