from __future__ import annotations

def _sext(v, w): return v - (1 << w) if v & (1 << (w - 1)) else v
def _u(v, w): return v & ((1 << w) - 1)
def rol2(v): return ((v << 2) | (v >> 30)) & 0xFFFFFFFF
def ror2(v): return ((v >> 2) | (v << 30)) & 0xFFFFFFFF
def _fmt_arg(v): return f"0x{v:X}" if isinstance(v, int) and v >= 10 else repr(v)

class Reg:
  _NAMES = {
    0: "zero", 1: "ra", 2: "sp", 3: "gp", 4: "tp",
    5: "t0", 6: "t1", 7: "t2", 8: "s0", 9: "s1",
    10: "a0", 11: "a1", 12: "a2", 13: "a3", 14: "a4", 15: "a5",
    16: "a6", 17: "a7", 18: "s2", 19: "s3", 20: "s4", 21: "s5",
    22: "s6", 23: "s7", 24: "s8", 25: "s9", 26: "s10", 27: "s11",
    28: "t3", 29: "t4", 30: "t5", 31: "t6",
  }

  def __init__(self, idx: int):
    if not 0 <= idx < 32: raise RuntimeError(f"unknown RISC-V register: {idx!r}")
    self.idx = idx

  def __int__(self): return self.idx
  def __index__(self): return self.idx
  def __repr__(self): return self._NAMES[self.idx]

zero, ra, sp, gp, tp = [Reg(i) for i in range(5)]
t0, t1, t2 = [Reg(i) for i in range(5, 8)]
s0, s1 = [Reg(i) for i in range(8, 10)]
a0, a1, a2, a3, a4, a5, a6, a7 = [Reg(i) for i in range(10, 18)]
s2, s3, s4, s5, s6, s7, s8, s9, s10, s11 = [Reg(i) for i in range(18, 28)]
t3, t4, t5, t6 = [Reg(i) for i in range(28, 32)]
fp = s0

class BitField:
  def __init__(self, hi, lo=None, *, default=0, signed=False):
    if lo is None: lo = hi
    if hi < lo: raise ValueError(f"invalid bit range {hi}:{lo}")
    self.hi, self.lo, self.default, self.signed = hi, lo, default, signed
    self.width = hi - lo + 1
    self.mask = (1 << self.width) - 1
    self.name = None

  def __set_name__(self, owner, name): self.name = name
  def __get__(self, obj, objtype=None):
    if obj is None: return self
    return self.decode((obj._raw >> self.lo) & self.mask)
  def __set__(self, obj, val):
    enc = self.encode(self.default if val is None else val)
    obj._raw = (obj._raw & ~(self.mask << self.lo)) | (enc << self.lo)
  def __eq__(self, value): return FixedBitField(self.hi, self.lo, value)
  def encode(self, val):
    if self.signed:
      if not -(1 << (self.width - 1)) <= val < (1 << (self.width - 1)):
        raise ValueError(f"{val} does not fit in signed {self.width} bits")
      return val & self.mask
    if not 0 <= val <= self.mask:
      raise ValueError(f"{val} does not fit in {self.width} bits")
    return val
  def decode(self, val): return _sext(val, self.width) if self.signed else val

class FixedBitField(BitField):
  def __init__(self, hi, lo, value):
    super().__init__(hi, lo, default=value)
    self.value = value

class RegField(BitField):
  def encode(self, val): return int(val)
  def decode(self, val): return Reg(val)

class _Bits:
  def __getitem__(self, key):
    if isinstance(key, slice): return BitField(key.start, key.stop)
    return BitField(key)
bits = b = _Bits()

class _Insn:
  """Shared base: collects BitField descriptors into a sorted layout and
  packs/unpacks a 32-bit word. Subclasses pass ``op=`` to stamp a fixed
  8-bit opcode (bits 31:24) and derive ``name`` from the class name."""
  _fields = ()
  name = None

  def __init_subclass__(cls, op=None, **kw):
    super().__init_subclass__(**kw)
    if op is not None:
      cls.opcode_ = opf = FixedBitField(31, 24, op)
      opf.name = "opcode_"
      if cls.name is None and cls.__name__.startswith("TT"): cls.name = cls.__name__[2:]
    fields = []
    for base in reversed(cls.__mro__):
      for val in vars(base).values():
        if isinstance(val, BitField) and not any(val is f for f in fields):
          fields.append(val)
    cls._fields = tuple(sorted(fields, key=lambda f: -f.hi))

  @classmethod
  def _arg_names(cls):
    seen, names = set(), []
    for f in cls._fields:
      if not isinstance(f, FixedBitField) and f.name not in seen:
        seen.add(f.name); names.append(f.name)
    return names

  def __init__(self, *args, **kw):
    self._raw = 0
    self.name = kw.pop("name", self.name)
    names = self._arg_names()
    if len(args) > len(names):
      raise TypeError(f"{type(self).__name__} expected at most {len(names)} positional args, got {len(args)}")
    vals = dict(zip(names, args))
    for k, v in kw.items():
      if k in vals: raise TypeError(f"{type(self).__name__} got duplicate value for {k!r}")
      vals[k] = v
    extra = set(vals) - set(names)
    if extra: raise TypeError(f"unexpected fields: {', '.join(sorted(extra))}")
    for f in self._fields:
      setattr(self, f.name, f.value if isinstance(f, FixedBitField) else vals.get(f.name, f.default))

  @classmethod
  def from_word(cls, word, *, name=None):
    obj = object.__new__(cls)
    obj._raw = word & 0xFFFFFFFF
    obj.name = name or cls.name
    return obj

  def to_bytes(self): return self.to_word().to_bytes(4, "little")
  def __int__(self): return self.to_word()
  def __hash__(self): return hash(self.to_word())

# --- RISC-V ---------------------------------------------------------------

class Inst(_Insn):
  def to_word(self): return self._raw & 0xFFFFFFFF
  def __eq__(self, other): return isinstance(other, Inst) and self.to_word() == other.to_word()
  def __hash__(self): return hash(self.to_word())
  def __repr__(self):
    op = _RV_OPS_BY_NAME.get(self.name)
    if op is not None: return f"{self.name}({op.repr_args(self)})"
    args = ", ".join(f"{f.name}={getattr(self, f.name)!r}" for f in self._fields if not isinstance(f, FixedBitField))
    return f"{self.name or type(self).__name__}({args})"

class RType(Inst):
  funct7 = bits[31:25]
  rs2 = RegField(24, 20)
  rs1 = RegField(19, 15)
  funct3 = bits[14:12]
  rd = RegField(11, 7)
  opcode = bits[6:0]

class IType(Inst):
  imm = BitField(31, 20, signed=True)
  rs1 = RegField(19, 15)
  funct3 = bits[14:12]
  rd = RegField(11, 7)
  opcode = bits[6:0]

class SType(Inst):
  imm11_5 = bits[31:25]
  rs2 = RegField(24, 20)
  rs1 = RegField(19, 15)
  funct3 = bits[14:12]
  imm4_0 = bits[11:7]
  opcode = bits[6:0]

  # Named construction accepts imm and splits it; from_word() decodes directly from raw bits.
  def __init__(self, *, imm=0, **kw):
    super().__init__(imm11_5=_u(imm, 12) >> 5, imm4_0=_u(imm, 5), **kw)
  @property
  def imm(self): return _sext((self.imm11_5 << 5) | self.imm4_0, 12)

class BType(Inst):
  imm12 = bits[31]
  imm10_5 = bits[30:25]
  rs2 = RegField(24, 20)
  rs1 = RegField(19, 15)
  funct3 = bits[14:12]
  imm4_1 = bits[11:8]
  imm11 = bits[7]
  opcode = bits[6:0]

  def __init__(self, *, imm=0, **kw):
    u = _u(imm, 13)
    super().__init__(imm12=(u >> 12) & 1, imm10_5=(u >> 5) & 0x3F,
                     imm4_1=(u >> 1) & 0xF, imm11=(u >> 11) & 1, **kw)
  @property
  def imm(self): return _sext((self.imm12 << 12) | (self.imm11 << 11) | (self.imm10_5 << 5) | (self.imm4_1 << 1), 13)

class UType(Inst):
  imm = bits[31:12]
  rd = RegField(11, 7)
  opcode = bits[6:0]

class JType(Inst):
  imm20 = bits[31]
  imm10_1 = bits[30:21]
  imm11 = bits[20]
  imm19_12 = bits[19:12]
  rd = RegField(11, 7)
  opcode = bits[6:0]

  def __init__(self, *, imm=0, **kw):
    u = _u(imm, 21)
    super().__init__(imm20=(u >> 20) & 1, imm10_1=(u >> 1) & 0x3FF,
                     imm11=(u >> 11) & 1, imm19_12=(u >> 12) & 0xFF, **kw)
  @property
  def imm(self): return _sext((self.imm20 << 20) | (self.imm19_12 << 12) | (self.imm11 << 11) | (self.imm10_1 << 1), 21)

class RVOp:
  def __init__(self, name, cls, args=(), *, encode=None, display=None, **fields):
    self.name, self.cls, self.args = name, cls, tuple(args)
    self.fields, self.encode, self.display = fields, encode, display or {}
    self.__name__ = name

  def __call__(self, *args, **kw):
    if len(args) > len(self.args):
      raise TypeError(f"{self.name} expected at most {len(self.args)} positional args, got {len(args)}")
    vals = {}
    for spec, val in zip(self.args, args):
      vals[spec[0] if isinstance(spec, tuple) else spec] = val
    for key, val in kw.items():
      if key in vals:
        raise TypeError(f"{self.name} got duplicate value for {key!r}")
      vals[key] = val
    for spec in self.args[len(args):]:
      if isinstance(spec, tuple) and spec[0] not in vals:
        vals[spec[0]] = spec[1]
    names = {spec[0] if isinstance(spec, tuple) else spec for spec in self.args}
    extra = set(vals) - names
    if extra: raise TypeError(f"unexpected fields: {', '.join(sorted(extra))}")
    fields = {**self.fields, **vals}
    if self.encode is not None:
      fields = self.encode(fields)
    return self.cls(name=self.name, **fields)

  def __repr__(self): return f"<RVOp {self.name}>"

  def repr_args(self, inst):
    parts = []
    for spec in self.args:
      name = spec[0] if isinstance(spec, tuple) else spec
      val = self.display[name](inst) if name in self.display else getattr(inst, name)
      parts.append((_fmt_arg(val), isinstance(spec, tuple) and val == spec[1]))
    while parts and parts[-1][1]:
      parts.pop()
    return ", ".join(part for part, _ in parts)

def _u_imm(fields): return {**fields, "imm": fields["imm"] >> 12}
def _csr_imm(fields): return {**{k: v for k, v in fields.items() if k != "csr"}, "imm": fields["csr"]}
def _shamt_imm(fields): return {**{k: v for k, v in fields.items() if k != "shamt"}, "imm": fields["shamt"]}
def _srai_imm(fields): return {**{k: v for k, v in fields.items() if k != "shamt"}, "imm": 0x400 | fields["shamt"]}

def _shamt_arg(inst): return inst.imm & 0x1F
def _u_imm_arg(inst): return inst.imm << 12
def _csr_arg(inst): return inst.imm

_R_SPECS = (
  ("add", 0, 0x00), ("sub", 0, 0x20), ("sll", 1, 0x00), ("slt", 2, 0x00),
  ("sltu", 3, 0x00), ("xor", 4, 0x00), ("srl", 5, 0x00), ("sra", 5, 0x20),
  ("or", 6, 0x00), ("and", 7, 0x00), ("mul", 0, 0x01), ("mulhu", 3, 0x01),
  ("divu", 5, 0x01), ("remu", 7, 0x01), ("sh1add", 2, 0x10),
  ("sh2add", 4, 0x10), ("sh3add", 6, 0x10), ("min", 4, 0x05),
  ("minu", 5, 0x05), ("maxu", 7, 0x05),
)
_I_SPECS = (("addi", 0), ("sltiu", 3), ("xori", 4), ("ori", 6), ("andi", 7))
_LOAD_SPECS = (("lw", 2), ("lbu", 4), ("lhu", 5))
_STORE_SPECS = (("sb", 0), ("sh", 1), ("sw", 2))
_BRANCH_SPECS = (("beq", 0), ("bne", 1), ("blt", 4), ("bge", 5), ("bltu", 6), ("bgeu", 7))

add, sub, sll, slt, sltu, xor, srl, sra, or_, and_, mul, mulhu, divu, remu, sh1add, sh2add, sh3add, min, minu, maxu = [
  RVOp(name, RType, ("rd", "rs1", "rs2"), opcode=0x33, funct3=funct3, funct7=funct7)
  for name, funct3, funct7 in _R_SPECS
]
or_.name = "or"
and_.name = "and"
zext_h = RVOp("zext_h", RType, ("rd", "rs1"), opcode=0x33, funct3=4, funct7=0x04, rs2=zero)

addi, sltiu, xori, ori, andi = [
  RVOp(name, IType, ("rd", "rs1", "imm"), opcode=0x13, funct3=funct3)
  for name, funct3 in _I_SPECS
]
slli = RVOp("slli", IType, ("rd", "rs1", ("shamt", 0)), opcode=0x13, funct3=1, encode=_shamt_imm, display={"shamt": _shamt_arg})
srli = RVOp("srli", IType, ("rd", "rs1", ("shamt", 0)), opcode=0x13, funct3=5, encode=_shamt_imm, display={"shamt": _shamt_arg})
srai = RVOp("srai", IType, ("rd", "rs1", ("shamt", 0)), opcode=0x13, funct3=5, encode=_srai_imm, display={"shamt": _shamt_arg})
ctz = RVOp("ctz", IType, ("rd", "rs1"), opcode=0x13, funct3=1, imm=0x601)
sext_b = RVOp("sext_b", IType, ("rd", "rs1"), opcode=0x13, funct3=1, imm=0x604)
sext_h = RVOp("sext_h", IType, ("rd", "rs1"), opcode=0x13, funct3=1, imm=0x605)

lw, lbu, lhu = [
  RVOp(name, IType, ("rd", "rs1", "imm"), opcode=0x03, funct3=funct3)
  for name, funct3 in _LOAD_SPECS
]
sb, sh, sw = [
  RVOp(name, SType, ("rs2", "rs1", "imm"), opcode=0x23, funct3=funct3)
  for name, funct3 in _STORE_SPECS
]
beq, bne, blt, bge, bltu, bgeu = [
  RVOp(name, BType, ("rs1", "rs2", "imm"), opcode=0x63, funct3=funct3)
  for name, funct3 in _BRANCH_SPECS
]

lui = RVOp("lui", UType, ("rd", "imm"), opcode=0x37, encode=_u_imm, display={"imm": _u_imm_arg})
auipc = RVOp("auipc", UType, ("rd", "imm"), opcode=0x17, encode=_u_imm, display={"imm": _u_imm_arg})
jal = RVOp("jal", JType, ("rd", "imm"), opcode=0x6F)
jalr = RVOp("jalr", IType, ("rd", "rs1", ("imm", 0)), opcode=0x67, funct3=0)
csrrs = RVOp("csrrs", IType, ("rd", "rs1", "csr"), opcode=0x73, funct3=2, encode=_csr_imm, display={"csr": _csr_arg})
csrrc = RVOp("csrrc", IType, ("rd", "rs1", "csr"), opcode=0x73, funct3=3, encode=_csr_imm, display={"csr": _csr_arg})
fence = RVOp("fence", IType, (), opcode=0x0F, funct3=0, rd=zero, rs1=zero, imm=0x0FF)

_RV_OPS = (
  add, sub, sll, slt, sltu, xor, srl, sra, or_, and_, mul, mulhu, divu, remu,
  sh1add, sh2add, sh3add, min, minu, maxu, zext_h, addi, sltiu, xori, ori,
  andi, slli, srli, srai, ctz, sext_b, sext_h, lw, lbu, lhu, sb, sh, sw, beq,
  bne, blt, bge, bltu, bgeu, lui, auipc, jal, jalr, csrrs, csrrc, fence,
)
_RV_OPS_BY_NAME = {op.name: op for op in _RV_OPS}

for _op in _RV_OPS:
  globals()[_op.name.upper()] = _op
OR = or_
AND = and_
SB = lambda rs1, rs2, imm: sb(rs2, rs1, imm)
SH = lambda rs1, rs2, imm: sh(rs2, rs1, imm)
SW = lambda rs1, rs2, imm: sw(rs2, rs1, imm)

def LI32(rd, imm):
  imm &= 0xFFFFFFFF
  hi = (imm + 0x800) & 0xFFFFF000
  lo = _sext(imm & 0xFFF, 12)
  return [lui(rd, hi), addi(rd, rd, lo)]

def J(imm): return jal(zero, imm)
def RET(): return jalr(zero, ra, 0)
def pack(insns): return b"".join(insn.to_bytes() for insn in insns)

_DECODE = {
  **{(0x33, funct3, funct7): (name, RType) for name, funct3, funct7 in _R_SPECS},
  (0x33, 4, 0x04): ("zext_h", RType),
  **{(0x13, funct3, None): (name, IType) for name, funct3 in _I_SPECS},
  (0x13, 1, 0x00): ("slli", IType), (0x13, 5, 0x00): ("srli", IType),
  (0x13, 5, 0x20): ("srai", IType),
  **{(0x03, funct3, None): (name, IType) for name, funct3 in _LOAD_SPECS},
  **{(0x23, funct3, None): (name, SType) for name, funct3 in _STORE_SPECS},
  **{(0x63, funct3, None): (name, BType) for name, funct3 in _BRANCH_SPECS},
  (0x37, None, None): ("lui", UType), (0x17, None, None): ("auipc", UType),
  (0x6F, None, None): ("jal", JType), (0x67, 0, None): ("jalr", IType),
  (0x73, 2, None): ("csrrs", IType), (0x73, 3, None): ("csrrc", IType),
  (0x0F, 0, None): ("fence", IType),
}

# --- Tensix ---------------------------------------------------------------

class TTInst(_Insn):
  """A Tensix instruction: 8-bit opcode in bits 31:24, fields in bits 23:0.

  ``raw_word()`` is the value the hardware decodes (what ttas emits).
  ``to_word()`` additionally rotate-lefts by 2 so the word never looks like a
  RISC-V instruction (low bits != 0b11) when embedded inline in a RISC-V
  stream; ``decode()`` undoes that with ror2."""
  @classmethod
  def from_raw_word(cls, word, *, name=None): return cls.from_word(word, name=name)

  @property
  def opcode(self): return (self._raw >> 24) & 0xFF
  @property
  def payload(self): return self._raw & 0xFFFFFF
  def raw_word(self): return self._raw & 0xFFFFFFFF
  def to_word(self):
    raw = self.raw_word()
    if raw >= 0xC0000000:
      raise ValueError(f"Tensix inline word would look like RISC-V: 0x{raw:08x}")
    return rol2(raw)
  def __eq__(self, other): return isinstance(other, TTInst) and self.raw_word() == other.raw_word()
  def __hash__(self): return hash(self.raw_word())
  def __repr__(self):
    parts = []
    for name in self._arg_names():
      f = getattr(type(self), name)
      parts.append((_fmt_arg(getattr(self, name)), getattr(self, name) == f.default))
    while parts and parts[-1][1]:
      parts.pop()
    return f"{type(self).__name__}({', '.join(p for p, _ in parts)})"

def TTINSN(imm32):
  if imm32 >= 0xC0000000:
    raise ValueError(f".ttinsn requires imm32 < 0xC0000000, got 0x{imm32:08x}")
  return TTInst.from_raw_word(imm32)

class TTMOP(TTInst, op=0x01): mop_type, loop_count, zmask_lo16_or_loop_count = b[23], b[22:16], b[15:0]
class TTNOP(TTInst, op=0x02): pass
class TTMOP_CFG(TTInst, op=0x03): zmask_hi16 = b[23:0]
class TTREPLAY(TTInst, op=0x04): start_idx, len, execute_while_loading, load_mode = b[23:14], b[13:4], b[3:1], b[0]
class TTRESOURCEDECL(TTInst, op=0x05): linger_time, resources, op_class = b[23:13], b[12:4], b[3:0]
class TTMOVD2A(TTInst, op=0x08): dest_32b_lo, src, addr_mode, instr_mod, dst = b[23], b[22:17], b[16:14], b[13:12], b[11:0]
class TTMOVDBGA2D(TTInst, op=0x09): dest_32b_lo, src, addr_mode, instr_mod, dst = b[23], b[22:17], b[16:14], b[13:12], b[11:0]
class TTMOVD2B(TTInst, op=0x0A): dest_32b_lo, src, addr_mode, instr_mod, dst = b[23], b[22:17], b[16:14], b[13:12], b[11:0]
class TTMOVB2A(TTInst, op=0x0B): srca, addr_mode, instr_mod, srcb = b[23:17], b[16:14], b[13:12], b[11:0]
class TTMOVDBGB2D(TTInst, op=0x0C): dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst = b[23], b[22:17], b[16:14], b[13:11], b[10:0]
class TTZEROACC(TTInst, op=0x10): clear_mode, use_32_bit_mode, clear_zero_flags, addr_mode, where = b[23:19], b[18], b[17], b[16:14], b[13:0]
class TTZEROSRC(TTInst, op=0x11): zero_val, write_mode, bank_mask, src_mask = b[23:4], b[3], b[2], b[1:0]
class TTMOVA2D(TTInst, op=0x12): dest_32b_lo, src, addr_mode, instr_mod, dst = b[23], b[22:17], b[16:14], b[13:12], b[11:0]
class TTMOVB2D(TTInst, op=0x13): dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst = b[23], b[22:17], b[16:14], b[13:11], b[10:0]
class TTTRNSPSRCA(TTInst, op=0x14): pass
class TTRAREB(TTInst, op=0x15): pass
class TTTRNSPSRCB(TTInst, op=0x16): pass
class TTSHIFTXA(TTInst, op=0x17): log2_amount2, shift_mode = b[23:2], b[1:0]
class TTSHIFTXB(TTInst, op=0x18): addr_mode, rot_shift, shift_row = b[23:14], b[13:10], b[9:0]
class TTSETASHRMH0(TTInst, op=0x1A): reg_mask, halo_mask = b[23:1], b[0]
class TTSETASHRMH1(TTInst, op=0x1B): reg_mask, halo_mask = b[23:1], b[0]
class TTSETASHRMV(TTInst, op=0x1C): reg_mask2 = b[23:0]
class TTSETPKEDGOF(TTInst, op=0x1D): y_end, y_start, x_end, x_start = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSETASHRMH(TTInst, op=0x1E): reg_mask, halo_mask = b[23:1], b[0]
class TTCLREXPHIST(TTInst, op=0x21): pass
class TTCONV3S1(TTInst, op=0x22): clear_dvalid, rotate_weights, addr_mode, dst = b[23:22], b[21:17], b[16:14], b[13:0]
class TTCONV3S2(TTInst, op=0x23): clear_dvalid, rotate_weights, addr_mode, dst = b[23:22], b[21:17], b[16:14], b[13:0]
class TTMPOOL3S1(TTInst, op=0x24): clear_dvalid, pool_addr_mode, index_en, dst = b[23:22], b[21:15], b[14], b[13:0]
class TTAPOOL3S1(TTInst, op=0x25): clear_dvalid, pool_addr_mode, index_en, dst = b[23:22], b[21:15], b[14], b[13:0]
class TTMVMUL(TTInst, op=0x26): clear_dvalid, instr_mod19, addr_mode, dst = b[23:22], b[21:19], b[18:14], b[13:0]
class TTELWMUL(TTInst, op=0x27): clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst = b[23:22], b[21], b[20:19], b[18:14], b[13:0]
class TTELWADD(TTInst, op=0x28): clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst = b[23:22], b[21], b[20:19], b[18:14], b[13:0]
class TTDOTPV(TTInst, op=0x29): clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst = b[23:22], b[21], b[20:19], b[18:14], b[13:0]
class TTELWSUB(TTInst, op=0x30): clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst = b[23:22], b[21], b[20:19], b[18:14], b[13:0]
class TTMPOOL3S2(TTInst, op=0x31): clear_dvalid, pool_addr_mode, index_en, dst = b[23:22], b[21:15], b[14], b[13:0]
class TTAPOOL3S2(TTInst, op=0x32): clear_dvalid, pool_addr_mode, index_en, dst = b[23:22], b[21:15], b[14], b[13:0]
class TTGMPOOL(TTInst, op=0x33): clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst = b[23:22], b[21:19], b[18:15], b[14], b[13:0]
class TTGAPOOL(TTInst, op=0x34): clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst = b[23:22], b[21:19], b[18:15], b[14], b[13:0]
class TTGATESRCRST(TTInst, op=0x35): reset_srcb_gate_control, reset_srca_gate_control = b[23:1], b[0]
class TTCLEARDVALID(TTInst, op=0x36): cleardvalid, reset = b[23:22], b[21:0]
class TTSETRWC(TTInst, op=0x37): clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask = b[23:22], b[21:18], b[17:14], b[13:10], b[9:6], b[5:0]
class TTINCRWC(TTInst, op=0x38): rwc_cr, rwc_d, rwc_b, rwc_a = b[23:18], b[17:14], b[13:10], b[9:6]
class TTSETIBRWC(TTInst, op=0x39): rwc_cr, rwc_bias, set_inc_ctrl = b[23:18], b[17:6], b[5:0]
class TTMFCONV3S1(TTInst, op=0x3A): clear_dvalid, rotate_weights, addr_mode, dst = b[23:22], b[21:17], b[16:14], b[13:0]
class TTXMOV(TTInst, op=0x40): Mov_block_selection, Last = b[23], b[22:0]
class TTPACR(TTInst, op=0x41): CfgContext, RowPadZero, DstAccessMode, AddrMode, AddrCntContext, ZeroWrite, ReadIntfSel, OvrdThreadId, Concat, CtxtCtrl, Flush, Last = b[23:21], b[20:18], b[17], b[16:15], b[14:13], b[12], b[11:8], b[7], b[6:4], b[3:2], b[1], b[0]
class TTUNPACR(TTInst, op=0x42): Unpack_block_selection, AddrMode, CfgContextCntInc, CfgContextId, AddrCntContextId, OvrdThreadId, SetDatValid, srcb_bcast, ZeroWrite2, AutoIncContextID, RowSearch, SearchCacheFlush, Last = b[23], b[22:15], b[14:13], b[12:10], b[9:8], b[7], b[6], b[5], b[4], b[3], b[2], b[1], b[0]
class TTUNPACR_NOP(TTInst, op=0x43): Unpacker_Select, Stream_Id, Msg_Clr_Cnt, Set_Dvalid, Clr_to1_fmt_Ctrl, Stall_Clr_Cntrl, Bank_Clr_Ctrl, Src_ClrVal_Ctrl, Unpack_Pop = b[23], b[22:16], b[15:12], b[11:8], b[7:6], b[5], b[4], b[3:2], b[1:0]
class TTRSTDMA(TTInst, op=0x44): pass
class TTSETDMAREG(TTInst, op=0x45): Payload_SigSelSize, Payload_SigSel, SetSignalsMode, RegIndex16b = b[23:22], b[21:8], b[7], b[6:0]
class TTFLUSHDMA(TTInst, op=0x46): FlushSpec = b[23:0]
class TTREG2FLOP(TTInst, op=0x48): SizeSel, TargetSel, ByteOffset, ContextId_2, FlopIndex, RegIndex = b[23:22], b[21:20], b[19:18], b[17:16], b[15:6], b[5:0]
class TTLOADIND(TTInst, op=0x49): SizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex = b[23:22], b[21:14], b[13:12], b[11:6], b[5:0]
class TTPACR_SETREG(TTInst, op=0x4A): Push, ModeSel, Unused, DisableStall, AddrSel, StreamId, Flush, Last = b[23], b[22], b[21:12], b[11:10], b[9:8], b[7:2], b[1], b[0]
class TTTBUFCMD(TTInst, op=0x4B): pass
class TTSETADC(TTInst, op=0x50): CntSetMask, ChannelIndex, DimensionIndex, Value = b[23:21], b[20], b[19:18], b[17:0]
class TTSETADCXY(TTInst, op=0x51): CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask = b[23:21], b[20:15], b[14:12], b[11:9], b[8:6], b[5:0]
class TTINCADCXY(TTInst, op=0x52): CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X = b[23:21], b[20:15], b[14:12], b[11:9], b[8:6]
class TTADDRCRXY(TTInst, op=0x53): CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask = b[23:21], b[20:15], b[14:12], b[11:9], b[8:6], b[5:0]
class TTSETADCZW(TTInst, op=0x54): CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask = b[23:21], b[20:15], b[14:12], b[11:9], b[8:6], b[5:0]
class TTINCADCZW(TTInst, op=0x55): CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z = b[23:21], b[20:15], b[14:12], b[11:9], b[8:6]
class TTADDRCRZW(TTInst, op=0x56): CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask = b[23:21], b[20:15], b[14:12], b[11:9], b[8:6], b[5:0]
class TTSETDVALID(TTInst, op=0x57): setvalid = b[23:0]
class TTADDDMAREG(TTInst, op=0x58): OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex = b[23], b[22:12], b[11:6], b[5:0]
class TTSUBDMAREG(TTInst, op=0x59): OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex = b[23], b[22:12], b[11:6], b[5:0]
class TTMULDMAREG(TTInst, op=0x5A): OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex = b[23], b[22:12], b[11:6], b[5:0]
class TTBITWOPDMAREG(TTInst, op=0x5B): OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex = b[23], b[22:18], b[17:12], b[11:6], b[5:0]
class TTSHIFTDMAREG(TTInst, op=0x5C): OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex = b[23], b[22:18], b[17:12], b[11:6], b[5:0]
class TTCMPDMAREG(TTInst, op=0x5D): OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex = b[23], b[22:18], b[17:12], b[11:6], b[5:0]
class TTSETADCXX(TTInst, op=0x5E): CntSetMask, x_end2, x_start = b[23:21], b[20:10], b[9:0]
class TTDMANOP(TTInst, op=0x60): pass
class TTATINCGET(TTInst, op=0x61): MemHierSel, WrapVal, Sel32b, DataRegIndex, AddrRegIndex = b[23], b[22:14], b[13:12], b[11:6], b[5:0]
class TTATINCGETPTR(TTInst, op=0x62): MemHierSel, NoIncr, IncrVal, WrapVal, Sel32b, DataRegIndex, AddrRegIndex = b[23], b[22], b[21:18], b[17:14], b[13:12], b[11:6], b[5:0]
class TTATSWAP(TTInst, op=0x63): MemHierSel, SwapMask, DataRegIndex, AddrRegIndex = b[23], b[22:14], b[13:6], b[5:0]
class TTATCAS(TTInst, op=0x64): MemHierSel, SwapVal, CmpVal, Sel32b, DataRegIndex, AddrRegIndex = b[23], b[22:18], b[17:14], b[13:12], b[11:6], b[5:0]
class TTSTOREIND(TTInst, op=0x66): MemHierSel, SizeSel, RegSizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex = b[23], b[22], b[21], b[20:14], b[13:12], b[11:6], b[5:0]
class TTSTOREREG(TTInst, op=0x67): TdmaDataRegIndex, RegAddr = b[23:18], b[17:0]
class TTLOADREG(TTInst, op=0x68): TdmaDataRegIndex, RegAddr = b[23:18], b[17:0]
class TTSFPLOAD(TTInst, op=0x70): lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr = b[23:20], b[19:16], b[15:13], b[12:0]
class TTSFPLOADI(TTInst, op=0x71): lreg_ind, instr_mod0, imm16 = b[23:20], b[19:16], b[15:0]
class TTSFPSTORE(TTInst, op=0x72): lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr = b[23:20], b[19:16], b[15:13], b[12:0]
class TTSFPLUT(TTInst, op=0x73): lreg_ind, instr_mod0, dest_reg_addr = b[23:20], b[19:16], b[15:0]
class TTSFPMULI(TTInst, op=0x74): imm16_math, lreg_dest, instr_mod1 = b[23:8], b[7:4], b[3:0]
class TTSFPADDI(TTInst, op=0x75): imm16_math, lreg_dest, instr_mod1 = b[23:8], b[7:4], b[3:0]
class TTSFPDIVP2(TTInst, op=0x76): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPEXEXP(TTInst, op=0x77): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPEXMAN(TTInst, op=0x78): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPIADD(TTInst, op=0x79): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPSHFT(TTInst, op=0x7A): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPSETCC(TTInst, op=0x7B): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPMOV(TTInst, op=0x7C): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPABS(TTInst, op=0x7D): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPAND(TTInst, op=0x7E): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPOR(TTInst, op=0x7F): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPNOT(TTInst, op=0x80): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPLZ(TTInst, op=0x81): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPSETEXP(TTInst, op=0x82): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPSETMAN(TTInst, op=0x83): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPMAD(TTInst, op=0x84): lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1 = b[23:16], b[15:12], b[11:8], b[7:4], b[3:0]
class TTSFPADD(TTInst, op=0x85): lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1 = b[23:16], b[15:12], b[11:8], b[7:4], b[3:0]
class TTSFPMUL(TTInst, op=0x86): lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1 = b[23:16], b[15:12], b[11:8], b[7:4], b[3:0]
class TTSFPPUSHC(TTInst, op=0x87): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPPOPC(TTInst, op=0x88): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPSETSGN(TTInst, op=0x89): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPENCC(TTInst, op=0x8A): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPCOMPC(TTInst, op=0x8B): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPTRANSP(TTInst, op=0x8C): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPXOR(TTInst, op=0x8D): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPSTOCHRND(TTInst, op=0x8E): rnd_mode, imm8_math, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1 = b[23:21], b[20:16], b[15:12], b[11:8], b[7:4], b[3:0]
class TTSFPNOP(TTInst, op=0x8F): pass
class TTSFPCAST(TTInst, op=0x90): lreg_src_c, lreg_dest, instr_mod1 = b[23:8], b[7:4], b[3:0]
class TTSFPCONFIG(TTInst, op=0x91): imm16_math, config_dest, instr_mod1 = b[23:8], b[7:4], b[3:0]
class TTSFPSWAP(TTInst, op=0x92): imm12_math, lreg_src_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPLOADMACRO(TTInst, op=0x93): lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr = b[23:20], b[19:16], b[15:13], b[12:0]
class TTSFPSHFT2(TTInst, op=0x94): imm12_math, lreg_src_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPLUTFP32(TTInst, op=0x95): lreg_dest, instr_mod1 = b[23:4], b[3:0]
class TTSFPLE(TTInst, op=0x96): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPGT(TTInst, op=0x97): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTSFPMUL24(TTInst, op=0x98): lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1 = b[23:16], b[15:12], b[11:8], b[7:4], b[3:0]
class TTSFPARECIP(TTInst, op=0x99): imm12_math, lreg_c, lreg_dest, instr_mod1 = b[23:12], b[11:8], b[7:4], b[3:0]
class TTATGETM(TTInst, op=0xA0): mutex_index = b[23:0]
class TTATRELM(TTInst, op=0xA1): mutex_index = b[23:0]
class TTSTALLWAIT(TTInst, op=0xA2): stall_res, wait_res = b[23:15], b[14:0]
class TTSEMINIT(TTInst, op=0xA3): max_value, init_value, sem_sel = b[23:20], b[19:16], b[15:2]
class TTSEMPOST(TTInst, op=0xA4): sem_sel = b[23:2]
class TTSEMGET(TTInst, op=0xA5): sem_sel = b[23:2]
class TTSEMWAIT(TTInst, op=0xA6): stall_res, sem_sel, wait_sem_cond = b[23:15], b[14:2], b[1:0]
class TTSTREAMWAIT(TTInst, op=0xA7): stall_res, target_value, target_sel, wait_stream_sel = b[23:15], b[14:4], b[3], b[2:0]
class TTWRCFG(TTInst, op=0xB0): GprAddress, wr128b, CfgReg = b[23:16], b[15], b[14:0]
class TTRDCFG(TTInst, op=0xB1): GprAddress, CfgReg = b[23:16], b[15:0]
class TTSETC16(TTInst, op=0xB2): setc16_reg, setc16_value = b[23:16], b[15:0]
class TTRMWCIB0(TTInst, op=0xB3): Mask, Data, CfgRegAddr = b[23:16], b[15:8], b[7:0]
class TTRMWCIB1(TTInst, op=0xB4): Mask, Data, CfgRegAddr = b[23:16], b[15:8], b[7:0]
class TTRMWCIB2(TTInst, op=0xB5): Mask, Data, CfgRegAddr = b[23:16], b[15:8], b[7:0]
class TTRMWCIB3(TTInst, op=0xB6): Mask, Data, CfgRegAddr = b[23:16], b[15:8], b[7:0]
class TTSTREAMWRCFG(TTInst, op=0xB7): stream_id_sel, StreamRegAddr, CfgReg = b[23:21], b[20:11], b[10:0]
class TTCFGSHIFTMASK(TTInst, op=0xB8): disable_mask_on_old_val, operation, mask_width, right_cshift_amt, scratch_sel, CfgReg = b[23], b[22:20], b[19:15], b[14:10], b[9:8], b[7:0]
class TTWRCFG32(TTInst, op=0xC0): GprAddress, CfgReg = b[23:18], b[10:0]  # not in Blackhole assembly.yaml; kept from prior dsl

_TENSIX_BY_OPCODE = {cls.opcode_.value: (cls.name, cls) for cls in TTInst.__subclasses__()}

def decode_tensix(word):
  w = word & 0xFFFFFFFF
  op = (w >> 24) & 0xFF
  name_cls = _TENSIX_BY_OPCODE.get(op)
  if name_cls is None:
    return TTInst.from_raw_word(w, name=f"UNKNOWN_0x{op:02X}")
  name, cls = name_cls
  return cls.from_raw_word(w, name=name)

def decode(word):
  word &= 0xFFFFFFFF
  if (word & 3) != 3:
    return decode_tensix(ror2(word))
  opcode, funct3, funct7 = word & 0x7F, (word >> 12) & 7, (word >> 25) & 0x7F
  if opcode == 0x13 and funct3 == 1 and (word >> 20) in {0x601, 0x604, 0x605}:
    return IType.from_word(word, name={0x601: "ctz", 0x604: "sext_b", 0x605: "sext_h"}[word >> 20])
  name_cls = (_DECODE.get((opcode, funct3, funct7)) or
              _DECODE.get((opcode, funct3, None)) or
              _DECODE.get((opcode, None, None)))
  if name_cls is None: raise ValueError(f"unknown RISC-V word 0x{word:08x}")
  name, cls = name_cls
  return cls.from_word(word, name=name)

def decode_rv(word):
  word &= 0xFFFFFFFF
  if (word & 3) != 3:
    raise ValueError(f"not a RISC-V word 0x{word:08x}")
  return decode(word)

def disasm(binary: bytes, base: int = 0) -> list[str]:
  """Decode a mixed RISC-V/Tensix instruction stream."""
  if len(binary) % 4:
    raise ValueError("disasm() input length must be a multiple of 4")
  return [
    f"{base + off:08x}: {decode(int.from_bytes(binary[off:off + 4], 'little'))}"
    for off in range(0, len(binary), 4)
  ]
