update = """
	UPDATE spr_prod_price SET 
		prod_id  = $2, 
		price_id = $3, 
		price    = $4 
	WHERE prod_price_id = $1;
	"""

import re

REC_FIELD = re.compile("(?i)([_A-Z0-9]+)\s*\=\s*\$([0-9]+)")

fields = {}

def matched(m):
	name, pos = m.groups()
	pos = int(pos)
	fields[pos] = name

REC_FIELD.sub(matched, update, )

keys = fields.keys()
keys.sort()

assert keys == range(1, len(keys) + 1), 'Some parameter not used in update: %s' % keys

print """\
	'' : {
		'default' : '%s',
	},
""" % ', '.join([fields[k] for k in keys])
	