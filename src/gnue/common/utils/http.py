# GNU Enterprise Common Library - Utilities - Fixes to the httplib classes
#
# Copyright 2001-2007 Free Software Foundation
#
# This file is part of GNU Enterprise
#
# GNU Enterprise is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# GNU Enterprise is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.
#
# $Id: http.py 9222 2007-01-08 13:02:49Z johannes $

import httplib
import BaseHTTPServer


# =============================================================================
# HTTPConnection sending headers and body within a single packet
# =============================================================================

class HTTPConnection (httplib.HTTPConnection):
	"""
	Class implementing a HTTP/1.1 connection, where the headers and body of a
	request is transmitted as a single packet. This improves communication speed
	of persistent connections very much.
	"""

	# ---------------------------------------------------------------------------
	# Send a complete request to the server
	# ---------------------------------------------------------------------------

	def _send_request (self, method, url, body, headers):
		"""
		Send a complete request to the server. This function is called by
		L{request} and is nearly a copy of httplib.HTTPConnection._send_request,
		having only a small change at the end.

		@param method: HTTP request method, e.g. 'POST' or 'GET'
		@param url: specifies the object beeing requested, e.g. '/index.html'
		@param body: contents to be sent as request body
		@param headers: dictionary of headers to be send as request headers
		"""

		# honour explicitly requested Host: and Accept-Encoding headers
		header_names = dict.fromkeys([k.lower() for k in headers])
		skips = {}
		if 'host' in header_names:
			skips['skip_host'] = 1
		if 'accept-encoding' in header_names:
			skips['skip_accept_encoding'] = 1

		self.putrequest(method, url, **skips)

		if body and ('content-length' not in header_names):
			self.putheader('Content-Length', str(len(body)))
		for hdr, value in headers.iteritems():
			self.putheader(hdr, value)

		if body:
			# This should be self.endheaders () without doing the actual send (). But
			# we have to maintain the proper state.
			self._buffer.extend (("", ""))

			state = self.__dict__ ['_HTTPConnection__state']
			if state == httplib._CS_REQ_STARTED:
				self.__dict__ ['_HTTPConnection__state'] = httplib._CS_REQ_SENT

			# Finally send the buffer and the body
			self.send ('\r\n'.join (self._buffer) + body)
			del self._buffer [:]

		else:
			self.endheaders ()


# =============================================================================
# HTTP request handler
# =============================================================================

class HTTPRequestHandler (BaseHTTPServer.BaseHTTPRequestHandler):
	"""
	HTTP request handler class adding the capability of buffered transfers. This
	improves communication speed of persistent connections.
	"""

	# ---------------------------------------------------------------------------
	# Setup a handler
	# ---------------------------------------------------------------------------

	def setup (self):
		"""
		Prepare the request handler for work
		"""

		self._buffer = []
		BaseHTTPServer.BaseHTTPRequestHandler.setup (self)


	# ---------------------------------------------------------------------------
	# Send server response
	# ---------------------------------------------------------------------------

	def send_response (self, code, message = None, flush = True):
		"""
		Send the response header as well as two standard headers with the server
		software and the current date. The response code will be logged.

		@param code: response code
		@param message: message of the response. If no message is given and the
		  code is listed in L{responses}, the corresponding standard message will be
		  sent.
		@param flush: if True, the current buffer as well as the response will be
		  sent immediatley to the client, otherwise it will be buffered.
		"""

		self.log_request (code)

		if message is None:
			if code in self.responses:
				message = self.responses [code][0]
			else:
				message = ''

		if self.request_version != 'HTTP/0.9':
			self.write ("%s %d %s\r\n" % (self.protocol_version, code, message),
				flush)

		self.send_header ('Server', self.version_string (), flush)
		self.send_header ('Date', self.date_time_string (), flush)


	# ---------------------------------------------------------------------------
	# Send a MIME header
	# ---------------------------------------------------------------------------

	def send_header (self, keyword, value, flush = True):
		"""
		Send a MIME header.

		@param keyword: name of the header to send
		@param value: value of the header
		@param flush: if True, the current buffer as well as the MIME header will
		  be sent immediately, otherwise it will be buffered.
		"""

		if self.request_version != 'HTTP/0.9':
			self.write ("%s: %s\r\n" % (keyword, value), flush)

		if keyword.lower () == 'connection':
			if value.lower () == 'close':
				self.close_connection = 1
			elif value.lower () == 'keep-alive':
				self.close_connection = 0


	# ---------------------------------------------------------------------------
	# End the block of MIME headers
	# ---------------------------------------------------------------------------

	def end_headers (self, flush = True):
		"""
		Send the blank line ending the MIME headers.

		@param flush: if True, send the current buffer and the blank line
		  immediately, otherwise add it to the buffer.
		"""

		if self.request_version != 'HTTP/0.9':
			self.write ("\r\n", flush)


	# ---------------------------------------------------------------------------
	# Buffer a message or transmit the current buffer
	# ---------------------------------------------------------------------------

	def write (self, message = None, flush = True):
		"""
		Add a message to the transmission buffer or send the current buffer.

		@param message: contents to be buffered or sent
		@param flush: if True, the current buffer will be sent, otherwise message
		  will be added to the buffer. The buffer get's cleared after sending.
		"""

		if flush:
			data = ''.join (self._buffer)
			if message is not None:
				data += message

			assert gDebug (2, "batch: %s" % self._buffer)
			self.wfile.write (data)
			self.wfile.flush ()

			self._buffer = []

		else:
			self._buffer.append (message)
