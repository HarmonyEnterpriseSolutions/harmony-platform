import urllib
import urllib2


def get_execute_url(form):
	return '%s/execute?%s' % (form.get_global('server_url'), form.get_global('__form_server_query_string__'))

def execute(form, command, email=None):
	response = urllib2.urlopen(get_execute_url(form), urllib.urlencode({'command' : command, 'email' : email or ''}))
	return response.read()
	