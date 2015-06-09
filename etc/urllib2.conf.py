"""
Default urllib2 initialization

must ne executed before any
	urllib2.urlopen

"""

PROXY_CONF = {
	#"http" : "http://user:password@proxy:8080",
}

__all__ = ['PROXY_HANDLER']

import urllib2
PROXY_HANDLER = urllib2.ProxyHandler(PROXY_CONF)
urllib2.install_opener(urllib2.build_opener(PROXY_HANDLER))
