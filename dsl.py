from dataclasses import dataclass
from functools import partial
import struct
import sys

# =============================================================================
# Types
# =============================================================================
@dataclass(frozen=True)
class Insn:
  word: int
  def __int__(self): return self.word

@dataclass(frozen=True)
class RiscVInsn(Insn): pass

@dataclass(frozen=True)
class TensixInsn(Insn): pass

# =============================================================================
# Field validation
# =============================================================================
def R(v):
  v = int(v)
  if not 0 <= v <= 31: raise ValueError(f"register {v} not in 0..31")
  return v
def U(v, w):
  if not 0 <= v < (1 << w): raise ValueError(f"{v} doesn't fit in {w}-bit unsigned field")
  return v
def S(v, w):
  if not -(1 << (w-1)) <= v < (1 << (w-1)): raise ValueError(f"{v} doesn't fit in {w}-bit signed field")
  return v & ((1 << w) - 1)

def bits(v, hi, lo=None):
  if lo is None: lo = hi
  return (v >> lo) & ((1 << (hi - lo + 1)) - 1)

# =============================================================================
# TensixOp: declarative instruction definitions with encode + decode
# =============================================================================
@dataclass(frozen=True)
class F:
  name: str
  shift: int
  width: int

class TensixOp:
  _all = []

  def __init__(self, opcode, doc, fields=()):
    self.opcode = opcode
    self.doc = doc
    self.fields = tuple(fields)
    self.name = None  # set by _register_names()
    TensixOp._all.append(self)

  def __call__(self, *args, **kwargs):
    if len(args) > len(self.fields):
      raise TypeError(f"{self.name or '?'}: expected at most {len(self.fields)} positional args, got {len(args)}")
    field_names = {f.name for f in self.fields}
    extra_kwargs = sorted(kwargs.keys() - field_names)
    if extra_kwargs:
      names = ", ".join(repr(k) for k in extra_kwargs)
      raise TypeError(f"{self.name or '?'}: unexpected keyword arg(s): {names}")
    vals = {}
    for i, f in enumerate(self.fields):
      if i < len(args):
        if f.name in kwargs:
          raise TypeError(f"{self.name or '?'}: got multiple values for arg '{f.name}'")
        vals[f.name] = args[i]
      elif f.name in kwargs: vals[f.name] = kwargs[f.name]
      else: raise TypeError(f"{self.name or '?'}: missing arg '{f.name}'")
    p = 0
    for f in self.fields:
      v = int(vals[f.name])
      if not 0 <= v < (1 << f.width):
        raise ValueError(f"{self.name}.{f.name}={v} doesn't fit in {f.width} bits")
      p |= v << f.shift
    return TensixInsn((self.opcode << 24) | p)

  def decode(self, word):
    op = (word >> 24) & 0xFF
    if op != self.opcode:
      raise ValueError(f"opcode 0x{op:02X} != 0x{self.opcode:02X} ({self.name})")
    return {f.name: (word >> f.shift) & ((1 << f.width) - 1) for f in self.fields}

  def __repr__(self):
    return f"TensixOp(0x{self.opcode:02X}, {self.name or '?'})"

TENSIX_ISA = TensixOp._all

class TensixDecoded:
  """Decoded Tensix instruction. Fields are accessible as attributes:
    d = decode_tensix(word)
    d.name        # e.g. 'ZEROACC', or 'UNKNOWN_0x03' for unknown opcodes
    d.word        # raw 32-bit word
    d.clear_mode  # op-specific field (KeyError-as-AttributeError otherwise)
  """
  def __init__(self, name, word, fields):
    self.name = name
    self.word = word & 0xFFFFFFFF
    self._fields = fields

  def __getattr__(self, k):
    fields = object.__getattribute__(self, '_fields')
    if k in fields: return fields[k]
    raise AttributeError(f"{self.name!r} has no field {k!r}; fields: {list(fields)}")

  def __int__(self): return self.word

  def __repr__(self):
    args = ', '.join(f'{k}=0x{v:X}' for k, v in self._fields.items())
    return f'{self.name}({args})' if args else f'{self.name}()'

_TENSIX_BY_OPCODE = {}  # rebuilt below after names are assigned

def decode_tensix(word):
  op = (word >> 24) & 0xFF
  insn = _TENSIX_BY_OPCODE.get(op)
  if insn is None:
    return TensixDecoded(f"UNKNOWN_0x{op:02X}", word, {"raw_params": word & 0xFFFFFF})
  return TensixDecoded(insn.name, word, insn.decode(word))

# =============================================================================
# RISC-V encoding formats
# =============================================================================
def _r(op, f3, f7, rd, rs1, rs2):
  return RiscVInsn(op | R(rd)<<7 | f3<<12 | R(rs1)<<15 | R(rs2)<<20 | f7<<25)
def _i(op, f3, rd, rs1, imm):
  return RiscVInsn(op | R(rd)<<7 | f3<<12 | R(rs1)<<15 | S(imm,12)<<20)
def _s(op, f3, rs1, rs2, imm):
  i = S(imm, 12)
  return RiscVInsn(op | bits(i,4,0)<<7 | f3<<12 | R(rs1)<<15 | R(rs2)<<20 | bits(i,11,5)<<25)
def _b(op, f3, rs1, rs2, imm):
  i = S(imm, 13)
  return RiscVInsn(op | bits(i,11)<<7 | bits(i,4,1)<<8 | f3<<12
    | R(rs1)<<15 | R(rs2)<<20 | bits(i,10,5)<<25 | bits(i,12)<<31)
def _u(op, rd, imm):
  return RiscVInsn(op | R(rd)<<7 | (imm & 0xFFFFF000))
def _j(op, rd, imm):
  i = S(imm, 21)
  return RiscVInsn(op | R(rd)<<7 | bits(i,19,12)<<12 | bits(i,11)<<20
    | bits(i,10,1)<<21 | bits(i,20)<<31)

# =============================================================================
# RV32I base
# =============================================================================
ADD  = partial(_r, 0x33, 0, 0x00); SUB  = partial(_r, 0x33, 0, 0x20)
SLL  = partial(_r, 0x33, 1, 0x00); SLT  = partial(_r, 0x33, 2, 0x00)
SLTU = partial(_r, 0x33, 3, 0x00); XOR  = partial(_r, 0x33, 4, 0x00)
SRL  = partial(_r, 0x33, 5, 0x00); SRA  = partial(_r, 0x33, 5, 0x20)
OR   = partial(_r, 0x33, 6, 0x00); AND  = partial(_r, 0x33, 7, 0x00)
ADDI  = partial(_i, 0x13, 0)
SLTIU = partial(_i, 0x13, 3); XORI  = partial(_i, 0x13, 4)
ORI   = partial(_i, 0x13, 6); ANDI  = partial(_i, 0x13, 7)
SLLI  = lambda rd, rs1, shamt: _i(0x13, 1, rd, rs1, U(shamt,5))
SRLI  = lambda rd, rs1, shamt: _i(0x13, 5, rd, rs1, U(shamt,5))
SRAI  = lambda rd, rs1, shamt: _i(0x13, 5, rd, rs1, U(shamt,5) | 0x400)
LW  = partial(_i, 0x03, 2); LBU = partial(_i, 0x03, 4); LHU = partial(_i, 0x03, 5)
SB = partial(_s, 0x23, 0); SH = partial(_s, 0x23, 1); SW = partial(_s, 0x23, 2)
BEQ  = partial(_b, 0x63, 0); BNE  = partial(_b, 0x63, 1)
BLT  = partial(_b, 0x63, 4); BGE  = partial(_b, 0x63, 5)
BLTU = partial(_b, 0x63, 6); BGEU = partial(_b, 0x63, 7)
LUI   = partial(_u, 0x37); AUIPC = partial(_u, 0x17)
JAL  = partial(_j, 0x6F); JALR = partial(_i, 0x67, 0)
FENCE  = lambda: _i(0x0F, 0, 0, 0, 0xFF)
CSRRS  = lambda rd, rs1, csr: _i(0x73, 2, rd, rs1, U(csr,12))
CSRRC  = lambda rd, rs1, csr: _i(0x73, 3, rd, rs1, U(csr,12))

# -- M extension ---------------------------------------------------------------
MUL    = partial(_r, 0x33, 0, 0x01)
MULH   = partial(_r, 0x33, 1, 0x01)
MULHSU = partial(_r, 0x33, 2, 0x01)
MULHU  = partial(_r, 0x33, 3, 0x01)
DIV    = partial(_r, 0x33, 4, 0x01)
DIVU   = partial(_r, 0x33, 5, 0x01)
REM    = partial(_r, 0x33, 6, 0x01)
REMU   = partial(_r, 0x33, 7, 0x01)

# -- Zba -----------------------------------------------------------------------
SH1ADD = partial(_r, 0x33, 2, 0x10)
SH2ADD = partial(_r, 0x33, 4, 0x10)
SH3ADD = partial(_r, 0x33, 6, 0x10)

# -- Zbb + Zbkb ----------------------------------------------------------------
MAX  = partial(_r, 0x33, 6, 0x05)
MAXU = partial(_r, 0x33, 7, 0x05)
MIN  = partial(_r, 0x33, 4, 0x05); MINU = partial(_r, 0x33, 5, 0x05)
ANDN = partial(_r, 0x33, 7, 0x20)
ORN  = partial(_r, 0x33, 6, 0x20)
XNOR = partial(_r, 0x33, 4, 0x20)
ROL  = partial(_r, 0x33, 1, 0x30)
ROR  = partial(_r, 0x33, 5, 0x30)
CLZ    = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x600)
CTZ    = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x601)
CPOP   = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x602)
SEXT_B = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x604)
SEXT_H = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x605)
ZEXT_H = lambda rd, rs1: _r(0x33, 4, 0x04, rd, rs1, 0)
RORI   = lambda rd, rs1, shamt: _i(0x13, 5, rd, rs1, U(shamt, 5) | 0x600)
REV8   = lambda rd, rs1: _i(0x13, 5, rd, rs1, 0x698)
ORC_B  = lambda rd, rs1: _i(0x13, 5, rd, rs1, 0x287)

# -- registers -----------------------------------------------------------------
zero, ra, sp, gp, tp, t0, t1, t2, s0, s1 = range(10)
a0, a1, a2, a3, a4, a5, a6, a7 = range(10, 18)
s2, s3, s4, s5, s6, s7, s8, s9, s10, s11 = range(18, 28)
t3, t4, t5, t6 = range(28, 32)
fp = s0

# -- pseudo-instructions -------------------------------------------------------
NOP    = lambda: ADDI(0, 0, 0)
LI     = lambda rd, imm: ADDI(rd, zero, imm)
MV     = lambda rd, rs: ADDI(rd, rs, 0)
NOT    = lambda rd, rs: XORI(rd, rs, -1)
NEG    = lambda rd, rs: SUB(rd, zero, rs)
SEQZ   = lambda rd, rs: SLTIU(rd, rs, 1)
SNEZ   = lambda rd, rs: SLTU(rd, zero, rs)
BEQZ   = lambda rs, imm: BEQ(rs, zero, imm)
BNEZ   = lambda rs, imm: BNE(rs, zero, imm)
BLEZ   = lambda rs, imm: BGE(zero, rs, imm)
BGEZ   = lambda rs, imm: BGE(rs, zero, imm)
BLTZ   = lambda rs, imm: BLT(rs, zero, imm)
BGTZ   = lambda rs, imm: BLT(zero, rs, imm)
J      = lambda imm: JAL(zero, imm)
JR     = lambda rs: JALR(zero, rs, 0)
RET    = lambda: JALR(zero, ra, 0)
ZEXT_B = lambda rd, rs: ANDI(rd, rs, 0xFF)

# =============================================================================
# RISC-V decoder — raw 32-bit word → RvDecoded(name, rd, rs1, ...)
# Mirrors decode_tensix; covers the RV32IMZba/Zbb subset above.
# =============================================================================
@dataclass(frozen=True)
class RvDecoded:
  name: str     # e.g. 'ADD', 'ZEXT_H', 'CSRRS', or 'UNKNOWN'
  word: int = 0
  rd: int = 0
  rs1: int = 0  # for CSRRWI/CSRRSI/CSRRCI this holds the 5-bit zimm
  rs2: int = 0
  imm: int = 0  # sign-extended where applicable; LUI/AUIPC keep upper 20 in place
  shamt: int = 0
  csr: int = 0
  def __int__(self): return self.word

def _sext(v, w): return v - (1 << w) if v & (1 << (w-1)) else v

def _x_R(w):   return dict(rd=bits(w,11,7), rs1=bits(w,19,15), rs2=bits(w,24,20))
def _x_I(w):   return dict(rd=bits(w,11,7), rs1=bits(w,19,15), imm=_sext(bits(w,31,20), 12))
def _x_Ish(w): return dict(rd=bits(w,11,7), rs1=bits(w,19,15), shamt=bits(w,24,20))
def _x_S(w):   return dict(rs1=bits(w,19,15), rs2=bits(w,24,20),
                           imm=_sext(bits(w,11,7) | (bits(w,31,25)<<5), 12))
def _x_B(w):   return dict(rs1=bits(w,19,15), rs2=bits(w,24,20),
                           imm=_sext((bits(w,11,8)<<1) | (bits(w,30,25)<<5)
                             | (bits(w,7)<<11) | (bits(w,31)<<12), 13))
def _x_U(w):   return dict(rd=bits(w,11,7), imm=w & 0xFFFFF000)
def _x_J(w):   return dict(rd=bits(w,11,7),
                           imm=_sext((bits(w,30,21)<<1) | (bits(w,20)<<11)
                             | (bits(w,19,12)<<12) | (bits(w,31)<<20), 21))
def _x_CSR(w): return dict(rd=bits(w,11,7), rs1=bits(w,19,15), csr=bits(w,31,20))
def _x_NONE(w): return {}

_FMT = {'R':_x_R, 'I':_x_I, 'Ish':_x_Ish, 'S':_x_S, 'B':_x_B,
        'U':_x_U, 'J':_x_J, 'CSR':_x_CSR, 'NONE':_x_NONE}

# (mask, bits, name, fmt) — source of truth for every opcode the core emulates.
_RV_DECODE = [
    # RV32I R-type
    (0xFE00707F, 0x00000033, 'ADD',    'R'),
    (0xFE00707F, 0x40000033, 'SUB',    'R'),
    (0xFE00707F, 0x00001033, 'SLL',    'R'),
    (0xFE00707F, 0x00002033, 'SLT',    'R'),
    (0xFE00707F, 0x00003033, 'SLTU',   'R'),
    (0xFE00707F, 0x00004033, 'XOR',    'R'),
    (0xFE00707F, 0x00005033, 'SRL',    'R'),
    (0xFE00707F, 0x40005033, 'SRA',    'R'),
    (0xFE00707F, 0x00006033, 'OR',     'R'),
    (0xFE00707F, 0x00007033, 'AND',    'R'),
    # M extension
    (0xFE00707F, 0x02000033, 'MUL',    'R'),
    (0xFE00707F, 0x02001033, 'MULH',   'R'),
    (0xFE00707F, 0x02002033, 'MULHSU', 'R'),
    (0xFE00707F, 0x02003033, 'MULHU',  'R'),
    (0xFE00707F, 0x02004033, 'DIV',    'R'),
    (0xFE00707F, 0x02005033, 'DIVU',   'R'),
    (0xFE00707F, 0x02006033, 'REM',    'R'),
    (0xFE00707F, 0x02007033, 'REMU',   'R'),
    # Zba
    (0xFE00707F, 0x20002033, 'SH1ADD', 'R'),
    (0xFE00707F, 0x20004033, 'SH2ADD', 'R'),
    (0xFE00707F, 0x20006033, 'SH3ADD', 'R'),
    # Zbb R-type (ZEXT_H also mandates rs2=0 → wider mask)
    (0xFFF0707F, 0x08004033, 'ZEXT_H', 'R'),
    (0xFE00707F, 0x0A004033, 'MIN',    'R'),
    (0xFE00707F, 0x0A005033, 'MINU',   'R'),
    (0xFE00707F, 0x0A006033, 'MAX',    'R'),
    (0xFE00707F, 0x0A007033, 'MAXU',   'R'),
    (0xFE00707F, 0x40004033, 'XNOR',   'R'),
    (0xFE00707F, 0x40006033, 'ORN',    'R'),
    (0xFE00707F, 0x40007033, 'ANDN',   'R'),
    (0xFE00707F, 0x60001033, 'ROL',    'R'),
    (0xFE00707F, 0x60005033, 'ROR',    'R'),
    # RV32I I-type ALU
    (0x0000707F, 0x00000013, 'ADDI',   'I'),
    (0x0000707F, 0x00002013, 'SLTI',   'I'),
    (0x0000707F, 0x00003013, 'SLTIU',  'I'),
    (0x0000707F, 0x00004013, 'XORI',   'I'),
    (0x0000707F, 0x00006013, 'ORI',    'I'),
    (0x0000707F, 0x00007013, 'ANDI',   'I'),
    # Zbb I-type unary (funct12 fully fixed → mask before I-shift)
    (0xFFF0707F, 0x60001013, 'CLZ',    'Ish'),
    (0xFFF0707F, 0x60101013, 'CTZ',    'Ish'),
    (0xFFF0707F, 0x60201013, 'CPOP',   'Ish'),
    (0xFFF0707F, 0x60401013, 'SEXT_B', 'Ish'),
    (0xFFF0707F, 0x60501013, 'SEXT_H', 'Ish'),
    (0xFFF0707F, 0x28705013, 'ORC_B',  'Ish'),
    (0xFFF0707F, 0x69805013, 'REV8',   'Ish'),
    # I-type shifts
    (0xFE00707F, 0x00001013, 'SLLI',   'Ish'),
    (0xFE00707F, 0x00005013, 'SRLI',   'Ish'),
    (0xFE00707F, 0x40005013, 'SRAI',   'Ish'),
    (0xFE00707F, 0x60005013, 'RORI',   'Ish'),
    # Loads
    (0x0000707F, 0x00000003, 'LB',     'I'),
    (0x0000707F, 0x00001003, 'LH',     'I'),
    (0x0000707F, 0x00002003, 'LW',     'I'),
    (0x0000707F, 0x00004003, 'LBU',    'I'),
    (0x0000707F, 0x00005003, 'LHU',    'I'),
    # Stores
    (0x0000707F, 0x00000023, 'SB',     'S'),
    (0x0000707F, 0x00001023, 'SH',     'S'),
    (0x0000707F, 0x00002023, 'SW',     'S'),
    # Branches
    (0x0000707F, 0x00000063, 'BEQ',    'B'),
    (0x0000707F, 0x00001063, 'BNE',    'B'),
    (0x0000707F, 0x00004063, 'BLT',    'B'),
    (0x0000707F, 0x00005063, 'BGE',    'B'),
    (0x0000707F, 0x00006063, 'BLTU',   'B'),
    (0x0000707F, 0x00007063, 'BGEU',   'B'),
    # Upper-immediate
    (0x0000007F, 0x00000037, 'LUI',    'U'),
    (0x0000007F, 0x00000017, 'AUIPC',  'U'),
    # Jumps
    (0x0000007F, 0x0000006F, 'JAL',    'J'),
    (0x0000707F, 0x00000067, 'JALR',   'I'),
    # CSR (register form)
    (0x0000707F, 0x00001073, 'CSRRW',  'CSR'),
    (0x0000707F, 0x00002073, 'CSRRS',  'CSR'),
    (0x0000707F, 0x00003073, 'CSRRC',  'CSR'),
    # CSR (immediate form — zimm lives in the rs1 slot)
    (0x0000707F, 0x00005073, 'CSRRWI', 'CSR'),
    (0x0000707F, 0x00006073, 'CSRRSI', 'CSR'),
    (0x0000707F, 0x00007073, 'CSRRCI', 'CSR'),
    # FENCE (catch any opcode 0x0F — FENCE.I etc. are no-ops here)
    (0x0000007F, 0x0000000F, 'FENCE',  'NONE'),
]

# Bucket by opcode (low 7 bits) for O(1) lookup per decode.
_RV_BY_OPCODE = {}
for _m, _b, _n, _f in _RV_DECODE:
  _RV_BY_OPCODE.setdefault(_b & 0x7F, []).append((_m, _b, _n, _f))

def decode_rv(word):
  w = word & 0xFFFFFFFF
  for mask, b, name, fmt in _RV_BY_OPCODE.get(w & 0x7F, ()):
    if (w & mask) == b:
      return RvDecoded(name=name, word=w, **_FMT[fmt](w))
  return RvDecoded(name='UNKNOWN', word=w)

def parse(data):
  if isinstance(data, (bytes, bytearray, memoryview)):
    if len(data) % 4: raise ValueError(f"byte length {len(data)} not a multiple of 4")
    data = struct.unpack(f'<{len(data)//4}I', bytes(data))
  return [decode_rv(int(w)) for w in data]

def pack(insns):
  return b''.join((int(i) & 0xFFFFFFFF).to_bytes(4, 'little') for i in insns)

# =============================================================================
# .ttinsn encoding: Tensix word → RISC-V custom instruction
# =============================================================================
# Rotates the 32-bit Tensix word left by 2 bits. Hardware rotates right 2 and
# pushes the result into the Tensix instruction FIFO at INSTRN_BUF_BASE (0xFFE40000).
def TTINSN(imm32):
  assert imm32 < 0xC0000000, f".ttinsn requires imm32 < 0xC0000000, got 0x{imm32:08x}"
  return RiscVInsn(((imm32 << 2) | (imm32 >> 30)) & 0xFFFFFFFF)

# =============================================================================
# Tensix coprocessor ISA — [opcode:8][params:24]
#
# Issued via TTINSN inline encoding or sw to INSTRN_BUF_BASE.
# Functional units: Matrix engine (FPU), SFPU (32-lane SIMD), Packer/Unpacker,
# Sync unit, Config unit, Scalar/DMA unit (ThCon).
# =============================================================================

# -- flow control --------------------------------------------------------------
TT_NOP   = TensixOp(0x02, "No-op; occupies one Tensix issue slot and one cycle")
TT_MOP   = TensixOp(0x01, "Execute macro-op template in a loop", [
    F("mop_type",                  23, 1),  # 0=MOP_A, 1=MOP_B template
    F("loop_count",                16, 7),  # outer loop iterations (0-127)
    F("zmask_lo16_or_loop_count",   0, 16), # zero-column mask low 16b OR inner loop count
])
TT_REPLAY = TensixOp(0x04, "Re-execute instructions from the replay buffer", [
    F("start_idx",              14, 10), # starting index in replay buffer
    F("len",                     4, 10), # number of instructions to replay
    F("execute_while_loading",   1,  1), # 1=begin execution before buffer fully loaded
    F("load_mode",               0,  1), # replay buffer load mode
])

# -- sync unit -----------------------------------------------------------------
TT_ATGETM    = TensixOp(0xA0, "Acquire mutex; blocks thread until acquired (indices 0,2-4 valid)", [
    F("mutex_index", 0, 24),
])
TT_ATRELM    = TensixOp(0xA1, "Release mutex held by current thread", [
    F("mutex_index", 0, 24),
])
TT_STALLWAIT = TensixOp(0xA2, "Block instruction types (BlockMask) until conditions (ConditionMask) are met", [
    F("stall_res", 15, 9),  # BlockMask: B0=Misc, B2=Pack, B3=Unpack, B4=Mover, B5=ThCon, B6=FPU, B7=Config, B8=SFPU; 0 defaults to B6
    F("wait_res",   0, 15), # ConditionMask: C0=ThCon idle, C4=FPU idle, C11=SFPU idle, etc; 0 defaults to 0x0F
])
TT_SEMINIT   = TensixOp(0xA3, "Initialize semaphore(s): set Value and Max for selected semaphores", [
    F("max_value",  20, 4), # saturation value (0-15)
    F("init_value", 16, 4), # starting count (0-15)
    F("sem_sel",     2, 8), # 8-bit bitmask selecting which semaphores to initialize
])
TT_SEMPOST   = TensixOp(0xA4, "Increment selected semaphores (saturates at 15)", [
    F("sem_sel", 2, 8), # 8-bit bitmask selecting which semaphores to increment
])
TT_SEMGET    = TensixOp(0xA5, "Decrement selected semaphores (floors at 0)", [
    F("sem_sel", 2, 8), # 8-bit bitmask selecting which semaphores to decrement
])
TT_SEMWAIT   = TensixOp(0xA6, "Block instruction types until semaphore conditions are met", [
    F("stall_res",      15, 9), # BlockMask (same as STALLWAIT); 0 defaults to B6
    F("sem_sel",         2, 8), # 8-bit bitmask selecting which semaphores to check
    F("wait_sem_cond",   0, 2), # C0=wait while Value==0, C1=wait while Value>=Max; 0 is UB
])
TT_STREAMWAIT = TensixOp(0xA7, "Block instruction types until a selected stream condition is met", [
    F("stall_res",       15, 9), # BlockMask (same as STALLWAIT); 0 defaults to B6
    F("target_value",     4, 11), # low bits of target phase/message count
    F("target_sel",       3, 1), # 0=phase, 1=num_msgs
    F("wait_stream_sel",  0, 2), # select STREAM_ID_SYNC_SEC register
])

# -- config unit ---------------------------------------------------------------
TT_WRCFG   = TensixOp(0xB0, "Write GPR(s) to shared config register (needs NOP after if next insn reads it)", [
    F("GprAddress", 16, 6), # source GPR index (6b)
    F("wr128b",     15, 1), # 1=write 128b (4 consecutive GPRs), 0=write 32b
    F("CfgReg",      0, 11), # destination config register address
])
TT_RDCFG   = TensixOp(0xB1, "Read shared config register into GPR", [
    F("GprAddress", 16, 6), # destination GPR index
    F("CfgReg",      0, 11), # source config register address
])
TT_SETC16  = TensixOp(0xB2, "Write 16-bit immediate to thread-specific config register", [
    F("setc16_reg",   16, 8),  # ThreadConfig register index
    F("setc16_value",  0, 16), # immediate value
])
TT_RMWCIB0 = TensixOp(0xB3, "Read-modify-write byte 0 of shared config register", [
    F("Mask",       16, 8), # which bits to modify
    F("Data",        8, 8), # new bit values (applied where Mask=1)
    F("CfgRegAddr",  0, 8), # config register 32-bit word index
])
TT_RMWCIB1 = TensixOp(0xB4, "Read-modify-write byte 1 of shared config register", [
    F("Mask",       16, 8),
    F("Data",        8, 8),
    F("CfgRegAddr",  0, 8),
])
TT_STREAMWRCFG = TensixOp(0xB7, "Copy one stream register into shared config", [
    F("stream_id_sel",   21, 2),
    F("StreamRegAddr",   11, 10),
    F("CfgReg",           0, 11),
])
TT_CFGSHIFTMASK = TensixOp(0xB8, "Masked rotated ALU update of shared config using a scratch config register", [
    F("mask_mode",     23, 1),
    F("alu_mode",      20, 3),
    F("mask_width",    15, 5),
    F("rotate_amt",    10, 5),
    F("scratch_index",  8, 2),
    F("cfg_index",      0, 8),
])

# -- matrix unit / FPU ---------------------------------------------------------
TT_ZEROACC = TensixOp(0x10, "Zero out Dest (accumulator) registers", [
    F("clear_mode",       19, 5), # which rows/tiles to clear
    F("use_32_bit_mode",  18, 1), # 1=clear as 32-bit, 0=use configured format
    F("clear_zero_flags", 17, 1), # 1=also clear zero-detect flags
    F("addr_mode",        14, 3), # Dest addressing mode
    F("where",             0, 14), # address/range in Dest to clear
])
TT_ZEROSRC = TensixOp(0x11, "Zero out SrcA/SrcB register banks", [
    F("zero_val",    4, 20), # value to write (usually 0)
    F("write_mode",  3,  1), # 0=zero, 1=write zero_val pattern
    F("bank_mask",   2,  1), # which bank
    F("src_mask",    0,  2), # 0=none, 1=SrcA, 2=SrcB, 3=both
])
TT_MOVB2D  = TensixOp(0x13, "Move data from SrcB to Dest", [
    F("dest_32b_lo",      23, 1), # select low 32b of dest row
    F("src",              17, 6), # SrcB register index
    F("addr_mode",        14, 3), # Dest addressing mode
    F("movb2d_instr_mod", 11, 3), # format conversion mode
    F("dst",               0, 11), # Dest register address
])
TT_TRNSPSRCB = TensixOp(0x16, "Transpose SrcB rows 16-31 in-place (16x16 matrix transpose)")
TT_SHIFTXA = TensixOp(0x17, "Shift SrcA row data horizontally", [
    F("raw", 0, 24),
])
TT_SHIFTXB = TensixOp(0x18, "Shift SrcB row data horizontally", [
    F("raw", 0, 24),
])
TT_MVMUL  = TensixOp(0x26, "Matrix-vector multiply: Dest = SrcA * SrcB", [
    F("clear_dvalid", 22, 2), # clear data-valid flags after consuming sources
    F("instr_mod19",  19, 3), # math mode / format control
    F("addr_mode",    14, 2), # Dest addressing mode
    F("dst",           0, 10), # Dest register address
])
TT_DOTPV = TensixOp(0x29, "Dot-product vector op; functional emulation matches MVMUL", [
    F("clear_dvalid", 22, 2),
    F("instr_mod19",  19, 3),
    F("addr_mode",    14, 2),
    F("dst",           0, 10),
])
TT_GAPOOL = TensixOp(0x34, "Global average/pooling style half-height matrix op", [
    F("clear_dvalid", 22, 2),
    F("instr_mod19",  19, 3),
    F("addr_mode",    14, 2),
    F("dst",           0, 10),
])
TT_ELWADD  = TensixOp(0x28, "Element-wise add: Dest = SrcA + SrcB", [
    F("clear_dvalid",  22, 2),
    F("dest_accum_en", 21, 1), # 1=accumulate into Dest, 0=overwrite
    F("instr_mod19",   19, 2),
    F("addr_mode",     14, 2),
    F("dst",            0, 14),
])
TT_GMPOOL  = TensixOp(0x33, "Global max pooling", [
    F("clear_dvalid",      22, 2),
    F("instr_mod19",       19, 3),
    F("pool_addr_mode",    15, 4),
    F("max_pool_index_en", 14, 1),
    F("dst",                0, 14),
])
TT_CLEARDVALID = TensixOp(0x36, "Clear data-valid flags on SrcA/SrcB", [
    F("cleardvalid", 22, 2), # which flags to clear (2b)
    F("reset",        0, 22), # reset value/address
])

# -- read/write counters -------------------------------------------------------
TT_SETRWC  = TensixOp(0x37, "Set read/write counter offsets for SrcA, SrcB, Dst, CR", [
    F("clear_ab_vld", 22, 2), # clear SrcA/SrcB valid flags
    F("rwc_cr",       18, 4), # CR counter value
    F("rwc_d",        14, 4), # Dst counter value
    F("rwc_b",        10, 4), # SrcB counter value
    F("rwc_a",         6, 4), # SrcA counter value
    F("BitMask",       0, 6), # which counters to update (bitmask)
])
TT_INCRWC  = TensixOp(0x38, "Increment read/write counters by specified amounts", [
    F("rwc_cr", 18, 3),
    F("rwc_d",  14, 4),
    F("rwc_b",  10, 4),
    F("rwc_a",   6, 4),
])

# -- data moves ----------------------------------------------------------------
TT_MOVD2A = TensixOp(0x08, "Move Dest to SrcA (1 or 4 aligned rows, 2-cycle latency, needs STALLWAIT)", [
    F("dest_32b_lo", 23, 1),
    F("src",         17, 6),
    F("addr_mode",   14, 3),
    F("instr_mod",   12, 2),
    F("dst",          0, 12),
])
TT_MOVD2B = TensixOp(0x0A, "Move Dest to SrcB (1 or 4 aligned rows, 3-cycle latency, needs STALLWAIT)", [
    F("dest_32b_lo", 23, 1),
    F("src",         17, 6),
    F("addr_mode",   14, 3),
    F("instr_mod",   12, 2),
    F("dst",          0, 12),
])

# -- mover (XMOV) -------------------------------------------------------------
TT_XMOV = TensixOp(0x40, "Start Mover DMA transfer; src/dst/size/dir come from THCON_SEC0_REG6 config space", [
    F("Mov_block_selection", 23, 1), # selects between two move blocks (no functional effect in sync emu)
    F("Last",                 0, 1), # 1=flush accumulation buffers on completion
])

# -- packer / unpacker ---------------------------------------------------------
TT_PACR = TensixOp(0x41, "Pack one tile face (16 rows) from Dest to L1 with format conversion", [
    F("CfgContext",     21, 3),
    F("RowPadZero",     18, 3),
    F("DstAccessMode",  17, 1), # 0=16b, 1=32b
    F("AddrMode",       15, 2),
    F("AddrCntContext",  13, 2),
    F("ZeroWrite",      12, 1), # write zeros instead of data
    F("ReadIntfSel",     8, 4), # which Dest read port
    F("OvrdThreadId",    7, 1),
    F("Concat",          4, 3), # multi-face packing mode
    F("CtxtCtrl",        2, 2),
    F("Flush",           1, 1), # flush packer pipeline
    F("Last",            0, 1), # signal tile pack complete
])
TT_UNPACR = TensixOp(0x42, "Unpack L1 data to SrcA or SrcB with format conversion", [
    F("Unpack_block_selection", 23, 1), # 0=SrcA, 1=SrcB
    F("AddrMode",               15, 8),
    F("CfgContextCntInc",       13, 2),
    F("CfgContextId",           10, 3),
    F("AddrCntContextId",        8, 2),
    F("OvrdThreadId",            7, 1),
    F("SetDatValid",             6, 1), # 1=flip SrcA/SrcB bank ownership
    F("srcb_bcast",              5, 1), # 1=broadcast SrcB row to all columns
    F("ZeroWrite2",              4, 1),
    F("AutoIncContextID",        3, 1),
    F("RowSearch",               2, 1),
    F("SearchCacheFlush",        1, 1),
    F("Last",                    0, 1), # signal unpack complete
])
TT_UNPACR_NOP = TensixOp(0x43, "Unpacker no-op with side effects: clear msg counts, set dvalid, pop stream msgs", [
    F("Unpacker_Select",   23, 1),
    F("Stream_Id",         16, 7),
    F("Msg_Clr_Cnt",       12, 4),
    F("Set_Dvalid",         8, 4),
    F("Clr_to1_fmt_Ctrl",   6, 2),
    F("Stall_Clr_Cntrl",    5, 1),
    F("Bank_Clr_Ctrl",      4, 1),
    F("Src_ClrVal_Ctrl",    2, 2),
    F("Unpack_Pop",         0, 2),
])

# -- scalar unit (ThCon / DMA) ------------------------------------------------
TT_SETDMAREG = TensixOp(0x45, "Load 16-bit immediate into DMA register or set signal bits", [
    F("Payload_SigSelSize", 22, 2), # 0=16b payload, 1=signal select, 2=extended
    F("Payload_SigSel",      8, 14), # immediate value or signal selector
    F("SetSignalsMode",      7, 1), # 1=set signals mode
    F("RegIndex16b",         0, 7), # target DMA register (0-63 usable)
])
TT_REG2FLOP = TensixOp(0x48, "Move GPR(s) into THCON configuration", [
    F("SizeSel",        22, 2), # 0=128b, nonzero=32b for config variant
    F("ThConCfgIndex",   8, 7),
    F("InputReg",        0, 6),
])
TT_ADDDMAREG = TensixOp(0x58, "DMA register add: Result = OpA + OpB", [
    F("OpBisConst",      23, 1),  # 1=OpB is immediate constant
    F("ResultRegIndex",  12, 11), # destination DMA register
    F("OpBRegIndex",      6, 6),  # source B register or constant
    F("OpARegIndex",      0, 6),  # source A register
])
TT_MULDMAREG = TensixOp(0x5A, "DMA register multiply: Result = OpA * OpB", [
    F("OpBisConst",      23, 1),
    F("ResultRegIndex",  12, 11),
    F("OpBRegIndex",      6, 6),
    F("OpARegIndex",      0, 6),
])
TT_BITWOPDMAREG = TensixOp(0x5B, "DMA register bitwise AND/OR/XOR (OpSel 0/1/2); OpB is reg or 6-bit imm", [
    F("OpBisConst",      23, 1),
    F("OpSel",           18, 3),
    F("ResultRegIndex",  12, 6),
    F("OpBRegIndex",      6, 6),  # GPR index or 6-bit constant
    F("OpARegIndex",      0, 6),
])
TT_SHIFTDMAREG = TensixOp(0x5C, "DMA register shift (Mode 0=left, 1=right); OpB is reg or 5-bit imm", [
    F("OpBisConst",      23, 1),
    F("Mode",            18, 3),
    F("ResultRegIndex",  12, 6),
    F("OpBRegIndex",      6, 6),  # GPR index or 5-bit constant (low 5 bits used)
    F("OpARegIndex",      0, 6),
])
TT_CMPDMAREG = TensixOp(0x5D, "DMA register unsigned compare (OpSel 0=GT, 1=LT, 2=EQ); result 0/1", [
    F("OpBisConst",      23, 1),
    F("OpSel",           18, 3),
    F("ResultRegIndex",  12, 6),
    F("OpBRegIndex",      6, 6),  # GPR index or 6-bit constant
    F("OpARegIndex",      0, 6),
])
TT_FLUSHDMA = TensixOp(0x46, "Occupy Scalar Unit until selected conditions (C0-C3) clear; 0 defaults to 0xF", [
    F("ConditionMask",    0, 4),
])
TT_DMANOP = TensixOp(0x60, "Scalar unit no-op; occupies one ThCon issue slot")

# -- ADC (address counters) ---------------------------------------------------
TT_SETADC   = TensixOp(0x50, "Set a single ADC dimension to an absolute value", [
    F("CntSetMask",     21, 3), # bitmask: UNP0=1, UNP1=2, PCK0=4
    F("ChannelIndex",   20, 1),
    F("DimensionIndex", 18, 2), # 0=X, 1=Y, 2=Z, 3=W
    F("Value",           0, 18),
])
TT_SETADCXY = TensixOp(0x51, "Set X/Y dimensions for both channels simultaneously", [
    F("CntSetMask", 21, 3),
    F("Ch1_Y",      15, 6),
    F("Ch1_X",      12, 3),
    F("Ch0_Y",       9, 3),
    F("Ch0_X",       6, 3),
    F("BitMask",     0, 6),
])
TT_SETADCZW = TensixOp(0x54, "Set Z/W dimensions for both channels simultaneously", [
    F("CntSetMask", 21, 3),
    F("Ch1_W",      15, 6),
    F("Ch1_Z",      12, 3),
    F("Ch0_W",       9, 3),
    F("Ch0_Z",       6, 3),
    F("BitMask",     0, 6),
])
TT_INCADCZW = TensixOp(0x55, "Increment Z/W dimensions for both channels", [
    F("CntSetMask", 21, 3),
    F("Ch1_W",      15, 6),
    F("Ch1_Z",      12, 3),
    F("Ch0_W",       9, 3),
    F("Ch0_Z",       6, 3),
])
TT_SETADCXX = TensixOp(0x5E, "Set X-dimension start and end for address wrapping", [
    F("CntSetMask", 21, 3),
    F("x_end2",     10, 11),
    F("x_start",     0, 10),
])

# =============================================================================
# SFPU — 32-lane SIMD vector unit, FP32/INT32, LReg[0..7]
# Reads/writes Dest via SFPLOAD/SFPSTORE. Runs at 1.35 GHz on BH.
# =============================================================================

# Common field sets for conciseness
_SIMPLE = lambda: [F("imm12_math",12,12), F("lreg_c",8,4), F("lreg_dest",4,4), F("instr_mod1",0,4)]
_MAD    = lambda: [F("lreg_src_a",16,4), F("lreg_src_b",12,4), F("lreg_src_c",8,4), F("lreg_dest",4,4), F("instr_mod1",0,4)]

# -- data movement: Dest <-> LReg
TT_SFPLOAD  = TensixOp(0x70, "Load 32 elements from Dest into LReg (4 rows x 8 cols)", [
    F("lreg_ind",       20, 4), # target LReg
    F("instr_mod0",     16, 4), # format conversion mode
    F("sfpu_addr_mode", 13, 3),
    F("dest_reg_addr",   0, 13), # Dest row address (added to RWC offset)
])
TT_SFPLOADI = TensixOp(0x71, "Load immediate into all lanes of LReg (mode: 0=BF16, 2=FP16, 4=U16, 6=S15, 8=hi16, 10=lo16)", [
    F("lreg_ind",   20, 4),
    F("instr_mod0", 16, 4), # format selector
    F("imm16",       0, 16),
])
TT_SFPSTORE = TensixOp(0x72, "Store LReg back to Dest (inverse of SFPLOAD)", [
    F("lreg_ind",       20, 4),
    F("instr_mod0",     16, 4),
    F("sfpu_addr_mode", 13, 3),
    F("dest_reg_addr",   0, 13),
])

# -- FP32 immediate arithmetic (MAD sub-unit, 2-cycle)
TT_SFPMULI = TensixOp(0x74, "VD *= BF16ToFP32(imm16)", [
    F("imm16_math", 8, 16), F("lreg_dest", 4, 4), F("instr_mod1", 0, 4),
])
TT_SFPADDI = TensixOp(0x75, "VD += BF16ToFP32(imm16)", [
    F("imm16_math", 8, 16), F("lreg_dest", 4, 4), F("instr_mod1", 0, 4),
])

# -- simple FP32/INT ops (1-cycle)
TT_SFPDIVP2  = TensixOp(0x76, "Multiply/divide by power of 2 via exponent add, or set exponent directly", _SIMPLE())
TT_SFPEXEXP  = TensixOp(0x77, "Extract exponent: VD = VC.Exp (raw or debiased)", _SIMPLE())
TT_SFPEXMAN  = TensixOp(0x78, "Extract mantissa: VD = {0, !Imm1, VC.Mant}", _SIMPLE())
TT_SFPIADD   = TensixOp(0x79, "Integer add: VD = VC +/- VD or VC +/- Imm11, optional CC set", _SIMPLE())
TT_SFPSHFT   = TensixOp(0x7A, "Bit shift: logical/arithmetic left or right", _SIMPLE())
TT_SFPSETCC  = TensixOp(0x7B, "Set per-lane condition flags from VC comparisons (<0, !=0, >=0, ==0)", _SIMPLE())
TT_SFPMOV    = TensixOp(0x7C, "Move: VD=VC, VD=-VC, VD=Config, or VD=PRNG() (mode-dependent)", _SIMPLE())
TT_SFPABS    = TensixOp(0x7D, "Absolute value: VD = Abs(VC)", _SIMPLE())
TT_SFPAND    = TensixOp(0x7E, "Bitwise AND: VD = VB & VC", _SIMPLE())
TT_SFPOR     = TensixOp(0x7F, "Bitwise OR: VD = VB | VC", _SIMPLE())
TT_SFPNOT    = TensixOp(0x80, "Bitwise NOT: VD = ~VC", _SIMPLE())
TT_SFPLZ     = TensixOp(0x81, "Count leading zeros: VD = CLZ(VC)", _SIMPLE())
TT_SFPSETEXP = TensixOp(0x82, "Replace exponent: VD = {VC.Sign, NewExp, VC.Mant}", _SIMPLE())

# -- FP32 FMA / multiply / add (MAD sub-unit, 2-cycle)
TT_SFPMAD = TensixOp(0x84, "Fused multiply-add: VD = VA * +/-VB +/- VC", _MAD())
TT_SFPADD = TensixOp(0x85, "Add: VD = +/-VB +/- VC (VA ignored)", _MAD())
TT_SFPMUL = TensixOp(0x86, "Multiply: VD = VA * +/-VB (VC ignored)", _MAD())

# -- conditional execution / predication
TT_SFPPUSHC = TensixOp(0x87, "Push per-lane flags onto flag stack (for nested if/else)", _SIMPLE())
TT_SFPPOPC  = TensixOp(0x88, "Pop flag stack (restore previous predication state)", _SIMPLE())
TT_SFPSETSGN = TensixOp(0x89, "Set/clear/copy sign bit: Abs(VC), -Abs(VC), or copy VD sign to VC", _SIMPLE())
TT_SFPENCC  = TensixOp(0x8A, "Set UseLaneFlagsForLaneEnable and LaneFlags (controls SIMT predication)", _SIMPLE())
TT_SFPCOMPC = TensixOp(0x8B, "Complement per-lane flags (implements 'else' in SIMT if/else)", _SIMPLE())
TT_SFPTRANSP = TensixOp(0x8C, "Transpose 4x4 groups of SFPU LRegs", [
    F("lreg_dest", 4, 4), F("instr_mod1", 0, 4),
])

# -- bitwise
TT_SFPXOR   = TensixOp(0x8D, "Bitwise XOR: VD ^= VC (self-modifying, source is VD not VB)", _SIMPLE())

# -- type conversion and rounding
TT_SFPSTOCHRND = TensixOp(0x8E, "Stochastic/deterministic rounding + type conversion (FP32<->BF16/FP16/INT8/INT16)", [
    F("rnd_mode",    21, 3), # rounding mode
    F("imm8_math",   16, 8), # shift amount or format selector
    F("lreg_src_b",  12, 4),
    F("lreg_src_c",   8, 4),
    F("lreg_dest",    4, 4),
    F("instr_mod1",   0, 4),
])
TT_SFPNOP  = TensixOp(0x8F, "SFPU no-op; occupies one SFPU issue slot")
TT_SFPCAST = TensixOp(0x90, "Type cast: SignMag32<->FP32, SignMag32<->INT32, IntAbs", [
    F("lreg_src_c", 8, 4), F("lreg_dest", 4, 4), F("instr_mod1", 0, 4),
])
TT_SFPCONFIG = TensixOp(0x91, "Configure SFPU: write LoadMacroConfig, LaneConfig, or constant LRegs (VD selects mode)", [
    F("imm16_math",  8, 16), F("config_dest", 4, 4), F("instr_mod1", 0, 4),
])
TT_SFPSWAP = TensixOp(0x92, "Min/max swap: VD=Min(VC,VD), VC=Max(VC,VD) simultaneously (2-cycle)", _SIMPLE())
TT_SFPLOADMACRO = TensixOp(0x93, "Load from Dest to LReg + schedule 4 pipelined ops across SFPU sub-units", [
    F("lreg_ind",       20, 4),
    F("instr_mod0",     16, 4),
    F("sfpu_addr_mode", 13, 3),
    F("dest_reg_addr",   0, 13),
])
TT_SFPSHFT2 = TensixOp(0x94, "Two-source shift: VD = VB << (VC%32); also lane rotation modes", _SIMPLE())
TT_SFPLUTFP32 = TensixOp(0x95, "FP32 3-piece LUT: VD = LReg[i]*Abs(LReg[3]) + LReg[4+i], i from magnitude", [
    F("lreg_dest", 4, 4), F("instr_mod1", 0, 4),
])

# -- BH-new instructions
TT_SFPGT    = TensixOp(0x97, "Greater-than: set per-lane flags where VD > VC (BH-new)", _SIMPLE())
TT_SFPMUL24 = TensixOp(0x98, "24-bit integer multiply (BH-new)", _MAD())
TT_SFPARECIP = TensixOp(0x99, "Approximate reciprocal: ~1/VC (7-bit), or ~exp(|VC|) with sign copy", _SIMPLE())

# =============================================================================
# Post-init: set .name from module globals (strip TT_ prefix) and bucket by opcode
# =============================================================================
_mod = sys.modules[__name__]
for _n in list(vars(_mod)):
  _o = getattr(_mod, _n)
  if isinstance(_o, TensixOp):
    _o.name = _n.removeprefix('TT_')
    _TENSIX_BY_OPCODE[_o.opcode] = _o
