import os
import sys
import re

REC_CREATE = re.compile('(?i)CREATE\s+OR\s+REPLACE\s+FUNCTION\s+[_A-Z]+\s*\(([^\)]*)\)')
REC_UNNAMED_VAR = re.compile('(\$[\d]+)')

def main(f='1.sql'):
	
	text = open(f, 'rt').read()

	m = REC_CREATE.search(text)

	if not m:
		raise "Can't find signaure: CREATE OR REPLACE FUNCTION"

	names = [i.strip().split(' ')[0] for i in m.groups()[0].split(',')]

	for i, name in enumerate(names):
		print i+1, name

	def f_sub(m):
		return names[int(m.groups()[0][1:])-1]

	text = REC_UNNAMED_VAR.sub(f_sub, text)

	open(f+'+', 'wt').write(text)
	
	print 'saved:', f
		
if __name__ == '__main__':
	main(*sys.argv[1:])
