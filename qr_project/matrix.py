# Code was written by Pang Yuyan(31808748),Ding Sihan(31808904).

from __future__ import annotations
from collections.abc import Sequence
from typing import Optional, Union
from reedsolo import RSCodec
import itertools, collections
import re

from datablock import QRDataBlock
from bitstream import _BitStream
from utils import _get_bit, DataTooLongError



class QRMatrix:
	"""Core class for generating QR codes with support for all standard versions and error levels"""
	
	# Core parameters
	MIN_VERSION: int = 1  # Minimum supported QR version
	MAX_VERSION: int = 40  # Maximum supported QR version
	
	# Score calculation factors for mask evaluation
	_PENALTY_N1: int = 3
	_PENALTY_N2: int = 3
	_PENALTY_N3: int = 40
	_PENALTY_N4: int = 10
	
	# Core generation methods
	@staticmethod
	def encode_text(text: str, ecl: QRMatrix.Ecc, qr_color: tuple = (0, 0, 0)) -> QRMatrix:
		"""Generates QR code from input text with specified error correction and color settings"""
		segs: list[QRDataBlock] = QRDataBlock.make_segments(text)
		qr = QRMatrix.encode_segments(segs, ecl)
		qr._color = qr_color
		return qr
	
	@staticmethod
	def encode_binary(data: Union[bytes,Sequence[int]], ecl: QRMatrix.Ecc) -> QRMatrix:
		"""Creates QR from binary input (max 2953 bytes) with specified error correction"""
		return QRMatrix.encode_segments([QRDataBlock.make_bytes(data)], ecl)
	
	@staticmethod
	def encode_segments(segs: Sequence[QRDataBlock], ecl: QRMatrix.Ecc, minversion: int = 1, maxversion: int = 40, mask: int = -1, boostecl: bool = True) -> QRMatrix:
		"""Builds QR code from data segments using specified parameters. Handles version selection and masking"""
		
		if not (QRMatrix.MIN_VERSION <= minversion <= maxversion <= QRMatrix.MAX_VERSION) or not (-1 <= mask <= 7):
			raise ValueError("Invalid value")
		
		# Find optimal version
		for version in range(minversion, maxversion + 1):
			datacapacitybits: int = QRMatrix._get_num_data_codewords(version, ecl) * 8
			datausedbits: Optional[int] = QRDataBlock.get_total_bits(segs, version)
			if (datausedbits is not None) and (datausedbits <= datacapacitybits):
				break
			if version >= maxversion:
				msg: str = "Segment too long"
				if datausedbits is not None:
					msg = f"Data length = {datausedbits} bits, Max capacity = {datacapacitybits} bits"
				raise DataTooLongError(msg)
		assert datausedbits is not None
		
		# Optimize error correction
		for newecl in (QRMatrix.Ecc.MEDIUM, QRMatrix.Ecc.QUARTILE, QRMatrix.Ecc.HIGH):
			if boostecl and (datausedbits <= QRMatrix._get_num_data_codewords(version, newecl) * 8):
				ecl = newecl
		
		# Build data stream
		bb = _BitStream()
		for seg in segs:
			bb.append_bits(seg.get_mode().get_mode_bits(), 4)
			bb.append_bits(seg.get_num_chars(), seg.get_mode().num_char_count_bits(version))
			bb.extend(seg._bitdata)
		assert len(bb) == datausedbits
		
		# Add padding
		datacapacitybits = QRMatrix._get_num_data_codewords(version, ecl) * 8
		assert len(bb) <= datacapacitybits
		bb.append_bits(0, min(4, datacapacitybits - len(bb)))
		bb.append_bits(0, -len(bb) % 8)
		assert len(bb) % 8 == 0
		
		# Fill remaining space
		for padbyte in itertools.cycle((0xEC, 0x11)):
			if len(bb) >= datacapacitybits:
				break
			bb.append_bits(padbyte, 8)
		
		# Convert to bytes
		datacodewords = bytearray([0] * (len(bb) // 8))
		for (i, bit) in enumerate(bb):
			datacodewords[i >> 3] |= bit << (7 - (i & 7))
		
		# Initialize QR object
		return QRMatrix(version, ecl, datacodewords, mask)
	
	
	# QR version identifier (1-40)
	_version: int
	
	# Matrix dimensions in modules (21-177)
	_size: int
	
	# Error correction configuration
	_errcorlvl: QRMatrix.Ecc
	
	# Selected mask pattern (0-7)
	_mask: int
	
	# Module matrix (dark/light pattern)
	_modules: list[list[bool]]
	
	# Function module tracking
	_isfunction: list[list[bool]]
	
	# Visual color settings
	_color: tuple
 
 
	def __init__(self, version: int, errcorlvl: QRMatrix.Ecc, datacodewords: Union[bytes,Sequence[int]], msk: int) -> None:
		"""Low-level QR Code constructor. Most users should use encode_text() instead.
		
		Args:
			version: QR version (1-40)
			errcorlvl: Error correction level
			datacodewords: Data bytes to encode
			msk: Mask pattern (-1 for auto)
		"""
		if not (QRMatrix.MIN_VERSION <= version <= QRMatrix.MAX_VERSION):
			raise ValueError("Version value out of range")
		if not (-1 <= msk <= 7):
			raise ValueError("Mask value out of range")
		
		self._version = version
		self._size = version * 4 + 17
		self._errcorlvl = errcorlvl
		self._color = (0, 0, 0)
		
		# Setup matrices
		self._modules = [[False] * self._size for _ in range(self._size)]
		self._isfunction = [[False] * self._size for _ in range(self._size)]
		self._modules_before_mask = [[False] * self._size for _ in range(self._size)]
		
		# Generate pattern
		self._draw_function_patterns()
		allcodewords: bytes = self._add_ecc_and_interleave(bytearray(datacodewords))
		self._draw_codewords(allcodewords)

		# Store pre-mask state
		for y in range(self._size):
			for x in range(self._size):
				self._modules_before_mask[y][x] = self._modules[y][x]
		
		# Apply optimal masking
		if msk == -1:
			minpenalty: int = 1 << 32
			for i in range(8):
				self._apply_mask(i)
				self._draw_format_bits(i)
				penalty = self._calculate_penalty_score()
				if penalty < minpenalty:
					msk = i
					minpenalty = penalty
				self._apply_mask(i)
		
		assert 0 <= msk <= 7
		self._mask = msk
		self._apply_mask(msk)
		self._draw_format_bits(msk)
		
		del self._isfunction
	

	def _draw_function_patterns(self) -> None:
		"""Sets up the basic structural elements of the QR matrix"""
		# Place timing patterns
		for i in range(self._size):
			self._set_function_module(6, i, i % 2 == 0)
			self._set_function_module(i, 6, i % 2 == 0)
		
		# Place finder patterns
		self._draw_finder_pattern(3, 3)
		self._draw_finder_pattern(self._size - 4, 3)
		self._draw_finder_pattern(3, self._size - 4)
		
		# Setup alignment pattern grid
		alignpatpos: list[int] = self._get_alignment_pattern_positions()
		numalign: int = len(alignpatpos)
		skips: Sequence[tuple[int,int]] = ((0, 0), (0, numalign - 1), (numalign - 1, 0))
		for i in range(numalign):
			for j in range(numalign):
				if (i, j) not in skips:  # Skip finder pattern locations
					self._draw_alignment_pattern(alignpatpos[i], alignpatpos[j])
		
		# Initialize format data
		self._draw_format_bits(0)  # Temporary mask, updated later
		self._draw_version()
	
	
	def _draw_format_bits(self, mask: int) -> None:
		"""Implements format information encoding with error correction in two locations"""
		# Generate ECC and combine data
		data: int = self._errcorlvl.formatbits << 3 | mask
		rem: int = data
		for _ in range(10):
			rem = (rem << 1) ^ ((rem >> 9) * 0x537)
		bits: int = (data << 10 | rem) ^ 0x5412
		assert bits >> 15 == 0
		
		# Primary format info placement
		for i in range(0, 6):
			self._set_function_module(8, i, _get_bit(bits, i))
		self._set_function_module(8, 7, _get_bit(bits, 6))
		self._set_function_module(8, 8, _get_bit(bits, 7))
		self._set_function_module(7, 8, _get_bit(bits, 8))
		for i in range(9, 15):
			self._set_function_module(14 - i, 8, _get_bit(bits, i))
		
		# Backup format info placement
		for i in range(0, 8):
			self._set_function_module(self._size - 1 - i, 8, _get_bit(bits, i))
		for i in range(8, 15):
			self._set_function_module(8, self._size - 15 + i, _get_bit(bits, i))
		self._set_function_module(8, self._size - 8, True)  # Fixed dark module
	
	
	def _draw_version(self) -> None:
		"""Encodes version information for QR codes version 7 and above"""
		if self._version < 7:
			return
		
		# Generate ECC for version info
		rem: int = self._version
		for _ in range(12):
			rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
		bits: int = self._version << 12 | rem
		assert bits >> 18 == 0
		
		# Place version blocks
		for i in range(18):
			bit: bool = _get_bit(bits, i)
			a: int = self._size - 11 + i % 3
			b: int = i // 3
			self._set_function_module(a, b, bit)
			self._set_function_module(b, a, bit)
	
	
	def _draw_finder_pattern(self, x: int, y: int) -> None:
		"""Places a finder pattern block at specified coordinates"""
		for dy in range(-4, 5):
			for dx in range(-4, 5):
				xx, yy = x + dx, y + dy
				if (0 <= xx < self._size) and (0 <= yy < self._size):
					self._set_function_module(xx, yy, max(abs(dx), abs(dy)) not in (2, 4))
	
	
	def _draw_alignment_pattern(self, x: int, y: int) -> None:
		"""Creates alignment pattern at given position"""
		for dy in range(-2, 3):
			for dx in range(-2, 3):
				self._set_function_module(x + dx, y + dy, max(abs(dx), abs(dy)) != 1)
	
	
	def _set_function_module(self, x: int, y: int, isdark: bool) -> None:
		"""Marks module as functional and sets its state"""
		assert type(isdark) is bool
		self._modules[y][x] = isdark
		self._isfunction[y][x] = True
  
	def get_version(self) -> int:
		"""Retrieves QR code version (1-40)"""
		return self._version
	
	def get_size(self) -> int:
		"""Returns matrix size (21-177)"""
		return self._size
	
	def get_error_correction_level(self) -> QRMatrix.Ecc:
		"""Retrieves error correction configuration"""
		return self._errcorlvl
	
	def get_mask(self) -> int:
		"""Gets applied mask pattern (0-7)"""
		return self._mask
	
	def get_module(self, x: int, y: int) -> bool:
		"""Checks module state at given coordinates
		Returns dark (True) or light (False) state
		Origin at top-left (0,0)"""
		return (0 <= x < self._size) and (0 <= y < self._size) and self._modules[y][x]
	
	def get_color(self) -> tuple:
		"""Retrieves QR code RGB color value"""
		return self._color
	
	def set_color(self, color: tuple) -> None:
		"""Sets the color of this QR Code.
		
		Args:
			color: RGB color tuple
		"""
		self._color = color
  

	@staticmethod
	def _get_num_data_codewords(ver: int, ecl: QRMatrix.Ecc) -> int:
		"""Calculates data capacity in codewords for given version and ECC level"""
		return QRMatrix._get_num_raw_data_modules(ver) // 8 \
			- QRMatrix._ECC_CODEWORDS_PER_BLOCK    [ecl.ordinal][ver] \
			* QRMatrix._NUM_ERROR_CORRECTION_BLOCKS[ecl.ordinal][ver]
	
	
	def _count_penalty_patterns(self, runhistory: collections.deque[int]) -> int:
		"""Evaluates pattern penalties after light run addition"""
		n: int = runhistory[1]
		assert n <= self._size * 3
		core: bool = n > 0 and (runhistory[2] == runhistory[4] == runhistory[5] == n) and runhistory[3] == n * 3
		return (1 if (core and runhistory[0] >= n * 4 and runhistory[6] >= n) else 0) \
		     + (1 if (core and runhistory[6] >= n * 4 and runhistory[0] >= n) else 0)
	
	
	def _finalize_penalty_count(self, currentruncolor: bool, currentrunlength: int, runhistory: collections.deque[int]) -> int:
		"""Processes final penalty calculation at line end"""
		if currentruncolor:
			self._update_penalty_history(currentrunlength, runhistory)
			currentrunlength = 0
		currentrunlength += self._size
		self._update_penalty_history(currentrunlength, runhistory)
		return self._count_penalty_patterns(runhistory)
	
	
	def _update_penalty_history(self, currentrunlength: int, runhistory: collections.deque[int]) -> None:
		if runhistory[0] == 0:
			currentrunlength += self._size
		runhistory.appendleft(currentrunlength)
	
	def _add_ecc_and_interleave(self, data: bytearray) -> bytes:
		"""Applies error correction and data interleaving"""
		version: int = self._version
		assert len(data) == QRMatrix._get_num_data_codewords(version, self._errcorlvl)
		
		# Setup ECC parameters
		num_blocks: int = QRMatrix._NUM_ERROR_CORRECTION_BLOCKS[self._errcorlvl.ordinal][version]
		ecc_codewords_per_block = QRMatrix._ECC_CODEWORDS_PER_BLOCK[self._errcorlvl.ordinal][version]
		
		rs = RSCodec(ecc_codewords_per_block)
		
		# Split into blocks
		data_per_block = len(data) // num_blocks
		blocks = []
		for i in range(num_blocks):
			start = i * data_per_block
			end = (i + 1) * data_per_block
			if i == num_blocks - 1:
				end = len(data)
			blocks.append(bytes(data[start:end]))
		
		# Apply ECC to blocks
		encoded_blocks = []
		for blk in blocks:
			encoded = rs.encode(blk)
			encoded_blocks.append(encoded)
		
		# Interleave blocks
		result = bytearray()
		max_block_len = max(len(b) for b in encoded_blocks)
		for i in range(max_block_len):
			for blk in encoded_blocks:
				if i < len(blk):
					result.append(blk[i])
		return bytes(result)
	
	
	def _draw_codewords(self, data: bytes) -> None:
		"""Maps codewords to matrix using zigzag pattern"""
		assert len(data) == QRMatrix._get_num_raw_data_modules(self._version) // 8
		
		i: int = 0  # Bit position tracker
		for right in range(self._size - 1, 0, -2):
			if right <= 6:
				right -= 1
			for vert in range(self._size):
				for j in range(2):
					x: int = right - j
					upward: bool = (right + 1) & 2 == 0
					y: int = (self._size - 1 - vert) if upward else vert
					if (not self._isfunction[y][x]) and (i < len(data) * 8):
						self._modules[y][x] = _get_bit(data[i >> 3], 7 - (i & 7))
						i += 1
		assert i == len(data) * 8
  

	
	
	def _apply_mask(self, mask: int) -> None:
		"""Applies XOR masking pattern to data modules
		Requires function modules to be marked and codewords drawn
		Note: Applying same mask twice reverses the effect"""
		if not (0 <= mask <= 7):
			raise ValueError("Mask value out of range")
		masker: collections.abc.Callable[[int,int],int] = QRMatrix._MASK_PATTERNS[mask]
		for y in range(self._size):
			for x in range(self._size):
				self._modules[y][x] ^= (masker(x, y) == 0) and (not self._isfunction[y][x])
	
	
	def _calculate_penalty_score(self) -> int:
		"""Evaluates current module configuration and returns penalty score
		Used for optimal mask pattern selection"""
		result: int = 0
		size: int = self._size
		modules: list[list[bool]] = self._modules
		
		# Row pattern analysis
		for y in range(size):
			runcolor: bool = False
			runx: int = 0
			runhistory = collections.deque([0] * 7, 7)
			for x in range(size):
				if modules[y][x] == runcolor:
					runx += 1
					if runx == 5:
						result += QRMatrix._PENALTY_N1
					elif runx > 5:
						result += 1
				else:
					self._update_penalty_history(runx, runhistory)
					if not runcolor:
						result += self._count_penalty_patterns(runhistory) * QRMatrix._PENALTY_N3
					runcolor = modules[y][x]
					runx = 1
			result += self._finalize_penalty_count(runcolor, runx, runhistory) * QRMatrix._PENALTY_N3
		
		# Column pattern analysis
		for x in range(size):
			runcolor = False
			runy: int = 0
			runhistory = collections.deque([0] * 7, 7)
			for y in range(size):
				if modules[y][x] == runcolor:
					runy += 1
					if runy == 5:
						result += QRMatrix._PENALTY_N1
					elif runy > 5:
						result += 1
				else:
					self._update_penalty_history(runy, runhistory)
					if not runcolor:
						result += self._count_penalty_patterns(runhistory) * QRMatrix._PENALTY_N3
					runcolor = modules[y][x]
					runy = 1
			result += self._finalize_penalty_count(runcolor, runy, runhistory) * QRMatrix._PENALTY_N3
		
		# Block pattern check
		for y in range(size - 1):
			for x in range(size - 1):
				if modules[y][x] == modules[y][x + 1] == modules[y + 1][x] == modules[y + 1][x + 1]:
					result += QRMatrix._PENALTY_N2
		
		# Module balance analysis
		dark: int = sum((1 if cell else 0) for row in modules for cell in row)
		total: int = size**2
		k: int = (abs(dark * 20 - total * 10) + total - 1) // total - 1
		assert 0 <= k <= 9
		result += k * QRMatrix._PENALTY_N4
		assert 0 <= result <= 2568888
		return result
	
	
	def _get_alignment_pattern_positions(self) -> list[int]:
		"""Generates coordinates for alignment patterns based on version"""
		if self._version == 1:
			return []
		else:
			numalign: int = self._version // 7 + 2
			step: int = (self._version * 8 + numalign * 3 + 5) // (numalign * 4 - 4) * 2
			result: list[int] = [(self._size - 7 - i * step) for i in range(numalign - 1)] + [6]
			return list(reversed(result))
	
	
	@staticmethod
	def _get_num_raw_data_modules(ver: int) -> int:
		"""Calculates total data capacity for given version
		Returns bit count after excluding function modules"""
		if not (QRMatrix.MIN_VERSION <= ver <= QRMatrix.MAX_VERSION):
			raise ValueError("Version number out of range")
		result: int = (16 * ver + 128) * ver + 64
		if ver >= 2:
			numalign: int = ver // 7 + 2
			result -= (25 * numalign - 10) * numalign - 55
			if ver >= 7:
				result -= 36
		assert 208 <= result <= 29648
		return result
	
	
	
	
	_ECC_CODEWORDS_PER_BLOCK: Sequence[Sequence[int]] = (
		# Version: (note that index 0 is for padding, and is set to an illegal value)
		# 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40    Error correction level
		(-1,  7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),  # Low
		(-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28),  # Medium
		(-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30),  # Quartile
		(-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30))  # High
	
	_NUM_ERROR_CORRECTION_BLOCKS: Sequence[Sequence[int]] = (
		# Version: (note that index 0 is for padding, and is set to an illegal value)
		# 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40    Error correction level
		(-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4,  4,  4,  4,  4,  6,  6,  6,  6,  7,  8,  8,  9,  9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25),  # Low
		(-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5,  5,  8,  9,  9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49),  # Medium
		(-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8,  8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68),  # Quartile
		(-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81))  # High
	
	_MASK_PATTERNS: Sequence[collections.abc.Callable[[int,int],int]] = (
		(lambda x, y:  (x + y) % 2                  ),
		(lambda x, y:  y % 2                        ),
		(lambda x, y:  x % 3                        ),
		(lambda x, y:  (x + y) % 3                  ),
		(lambda x, y:  (x // 3 + y // 2) % 2        ),
		(lambda x, y:  x * y % 2 + x * y % 3        ),
		(lambda x, y:  (x * y % 2 + x * y % 3) % 2  ),
		(lambda x, y:  ((x + y) % 2 + x * y % 3) % 2),
	)
	
	class Ecc:
		ordinal: int  # Error level index (0-3)
		formatbits: int  # Format information bits
		
		"""Error correction configuration for QR symbols"""
		def __init__(self, i: int, fb: int) -> None:
			self.ordinal = i
			self.formatbits = fb
		
		# Level definitions
		LOW     : QRMatrix.Ecc
		MEDIUM  : QRMatrix.Ecc
		QUARTILE: QRMatrix.Ecc
		HIGH    : QRMatrix.Ecc
	
	# Error correction level definitions with tolerance percentages
	Ecc.LOW      = Ecc(0, 1)  # ~7% error tolerance
	Ecc.MEDIUM   = Ecc(1, 0)  # ~15% error tolerance
	Ecc.QUARTILE = Ecc(2, 3)  # ~25% error tolerance
	Ecc.HIGH     = Ecc(3, 2)  # ~30% error tolerance



