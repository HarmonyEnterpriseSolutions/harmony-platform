# GNU Enterprise Forms - wx 2.6 UI Driver - Splash Screen
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
# $Id: UISplashScreen.py,v 1.2 2008/11/04 20:14:19 oleg Exp $

import wx
import os.path

from gnue.common.apps import GConfig
from gnue.forms import VERSION

# =============================================================================
# Implementation of a splash screen
# =============================================================================

class SplashScreen (wx.SplashScreen):

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self):

		iDir    = GConfig.getInstalledBase ('forms_images', 'common_images')
		picture = gConfigForms ('splashScreenPNG')
		if not os.path.isabs (picture):
			picture = os.path.join (iDir, picture)

		image = wx.Image (picture).ConvertToBitmap ()

		size = image.GetSize () [1]

		dc = wx.MemoryDC ()
		dc.SelectObject (image)
		dc.SetFont (wx.SystemSettings.GetFont (wx.SYS_DEFAULT_GUI_FONT))
		dc.DrawText (u_('Version: %s') % VERSION, 24, size - 29)
		dc.SelectObject (wx.NullBitmap)

		wx.SplashScreen.__init__ (self, image,
			wx.SPLASH_CENTRE_ON_SCREEN, 0, None)

		wx.GetApp ().Yield ()
