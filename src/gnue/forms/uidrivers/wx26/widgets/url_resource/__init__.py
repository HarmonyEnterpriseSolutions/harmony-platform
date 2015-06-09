# GNU Enterprise Forms - wx 2.6 UI Driver - Image widgets
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
# $Id: __init__.py,v 1.17 2013/11/21 18:53:19 oleg Exp $

import wx

from gnue.forms.uidrivers.wx26.widgets import _base
from toolib import debug
from src.gnue.forms.uidrivers.wx26.widgets.url_resource import LazyModule


class UIUrlResource (_base.UIHelper):
	"""
	Creates a single instance of an image.
	"""

	# ------------------------------------------------------------------------
	# Create an image widget
	# ------------------------------------------------------------------------

	VIEWER_MODULES = {
		'application/pdf' : [
			LazyModule(__name__ + '.' + 'PDF',             globals(), locals()),
			LazyModule(__name__ + '.' + 'AcrobatReader7',   globals(), locals()),
			LazyModule(__name__ + '.' + 'AcrobatReader5',   globals(), locals()),
			LazyModule(__name__ + '.' + 'FoxitReader',      globals(), locals()),
		],
		'*/*'             : [
			LazyModule(__name__ + '.' + 'Chrome',          globals(), locals()),
			LazyModule(__name__ + '.' + 'IE',              globals(), locals()),
			LazyModule(__name__ + '.' + 'StubViewer',      globals(), locals()),
		],
	}

	def __resolve(self, key):
		for i, m in enumerate(self.VIEWER_MODULES[key]):
			if m is not None:
				try:
					return getattr(m, m.__name__[m.__name__.rfind('.')+1:]), key, i
				except ImportError, e:
					debug.warning("%s: %s. Falling through" % (e.__class__.__name__, e))

					# remove unimportable module from config
					self.__reject_module(key, i)

		raise KeyError, 'Nothing suitable for %s' % key

	def __reject_module(self, content_type, index):
		self.VIEWER_MODULES[content_type][index] = None

	def __resolveContentViewerClass(self, contentType):
		while True:
			try:
				return self.__resolve(contentType)
			except KeyError:
				# try * at second part e.g. image/*
				try:
					return self.__resolve(contentType.split('/')[0] + '/*')
				except KeyError:
					return self.__resolve('*/*')

	def _create_widget_(self, event):
		"""
		Creates a new StaticBitmap widget.
		"""
		parent = event.container

		while True:
			widgetClass, content_type, index = self.__resolveContentViewerClass(self._gfObject.content_type)
			try:
				widget = self.widget = widgetClass(parent, -1)
			except Exception, e:
				msg = "%s: %s" % (e.__class__.__name__, e)
			except:		# must catch even string exception
				import sys
				msg = sys.exc_info()[1]
			else:
				if self._gfObject.label:
					# Replace blanks by non-breaking space to avoid random linebreaks
					# in labels (sometimes done by wx, probably due to rounding errors
					# in size calculations)
					text = self._gfObject.label.replace(u" ", u"\240")
					self.label = wx.StaticText(parent, -1, text)
				else:
					self.label = None

				if hasattr(widget, 'onExit'):
					self._gfObject._form.associateTrigger('ON-EXIT', lambda self: widget.onExit())

				break

			debug.warning("* Can't instantiate widget %s. Reason: %s. Falling through" % (widgetClass.__name__, msg))
			self.__reject_module(content_type, index)

		self.getParent().add_widgets(self)

		self._gfObject._form.associateTrigger('ON-EXIT', self.__on_exit)


	def __on_exit(__self, self):
		try:
			__self.widget.setUrl(None)	# will close file
		except wx.PyDeadObjectError:
			pass

	# -------------------------------------------------------------------------
	# Set "editable" status for this widget
	# -------------------------------------------------------------------------

	def _ui_set_editable_(self, editable):
		pass

	# ------------------------------------------------------------------------
	# Set the widget's PIL
	# ------------------------------------------------------------------------

	def _ui_set_value_(self, value):
		"""
		Loads an image.
		"""
		self.widget.setUrl(value)

	def _ui_get_data_(self):
		return self.widget.getData()

	def is_growable(self):
		return True

	def _ui_enable_(self, enabled):
		pass


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIUrlResource,
	'provides' : 'GFUrlResource',
	'container': 0,
}
