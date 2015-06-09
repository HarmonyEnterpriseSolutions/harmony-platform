
import os, sys

lib     = "\\PURELIB"
scripts = "\\SCRIPTS"

data = __file__
for i in xrange(3):
	data = os.path.split(data)[0]

config  = os.path.join(data, "etc")
