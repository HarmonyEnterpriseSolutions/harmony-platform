from wkroot import report


class image(report):

	def getTargetUrl(self):
		return self.getConfig('servers.conf').get('reports', 'report_server') + "/image"

