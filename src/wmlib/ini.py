from ConfigParser import ConfigParser, Error
from StringIO import StringIO	# cStringIO can't work with unicode in python <= 2.6, #1205

CACHE = {
}

def getConfig(text):
	c = CACHE.get(text)
	if c is None:
		CACHE[text] = c = ConfigParser()
		c.readfp(StringIO(text))
	return c

def getValue(text, section, option, default=NotImplemented):
	c = getConfig(text or '')
	try:
		return c.get(section, option, raw=True).replace('\\n', '\n')
	except Error:
		if default is NotImplemented:
			raise
		else:
			return default


if __name__ == '__main__':
	print getValue(open('z:\\projects\\wm\\etc\\harm\\servers.conf', 'rt').read(), 'reports', 'report_server', 'xxxxxxxxx')