import re
from gnue.common.apps.errors import UserError


class ErrorDecorators(object):


	def decorateValueRequiredError(self, error, match):
		return UserError(u_("The field '%s' is required. Please fill the field and try again") % match.groups()[0])


	def decorateForceRollbackAndRetry(self, error, match):
		print "! rollback forced via server error"
		self.rollback()
		return None # means to retry


	def decorateSyntaxError(self, error, match):
		return error

	
	def decorateInternalError(self, error, match):
		try:
			s = match.groups()[0].decode('UTF-8')
		except:
			try:
				s = match.groups()[0].decode('cp1251')
			except:
				s = repr(match.groups()[0])
		return UserError(s)

	
	def decorateUniqueConstraint(self, error, match):
		return UserError(u_("Value already exists. Duplicate key value violates unique constraint '%s'") % match.groups()[0])
	

	ERROR_DECORATORS = (
		(
			re.compile(r'IntegrityError\: null value in column \"(\w+)\" violates not\-null constraint'),
			decorateValueRequiredError
		),
		(
			re.compile(r'(?:ProgrammingError|InternalError)\: current transaction is aborted, commands ignored until end of transaction block'),
			decorateForceRollbackAndRetry
		),
		(
			re.compile(r'duplicate key value violates unique constraint "(\w+)"'),
			decorateUniqueConstraint
		),

		
		#(
		#	re.compile(r'ProgrammingError\: syntax error at or near (.*)'),
		#	decorateSyntaxError
		#),
		(
			re.compile(r'InternalError\: (.*)'),
			decorateInternalError
		),
	)


	def decorateError(self, error):
		"""
		This function used to make database related error user frielndly
		"""
		for pattern, decoratorFn in self.ERROR_DECORATORS:
			match = pattern.search('%s: %s' % (error.__class__.__name__, str(error)))
			if match:
				error = decoratorFn(self, error, match)
				break

		return error
