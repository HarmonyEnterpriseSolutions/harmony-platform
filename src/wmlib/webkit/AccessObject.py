import operator


class AccessObject(object):

	# access is PRUID
	ACCESS_PRINT  = 16
	ACCESS_READ   = 8
	ACCESS_UPDATE = 4
	ACCESS_INSERT = 2
	ACCESS_DELETE = 1
	ACCESS_ALL = ACCESS_READ | ACCESS_UPDATE | ACCESS_INSERT | ACCESS_DELETE | ACCESS_PRINT

	def __init__(self, objectResult, accessResult):
		
		for k, v in objectResult.iteritems():
			if k.startswith('object_'):
				setattr(self, k[len('object_'):], v)
			else:
				setattr(self, k, v)

		accesses = [
			(
				  int(i['objectaccess_is_print']) << 4
				| int(i['objectaccess_is_view' ]) << 3
				| int(i['objectaccess_is_edit' ]) << 2
				| int(i['objectaccess_is_ins'  ]) << 1
				| int(i['objectaccess_is_del'  ])
			)
			for i in accessResult
		]

		self.access = reduce(operator.or_, accesses, 0)
