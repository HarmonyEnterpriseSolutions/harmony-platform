# GNU Enterprise Forms - GF Object Hierarchy - Base class for all GF-Objects
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
# $Id: GFObj.py,v 1.8 2009/07/24 15:00:29 oleg Exp $
"""
Base class for all objects represented by an XML tag in a GFD tree.
"""

from gnue.common.definitions.GObjects import GObj
from gnue.common.logic.GTrigger import GTriggerExtension
from gnue.common.definitions.GParser import MarkupError
from gnue.common.apps import i18n

LOCALIZEABLE_ATTRIBUTES = ('label', 'description', 'title', 'caption', 'text')
__all__ = ['GFObj']

# =============================================================================
# Base class for GF* objects
# =============================================================================

class GFObj(GObj, GTriggerExtension):
	"""
	A GFObj is the base class for all objects of a GF object tree. It
	implements the GTriggerExtension interface, so all GF objects are capable
	of associating and calling triggers.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None, object_type='GFObj'):

		GTriggerExtension.__init__(self)
		GObj.__init__(self, parent, object_type)

		self.hidden = False
		self.name = "%s%x" % (("%s" % self.__class__).split('.')[-1][:-2], id(self))

		self._visibleIndex = 0
		self._inits = [self.phase_1_init]
		self._form = None

		# The reference to the uiWidget will be set by the
		# uidrivers._base.UIdriver._buildUI () function.
		self.uiWidget = None


	# -------------------------------------------------------------------------
	# Check wether an object is navigable or not
	# -------------------------------------------------------------------------

	def is_navigable(self, mode='edit'):
		"""
		Return wether the object is currently navigable or not.

		@param mode: current state of the object. Can be 'edit', 'query' or
		    'new'
		@returns: True or False
		"""

		return self._is_navigable_(mode)


	# -------------------------------------------------------------------------
	# Phase 1 initialization
	# -------------------------------------------------------------------------

	def phase_1_init(self):
		"""
		Phase 1 initialization called after all objects of the XML tree were
		created.
		"""

		self._phase_1_init_()
		self._localize_init_()


	# -------------------------------------------------------------------------
	# Get an option of the object
	# -------------------------------------------------------------------------

	def get_option(self, name):
		"""
		Return the value of a given option of the object or None if no such
		option is present.

		@param name: name of the option to be queried
		@returns: the value of the requested option or None
		"""

		option = None

		for child in self.findChildrenOfType('GFOption', False, True):
			if child.name == name:
				option = child.value
				break

		return option


	# --------------------------------------------------------------------------
	# Get a block from the block map
	# -------------------------------------------------------------------------

	def get_block(self):
		"""
		Return the objects' block from the block mapping.

		@returns: the block of the current object or None if the current object
		  does not support blocks.
		@raises BlockNotFoundError: if the block specified by the object is not
		  listed in the block mapping of the logic instance
		"""
		if getattr(self, 'block', None) is None:
			try:
				self.block = self.lookupAttribute('block')
			except AttributeLookupError:
				return None
		return self._form._logic.getBlock(self.block)

	# -------------------------------------------------------------------------
	# Get a field
	# -------------------------------------------------------------------------

	def get_field(self):
		"""
		Returns the objects' field from the blocks' field mapping

		@returns: GFField instance or None if the object does not support fields
		@raises FieldNotFoundError: if the field is not available through the
		  block
		"""

		if getattr(self, 'field', None) is not None:
			block = self.get_block()
			if block is not None:
				return block.getField(self.field)
		return None

	# -------------------------------------------------------------------------
	# Virtual methods to be implemented by descendants
	# -------------------------------------------------------------------------

	def _is_navigable_(self, mode):
		"""
		Return wether the object is currently navigable or not.

		Descendants can overwrite this method to return either True or False. If
		this method is not overwritten it returns False.

		@param mode: current state of the object. Can be 'edit', 'query' or
		  'new'
		"""

		return False


	# -------------------------------------------------------------------------
	# Phase 1 initialization
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		"""
		Phase 1 initialization called after all objects of the XML tree were
		created. Descendants can overwrite this function to perform actions
		after construction of the objects.
		"""

		self._form = self.findParentOfType('GFForm')

	def _localize_init_(self):
		if i18n.getCatalog('forms'):
			for i in LOCALIZEABLE_ATTRIBUTES:
				if getattr(self, i, None):
					setattr(self, i, i18n.getCatalog('forms').ugettext(getattr(self, i)))

	# -------------------------------------------------------------------------
	# Indicate whether this widget makes use of the separate label column
	# -------------------------------------------------------------------------

	def hasLabel(self):
		return False


	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, getattr(self, 'name', ''))


	# TODO: move it to some base class
	def lookupAttribute(self, name):
		"""
		lookup attribute from this object or from parent recursively
		"""
		owner = self
		while owner:
			if getattr(owner, name, None) is not None:
				return getattr(owner, name)
			owner = owner.getParent()
		else:
			raise AttributeLookupError(self, name)


# =============================================================================
# Errors
# =============================================================================

class AttributeLookupError(MarkupError):

	def __init__(self, source, name):
		MarkupError.__init__(self,
			u_("Expected attribute '%(attr)s' not found "
				"in %(source_type)s '%(source)s' and parents") % {
				'attr'        : name,
				'source_type' : source._type[2:],
				'source'      : source.name,
			},
			source._url,
			source._lineNumber
		)


class UnresolvedNameError(MarkupError):
	"""
	Base class for any *NotFoundError
	"""

	def __init__(self, source, subject, name, referer=None):
		args = {
			'source_type'   : source._type[2:],
			'source'        : source.name,
			'subject'       : subject,
			'name'          : name,
		}

		if isinstance(referer, GFObj):
			location = referer
			args['referer_type'] = referer._type[2:]
			args['referer']      = referer.name
			pattern = u_("%(source_type)s '%(source)s': "
				"%(subject)s '%(name)s' in "
				"%(referer_type)s '%(referer)s' not found")
		else:
			location = source
			pattern = u_("%(source_type)s '%(source)s': "
				"%(subject)s '%(name)s' not found")

		MarkupError.__init__(self,
			pattern % args,
			location._url,
			location._lineNumber
		)
