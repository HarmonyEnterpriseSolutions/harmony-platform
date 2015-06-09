# GNU Enterprise Forms - GF Object Hierarchy - Parameters
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
# $Id: GFParameter.py,v 1.3 2008/11/04 20:14:16 oleg Exp $
"""
Parameter support.
"""

__all__ = [
	# Object tree classes
	'GFParameter', 'GFCParam',

	# Exceptions
	'ParameterValueError', 'UndefinedParameterError']

from gnue.common.utils import datatypes
from gnue.common.apps import errors
from gnue.common.datasources import GConditions
from gnue.common.definitions import GParser
from gnue.forms.GFObjects.GFObj import GFObj


# =============================================================================
# Wrapper for a single forms parameter
# =============================================================================

class GFParameter(GFObj):
	"""
	A parameter defined in a form.

	Parameters can be used to pass data into forms. Parameters can be used in
	conditions of datasources. Besides that, trigger code can read and write
	parameter values arbitarily.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent):

		GFObj.__init__(self, parent, 'GFParameter')

		# Initialize attributes
		self.datatype = 'text'
		self.length = None
		self.scale = None
		self.default = None

		# Current value of the parameter
		self.__value = None

		# Trigger support
		self._triggerGlobal = True

		self._triggerProperties = {
			'value': {
				'get': self.__get_value,
				'set': self.__set_value}}


	# -------------------------------------------------------------------------
	# Object initialization
	# -------------------------------------------------------------------------

	def _buildObject(self):

		# Convert deprecated attribute "type" into "datatype".
		if hasattr(self, 'type'):
			if self.type == 'char':
				self.datatype = 'text'
			else:
				self.datatype = self.type

		# Set the default value.
		self.value = self.default

		return GFObj._buildObject(self)


	# -------------------------------------------------------------------------
	# Read and write parameter value
	# -------------------------------------------------------------------------

	def __get_value(self):

		return self.__value

	# -------------------------------------------------------------------------

	def __set_value(self, value):

		try:
			self.__value = datatypes.convert(value, self.datatype, self.length,
				self.scale)
		except ValueError:
			raise ParameterValueError(self.name, value)

	# -------------------------------------------------------------------------

	value = property(__get_value, __set_value, None,
	"""
	Value of the parameter.

	@type: depending on the datatype attribute. If possible, the
	value is converted on being set.
	""")


# =============================================================================
# A parameter for datasource conditions
# =============================================================================

class GFCParam(GConditions.GCParam):
	"""
	Parameter used in conditions. The referenced parameter must be defined in
	the form using a GFParameter tag.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent):

		GConditions.GCParam.__init__(self, parent)
		self._type = "GFCParam"
		self._inits.append(self.__phase_1_init)


	# -------------------------------------------------------------------------
	# Phase 1 initialization
	# -------------------------------------------------------------------------

	def __phase_1_init(self):

		self._form = self.findParentOfType('GFForm')
		self._parameter = None

		for param in self._form._children:
			if isinstance(param, GFParameter) and param.name == self.name:
				self._parameter = param
				break

		if not self._parameter:
			raise UndefinedParameterError(self.name, self)


	# -------------------------------------------------------------------------
	# Get the current value of a parameter
	# -------------------------------------------------------------------------

	def getValue(self):
		"""
		Return the value of the parameter.
		"""

		return self._parameter.value


# =============================================================================
# Exceptions
# =============================================================================

class ParameterValueError(errors.ApplicationError):
	"""
	A parameter has been assigned a value that can not be converted into the
	parameter's datatype.
	"""
	def __init__(self, name, value):
		errors.ApplicationError.__init__(self, u_(
				"Value %(value)r is not valid for parameter '%(name)s'") % {
				'name': name,
				'value': value})

# =============================================================================

class UndefinedParameterError(GParser.MarkupError):
	"""
	A parameter referenced in a condition is not defined.
	"""
	def __init__(self, name, parameter):
		GParser.MarkupError.__init__(self, u_(
				"Parameter '%(name)s' not defined in the form") % {'name': name},
			parameter._url, parameter._lineNumber)
