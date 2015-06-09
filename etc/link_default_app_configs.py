"""
makes links of application configs in etc directory
to allow directly rin forms of this app
"""

import os
import sys

FILES = ('connections.conf', 'fn_signatures.conf.py')

def linkFile(link, file=None):
	if os.path.exists(link):
		os.remove(link)
	if file:
		os.system("xln %s %s" % (file, link))


def main(app=None):
	if not app:
		for file in FILES:
			linkFile(file)
	elif os.path.isdir(app):
		for file in FILES:
			linkFile(file, os.path.join(app, file))
	else:
		print "app not found:", app

if __name__ == '__main__':
	main(*sys.argv[1:])
