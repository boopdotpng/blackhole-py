from __future__ import annotations

def _sext(v, w): return v - (1 << w) if v & (1 << (w - 1)) else v
def _u(v, w): return v & ((1 << w) - 1)
def rol2(v): return ((v << 2) | (v >> 30)) & 0xFFFFFFFF
def ror2(v): return ((v >> 2) | (v << 30)) & 0xFFFFFFFF

class Reg:
  _NAMES = {
    0: "zero", 1: "ra", 2: "sp", 3: "gp", 4: "tp",
    5: "t0", 6: "t1", 7: "t2", 8: "s0", 9: "s1",
    10: "a0", 11: "a1", 12: "a2", 13: "a3", 14: "a4", 15: "a5",
    16: "a6", 17: "a7", 18: "s2", 19: "s3", 20: "s4", 21: "s5",
    22: "s6", 23: "s7", 24: "s8", 25: "s9", 26: "s10", 27: "s11",
    28: "t3", 29: "t4", 30: "t5", 31: "t6",
  }
  _BY_NAME = {v: k for k, v in _NAMES.items()}
  _ALIASES = {"fp": 8}

  def __init__(self, idx: int | str):
    if isinstance(idx, str):
      idx = self._ALIASES.get(idx, self._BY_NAME.get(idx, idx))
    if not isinstance(idx, int) or not 0 <= idx < 32:
      raise RuntimeError(f"unknown RISC-V register: {idx!r}")
    self.idx = idx

  def __int__(self): return self.idx
  def __index__(self): return self.idx
  def fmt(self, *, abi=True): return self._NAMES[self.idx] if abi else f"x{self.idx}"
  def __repr__(self): return self.fmt()

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
  def __repr__(self):
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

_R = [
  ("add", 0x00, 0), ("sub", 0x20, 0), ("sll", 0x00, 1), ("slt", 0x00, 2),
  ("sltu", 0x00, 3), ("xor", 0x00, 4), ("srl", 0x00, 5), ("sra", 0x20, 5),
  ("or", 0x00, 6), ("and", 0x00, 7), ("mul", 0x01, 0), ("mulhu", 0x01, 3),
  ("divu", 0x01, 5), ("remu", 0x01, 7), ("sh1add", 0x10, 2),
  ("sh2add", 0x10, 4), ("sh3add", 0x10, 6), ("min", 0x05, 4),
  ("minu", 0x05, 5), ("maxu", 0x05, 7),
]
_I = [("addi", 0), ("sltiu", 3), ("xori", 4), ("ori", 6), ("andi", 7)]
_ISH = [("slli", 0x00, 1), ("srli", 0x00, 5), ("srai", 0x20, 5),
        ("ctz", 0x30, 1), ("sext_b", 0x30, 1), ("sext_h", 0x30, 1)]
_ISH_IMM = {"ctz": 0x601, "sext_b": 0x604, "sext_h": 0x605}
_LOAD = [("lw", 2), ("lbu", 4), ("lhu", 5)]
_STORE = [("sb", 0), ("sh", 1), ("sw", 2)]
_BR = [("beq", 0), ("bne", 1), ("blt", 4), ("bge", 5), ("bltu", 6), ("bgeu", 7)]

_DECODE = {}

def _add_decode(name, cls, key):
  _DECODE[key] = (name, cls)

def _ctor(name, cls, **fixed):
  def f(**kw): return cls(name=name, **fixed, **kw)
  f.__name__ = name
  return f

for name, f7, f3 in _R:
  globals()[name] = lambda rd, rs1, rs2, _n=name, _f7=f7, _f3=f3: RType(name=_n, opcode=0x33, funct3=_f3, funct7=_f7, rd=rd, rs1=rs1, rs2=rs2)
  _add_decode(name, RType, (0x33, f3, f7))
zext_h = lambda rd, rs1: RType(name="zext_h", opcode=0x33, funct3=4, funct7=4, rd=rd, rs1=rs1, rs2=Reg(0))
_add_decode("zext_h", RType, (0x33, 4, 4))
for name, f3 in _I:
  globals()[name] = lambda rd, rs1, imm, _n=name, _f3=f3: IType(name=_n, opcode=0x13, funct3=_f3, rd=rd, rs1=rs1, imm=imm)
  _add_decode(name, IType, (0x13, f3, None))
for name, f7, f3 in _ISH:
  globals()[name] = lambda rd, rs1, shamt=0, _n=name, _f7=f7, _f3=f3: IType(name=_n, opcode=0x13, funct3=_f3, rd=rd, rs1=rs1, imm=_ISH_IMM.get(_n, (_f7 << 5) | shamt))
  _add_decode(name, IType, (0x13, f3, _ISH_IMM.get(name, f7 << 5) >> 5))
for name, f3 in _LOAD:
  globals()[name] = lambda rd, rs1, imm, _n=name, _f3=f3: IType(name=_n, opcode=0x03, funct3=_f3, rd=rd, rs1=rs1, imm=imm)
  _add_decode(name, IType, (0x03, f3, None))
for name, f3 in _STORE:
  globals()[name] = lambda rs2, rs1, imm, _n=name, _f3=f3: SType(name=_n, opcode=0x23, funct3=_f3, rs2=rs2, rs1=rs1, imm=imm)
  _add_decode(name, SType, (0x23, f3, None))
for name, f3 in _BR:
  globals()[name] = lambda rs1, rs2, imm, _n=name, _f3=f3: BType(name=_n, opcode=0x63, funct3=_f3, rs1=rs1, rs2=rs2, imm=imm)
  _add_decode(name, BType, (0x63, f3, None))

lui = lambda rd, imm: UType(name="lui", opcode=0x37, rd=rd, imm=imm >> 12)
auipc = lambda rd, imm: UType(name="auipc", opcode=0x17, rd=rd, imm=imm >> 12)
jal = lambda rd, imm: JType(name="jal", opcode=0x6F, rd=rd, imm=imm)
jalr = lambda rd, rs1, imm=0: IType(name="jalr", opcode=0x67, funct3=0, rd=rd, rs1=rs1, imm=imm)
csrrs = lambda rd, rs1, csr: IType(name="csrrs", opcode=0x73, funct3=2, rd=rd, rs1=rs1, imm=csr)
csrrc = lambda rd, rs1, csr: IType(name="csrrc", opcode=0x73, funct3=3, rd=rd, rs1=rs1, imm=csr)
fence = lambda: IType(name="fence", opcode=0x0F, funct3=0, rd=Reg(0), rs1=Reg(0), imm=0x0FF)
for name, cls, key in (("lui", UType, (0x37, None, None)), ("auipc", UType, (0x17, None, None)),
                       ("jal", JType, (0x6F, None, None)), ("jalr", IType, (0x67, 0, None)),
                       ("csrrs", IType, (0x73, 2, None)), ("csrrc", IType, (0x73, 3, None)),
                       ("fence", IType, (0x0F, 0, None))):
  _add_decode(name, cls, key)

def decode(word):
  word &= 0xFFFFFFFF
  if (word & 3) != 3:
    return TTInst.from_stream_word(word)
  opcode, funct3, funct7 = word & 0x7F, (word >> 12) & 7, (word >> 25) & 0x7F
  if opcode == 0x13 and funct3 == 1 and (word >> 20) in {0x601, 0x604, 0x605}:
    return IType.from_word(word, name={0x601: "ctz", 0x604: "sext_b", 0x605: "sext_h"}[word >> 20])
  name_cls = (_DECODE.get((opcode, funct3, funct7)) or
              _DECODE.get((opcode, funct3, None)) or
              _DECODE.get((opcode, None, None)))
  if name_cls is None: raise ValueError(f"unknown RISC-V word 0x{word:08x}")
  name, cls = name_cls
  return cls.from_word(word, name=name)

class TTInst:
  def __init__(self, opcode, payload=0):
    if not 0 <= opcode < 256: raise ValueError("Tensix opcode must fit in 8 bits")
    if not 0 <= payload < (1 << 24): raise ValueError("Tensix payload must fit in 24 bits")
    self.opcode, self.payload = opcode, payload

  @classmethod
  def from_raw_word(cls, word):
    return cls((word >> 24) & 0xFF, word & 0xFFFFFF)

  @classmethod
  def from_stream_word(cls, word):
    return cls.from_raw_word(ror2(word))

  def raw_word(self): return (self.opcode << 24) | self.payload
  def to_word(self):
    raw = self.raw_word()
    if raw >= 0xC0000000:
      raise ValueError(f"Tensix inline word would look like RISC-V: 0x{raw:08x}")
    return rol2(raw)
  def to_bytes(self): return self.to_word().to_bytes(4, "little")
  def __int__(self): return self.to_word()
  def __repr__(self): return f"tt(opcode=0x{self.opcode:02x}, payload=0x{self.payload:06x})"

def tt_raw(word): return TTInst.from_raw_word(word)
def tt(opcode, payload=0): return TTInst(opcode, payload)
