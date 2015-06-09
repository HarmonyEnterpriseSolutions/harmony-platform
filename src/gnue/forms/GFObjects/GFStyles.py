# GNU Enterprise Forms - GF Object Hierarchy - Box
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
# $Id: GFStyles.py,v 1.5 2012/09/21 16:52:57 oleg Exp $
"""
Styles
"""

from copy import copy

from src.gnue.forms.GFObjects import GFObj


__all__ = ['GFStyles']

# =============================================================================
# <Styles>
# =============================================================================

class GFStyles(GFObj):

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		GFObj.__init__(self, parent, "GFStyles")

		self.__baseStyles = None
		self.__styles = {}
		#self.__noneStyle = None

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		GFObj._phase_1_init_(self)

		self.__baseStyles = self.findChildrenOfType('GFStyle', allowAllChildren=True)

		# style: style index dict
		self.__baseStyleIndex = dict(((style.name, i) for i, style in enumerate(self.__baseStyles)))

		for i in self.__baseStyles:
			self.__styles[(i.name,)] = i

	def __iter__(self):
		return iter(self.__baseStyles)

	def _cmpStyles(self, style1, style2):
		try:
			return cmp(self.__baseStyleIndex[style1], self.__baseStyleIndex[style2])
		except KeyError, e:
			return cmp(style1, style2)

	def getStyle(self, keys):
		"""
		@param keys: comma separated string of keys or iterable of keys or None
		@return style object or None
		"""

		if keys is None:
			keys = ()
		else:
			if isinstance(keys, (int, long)):
				keys = str(keys)
			if isinstance(keys, basestring):
				keys = filter(None, (i.strip() for i in keys.split(',')))
				keys.sort(self._cmpStyles)
			keys = tuple(keys)

		if len(keys) == 1:
			try:
				style = self.__styles[keys]
			except KeyError:
				style = self.__styles[keys] = None
				#self._form.show_message(_("Style not defined: '%s'") % ','.join(keys), kind='warning')
				print "! Style not defined: %s" % ','.join(keys)
		else:
			styles = filter(None, map(self.getStyle, keys))
			if styles:
				style = copy(styles[0])
				style.name = ','.join(keys)
				for i in styles[1:]:
					style.merge(i, overwrite=True)
			else:
				style = None

			self.__styles[keys] = style
		
		return style

	def hasStyle(self, filter = lambda style: True):
		for style in self.__baseStyles:
			if filter(style):
				return True
		return False
