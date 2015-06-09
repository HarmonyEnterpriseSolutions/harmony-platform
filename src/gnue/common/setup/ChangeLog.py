# GNU Enterprise Common Library - ChangeLog creation
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
# Copyright 2001-2007 Free Software Foundation
#
# $Id: ChangeLog.py 9222 2007-01-08 13:02:49Z johannes $

SVNCMD='svn log -v --xml'

import xml.parsers.expat
import tempfile, os, sys, string

# -----------------------------------------------------------------------------
# The Parser
# -----------------------------------------------------------------------------

class Parser:
	def __init__ (self, input, output):

		self.out = output
		self.package = os.path.basename (os.getcwd ())

		p = xml.parsers.expat.ParserCreate ()

		p.StartElementHandler = self.start_element
		p.EndElementHandler = self.end_element
		p.CharacterDataHandler = self.char_data

		p.ParseFile (input)

		self.paths = []
		self.revision = ''

	# 3 handler functions
	def start_element (self, name, attrs):
		self.text = ''
		if name == 'logentry':
			self.revision = string.ljust (attrs ['revision'], 5)
		elif name == 'paths':
			self.paths = []

	def end_element (self, name):
		if name == 'logentry':
			self.out.write ('\n')
		elif name == 'author':
			self.author = self.text
		elif name == 'path':
			p = string.split (self.text, '/', 3)
			if len (p) == 4:
				if p [2] == self.package:
					self.paths.append (p [3])
		elif name == 'msg':
			self.out.write ('%s  Rev %s  %s\n\n' % \
					(self.date, self.revision, self.author))
			text = '%s: %s' % (string.join (self.paths, ', '), self.text)
			self.out.write ('\t* %s' % linewrap (text))
		elif name == 'date':
			self.date = self.text[:10] + ' ' + self.text[11:19]

	def char_data(self, data):
		self.text += data.encode('ascii','replace')

# -----------------------------------------------------------------------------
# Helper function to wrap long lines
# -----------------------------------------------------------------------------

def linewrap (message, maxWidth=69, indent = '\t  '):

	text = ''

	temptext = string.strip (str (message))
	temptext = temptext.replace ('\n\n', '\r')
	temptext = temptext.replace ('\n', ' ')

	buff = string.split (temptext, '\r')

	for strings in buff:
		while len (strings) > maxWidth:

			index = string.rfind (strings, ' ', 0, maxWidth)

			if index > 0:
				line = strings [:index]
			else:
				line = strings [:maxWidth]
				index = maxWidth - 1

			if text != '':
				text += indent
			text += '%s\n' % line
			strings = strings [index+1:]
			strings = strings.strip ()

		line = strings
		if text != '':
			text += indent
		text += '%s\n' % line
		first = 0
	return text

# -----------------------------------------------------------------------------
# Build the ChangeLog file
# -----------------------------------------------------------------------------

def build ():
	filename = tempfile.mktemp ('xml')
	if os.system (SVNCMD + '> %s' % filename):
		print 'Unable to retrieve svn log'
		sys.exit (1)

	inp = open (filename)
	out = open ('ChangeLog' ,'w')

	try:
		Parser (inp, out)
	except:
		try:
			inp.close ()
			out.close ()
			os.unlink (filename)
		except:
			pass
		raise

	# Clean up input/output files
	inp.close ()
	out.close ()
	os.unlink (filename)
