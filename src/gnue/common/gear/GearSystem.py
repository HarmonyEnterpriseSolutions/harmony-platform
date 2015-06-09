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
# GearSystem.py
#
# DESCRIPTION:
# tools to access files in a .gear archive
#
# NOTES:
#
# TODO:  * add Zipfile write support. i.e. write stringbuffer into zipfile
#          if .. close is called
#        * provide zipfile cache, i.e. load zipfile just once into memory

import cStringIO, zipfile, string

class GearFileSystem:

	def __init__(self,gearFileRes):
		self._gearFileRes=gearFileRes
		self._zf=zipfile.ZipFile(gearFileRes, mode="r")

	def openFile(self,filename,as_string=0):
		if as_string:
			return self._zf.read(filename)
		else:
			return cStringIO.StringIO(self._zf.read(filename))

	def addEntryToTree(self,pos,subtree,name,value):
		if len(name)-1==pos:
			subtree[name[pos]]=value
			return subtree
		else:
			if (not subtree.has_key(name[pos])) or \
				(type(subtree[name[pos]])!=type({})):
				subtree[name[pos]]={}

			subtree[name[pos]]=self.addEntryToTree(pos+1, \
					subtree[name[pos]], \
					name, \
					value)
			return subtree




	def getArchiveListing(self,as_tree=1):
		if as_tree:
			treelist={}

			for i in self._list:

				ps=string.split(i,"/")

				if ps[len(ps)-1]=="README":
					value=self._zf.read(i)
					value=string.join(string.split(value,"\n"),"<BR>\n")

				else:
					value=self._gearFileRes+i

				treelist=self.addEntryToTree(0,treelist,ps,value)

			return treelist

		else:
			if not hasattr(self,'_list'):
				self._list=self._zf.namelist()

			return self._list


	def hasFile(self,filename):

		if not hasattr(self,'_list'):
			self._list=self._zf.namelist()

		return filename in self._list
