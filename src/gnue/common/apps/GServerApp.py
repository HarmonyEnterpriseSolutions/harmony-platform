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
# GServerApp.py
#
# DESCRIPTION:
# Class that provides a basis for GNUe server applications.
#
# NOTES:
# This will eventually have features only needed by "server"
# applications, such as abstracted client RPC calls via
# CORBA, RPC-XML, SOAP, etc and daemon/forking/threading.
#

from gnue.common.apps.GBaseApp import GBaseApp
from gnue.common.apps import GConfig, errors
from gnue.common.apps.GLogger import Logger
import sys
import os
import os.path
import signal


class ServerRunningError (errors.UserError):
	def __init__ (self, pid):
		msg = u_("The server is already running on pid %s") % pid
		errors.UserError.__init__ (self, msg)


class GServerApp(GBaseApp):

	def __init__(self, connections=None, application=None, defaults=None):

		self.COMMAND_OPTIONS.append (
			[ 'foreground','Z','no-detach',0,0, None,
				u_("Do not send the server into the background. For a POSIX system, "
					"this option keeps the server process from forking and detaching "
					"from its controlling terminal.")],
		)

		self.COMMAND_OPTIONS.append (
			['pidfile', 'P', 'pidfile', True,
				'/var/run/gnue/%s.pid' % application or 'gnue', u_('pid-file'),
				u_("Filename to store the server's process id.")])

		GBaseApp.__init__(self, connections, application, defaults)

		if not self.OPTIONS ['foreground']:
			if os.name == 'posix':
				self.__removeStaleFile ()
				self.__createPidFile (0)

		try:
			signal.signal (signal.SIGTERM, self._terminate)
		except ValueError:
			# signal only works in main thread, but
			# in a win32 service we are not in the main thread here
			pass



	# This can be overwritten by code necessary
	# for startup.  If overwritten, do not first
	# call the original GServerApp.run(self) as
	# this would send to background immediately.
	# Instead, call the original GServerApp.run(self)
	# after you are sure you are finished with
	# startup code and are ready to go to server
	# mode.
	def run(self):

		# Fork, if applicable/possible, and send to background
		if not self.OPTIONS ["foreground"]:
			self.daemonize ()


	# Called when a request to shutdown the server is received
	def shutdown(self):
		pass


	# Turn ourselves into a daemon/service/etc.
	# Returns 1 if program successfully converted,
	# 0 otherwise.
	#
	def daemonize (self):

		# For an overview of what we're doing here,
		# check out the Unix Programmer's FAQ at:
		# http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16

		# We enclose these actions in try: blocks so that
		# this doesn't fail on non-Unix environments.

		self.__removeStaleFile ()

		try:
			# Fork #1
			pid = os.fork()
			if pid != 0:
				# Close main process
				sys.exit(0)

			# Open new filehandles for stdin, stdout, stderr
			# TODO: This may eventually be log files.
			sin = open('/dev/null','r')
			sout = open('/dev/null','w')
			serr = open('/dev/null','w')

		except AttributeError:
			return 0
		except IOError:
			return 0
		except OSError:
			return 0


		# Disassociate ourselves
		try:
			os.chdir('/')
			os.setsid()
			os.umask(0)
		except AttributeError:
			pass
		except OSError:
			pass


		try:
			# Fork #2
			pid = os.fork()
			if pid != 0:
				self.__createPidFile (pid)

				sys.exit(0)
		except OSError:
			pass


		# Redirect all the stdio channels.
		# (after all, we have no terminal :)
		try:
			sys.stdin.close()
			sys.stdin = sin

			sys.stdout.close()
			sys.stdout = sout

			sys.stderr.close()
			sys.stderr = serr
		except AttributeError:
			pass

		return 1


	# ---------------------------------------------------------------------------
	# Create a new pid file
	# ---------------------------------------------------------------------------

	def __createPidFile (self, pid):
		"""
		This function creates a new pid file for the current process.

		@param pid: Process id to store in the pid file
		"""

		piddir = os.path.dirname (self.OPTIONS ['pidfile'])
		if not os.path.exists (piddir):
			os.makedirs (piddir)

		pidfile = open (self.OPTIONS ['pidfile'], 'w')
		pidfile.write ("%s%s" % (pid, os.linesep))
		pidfile.close ()


	# ---------------------------------------------------------------------------
	# Remove a stale pid file
	# ---------------------------------------------------------------------------

	def __removeStaleFile (self):
		"""
		This function checks for a stale pid file. If a file exists, this function
		raises a ServerRunningError exception if the process is till alive.
		"""

		if os.path.exists (self.OPTIONS ['pidfile']):
			pidfile = open (self.OPTIONS ['pidfile'], 'r')

			try:
				oldPid = int (pidfile.readline ().strip ())

				if oldPid:
					try:
						os.kill (oldPid, 0)

					except OSError:
						# remove the stale pid-file
						os.unlink (self.OPTIONS ['pidfile'])

					else:
						raise ServerRunningError, oldPid

			finally:
				pidfile.close ()


	# ---------------------------------------------------------------------------
	# Handle a SIGTERM signal
	# ---------------------------------------------------------------------------

	def _terminate (self, signal, frame):
		"""
		This function handles a SIGTERM signal and removes the pid-file if the
		server is running in the background.
		"""

		if not self.OPTIONS ["foreground"] and \
			os.path.exists (self.OPTIONS ['pidfile']):
			os.unlink (self.OPTIONS ['pidfile'])

		sys.exit ()
