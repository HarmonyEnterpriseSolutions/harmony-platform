# GNU Enterprise Common Library - Events framework - Event dispatching
#
# Copyright 2001-2007 Free Software Foundation
#
# This file is part of GNU Enterprise
#
# GNU Enterprise is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or(at your option) any later version.
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
# $Id: EventController.py 9222 2007-01-08 13:02:49Z johannes $

"""
Class for event dispatching.
"""

from gnue.common.events import Event

__all__ = ['EventController']

RECYCLING = True

# =============================================================================
# Implmentation of an event dispatcher
# =============================================================================

class EventController(object):
	"""
	An EventController is responsible for dispatching events to registered
	listeners.
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self):

		self.__registered_events = {}
		self.__caching = False
		self.__cache = None

		# reenter depth, used for recycling
		# only one event object created for each
		self.__inline = 0
		if RECYCLING:
			self.__instances = {}

	if RECYCLING:
		def __getEvent(self, name, **params):
			event = self.__instances.get(self.__inline)
			if event:
				event.reinit(name, **params)
			else:
				self.__instances[self.__inline] = event = Event(name, **params)
			return event
	else:
		__getEvent = Event

	# -------------------------------------------------------------------------
	# Register listeners
	# -------------------------------------------------------------------------

	def register_listeners(self, events, user_data=None):
		"""
		Registers an event listener for a dictionary of events

		@param events: A dictionary of {'eventName': listenerFuction} pairs
		"""

		checktype(events, dict)

		for event, listener in events.iteritems():
			self.register_listener(event, listener, user_data)

	# -------------------------------------------------------------------------

	def register_listener(self, event, listener, user_data=None):
		"""
		Registers an event listener for a specific event

		@param event: The string representation of the event
		@param listener: The method to call for the event
		"""

		try:
			self.__registered_events[event].append((listener, user_data))
		except KeyError:
			self.__registered_events[event] = [(listener, user_data)]


	# -------------------------------------------------------------------------
	# Start storing events rather than dispatching them
	# -------------------------------------------------------------------------

	def start_event_cache(self):
		"""
		Causes the event controller to start storing events rather than
		dispatching them. It will continue to store events until
		L{stop_event_cache} is called.
		"""

		self.__caching = True
		self.__cache = []


	# -------------------------------------------------------------------------
	# Stop storing events
	# -------------------------------------------------------------------------

	def stop_event_cache(self):
		"""
		Notifies the event controller that is should start processing events
		again.  Any previously cached events are dispatched.
		"""

		self.__caching = False

		for event, params in self.__cache:
			self.dispatch_event(event, **params)

		self.__cache = None


	# -------------------------------------------------------------------------
	# Dispatch or cache a given event
	# -------------------------------------------------------------------------

	def dispatch_event(self, event, **params):
		"""
		Dispatch or cache the given event.

		@param event: L{Event} object or text identifying the type of event to
		    be cached or dispatched.  If text-style event names are used, then
		    name-based parameters are passing into the inline Event()
		    conversion.
		@returns: the event object's __result__ attribute
		"""

		self.__inline += 1
		assert gDebug(8, event)

		if self.__caching:
			self.__cache.append((event, params))
			return

		registered_events = self.__registered_events

		# Improve performance if there is no event listener
		if not registered_events:
			return

		if not isinstance(event, Event):
			event = self.__getEvent(event, **params)

		methods = []
		for key in ('__before__', event.__event__, '__after__'):
			methods.extend(registered_events.get(key, []))

		for handler, user_data in methods:
			event.user_data = user_data
			handler(event)
			if event.__error__ or event.__dropped__:
				break

		if event.__after__:
			for event, params in event.__after__:
				self.dispatch_event(event, **params)

		self.__inline -= 1
		return event.__result__


	# -------------------------------------------------------------------------
	# For compatability (DEPRECATED)
	# -------------------------------------------------------------------------

	registerEventListeners = register_listeners
	dispatchEvent = dispatch_event
	startCachingEvents = start_event_cache
	stopCachingEvents = stop_event_cache
