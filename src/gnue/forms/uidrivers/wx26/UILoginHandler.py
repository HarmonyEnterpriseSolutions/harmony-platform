# GNU Enterprise Forms - wx 2.6 UI Driver - Login Handler
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
# $Id: UILoginHandler.py,v 1.2 2008/11/04 20:14:19 oleg Exp $

import os.path
import wx

from gnue.common.datasources import GLoginHandler
from gnue.common.apps import GConfig, i18n
from gnue.forms.uidrivers.wx26 import dialogs


# =============================================================================
# This class implements a login handler for wx 2.6
# =============================================================================

class UILoginHandler (GLoginHandler.LoginHandler):

	# ---------------------------------------------------------------------------
	# Prompt for all fields
	# ---------------------------------------------------------------------------

	def __init__(self):

		# Make sure to have an application instance available
		self.app = wx.GetApp () or wx.App ()


	def _askLogin_ (self, title, fields):

		lfields = fields [:]
		if lfields [0][2] != 'image':
			imageFile = gConfigForms('loginPNG')
			if not os.path.exists (imageFile):
				imageFile = os.path.join (os.path.normpath ( \
							GConfig.getInstalledBase ('forms_images', 'common_images')),
					gConfigForms ('loginPNG'))

			if os.path.exists (imageFile):
				lfields.insert (0, (None, imageFile, 'image', None, None, []))

		dialog = dialogs.InputDialog (title, lfields, on_top=True)

		try:
			dialog.ShowModal ()
			result = dialog.inputData
		finally:
			dialog.Destroy ()

		return result
