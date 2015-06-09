#-*- coding: Cp1251 -*-

import re

def decorate_windows_error_13(group, name, message, message_match, detail):
	return 'user', name, u_(u"Access demied: %s") % (eval(message_match.groups()[0],{},{}),), detail

def decorate_windows_error_32(group, name, message, message_match, detail):
	return 'user', name, u_(u"Process can't access file because file used by another process: %s") % message_match.groups(), detail


PATTERNS = (
	(
		'application', 
		'WindowsError', 
		re.compile("""\[Error 32\][^']+'([^']+)'"""), 
		decorate_windows_error_32,
    ),

    (
		'application',
		'IOError', 
		re.compile("""(?u)\[Errno 13\] [\w\s]+: (u'[^']+')"""),
		decorate_windows_error_13,
    ),
)


def decorate_exception(group, name, message, detail):

	for pgroup, pname, pmessage, function in PATTERNS:
		if pgroup == group and pname == name:
			m = pmessage.search(message)
			if m:
				group, name, message, detail = function(group, name, message, m, detail)

	return group, name, message, detail
