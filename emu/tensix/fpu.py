import struct
import math

M32 = 0xFFFFFFFF

# ── Format conversion ────────────────────────────────────────────────────

def _19bit_to_float(val):
  # Layout: { sign[18], mantissa[17:8] (10 bits), exponent[7:0] (8 bits) }
  sign = (val >> 18) & 1
  mant = (val >> 8) & 0x3FF
  exp  = val & 0xFF
  # Map to FP32: mantissa zero-padded from 10 to 23 bits
  fp32_bits = (sign << 31) | (exp << 23) | (mant << 13)
  return struct.unpack('f', struct.pack('I', fp32_bits))[0]

def _float_to_19bit(f):
  if math.isnan(f):
    return (0x7F << 8) | 0x200  # NaN marker: exp=0x7F in bits[7:0], quiet-NaN mant bit in bits[17:8]
  bits = struct.unpack('I', struct.pack('f', float(f)))[0]
  sign = (bits >> 31) & 1
  exp  = (bits >> 23) & 0xFF
  mant = (bits >> 13) & 0x3FF
  return (sign << 18) | (mant << 8) | exp

def _dest_to_float(val):
  return struct.unpack('f', struct.pack('I', val & M32))[0]

def _float_to_dest(f):
  if math.isnan(f):
    return 0x7FC00000
  return struct.unpack('I', struct.pack('f', float(f)))[0]

# 19-bit -inf for ZEROSRC with write_mode=1 (SrcA negative-infinity fill)
# Layout: sign=1, mant=0, exp=0xFF in bits[7:0]
_NEG_INF_19BIT = (1 << 18) | 0xFF


class FPU:
  def __init__(self, srca, srcb, dest):
    self.srca = srca
    self.srcb = srcb
    self.dest = dest

  def zeroacc(self, d):
    if d.clear_mode == 0:   self.dest.clear_valid(d.where)
    elif d.clear_mode == 1: self.dest.clear_range(d.where, 16)
    elif d.clear_mode == 2: self.dest.clear_half(d.where & 1)
    else:                   self.dest.clear_all()

  def zerosrc(self, d):
    if d.src_mask & 1:  # SrcA
      fill = _NEG_INF_19BIT if d.write_mode else 0
      bank = self.srca.banks[self.srca.fpu_bank]
      for r in range(64):
        for c in range(16):
          bank.rows[r][c] = fill
    if d.src_mask & 2:  # SrcB (always zero, never -inf)
      bank = self.srcb.banks[self.srcb.fpu_bank]
      for r in range(64):
        for c in range(16):
          bank.rows[r][c] = 0

  def mvmul(self, d, rwc):
    dst_base = d.dst + rwc.d * 16
    srca_bank = self.srca.banks[self.srca.fpu_bank]
    srcb_bank = self.srcb.banks[self.srcb.fpu_bank]
    srca_base = rwc.a * 16
    srcb_base = rwc.b * 8
    for row in range(8):
      for col in range(16):
        acc = 0.0
        for k in range(16):
          srca_row = (srca_base + k) % 64
          srcb_row = (srcb_base + row) % 64
          a = _19bit_to_float(srca_bank.rows[srca_row][col])
          b = _19bit_to_float(srcb_bank.rows[srcb_row][k])
          acc += a * b
        dest_row = (dst_base + row) % self.dest.ROWS
        if self.dest.valid[dest_row]:
          acc += _dest_to_float(self.dest.bits[dest_row][col])
        self.dest.bits[dest_row][col] = _float_to_dest(acc)
        self.dest.valid[dest_row] = True

  def elwadd(self, d, rwc):
    dst_base = d.dst + rwc.d * 16
    srca_bank = self.srca.banks[self.srca.fpu_bank]
    srcb_bank = self.srcb.banks[self.srcb.fpu_bank]
    srca_base = rwc.a * 16
    srcb_base = rwc.b * 16
    for row in range(16):
      for col in range(16):
        srca_row = (srca_base + row) % 64
        srcb_row = (srcb_base + row) % 64
        a = _19bit_to_float(srca_bank.rows[srca_row][col])
        b = _19bit_to_float(srcb_bank.rows[srcb_row][col])
        result = a + b
        dest_row = (dst_base + row) % self.dest.ROWS
        if d.dest_accum_en and self.dest.valid[dest_row]:
          result += _dest_to_float(self.dest.bits[dest_row][col])
        self.dest.bits[dest_row][col] = _float_to_dest(result)
        self.dest.valid[dest_row] = True

  def gmpool(self, d, rwc):
    dst_base = d.dst + rwc.d * 16
    srca_bank = self.srca.banks[self.srca.fpu_bank]
    srca_base = rwc.a * 16
    for row in range(16):
      srca_row = (srca_base + row) % 64
      dest_row = (dst_base + row) % self.dest.ROWS
      was_valid = self.dest.valid[dest_row]
      for col in range(16):
        val = _19bit_to_float(srca_bank.rows[srca_row][col])
        if was_valid:
          old = _dest_to_float(self.dest.bits[dest_row][col])
          val = max(val, old)
        self.dest.bits[dest_row][col] = _float_to_dest(val)
      self.dest.valid[dest_row] = True

  def movb2d(self, d, rwc):
    srcb_bank = self.srcb.banks[self.srcb.fpu_bank]
    m = d.movb2d_instr_mod
    nrows = 1 if m == 0 else (4 if m == 1 else 8)
    for row in range(nrows):
      src_row = (d.src + row) % 64
      dest_row = (d.dst + rwc.d * 16 + row) % self.dest.ROWS
      for col in range(16):
        val = _19bit_to_float(srcb_bank.rows[src_row][col])
        self.dest.bits[dest_row][col] = _float_to_dest(val)
        self.dest.valid[dest_row] = True

  def _movd2x(self, d, rwc, bank):
    nrows = 1 if d.instr_mod == 0 else 4
    for row in range(nrows):
      dest_row = (d.dst + rwc.d * 16 + row) % self.dest.ROWS
      dst_row = (d.src + row) % 64
      for col in range(16):
        val = _dest_to_float(self.dest.bits[dest_row][col]) if self.dest.valid[dest_row] else 0.0
        bank.rows[dst_row][col] = _float_to_19bit(val)

  def movd2a(self, d, rwc): self._movd2x(d, rwc, self.srca.banks[self.srca.fpu_bank])
  def movd2b(self, d, rwc): self._movd2x(d, rwc, self.srcb.banks[self.srcb.fpu_bank])

  def cleardvalid(self, d):
    if d.cleardvalid & 1: self.srca.release_from_fpu()
    if d.cleardvalid & 2: self.srcb.release_from_fpu()

  def trnspsrcb(self, d):
    bank = self.srcb.banks[self.srcb.fpu_bank]
    block = [[bank.rows[16 + r][c] for c in range(16)] for r in range(16)]
    for r in range(16):
      for c in range(16):
        bank.rows[16 + r][c] = block[c][r]
