try:
	from django.conf.urls import patterns, include, url
except ImportError:
	# django 1.3 support
	from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

	url(r'^$', 'harmonyserv.javaui.views.index'),
	url(r'^javaui/', include('harmonyserv.javaui.urls')),
	url(r'^dbi/', include('harmonyserv.dbi.urls')),

	# Uncomment the admin/doc line below to enable admin documentation:
	# url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

	# Uncomment the next line to enable the admin:
	#url(r'^admin/', include(admin.site.urls)),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
