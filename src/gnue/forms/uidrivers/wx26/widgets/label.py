# GNU Enterprise Forms - wx 2.6 UI Driver - Label widgets
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
# $Id: label.py,v 1.4 2015/03/25 14:32:43 oleg Exp $

import wx

from gnue.forms.uidrivers.wx26.widgets import _base


# =============================================================================
# Interface implementation of label widgets
# =============================================================================

class UILabel (_base.UIHelper):

	_ALIGNMENT = {'left'  : wx.ALIGN_LEFT,
		'right' : wx.ALIGN_RIGHT,
		'center': wx.ALIGN_CENTRE}

	# ---------------------------------------------------------------------------
	# Create a label widget
	# ---------------------------------------------------------------------------

	def _create_widget_ (self, event):

		flags = self._ALIGNMENT [self._gfObject.alignment] | wx.ST_NO_AUTORESIZE

		parent = event.container
		self.widget = wx.StaticText(parent, -1, self._gfObject.text, style=flags)

		self.getParent().add_widgets(self)


	def _ui_set_text_(self, text):
		self.widget.SetLabel(text)
		self.widget.GetParent().Layout()


# =============================================================================
# Configuration
# =============================================================================

configuration = {
	'baseClass': UILabel,
	'provides' : 'GFLabel',
	'container': 0
}
