from __future__ import with_statement
#import weakref
import sys
import thread
from collections import deque
from src.gnue.forms.uidrivers._base.rpc import outconv


class RemoteHive(object):

	_debug = False
	
	def __init__(self, id):
		self.__id = id
		self.__objects = {} #weakref.WeakValueDictionary()
		self.__calls = deque()
		self.__callsLock = thread.allocate_lock()
		self.__callbacks = []
		self.__flush = False
		self.__idCounter = 0

		self.__inconv = {
			dict  : self.inconv_dict,
			list  : self.inconv_list,
			tuple : self.inconv_list,
		}


	def newId(self):
		self.__idCounter += 1
		return self.__idCounter

	def processCalls(self, calls):
		"""
		calls is
		[
			[id1, methodName1, args1, kwargs1],
			...
			[idN, methodNameN, argsN, kwargsN],
		]

		start calls processing

		"""
		with self.__callsLock:
			returnValue = None
			
			for id, method, args, kwargs in calls:
				if self._debug: print "APPEND CALL: <%s>.%s(*%s, **%s)" % (id, method, args, kwargs)

			self.__calls.extend(calls)

			while self.__calls and not self.__flush:
				id, method, args, kwargs = self.__calls.popleft()
				
				o = self.__objects[id]

				if o.__methods__ is None or method in o.__methods__:
					if self._debug: print "CALL: <%s id=%s>.%s(*%s, **%s)" % (o.__class__.__name__, id, method, args, kwargs)
					try:
						returnValue = getattr(o, method)(*self.inconv_list(args), **self.inconv_dict(kwargs))
					except:
						self.handleError(*sys.exc_info())
						returnValue = None

					if self._debug: print "RET: ", returnValue
					# TODO: exception to client
				else:
					raise AttributeError, method

			resp = tuple(self.__callbacks)
			del self.__callbacks[:]
			self.__flush = False
			#for id, method, args in resp:
			#	if self._debug: print "CALLBACK: <%s>.%s(%s)" % (id, method, args)
			if self._debug: print "CALLS LEFT:"	, len(self.__calls)
			return (resp, len(self.__calls), None if self.__calls else outconv(returnValue))

				
	def appendCallback(self, object, method, args, kwargs):
		"""
		may be called inside processCalls
		"""
		assert hasattr(object, '__roid__'), object
		assert isinstance(method, basestring), method
		assert isinstance(args,   tuple), args
		assert isinstance(kwargs, dict), kwargs

		self.__flush = self.__flush or kwargs.pop('flush', False)
		assert not kwargs
		if method.startswith('new '):
			# constructor call
			self.__objects[object.__roid__()] = object

		if self._debug: print "APPEND CALLBACK: <%s>.%s(%s), flush=%s" % (object.__roid__(), method, args, self.__flush)
		self.__callbacks.append((object.__roid__(), method, args))

	def inconv(self, o):
		if isinstance(o, dict) and '__roid__' in o:
			return self.__objects[o['__roid__']]
		else:
			return self.__inconv.get(o.__class__, self.inconv_none)(o)

	def inconv_none(self, o):
		return o

	def inconv_list(self, o):
		return map(self.inconv, o)

	def inconv_dict(self, o):
		return dict((map(self.inconv, i) for i in o.iteritems()))

	def handleError(self, e, ec, tb):
		raise e, ec, tb
