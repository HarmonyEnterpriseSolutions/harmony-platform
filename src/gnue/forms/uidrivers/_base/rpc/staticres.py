import os

# maps web path to file path for given resource
__staticResources = {}
__staticPathes = {}

# ---------------------------------------------------------------------------
# Static resources
# ---------------------------------------------------------------------------

def getStaticResourceWebPath(path):
	"""
	maps any static resource that client gets from filesystem
	so applet can access it thrue staticres servlet
	returns some web path for this resource
	"""
	if path:
		res = __staticPathes.get(path)
		if not res:
			res = os.path.split(path)[1]
			if res in __staticResources:
				fname, ext = os.path.splitext(res)
				i = 0
				while True:
					i += 1
					res = ''.join((fname, str(i), ext))
					if res not in __staticResources:
						break
			__staticResources[res] = path
			__staticPathes[path]   = res
		return res

def getStaticResourceFilePath(res):
	"""
	used by staticres servlet to populate the static resource
	"""
	return __staticResources[res]
