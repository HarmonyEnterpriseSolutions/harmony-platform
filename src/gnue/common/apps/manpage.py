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
# Copyright 2000-2007 Free Software Foundation
#
# FILE:
# selfdoc.py
#
# DESCRIPTION:
"""
Tool self-documenting base class
"""
# NOTES:
#

import time, string
from gnue.common.utils.TextUtils import lineWrap


class ManPage:
	"""
	Create a man page for this utility.
	"""

	def __init__(self, app, dest, format=None, options={}):

		year = time.strftime("%Y", time.localtime(time.time()))

		COMMAND = string.replace(app.COMMAND,'-','\-')

		#
		# HEADER + NAME Sections
		#
		#     dest.write ("""\
		# .ig
		# Copyright (C) 2000-%s Free Software Foundation, Inc.
		#
		# Permission is granted to make and distribute verbatim copies of
		# this manual provided the copyright notice and this permission notice
		# are preserved on all copies.
		#
		# Permission is granted to copy and distribute modified versions of this
		# manual under the conditions for verbatim copying, provided that the
		# entire resulting derived work is distributed under the terms of a
		# permission notice identical to this one.
		#
		# Permission is granted to copy and distribute translations of this
		# manual into another language, under the above conditions for modified
		# versions, except that this permission notice may be included in
		# translations approved by the Free Software Foundation instead of in
		# the original English.
		# ..
		# """ % year)

		dest.write('.TH %s 1 "%s" "%s"\n' % (
				string.upper(COMMAND),
				time.strftime("%d %B %Y",
					time.localtime(time.time())),
				app.NAME))
		dest.write('.SH NAME\n')
		dest.write('%s \- %s\n' % (COMMAND,
				string.replace(app.NAME,'-','\-')))


		#
		# SYNOPSIS Section
		#
		dest.write('.SH SYNOPSIS\n')
		# dest.write('.ll +8\n')
		dest.write('.B %s\n' % COMMAND)
		for p in string.split(app.USAGE):
			part = p
			if part[0] == '[' and part[-1] == ']':
				pre = '[\n.I '
				post = '\n]'
				part = part[1:-1]
			else:
				pre = '.I '
				post = ''

			if part == '...':
				part = '\&...'

			if string.find(part,'=') > 0:
				first, last = string.split(part,'=',2)
				part = string.replace(part,
					'=','\n=\n.I ',1)

			dest.write('%s%s%s\n' % (pre, part, post))


		#
		# DESCRIPTION Section
		#
		dest.write('.SH DESCRIPTION\n')
		dest.write(lineWrap(string.replace(app.SUMMARY,'-','\-'),70) + '\n')


		#
		# OPTIONS Section
		#
		dest.write('.SH OPTIONS\n')

		allOptions = {}
		devOptions = {}
		descriptors = {}
		for optionset in [app._base_options, app.COMMAND_OPTIONS]:
			for option in optionset:
				if option.category == 'dev':
					devOptions[string.upper(option.longOption)] = option
				else:
					allOptions[string.upper(option.longOption)] = option

				if option.acceptsArgument:
					descr = '.B \-\-%s <%s>' % (option.longOption, option.argumentName or u_("value"))
				else:
					descr = '.B \-\-%s' % (option.longOption)
				if option.shortOption:
					descr += ', \-%s' % option.shortOption

				descriptors[string.upper(option.longOption)] = descr


		for optionSet, descr in (
			(allOptions,'GENERAL OPTIONS'),
			(devOptions,'DEVELOPER OPTIONS') ):

			sorted = optionSet.keys()
			sorted.sort()

			dest.write(".TP\n.B %s\n.TP\n" %descr)

			for optionKey in sorted:
				dest.write(".TP\n%s\n" % (descriptors[optionKey]))
				dest.write(string.replace(string.replace(
							lineWrap(
								string.replace(optionSet[optionKey].help,'-','\-'),70),
							"\n.", "\n\\."), "\n'", "\n\\'"))

		#
		# AUTHOR, BUGS, and COPYRIGHT sections
		#
		dest.write("""\
.SH AUTHOR
%(AUTHOR)s <%(EMAIL)s>
.SH BUGS
%(BUGS)s
Include a complete, self-contained example
that will allow the bug to be reproduced,
and say which version of this tool you are using.
.SH COPYRIGHT
Copyright \(co 2000-%(YEAR)s Free Software Foundation, Inc.
.LP
%(COMMAND)s is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2, or (at your option) any later
version.
.LP
%(COMMAND)s is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.
.LP
You should have received a copy of the GNU General Public License along
with %(COMMAND)s; see the file COPYING.  If not, write to the Free Software
Foundation, 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
""" % {'COMMAND': COMMAND,
				'YEAR': year,
				'BUGS': app.REPORT_BUGS_TO,
				'AUTHOR': app.AUTHOR,
				'EMAIL': app.EMAIL})
