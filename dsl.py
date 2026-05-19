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
    val = (obj._raw >> self.lo) & self.mask
    return self.decode(val)
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
bits = _Bits()

class Inst:
  _fields = ()
  name = None

  def __init_subclass__(cls):
    fields = []
    for base in reversed(cls.__mro__):
      for _, val in base.__dict__.items():
        if isinstance(val, BitField) and not any(val is field for field in fields):
          fields.append(val)
    cls._fields = tuple(sorted(fields, key=lambda f: -f.hi))

  def __init__(self, **kw):
    self._raw = 0
    self.name = kw.pop("name", self.name)
    for field in self._fields:
      setattr(self, field.name, field.value if isinstance(field, FixedBitField) else kw.pop(field.name, field.default))
    if kw: raise TypeError(f"unexpected fields: {', '.join(kw)}")

  @classmethod
  def from_word(cls, word, *, name=None):
    obj = object.__new__(cls)
    obj._raw = word & 0xFFFFFFFF
    obj.name = name or cls.name
    return obj

  def to_word(self): return self._raw & 0xFFFFFFFF
  def to_bytes(self): return self.to_word().to_bytes(4, "little")
  def __int__(self): return self.to_word()
  def __eq__(self, other): return isinstance(other, Inst) and self.to_word() == other.to_word()
  def __hash__(self): return hash(self.to_word())
  def __repr__(self):
    rv_ops = globals().get("_RV_OPS_BY_NAME", {})
    if self.name in rv_ops:
      return f"{self.name}({rv_ops[self.name].repr_args(self)})"
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

  def __repr__(self):
    return f"<RVOp {self.name}>"

  def repr_args(self, inst):
    parts = []
    for spec in self.args:
      name = spec[0] if isinstance(spec, tuple) else spec
      val = self.display[name](inst) if name in self.display else getattr(inst, name)
      parts.append((_fmt_arg(val), isinstance(spec, tuple) and val == spec[1]))
    while parts and parts[-1][1]:
      parts.pop()
    return ", ".join(part for part, _ in parts)

def _u_imm(fields):
  return {**fields, "imm": fields["imm"] >> 12}

def _csr_imm(fields):
  fields = dict(fields)
  fields["imm"] = fields.pop("csr")
  return fields

def _shamt_imm(fields):
  fields = dict(fields)
  fields["imm"] = fields.pop("shamt")
  return fields

def _srai_imm(fields):
  fields = dict(fields)
  fields["imm"] = 0x400 | fields.pop("shamt")
  return fields

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
_I_SPECS = (
  ("addi", 0), ("sltiu", 3), ("xori", 4), ("ori", 6), ("andi", 7),
)
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

def J(imm):
  return jal(zero, imm)

def RET():
  return jalr(zero, ra, 0)

def pack(insns):
  return b"".join(insn.to_bytes() for insn in insns)

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

class TTInst:
  _fields = ()
  name = None

  def __init_subclass__(cls):
    fields = []
    for base in reversed(cls.__mro__):
      for _, val in base.__dict__.items():
        if isinstance(val, BitField) and not any(val is field for field in fields):
          fields.append(val)
    cls._fields = tuple(sorted(fields, key=lambda f: -f.hi))

  @classmethod
  def _arg_names(cls):
    names = []
    for field in cls._fields:
      if not isinstance(field, FixedBitField) and field.name not in names:
        names.append(field.name)
    return names

  def __init__(self, *args, **kw):
    names = type(self)._arg_names()
    if len(args) > len(names):
      raise TypeError(f"{type(self).__name__} expected at most {len(names)} positional args, got {len(args)}")
    vals = dict(zip(names, args))
    for k, v in kw.items():
      if k in vals:
        raise TypeError(f"{type(self).__name__} got duplicate value for {k!r}")
      vals[k] = v

    self._raw = 0
    self.name = vals.pop("name", self.name)
    extra = set(vals) - set(names)
    if extra: raise TypeError(f"unexpected fields: {', '.join(sorted(extra))}")
    for field in self._fields:
      if isinstance(field, FixedBitField):
        setattr(self, field.name, field.value)
      elif field.name in vals:
        setattr(self, field.name, vals[field.name])

  @classmethod
  def from_raw_word(cls, word, *, name=None):
    obj = object.__new__(cls)
    obj._raw = word & 0xFFFFFFFF
    obj.name = name or cls.name
    return obj

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
  def to_bytes(self): return self.to_word().to_bytes(4, "little")
  def __int__(self): return self.to_word()
  def __eq__(self, other): return isinstance(other, TTInst) and self.raw_word() == other.raw_word()
  def __hash__(self): return hash(self.raw_word())
  def __repr__(self):
    fields = {field.name: field for field in self._fields if not isinstance(field, FixedBitField)}
    parts = []
    for name in type(self)._arg_names():
      val = getattr(self, name)
      default = fields[name].default
      parts.append((_fmt_arg(val), val == default))
    while parts and parts[-1][1]:
      parts.pop()
    return f"{type(self).__name__}({', '.join(part for part, _ in parts)})"

def TTINSN(imm32):
  if imm32 >= 0xC0000000:
    raise ValueError(f".ttinsn requires imm32 < 0xC0000000, got 0x{imm32:08x}")
  return TTInst.from_raw_word(imm32)

class TTMOP(TTInst):
  name = 'MOP'
  opcode_ = FixedBitField(31, 24, 0x01)
  mop_type = BitField(23, 23)
  loop_count = BitField(22, 16)
  zmask_lo16_or_loop_count = BitField(15, 0)

class TTNOP(TTInst):
  name = 'NOP'
  opcode_ = FixedBitField(31, 24, 0x02)

class TTMOP_CFG(TTInst):
  name = 'MOP_CFG'
  opcode_ = FixedBitField(31, 24, 0x03)
  zmask_hi16 = BitField(15, 0)

class TTREPLAY(TTInst):
  name = 'REPLAY'
  opcode_ = FixedBitField(31, 24, 0x04)
  start_idx = BitField(23, 14)
  len = BitField(13, 4)
  execute_while_loading = BitField(1, 1)
  load_mode = BitField(0, 0)

class TTMOVD2A(TTInst):
  name = 'MOVD2A'
  opcode_ = FixedBitField(31, 24, 0x08)
  dest_32b_lo = BitField(23, 23)
  src = BitField(22, 17)
  addr_mode = BitField(16, 14)
  instr_mod = BitField(13, 12)
  dst = BitField(11, 0)

class TTMOVD2B(TTInst):
  name = 'MOVD2B'
  opcode_ = FixedBitField(31, 24, 0x0A)
  dest_32b_lo = BitField(23, 23)
  src = BitField(22, 17)
  addr_mode = BitField(16, 14)
  instr_mod = BitField(13, 12)
  dst = BitField(11, 0)

class TTZEROACC(TTInst):
  name = 'ZEROACC'
  opcode_ = FixedBitField(31, 24, 0x10)
  clear_mode = BitField(23, 19)
  use_32_bit_mode = BitField(18, 18)
  clear_zero_flags = BitField(17, 17)
  addr_mode = BitField(16, 14)
  where = BitField(13, 0)

class TTZEROSRC(TTInst):
  name = 'ZEROSRC'
  opcode_ = FixedBitField(31, 24, 0x11)
  zero_val = BitField(23, 4)
  write_mode = BitField(3, 3)
  bank_mask = BitField(2, 2)
  src_mask = BitField(1, 0)

class TTMOVA2D(TTInst):
  name = 'MOVA2D'
  opcode_ = FixedBitField(31, 24, 0x12)
  dest_32b_lo = BitField(23, 23)
  src = BitField(22, 17)
  addr_mode = BitField(16, 14)
  instr_mod = BitField(13, 12)
  dst = BitField(11, 0)

class TTMOVB2D(TTInst):
  name = 'MOVB2D'
  opcode_ = FixedBitField(31, 24, 0x13)
  dest_32b_lo = BitField(23, 23)
  src = BitField(22, 17)
  addr_mode = BitField(16, 14)
  movb2d_instr_mod = BitField(13, 11)
  dst = BitField(10, 0)

class TTTRNSPSRCA(TTInst):
  name = 'TRNSPSRCA'
  opcode_ = FixedBitField(31, 24, 0x14)

class TTRAREB(TTInst):
  name = 'RAREB'
  opcode_ = FixedBitField(31, 24, 0x15)

class TTTRNSPSRCB(TTInst):
  name = 'TRNSPSRCB'
  opcode_ = FixedBitField(31, 24, 0x16)

class TTSHIFTXA(TTInst):
  name = 'SHIFTXA'
  opcode_ = FixedBitField(31, 24, 0x17)
  raw = BitField(23, 0)
  shift_mode = BitField(1, 0)
  log2_amount2 = BitField(23, 2)

class TTSHIFTXB(TTInst):
  name = 'SHIFTXB'
  opcode_ = FixedBitField(31, 24, 0x18)
  raw = BitField(23, 0)
  shift_row = BitField(9, 0)
  rot_shift = BitField(13, 10)
  addr_mode = BitField(16, 14)

class TTCLREXPHIST(TTInst):
  name = 'CLREXPHIST'
  opcode_ = FixedBitField(31, 24, 0x21)

class TTCONV3S1(TTInst):
  name = 'CONV3S1'
  opcode_ = FixedBitField(31, 24, 0x22)
  clear_dvalid = BitField(23, 22)
  rotate_weights = BitField(21, 17)
  addr_mode = BitField(16, 14)
  dst = BitField(13, 0)

class TTCONV3S2(TTInst):
  name = 'CONV3S2'
  opcode_ = FixedBitField(31, 24, 0x23)
  clear_dvalid = BitField(23, 22)
  rotate_weights = BitField(21, 17)
  addr_mode = BitField(16, 14)
  dst = BitField(13, 0)

class TTMFCONV3S1(TTInst):
  name = 'MFCONV3S1'
  opcode_ = FixedBitField(31, 24, 0x24)
  clear_dvalid = BitField(23, 22)
  rotate_weights = BitField(21, 17)
  addr_mode = BitField(16, 14)
  dst = BitField(13, 0)

class TTAPOOL3S1(TTInst):
  name = 'APOOL3S1'
  opcode_ = FixedBitField(31, 24, 0x25)
  clear_dvalid = BitField(23, 22)
  pool_addr_mode = BitField(21, 15)
  index_en = BitField(14, 14)
  dst = BitField(13, 0)

class TTMVMUL(TTInst):
  name = 'MVMUL'
  opcode_ = FixedBitField(31, 24, 0x26)
  clear_dvalid = BitField(23, 22)
  instr_mod19 = BitField(21, 19)
  addr_mode = BitField(16, 14)
  dst = BitField(9, 0)
  broadcast_srcb = BitField(19, 19)

class TTELWMUL(TTInst):
  name = 'ELWMUL'
  opcode_ = FixedBitField(31, 24, 0x27)
  clear_dvalid = BitField(23, 22)
  dest_accum_en = BitField(21, 21)
  instr_mod19 = BitField(20, 19)
  addr_mode = BitField(15, 14)
  dst = BitField(13, 0)

class TTELWADD(TTInst):
  name = 'ELWADD'
  opcode_ = FixedBitField(31, 24, 0x28)
  clear_dvalid = BitField(23, 22)
  dest_accum_en = BitField(21, 21)
  instr_mod19 = BitField(20, 19)
  addr_mode = BitField(15, 14)
  dst = BitField(13, 0)

class TTDOTPV(TTInst):
  name = 'DOTPV'
  opcode_ = FixedBitField(31, 24, 0x29)
  clear_dvalid = BitField(23, 22)
  dest_accum_en = BitField(21, 21)
  instr_mod19 = BitField(20, 19)
  addr_mode = BitField(15, 14)
  dst = BitField(13, 0)

class TTMPOOL3S2(TTInst):
  name = 'MPOOL3S2'
  opcode_ = FixedBitField(31, 24, 0x2A)
  clear_dvalid = BitField(23, 22)
  pool_addr_mode = BitField(21, 15)
  index_en = BitField(14, 14)
  dst = BitField(13, 0)

class TTELWSUB(TTInst):
  name = 'ELWSUB'
  opcode_ = FixedBitField(31, 24, 0x30)
  clear_dvalid = BitField(23, 22)
  dest_accum_en = BitField(21, 21)
  instr_mod19 = BitField(20, 19)
  addr_mode = BitField(15, 14)
  dst = BitField(13, 0)

class TTMPOOL3S1(TTInst):
  name = 'MPOOL3S1'
  opcode_ = FixedBitField(31, 24, 0x31)
  clear_dvalid = BitField(23, 22)
  pool_addr_mode = BitField(21, 15)
  index_en = BitField(14, 14)
  dst = BitField(13, 0)

class TTAPOOL3S2(TTInst):
  name = 'APOOL3S2'
  opcode_ = FixedBitField(31, 24, 0x32)
  clear_dvalid = BitField(23, 22)
  pool_addr_mode = BitField(21, 15)
  index_en = BitField(14, 14)
  dst = BitField(13, 0)

class TTGMPOOL(TTInst):
  name = 'GMPOOL'
  opcode_ = FixedBitField(31, 24, 0x33)
  clear_dvalid = BitField(23, 22)
  instr_mod19 = BitField(21, 19)
  pool_addr_mode = BitField(18, 15)
  max_pool_index_en = BitField(14, 14)
  dst = BitField(13, 0)

class TTGAPOOL(TTInst):
  name = 'GAPOOL'
  opcode_ = FixedBitField(31, 24, 0x34)
  clear_dvalid = BitField(23, 22)
  instr_mod19 = BitField(21, 19)
  pool_addr_mode = BitField(18, 15)
  max_pool_index_en = BitField(14, 14)
  dst = BitField(13, 0)

class TTGATESRCRST(TTInst):
  name = 'GATESRCRST'
  opcode_ = FixedBitField(31, 24, 0x35)
  reset_srcb_gate_control = BitField(1, 1)
  reset_srca_gate_control = BitField(0, 0)

class TTCLEARDVALID(TTInst):
  name = 'CLEARDVALID'
  opcode_ = FixedBitField(31, 24, 0x36)
  cleardvalid = BitField(23, 22)
  clear_dvalid = BitField(23, 22)
  reset = BitField(21, 0)

class TTSETRWC(TTInst):
  name = 'SETRWC'
  opcode_ = FixedBitField(31, 24, 0x37)
  clear_ab_vld = BitField(23, 22)
  rwc_cr = BitField(21, 18)
  rwc_d = BitField(17, 14)
  rwc_b = BitField(13, 10)
  rwc_a = BitField(9, 6)
  BitMask = BitField(5, 0)

class TTINCRWC(TTInst):
  name = 'INCRWC'
  opcode_ = FixedBitField(31, 24, 0x38)
  rwc_cr = BitField(20, 18)
  rwc_d = BitField(17, 14)
  rwc_b = BitField(13, 10)
  rwc_a = BitField(9, 6)

class TTXMOV(TTInst):
  name = 'XMOV'
  opcode_ = FixedBitField(31, 24, 0x40)
  Mov_block_selection = BitField(23, 23)
  Last = BitField(0, 0)

class TTPACR(TTInst):
  name = 'PACR'
  opcode_ = FixedBitField(31, 24, 0x41)
  CfgContext = BitField(23, 21)
  RowPadZero = BitField(20, 18)
  DstAccessMode = BitField(17, 17)
  AddrMode = BitField(16, 15)
  AddrCntContext = BitField(14, 13)
  ZeroWrite = BitField(12, 12)
  ReadIntfSel = BitField(11, 8)
  OvrdThreadId = BitField(7, 7)
  Concat = BitField(6, 4)
  CtxtCtrl = BitField(3, 2)
  Flush = BitField(1, 1)
  Last = BitField(0, 0)

class TTUNPACR(TTInst):
  name = 'UNPACR'
  opcode_ = FixedBitField(31, 24, 0x42)
  Unpack_block_selection = BitField(23, 23)
  AddrMode = BitField(22, 15)
  CfgContextCntInc = BitField(14, 13)
  CfgContextId = BitField(12, 10)
  AddrCntContextId = BitField(9, 8)
  OvrdThreadId = BitField(7, 7)
  SetDatValid = BitField(6, 6)
  srcb_bcast = BitField(5, 5)
  ZeroWrite2 = BitField(4, 4)
  AutoIncContextID = BitField(3, 3)
  RowSearch = BitField(2, 2)
  SearchCacheFlush = BitField(1, 1)
  Last = BitField(0, 0)

class TTUNPACR_NOP(TTInst):
  name = 'UNPACR_NOP'
  opcode_ = FixedBitField(31, 24, 0x43)
  Unpacker_Select = BitField(23, 23)
  Stream_Id = BitField(22, 16)
  Msg_Clr_Cnt = BitField(15, 12)
  Set_Dvalid = BitField(11, 8)
  Clr_to1_fmt_Ctrl = BitField(7, 6)
  Stall_Clr_Cntrl = BitField(5, 5)
  Bank_Clr_Ctrl = BitField(4, 4)
  Src_ClrVal_Ctrl = BitField(3, 2)
  Unpack_Pop = BitField(1, 0)

class TTSETDMAREG(TTInst):
  name = 'SETDMAREG'
  opcode_ = FixedBitField(31, 24, 0x45)
  Payload_SigSelSize = BitField(23, 22)
  Payload_SigSel = BitField(21, 8)
  SetSignalsMode = BitField(7, 7)
  RegIndex16b = BitField(6, 0)

class TTFLUSHDMA(TTInst):
  name = 'FLUSHDMA'
  opcode_ = FixedBitField(31, 24, 0x46)
  ConditionMask = BitField(3, 0)

class TTREG2FLOP(TTInst):
  name = 'REG2FLOP'
  opcode_ = FixedBitField(31, 24, 0x48)
  SizeSel = BitField(23, 22)
  ThConCfgIndex = BitField(14, 8)
  InputReg = BitField(5, 0)

class TTTBUFCMD(TTInst):
  name = 'TBUFCMD'
  opcode_ = FixedBitField(31, 24, 0x4B)

class TTSETADC(TTInst):
  name = 'SETADC'
  opcode_ = FixedBitField(31, 24, 0x50)
  CntSetMask = BitField(23, 21)
  ChannelIndex = BitField(20, 20)
  DimensionIndex = BitField(19, 18)
  Value = BitField(17, 0)

class TTSETADCXY(TTInst):
  name = 'SETADCXY'
  opcode_ = FixedBitField(31, 24, 0x51)
  CntSetMask = BitField(23, 21)
  Ch1_Y = BitField(20, 15)
  Ch1_X = BitField(14, 12)
  Ch0_Y = BitField(11, 9)
  Ch0_X = BitField(8, 6)
  BitMask = BitField(5, 0)

class TTSETADCZW(TTInst):
  name = 'SETADCZW'
  opcode_ = FixedBitField(31, 24, 0x54)
  CntSetMask = BitField(23, 21)
  Ch1_W = BitField(20, 15)
  Ch1_Z = BitField(14, 12)
  Ch0_W = BitField(11, 9)
  Ch0_Z = BitField(8, 6)
  BitMask = BitField(5, 0)

class TTINCADCZW(TTInst):
  name = 'INCADCZW'
  opcode_ = FixedBitField(31, 24, 0x55)
  CntSetMask = BitField(23, 21)
  Ch1_W = BitField(20, 15)
  Ch1_Z = BitField(14, 12)
  Ch0_W = BitField(11, 9)
  Ch0_Z = BitField(8, 6)

class TTADDDMAREG(TTInst):
  name = 'ADDDMAREG'
  opcode_ = FixedBitField(31, 24, 0x58)
  OpBisConst = BitField(23, 23)
  ResultRegIndex = BitField(22, 12)
  OpBRegIndex = BitField(11, 6)
  OpARegIndex = BitField(5, 0)

class TTMULDMAREG(TTInst):
  name = 'MULDMAREG'
  opcode_ = FixedBitField(31, 24, 0x5A)
  OpBisConst = BitField(23, 23)
  ResultRegIndex = BitField(22, 12)
  OpBRegIndex = BitField(11, 6)
  OpARegIndex = BitField(5, 0)

class TTBITWOPDMAREG(TTInst):
  name = 'BITWOPDMAREG'
  opcode_ = FixedBitField(31, 24, 0x5B)
  OpBisConst = BitField(23, 23)
  OpSel = BitField(22, 18)
  ResultRegIndex = BitField(17, 12)
  OpBRegIndex = BitField(11, 6)
  OpARegIndex = BitField(5, 0)

class TTSHIFTDMAREG(TTInst):
  name = 'SHIFTDMAREG'
  opcode_ = FixedBitField(31, 24, 0x5C)
  OpBisConst = BitField(23, 23)
  Mode = BitField(22, 18)
  OpSel = BitField(22, 18)
  ResultRegIndex = BitField(17, 12)
  OpBRegIndex = BitField(11, 6)
  OpARegIndex = BitField(5, 0)

class TTCMPDMAREG(TTInst):
  name = 'CMPDMAREG'
  opcode_ = FixedBitField(31, 24, 0x5D)
  OpBisConst = BitField(23, 23)
  OpSel = BitField(22, 18)
  ResultRegIndex = BitField(17, 12)
  OpBRegIndex = BitField(11, 6)
  OpARegIndex = BitField(5, 0)

class TTSETADCXX(TTInst):
  name = 'SETADCXX'
  opcode_ = FixedBitField(31, 24, 0x5E)
  CntSetMask = BitField(23, 21)
  x_end2 = BitField(20, 10)
  x_start = BitField(9, 0)

class TTDMANOP(TTInst):
  name = 'DMANOP'
  opcode_ = FixedBitField(31, 24, 0x60)

class TTSTOREREG(TTInst):
  name = 'STOREREG'
  opcode_ = FixedBitField(31, 24, 0x67)
  TdmaDataRegIndex = BitField(23, 18)
  RegAddr = BitField(17, 0)

class TTSFPLOAD(TTInst):
  name = 'SFPLOAD'
  opcode_ = FixedBitField(31, 24, 0x70)
  lreg_ind = BitField(23, 20)
  instr_mod0 = BitField(19, 16)
  sfpu_addr_mode = BitField(15, 13)
  dest_reg_addr = BitField(12, 0)

class TTSFPLOADI(TTInst):
  name = 'SFPLOADI'
  opcode_ = FixedBitField(31, 24, 0x71)
  lreg_ind = BitField(23, 20)
  instr_mod0 = BitField(19, 16)
  imm16 = BitField(15, 0)

class TTSFPSTORE(TTInst):
  name = 'SFPSTORE'
  opcode_ = FixedBitField(31, 24, 0x72)
  lreg_ind = BitField(23, 20)
  instr_mod0 = BitField(19, 16)
  sfpu_addr_mode = BitField(15, 13)
  dest_reg_addr = BitField(12, 0)

class TTSFPLUT(TTInst):
  name = 'SFPLUT'
  opcode_ = FixedBitField(31, 24, 0x73)
  lreg_ind = BitField(23, 20)
  instr_mod0 = BitField(19, 16)
  dest_reg_addr = BitField(15, 0)

class TTSFPMULI(TTInst):
  name = 'SFPMULI'
  opcode_ = FixedBitField(31, 24, 0x74)
  imm16_math = BitField(23, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPADDI(TTInst):
  name = 'SFPADDI'
  opcode_ = FixedBitField(31, 24, 0x75)
  imm16_math = BitField(23, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPDIVP2(TTInst):
  name = 'SFPDIVP2'
  opcode_ = FixedBitField(31, 24, 0x76)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPEXEXP(TTInst):
  name = 'SFPEXEXP'
  opcode_ = FixedBitField(31, 24, 0x77)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPEXMAN(TTInst):
  name = 'SFPEXMAN'
  opcode_ = FixedBitField(31, 24, 0x78)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPIADD(TTInst):
  name = 'SFPIADD'
  opcode_ = FixedBitField(31, 24, 0x79)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPSHFT(TTInst):
  name = 'SFPSHFT'
  opcode_ = FixedBitField(31, 24, 0x7A)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPSETCC(TTInst):
  name = 'SFPSETCC'
  opcode_ = FixedBitField(31, 24, 0x7B)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPMOV(TTInst):
  name = 'SFPMOV'
  opcode_ = FixedBitField(31, 24, 0x7C)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPABS(TTInst):
  name = 'SFPABS'
  opcode_ = FixedBitField(31, 24, 0x7D)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPAND(TTInst):
  name = 'SFPAND'
  opcode_ = FixedBitField(31, 24, 0x7E)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPOR(TTInst):
  name = 'SFPOR'
  opcode_ = FixedBitField(31, 24, 0x7F)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPNOT(TTInst):
  name = 'SFPNOT'
  opcode_ = FixedBitField(31, 24, 0x80)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPLZ(TTInst):
  name = 'SFPLZ'
  opcode_ = FixedBitField(31, 24, 0x81)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPSETEXP(TTInst):
  name = 'SFPSETEXP'
  opcode_ = FixedBitField(31, 24, 0x82)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPSETMAN(TTInst):
  name = 'SFPSETMAN'
  opcode_ = FixedBitField(31, 24, 0x83)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPMAD(TTInst):
  name = 'SFPMAD'
  opcode_ = FixedBitField(31, 24, 0x84)
  lreg_src_a = BitField(19, 16)
  lreg_src_b = BitField(15, 12)
  lreg_src_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPADD(TTInst):
  name = 'SFPADD'
  opcode_ = FixedBitField(31, 24, 0x85)
  lreg_src_a = BitField(19, 16)
  lreg_src_b = BitField(15, 12)
  lreg_src_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPMUL(TTInst):
  name = 'SFPMUL'
  opcode_ = FixedBitField(31, 24, 0x86)
  lreg_src_a = BitField(19, 16)
  lreg_src_b = BitField(15, 12)
  lreg_src_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPPUSHC(TTInst):
  name = 'SFPPUSHC'
  opcode_ = FixedBitField(31, 24, 0x87)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPPOPC(TTInst):
  name = 'SFPPOPC'
  opcode_ = FixedBitField(31, 24, 0x88)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPSETSGN(TTInst):
  name = 'SFPSETSGN'
  opcode_ = FixedBitField(31, 24, 0x89)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPENCC(TTInst):
  name = 'SFPENCC'
  opcode_ = FixedBitField(31, 24, 0x8A)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPCOMPC(TTInst):
  name = 'SFPCOMPC'
  opcode_ = FixedBitField(31, 24, 0x8B)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPTRANSP(TTInst):
  name = 'SFPTRANSP'
  opcode_ = FixedBitField(31, 24, 0x8C)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPXOR(TTInst):
  name = 'SFPXOR'
  opcode_ = FixedBitField(31, 24, 0x8D)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPSTOCHRND(TTInst):
  name = 'SFPSTOCHRND'
  opcode_ = FixedBitField(31, 24, 0x8E)
  rnd_mode = BitField(23, 21)
  imm8_math = BitField(23, 16)
  lreg_src_b = BitField(15, 12)
  lreg_src_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPNOP(TTInst):
  name = 'SFPNOP'
  opcode_ = FixedBitField(31, 24, 0x8F)

class TTSFPCAST(TTInst):
  name = 'SFPCAST'
  opcode_ = FixedBitField(31, 24, 0x90)
  lreg_src_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPCONFIG(TTInst):
  name = 'SFPCONFIG'
  opcode_ = FixedBitField(31, 24, 0x91)
  imm16_math = BitField(23, 8)
  config_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPSWAP(TTInst):
  name = 'SFPSWAP'
  opcode_ = FixedBitField(31, 24, 0x92)
  imm12_math = BitField(23, 12)
  lreg_src_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPLOADMACRO(TTInst):
  name = 'SFPLOADMACRO'
  opcode_ = FixedBitField(31, 24, 0x93)
  lreg_ind = BitField(23, 20)
  instr_mod0 = BitField(19, 16)
  sfpu_addr_mode = BitField(15, 13)
  dest_reg_addr = BitField(12, 0)

class TTSFPSHFT2(TTInst):
  name = 'SFPSHFT2'
  opcode_ = FixedBitField(31, 24, 0x94)
  imm12_math = BitField(23, 12)
  lreg_src_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPLUTFP32(TTInst):
  name = 'SFPLUTFP32'
  opcode_ = FixedBitField(31, 24, 0x95)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPLE(TTInst):
  name = 'SFPLE'
  opcode_ = FixedBitField(31, 24, 0x96)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPGT(TTInst):
  name = 'SFPGT'
  opcode_ = FixedBitField(31, 24, 0x97)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPMUL24(TTInst):
  name = 'SFPMUL24'
  opcode_ = FixedBitField(31, 24, 0x98)
  lreg_src_a = BitField(19, 16)
  lreg_src_b = BitField(15, 12)
  lreg_src_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTSFPARECIP(TTInst):
  name = 'SFPARECIP'
  opcode_ = FixedBitField(31, 24, 0x99)
  imm12_math = BitField(23, 12)
  lreg_c = BitField(11, 8)
  lreg_dest = BitField(7, 4)
  instr_mod1 = BitField(3, 0)

class TTATGETM(TTInst):
  name = 'ATGETM'
  opcode_ = FixedBitField(31, 24, 0xA0)
  mutex_index = BitField(23, 0)

class TTATRELM(TTInst):
  name = 'ATRELM'
  opcode_ = FixedBitField(31, 24, 0xA1)
  mutex_index = BitField(23, 0)

class TTSTALLWAIT(TTInst):
  name = 'STALLWAIT'
  opcode_ = FixedBitField(31, 24, 0xA2)
  stall_res = BitField(23, 15)
  wait_res = BitField(14, 0)

class TTSEMINIT(TTInst):
  name = 'SEMINIT'
  opcode_ = FixedBitField(31, 24, 0xA3)
  max_value = BitField(23, 20)
  init_value = BitField(19, 16)
  sem_sel = BitField(9, 2)

class TTSEMPOST(TTInst):
  name = 'SEMPOST'
  opcode_ = FixedBitField(31, 24, 0xA4)
  sem_sel = BitField(9, 2)

class TTSEMGET(TTInst):
  name = 'SEMGET'
  opcode_ = FixedBitField(31, 24, 0xA5)
  sem_sel = BitField(9, 2)

class TTSEMWAIT(TTInst):
  name = 'SEMWAIT'
  opcode_ = FixedBitField(31, 24, 0xA6)
  stall_res = BitField(23, 15)
  sem_sel = BitField(9, 2)
  wait_sem_cond = BitField(1, 0)

class TTSTREAMWAIT(TTInst):
  name = 'STREAMWAIT'
  opcode_ = FixedBitField(31, 24, 0xA7)
  stall_res = BitField(23, 15)
  target_value = BitField(13, 4)
  target_sel = BitField(3, 3)
  wait_stream_sel = BitField(1, 0)

class TTWRCFG(TTInst):
  name = 'WRCFG'
  opcode_ = FixedBitField(31, 24, 0xB0)
  GprAddress = BitField(21, 16)
  wr128b = BitField(15, 15)
  CfgReg = BitField(10, 0)

class TTRDCFG(TTInst):
  name = 'RDCFG'
  opcode_ = FixedBitField(31, 24, 0xB1)
  GprAddress = BitField(21, 16)
  CfgReg = BitField(10, 0)

class TTSETC16(TTInst):
  name = 'SETC16'
  opcode_ = FixedBitField(31, 24, 0xB2)
  setc16_reg = BitField(23, 16)
  setc16_value = BitField(15, 0)

class TTRMWCIB0(TTInst):
  name = 'RMWCIB0'
  opcode_ = FixedBitField(31, 24, 0xB3)
  Mask = BitField(23, 16)
  Data = BitField(15, 8)
  CfgRegAddr = BitField(7, 0)

class TTRMWCIB1(TTInst):
  name = 'RMWCIB1'
  opcode_ = FixedBitField(31, 24, 0xB4)
  Mask = BitField(23, 16)
  Data = BitField(15, 8)
  CfgRegAddr = BitField(7, 0)

class TTRMWCIB2(TTInst):
  name = 'RMWCIB2'
  opcode_ = FixedBitField(31, 24, 0xB5)
  Mask = BitField(23, 16)
  Data = BitField(15, 8)
  CfgRegAddr = BitField(7, 0)

class TTRMWCIB3(TTInst):
  name = 'RMWCIB3'
  opcode_ = FixedBitField(31, 24, 0xB6)
  Mask = BitField(23, 16)
  Data = BitField(15, 8)
  CfgRegAddr = BitField(7, 0)

class TTSTREAMWRCFG(TTInst):
  name = 'STREAMWRCFG'
  opcode_ = FixedBitField(31, 24, 0xB7)
  stream_id_sel = BitField(22, 21)
  StreamRegAddr = BitField(20, 11)
  CfgReg = BitField(10, 0)

class TTCFGSHIFTMASK(TTInst):
  name = 'CFGSHIFTMASK'
  opcode_ = FixedBitField(31, 24, 0xB8)
  mask_mode = BitField(23, 23)
  disable_mask_on_old_val = BitField(23, 23)
  alu_mode = BitField(22, 20)
  operation = BitField(22, 20)
  mask_width = BitField(19, 15)
  rotate_amt = BitField(14, 10)
  right_cshift_amt = BitField(14, 10)
  scratch_index = BitField(9, 8)
  scratch_sel = BitField(9, 8)
  cfg_index = BitField(7, 0)
  CfgReg = BitField(7, 0)

class TTWRCFG32(TTInst):
  name = 'WRCFG32'
  opcode_ = FixedBitField(31, 24, 0xC0)
  GprAddress = BitField(23, 18)
  CfgReg = BitField(10, 0)

def _tt_fixed_field(cls, name):
  for field in cls._fields:
    if field.name == name and isinstance(field, FixedBitField):
      return field.value
  return None

_TENSIX_BY_OPCODE = {
  opcode: (cls.name, cls)
  for cls in TTInst.__subclasses__()
  if (opcode := _tt_fixed_field(cls, "opcode_")) is not None
}

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
