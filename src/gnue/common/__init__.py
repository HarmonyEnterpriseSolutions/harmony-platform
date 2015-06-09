# GNU Enterprise Common Library
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
# $Id: __init__.py 9754 2007-07-12 14:15:34Z reinhard $
"""
The GNUe Common Library is a set of Python modules used in the GNUe tools. Many
of the modules can also be used outside GNUe.
"""

import sys

from src.gnue.common import svnrev

from src.gnue.common.utils import version


try:
	svn_revision = svnrev.svnrev
except ImportError:
	svn_revision = None

PACKAGE = "GNUe-Common"
TITLE = "GNUe Common Library"

version = version.Version(0, 6, 'final', 9, svn_revision)

VERSION = version.get_version()
HEXVERSION = version.get_hexversion()

__version__ = VERSION
__hexversion__ = HEXVERSION

# TODO: remove this stuff from here
if os.name == 'nt':
	# under windows
	try:
		import WebKit
	except:
		# not under webkit
		try:
			from django.conf import settings
			settings.SITE_ID
		except:
			# not under django or webkit
			from toolib import startup
			startup.setDefaultEncoding()
			#startup.hookStd()
			#rint "+ default encoding set to", sys.getdefaultencoding()

# static urllib2 configuration
# to modify urlopen behaviour
import os
try:
	from gnue.paths import config
	execfile(os.path.join(config, 'urllib2.conf.py'), {}, {})
except Exception, e:
	print "* etc/urllib2.conf.py failed: %s: %s" % (e.__class__.__name__, e)

# c-decimal substitution
try:
	import _decimal
	sys.modules['decimal'] = _decimal
	del _decimal
except ImportError:
	#print >>sys.stderr, "* c-decimal is not installed. We'll slow"
	pass
