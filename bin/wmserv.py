#!/usr/bin/env python
import os
import sys

HOST = None
PORT = 8000

def main(host=None, port=None):
	if port is None:
		try:
			port = int(host)
			host = None
		except:
			pass

	if host is None:
		host = HOST

	if host is None:
		import socket
		host = socket.gethostbyname(socket.gethostname())

	os.chdir(os.path.abspath('./../src/harmonyserv'))

	if os.name == 'posix':
		python_bin = os.path.join(sys.prefix, 'bin')
	else:
		python_bin = sys.prefix

	os.system('%s/python manage.py runserver %s:%s' % (python_bin, host, port or PORT))	

if __name__ == '__main__':
	print "Usage: %s [<host>] [<port>]" % sys.argv[0]
	main(*sys.argv[1:])
