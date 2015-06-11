#!/usr/bin/env python
#
# GNU Enterprise Forms - Main Script
#
# Copyright 2001-2003 Free Software Foundation
#
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
# $Id: gnue-forms.py,v 1.7 2013/02/27 13:34:36 oleg Exp $

import os, sys
if hasattr(sys, 'frozen'):
	sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0])))

SRC_DIR = os.path.join(os.path.split(os.path.split(os.path.abspath(__file__))[0])[0], 'src')
sys.path.insert(1, SRC_DIR)

from  gnue.forms import GFClient

if __name__ == '__main__':
	
	if sys.platform == 'win32' and os.path.split(sys.executable)[1].lower() == 'pythonw.exe':
		# write harmony.log under pythonw if have debug level
		if ' --debug-level=' in ' '.join(sys.argv[1:]):
			sys.stdout = sys.stderr = open(os.path.join(os.environ['USERPROFILE'], 'harmony.log'), 'at', 0)
		else:
			# running in pythonw.exe
			# default streams are invalid and fail after 4097 bytes written (Bad File Descriptor)
			sys.stdout = sys.stderr = open('nul', 'wb')
			
	client = GFClient.GFClient()
	client.run ()
