# GNU Enterprise Common Library - Utilities - Version handling
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
# $Id: version.py 9696 2007-06-08 19:44:54Z reinhard $
"""
Helper functions for version handling.

About the release process in GNU Enterprise
===========================================

Releases
--------

GNU Enterprise is under ongoing development, and once a new set of functions is
ready to be used, a release is made.

Releases are numbered with a two-part release number, like 0.6 or 1.0 or 2.4.

Builds
------

A build is a specific version of the software. For every release, several
builds are made.

Before the release, so called "prerelease" or "unstable" builds are made. The
version number of these builds consist of the release number of the upcoming
release, a dash, the name of the phase of the release cycle, and the build
number within the phase.

The first phase of the release cycle is "alpha", in which the software is
expected to have bugs, and new features usually are freshly (and probably
incompletely) implemented. As soon as the software is deemed feature-complete,
it switches to "beta" phase, in which the bug hunting season starts. Once the
developers feel that no serious bugs should be left over, the "pre" phase
begins. In the last phase before the release, the versions are named "rc"
(meaning "release candidate").

Then the software goes into the stable (read: end user suitable) phase. The
first stable version of each release ends in ".0", but people will still find
bugs or major improvements, and there will be further bug fix builds within the
same release cycle, where the last number is incremented.

Snapshots
---------

Some people want to be on the bleeding edge of development and use Subversion
snapshots. The version number of such a snapshot is the version number of the
last build, a "+" sign, the text "svn", a dot, and the Subversion revision.
"""

import os
import sys

__all__ = ['get_svn_revision', 'Version']


# =============================================================================
# Find out current SVN revision
# =============================================================================

def get_svn_revision(directory):
	"""
	Find out the SVN revision of the last change in the current directory.

	The current directory must be an SVN checkout, and the "svn" command must
	be available.

	This function only works on POSIX systems. On other systems, it returns
	C{'unknown'}.

	If the environment variable C{GNUE_BUILD} is set, the function returns 0.

	@param directory: Source directory to check the revision for.
	"""

	if os.environ.has_key('GNUE_BUILD'):
		return 0

	if os.name != 'posix':
		return 'unknown'

	if os.path.islink(directory):
		directory = os.readlink(directory)

	cmd = ("LANG=C svn info %s | grep 'Last Changed Rev:' " + \
			"| sed -e 's/Last Changed Rev: //'") % directory

	import commands
	# Unfortunately, svn does not set an exit status on all errors, so there's
	# no use in testing the status.
	output = commands.getoutput(cmd)
	try:
		return int(output)
	except ValueError:
		return 'unknown'


# =============================================================================
# Version class
# =============================================================================

class Version:
	"""
	A version number consisting of several parts.

	A version number defined by this class can be one of 4 types:

	Unstable Build
	==============
	    A version number for an unstable build follows the format
	    <major>.<minor>-<phase><build> (e.g. "1.5-pre2").

	Unstable Snapshot
	=================
	    A version number for an unstable SVN snapshot follows the format
	    <major>.<minor>-<phase><build>+svn.<svn> (e.g. "1.5-pre2+svn.9876).

	Stable Build
	============
	    A version number for a stable build follows the format
	    <major>.<minor>.<build> (e.g. 1.5.2).

	Stable Snapshot
	===============
	    A version number for a stable snapshot follows the format
	    <major>.<minor>.<build>+svn.<svn> (e.g. 1.5.2+svn.9876).

	@ivar major: Major release number
	@ivar minor: Minor release number
	@ivar phase: Phase of the release process. Can be C{'alpha'}, C{'beta'},
	    C{'pre'}, C{'rc'}, or C{'final'}. If the phase is C{'final'}, it is a
	    stable version, otherwise it is an unstable version.
	@ivar build: Build number within the phase.
	@ivar svn: SVN revision number. If this parameter is 0, the version is an
	    explicit build, otherwise it is an SVN snapshot.
	"""

	__phases = {
		'alpha': 'a',
		'beta': 'b',
		'pre': 'd',
		'rc': 'e',
		'final': 'f'}

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, major, minor, phase, build, svn):
		"""
		Create a new Version object instance.

		@param major: Major release number.
		@param minor: Minor release number.
		@param phase: Phase of the release process. Can be C{'alpha'},
		    C{'beta'}, C{'pre'}, C{'rc'}, or C{'final'}. If the phase is
		    C{'final'}, it is a stable version, otherwise it is an unstable
		    version.
		@param build: Build number within the phase.
		@param svn: SVN revision number. If this parameter is 0, the version is
		    an explicit build, otherwise it is an SVN snapshot. If this
		    parameter is C{None}, the SVN revision is determined automatically.
		"""

		assert isinstance(major, int) and major >= 0 and major < 100
		assert isinstance(minor, int) and minor >= 0 and minor < 100
		assert phase in self.__phases.keys()
		assert isinstance(build, int) and build >= 0 and build < 10

		self.major = major
		self.minor = minor
		self.phase = phase
		self.build = build
		self.svn = svn

		if self.svn is None:
			caller_file = sys._getframe(1).f_code.co_filename
			self.svn = get_svn_revision(os.path.dirname(caller_file))


	# -------------------------------------------------------------------------
	# Get version number
	# -------------------------------------------------------------------------

	def get_version(self):
		"""
		Return the version number as a human readable string.
		"""

		if self.phase == 'final':
			result = '%s.%s.%s' % (self.major, self.minor, self.build)
		else:
			result = '%s.%s-%s%s' % (self.major, self.minor, self.phase,
				self.build)

		if self.svn:
			result += '+svn.%s' % self.svn

		return result


	# -------------------------------------------------------------------------
	# Get hexversion number
	# -------------------------------------------------------------------------

	def get_hexversion(self):
		"""
		Return the version number as an eight character hexadecimal number.

		Later versions will always result in higher numbers.
		"""

		if not self.svn:
			svn = '00'
		else:
			svn = '80'

		return '%02d%02d%s%01d%s' % (self.major, self.minor,
			self.__phases[self.phase], self.build, svn)


# =============================================================================
# Self test code
# =============================================================================

if __name__ == '__main__':
	version = Version(1, 5, 'beta', 3, None)
	print version.get_version()
	print version.get_hexversion()
