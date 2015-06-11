import os

LOCALE_PATH='..\\share\\locale'

DOMAINS = {
	'gnue-common' : ['..\\src\\gnue\\common'],
	'gnue-forms'  : ['..\\src\\gnue\\forms'],
	'toolib'      : ['..\\src\\toolib'],
	'harmonylib'       : ['..\\src\\harmonylib'],
	'harmony'          : ['..\\wkroot'],
	'forms'       : ['..\\forms'],
}

GETTEXT_HOME=os.path.sep.join((os.environ['SystemDrive'], 'pro', 'gettext'))

LOCALES = ['ru_RU', 'en_EN']

LOCALE_ALIASES = {
	'ru' : 'ru_RU',
	'en' : 'en_EN',
	'ua' : 'uk_UA',
}

FORMS = [
	"..\\share\\gnue\\forms\\defaults\\default.gfd",
	"..\\forms\\*.gfd",
	"..\\forms\\common\\**\\*.gfd",
	"..\\forms\\harmony\\**\\*.gfd",
	"..\\forms\\ksbilling\\**\\*.gfd",
]

FORMS_OUTPUT = "..\\forms\\.text.py" 

from gnue.forms.GFObjects.GFObj import LOCALIZEABLE_ATTRIBUTES as FORMS_ATTRS
