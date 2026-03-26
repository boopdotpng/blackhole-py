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
def _amo(f5, aq, rl, rs2, rs1, f3, rd):
  return RiscVInsn(0x2F | R(rd)<<7 | f3<<12 | R(rs1)<<15 | R(rs2)<<20 | U(rl,1)<<25 | U(aq,1)<<26 | f5<<27)

# -- registers -----------------------------------------------------------------
zero, ra, sp, gp, tp = 0, 1, 2, 3, 4
t0, t1, t2 = 5, 6, 7
s0, fp, s1 = 8, 8, 9
a0, a1, a2, a3, a4, a5, a6, a7 = range(10, 18)
s2, s3, s4, s5, s6, s7, s8, s9, s10, s11 = range(18, 28)
t3, t4, t5, t6 = 28, 29, 30, 31

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
TT_MOP_CFG = lambda zmask_hi16: _tt(0x03, U(zmask_hi16,16))
  # zmask_hi16: upper 16 bits of the 32-bit zero-column mask for MOP
TT_REPLAY  = lambda start_idx, len, execute_while_loading=0, load_mode=0: _tt(0x04, U(start_idx,10)<<14 | U(len,10)<<4 | U(execute_while_loading,1)<<1 | U(load_mode,1))
  # start_idx: starting instruction index in the replay buffer (10b)
  # len: number of instructions to replay (10b)
  # execute_while_loading: 1=begin execution before buffer is fully loaded
  # load_mode: replay buffer load mode
TT_RESOURCEDECL = lambda linger_time, resources, op_class: _tt(0x05, U(linger_time,11)<<13 | U(resources,9)<<4 | U(op_class,4))
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
TT_STREAMWAIT = lambda stall_res, target_value, target_sel, wait_stream_sel: _tt(0xA7, U(stall_res,9)<<15 | U(target_value,10)<<4 | U(target_sel,1)<<3 | U(wait_stream_sel,2))
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
TT_RMWCIB0      = lambda Mask, Data, CfgRegAddr: _tt(0xB3, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
TT_RMWCIB1      = lambda Mask, Data, CfgRegAddr: _tt(0xB4, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
TT_RMWCIB2      = lambda Mask, Data, CfgRegAddr: _tt(0xB5, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
TT_RMWCIB3      = lambda Mask, Data, CfgRegAddr: _tt(0xB6, U(Mask,8)<<16 | U(Data,8)<<8 | U(CfgRegAddr,8))
  # Read-Modify-Write Config register, byte 0/1/2/3 respectively.
  # Mask: which bits to modify (8b), Data: new bit values (8b)
  # CfgRegAddr: config register address (8b)
TT_STREAMWRCFG  = lambda stream_id_sel, StreamRegAddr, CfgReg: _tt(0xB7, U(stream_id_sel,2)<<21 | U(StreamRegAddr,10)<<11 | U(CfgReg,11))
  # Write from a stream register into a config register
  # stream_id_sel: stream selector (2b), StreamRegAddr: stream reg (10b)
TT_CFGSHIFTMASK = lambda disable_mask_on_old_val, operation, mask_width, right_cshift_amt, scratch_sel, CfgReg: _tt(0xB8,
  U(disable_mask_on_old_val,1)<<23 | U(operation,3)<<20 | U(mask_width,5)<<15 | U(right_cshift_amt,5)<<10 | U(scratch_sel,2)<<8 | U(CfgReg,8))
  # Shift-and-mask operation on a config register (for bitfield insertion/extraction)
  # operation: ALU op (3b), mask_width: number of bits (5b)
  # right_cshift_amt: circular right shift amount (5b)
  # scratch_sel: scratch register for intermediate (2b)
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
TT_MOVA2D    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x12, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
  # Move data from SrcA to Dest. src: SrcA register index (6b)
  # dest_32b_lo: select low 32b of dest row; instr_mod: format conversion mode
TT_MOVB2D    = lambda dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst: _tt(0x13, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(movb2d_instr_mod,3)<<11 | U(dst,11))
  # Move data from SrcB to Dest. src: SrcB register index (6b)
TT_TRNSPSRCA = lambda: _tt(0x14)   # dead — SrcA transpose not functional on Blackhole
TT_RAREB     = lambda: _tt(0x15)   # dead — not used in Blackhole
TT_TRNSPSRCB = lambda: _tt(0x16)   # Transpose SrcB rows 16-31 in-place (16x16 transpose)
TT_SHIFTXA   = lambda log2_amount2, shift_mode: _tt(0x17, U(log2_amount2,22)<<2 | U(shift_mode,2))
  # Shift SrcA data. log2_amount2: shift amount (22b encoding)
  # shift_mode: type of shift (row shift, etc.)
TT_SHIFTXB   = lambda addr_mode, rot_shift, shift_row: _tt(0x18, U(addr_mode,3)<<14 | U(rot_shift,4)<<10 | U(shift_row,10))
  # Shift/rotate SrcB data. rot_shift: rotation amount (4b)
  # shift_row: which row to shift (10b)
TT_SETASHRMH0 = lambda reg_mask, halo_mask: _tt(0x1A, U(reg_mask,23)<<1 | U(halo_mask,1))
TT_SETASHRMH1 = lambda reg_mask, halo_mask: _tt(0x1B, U(reg_mask,23)<<1 | U(halo_mask,1))
TT_SETASHRMV  = lambda reg_mask2: _tt(0x1C, U(reg_mask2,24))
TT_SETASHRMH  = lambda reg_mask, halo_mask: _tt(0x1E, U(reg_mask,23)<<1 | U(halo_mask,1))
  # SETASHRM{H0,H1,V,H}: configure auto-shift/mask registers for halo handling
  # in convolution operations. reg_mask: row mask (23b), halo_mask: enable halo (1b)
TT_SETPKEDGOF = lambda y_end, y_start, x_end, x_start: _tt(0x1D, U(y_end,4)<<12 | U(y_start,4)<<8 | U(x_end,4)<<4 | U(x_start,4))
  # Set packer edge offsets for handling tile boundaries
  # y_end/y_start/x_end/x_start: edge offsets (4b each)
TT_CLREXPHIST = lambda: _tt(0x21)  # Clear exponent histogram (used by SFPU for format tracking)
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
TT_ELWMUL   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x27, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
  # Element-wise multiply (SrcA * SrcB -> Dest)
TT_ELWADD   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x28, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
  # Element-wise add (SrcA + SrcB -> Dest)
TT_DOTPV    = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x29, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
  # Legacy matmul — prefer MVMUL. Functionally identical.
TT_MPOOL3S2 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x2A, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
  # dead — neutered on BH, behaves like GMPOOL on all-zero SrcA (was max pool 3x3 s2)
TT_ELWSUB   = lambda clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst: _tt(0x30, U(clear_dvalid,2)<<22 | U(dest_accum_en,1)<<21 | U(instr_mod19,2)<<19 | U(addr_mode,2)<<14 | U(dst,14))
  # Element-wise subtract (SrcA - SrcB -> Dest)
TT_MPOOL3S1 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x31, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
  # dead — neutered on BH, behaves like GMPOOL on all-zero SrcA (was max pool 3x3 s1)
TT_APOOL3S2 = lambda clear_dvalid, pool_addr_mode, index_en, dst: _tt(0x32, U(clear_dvalid,2)<<22 | U(pool_addr_mode,7)<<15 | U(index_en,1)<<14 | U(dst,14))
  # dead — neutered on BH, computes Dst += 0 only (was avg pool 3x3 stride 2 on GS)
TT_GMPOOL   = lambda clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst: _tt(0x33, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(pool_addr_mode,4)<<15 | U(max_pool_index_en,1)<<14 | U(dst,14))
  # Global max pooling
TT_GAPOOL   = lambda clear_dvalid, instr_mod19, pool_addr_mode, max_pool_index_en, dst: _tt(0x34, U(clear_dvalid,2)<<22 | U(instr_mod19,3)<<19 | U(pool_addr_mode,4)<<15 | U(max_pool_index_en,1)<<14 | U(dst,14))
  # Global average pooling
TT_GATESRCRST  = lambda reset_srcb_gate_control, reset_srca_gate_control: _tt(0x35, U(reset_srcb_gate_control,1)<<1 | U(reset_srca_gate_control,1))
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
TT_SETIBRWC = lambda rwc_cr, rwc_bias, set_inc_ctrl: _tt(0x39, U(rwc_cr,3)<<18 | U(rwc_bias,12)<<6 | U(set_inc_ctrl,6))
  # Set RWC bias and increment control. rwc_bias: base offset (12b)
  # set_inc_ctrl: auto-increment behavior selector (6b)
# -- data moves (between register files) ---------------------------------------
# Move data between SrcA, SrcB, and Dst register files. These are used for
# transpose, data reformatting, and feeding SFPU results back into FPU inputs.
TT_MOVD2A    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x08, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
  # Dst → SrcA. 1 or 4 aligned rows, 2-cycle latency. Requires manual STALLWAIT.
  # dest_32b_lo: select low 32b half; src: Dst row (6b); dst: SrcA row (12b)
TT_MOVDBGA2D = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x09, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
  # SrcA → Dst (debug variant of MOVA2D, skips SrcA bank ownership check)
TT_MOVD2B    = lambda dest_32b_lo, src, addr_mode, instr_mod, dst: _tt(0x0A, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(dst,12))
  # Dst → SrcB. 1 or 4 aligned rows, 3-cycle latency. Requires manual STALLWAIT.
  # Used in tile transpose: MOVD2B to SrcB[16:31], TRNSPSRCB, then MOVB2D back.
TT_MOVB2A    = lambda srca, addr_mode, instr_mod, srcb: _tt(0x0B, U(srca,6)<<17 | U(addr_mode,3)<<14 | U(instr_mod,2)<<12 | U(srcb,12))
  # SrcB → SrcA. Raw 19-bit copy, no format conversion. 4-cycle latency.
  # srca: SrcA dest row (6b), srcb: SrcB source row (12b)
TT_MOVDBGB2D = lambda dest_32b_lo, src, addr_mode, movb2d_instr_mod, dst: _tt(0x0C, U(dest_32b_lo,1)<<23 | U(src,6)<<17 | U(addr_mode,3)<<14 | U(movb2d_instr_mod,3)<<11 | U(dst,11))
  # SrcB → Dst (debug variant of MOVB2D, skips SrcB bank ownership check)
TT_SETDVALID = lambda setvalid: _tt(0x57, U(setvalid,24))
  # Set data-valid flags to transfer SrcA/SrcB bank ownership from unpacker to FPU.
  # Equivalent to UNPACR with FlipSrc=1 but without triggering an unpack.
# -- packer / unpacker / mover -------------------------------------------------
# Packers move data from Dst → L1 (with format conversion, ReLU, edge masking).
# Unpackers move data from L1 → SrcA/SrcB (with format conversion, decompress).
# The Mover (XMOV) handles L1 → L1 block moves for stream management.
TT_XMOV = lambda Mov_block_selection, Last: _tt(0x40, U(Mov_block_selection,1)<<23 | U(Last,23))
  # L1-to-L1 block mover. Mov_block_selection: which mover block to trigger
  # Last: signal completion (used for stream flow control)
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
TT_PACR_SETREG = lambda Push, ModeSel, Unused, DisableStall, AddrSel, StreamId, Flush, Last: _tt(0x4A,
  U(Push,1)<<23 | U(ModeSel,1)<<22 | U(Unused,10)<<12 | U(DisableStall,2)<<10 | U(AddrSel,2)<<8 | U(StreamId,6)<<2 | U(Flush,1)<<1 | U(Last,1))
  # Configure packer stream destination. Push: push data to stream
  # StreamId: target stream for packed output (6b)
# -- scalar unit (ThCon / DMA) -------------------------------------------------
# The Scalar Unit (ThCon = Thread Controller) provides integer ALU ops on
# 16-bit DMA registers, indirect memory access, and configuration register
# writes. It's the Tensix control plane — not a user-facing compute path.
# Each thread has 64 x 16-bit DMA registers (RegIndex 0-63).
TT_RSTDMA    = lambda: _tt(0x44)  # Reset DMA engine state
TT_SETDMAREG = lambda Payload_SigSelSize, Payload_SigSel, SetSignalsMode, RegIndex16b: _tt(0x45, U(Payload_SigSelSize,2)<<22 | U(Payload_SigSel,14)<<8 | U(SetSignalsMode,1)<<7 | U(RegIndex16b,7))
  # Load an immediate value into a DMA register, or set signal/control bits.
  # Payload_SigSelSize: 0=16b payload, 1=signal select, 2=extended
  # Payload_SigSel: immediate value or signal selector (14b)
  # SetSignalsMode: 1=set signals mode; RegIndex16b: target register (7b, 0-63)
TT_FLUSHDMA  = lambda FlushSpec: _tt(0x46, U(FlushSpec,24))
  # Flush DMA pipeline. FlushSpec selects which DMA channels/buffers to flush.
TT_REG2FLOP  = lambda SizeSel, TargetSel, ByteOffset, ContextId_2, FlopIndex, RegIndex: _tt(0x48,
  U(SizeSel,2)<<22 | U(TargetSel,2)<<20 | U(ByteOffset,2)<<18 | U(ContextId_2,2)<<16 | U(FlopIndex,10)<<6 | U(RegIndex,6))
  # Write DMA register to a config flop (register-mapped configuration).
  # SizeSel: 0=16b, 1=32b (uses 2 consecutive regs); TargetSel: target unit (2b)
  # FlopIndex: destination flop address (10b); RegIndex: source DMA reg (6b)
TT_LOADIND   = lambda SizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex: _tt(0x49, U(SizeSel,2)<<22 | U(OffsetIndex,8)<<14 | U(AutoIncSpec,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
  # Indirect load: read memory at address in AddrRegIndex + offset into DataRegIndex.
  # SizeSel: 0=16b, 1=32b; OffsetIndex: byte offset table index (8b)
  # AutoIncSpec: auto-increment addr reg after load (2b)
TT_TBUFCMD   = lambda: _tt(0x4B)  # dead — tile buffer command, not used on Blackhole
# -- ADC (Address Counters) ----------------------------------------------------
# ADCs provide multi-dimensional address generation for pack/unpack operations.
# Each has X, Y, Z, W dimensions across 2 channels (Ch0, Ch1).
# CntSetMask selects which counter sets to modify (3b bitmask).
TT_SETADC    = lambda CntSetMask, ChannelIndex, DimensionIndex, Value: _tt(0x50, U(CntSetMask,3)<<21 | U(ChannelIndex,1)<<20 | U(DimensionIndex,2)<<18 | U(Value,18))
  # Set a single ADC dimension to an absolute value (18b)
TT_SETADCXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask: _tt(0x51, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6 | U(BitMask,6))
  # Set X/Y dimensions for both channels simultaneously
TT_INCADCXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X: _tt(0x52, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6)
  # Increment X/Y dimensions for both channels
TT_ADDRCRXY  = lambda CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask: _tt(0x53, U(CntSetMask,3)<<21 | U(Ch1_Y,6)<<15 | U(Ch1_X,3)<<12 | U(Ch0_Y,3)<<9 | U(Ch0_X,3)<<6 | U(BitMask,6))
  # Address counter read + conditional reset for X/Y
TT_SETADCZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask: _tt(0x54, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6 | U(BitMask,6))
  # Set Z/W dimensions for both channels
TT_INCADCZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z: _tt(0x55, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6)
  # Increment Z/W dimensions
TT_ADDRCRZW  = lambda CntSetMask, Ch1_W, Ch1_Z, Ch0_W, Ch0_Z, BitMask: _tt(0x56, U(CntSetMask,3)<<21 | U(Ch1_W,6)<<15 | U(Ch1_Z,3)<<12 | U(Ch0_W,3)<<9 | U(Ch0_Z,3)<<6 | U(BitMask,6))
  # Address counter read + conditional reset for Z/W
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
TT_SUBDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x59, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
  # Result = OpA - OpB
TT_MULDMAREG    = lambda OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5A, U(OpBisConst,1)<<23 | U(ResultRegIndex,11)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
  # Result = OpA * OpB
TT_BITWOPDMAREG = lambda OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5B, U(OpBisConst,1)<<23 | U(OpSel,5)<<18 | U(ResultRegIndex,6)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
  # Bitwise op on DMA regs. OpSel selects AND/OR/XOR/NOT etc. (5b)
TT_SHIFTDMAREG  = lambda OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5C, U(OpBisConst,1)<<23 | U(OpSel,5)<<18 | U(ResultRegIndex,6)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
  # Shift DMA reg. OpSel selects left/right/arithmetic (5b)
TT_CMPDMAREG    = lambda OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex: _tt(0x5D, U(OpBisConst,1)<<23 | U(OpSel,5)<<18 | U(ResultRegIndex,6)<<12 | U(OpBRegIndex,6)<<6 | U(OpARegIndex,6))
  # Compare DMA regs. OpSel selects EQ/NE/LT/GE etc. (5b)
TT_DMANOP       = lambda: _tt(0x60)  # DMA no-op, occupies one scalar unit slot
# -- atomic memory ops (scalar unit) -------------------------------------------
# Atomic read-modify-write ops on L1 memory via DMA registers.
# MemHierSel: 0=L1, 1=register space; DataRegIndex/AddrRegIndex: DMA reg pair
TT_ATINCGET    = lambda MemHierSel, WrapVal, Sel32b, DataRegIndex, AddrRegIndex: _tt(0x61, U(MemHierSel,1)<<23 | U(WrapVal,9)<<14 | U(Sel32b,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
  # Atomic increment-and-get. WrapVal: wrap-around value (9b)
  # Sel32b: 0=16b, 1=32b access
TT_ATINCGETPTR = lambda MemHierSel, NoIncr, IncrVal, WrapVal, Sel32b, DataRegIndex, AddrRegIndex: _tt(0x62, U(MemHierSel,1)<<23 | U(NoIncr,1)<<22 | U(IncrVal,4)<<18 | U(WrapVal,4)<<14 | U(Sel32b,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
  # Atomic increment-and-get with configurable increment.
  # NoIncr: 1=read without incrementing; IncrVal: increment amount (4b)
TT_ATSWAP      = lambda MemHierSel, SwapMask, DataRegIndex, AddrRegIndex: _tt(0x63, U(MemHierSel,1)<<23 | U(SwapMask,9)<<14 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
  # Atomic swap: exchange memory value with DMA register value
TT_ATCAS       = lambda MemHierSel, SwapVal, CmpVal, Sel32b, DataRegIndex, AddrRegIndex: _tt(0x64, U(MemHierSel,1)<<23 | U(SwapVal,5)<<18 | U(CmpVal,4)<<14 | U(Sel32b,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
  # Atomic compare-and-swap. If mem[addr]==CmpVal, set to SwapVal.
TT_STOREIND    = lambda MemHierSel, SizeSel, RegSizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex: _tt(0x66,
  U(MemHierSel,1)<<23 | U(SizeSel,1)<<22 | U(RegSizeSel,1)<<21 | U(OffsetIndex,7)<<14 | U(AutoIncSpec,2)<<12 | U(DataRegIndex,6)<<6 | U(AddrRegIndex,6))
  # Indirect store: write DataReg to memory at AddrReg + offset.
  # SizeSel: memory access size; RegSizeSel: register access size
TT_STOREREG    = lambda TdmaDataRegIndex, RegAddr: _tt(0x67, U(TdmaDataRegIndex,6)<<18 | U(RegAddr,18))
  # Store DMA register to a register-mapped address (18b absolute address)
TT_LOADREG     = lambda TdmaDataRegIndex, RegAddr: _tt(0x68, U(TdmaDataRegIndex,6)<<18 | U(RegAddr,18))
  # Load from register-mapped address into DMA register
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
TT_SFPLUT      = lambda lreg_ind, instr_mod0, dest_reg_addr: _tt(0x73, U(lreg_ind,4)<<20 | U(instr_mod0,4)<<16 | U(dest_reg_addr,16))
  # 8-bit coefficient LUT: VD = LUT[i]*Abs(LReg[3]) + LUT_offset[i]
  # where i ∈ {0,1,2} depends on magnitude of LReg[3] (3-piece approx)
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
TT_SFPOR       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x7F, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Bitwise OR: VD = VB | VC
TT_SFPNOT      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x80, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Bitwise NOT: VD = ~VC
TT_SFPLZ       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x81, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Count leading zeros: VD = CLZ(VC). Also sets CC flags (VC != 0, VC == 0).
TT_SFPSETEXP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x82, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Replace exponent: VD = {VC.Sign, Imm8 or VD.Exp or VD.Mant&255, VC.Mant}
TT_SFPSETMAN   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x83, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Replace mantissa: VD = {VC.Sign, VC.Exp, VD.Mant or Imm12<<11}
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
TT_SFPTRANSP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8C, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # 4x4 transpose within LReg lane groups (LReg[0:4] and LReg[4:8])
TT_SFPXOR      = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x8D, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Bitwise XOR: VD ^= VC
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
TT_SFPLE       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x96, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Less-or-equal: set flags based on VD <= VC. Total ordering: -NaN < -Inf < ... < +Inf < +NaN
TT_SFPGT       = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x97, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Greater-than: set flags based on VD > VC. Same total ordering as SFPLE.
# Integer multiply (BH-new)
TT_SFPMUL24    = lambda lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1: _tt(0x98, U(lreg_src_a,4)<<16 | U(lreg_src_b,4)<<12 | U(lreg_src_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # 24-bit integer multiply: VD = (VA*VB) & 0x7FFFFF (lower) or >> 23 (upper)
  # Supports both two's complement and sign-magnitude inputs.
# Approximate reciprocal (BH-new)
TT_SFPARECIP   = lambda imm12_math, lreg_c, lreg_dest, instr_mod1: _tt(0x99, U(imm12_math,12)<<12 | U(lreg_c,4)<<8 | U(lreg_dest,4)<<4 | U(instr_mod1,4))
  # Approx 1/VC (7-bit accuracy), or approx e^Abs(VC) with sign copy

# -- assembly helpers ----------------------------------------------------------
def Program(*insns):
  """Assemble a sequence of instructions into a flat bytes object.
  TensixInsn objects are automatically wrapped in TTINSN encoding.
  RiscVInsn objects are emitted directly. Raw bytes are passed through."""
  out = bytearray()
  for i in insns:
    if isinstance(i, TensixInsn): out += TTINSN(i.word).word.to_bytes(4, 'little')
    elif isinstance(i, Insn): out += i.word.to_bytes(4, 'little')
    else: out += i
  return bytes(out)
