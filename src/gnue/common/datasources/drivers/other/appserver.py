# GNU Enterprise Datasource Library - GNUe-AppServer database driver
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
# $Id: appserver.py 9222 2007-01-08 13:02:49Z johannes $

"""
Database driver plugin for GNU Enterprise Application Server backends.
"""

__all__ = ['DriverInfo', 'Behavior', 'ResultSet', 'Connection']

import sys

from gnue.common.apps import errors, i18n
from gnue.common.rpc import client
from gnue.common.datasources import Exceptions, GSchema
from gnue.common.datasources.drivers import Base


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:

	name = "GNU Enterprise Application Server"

	url = "http://www.gnuenterprise.org/tools/appserver/"

	description = """
GNUe AppServer is GNUe's middleware for database access.
"""
	isfree = True

	doc = """
Description
-----------
Python driver GNUe Application Server.

Support
-------
POSIX Support: YES

Win32 Support: YES

Platforms Tested:

  - Linux/Unix (Debian, RedHat, SuSe, etc)
  - Windows NT/XP/2000

Connection Properties
---------------------
* host       -- This is the hostname/ip address of the host running AppServer (required)
* port       -- The port that AppServer is running on (required)
* timeout    -- Command timeout in seconds (optional)
* transport  -- Transport used for network connections (http, https) (required)
* rpctype    -- RPC driver used for network communication (xmlrpc, soap, etc.)
  See GNUe Common's RPC documentation for a list of all RPC types. (required)

Examples
--------
  [appserver]
  comment = Connection to the GNUe Application Server
  provider = appserver
  rpctype = xmlrpc
  host = localhost
  port = 8765
  transport = http

Notes
-----
1. GNUe AppServer works natively in utf-8, so encoding= is not a valid property.

2. This driver is fully functional with no known serious problems.
"""


# =============================================================================
# Schema handling for GNUe-AppServer
# =============================================================================

class Behavior (Base.Behavior):
	"""
	Behavior class for GNUe-AppServer backends.

	Limitations:
	  - Appserver cannot reproduce indices
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connection):

		Base.Behavior.__init__ (self, connection)

		self.__RELTYPE = {'type': 'object', 'name': u_('Business Object Class')}


	# ---------------------------------------------------------------------------
	# Read the connection's schema
	# ---------------------------------------------------------------------------

	def _readSchema_ (self, parent):
		"""
		Read the connection's schema and build a GSchema object tree connected to
		the given parent object (which is of type GSSchema).
		"""

		tables = self.__readTables (parent)
		self.__readFields (tables)
		self.__addConstraints (tables)

		# We read calculated fields after building the constraints, because this
		# way a field having a reference type does not introduce a non-existing
		# constraint.
		self.__readCalculatedFields (tables)


	# ---------------------------------------------------------------------------
	# Read all classes
	# ---------------------------------------------------------------------------

	def __readTables (self, parent):

		_list = self.__connection._session.request (u"gnue_class", [],
			[u"gnue_module.gnue_name", u"gnue_name"], [u"gnue_module.gnue_name",
				u"gnue_name"])

		result = {}
		for (gid, module, name) in _list.fetch (0, _list.count ()):
			fullname = "%s_%s" % (module, name)
			master = parent.findChildOfType ('GSTables') or \
				GSchema.GSTables (parent, **self.__RELTYPE)
			result [gid] = GSchema.GSTable (master, name = fullname, id = gid)

		return result


	# ---------------------------------------------------------------------------
	# Read all properties
	# ---------------------------------------------------------------------------

	def __readFields (self, tables):

		sess  = self.__connection._session
		sort  = [u"gnue_module", u"gnue_name"]
		props = [u"gnue_module.gnue_name", u"gnue_class", u"gnue_name",
			u"gnue_length", u"gnue_nullable", u"gnue_scale", u"gnue_type"]
		_list = sess.request (u"gnue_property", [], sort, props)

		result = {}
		for record in _list.fetch (0, _list.count ()):
			(gid, module, cid, name, length, nullable, scale, ftype) = record

			result [gid] = self.__createField (tables, gid, module, cid, name,
				length, nullable, scale, ftype)


	# ---------------------------------------------------------------------------
	# Add all kind of constraints
	# ---------------------------------------------------------------------------

	def __addConstraints (self, tables):

		for (gid, table) in tables.items ():
			# Add the primary key constraint, as it is 'well known'
			pk = GSchema.GSPrimaryKey (table, name = u"pk_%s" % table.name)
			GSchema.GSPKField (pk, name = u"gnue_id")

			# Iterate over all fields and create a foreign key constraint for
			# reference type properties
			for field in table.findChildrenOfType ('GSField', False, True):
				if '_' in field.nativetype:
					master = table.findChildOfType ('GSConstraints') or \
						GSchema.GSConstraints (table)
					constraint = GSchema.GSForeignKey (master,
						name = "fk_%s_%s" % (table.name, field.nativetype),
						references = field.nativetype)

					GSchema.GSFKField (constraint, name = field.name,
						references = u"gnue_id")


	# ---------------------------------------------------------------------------
	# Read all calculated fields
	# ---------------------------------------------------------------------------

	def __readCalculatedFields (self, tables):

		sess  = self.__connection._session
		sort  = [u"gnue_module", u"gnue_class", u"gnue_name"]
		props = [u"gnue_module.gnue_name", u"gnue_class", u"gnue_name",
			u"gnue_length", u"gnue_nullable", u"gnue_scale", u"gnue_type"]
		cond  = ['and', ['like',    ['field', u'gnue_name'], ['const', u'get%']],
			['notnull', ['field', u'gnue_type']]]
		_list = sess.request (u"gnue_procedure", cond, sort, props)

		result = {}
		for record in _list.fetch (0, _list.count ()):
			(gid, module, cid, name, length, nullable, scale, ftype) = record

			result [gid] = self.__createField (tables, gid, module, cid, name [3:],
				length, nullable, scale, ftype)


	# ---------------------------------------------------------------------------
	# Create a new GSField instance from the given arguments
	# ---------------------------------------------------------------------------

	def __createField (self, tables, gid, module, cid, name, length, nullable,
		scale, ftype):

		table  = tables [cid]
		master = table.findChildOfType ('GSFields') or GSchema.GSFields (table)

		if '_' in ftype or ftype == 'id':
			dtype  = 'string'
			length = 32
		else:
			dtype = ftype

		attrs = {'id'        : gid,
			'name'      : "%s_%s" % (module, name),
			'type'      : dtype,
			'nativetype': ftype,
			'nullable'  : nullable}
		if length:
			attrs ['length'] = length
		if scale:
			attrs ['precision'] = scale

		return GSchema.GSField (master, **attrs)


# =============================================================================
# ResultSet class
# =============================================================================

class ResultSet (Base.ResultSet):
	"""
	ResultSet class for GNUe-AppServer backends.
	"""

	# ---------------------------------------------------------------------------
	# Implementation of virtual methods
	# ---------------------------------------------------------------------------

	def _query_object_ (self, connection, table, fieldnames, condition, sortorder,
		distinct):

		self.__list = connection._session.request (table,
			condition.prefixNotation (), sortorder, fieldnames)
		self.__fieldnames = fieldnames
		self.__distinct   = distinct        # currently not honored

	# ---------------------------------------------------------------------------

	def _count_ (self):
		return self.__list.count ()

	# ---------------------------------------------------------------------------

	def _fetch_ (self, cachesize):
		position = 0
		while True:
			rows = self.__list.fetch (position, cachesize)

			for row in rows:
				# row [0] is the gnue_id that wasn't requested
				yield dict (zip (self.__fieldnames, row[1:]))

			# if fetch returned less rows than we requested, we're at the end of data
			if len (rows) < cachesize:
				break
			position += len (rows)


# =============================================================================
# GNUe-AppServer Connection class
# =============================================================================

class Connection (Base.Connection):
	"""
	Connection class for GNUe-AppServer backends.
	"""

	_resultSetClass_                = ResultSet
	_behavior_                      = Behavior
	_primarykeyFields_              = [u'gnue_id']


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections, name, parameters):

		Base.Connection.__init__ (self, connections, name, parameters)
		self.__filters = None
		self._sm       = None
		self._session  = None


	# ---------------------------------------------------------------------------
	# Implementations of virtual methods
	# ---------------------------------------------------------------------------

	def _getLoginFields_ (self):
		result = []

		dbauth = self.parameters.get ('authentication', 'False')
		if dbauth.lower () in ['true', 'yes', 'y']:
			result.extend ([(u_('User Name'), '_username', 'string', None, None, []),
					(u_('Password'), '_password', 'password', None, None, [])])

		self.__getSessionManager ()
		self.__filters = self._sm.getFilters (i18n.getuserlocale ())

		for item in self.__filters:
			(filterId, filterLabel) = item [0]
			(master, allowed)  = item [2:4]

			elements = []
			cdefault = self.parameters.get (filterId)
			default  = None

			for (label, search, field) in item [1]:
				data = {}
				if master is not None:
					for (mkey, values) in allowed.items ():
						add = data.setdefault (mkey, {})
						for vdict in values:
							if vdict [field] == cdefault:
								default = vdict ['gnue_id']
							add [vdict ['gnue_id']] = vdict [field]

				else:
					for values in allowed.values ():
						for vdict in values:
							if vdict [field] == cdefault:
								default = vdict ['gnue_id']
							data [vdict ['gnue_id']] = vdict [field]

				elements.append ((label, data))

			# Make sure to have the proper default values (keys) set
			if default is None and filterId in self.parameters:
				del self.parameters [filterId]
			elif default:
				self.parameters [filterId] = default

			fielddef = [filterLabel, filterId, 'dropdown', default, master, elements]
			result.append (fielddef)

		return result

	# ---------------------------------------------------------------------------

	def _connect_ (self, connectData):

		self.__getSessionManager ()
		self.__updateFilters (connectData)

		try:
			self._session = self._sm.open (connectData)

		except errors.RemoteError, e:
			if e.getName () == 'AuthError':
				raise Exceptions.LoginError, e.getMessage ()
			else:
				raise

	# ---------------------------------------------------------------------------

	def __updateFilters (self, connectData):

		for item in self.__filters:
			(filterId, filterLabel) = item [0]

			if connectData.has_key (filterId):
				value = connectData [filterId]
				(label, search, field) = item [1][0]

				# if there are no filter values we've to skip replacement. Maybe the
				# user just wants to add new filter values
				if not len (item [3].keys ()):
					continue

				if item [2] is None:
					masterkey = None
				else:
					masterkey = connectData [item [2]]

				found = False
				vDict = item [3][masterkey]
				for record in vDict:
					# The supplied value of a filter might could be the description or
					# the gnue_id.
					if record [field] == value or record ['gnue_id'] == value:
						connectData [filterId] = record [u'gnue_id']
						found = True
						break

				if not found:
					raise Exceptions.LoginError, \
						u_("'%(value)s' is not a valid filter-value for '%(filter)s'") \
						% {'value': value,
						'filter': label}

	# ---------------------------------------------------------------------------

	def _initialize_ (self, table, fields):
		id = self._session.store (table, [None], [], [[]]) [0]
		return self.requery (table, {u'gnue_id': id}, fields)

	# ---------------------------------------------------------------------------

	def _insert_ (self, table, newfields):
		f = newfields.copy ()
		id = f.pop (u'gnue_id')
		self._session.store (table, [id], f.keys (), [f.values ()])

	# ---------------------------------------------------------------------------

	def _update_ (self, table, oldfields, newfields):
		f = newfields
		id = oldfields [u'gnue_id']
		self._session.store (table, [id], f.keys (), [f.values ()])

	# ---------------------------------------------------------------------------

	def _delete_ (self, table, oldfields):
		id = oldfields [u'gnue_id']
		self._session.delete (table, [id])

	# ---------------------------------------------------------------------------

	def _requery_ (self, table, oldfields, fields, parameters):
		id = oldfields [u'gnue_id']
		rows = self._session.load (table, [id], fields)
		if len (rows):
			row = rows [0]
			result = {}
			for i in range (len (fields)):
				result [fields [i]] = row [i]
			return result
		else:
			return None

	# ---------------------------------------------------------------------------

	def _call_ (self, table, oldfields, methodname, parameters):
		id = oldfields [u'gnue_id']
		return self._session.call (table, [id], methodname, parameters) [0]

	# ---------------------------------------------------------------------------

	def _commit_ (self):
		self._session.commit ()

	# ---------------------------------------------------------------------------

	def _rollback_ (self):
		self._session.rollback ()

	# ---------------------------------------------------------------------------

	def _close_ (self):
		if self._session is not None:
			self._session = None

		if self._sm is not None:
			self._sm._destroy ()
			self._sm = None


	# ---------------------------------------------------------------------------
	# Create/return a connection to the appserver
	# ---------------------------------------------------------------------------

	def __getSessionManager (self):

		if self._sm is None:
			params = {'host'     : self.parameters.get ('host'),
				'port'     : self.parameters.get ('port'),
				'transport': self.parameters.get ('transport')}
			if 'timeout' in self.parameters:
				params ['timeout'] = float (self.parameters ['timeout'])

			rpcType = self.parameters.get ('rpctype')
			self._sm = client.attach (rpcType, params)

		return self._sm
