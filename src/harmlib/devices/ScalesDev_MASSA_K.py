import time
import serial
from decimal import Decimal


class ScalesDevProtocol(object):
	
	def getWeight(self):
		"""
		waits for finish and returns weights
		"""
		return self.queryFinished().getWeight()

	def queryWait(self):
		"""
		waits for finish and returns result
		"""
		while True:
			result = self.query()
			if result.isFinished():
				break
		return result


class ScalesDevProtocol2Result(ScalesDevProtocol):
	def __init__(self, bytes, debugInfo=None):
		data = map(ord, bytes)
		self.__status = data[0]
		self.__scale  = data[1]
		self.__weight = data[4] << 16 | data[3] << 8 | data[2]
		self.__debugInfo = debugInfo

	def getWeight(self):
		w = self.__weight
		if w & 1 << 23:
			w = (1 << 23) - w
		return Decimal(w) / Decimal(10 ** (self.__scale + 3))

	def isFinished(self):
		return bool(self.__status & 1<<7)

	def isZero(self):
		return bool(self.__status & 1<<6)

	def isNET(self):
		return bool(self.__status & 1<<5)
	
	# for debug tuneup
	def getDebugInfo(self):
		return self.__debugInfo


class ScalesDevProtocol2(ScalesDevProtocol):

	def __init__(self, port, timeout=0.100, retries=3):
		self.__port = serial.Serial(
			port         = port, 
			baudrate     = 4800, 
			bytesize     = serial.EIGHTBITS,
			parity       = serial.PARITY_EVEN,
			stopbits     = serial.STOPBITS_ONE,
			timeout      = timeout,
		)
		self.__retries = retries

		# stats for debug tuneup
		self.__maxtime = 0
		self.__maxtries = 0


	def query(self):
		for i in xrange(self.__retries):
			self.__port.write(chr(0x4A))
			t = time.time()
			data = self.__port.read(5)
			t = time.time() - t
			if len(data) == 5:
				self.__maxtime  = max(self.__maxtime,  t)
				self.__maxtries = max(self.__maxtries, i+1)
				return ScalesDevProtocol2Result(data, (self.__maxtime, self.__maxtries))
		raise serial.SerialTimeoutException, 'Read timeout'


	def selectZero(self):
		self.__port.write(chr(0x0E))

	def selectTareWeight(self):
		self.__port.write(chr(0x0D))

	def close(self):
		self.__port.close()


class ScalesDev(object):

	PROTOCOLS = {
		2 : ScalesDevProtocol2,
	}

	def __init__(self, port, protocol=2):
		self.__protocol = self.PROTOCOLS[protocol](port)

	def __getattr__(self, name):
		return getattr(self.__protocol, name)


if __name__ == '__main__':
	from harmonylib.test.testScalesDev_MASSA_K import test
	test()
