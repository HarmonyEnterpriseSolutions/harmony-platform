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
# Copyright 2002-2007 Free Software Foundation
#
# FILE:
# GFKeyMapper.py
#
# DESCRIPTION:
"""
Handles physical to logical key mapping for GNUe Forms.
Also performs logical key to Events mapping.
"""
#
# NOTES:
#

from gnue.common.apps import errors


class InvalidKeystrokeName (errors.SystemError):
	"""
	This class is used for exceptions indicating that a
	keystroke that was received was not valid.
	"""
	pass


##
##
##
class BaseKeyMapper:
	"""
	A basic key mapper. This will normally serve most UI's input needs.

	Handles physical to logical key mapping for GNUe Forms.
	Also performs logical key to Events mapping.
	"""

	def __init__(self, userKeyMap):
		"""
		Stores the base key map and initializes the translations dict.
		"""
		self.__functionMap = userKeyMap
		self.__keyTranslations = {}


	def setUIKeyMap(self, keyset):
		"""
		Called by the UI class to setup their required key mappings.

		i.e., we need to know what wxPython thinks F1 is, etc
		"""
		self.__keyTranslations = keyset
		self._translateUserKeyMap()


	# ---------------------------------------------------------------------------
	# Install a key/event mapping
	# ---------------------------------------------------------------------------

	def setUserKeyMap (self, keymap):
		"""
		Install a key/event mapping.

		@param keymap: a dictinonary with tuples (basekey, shift-state, ctrl-state,
		  meta-state) as keys and event names as values
		"""

		for (keydef, event) in keymap.items ():
			for (oldkey, oldevent) in self.__functionMap.items ():
				if oldevent == event:
					del self.__functionMap [oldkey]
					self.__functionMap [keydef] = event
					break

		self._translateUserKeyMap ()

	#
	# Given a hash of the form:
	# { 'PREVBLOCK': 'Ctrl-F1' }
	# decode the key events and save into our usermap
	#
	def loadUserKeyMap(self, dict):
		usermap = {}

		for event in dict.keys ():
			val = dict [event]

			# Save any actual '+' keystrokes
			if val[:1] == '-':
				val = 'NEG' + val[1:]
			if val[-1:] == '-':
				val = val[:-2] + 'NEG'
			val = val.replace(' ','').replace('--','-NEG')

			keys = val.split ('-')

			base    = None
			shifted = False
			meta    = False
			ctrl    = False

			for key in keys:
				current = key.upper ()

				if current in ('CTRL','CONTROL'):
					ctrl = True
				elif current in ('META','ALT'):
					meta = True
				elif current in ('SHFT','SHIFT'):
					shifted = True
				elif vk.__dict__.has_key (current):
					base = vk.__dict__ [current]

				elif len(current) == 1:
					# We have to use the given key, so Ctrl-r is different than Ctrl-R
					base = ord (key)
				else:
					raise InvalidKeystrokeName, \
						u_("Invalid keystroke id '%(key)s' in keymap for '%(event)s'") \
						% {'key': key, 'event': event}

			if base is None:
				raise InvalidKeystrokeName, \
					u_("Invalid keystroke combination '%(comb)s' in keymap "
					"for '%(event)s'") \
					% {'comb' : dict [event],
					'event': event}

			usermap [(base, shifted, ctrl, meta)] = event.upper ()


		# Now, load any default keys they forgot to bind
		for key in DefaultMapping.keys():
			if  DefaultMapping[key] not in usermap.values() and \
				not usermap.has_key(key):
				usermap[key] = DefaultMapping[key]

		# Just in case...
		usermap.update( {
				(vk.TAB,      False, False, False) : 'NEXTENTRY',
				(vk.ENTER,    False, False, False) : 'ENTER',
				(vk.RETURN,   False, False, False) : 'ENTER'} )

		self.setUserKeyMap(usermap)


	def getEvent(self, basekey, shift=False, ctrl=False, meta=False):
		"""
		If an event is assigned to the specified keystroke then return
		that command.

		The keystroke is the UI-specific keystroke, not our virtual keys.  If
		a command isn't defined but a modifier key is held down then a command
		USERCOMMAND-[CTRL-][ALT-]key will be returned.

		This needs to stay as simple as possible as it gets called for
		each keystroke

		@returns: The command name or None if the keystroke isn't tied to an event.
		"""
		try:
			return (self._translatedUserKeyMap[(basekey, shift, ctrl, meta)], None)
		except KeyError:
			if (ctrl or meta) and basekey < 255:
				actionText = ""
				if ctrl and basekey < 64:
					basekey += 64  # TODO: Need a real way to get the key pressed when
				# control is depressed

				actionText += ctrl and 'CTRL-' or ''
				actionText += meta and 'ALT-' or ''
				actionText += '%s' % chr (basekey).upper ()
				return ("USERCOMMAND", actionText)
			else:
				return (None,None)

	#
	# Used internally to create a quick lookup
	# hash for time-sensitive methods.
	#
	def _translateUserKeyMap(self):
		self._translatedUserKeyMap = {}
		for keys in self.__functionMap.keys():
			base, sh, ctrl, meta = keys

			if self.__keyTranslations.has_key(base):
				base = self.__keyTranslations[base]
				if not isinstance(base, tuple):
					base = (base, )
			else:
				base = (base, )
			for i in base:
				self._translatedUserKeyMap[(i, sh, ctrl, meta)] = self.__functionMap[keys]


#####################################################################
#
#
class _VirtualKeys:
	"""
	A container class for the Virtual Key definitions.

	This helps keep our namespace clean.
	"""

	def __init__(self):
		self.F1        = -999
		self.F2        = -998
		self.F3        = -997
		self.F4        = -996
		self.F5        = -995
		self.F6        = -994
		self.F7        = -993
		self.F8        = -992
		self.F9        = -991
		self.F10       = -990
		self.F11       = -989
		self.F12       = -988
		self.INSERT    = -987
		self.DELETE    = -986
		self.HOME      = -985
		self.END       = -984
		self.PAGEUP    = -983
		self.PAGEDOWN  = -982
		self.UP        = -981
		self.DOWN      = -980
		self.LEFT      = -979
		self.RIGHT     = -978
		self.TAB       = -977
		self.ENTER     = -976
		self.RETURN    = -975
		self.BACKSPACE = -974
		self.X         = -973
		self.V         = -972
		self.C         = -971
		self.A         = -970
		self.Q         = -969
		self.ESC       = -968


#
# ..and the application will only
#   need one instance, so create one.
#
vk = _VirtualKeys()

# =============================================================================
# Default key to command event mappings
# =============================================================================
DefaultMapping = {

	#Key,          Shift, Ctrl,  Alt
	(vk.TAB,       True,  True,  False) : 'PREVBLOCK',
	(vk.TAB,       False, True,  False) : 'NEXTBLOCK',

	# Focus navigation
	(vk.ENTER,     False, False, False) : 'ENTER',
	(vk.ENTER,     True,  False, False) : 'NEWLINE',
	(vk.RETURN,    False, False, False) : 'ENTER',
	(vk.TAB,       False, False, False) : 'NEXTENTRY',
	(vk.TAB,       True,  False, False) : 'PREVENTRY',

	# Cursor movement, usually implemented by the UI widget
	(vk.LEFT,      False, False, False) : 'CURSORLEFT',
	(vk.RIGHT,     False, False, False) : 'CURSORRIGHT',
	(vk.END,       False, False, False) : 'CURSOREND',
	(vk.HOME,      False, False, False) : 'CURSORHOME',
	(vk.LEFT,      True,  False, False) : 'SELECTLEFT',
	(vk.RIGHT,     True,  False, False) : 'SELECTRIGHT',
	(vk.END,       True,  False, False) : 'SELECTTOEND',
	(vk.HOME,      True,  False, False) : 'SELECTTOHOME',
	(vk.BACKSPACE, False, False, False) : 'BACKSPACE',
	(vk.INSERT,    False, False, False) : 'MODETOGGLE',
	(vk.DELETE,    False, False, False) : 'DELETE',

	(vk.ESC,       False, False, False) : 'UNMODIFYFIELD',
	(vk.ESC,       True,  False, False) : 'UNMODIFYRECORD',

	# Old keybindings, now replaced by ALT+..., for compatibility (remove in
	# gnue-forms 0.7)
	(vk.UP,        False, False, True) : 'PREVRECORD',
	(vk.DOWN,      False, False, True) : 'NEXTRECORD',
	(vk.HOME,      False, False, True) : 'FIRSTRECORD',
	(vk.END,       False, False, True) : 'LASTRECORD',
#(vk.F5,        False, False, False) : 'MARKFORDELETE',
#(vk.F6,        False, False, False) : 'COMMIT',
#(vk.F11,       False, False, False) : 'ROLLBACK',
#(vk.F12,       False, False, False) : 'NEWRECORD',
}

#
# The application will only need one instance, so create one.
#
KeyMapper = BaseKeyMapper(DefaultMapping)
