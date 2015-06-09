import SilverCity
from SilverCity import ScintillaConstants as SC

INDENT = ' ' * 4
START_INDENT = 1

SC_NAME = {}
for i in dir(SC):
	if i.startswith('SCE_P_'):
		#print i,  '=', getattr(SC, i)
		SC_NAME[getattr(SC, i)] = i

class Formatter(object):

	def __init__(self):

		self.o = file('output.py', 'wt')

		print >> self.o, """\
from gnue.common.formatting import GTypecast
from gnue.forms import GFObjects, GFLibrary, GFForm
from gnue.forms.GFObjects import commanders

		"""

		self.indent = START_INDENT
		self.newline = True
		self.inlist = False
		self.lastline = ''
		self.prevtext = None
		self.prevstyle = None

		self.lexer = SilverCity.find_lexer_module_by_id(SC.SCLEX_PYTHON)

	def process(self):
		keywords = SilverCity.WordList(SilverCity.Keywords.python_keywords)
		properties = SilverCity.PropertySet()
		self.lexer.tokenize_by_style(file('sample.py').read(), [keywords, SilverCity.WordList()], properties, self.funcw)

	def n(self):
		self.o.write('\n')
		self.newline = True

	def w(self, s):
		if self.newline:
			#o.write(str(self.indent))
			self.o.write(INDENT * self.indent)
			self.newline = False
			self.lastline = ""
		self.o.write(s)
		self.lastline += s

	def funcw(self, style, text, start_column, start_line, **other_args): 
		if style != SC.SCE_P_DEFAULT:
			if style == SC.SCE_P_OPERATOR and not text.isalpha():
				for i in text:
					self.func(style, i, start_column, start_line, **other_args)
			else:
				self.func(style, text, start_column, start_line, **other_args)
			self.prevstyle = style
			self.prevtext = text

	def func(self, style, text, start_column, start_line, **other_args): 

		if style == SC.SCE_P_IDENTIFIER:
			self.w(text)

		elif style == SC.SCE_P_OPERATOR:
			
			if   text in '([':	self.inlist = True
			elif text in '])':	self.inlist = False
			elif text == '{':	self.indent += 1
			elif text == '}':	self.indent -= 1

			if text in ':=': self.w(" ")
			self.w(text)
			if text in ':=': self.w(" ")
			
			if text not in ':=.}()[]':
				if text == ',' and self.inlist:
					self.w(' ')
				else:
					self.n()

			if text == ',' and self.prevtext=='}':	self.n()

		elif style == SC.SCE_P_COMMENTLINE:
			self.w(text)
			self.n()

		elif style == SC.SCE_P_NUMBER:
			self.w(text)
			self.n()
		
		elif style in (SC.SCE_P_STRING, SC.SCE_P_CHARACTER):
			if self.prevstyle in (SC.SCE_P_STRING, SC.SCE_P_CHARACTER):
				self.n()
				self.w(' ' * self.lastline.find(self.prevtext))
			self.w(text)

		elif style == SC.SCE_P_WORD:
			self.w(text)
		
		elif style == SC.SCE_P_COMMENTBLOCK:
			self.w(text)
			self.n()
		
Formatter().process()
