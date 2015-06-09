from src.gnue.common.datasources.drivers.Base.Record import ACCESS

__all__ = ['ACCESS', 'accessToEditable', 'accessToDeletable', 'editableToAccess', 'deletableToAccess']

__EDITABLE_TO_ACCESS = {
	'N'      : ACCESS.NONE,
	'NEW'    : ACCESS.INSERT,
	'UPDATE' : ACCESS.UPDATE,
	'Y'      : ACCESS.WRITE,
}

__DELETABLE_TO_ACCESS = {
	False    : ACCESS.NONE,
	True     : ACCESS.DELETE,
}

__ACCESS_TO_EDITABLE = {}
__ACCESS_TO_DELETABLE = {}

for k, v in __EDITABLE_TO_ACCESS.iteritems():
	__ACCESS_TO_EDITABLE[v] = k

for k, v in __DELETABLE_TO_ACCESS.iteritems():
	__ACCESS_TO_DELETABLE[v] = k

def editableToAccess(editable):
	if isinstance(editable, basestring):
		editable = str(editable).upper()
	else:
		editable = 'Y' if editable else 'N'
	try:
		return __EDITABLE_TO_ACCESS[editable]
	except KeyError:
		raise ValueError, "Invalid value: '%s'. 'editable' accepts case insensitive string values: 'N', 'NEW', 'UPDATE', 'Y'. Non-string values coerced to bool and then to 'N', 'Y'" % (editable,)

def deletableToAccess(deletable):
	return __DELETABLE_TO_ACCESS[deletable]

def accessToEditable(access):
	return __ACCESS_TO_EDITABLE[access & ACCESS.WRITE]

def accessToDeletable(access):
	return __ACCESS_TO_DELETABLE[access & ACCESS.DELETE]

del k
del v

if __name__ == '__main__':
	for i in xrange(8):
		e = accessToEditable(i)
		d = accessToDeletable(i)
		i2 = editableToAccess(e) | deletableToAccess(d)
		print "%s\t%s\t%s" % (i, e, d)
		assert i == i2

	print 
	print editableToAccess(u'')