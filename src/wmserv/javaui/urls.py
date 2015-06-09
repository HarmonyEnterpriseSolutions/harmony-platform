try:
	from django.conf.urls import patterns, include, url
except ImportError:
	# django 1.3 support
	from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('wmserv.javaui.views',
	url(r'^$', 'applet'),
	url(r'^staticres/(.*)$', 'staticres'),
	url(r'^dynamicres/$', 'dynamicres'),
	url(r'^javaui.jnlp$', 'webstart'),
	url(r'^test_cookies/$', 'test_cookies'),
	url(r'^test_cookies_result/$', 'test_cookies_result'),
)
