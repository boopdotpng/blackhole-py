from dataclasses import dataclass
from functools import partial

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
def _r4(op, f2, rs3, rs2, rs1, rm, rd):
  return RiscVInsn(op | R(rd)<<7 | U(rm,3)<<12 | R(rs1)<<15 | R(rs2)<<20 | f2<<25 | R(rs3)<<27)
def _amo(f5, aq, rl, rs2, rs1, f3, rd):
  return RiscVInsn(0x2F | R(rd)<<7 | f3<<12 | R(rs1)<<15 | R(rs2)<<20 | U(rl,1)<<25 | U(aq,1)<<26 | f5<<27)
def _rv(w): return RiscVInsn(w)

# -- registers -----------------------------------------------------------------
zero, ra, sp, gp, tp = 0, 1, 2, 3, 4
t0, t1, t2 = 5, 6, 7
s0, fp, s1 = 8, 8, 9
a0, a1, a2, a3, a4, a5, a6, a7 = range(10, 18)
s2, s3, s4, s5, s6, s7, s8, s9, s10, s11 = range(18, 28)
t3, t4, t5, t6 = 28, 29, 30, 31
ft0, ft1, ft2, ft3, ft4, ft5, ft6, ft7 = range(0, 8)
fs0, fs1 = 8, 9
fa0, fa1, fa2, fa3, fa4, fa5, fa6, fa7 = range(10, 18)
fs2, fs3, fs4, fs5, fs6, fs7, fs8, fs9, fs10, fs11 = range(18, 28)
ft8, ft9, ft10, ft11 = 28, 29, 30, 31

# -- RV32I base ----------------------------------------------------------------
ADD  = partial(_r, 0x33, 0, 0x00); SUB  = partial(_r, 0x33, 0, 0x20)
SLL  = partial(_r, 0x33, 1, 0x00); SLT  = partial(_r, 0x33, 2, 0x00)
SLTU = partial(_r, 0x33, 3, 0x00); XOR  = partial(_r, 0x33, 4, 0x00)
SRL  = partial(_r, 0x33, 5, 0x00); SRA  = partial(_r, 0x33, 5, 0x20)
OR   = partial(_r, 0x33, 6, 0x00); AND  = partial(_r, 0x33, 7, 0x00)
ADDI  = partial(_i, 0x13, 0); SLTI  = partial(_i, 0x13, 2)
SLTIU = partial(_i, 0x13, 3); XORI  = partial(_i, 0x13, 4)
ORI   = partial(_i, 0x13, 6); ANDI  = partial(_i, 0x13, 7)
SLLI  = partial(_i, 0x13, 1); SRLI  = partial(_i, 0x13, 5)
SRAI  = lambda rd, rs1, shamt: _i(0x13, 5, rd, rs1, U(shamt,5) | 0x400)
LB  = partial(_i, 0x03, 0); LH  = partial(_i, 0x03, 1)
LW  = partial(_i, 0x03, 2); LBU = partial(_i, 0x03, 4); LHU = partial(_i, 0x03, 5)
SB = partial(_s, 0x23, 0); SH = partial(_s, 0x23, 1); SW = partial(_s, 0x23, 2)
BEQ  = partial(_b, 0x63, 0); BNE  = partial(_b, 0x63, 1)
BLT  = partial(_b, 0x63, 4); BGE  = partial(_b, 0x63, 5)
BLTU = partial(_b, 0x63, 6); BGEU = partial(_b, 0x63, 7)
LUI   = partial(_u, 0x37); AUIPC = partial(_u, 0x17)
JAL  = partial(_j, 0x6F); JALR = partial(_i, 0x67, 0)
ECALL  = lambda: _i(0x73, 0, 0, 0, 0)
EBREAK = lambda: _i(0x73, 0, 0, 0, 1)
FENCE  = lambda pred=0xF, succ=0xF: _i(0x0F, 0, 0, 0, U(pred,4)<<4 | U(succ,4))
# Zicsr
CSRRW  = lambda rd, rs1, csr: _i(0x73, 1, rd, rs1, U(csr,12))
CSRRS  = lambda rd, rs1, csr: _i(0x73, 2, rd, rs1, U(csr,12))
CSRRC  = lambda rd, rs1, csr: _i(0x73, 3, rd, rs1, U(csr,12))
CSRRWI = lambda rd, uimm, csr: _i(0x73, 5, rd, U(uimm,5), U(csr,12))
CSRRSI = lambda rd, uimm, csr: _i(0x73, 6, rd, U(uimm,5), U(csr,12))
CSRRCI = lambda rd, uimm, csr: _i(0x73, 7, rd, U(uimm,5), U(csr,12))

# -- M extension ---------------------------------------------------------------
MUL    = partial(_r, 0x33, 0, 0x01); MULH   = partial(_r, 0x33, 1, 0x01)
MULHSU = partial(_r, 0x33, 2, 0x01); MULHU  = partial(_r, 0x33, 3, 0x01)
DIV    = partial(_r, 0x33, 4, 0x01); DIVU   = partial(_r, 0x33, 5, 0x01)
REM    = partial(_r, 0x33, 6, 0x01); REMU   = partial(_r, 0x33, 7, 0x01)

# -- Zaamo (no lr/sc) ----------------------------------------------------------
AMOADD_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x00, aq, rl, rs2, rs1, 2, rd)
AMOSWAP_W = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x01, aq, rl, rs2, rs1, 2, rd)
AMOXOR_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x04, aq, rl, rs2, rs1, 2, rd)
AMOOR_W   = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x08, aq, rl, rs2, rs1, 2, rd)
AMOAND_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x0C, aq, rl, rs2, rs1, 2, rd)
AMOMIN_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x10, aq, rl, rs2, rs1, 2, rd)
AMOMAX_W  = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x14, aq, rl, rs2, rs1, 2, rd)
AMOMINU_W = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x18, aq, rl, rs2, rs1, 2, rd)
AMOMAXU_W = lambda rd, rs2, rs1, aq=0, rl=0: _amo(0x1C, aq, rl, rs2, rs1, 2, rd)

# -- Zba -----------------------------------------------------------------------
SH1ADD = partial(_r, 0x33, 2, 0x10)
SH2ADD = partial(_r, 0x33, 4, 0x10)
SH3ADD = partial(_r, 0x33, 6, 0x10)

# -- Zbb + Zbkb ----------------------------------------------------------------
ANDN = partial(_r, 0x33, 7, 0x20); ORN  = partial(_r, 0x33, 6, 0x20)
XNOR = partial(_r, 0x33, 4, 0x20)
MAX  = partial(_r, 0x33, 6, 0x05); MAXU = partial(_r, 0x33, 7, 0x05)
MIN  = partial(_r, 0x33, 4, 0x05); MINU = partial(_r, 0x33, 5, 0x05)
ROL  = partial(_r, 0x33, 1, 0x30); ROR  = partial(_r, 0x33, 5, 0x30)
RORI   = lambda rd, rs1, shamt: _i(0x13, 5, rd, rs1, U(shamt,5) | 0x600)
CLZ    = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x600)
CTZ    = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x601)
CPOP   = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x602)
SEXT_B = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x604)
SEXT_H = lambda rd, rs1: _i(0x13, 1, rd, rs1, 0x605)
ZEXT_H = lambda rd, rs1: _r(0x33, 4, 0x04, rd, rs1, 0)
REV8   = lambda rd, rs1: _i(0x13, 5, rd, rs1, 0x698)
ORC_B  = lambda rd, rs1: _i(0x13, 5, rd, rs1, 0x287)
PACK   = partial(_r, 0x33, 4, 0x04)
BREV8  = lambda rd, rs1: _i(0x13, 5, rd, rs1, 0x687)
GREVI  = lambda rd, rs1, shamt: _i(0x13, 5, rd, rs1, U(shamt,5) | 0x680)

# -- F extension (partial: no fdiv.s, fsqrt.s) ---------------------------------
FLW = lambda rd, rs1, imm: _i(0x07, 2, rd, rs1, imm)
FSW = lambda rs1, rs2, imm: _s(0x27, 2, rs1, rs2, imm)
FADD_S   = lambda rd, rs1, rs2, rm=0: _r4(0x53, 0, 0x00, rs2, rs1, rm, rd)
FSUB_S   = lambda rd, rs1, rs2, rm=0: _r4(0x53, 0, 0x04, rs2, rs1, rm, rd)
FMUL_S   = lambda rd, rs1, rs2, rm=0: _r4(0x53, 0, 0x08, rs2, rs1, rm, rd)
FMADD_S  = lambda rd, rs1, rs2, rs3, rm=0: _r4(0x43, 0, rs3, rs2, rs1, rm, rd)
FMSUB_S  = lambda rd, rs1, rs2, rs3, rm=0: _r4(0x47, 0, rs3, rs2, rs1, rm, rd)
FNMSUB_S = lambda rd, rs1, rs2, rs3, rm=0: _r4(0x4B, 0, rs3, rs2, rs1, rm, rd)
FNMADD_S = lambda rd, rs1, rs2, rs3, rm=0: _r4(0x4F, 0, rs3, rs2, rs1, rm, rd)
FSGNJ_S  = lambda rd, rs1, rs2: _rv(0x53 | R(rd)<<7 | 0<<12 | R(rs1)<<15 | R(rs2)<<20 | 0x10<<25)
FSGNJN_S = lambda rd, rs1, rs2: _rv(0x53 | R(rd)<<7 | 1<<12 | R(rs1)<<15 | R(rs2)<<20 | 0x10<<25)
FSGNJX_S = lambda rd, rs1, rs2: _rv(0x53 | R(rd)<<7 | 2<<12 | R(rs1)<<15 | R(rs2)<<20 | 0x10<<25)
FMIN_S   = lambda rd, rs1, rs2: _rv(0x53 | R(rd)<<7 | 0<<12 | R(rs1)<<15 | R(rs2)<<20 | 0x14<<25)
FMAX_S   = lambda rd, rs1, rs2: _rv(0x53 | R(rd)<<7 | 1<<12 | R(rs1)<<15 | R(rs2)<<20 | 0x14<<25)
FEQ_S    = lambda rd, rs1, rs2: _rv(0x53 | R(rd)<<7 | 2<<12 | R(rs1)<<15 | R(rs2)<<20 | 0x50<<25)
FLT_S    = lambda rd, rs1, rs2: _rv(0x53 | R(rd)<<7 | 1<<12 | R(rs1)<<15 | R(rs2)<<20 | 0x50<<25)
FLE_S    = lambda rd, rs1, rs2: _rv(0x53 | R(rd)<<7 | 0<<12 | R(rs1)<<15 | R(rs2)<<20 | 0x50<<25)
FCLASS_S = lambda rd, rs1: _rv(0x53 | R(rd)<<7 | 1<<12 | R(rs1)<<15 | 0x70<<25)
FCVT_W_S  = lambda rd, rs1, rm=0: _rv(0x53 | R(rd)<<7 | U(rm,3)<<12 | R(rs1)<<15 | 0x60<<25)
FCVT_WU_S = lambda rd, rs1, rm=0: _rv(0x53 | R(rd)<<7 | U(rm,3)<<12 | R(rs1)<<15 | 1<<20 | 0x60<<25)
FCVT_S_W  = lambda rd, rs1, rm=0: _rv(0x53 | R(rd)<<7 | U(rm,3)<<12 | R(rs1)<<15 | 0x68<<25)
FCVT_S_WU = lambda rd, rs1, rm=0: _rv(0x53 | R(rd)<<7 | U(rm,3)<<12 | R(rs1)<<15 | 1<<20 | 0x68<<25)
FMV_X_W   = lambda rd, rs1: _rv(0x53 | R(rd)<<7 | R(rs1)<<15 | 0x70<<25)
FMV_W_X   = lambda rd, rs1: _rv(0x53 | R(rd)<<7 | R(rs1)<<15 | 0x78<<25)

# -- Zfh (partial, BH CSR switches FP16/BF16) ----------------------------------
FLH = lambda rd, rs1, imm: _i(0x07, 1, rd, rs1, imm)
FSH = lambda rs1, rs2, imm: _s(0x27, 1, rs1, rs2, imm)
FADD_H   = lambda rd, rs1, rs2, rm=0: _r4(0x53, 2, 0x00, rs2, rs1, rm, rd)
FSUB_H   = lambda rd, rs1, rs2, rm=0: _r4(0x53, 2, 0x04, rs2, rs1, rm, rd)
FMUL_H   = lambda rd, rs1, rs2, rm=0: _r4(0x53, 2, 0x08, rs2, rs1, rm, rd)
FMADD_H  = lambda rd, rs1, rs2, rs3, rm=0: _r4(0x43, 2, rs3, rs2, rs1, rm, rd)
FMSUB_H  = lambda rd, rs1, rs2, rs3, rm=0: _r4(0x47, 2, rs3, rs2, rs1, rm, rd)
FNMSUB_H = lambda rd, rs1, rs2, rs3, rm=0: _r4(0x4B, 2, rs3, rs2, rs1, rm, rd)
FNMADD_H = lambda rd, rs1, rs2, rs3, rm=0: _r4(0x4F, 2, rs3, rs2, rs1, rm, rd)
FCVT_S_H = lambda rd, rs1, rm=0: _rv(0x53 | R(rd)<<7 | U(rm,3)<<12 | R(rs1)<<15 | 0x20<<25)
FCVT_H_S = lambda rd, rs1, rm=0: _rv(0x53 | R(rd)<<7 | U(rm,3)<<12 | R(rs1)<<15 | 2<<20 | 0x22<<25)

# -- pseudo-instructions -------------------------------------------------------
NOP    = lambda: ADDI(0, 0, 0)
LI     = lambda rd, imm: ADDI(rd, zero, imm)
MV     = lambda rd, rs: ADDI(rd, rs, 0)
NOT    = lambda rd, rs: XORI(rd, rs, -1)
NEG    = lambda rd, rs: SUB(rd, zero, rs)
SEQZ   = lambda rd, rs: SLTIU(rd, rs, 1)
SNEZ   = lambda rd, rs: SLTU(rd, zero, rs)
SGTZ   = lambda rd, rs: SLT(rd, zero, rs)
SLTZ   = lambda rd, rs: SLT(rd, rs, zero)
BEQZ   = lambda rs, imm: BEQ(rs, zero, imm)
BNEZ   = lambda rs, imm: BNE(rs, zero, imm)
BLEZ   = lambda rs, imm: BGE(zero, rs, imm)
BGEZ   = lambda rs, imm: BGE(rs, zero, imm)
BLTZ   = lambda rs, imm: BLT(rs, zero, imm)
BGTZ   = lambda rs, imm: BLT(zero, rs, imm)
J      = lambda imm: JAL(zero, imm)
JR     = lambda rs: JALR(zero, rs, 0)
RET    = lambda: JALR(zero, ra, 0)
CALL   = lambda imm: JAL(ra, imm)
ZEXT_B = lambda rd, rs: ANDI(rd, rs, 0xFF)
FMV_S  = lambda rd, rs: FSGNJ_S(rd, rs, rs)
FABS_S = lambda rd, rs: FSGNJX_S(rd, rs, rs)
FNEG_S = lambda rd, rs: FSGNJN_S(rd, rs, rs)

# -- .ttinsn encoding ----------------------------------------------------------
def TTINSN(imm32):
  assert imm32 < 0xC0000000, f".ttinsn requires imm32 < 0xC0000000, got 0x{imm32:08x}"
  return RiscVInsn(((imm32 << 2) | (imm32 >> 30)) & 0xFFFFFFFF)

# ==============================================================================
# Tensix coprocessor ISA — opcode in bits[31:24], params in bits[23:0]
# ==============================================================================
def _tt(op, p=0):
  if p != (p & 0xFFFFFF): raise ValueError(f"Tensix params overflow: 0x{p:x} doesn't fit in 24 bits")
  return TensixInsn((op << 24) | p)

# flow control / MOP / replay
TT_NOP     = lambda: _tt(0x02)
TT_MOP     = lambda mop_type, loop_count, zmask_lo16_or_loop_count: _tt(0x01, U(mop_type,1)<<23 | U(loop_count,7)<<16 | U(zmask_lo16_or_loop_count,16))
TT_MOP_CFG = lambda zmask_hi16: _tt(0x03, U(zmask_hi16,16))
TT_REPLAY  = lambda start_idx, len, execute_while_loading=0, load_mode=0: _tt(0x04, U(start_idx,10)<<14 | U(len,10)<<4 | U(execute_while_loading,1)<<1 | U(load_mode,1))
TT_RESOURCEDECL = lambda linger_time, resources, op_class: _tt(0x05, U(linger_time,11)<<13 | U(resources,9)<<4 | U(op_class,4))
# sync unit
TT_ATGETM     = lambda mutex_index: _tt(0xA0, U(mutex_index,24))
TT_ATRELM     = lambda mutex_index: _tt(0xA1, U(mutex_index,24))
TT_STALLWAIT  = lambda stall_res, wait_res: _tt(0xA2, U(stall_res,9)<<15 | U(wait_res,15))
TT_SEMINIT    = lambda max_value, init_value, sem_sel: _tt(0xA3, U(max_value,4)<<20 | U(init_value,4)<<16 | U(sem_sel,8)<<2)
TT_SEMPOST    = lambda sem_sel: _tt(0xA4, U(sem_sel,8)<<2)
TT_SEMGET     = lambda sem_sel: _tt(0xA5, U(sem_sel,8)<<2)
TT_SEMWAIT    = lambda stall_res, sem_sel, wait_sem_cond: _tt(0xA6, U(stall_res,9)<<15 | U(sem_sel,8)<<2 | U(wait_sem_cond,2))
TT_STREAMWAIT = lambda stall_res, target_value, target_sel, wait_stream_sel: _tt(0xA7, U(stall_res,9)<<15 | U(target_value,10)<<4 | U(target_sel,1)<<3 | U(wait_stream_sel,2))
# config unit
TT_WRCFG        = lambda GprAddress, wr128b, CfgReg: _tt(0xB0, U(GprAddress,6)<<16 | U(wr128b,1)<<15 | U(CfgReg,11))
TT_RDCFG        = lambda GprAddress, CfgReg: _tt(0xB1, U(GprAddress,6)<<16 | U(CfgReg,11))
TT_SETC16       = lambda setc16_reg, setc16_value: _tt(0xB2, U(setc16_reg,8)<<16 | U(setc16_value,16))
TT_RMWCIB0      = lambda Mask, Data, CfgRegAddr: _tt(0xB3, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
TT_RMWCIB1      = lambda Mask, Data, CfgRegAddr: _tt(0xB4, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
TT_RMWCIB2      = lambda Mask, Data, CfgRegAddr: _tt(0xB5, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
TT_RMWCIB3      = lambda Mask, Data, CfgRegAddr: _tt(0xB6, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
TT_STREAMWRCFG  = lambda stream_id_sel, StreamRegAddr, CfgReg: _tt(0xB7, U(stream_id_sel,2)<<21 | U(StreamRegAddr,10)<<11 | U(CfgReg,11))
TT_CFGSHIFTMASK = lambda disable_mask_on_old_val, operation, mask_width, right_cshift_amt, scratch_sel, CfgReg: _tt(0xB8,
  U(disable_mask_on_old_val,1)<<23 | U(operation,3)<<20 | U(mask_width,5)<<15 | U(right_cshift_amt,5)<<10 | U(scratch_sel,2)<<8 | U(CfgReg,8))
# matrix unit / FPU
TT_ZEROACC   = lambda clear_mode, use_32_bit_mode, clear_zero_flags, addr_mode, where: _tt(0x10,
  U(clear_mode,5)<<19 | U(use_32_bit_mode,1)<<18 | U(clear_zero_flags,1)<<17 | U(addr_mode,3)<<14 | U(where,14))
TT_ZEROSRC   = lambda zero_val, write_mode, bank_mask, src_mask: _tt(0x11, U(zero_val,20)<<4 | U(write_mode,1)<<3 | U(bank_mask,1)<<2 | U(src_mask,2))
TT_MOVA2D    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x12, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
TT_MOVB2D    = lambda dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst: _tt(0x13, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(movb2d_instr_mod,3)<<11 | U(dst,11))
TT_TRNSPSRCA = lambda: _tt(0x14)
TT_RAREB     = lambda: _tt(0x15)
TT_TRNSPSRCB = lambda: _tt(0x16)
TT_SHIFTXA   = lambda log2_amount2, shift_mode: _tt(0x17, U(log2_amount2,22)<<2 | U(shift_mode,2))
TT_SHIFTXB   = lambda addr_mode, rot_shift, shift_row: _tt(0x18, U(addr_mode,3)<<14 | U(rot_shift,4)<<10 | U(shift_row,10))
TT_SETASHRMH0 = lambda reg_mask, halo_mask: _tt(0x1A, U(reg_mask,23)<<1 | U(halo_mask,1))
TT_SETASHRMH1 = lambda reg_mask, halo_mask: _tt(0x1B, U(reg_mask,23)<<1 | U(halo_mask,1))
TT_SETASHRMV  = lambda reg_mask2: _tt(0x1C, U(reg_mask2,24))
TT_SETPKEDGOF = lambda y_end, y_start, x_end, x_start: _tt(0x1D, U(y_end,4)<<12 | U(y_start,4)<<8 | U(x_end,4)<<4 | U(x_start,4))
TT_SETASHRMH  = lambda reg_mask, halo_mask: _tt(0x1E, U(reg_mask,23)<<1 | U(halo_mask,1))
TT_CLREXPHIST = lambda: _tt(0x21)
TT_CONV3S1  = lambda clear_dvalid, rotate_weights, addr_mode, dst: _tt(0x22, U(clear_dvalid,2)<<22 | U(rotate_weights,5)<<17 | U(addr_mode,3)<<14 | U(dst,14))
TT_CONV3S2  = lambda clear_dvalid, rotate_weights, addr_mode, dst: _tt(0x23, U(clear_dvalid,2)<<22 | U(rotate_weights,5)<<17 | U(addr_mode,3)<<14 | U(dst,14))
TT_MFCONV3S1 = lambda clear_dvalid, rotate_weights, addr_mode, dst: _tt(0x24, U(clear_dvalid,2)<<22 | U(rotate_weights,5)<<17 | U(addr_mode,3)<<14 | U(dst,14))
TT_APOOL3S1 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x25, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
TT_MVMUL    = lambda clear_dvalid, instr_mod19, addr_mode, dst: _tt(0x26, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(addr_mode,2)<<14 | U(dst,10))
TT_ELWMUL   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x27, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
TT_ELWADD   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x28, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
TT_DOTPV    = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x29, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
TT_MPOOL3S2 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x2A, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
TT_ELWSUB   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x30, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
TT_MPOOL3S1 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x31, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
TT_APOOL3S2 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x32, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
TT_GMPOOL   = lambda clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst: _tt(0x33, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(pool_addr_mode,4)<<15 | U(max_pool_index_en,1)<<14 | U(dst,14))
TT_GAPOOL   = lambda clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst: _tt(0x34, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(pool_addr_mode,4)<<15 | U(max_pool_index_en,1)<<14 | U(dst,14))
TT_GATESRCRST  = lambda reset_srcb_gate_control, reset_srca_gate_control: _tt(0x35, U(reset_srcb_gate_control,1)<<1 | U(reset_srca_gate_control,1))
TT_CLEARDVALID = lambda cleardvalid, reset: _tt(0x36, U(cleardvalid,2)<<22 | U(reset,22))
# read/write counters
TT_SETRWC   = lambda clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask: _tt(0x37, U(clear_ab_vld,2)<<22 | U(rwc_cr,4)<<18 | U(rwc_d,4)<<14 | U(rwc_b,4)<<10 | U(rwc_a,4)<<6 | U(BitMask,6))
TT_INCRWC   = lambda rwc_cr, rwc_d, rwc_b, rwc_a: _tt(0x38, U(rwc_cr,3)<<18 | U(rwc_d,4)<<14 | U(rwc_b,4)<<10 | U(rwc_a,4)<<6)
TT_SETIBRWC = lambda rwc_cr, rwc_bias, set_inc_ctrl: _tt(0x39, U(rwc_cr,3)<<18 | U(rwc_bias,12)<<6 | U(set_inc_ctrl,6))
# data moves
TT_MOVD2A    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x08, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
TT_MOVDBGA2D = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x09, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
TT_MOVD2B    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x0A, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
TT_MOVB2A    = lambda srca, addr_mode, instr_mod, srcb: _tt(0x0B, U(srca,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(srcb,12))
TT_MOVDBGB2D = lambda dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst: _tt(0x0C, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(movb2d_instr_mod,3)<<11 | U(dst,11))
TT_SETDVALID = lambda setvalid: _tt(0x57, U(setvalid,24))
# packer / unpacker / mover
TT_XMOV = lambda Mov_block_selection, Last: _tt(0x40, U(Mov_block_selection,1)<<23 | U(Last,23))
TT_PACR = lambda CfgContext, RowPadZero, DstAccessMode, AddrMode, AddrCntContext, ZeroWrite, ReadIntfSel, OvrdThreadId, Concat, CtxtCtrl, Flush, Last: _tt(0x41,
  U(CfgContext,3)<<21 | U(RowPadZero,3)<<18 | U(DstAccessMode,1)<<17 | U(AddrMode,2)<<15 | U(AddrCntContext,2)<<13 | U(ZeroWrite,1)<<12 | U(ReadIntfSel,4)<<8 | U(OvrdThreadId,1)<<7 | U(Concat,3)<<4 | U(CtxtCtrl,2)<<2 | U(Flush,1)<<1 | U(Last,1))
TT_UNPACR = lambda Unpack_block_selection, AddrMode, CfgContextCntInc, CfgContextId, AddrCntContextId, OvrdThreadId, SetDatValid, srcb_bcast, ZeroWrite2, AutoIncContextID, RowSearch, SearchCacheFlush, Last: _tt(0x42,
  U(Unpack_block_selection,1)<<23 | U(AddrMode,8)<<15 | U(CfgContextCntInc,2)<<13 | U(CfgContextId,3)<<10 | U(AddrCntContextId,2)<<8 | U(OvrdThreadId,1)<<7 | U(SetDatValid,1)<<6 | U(srcb_bcast,1)<<5 | U(ZeroWrite2,1)<<4 | U(AutoIncContextID,1)<<3 | U(RowSearch,1)<<2 | U(SearchCacheFlush,1)<<1 | U(Last,1))
TT_UNPACR_NOP = lambda Unpacker_Select, Stream_Id, Msg_Clr_Cnt, Set_Dvalid, Clr_to1_fmt_Ctrl, Stall_Clr_Cntrl, Bank_Clr_Ctrl, Src_ClrVal_Ctrl, Unpack_Pop: _tt(0x43,
  U(Unpacker_Select,1)<<23 | U(Stream_Id,7)<<16 | U(Msg_Clr_Cnt,4)<<12 | U(Set_Dvalid,4)<<8 | U(Clr_to1_fmt_Ctrl,2)<<6 | U(Stall_Clr_Cntrl,1)<<5 | U(Bank_Clr_Ctrl,1)<<4 | U(Src_ClrVal_Ctrl,2)<<2 | U(Unpack_Pop,2))
TT_PACR_SETREG = lambda Push, ModeSel, Unused, DisableStall, AddrSel, StreamId, Flush, Last: _tt(0x4A,
  U(Push,1)<<23 | U(ModeSel,1)<<22 | U(Unused,10)<<12 | U(DisableStall,2)<<10 | U(AddrSel,2)<<8 | U(StreamId,6)<<2 | U(Flush,1)<<1 | U(Last,1))
# scalar unit (ThCon / DMA)
TT_RSTDMA    = lambda: _tt(0x44)
TT_SETDMAREG = lambda Payload_SigSelSize, Payload_SigSel, SetSignalsMode, RegIndex16b: _tt(0x45, U(Payload_SigSelSize,2)<<22 | U(Payload_SigSel,14)<<8 | U(SetSignalsMode,1)<<7 | U(RegIndex16b,7))
TT_FLUSHDMA  = lambda FlushSpec: _tt(0x46, U(FlushSpec,24))
TT_REG2FLOP  = lambda SizeSel, TargetSel, ByteOffset, ContextId_2, FlopIndex, RegIndex: _tt(0x48,
  U(SizeSel,2)<<22 | U(TargetSel,2)<<20 | U(ByteOffset,2)<<18 | U(ContextId_2,2)<<16 | U(FlopIndex,10)<<6 | U(RegIndex,6))
TT_LOADIND   = lambda SizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex: _tt(0x49, U(SizeSel,2)<<22 | U(OffsetIndex,8)<<14 | U(AutoIncSpec,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
TT_TBUFCMD   = lambda: _tt(0x4B)
TT_SETADC    = lambda CntSetMask, ChannelIndex, DimensionIndex, Value: _tt(0x50, U(CntSetMask,3)<<21 | U(ChannelIndex,1)<<20 | U(DimensionIndex,2)<<18 | U(Value,18))
TT_SETADCXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask: _tt(0x51, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6 | U(BitMask,6))
TT_INCADCXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X: _tt(0x52, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6)
TT_ADDRCRXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask: _tt(0x53, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6 | U(BitMask,6))
TT_SETADCZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask: _tt(0x54, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6 | U(BitMask,6))
TT_INCADCZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z: _tt(0x55, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6)
TT_ADDRCRZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask: _tt(0x56, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6 | U(BitMask,6))
TT_SETADCXX  = lambda CntSetMask, x_end2, x_start: _tt(0x5E, U(CntSetMask,3)<<21 | U(x_end2,11)<<10 | U(x_start,10))
TT_ADDDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x58, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
TT_SUBDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x59, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
TT_MULDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5A, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
TT_BITWOPDMAREG = lambda OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5B, U(OpBisConst,1)<<23 | U(OpSel,5)<<18 | U(ResultRegIndex,6)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
TT_SHIFTDMAREG  = lambda OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5C, U(OpBisConst,1)<<23 | U(OpSel,5)<<18 | U(ResultRegIndex,6)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
TT_CMPDMAREG    = lambda OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5D, U(OpBisConst,1)<<23 | U(OpSel,5)<<18 | U(ResultRegIndex,6)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
TT_DMANOP       = lambda: _tt(0x60)
TT_ATINCGET    = lambda MemHierSel, WrapVal, Sel32b, DataRegIndex, AddrRegIndex: _tt(0x61, U(MemHierSel,1)<<23 | U(WrapVal,9)<<14 | U(Sel32b,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
TT_ATINCGETPTR = lambda MemHierSel, NoIncr, IncrVal, WrapVal, Sel32b, DataRegIndex, AddrRegIndex: _tt(0x62, U(MemHierSel,1)<<23 | U(NoIncr,1)<<22 | U(IncrVal,4)<<18 | U(WrapVal,4)<<14 | U(Sel32b,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
TT_ATSWAP      = lambda MemHierSel, SwapMask, DataRegIndex, AddrRegIndex: _tt(0x63, U(MemHierSel,1)<<23 | U(SwapMask,9)<<14 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
TT_ATCAS       = lambda MemHierSel, SwapVal, CmpVal, Sel32b, DataRegIndex, AddrRegIndex: _tt(0x64, U(MemHierSel,1)<<23 | U(SwapVal,5)<<18 | U(CmpVal,4)<<14 | U(Sel32b,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
TT_STOREIND    = lambda MemHierSel, SizeSel, RegSizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex: _tt(0x66,
  U(MemHierSel,1)<<23 | U(SizeSel,1)<<22 | U(RegSizeSel,1)<<21 | U(OffsetIndex,7)<<14 | U(AutoIncSpec,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
TT_STOREREG    = lambda TdmaDataRegIndex, RegAddr: _tt(0x67, U(TdmaDataRegIndex,6)<<18 | U(RegAddr,18))
TT_LOADREG     = lambda TdmaDataRegIndex, RegAddr: _tt(0x68, U(TdmaDataRegIndex,6)<<18 | U(RegAddr,18))
# SFPU (vector unit)
TT_SFPLOAD     = lambda lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr: _tt(0x70, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(sfpu_addr_mode,3)<<13 | U(dest_reg_addr,13))
TT_SFPLOADI    = lambda lreg_ind, instr_mod0, imm16: _tt(0x71, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(imm16,16))
TT_SFPSTORE    = lambda lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr: _tt(0x72, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(sfpu_addr_mode,3)<<13 | U(dest_reg_addr,13))
TT_SFPLUT      = lambda lreg_ind, instr_mod0, dest_reg_addr: _tt(0x73, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(dest_reg_addr,16))
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
TT_SFPOR       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7F, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPNOT      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x80, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPLZ       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x81, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSETEXP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x82, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSETMAN   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x83, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPMAD      = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x84, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPADD      = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x85, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPMUL      = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x86, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPPUSHC    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x87, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPPOPC     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x88, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSETSGN   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x89, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPENCC     = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8A, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPCOMPC    = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8B, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPTRANSP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8C, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPXOR      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8D, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSTOCHRND = lambda rnd_mode, imm8_math, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x8E, U(rnd_mode,3)<<21 | U(imm8_math,8)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPNOP      = lambda: _tt(0x8F)
TT_SFPCAST     = lambda lreg_src_c, lreg_dest, instr_mod1: _tt(0x90, U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPCONFIG   = lambda imm16_math, config_dest, instr_mod1: _tt(0x91, U(imm16_math,16)<<8 | U(config_dest,4)<<4 | U(instr_mod1,4))
TT_SFPSWAP     = lambda imm12_math, lreg_src_c, lreg_dest, instr_mod1: _tt(0x92, U(imm12_math,12)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPLOADMACRO = lambda lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr: _tt(0x93, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(sfpu_addr_mode,3)<<13 | U(dest_reg_addr,13))
TT_SFPSHFT2    = lambda imm12_math, lreg_src_c, lreg_dest, instr_mod1: _tt(0x94, U(imm12_math,12)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPLUTFP32  = lambda lreg_dest, instr_mod1: _tt(0x95, U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPLE       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x96, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPGT       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x97, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPMUL24    = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x98, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
TT_SFPARECIP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x99, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))

# -- assembly helpers ----------------------------------------------------------
def Program(*insns):
  out = bytearray()
  for i in insns:
    if isinstance(i, TensixInsn): out += TTINSN(i.word).word.to_bytes(4, 'little')
    elif isinstance(i, Insn): out += i.word.to_bytes(4, 'little')
    else: out += i
  return bytes(out)
