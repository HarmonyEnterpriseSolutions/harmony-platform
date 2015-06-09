# GNU Enterprise Common Library - Events framework - Events
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
# $Id: Event.py 9222 2007-01-08 13:02:49Z johannes $

"""
Implementation of an event.
"""

__all__ = ['Event']

# =============================================================================
# Implementation of an Event
# =============================================================================

class Event(object):
	"""
	An Event is the actual event object passed back and forth between the event
	listeners.

	Any parameters passed to the Event's __init__ are added as attributes of
	the event. The first attribute, however, should always be the case
	sensitive event name.

	Creating an Event:

	>>> myEvent = Event('myEventName', color='Blue', x=1, y=2)
	>>> myEvent.color
	'Blue'
	>>> myEvent.x
	1
	>>> myEvent.y
	2
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, event, **params):
		"""
		@param event: The name of the event. GNUe event listeners register the
		    names of the events they wish to receive.
		@param data: B{OBSOLETE: Do not use}
		@param params: Allows the event to accept any argument names you like.
		    Examples would be things like::
		        caller = self
		        x = 15
		        vals = {'name': 'Bob', 'title': 'Mr'}
		"""
		self.__dict__.update(params)

		self.__event__ = event
		self.__result__ = None
		self.__dropped__ = 0
		self.__error__ = 0
		self.__errortext__ = ""
		self.__after__ = []


	def reinit(self, event, **params):
		self.__dict__.clear()
		self.__init__(event, **params)

	# -------------------------------------------------------------------------
	# Nice string representation
	# -------------------------------------------------------------------------

	def __repr__(self):

		return "<Event %s at %s>" % (self.__event__, id(self))


	# -------------------------------------------------------------------------
	# Result property
	# -------------------------------------------------------------------------

	def getResult(self):
		"""
		Returns the result value stored in the event by the L{setResult}
		function.

		@return: The result value of the event.
		"""

		return self.__result__

	# -------------------------------------------------------------------------

	def setResult(self, value):
		"""
		Can be used by an event listener to assign a return value to an event.
		The result will be returned by the event controller's
		L{dispatchEvent<gnue.common.events.EventController.EventController>}
		function. It can also be obtained by the L{getResult} function.

		@param value: The result value to assign to the event. It can be
		    anything that is concidered valid python.
		"""

		self.__result__ = value

	# -------------------------------------------------------------------------

	result = property(getResult, setResult)


	# -------------------------------------------------------------------------
	# Get the name of the event
	# -------------------------------------------------------------------------

	def getEvent(self):
		"""
		Returns the name of the event.

		@return: The name of the event
		"""

		return self.__event__

	# -------------------------------------------------------------------------

	event = property(getEvent, None)


	# -------------------------------------------------------------------------
	# Drop the event
	# -------------------------------------------------------------------------

	def drop(self):
		"""
		Drop the event; no additional event listeners will recieve the event.
		"""

		self.__dropped__ = True


	# -------------------------------------------------------------------------
	# Set the event's error flag and drop the event
	# -------------------------------------------------------------------------

	def setError(self, text = ""):
		"""
		Set the event's error flag and drop it (see L{drop}).

		@param text: Text describing the error.
		"""

		self.__error__ = 1
		self.__errortext__ = text

	# -------------------------------------------------------------------------

	def getError(self):

		if self.__error__:
			return (self.__errortext__ or 'Unnamed Error')
		else:
			return None

	# -------------------------------------------------------------------------

	error = property(getError, setError)


	# -------------------------------------------------------------------------
	# Add an event to the event queue
	# -------------------------------------------------------------------------

	def dispatch_after(self, event, **params):
		"""
		Adds an event to the event queue that will be dispatched upon this events
		completion. The arguments to this function match those used in creating an
		event.

		Sample Usage:

		>>> from gnue.common.events.Event import *
		>>> myEvent = Event('myEventName', color = 'Blue', x = 1, y = 2)
		>>> myEvent.dispatchAfter('theNextEvent', name = 'FSF')
		"""

		self.__after__.append((event, params))

	def __str__(self):
		params = dict([
				(key, value)
				for key, value in self.__dict__.iteritems()
				if not (key.startswith('__') and key.endswith('__'))
			])
		return "<%s %s (%s)>" % (self.__class__.__name__, self.event, ', '.join(["%s=%s" % (name, value) for name, value in params.iteritems()]))

	# -------------------------------------------------------------------------
	# Old function names (DEPRECATED)
	# -------------------------------------------------------------------------

	dispatchAfter = dispatch_after
