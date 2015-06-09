import re

REC_VARIABLE = re.compile(r"(?i)\$\{([_A-Z][_A-Z0-9]*)\}")

def subst(text, f):
	return REC_VARIABLE.sub(f, text)

def blockAsSource(b):
	def f(match):
		# TODO: GFField must know how to format value
		return unicode(b.getField(match.groups()[0]).get() or u'')
	return f
	
def substFromBlock(text, block):
	return subst(text, blockAsSource(block))

