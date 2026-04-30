from dataclasses import dataclass
from functools import partial
import struct

@dataclass(frozen=True)
class Insn:
  word: int
  def __int__(self): return self.word

@dataclass(frozen=True)
class RiscVInsn(Insn): pass

@dataclass(frozen=True)
class TensixInsn(Insn): pass

# -- field validation ----------------------------------------------------------
def R(v):
  """Validate register index (0-31)."""
  if not 0 <= v <= 31: raise ValueError(f"register {v} not in 0..31")
  return v
def U(v, w):
  """Validate unsigned field fits in w bits."""
  if not 0 <= v < (1 << w): raise ValueError(f"{v} doesn't fit in {w}-bit unsigned field")
  return v
def S(v, w):
  """Validate signed field fits in w bits, return masked."""
  if not -(1 << (w-1)) <= v < (1 << (w-1)): raise ValueError(f"{v} doesn't fit in {w}-bit signed field")
  return v & ((1 << w) - 1)

def bits(v, hi, lo=None):
  if lo is None: lo = hi
  return (v >> lo) & ((1 << (hi - lo + 1)) - 1)

# -- encoding formats ----------------------------------------------------------
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

# -- RV32I base ----------------------------------------------------------------
ADD  = partial(_r, 0x33, 0, 0x00); SUB  = partial(_r, 0x33, 0, 0x20)
SLL  = partial(_r, 0x33, 1, 0x00); SLT  = partial(_r, 0x33, 2, 0x00)
SLTU = partial(_r, 0x33, 3, 0x00); XOR  = partial(_r, 0x33, 4, 0x00)
SRL  = partial(_r, 0x33, 5, 0x00)
# rare: SRA  = partial(_r, 0x33, 5, 0x20)
OR   = partial(_r, 0x33, 6, 0x00); AND  = partial(_r, 0x33, 7, 0x00)
ADDI  = partial(_i, 0x13, 0)
# rare: SLTI  = partial(_i, 0x13, 2)
SLTIU = partial(_i, 0x13, 3); XORI  = partial(_i, 0x13, 4)
ORI   = partial(_i, 0x13, 6); ANDI  = partial(_i, 0x13, 7)
SLLI  = partial(_i, 0x13, 1); SRLI  = partial(_i, 0x13, 5)
SRAI  = lambda rd, rs1, shamt: _i(0x13, 5, rd, rs1, U(shamt,5) | 0x400)
# rare: LB  = partial(_i, 0x03, 0); LH  = partial(_i, 0x03, 1)
LW  = partial(_i, 0x03, 2); LBU = partial(_i, 0x03, 4); LHU = partial(_i, 0x03, 5)
SB = partial(_s, 0x23, 0); SH = partial(_s, 0x23, 1); SW = partial(_s, 0x23, 2)
BEQ  = partial(_b, 0x63, 0); BNE  = partial(_b, 0x63, 1)
BLT  = partial(_b, 0x63, 4); BGE  = partial(_b, 0x63, 5)
BLTU = partial(_b, 0x63, 6); BGEU = partial(_b, 0x63, 7)
LUI   = partial(_u, 0x37); AUIPC = partial(_u, 0x17)
JAL  = partial(_j, 0x6F); JALR = partial(_i, 0x67, 0)
# rare: ECALL  = lambda: _i(0x73, 0, 0, 0, 0)
# rare: EBREAK = lambda: _i(0x73, 0, 0, 0, 1)
FENCE  = lambda: _i(0x0F, 0, 0, 0, 0xFF)
# Zicsr
# rare: CSRRW  = lambda rd, rs1, csr: _i(0x73, 1, rd, rs1, U(csr,12))
CSRRS  = lambda rd, rs1, csr: _i(0x73, 2, rd, rs1, U(csr,12))
CSRRC  = lambda rd, rs1, csr: _i(0x73, 3, rd, rs1, U(csr,12))
# rare: CSRRWI = lambda rd, uimm, csr: _i(0x73, 5, rd, U(uimm,5), U(csr,12))
# rare: CSRRSI = lambda rd, uimm, csr: _i(0x73, 6, rd, U(uimm,5), U(csr,12))
# rare: CSRRCI = lambda rd, uimm, csr: _i(0x73, 7, rd, U(uimm,5), U(csr,12))

# -- M extension ---------------------------------------------------------------
MUL    = partial(_r, 0x33, 0, 0x01)
# rare: MULH   = partial(_r, 0x33, 1, 0x01)
# rare: MULHSU = partial(_r, 0x33, 2, 0x01)
MULHU  = partial(_r, 0x33, 3, 0x01)
# rare: DIV    = partial(_r, 0x33, 4, 0x01)
DIVU   = partial(_r, 0x33, 5, 0x01)
# rare: REM    = partial(_r, 0x33, 6, 0x01)
REMU   = partial(_r, 0x33, 7, 0x01)

# -- Zaamo (no lr/sc) ----------------------------------------------------------
# rare: Tensix uses semaphores instead of RISC-V atomics; compiler never emits these
# rare: AMOADD_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x00, aq, rl, rs2, rs1, 2, rd)
# rare: AMOSWAP_W = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x01, aq, rl, rs2, rs1, 2, rd)
# rare: AMOXOR_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x04, aq, rl, rs2, rs1, 2, rd)
# rare: AMOOR_W   = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x08, aq, rl, rs2, rs1, 2, rd)
# rare: AMOAND_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x0C, aq, rl, rs2, rs1, 2, rd)
# rare: AMOMIN_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x10, aq, rl, rs2, rs1, 2, rd)
# rare: AMOMAX_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x14, aq, rl, rs2, rs1, 2, rd)
# rare: AMOMINU_W = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x18, aq, rl, rs2, rs1, 2, rd)
# rare: AMOMAXU_W = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x1C, aq, rl, rs2, rs1, 2, rd)

# -- Zba -----------------------------------------------------------------------
SH1ADD = partial(_r, 0x33, 2, 0x10)
SH2ADD = partial(_r, 0x33, 4, 0x10)
SH3ADD = partial(_r, 0x33, 6, 0x10)

# -- Zbb + Zbkb ----------------------------------------------------------------
# rare: ANDN = partial(_r, 0x33, 7, 0x20); ORN  = partial(_r, 0x33, 6, 0x20)
# rare: XNOR = partial(_r, 0x33, 4, 0x20)
# rare: MAX  = partial(_r, 0x33, 6, 0x05)
MAXU = partial(_r, 0x33, 7, 0x05)
MIN  = partial(_r, 0x33, 4, 0x05); MINU = partial(_r, 0x33, 5, 0x05)
# rare: ROL  = partial(_r, 0x33, 1, 0x30); ROR  = partial(_r, 0x33, 5, 0x30)
# rare: RORI   = lambda rd, rs1, shamt: _i(0x13, 5, rd, rs1, U(shamt,5) | 0x600)
# rare: CLZ    = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x600)
CTZ    = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x601)
# rare: CPOP   = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x602)
SEXT_B = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x604)
SEXT_H = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x605)
ZEXT_H = lambda rd, rs1: _r(0x33, 4, 0x04, rd, rs1, 0)
# rare: REV8   = lambda rd, rs1: _i(0x13, 5, rd, rs1, 0x698)
# rare: ORC_B  = lambda rd, rs1: _i(0x13, 5, rd, rs1, 0x287)
# rare: PACK   = partial(_r, 0x33, 4, 0x04)
# rare: BREV8  = lambda rd, rs1: _i(0x13, 5, rd, rs1, 0x687)
# rare: GREVI  = lambda rd, rs1, shamt: _i(0x13, 5, rd, rs1, U(shamt,5) | 0x680)

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
# rare: SGTZ   = lambda rd, rs: SLT(rd, zero, rs)
# rare: SLTZ   = lambda rd, rs: SLT(rd, rs, zero)
BEQZ   = lambda rs, imm: BEQ(rs, zero, imm)
BNEZ   = lambda rs, imm: BNE(rs, zero, imm)
BLEZ   = lambda rs, imm: BGE(zero, rs, imm)
BGEZ   = lambda rs, imm: BGE(rs, zero, imm)
BLTZ   = lambda rs, imm: BLT(rs, zero, imm)
BGTZ   = lambda rs, imm: BLT(zero, rs, imm)
J      = lambda imm: JAL(zero, imm)
JR     = lambda rs: JALR(zero, rs, 0)
RET    = lambda: JALR(zero, ra, 0)
# rare: CALL   = lambda imm: JAL(ra, imm)
ZEXT_B = lambda rd, rs: ANDI(rd, rs, 0xFF)

def LI32(rd, imm):
  imm &= 0xFFFFFFFF
  imm_s = imm if imm < 0x80000000 else imm - 0x100000000
  hi = (imm_s + 0x800) & 0xFFFFF000
  hi_s = hi if hi < 0x80000000 else hi - 0x100000000
  lo = imm_s - hi_s
  if hi == 0:
    return [ADDI(rd, zero, lo)]
  return [LUI(rd, hi), ADDI(rd, rd, lo)]

# -- RISC-V decoder ------------------------------------------------------------
# Raw 32-bit word -> RvDecoded(name, rd, rs1, ...).  Covers the RV32IMZba/Zbb
# subset implemented by the emulator in emu/rv.py.
@dataclass(frozen=True)
class RvDecoded:
  name: str
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

_RV_DECODE = [
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
  (0xFE00707F, 0x02000033, 'MUL',    'R'),
  (0xFE00707F, 0x02001033, 'MULH',   'R'),
  (0xFE00707F, 0x02002033, 'MULHSU', 'R'),
  (0xFE00707F, 0x02003033, 'MULHU',  'R'),
  (0xFE00707F, 0x02004033, 'DIV',    'R'),
  (0xFE00707F, 0x02005033, 'DIVU',   'R'),
  (0xFE00707F, 0x02006033, 'REM',    'R'),
  (0xFE00707F, 0x02007033, 'REMU',   'R'),
  (0xFE00707F, 0x20002033, 'SH1ADD', 'R'),
  (0xFE00707F, 0x20004033, 'SH2ADD', 'R'),
  (0xFE00707F, 0x20006033, 'SH3ADD', 'R'),
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
  (0x0000707F, 0x00000013, 'ADDI',   'I'),
  (0x0000707F, 0x00002013, 'SLTI',   'I'),
  (0x0000707F, 0x00003013, 'SLTIU',  'I'),
  (0x0000707F, 0x00004013, 'XORI',   'I'),
  (0x0000707F, 0x00006013, 'ORI',    'I'),
  (0x0000707F, 0x00007013, 'ANDI',   'I'),
  (0xFFF0707F, 0x60001013, 'CLZ',    'Ish'),
  (0xFFF0707F, 0x60101013, 'CTZ',    'Ish'),
  (0xFFF0707F, 0x60201013, 'CPOP',   'Ish'),
  (0xFFF0707F, 0x60401013, 'SEXT_B', 'Ish'),
  (0xFFF0707F, 0x60501013, 'SEXT_H', 'Ish'),
  (0xFFF0707F, 0x28705013, 'ORC_B',  'Ish'),
  (0xFFF0707F, 0x69805013, 'REV8',   'Ish'),
  (0xFE00707F, 0x00001013, 'SLLI',   'Ish'),
  (0xFE00707F, 0x00005013, 'SRLI',   'Ish'),
  (0xFE00707F, 0x40005013, 'SRAI',   'Ish'),
  (0xFE00707F, 0x60005013, 'RORI',   'Ish'),
  (0x0000707F, 0x00000003, 'LB',     'I'),
  (0x0000707F, 0x00001003, 'LH',     'I'),
  (0x0000707F, 0x00002003, 'LW',     'I'),
  (0x0000707F, 0x00004003, 'LBU',    'I'),
  (0x0000707F, 0x00005003, 'LHU',    'I'),
  (0x0000707F, 0x00000023, 'SB',     'S'),
  (0x0000707F, 0x00001023, 'SH',     'S'),
  (0x0000707F, 0x00002023, 'SW',     'S'),
  (0x0000707F, 0x00000063, 'BEQ',    'B'),
  (0x0000707F, 0x00001063, 'BNE',    'B'),
  (0x0000707F, 0x00004063, 'BLT',    'B'),
  (0x0000707F, 0x00005063, 'BGE',    'B'),
  (0x0000707F, 0x00006063, 'BLTU',   'B'),
  (0x0000707F, 0x00007063, 'BGEU',   'B'),
  (0x0000007F, 0x00000037, 'LUI',    'U'),
  (0x0000007F, 0x00000017, 'AUIPC',  'U'),
  (0x0000007F, 0x0000006F, 'JAL',    'J'),
  (0x0000707F, 0x00000067, 'JALR',   'I'),
  (0x0000707F, 0x00001073, 'CSRRW',  'CSR'),
  (0x0000707F, 0x00002073, 'CSRRS',  'CSR'),
  (0x0000707F, 0x00003073, 'CSRRC',  'CSR'),
  (0x0000707F, 0x00005073, 'CSRRWI', 'CSR'),
  (0x0000707F, 0x00006073, 'CSRRSI', 'CSR'),
  (0x0000707F, 0x00007073, 'CSRRCI', 'CSR'),
  (0x0000007F, 0x0000000F, 'FENCE',  'NONE'),
]

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

# -- .ttinsn encoding ----------------------------------------------------------
# Encodes a 32-bit Tensix instruction into the .ttinsn custom RISC-V instruction.
# The encoding rotates the Tensix word left by 2 bits. The hardware decodes the
# RV32 instruction, rotates right 2, and pushes the result into the Tensix
# instruction FIFO at INSTRN_BUF_BASE (0xFFE40000).
def TTINSN(imm32):
  assert imm32 < 0xC0000000, f".ttinsn requires imm32 < 0xC0000000, got 0x{imm32:08x}"
  return RiscVInsn(((imm32 << 2) | (imm32 >> 30)) & 0xFFFFFFFF)

# ==============================================================================
# Tensix coprocessor ISA — opcode in bits[31:24], params in bits[23:0]
#
# Each Tensix instruction is a 32-bit word: [opcode:8][params:24].
# Instructions are issued to the Tensix coprocessor via TTINSN, which rotates
# the 32-bit word so it fits in a RISC-V custom encoding slot.
#
# The Tensix core has several functional units:
#   - Matrix engine (FPU): matmul, element-wise ops, convolutions, pooling
#   - SFPU (vector unit): per-element scalar FP ops on LREG files
#   - Packer/Unpacker: move data between L1 and src/dst register files
#   - Sync unit: mutexes, semaphores, stalls for cross-unit synchronization
#   - Config unit: read/write configuration registers
#   - Scalar/DMA unit (ThCon): DMA register ops, indirect loads/stores
# ==============================================================================
def _tt(op, p=0):
  if p != (p & 0xFFFFFF): raise ValueError(f"Tensix params overflow: 0x{p:x} doesn't fit in 24 bits")
  return TensixInsn((op << 24) | p)

# -- flow control / MOP / replay ----------------------------------------------
# MOP (Macro-OP) executes a predefined sequence of micro-ops in a loop.
# REPLAY re-executes instructions from an instruction buffer.
TT_NOP     = lambda: _tt(0x02)  # no-op, occupies one Tensix issue slot
TT_MOP     = lambda mop_type, loop_count, zmask_lo16_or_loop_count: _tt(0x01, U(mop_type,1)<<23 | U(loop_count,7)<<16 | U(zmask_lo16_or_loop_count,16))
  # mop_type: 0=MOP_A, 1=MOP_B (selects which macro-op template)
  # loop_count: number of outer loop iterations (7b, 0-127)
  # zmask_lo16_or_loop_count: low 16 bits of zero-mask OR inner loop count
# rare: TT_MOP_CFG = lambda zmask_hi16: _tt(0x03, U(zmask_hi16,16))
  # zmask_hi16: upper 16 bits of the 32-bit zero-column mask for MOP
TT_REPLAY  = lambda start_idx, len, execute_while_loading=0, load_mode=0: _tt(0x04, U(start_idx,10)<<14 | U(len,10)<<4 | U(execute_while_loading,1)<<1 | U(load_mode,1))
  # start_idx: starting instruction index in the replay buffer (10b)
  # len: number of instructions to replay (10b)
  # execute_while_loading: 1=begin execution before buffer is fully loaded
  # load_mode: replay buffer load mode
# rare: TT_RESOURCEDECL = lambda linger_time, resources, op_class: _tt(0x05, U(linger_time,11)<<13 | U(resources,9)<<4 | U(op_class,4))
  # linger_time: how long to hold resources after op completes (11b)
  # resources: bitmask of hardware resources needed (9b)
  # op_class: class of operation for scheduling (4b)
# -- sync unit -----------------------------------------------------------------
# Synchronization primitives: mutexes, semaphores, stalls, and stream waits.
# Used to coordinate between Tensix functional units and external streams.
TT_ATGETM     = lambda mutex_index: _tt(0xA0, U(mutex_index,24))
  # Acquire mutex. mutex_index: which mutex to lock (blocks until acquired)
TT_ATRELM     = lambda mutex_index: _tt(0xA1, U(mutex_index,24))
  # Release mutex. mutex_index: which mutex to unlock
TT_STALLWAIT  = lambda stall_res, wait_res: _tt(0xA2, U(stall_res,9)<<15 | U(wait_res,15))
  # Block specific units until conditions are met. Does NOT block the issuing thread
  # immediately — the thread keeps running until it tries to issue a blocked instruction.
  # stall_res (BlockMask, 9b): which instruction types to block
  #   B0=Misc/Mover/ThCon/Pack/Unpack, B1=Sync, B2=Pack, B3=Unpack, B4=Mover,
  #   B5=ThCon, B6=FPU, B7=Config, B8=SFPU. Default if 0: B6 (FPU only).
  # wait_res (ConditionMask, 15b): which conditions must ALL be met to unblock
TT_SEMINIT    = lambda max_value, init_value, sem_sel: _tt(0xA3, U(max_value,4)<<20 | U(init_value,4)<<16 | U(sem_sel,8)<<2)
  # Initialize a semaphore. max_value: saturation value (4b)
  # init_value: starting count (4b), sem_sel: semaphore index (8b)
TT_SEMPOST    = lambda sem_sel: _tt(0xA4, U(sem_sel,8)<<2)
  # Increment semaphore count. sem_sel: semaphore index
TT_SEMGET     = lambda sem_sel: _tt(0xA5, U(sem_sel,8)<<2)
  # Decrement semaphore count. sem_sel: semaphore index
TT_SEMWAIT    = lambda stall_res, sem_sel, wait_sem_cond: _tt(0xA6, U(stall_res,9)<<15 | U(sem_sel,8)<<2 | U(wait_sem_cond,2))
  # Block instructions (per stall_res) until semaphore conditions are met.
  # stall_res (BlockMask, 9b): same as STALLWAIT. Default if 0: B6 (FPU).
  # sem_sel (SemaphoreMask, 8b): bitmask selecting which semaphores to check
  # wait_sem_cond (ConditionMask, 2b): C0=wait while any selected has Value==0,
  #   C1=wait while any selected has Value>=Max. Both can be set simultaneously.
# rare: TT_STREAMWAIT = lambda stall_res, target_value, target_sel, wait_stream_sel: _tt(0xA7, U(stall_res,9)<<15 | U(target_value,10)<<4 | U(target_sel,1)<<3 | U(wait_stream_sel,2))
  # Block instructions until a NoC Overlay stream condition is met (BH-new).
  # stall_res (BlockMask, 9b): same as STALLWAIT
  # target_value (TargetValueLo, 10b): low 10 bits of target (hi bits from ThreadConfig)
  # target_sel (ConditionIndex, 1b): 0=wait on phase count, 1=wait on msg count
  # wait_stream_sel (StreamSelect, 2b): which stream to monitor
# -- config unit ---------------------------------------------------------------
# Read/write Tensix configuration registers (CfgRegs). These control data
# formats, tile dimensions, math modes, and other per-operation settings.
TT_WRCFG        = lambda GprAddress, wr128b, CfgReg: _tt(0xB0, U(GprAddress,6)<<16 | U(wr128b,1)<<15 | U(CfgReg,11))
  # Write GPR data to a config register. GprAddress: source GPR (6b)
  # wr128b: 1=write 128 bits (4 consecutive GPRs), 0=write 32 bits
  # CfgReg: destination config register address (11b)
TT_RDCFG        = lambda GprAddress, CfgReg: _tt(0xB1, U(GprAddress,6)<<16 | U(CfgReg,11))
  # Read config register into GPR. GprAddress: dest GPR, CfgReg: source config reg
TT_SETC16       = lambda setc16_reg, setc16_value: _tt(0xB2, U(setc16_reg,8)<<16 | U(setc16_value,16))
  # Write a 16-bit immediate directly to a config register
  # setc16_reg: config register index (8b), setc16_value: immediate (16b)
# rare: TT_RMWCIB0      = lambda Mask, Data, CfgRegAddr: _tt(0xB3, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
# rare: TT_RMWCIB1      = lambda Mask, Data, CfgRegAddr: _tt(0xB4, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
# rare: TT_RMWCIB2      = lambda Mask, Data, CfgRegAddr: _tt(0xB5, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
# rare: TT_RMWCIB3      = lambda Mask, Data, CfgRegAddr: _tt(0xB6, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
  # Read-Modify-Write Config register, byte 0/1/2/3 respectively.
  # Mask: which bits to modify (8b), Data: new bit values (8b)
  # CfgRegAddr: config register address (8b)
# rare: TT_STREAMWRCFG  = lambda stream_id_sel, StreamRegAddr, CfgReg: _tt(0xB7, U(stream_id_sel,2)<<21 | U(StreamRegAddr,10)<<11 | U(CfgReg,11))
  # Write from a stream register into a config register
  # stream_id_sel: stream selector (2b), StreamRegAddr: stream reg (10b)
# rare: TT_CFGSHIFTMASK = lambda disable_mask_on_old_val, operation, mask_width, right_cshift_amt, scratch_sel, CfgReg: _tt(0xB8,
#   U(disable_mask_on_old_val,1)<<23 | U(operation,3)<<20 | U(mask_width,5)<<15 | U(right_cshift_amt,5)<<10 | U(scratch_sel,2)<<8 | U(CfgReg,8))
  # Shift-and-mask operation on a config register (for bitfield insertion/extraction)
# -- matrix unit / FPU ---------------------------------------------------------
# The matrix engine performs tile-level math: matmul, element-wise ops,
# convolutions, and pooling. It reads from SrcA/SrcB register files and
# writes to the Dest (accumulator) register file.
#
# Common args across matrix instructions:
#   clear_dvalid: clear data-valid flags (2b); signals source data consumed
#   addr_mode: addressing mode for dest register file (2-3b)
#   dst: destination register address in Dest accumulator
#   dest_accum_en: 1=accumulate into dest, 0=overwrite
#   instr_mod19: instruction modifier bits (math mode, format control)
TT_ZEROACC   = lambda clear_mode, use_32_bit_mode, clear_zero_flags, addr_mode, where: _tt(0x10,
  U(clear_mode,5)<<19 | U(use_32_bit_mode,1)<<18 | U(clear_zero_flags,1)<<17 | U(addr_mode,3)<<14 | U(where,14))
  # Zero out accumulator (Dest) registers
  # clear_mode: which rows/tiles to clear (5b)
  # use_32_bit_mode: 1=clear as 32-bit, 0=clear as configured format
  # clear_zero_flags: 1=also clear associated zero-detect flags
  # where: address/range in Dest to clear (14b)
TT_ZEROSRC   = lambda zero_val, write_mode, bank_mask, src_mask: _tt(0x11, U(zero_val,20)<<4 | U(write_mode,1)<<3 | U(bank_mask,1)<<2 | U(src_mask,2))
  # Zero out SrcA/SrcB register banks
  # zero_val: value to write (usually 0) (20b)
  # write_mode: 0=zero, 1=write zero_val pattern
  # bank_mask: which bank, src_mask: 0=none,1=SrcA,2=SrcB,3=both
# rare: TT_MOVA2D    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x12, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
  # Move data from SrcA to Dest. src: SrcA register index (6b)
  # dest_32b_lo: select low 32b of dest row; instr_mod: format conversion mode
TT_MOVB2D    = lambda dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst: _tt(0x13, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(movb2d_instr_mod,3)<<11 | U(dst,11))
  # Move data from SrcB to Dest. src: SrcB register index (6b)
TT_TRNSPSRCA = lambda: _tt(0x14)   # dead — SrcA transpose not functional on Blackhole
TT_RAREB     = lambda: _tt(0x15)   # dead — not used in Blackhole
TT_TRNSPSRCB = lambda: _tt(0x16)   # Transpose SrcB rows 16-31 in-place (16x16 transpose)
# rare: TT_SHIFTXA   = lambda log2_amount2, shift_mode: _tt(0x17, U(log2_amount2,22)<<2 | U(shift_mode,2))
  # Shift SrcA data. log2_amount2: shift amount (22b encoding)
  # shift_mode: type of shift (row shift, etc.)
# rare: TT_SHIFTXB   = lambda addr_mode, rot_shift, shift_row: _tt(0x18, U(addr_mode,3)<<14 | U(rot_shift,4)<<10 | U(shift_row,10))
  # Shift/rotate SrcB data. rot_shift: rotation amount (4b)
  # shift_row: which row to shift (10b)
# rare: legacy Grayskull halo/conv mask instructions — no BH LLK code path
# rare: TT_SETASHRMH0 = lambda reg_mask, halo_mask: _tt(0x1A, U(reg_mask,23)<<1 | U(halo_mask,1))
# rare: TT_SETASHRMH1 = lambda reg_mask, halo_mask: _tt(0x1B, U(reg_mask,23)<<1 | U(halo_mask,1))
# rare: TT_SETASHRMV  = lambda reg_mask2: _tt(0x1C, U(reg_mask2,24))
# rare: TT_SETASHRMH  = lambda reg_mask, halo_mask: _tt(0x1E, U(reg_mask,23)<<1 | U(halo_mask,1))
# rare: TT_SETPKEDGOF = lambda y_end, y_start, x_end, x_start: _tt(0x1D, U(y_end,4)<<12 | U(y_start,4)<<8 | U(x_end,4)<<4 | U(x_start,4))
# rare: TT_CLREXPHIST = lambda: _tt(0x21)
TT_CONV3S1  = lambda clear_dvalid, rotate_weights, addr_mode, dst: _tt(0x22, U(clear_dvalid,2)<<22 | U(rotate_weights,5)<<17 | U(addr_mode,3)<<14 | U(dst,14))
  # dead — neutered on BH, computes Dst += 0 only (was 3x3 conv stride 1 on GS)
TT_CONV3S2  = lambda clear_dvalid, rotate_weights, addr_mode, dst: _tt(0x23, U(clear_dvalid,2)<<22 | U(rotate_weights,5)<<17 | U(addr_mode,3)<<14 | U(dst,14))
  # dead — neutered on BH, computes Dst += 0 only (was 3x3 conv stride 2 on GS)
TT_MFCONV3S1 = lambda clear_dvalid, rotate_weights, addr_mode, dst: _tt(0x24, U(clear_dvalid,2)<<22 | U(rotate_weights,5)<<17 | U(addr_mode,3)<<14 | U(dst,14))
  # dead — neutered on BH, computes Dst += 0 only (was multi-filter 3x3 conv on GS)
TT_APOOL3S1 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x25, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
  # dead — neutered on BH, computes Dst += 0 only (was avg pool 3x3 stride 1 on GS)
TT_MVMUL    = lambda clear_dvalid, instr_mod19, addr_mode, dst: _tt(0x26, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(addr_mode,2)<<14 | U(dst,10))
  # Matrix-vector multiply (SrcA * SrcB -> Dest)
# rare: TT_ELWMUL   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x27, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
  # Element-wise multiply — experimental LLK only, production uses SFPU
TT_ELWADD   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x28, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
  # Element-wise add (SrcA + SrcB -> Dest)
# rare: TT_DOTPV    = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x29, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
  # Legacy matmul — prefer MVMUL. Functionally identical.
TT_MPOOL3S2 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x2A, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
  # dead — neutered on BH, behaves like GMPOOL on all-zero SrcA (was max pool 3x3 s2)
# rare: TT_ELWSUB   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x30, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
  # Element-wise subtract — experimental LLK only, production uses SFPU
TT_MPOOL3S1 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x31, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
  # dead — neutered on BH, behaves like GMPOOL on all-zero SrcA (was max pool 3x3 s1)
TT_APOOL3S2 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x32, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
  # dead — neutered on BH, computes Dst += 0 only (was avg pool 3x3 stride 2 on GS)
TT_GMPOOL   = lambda clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst: _tt(0x33, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(pool_addr_mode,4)<<15 | U(max_pool_index_en,1)<<14 | U(dst,14))
  # Global max pooling
# rare: TT_GAPOOL   = lambda clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst: _tt(0x34, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(pool_addr_mode,4)<<15 | U(max_pool_index_en,1)<<14 | U(dst,14))
  # Global average pooling — no BH LLK code path
# rare: TT_GATESRCRST  = lambda reset_srcb_gate_control, reset_srca_gate_control: _tt(0x35, U(reset_srcb_gate_control,1)<<1 | U(reset_srca_gate_control,1))
  # Reset gating control for SrcA/SrcB (used in power management)
TT_CLEARDVALID = lambda cleardvalid, reset: _tt(0x36, U(cleardvalid,2)<<22 | U(reset,22))
  # Clear data-valid flags on source registers. cleardvalid: which to clear (2b)
  # reset: reset value/address (22b)
# -- read/write counters -------------------------------------------------------
# RWCs (Read/Write Counters) are offsets added to instruction addresses to
# auto-stride through SrcA, SrcB, and Dst rows. Updated between fidelity phases
# or between tiles to advance the register file window.
TT_SETRWC   = lambda clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask: _tt(0x37, U(clear_ab_vld,2)<<22 | U(rwc_cr,4)<<18 | U(rwc_d,4)<<14 | U(rwc_b,4)<<10 | U(rwc_a,4)<<6 | U(BitMask,6))
  # Set RWC values. clear_ab_vld: clear SrcA/SrcB valid flags (2b)
  # rwc_cr/rwc_d/rwc_b/rwc_a: new counter values for CR/Dst/SrcB/SrcA
  # BitMask: which counters to update (6b bitmask)
TT_INCRWC   = lambda rwc_cr, rwc_d, rwc_b, rwc_a: _tt(0x38, U(rwc_cr,3)<<18 | U(rwc_d,4)<<14 | U(rwc_b,4)<<10 | U(rwc_a,4)<<6)
  # Increment RWCs by specified amounts. Used between fidelity phases.
# rare: TT_SETIBRWC = lambda rwc_cr, rwc_bias, set_inc_ctrl: _tt(0x39, U(rwc_cr,3)<<18 | U(rwc_bias,12)<<6 | U(set_inc_ctrl,6))
  # Set RWC bias and increment control. rwc_bias: base offset (12b)
  # set_inc_ctrl: auto-increment behavior selector (6b)
# -- data moves (between register files) ---------------------------------------
# Move data between SrcA, SrcB, and Dst register files. These are used for
# transpose, data reformatting, and feeding SFPU results back into FPU inputs.
# rare: TT_MOVD2A    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x08, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
  # Dst → SrcA. 1 or 4 aligned rows, 2-cycle latency. Requires manual STALLWAIT.
# rare: TT_MOVDBGA2D = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x09, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
  # SrcA → Dst (debug variant of MOVA2D, skips SrcA bank ownership check)
TT_MOVD2B    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x0A, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
  # Dst → SrcB. 1 or 4 aligned rows, 3-cycle latency. Requires manual STALLWAIT.
  # Used in tile transpose: MOVD2B to SrcB[16:31], TRNSPSRCB, then MOVB2D back.
# rare: TT_MOVB2A    = lambda srca, addr_mode, instr_mod, srcb: _tt(0x0B, U(srca,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(srcb,12))
  # SrcB → SrcA. Raw 19-bit copy, no format conversion. 4-cycle latency.
# rare: TT_MOVDBGB2D = lambda dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst: _tt(0x0C, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(movb2d_instr_mod,3)<<11 | U(dst,11))
  # SrcB → Dst (debug variant of MOVB2D, skips SrcB bank ownership check)
# rare: TT_SETDVALID = lambda setvalid: _tt(0x57, U(setvalid,24))
  # Set data-valid flags — no BH LLK code path
# -- packer / unpacker / mover -------------------------------------------------
# Packers move data from Dst → L1 (with format conversion, ReLU, edge masking).
# Unpackers move data from L1 → SrcA/SrcB (with format conversion, decompress).
# The Mover (XMOV) handles L1 → L1 block moves for stream management.
# rare: TT_XMOV = lambda Mov_block_selection, Last: _tt(0x40, U(Mov_block_selection,1)<<23 | U(Last,23))
  # L1-to-L1 block mover — no BH LLK code path
TT_PACR = lambda CfgContext, RowPadZero, DstAccessMode, AddrMode, AddrCntContext, ZeroWrite, ReadIntfSel, OvrdThreadId, Concat, CtxtCtrl, Flush, Last: _tt(0x41,
  U(CfgContext,3)<<21 | U(RowPadZero,3)<<18 | U(DstAccessMode,1)<<17 | U(AddrMode,2)<<15 | U(AddrCntContext,2)<<13 | U(ZeroWrite,1)<<12 | U(ReadIntfSel,4)<<8 | U(OvrdThreadId,1)<<7 | U(Concat,3)<<4 | U(CtxtCtrl,2)<<2 | U(Flush,1)<<1 | U(Last,1))
  # Pack one tile face (16 rows) from Dst → L1 via format conversion pipeline.
  # CfgContext: config context for format/addr settings (3b)
  # RowPadZero: pad rows with zeros (3b); DstAccessMode: 0=16b, 1=32b
  # ZeroWrite: write zeros instead of data; ReadIntfSel: which Dst read port (4b)
  # Concat: concatenation mode for multi-face packing (3b)
  # Flush: flush packer pipeline; Last: signal tile pack complete
TT_UNPACR = lambda Unpack_block_selection, AddrMode, CfgContextCntInc, CfgContextId, AddrCntContextId, OvrdThreadId, SetDatValid, srcb_bcast, ZeroWrite2, AutoIncContextID, RowSearch, SearchCacheFlush, Last: _tt(0x42,
  U(Unpack_block_selection,1)<<23 | U(AddrMode,8)<<15 | U(CfgContextCntInc,2)<<13 | U(CfgContextId,3)<<10 | U(AddrCntContextId,2)<<8 | U(OvrdThreadId,1)<<7 | U(SetDatValid,1)<<6 | U(srcb_bcast,1)<<5 | U(ZeroWrite2,1)<<4 | U(AutoIncContextID,1)<<3 | U(RowSearch,1)<<2 | U(SearchCacheFlush,1)<<1 | U(Last,1))
  # Unpack L1 data → SrcA or SrcB with format conversion.
  # Unpack_block_selection: 0=SrcA (unpacker 0), 1=SrcB (unpacker 1)
  # AddrMode: complex address mode encoding (8b, includes tile face selection)
  # SetDatValid: 1=flip SrcA/SrcB bank ownership (transfers to FPU)
  # srcb_bcast: 1=broadcast SrcB row to all columns
  # Last: signal unpack complete for this tile
TT_UNPACR_NOP = lambda Unpacker_Select, Stream_Id, Msg_Clr_Cnt, Set_Dvalid, Clr_to1_fmt_Ctrl, Stall_Clr_Cntrl, Bank_Clr_Ctrl, Src_ClrVal_Ctrl, Unpack_Pop: _tt(0x43,
  U(Unpacker_Select,1)<<23 | U(Stream_Id,7)<<16 | U(Msg_Clr_Cnt,4)<<12 | U(Set_Dvalid,4)<<8 | U(Clr_to1_fmt_Ctrl,2)<<6 | U(Stall_Clr_Cntrl,1)<<5 | U(Bank_Clr_Ctrl,1)<<4 | U(Src_ClrVal_Ctrl,2)<<2 | U(Unpack_Pop,2))
  # Unpacker no-op with side effects: clear stream msg counts, set dvalid,
  # clear banks, pop stream messages without actually unpacking data.
  # Used for stream management and synchronization.
# rare: TT_PACR_SETREG = lambda Push, ModeSel, Unused, DisableStall, AddrSel, StreamId, Flush, Last: _tt(0x4A,
#   U(Push,1)<<23 | U(ModeSel,1)<<22 | U(Unused,10)<<12 | U(DisableStall,2)<<10 | U(AddrSel,2)<<8 | U(StreamId,6)<<2 | U(Flush,1)<<1 | U(Last,1))
  # Configure packer stream destination — no BH LLK code path
# -- scalar unit (ThCon / DMA) -------------------------------------------------
# The Scalar Unit (ThCon = Thread Controller) provides integer ALU ops on
# 16-bit DMA registers, indirect memory access, and configuration register
# writes. It's the Tensix control plane — not a user-facing compute path.
# Each thread has 64 x 16-bit DMA registers (RegIndex 0-63).
# rare: TT_RSTDMA    = lambda: _tt(0x44)  # Reset DMA engine state
TT_SETDMAREG = lambda Payload_SigSelSize, Payload_SigSel, SetSignalsMode, RegIndex16b: _tt(0x45, U(Payload_SigSelSize,2)<<22 | U(Payload_SigSel,14)<<8 | U(SetSignalsMode,1)<<7 | U(RegIndex16b,7))
  # Load an immediate value into a DMA register, or set signal/control bits.
  # Payload_SigSelSize: 0=16b payload, 1=signal select, 2=extended
  # Payload_SigSel: immediate value or signal selector (14b)
  # SetSignalsMode: 1=set signals mode; RegIndex16b: target register (7b, 0-63)
# rare: TT_FLUSHDMA  = lambda FlushSpec: _tt(0x46, U(FlushSpec,24))
# rare: TT_REG2FLOP  = lambda SizeSel, TargetSel, ByteOffset, ContextId_2, FlopIndex, RegIndex: _tt(0x48,
#   U(SizeSel,2)<<22 | U(TargetSel,2)<<20 | U(ByteOffset,2)<<18 | U(ContextId_2,2)<<16 | U(FlopIndex,10)<<6 | U(RegIndex,6))
# rare: TT_LOADIND   = lambda SizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex: _tt(0x49, U(SizeSel,2)<<22 | U(OffsetIndex,8)<<14 | U(AutoIncSpec,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
TT_TBUFCMD   = lambda: _tt(0x4B)  # dead — tile buffer command, not used on Blackhole
# -- ADC (Address Counters) ----------------------------------------------------
# ADCs provide multi-dimensional address generation for pack/unpack operations.
# Each has X, Y, Z, W dimensions across 2 channels (Ch0, Ch1).
# CntSetMask selects which counter sets to modify (3b bitmask).
# rare: TT_SETADC    = lambda CntSetMask, ChannelIndex, DimensionIndex, Value: _tt(0x50, U(CntSetMask,3)<<21 | U(ChannelIndex,1)<<20 | U(DimensionIndex,2)<<18 | U(Value,18))
  # Set a single ADC dimension to an absolute value (18b)
TT_SETADCXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask: _tt(0x51, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6 | U(BitMask,6))
  # Set X/Y dimensions for both channels simultaneously
# rare: TT_INCADCXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X: _tt(0x52, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6)
# rare: TT_ADDRCRXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask: _tt(0x53, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6 | U(BitMask,6))
TT_SETADCZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask: _tt(0x54, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6 | U(BitMask,6))
  # Set Z/W dimensions for both channels
TT_INCADCZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z: _tt(0x55, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6)
  # Increment Z/W dimensions
# rare: TT_ADDRCRZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask: _tt(0x56, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6 | U(BitMask,6))
TT_SETADCXX  = lambda CntSetMask, x_end2, x_start: _tt(0x5E, U(CntSetMask,3)<<21 | U(x_end2,11)<<10 | U(x_start,10))
  # Set X-dimension start and end for address wrapping
# -- DMA register ALU ----------------------------------------------------------
# Integer arithmetic on 16-bit DMA registers. Used for address computation,
# loop counters, and configuration value manipulation in the scalar unit.
# Common args: OpBisConst: 1=OpB is an immediate constant, 0=OpB is a register
#   ResultRegIndex: destination DMA register
#   OpBRegIndex/OpARegIndex: source DMA register indices (6b each)
TT_ADDDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x58, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
  # Result = OpA + OpB
# rare: TT_SUBDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x59, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
  # Result = OpA - OpB
TT_MULDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5A, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
  # Result = OpA * OpB
# rare: TT_BITWOPDMAREG = lambda OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5B, U(OpBisConst,1)<<23 | U(OpSel,5)<<18 | U(ResultRegIndex,6)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
# rare: TT_SHIFTDMAREG  = lambda OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5C, U(OpBisConst,1)<<23 | U(OpSel,5)<<18 | U(ResultRegIndex,6)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
# rare: TT_CMPDMAREG    = lambda OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5D, U(OpBisConst,1)<<23 | U(OpSel,5)<<18 | U(ResultRegIndex,6)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
TT_DMANOP       = lambda: _tt(0x60)  # DMA no-op, occupies one scalar unit slot
# -- atomic memory ops (scalar unit) -------------------------------------------
# Atomic read-modify-write ops on L1 memory via DMA registers.
# MemHierSel: 0=L1, 1=register space; DataRegIndex/AddrRegIndex: DMA reg pair
# rare: Tensix atomics — no BH LLK code path, semaphores used instead
# rare: TT_ATINCGET    = lambda MemHierSel, WrapVal, Sel32b, DataRegIndex, AddrRegIndex: _tt(0x61, U(MemHierSel,1)<<23 | U(WrapVal,9)<<14 | U(Sel32b,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
# rare: TT_ATINCGETPTR = lambda MemHierSel, NoIncr, IncrVal, WrapVal, Sel32b, DataRegIndex, AddrRegIndex: _tt(0x62, U(MemHierSel,1)<<23 | U(NoIncr,1)<<22 | U(IncrVal,4)<<18 | U(WrapVal,4)<<14 | U(Sel32b,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
# rare: TT_ATSWAP      = lambda MemHierSel, SwapMask, DataRegIndex, AddrRegIndex: _tt(0x63, U(MemHierSel,1)<<23 | U(SwapMask,9)<<14 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
# rare: TT_ATCAS       = lambda MemHierSel, SwapVal, CmpVal, Sel32b, DataRegIndex, AddrRegIndex: _tt(0x64, U(MemHierSel,1)<<23 | U(SwapVal,5)<<18 | U(CmpVal,4)<<14 | U(Sel32b,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
# rare: TT_STOREIND    = lambda MemHierSel, SizeSel, RegSizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex: _tt(0x66,
#   U(MemHierSel,1)<<23 | U(SizeSel,1)<<22 | U(RegSizeSel,1)<<21 | U(OffsetIndex,7)<<14 | U(AutoIncSpec,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
# rare: TT_STOREREG    = lambda TdmaDataRegIndex, RegAddr: _tt(0x67, U(TdmaDataRegIndex,6)<<18 | U(RegAddr,18))
# rare: TT_LOADREG     = lambda TdmaDataRegIndex, RegAddr: _tt(0x68, U(TdmaDataRegIndex,6)<<18 | U(RegAddr,18))
# -- SFPU (vector unit) --------------------------------------------------------
# 32-lane SIMD engine operating on 32-bit FP32/INT32 values in LReg[0..7].
# Reads/writes Dst register file via SFPLOAD/SFPSTORE. Runs at 1.35 GHz on BH.
#
# Common args for "simple" form (imm12 + lreg_c + lreg_dest + instr_mod1):
#   imm12_math: 12-bit immediate (meaning varies per instruction)
#   lreg_c: source LReg index (VC, 4b, 0-15)
#   lreg_dest: destination LReg index (VD, 4b, 0-7 writable)
#   instr_mod1: instruction modifier (4b, controls sign/mode/CC behavior)
#
# Common args for "MAD" form (4 LReg operands + instr_mod1):
#   lreg_src_a/b/c: source LReg indices (VA, VB, VC)
#   lreg_dest: destination LReg (VD)
#   instr_mod1: modifier (sign flips, accumulate mode, etc.)
#
# Data movement: Dst ↔ LReg
TT_SFPLOAD     = lambda lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr: _tt(0x70, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(sfpu_addr_mode,3)<<13 | U(dest_reg_addr,13))
  # Load 32 elements from Dst into LReg (4 rows x 8 cols → 32 lanes).
  # lreg_ind: target LReg (4b); instr_mod0: format conversion mode
  # dest_reg_addr: Dst row address (13b, added to RWC offset)
TT_SFPLOADI    = lambda lreg_ind, instr_mod0, imm16: _tt(0x71, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(imm16,16))
  # Load immediate into all lanes of LReg. instr_mod0 selects format:
  # 0=BF16→FP32, 2=FP16→FP32, 4=unsigned 16b, 6=signed 15b,
  # 8=set high 16b, 10=set low 16b
TT_SFPSTORE    = lambda lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr: _tt(0x72, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(sfpu_addr_mode,3)<<13 | U(dest_reg_addr,13))
  # Store LReg back to Dst (inverse of SFPLOAD). Same addressing.
# LUT-based piecewise linear approximation (MAD sub-unit, 2-cycle)
# rare: TT_SFPLUT      = lambda lreg_ind, instr_mod0, dest_reg_addr: _tt(0x73, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(dest_reg_addr,16))
  # 8-bit coefficient LUT — superseded by SFPLUTFP32 on BH
# FP32 arithmetic (MAD sub-unit, 2-cycle latency)
TT_SFPMULI     = lambda imm16_math, lreg_dest, instr_mod1: _tt(0x74, U(imm16_math,16)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # VD *= BF16ToFP32(imm16). Multiply LReg by BF16 immediate.
TT_SFPADDI     = lambda imm16_math, lreg_dest, instr_mod1: _tt(0x75, U(imm16_math,16)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # VD += BF16ToFP32(imm16). Add BF16 immediate to LReg.
# Simple FP32/INT ops (1-cycle latency)
TT_SFPDIVP2    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x76, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Multiply/divide by power of 2: VD = {VC.Sign, VC.Exp + Imm8, VC.Mant}
  # Or set exponent directly: VD = {VC.Sign, Imm8, VC.Mant}
TT_SFPEXEXP    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x77, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Extract exponent: VD = VC.Exp (raw) or VD = VC.Exp - 127 (debiased)
TT_SFPEXMAN    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x78, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Extract mantissa: VD = {0, !Imm1, VC.Mant} (optionally with implicit 1)
TT_SFPIADD     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x79, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Integer add: VD = VC ± VD or VD = VC ± Imm11. Optional CC flag set.
TT_SFPSHFT     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7A, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Bit shift: logical/arithmetic left or right by register or immediate amount
TT_SFPSETCC    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7B, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Set per-lane condition flags from VC comparisons (< 0, != 0, >= 0, == 0)
TT_SFPMOV      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7C, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Move: VD = VC, VD = -VC, VD = Config, or VD = PRNG() (mode-dependent)
TT_SFPABS      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7D, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Absolute value: VD = Abs(VC) (FP32 mode: NaN passthrough; INT mode)
TT_SFPAND      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7E, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Bitwise AND: VD = VB & VC
# rare: TT_SFPOR       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7F, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Bitwise OR — reachable via ttnn.gcd but not seen in standard workloads
TT_SFPNOT      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x80, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Bitwise NOT: VD = ~VC
# rare: TT_SFPLZ       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x81, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Count leading zeros — reachable via ttnn.gcd but not seen in standard workloads
TT_SFPSETEXP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x82, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Replace exponent: VD = {VC.Sign, Imm8 or VD.Exp or VD.Mant&255, VC.Mant}
# rare: TT_SFPSETMAN   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x83, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Replace mantissa — no BH LLK code path
# FP32 FMA / multiply / add (MAD sub-unit, 2-cycle latency)
TT_SFPMAD      = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x84, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Fused multiply-add: VD = VA * ±VB ± VC (sign controlled by instr_mod1)
TT_SFPADD      = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x85, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Add: VD = ±VB ± VC (VA ignored; sign controlled by instr_mod1)
TT_SFPMUL      = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x86, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Multiply: VD = VA * ±VB (VC ignored; sign controlled by instr_mod1)
# Conditional execution / predication
TT_SFPPUSHC    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x87, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Push current per-lane flags onto the flag stack (for nested if/else)
TT_SFPPOPC     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x88, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Pop flag stack (restore previous predication state)
TT_SFPSETSGN   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x89, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Set/clear/copy sign bit: VD = Abs(VC), -Abs(VC), or {VD.Sign, VC.Exp, VC.Mant}
TT_SFPENCC     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8A, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Enable/disable conditional execution; load CC result into LReg
TT_SFPCOMPC    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8B, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Complement per-lane flags (implements "else" in SIMT if/else)
# Data rearrangement
# rare: TT_SFPTRANSP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8C, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # 4x4 transpose within LReg lane groups — no BH LLK code path
# rare: TT_SFPXOR      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8D, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Bitwise XOR — reachable via ttnn.gcd but not seen in standard workloads
# Type conversion and rounding
TT_SFPSTOCHRND = lambda rnd_mode, imm8_math, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x8E, U(rnd_mode,3)<<21 | U(imm8_math,8)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Stochastic/deterministic rounding + type conversion.
  # FP32→BF16/FP16A, FP32→INT8/UINT8/INT16/UINT16, INT→INT (right-shift+round)
  # rnd_mode: rounding mode (3b); imm8_math: shift amount or format selector
TT_SFPNOP      = lambda: _tt(0x8F)  # SFPU no-op, occupies one SFPU issue slot
TT_SFPCAST     = lambda lreg_src_c, lreg_dest, instr_mod1: _tt(0x90, U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Type cast: SignMag32↔FP32, SignMag32↔INT32, IntAbs. Mode via instr_mod1.
TT_SFPCONFIG   = lambda imm16_math, config_dest, instr_mod1: _tt(0x91, U(imm16_math,16)<<8 | U(config_dest,4)<<4 | U(instr_mod1,4))
  # Write LReg[0] lane 0 into a programmable constant register (LReg[11-14])
  # config_dest: which constant register to write (4b)
TT_SFPSWAP     = lambda imm12_math, lreg_src_c, lreg_dest, instr_mod1: _tt(0x92, U(imm12_math,12)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Min/max swap: VD = Min(VC, VD), VC = Max(VC, VD) (simultaneous). 2-cycle.
  # Also supports plain swap and sub-vector swap modes.
TT_SFPLOADMACRO = lambda lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr: _tt(0x93, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(sfpu_addr_mode,3)<<13 | U(dest_reg_addr,13))
  # Load + schedule 4 pipelined ops across all 5 SFPU sub-units (macro mode)
TT_SFPSHFT2    = lambda imm12_math, lreg_src_c, lreg_dest, instr_mod1: _tt(0x94, U(imm12_math,12)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Two-source shift: VD = VB << (VC % 32) or VB >> (-VC % 32).
  # Also supports lane rotation/shift for cross-lane data movement.
TT_SFPLUTFP32  = lambda lreg_dest, instr_mod1: _tt(0x95, U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # FP32-native 3-piece LUT: VD = LReg[i] * Abs(LReg[3]) + LReg[4+i]
  # where i ∈ {0,1,2} based on LReg[3] magnitude. Also 16-bit LUT modes.
# Comparisons (BH-new: SFPGT, SFPLE)
# rare: TT_SFPLE       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x96, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Less-or-equal — BH-new, no LLK code path yet (SFPSETCC covers most comparison needs)
# rare: TT_SFPGT       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x97, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Greater-than — BH-new, no LLK code path yet
# Integer multiply (BH-new)
# rare: TT_SFPMUL24    = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x98, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # 24-bit integer multiply — BH-new, reachable via ttnn.gcd/lcm/int32 ops
# Approximate reciprocal (BH-new)
TT_SFPARECIP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x99, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Approx 1/VC (7-bit accuracy), or approx e^Abs(VC) with sign copy


# -- Tensix decoder ------------------------------------------------------------
class TensixDecoded:
  def __init__(self, name, word, fields):
    self.name = name
    self.word = word & 0xFFFFFFFF
    self._fields = fields

  def __getattr__(self, k):
    fields = object.__getattribute__(self, "_fields")
    if k in fields: return fields[k]
    raise AttributeError(f"{self.name!r} has no field {k!r}; fields: {list(fields)}")

  def __int__(self): return self.word

  def __repr__(self):
    args = ", ".join(f"{k}=0x{v:X}" for k, v in self._fields.items())
    return f"{self.name}({args})" if args else f"{self.name}()"

def _tf(name, shift, width):
  return (name, shift, width)

def _simple_fields(c_name="lreg_c"):
  return [
    _tf("imm12_math", 12, 12),
    _tf(c_name, 8, 4),
    _tf("lreg_dest", 4, 4),
    _tf("instr_mod1", 0, 4),
  ]

def _mad_fields():
  return [
    _tf("lreg_src_a", 16, 4),
    _tf("lreg_src_b", 12, 4),
    _tf("lreg_src_c", 8, 4),
    _tf("lreg_dest", 4, 4),
    _tf("instr_mod1", 0, 4),
  ]

_TENSIX_DECODE = {
  0x01: ("MOP", [_tf("mop_type", 23, 1), _tf("loop_count", 16, 7), _tf("zmask_lo16_or_loop_count", 0, 16)]),
  0x02: ("NOP", []),
  0x03: ("MOP_CFG", [_tf("zmask_hi16", 0, 16)]),
  0x04: ("REPLAY", [_tf("start_idx", 14, 10), _tf("len", 4, 10), _tf("execute_while_loading", 1, 1), _tf("load_mode", 0, 1)]),
  0x08: ("MOVD2A", [_tf("dest_32b_lo", 23, 1), _tf("src", 17, 6), _tf("addr_mode", 14, 3), _tf("instr_mod", 12, 2), _tf("dst", 0, 12)]),
  0x0A: ("MOVD2B", [_tf("dest_32b_lo", 23, 1), _tf("src", 17, 6), _tf("addr_mode", 14, 3), _tf("instr_mod", 12, 2), _tf("dst", 0, 12)]),
  0x10: ("ZEROACC", [_tf("clear_mode", 19, 5), _tf("use_32_bit_mode", 18, 1), _tf("clear_zero_flags", 17, 1), _tf("addr_mode", 14, 3), _tf("where", 0, 14)]),
  0x11: ("ZEROSRC", [_tf("zero_val", 4, 20), _tf("write_mode", 3, 1), _tf("bank_mask", 2, 1), _tf("src_mask", 0, 2)]),
  0x12: ("MOVA2D", [_tf("dest_32b_lo", 23, 1), _tf("src", 17, 6), _tf("addr_mode", 14, 3), _tf("instr_mod", 12, 2), _tf("dst", 0, 12)]),
  0x13: ("MOVB2D", [_tf("dest_32b_lo", 23, 1), _tf("src", 17, 6), _tf("addr_mode", 14, 3), _tf("movb2d_instr_mod", 11, 3), _tf("dst", 0, 11)]),
  0x14: ("TRNSPSRCA", []),
  0x15: ("RAREB", []),
  0x16: ("TRNSPSRCB", []),
  0x17: ("SHIFTXA", [_tf("raw", 0, 24), _tf("shift_mode", 0, 2), _tf("log2_amount2", 2, 22)]),
  0x18: ("SHIFTXB", [_tf("raw", 0, 24), _tf("shift_row", 0, 10), _tf("rot_shift", 10, 4), _tf("addr_mode", 14, 3)]),
  0x21: ("CLREXPHIST", []),
  0x22: ("CONV3S1", [_tf("clear_dvalid", 22, 2), _tf("rotate_weights", 17, 5), _tf("addr_mode", 14, 3), _tf("dst", 0, 14)]),
  0x23: ("CONV3S2", [_tf("clear_dvalid", 22, 2), _tf("rotate_weights", 17, 5), _tf("addr_mode", 14, 3), _tf("dst", 0, 14)]),
  0x24: ("MFCONV3S1", [_tf("clear_dvalid", 22, 2), _tf("rotate_weights", 17, 5), _tf("addr_mode", 14, 3), _tf("dst", 0, 14)]),
  0x25: ("APOOL3S1", [_tf("clear_dvalid", 22, 2), _tf("pool_addr_mode", 15, 7), _tf("index_en", 14, 1), _tf("dst", 0, 14)]),
  0x26: ("MVMUL", [_tf("clear_dvalid", 22, 2), _tf("instr_mod19", 19, 3), _tf("addr_mode", 14, 3), _tf("dst", 0, 10), _tf("broadcast_srcb", 19, 1)]),
  0x27: ("ELWMUL", [_tf("clear_dvalid", 22, 2), _tf("dest_accum_en", 21, 1), _tf("instr_mod19", 19, 2), _tf("addr_mode", 14, 2), _tf("dst", 0, 14)]),
  0x28: ("ELWADD", [_tf("clear_dvalid", 22, 2), _tf("dest_accum_en", 21, 1), _tf("instr_mod19", 19, 2), _tf("addr_mode", 14, 2), _tf("dst", 0, 14)]),
  0x29: ("DOTPV", [_tf("clear_dvalid", 22, 2), _tf("dest_accum_en", 21, 1), _tf("instr_mod19", 19, 2), _tf("addr_mode", 14, 2), _tf("dst", 0, 14)]),
  0x2A: ("MPOOL3S2", [_tf("clear_dvalid", 22, 2), _tf("pool_addr_mode", 15, 7), _tf("index_en", 14, 1), _tf("dst", 0, 14)]),
  0x30: ("ELWSUB", [_tf("clear_dvalid", 22, 2), _tf("dest_accum_en", 21, 1), _tf("instr_mod19", 19, 2), _tf("addr_mode", 14, 2), _tf("dst", 0, 14)]),
  0x31: ("MPOOL3S1", [_tf("clear_dvalid", 22, 2), _tf("pool_addr_mode", 15, 7), _tf("index_en", 14, 1), _tf("dst", 0, 14)]),
  0x32: ("APOOL3S2", [_tf("clear_dvalid", 22, 2), _tf("pool_addr_mode", 15, 7), _tf("index_en", 14, 1), _tf("dst", 0, 14)]),
  0x33: ("GMPOOL", [_tf("clear_dvalid", 22, 2), _tf("instr_mod19", 19, 3), _tf("pool_addr_mode", 15, 4), _tf("max_pool_index_en", 14, 1), _tf("dst", 0, 14)]),
  0x34: ("GAPOOL", [_tf("clear_dvalid", 22, 2), _tf("instr_mod19", 19, 3), _tf("pool_addr_mode", 15, 4), _tf("max_pool_index_en", 14, 1), _tf("dst", 0, 14)]),
  0x35: ("GATESRCRST", [_tf("reset_srcb_gate_control", 1, 1), _tf("reset_srca_gate_control", 0, 1)]),
  0x36: ("CLEARDVALID", [_tf("cleardvalid", 22, 2), _tf("clear_dvalid", 22, 2), _tf("reset", 0, 22)]),
  0x37: ("SETRWC", [_tf("clear_ab_vld", 22, 2), _tf("rwc_cr", 18, 4), _tf("rwc_d", 14, 4), _tf("rwc_b", 10, 4), _tf("rwc_a", 6, 4), _tf("BitMask", 0, 6)]),
  0x38: ("INCRWC", [_tf("rwc_cr", 18, 3), _tf("rwc_d", 14, 4), _tf("rwc_b", 10, 4), _tf("rwc_a", 6, 4)]),
  0x40: ("XMOV", [_tf("Mov_block_selection", 23, 1), _tf("Last", 0, 1)]),
  0x41: ("PACR", [_tf("CfgContext", 21, 3), _tf("RowPadZero", 18, 3), _tf("DstAccessMode", 17, 1), _tf("AddrMode", 15, 2), _tf("AddrCntContext", 13, 2), _tf("ZeroWrite", 12, 1), _tf("ReadIntfSel", 8, 4), _tf("OvrdThreadId", 7, 1), _tf("Concat", 4, 3), _tf("CtxtCtrl", 2, 2), _tf("Flush", 1, 1), _tf("Last", 0, 1)]),
  0x42: ("UNPACR", [_tf("Unpack_block_selection", 23, 1), _tf("AddrMode", 15, 8), _tf("CfgContextCntInc", 13, 2), _tf("CfgContextId", 10, 3), _tf("AddrCntContextId", 8, 2), _tf("OvrdThreadId", 7, 1), _tf("SetDatValid", 6, 1), _tf("srcb_bcast", 5, 1), _tf("ZeroWrite2", 4, 1), _tf("AutoIncContextID", 3, 1), _tf("RowSearch", 2, 1), _tf("SearchCacheFlush", 1, 1), _tf("Last", 0, 1)]),
  0x43: ("UNPACR_NOP", [_tf("Unpacker_Select", 23, 1), _tf("Stream_Id", 16, 7), _tf("Msg_Clr_Cnt", 12, 4), _tf("Set_Dvalid", 8, 4), _tf("Clr_to1_fmt_Ctrl", 6, 2), _tf("Stall_Clr_Cntrl", 5, 1), _tf("Bank_Clr_Ctrl", 4, 1), _tf("Src_ClrVal_Ctrl", 2, 2), _tf("Unpack_Pop", 0, 2)]),
  0x45: ("SETDMAREG", [_tf("Payload_SigSelSize", 22, 2), _tf("Payload_SigSel", 8, 14), _tf("SetSignalsMode", 7, 1), _tf("RegIndex16b", 0, 7)]),
  0x46: ("FLUSHDMA", [_tf("ConditionMask", 0, 4)]),
  0x48: ("REG2FLOP", [_tf("SizeSel", 22, 2), _tf("ThConCfgIndex", 8, 7), _tf("InputReg", 0, 6)]),
  0x4B: ("TBUFCMD", []),
  0x50: ("SETADC", [_tf("CntSetMask", 21, 3), _tf("ChannelIndex", 20, 1), _tf("DimensionIndex", 18, 2), _tf("Value", 0, 18)]),
  0x51: ("SETADCXY", [_tf("CntSetMask", 21, 3), _tf("Ch1_Y", 15, 6), _tf("Ch1_X", 12, 3), _tf("Ch0_Y", 9, 3), _tf("Ch0_X", 6, 3), _tf("BitMask", 0, 6)]),
  0x54: ("SETADCZW", [_tf("CntSetMask", 21, 3), _tf("Ch1_W", 15, 6), _tf("Ch1_Z", 12, 3), _tf("Ch0_W", 9, 3), _tf("Ch0_Z", 6, 3), _tf("BitMask", 0, 6)]),
  0x55: ("INCADCZW", [_tf("CntSetMask", 21, 3), _tf("Ch1_W", 15, 6), _tf("Ch1_Z", 12, 3), _tf("Ch0_W", 9, 3), _tf("Ch0_Z", 6, 3)]),
  0x58: ("ADDDMAREG", [_tf("OpBisConst", 23, 1), _tf("ResultRegIndex", 12, 11), _tf("OpBRegIndex", 6, 6), _tf("OpARegIndex", 0, 6)]),
  0x5A: ("MULDMAREG", [_tf("OpBisConst", 23, 1), _tf("ResultRegIndex", 12, 11), _tf("OpBRegIndex", 6, 6), _tf("OpARegIndex", 0, 6)]),
  0x5B: ("BITWOPDMAREG", [_tf("OpBisConst", 23, 1), _tf("OpSel", 18, 5), _tf("ResultRegIndex", 12, 6), _tf("OpBRegIndex", 6, 6), _tf("OpARegIndex", 0, 6)]),
  0x5C: ("SHIFTDMAREG", [_tf("OpBisConst", 23, 1), _tf("Mode", 18, 5), _tf("OpSel", 18, 5), _tf("ResultRegIndex", 12, 6), _tf("OpBRegIndex", 6, 6), _tf("OpARegIndex", 0, 6)]),
  0x5D: ("CMPDMAREG", [_tf("OpBisConst", 23, 1), _tf("OpSel", 18, 5), _tf("ResultRegIndex", 12, 6), _tf("OpBRegIndex", 6, 6), _tf("OpARegIndex", 0, 6)]),
  0x5E: ("SETADCXX", [_tf("CntSetMask", 21, 3), _tf("x_end2", 10, 11), _tf("x_start", 0, 10)]),
  0x60: ("DMANOP", []),
  0x67: ("STOREREG", [_tf("TdmaDataRegIndex", 18, 6), _tf("RegAddr", 0, 18)]),
  0x70: ("SFPLOAD", [_tf("lreg_ind", 20, 4), _tf("instr_mod0", 16, 4), _tf("sfpu_addr_mode", 13, 3), _tf("dest_reg_addr", 0, 13)]),
  0x71: ("SFPLOADI", [_tf("lreg_ind", 20, 4), _tf("instr_mod0", 16, 4), _tf("imm16", 0, 16)]),
  0x72: ("SFPSTORE", [_tf("lreg_ind", 20, 4), _tf("instr_mod0", 16, 4), _tf("sfpu_addr_mode", 13, 3), _tf("dest_reg_addr", 0, 13)]),
  0x73: ("SFPLUT", [_tf("lreg_ind", 20, 4), _tf("instr_mod0", 16, 4), _tf("dest_reg_addr", 0, 16)]),
  0x74: ("SFPMULI", [_tf("imm16_math", 8, 16), _tf("lreg_dest", 4, 4), _tf("instr_mod1", 0, 4)]),
  0x75: ("SFPADDI", [_tf("imm16_math", 8, 16), _tf("lreg_dest", 4, 4), _tf("instr_mod1", 0, 4)]),
  0x76: ("SFPDIVP2", _simple_fields()),
  0x77: ("SFPEXEXP", _simple_fields()),
  0x78: ("SFPEXMAN", _simple_fields()),
  0x79: ("SFPIADD", _simple_fields()),
  0x7A: ("SFPSHFT", _simple_fields()),
  0x7B: ("SFPSETCC", _simple_fields()),
  0x7C: ("SFPMOV", _simple_fields()),
  0x7D: ("SFPABS", _simple_fields()),
  0x7E: ("SFPAND", _simple_fields()),
  0x7F: ("SFPOR", _simple_fields()),
  0x80: ("SFPNOT", _simple_fields()),
  0x81: ("SFPLZ", _simple_fields()),
  0x82: ("SFPSETEXP", _simple_fields()),
  0x83: ("SFPSETMAN", _simple_fields()),
  0x84: ("SFPMAD", _mad_fields()),
  0x85: ("SFPADD", _mad_fields()),
  0x86: ("SFPMUL", _mad_fields()),
  0x87: ("SFPPUSHC", _simple_fields()),
  0x88: ("SFPPOPC", _simple_fields()),
  0x89: ("SFPSETSGN", _simple_fields()),
  0x8A: ("SFPENCC", _simple_fields()),
  0x8B: ("SFPCOMPC", _simple_fields()),
  0x8C: ("SFPTRANSP", [_tf("imm12_math", 12, 12), _tf("lreg_c", 8, 4), _tf("lreg_dest", 4, 4), _tf("instr_mod1", 0, 4)]),
  0x8D: ("SFPXOR", _simple_fields()),
  0x8E: ("SFPSTOCHRND", [_tf("rnd_mode", 21, 3), _tf("imm8_math", 16, 8), _tf("lreg_src_b", 12, 4), _tf("lreg_src_c", 8, 4), _tf("lreg_dest", 4, 4), _tf("instr_mod1", 0, 4)]),
  0x8F: ("SFPNOP", []),
  0x90: ("SFPCAST", [_tf("lreg_src_c", 8, 4), _tf("lreg_dest", 4, 4), _tf("instr_mod1", 0, 4)]),
  0x91: ("SFPCONFIG", [_tf("imm16_math", 8, 16), _tf("config_dest", 4, 4), _tf("instr_mod1", 0, 4)]),
  0x92: ("SFPSWAP", _simple_fields("lreg_src_c")),
  0x93: ("SFPLOADMACRO", [_tf("lreg_ind", 20, 4), _tf("instr_mod0", 16, 4), _tf("sfpu_addr_mode", 13, 3), _tf("dest_reg_addr", 0, 13)]),
  0x94: ("SFPSHFT2", _simple_fields("lreg_src_c")),
  0x95: ("SFPLUTFP32", [_tf("lreg_dest", 4, 4), _tf("instr_mod1", 0, 4)]),
  0x96: ("SFPLE", _simple_fields()),
  0x97: ("SFPGT", _simple_fields()),
  0x98: ("SFPMUL24", _mad_fields()),
  0x99: ("SFPARECIP", _simple_fields()),
  0xA0: ("ATGETM", [_tf("mutex_index", 0, 24)]),
  0xA1: ("ATRELM", [_tf("mutex_index", 0, 24)]),
  0xA2: ("STALLWAIT", [_tf("stall_res", 15, 9), _tf("wait_res", 0, 15)]),
  0xA3: ("SEMINIT", [_tf("max_value", 20, 4), _tf("init_value", 16, 4), _tf("sem_sel", 2, 8)]),
  0xA4: ("SEMPOST", [_tf("sem_sel", 2, 8)]),
  0xA5: ("SEMGET", [_tf("sem_sel", 2, 8)]),
  0xA6: ("SEMWAIT", [_tf("stall_res", 15, 9), _tf("sem_sel", 2, 8), _tf("wait_sem_cond", 0, 2)]),
  0xA7: ("STREAMWAIT", [_tf("stall_res", 15, 9), _tf("target_value", 4, 10), _tf("target_sel", 3, 1), _tf("wait_stream_sel", 0, 2)]),
  0xB0: ("WRCFG", [_tf("GprAddress", 16, 6), _tf("wr128b", 15, 1), _tf("CfgReg", 0, 11)]),
  0xB1: ("RDCFG", [_tf("GprAddress", 16, 6), _tf("CfgReg", 0, 11)]),
  0xB2: ("SETC16", [_tf("setc16_reg", 16, 8), _tf("setc16_value", 0, 16)]),
  0xB3: ("RMWCIB0", [_tf("Mask", 16, 8), _tf("Data", 8, 8), _tf("CfgRegAddr", 0, 8)]),
  0xB4: ("RMWCIB1", [_tf("Mask", 16, 8), _tf("Data", 8, 8), _tf("CfgRegAddr", 0, 8)]),
  0xB5: ("RMWCIB2", [_tf("Mask", 16, 8), _tf("Data", 8, 8), _tf("CfgRegAddr", 0, 8)]),
  0xB6: ("RMWCIB3", [_tf("Mask", 16, 8), _tf("Data", 8, 8), _tf("CfgRegAddr", 0, 8)]),
  0xB7: ("STREAMWRCFG", [_tf("stream_id_sel", 21, 2), _tf("StreamRegAddr", 11, 10), _tf("CfgReg", 0, 11)]),
  0xB8: ("CFGSHIFTMASK", [_tf("mask_mode", 23, 1), _tf("disable_mask_on_old_val", 23, 1), _tf("alu_mode", 20, 3), _tf("operation", 20, 3), _tf("mask_width", 15, 5), _tf("rotate_amt", 10, 5), _tf("right_cshift_amt", 10, 5), _tf("scratch_index", 8, 2), _tf("scratch_sel", 8, 2), _tf("cfg_index", 0, 8), _tf("CfgReg", 0, 8)]),
  0xC0: ("WRCFG32", [_tf("GprAddress", 18, 6), _tf("CfgReg", 0, 11)]),
}

def decode_tensix(word):
  w = word & 0xFFFFFFFF
  op = (w >> 24) & 0xFF
  spec = _TENSIX_DECODE.get(op)
  if spec is None:
    return TensixDecoded(f"UNKNOWN_0x{op:02X}", w, {"raw_params": w & 0xFFFFFF})
  name, fields = spec
  return TensixDecoded(
    name,
    w,
    {name: (w >> shift) & ((1 << width) - 1) for name, shift, width in fields},
  )
