"""
File Name: datablock.py
Description: This class handles QR code data blocks, supporting encoding in numeric, alphanumeric, binary, and ECI formats for QR codes.
Author: Ni Ruiyang 31808600
Date: May 23, 2025
"""

from __future__ import annotations
import re
from collections.abc import Sequence
from typing import Union, Optional

from bitstream import _BitStream



class QRDataBlock:
	"""Data segment for QR Code. Supports numeric, alphanumeric, and binary modes."""
	
	@staticmethod
	def make_bytes(data: Union[bytes,Sequence[int]]) -> QRDataBlock:
		"""Creates a segment for raw binary data.
		
		This method takes a sequence of bytes or integers and converts it into a QRDataBlock
		that represents the binary data in a format suitable for QR code encoding.
		"""
		bb = _BitStream()
		for b in data:
			bb.append_bits(b, 8)
		return QRDataBlock(QRDataBlock.Mode.BYTE, len(data), bb)
	
	
	@staticmethod
	def make_numeric(digits: str) -> QRDataBlock:
		"""Creates a segment for decimal digits.
		
		This method takes a string of digits and encodes it into a QRDataBlock. 
		It raises a ValueError if the input string contains any non-numeric characters.
		"""
		if not QRDataBlock.is_numeric(digits):
			raise ValueError("String contains non-numeric characters")
		bb = _BitStream()
		i: int = 0
		while i < len(digits):
			n: int = min(len(digits) - i, 3)
			bb.append_bits(int(digits[i: i + n]), n * 3 + 1)
			i += n
		return QRDataBlock(QRDataBlock.Mode.NUMERIC, len(digits), bb)
	
	
	@staticmethod
	def make_alphanumeric(text: str) -> QRDataBlock:
		"""Creates a segment for alphanumeric text (A-Z, 0-9, space, $%*+-./:).
		
		This method encodes a string of alphanumeric characters into a QRDataBlock.
		It raises a ValueError if the input string contains any characters that cannot be encoded
		in alphanumeric mode.
		"""
		if not QRDataBlock.is_alphanumeric(text):
			raise ValueError("String contains unencodable characters in alphanumeric mode")
		bb = _BitStream()
		for i in range(0, len(text) - 1, 2):
			temp: int = QRDataBlock._ALPHANUMERIC_ENCODING_TABLE[text[i]] * 45
			temp += QRDataBlock._ALPHANUMERIC_ENCODING_TABLE[text[i + 1]]
			bb.append_bits(temp, 11)
		if len(text) % 2 > 0:
			bb.append_bits(QRDataBlock._ALPHANUMERIC_ENCODING_TABLE[text[-1]], 6)
		return QRDataBlock(QRDataBlock.Mode.ALPHANUMERIC, len(text), bb)
	
	
	@staticmethod
	def make_segments(text: str) -> list[QRDataBlock]:
		"""Creates an optimal segment list from text, choosing the best encoding modes.
		
		This method analyzes the input text and determines the most efficient way to encode it
		into QR code segments, returning a list of QRDataBlock instances.
		If the input text is empty, it returns an empty list.
		"""
		if text == "":
			return []
		elif QRDataBlock.is_numeric(text):
			return [QRDataBlock.make_numeric(text)]
		elif QRDataBlock.is_alphanumeric(text):
			return [QRDataBlock.make_alphanumeric(text)]
		else:
			return [QRDataBlock.make_bytes(text.encode("UTF-8"))]
	
	
	@staticmethod
	def make_eci(assignval: int) -> QRDataBlock:
		"""Creates a segment for ECI (Extended Channel Interpretation) assignment.
		
		This method encodes an ECI assignment value into a QRDataBlock. 
		It raises a ValueError if the assignment value is out of the valid range.
		"""
		bb = _BitStream()
		if assignval < 0:
			raise ValueError("ECI assignment value out of range")
		elif assignval < (1 << 7):
			bb.append_bits(assignval, 8)
		elif assignval < (1 << 14):
			bb.append_bits(0b10, 2)
			bb.append_bits(assignval, 14)
		elif assignval < 1000000:
			bb.append_bits(0b110, 3)
			bb.append_bits(assignval, 21)
		else:
			raise ValueError("ECI assignment value out of range")
		return QRDataBlock(QRDataBlock.Mode.ECI, 0, bb)
	
	
	@staticmethod
	def is_numeric(text: str) -> bool:
		"""Checks if text contains only digits (0-9).
		
		This method uses a regular expression to verify that the input string consists solely
		of numeric characters. It returns True if the string is numeric, otherwise False.
		"""
		return QRDataBlock._NUMERIC_REGEX.fullmatch(text) is not None
	
	
	@staticmethod
	def is_alphanumeric(text: str) -> bool:
		"""Checks if text contains only allowed alphanumeric characters.
		
		This method uses a regular expression to check if the input string contains only
		characters that are valid in alphanumeric mode. It returns True if the string is valid,
		otherwise False.
		"""
		return QRDataBlock._ALPHANUMERIC_REGEX.fullmatch(text) is not None
	
	
	def __init__(self, mode: QRDataBlock.Mode, numch: int, bitdata: Sequence[int]) -> None:
		"""Creates a QR Code segment with given mode and data.
		
		Args:
			mode: Encoding mode
			numch: Character count
			bitdata: Encoded data bits
		"""
		if numch < 0:
			raise ValueError()
		self._mode = mode
		self._numchars = numch
		self._bitdata = list(bitdata)
	
	
	def get_mode(self) -> QRDataBlock.Mode:
		"""Returns segment's encoding mode.
		
		This method retrieves the encoding mode of the QRDataBlock instance.
		"""
		return self._mode
	
	def get_num_chars(self) -> int:
		"""Returns segment's character count.
		
		This method returns the number of characters represented in the QRDataBlock.
		"""
		return self._numchars
	
	def get_data(self) -> list[int]:
		"""Returns a copy of segment's data bits.
		
		This method provides a copy of the encoded data bits stored in the QRDataBlock.
		"""
		return list(self._bitdata)
	
	
	@staticmethod
	def get_total_bits(segs: Sequence[QRDataBlock], version: int) -> Optional[int]:
		"""Calculates total bits needed for segments at given version.
		
		This method computes the total number of bits required to encode a list of QRDataBlock
		segments for a specified QR code version. If the character count exceeds the limit for
		the given version, it returns None.
		"""
		result = 0
		for seg in segs:
			ccbits: int = seg.get_mode().num_char_count_bits(version)
			if seg.get_num_chars() >= (1 << ccbits):
				return None
			result += 4 + ccbits + len(seg._bitdata)
		return result
	
	
	# ---- Constants ----
	
	# Describes precisely all strings that are encodable in numeric mode.
	_NUMERIC_REGEX: re.Pattern[str] = re.compile(r"[0-9]*")
	
	# Describes precisely all strings that are encodable in alphanumeric mode.
	_ALPHANUMERIC_REGEX: re.Pattern[str] = re.compile(r"[A-Z0-9 $%*+./:-]*")
	
	# Dictionary of "0"->0, "A"->10, "$"->37, etc.
	_ALPHANUMERIC_ENCODING_TABLE: dict[str,int] = {ch: i for (i, ch) in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:")}
	
	
	# ---- Public helper enumeration ----
	
	class Mode:
		"""QR Code segment encoding mode."""
		
		def __init__(self, modebits: int, charcounts: tuple[int,int,int]):
			"""Creates encoding mode with bit pattern and character count lengths.
			
			Args:
				modebits: The bit pattern representing the encoding mode.
				charcounts: A tuple containing the character count lengths for different versions.
			"""
			self._modebits = modebits
			self._charcounts = charcounts
		
		def get_mode_bits(self) -> int:
			"""Returns mode indicator bits.
			
			This method retrieves the bit pattern that indicates the encoding mode.
			"""
			return self._modebits
		
		def num_char_count_bits(self, ver: int) -> int:
			"""Returns character count field width for given version.
			
			This method determines the number of bits required to represent the character count
			for a specific QR code version.
			"""
			return self._charcounts[(ver + 7) // 17]
		
		# Placeholders
		NUMERIC     : QRDataBlock.Mode
		ALPHANUMERIC: QRDataBlock.Mode
		BYTE        : QRDataBlock.Mode
		KANJI       : QRDataBlock.Mode
		ECI         : QRDataBlock.Mode
	
	# Public constants. Create them outside the class.
	Mode.NUMERIC      = Mode(0x1, (10, 12, 14))
	Mode.ALPHANUMERIC = Mode(0x2, ( 9, 11, 13))
	Mode.BYTE         = Mode(0x4, ( 8, 16, 16))
	Mode.KANJI        = Mode(0x8, ( 8, 10, 12))
	Mode.ECI          = Mode(0x7, ( 0,  0,  0))



