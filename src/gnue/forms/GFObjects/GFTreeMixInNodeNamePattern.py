import datetime
import re

from gnue.common.datasources.access  import ACCESS
from src.gnue.forms.GFObjects import GFTreeMixInBase

REC_FIELD = re.compile(r"\%(\([A-Za-z_]\w*\))")


class GFTreeMixInNodeNamePattern(GFTreeMixInBase):

	def _phase_1_init_(self):
		super(GFTreeMixInNodeNamePattern, self)._phase_1_init_()
	
		# state fix
		self.__nodeNameChanging = False

		# nodename -> create __nodeNameFields, __nodeNamePattern
		# substitute %(fieldname)s with %s and add field into list
		self.__nodeNameFields = []
		def sub(m):
			self.__nodeNameFields.append(m.groups()[0][1:-1])
			return '%'
		self.__nodeNamePattern = REC_FIELD.sub(sub, self.nodename)

		#rint "nodename fields:", self.__nodeNameFields
		#rint "nodename pattern:", self.__nodeNamePattern


	#############################################################################################
	# Accessing data via fields
	#
	def _getFieldValueAt(self, row, field):
		return self._rs[row][self._rsField(field)]

	def _setFieldValueAt(self, row, field, value):
		self._rs[row][self._rsField(field)] = value

	def getFieldFormattedValueAt(self, row, field):

		# NOTE: tree has no entries so displayparser is not accessible
		# TODO: extract display parsing and formatting to GFField
		# unless can't set values to notext fields

		value = self._getFieldValueAt(row, field)
		if value is None:
			return ""
		else:
			value = self._block.getField(field).lookup(value)

			# WORKAROUND: since displayHandler in entry we ca't use it for formatting
			# TODO: formatter must be at field level
			if isinstance(value, datetime.date):
				return value.strftime('%x')
			else:
				return str(value)

	def _setFieldFormattedValueAt(self, row, field, text):
		"""
		used when setting from clipboard
		"""

		# NOTE: tree has no entries so displayparser is not accessible
		# TODO: extract display parsing and formatting to GFField
		# unless can't set values to notext fields

		text = self._block.getField(field).reverse_lookup(text)
		self._setFieldValueAt(row, field, text or None)

	#############################################################################################

	def formatNodeNameAt(self, row, colIgnored=0):
		return self.__nodeNamePattern % tuple([self.getFieldFormattedValueAt(row, field) for field in self.__nodeNameFields])

	def setNodeNameAt(self, row, text):
		"""
		tries to unparse text as in nodeNamePattern and set to fields
		works only for text fields
		"""
		pattern = re.sub(r'(?i)\\\%[^a-z]*[a-z]', lambda m: '(.+)', re.escape(self.__nodeNamePattern)) + '$'
		m = re.match(pattern, text)
		if m:
			for i, text in enumerate(m.groups()):
				field = self.__nodeNameFields[i]
				# do not allow to edit primary key
				if field != self.fld_id:
					# avoid node revalidation when changing tree label text
					self.__nodeNameChanging = True
					self._setFieldFormattedValueAt(row, field, text)
					self.__nodeNameChanging = False
			return True
		return False

	def isNodeNameChanging(self):
		"""
		called from __ds_record_changed to make shure that node field change was not made from setNodeNameAt
		"""
		return self.__nodeNameChanging
	
	def getNodeNameFields(self):
		return self.__nodeNameFields

	def isNodeNameEditable(self):
		"""
		if tree node name can be updated on existent or new node
		"""
		if self.labelEdit:
			for i in self.getNodeNameFields():
				if not self._block.getField(i).hasAccess(ACCESS.WRITE):
					return False
			return True
		else:
			return False
