# GNU Enterprise Forms - The Forms Client
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
# $Id: GFClient.py,v 1.16 2015/03/28 00:09:06 oleg Exp $

"""
configures the controling GFInstance and passes control to it
"""
from src.gnue.forms.uidrivers.java import config, UIdriver

__revision__ = "$Id: GFClient.py,v 1.16 2015/03/28 00:09:06 oleg Exp $"

from gnue.common.datasources.GConnections import GConnections
from gnue.forms.GFInstance import GFInstance
from gnue.common.apps.GConfig import GConfig
from gnue.forms.GFConfig import ConfigOptions
from gnue.common.apps import GDebug


class InstanceNotFoundError(KeyError):
	pass

# =============================================================================
# GNU Enterprise Forms Client
# =============================================================================

class GFClient(object):

	"""
	one per browser
		creates GFInstance
	"""

	def __init__ (self, appContextUrl, debug=False):
		assert appContextUrl
		self._appContextUrl = appContextUrl

		self._instances = {}
		self._configurationManager = GConfig('forms', ConfigOptions, configFilename = 'gnue.conf')
		self._configurationManager.registerAlias('gConfigForms', 'forms')
		self._debug = debug

		if config.GNUE_DEBUG_LEVEL:
			GDebug.setDebug(config.GNUE_DEBUG_LEVEL)

	def setGetUserContextBySid(self, getUserContextBySid):
		self._getUserContextBySid = getUserContextBySid
	
	def set_get_clientproperty_storage(self, get_storage):
		"""set by javaui servlet"""
		self.__clientproperty_storage = None
		self.__get_clientproperty_storage = get_storage

	def get_clientproperty_storage(self):
		"""called from GFInstance to get storage"""
		if self.__clientproperty_storage is None:
			self.__clientproperty_storage = self.__get_clientproperty_storage()
		return self.__clientproperty_storage
	
	def processCalls(self, hiveId, calls):
		"""
		dispatch event from applet
		redirect it to corresponding GFUserInterface
		"""
		# if client is just started but instance already exists, force new instance to be created
		# this shound never happen, except 8-byte random repeated when generating hiveId on client
		if not calls and hiveId in self._instances:
			del self._instances[hiveId]

		# have client with calls but instance not exist, raise error that client must restart
		if calls and not hiveId in self._instances:
			raise InstanceNotFoundError

		return self.getInstance(hiveId)._uiinstance.processCalls(calls)


	def getInstance(self, hiveId):
		try:
			instance = self._instances[hiveId]
		except KeyError:
			self._instances[hiveId] = instance = self.createInstance(hiveId)

		# needed to retrieve user context by sid stored in GFInstance.globals
		instance._uiinstance.setGetUserContextBySid(self._getUserContextBySid)

		return instance
			

	def createInstance(self, id):
		"""
		Responsible for setting up the desired UI driver, parsing command line
		arguments, loading the desired form, and passing control to the GFInstance
		that will control the application.
		"""
		connectionsFile = ''
		connections = GConnections(connectionsFile, loginOptions = {})

		instance = GFInstance(self, connections, UIdriver, True, {})
		instance._uiinstance.initRemoteHive(id)
		instance._uiinstance._debug = self._debug

		# needed only to call GFInstance.show_exception
		instance._uiinstance._setInstance(instance)

		try:
			instance.run_from_file(self._appContextUrl + "/forms/" + config.START_FORM, config.START_FORM_PARAMETERS)
		except UIdriver.MainLoopEntered:
			pass

		return instance


	def closeAllConnections(self):
		for instance in self._instances.values():
			instance.connections.closeAll()


	# this was for webkit session storage
	#def __getstate__(self):
	#	dict = self.__dict__.copy()
	#	dict['_getUserContextBySid'] = None
	#
	#	instances = dict['_instances']
	#	for id in instances.iterkeys():
	#		if instances[id]:
	#			print "* DynamicSessionTimeout reached. Can't save gnue intances. gnue instance (id=%s) will be dropped" % (id,)
	#		instances[id] = None
	#	
	#	return dict
	
