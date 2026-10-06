# Tensix coprocessor and baby RISC-V instruction tables, shaped for tinygrad-style Ops.INS lowering:
#   UOp(Ops.INS, src=operands, arg=(TensixOps.SFPMAD, dtype), tag=(dst_reg,))
# the enum names the instruction, the table below says how its fields pack into a 32-bit word, encode() packs it.
# A Tensix word is pushed by storing it to INSTRN_BUF (0xFFE40000) as is, or placed inline in RISC-V code via ttinsn().
#
# Field layouts are (name, low bit, width), listed high bit -> low bit, the same order as the TT_OP_* macros.
# Bit positions are from tt-llk/tt_llk_blackhole/instructions/assembly.yaml, names and widths from tt-isa-documentation.
# Naming conventions, the same in every instruction:
#   dest_row / srca_row / srcb_row   a row in the Dest / SrcA / SrcB register file (named by register file, not by direction)
#   a, b, c, dst                     SFPU LReg operands: dst = a * b + c (SFPMAD), dst = op(c) for unary ops
#   mod                              the instruction modifier (instr_mod0 / instr_mod1 / instr_mod19 in the yaml)
#   imm                              an immediate operand
#   addr_mod                         index of the ADDR_MOD_* config slot that advances the RWC / ADC counters
#   clear_dvalid                     2-bit {srcb, srca} mask: release the source bank to the unpacker when done
#   counter_mask                     which address counters: 1 unpacker0, 2 unpacker1, 4 packer
#   block_mask                       STALLWAIT/SEMWAIT: which units are stalled while waiting
#   *_reg                            a register index (TDMA GPR, config register, ...), never a value
from enum import Enum, auto

class TensixOps(Enum):
  # instruction stream: macro-op expander, replay buffer, resource hints
  MOP = auto(); MOP_CFG = auto(); REPLAY = auto(); RESOURCEDECL = auto()
  NOP = auto(); DMANOP = auto(); SFPNOP = auto()
  # matrix unit (FPU): math
  MVMUL = auto(); ELWMUL = auto(); ELWADD = auto(); ELWSUB = auto(); DOTPV = auto()
  GMPOOL = auto(); GAPOOL = auto(); MPOOL3S1 = auto(); APOOL3S1 = auto(); MPOOL3S2 = auto(); APOOL3S2 = auto()
  CONV3S1 = auto(); CONV3S2 = auto(); MFCONV3S1 = auto()
  # matrix unit: moves between Dest / SrcA / SrcB and source register control
  MOVD2A = auto(); MOVD2B = auto(); MOVA2D = auto(); MOVB2A = auto(); MOVB2D = auto(); MOVDBGA2D = auto(); MOVDBGB2D = auto()
  ZEROACC = auto(); ZEROSRC = auto(); TRNSPSRCA = auto(); TRNSPSRCB = auto(); RAREB = auto(); SHIFTXA = auto(); SHIFTXB = auto()
  SETASHRMH0 = auto(); SETASHRMH1 = auto(); SETASHRMH = auto(); SETASHRMV = auto(); SETPKEDGOF = auto(); CLREXPHIST = auto()
  GATESRCRST = auto(); SETDVALID = auto(); CLEARDVALID = auto()
  # register-window counters (RWC) that address Dest / SrcA / SrcB for math
  SETRWC = auto(); INCRWC = auto(); SETIBRWC = auto()
  # pack / unpack / xmov
  PACR = auto(); PACR_SETREG = auto(); UNPACR = auto(); UNPACR_NOP = auto(); XMOV = auto()
  # address counters (ADC) that address L1 for pack / unpack
  SETADC = auto(); SETADCXY = auto(); SETADCZW = auto(); SETADCXX = auto()
  INCADCXY = auto(); INCADCZW = auto(); ADDRCRXY = auto(); ADDRCRZW = auto()
  # TDMA GPRs: set, arithmetic, load/store, atomics
  SETDMAREG = auto(); ADDDMAREG = auto(); SUBDMAREG = auto(); MULDMAREG = auto(); BITWOPDMAREG = auto(); SHIFTDMAREG = auto(); CMPDMAREG = auto()
  RSTDMA = auto(); FLUSHDMA = auto(); REG2FLOP = auto(); LOADIND = auto(); STOREIND = auto(); LOADREG = auto(); STOREREG = auto(); TBUFCMD = auto()
  ATINCGET = auto(); ATINCGETPTR = auto(); ATSWAP = auto(); ATCAS = auto()
  # vector unit (SFPU)
  SFPLOAD = auto(); SFPLOADI = auto(); SFPSTORE = auto(); SFPLOADMACRO = auto(); SFPLUT = auto(); SFPLUTFP32 = auto(); SFPCONFIG = auto()
  SFPMAD = auto(); SFPADD = auto(); SFPMUL = auto(); SFPMUL24 = auto(); SFPMULI = auto(); SFPADDI = auto(); SFPDIVP2 = auto(); SFPARECIP = auto()
  SFPEXEXP = auto(); SFPEXMAN = auto(); SFPSETEXP = auto(); SFPSETMAN = auto(); SFPSETSGN = auto(); SFPABS = auto(); SFPLZ = auto()
  SFPIADD = auto(); SFPSHFT = auto(); SFPSHFT2 = auto(); SFPAND = auto(); SFPOR = auto(); SFPXOR = auto(); SFPNOT = auto()
  SFPMOV = auto(); SFPSWAP = auto(); SFPTRANSP = auto(); SFPCAST = auto(); SFP_STOCH_RND = auto()
  SFPSETCC = auto(); SFPENCC = auto(); SFPCOMPC = auto(); SFPPUSHC = auto(); SFPPOPC = auto(); SFPLE = auto(); SFPGT = auto()
  # sync: mutexes, semaphores, stalls
  ATGETM = auto(); ATRELM = auto(); STALLWAIT = auto(); SEMINIT = auto(); SEMPOST = auto(); SEMGET = auto(); SEMWAIT = auto(); STREAMWAIT = auto()
  # config registers
  WRCFG = auto(); RDCFG = auto(); SETC16 = auto(); RMWCIB0 = auto(); RMWCIB1 = auto(); RMWCIB2 = auto(); RMWCIB3 = auto()
  STREAMWRCFG = auto(); CFGSHIFTMASK = auto()

class RV32Ops(Enum):
  LUI = auto(); AUIPC = auto(); JAL = auto(); JALR = auto()
  BEQ = auto(); BNE = auto(); BLT = auto(); BGE = auto(); BLTU = auto(); BGEU = auto()
  LB = auto(); LH = auto(); LW = auto(); LBU = auto(); LHU = auto(); SB = auto(); SH = auto(); SW = auto()
  ADDI = auto(); SLTI = auto(); SLTIU = auto(); XORI = auto(); ORI = auto(); ANDI = auto(); SLLI = auto(); SRLI = auto(); SRAI = auto()
  ADD = auto(); SUB = auto(); SLL = auto(); SLT = auto(); SLTU = auto(); XOR = auto(); SRL = auto(); SRA = auto(); OR = auto(); AND = auto()
  MUL = auto(); MULH = auto(); MULHSU = auto(); MULHU = auto(); DIV = auto(); DIVU = auto(); REM = auto(); REMU = auto()  # M
  SH1ADD = auto(); SH2ADD = auto(); SH3ADD = auto(); MIN = auto()  # Zba, Zbb min
  CSRRW = auto(); CSRRS = auto(); CSRRC = auto(); CSRRWI = auto(); CSRRSI = auto(); CSRRCI = auto()  # Zicsr
  FENCE = auto(); ECALL = auto(); EBREAK = auto()

T = TensixOps

# shared layouts
FPU_ELW = (("clear_dvalid", 22, 2), ("accumulate", 21, 1), ("srcb_bcast", 19, 2), ("addr_mod", 14, 5), ("dest_row", 0, 14))
FPU_POOL = (("clear_dvalid", 22, 2), ("mode", 19, 3), ("addr_mod", 15, 4), ("argmax", 14, 1), ("dest_row", 0, 14))
FPU_POOL3 = (("clear_dvalid", 22, 2), ("addr_mod", 15, 7), ("argmax", 14, 1), ("dest_row", 0, 14))
FPU_CONV3 = (("clear_dvalid", 22, 2), ("rotate_weights", 17, 5), ("addr_mod", 14, 3), ("dest_row", 0, 14))
MOV_DEST_SRCA = (("dest_32b_lo", 23, 1), ("srca_row", 17, 6), ("addr_mod", 14, 3), ("row_mode", 12, 2), ("dest_row", 0, 12))
MOV_DEST_SRCB = (("dest_32b_lo", 23, 1), ("srcb_row", 17, 6), ("addr_mod", 14, 3), ("row_mode", 12, 2), ("dest_row", 0, 12))
MOV_B2D = (("dest_32b_lo", 23, 1), ("srcb_row", 17, 6), ("addr_mod", 14, 3), ("row_mode", 11, 3), ("dest_row", 0, 11))
SET_ASHR_H = (("reg_mask", 1, 23), ("halo_mask", 0, 1))
ADC_XY = (("counter_mask", 21, 3), ("y1", 15, 6), ("x1", 12, 3), ("y0", 9, 3), ("x0", 6, 3), ("set_mask", 0, 6))
ADC_ZW = (("counter_mask", 21, 3), ("w1", 15, 6), ("z1", 12, 3), ("w0", 9, 3), ("z0", 6, 3), ("set_mask", 0, 6))
DMA_ARITH = (("b_is_imm", 23, 1), ("result_reg", 12, 11), ("b_reg", 6, 6), ("a_reg", 0, 6))
DMA_ALU = (("b_is_imm", 23, 1), ("op", 18, 5), ("result_reg", 12, 6), ("b_reg", 6, 6), ("a_reg", 0, 6))
SFPU_MEM = lambda lreg: ((lreg, 20, 4), ("mod", 16, 4), ("addr_mod", 13, 3), ("dest_row", 0, 13))
SFPU_C = (("imm", 12, 12), ("c", 8, 4), ("dst", 4, 4), ("mod", 0, 4))        # dst = op(c, imm)
SFPU_BC = (("b", 12, 4), ("c", 8, 4), ("dst", 4, 4), ("mod", 0, 4))          # dst = op(b, c)
SFPU_ABC = (("a", 16, 4), ("b", 12, 4), ("c", 8, 4), ("dst", 4, 4), ("mod", 0, 4))  # dst = a * b + c
SFPU_IMM16 = (("imm", 8, 16), ("dst", 4, 4), ("mod", 0, 4))
RMWCIB = (("mask", 16, 8), ("data", 8, 8), ("cfg_reg", 0, 8))

# name: (opcode, fields)
TENSIX = {
  # mask_lo is the low 16 bits of the unpack z-mask (template 0), or the inner/outer loop counts (template 1)
  T.MOP: (0x01, (("template", 23, 1), ("count", 16, 7), ("mask_lo", 0, 16))),
  T.MOP_CFG: (0x03, (("mask_hi", 0, 16),)),
  # load=1: capture the next `count` instructions into replay_buffer[start:], exec=1 also runs them while capturing
  T.REPLAY: (0x04, (("start", 14, 10), ("count", 4, 10), ("exec", 1, 1), ("load", 0, 1))),
  T.RESOURCEDECL: (0x05, (("linger_time", 13, 11), ("resources", 4, 9), ("op_class", 0, 4))),
  T.NOP: (0x02, ()), T.DMANOP: (0x60, ()), T.SFPNOP: (0x8F, ()),

  # mode: 0 compute 4 rows, 1 compute 1 row (Blackhole yaml)
  T.MVMUL: (0x26, (("clear_dvalid", 22, 2), ("mode", 19, 3), ("addr_mod", 14, 5), ("dest_row", 0, 14))),
  # srcb_bcast: 0 none, 1 broadcast column 0, 2 broadcast row 0, 3 both. accumulate: add into Dest instead of overwrite
  T.ELWMUL: (0x27, FPU_ELW), T.ELWADD: (0x28, FPU_ELW), T.ELWSUB: (0x30, FPU_ELW), T.DOTPV: (0x29, FPU_ELW),
  # mode: 0 one row wide, 1 16x16 wide. argmax: also produce the index of the max
  T.GMPOOL: (0x33, FPU_POOL), T.GAPOOL: (0x34, FPU_POOL),
  T.MPOOL3S1: (0x24, FPU_POOL3), T.APOOL3S1: (0x25, FPU_POOL3), T.MPOOL3S2: (0x31, FPU_POOL3), T.APOOL3S2: (0x32, FPU_POOL3),
  T.CONV3S1: (0x22, FPU_CONV3), T.CONV3S2: (0x23, FPU_CONV3), T.MFCONV3S1: (0x3A, FPU_CONV3),

  # row_mode: 0 one row, 2 four rows (A2D: eight rows). MOVB2D row_mode bits: 0 broadcast datum 0, 1 broadcast row to 8, 2 four rows
  T.MOVD2A: (0x08, MOV_DEST_SRCA), T.MOVA2D: (0x12, MOV_DEST_SRCA), T.MOVDBGA2D: (0x09, MOV_DEST_SRCA),
  T.MOVD2B: (0x0A, MOV_DEST_SRCB), T.MOVB2D: (0x13, MOV_B2D), T.MOVDBGB2D: (0x0C, MOV_B2D),
  T.MOVB2A: (0x0B, (("srca_row", 17, 7), ("addr_mod", 14, 3), ("row_mode", 12, 2), ("srcb_row", 0, 12))),
  # clear_mode: 0 one row at dest_row, 1 one face, 2 half of Dest, 3 all of Dest. clear_zero_flags: mark rows nonzero instead
  T.ZEROACC: (0x10, (("clear_mode", 19, 5), ("dest_32b", 18, 1), ("clear_zero_flags", 17, 1), ("addr_mod", 14, 3), ("dest_row", 0, 14))),
  # srcs: 1 SrcA, 2 SrcB. read_bank: clear the bank math reads (1) or the one the unpacker writes (0). neg_inf: fill -inf, not 0
  T.ZEROSRC: (0x11, (("neg_inf", 4, 20), ("read_bank", 3, 1), ("all_banks", 2, 1), ("srcs", 0, 2))),
  T.TRNSPSRCA: (0x14, ()), T.TRNSPSRCB: (0x16, ()), T.RAREB: (0x15, ()), T.CLREXPHIST: (0x21, ()),
  T.SHIFTXA: (0x17, (("log2_amount", 2, 22), ("direction", 0, 2))),
  T.SHIFTXB: (0x18, (("addr_mod", 14, 10), ("shift_in_zero", 10, 4), ("srcb_row", 0, 10))),
  T.SETASHRMH0: (0x1A, SET_ASHR_H), T.SETASHRMH1: (0x1B, SET_ASHR_H), T.SETASHRMH: (0x1E, SET_ASHR_H),
  T.SETASHRMV: (0x1C, (("reg_mask", 0, 24),)),
  T.SETPKEDGOF: (0x1D, (("y_end", 12, 12), ("y_start", 8, 4), ("x_end", 4, 4), ("x_start", 0, 4))),
  T.GATESRCRST: (0x35, (("reset_srcb_gate", 1, 1), ("reset_srca_gate", 0, 1))),
  T.SETDVALID: (0x57, (("set_dvalid", 0, 2),)),
  # reset bit 0: clear all dvalid and reset bank ids. bit 1: clear dvalid without switching bank
  T.CLEARDVALID: (0x36, (("clear_dvalid", 22, 2), ("reset", 0, 22))),

  # set_mask bits: 0 srca, 1 srcb, 2 dest, 3 fidelity phase clear, 4-5 SFPU. cr_mask bits: 0 srca, 1 srcb, 2 dest, 3 dest counter-to-cr
  T.SETRWC: (0x37, (("clear_dvalid", 22, 2), ("cr_mask", 18, 4), ("dest", 14, 4), ("srcb", 10, 4), ("srca", 6, 4), ("set_mask", 0, 6))),
  T.INCRWC: (0x38, (("cr_mask", 18, 3), ("dest", 14, 4), ("srcb", 10, 4), ("srca", 6, 4))),
  T.SETIBRWC: (0x39, (("cr_mask", 18, 6), ("bias", 6, 12), ("bias_ctrl", 0, 6))),

  # dest_read_mask: which of the 4 Dest read interfaces (0 = all). dest_strided: read Dest rows [0,8,16,24] instead of [0,1,2,3]
  T.PACR: (0x41, (("cfg_ctx", 21, 3), ("row_pad_zero", 18, 3), ("dest_strided", 17, 1), ("addr_mod", 15, 2), ("addr_cnt_ctx", 13, 2),
                  ("zero_write", 12, 1), ("dest_read_mask", 8, 4), ("ovrd_thread", 7, 1), ("concat", 4, 3), ("ctx_ctrl", 2, 2),
                  ("flush", 1, 1), ("last", 0, 1))),
  T.PACR_SETREG: (0x4A, (("push", 23, 1), ("mode_sel", 22, 1), ("disable_stall", 10, 2), ("addr_sel", 8, 2), ("stream_id", 2, 6),
                         ("flush", 1, 1), ("last", 0, 1))),
  # addr_mod bits: 0 cr, 1-2 ch0 z inc, 3-4 ch0 y inc, 5-6 ch1 z inc, 7 ch1 y inc. srcb_bcast: copy the first row into 8 rows of SrcB
  # multi_context: read config from context cfg_ctx (+ ThreadCfg.unpack{n}_context), or the context counter if use_context_counter
  T.UNPACR: (0x42, (("unpacker", 23, 1), ("addr_mod", 15, 8), ("cfg_ctx_inc", 13, 2), ("cfg_ctx", 10, 3), ("addr_cnt_ctx", 8, 2),
                    ("multi_context", 7, 1), ("set_dvalid", 6, 1), ("srcb_bcast", 5, 1), ("zero_write", 4, 1), ("use_context_counter", 3, 1),
                    ("row_search", 2, 1), ("search_cache_flush", 1, 1), ("last", 0, 1))),
  # op: 0 pop the overlay buffer, 1 clear a source bank, 3 pop for stream. the clr_* fields apply when op is 1
  T.UNPACR_NOP: (0x43, (("unpacker", 23, 1), ("stream", 16, 7), ("msg_clr_cnt", 12, 4), ("set_dvalid", 8, 4), ("clr_fmt", 6, 2),
                        ("clr_stall_mode", 5, 1), ("clr_all_banks", 4, 1), ("clr_val", 2, 2), ("op", 0, 2))),
  T.XMOV: (0x40, (("mover", 23, 1), ("last", 0, 1))),

  # counter_mask: 1 unpacker0, 2 unpacker1, 4 packer. dim: 0 x, 1 y, 2 z, 3 w
  T.SETADC: (0x50, (("counter_mask", 21, 3), ("channel", 20, 1), ("dim", 18, 2), ("value", 0, 18))),
  T.SETADCXY: (0x51, ADC_XY), T.ADDRCRXY: (0x53, ADC_XY), T.INCADCXY: (0x52, ADC_XY[:-1]),
  T.SETADCZW: (0x54, ADC_ZW), T.ADDRCRZW: (0x56, ADC_ZW), T.INCADCZW: (0x55, ADC_ZW[:-1]),
  T.SETADCXX: (0x5E, (("counter_mask", 21, 3), ("x_end", 10, 11), ("x_start", 0, 10))),

  # TDMA GPRs. reg is in 16-bit units. from_signals: payload picks a 16-bit chunk of hardware signals, signals_size its width
  T.SETDMAREG: (0x45, (("signals_size", 22, 2), ("payload", 8, 14), ("from_signals", 7, 1), ("reg", 0, 7))),
  T.ADDDMAREG: (0x58, DMA_ARITH), T.SUBDMAREG: (0x59, DMA_ARITH), T.MULDMAREG: (0x5A, DMA_ARITH),
  T.BITWOPDMAREG: (0x5B, DMA_ALU),  # op: 0 and, 1 or, 2 xor
  T.SHIFTDMAREG: (0x5C, DMA_ALU),   # op: 0 left, 1 right
  T.CMPDMAREG: (0x5D, DMA_ALU),     # op: 0 a>b, 1 a<b, 2 a==b
  T.RSTDMA: (0x44, ()), T.TBUFCMD: (0x4B, ()),
  T.FLUSHDMA: (0x46, (("flush_mask", 0, 24),)),
  # target: 0 TDMA regs, 1 local regs, 2 context regs. size: 0 16B, 1 32b, 2 16b, 3 8b
  T.REG2FLOP: (0x48, (("size", 22, 2), ("target", 20, 2), ("byte_offset", 18, 2), ("ctx", 16, 2), ("flop", 6, 10), ("reg", 0, 6))),
  # auto_inc: 0 none, 1 +2B, 2 +4B, 3 +16B. size: 0 16B, 1 32b, 2 16b, 3 8b
  T.LOADIND: (0x49, (("size", 22, 2), ("offset_reg", 14, 8), ("auto_inc", 12, 2), ("data_reg", 6, 6), ("addr_reg", 0, 6))),
  T.STOREIND: (0x66, (("l1", 23, 1), ("size", 22, 1), ("to_srcb", 21, 1), ("offset_reg", 14, 7), ("auto_inc", 12, 2), ("data_reg", 6, 6), ("addr_reg", 0, 6))),
  T.LOADREG: (0x68, (("data_reg", 18, 6), ("reg_addr", 0, 18))),
  T.STOREREG: (0x67, (("data_reg", 18, 6), ("reg_addr", 0, 18))),
  # atomics on L1 (l1=1) or data RAM. word: which 32-bit word of the 16B line. wrap_log2: the value wraps at 1 << wrap_log2
  T.ATINCGET: (0x61, (("l1", 23, 1), ("wrap_log2", 14, 9), ("word", 12, 2), ("data_reg", 6, 6), ("addr_reg", 0, 6))),
  T.ATINCGETPTR: (0x62, (("l1", 23, 1), ("no_incr", 22, 1), ("incr_log2", 18, 4), ("wrap_log2", 14, 4), ("word", 12, 2), ("data_reg", 6, 6), ("addr_reg", 0, 6))),
  T.ATSWAP: (0x63, (("l1", 23, 1), ("swap_mask", 14, 9), ("data_reg", 6, 8), ("addr_reg", 0, 6))),
  T.ATCAS: (0x64, (("l1", 23, 1), ("swap", 18, 5), ("cmp", 14, 4), ("word", 12, 2), ("data_reg", 6, 6), ("addr_reg", 0, 6))),

  # SFPU. mod on load/store is the data format: 0 default, 1 fp16a, 2 fp16b, 3 fp32, 4 int32, 5 int8, 6 lo16, 12 int32 sign-magnitude
  T.SFPLOAD: (0x70, SFPU_MEM("dst")), T.SFPSTORE: (0x72, SFPU_MEM("src")),
  T.SFPLOADI: (0x71, (("dst", 20, 4), ("mod", 16, 4), ("imm", 0, 16))),
  # runs macro `macro` from the SFPU macro slots. the destination LReg is split: dst_lo in bits 20-21, dst_hi in bit 0
  T.SFPLOADMACRO: (0x93, (("macro", 22, 2), ("dst_lo", 20, 2), ("mod", 16, 4), ("addr_mod", 13, 3), ("dest_row", 1, 12), ("dst_hi", 0, 1))),
  T.SFPLUT: (0x73, (("dst", 20, 4), ("mod", 16, 4))),
  T.SFPLUTFP32: (0x95, (("dst", 4, 4), ("mod", 0, 4))),
  # config_reg: 0-3 macro instruction slots, 4-7 macro sequence slots, 8 lane-enable / misc, 15 LaneConfig
  T.SFPCONFIG: (0x91, (("imm", 8, 16), ("config_reg", 4, 4), ("mod", 0, 4))),
  T.SFPMAD: (0x84, SFPU_ABC), T.SFPADD: (0x85, SFPU_ABC), T.SFPMUL: (0x86, SFPU_ABC), T.SFPMUL24: (0x98, SFPU_ABC),
  T.SFPMULI: (0x74, SFPU_IMM16), T.SFPADDI: (0x75, SFPU_IMM16),
  T.SFPDIVP2: (0x76, SFPU_C), T.SFPEXEXP: (0x77, SFPU_C), T.SFPEXMAN: (0x78, SFPU_C), T.SFPIADD: (0x79, SFPU_C), T.SFPSHFT: (0x7A, SFPU_C),
  T.SFPSETCC: (0x7B, SFPU_C), T.SFPMOV: (0x7C, SFPU_C), T.SFPABS: (0x7D, SFPU_C), T.SFPNOT: (0x80, SFPU_C), T.SFPLZ: (0x81, SFPU_C),
  T.SFPSETEXP: (0x82, SFPU_C), T.SFPSETMAN: (0x83, SFPU_C), T.SFPSETSGN: (0x89, SFPU_C), T.SFPXOR: (0x8D, SFPU_C),
  T.SFPLE: (0x96, SFPU_C), T.SFPGT: (0x97, SFPU_C), T.SFPSWAP: (0x92, SFPU_C),
  T.SFPAND: (0x7E, SFPU_BC), T.SFPOR: (0x7F, SFPU_BC), T.SFPARECIP: (0x99, SFPU_BC),
  T.SFPSHFT2: (0x94, SFPU_C),  # some modes read the imm bits as a b LReg index
  T.SFPENCC: (0x8A, SFPU_C), T.SFPCOMPC: (0x8B, SFPU_C), T.SFPPUSHC: (0x87, SFPU_C), T.SFPPOPC: (0x88, SFPU_C), T.SFPTRANSP: (0x8C, SFPU_C),
  T.SFPCAST: (0x90, (("c", 8, 4), ("dst", 4, 4), ("mod", 0, 4))),
  # round_mode: 0 nearest, 1 stochastic. imm is the int8 descale, used instead of b when mod bit 3 is set
  T.SFP_STOCH_RND: (0x8E, (("round_mode", 21, 3), ("imm", 16, 5), ("b", 12, 4), ("c", 8, 4), ("dst", 4, 4), ("mod", 0, 4))),

  # mutex: 0 math, 2 unpack0, 3 unpack1, 4 pack0
  T.ATGETM: (0xA0, (("mutex", 0, 24),)), T.ATRELM: (0xA1, (("mutex", 0, 24),)),
  # block_mask: units stalled until every condition in wait_mask is met
  T.STALLWAIT: (0xA2, (("block_mask", 15, 9), ("wait_mask", 0, 15))),
  # sem_mask is one-hot over semaphores 0..7
  T.SEMINIT: (0xA3, (("max", 20, 4), ("init", 16, 4), ("sem_mask", 2, 8))),
  T.SEMPOST: (0xA4, (("sem_mask", 2, 8),)), T.SEMGET: (0xA5, (("sem_mask", 2, 8),)),
  # wait_cond: 1 wait while the semaphore is 0, 2 wait while it is at max
  T.SEMWAIT: (0xA6, (("block_mask", 15, 9), ("sem_mask", 2, 8), ("wait_cond", 0, 2))),
  # target_is_msgs: target counts received messages (1) or is a phase number (0)
  T.STREAMWAIT: (0xA7, (("block_mask", 15, 9), ("target", 4, 11), ("target_is_msgs", 3, 1), ("stream_sel", 0, 3))),

  # gpr is a Tensix thread GPR index; cfg_reg is a 32-bit config register index
  T.WRCFG: (0xB0, (("gpr", 16, 8), ("is_128b", 15, 1), ("cfg_reg", 0, 15))),
  T.RDCFG: (0xB1, (("gpr", 16, 8), ("cfg_reg", 0, 16))),
  T.SETC16: (0xB2, (("cfg_reg", 16, 8), ("value", 0, 16))),
  # RMWCIBn read-modify-writes byte n of cfg_reg: new = (old & ~mask) | (data & mask)
  T.RMWCIB0: (0xB3, RMWCIB), T.RMWCIB1: (0xB4, RMWCIB), T.RMWCIB2: (0xB5, RMWCIB), T.RMWCIB3: (0xB6, RMWCIB),
  T.STREAMWRCFG: (0xB7, (("stream_sel", 21, 3), ("stream_reg", 11, 10), ("cfg_reg", 0, 11))),
  # cfg_reg = op(rotr(scratch, rotate) & mask, cfg_reg & ~mask), mask has mask_width+1 ones
  # op: 0 or, 1 and, 2 xor, 3 add, 4 or-not. mask_mode=1 disables the mask on the old value
  T.CFGSHIFTMASK: (0xB8, (("mask_mode", 23, 1), ("op", 20, 3), ("mask_width", 15, 5), ("rotate", 10, 5), ("scratch", 8, 2), ("cfg_reg", 0, 8))),
}

# instruction groups, for passes that care about a property rather than one op (like tinygrad's GroupOp)
class TensixGroup:
  # writes config state: the config dedup pass forgets what it knows about the target when it sees one it did not emit
  WritesCfg = {T.WRCFG, T.RMWCIB0, T.RMWCIB1, T.RMWCIB2, T.RMWCIB3, T.SETC16, T.CFGSHIFTMASK, T.STREAMWRCFG, T.SFPCONFIG}
  # read config, so a config write must STALLWAIT until earlier ones of these drain
  ReadsUnpackCfg = {T.UNPACR, T.UNPACR_NOP}
  ReadsPackCfg = {T.PACR, T.PACR_SETREG}
  Fpu = {T.MVMUL, T.ELWMUL, T.ELWADD, T.ELWSUB, T.DOTPV, T.GMPOOL, T.GAPOOL, T.MPOOL3S1, T.APOOL3S1, T.MPOOL3S2, T.APOOL3S2,
         T.CONV3S1, T.CONV3S2, T.MFCONV3S1}
  Move = {T.MOVD2A, T.MOVD2B, T.MOVA2D, T.MOVB2A, T.MOVB2D, T.MOVDBGA2D, T.MOVDBGB2D, T.ZEROACC, T.ZEROSRC}
  ReadsAluCfg = Fpu | Move
  Sfpu = {op for op in TensixOps if op.name.startswith("SFP")}
  # address counters: SET* are absolute (dedupable), INC*/ADDRCR* and every FPU/pack/unpack op advance them
  CounterSet = {T.SETRWC, T.SETIBRWC, T.SETADC, T.SETADCXY, T.SETADCZW, T.SETADCXX}
  CounterInc = {T.INCRWC, T.INCADCXY, T.INCADCZW, T.ADDRCRXY, T.ADDRCRZW}
  # ordering barriers: never reordered across, never deduped
  Semaphore = {T.SEMINIT, T.SEMPOST, T.SEMGET, T.SEMWAIT}
  Sync = Semaphore | {T.STALLWAIT, T.STREAMWAIT, T.ATGETM, T.ATRELM}
  # change the instruction stream itself
  Stream = {T.MOP, T.MOP_CFG, T.REPLAY}

# SFPU immediates that are signed 12-bit (two's complement accepted)
SIGNED_IMM = {T.SFPIADD, T.SFPSHFT, T.SFPSHFT2}

# RISC-V: name: (fixed bits, fields). A field split across the word (S/B/J immediates) has one entry per piece, the 4th
# number is which bit of the value the piece starts at. "imm" fields are signed.
RD, RS1, RS2 = ("rd", 7, 5), ("rs1", 15, 5), ("rs2", 20, 5)
IMM_I, IMM_S = (("imm", 20, 12),), (("imm", 7, 5), ("imm", 25, 7, 5))
IMM_B = (("imm", 8, 4, 1), ("imm", 25, 6, 5), ("imm", 7, 1, 11), ("imm", 31, 1, 12))
IMM_J = (("imm", 21, 10, 1), ("imm", 20, 1, 11), ("imm", 12, 8, 12), ("imm", 31, 1, 20))
def R(f7, f3): return (f7 << 25 | f3 << 12 | 0x33, (RD, RS1, RS2))
def I(f3, op=0x13): return (f3 << 12 | op, (RD, RS1, *IMM_I))
def SH(f3, f7=0): return (f7 << 25 | f3 << 12 | 0x13, (RD, RS1, ("shamt", 20, 5)))
def B(f3): return (f3 << 12 | 0x63, (RS1, RS2, *IMM_B))
def L(f3): return I(f3, 0x03)
def S(f3): return (f3 << 12 | 0x23, (RS1, RS2, *IMM_S))
def CSR(f3): return (f3 << 12 | 0x73, (RD, RS1, ("csr", 20, 12)))
def CSRI(f3): return (f3 << 12 | 0x73, (RD, ("uimm", 15, 5), ("csr", 20, 12)))

V = RV32Ops
RV32 = {
  V.LUI: (0x37, (RD, ("upper", 12, 20, 12))), V.AUIPC: (0x17, (RD, ("upper", 12, 20, 12))),  # upper: the value, low 12 bits 0
  V.JAL: (0x6F, (RD, *IMM_J)), V.JALR: I(0, 0x67),
  V.BEQ: B(0), V.BNE: B(1), V.BLT: B(4), V.BGE: B(5), V.BLTU: B(6), V.BGEU: B(7),
  V.LB: L(0), V.LH: L(1), V.LW: L(2), V.LBU: L(4), V.LHU: L(5), V.SB: S(0), V.SH: S(1), V.SW: S(2),
  V.ADDI: I(0), V.SLTI: I(2), V.SLTIU: I(3), V.XORI: I(4), V.ORI: I(6), V.ANDI: I(7),
  V.SLLI: SH(1), V.SRLI: SH(5), V.SRAI: SH(5, 0x20),
  V.ADD: R(0, 0), V.SUB: R(0x20, 0), V.SLL: R(0, 1), V.SLT: R(0, 2), V.SLTU: R(0, 3),
  V.XOR: R(0, 4), V.SRL: R(0, 5), V.SRA: R(0x20, 5), V.OR: R(0, 6), V.AND: R(0, 7),
  V.MUL: R(1, 0), V.MULH: R(1, 1), V.MULHSU: R(1, 2), V.MULHU: R(1, 3), V.DIV: R(1, 4), V.DIVU: R(1, 5), V.REM: R(1, 6), V.REMU: R(1, 7),
  V.SH1ADD: R(0x10, 2), V.SH2ADD: R(0x10, 4), V.SH3ADD: R(0x10, 6), V.MIN: R(0x05, 4),  # shNadd: rd = (rs1 << N) + rs2
  V.CSRRW: CSR(1), V.CSRRS: CSR(2), V.CSRRC: CSR(3), V.CSRRWI: CSRI(5), V.CSRRSI: CSRI(6), V.CSRRCI: CSRI(7),
  V.FENCE: (0x0FF00000 | 0x0F, ()),  # fence iorw, iorw
  V.ECALL: (0x00000073, ()), V.EBREAK: (0x00100073, ()),
}

class RV32Group:
  Branch = {V.BEQ, V.BNE, V.BLT, V.BGE, V.BLTU, V.BGEU}
  Jump = {V.JAL, V.JALR}
  Load = {V.LB, V.LH, V.LW, V.LBU, V.LHU}
  Store = {V.SB, V.SH, V.SW}

OPS = RV32 | {op: (opcode << 24, layout) for op, (opcode, layout) in TENSIX.items()}

def encode(op: TensixOps | RV32Ops, **fields) -> int:
  word, layout = OPS[op]
  for name, v in fields.items():
    pieces = [(lo, w, s[0] if s else 0) for n, lo, w, *s in layout if n == name]
    assert pieces, f"{op.name} has no field {name}, fields are {[f[0] for f in layout]}"
    covered = sum(((1 << w) - 1) << s for _, w, s in pieces)
    bits = covered.bit_length()
    if name == "imm" and isinstance(op, RV32Ops): ok = v & covered == v or v - (v & covered) == -(1 << bits) and v >> (bits - 1) == -1
    elif name == "imm" and op in SIGNED_IMM: ok = -(1 << (bits - 1)) <= v <= covered
    else: ok = 0 <= v <= covered and v & covered == v
    assert ok, f"{op.name}.{name}={v} does not fit"
    for lo, w, s in pieces: word |= (v >> s & (1 << w) - 1) << lo
  return word

def ttinsn(word): return (word << 2 | word >> 30) & 0xFFFFFFFF  # Tensix word placed inline in RISC-V code (.ttinsn)
