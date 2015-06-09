# GNU Enterprise Common Library - Generic DBSIG2 database driver - Result set
#
# Copyright 2000-2007 Free Software Foundation
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
# $Id: ResultSet.py,v 1.7 2011/11/10 16:34:34 oleg Exp $

"""

"""

__all__ = ['ResultSet']

from gnue.common.datasources.drivers import DBSIG2

# =============================================================================
# ResultSet class
# =============================================================================

class ResultSet(DBSIG2.ResultSet):

	def _query_object_ (self, connection, table, fieldnames, condition, sortorder, distinct, parameters):
		#		print "--------------------------------"
		#		print """>>> _query_object_
		#...	table      = %s
		#...	fieldnames = %s
		#...	condition  = %s
		#...	sortorder  = %s
		#...	distinct   = %s
		#...	parameters = %s
		#""" % (table, fieldnames, condition, sortorder, distinct, parameters)
		#if condition:
		#	condition.showTree()

		sql, parameters = connection.getFnSignatureFactory()[table]['select'].genSql(parameters, sessionKey=connection._getSessionKey())

		#		print "EXECUTE: ", sql % parameters
		#		print

		# pass condition WHERE field = const as parameter,
		# (master-detail optimization)

		and_ = condition.findChildOfType('GCand', False)
		if and_:
			for eq in and_.findChildrenOfType('GCeq', False):
				field = eq.findChildOfType('GCCField', False)
				const = eq.findChildOfType('GCCConst', False)
				if field and const:
					parameters[field.name] = const.value

		return DBSIG2.ResultSet._query_object_(self,
			connection,
			sql,
			fieldnames,
			condition,
			sortorder,
			distinct,
			parameters
		)
