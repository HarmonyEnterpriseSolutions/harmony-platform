# GNU Enterprise Common Library - Utilities - DBase driver
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
# $Id: dbf.py 9222 2007-01-08 13:02:49Z johannes $

import struct
import datetime
import types
import os

# =============================================================================
# Exceptions
# =============================================================================

class InvalidFormatError (Exception):
	def __init__ (self, message):
		Exception.__init__ (self, "Not a valid DBF file: %s" % message)


# =============================================================================
# Class implementing read-only access to dBase files
# =============================================================================

class dbf:

	_SIGNATURES = { 2: 'FoxBase',
		3: 'File without DBT',
		4: 'dBase IV w/o memo file',
		5: 'dBase V w/o memo file',
		48: 'Visual FoxPro with DBC',
		49: 'Visual FoxPro with AutoIncrement field',
		67: '.dbv memo var size (Flagship)',
		123: 'dBase IV with memo',
		131: 'dBase III with memo file',
		139: 'dBase IV with memo file',
		142: 'dBase IV with SQL table',
		179: '.dbv and .dbt memo (Flagship)',
		229: 'Clipper SIX driver with SMT memo file',
		245: 'FoxPro with memo file',
		251: 'FoxPro'}

	# ---------------------------------------------------------------------------
	# Create a new wrapper around the given dbase file
	# ---------------------------------------------------------------------------

	def __init__ (self, filename):

		self.__filename = filename
		self.__file     = open (filename, 'rb')
		self.__size     = os.stat (filename).st_size

		self.fields     = []
		self.signature  = None
		self.lastUpdate = None
		self.headerLen  = 0
		self.recordLen  = 0
		self.incompleteTransaction = False
		self.encrypted             = False
		self.mdxFlag        = None
		self.languageDriver = None

		self.__version    = None
		self.__cache      = []

		self.__readHeader ()
		self.__readFieldDescriptorArray ()
		self.__readRecords ()


	# ---------------------------------------------------------------------------
	# Read and parse the header of the file
	# ---------------------------------------------------------------------------

	def __readHeader (self):

		self.__file.seek (0, 0)

		self.__version = struct.unpack ('<B', self.__file.read (1)) [0]
		if not self.__version in self._SIGNATURES:
			raise InvalidFormatError, "wrong signature"

		self.signature = self._SIGNATURES [self.__version]

		self.lastUpdate   = struct.unpack ('<3B', self.__file.read (3))
		self.__numRecords = struct.unpack ('<L', self.__file.read (4)) [0]
		self.headerLen    = struct.unpack ('<H', self.__file.read (2)) [0]
		self.recordLen    = struct.unpack ('<H', self.__file.read (2)) [0]

		# Check the real and logical file size
		cSize = self.headerLen + self.__numRecords * self.recordLen
		if not self.__size - cSize in [0, 1]:
			raise InvalidFormatError, "wrong file size"

		reserved = self.__file.read (2)

		self.incompleteTransaction = self.__file.read (1) == '\x01'
		self.encrypted             = self.__file.read (1) == '\x01'

		freeRecordThread = self.__file.read (4)
		reserved         = self.__file.read (8)

		self.mdxFlag        = struct.unpack ('<B', self.__file.read (1)) [0]

		# TODO: Add support for codepages (as specified by languageDriver), and
		#       have all field-values beeing unicode.
		self.languageDriver = self.__file.read (1)

		reserved = self.__file.read (2)

		self.__file.seek (self.headerLen - 1, 0)
		if not self.__file.read (1) in ['\x00', '\x0d']:
			raise InvalidFormatError, "Missing terminator flag"

		self.dataOffset = self.headerLen
		# For Visual FoxPro with DBC we have to skip the database container
		if self.__version == '\x30':
			self.dataOffset += 263


	# ---------------------------------------------------------------------------
	# Read and parse the field descriptor array starting at offset 20h
	# ---------------------------------------------------------------------------

	def __readFieldDescriptorArray (self):

		self.__file.seek (32, 0)
		append = self.fields.append

		for fix in range ((self.headerLen - 33) / 32):
			fieldName = self.__file.read (11).split ('\x00', 1) [0].strip ()
			fieldType = self.__file.read (1)
			(addr, fieldLen, decCount) = struct.unpack ('<LBB', self.__file.read (6))

			reserved       = self.__file.read (2)
			workAreaId     = struct.unpack ('<B', self.__file.read (1)) [0]
			reserved       = self.__file.read (2)
			setFieldsFlags = self.__file.read (1)
			reserved       = self.__file.read (7)
			hasIndex       = self.__file.read (1) == '\x01'

			append ((fieldName, fieldType, fieldLen, decCount, hasIndex))

		if not self.fields:
			raise InvalidFormatError, "Invalid field count"


	# ---------------------------------------------------------------------------
	# Read all records from the file and put them into the cache sequence
	# ---------------------------------------------------------------------------

	def __readRecords (self):

		self.__file.seek (self.dataOffset)
		append = self.__cache.append

		for recordNumber in xrange (self.__numRecords):
			stream = self.__file.read (self.recordLen)

			# The first byte in the record stream holds the 'deleted flag'
			if stream [0] == '*':
				continue

			append (self.__getRecordDict (stream [1:]))


	# ---------------------------------------------------------------------------
	# Convert a given record stream into a dictionary
	# ---------------------------------------------------------------------------

	def __getRecordDict (self, stream):

		# The given stream starts *after* the deleted flag, so position 0 is the
		# first byte of the first field.

		cpos   = 0
		record = {}

		for (fname, ftype, flen, fdec, index) in self.fields:
			raw = stream [cpos:cpos + flen]
			cpos += flen

			# Is the field empty ?
			if not raw.strip ():
				value = None

			# Numeric conversion
			elif ftype == 'N':
				if fdec:
					value = float (raw.split ('\x00', 1) [0].strip () or 0)
				else:
					value = int (raw.split ('\x00', 1) [0].strip () or 0)

			# Booleans
			elif ftype == 'L':
				if raw.strip () in ['?', '']:
					value = None
				else:
					value = raw.strip ().lower () in ['t', 'y']

			# Date values
			elif ftype == 'D':
				(year, month, day) = map (int, [raw [:4], raw [4:6], raw [6:]])
				value = datetime.date (year, month, day)

			# FoxPro Integers
			elif ftype == 'I':
				value = struct.unpack ('<i', raw) [0]

			# All other types (including character data)
			else:
				value = raw

			record [fname] = value

		return record


	# ---------------------------------------------------------------------------
	# Length of the file is equal to the number of records
	# ---------------------------------------------------------------------------

	def __len__ (self):
		return len (self.__cache)


	# ---------------------------------------------------------------------------
	# A file is zero if it has no records
	# ---------------------------------------------------------------------------

	def __nonzero__ (self):
		return len (self.__cache) > 0


	# ---------------------------------------------------------------------------
	# Return a generator as iterator for all records
	# ---------------------------------------------------------------------------

	def __iter__ (self):

		for record in self.__cache:
			yield record


	# ---------------------------------------------------------------------------
	# Add access method via record number (or slices)
	# ---------------------------------------------------------------------------

	def __getitem__ (self, index):
		return self.__cache [index]

# =============================================================================
# Module self test
# =============================================================================

if __name__ == '__main__':

	dbfile = dbf ('/home/johannes/checkit.dbf')

	print "STATs:"
	print "  Signature:", dbfile.signature
	print "  # Records:", len (dbfile)
	print "  Recordlen:", dbfile.recordLen
	print "  incomplete transactions:", dbfile.incompleteTransaction
	print "  Encrypted              :", dbfile.encrypted
	print
	print "  Fields"
	for fdef in dbfile.fields:
		print "    ", fdef

	raw_input ()
	print
	print "ROWS:"
	print

	for row in dbfile:
		print "  ", row
