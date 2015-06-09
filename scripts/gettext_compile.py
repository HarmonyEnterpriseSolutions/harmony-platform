import os
import sys

from scripts.gettext_config import *


def usage():
	print "Use language notation (ru, ua...) as first parameter"

def main(locale = None):
	if locale is not None:
		locale = LOCALE_ALIASES.get(locale, locale)
		for domain in DOMAINS:
			command = '%(gettext_home)s\\bin\\msgfmt ..\\share\\locale\\%(locale)s\\LC_MESSAGES\\%(domain)s.po -o ..\\share\\locale\\%(locale)s\\LC_MESSAGES\\%(domain)s.mo' % {
				'gettext_home' : GETTEXT_HOME,
				'locale' : locale,
				'domain' : domain,
			}
			print "Compilling", locale, domain
			os.system(command) 
	else:
		for locale in LOCALES:
			main(locale)



if __name__ == '__main__':
	try:
		main(*sys.argv[1:])
	except TypeError:
		usage()
