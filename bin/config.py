server_url = 'http://127.0.0.1:8080/harmony'

import os
import sys

project_path = os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]

if os.name == 'posix':
	python_bin = os.path.join(sys.prefix, 'bin')
else:
	python_bin = sys.prefix
