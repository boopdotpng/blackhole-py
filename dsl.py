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

ADD  = partial(_r, 0x33, 0, 0x00); SUB  = partial(_r, 0x33, 0, 0x20)
SLL  = partial(_r, 0x33, 1, 0x00); SLT  = partial(_r, 0x33, 2, 0x00)
SLTU = partial(_r, 0x33, 3, 0x00); XOR  = partial(_r, 0x33, 4, 0x00)
SRL  = partial(_r, 0x33, 5, 0x00)
OR   = partial(_r, 0x33, 6, 0x00); AND  = partial(_r, 0x33, 7, 0x00)
ADDI  = partial(_i, 0x13, 0)
SLTIU = partial(_i, 0x13, 3); XORI  = partial(_i, 0x13, 4)
ORI   = partial(_i, 0x13, 6); ANDI  = partial(_i, 0x13, 7)
SLLI  = partial(_i, 0x13, 1); SRLI  = partial(_i, 0x13, 5)
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

MUL    = partial(_r, 0x33, 0, 0x01)
MULHU  = partial(_r, 0x33, 3, 0x01)
DIVU   = partial(_r, 0x33, 5, 0x01)
REMU   = partial(_r, 0x33, 7, 0x01)

SH1ADD = partial(_r, 0x33, 2, 0x10)
SH2ADD = partial(_r, 0x33, 4, 0x10)
SH3ADD = partial(_r, 0x33, 6, 0x10)

MAXU = partial(_r, 0x33, 7, 0x05)
MIN  = partial(_r, 0x33, 4, 0x05); MINU = partial(_r, 0x33, 5, 0x05)
CTZ    = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x601)
SEXT_B = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x604)
SEXT_H = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x605)
ZEXT_H = lambda rd, rs1: _r(0x33, 4, 0x04, rd, rs1, 0)

zero, ra, sp, gp, tp, t0, t1, t2, s0, s1 = range(10)
a0, a1, a2, a3, a4, a5, a6, a7 = range(10, 18)
s2, s3, s4, s5, s6, s7, s8, s9, s10, s11 = range(18, 28)
t3, t4, t5, t6 = range(28, 32)
fp = s0

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

def LI32(rd, imm):
  imm &= 0xFFFFFFFF
  imm_s = imm if imm < 0x80000000 else imm - 0x100000000
  hi = (imm_s + 0x800) & 0xFFFFF000
  hi_s = hi if hi < 0x80000000 else hi - 0x100000000
  lo = imm_s - hi_s
  if hi == 0:
    return [ADDI(rd, zero, lo)]
  return [LUI(rd, hi), ADDI(rd, rd, lo)]

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

def TTINSN(imm32):
  assert imm32 < 0xC0000000, f".ttinsn requires imm32 < 0xC0000000, got 0x{imm32:08x}"
  return RiscVInsn(((imm32 << 2) | (imm32 >> 30)) & 0xFFFFFFFF)

def _tt(op, p=0):
  if p != (p & 0xFFFFFF): raise ValueError(f"Tensix params overflow: 0x{p:x} doesn't fit in 24 bits")
  return TensixInsn((op << 24) | p)

TT_NOP     = lambda: _tt(0x02)  # no-op, occupies one Tensix issue slot
TT_MOP     = lambda mop_type, loop_count, zmask_lo16_or_loop_count: _tt(0x01, U(mop_type,1)<<23 | U(loop_count,7)<<16 | U(zmask_lo16_or_loop_count,16))
TT_REPLAY  = lambda start_idx, len, execute_while_loading=0, load_mode=0: _tt(0x04, U(start_idx,10)<<14 | U(len,10)<<4 | U(execute_while_loading,1)<<1 | U(load_mode,1))
TT_ATGETM     = lambda mutex_index: _tt(0xA0, U(mutex_index,24))
TT_ATRELM     = lambda mutex_index: _tt(0xA1, U(mutex_index,24))
TT_STALLWAIT  = lambda stall_res, wait_res: _tt(0xA2, U(stall_res,9)<<15 | U(wait_res,15))
TT_SEMINIT    = lambda max_value, init_value, sem_sel: _tt(0xA3, U(max_value,4)<<20 | U(init_value,4)<<16 | U(sem_sel,8)<<2)
TT_SEMPOST    = lambda sem_sel: _tt(0xA4, U(sem_sel,8)<<2)
TT_SEMGET     = lambda sem_sel: _tt(0xA5, U(sem_sel,8)<<2)
TT_SEMWAIT    = lambda stall_res, sem_sel, wait_sem_cond: _tt(0xA6, U(stall_res,9)<<15 | U(sem_sel,8)<<2 | U(wait_sem_cond,2))
TT_WRCFG        = lambda GprAddress, wr128b, CfgReg: _tt(0xB0, U(GprAddress,6)<<16 | U(wr128b,1)<<15 | U(CfgReg,11))
TT_RDCFG        = lambda GprAddress, CfgReg: _tt(0xB1, U(GprAddress,6)<<16 | U(CfgReg,11))
TT_SETC16       = lambda setc16_reg, setc16_value: _tt(0xB2, U(setc16_reg,8)<<16 | U(setc16_value,16))
TT_ZEROACC   = lambda clear_mode, use_32_bit_mode, clear_zero_flags, addr_mode, where: _tt(0x10,
  U(clear_mode,5)<<19 | U(use_32_bit_mode,1)<<18 | U(clear_zero_flags,1)<<17 | U(addr_mode,3)<<14 | U(where,14))
TT_ZEROSRC   = lambda zero_val, write_mode, bank_mask, src_mask: _tt(0x11, U(zero_val,20)<<4 | U(write_mode,1)<<3 | U(bank_mask,1)<<2 | U(src_mask,2))
TT_MOVB2D    = lambda dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst: _tt(0x13, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(movb2d_instr_mod,3)<<11 | U(dst,11))
TT_TRNSPSRCA = lambda: _tt(0x14)   # dead — SrcA transpose not functional on Blackhole
TT_RAREB     = lambda: _tt(0x15)   # dead — not used in Blackhole
TT_TRNSPSRCB = lambda: _tt(0x16)   # Transpose SrcB rows 16-31 in-place (16x16 transpose)
TT_CONV3S1  = lambda clear_dvalid, rotate_weights, addr_mode, dst: _tt(0x22, U(clear_dvalid,2)<<22 | U(rotate_weights,5)<<17 | U(addr_mode,3)<<14 | U(dst,14))
TT_CONV3S2  = lambda clear_dvalid, rotate_weights, addr_mode, dst: _tt(0x23, U(clear_dvalid,2)<<22 | U(rotate_weights,5)<<17 | U(addr_mode,3)<<14 | U(dst,14))
TT_MFCONV3S1 = lambda clear_dvalid, rotate_weights, addr_mode, dst: _tt(0x24, U(clear_dvalid,2)<<22 | U(rotate_weights,5)<<17 | U(addr_mode,3)<<14 | U(dst,14))
TT_APOOL3S1 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x25, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
TT_MVMUL    = lambda clear_dvalid, instr_mod19, addr_mode, dst: _tt(0x26, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(addr_mode,2)<<14 | U(dst,10))
TT_ELWADD   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x28, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
TT_MPOOL3S2 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x2A, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
TT_MPOOL3S1 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x31, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
TT_APOOL3S2 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x32, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
TT_GMPOOL   = lambda clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst: _tt(0x33, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(pool_addr_mode,4)<<15 | U(max_pool_index_en,1)<<14 | U(dst,14))
TT_CLEARDVALID = lambda cleardvalid, reset: _tt(0x36, U(cleardvalid,2)<<22 | U(reset,22))
TT_SETRWC   = lambda clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask: _tt(0x37, U(clear_ab_vld,2)<<22 | U(rwc_cr,4)<<18 | U(rwc_d,4)<<14 | U(rwc_b,4)<<10 | U(rwc_a,4)<<6 | U(BitMask,6))
TT_INCRWC   = lambda rwc_cr, rwc_d, rwc_b, rwc_a: _tt(0x38, U(rwc_cr,3)<<18 | U(rwc_d,4)<<14 | U(rwc_b,4)<<10 | U(rwc_a,4)<<6)
TT_MOVD2B    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x0A, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
TT_PACR = lambda CfgContext, RowPadZero, DstAccessMode, AddrMode, AddrCntContext, ZeroWrite, ReadIntfSel, OvrdThreadId, Concat, CtxtCtrl, Flush, Last: _tt(0x41,
  U(CfgContext,3)<<21 | U(RowPadZero,3)<<18 | U(DstAccessMode,1)<<17 | U(AddrMode,2)<<15 | U(AddrCntContext,2)<<13 | U(ZeroWrite,1)<<12 | U(ReadIntfSel,4)<<8 | U(OvrdThreadId,1)<<7 | U(Concat,3)<<4 | U(CtxtCtrl,2)<<2 | U(Flush,1)<<1 | U(Last,1))
TT_UNPACR = lambda Unpack_block_selection, AddrMode, CfgContextCntInc, CfgContextId, AddrCntContextId, OvrdThreadId, SetDatValid, srcb_bcast, ZeroWrite2, AutoIncContextID, RowSearch, SearchCacheFlush, Last: _tt(0x42,
  U(Unpack_block_selection,1)<<23 | U(AddrMode,8)<<15 | U(CfgContextCntInc,2)<<13 | U(CfgContextId,3)<<10 | U(AddrCntContextId,2)<<8 | U(OvrdThreadId,1)<<7 | U(SetDatValid,1)<<6 | U(srcb_bcast,1)<<5 | U(ZeroWrite2,1)<<4 | U(AutoIncContextID,1)<<3 | U(RowSearch,1)<<2 | U(SearchCacheFlush,1)<<1 | U(Last,1))
TT_UNPACR_NOP = lambda Unpacker_Select, Stream_Id, Msg_Clr_Cnt, Set_Dvalid, Clr_to1_fmt_Ctrl, Stall_Clr_Cntrl, Bank_Clr_Ctrl, Src_ClrVal_Ctrl, Unpack_Pop: _tt(0x43,
  U(Unpacker_Select,1)<<23 | U(Stream_Id,7)<<16 | U(Msg_Clr_Cnt,4)<<12 | U(Set_Dvalid,4)<<8 | U(Clr_to1_fmt_Ctrl,2)<<6 | U(Stall_Clr_Cntrl,1)<<5 | U(Bank_Clr_Ctrl,1)<<4 | U(Src_ClrVal_Ctrl,2)<<2 | U(Unpack_Pop,2))
TT_SETDMAREG = lambda Payload_SigSelSize, Payload_SigSel, SetSignalsMode, RegIndex16b: _tt(0x45, U(Payload_SigSelSize,2)<<22 | U(Payload_SigSel,14)<<8 | U(SetSignalsMode,1)<<7 | U(RegIndex16b,7))
TT_TBUFCMD   = lambda: _tt(0x4B)  # dead — tile buffer command, not used on Blackhole
TT_SETADCXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask: _tt(0x51, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6 | U(BitMask,6))
TT_SETADCZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask: _tt(0x54, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6 | U(BitMask,6))
TT_INCADCZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z: _tt(0x55, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6)
TT_SETADCXX  = lambda CntSetMask, x_end2, x_start: _tt(0x5E, U(CntSetMask,3)<<21 | U(x_end2,11)<<10 | U(x_start,10))
TT_ADDDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x58, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
TT_MULDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5A, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
TT_DMANOP       = lambda: _tt(0x60)  # DMA no-op, occupies one scalar unit slot
TT_SFPLOAD     = lambda lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr: _tt(0x70, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(sfpu_addr_mode,3)<<13 | U(dest_reg_addr,13))
TT_SFPLOADI    = lambda lreg_ind, instr_mod0, imm16: _tt(0x71, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(imm16,16))
TT_SFPSTORE    = lambda lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr: _tt(0x72, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(sfpu_addr_mode,3)<<13 | U(dest_reg_addr,13))
TT_SFPMULI     = lambda imm16_math, lreg_dest, instr_mod1: _tt(0x74, U(imm16_math,16)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPADDI     = lambda imm16_math, lreg_dest, instr_mod1: _tt(0x75, U(imm16_math,16)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPDIVP2    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x76, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPEXEXP    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x77, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPEXMAN    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x78, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPIADD     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x79, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSHFT     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7A, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSETCC    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7B, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPMOV      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7C, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPABS      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7D, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPAND      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7E, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPNOT      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x80, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSETEXP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x82, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPMAD      = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x84, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPADD      = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x85, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPMUL      = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x86, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPPUSHC    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x87, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPPOPC     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x88, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSETSGN   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x89, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPENCC     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8A, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPCOMPC    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8B, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSTOCHRND = lambda rnd_mode, imm8_math, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x8E, U(rnd_mode,3)<<21 | U(imm8_math,8)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPNOP      = lambda: _tt(0x8F)  # SFPU no-op, occupies one SFPU issue slot
TT_SFPCAST     = lambda lreg_src_c, lreg_dest, instr_mod1: _tt(0x90, U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPCONFIG   = lambda imm16_math, config_dest, instr_mod1: _tt(0x91, U(imm16_math,16)<<8 | U(config_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSWAP     = lambda imm12_math, lreg_src_c, lreg_dest, instr_mod1: _tt(0x92, U(imm12_math,12)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPLOADMACRO = lambda lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr: _tt(0x93, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(sfpu_addr_mode,3)<<13 | U(dest_reg_addr,13))
TT_SFPSHFT2    = lambda imm12_math, lreg_src_c, lreg_dest, instr_mod1: _tt(0x94, U(imm12_math,12)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPLUTFP32  = lambda lreg_dest, instr_mod1: _tt(0x95, U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPARECIP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x99, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))

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
