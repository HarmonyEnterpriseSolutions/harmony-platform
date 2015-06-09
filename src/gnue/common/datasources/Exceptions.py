# GNU Enterprise Common Library - Exceptions
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
# $Id: Exceptions.py 9222 2007-01-08 13:02:49Z johannes $
"""
Exceptions used in the database driver system.
"""

from gnue.common.apps import errors
from gnue.common.utils import TextUtils


# =============================================================================
# Exceptions
# =============================================================================

# -----------------------------------------------------------------------------
# Login failed
# -----------------------------------------------------------------------------

class LoginError (errors.UserError):
	"""
	Login failed.

	Raised by the database drivers whenever connecting to the backend failed due
	to bad authentication data. The user will be prompted for new login data and
	can try again.
	"""
	pass


# -----------------------------------------------------------------------------
# Query type not available
# -----------------------------------------------------------------------------

class ObjectTypeNotAvailableError (errors.AdminError):
	"""
	Query type not available.

	A datasource requested a query with a type that is not supported by the
	database driver.
	"""
	pass


# -----------------------------------------------------------------------------
# Read only violation
# -----------------------------------------------------------------------------

class ReadOnlyError (errors.ApplicationError):
	"""
	Cannot insert/modify/delete data from a read only datasource.
	"""
	pass

# -----------------------------------------------------------------------------

class ReadOnlyInsertError (ReadOnlyError):
	"""
	Cannot insert a new record into a read only datasource.
	"""
	def __init__ (self):
		ReadOnlyError.__init__ (self,
			u_("Cannot insert a new record into a read only datasource"))

# -----------------------------------------------------------------------------

class ReadOnlyModifyError (ReadOnlyError):
	"""
	Cannot modify data of a read only datasource.
	"""
	def __init__ (self):
		ReadOnlyError.__init__ (self,
			u_("Cannot modify data of a read only datasource"))

# -----------------------------------------------------------------------------

class ReadOnlyDeleteError (ReadOnlyError):
	"""
	Cannot delete a record from a read only datasource.
	"""
	def __init__ (self):
		ReadOnlyError.__init__ (self,
			u_("Cannot delete a record from a read only datasource"))


# -----------------------------------------------------------------------------
# Invalid <datasource> definitions
# -----------------------------------------------------------------------------

class InvalidDatasourceDefinition (errors.ApplicationError):
	"""
	<datasource> definition is incomplete or self-contradictory.
	"""
	pass

# -----------------------------------------------------------------------------

class MissingSqlDefinitionError (InvalidDatasourceDefinition):
	"""
	Datasource is of type 'sql', but has no <sql> definition
	"""
	def __init__ (self, name):
		InvalidDatasourceDefinition.__init__ (self,
			u_("Datasource %s is of type 'sql', but has no <sql> definition.") \
				% name)

# -----------------------------------------------------------------------------

class NotSqlTypeError (InvalidDatasourceDefinition):
	"""
	Datasource is not of type 'sql', but has an <sql> definition
	"""
	def __init__ (self, name):
		InvalidDatasourceDefinition.__init__ (self,
			u_("Datasource %s is not of type 'sql', but has an <sql> definition.") \
				% name)

# -----------------------------------------------------------------------------

class MasterNotFoundError (InvalidDatasourceDefinition):
	"""
	"master" attribute points to an non-existant datasource.
	"""
	def __init__ (self, name, master):
		InvalidDatasourceDefinition.__init__ (self,
			u_("Detail datasource '%(name)s' references non-existant master "
				"'%(master)s'") % {'name': name, 'master': master})

# -----------------------------------------------------------------------------

class MissingMasterlinkError (InvalidDatasourceDefinition):
	"""
	"masterlink" attribute missing.
	"""
	def __init__ (self, name):
		InvalidDatasourceDefinition.__init__ (self,
			u_("Datasource '%s' contains a 'master' attribute, but no 'masterlink' "
				"attribute") % name)

# -----------------------------------------------------------------------------

class MissingDetaillinkError (InvalidDatasourceDefinition):
	"""
	"detaillink" attribute missing.
	"""
	def __init__ (self, name):
		InvalidDatasourceDefinition.__init__ (self,
			u_("Datasource '%s' contains a 'master' attribute, but no 'detaillink' "
				"attribute") % name)

# -----------------------------------------------------------------------------

class MasterDetailFieldMismatch (InvalidDatasourceDefinition):
	"""
	"masterfield" and "detailfield" attributes contain different numbers of
	fields.
	"""
	def __init__ (self, name):
		InvalidDatasourceDefinition.__init__ (self,
			u_("Number of fields in 'masterlink' and 'detaillink' attributes does "
				"not match for datasource '%s'") % name)


# -----------------------------------------------------------------------------
# Call of trigger function not available in this datasource
# -----------------------------------------------------------------------------

class FunctionNotAvailableError (errors.AdminError):
	"""
	Cannot use "update" and "call" functions on this datasource.
	"""
	def __init__ (self):
		errors.AdminError.__init__ (self,
			u_("Cannot use 'update' and 'call' functions on this datasource"))


# -----------------------------------------------------------------------------
# Cannot call a function of an empty record
# -----------------------------------------------------------------------------

class FunctionCallOfEmptyRecordError (errors.ApplicationError):
	"""
	Cannot call a function on an empty record - it doesn't exist in the backend.
	"""
	def __init__ (self):
		errors.ApplicationError.__init__ (self,
			u_("Cannot call a function on an empty record"))


# -----------------------------------------------------------------------------
# Record not found on requery
# -----------------------------------------------------------------------------

class RecordNotFoundError (errors.SystemError):
	"""
	Record not found on requery. This shouldn't happen.
	"""
	def __init__ (self):
		errors.SystemError.__init__ (self,
			u_("Record not found on attempt to requery changed record"))


# -----------------------------------------------------------------------------
# Backend error
# -----------------------------------------------------------------------------

class ConnectionError (errors.AdminError):
	"""
	Backend error.

	Raised whenever the database backend cannot execute what GNUe tells to do.
	"""
	def __init__ (self, message, statement, parameters):
		errors.AdminError.__init__ (self, message)
		self.detail = TextUtils.lineWrap (statement, 80)
		if parameters is not None:
			for (key, value) in parameters.items ():
				self.detail += "\n  %s: %s" % (key, repr (value))
