import os
import sys

from scripts.gettext_config import *


def usage():
	print "Use language notation (ru, ua...) as first parameter"

def main(locale):
	
	locale = LOCALE_ALIASES.get(locale, locale)
	localeDir = os.path.join(LOCALE_PATH, locale)

	if os.path.exists(localeDir):

		for domain, paths in DOMAINS.iteritems():

			paths = [os.path.join(i, '*.py') for i in paths]
	
			command = "%(pythonBinDir)s\\python ..\\src\\toolib\\scripts\\pygettext.py -r -j -p %(localeDir)s\\LC_MESSAGES -d %(domain)s %(paths)s" % {
				'pythonBinDir' : sys.prefix,
				'localeDir' : localeDir,
				'domain' : domain,
				'paths' : ' '.join(paths),
			}

			os.system(command)
	
	else:
		print "locale dir does not exists", localeDir


if __name__ == '__main__':
	try:
		main(*sys.argv[1:])
	except TypeError:
		usage()
