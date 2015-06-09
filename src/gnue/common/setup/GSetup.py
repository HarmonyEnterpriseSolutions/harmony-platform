# GNU Enterprise Common Library - Installation Helper For Tools
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
# $Id: GSetup.py,v 1.4 2003/10/06 18:33:16 reinhard Exp $

import sys
import string
import time
import os
from distutils import log
from distutils.core import setup
from distutils.filelist import FileList
import distutils.command.sdist
import distutils.command.build
import distutils.command.install
import gnue.paths
from gnue.common.utils import version
from gnue.common.setup import ChangeLog

# -----------------------------------------------------------------------------
# Check Python version
# -----------------------------------------------------------------------------

try:
	if sys.hexversion < 0x02030000:
		raise AttributeError
except AttributeError:
	print "-" * 70
	print """
  You are running Python %s.

  GNU Enterprise requires at least Python 2.3.
  If you have a later version installed, you should run setup.py
  against that version. For example, if you have Python 2.3
  installed, you may need to run:

       python2.3 setup.py
""" % string.split(sys.version)[0]
	print "-" * 70
	sys.exit (1)

# -----------------------------------------------------------------------------
# Global GSetup instance
# -----------------------------------------------------------------------------

_setup = None

# =============================================================================
# sdist: build files to be distributed first
# =============================================================================

class sdist (distutils.command.sdist.sdist):

	def run (self):
		global _setup

		_setup.do_build_files ('sdist')
		distutils.command.sdist.sdist.run (self)

	def prune_file_list(self):
		distutils.command.sdist.sdist.prune_file_list(self)
		self.filelist.exclude_pattern('*.dist_template', anchor=0)

	def make_release_tree (self, base_dir, files):
		distutils.command.sdist.sdist.make_release_tree (self, base_dir, files)
		self.process_templates(base_dir)
		_setup.do_build_svnrev (os.path.join(base_dir, 'src', 'svnrev.py'))

	def process_templates(self, target):

		# Build list of files to be processed.
		filelist = FileList()
		if filelist.include_pattern('*.dist_template', anchor=0) == 0:
			# Nothing to do.
			return

		# FIXME: For compatibility with old packages not yet using the version
		# module. Change to unconditional import in gnue-common 0.8.
		try:
			from src import version
		except:
			return

		# List of keywords to replace.
		keywords = {
			':PACKAGE:': self.distribution.get_name(),
			':TITLE:': self.distribution.get_description(),
			':VERSION:': self.distribution.get_version(),
			':MAJOR:': str(version.major),
			':MINOR:': str(version.minor),
			':PHASE:': str(version.phase),
			':BUILD:': str(version.build),
			':SVN:': str(version.svn),
			':DATE_ISO:': time.strftime('%Y-%m-%d', time.gmtime()),
			':DATE_RFC:': time.strftime('%a, %d %b %Y', time.gmtime()),
			':TIME:': time.strftime('%H:%M:%S', time.gmtime())}
		# Hack for version numbering schemes that are limited to x.y.z.
		if version.phase == 'final':
			keywords[':FINAL:'] = str(version.build)
		else:
			keywords[':FINAL:'] = '0'

		for src in filelist.files:
			dst = os.path.join(target, src[:-14])
			args = (src, dst, keywords)
			self.execute(self.__process_template, args,
				"generating %s from %s" % (dst, src))

	def __process_template(self, src, dst, keywords):
		infile = open(src, 'r')
		content = infile.read()
		infile.close()
		for keyword, value in keywords.iteritems():
			content = content.replace(keyword, value)
		outfile = open(dst, 'w')
		outfile.write(content)
		outfile.close()
		# Let destination file have the same mode than the source file.
		os.chmod(dst, os.stat(src).st_mode)

# =============================================================================
# build: if done from SVN, build files to be installed first
# =============================================================================

class build (distutils.command.build.build):

	def run (self):
		global _setup

		if not os.path.isfile ("PKG-INFO"):         # downloaded from SVN?
			_setup.do_build_files ('build')
		distutils.command.build.build.run (self)
		if not os.path.isfile ("PKG-INFO"):
			_setup.do_build_svnrev (os.path.join(self.build_lib, 'gnue',
					_setup.package[5:].lower(), 'svnrev.py'))

# =============================================================================
# install: Some user_options are no longer allowed
# =============================================================================

class install (distutils.command.install.install):

	# Commented out because sometimes, to create packages, we want to install
	# other tools in a different target directory than common is installed
	#user_options = distutils.command.install.install.user_options

	#allowed_options = ["root=", "compile", "no-compile", "optimize=", "force",
	#                   "skip-build", "record="]

	#user_options = [opt for opt in user_options if opt [0] in allowed_options]

	user_options = distutils.command.install.install.user_options
	i = 0
	for option in user_options:
		i = i + 1
		if option [0] == "install-data=":
			user_options.insert (i, ("install-config=", None,
					"installation directory for configuration files"))
			break

	# ---------------------------------------------------------------------------
	# Initalize options
	# ---------------------------------------------------------------------------

	def initialize_options (self):
		distutils.command.install.install.initialize_options (self)
		self.install_config = None

	# ---------------------------------------------------------------------------
	# Finalize options - set all install targets
	# ---------------------------------------------------------------------------

	def finalize_options (self):

		if self.install_lib     is None: self.install_lib     = gnue.paths.lib
		if self.install_scripts is None: self.install_scripts = gnue.paths.scripts
		if self.install_data    is None: self.install_data    = gnue.paths.data
		if self.install_config  is None: self.install_config  = gnue.paths.config

		distutils.command.install.install.finalize_options (self)

	# ---------------------------------------------------------------------------
	# install.run: generate and install path dependent files afterwards
	# ---------------------------------------------------------------------------

	def run (self):
		global _setup

		_setup.check_dependencies ()

		self.__outputs = []

		# install translations
		if os.path.isdir ('po'):
			# copy files
			for f in os.listdir ('po'):
				if f [-4:] == '.gmo':
					src = os.path.join ('po', f)
					dst = os.path.join (self.install_data, 'share', 'locale', f [:-4],
						'LC_MESSAGES')
					self.mkpath (dst)
					dst = os.path.join (dst, _setup.package + '.mo')
					self.copy_file (src, dst)
					self.__outputs.append (dst)

		distutils.command.install.install.run (self)

	# ---------------------------------------------------------------------------
	# install.get_outputs: list all installed files
	# ---------------------------------------------------------------------------

	def get_outputs (self):
		return distutils.command.install.install.get_outputs (self) \
			+ self.__outputs

# =============================================================================
# GSetup: Basic class for setup scripts of GNUe packages
# =============================================================================

class GSetup:

	# ---------------------------------------------------------------------------
	# Abstract methods: setup.py scripts generally override these
	# ---------------------------------------------------------------------------

	def set_params (self, params):
		pass

	def build_files (self, action):
		pass

	def check_dependencies (self):
		pass

	# ---------------------------------------------------------------------------
	# Build files if called from SVN
	# ---------------------------------------------------------------------------

	def do_build_files (self, action):

		if os.name == 'posix':

			# First check if we have everything installed we need to build the
			# distribution

			if os.path.isdir ('po'):
				# xgettext
				if os.system ("pygettext --version > /dev/null") != 0:
					log.fatal("Could not find 'pygettext'. Strange.")
					log.fatal("It should be included in the Python distribution.")
					sys.exit (1)

				# msgmerge
				if os.system ("msgmerge --version > /dev/null") != 0:
					log.fatal("Could not find 'msgmerge'. Please install Gettext.")
					sys.exit (1)

				# msgfmt
				if os.system ("msgfmt --version > /dev/null") != 0:
					log.fatal("Could not find 'msgfmt'. Please install Gettext.")
					sys.exit (1)

			# -----------------------------------------------------------------------

			if action == 'sdist':
				# build ChangeLog file
				log.info("building ChangeLog")
				ChangeLog.build ()

			# build translations
			if os.path.isdir ('po'):
				log.info("building translations")
				if os.system ("cd po && make gmo") != 0:
					sys.exit (1)

		else:
			# on non posix systems just run msgfmt on existing .po files
			if os.path.isdir ('po'):
				# msgfmt.py
				argv0_path = os.path.dirname(os.path.abspath(sys.executable))
				sys.path.append(argv0_path + "\\tools\\i18n")

				msgfmtOK = 0
				try:
					import msgfmt
					msgfmtOK = 1
				except:
					pass

				if msgfmtOK == 1:
					# pygettext.py exist in Python, but no msgmerge, so
					# just create a placeholder...
					potfile = open('po/'+ self.package +'.pot', 'w')
					potfile.write("#placeholder")
					potfile.close()

					# build translations
					log.info("building translations")
					for f in os.listdir('po'):
						if f[-3:] == '.po':
							msgfmt.make ('po/'+f, 'po/'+f[:-3]+'.gmo')
							msgfmt.MESSAGES = {}

		# -------------------------------------------------------------------------

		# do package specific stuff
		self.build_files (action)

	# ---------------------------------------------------------------------------
	# Build files if called from SVN
	# ---------------------------------------------------------------------------

	def do_build_svnrev (self, filename):

		log.info("building svnrev.py")
		output = open(filename, 'w')
		output.write('svnrev = %r' % version.get_svn_revision('src'))
		output.close()

	# ---------------------------------------------------------------------------
	# Helper methods for descendants
	# ---------------------------------------------------------------------------

	def allfiles (self, directory):
		directory = os.path.normpath (directory)
		exclude = [".svn", "CVS", "README.cvs", ".cvsignore", "Makefile"]
		return [directory + "/" + file for file in os.listdir (directory) \
				if not file in exclude and
			not os.path.isdir (os.path.join (directory, file))]

	# ---------------------------------------------------------------------------
	# Get all packages in a directory
	# ---------------------------------------------------------------------------

	def __get_packages (self, directory, package):
		content = os.listdir (directory)
		result = []
		if "__init__.py" in content:
			result = [package]
			for name in content:
				fullname = os.path.join (directory, name)
				if os.path.isdir (fullname):
					result = result + self.__get_packages (fullname, package + "." + name)
		return result

	# ---------------------------------------------------------------------------
	# Call the actual setup routine
	# ---------------------------------------------------------------------------

	def run (self):
		global _setup

		# set global variable
		_setup = self

		setup_params = {"cmdclass_sdist": sdist,
			"cmdclass_build": build,
			"cmdclass_install": install,
		}

		_setup.set_params (setup_params)

		# make package available
		self.package = setup_params ["name"]


		# find out all packages
		if not setup_params.has_key ("packages"):
			packages = []
			for module, directory in setup_params["package_dir"].items ():
				packages = packages + self.__get_packages (directory, module)
			setup_params ["packages"] = packages

		# remove data files that are not available
		for target, files in setup_params ["data_files"]:
			i = 0
			while i < len (files):
				file = files [i]
				if os.path.isfile (file):
					i += 1
				else:
					log.warn("warning: did not find file %s" % file)
					files.remove (file)

		# now call setup
		setup (name             = setup_params ["name"],
			version          = setup_params ["version"],
			description      = setup_params ["description"],
			long_description = setup_params ["long_description"],
			author           = setup_params ["author"],
			author_email     = setup_params ["author_email"],
			url              = setup_params ["url"],
			license          = setup_params ["license"],
			packages         = setup_params ["packages"],
			package_dir      = setup_params ["package_dir"],
			scripts          = setup_params ["scripts"],
			data_files       = setup_params ["data_files"],

			# Override certain command classes with our own ones
			cmdclass = {"sdist":   setup_params["cmdclass_sdist"],
				"build":   setup_params["cmdclass_build"],
				"install": setup_params["cmdclass_install"]})
