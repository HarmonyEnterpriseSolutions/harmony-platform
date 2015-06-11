import os
import sys

from django.core.management import setup_environ, ManagementUtility

import win32serviceutil
import win32service


project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_dir, 'src'))
from bin.harmonyserv import settings


HOST = None
PORT = 8888


class MyService(win32serviceutil.ServiceFramework):
	"""NT Service."""
    
	_svc_name_ = "harmonyserv_service"
	_svc_display_name_ = "django - harmonyserv"

	def SvcDoRun(self):
		sys.stdout = open(os.path.join(project_dir, 'log', 'harmonyserv.log'      ), 'at', buffering=0)
		sys.stderr = open(os.path.join(project_dir, 'log', 'harmonyserv.error.log'), 'at', buffering=0)
		
		host = HOST
		port = PORT
		
		if port is None:
			try:
				port = int(host)
				host = None
			except:
				pass

		if host is None:
			if HOST is None:
				import socket
				host = socket.gethostbyname(socket.gethostname())
			else:
				host = HOST

		setup_environ(settings)
		utility = ManagementUtility([sys.argv[0], 'runserver', '%s:%s' % (host, port or PORT), '--noreload'])
		utility.execute()
        
	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		try:
			sys.exit(0)
		finally:
			# very important for use with py2exe
			# otherwise the Service Controller never knows that it is stopped !
			self.ReportServiceStatus(win32service.SERVICE_STOPPED) 
        
if __name__ == '__main__':
	win32serviceutil.HandleCommandLine(MyService)
