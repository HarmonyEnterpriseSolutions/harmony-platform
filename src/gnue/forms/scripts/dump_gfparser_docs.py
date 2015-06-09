from gnue.forms.GFParser import getXMLelements



def main():
	for k, v in sorteditems(getXMLelements()):

		if k.startswith('import-'):
			continue

		print '== Tag: %s ==' % k
		
		print "%s[[br]]" % v.get('Description', '') or v.get('Label', '')
		
		print 'Importable: %s[[br]]' % v.get('Importable', False)

		print 'Parent tags: %s[[br]]' % ', '.join(v.get('ParentTags', ('-',)))

		if v.get('SingleInstance'):
			print 'Single instance: %s[[br]]' %  v['SingleInstance']

		if v.get('Attributes'):
			print "=== Attributes: ==="
			print "|| Attribute || Type || Default || Description ||"

			
			for a, av in sorteditems(v['Attributes']):
				print "|| %s || %s || %s || %s ||" % (
					a,
					av.get('Typecast').__name__,
					av.get('Default', 'N'),
					av.get('Description', '') or av.get('Label', ''),
				)


def sorteditems(d):
	attrs = d.keys()
	attrs.sort()
	for a in attrs:
		yield a, d[a]

if __name__ == '__main__':
	main()