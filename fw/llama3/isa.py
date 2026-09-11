from enum import IntEnum

class R(IntEnum):
  X0, X1, X2, X3, X4, X5, X6, X7 = range(8)
  X8, X9, X10, X11, X12, X13, X14, X15 = range(8, 16)
  X16, X17, X18, X19, X20, X21, X22, X23 = range(16, 24)
  X24, X25, X26, X27, X28, X29, X30, X31 = range(24, 32)
  ZERO, RA, SP, GP, TP, T0, T1, T2 = X0, X1, X2, X3, X4, X5, X6, X7
  S0, S1, A0, A1, A2, A3, A4, A5, A6, A7 = X8, X9, X10, X11, X12, X13, X14, X15, X16, X17
  S2, S3, S4, S5, S6, S7, S8, S9, S10, S11 = X18, X19, X20, X21, X22, X23, X24, X25, X26, X27
  T3, T4, T5, T6 = X28, X29, X30, X31

def _signed(value, bits, alignment=1):
  if value % alignment or not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
    raise ValueError(f"{value} does not fit in a signed {bits}-bit immediate")
  return value & ((1 << bits) - 1)

def _r(op, f3, f7, rd, rs1, rs2): return f7 << 25 | int(rs2) << 20 | int(rs1) << 15 | f3 << 12 | int(rd) << 7 | op
def _i(op, f3, rd, rs1, imm): return (_signed(imm, 12) << 20) | int(rs1) << 15 | f3 << 12 | int(rd) << 7 | op
def _iu(op, f3, rd, rs1, imm):
  if not 0 <= imm < 1 << 12: raise ValueError(f"{imm} does not fit in a 12-bit immediate")
  return imm << 20 | int(rs1) << 15 | f3 << 12 | int(rd) << 7 | op
def _s(op, f3, rs1, rs2, imm):
  imm = _signed(imm, 12)
  return (imm >> 5) << 25 | int(rs2) << 20 | int(rs1) << 15 | f3 << 12 | (imm & 0x1F) << 7 | op
def _b(op, f3, rs1, rs2, imm):
  imm = _signed(imm, 13, 2)
  return (imm >> 12) << 31 | ((imm >> 5) & 0x3F) << 25 | int(rs2) << 20 | int(rs1) << 15 | f3 << 12 | ((imm >> 1) & 0xF) << 8 | ((imm >> 11) & 1) << 7 | op
def _u(op, rd, imm): return imm & 0xFFFFF000 | int(rd) << 7 | op
def _j(op, rd, imm):
  imm = _signed(imm, 21, 2)
  return (imm >> 20) << 31 | ((imm >> 1) & 0x3FF) << 21 | ((imm >> 11) & 1) << 20 | ((imm >> 12) & 0xFF) << 12 | int(rd) << 7 | op

class RV32:
  def _emit(self, word: int): return word

  def add(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 0, 0x00, rd, rs1, rs2))
  def sub(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 0, 0x20, rd, rs1, rs2))
  def mul(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 0, 0x01, rd, rs1, rs2))
  def divu(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 5, 0x01, rd, rs1, rs2))
  def remu(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 7, 0x01, rd, rs1, rs2))
  def sltu(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 3, 0x00, rd, rs1, rs2))
  def min(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 4, 0x05, rd, rs1, rs2))
  def and_(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 7, 0x00, rd, rs1, rs2))
  def or_(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 6, 0x00, rd, rs1, rs2))
  def xor(self, rd: R, rs1: R, rs2: R): return self._emit(_r(0x33, 4, 0x00, rd, rs1, rs2))
  def addi(self, rd: R, rs1: R, imm: int): return self._emit(_i(0x13, 0, rd, rs1, imm))
  def sltiu(self, rd: R, rs1: R, imm: int): return self._emit(_i(0x13, 3, rd, rs1, imm))
  def andi(self, rd: R, rs1: R, imm: int): return self._emit(_i(0x13, 7, rd, rs1, imm))
  def ori(self, rd: R, rs1: R, imm: int): return self._emit(_i(0x13, 6, rd, rs1, imm))
  def xori(self, rd: R, rs1: R, imm: int): return self._emit(_i(0x13, 4, rd, rs1, imm))
  def slli(self, rd: R, rs1: R, shamt: int): return self._emit(_i(0x13, 1, rd, rs1, shamt))
  def srli(self, rd: R, rs1: R, shamt: int): return self._emit(_i(0x13, 5, rd, rs1, shamt))
  def srai(self, rd: R, rs1: R, shamt: int): return self._emit(_i(0x13, 5, rd, rs1, 0x400 | shamt))
  def lw(self, rd: R, rs1: R, offset: int = 0): return self._emit(_i(0x03, 2, rd, rs1, offset))
  def lbu(self, rd: R, rs1: R, offset: int = 0): return self._emit(_i(0x03, 4, rd, rs1, offset))
  def lhu(self, rd: R, rs1: R, offset: int = 0): return self._emit(_i(0x03, 5, rd, rs1, offset))
  def sb(self, rs2: R, rs1: R, offset: int = 0): return self._emit(_s(0x23, 0, rs1, rs2, offset))
  def sh(self, rs2: R, rs1: R, offset: int = 0): return self._emit(_s(0x23, 1, rs1, rs2, offset))
  def sw(self, rs2: R, rs1: R, offset: int = 0): return self._emit(_s(0x23, 2, rs1, rs2, offset))
  def beq(self, rs1: R, rs2: R, offset: int): return self._emit(_b(0x63, 0, rs1, rs2, offset))
  def bne(self, rs1: R, rs2: R, offset: int): return self._emit(_b(0x63, 1, rs1, rs2, offset))
  def blt(self, rs1: R, rs2: R, offset: int): return self._emit(_b(0x63, 4, rs1, rs2, offset))
  def bge(self, rs1: R, rs2: R, offset: int): return self._emit(_b(0x63, 5, rs1, rs2, offset))
  def bltu(self, rs1: R, rs2: R, offset: int): return self._emit(_b(0x63, 6, rs1, rs2, offset))
  def bgeu(self, rs1: R, rs2: R, offset: int): return self._emit(_b(0x63, 7, rs1, rs2, offset))
  def lui(self, rd: R, imm: int): return self._emit(_u(0x37, rd, imm))
  def auipc(self, rd: R, imm: int): return self._emit(_u(0x17, rd, imm))
  def jal(self, rd: R, offset: int): return self._emit(_j(0x6F, rd, offset))
  def jalr(self, rd: R, rs1: R, offset: int = 0): return self._emit(_i(0x67, 0, rd, rs1, offset))
  def csrrs(self, rd: R, rs1: R, csr: int): return self._emit(_iu(0x73, 2, rd, rs1, csr))
  def csrrc(self, rd: R, rs1: R, csr: int): return self._emit(_iu(0x73, 3, rd, rs1, csr))
  def fence(self): return self._emit(_i(0x0F, 0, R.ZERO, R.ZERO, 0x0FF))

class TensixWord(int): pass

class _Tensix:
  def _emit(self, word: int): return word

  def _tt(self, opcode, *fields):
    word = opcode << 24
    for value, hi, lo in fields:
      width = hi - lo + 1
      if not 0 <= int(value) < 1 << width: raise ValueError(f"{value} does not fit in bits {hi}:{lo}")
      word |= int(value) << lo
    if word >= 0xC0000000: raise ValueError(f"Tensix instruction looks like RISC-V: 0x{word:08x}")
    return self._emit(TensixWord(word))

  def TTADDDMAREG(self, OpBisConst: int = 0, ResultRegIndex: int = 0, OpBRegIndex: int = 0, OpARegIndex: int = 0):
    return self._tt(0x58, (OpBisConst, 23, 23), (ResultRegIndex, 22, 12), (OpBRegIndex, 11, 6), (OpARegIndex, 5, 0))
  def TTATGETM(self, mutex_index: int = 0): return self._tt(0xA0, (mutex_index, 23, 0))
  def TTATRELM(self, mutex_index: int = 0): return self._tt(0xA1, (mutex_index, 23, 0))
  def TTDMANOP(self): return self._tt(0x60)
  def TTELWADD(self, clear_dvalid: int = 0, dest_accum_en: int = 0, instr_mod19: int = 0, addr_mode: int = 0, dst: int = 0):
    return self._tt(0x28, (clear_dvalid, 23, 22), (dest_accum_en, 21, 21), (instr_mod19, 20, 19), (addr_mode, 18, 14), (dst, 13, 0))
  def TTELWMUL(self, clear_dvalid: int = 0, dest_accum_en: int = 0, instr_mod19: int = 0, addr_mode: int = 0, dst: int = 0):
    return self._tt(0x27, (clear_dvalid, 23, 22), (dest_accum_en, 21, 21), (instr_mod19, 20, 19), (addr_mode, 18, 14), (dst, 13, 0))
  def TTINCRWC(self, rwc_cr: int = 0, rwc_d: int = 0, rwc_b: int = 0, rwc_a: int = 0):
    return self._tt(0x38, (rwc_cr, 23, 18), (rwc_d, 17, 14), (rwc_b, 13, 10), (rwc_a, 9, 6))
  def TTMOP(self, mop_type: int = 0, loop_count: int = 0, zmask_lo16_or_loop_count: int = 0):
    return self._tt(0x01, (mop_type, 23, 23), (loop_count, 22, 16), (zmask_lo16_or_loop_count, 15, 0))
  def TTMOVA2D(self, dest_32b_lo: int = 0, src: int = 0, addr_mode: int = 0, instr_mod: int = 0, dst: int = 0):
    return self._tt(0x12, (dest_32b_lo, 23, 23), (src, 22, 17), (addr_mode, 16, 14), (instr_mod, 13, 12), (dst, 11, 0))
  def TTMULDMAREG(self, OpBisConst: int = 0, ResultRegIndex: int = 0, OpBRegIndex: int = 0, OpARegIndex: int = 0):
    return self._tt(0x5A, (OpBisConst, 23, 23), (ResultRegIndex, 22, 12), (OpBRegIndex, 11, 6), (OpARegIndex, 5, 0))
  def TTMVMUL(self, clear_dvalid: int = 0, instr_mod19: int = 0, addr_mode: int = 0, dst: int = 0):
    return self._tt(0x26, (clear_dvalid, 23, 22), (instr_mod19, 21, 19), (addr_mode, 18, 14), (dst, 13, 0))
  def TTNOP(self): return self._tt(0x02)
  def TTPACR(self, CfgContext: int = 0, RowPadZero: int = 0, DstAccessMode: int = 0, AddrMode: int = 0, AddrCntContext: int = 0, ZeroWrite: int = 0, ReadIntfSel: int = 0, OvrdThreadId: int = 0, Concat: int = 0, CtxtCtrl: int = 0, Flush: int = 0, Last: int = 0):
    return self._tt(0x41, (CfgContext, 23, 21), (RowPadZero, 20, 18), (DstAccessMode, 17, 17), (AddrMode, 16, 15), (AddrCntContext, 14, 13), (ZeroWrite, 12, 12), (ReadIntfSel, 11, 8), (OvrdThreadId, 7, 7), (Concat, 6, 4), (CtxtCtrl, 3, 2), (Flush, 1, 1), (Last, 0, 0))
  def TTRDCFG(self, GprAddress: int = 0, CfgReg: int = 0): return self._tt(0xB1, (GprAddress, 23, 16), (CfgReg, 15, 0))
  def TTREPLAY(self, start_idx: int = 0, len: int = 0, execute_while_loading: int = 0, load_mode: int = 0):
    return self._tt(0x04, (start_idx, 23, 14), (len, 13, 4), (execute_while_loading, 3, 1), (load_mode, 0, 0))
  def TTRMWCIB0(self, Mask: int = 0, Data: int = 0, CfgRegAddr: int = 0): return self._tt(0xB3, (Mask, 23, 16), (Data, 15, 8), (CfgRegAddr, 7, 0))
  def TTRMWCIB1(self, Mask: int = 0, Data: int = 0, CfgRegAddr: int = 0): return self._tt(0xB4, (Mask, 23, 16), (Data, 15, 8), (CfgRegAddr, 7, 0))
  def TTRMWCIB2(self, Mask: int = 0, Data: int = 0, CfgRegAddr: int = 0): return self._tt(0xB5, (Mask, 23, 16), (Data, 15, 8), (CfgRegAddr, 7, 0))
  def TTRMWCIB3(self, Mask: int = 0, Data: int = 0, CfgRegAddr: int = 0): return self._tt(0xB6, (Mask, 23, 16), (Data, 15, 8), (CfgRegAddr, 7, 0))
  def TTSEMGET(self, sem_sel: int = 0): return self._tt(0xA5, (sem_sel, 23, 2))
  def TTSEMINIT(self, max_value: int = 0, init_value: int = 0, sem_sel: int = 0):
    return self._tt(0xA3, (max_value, 23, 20), (init_value, 19, 16), (sem_sel, 15, 2))
  def TTSEMPOST(self, sem_sel: int = 0): return self._tt(0xA4, (sem_sel, 23, 2))
  def TTSEMWAIT(self, stall_res: int = 0, sem_sel: int = 0, wait_sem_cond: int = 0):
    return self._tt(0xA6, (stall_res, 23, 15), (sem_sel, 14, 2), (wait_sem_cond, 1, 0))
  def TTSETADC(self, CntSetMask: int = 0, ChannelIndex: int = 0, DimensionIndex: int = 0, Value: int = 0):
    return self._tt(0x50, (CntSetMask, 23, 21), (ChannelIndex, 20, 20), (DimensionIndex, 19, 18), (Value, 17, 0))
  def TTSETADCXX(self, CntSetMask: int = 0, x_end2: int = 0, x_start: int = 0):
    return self._tt(0x5E, (CntSetMask, 23, 21), (x_end2, 20, 10), (x_start, 9, 0))
  def TTSETADCXY(self, CntSetMask: int = 0, Ch1_Y: int = 0, Ch1_X: int = 0, Ch0_Y: int = 0, Ch0_X: int = 0, BitMask: int = 0):
    return self._tt(0x51, (CntSetMask, 23, 21), (Ch1_Y, 20, 15), (Ch1_X, 14, 12), (Ch0_Y, 11, 9), (Ch0_X, 8, 6), (BitMask, 5, 0))
  def TTSETADCZW(self, CntSetMask: int = 0, Ch1_W: int = 0, Ch1_Z: int = 0, Ch0_W: int = 0, Ch0_Z: int = 0, BitMask: int = 0):
    return self._tt(0x54, (CntSetMask, 23, 21), (Ch1_W, 20, 15), (Ch1_Z, 14, 12), (Ch0_W, 11, 9), (Ch0_Z, 8, 6), (BitMask, 5, 0))
  def TTSETC16(self, setc16_reg: int = 0, setc16_value: int = 0): return self._tt(0xB2, (setc16_reg, 23, 16), (setc16_value, 15, 0))
  def TTSETDMAREG(self, Payload_SigSelSize: int = 0, Payload_SigSel: int = 0, SetSignalsMode: int = 0, RegIndex16b: int = 0):
    return self._tt(0x45, (Payload_SigSelSize, 23, 22), (Payload_SigSel, 21, 8), (SetSignalsMode, 7, 7), (RegIndex16b, 6, 0))
  def TTSETRWC(self, clear_ab_vld: int = 0, rwc_cr: int = 0, rwc_d: int = 0, rwc_b: int = 0, rwc_a: int = 0, BitMask: int = 0):
    return self._tt(0x37, (clear_ab_vld, 23, 22), (rwc_cr, 21, 18), (rwc_d, 17, 14), (rwc_b, 13, 10), (rwc_a, 9, 6), (BitMask, 5, 0))
  def TTSFPADD(self, lreg_src_a: int = 0, lreg_src_b: int = 0, lreg_src_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x85, (lreg_src_a, 23, 16), (lreg_src_b, 15, 12), (lreg_src_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPADDI(self, imm16_math: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x75, (imm16_math, 23, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPARECIP(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x99, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPCAST(self, lreg_src_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x90, (lreg_src_c, 23, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPCONFIG(self, imm16_math: int = 0, config_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x91, (imm16_math, 23, 8), (config_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPENCC(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x8A, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPEXEXP(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x77, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPEXMAN(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x78, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPIADD(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x79, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPLOAD(self, lreg_ind: int = 0, instr_mod0: int = 0, sfpu_addr_mode: int = 0, dest_reg_addr: int = 0):
    return self._tt(0x70, (lreg_ind, 23, 20), (instr_mod0, 19, 16), (sfpu_addr_mode, 15, 13), (dest_reg_addr, 12, 0))
  def TTSFPLOADI(self, lreg_ind: int = 0, instr_mod0: int = 0, imm16: int = 0):
    return self._tt(0x71, (lreg_ind, 23, 20), (instr_mod0, 19, 16), (imm16, 15, 0))
  def TTSFPLUT(self, lreg_ind: int = 0, instr_mod0: int = 0, dest_reg_addr: int = 0):
    return self._tt(0x73, (lreg_ind, 23, 20), (instr_mod0, 19, 16), (dest_reg_addr, 15, 0))
  def TTSFPMAD(self, lreg_src_a: int = 0, lreg_src_b: int = 0, lreg_src_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x84, (lreg_src_a, 23, 16), (lreg_src_b, 15, 12), (lreg_src_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPMOV(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x7C, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPMUL(self, lreg_src_a: int = 0, lreg_src_b: int = 0, lreg_src_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x86, (lreg_src_a, 23, 16), (lreg_src_b, 15, 12), (lreg_src_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPNOP(self): return self._tt(0x8F)
  def TTSFPSETEXP(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x82, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPSHFT(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x7A, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPSHFT2(self, imm12_math: int = 0, lreg_src_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x94, (imm12_math, 23, 12), (lreg_src_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPSTORE(self, lreg_ind: int = 0, instr_mod0: int = 0, sfpu_addr_mode: int = 0, dest_reg_addr: int = 0):
    return self._tt(0x72, (lreg_ind, 23, 20), (instr_mod0, 19, 16), (sfpu_addr_mode, 15, 13), (dest_reg_addr, 12, 0))
  def TTSFPSWAP(self, imm12_math: int = 0, lreg_src_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x92, (imm12_math, 23, 12), (lreg_src_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSTALLWAIT(self, stall_res: int = 0, wait_res: int = 0): return self._tt(0xA2, (stall_res, 23, 15), (wait_res, 14, 0))
  def TTSTOREREG(self, TdmaDataRegIndex: int = 0, RegAddr: int = 0): return self._tt(0x67, (TdmaDataRegIndex, 23, 18), (RegAddr, 17, 0))
  def TTUNPACR(self, Unpack_block_selection: int = 0, AddrMode: int = 0, CfgContextCntInc: int = 0, CfgContextId: int = 0, AddrCntContextId: int = 0, OvrdThreadId: int = 0, SetDatValid: int = 0, srcb_bcast: int = 0, ZeroWrite2: int = 0, AutoIncContextID: int = 0, RowSearch: int = 0, SearchCacheFlush: int = 0, Last: int = 0):
    return self._tt(0x42, (Unpack_block_selection, 23, 23), (AddrMode, 22, 15), (CfgContextCntInc, 14, 13), (CfgContextId, 12, 10), (AddrCntContextId, 9, 8), (OvrdThreadId, 7, 7), (SetDatValid, 6, 6), (srcb_bcast, 5, 5), (ZeroWrite2, 4, 4), (AutoIncContextID, 3, 3), (RowSearch, 2, 2), (SearchCacheFlush, 1, 1), (Last, 0, 0))
  def TTUNPACR_NOP(self, Unpacker_Select: int = 0, Stream_Id: int = 0, Msg_Clr_Cnt: int = 0, Set_Dvalid: int = 0, Clr_to1_fmt_Ctrl: int = 0, Stall_Clr_Cntrl: int = 0, Bank_Clr_Ctrl: int = 0, Src_ClrVal_Ctrl: int = 0, Unpack_Pop: int = 0):
    return self._tt(0x43, (Unpacker_Select, 23, 23), (Stream_Id, 22, 16), (Msg_Clr_Cnt, 15, 12), (Set_Dvalid, 11, 8), (Clr_to1_fmt_Ctrl, 7, 6), (Stall_Clr_Cntrl, 5, 5), (Bank_Clr_Ctrl, 4, 4), (Src_ClrVal_Ctrl, 3, 2), (Unpack_Pop, 1, 0))
  def TTWRCFG(self, GprAddress: int = 0, wr128b: int = 0, CfgReg: int = 0):
    return self._tt(0xB0, (GprAddress, 23, 16), (wr128b, 15, 15), (CfgReg, 14, 0))
  def TTZEROACC(self, clear_mode: int = 0, use_32_bit_mode: int = 0, clear_zero_flags: int = 0, addr_mode: int = 0, where: int = 0):
    return self._tt(0x10, (clear_mode, 23, 19), (use_32_bit_mode, 18, 18), (clear_zero_flags, 17, 17), (addr_mode, 16, 14), (where, 13, 0))
  def TTZEROSRC(self, zero_val: int = 0, write_mode: int = 0, bank_mask: int = 0, src_mask: int = 0):
    return self._tt(0x11, (zero_val, 23, 4), (write_mode, 3, 3), (bank_mask, 2, 2), (src_mask, 1, 0))

  def TTADDRCRXY(self, CntSetMask: int = 0, Ch1_Y: int = 0, Ch1_X: int = 0, Ch0_Y: int = 0, Ch0_X: int = 0, BitMask: int = 0):
    return self._tt(0x53, (CntSetMask, 23, 21), (Ch1_Y, 20, 15), (Ch1_X, 14, 12), (Ch0_Y, 11, 9), (Ch0_X, 8, 6), (BitMask, 5, 0))
  def TTADDRCRZW(self, CntSetMask: int = 0, Ch1_W: int = 0, Ch1_Z: int = 0, Ch0_W: int = 0, Ch0_Z: int = 0, BitMask: int = 0):
    return self._tt(0x56, (CntSetMask, 23, 21), (Ch1_W, 20, 15), (Ch1_Z, 14, 12), (Ch0_W, 11, 9), (Ch0_Z, 8, 6), (BitMask, 5, 0))
  def TTAPOOL3S1(self, clear_dvalid: int = 0, pool_addr_mode: int = 0, index_en: int = 0, dst: int = 0):
    return self._tt(0x25, (clear_dvalid, 23, 22), (pool_addr_mode, 21, 15), (index_en, 14, 14), (dst, 13, 0))
  def TTAPOOL3S2(self, clear_dvalid: int = 0, pool_addr_mode: int = 0, index_en: int = 0, dst: int = 0):
    return self._tt(0x32, (clear_dvalid, 23, 22), (pool_addr_mode, 21, 15), (index_en, 14, 14), (dst, 13, 0))
  def TTATCAS(self, MemHierSel: int = 0, SwapVal: int = 0, CmpVal: int = 0, Sel32b: int = 0, DataRegIndex: int = 0, AddrRegIndex: int = 0):
    return self._tt(0x64, (MemHierSel, 23, 23), (SwapVal, 22, 18), (CmpVal, 17, 14), (Sel32b, 13, 12), (DataRegIndex, 11, 6), (AddrRegIndex, 5, 0))
  def TTATINCGET(self, MemHierSel: int = 0, WrapVal: int = 0, Sel32b: int = 0, DataRegIndex: int = 0, AddrRegIndex: int = 0):
    return self._tt(0x61, (MemHierSel, 23, 23), (WrapVal, 22, 14), (Sel32b, 13, 12), (DataRegIndex, 11, 6), (AddrRegIndex, 5, 0))
  def TTATINCGETPTR(self, MemHierSel: int = 0, NoIncr: int = 0, IncrVal: int = 0, WrapVal: int = 0, Sel32b: int = 0, DataRegIndex: int = 0, AddrRegIndex: int = 0):
    return self._tt(0x62, (MemHierSel, 23, 23), (NoIncr, 22, 22), (IncrVal, 21, 18), (WrapVal, 17, 14), (Sel32b, 13, 12), (DataRegIndex, 11, 6), (AddrRegIndex, 5, 0))
  def TTATSWAP(self, MemHierSel: int = 0, SwapMask: int = 0, DataRegIndex: int = 0, AddrRegIndex: int = 0):
    return self._tt(0x63, (MemHierSel, 23, 23), (SwapMask, 22, 14), (DataRegIndex, 13, 6), (AddrRegIndex, 5, 0))
  def TTBITWOPDMAREG(self, OpBisConst: int = 0, OpSel: int = 0, ResultRegIndex: int = 0, OpBRegIndex: int = 0, OpARegIndex: int = 0):
    return self._tt(0x5B, (OpBisConst, 23, 23), (OpSel, 22, 18), (ResultRegIndex, 17, 12), (OpBRegIndex, 11, 6), (OpARegIndex, 5, 0))
  def TTCFGSHIFTMASK(self, disable_mask_on_old_val: int = 0, operation: int = 0, mask_width: int = 0, right_cshift_amt: int = 0, scratch_sel: int = 0, CfgReg: int = 0):
    return self._tt(0xB8, (disable_mask_on_old_val, 23, 23), (operation, 22, 20), (mask_width, 19, 15), (right_cshift_amt, 14, 10), (scratch_sel, 9, 8), (CfgReg, 7, 0))
  def TTCLEARDVALID(self, cleardvalid: int = 0, reset: int = 0): return self._tt(0x36, (cleardvalid, 23, 22), (reset, 21, 0))
  def TTCLREXPHIST(self): return self._tt(0x21)
  def TTCMPDMAREG(self, OpBisConst: int = 0, OpSel: int = 0, ResultRegIndex: int = 0, OpBRegIndex: int = 0, OpARegIndex: int = 0):
    return self._tt(0x5D, (OpBisConst, 23, 23), (OpSel, 22, 18), (ResultRegIndex, 17, 12), (OpBRegIndex, 11, 6), (OpARegIndex, 5, 0))
  def TTCONV3S1(self, clear_dvalid: int = 0, rotate_weights: int = 0, addr_mode: int = 0, dst: int = 0):
    return self._tt(0x22, (clear_dvalid, 23, 22), (rotate_weights, 21, 17), (addr_mode, 16, 14), (dst, 13, 0))
  def TTCONV3S2(self, clear_dvalid: int = 0, rotate_weights: int = 0, addr_mode: int = 0, dst: int = 0):
    return self._tt(0x23, (clear_dvalid, 23, 22), (rotate_weights, 21, 17), (addr_mode, 16, 14), (dst, 13, 0))
  def TTDOTPV(self, clear_dvalid: int = 0, dest_accum_en: int = 0, instr_mod19: int = 0, addr_mode: int = 0, dst: int = 0):
    return self._tt(0x29, (clear_dvalid, 23, 22), (dest_accum_en, 21, 21), (instr_mod19, 20, 19), (addr_mode, 18, 14), (dst, 13, 0))
  def TTELWSUB(self, clear_dvalid: int = 0, dest_accum_en: int = 0, instr_mod19: int = 0, addr_mode: int = 0, dst: int = 0):
    return self._tt(0x30, (clear_dvalid, 23, 22), (dest_accum_en, 21, 21), (instr_mod19, 20, 19), (addr_mode, 18, 14), (dst, 13, 0))
  def TTFLUSHDMA(self, FlushSpec: int = 0): return self._tt(0x46, (FlushSpec, 23, 0))
  def TTGAPOOL(self, clear_dvalid: int = 0, instr_mod19: int = 0, pool_addr_mode: int = 0, max_pool_index_en: int = 0, dst: int = 0):
    return self._tt(0x34, (clear_dvalid, 23, 22), (instr_mod19, 21, 19), (pool_addr_mode, 18, 15), (max_pool_index_en, 14, 14), (dst, 13, 0))
  def TTGATESRCRST(self, reset_srcb_gate_control: int = 0, reset_srca_gate_control: int = 0):
    return self._tt(0x35, (reset_srcb_gate_control, 23, 1), (reset_srca_gate_control, 0, 0))
  def TTGMPOOL(self, clear_dvalid: int = 0, instr_mod19: int = 0, pool_addr_mode: int = 0, max_pool_index_en: int = 0, dst: int = 0):
    return self._tt(0x33, (clear_dvalid, 23, 22), (instr_mod19, 21, 19), (pool_addr_mode, 18, 15), (max_pool_index_en, 14, 14), (dst, 13, 0))
  def TTINCADCXY(self, CntSetMask: int = 0, Ch1_Y: int = 0, Ch1_X: int = 0, Ch0_Y: int = 0, Ch0_X: int = 0):
    return self._tt(0x52, (CntSetMask, 23, 21), (Ch1_Y, 20, 15), (Ch1_X, 14, 12), (Ch0_Y, 11, 9), (Ch0_X, 8, 6))
  def TTINCADCZW(self, CntSetMask: int = 0, Ch1_W: int = 0, Ch1_Z: int = 0, Ch0_W: int = 0, Ch0_Z: int = 0):
    return self._tt(0x55, (CntSetMask, 23, 21), (Ch1_W, 20, 15), (Ch1_Z, 14, 12), (Ch0_W, 11, 9), (Ch0_Z, 8, 6))
  def TTLOADIND(self, SizeSel: int = 0, OffsetIndex: int = 0, AutoIncSpec: int = 0, DataRegIndex: int = 0, AddrRegIndex: int = 0):
    return self._tt(0x49, (SizeSel, 23, 22), (OffsetIndex, 21, 14), (AutoIncSpec, 13, 12), (DataRegIndex, 11, 6), (AddrRegIndex, 5, 0))
  def TTLOADREG(self, TdmaDataRegIndex: int = 0, RegAddr: int = 0): return self._tt(0x68, (TdmaDataRegIndex, 23, 18), (RegAddr, 17, 0))
  def TTMFCONV3S1(self, clear_dvalid: int = 0, rotate_weights: int = 0, addr_mode: int = 0, dst: int = 0):
    return self._tt(0x3A, (clear_dvalid, 23, 22), (rotate_weights, 21, 17), (addr_mode, 16, 14), (dst, 13, 0))
  def TTMOP_CFG(self, zmask_hi16: int = 0): return self._tt(0x03, (zmask_hi16, 23, 0))
  def TTMOVB2A(self, srca: int = 0, addr_mode: int = 0, instr_mod: int = 0, srcb: int = 0):
    return self._tt(0x0B, (srca, 23, 17), (addr_mode, 16, 14), (instr_mod, 13, 12), (srcb, 11, 0))
  def TTMOVB2D(self, dest_32b_lo: int = 0, src: int = 0, addr_mode: int = 0, movb2d_instr_mod: int = 0, dst: int = 0):
    return self._tt(0x13, (dest_32b_lo, 23, 23), (src, 22, 17), (addr_mode, 16, 14), (movb2d_instr_mod, 13, 11), (dst, 10, 0))
  def TTMOVD2A(self, dest_32b_lo: int = 0, src: int = 0, addr_mode: int = 0, instr_mod: int = 0, dst: int = 0):
    return self._tt(0x08, (dest_32b_lo, 23, 23), (src, 22, 17), (addr_mode, 16, 14), (instr_mod, 13, 12), (dst, 11, 0))
  def TTMOVD2B(self, dest_32b_lo: int = 0, src: int = 0, addr_mode: int = 0, instr_mod: int = 0, dst: int = 0):
    return self._tt(0x0A, (dest_32b_lo, 23, 23), (src, 22, 17), (addr_mode, 16, 14), (instr_mod, 13, 12), (dst, 11, 0))
  def TTMOVDBGA2D(self, dest_32b_lo: int = 0, src: int = 0, addr_mode: int = 0, instr_mod: int = 0, dst: int = 0):
    return self._tt(0x09, (dest_32b_lo, 23, 23), (src, 22, 17), (addr_mode, 16, 14), (instr_mod, 13, 12), (dst, 11, 0))
  def TTMOVDBGB2D(self, dest_32b_lo: int = 0, src: int = 0, addr_mode: int = 0, movb2d_instr_mod: int = 0, dst: int = 0):
    return self._tt(0x0C, (dest_32b_lo, 23, 23), (src, 22, 17), (addr_mode, 16, 14), (movb2d_instr_mod, 13, 11), (dst, 10, 0))
  def TTMPOOL3S1(self, clear_dvalid: int = 0, pool_addr_mode: int = 0, index_en: int = 0, dst: int = 0):
    return self._tt(0x24, (clear_dvalid, 23, 22), (pool_addr_mode, 21, 15), (index_en, 14, 14), (dst, 13, 0))
  def TTMPOOL3S2(self, clear_dvalid: int = 0, pool_addr_mode: int = 0, index_en: int = 0, dst: int = 0):
    return self._tt(0x31, (clear_dvalid, 23, 22), (pool_addr_mode, 21, 15), (index_en, 14, 14), (dst, 13, 0))
  def TTPACR_SETREG(self, Push: int = 0, ModeSel: int = 0, Unused: int = 0, DisableStall: int = 0, AddrSel: int = 0, StreamId: int = 0, Flush: int = 0, Last: int = 0):
    return self._tt(0x4A, (Push, 23, 23), (ModeSel, 22, 22), (Unused, 21, 12), (DisableStall, 11, 10), (AddrSel, 9, 8), (StreamId, 7, 2), (Flush, 1, 1), (Last, 0, 0))
  def TTRAREB(self): return self._tt(0x15)
  def TTREG2FLOP(self, SizeSel: int = 0, TargetSel: int = 0, ByteOffset: int = 0, ContextId_2: int = 0, FlopIndex: int = 0, RegIndex: int = 0):
    return self._tt(0x48, (SizeSel, 23, 22), (TargetSel, 21, 20), (ByteOffset, 19, 18), (ContextId_2, 17, 16), (FlopIndex, 15, 6), (RegIndex, 5, 0))
  def TTRESOURCEDECL(self, linger_time: int = 0, resources: int = 0, op_class: int = 0):
    return self._tt(0x05, (linger_time, 23, 13), (resources, 12, 4), (op_class, 3, 0))
  def TTRSTDMA(self): return self._tt(0x44)
  def TTSETASHRMH(self, reg_mask: int = 0, halo_mask: int = 0): return self._tt(0x1E, (reg_mask, 23, 1), (halo_mask, 0, 0))
  def TTSETASHRMH0(self, reg_mask: int = 0, halo_mask: int = 0): return self._tt(0x1A, (reg_mask, 23, 1), (halo_mask, 0, 0))
  def TTSETASHRMH1(self, reg_mask: int = 0, halo_mask: int = 0): return self._tt(0x1B, (reg_mask, 23, 1), (halo_mask, 0, 0))
  def TTSETASHRMV(self, reg_mask2: int = 0): return self._tt(0x1C, (reg_mask2, 23, 0))
  def TTSETDVALID(self, setvalid: int = 0): return self._tt(0x57, (setvalid, 23, 0))
  def TTSETIBRWC(self, rwc_cr: int = 0, rwc_bias: int = 0, set_inc_ctrl: int = 0):
    return self._tt(0x39, (rwc_cr, 23, 18), (rwc_bias, 17, 6), (set_inc_ctrl, 5, 0))
  def TTSETPKEDGOF(self, y_end: int = 0, y_start: int = 0, x_end: int = 0, x_start: int = 0):
    return self._tt(0x1D, (y_end, 23, 12), (y_start, 11, 8), (x_end, 7, 4), (x_start, 3, 0))
  def TTSFPABS(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x7D, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPAND(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x7E, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPCOMPC(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x8B, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPDIVP2(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x76, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPGT(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x97, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPLE(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x96, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPLOADMACRO(self, lreg_ind: int = 0, instr_mod0: int = 0, sfpu_addr_mode: int = 0, dest_reg_addr: int = 0):
    return self._tt(0x93, (lreg_ind, 23, 20), (instr_mod0, 19, 16), (sfpu_addr_mode, 15, 13), (dest_reg_addr, 12, 0))
  def TTSFPLUTFP32(self, lreg_dest: int = 0, instr_mod1: int = 0): return self._tt(0x95, (lreg_dest, 23, 4), (instr_mod1, 3, 0))
  def TTSFPLZ(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x81, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPMUL24(self, lreg_src_a: int = 0, lreg_src_b: int = 0, lreg_src_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x98, (lreg_src_a, 23, 16), (lreg_src_b, 15, 12), (lreg_src_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPMULI(self, imm16_math: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x74, (imm16_math, 23, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPNOT(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x80, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPOR(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x7F, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPPOPC(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x88, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPPUSHC(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x87, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPSETCC(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x7B, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPSETMAN(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x83, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPSETSGN(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x89, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPSTOCHRND(self, rnd_mode: int = 0, imm8_math: int = 0, lreg_src_b: int = 0, lreg_src_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x8E, (rnd_mode, 23, 21), (imm8_math, 20, 16), (lreg_src_b, 15, 12), (lreg_src_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPTRANSP(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x8C, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSFPXOR(self, imm12_math: int = 0, lreg_c: int = 0, lreg_dest: int = 0, instr_mod1: int = 0):
    return self._tt(0x8D, (imm12_math, 23, 12), (lreg_c, 11, 8), (lreg_dest, 7, 4), (instr_mod1, 3, 0))
  def TTSHIFTDMAREG(self, OpBisConst: int = 0, OpSel: int = 0, ResultRegIndex: int = 0, OpBRegIndex: int = 0, OpARegIndex: int = 0):
    return self._tt(0x5C, (OpBisConst, 23, 23), (OpSel, 22, 18), (ResultRegIndex, 17, 12), (OpBRegIndex, 11, 6), (OpARegIndex, 5, 0))
  def TTSHIFTXA(self, log2_amount2: int = 0, shift_mode: int = 0): return self._tt(0x17, (log2_amount2, 23, 2), (shift_mode, 1, 0))
  def TTSHIFTXB(self, addr_mode: int = 0, rot_shift: int = 0, shift_row: int = 0):
    return self._tt(0x18, (addr_mode, 23, 14), (rot_shift, 13, 10), (shift_row, 9, 0))
  def TTSTOREIND(self, MemHierSel: int = 0, SizeSel: int = 0, RegSizeSel: int = 0, OffsetIndex: int = 0, AutoIncSpec: int = 0, DataRegIndex: int = 0, AddrRegIndex: int = 0):
    return self._tt(0x66, (MemHierSel, 23, 23), (SizeSel, 22, 22), (RegSizeSel, 21, 21), (OffsetIndex, 20, 14), (AutoIncSpec, 13, 12), (DataRegIndex, 11, 6), (AddrRegIndex, 5, 0))
  def TTSTREAMWAIT(self, stall_res: int = 0, target_value: int = 0, target_sel: int = 0, wait_stream_sel: int = 0):
    return self._tt(0xA7, (stall_res, 23, 15), (target_value, 14, 4), (target_sel, 3, 3), (wait_stream_sel, 2, 0))
  def TTSTREAMWRCFG(self, stream_id_sel: int = 0, StreamRegAddr: int = 0, CfgReg: int = 0):
    return self._tt(0xB7, (stream_id_sel, 23, 21), (StreamRegAddr, 20, 11), (CfgReg, 10, 0))
  def TTSUBDMAREG(self, OpBisConst: int = 0, ResultRegIndex: int = 0, OpBRegIndex: int = 0, OpARegIndex: int = 0):
    return self._tt(0x59, (OpBisConst, 23, 23), (ResultRegIndex, 22, 12), (OpBRegIndex, 11, 6), (OpARegIndex, 5, 0))
  def TTTBUFCMD(self): return self._tt(0x4B)
  def TTTRNSPSRCA(self): return self._tt(0x14)
  def TTTRNSPSRCB(self): return self._tt(0x16)
  def TTXMOV(self, Mov_block_selection: int = 0, Last: int = 0):
    return self._tt(0x40, (Mov_block_selection, 23, 23), (Last, 22, 0))

Tensix = _Tensix()
