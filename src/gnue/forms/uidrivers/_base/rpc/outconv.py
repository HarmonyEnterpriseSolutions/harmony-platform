# -*- coding: Cp1251 -*-
"""
outconv(object) returns save json structure as o
but replaces ServerObject instances with { '__roid__' : ROID }
from decimal import Decimal

"""
from decimal import Decimal

__all__ = ['outconv']

ALLOWED = set((str, unicode, int, long, float, None.__class__, bool))


def outconv(o):
	if hasattr(o, '__roid__'):
		return { '__roid__' : o.__roid__() }
	else:
		return OUTCONV.get(o.__class__, outconv_none)(o)

def outconv_none(o):
	assert o.__class__ in ALLOWED, 'Invalid json value: %s' % repr(o)
	return o

def outconv_list(o):
	return map(outconv, o)

def outconv_dict(o):
	return dict((map(outconv, i) for i in o.iteritems()))

def outconv_decimal(o):
	return float(o)

OUTCONV = {
	dict    : outconv_dict,

	list    : outconv_list,
	tuple   : outconv_list,

	Decimal : outconv_decimal,	# convert to float
}


if __name__ == '__main__':
	class O(object):
		def __init__(self, id):
			self.id = id

		def __roid__(self):
			return self.id
	
	from toolib import startup
	startup.startup()

	print outconv({ u"Привет" : [O(1), O(2)]})
	print repr(outconv("Привет"))
	print repr("Привет".encode("UTF-8"))
