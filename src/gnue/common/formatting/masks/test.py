import string
import locale

from src.gnue.common.formatting.masks.Masks import InputMask


locale.setlocale(locale.LC_ALL,'')

# =============================================================================
#
# =============================================================================
def formatOutput(output, cursor):
	"""
	Uses ansi escape sequences to highlight the cursor position (hackish)
	"""
	output += "'"
	output = output[:cursor] + chr(27) + '[7m' + \
		output[cursor:cursor+1] + chr(27) + '[0m' + output[cursor+1:]
	return "'" + output

# =============================================================================
# Test date mask
# =============================================================================
if __name__ == '__main__':
	m='"Date:" M/D/y'
	mask = InputMask(m)
	print "Mask: %s" % m
	mask.begin()
	for f in ('','1','12','123','1234','12345','9999'):
		print string.ljust("Input: '%s'" % f, 18),
		output, cursor = mask._parseInput(newtext='%s'%f)
		print "Output: " + formatOutput(output, cursor)

	# =============================================================================
	# Test numeric mask
	# =============================================================================
	m='\\$###,##0!.00'
	mask = InputMask(m)
	print "Mask: %s" % m

	for f in ('','1','12','123','1234','12345','9999'):
		mask.begin()
		print string.ljust("Input: '%s'" % f, 18),
		output, cursor = mask._parseInput(newtext='%s'%f)
		print "Output: " + formatOutput(output, cursor)


	exit
	# =============================================================================
	# Test cursor positioning
	# =============================================================================

	# Commands:
	#  < Left arrow
	#  > right arrow
	#  { delete left
	#  } delete right
	#  ^ Home
	#  v End
	#    Anything else: As is
	t = "9311<<^v"

	output, cursor = mask.begin()
	print "Init: " + formatOutput(output, cursor)

	for c in t:
		print "-----------"
		if c == "<":
			print string.ljust("Left.", 18),
			output, cursor = mask.moveLeft()
		elif c == '>':
			print string.ljust("Right.", 18),
			output, cursor = mask.moveRight()
		elif c == '^':
			print string.ljust("Home.", 18),
			output, cursor = mask.moveHome()
		elif c == 'v':
			print string.ljust("End.", 18),
			output, cursor = mask.moveEnd()
		elif c == '{':
			print string.ljust("Backspace.", 18),
			output, cursor = mask.backspace()
		elif c == '}':
			print string.ljust("Delete.", 18),
			output, cursor = mask.delete()
		else:
			print string.ljust("Type char %s" % c, 18),
			output, cursor = mask.add(c)

		print "Output: " + formatOutput(output, cursor)
