
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
# Copyright 2002-2007 Free Software Foundation
#
# FILE:
# GFDisplayHandler.py
#
# $Id: Image.py,v 1.2 2008/11/04 20:14:17 oleg Exp $
"""
Display handler responsible for handling image style entries.
"""
__revision__ = "$Id: Image.py,v 1.2 2008/11/04 20:14:17 oleg Exp $"

from gnue.common.utils.FileUtils import openResource
from gnue.forms.input.displayHandlers.Cursor import BaseCursor
from gnue.common.apps import errors
import cStringIO

class NeedsPilForImages(errors.AdminError):
	"""
	Python Imaging (PIL) is required but not installed.
	"""
	def __init__(self):
		errors.AdminError.__init__(self, u_(
				"Form contains a <image> but python image support not installed"))
		self.detail = "Installation sources:\n" + \
			"Source: http://www.pythonware.com/products/pil/\n" + \
			"Debian package: python-imaging"

try:
	from PIL import Image as PILImage
except ImportError:
	PILImage = None
	raise NeedsPilForImages()

class Image(BaseCursor):
	"""
	Display handler responsible for handling image style entries.
	"""
	def build_display(self, value, editing):
		"""
		Opens and returns a PIL Image for the requested url

		@param value: The url of the image to be displayed
		@param editing: Not used
		"""
		if PILImage and value and self.entry.type.lower() == 'url':
			try:
				# PIL doesn't like our openResource function as it's based
				# upon urlopen which doesn't provide seek.  We'll use the
				# StringIO function to get around that so that urls can
				# still be used
				urlFile = openResource(value, 'rb')
				fileObject = cStringIO.StringIO(urlFile.read())
				image = PILImage.open(fileObject)

			except IOError:
				image = PILImage.new("RGB", (1, 1, ))
		else:
			image = PILImage.new("RGB", (1, 1, ))

		return image
