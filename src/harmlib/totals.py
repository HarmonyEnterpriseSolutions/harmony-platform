from decimal import Decimal
import locale
zero = Decimal(0)

def calc_total_by_unit(block, total_field, unit_field, zero=zero):
	sums = {}
	for row in block.get_user_data((total_field, unit_field)):
		key = row[unit_field]
		sum  = row[total_field]
		if sum is not None:
			sums[key] = sums.get(key, zero) + sum

	return sums

def format_total_by_unit(block, total_field, unit_field, zero=zero, pattern="%(total)s (%(unit)s)", join='; '):
	sums = 	calc_total_by_unit(block, total_field, unit_field, zero)
	currenncies = sums.keys()
	currenncies.sort()

	decimal_pattern='%%.%sf' % getattr(block.getField(total_field)._object, 'scale', 0)
	res = [pattern % {'total' : locale.format(decimal_pattern, sums[i], True), 'unit':i or ''} for i in currenncies]
	return join.join(res)
