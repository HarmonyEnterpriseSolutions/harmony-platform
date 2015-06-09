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
# xmlrpc/RpcDoc.py
#
# DESCRIPTION:
# Document a GRPC file for XML-RPC clients.
#
# NOTES:


import string
import sys
from gnue.common.rpc import server

# a global output file  (small hack, to be removed a soon as possible)
gloutfile=sys.stdout

def doc(outfile, command, *arguments):

	command = string.lower(command)


	if command == 'help':
		print """
GNUe RPC Documentation Generator

Module:   xmlrpc

Commands: doc       list all methods and objects in a .grpc file
          doc-py    create example code for all methods and objects
                    of the .grpc file in python
          doc-c     create example code for all methods and objects
                    of the .grpc file in c
          doc-php   create example code for all methods and objects
                    of the .grpc file in PHP
          js-stub   creates stub file to allow direct access to all methods
                    and objects defined in the .grpc file by an Javascript
                    client
          help      prints this help message
          
"""
		sys.exit()

	elif command == 'doc':

		try:
			rpcdef = server.loadDefinition(arguments[0])

		except IndexError:
			print o(u_("'doc' command expects a .grpc file as its argument."))
			sys.exit()

		gendoc(rpcdef, outfile)

	elif command == 'doc-py':

		try:
			rpcdef = server.loadDefinition(arguments[0])

		except IndexError:
			print o(u_("'doc' command expects a .grpc file as its argument."))
			sys.exit()

		gendocPy(rpcdef, outfile)

	elif command == 'doc-c':

		try:
			rpcdef = server.loadDefinition(arguments[0])

		except IndexError:
			print o(u_("'doc' command expects a .grpc file as its argument."))
			sys.exit()

		gendocC(rpcdef, outfile)

	elif command == 'doc-php':

		try:
			rpcdef = server.loadDefinition(arguments[0])

		except IndexError:
			print o(u_("'doc-php' command expects a .grpc file as its argument."))
			sys.exit()

		gendocPHP(rpcdef, outfile)

	elif command == 'js-stub':

		try:
			rpcdef = server.loadDefinition(arguments[0])

		except IndexError:
			print o(u_("'js-stub' command expects a .grpc file as its argument."))
			sys.exit()

		gendocJS(rpcdef, outfile)

	else:
		tmsg = u_("Unrecognized XML-RPC doc command: %s") % command
		raise StandardError, tmsg

##
##  Create normal documentation
##
def gendoc(rpcdef, outfile):

	outfile.write("XML-RPC Namespace\n")
	outfile.write("=================\n\n")
	gloutfile= outfile
	rpcdef.walk(_gen)


def _gen(object):
	if hasattr(object,'name'):
		name=object.name
		if hasattr(object,'_path'): # and hasattr(object._parent,'name'):
			name=object._path+'.'+name
	else:
		name=""

	if hasattr(object,'_children'):
		for child in object._children:
			child._path=name

	gloutfile.write(name[1:] + "\n")

##
##  Create python exsample
##
def gendocPy(rpcdef, outfile):

	outfile.write("## Python example\n")
	outfile.write("## ===============\n\n")
	outfile.write("params = { 'host': 'localhost',  # insert your local\n"+
		"           'port': 8765,         # values here\n"+
		"           'transport': 'http' }\n"+
		"rpcClient = geasRpcClient('xmlrpc',params)\n\n")
	gloutfile= outfile
	rpcdef.walk(_genPy)


def _genPy(object):
	if hasattr(object,'name'):
		name=object.name
		if hasattr(object,'_path'): # and hasattr(object._parent,'name'):
			name=object._path+'.'+name
	else:
		name=""

	if hasattr(object,'_children'):
		for child in object._children:
			child._path=name
	gloutfile.write("rpcClient.execute('%s')\n" % name[1:])


##
##  Create c example
##
def gendocC(rpcdef, outfile):

	outfile.write("XML-RPC Namespace\n")
	outfile.write("=================\n\n")
	gloutfile= outfile
	rpcdef.walk(_genC)


def _genC(object):
	if hasattr(object,'name'):
		name=object.name
	else:
		name=""
	gloutfile.write(name + "\n")

##
##  Create PHP example
##
php_XMLRPC_types = {'int4'     : '$xmlrpcI4',
	'integer'  : '$xmlrpcInt',
	'boolean'  : '$xmlrpcBoolean',
	'double'   : '$xmlrpcDouble',
	'string'   : '$xmlrpcString',
	'dateTime' : '$xmlrpcDateTime',
	'base64'   : '$xmlrpcBase64',
	'array'    : '$xmlrpcArray',
	'struct'   : '$xmlrpcStruct'}

def gendocPHP(rpcdef, outfile):

	outfile.write("<?php\n")
	outfile.write("// ***************************************\n")
	outfile.write("// XML-RPC Server Side Stubs\n")
	outfile.write("// ***************************************\n\n")
	outfile.write('include("xmlrpc.inc");\n')
	outfile.write('include("xmlrpcs.inc");\n\n')
	outfile.write("$server_def= array();\n")
	gloutfile= outfile
	rpcdef.walk(_genPHP)
	outfile.write("$s=new xmlrpc_server($server_def)\n?>\n")


def _genPHP(object):
	if hasattr(object,'name'):
		name=object.name
		if hasattr(object,'_path'): # and hasattr(object._parent,'name'):
			name=object._path+'_'+name
	else:
		name=""
	if object._type=="RpObject" or object._type=="RpService":
		gloutfile.write("// ***************************************\n")
		gloutfile.write("//   Service  %s \n" % name[1:])
		gloutfile.write("// ***************************************\n\n")
		if hasattr(object,'_children'):
			for child in object._children:
				child._path=name
				if child._type=="RpMethod" or child._type=="RpAttribute":
					_genPHP(child)
		gloutfile.write("\n")
		if hasattr(object,'_children'):
			for child in object._children:
				child._path=name
				if child._type=="RpObject" or child._type=="RpService":
					_genPHP(child)


	elif object._type=="RpGnuRpc":
		if hasattr(object,'_children'):
			for child in object._children:
				child._path=name
				_genPHP(child)


	elif object._type=="RpMethod":

		if hasattr(object,"return"):
			try:
				sign=php_XMLRPC_types[getattr(object,'return')]+","
			except KeyError:
				sign="$xmlrpcArray,"
		else:
			sign="Null,"


		# build attribut list
		attr=""
		delim=""
		if hasattr(object,'_children'):
			for child in object._children:
				attr=attr+delim+child.name
				try:
					sign=sign+delim+php_XMLRPC_types[child.type]
				except KeyError:
					sign=sign+delim+"$xmlrpcArray"

				delim=","
		# TODO: add return type

		gloutfile.write("// ***************************************\n")
		gloutfile.write("// function %s (%s) \n" % (object.name,attr) )
		gloutfile.write("// ***************************************\n\n")

		gloutfile.write("$%s_sign = array(array(%s));\n" % \
				(object.name,sign) )
		gloutfile.write("$server_def['%s']=\n" % object.name)
		gloutfile.write("   array('function' => '%s_func',\n" % object.name)
		gloutfile.write("         'signature' => $%s_sign,\n" % object.name)
		if hasattr(object,'helptext'):
			gloutfile.write("         'docstring' => '%s');\n\n" % object.helptext)
		else:
			gloutfile.write("         'docstring' => 'Some Procedure');\n\n")

		gloutfile.write("function %s_func ($message) {\n" % object.name )

		count=0
		if hasattr(object,'_children'):
			for child in object._children:
				gloutfile.write("    $%s=$message->getParam(%s);\n" % (child.name,\
							count))
				count+=1

		gloutfile.write("\n     /* Add your code here.*/\n\n");
		gloutfile.write("\n     error_log('function %s called',3,'/tmp/log');\n\n"\
				% object.name );

		procname=""

		ret="nothing"

		if hasattr(object,"return"):
			ret=getattr(object,"return")

		if ret[:1]=="<" and ret[-1:]==">":

			gloutfile.write("/*Return an object handle is not supported")
			gloutfile.write("         $s_stub = array(%s...);\n"
				% procname)
			gloutfile.write("         return new %s(host,handle)*/" %
				string.join(string.split(ret[1:-1],"."),"_"))

		elif ret=="nothing":
			gloutfile.write("    return new xmlrpcresp();\n")

		else:
			gloutfile.write("    return new xmlrpcresp(new xmlrpcval(result));\n")
			gloutfile.write("    // result should be of type %s\n" % ret)

		gloutfile.write("}\n")


##
##  Create Javascript exsample
##
def gendocJS(rpcdef, outfile):

	outfile.write("// Javascript example\n")
	outfile.write("// ==================\n\n")
	outfile.write("include ( 'vcXMLRPC.js')\n")

	gloutfile= outfile
	_genJs(rpcdef)


def _genJs(object):
	if hasattr(object,'name'):
		name=object.name
		if hasattr(object,'_path'): # and hasattr(object._parent,'name'):
			name=object._path+'_'+name
	else:
		name=""
	if object._type=="RpObject" or object._type=="RpService":
		gloutfile.write("function %s(host,handle) {\n" % name[1:])
		gloutfile.write("     this.host=host\n")
		gloutfile.write("     this.handle=handle\n")
		if hasattr(object,'_children'):
			for child in object._children:
				child._path=name
				if child._type=="RpMethod" or child._type=="RpAttribute":
					_genJs(child)
		gloutfile.write("}\n")
		if hasattr(object,'_children'):
			for child in object._children:
				child._path=name
				if child._type=="RpObject" or child._type=="RpService":
					_genJs(child)

	elif object._type=="RpGnuRpc":
		if hasattr(object,'_children'):
			for child in object._children:
				child._path=name
				_genJs(child)

	elif object._type=="RpMethod":
		# build attribut list
		attr=""
		delim=""
		if hasattr(object,'_children'):
			for child in object._children:
				attr=attr+delim+child.name
				delim=","

		gloutfile.write("     this.%s = function (%s) {\n" % (object.name,attr) )

		if object._parent._type=="RpObject":
			procname="'['+this.handle+'].%s'" % object.name
		else:
			procname="'%s'" % string.join(string.split(name[1:],"_"),".")

		if len(attr):
			procname=procname+","+attr

		ret="nothing"
		if hasattr(object,"return"):
			ret=getattr(object,"return")

		if ret[:1]=="<" and ret[-1:]==">":

			gloutfile.write("         handle=XMLRPC.call(this.host,%s);\n"
				% procname)
			gloutfile.write("         return new %s(host,handle)" %
				string.join(string.split(ret[1:-1],"."),"_"))

		else:
			gloutfile.write("         return XMLRPC.call(this.host,%s);\n"
				% procname)

		gloutfile.write("     }\n")



if __name__ == '__main__':
	if len(sys.argv)<2:
		print o(u_("RpcDoc.py has to be called with an command argument. "))
		print o(u_("call 'RpcDoc.py help' for more information."))
	else:
		doc(sys.stdout, *sys.argv[1:])
