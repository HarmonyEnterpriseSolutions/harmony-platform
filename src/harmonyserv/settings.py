import os

# make src/ content importable
import sys
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC_DIR)

# set default encoding to UTF8
# this is for sending python exceptions via json-rpc, which expecting UTF8
reload(sys)
sys.setdefaultencoding('UTF8')


# Django settings for harmonyserv project.
GNUE_SERVER_URL = "http://localhost:82/harmony/wk.cgi/harmony"

# manually handled in javaui.views.process
SESSION_EXPIRY = 30 * 60 	# 30 minutes

# allways true for javaui
# this will not work since session.set_expiry manually
#SESSION_EXPIRE_AT_BROWSER_CLOSE = True

DEBUG = True

# Set to suppres normal http error, dump to console
DEBUG_PROPAGATE_EXCEPTIONS = True

TEMPLATE_DEBUG = DEBUG

ADMINS = (
	# ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
		'NAME': 'javaui',						# Or path to database file if using sqlite3.
		'USER': 'postgres',						 # Not used with sqlite3.
		'PASSWORD': 'postgres',					 # Not used with sqlite3.
		'HOST': '192.168.2.21',                  # Set to empty string for localhost. Not used with sqlite3. 
		'PORT': '5432',						 # Set to empty string for default. Not used with sqlite3.
	}
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Kiev'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'RU'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(os.path.dirname(SRC_DIR), 'www')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
#STATICFILES_DIRS = (
	# Put strings here, like "/home/html/static" or "C:/www/django/static".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
#)

# List of finder classes that know how to find static files in
# various locations.
#STATICFILES_FINDERS = (
	#'django.contrib.staticfiles.finders.FileSystemFinder',
	#'django.contrib.staticfiles.finders.AppDirectoriesFinder',
	#'django.contrib.staticfiles.finders.DefaultStorageFinder',
#)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '4rm0pjiau7w2i5yv@dh4d@w#vm8p3k)%a(&bz-ensd78p5lj8e'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	#'django.template.loaders.filesystem.Loader',
	'django.template.loaders.app_directories.Loader',
	#'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	# TODO: why error 403
	#'django.middleware.csrf.CsrfViewMiddleware',
	#'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'harmonyserv.urls'

TEMPLATE_DIRS = (
	# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
	#'django.contrib.auth',
	#'django.contrib.contenttypes',
	'django.contrib.sessions',
	#'django.contrib.sites',
	'django.contrib.messages',
	#'django.contrib.staticfiles',	# this interferes to serve static in debug
	# Uncomment the next line to enable the admin:
	# 'django.contrib.admin',
	# Uncomment the next line to enable admin documentation:
	# 'django.contrib.admindocs',
	'harmonyserv',
	'harmonyserv.javaui',
	'harmonyserv.clientproperty',
	'harmonyserv.dbi',
)

# in django >= 1.6 json serializer used by default, this not works with UserSession
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		#'verbose': {
		#	'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
		#},
		'simple': {
			'format': '%(levelname)s %(message)s'
		},
	},
	'handlers': {
		#'mail_admins': {
		#	'level': 'ERROR',
		#	'class': 'django.utils.log.AdminEmailHandler'
		#}
		'console':{
			'level':'DEBUG',
			'class':'logging.StreamHandler',
			'formatter': 'simple'
		},	
	},
	'loggers': {
		'django.request': {
			'handlers': ['console'],
			'level': 'WARNING',
			'propagate': False,
		},
	}
}
