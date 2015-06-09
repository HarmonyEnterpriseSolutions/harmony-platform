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
# $Id: url_resource.py,v 1.6 2011/07/01 20:08:23 oleg Exp $

from urllib2 import urlopen

from toolib  import debug
from _base   import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import URLViewerPDF, URLViewerStub
from gnue.forms.input.GFKeyMapper import KeyMapper


class UIUrlResource(UIWidget):
	"""
	Creates a single instance of an image.
	"""

	# ------------------------------------------------------------------------
	# Create an image widget
	# ------------------------------------------------------------------------

	VIEWER_CLASSES = {
		'application/pdf' : [
			URLViewerPDF
		],
		'*/*'             : [
			URLViewerStub
		],
	}

	def __resolve(self, key):
		for i, c in enumerate(self.VIEWER_CLASSES[key]):
			if c is not None:
				return c, key, i
		raise KeyError, 'Nothing suitable for %s' % key

	def __reject_class(self, content_type, index):
		self.VIEWER_CLASSES[content_type][index] = None

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
		self.__url = None
		parent = event.container

		while True:
			widgetClass, content_type, index = self.__resolveContentViewerClass(self._gfObject.content_type)
			try:
				self.widget = widgetClass(self, self._gfObject.label or "")
			except Exception, e:
				raise
				msg = "%s: %s" % (e.__class__.__name__, e)
			except:		# must catch even string exception
				raise
				import sys
				msg = sys.exc_info()[1]
			else:
				break

			debug.warning("* Can't instantiate widget %s. Reason: %s. Falling through" % (widgetClass.__name__, msg))
			self.__reject_class(content_type, index)

		self.getParent().addWidget(self)

		self._gfObject._form.associateTrigger('ON-EXIT', self.__on_exit)

	def __on_exit(__self, self):
		try:
			__self._ui_set_value_(None)		# will close file
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
		self.__url = value
		self.widget.uiSetUrl(str(value or ''))

	def _ui_get_data_(self):
		if self.__url:
			return urlopen(self.__url).read()

	# navigable

	def _ui_set_focus_(self):
		self.widget.uiSetFocus()

	def onSetFocus(self):
		self._gfObject._event_set_focus()
		
	def onKeyPressed(self, keycode, shiftDown, ctrlDown, altDown):
		command, args = KeyMapper.getEvent(keycode, shiftDown, ctrlDown, altDown)
		if command:
			self._request(command, triggerName=args)

# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIUrlResource,
	'provides' : 'GFUrlResource',
	'container': 0,
}
