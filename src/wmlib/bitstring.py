
def getBit(s, n):
	if s is not None:
		assert isinstance(s, basestring)
		i = len(s) - n - 1
		if i < 0:
			return False
		try:
			return s[len(s) - n - 1] != '0'
		except IndexError:
			return False


def setBit(s, n, value):

	l = list(s or '')
	l.reverse()

	while len(l) < n+1:
		l.append('0')

	l[n] = '1' if value else '0'

	l.reverse()

	return ''.join(l)

if __name__ == '__main__':
	s = None
	s = setBit(s, 1, True)
	print s
	s = setBit(s, 5, True)
	print s
	s = setBit(s, 2, True)
	print s
	s = setBit(s, 5, False)

	print s

	print getBit(s, 0)
	print getBit(s, 1)
	print getBit(s, 2)
	print getBit(s, 3)
	print getBit(s, 4)
	print getBit(s, 5)
	print getBit(s, 6)
