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
# FILE:
# GLogger.py
#
# DESCRIPTION:
# Class that provides logging facilities for GNUe apps.
#
# NOTES:
# This package implements both a Logger class and a system wide
# logging instance.  If you need just one logging system for your app,
# you can just use the openlog, closelog, and log methods. If you need
# more control over your logs or may have several logging destinations,
# you will want to use the Logger class.


from gnue.common.apps import GDebug
import time, string


_logger = None


class LogIOError (StandardError):
	pass


class Logger:

	def __init__(self, logfile):
		try:
			self._filehandle = open(logfile,'a')
			self.log ('---- [ Logging started ] ----')
		except IOError, mesg:
			raise LogIOError, "[IOError] %s" % (mesg)


	def __del__(self):
		try:
			self.closelog()
		except:
			pass


	def closelog(self):
		try:
			self.log ('---- [ Logging stopped ] ----')
			close (self._filehandle)
		except:
			pass
		self._filehandle = None


	def log(self, *messages):
		timestamp = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))

		# TODO: Is this thread safe?

		for messageset in messages:
			for message in string.split("%s" % messageset,'\n'):
				assert gDebug(2,'>> Logger: [%s] %s' % (timestamp, message))
				try:
					self._filehandle.write('[%s] %s\n' % (timestamp, message))
				except IOError, mesg:
					raise LogIOError, "[IOError] %s" % (mesg)



def openlog(logfile):
	global _logger
	_logger = Logger(logfile)


def closelog():
	global _logger
	if _logger:
		_logger.closelog()
	_logger = None


def log(*messages):
	if _logger:
		for message in messages:
			_logger.log(message)



if __name__ == '__main__':
	openlog('test.log')
	log ('Message1')
	log ('Message2')
	log ('Message3')
	closelog()
