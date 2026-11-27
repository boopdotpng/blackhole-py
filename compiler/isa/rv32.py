import struct
from enum import Enum, auto
from hw import isa as hw_isa
from ..dtype import DType, dtypes
from ..uop import Ops, PatternMatcher, UOp, UPat
from . import ISARenderer, IselContext, LinearContext, rdef, regs, vdef, vreg

# ---- RV32IM Opcodes & Groups ----

class RVOps(Enum):
  # structural / pseudo
  LABEL = auto()
  LI = auto()
  RET = auto()
  # R-type ALU + M extension
  ADD = auto(); SUB = auto(); SLL = auto(); SLT = auto(); SLTU = auto()
  XOR = auto(); SRL = auto(); SRA = auto(); OR = auto(); AND = auto()
  MUL = auto(); MULH = auto(); MULHSU = auto(); MULHU = auto()
  DIV = auto(); DIVU = auto(); REM = auto(); REMU = auto()
  # I-type ALU + shifts
  ADDI = auto(); SLTI = auto(); SLTIU = auto()
  XORI = auto(); ORI = auto(); ANDI = auto()
  SLLI = auto(); SRLI = auto(); SRAI = auto()
  # U-type
  LUI = auto(); AUIPC = auto()
  # Memory & ordering
  LB = auto(); LH = auto(); LW = auto(); LBU = auto(); LHU = auto()
  SB = auto(); SH = auto(); SW = auto()
  FENCE = auto()
  # Branches & jumps
  BEQ = auto(); BNE = auto(); BLT = auto(); BGE = auto(); BLTU = auto(); BGEU = auto()
  JAL = auto(); JALR = auto()

class RVGroupOp:
  RType = frozenset({
    RVOps.ADD, RVOps.SUB, RVOps.SLL, RVOps.SLT, RVOps.SLTU,
    RVOps.XOR, RVOps.SRL, RVOps.SRA, RVOps.OR, RVOps.AND,
    RVOps.MUL, RVOps.MULH, RVOps.MULHSU, RVOps.MULHU,
    RVOps.DIV, RVOps.DIVU, RVOps.REM, RVOps.REMU,
  })
  IType = frozenset({RVOps.ADDI, RVOps.SLTI, RVOps.SLTIU, RVOps.XORI, RVOps.ORI, RVOps.ANDI})
  ShiftImm = frozenset({RVOps.SLLI, RVOps.SRLI, RVOps.SRAI})
  Load = frozenset({RVOps.LB, RVOps.LH, RVOps.LW, RVOps.LBU, RVOps.LHU})
  Store = frozenset({RVOps.SB, RVOps.SH, RVOps.SW})
  Branch = frozenset({RVOps.BEQ, RVOps.BNE, RVOps.BLT, RVOps.BGE, RVOps.BLTU, RVOps.BGEU})
  Jump = frozenset({RVOps.JAL, RVOps.JALR, RVOps.RET})
  Control = Branch | Jump
  Immediate = IType | ShiftImm | Load | Store | frozenset({RVOps.LUI, RVOps.AUIPC, RVOps.LI, RVOps.JALR, RVOps.FENCE})
  All = frozenset(RVOps)

# ---- RV32 physical registers ----

X = tuple(UOp.param(i, dtypes.u32, name=f"x{i}", file="gpr") for i in range(32))
X0, RA, SP = X[0], X[1], X[2]
# Blackhole firmware ABI base registers (local mem, NoC/cfg, PC_BUF)
LOCAL_BASE, NOC_BASE, PCBUF_BASE = X[3], X[4], X[5]
RV_PHYSICAL_REGS = frozenset(X)
# Default allocatable pool (keeps x0, x1/ra, x2/sp, x3..x5 base regs intact; x30..x31 used as spill scratch)
DEFAULT_WGPR = X[6:30]
DEFAULT_SCRATCH = (X[30], X[31])

def fits_simm12(v: int) -> bool: return -2048 <= v < 2048
def fits_shamt(v: int) -> bool: return 0 <= v < 32
def is_int_const(u: UOp) -> bool: return u.op is Ops.CONST and (u.dtype.is_int or u.dtype is dtypes.bool)
def const_int(u: UOp) -> int: return int(u.arg)

def rv_label(key: UOp, role: str = "") -> UOp:
  return UOp.ins(RVOps.LABEL, (key,), dtypes.void, role=role)

def rv_li(val: int, dtype: DType = dtypes.i32, *dst: UOp, role: str = "") -> UOp:
  if val == 0 and not dst: return X0.cast(dtype) if dtype != dtypes.u32 else X0
  return UOp.ins(RVOps.LI, (UOp.const(val & 0xFFFFFFFF if val >= (1 << 31) else val),), dtype, *dst, role=role)

def rv_arg(slot: int, *, high: bool = False, dtype: DType = dtypes.u32) -> UOp:
  """Load one word of a firmware argument; DRAM pointers use low/high loads."""
  if not 0 <= slot < 16: raise ValueError(f"argument slot {slot} is outside the 16-slot firmware ABI")
  if dtype.bits > 32 or dtype.is_float: raise ValueError("RV32 argument words must be integers of at most 32 bits")
  return UOp.ins(RVOps.LW, (X0, UOp.const(0x80 + 8 * slot + 4 * high)), dtype)

def expand_li(u: UOp) -> list[UOp]:
  """Expand pseudo LI into ADDI or LUI + ADDI once its destination physical register is known."""
  n = const_int(u.src_without_body[0]) & 0xFFFFFFFF
  rd = regs(u)[0]
  role = u.arg.role if hasattr(u.arg, "role") else ""
  lo = (n + 2048) % 4096 - 2048
  hi = ((n - lo) >> 12) & 0xFFFFF
  if hi == 0:
    return [UOp.ins(RVOps.ADDI, (X0, UOp.const(lo)), u.dtype, rd, role=role)]
  out = [UOp.ins(RVOps.LUI, (UOp.const(hi),), u.dtype, rd, role=role)]
  if lo != 0:
    out.append(UOp.ins(RVOps.ADDI, (out[0], UOp.const(lo)), u.dtype, rd, role=role))
  return out

# ---- RV32 instruction selection (graph_rewrite) ----

def _bin_imm_or_reg(u: UOp, r_op: RVOps, i_op: RVOps | None, *, shift: bool = False) -> UOp:
  a, b = u.src
  if i_op is not None and is_int_const(b):
    v = const_int(b)
    if (fits_shamt(v) if shift else fits_simm12(v)):
      return UOp.ins(i_op, (a, UOp.const(v)), u.dtype)
  return UOp.ins(r_op, (a, b), u.dtype)

def _fold_mem_addr(addr: UOp) -> tuple[UOp, UOp]:
  """Return (base_reg_uop, simm12_byte_offset_const) for LOAD/STORE addressing."""
  if addr.op is Ops.INDEX:
    base, idx = addr.src
    elem_sz = max(1, addr.dtype.itemsize)
    if is_int_const(idx) and fits_simm12(off := const_int(idx) * elem_sz):
      return base, UOp.const(off)
    if idx.op is Ops.ADD and is_int_const(idx.src[1]) and fits_simm12(off := const_int(idx.src[1]) * elem_sz):
      scaled = idx.src[0] if elem_sz == 1 else UOp.ins(RVOps.SLLI, (idx.src[0], UOp.const(elem_sz.bit_length() - 1)), dtypes.u32)
      return UOp.ins(RVOps.ADD, (base, scaled), dtypes.u32), UOp.const(off)
    scaled = idx if elem_sz == 1 else UOp.ins(RVOps.SLLI, (idx, UOp.const(elem_sz.bit_length() - 1)), dtypes.u32)
    return UOp.ins(RVOps.ADD, (base, scaled), dtypes.u32), UOp.const(0)
  return addr, UOp.const(0)

def _load_op(dt: DType) -> RVOps:
  if dt.bits <= 8: return RVOps.LB if dt.is_int and dt.is_signed else RVOps.LBU
  if dt.bits == 16: return RVOps.LH if dt.is_int and dt.is_signed else RVOps.LHU
  return RVOps.LW

def _store_op(dt: DType) -> RVOps:
  if dt.bits <= 8: return RVOps.SB
  if dt.bits == 16: return RVOps.SH
  return RVOps.SW

def _load_const_operand(s: UOp) -> UOp:
  if s.op is Ops.AFTER:
    base = _load_const_operand(s.src[0])
    return base.after(*s.src[1:]) if base is not s.src[0] else s
  if not is_int_const(s): return s
  v = const_int(s)
  return X0 if v == 0 else UOp.ins(RVOps.LI, (UOp.const(v),), s.dtype)

def _materialize_consts(x: UOp) -> UOp | None:
  if not x.is_ins: return None
  op = x.ins_op
  if op not in RVGroupOp.All or op in (RVOps.LABEL, RVOps.LI, RVOps.LUI, RVOps.AUIPC, RVOps.FENCE, RVOps.RET): return None
  src = x.src_without_body
  imm_idx = 1 if op is RVOps.JALR else len(src) - 1 if op in RVGroupOp.Immediate else -1
  keep_first = op in (RVGroupOp.Branch | {RVOps.JAL})
  nsrc = tuple(s if (i == imm_idx or (keep_first and i == 0)) else _load_const_operand(s) for i, s in enumerate(src))
  return None if nsrc == src else x.replace(src=(x.body, *nsrc))

def _make_alloc_vregs(wgpr: tuple[UOp, ...]):
  def alloc_vregs(ctx: IselContext, x: UOp) -> UOp | None:
    if not x.is_ins or x.ins_op not in RVGroupOp.All: return None
    if x.dtype is dtypes.void: return None
    if vdef(x) is not None: return None
    role = x.arg.role if hasattr(x.arg, "role") else ""
    return UOp.ins(x.ins_op, x.src_without_body, x.dtype, *ctx.vreg(x.dtype, wgpr), role=role)
  return alloc_vregs

def make_rv32_isel(wgpr: tuple[UOp, ...] = DEFAULT_WGPR) -> PatternMatcher:
  return PatternMatcher([
    (UPat(Ops.PARAM, name="u"), lambda u: rv_arg(u.arg.slot, dtype=u.dtype)
     if not u.arg.file and u.arg.vmin_vmax is not None else None),
    (UPat(Ops.SPECIAL, name="u"), lambda u: UOp.ins(RVOps.LW,
      (X0, UOp.const({"worker_x": 0x20, "worker_y": 0x24, "worker_id": 0x28}[u.arg])), u.dtype)),
    # a typed integer constant is just its value in a 32-bit register
    (UPat(Ops.CAST, src=(UPat(Ops.CONST, name="c"),), name="u"),
     lambda u, c: UOp.const(int(c.arg)) if u.dtype.is_int or u.dtype is dtypes.bool else None),
    # arithmetic & bitwise
    (UPat(Ops.ADD, name="u"), lambda u: _bin_imm_or_reg(u, RVOps.ADD, RVOps.ADDI)),
    (UPat(Ops.SUB, name="u"), lambda u: UOp.ins(RVOps.ADDI, (u.src[0], UOp.const(-const_int(u.src[1]))), u.dtype)
     if is_int_const(u.src[1]) and fits_simm12(-const_int(u.src[1])) else UOp.ins(RVOps.SUB, u.src, u.dtype)),
    (UPat(Ops.MUL, name="u"), lambda u: UOp.ins(RVOps.MUL, u.src, u.dtype)),
    (UPat(Ops.DIV, name="u"), lambda u: UOp.ins(RVOps.DIV if u.dtype.is_signed else RVOps.DIVU, u.src, u.dtype)),
    (UPat(Ops.MOD, name="u"), lambda u: UOp.ins(RVOps.REM if u.dtype.is_signed else RVOps.REMU, u.src, u.dtype)),
    (UPat(Ops.AND, name="u"), lambda u: _bin_imm_or_reg(u, RVOps.AND, RVOps.ANDI)),
    (UPat(Ops.OR,  name="u"), lambda u: _bin_imm_or_reg(u, RVOps.OR,  RVOps.ORI)),
    (UPat(Ops.XOR, name="u"), lambda u: _bin_imm_or_reg(u, RVOps.XOR, RVOps.XORI)),
    (UPat(Ops.SHL, name="u"), lambda u: _bin_imm_or_reg(u, RVOps.SLL, RVOps.SLLI, shift=True)),
    (UPat(Ops.SHR, name="u"), lambda u: _bin_imm_or_reg(u, RVOps.SRA if u.dtype.is_signed else RVOps.SRL,
                                                        RVOps.SRAI if u.dtype.is_signed else RVOps.SRLI, shift=True)),
    (UPat(Ops.NEG, name="u"), lambda u: UOp.ins(RVOps.SUB, (X0, u.src[0]), u.dtype)),

    # comparisons (produce 0/1 in a GPR)
    (UPat(Ops.CMPLT, name="u"), lambda u: _bin_imm_or_reg(
      u, RVOps.SLT if u.src[0].dtype.is_signed else RVOps.SLTU,
      RVOps.SLTI if u.src[0].dtype.is_signed else RVOps.SLTIU)),
    (UPat(Ops.CMPEQ, name="u"), lambda u: UOp.ins(RVOps.SLTIU, (UOp.ins(RVOps.XOR, u.src, dtypes.u32), UOp.const(1)), dtypes.bool)),
    (UPat(Ops.CMPNE, name="u"), lambda u: UOp.ins(RVOps.SLTU, (X0, UOp.ins(RVOps.XOR, u.src, dtypes.u32)), dtypes.bool)),

    # branchless integer WHERE: b + (0 - cond) & (a - b)
    (UPat(Ops.WHERE, name="u"), lambda u: UOp.ins(
      RVOps.ADD, (u.src[2], UOp.ins(RVOps.AND, (UOp.ins(RVOps.SUB, (X0, u.src[0]), u.dtype),
                                                UOp.ins(RVOps.SUB, (u.src[1], u.src[2]), u.dtype)), u.dtype)), u.dtype)
     if u.dtype.is_int or u.dtype is dtypes.bool else None),

    # memory LOAD / STORE
    (UPat(Ops.LOAD, src=(UPat.var("addr"),), name="u"), lambda addr, u: UOp.ins(_load_op(u.dtype), _fold_mem_addr(addr), u.dtype)),
    (UPat(Ops.STORE, src=(UPat.var("addr"), UPat.var("val"))),
     lambda addr, val: UOp.ins(_store_op(val.dtype), (_fold_mem_addr(addr)[0], val, _fold_mem_addr(addr)[1]), dtypes.void)),

    # unbounded while/polling loop backedge (keep body effect u.src[0] as trailing dep so linearize schedules it before BNE)
    (UPat(Ops.BACKEDGE, name="u"), lambda u: UOp.ins(RVOps.BNE, (u.src[1], u.src[2], X0, u.src[0]), dtypes.void)),

    # materialize non-immediate constants & assign virtual registers
    (UPat(Ops.CALL, name="x"), _materialize_consts),
    (UPat(Ops.CALL, name="x"), _make_alloc_vregs(wgpr)),
  ])

# ---- Pre-regalloc & Post-regalloc line_rewrite matchers ----

def _make_pre_regalloc(wgpr: tuple[UOp, ...]):
  def lower_range(ctx: LinearContext, x: UOp) -> tuple[UOp, list[UOp]]:
    if x.dtype is dtypes.void: return x, [x, rv_label(x)]
    bound = x.src[0].without_after
    bound_r = _load_const_operand(bound)
    extra = [bound_r] if bound_r is not bound and bound_r is not X0 else []
    if extra and vdef(bound_r) is None:
      bound_r = UOp.ins(bound_r.ins_op, bound_r.src_without_body, bound_r.dtype, *ctx.vreg(bound_r.dtype, wgpr, name=f"bnd{x.arg.axis}"))
      extra = [bound_r]
    idx = UOp.ins(RVOps.LI, (UOp.const(0),), x.dtype, *ctx.vreg(x.dtype, wgpr, name=x.arg.name or f"r{x.arg.axis}"))
    start = rv_label(x)
    exit_key = start  # exit label is keyed by rv_label(x) (matches x86.py)
    cmp_op = RVOps.BGE if x.dtype.is_signed else RVOps.BGEU
    br = UOp.ins(cmp_op, (exit_key, idx, bound_r), dtypes.void)
    return idx.after(x), [*extra, idx, x, start, br]

  def lower_end(ctx: LinearContext, x: UOp, c: UOp) -> tuple[UOp, list[UOp]]:
    rng = c.src[1]
    inc = UOp.ins(RVOps.ADDI, (c, UOp.const(1)), c.dtype, *regs(c.src[0]))
    jmp = UOp.ins(RVOps.JAL, (rng,), dtypes.void)
    end_lbl = rv_label(rv_label(rng))
    return x.replace(src=(x.src[0], rng)), [inc, jmp, end_lbl]

  return PatternMatcher([
    (UPat(Ops.RANGE, name="x"), lower_range),
    (UPat(Ops.END, src=(UPat(), UPat(Ops.AFTER, name="c")), name="x"), lower_end),
    (UPat(Ops.END, name="x"), lambda x: (x, [UOp.ins(RVOps.JAL, (x.src[1],), dtypes.void), rv_label(rv_label(x.src[1]))])),
  ])

post_regalloc_matcher = PatternMatcher([
  (UPat(Ops.SINK, name="x"), lambda x: (x, [UOp.ins(RVOps.RET, (), dtypes.void)])),
  (UPat.ins(RVOps.LI, name="x"), lambda x: (x, expand_li(x))),
  # drop no-op register moves: addi xd, xd, 0
  (UPat.ins(RVOps.ADDI, name="x"), lambda x: (x.src_without_body[0], [])
   if is_int_const(x.src_without_body[1]) and const_int(x.src_without_body[1]) == 0
   and vdef(x) is not None and vdef(x) is vdef(x.src_without_body[0]) else None),
  # strip structural markers that don't emit words
  (UPat((Ops.RANGE, Ops.END, Ops.CONST, Ops.BUFFER, Ops.ALLOC, Ops.PARAM, Ops.NOOP, Ops.AFTER, Ops.INDEX), name="x"),
   lambda x: (x, [])),
])

# ---- RV32IM binary encoding (directly backed by hw.isa) ----

_RV_ENC = {
  RVOps.ADD: hw_isa.add, RVOps.SUB: hw_isa.sub, RVOps.SLL: hw_isa.sll, RVOps.SLT: hw_isa.slt, RVOps.SLTU: hw_isa.sltu,
  RVOps.XOR: hw_isa.xor, RVOps.SRL: hw_isa.srl, RVOps.SRA: hw_isa.sra, RVOps.OR: hw_isa.or_, RVOps.AND: hw_isa.and_,
  RVOps.MUL: hw_isa.mul, RVOps.MULH: hw_isa.mulh, RVOps.MULHSU: hw_isa.mulhsu, RVOps.MULHU: hw_isa.mulhu,
  RVOps.DIV: hw_isa.div, RVOps.DIVU: hw_isa.divu, RVOps.REM: hw_isa.rem, RVOps.REMU: hw_isa.remu,
  RVOps.ADDI: hw_isa.addi, RVOps.SLTI: hw_isa.slti, RVOps.SLTIU: hw_isa.sltiu,
  RVOps.XORI: hw_isa.xori, RVOps.ORI: hw_isa.ori, RVOps.ANDI: hw_isa.andi,
  RVOps.SLLI: hw_isa.slli, RVOps.SRLI: hw_isa.srli, RVOps.SRAI: hw_isa.srai,
  RVOps.LUI: hw_isa.lui, RVOps.AUIPC: hw_isa.auipc,
  RVOps.LB: hw_isa.lb, RVOps.LH: hw_isa.lh, RVOps.LW: hw_isa.lw, RVOps.LBU: hw_isa.lbu, RVOps.LHU: hw_isa.lhu,
  RVOps.SB: hw_isa.sb, RVOps.SH: hw_isa.sh, RVOps.SW: hw_isa.sw, RVOps.FENCE: hw_isa.fence,
  RVOps.BEQ: hw_isa.beq, RVOps.BNE: hw_isa.bne, RVOps.BLT: hw_isa.blt,
  RVOps.BGE: hw_isa.bge, RVOps.BLTU: hw_isa.bltu, RVOps.BGEU: hw_isa.bgeu,
  RVOps.JAL: hw_isa.jal, RVOps.JALR: hw_isa.jalr,
}

def _reg_num(u: UOp, ren: ISARenderer) -> int:
  r = rdef(u, ren)
  if r is None: raise RuntimeError(f"expected physical RV32 register, got {u.op.name} ({u.arg})")
  return int(r.arg.slot)

def encode_rv32(u: UOp, ren: ISARenderer, targets: dict[UOp, int], pc: int) -> int:
  op = u.ins_op
  src = u.src_without_body
  if op is RVOps.RET: return int(hw_isa.jalr(rd=0, rs1=1, imm=0))
  if op is RVOps.FENCE: return int(hw_isa.fence(imm=const_int(src[0]) if src else 0xFF))
  if op in RVGroupOp.RType:
    return int(_RV_ENC[op](rd=_reg_num(u, ren), rs1=_reg_num(src[0], ren), rs2=_reg_num(src[1], ren)))
  if op in RVGroupOp.IType:
    return int(_RV_ENC[op](rd=_reg_num(u, ren), rs1=_reg_num(src[0], ren), imm=const_int(src[1])))
  if op in RVGroupOp.ShiftImm:
    return int(_RV_ENC[op](rd=_reg_num(u, ren), rs1=_reg_num(src[0], ren), shamt=const_int(src[1])))
  if op in (RVOps.LUI, RVOps.AUIPC):
    return int(_RV_ENC[op](rd=_reg_num(u, ren), imm=const_int(src[0]) & 0xFFFFF))
  if op in RVGroupOp.Load:
    return int(_RV_ENC[op](rd=_reg_num(u, ren), rs1=_reg_num(src[0], ren), imm=const_int(src[1])))
  if op in RVGroupOp.Store:
    return int(_RV_ENC[op](rs1=_reg_num(src[0], ren), rs2=_reg_num(src[1], ren), imm=const_int(src[2])))
  if op in RVGroupOp.Branch:
    off = targets[src[0]] - pc
    if off % 2 or not -4096 <= off < 4096: raise ValueError(f"RV32 branch offset out of range: {off}")
    return int(_RV_ENC[op](rs1=_reg_num(src[1], ren), rs2=_reg_num(src[2], ren), imm=off))
  if op is RVOps.JAL:
    rd = _reg_num(u, ren) if rdef(u, ren) is not None else 0
    off = targets[src[0]] - pc
    if off % 2 or not -(1 << 20) <= off < (1 << 20): raise ValueError(f"RV32 JAL offset out of range: {off}")
    return int(hw_isa.jal(rd=rd, imm=off))
  if op is RVOps.JALR:
    rd = _reg_num(u, ren) if rdef(u, ren) is not None else 0
    imm = const_int(src[1]) if len(src) > 1 else 0
    return int(hw_isa.jalr(rd=rd, rs1=_reg_num(src[0], ren), imm=imm))
  raise RuntimeError(f"unsupported RV32 op {op}")

# ---- RV32Renderer ----

class RV32Renderer(ISARenderer):
  physical_regs = RV_PHYSICAL_REGS

  def __init__(self, wgpr: tuple[UOp, ...] = DEFAULT_WGPR, scratch_regs: tuple[UOp, ...] = DEFAULT_SCRATCH,
               spill_base: UOp = LOCAL_BASE, spill_offset: int = 0):
    self.wgpr = wgpr
    self.scratch_regs = scratch_regs
    self.spill_base = spill_base
    self.spill_offset = spill_offset
    self.isel_matcher = make_rv32_isel(wgpr)
    self.pre_regalloc_matcher = _make_pre_regalloc(wgpr)
    self.post_regalloc_matcher = post_regalloc_matcher

  def is_label(self, u: UOp) -> bool: return u.is_ins and u.ins_op is RVOps.LABEL

  def jump_targets(self, u: UOp) -> tuple[UOp, ...]:
    if u.is_ins and u.ins_op in (RVGroupOp.Branch | {RVOps.JAL}): return (u.src_without_body[0],)
    return ()

  def falls_through(self, u: UOp) -> bool:
    if u.is_ins and u.ins_op in (RVOps.JAL, RVOps.JALR) and rdef(u, self) == RA: return True
    return not (u.is_ins and u.ins_op in (RVOps.JAL, RVOps.JALR, RVOps.RET))

  def copy(self, x: UOp, reg: UOp) -> UOp:
    return UOp.ins(RVOps.ADDI, (x, UOp.const(0)), x.dtype, reg)

  def spill(self, spill_slot: int, x: UOp) -> UOp:
    return UOp.ins(RVOps.SW, (self.spill_base, x, UOp.const(self.spill_offset + spill_slot)), dtypes.void)

  def fill(self, spill_slot: int, x: UOp, reg: UOp) -> UOp:
    return UOp.ins(RVOps.LW, (self.spill_base, UOp.const(self.spill_offset + spill_slot)), x.dtype, reg)

  def assemble(self, uops: list[UOp]) -> bytes:
    uops = relax_branches(uops, self)
    targets: dict[UOp, int] = {}
    pc = 0
    for u in uops:
      if not u.is_ins: continue
      if self.is_label(u): targets[u.src_without_body[0]] = pc
      else: pc += 4
    words: list[int] = []
    pc = 0
    for u in uops:
      if not u.is_ins or self.is_label(u): continue
      words.append(encode_rv32(u, self, targets, pc))
      pc += 4
    return struct.pack(f"<{len(words)}I", *words)

def relax_branches(uops: list[UOp], ren: RV32Renderer) -> list[UOp]:
  """Expand distant conditional jumps after register allocation and LI expansion.

  Iterate because expanding one branch can put another beyond B-type reach.
  New labels use the branch's position, so repeated instruction objects remain
  distinct in linear streams.
  """
  inverse = {RVOps.BEQ: RVOps.BNE, RVOps.BNE: RVOps.BEQ, RVOps.BLT: RVOps.BGE,
             RVOps.BGE: RVOps.BLT, RVOps.BLTU: RVOps.BGEU, RVOps.BGEU: RVOps.BLTU}
  while True:
    targets, pc = {}, 0
    for u in uops:
      if ren.is_label(u): targets[u.src_without_body[0]] = pc
      elif u.is_ins: pc += 4
    out, pc, changed = [], 0, False
    for i, u in enumerate(uops):
      if u.is_ins and u.ins_op in RVGroupOp.Branch and not -4096 <= targets[u.src_without_body[0]] - pc < 4096:
        target, a, b, *deps = u.src_without_body
        key = UOp(Ops.NOOP, arg=("long_branch", i, u))
        out.extend((UOp.ins(inverse[u.ins_op], (key, a, b, *deps), dtypes.void, role=u.arg.role),
                    UOp.ins(RVOps.JAL, (target,), dtypes.void, role=u.arg.role), rv_label(key)))
        changed = True
      else: out.append(u)
      if u.is_ins and not ren.is_label(u): pc += 4
    if not changed: return out
    uops = out
