"""
Generates colors.gfd
"""

from gnue.common.datatypes.Color import colorNames

CODE = """\
<?xml version="1.0" encoding="windows-1251"?>
<form title="GNUe colors">

	<datasource name="ds_tree" type="static">
		<staticset fields='name,style'>
%s
		</staticset>
	</datasource>

<logic>
	<block name="b_tree" datasource="ds_tree" startup='full' editable='N' deletable='N'>
		<field name="name"      field="name"      />
		<field name="code"      field="code"      />
		<field name="style"     field="style"     />
	 </block>
	</logic>
	
<layout>
	<table block = 'b_tree' fld_style='style' >
		<entry field="name"     label="Name"       />
		<entry field="code"     label="Code"       />

		<table-row-styles>
%s
		</table-row-styles>
	
	</table>
</layout>
</form>
"""

STATICSETROW = """\
			<staticsetrow><staticsetfield name="name" value="'%(color)s'"/><staticsetfield name="code" value="'%(code)s'"/><staticsetfield name="style" value="'%(color)s'"/></staticsetrow>
"""

TABLEROWSTYLE = """\
			<table-row-style name='%(color)s' bgcolor='%(color)s' textcolor='%(textcolor)s'/>"
"""

import sys

import re

REC_COLORNAME = re.compile("(?i)([A-Z]+)(\d+)")

def cmpColorNames(cn1, cn2):
	m1 = REC_COLORNAME.match(cn1)
	if m1:
		m2 = REC_COLORNAME.match(cn2)
		if m2:
			a1, n1 = m1.groups()
			
			a2, n2 = m2.groups()

			if a1 == a2:
				return cmp(int(n1), int(n2))

	return cmp(cn1, cn2)

def textColor(color):
	r, g, b  = colorNames[color]
	return 'white' if (r+g+b)/3 < 128 else 'black'


if __name__ == '__main__':

	f = open('colors.gfd', 'wt')

	colors = colorNames.keys()
	colors.sort(cmpColorNames)

	print >>f, CODE % (
		''.join([STATICSETROW  % {'color' : i, 'code' : repr(colorNames[i])} for i in colors]),
		''.join([TABLEROWSTYLE % {'color' : i, 'textcolor' : textColor(i) } for i in colors]),
	)

	f.close()
	