# GNU Enterprise Forms - UI drivers - Base class for widgets implementation
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
# $Id: _base.py,v 1.5 2009/09/07 15:31:37 oleg Exp $

"""
Base class for UIwidgets used by specific UI drivers to subclass their widgets
from.
"""

from gnue.common import events
from gnue.common.definitions import GParser
from gnue.common.definitions.GObjects import GObj
from gnue.forms.GFObjects import GFTabStop, GFBox, GFLabel

__all__ = ['UIWidget', 'InvalidBoundingBoxError']

# =============================================================================
# Exceptions
# =============================================================================

class InvalidBoundingBoxError(GParser.MarkupError):
	""" Element A overlaps Element B """
	def __init__(self, current, item):
		cur_type = current._type[2:]
		cmp_type = item._type[2:]
		msg = u_("Widget %(cur_type)s '%(cur_name)s' overlaps %(cmp_type)s "
			"'%(cmp_name)s'") \
			% {'cur_type': cur_type, 'cur_name': current.name,
			'cmp_type': cmp_type, 'cmp_name': item.name}
		GParser.MarkupError.__init__(self, msg, current._url,
			current._lineNumber)

# =============================================================================

class InvalidSpanError(GParser.MarkupError):
	""" An element has an invalid width or height """
	def __init__(self, item):
		msg = u_("Widget %(type)s '%(name)s' has an invalid width or height") \
			% {'type': item._type[2:], 'name': item.name}
		GParser.MarkupError.__init__(self, msg, item._url, item._lineNumber)

ANCHOR = {
	'bottom-left'  : 1,
	'bottom'       : 2,
	'bottom-right' : 3,
	'left'         : 4,
	'center'       : 5,
	'right'        : 6,
	'top-left'     : 7,
	'top'          : 8,
	'top-right'    : 9,
	'default'      : 4,		# default is left
}

# =============================================================================
# Base class for ui widgets
# =============================================================================

class UIWidget(GObj):
	"""
	Base class for user interface widgets.

	@ivar _gfObject: The GFObject for this UIWidget
	@ivar _container: If this widget can contain other widgets then _container
	    is the specific container children should use (as parent)
	@ivar _uiDriver: the GFUserInterface instance of the current ui driver used
	    to render the form
	@ivar _uiForm: the UIForm widget this widget is a child of
	@ivar _form: the GFForm instance owning this widget

	"""

	DEFAULT_ANCHOR = ANCHOR['default']

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event):
		GObj.__init__(self, parent=event.parent)
		self._type = ("%s" % self.__class__).split('.')[-1][:-2]
		self._inits = [self.__primary_init]

		self.__creationEvent = event
		self._gfObject = event.object
		self._container = None
		self._uiForm = None
		self._uiDriver = None
		self._form = event.gfForm

		self.stretch = int(getattr(self._gfObject, 'Sizer__stretch', 1))
		self.min_width = int(getattr(self._gfObject, 'Sizer__min_width', 0))
		self.min_height = int(getattr(self._gfObject, 'Sizer__min_height',
				0))
		self.max_width = int(getattr(self._gfObject, 'Sizer__max_width', 0))
		self.max_height = int(getattr(self._gfObject, 'Sizer__max_height',
				0))
		self.def_width = int(getattr(self._gfObject, 'Sizer__def_width', 0))
		self.def_height = int(getattr(self._gfObject, 'Sizer__def_height',
				0))
		self.span = int(getattr(self._gfObject, 'Sizer__span', 1))

		self.anchor = ANCHOR[str(getattr(self._gfObject, 'Sizer__anchor', 'default'))]

	# -------------------------------------------------------------------------
	# Phase 1 initialization
	# -------------------------------------------------------------------------

	def __primary_init(self):

		self._uiDriver = self.findParentOfType('UIDriver')
		self._uiForm = self.findParentOfType('UIForm')

		try:
			owner = self.getParent()
			self.__creationEvent.container = owner._container

		except AttributeError:
			if not hasattr(self.__creationEvent, 'container'):
				self.__creationEvent.container = None

		if not getattr(self._gfObject, 'hidden', False):
			self._create_widget_(self.__creationEvent)

		del self.__creationEvent

	# -------------------------------------------------------------------------
	# Fire a request* event
	# -------------------------------------------------------------------------

	def _request(self, name, **params):
		"""
		Fire a request<name> event passing the GFObject and the GFObject's form
		as additional event parameters.

		@param name: name of the event, i.e. a name of 'FOO' would fire a
		    'requestFOO' event.
		@param params: dictionary with parameters passed with the event. this
		    dictionary will always get the keys '_object' (with the GFObject of
		    this widget) and '_form' (with the GFForm of this widget) set.
		"""

		params['_object'] = self._gfObject
		params['_form'] = self._gfObject._form

		self._uiDriver.dispatchEvent(events.Event("request%s" % name, **params))


	# -------------------------------------------------------------------------
	# Virtual methods // Descendants should override these functions
	# -------------------------------------------------------------------------
	# TODO: add docstrings to these methods and pep8-ify them

	def _create_widget_(self, event):
		assert gDebug(1, "UI does not support %s" % self.__class__)
