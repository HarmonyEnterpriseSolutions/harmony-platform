try:
	from django.conf.urls import patterns, include, url
except ImportError:
	# django 1.3 support
	from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('harmonyserv.dbi.views',
	url(r'^$', 'service', name='service'),
	url(r'^(?P<method>\w+)/(?P<application>\w+)/(?P<connection>\w+)/(?P<function>\w+)/$', 'raw_service'),
	url(r'^report/$', 'report', name='report'),
	url(r'^execute/$', 'execute', name='execute'),
	url(r'^test_streamed_response/$', 'test_streamed_response', name='test_streamed_response'),
)
