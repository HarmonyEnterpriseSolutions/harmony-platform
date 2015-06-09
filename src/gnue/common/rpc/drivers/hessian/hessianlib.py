# Credits: hessianlib.py was inspired by and based on
# xmlrpclib.py created by Fredrik Lundh at www.pythonware.org

import time, operator

from types import *
from struct import unpack, pack

from cStringIO import StringIO

# --------------------------------------------------------------------
# Internal stuff
try:
	_bool_is_builtin = False.__class__.__name__ == "bool"
except NameError:
	_bool_is_builtin = 0

__version__ = "0.2"

# --------------------------------------------------------------------
# Exceptions

##
# Base class for all kinds of client-side errors.

class Error(Exception):
	"""Base class for client errors."""
	def __str__(self):
		return repr(self)

##
# Indicates an HTTP-level protocol error.  This is raised by the HTTP
# transport layer, if the server returns an error code other than 200
# (OK).
#
# @param url The target URL.
# @param status Status code returned by server.
# @param reason Reason phrase returned by server.
# @param msg A mimetools.Message instance containing the response headers.

class ProtocolError(Error):
	"""Indicates an HTTP protocol error."""
	def __init__(self, url, status, reason, msg):
		Error.__init__(self)
		self.url = url
		self.status = status
		self.reason = reason
		self.msg = msg
	def __repr__(self):
		return (
			"<ProtocolError for %s: %s %s>" %
			(self.url, self.status, self.reason)
		)

##
# Indicates a broken Hessian response package.  This exception is
# raised by the unmarshalling layer, if the Hessian response is
# malformed.

class ResponseError(Error):
	"""Indicates a broken response package."""
	pass

##
# Indicates an Hessian fault response package.  This exception is
# raised by the unmarshalling layer, if the Hessian response contains
# a fault.  This exception can also used as a class,
# to generate a fault Hessian message.
#
# @param code The Hessian fault code.
# @param message The Hessian fault string.

class Fault(Error):
	"""Indicates an Hessian fault package."""
	def __init__(self, code, message, **detail):
		Error.__init__(self)
		self.code = code
		self.message = message
	def __repr__(self):
		return (
			"<Fault %s: %s>" %
			(self.code, repr(self.message))
		)

# --------------------------------------------------------------------
# Special values

##
# Wrapper for Hessian boolean values.  Use the hessianlib.True and
# hessianlib.False constants to generate boolean Hessian values.
#
# @param value A boolean value.  Any true value is interpreted as True,
#              all other values are interpreted as False.

if _bool_is_builtin:
	boolean = Boolean = bool
	True, False = True, False
else:
	class Boolean:
		"""Boolean-value wrapper.

		Use True or False to generate a "boolean" Hessian value.
		"""

		def __init__(self, value=0):
			self.value = operator.truth(value)

		def __cmp__(self, other):
			if isinstance(other, Boolean):
				other = other.value
			return cmp(self.value, other)

		def __repr__(self):
			if self.value:
				return "<Boolean True at %x>" % id(self)
			else:
				return "<Boolean False at %x>" % id(self)

		def __int__(self):
			return self.value

		def __nonzero__(self):
			return self.value

		def encode(self, out):
			if self.value:
				out.append("T")
			else:
				out.append("F")

	True, False = Boolean(1), Boolean(0)

	##
	# Map true or false value to Hessian boolean values.
	#
	# @def boolean(value)
	# @param value A boolean value.  Any true value is mapped to True,
	#              all other values are mapped to False.
	# @return hessianlib.True or hessianlib.False.
	# @see Boolean
	# @see True
	# @see False

	def boolean(value, _truefalse=(False, True)):
		"""Convert any Python value to Hessian 'boolean'."""
		return _truefalse[operator.truth(value)]

##
# Wrapper for Hessian DateTime values.  This converts a time value to
# the format used by Hessian.
# <p>
# The value must be given as the number of seconds since epoch (UTC).

class DateTime:
	"""DateTime wrapper for a datetime integer value
	to generate Hessian value.
	"""

	def __init__(self, value=0):
		self.value = int(value)

	def __cmp__(self, other):
		if isinstance(other, DateTime):
			other = other.value
		return cmp(self.value, other)

	def __str__(self):
		return time.strftime("%Y-%m-%d %H:%M:%S", self.timetuple())

	def __repr__(self):
		return "<DateTime %s at %x>" % (self, id(self))

	def timetuple(self):
		return time.gmtime(self.value)

	def encode(self, out):
		out.append("d")
		out.append(pack(">q", self.value * 1000))

##
# Wrapper for binary data.  This can be used to transport any kind
# of binary data over Hessian.
#
# @param data Raw binary data.

class Binary:
	"""Wrapper for binary data."""

	def __init__(self, data=None):
		self.data = data

	def __cmp__(self, other):
		if isinstance(other, Binary):
			other = other.data
		return cmp(self.data, other)

	def __repr__(self):
		return "<Binary at %x>" % (id(self))

	def encode(self, out):
		out.append("B")
		out.append(pack(">H", len(self.data)))
		out.append(self.data)

WRAPPERS = (DateTime, Binary)
if not _bool_is_builtin:
	WRAPPERS = WRAPPERS + (Boolean,)

# --------------------------------------------------------------------
# Hessian marshalling and unmarshalling code

##
# Hessian marshaller.
#
# @see dumps

class Marshaller:
	"""Generate an Hessian params chunk from a Python data structure.

	Create a Marshaller instance for each set of parameters, and use
	the "dumps" method to convert your data (represented as a tuple)
	to an Hessian params chunk.  To write a fault response, pass a
	Fault instance instead.  You may prefer to use the "dumps" module
	function for this purpose.
	"""

	def __init__(self):
		self.stack = []
		self.append = self.stack.append #write

	dispatch = {}

	def dumps(self, values):
		if isinstance(values, Fault):
			# fault instance
			self.append("f")
			self.dump("code")
			self.dump(values.code)
			self.dump("message")
			self.dump(values.message)
		else:
			for v in values:
				self.dump(v)
		result = "".join(self.stack)
		del self.append, self.stack
		return result

	def dump(self, value):
		try:
			func = self.dispatch[type(value)]
			func(self, value)
		except KeyError:
			raise TypeError, "cannot marshal %s objects" % type(value)

	def dump_nil (self, value):
		self.append("N")
	dispatch[NoneType] = dump_nil

	if _bool_is_builtin:
		def dump_bool(self, value):
			self.append(value and "T" or "F")
		dispatch[bool] = dump_bool

	def dump_int(self, value):
		self.append("I")
		self.append(pack(">l", value))
	dispatch[IntType] = dump_int

	def dump_long(self, value):
		self.append("L")
		self.append(pack(">q", value))
	dispatch[LongType] = dump_long

	def dump_double(self, value):
		self.append("D")
		self.append(pack(">d", value))
	dispatch[FloatType] = dump_double

	def dump_string(self, value):
		self.append("S")
		self.append(pack(">H", len(value)))
		self.append(value)
	dispatch[StringType] = dump_string

	def dump_unicode(self, value):
		value = value.encode("utf-8")
		self.append("S")
		self.append(pack(">H", len(value)))
		self.append(value)
	dispatch[UnicodeType] = dump_unicode

	def dump_array(self, value):
		self.append("V")
		for v in value:
			self.dump(v)
		self.append("z")
	dispatch[TupleType] = dump_array
	dispatch[ListType] = dump_array

	def dump_struct(self, value):
		self.append("M")
		for k, v in value.items():
			if type(k) not in (StringType, UnicodeType):
				raise TypeError, "dictionary key must be string"
			self.dump(k)
			self.dump(v)
		self.append("z")
	dispatch[DictType] = dump_struct

	def dump_instance(self, value):
		# check for special wrappers
		if value.__class__ in WRAPPERS:
			value.encode(self)
		else:
			# store instance attributes as a struct (really?)
			self.dump_struct(value.__dict__)
	dispatch[InstanceType] = dump_instance

##
# Hessian unmarshaller.
#
# @see loads

class Unmarshaller:
	"""Unmarshal an Hessian response. Call close() to get the resulting
	data structure.
	"""

	def __init__(self):
		self.stack = []
		self.append = self.stack.append #write
		self.typ = None
		self.method = None

	dispatch = {}

	def loads(self, data):
		data = StringIO(data)
		typ = data.read(1)
		if typ in ("c", "r"):
			major = data.read(1)
			minor = data.read(1)
			typ = data.read(1)
		while typ not in ("z", ""):
			self.load(typ, data)
			typ = data.read(1)
		data.close()

	def load(self, typ, data):
		if typ in ("m", "f"):
			self.__load(typ, data)
		else:
			self.append(self.__load(typ, data))

	def __load(self, typ, data):
		try:
			func = self.dispatch[typ]
			return func(self, data)
		except KeyError:
			raise TypeError, "cannot unmarshal %s objects" % typ

	def close(self):
		if self.typ == "f":
			raise Fault(**self.stack[0])
		result = tuple(self.stack)
		del self.append, self.stack
		return result

	def getmethodname(self):
		return self.method

	dispatch = {}

	def load_nil (self, data):
		return None
	dispatch["N"] = load_nil

	def load_true(self, data):
		return True
	dispatch["T"] = load_true

	def load_false(self, data):
		return False
	dispatch["F"] = load_false

	def load_int(self, data):
		return unpack(">l", data.read(4))[0]
	dispatch["I"] = load_int

	def load_long(self, data):
		return unpack(">q", data.read(8))[0]
	dispatch["L"] = load_long

	def load_double(self, data):
		return unpack(">d", data.read(8))[0]
	dispatch["D"] = load_double

	def load_string(self, data):
		res = data.read(unpack(">H", data.read(2))[0]).decode("utf-8")
		try:
			return res.encode("ascii")
		except UnicodeError:
			return res
	dispatch["S"] = load_string

	def load_array(self, data):
		res = []
		typ = data.read(1)
		while typ != "z":
			res.append(self.__load(typ, data))
			typ = data.read(1)
		return res
	dispatch["V"] = load_array

	def load_struct(self, data):
		res = {}
		typ = data.read(1)
		while typ != "z":
			k = self.__load(typ, data)
			v = self.__load(data.read(1), data)
			res[k] = v
			typ = data.read(1)
		return res
	dispatch["M"] = load_struct

	def load_binary(self, data):
		return Binary(data.read(unpack(">H", data.read(2))[0]))
	dispatch["B"] = load_binary

	def load_datetime(self, data):
		return DateTime(unpack(">q", data.read(8))[0] / 1000)
	dispatch["d"] = load_datetime

	def load_fault(self, data):
		fault = {}
		typ = data.read(1)
		while typ != "z":
			k = self.__load(typ, data)
			v = self.__load(data.read(1), data)
			fault[k] = v
			typ = data.read(1)
		self.stack = [fault]
		self.typ = "f"
	dispatch["f"] = load_fault

	def load_method(self, data):
		res = data.read(unpack(">H", data.read(2))[0]).decode("utf-8")
		try:
			self.method = res.encode("ascii")
		except UnicodeError:
			self.method = res
	dispatch["m"] = load_method

## Multicall support
#

class _MultiCallMethod:
	# some lesser magic to store calls made to a MultiCall object
	# for batch execution
	def __init__(self, call_list, name):
		self.__call_list = call_list
		self.__name = name
	def __getattr__(self, name):
		return _MultiCallMethod(self.__call_list, "%s.%s" % (self.__name, name))
	def __call__(self, *args):
		self.__call_list.append((self.__name, args))

class MultiCallIterator:
	"""Iterates over the results of a multicall. Exceptions are
	thrown in response to hessian faults."""

	def __init__(self, results):
		self.results = results

	def __getitem__(self, i):
		item = self.results[i]
		if type(item) == type({}):
			raise Fault(item["code"], item["message"])
		elif type(item) == type([]):
			return item[0]
		else:
			raise ValueError,\
				"unexpected type in multicall result"

class MultiCall:
	"""server -> a object used to boxcar method calls

	server should be a ServerProxy object.

	Methods can be added to the MultiCall using normal
	method call syntax e.g.:

	multicall = MultiCall(server_proxy)
	multicall.add(2,3)
	multicall.get_address("Guido")

	To execute the multicall, call the MultiCall object e.g.:

	add_result, address = multicall()
	"""

	def __init__(self, server):
		self.__server = server
		self.__call_list = []

	def __repr__(self):
		return "<MultiCall at %x>" % id(self)

	__str__ = __repr__

	def __getattr__(self, name):
		return _MultiCallMethod(self.__call_list, name)

	def __call__(self):
		marshalled_list = []
		for name, args in self.__call_list:
			marshalled_list.append({"methodName" : name, "params" : args})

		return MultiCallIterator(self.__server.system.multicall(marshalled_list))

# --------------------------------------------------------------------
# convenience functions

##
# Convert a Python tuple or a Fault instance to an Hessian packet.
#
# @def dumps(params, **options)
# @param params A tuple or Fault instance.
# @keyparam methodname If given, create a call request for
#     this method name.
# @keyparam methodresponse If given, create a reply packet.
#     If used with a tuple, the tuple must be a singleton (that is,
#     it must contain exactly one element).
# @return A string containing marshalled data.

def dumps(params, methodname=None, methodresponse=None):
	"""data [,options] -> marshalled data

	Convert an argument tuple or a Fault instance to an Hessian
	request (or response, if the methodresponse option is used).

	In addition to the data object, the following options can be given
	as keyword arguments:

	@param methodname: the method name for a call packet
	    Unicode strings are automatically converted, where necessary.

	@param methodresponse: true to create a reply packet.
	    If this option is used with a tuple, the tuple must be
	    a singleton (i.e. it can contain only one element).
	"""

	assert isinstance(params, TupleType) or isinstance(params, Fault),\
		"argument must be tuple or Fault instance"

	if isinstance(params, Fault):
		methodresponse = 1
	elif methodresponse and isinstance(params, TupleType):
		assert len(params) == 1, "response tuple must be a singleton"

	m = Marshaller()
	data = m.dumps(params)

	# standard Hessian wrappings
	if methodname:
		if isinstance(methodname, UnicodeType):
			methodname = methodname.encode("utf-8")
		data = ("c\x01\x00m", pack(">H", len(methodname)), methodname, data, "z")
	elif methodresponse:
		# a method response, or a fault structure
		data = ("r\x01\x00", data, "z")
	else:
		return data # return as is
	return "".join(data)

##
# Convert an Hessian packet to a Python object.  If the Hessian packet
# represents a fault condition, this function raises a Fault exception.
#
# @param data An Hessian.
# @return A tuple containing the unpacked data, and the method name
#     (None if not present).
# @see Fault

def loads(data):
	"""data -> unmarshalled data, method name

	Convert an Hessian packet to unmarshalled data plus a method
	name (None if not present).

	If the Hessian packet represents a fault condition, this function
	raises a Fault exception.
	"""
	u = Unmarshaller()
	u.loads(data)

	return u.close(), u.getmethodname()


# --------------------------------------------------------------------
# request dispatcher

class _Method:
	# some magic to bind an Hessian method to an RPC server.
	# supports "nested" methods (e.g. examples.getStateName)
	def __init__(self, send, name):
		self.__send = send
		self.__name = name
	def __getattr__(self, name):
		return _Method(self.__send, "%s.%s" % (self.__name, name))
	def __call__(self, *args):
		return self.__send(self.__name, args)

##
# Standard transport class for Hessian over HTTP.
# <p>
# You can create custom transports by subclassing this method, and
# overriding selected methods.

class Transport:
	"""Handles an HTTP transaction to an Hessian server."""

	# client identifier (may be overridden)
	user_agent = "hessianlib.py/%s" % __version__

	def __init__ (self):
		self.__connection = None

	##
	# Send a complete request, and parse the response.
	#
	# @param host Target host.
	# @param handler Target PRC handler.
	# @param request_body Hessian request body.
	# @param verbose Debugging flag.
	# @return Parsed response.

	def request(self, host, handler, request_body, verbose=0):
		if not self.__connection:
			self.__connection = self.make_connection(host)
		self.__connection.set_debuglevel (verbose)
		self.__connection.request ("POST", handler, request_body)
		response = self.__connection.getresponse ()
		if response:
			if response.status != 200:
				raise ProtocolError (host + handler, response.status,
					response.reason, response.msg)
			u = Unmarshaller()
			u.loads(response.read())
			result = u.close()
		else:
			result = None
		return result

	##
	# Connect to server.
	#
	# @param host Target host.
	# @return A connection handle.

	def make_connection(self, host):
		import httplib
		return httplib.HTTPConnection(host)

##
# Standard transport class for Hessian over HTTPS.

class SafeTransport(Transport):
	"""Handles an HTTPS transaction to an Hessian server."""

	# FIXME: mostly untested

	def make_connection(self, host):
		import httplib
		return httplib.HTTPSConnection(host)

##
# Standard server proxy.  This class establishes a virtual connection
# to an Hessian server.
# <p>
# This class is available as ServerProxy and Server.  New code should
# use ServerProxy, to avoid confusion.
#
# @def ServerProxy(uri, **options)
# @param uri The connection point on the server.
# @keyparam transport A transport factory, compatible with the
#    standard transport class.
# @keyparam verbose Use a true value to enable debugging output.
#    (printed to standard output).
# @see Transport

class ServerProxy:
	"""uri [,options] -> a logical connection to an Hessian server

	uri is the connection point on the server, given as
	scheme://host/target.

	The standard implementation always supports the "http" scheme.  If
	SSL socket support is available (Python 2.0), it also supports
	"https".

	If the target part and the slash preceding it are both omitted,
	"/Hessian" is assumed.

	The following options can be given as keyword arguments:

	transport: a transport factory
	"""

	def __init__(self, uri, transport=None, verbose=0):
		# establish a "logical" server connection

		# get the url
		import urllib
		type, uri = urllib.splittype(uri)
		if type not in ("http", "https"):
			raise IOError, "unsupported Hessian protocol"
		self.__host, self.__handler = urllib.splithost(uri)
		if not self.__handler:
			self.__handler = "/Hessian"

		if transport is None:
			if type == "https":
				transport = SafeTransport()
			else:
				transport = Transport()
		self.__transport = transport

		self.__verbose = verbose

	def __request(self, methodname, params):
		# call a method on the remote server

		request = dumps(params, methodname)

		response = self.__transport.request(
			self.__host,
			self.__handler,
			request,
			verbose=self.__verbose
		)

		if len(response) == 1:
			response = response[0]

		return response

	def __repr__(self):
		return (
			"<ServerProxy for %s%s>" %
			(self.__host, self.__handler)
		)

	__str__ = __repr__

	def __getattr__(self, name):
		# magic method dispatcher
		return _Method(self.__request, name)

# note: to call a remote object with an non-standard name, use
# result getattr(server, "strange-python-name")(args)

# compatibility

Server = ServerProxy

# --------------------------------------------------------------------
# test code

if __name__ == "__main__":

	server = ServerProxy("http://localhost:7000", verbose=1)

	try:
		print server.hello()
		print server.system.listMethods()
	except Error, v:
		print "ERROR", v

	server.raiseErr(42, "don't panic")
