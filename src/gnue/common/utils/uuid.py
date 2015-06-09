# GNU Enterprise Common - Utilities - UUID generator
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
# $Id: uuid.py 9222 2007-01-08 13:02:49Z johannes $
#
# pylint: disable-msg=W0703
# pylint: disable-msg=F0401
"""
This module implements an UUID generator as described in the internet draft at
'http://www.ietf.org/internet-drafts/draft-mealling-uuid-urn-05.txt' or also
described in the RPC-RFC.
"""

import sys
import os
import os.path
import random
import array
import threading
import time
from hashlib import md5
import sha
import socket
import struct

from gnue.common.apps import errors

if sys.platform == 'win32':
	from win32com.client import GetObject
else:
	import fcntl


# Namespace available if imported all (from uuid import *)
__all__ = ['InvalidVersionError', 'InvalidNamespaceError',
	'MissingNamespaceError', 'get_hardware_addresses', 'Generator',
	'UUID', 'TIME', 'MD5', 'RANDOM', 'SHA1']

# =============================================================================
# Exceptions
# =============================================================================

class InvalidVersionError(errors.SystemError):
	"""
	The version '<version>' is not a valid UUID version.

	Raised when L{Generator.generate}() gets called with an invalid
	UUID-version.
	"""
	def __init__(self, version):
		msg = u_("The version '%s' is not a valid UUID version") \
			% repr(version)
		errors.SystemError.__init__(self, msg)

# =============================================================================

class InvalidNamespaceError(errors.SystemError):
	"""
	'namespace' is not recognized as valid namespace argument.

	Raised whenever an invalid namespace is given to L{Generator.set_namespace}.
	A valid namespace for name-based UUID generation is made up of either 36 or
	32 characters.
	"""
	def __init__(self, namespace):
		msg = u_("'%s' is not recognized as valid namespace argument") \
			% repr(namespace)
		errors.SystemError.__init__(self, msg)

# =============================================================================

class MissingNamespaceError(errors.ApplicationError):
	"""
	No namespace given for SHA1-/MD5-based UUIDs.

	MD5- and SHA1-based UUIDs must have a namespace defined. Use
	L{Generator.set_namespace} to define this value.
	"""
	def __init__(self):
		msg = u_("No namespace given for namebased UUID generation")
		errors.ApplicationError.__init__(self, msg)


# =============================================================================
# Implementation of a thread safe random number generator
# =============================================================================

dev_random = None
pseudoRng  = random.Random()
lock       = threading.Lock()
manualLock = sys.version_info[:2] < (2, 3)

if os.path.exists('/dev/urandom'):
	dev_random = os.open('/dev/urandom', os.O_RDONLY)


# -----------------------------------------------------------------------------
# Get a sequence of random bytes
# -----------------------------------------------------------------------------

def get_random_bytes(count):
	"""
	Return a sequence of 'count' random bytes from the best random number
	generator available.

	@param count: number of bytes to return
	@type count: integer
	@return: sequence of 'count' random bytes
	@rtype: list
	"""

	result = []

	# If there's a random device we prefer this source
	if dev_random is not None:
		lock.acquire()

		while len(result) < count:
			rdata = os.read(dev_random, count - len(result))
			result.extend(array.array('B', rdata).tolist())

		lock.release()

	# otherwise use the random module (which is threadsafe for python 2.3+)
	else:
		for dummy in xrange(count):
			if manualLock:
				lock.acquire()

			result.append(pseudoRng.randrange(0, 256))

			if manualLock:
				lock.release()

	return result


# =============================================================================
# Get the hardware addresses of the installed network interfaces
# =============================================================================

def get_hardware_addresses():
	"""
	Retrieve a list of all available network interfaces and their hardware
	addresses. After creating an instance of this class the attribute nics is a
	sequence of tuples (name, hwaddr, hwstr) where name is the name of the
	interface, hwaddr is a list of integers and hwstr is the string
	representation of the hardware-address.

	On systems identifying as 'linux2' the proc-filesystem will be searched for
	interface information first. If that fails (or isn't available) we try to
	get a list of interfaces via sockets.

	On OS X the NetworkInterfaces.plist will be examined.

	On win32 systems the Windows Management Instrumentation will be queried.

	If no interface could be detected at all, an interface will be generated
	using the random number source. It will have the name 'generated'.

	@return: list of tuples (ifname, hwaddr, hwstr) as described above
	@rtype: list of tuples
	"""

	trys = {'linux2': [_load_from_proc, _load_via_ifconf],
		'darwin': [_load_from_plist],
		'win32' : [_load_from_winmgmts]}

	nics = []
	if sys.platform in trys:
		for method in trys[sys.platform]:
			nics = [item for item in method() if sum(item[1])]
			if nics:
				break

	if not nics:
		nics = [('generated', get_random_bytes(6))]

	return [(name, hwaddr, ("%02x:" * 6)[:-1] % tuple(hwaddr)) \
			for (name, hwaddr) in nics]



# -------------------------------------------------------------------------
# Load a list of interfaces from the proc-filesystem
# -------------------------------------------------------------------------

def _load_from_proc():
	"""
	Load a list of network-interfaces from the proc-filesystem (/proc/net/dev).
	For each interface a tuple with it's name and hardware address will be
	returned. The hardware address is a list of decimal numbers.

	@return: list of tuples (ifname, hwaddr)
	@rtype: list of tuples
	"""

	result = []
	try:
		nfhd = open('/proc/net/dev', 'r')

		try:
			for line in [raw.strip() for raw in nfhd.readlines() \
					if ':' in raw]:
				result.append(line.split(':', 1)[0])

		finally:
			nfhd.close()

		result = [(name, _hw_addr_from_socket(name)) \
				for name in result]

	except IOError:
		result = []

	return result


# -------------------------------------------------------------------------
# Load a list of interfaces via IFCONF socket call
# -------------------------------------------------------------------------

def _load_via_ifconf():
	"""
	Load a list of network-interfaces using a SIOCGIFCONF (0x8912) socket
	IO-call.  For each interface a tuple with it's name and hardware address
	will be returned.  The hardware address is a list of decimal numbers.

	@return: list of tuples (ifname, hwaddr)
	@rtype: list of tuples
	"""

	SIOCGIFCONF = 0x8912
	result = []

	try:
		sfhd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		try:
			dbuf = array.array('c', '\0' * 1024)
			(addr, length) = dbuf.buffer_info()
			ifconf = struct.pack("iP", length, addr)
			data = fcntl.ioctl(sfhd.fileno(), SIOCGIFCONF, ifconf)

			size = struct.unpack("iP", data)[0]
			for idx in range(0, size, 32):
				ifconf = dbuf.tostring()[idx:idx+32]
				name = struct.unpack("16s16s", ifconf)[0].split('\0', 1)[0]
				result.append(name)

		finally:
			sfhd.close()

		result = [(name, _hw_addr_from_socket(name)) for name in result]

	except Exception:
		result = []

	return result


# -------------------------------------------------------------------------
# Get a hardware address for an interface using a socket
# -------------------------------------------------------------------------

def _hw_addr_from_socket(iff):
	"""
	Get the hardware address for a given interface name using the socket
	IO-call SIOCGIFHWADDR (0x8927).  The hardware address will be returned as a
	list of bytes.

	@param iff: name of the interface to get the hardware address for
	@type iff: string
	@return: hardware address of the requested interface
	@rtype: list of 6 bytes
	"""

	SIOCGIFHWADDR = 0x8927
	sfhd  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	ifreq = (iff + '\0' * 32)[:32]

	try:
		data   = fcntl.ioctl(sfhd.fileno(), SIOCGIFHWADDR, ifreq)
		result = array.array('B', data[18:24]).tolist()

	finally:
		sfhd.close()

	return result


# -------------------------------------------------------------------------
# Get a list of interfaces using the windows management instrumentation
# -------------------------------------------------------------------------

def _load_from_winmgmts():
	"""
	Load a list of network-interfaces using the windows management
	instrumentation.  This assumes to have the win32 modules installed.  For
	each interface a tuple with it's name and hardware address will be
	returned.  The hardware address is a list of bytes.

	@return: list of tuples (ifname, hwaddr)
	@rtype: list of tuples
	"""

	result = []
	try:
		cmd = "SELECT * FROM Win32_NetworkAdapterConfiguration " \
			"WHERE IPEnabled=True"
		for iff in [intf for intf in GetObject('winmgmts:').ExecQuery(cmd)]:
			parts = iff.MACAddress.split(':')
			result.append((iff.Caption, \
						[int(value, 16) for value in parts]))

	except Exception:
		result = []

	return result


# -------------------------------------------------------------------------
# Load the network information from the NetworkInterfaces.plist XML file
# -------------------------------------------------------------------------

def _load_from_plist():
	"""
	Load a list of network-interfaces from the NetworkInterfaces preference
	file (/Library/Preferences/SystemConfiguration/NetworkInterfaces.plist).
	For each interface a tuple with it's name and hardware address will be
	returned.  The hardware address is a list of bytes.

	@return: list of tuples (ifname, hwaddr)
	@rtype: list of tuples
	"""

	result = []
	try:
		import plistlib
		path = "/Library/Preferences/SystemConfiguration/" \
			"NetworkInterfaces.plist"

		pref = plistlib.Plist.fromFile(path)
		for iff in pref.Interfaces:
			name = iff ['BSD Name']
			hwaddr = [ord(char) for char in iff.IOMACAddress.data]

			# FireWire devices seem to have longer hardware addresses which
			# are theirfore not usable for UUID generation.
			if len(hwaddr) == 6:
				result.append((name, hwaddr))

	except Exception:
		result = []

	return result



# =============================================================================
# This class implements an UUID generator
# =============================================================================

TIME   = 1
MD5    = 3
RANDOM = 4
SHA1   = 5

class Generator:
	"""
	This class implements an UUID generator described in the internet draft at
	'http://www.ietf.org/internet-drafts/draft-mealling-uuid-urn-05.txt' or
	also described in the RPC-RFC.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, version=TIME, namespace=None):

		self.version = version
		self.__lastTime = None
		self.__clockSeq = int("%02x%02x" % tuple(get_random_bytes(2)), 16)
		self.__clockField = self.__clockSeq & 0x3FFF | 0x8000
		self.__namespace = None

		if namespace is not None:
			self.set_namespace(namespace)

		self.__timeFormat = u"%016x%04x%s"
		self.__randFormat = u"%02x" * 16
		self.__hashFormat = u"%08x%04x%04x" + "%02x" * 8
		self.__currNode   = "%02x" * 6 % tuple(get_hardware_addresses()[0][1])
		self.__uuids_per_tick = 0


	# -------------------------------------------------------------------------
	# Generate a new UUID
	# -------------------------------------------------------------------------

	def generate(self, version=None, namespace=None, name=None):
		"""
		This function calls the appropriate method to generate a new UUID. If
		you're about to create a lot of id's in a short time, you're better off
		using the proper fucntion directly.

		@param version: if set generate an id of this version
		@param namespace: if version is currently MD5 or SHA1 this parameter
		  defines the namespace to use. Alternatively one can use
		  set_namespace()
		@param name: if version is MD5 or SHA1 this parameter specifies the
		  name to encode

		@return: UUID as 32 character unicode string
		"""

		vers = version or self.version

		if vers == TIME:
			return self.generate_time_based()

		elif vers == RANDOM:
			return self.generate_random()

		elif vers == MD5:
			return self.generate_md5(name, namespace)

		elif vers == SHA1:
			return self.generate_sha1(name, namespace)

		else:
			raise InvalidVersionError, version


	# -------------------------------------------------------------------------
	# Generate a time-based UUID
	# -------------------------------------------------------------------------

	def generate_time_based(self):
		"""
		Create a time-based UUID.

		@return: UUID (as 32 character unicode string)
		"""

		lock.acquire()

		timeStamp = long(time.time() * 10000000) + 122192928000000000L
		if timeStamp != self.__lastTime:
			self.__uuids_per_tick = 0

			# If the time has been set backward, we change the clock sequence
			if timeStamp < self.__lastTime:
				self.__clockSeq += 1
				if self.__clockSeq > 0xFFFF:
					self.__clockSeq = 0

				self.__clockField = self.__clockSeq & 0x3FFF | 0x8000

			self.__lastTime = timeStamp

		else:
			self.__uuids_per_tick += 1
			timeStamp += self.__uuids_per_tick

		lock.release()

		timeField = timeStamp & 0x0FFFFFFFFFFFFFFFF | 0x1000000000000000

		return self.__timeFormat % (timeField, self.__clockField,
			self.__currNode)


	# -------------------------------------------------------------------------
	# Generate an UUID from pseudo random numbers
	# -------------------------------------------------------------------------

	def generate_random(self):
		"""
		This function generates an UUID from pseudo random numbers

		@return: UUID (as 32 character unicode string)
		"""

		data = get_random_bytes(16)
		# Set the two most significant bits (bits 6, 7) of the
		# clock_seq_hi_and_reserved to zero and one
		data[8] = data[8] & 0x3F | 0x80

		# Multiplex the most significant bits of time_hi_and_version with 4
		data[6] = data[6] | 0x40

		return self.__randFormat % tuple(data)


	# -------------------------------------------------------------------------
	# Generate a name-based UUID using an MD5 hash
	# -------------------------------------------------------------------------

	def generate_md5(self, name, namespace=None):
		"""
		Generate a name based UUID using a MD5 hash.

		@return: UUID (as 32 character unicode string)
		"""

		if namespace is not None:
			self.set_namespace(namespace)

		if self.__namespace is None:
			raise MissingNamespaceError

		digest = md5(self.__namespace)
		if name is not None:
			digest.update(name)

		return unicode(digest.hexdigest())


	# -------------------------------------------------------------------------
	# Generate an UUID using a SHA1 hash
	# -------------------------------------------------------------------------

	def generate_sha1(self, name, namespace=None):
		"""
		Generate a name based UUID using a SHA1 hash.

		@return: UUID (as 32 character unicode string)
		"""

		if namespace is not None:
			self.set_namespace(namespace)

		if self.__namespace is None:
			raise MissingNamespaceError

		digest = sha.new(self.__namespace)
		if name is not None:
			digest.update(name)

		return unicode(digest.hexdigest()[:32])


	# -------------------------------------------------------------------------
	# Set the namespace to be used for name based UUIDs
	# -------------------------------------------------------------------------

	def set_namespace(self, new_ns):
		"""
		Set the namespace used for name based UUID generation.
		"""

		if isinstance(new_ns, basestring):
			if len(new_ns) == 36:
				new_ns = "".join(new_ns.split('-'))

			elif len(new_ns) != 32:
				raise InvalidNamespaceError(new_ns)

			parts = [new_ns[:8], new_ns[8:12], new_ns[12:16], new_ns[16:]]

			timeLow = socket.htonl(long(parts[0], 16))
			timeMid = socket.htons(int(parts[1], 16))
			timeHi  = socket.htons(int(parts[2], 16))
			rest    = [int(parts[3][inx:inx+2], 16) for inx in range(0, 16, 2)]

			self.__namespace = struct.pack('>LHH8B', timeLow, timeMid, timeHi,
				rest[0], rest[1], rest[2],rest[3],rest[4],rest[5],
				rest[6], rest[7])

		else:
			raise InvalidNamespaceError(new_ns)


# Create a ready-to-use instance of the UUID generator
UUID = Generator()


# =============================================================================
# Unit-Test
# =============================================================================

if __name__ == '__main__':

	for i in range(5):
		print "Time-Base:", repr(UUID.generate_time_based())

	for i in range(5):
		print "Random   :", repr(UUID.generate_random())

	UUID.set_namespace('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
	print "Namespace: '6ba7b810-9dad-11d1-80b4-00c04fd430c8'"
	print "Encoding : 'www.gnuenterprise.org'"
	print "MD5      :", repr(UUID.generate_md5('www.gnuenterprise.org'))
	print "SHA1     :", repr(UUID.generate_sha1('www.gnuenterprise.org'))

	print "T:", repr(UUID.generate(version = TIME))
	print "R:", repr(UUID.generate(version = RANDOM))
	print "M:", repr(UUID.generate(version = MD5, name = 'foobar'))
	print "S:", repr(UUID.generate(version = SHA1, name = 'foobar'))
