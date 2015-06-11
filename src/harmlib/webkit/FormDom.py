import re
import codecs
from xml.dom import Node
import xml.dom.minidom

from gnue.common.datasources.access import *
from src.harmonylib.webkit import AccessObject


def nodeApplyEditable(node, update, insert):
	node.setAttribute('editable', accessToEditable(
		((ACCESS.UPDATE if update else 0) | (ACCESS.INSERT if insert else 0)) & editableToAccess(node.getAttribute('editable') or 'Y')
	))


def nodeApplyDeletable(node, deletable):
	node.setAttribute('deletable', 'Y' if accessToDeletable(
		(ACCESS.DELETE if deletable else 0) & deletableToAccess(node.getAttribute('deletable') != 'N')
	) else 'N')

def nodeComplyAttributes(node, attributes):
	for key, value in attributes.iteritems():
		if node.getAttribute(key) != value:
			return False
	return True


def nodeIterChildren(node):
	child = node.firstChild
	while child:
		yield child
		child = child.nextSibling


def nodeFindChild(node, nodeType, nodeName, attributes=None):
	for i in nodeIterChildren(node):
		if i.nodeType == nodeType and i.nodeName == nodeName and (attributes is None or nodeComplyAttributes(i, attributes)):
			return i


def nodeMoveChildren(src, dst):
	for i in tuple(nodeIterChildren(src)):

		if i.nodeType == Node.ELEMENT_NODE and i.hasAttribute('name'):
			overwritten = nodeFindChild(dst, Node.ELEMENT_NODE, i.nodeName, {'name' : i.getAttribute('name')})
			if overwritten:
				nodeMoveChildren(overwritten, i)
				dst.removeChild(overwritten)

		dst.appendChild(src.removeChild(i))


def EncodeWriter(unicodeOutputStream, encoding, errors='replace'):
	"""
	Gets unicode. Writes str to output
	"""
	return codecs.lookup(encoding)[3](unicodeOutputStream, errors)


class Dom(object):

	CONTENT_NODES = set((Node.TEXT_NODE, Node.CDATA_SECTION_NODE))
		
	def __init__(self, fname, get_form_path=lambda x: x):
		f = open(get_form_path(fname), 'rt')
		try:
			self.dom = xml.dom.minidom.parse(f)
		finally:
			f.close()

	def iterNodesRecursiveFiltered(self, filter):

		def _iterNodesRecursive(node):

			if filter(node):
				yield node

			child = node.firstChild
			while child:
				for i in _iterNodesRecursive(child):
					yield i
				child = child.nextSibling

		return _iterNodesRecursive(self.dom)

	def iterNodesRecursive(self, nodeType, nodeName=None, nodeNameStartsWith=None, attributes=None):
		return self.iterNodesRecursiveFiltered(
			lambda node: (
					(nodeType           is None or node.nodeType == nodeType)
				and (nodeName           is None or node.nodeName == nodeName)
				and (nodeNameStartsWith is None or node.nodeName.startswith(nodeNameStartsWith))
				and (attributes         is None or nodeComplyAttributes(node, attributes))
			)
		)

	def writexml(self, out, encoding='Cp1251', indent=''):
		self.dom.writexml(EncodeWriter(out, encoding), encoding=encoding,  indent='\n' if indent else '', addindent=indent)
		

REC_CODE_FN_TAG = re.compile('''\$FN\{(\w+)\}([ruid]+)''')

class FormDom(Dom):

	def __init__(self, fname, get_form_path=lambda x: x):
		super(FormDom, self).__init__(fname, get_form_path=get_form_path)

		for importNode in tuple(self.iterNodesRecursive(Node.ELEMENT_NODE, nodeNameStartsWith='import-')):
			#rint "import", importNode.nodeName, importNode.getAttribute('name'), importNode.parentNode.nodeName, importNode.parentNode.getAttribute('name')

			newNode = LibraryDom.getLibrary(importNode.getAttribute('library'), get_form_path=get_form_path).createNode(importNode)
			importNode.parentNode.replaceChild(newNode, importNode)

		# remove all whitespace text nodes
		for node in tuple(self.iterNodesRecursiveFiltered(lambda node: node.nodeType in self.CONTENT_NODES)):
			if not node.data.lstrip():
				node.parentNode.removeChild(node)


	def applyAccess(self, access):

		# old global form access apply
		update = bool(access & AccessObject.ACCESS_UPDATE)
		insert = bool(access & AccessObject.ACCESS_INSERT)
		delete = bool(access & AccessObject.ACCESS_DELETE)

		if not (update and insert and delete):

			for node in self.iterNodesRecursiveFiltered(lambda node: node.nodeType == Node.ELEMENT_NODE):

				if node.nodeName == 'block' and node.hasAttribute('datasource'):
					nodeApplyEditable(node, update, insert)
					nodeApplyDeletable(node, delete)

				elif node.nodeName == 'field' and node.parentNode.hasAttribute('datasource'):
					nodeApplyEditable(node, update, insert)


	def applyFunctionAccess(self, functionAccess):

		# apply function access
		for node in tuple(self.iterNodesRecursiveFiltered(lambda node: node.nodeType == Node.ELEMENT_NODE)):
			#rint node.nodeName
	
			# apply code access
			if node.nodeName in ('trigger', 'action', 'calc'):
				child = node.firstChild
				while child:
					if isinstance(child, (xml.dom.minidom.Text, xml.dom.minidom.CDATASection)):
						child.data = self.applyCodeAccess(child.data, functionAccess)
					child = child.nextSibling

			fns = node.attributes.get('a:fn') 
			if fns:
				remove = False
				for fn in fns.value.split(','):
					a = functionAccess.get(fn.strip())

					if node.nodeName in ('block', 'field'):
						if a:
							insert, update, delete = a
						else:
							insert = update = delete = False
						#rint node.nodeName, update, insert, delete
						nodeApplyEditable(node, update, insert)
						if node.nodeName == 'block':
							nodeApplyDeletable(node, delete)
					else:
						if not a:
							remove = True
				if remove:
					#rint "remove node", node.nodeName
					node.parentNode.removeChild(node)

				
	def applyCodeAccess(self, code, functionAccess):
		"""
		'$FN{FN_FINDOC}ruid'
		"""
		def fn(m):
			fn, sa = m.groups()
			a = functionAccess.get(fn)
			if a:
				insert, update, delete = a
				read = True
			else:
				insert = update = delete = False
				read = False

			result = []

			if (not sa or 'r' in sa) and read:
				result.append('r')
			if (not sa or 'u' in sa) and update:
				result.append('u')
			if (not sa or 'i' in sa) and insert:
				result.append('i')
			if (not sa or 'd' in sa) and delete:
				result.append('d')

			return ''.join(result)

		return REC_CODE_FN_TAG.sub(fn, code)


class LibraryDom(FormDom):

	__cache = {}

	@classmethod
	def getLibrary(cls, fname, get_form_path=lambda x: x):
		mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = os.stat(get_form_path(fname))

		if fname in cls.__cache:
			l, old_size, old_mtime = cls.__cache[fname]
			if size != old_size or mtime != old_mtime:	# form was changed
				l = None
		else:
			l = None

		if l is None:
			l = LibraryDom(fname, get_form_path=get_form_path)
			cls.__cache[fname] = l, size, mtime
		return l

	def __init__(self, *args, **kwargs):
		super(LibraryDom, self).__init__(*args, **kwargs)
		#rint 'load lib', args[0]

	def createNode(self, importNode):
		
		assert importNode.hasAttribute('name')
		assert importNode.hasAttribute('library')

		#rint importNode.nodeName, importNode.getAttribute('library'), importNode.getAttribute('name')

		for i in self.iterNodesRecursive(
				Node.ELEMENT_NODE,
				importNode.nodeName[len('import-'):],
				attributes={'name' : importNode.getAttribute('name')},
			):

			newNode = i.cloneNode(True)

			# copy attributes from importNode to this node
			for i in xrange(importNode.attributes.length):
				attr = importNode.attributes.item(i)
				if attr.name == 'as':
					newNode.setAttribute('name', attr.value)
					
				elif attr.name not in ('name', 'library'):
					#rint 'attr nodetype', attr.nodeType, attr.name
					newNode.setAttributeNode(attr.cloneNode(True))
				

			# copy importNode contents
			nodeMoveChildren(importNode, newNode)

			return newNode

		raise KeyError, importNode


def EncodeWriter(unicodeOutputStream, encoding, errors='replace'):
	"""
	Gets unicode, writes str to output
	"""
	return codecs.lookup(encoding)[3](unicodeOutputStream, errors)


if __name__ == '__main__':

	import os
	os.chdir(r'Z:\projects\harmony\forms\harmony')

	import time
	t = time.time()
	d = FormDom(r'Z:\projects\harmony\forms\harmony\spr_prod.gfd')

	functionAccess = {
	#	'FN_PROD_ORG_ART' : (True, True, True),
	}

	#             UID
	d.applyAccess(7)
	d.applyFunctionAccess(functionAccess)
	d.writexml(open(r'Z:\projects\harmony\src\harmonylib\webkit\output.gfd', 'wb'), 'Cp1251', indent='\t')
	
	print time.time() - t
