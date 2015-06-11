from toolib.util				import lang

def getDevClass(klass, name):
	moduleName = "%s_%s" % (klass, name.replace('-', '_'))
	module = lang.import_module_relative(moduleName, __name__)
	return getattr(module, klass)
