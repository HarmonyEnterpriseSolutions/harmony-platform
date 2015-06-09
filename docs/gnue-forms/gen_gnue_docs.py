import os
import sys
from toolib import debug
from gnue.forms import GFParser
from toolib.util.Cache import cached_method_nogc as cached_method
from toolib.util import strings
from toolib.util import introspection
from toolib.text import html
from toolib.util import lang

class nbsp:
	def __repr__(self): return '&nbsp;'
	__str__ = __repr__
nbsp = nbsp()

class Tags(dict):

	def __init__(self, conf):
		for name, tagConf in conf.iteritems():
			self[name] = Tag(self, name, tagConf)
			
	def sorted(self):
		values = dict.values(self)
		values.sort()
		return values


# add config stub to create more GFObjects
import __builtin__
__builtin__.__dict__['gConfig'] = lambda x: None

class Tag(object):

	def __init__(self, tags, name, conf):
	 	self.tags = tags

		self.name = name

		self.Attributes = {}
		self.Deprecated = False
		self.Label = ''
		self.Description = ''

		self.__dict__.update(conf)
		self.ParentTags = tuple(conf.get('ParentTags') or ())

	@cached_method
	def _getParentSet(self):
		#print "IN", self, id(self)

		parentSet = set(self.ParentTags)
		oldLen = 0

		while len(parentSet) != oldLen:
			oldLen = len(parentSet)
			for i in tuple(parentSet):
				try:
					parentSet.update(self.tags[i].ParentTags)
				except KeyError:
					print "Suspecting that %s has bad ParentTags: %s" % (self.name, self.ParentTags,)
					raise
		try:
			parentSet.remove(self.name)
		except:
			pass
			
		#l = list(parentSet)
		#l.sort()
		#print '! %-20s %s' % (self.name, ','.join(l))

		#print "OUT", self
		return parentSet

	def isDescendant(self, parentTag):
		return parentTag.name in self._getParentSet()

	@cached_method
	def getParentTags(self):
		tags = map(self.tags.__getitem__, self.ParentTags)
		tags.sort()
		return tuple(tags)

	@cached_method
	def getChildTags(self):
		tags = []
		for tag in self.tags.itervalues():
			if self.name in tag.ParentTags:
				tags.append(tag)
		tags.sort()
		return tuple(tags)

	def __cmp__(t1, t2):
		if t1.isDescendant(t2) and not t2.isDescendant(t1):
			return  1
		elif t2.isDescendant(t1) and not t1.isDescendant(t2):
			return -1
		else:
			return cmp(t1.name, t2.name)

	def __str__(self):
		return self.name

def itemsSorted(d, cmp = lambda item1, item2: cmp(item1[0], item2[0])):
	items = d.items()
	items.sort(cmp)
	return items

def sorted(l,  cmp=cmp):
	l = list(l)
	l.sort(cmp)
	return l

def not_import_tag(tag):
	return not tag.startswith('import-')

def dumpDocs(xmlElements):

	o = file('xml-schema.htm', 'wt')

	print >> o, """\
<HTML>
<LINK href="../css/Report.css" type=text/css rel=stylesheet>
<TITLE>GFD XML schema</TITLE>
<BODY>
<H1>GFD XML schema</H1>
"""

	tags = Tags(xmlElements)

	triggerTags = []

	for tag in tags.sorted():

		if not not_import_tag(tag.name): continue
		if tag.Deprecated: continue

		print >>o, """\
<H2>Tag: %s</H2><br>
BaseClass: <b>%s</b><br>
""" % (
			tag.name, 
			tag.BaseClass.__name__, 
		)

		if getattr(tag, 'Importable', False):
			print >>o, "Importable: <b>%s</b><br>" % getattr(tag, 'Importable', False)

		if tag.getParentTags():
			print >>o, "Parent tags: <b>%s</b><br>" % ', '.join(filter(not_import_tag, map(str, tag.getParentTags())))
	
		if tag.getChildTags():
			print >>o, "Child tags: <b>%s</b><br>" % ', '.join(filter(not_import_tag, map(str, tag.getChildTags())))
		
		if tag.Description:	print >>o, "Description: %s" % html.escape(tag.Description)

		if tag.name == 'dialog':
			print >> o, "<br><b>Note: Attributes are similar to form tag attributes</b>"
			continue

		if tag.Attributes:
			assert isinstance(tag.Attributes, dict), repr(tag.Attributes)

			html.table((
					html.bold("Attribute name"),
					html.bold("Type"),
					html.bold("Default"),
					html.bold("Values"),
					html.bold("Description"),
				),
				(
					(
						attrName,
						attr['Typecast'].__name__,
						lang.iif(attr.has_key('Default'), repr(attr.get('Default')), None),
						html.inline(formatValueSet(attr)),
						attr.get('Description'),
					)
					for (attrName, attr) in itemsSorted(tag.Attributes)
					if not attr.get('Deprecated')

				)
			).__write_html__(o)


		try:
			gfObject = tag.BaseClass(None)
		except Exception, e:
			print '* Trigger namespace api wil not be shown for "%s"' % tag.name,
			print "via %s: %s" % (e.__class__.__name__, e)
			gfObject = None
		else:
			from gnue.common.logic.GTriggerCore import GTriggerCore
			if isinstance(gfObject, GTriggerCore):

				if gfObject._triggerGlobal or gfObject._triggerGet or gfObject._triggerSet or gfObject._triggerFunctions or gfObject._triggerProperties:
					triggerTags.append((tag, gfObject))

	print >>o, """\
</BODY>
</HTML>
"""
	o.close()

	#############################################################################################

	o = file('trigger-namespace.htm', 'wt')

	print >> o, """\
<HTML>
<LINK href="../css/Report.css" type=text/css rel=stylesheet>
<TITLE>Trigger namespace API</TITLE>
<BODY>
<H1>Trigger namespace API</H1>
"""
		
	for tag, gfObject in triggerTags:
		print >> o, """\
<H2>Tag: %s</H3>
""" % tag.name

		if gfObject._triggerGlobal:
			print >>o, "Trigger global: <b>True</b><br>"

		if tag.name == 'dialog':
			print >> o, "Similar to form tag"
			continue

		if gfObject._triggerFunctions:
			print >> o, """\
<H3>Tag %s trigger functions</H3>
""" % tag.name

			tf = gfObject._triggerFunctions.copy()

			if gfObject._triggerGet:
				tf['* str(object)'] = { 'function' : gfObject._triggerGet }

			if gfObject._triggerSet:
				tf['** parent.object assignment'] = { 'function' : gfObject._triggerSet }

			html.table((
					html.bold("Function name"),
					html.bold("Parameters"),
					html.bold("Description"),
				),
				(
					(
						html.inline(tfi.getName()),
						tfi.getSignature(),
						html.pre(tfi.getDescription()),
					)
					for tfi in
					(
						TriggerFunctionInfo(name, conf) 
						for (name, conf) in itemsSorted(tf)
					)
				),
			).__write_html__(o)
			

		if gfObject._triggerProperties:

			print >> o, "<H3>Tag %s trigger properties</H3>" % tag.name

			html.table((
					html.bold("Property name"),
					html.bold("Get description"),
					html.bold("Set description"),
				),
				(
					(
						html.inline(tpi.getName()),
						html.pre(tpi.getDescription('get')),
						html.pre(tpi.getDescription('set')),
					)
					for tpi in (
						TriggerPropertyInfo(name, conf)
						for (name, conf) in itemsSorted(gfObject._triggerProperties)
					)
				),
			).__write_html__(o)

	print >>o, """\
</BODY>
</HTML>
"""
	o.close()

class TriggerFunctionInfo(object):

	def __init__(self, name, conf):
		self.name = name
		self.is_global = bool(conf.get('global'))
		self.function = conf['function']

	def getName(self):
		res = "<b>%s</b>" % self.name

		if self.function.__name__ != self.name:
			res += "<br>(%s)" % self.function.__name__
	
		if self.is_global:
			res = 'global ' + res

		return res

	def getSignature(self):
		return ', '.join(introspection.signature(self.function)[1:])

	def getDescription(self):
		return strings.stripText(self.function.__doc__ or '', preserveIndent=True, stripLines=True)

class TriggerPropertyInfo(object):

	def __init__(self, name, conf):
		self.name = name
		self.is_direct = bool(conf.get('direct'))
		self._conf = conf

	def getName(self):
		res = "<b>%s</b>" % self.name
	
		if self.is_direct:
			res = 'direct ' + res

		return res

	def getDescription(self, direction):
		f = self._conf.get(direction)
		if f:
			res = strings.stripText(f.__doc__ or '', preserveIndent=True, stripLines=True)
			res = 'Calls %s\n\n%s' % (f.__name__, res)
			return res
		else:
			return ''

def formatValueSet(attr):
	vs = attr.get('ValueSet')
	if vs:
		res = []
		res.append('<TABLE>')
		for value, conf in itemsSorted(vs):
			label = conf.get('Label', '')
			if label.lower() == value: label = ''
			res.append('<TR><TD><b>%s</b></TD><TD>%s</TD></TR>' % (value, label))
		res.append('</TABLE>')
		return '\n'.join(res)
	else:
		return '&nbsp;'		



def main(*args, **kwargs):
	dumpDocs(GFParser.getXMLelements())

if __name__ == '__main__':
	main(sys.argv[1:])
