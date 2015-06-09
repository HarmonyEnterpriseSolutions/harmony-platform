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
# NavigationBuilder.py
#
# DESCRIPTION:
# builds a Navigation file out of a directory listing
#
# NOTES:
#
# HISTORY:
#

def buildNavigatorFile(list,name,top=0):
	if top:
		navi='<?xml version="1.0"?>\n\n'+\
			'<processes title="Package '+name+'">\n'
	else:
		navi='<process title="'+name+'" id="'+name+'">\n'

	for i in list.keys():
		if type(list[i])==type(""):
			if i[-4:]==".grd":
				navi=navi+'<step type="report" location="'+list[i]+\
					'" title="'+i+'">\n<description><![CDATA['+\
					'<CENTER><H3>'+i+'</H3></CENTER>'+\
					']]></description>\n</step>\n'
			elif i[-4:]==".gfd":
				navi=navi+'<step type="form" location="'+list[i]+\
					'" title="'+i+'">\n<description><![CDATA['+\
					'<CENTER><H3>'+i+'</H3></CENTER>'+\
					']]></description>\n</step>\n'
			elif i[-4:]==".gnd":
				navi=navi+'<step type="navigator" location="'+list[i]+\
					'" title="'+i+'">\n<description><![CDATA['+\
					'<CENTER><H3>'+i+'</H3></CENTER>'+\
					']]></description>\n</step>\n'
			elif i=="README":
				navi=navi+'<description><![CDATA[<H3 ALIGN="CENTER">README</H3>'+\
					list[i]+']]></description>\n'
		else:
			navi=navi+buildNavigatorFile(list[i],i)

	if top:
		navi=navi+'</processes>\n'
	else:
		navi=navi+'</process>\n'
	return navi
