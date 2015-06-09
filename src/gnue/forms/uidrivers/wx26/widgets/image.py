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
# $Id: image.py,v 1.4 2008/11/04 20:14:21 oleg Exp $

import wx

try:
	from PIL import Image as PILImage

except:
	PILImage = None

from gnue.common.definitions import GParser
from gnue.forms.uidrivers.wx26.widgets import _base

# =============================================================================
# Exceptions
# =============================================================================

class MissingSizeError(GParser.MarkupError):
	""" Image has no size given """
	def __init__(self, image):
		msg = u_("Image '%(name)s' is missing one of Sizer:width or "
			"Sizer:height") % {'name': image.name}
		GParser.MarkupError.__init__(self, msg, image._url, image._lineNumber)


# =============================================================================
# ImageViewer
# =============================================================================

class ImageViewer(wx.Window):
	"""
	An implementation of a wx widget used for displaying images
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent, size=wx.DefaultSize, fit='auto'):

		wx.Window.__init__(self, parent, -1, wx.DefaultPosition, size)
		self.win = parent
		self.image = None
		self.back_color = 'WHITE'
		self.border_color = 'BLACK'
		self.fit = fit

		self.image_sizex = size[0]
		self.image_sizey = size[1]

		self.Bind(wx.EVT_PAINT, self.OnPaint)


	# -------------------------------------------------------------------------
	# Draw the current image
	# -------------------------------------------------------------------------

	def OnPaint(self, event):
		dc = wx.PaintDC(self)
		self.DrawImage(dc)


	# -------------------------------------------------------------------------
	# Change the current image
	# -------------------------------------------------------------------------

	def SetValue(self, value):

		image = wx.EmptyImage(value.size[0], value.size[1])
		image.SetData(value.convert("RGB").tostring())
		self.image = image
		self.Refresh()


	# -------------------------------------------------------------------------
	# Draw a border around the widget
	# -------------------------------------------------------------------------

	def DrawBorder(self, dc):

		brush = wx.Brush(wx.NamedColour(self.back_color), wx.SOLID)
		dc.SetBrush(brush)
		dc.SetPen(wx.Pen(wx.NamedColour(self.border_color), 1))
		dc.DrawRectangle(0, 0, self.image_sizex, self.image_sizey)


	# -------------------------------------------------------------------------
	# Draw the image to the device context
	# -------------------------------------------------------------------------

	def DrawImage(self, dc):
		try:
			image = self.image
		except:
			return

		self.DrawBorder(dc)

		if image is None:
			return

		bmp = image.ConvertToBitmap()

		# Dimensions of the image file
		iwidth = bmp.GetWidth()
		iheight = bmp.GetHeight()
		scrx = self.image_sizex
		scry = self.image_sizey

		fit = self.fit

		if fit == "auto":
			if float(scrx) / iwidth < float(scry) / iwidth:
				fit = "width"
			else:
				fit = "height"

		if fit == 'width':
			prop = float(self.image_sizex-10) / iwidth
			iwidth = self.image_sizex - 10
			diffx = 5
			iheight = abs(int(iheight * prop))
			diffy = (self.image_sizey - iheight)/2

			if iheight >= self.image_sizey - 10:
				diffy = 5
				iheight = self.image_sizey - 10

		elif fit == 'height':
			prop = float(self.image_sizey-10) / iheight
			iheight = self.image_sizey - 10
			diffy = 5

			iwidth = abs(int(iwidth * prop))
			diffx = (self.image_sizex - iwidth) / 2
			if iwidth > self.image_sizex - 10:
				diffx = 5
				iwidth = self.image_sizex - 10

		elif fit == 'both':
			diffx = (self.image_sizex - iwidth)/2   # center calc
			if iwidth >= self.image_sizex -10:      # if image width fits in
				# window adjust
				diffx = 5
				iwidth = self.image_sizex - 10

			diffy = (self.image_sizey - iheight)/2  # center calc
			if iheight >= self.image_sizey - 10:    # if image height fits in
				# window adjust
				diffy = 5
				iheight = self.image_sizey - 10

		elif fit == 'none':
			diffx = (self.image_sizex - iwidth ) / 2
			diffy = (self.image_sizey - iheight) / 2

		image.Rescale(iwidth, iheight)      # rescale to fit the window
		bmp = image.ConvertToBitmap()
		if diffx < 0 or diffy < 0:
			dc.SetClippingRegion(0, 0, self.image_sizex-1, self.image_sizey-1)
		dc.DrawBitmap(bmp, diffx, diffy)        # draw the image to window


# ============================================================================= # Wrap an UI layer around a wx image
# =============================================================================

class UIImage (_base.UIHelper):
	"""
	Creates a single instance of an image.
	"""

	# ------------------------------------------------------------------------
	# Create an image widget
	# ------------------------------------------------------------------------

	def _create_widget_ (self, event):
		"""
		Creates a new StaticBitmap widget.
		"""
		parent = event.container
		self.image_size = self.get_default_size()
		self.widget = ImageViewer(parent, self.image_size, self._gfObject.fit)
		self.getParent().add_widgets(self)


	# -------------------------------------------------------------------------
	# Get the default size for the image
	# -------------------------------------------------------------------------

	def get_default_size(self):

		width = int(getattr(self._gfObject, 'Sizer__width', -1))
		height = int(getattr(self._gfObject, 'Sizer__height', -1))
		if width == -1 or height == -1:
			raise MissingSizeError(self._gfObject)

		return (width, height)


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

		if PILImage is None:
			return

		self.widget.SetValue(value)


# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIImage,
	'provides' : 'GFImage',
	'container': 0,
}
