from src.gnue.forms.uidrivers._base.rpc import RemoteHive


class RemoteObject(object):

	__callbacks__ = None
	__methods__ = None

	def __init__(self, hive, type, *args, **kwargs):

		assert isinstance(hive, RemoteHive), hive
		assert type is None or (isinstance(type, basestring) and type), type
		assert isinstance(args, tuple), args
		assert isinstance(kwargs, dict), kwargs

		self.__type = type or self.__class__.__name__
		self.__id = hive.newId()
		self.__hive = hive

		self.__hive.appendCallback(self, "new " + self.__type, args, kwargs)
	
	def __getattr__(self, name):
		if self.__callbacks__ is None or name in self.__callbacks__:
			def clientMethod(*args, **kwargs):
				self.__hive.appendCallback(self, name, args, kwargs)
			return clientMethod
		else:
			raise AttributeError, name

	def __roid__(self):
		"""
		remote object id
		"""
		return self.__id
