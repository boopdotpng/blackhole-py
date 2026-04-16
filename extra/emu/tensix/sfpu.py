import struct
import math

M32 = 0xFFFFFFFF

# ── FP32 bit helpers ─────────────────────────────────────────────────────

def _to_float(bits): return struct.unpack('f', struct.pack('I', bits & M32))[0]
def _to_bits(f):     return struct.unpack('I', struct.pack('f', float(f)))[0]
def _sign(bits):     return (bits >> 31) & 1
def _exp(bits):      return (bits >> 23) & 0xFF
def _mant(bits):     return bits & 0x7FFFFF
def _is_neg(bits):   return bool(bits & 0x80000000)

POS_INF      = 0x7F800000
NEG_INF      = 0xFF800000
CONST_0P8363 = 0x3F560000
CONST_ONE    = 0x3F800000

def _bf16_to_fp32(bf16):
  return (bf16 & 0xFFFF) << 16

def _fp16_to_fp32(fp16):
  s = (fp16 >> 15) & 1
  e = (fp16 >> 10) & 0x1F
  m = fp16 & 0x3FF
  if e == 0:
    if m == 0: return s << 31
    while not (m & 0x400):  # denorm -> normalized FP32
      m <<= 1
      e -= 1
    e += 1
    m &= 0x3FF
    return (s << 31) | ((e + 112) << 23) | (m << 13)
  if e == 0x1F:
    return (s << 31) | (0xFF << 23) | (m << 13)
  return (s << 31) | ((e + 112) << 23) | (m << 13)


# ── SFPU — 32-lane SIMD Vector Unit ──────────────────────────────────────

class SFPU:
  NUM_LREGS = 17
  NUM_LANES = 32

  def __init__(self, dest):
    self.dest = dest
    # LReg file: 17 registers x 32 lanes x 32 bits
    self.lregs = [[0] * self.NUM_LANES for _ in range(self.NUM_LREGS)]
    self.lane_flags = [False] * self.NUM_LANES  # per-lane condition flags
    self.flag_stack = []                        # stack for nested predication
    self.use_lane_flags = False                 # master predication enable
    for lane in range(self.NUM_LANES):
      self.lregs[8][lane] = POS_INF
      self.lregs[9][lane] = NEG_INF
      self.lregs[10][lane] = CONST_0P8363
      self.lregs[15][lane] = lane * 2  # TILEID
      self.lregs[16][lane] = CONST_ONE

  def _is_writable(self, idx):
    return 0 <= idx <= 7 or 11 <= idx <= 14

  def _lane_enabled(self, lane):
    return self.lane_flags[lane] if self.use_lane_flags else True

  def _lanes(self):
    for lane in range(self.NUM_LANES):
      if self._lane_enabled(lane):
        yield lane

  # ── Data movement: Dest <-> LReg ─────────────────────────────────────

  def sfpload(self, d, rwc):
    if not self._is_writable(d.lreg_ind): return
    base = (d.dest_reg_addr + rwc.d * 16) % self.dest.ROWS
    for lane in self._lanes():
      row = (base + lane // 16) % self.dest.ROWS
      col = lane % 16
      val = self.dest.bits[row][col] if self.dest.valid[row] else 0
      self.lregs[d.lreg_ind][lane] = val & M32

  def sfploadi(self, d):
    if not self._is_writable(d.lreg_ind): return
    for lane in self._lanes():
      match d.instr_mod0:
        case 0:  val = _bf16_to_fp32(d.imm16)  # BF16 -> FP32
        case 2:  val = _fp16_to_fp32(d.imm16)  # FP16 -> FP32
        case 4:  val = d.imm16                 # U16
        case 6:                                # S15 — sign-extend bit 14
          v = d.imm16 & 0x7FFF
          val = v | 0xFFFF8000 if v & 0x4000 else v
        case 8:  val = (self.lregs[d.lreg_ind][lane] & 0xFFFF) | (d.imm16 << 16)
        case 10: val = (self.lregs[d.lreg_ind][lane] & 0xFFFF0000) | d.imm16
        case _:  val = d.imm16
      self.lregs[d.lreg_ind][lane] = val & M32

  def sfpstore(self, d, rwc):
    base = (d.dest_reg_addr + rwc.d * 16) % self.dest.ROWS
    for lane in self._lanes():
      row = (base + lane // 16) % self.dest.ROWS
      col = lane % 16
      self.dest.bits[row][col] = self.lregs[d.lreg_ind][lane] & M32
      self.dest.valid[row] = True

  # ── FP32 FMA arithmetic (MAD sub-unit, 2-cycle) ─────────────────────

  def sfpmad(self, d):
    if not self._is_writable(d.lreg_dest): return
    neg_b = d.instr_mod1 & 1
    neg_c = (d.instr_mod1 >> 1) & 1
    for lane in self._lanes():
      a = _to_float(self.lregs[d.lreg_src_a][lane])
      b = _to_float(self.lregs[d.lreg_src_b][lane])
      c = _to_float(self.lregs[d.lreg_src_c][lane])
      if neg_b: b = -b
      if neg_c: c = -c
      self.lregs[d.lreg_dest][lane] = _to_bits(a * b + c)

  def sfpadd(self, d):
    if not self._is_writable(d.lreg_dest): return
    neg_b = d.instr_mod1 & 1
    neg_c = (d.instr_mod1 >> 1) & 1
    for lane in self._lanes():
      b = _to_float(self.lregs[d.lreg_src_b][lane])
      c = _to_float(self.lregs[d.lreg_src_c][lane])
      if neg_b: b = -b
      if neg_c: c = -c
      self.lregs[d.lreg_dest][lane] = _to_bits(b + c)

  def sfpmul(self, d):
    if not self._is_writable(d.lreg_dest): return
    neg_b = d.instr_mod1 & 1
    for lane in self._lanes():
      a = _to_float(self.lregs[d.lreg_src_a][lane])
      b = _to_float(self.lregs[d.lreg_src_b][lane])
      if neg_b: b = -b
      self.lregs[d.lreg_dest][lane] = _to_bits(a * b)

  # ── FP32 immediate arithmetic ────────────────────────────────────────

  def sfpmuli(self, d):
    if not self._is_writable(d.lreg_dest): return
    imm = _to_float(_bf16_to_fp32(d.imm16_math))
    for lane in self._lanes():
      x = _to_float(self.lregs[d.lreg_dest][lane])
      self.lregs[d.lreg_dest][lane] = _to_bits(x * imm)

  def sfpaddi(self, d):
    if not self._is_writable(d.lreg_dest): return
    imm = _to_float(_bf16_to_fp32(d.imm16_math))
    for lane in self._lanes():
      x = _to_float(self.lregs[d.lreg_dest][lane])
      self.lregs[d.lreg_dest][lane] = _to_bits(x + imm)

  # ── FP utilities ─────────────────────────────────────────────────────

  def sfpexexp(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      exp = _exp(self.lregs[d.lreg_c][lane])
      if d.instr_mod1 & 1:  # debiased
        result = (exp - 127) & M32 if exp > 0 else 0
      else:
        result = exp
      self.lregs[d.lreg_dest][lane] = result

  def sfpexman(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      m = _mant(self.lregs[d.lreg_c][lane])
      if not (d.imm12_math & 2): m |= 0x800000  # add implicit 1
      self.lregs[d.lreg_dest][lane] = m

  def sfpsetexp(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      new_exp = (d.imm12_math & 0xFF) if d.instr_mod1 & 1 else (self.lregs[d.lreg_dest][lane] & 0xFF)
      self.lregs[d.lreg_dest][lane] = (_sign(c) << 31) | (new_exp << 23) | _mant(c)

  def sfpdivp2(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      if d.instr_mod1 & 1:  # set exponent directly
        new_exp = d.imm12_math & 0xFF
      else:                 # add to exponent
        exp_add = d.imm12_math & 0xFF
        if d.imm12_math & 0x800: exp_add -= 256  # sign-extend
        new_exp = max(0, min(255, _exp(c) + exp_add))
      self.lregs[d.lreg_dest][lane] = (_sign(c) << 31) | (new_exp << 23) | _mant(c)

  def sfpabs(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = self.lregs[d.lreg_c][lane] & 0x7FFFFFFF

  def sfpsetsgn(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      match d.instr_mod1:
        case 0: self.lregs[d.lreg_dest][lane] = c & 0x7FFFFFFF
        case 1: self.lregs[d.lreg_dest][lane] = c | 0x80000000
        case 2:
          d_sign = self.lregs[d.lreg_dest][lane] & 0x80000000
          self.lregs[d.lreg_dest][lane] = d_sign | (c & 0x7FFFFFFF)
        case _: self.lregs[d.lreg_dest][lane] = c

  # ── Integer arithmetic ───────────────────────────────────────────────

  def sfpiadd(self, d):
    if not self._is_writable(d.lreg_dest): return
    use_imm = d.instr_mod1 & 1
    negate = (d.instr_mod1 >> 1) & 1
    set_cc = (d.instr_mod1 >> 2) & 1
    # Sign-extend 12-bit immediate
    imm = d.imm12_math if not (d.imm12_math & 0x800) else (d.imm12_math | 0xFFFFF000)
    imm &= M32
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      b = imm if use_imm else self.lregs[d.lreg_dest][lane]
      result = ((c - b) if negate else (c + b)) & M32
      self.lregs[d.lreg_dest][lane] = result
      if set_cc: self.lane_flags[lane] = bool(result & 0x80000000)

  def sfpmul24(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      a = self.lregs[d.lreg_src_a][lane] & 0xFFFFFF
      b = self.lregs[d.lreg_src_b][lane] & 0xFFFFFF
      self.lregs[d.lreg_dest][lane] = (a * b) & M32

  # ── Bit manipulation ─────────────────────────────────────────────────

  def sfpand(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] &= self.lregs[d.lreg_c][lane]

  def sfpor(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] |= self.lregs[d.lreg_c][lane]

  def sfpnot(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = (~self.lregs[d.lreg_c][lane]) & M32

  def sfpxor(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = (self.lregs[d.lreg_dest][lane] ^ self.lregs[d.lreg_c][lane]) & M32

  def sfplz(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      val = self.lregs[d.lreg_c][lane]
      self.lregs[d.lreg_dest][lane] = 32 if val == 0 else 31 - val.bit_length() + 1

  # ── Shifts ───────────────────────────────────────────────────────────

  def sfpshft(self, d):
    if not self._is_writable(d.lreg_dest): return
    shift = d.imm12_math & 0x1F
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      match d.instr_mod1:
        case 0: result = (c << shift) & M32        # logical left
        case 1: result = c >> shift                # logical right
        case 2:                                    # arithmetic right
          if c & 0x80000000:
            result = ((c >> shift) | (M32 << (32 - shift))) & M32
          else:
            result = c >> shift
        case _: result = c
      self.lregs[d.lreg_dest][lane] = result

  def sfpshft2(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      b = self.lregs[d.lreg_dest][lane]
      shift = self.lregs[d.lreg_c][lane] & 0x1F
      if d.instr_mod1 == 0:
        self.lregs[d.lreg_dest][lane] = (b << shift) & M32
      else:
        self.lregs[d.lreg_dest][lane] = b >> shift

  # ── Comparison / predication ─────────────────────────────────────────

  def sfpsetcc(self, d):
    for lane in range(self.NUM_LANES):
      c = self.lregs[d.lreg_c][lane]
      match d.instr_mod1 & 3:
        case 0: self.lane_flags[lane] = _is_neg(c)
        case 1: self.lane_flags[lane] = (c & 0x7FFFFFFF) != 0
        case 2: self.lane_flags[lane] = not _is_neg(c)
        case 3: self.lane_flags[lane] = (c & 0x7FFFFFFF) == 0

  def sfpgt(self, d):
    for lane in range(self.NUM_LANES):
      vd = _to_float(self.lregs[d.lreg_dest][lane])
      vc = _to_float(self.lregs[d.lreg_c][lane])
      self.lane_flags[lane] = vd > vc

  def sfpencc(self, d):
    if d.instr_mod1 == 0:
      self.use_lane_flags = False
    else:
      self.use_lane_flags = True
      if d.instr_mod1 == 1:   self.lane_flags = [True] * self.NUM_LANES
      elif d.instr_mod1 == 2: self.lane_flags = [False] * self.NUM_LANES

  def sfppushc(self, d): self.flag_stack.append(list(self.lane_flags))
  def sfppopc(self, d):
    if self.flag_stack: self.lane_flags = self.flag_stack.pop()
  def sfpcompc(self, d): self.lane_flags = [not f for f in self.lane_flags]

  # ── Move ─────────────────────────────────────────────────────────────

  def sfpmov(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c = self.lregs[d.lreg_c][lane]
      if d.instr_mod1 == 1: c ^= 0x80000000  # flip sign
      self.lregs[d.lreg_dest][lane] = c

  # ── Type conversion / rounding ───────────────────────────────────────

  def sfpstochrnd(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = self.lregs[d.lreg_src_c][lane]

  def sfpcast(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      self.lregs[d.lreg_dest][lane] = self.lregs[d.lreg_src_c][lane]

  # ── Configuration ────────────────────────────────────────────────────

  def sfpconfig(self, d):
    if 11 <= d.config_dest <= 14:
      val = _bf16_to_fp32(d.imm16_math)
      for lane in range(self.NUM_LANES):
        self.lregs[d.config_dest][lane] = val

  # ── Approximate reciprocal ──────────────────────────────────────────

  def sfparecip(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      c_bits = self.lregs[d.lreg_c][lane]
      c = _to_float(c_bits)
      if c == 0.0:
        self.lregs[d.lreg_dest][lane] = POS_INF if not _is_neg(c_bits) else NEG_INF
      elif math.isinf(c):
        self.lregs[d.lreg_dest][lane] = 0x80000000 if _is_neg(c_bits) else 0
      else:
        self.lregs[d.lreg_dest][lane] = _to_bits(1.0 / c)

  # ── LUT ──────────────────────────────────────────────────────────────

  def sfplutfp32(self, d):
    if not self._is_writable(d.lreg_dest): return
    for lane in self._lanes():
      x = _to_float(self.lregs[3][lane])
      abs_x = abs(x)
      i = 0 if abs_x < 1.0 else (1 if abs_x < 2.0 else 2)
      slope = _to_float(self.lregs[i][lane])
      intercept = _to_float(self.lregs[4 + i][lane])
      self.lregs[d.lreg_dest][lane] = _to_bits(slope * abs_x + intercept)

  # ── Swap ─────────────────────────────────────────────────────────────

  def sfpswap(self, d):
    if not (self._is_writable(d.lreg_dest) and self._is_writable(d.lreg_c)): return
    for lane in self._lanes():
      c = _to_float(self.lregs[d.lreg_c][lane])
      vd = _to_float(self.lregs[d.lreg_dest][lane])
      self.lregs[d.lreg_dest][lane] = _to_bits(min(c, vd))
      self.lregs[d.lreg_c][lane] = _to_bits(max(c, vd))
