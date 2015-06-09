# GNU Enterprise Common Library - Utilities - File & URI reading/opening
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
# $Id: file.py 9549 2007-05-05 12:13:54Z reinhard $
"""
Helper functions for opening/reading files or network resources.
"""


import os
import urllib
import urllib2
import urlparse
import sys
import cStringIO


# ===================================================================
# Convert a file name or URI into a URI (prepend file://)
# ===================================================================
def to_uri (resource):
	"""
	Try to turn a resource into a valid URI
	(because C:\ confuses some tools).

	i.e., prepend file:// to an absolute file name.
	"""
	if not resource.find(':'):
		return 'file://%s' % resource
	else:
		drive = os.path.splitdrive(resource)
		if len(drive[0]) and drive[0] == resource[:len(drive[0])]:
			return 'file://%s' % resource
		else:
			return resource


# ===================================================================
# string_to_buffer
# ===================================================================
def to_buffer(item):
	"""
	Convert a string to a file object if it is not already.

	    >>> to_buffer('This is text\nFoo.').read()

	    >>> my_file = open('/etc/passwd')
	    >>> to_buffer(my_file) == my_file
	    >>> myfile.read()
	    <<< True
	"""
	if hasattr(item, 'read'):
		return item
	return cStringIO.StringIO(item)



# ===================================================================
# Open a file or a URI as a file object
# ===================================================================
def open_uri(resource, mode='r'):
	"""
	Open a file or URI resource,
	properly handling drive letters.

	For example,

	  >>> resource = open_uri('/etc/passwd')
	  >>> resource = open_uri(r'A:\MyDir\MyFile')
	  >>> resource = open_uri('file:///etc/passwd')
	  >>> resource = open_uri('http://www.google.com/')

	"""
	drive = os.path.splitdrive(resource)
	if len(drive[0]):
		return open(resource, mode)
	else:
		(urltype, host, path, param, query, frag) = urlparse.urlparse(resource)

		# check for .gear files
		if resource[-5:] == ".gear":
			host = resource
			path = ""
			urltype = "gear"

		# normal files are directly passed to the application
		if urltype != "gear":
			if urltype in ('file', ''):
				return open(path, mode)
			if not mode.startswith('r'):
				raise IOError(
					"Network resource '%s' can only be opened as read only." % (
						resource))
			return urllib2.urlopen(resource)

		else:

			from gnue.common.gear.GearSystem import GearFileSystem

			# fix for a bug in URLPARSE
			if host=="":
				# path="//host/path" -> path=path host=host
				host, path ="/".split(path[2:],1)

			# check if host ends in ".gear"
			if host[-5:]!=".gear":
				host += ".gear"

			# 1. search for gear in the local directory
			try:
				gear=GearFileSystem(urllib.unquote(host))

			except:
				# 2. search in the package directory
				if sys.platform=="win32":
					host=sys.prefix+"/packages/"+host
				else:
					host=os.environ["HOME"]+"/gnue/packages/"+host

				gear=GearFileSystem(urllib.unquote(host))

			if len(path):
				return gear.openFile(path)

			# if no path provided, create a navigator file for this archive
			else:

				# check if the zip file contains a default navigator file
				if gear.hasFile("default.gpd"):
					# TODO: change navigator file and add relative paths
					# i.e. in case of gear-resource="sample/test.gear"
					#      gear://test.gear/mypath/my.gfd ->
					#      gear://sample%2Ftest.gear/mypath/my.gfd
					return gear.openFile("default.gpd")


				# convert a single filename to a full gear url
				if resource[:5] != "gear:":
					resource="gear://"+urllib.quote(resource,"")+"/"

				gear._gearFileRes=resource

				filelist = gear.getArchiveListing()

				from gnue.common.gear.NavigationBuilder import buildNavigatorFile

				navi = buildNavigatorFile(filelist,host,1)

				return cStringIO.StringIO(navi)
