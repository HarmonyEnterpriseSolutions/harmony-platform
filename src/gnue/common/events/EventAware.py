# GNU Enterprise Common Library - Events framework - Base classes
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
# $Id: EventAware.py 9222 2007-01-08 13:02:49Z johannes $

"""
Base class for objects using events.
"""

__all__ = ['EventAware']


# =============================================================================
# Base for an object that sends and receives events
# =============================================================================

class EventAware(object):
	"""
	The base class for an object that sends and receives events

	Sample Usage::

	    from gnue.common import events
	    class MyClass(events.EventAware):
	        def __init__(self)
	            self.eventController = events.EventController()
	            events.EventAware.__init__(self, self.eventController)
	            self.register_listener('myEvent1', self.eventOneHandler)
	            self.register_listener('myEvent2', self.eventTwoHandler)

	        def eventOneHandler(self, event)
	            print "I'm an event named ", event.event

	        def eventTwoHandler(self, event)
	            print "My event is named ", event.event

	    test = MyClass()
	    test.dispatch_event('myEvent2')
	"""

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, controller):

		self.dispatch_event = controller.dispatch_event
		self.register_listeners = controller.register_listeners
		self.register_listener = controller.register_listener

		# Old function names (DEPRECATED)
		self.dispatchEvent = self.dispatch_event
		self.registerEventListeners = self.register_listeners
