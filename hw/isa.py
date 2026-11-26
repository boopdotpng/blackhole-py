from enum import Enum, IntEnum, IntFlag
from functools import partial
from typing import Any, dataclass_transform

# descriptions of every instruction and field are in docs/index.html

# ---- DSL: one Inst subclass per encoding, fields declared as `name: type = bits[hi:lo]` ----

class BitField:
  enum: type[Enum] | None = None
  def __init__(self, hi:int, lo:int): self.hi, self.lo, self.mask = hi, lo, (1 << (hi - lo + 1)) - 1
  def __set_name__(self, owner, name:str): self.name = name
  def encode(self, v:int) -> int:
    if not 0 <= v <= self.mask: raise ValueError(f"{self.name}={v} does not fit {self.hi - self.lo + 1} bits")
    return v << self.lo
  def decode(self, w:int) -> int: return w >> self.lo & self.mask
  def __get__(self, obj, objtype=None):
    if obj is None: return self
    v = self.decode(int(obj))
    try: return self.enum(v) if self.enum is not None else v
    except ValueError: return v

class Imm(BitField):
  # an immediate scattered over (hi, lo, first imm bit) pieces of the word; signed unless it may also be unsigned
  def __init__(self, nbits:int, *pieces:tuple[int, int, int], align:int=1, unsigned:bool=False):
    self.nbits, self.pieces, self.align, self.unsigned = nbits, pieces, align, unsigned
  def encode(self, v:int) -> int:
    if v % self.align or not -(1 << (self.nbits - 1)) <= v < 1 << (self.nbits - (0 if self.unsigned else 1)):
      raise ValueError(f"{self.name}={v} does not fit {'' if self.unsigned else 'signed '}{self.nbits} bits")
    return sum((v >> at & ((1 << (hi - lo + 1)) - 1)) << lo for hi, lo, at in self.pieces)
  def decode(self, w:int) -> int:
    v = sum((w >> lo & ((1 << (hi - lo + 1)) - 1)) << at for hi, lo, at in self.pieces)
    return v if self.unsigned or not v >> (self.nbits - 1) else v - (1 << self.nbits)

def scatter(nbits:int, *pieces:tuple[int, int, int], align:int=1, unsigned:bool=False) -> Any: return Imm(nbits, *pieces, align=align, unsigned=unsigned)

class _Bits:
  def __getitem__(self, k:slice | int) -> Any: return BitField(k.start, k.stop) if isinstance(k, slice) else BitField(k, k)
bits = _Bits()

@dataclass_transform()
class Inst(int):
  _fields: tuple[BitField, ...] = ()
  def __init_subclass__(cls):
    own = [f for f in cls.__dict__.values() if isinstance(f, BitField)]
    for f in own:
      t = cls.__annotations__.get(f.name)
      f.enum = next((a for a in getattr(t, "__args__", (t,)) if isinstance(a, type) and issubclass(a, Enum)), None)
    cls._fields = cls._fields + tuple(own)
  def __new__(cls, *args, **kwargs):
    names = [f.name for f in cls._fields]
    if len(args) > len(names): raise TypeError(f"{cls.__name__} takes at most {len(names)} fields")
    vals = dict(zip(names, args))
    for k, v in kwargs.items():
      if k not in names or k in vals: raise TypeError(f"{cls.__name__}: unexpected or repeated field {k!r}")
      vals[k] = v
    return super().__new__(cls, sum(f.encode(int(vals.get(f.name, 0))) for f in cls._fields))
  def replace(self, **kwargs): return type(self)(**{f.name: getattr(self, f.name) for f in self._fields} | kwargs)
  def fields(self) -> dict[str, Any]: return {f.name: getattr(self, f.name) for f in self._fields}
  def __repr__(self):
    hidden = _HIDDEN.get(type(self), ())
    args = ", ".join(f"{k}={v.name if isinstance(v, Enum) and v.name else v}" for k, v in self.fields().items() if v and k not in hidden)
    return f"{self.name}({args})"
  @property
  def name(self) -> str: return type(self).__name__

# ---- RISC-V: RV32IM ----

class RV(Inst):
  @property
  def name(self) -> str:
    return next(n for n, f in RV32.items() if f.func is type(self) and all(getattr(self, k) == v for k, v in f.keywords.items()))

class R(RV):
  rd: int = bits[11:7]; rs1: int = bits[19:15]; rs2: int = bits[24:20]
  opcode: int = bits[6:0]; funct3: int = bits[14:12]; funct7: int = bits[31:25]
class I(RV):
  rd: int = bits[11:7]; rs1: int = bits[19:15]; imm: int = scatter(12, (31, 20, 0))
  opcode: int = bits[6:0]; funct3: int = bits[14:12]
class Shift(RV):
  rd: int = bits[11:7]; rs1: int = bits[19:15]; shamt: int = bits[24:20]
  opcode: int = bits[6:0]; funct3: int = bits[14:12]; funct7: int = bits[31:25]
class S(RV):
  rs1: int = bits[19:15]; rs2: int = bits[24:20]; imm: int = scatter(12, (31, 25, 5), (11, 7, 0))
  opcode: int = bits[6:0]; funct3: int = bits[14:12]
class B(RV):
  rs1: int = bits[19:15]; rs2: int = bits[24:20]; imm: int = scatter(13, (31, 31, 12), (30, 25, 5), (11, 8, 1), (7, 7, 11), align=2)
  opcode: int = bits[6:0]; funct3: int = bits[14:12]
class U(RV):
  rd: int = bits[11:7]; imm: int = scatter(20, (31, 12, 0), unsigned=True)
  opcode: int = bits[6:0]
class J(RV):
  rd: int = bits[11:7]; imm: int = scatter(21, (31, 31, 20), (30, 21, 1), (20, 20, 11), (19, 12, 12), align=2)
  opcode: int = bits[6:0]

lui, auipc = partial(U, opcode=0x37), partial(U, opcode=0x17)
jal, jalr = partial(J, opcode=0x6F), partial(I, opcode=0x67, funct3=0)
beq, bne = partial(B, opcode=0x63, funct3=0), partial(B, opcode=0x63, funct3=1)
blt, bge = partial(B, opcode=0x63, funct3=4), partial(B, opcode=0x63, funct3=5)
bltu, bgeu = partial(B, opcode=0x63, funct3=6), partial(B, opcode=0x63, funct3=7)
lb, lh, lw = partial(I, opcode=0x03, funct3=0), partial(I, opcode=0x03, funct3=1), partial(I, opcode=0x03, funct3=2)
lbu, lhu = partial(I, opcode=0x03, funct3=4), partial(I, opcode=0x03, funct3=5)
sb, sh, sw = partial(S, opcode=0x23, funct3=0), partial(S, opcode=0x23, funct3=1), partial(S, opcode=0x23, funct3=2)
addi, slti, sltiu = partial(I, opcode=0x13, funct3=0), partial(I, opcode=0x13, funct3=2), partial(I, opcode=0x13, funct3=3)
xori, ori, andi = partial(I, opcode=0x13, funct3=4), partial(I, opcode=0x13, funct3=6), partial(I, opcode=0x13, funct3=7)
slli, srli = partial(Shift, opcode=0x13, funct3=1, funct7=0), partial(Shift, opcode=0x13, funct3=5, funct7=0)
srai = partial(Shift, opcode=0x13, funct3=5, funct7=0x20)
add, sub = partial(R, opcode=0x33, funct3=0, funct7=0), partial(R, opcode=0x33, funct3=0, funct7=0x20)
sll, slt = partial(R, opcode=0x33, funct3=1, funct7=0), partial(R, opcode=0x33, funct3=2, funct7=0)
sltu, xor = partial(R, opcode=0x33, funct3=3, funct7=0), partial(R, opcode=0x33, funct3=4, funct7=0)
srl, sra = partial(R, opcode=0x33, funct3=5, funct7=0), partial(R, opcode=0x33, funct3=5, funct7=0x20)
or_, and_ = partial(R, opcode=0x33, funct3=6, funct7=0), partial(R, opcode=0x33, funct3=7, funct7=0)
mul, mulh = partial(R, opcode=0x33, funct3=0, funct7=1), partial(R, opcode=0x33, funct3=1, funct7=1)
mulhsu, mulhu = partial(R, opcode=0x33, funct3=2, funct7=1), partial(R, opcode=0x33, funct3=3, funct7=1)
div, divu = partial(R, opcode=0x33, funct3=4, funct7=1), partial(R, opcode=0x33, funct3=5, funct7=1)
rem, remu = partial(R, opcode=0x33, funct3=6, funct7=1), partial(R, opcode=0x33, funct3=7, funct7=1)
fence = partial(I, opcode=0x0F, funct3=0, imm=0xFF)  # imm = pred << 4 | succ, default iorw,iorw

RV32 = {n.rstrip("_"): f for n, f in dict(globals()).items() if isinstance(f, partial) and isinstance(f.func, type) and issubclass(f.func, RV)}

# ---- Tensix: field values ----

class Stall(IntFlag):
  TDMA, SYNC, PACK, UNPACK, XMOV, THCON, MATH, CFG, SFPU = (1 << x for x in range(9))
  THREAD = 0x1FF

class Wait(IntFlag):
  THCON, UNPACK0, UNPACK1, PACK0, MATH, SRCA_CLR, SRCB_CLR, SRCA_VLD, SRCB_VLD, XMOV, TRISC_CFG, SFPU, CFGEXU = (1 << x for x in range(13))

class SemWait(IntEnum): STALL_ON_ZERO, STALL_ON_MAX = 1, 2

class Adc(IntFlag): UNPACK0, UNPACK1, PACK = 1, 2, 4

class LReg(IntEnum):
  L0, L1, L2, L3, L4, L5, L6, L7 = range(8)
  CONST_0_8373, ZERO, ONE = 8, 9, 10
  NEG_ONE, CONFIG0, CONFIG1, CONFIG2 = 11, 12, 13, 14
  LANE_X2, LOAD_MACRO = 15, 16

class SfpuFormat(IntEnum):
  SRCB = DEFAULT = 0
  FP16, BF16, FP32, INT32 = range(1, 5)
  INT8, UINT16, HI16, INT16, LO16 = range(5, 10)
  INT32_ALL, ZERO = 10, 11
  LO16_ONLY, HI16_ONLY = 14, 15

class LoadImm(IntEnum): FLOATB, FLOATA, USHORT, SHORT, UPPER, LOWER = 0, 1, 2, 4, 8, 10

class Broadcast(IntEnum): NONE, COLUMN, ROW, SCALAR = range(4)

class TensixOp(IntEnum):
  MOP, NOP, MOP_CFG, REPLAY, MOVD2A, MOVD2B, MOVB2A, ZEROACC, ZEROSRC, MOVA2D, MOVB2D = 1, 2, 3, 4, 8, 0xA, 0xB, 0x10, 0x11, 0x12, 0x13
  TRNSPSRCB, MVMUL, ELWMUL, ELWADD, ELWSUB, GMPOOL, GAPOOL, CLEARDVALID, SETRWC, INCRWC = 0x16, 0x26, 0x27, 0x28, 0x30, 0x33, 0x34, 0x36, 0x37, 0x38
  XMOV, PACR, UNPACR, UNPACR_NOP, SETDMAREG, LOADIND, SETADC, SETADCXY, INCADCXY = 0x40, 0x41, 0x42, 0x43, 0x45, 0x49, 0x50, 0x51, 0x52
  ADDRCRXY, SETADCZW, INCADCZW, ADDRCRZW, ADDDMAREG, SUBDMAREG, MULDMAREG, SHIFTDMAREG = 0x53, 0x54, 0x55, 0x56, 0x58, 0x59, 0x5A, 0x5C
  SETADCXX, STOREIND, STOREREG, LOADREG = 0x5E, 0x66, 0x67, 0x68
  SFPLOAD, SFPLOADI, SFPSTORE, SFPLUT, SFPMULI, SFPADDI, SFPDIVP2, SFPEXEXP, SFPEXMAN = 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78
  SFPIADD, SFPSHFT, SFPSETCC, SFPMOV, SFPABS, SFPAND, SFPOR, SFPNOT, SFPLZ = 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F, 0x80, 0x81
  SFPSETEXP, SFPSETMAN, SFPMAD, SFPADD, SFPMUL, SFPPUSHC, SFPPOPC, SFPSETSGN = 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89
  SFPENCC, SFPCOMPC, SFPTRANSP, SFPXOR, SFP_STOCH_RND, SFPNOP, SFPCAST, SFPCONFIG = 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F, 0x90, 0x91
  SFPSWAP, SFPLOADMACRO, SFPSHFT2, SFPLUTFP32, SFPLE, SFPGT, SFPMUL24, SFPARECIP = 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99
  STALLWAIT, SEMINIT, SEMPOST, SEMGET, SEMWAIT, WRCFG, RDCFG, SETC16 = 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xB0, 0xB1, 0xB2
  RMWCIB0, RMWCIB1, RMWCIB2, RMWCIB3, CFGSHIFTMASK = 0xB3, 0xB4, 0xB5, 0xB6, 0xB8

# ---- Tensix: encodings (one class per field layout; words are unrotated, see inline()) ----

class Tensix(Inst):
  op: TensixOp = bits[31:24]
  @property
  def name(self) -> str: return self.op.name if isinstance(self.op, TensixOp) else f"op{self.op:#x}"

class NoArgs(Tensix): pass
# control
class Mop(Tensix): template: int = bits[23:23]; loop_count: int = bits[22:16]; mask_lo: int = bits[15:0]
class MopCfg(Tensix): mask_hi: int = bits[23:0]
class Replay(Tensix): start: int = bits[23:14]; length: int = bits[13:4]; execute: int = bits[3:1]; record: int = bits[0:0]
class StallWait(Tensix): stall: Stall | int = bits[23:15]; wait: Wait | int = bits[14:0]
class SemInit(Tensix): max: int = bits[23:20]; init: int = bits[19:16]; sems: int = bits[15:2]
class SemOp(Tensix): sems: int = bits[23:2]
class SemWaitInst(Tensix): stall: Stall | int = bits[23:15]; sems: int = bits[14:2]; cond: SemWait | int = bits[1:0]
# configuration
class SetC16(Tensix): word: int = bits[23:16]; value: int = bits[15:0]
class RmwCib(Tensix): mask: int = bits[23:16]; data: int = bits[15:8]; word: int = bits[7:0]
class WrCfg(Tensix): gpr: int = bits[23:16]; wide: int = bits[15:15]; word: int = bits[14:0]
class RdCfg(Tensix): gpr: int = bits[23:16]; word: int = bits[15:0]
class CfgShiftMask(Tensix):
  keep_old: int = bits[23:23]; operation: int = bits[22:20]; mask_width: int = bits[19:15]; rotate: int = bits[14:10]
  scratch: int = bits[9:8]; word: int = bits[7:0]
# scalar unit (the thread's 64 Tensix GPRs)
class SetDmaReg(Tensix): imm: int = bits[23:8]; signals_mode: int = bits[7:7]; half_reg: int = bits[6:0]
class DmaRegOp(Tensix): b_is_imm: int = bits[23:23]; dest: int = bits[22:12]; b: int = bits[11:6]; a: int = bits[5:0]
class ShiftDmaReg(Tensix):
  b_is_imm: int = bits[23:23]; right: int = bits[22:18]; dest: int = bits[17:12]; b: int = bits[11:6]; a: int = bits[5:0]
class LoadInd(Tensix):
  size: int = bits[23:22]; offset_reg: int = bits[21:14]; inc: int = bits[13:12]; data_reg: int = bits[11:6]; addr_reg: int = bits[5:0]
class StoreInd(Tensix):
  mmio: int = bits[23:23]; size: int = bits[22:22]; reg_size: int = bits[21:21]; offset_reg: int = bits[20:14]; inc: int = bits[13:12]
  data_reg: int = bits[11:6]; addr_reg: int = bits[5:0]
class RegMem(Tensix): reg: int = bits[23:18]; addr: int = bits[17:0]
# address counters (ADCs) of unpacker 0, unpacker 1 and the packer
class SetAdc(Tensix): counters: Adc | int = bits[23:21]; channel: int = bits[20:20]; dim: int = bits[19:18]; value: int = bits[17:0]
class SetAdcXX(Tensix): counters: Adc | int = bits[23:21]; x_end: int = bits[20:10]; x_start: int = bits[9:0]
class AdcXY(Tensix):
  counters: Adc | int = bits[23:21]; ch1_y: int = bits[20:15]; ch1_x: int = bits[14:12]; ch0_y: int = bits[11:9]; ch0_x: int = bits[8:6]
  mask: int = bits[5:0]
class AdcZW(Tensix):
  counters: Adc | int = bits[23:21]; ch1_w: int = bits[20:15]; ch1_z: int = bits[14:12]; ch0_w: int = bits[11:9]; ch0_z: int = bits[8:6]
  mask: int = bits[5:0]
class IncAdcXY(Tensix):
  counters: Adc | int = bits[23:21]; ch1_y: int = bits[20:15]; ch1_x: int = bits[14:12]; ch0_y: int = bits[11:9]; ch0_x: int = bits[8:6]
class IncAdcZW(Tensix):
  counters: Adc | int = bits[23:21]; ch1_w: int = bits[20:15]; ch1_z: int = bits[14:12]; ch0_w: int = bits[11:9]; ch0_z: int = bits[8:6]
# unpack, pack, mover
class Unpacr(Tensix):
  unpacker: int = bits[23:23]; steps: int = bits[22:15]; ctx_inc: int = bits[14:13]; ctx: int = bits[12:10]; adc_ctx: int = bits[9:8]
  per_ctx: int = bits[7:7]; set_dvalid: int = bits[6:6]; srcb_bcast: int = bits[5:5]; zero: int = bits[4:4]; auto_ctx: int = bits[3:3]
  row_search: int = bits[2:2]; cache_flush: int = bits[1:1]; last: int = bits[0:0]
class UnpacrNop(Tensix):
  unpacker: int = bits[23:23]; stream: int = bits[22:16]; msg_clear: int = bits[15:12]; set_dvalid: int = bits[11:8]
  clear_fmt: int = bits[7:6]; stall_own_bank: int = bits[5:5]; bank_clear: int = bits[4:4]; fill_neg_inf: int = bits[3:2]
  mode: int = bits[1:0]
class Pacr(Tensix):
  ctx: int = bits[23:21]; row_pad: int = bits[20:18]; strided: int = bits[17:17]; addr_mod: int = bits[16:15]; adc_ctx: int = bits[14:13]
  zero: int = bits[12:12]; rows: int = bits[11:8]; override_thread: int = bits[7:7]; concat: int = bits[6:4]; ctx_ctrl: int = bits[3:2]
  flush: int = bits[1:1]; last: int = bits[0:0]
class Xmov(Tensix): block: int = bits[23:23]; last: int = bits[22:0]
# FPU (matrix unit)
class MvMul(Tensix): release: int = bits[23:22]; single_row: int = bits[21:19]; addr_mod: int = bits[18:14]; dst: int = bits[13:0]
class Elw(Tensix):
  release: int = bits[23:22]; accumulate: int = bits[21:21]; broadcast: Broadcast | int = bits[20:19]; addr_mod: int = bits[18:14]
  dst: int = bits[13:0]
class Pool(Tensix):
  release: int = bits[23:22]; mode: int = bits[21:19]; addr_mod: int = bits[18:15]; index: int = bits[14:14]; dst: int = bits[13:0]
class MovSrcDst(Tensix):
  lo16: int = bits[23:23]; src: int = bits[22:17]; addr_mod: int = bits[16:14]; rows: int = bits[13:12]; dst: int = bits[11:0]
class MovB2D(Tensix):
  lo16: int = bits[23:23]; src: int = bits[22:17]; addr_mod: int = bits[16:14]; mode: int = bits[13:11]; dst: int = bits[10:0]
class MovB2A(Tensix): srca: int = bits[23:17]; addr_mod: int = bits[16:14]; rows: int = bits[13:12]; srcb: int = bits[11:0]
class ZeroAcc(Tensix):
  mode: int = bits[23:19]; fp32: int = bits[18:18]; set_defined: int = bits[17:17]; addr_mod: int = bits[16:14]; where: int = bits[13:0]
class ZeroSrc(Tensix): neg_inf: int = bits[23:4]; math_bank: int = bits[3:3]; both_banks: int = bits[2:2]; srcs: int = bits[1:0]
class ClearDvalid(Tensix): release: int = bits[23:22]; reset: int = bits[21:0]
class SetRwc(Tensix):
  release: int = bits[23:22]; cr: int = bits[21:18]; dst: int = bits[17:14]; srcb: int = bits[13:10]; srca: int = bits[9:6]; mask: int = bits[5:0]
class IncRwc(Tensix): cr: int = bits[23:18]; dst: int = bits[17:14]; srcb: int = bits[13:10]; srca: int = bits[9:6]
# SFPU (vector unit); register operands are LReg numbers
class SfpuMem(Tensix): lreg: LReg | int = bits[23:20]; format: SfpuFormat | int = bits[19:16]; addr_mod: int = bits[15:13]; addr: int = bits[12:0]
class SfpuLoadImm(Tensix): lreg: LReg | int = bits[23:20]; mode: LoadImm | int = bits[19:16]; imm: int = bits[15:0]
class SfpuConfig(Tensix): imm: int = bits[23:8]; target: int = bits[7:4]; mode: int = bits[3:0]
class SfpuMad(Tensix): a: LReg | int = bits[23:16]; b: LReg | int = bits[15:12]; c: LReg | int = bits[11:8]; dest: LReg | int = bits[7:4]; mode: int = bits[3:0]
class SfpuImm16(Tensix): imm: int = bits[23:8]; dest: LReg | int = bits[7:4]; mode: int = bits[3:0]
class SfpuLut(Tensix): lreg: LReg | int = bits[23:20]; mode: int = bits[19:16]; addr: int = bits[15:0]
class SfpuLutFp32(Tensix): dest: int = bits[23:4]; mode: int = bits[3:0]
class SfpuAlu(Tensix): imm: int = bits[23:12]; src: LReg | int = bits[11:8]; dest: LReg | int = bits[7:4]; mode: int = bits[3:0]
class SfpuCast(Tensix): src: LReg | int = bits[23:8]; dest: LReg | int = bits[7:4]; mode: int = bits[3:0]
class SfpuStochRnd(Tensix):
  rounding: int = bits[23:21]; imm: int = bits[20:16]; b: LReg | int = bits[15:12]; src: LReg | int = bits[11:8]; dest: LReg | int = bits[7:4]
  mode: int = bits[3:0]

O = TensixOp
NOP, TRNSPSRCB, SFPNOP = partial(NoArgs, O.NOP), partial(NoArgs, O.TRNSPSRCB), partial(NoArgs, O.SFPNOP)
MOP, MOP_CFG, REPLAY = partial(Mop, O.MOP), partial(MopCfg, O.MOP_CFG), partial(Replay, O.REPLAY)
STALLWAIT, SEMINIT, SEMWAIT = partial(StallWait, O.STALLWAIT), partial(SemInit, O.SEMINIT), partial(SemWaitInst, O.SEMWAIT)
SEMPOST, SEMGET = partial(SemOp, O.SEMPOST), partial(SemOp, O.SEMGET)
SETC16, WRCFG, RDCFG, CFGSHIFTMASK = partial(SetC16, O.SETC16), partial(WrCfg, O.WRCFG), partial(RdCfg, O.RDCFG), partial(CfgShiftMask, O.CFGSHIFTMASK)
RMWCIB0, RMWCIB1, RMWCIB2, RMWCIB3 = partial(RmwCib, O.RMWCIB0), partial(RmwCib, O.RMWCIB1), partial(RmwCib, O.RMWCIB2), partial(RmwCib, O.RMWCIB3)
SETDMAREG, SHIFTDMAREG = partial(SetDmaReg, O.SETDMAREG), partial(ShiftDmaReg, O.SHIFTDMAREG)
ADDDMAREG, SUBDMAREG, MULDMAREG = partial(DmaRegOp, O.ADDDMAREG), partial(DmaRegOp, O.SUBDMAREG), partial(DmaRegOp, O.MULDMAREG)
LOADIND, STOREIND = partial(LoadInd, O.LOADIND), partial(StoreInd, O.STOREIND)
LOADREG, STOREREG = partial(RegMem, O.LOADREG), partial(RegMem, O.STOREREG)
SETADC, SETADCXX, INCADCXY, INCADCZW = partial(SetAdc, O.SETADC), partial(SetAdcXX, O.SETADCXX), partial(IncAdcXY, O.INCADCXY), partial(IncAdcZW, O.INCADCZW)
SETADCXY, ADDRCRXY = partial(AdcXY, O.SETADCXY), partial(AdcXY, O.ADDRCRXY)
SETADCZW, ADDRCRZW = partial(AdcZW, O.SETADCZW), partial(AdcZW, O.ADDRCRZW)
UNPACR, UNPACR_NOP, PACR, XMOV = partial(Unpacr, O.UNPACR), partial(UnpacrNop, O.UNPACR_NOP), partial(Pacr, O.PACR), partial(Xmov, O.XMOV)
MVMUL, GAPOOL, GMPOOL = partial(MvMul, O.MVMUL), partial(Pool, O.GAPOOL), partial(Pool, O.GMPOOL)
ELWADD, ELWSUB, ELWMUL = partial(Elw, O.ELWADD), partial(Elw, O.ELWSUB), partial(Elw, O.ELWMUL)
MOVA2D, MOVD2A, MOVD2B = partial(MovSrcDst, O.MOVA2D), partial(MovSrcDst, O.MOVD2A), partial(MovSrcDst, O.MOVD2B)
MOVB2D, MOVB2A = partial(MovB2D, O.MOVB2D), partial(MovB2A, O.MOVB2A)
ZEROACC, ZEROSRC, CLEARDVALID = partial(ZeroAcc, O.ZEROACC), partial(ZeroSrc, O.ZEROSRC), partial(ClearDvalid, O.CLEARDVALID)
SETRWC, INCRWC = partial(SetRwc, O.SETRWC), partial(IncRwc, O.INCRWC)
SFPLOAD, SFPSTORE, SFPLOADMACRO = partial(SfpuMem, O.SFPLOAD), partial(SfpuMem, O.SFPSTORE), partial(SfpuMem, O.SFPLOADMACRO)
SFPLOADI, SFPCONFIG = partial(SfpuLoadImm, O.SFPLOADI), partial(SfpuConfig, O.SFPCONFIG)
SFPMAD, SFPADD, SFPMUL, SFPMUL24 = partial(SfpuMad, O.SFPMAD), partial(SfpuMad, O.SFPADD), partial(SfpuMad, O.SFPMUL), partial(SfpuMad, O.SFPMUL24)
SFPADDI, SFPMULI = partial(SfpuImm16, O.SFPADDI), partial(SfpuImm16, O.SFPMULI)
SFPLUT, SFPLUTFP32 = partial(SfpuLut, O.SFPLUT), partial(SfpuLutFp32, O.SFPLUTFP32)
SFPCAST, SFP_STOCH_RND = partial(SfpuCast, O.SFPCAST), partial(SfpuStochRnd, O.SFP_STOCH_RND)
SFPARECIP, SFPMOV, SFPABS, SFPAND = partial(SfpuAlu, O.SFPARECIP), partial(SfpuAlu, O.SFPMOV), partial(SfpuAlu, O.SFPABS), partial(SfpuAlu, O.SFPAND)
SFPOR, SFPXOR, SFPNOT, SFPLZ = partial(SfpuAlu, O.SFPOR), partial(SfpuAlu, O.SFPXOR), partial(SfpuAlu, O.SFPNOT), partial(SfpuAlu, O.SFPLZ)
SFPSHFT, SFPSHFT2, SFPIADD = partial(SfpuAlu, O.SFPSHFT), partial(SfpuAlu, O.SFPSHFT2), partial(SfpuAlu, O.SFPIADD)
SFPEXEXP, SFPEXMAN, SFPDIVP2 = partial(SfpuAlu, O.SFPEXEXP), partial(SfpuAlu, O.SFPEXMAN), partial(SfpuAlu, O.SFPDIVP2)
SFPSETEXP, SFPSETMAN, SFPSETSGN = partial(SfpuAlu, O.SFPSETEXP), partial(SfpuAlu, O.SFPSETMAN), partial(SfpuAlu, O.SFPSETSGN)
SFPSWAP, SFPTRANSP, SFPENCC, SFPSETCC = partial(SfpuAlu, O.SFPSWAP), partial(SfpuAlu, O.SFPTRANSP), partial(SfpuAlu, O.SFPENCC), partial(SfpuAlu, O.SFPSETCC)
SFPGT, SFPLE = partial(SfpuAlu, O.SFPGT), partial(SfpuAlu, O.SFPLE)
SFPPUSHC, SFPPOPC, SFPCOMPC = partial(SfpuAlu, O.SFPPUSHC), partial(SfpuAlu, O.SFPPOPC), partial(SfpuAlu, O.SFPCOMPC)

TENSIX: dict[int, type[Tensix]] = {f.args[0]: f.func for f in dict(globals()).values() if isinstance(f, partial) and isinstance(f.func, type) and issubclass(f.func, Tensix)}
_HIDDEN: dict[type, tuple[str, ...]] = {c: ("op",) for c in set(TENSIX.values())} | {c: ("opcode", "funct3", "funct7") for c in (R, I, Shift, S, B, U, J)}

def decode(w:int) -> Tensix | None:
  # an unrotated Tensix word, or None if it isn't one we encode (unknown opcode or stray bits)
  if (cls := TENSIX.get(w >> 24)) is None or w & ~sum(f.mask << f.lo for f in cls._fields) & 0xFFFFFFFF: return None
  return int.__new__(cls, w)

def inline(w:int) -> int: return (w << 2 | w >> 30) & 0xFFFFFFFF  # as stored in a TRISC instruction stream
def outline(w:int) -> int: return (w >> 2 | w << 30) & 0xFFFFFFFF

MOP_CFG_WORDS = 9
