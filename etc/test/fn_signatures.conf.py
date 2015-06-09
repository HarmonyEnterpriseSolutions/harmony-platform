# -*- coding: Cp1251 -*-

"""
STEP function signatures
"""

fn_signatures = {

	#####################################################################################
	# Access
	#
	'_spr_user' : {
		'default' : 'user_login, user_password, user_name, user_sign, primary user_id',
	},

	'_spr_group' : {
		'default' : 'group_name, group_sysname, primary group_id',
	},

	'_spr_usergroup' : {
		'default' : 'usergroup_user_id, usergroup_group_id, primary usergroup_id',
	},

	'_spr_object' : {
		'select'  : 'user_id',
		'default' : 'object_parent_id, object_type_id, object_name, object_url, primary object_id',
	},

	'_spr_objectaccess' : {
		'default' : 'objectaccess_object_id, objectaccess_group_id, objectaccess_is_view, objectaccess_is_ins, objectaccess_is_edit, objectaccess_is_del, primary objectaccess_id',
	},
	#####################################################################################
	
}

fn_names = {
	
	# This is how table name converted to function name by default
	# you can add similar configs for another datasources

	# default dictionary
	'*' : {
		'select' : 'f_%s_list',
		'insert' : 'f_%s_ins',
		'update' : 'f_%s_edit',
		'delete' : 'f_%s_del',
	},

}

# execute config to see how it expands
if __name__ == '__main__':
	from gnue.common.datasources.drivers.sql.postgresql_fn.FnSignatureFactory import FnSignatureFactory
	import os
	FnSignatureFactory.getInstance(os.path.abspath(__file__)).dump()
