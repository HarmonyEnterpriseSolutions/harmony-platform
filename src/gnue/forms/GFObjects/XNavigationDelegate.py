class XNavigationDelegate(object):
	"""
	required:
		#def ui_focus_out(self):
		#def ui_set_focused_entry(self, gfEntry):

	"""

	def isCellEditable(self):
		return True

	def isNavigationDelegationEnabled(self):
		return True

	def escapeEntry(self, entry):
		"""
		return False if no handling
		"""
		return False