import os, sys
import django.core.handlers.wsgi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = sys.stderr

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# default locale is 'C' in wsgi so set explicitly
# does not work under windows
#import locale
#locale.setlocale(locale.LC_ALL, 'rus_ukr')

#reload(sys)
#sys.setdefaultencoding('Cp1251')

application = django.core.handlers.wsgi.WSGIHandler()