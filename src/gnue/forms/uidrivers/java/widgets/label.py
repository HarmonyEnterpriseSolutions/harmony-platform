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
# $Id: label.py,v 1.3 2015/03/25 14:39:32 oleg Exp $

from src.gnue.forms.uidrivers.java.widgets._base import UIWidget
from src.gnue.forms.uidrivers.java.widgets._remote import Label

# =============================================================================
# Interface implementation of label widgets
# =============================================================================

class UILabel(UIWidget):

	# ---------------------------------------------------------------------------
	# Create a label widget
	# ---------------------------------------------------------------------------

	def _create_widget_ (self, event):

		self.widget = Label(
			self,
			self._gfObject.text, 
			self._gfObject.alignment
		)

		self.getParent().addWidget(self)

	def _ui_set_text_(self, text):
		self.widget.uiSetText(text)

# =============================================================================
# Configuration
# =============================================================================

configuration = {
	'baseClass': UILabel,
	'provides' : 'GFLabel',
	'container': 0
}
