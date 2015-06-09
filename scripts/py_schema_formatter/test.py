
import SilverCity
from SilverCity import ScintillaConstants

o = file('output.py', 'wt')

print >> o, """\
from gnue.common.formatting import GTypecast
from gnue.forms import GFObjects, GFLibrary, GFForm
from gnue.forms.GFObjects import commanders

"""

SC_NAME = {}
for i in dir(ScintillaConstants):
	if i.startswith('SCE_P_'):
		#print i,  '=', getattr(ScintillaConstants, i)
		SC_NAME[getattr(ScintillaConstants, i)] = i

styles = set()

indent = 0
newline = True
            
def n():
	o.write('\n')
	newline = True

def w(s):
	o.write(s)

def func(style, text, start_column, start_line, **other_args): 
	print >> o, '%s: "%s"' % (SC_NAME[style], text)
		


keywords = SilverCity.WordList(SilverCity.Keywords.python_keywords)
properties = SilverCity.PropertySet()
lexer = SilverCity.find_lexer_module_by_id(ScintillaConstants.SCLEX_PYTHON)
            
lexer.tokenize_by_style(file('sample.py').read(), [keywords, SilverCity.WordList()], properties, func)
