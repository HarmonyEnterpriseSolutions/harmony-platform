#-*- coding: Cp1251 -*-

import re
from gnue.common.apps.errors import UserError


class ErrorDecorators(object):


	def decorateInternalError(self, error, match):
		return UserError(eval('"%s"' % match.groups()[0], {}, {}).decode('Cp1251'))

	
	def decorateValueRequiredError(self, error, match):
		return UserError(u_("The field '%s' is required. Please fill the field and try again") % eval(match.groups()[0]))


	def decorateUniqueKeyError(self, error, match):
		return UserError(u_("Violation of UNIQUE KEY constraint '%s'. Cannot insert duplicate key in object '%s'.") % tuple(map(eval, match.groups())))


	ERROR_DECORATORS = (
		(
			re.compile('''\[42000\]\ \[[\w\s]+\](?:\[[\w\s]+\])?\[[\w\s]+\](.*)\ \(50000\)\ \(SQLExecDirectW\)'''),
			decorateInternalError
		),
		(
			re.compile('''Cannot insert the value NULL into column ('[^']+'), table'''),
			decorateValueRequiredError
		),
		(
			re.compile('''Violation of UNIQUE KEY constraint ('[^']+')\. Cannot insert duplicate key in object ('[^']+')\.'''),
			decorateUniqueKeyError
		),
	)


	def decorateError(self, error):
		"""
		This function used to make database related error user frielndly
		"""
		#rint "DECORATE ERROR", error
		for pattern, decoratorFn in self.ERROR_DECORATORS:
			match = pattern.search(str(error))
			if match:
				error = decoratorFn(self, error, match)
				break
		return error



if __name__ == '__main__':
	print ErrorDecorators.ERROR_DECORATORS[0][0].search("""Violation of UNIQUE KEY constraint 'IX_\xd1\xf7\xe5\xf2\xe0\xcf\xee\xe7_\xd1\xf7\xe5\xf2\xcf\xf0\xee\xe4\xc8\xc4'. Cannot insert duplicate key in object '\xd1\xf7\xe5\xf2\xe0\xcf\xee\xe7'.""")
