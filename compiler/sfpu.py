from __future__ import annotations
import itertools, math, struct
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Sequence
from hw import isa
from hw.sfpu_lat import (
  SfpuError as SfpuCompileError,
  fix_sfpu_hazards,
  sfpu_decode,
  verify_sfpu_words,
)
from .ops import lower_reduce_to_loop, pm_simplify
from .uop import DType, GroupOp, Ops, PatternMatcher, Space, UOp, UPat, dtypes, graph_rewrite

DST_TILE_ROWS = 64  # FP32 Dst tile stride (64 rows x 16 cols = 1024 elements)
_SFPU_SPACES = (Space.DST, Space.LREG)
_DEFAULTS_L11_14 = {11: 0xBF800000, 12: 0x3B000000, 13: 0xBF2CC4C7, 14: 0xBEB08FF9}

# Pass A: Pure UOp lowering (PatternMatcher + graph_rewrite)

@dataclass(frozen=True)
class SfpuPrim:
  op: str
  mod: int = 0
  imm: int = 0
  space: Space | None = None

def sfpu_prim(op: str, dtype: DType, *srcs: UOp, mod: int = 0, imm: int = 0, space: Space | None = None) -> UOp:
  return UOp(Ops.SFPU, dtype, srcs, SfpuPrim(op, mod, imm, space))

def mulacc(a: UOp, b: UOp, c: UOp, *, neg_ab: bool = False, neg_c: bool = False) -> UOp:
  return UOp(Ops.MULACC, a.dtype, (a, b, c), (neg_ab, neg_c))

ARECIP_ERR = 0.0056       # SFPARECIP: worst-case relative error ~0.0056
RSQRT_SEED_ERR = 2.1e-5   # magic + quadratic seed relative error ~2.02e-5

# Minimax polynomial coefficients for SFPU transcendentals
_EXP2_POLY_BF16 = (0.6918017864227295, -0.03182661160826683, 0.34228965640068054)
_EXP2_POLY_FP32 = (
  1.0, 0.6931471824645996, 0.2402210682630539,
  0.055503569543361664, 0.009676031768321991, 0.0013390863314270973,
)
_LOG2_POLY_BF16 = (2.885390043258667, 0.9618448615074158, 0.5733158588409424)
_LOG2_POLY_FP32 = (2.885390043258667, 0.9618448615074158, 0.5733158588409424, 0.48057064414024353)
_SIN_POLY_BF16 = (1.0, -0.16666658222675323, 0.008333049714565277, -0.0001980901724891737)
_SIN_POLY_FP32 = (1.0, -0.16666658222675323, 0.008333049714565277, -0.0001980901724891737, 2.6051077384181553e-06)
_PI_CW1, _PI_CW2, _PI_CW3 = 3.1416015625, -8.907169103622437e-06, -1.741103261565513e-09

# terms of y*(1 + e + e^2 + ...) needed to reach `bits` + 3 guard bits from `seed_err`
def newton_terms(seed_err: float, bits: int) -> int:
  k = 1
  while seed_err ** (k + 1) > 2.0 ** -(bits + 3): k += 1
  return k

def _horner(x: UOp, coeffs: Sequence[float]) -> UOp:
  acc = UOp.const(x.dtype, coeffs[-1])
  for c in reversed(coeffs[:-1]):
    acc = acc * x + UOp.const(x.dtype, c)
  return acc

def _decomp_exp2(x: UOp, bits: int) -> UOp:
  dt = x.dtype
  if bits <= 11:
    z = (x + UOp.const(dt, 127.0)).minimum(UOp.const(dt, 254.0))
    e = sfpu_prim("EXEXP", dtypes.i32, z, mod=0)
    m = sfpu_prim("EXMAN", dtypes.u32, z, mod=0)
    s = sfpu_prim("SHFT_VAR", dtypes.u32, m, e, mod=0)
    f1 = sfpu_prim("SETEXP", dt, s, mod=1, imm=127)
    raw = sfpu_prim("SETEXP", dt, s, _horner(f1, _EXP2_POLY_BF16), mod=2)
    return (z < UOp.const(dt, 1.0)).where(UOp.const(dt, 0.0), raw)
  x_c = x.minimum(UOp.const(dt, 127.0)).maximum(UOp.const(dt, -126.0))
  magic = UOp.const(dt, 12582912.0)
  u = x_c + magic
  f = x_c - (u - magic)
  e = u.bitcast(dtypes.i32) + UOp.const(dtypes.i32, 127)
  scale = sfpu_prim("SETEXP", dt, e, UOp.const(dt, 1.0), mod=0)
  return (x < UOp.const(dt, -126.0)).where(UOp.const(dt, 0.0), scale * _horner(f, _EXP2_POLY_FP32))

def _decomp_recip(x: UOp, bits: int) -> UOp:
  dt = x.dtype
  y = sfpu_prim("ARECIP", dt, x, mod=0)
  e = mulacc(x, y, UOp.const(dt, 1.0), neg_ab=True)
  c = e
  for _ in range(newton_terms(ARECIP_ERR, bits) - 1):
    c = mulacc(c, e, e)
  return mulacc(c.minimum(UOp.const(dt, 1.0)), y, y)

def _rsqrt_seed(x: UOp) -> UOp:
  dt = x.dtype
  y = (UOp.const(dtypes.u32, 0x5F1110A0) - (x.bitcast(dtypes.u32) >> UOp.const(dtypes.u32, 1))).bitcast(dt)
  t = -(x * y) * y
  return y * mulacc(t, t + UOp.const(dt, 2.2533049), UOp.const(dt, 2.2825186))

def _decomp_rsqrt(x: UOp, bits: int) -> UOp:
  dt = x.dtype
  y = _rsqrt_seed(x)
  if RSQRT_SEED_ERR > 2.0 ** -(bits + 3):
    e = mulacc(x * y, y, UOp.const(dt, 1.0), neg_ab=True)
    y = mulacc(e, y * UOp.const(dt, 0.5), y)
  return y

def _decomp_sqrt(x: UOp, bits: int) -> UOp:
  dt = x.dtype
  y = _rsqrt_seed(x)
  s = x * y
  if RSQRT_SEED_ERR > 2.0 ** -(bits + 3):
    r = mulacc(s, s, x, neg_ab=True)
    s = mulacc(r, y * UOp.const(dt, 0.5), s)
  return s

def _decomp_log2(x: UOp, bits: int) -> UOp:
  dt = x.dtype
  e_f = sfpu_prim("EXEXP", dtypes.i32, x, mod=0).cast(dt)
  m = sfpu_prim("SETEXP", dt, x, mod=1, imm=127)
  t = (m - UOp.const(dt, 1.0)) * _decomp_recip(m + UOp.const(dt, 1.0), bits)
  return mulacc(t, _horner(t * t, _LOG2_POLY_BF16 if bits <= 11 else _LOG2_POLY_FP32), e_f)

def _decomp_sin(x: UOp, bits: int) -> UOp:
  dt = x.dtype
  magic = UOp.const(dt, 12582912.0)
  u = mulacc(x, UOp.const(dt, 1.0 / math.pi), magic)
  n_f = u - magic
  if bits <= 11:
    r = mulacc(n_f, UOp.const(dt, math.pi), x, neg_ab=True)
  else:
    r = mulacc(n_f, UOp.const(dt, _PI_CW1), x, neg_ab=True)
    r = mulacc(n_f, UOp.const(dt, _PI_CW2), r, neg_ab=True)
    r = mulacc(n_f, UOp.const(dt, _PI_CW3), r, neg_ab=True)
  s = r * _horner(r * r, _SIN_POLY_BF16 if bits <= 11 else _SIN_POLY_FP32)
  sign_flip = u.bitcast(dtypes.u32) << UOp.const(dtypes.u32, 31)
  return (s.bitcast(dtypes.u32) ^ sign_flip).bitcast(dt)

@lru_cache(maxsize=2)
def _make_pm_sfpu_decomp(bits: int) -> PatternMatcher:
  sfpu_f = (dtypes.fp32, dtypes.bf16)
  return pm_simplify + PatternMatcher([
    # Algebraic cleanup (do NOT re-associate float adds so (x + magic) - magic stays exact).
    (UPat(Ops.DIV, dtype=sfpu_f, space=_SFPU_SPACES, src=(UPat.var("a"), UPat.var("b"))),
     lambda a, b: a * b.recip()),
    (UPat(Ops.MUL, dtype=sfpu_f, space=_SFPU_SPACES,
          src=[UPat(Ops.MUL, src=[UPat.var("x"), UPat.const("c1")]), UPat.const("c2")]),
     lambda x, c1, c2: x * UOp.const(x.dtype, float(c1.arg) * float(c2.arg))),
    (UPat(Ops.ADD, dtype=sfpu_f, space=_SFPU_SPACES, src=[UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),))]),
     lambda a, b: a - b),
    (UPat(Ops.SUB, dtype=sfpu_f, space=_SFPU_SPACES, src=(UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),)))),
     lambda a, b: a + b),
    (UPat((Ops.MIN, Ops.MAX), dtype=(dtypes.i32, dtypes.u32), space=_SFPU_SPACES,
          src=(UPat.var("a"), UPat.var("b")), name="u"),
     lambda u, a, b: (a < b).where(a, b) if u.op is Ops.MIN else (a < b).where(b, a)),
    # Transcendental decompositions on Space.DST and Space.LREG
    (UPat(Ops.EXP2,  dtype=sfpu_f, space=_SFPU_SPACES, src=(UPat.var("x"),)), lambda x: _decomp_exp2(x, bits)),
    (UPat(Ops.RECIP, dtype=sfpu_f, space=_SFPU_SPACES, src=(UPat.var("x"),)), lambda x: _decomp_recip(x, bits)),
    (UPat(Ops.RSQRT, dtype=sfpu_f, space=_SFPU_SPACES, src=(UPat.var("x"),)), lambda x: _decomp_rsqrt(x, bits)),
    (UPat(Ops.SQRT,  dtype=sfpu_f, space=_SFPU_SPACES, src=(UPat.var("x"),)), lambda x: _decomp_sqrt(x, bits)),
    (UPat(Ops.LOG2,  dtype=sfpu_f, space=_SFPU_SPACES, src=(UPat.var("x"),)), lambda x: _decomp_log2(x, bits)),
    (UPat(Ops.SIN,   dtype=sfpu_f, space=_SFPU_SPACES, src=(UPat.var("x"),)), lambda x: _decomp_sin(x, bits)),
  ])

def _is_sfpu_mul(u: UOp) -> bool:
  return u.op is Ops.MUL and u.space in _SFPU_SPACES and not u.is_fpu and u.dtype.is_float

pm_sfpu_fma = pm_simplify + PatternMatcher([
  (UPat(Ops.ADD, space=_SFPU_SPACES, src=[UPat(Ops.MUL, src=(UPat.var("a"), UPat.var("b"))).named("m"), UPat.var("c")]),
   lambda m, a, b, c: mulacc(a, b, c) if _is_sfpu_mul(m) and c.dtype.is_float else None),
  (UPat(Ops.SUB, space=_SFPU_SPACES, src=(UPat(Ops.MUL, src=(UPat.var("a"), UPat.var("b"))).named("m"), UPat.var("c"))),
   lambda m, a, b, c: mulacc(a, b, c, neg_c=True) if _is_sfpu_mul(m) and c.dtype.is_float else None),
  (UPat(Ops.SUB, space=_SFPU_SPACES, src=(UPat.var("c"), UPat(Ops.MUL, src=(UPat.var("a"), UPat.var("b"))).named("m"))),
   lambda m, a, b, c: mulacc(a, b, c, neg_ab=True) if _is_sfpu_mul(m) and c.dtype.is_float else None),
  (UPat(Ops.NEG, space=_SFPU_SPACES, src=(UPat(Ops.MUL, src=(UPat.var("a"), UPat.var("b"))).named("m"),)),
   lambda m, a, b: mulacc(a, b, UOp.const(a.dtype, 0.0), neg_ab=True) if _is_sfpu_mul(m) else None),
  (UPat(Ops.MULACC, space=_SFPU_SPACES, src=(UPat(Ops.NEG, src=(UPat.var("a"),)), UPat.var("b"), UPat.var("c")), name="u"),
   lambda u, a, b, c: mulacc(a, b, c, neg_ab=not u.arg[0], neg_c=u.arg[1])),
  (UPat(Ops.MULACC, space=_SFPU_SPACES, src=(UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),)), UPat.var("c")), name="u"),
   lambda u, a, b, c: mulacc(a, b, c, neg_ab=not u.arg[0], neg_c=u.arg[1])),
  (UPat(Ops.MULACC, space=_SFPU_SPACES, src=(UPat.var("a"), UPat.var("b"), UPat(Ops.NEG, src=(UPat.var("c"),))), name="u"),
   lambda u, a, b, c: mulacc(a, b, c, neg_ab=u.arg[0], neg_c=not u.arg[1])),
])

def lower_sfpu_uops(root: UOp, *, precision: DType = dtypes.fp32) -> UOp:
  bits = 8 if precision is dtypes.bf16 else 24
  if bits == 8:
    # Keep explicit FP32 predicate inputs at FP32 accuracy so approximation error never flips a branch.
    comparisons = [u for u in root.toposort() if u.op in GroupOp.Comparison and u.src[0].dtype is dtypes.fp32]
    sensitive = [u for u in UOp.sink(*comparisons).toposort()
                 if u.dtype is dtypes.fp32 and u.op in (Ops.DIV, Ops.EXP2, Ops.LOG2, Ops.RECIP, Ops.RSQRT, Ops.SQRT, Ops.SIN)]
    if sensitive:
      precise = graph_rewrite(UOp.sink(*sensitive), _make_pm_sfpu_decomp(24))
      root = root.substitute(dict(zip(sensitive, precise.src, strict=True)))
  return graph_rewrite(graph_rewrite(root, _make_pm_sfpu_decomp(bits)), pm_sfpu_fma)

# ---------------------------------------------------------------------------------------------------------------------
# Constant encoding & L8..L14 tiering
# ---------------------------------------------------------------------------------------------------------------------

def _const_u32(u: UOp) -> int:
  if u.dtype.is_float: return struct.unpack("<I", struct.pack("<f", float(u.arg)))[0]
  if u.dtype is dtypes.bool: return 0xFFFFFFFF if u.arg else 0
  return int(u.arg) & 0xFFFFFFFF

def _is_bf16_exact(u: UOp) -> bool:
  return u.dtype.is_float and (_const_u32(u) & 0xFFFF) == 0

def _hw_const_reg(u: UOp) -> int | None:
  bits = _const_u32(u)
  if bits == 0: return isa.LReg.ZERO
  if u.dtype.is_float and bits == 0x3F800000: return isa.LReg.ONE
  if u.dtype.is_float and bits == 0x3F56594B: return isa.LReg.CONST_0_8373
  return None

def _emit_loadi32(out: list[int], rd: int, u: UOp) -> None:
  assert 0 <= rd < 8, f"SFPLOADI requires L0..L7, got L{rd}"
  bits = _const_u32(u)
  hi, lo = (bits >> 16) & 0xFFFF, bits & 0xFFFF
  if not u.dtype.is_float and 0 <= bits <= 0xFFFF:
    out.append(isa.SFPLOADI(lreg=rd, mode=isa.LoadImm.USHORT, imm=bits))
  elif not u.dtype.is_float and -0x8000 <= (bits - (1 << 32) if bits >= (1 << 31) else bits) < 0:
    out.append(isa.SFPLOADI(lreg=rd, mode=isa.LoadImm.SHORT, imm=bits & 0xFFFF))
  elif lo == 0:
    out.append(isa.SFPLOADI(lreg=rd, mode=isa.LoadImm.FLOATB, imm=hi))
  else:
    out.append(isa.SFPLOADI(lreg=rd, mode=isa.LoadImm.FLOATB, imm=hi))
    out.append(isa.SFPLOADI(lreg=rd, mode=isa.LoadImm.LOWER, imm=lo))

# preserves L0 when it is live-in
def _emit_prologue_consts(
  const_regs: dict[UOp, int],
  live_in_regs: set[int],
  max_regs: int,
) -> list[int]:
  prog = [(r, c) for c, r in sorted(const_regs.items(), key=lambda kv: kv[1]) if 11 <= r <= 14]
  if not prog: return []
  needs_l0 = any(_DEFAULTS_L11_14.get(r) != _const_u32(c) for r, c in prog)
  save_reg: int | None = None
  out: list[int] = []
  if needs_l0 and 0 in live_in_regs:
    save_reg = next((r for r in range(1, max_regs) if r not in live_in_regs), None)
    assert save_reg is not None, "no free register to preserve live-in L0 across SFPCONFIG"
    out.append(isa.SFPMOV(dest=save_reg))
  for r, c in prog:
    if _DEFAULTS_L11_14.get(r) == _const_u32(c):
      out.append(isa.SFPCONFIG(target=r, mode=1))
    else:
      _emit_loadi32(out, 0, c)
      out.append(isa.SFPCONFIG(target=r))
  if save_reg is not None:
    out.append(isa.SFPMOV(src=save_reg))
  return fix_sfpu_hazards(out)

# INT32 for non-floats, so FP32 denormal flushing never corrupts integers or masks
def _sfpu_fmt(dt: DType) -> isa.SfpuFormat:
  return isa.SfpuFormat.FP32 if dt.is_float else isa.SfpuFormat.INT32

def _iadd_immediate(u: UOp) -> tuple[UOp, UOp, int] | None:
  if not u.dtype.is_int or u.op not in (Ops.ADD, Ops.SUB): return None
  var, const = u.src
  if u.op is Ops.ADD and var.op is Ops.CONST: var, const = const, var
  if const.op is Ops.CONST:
    imm = int(const.arg) if u.op is Ops.ADD else -int(const.arg)
    if -2048 <= imm < 2048: return var, const, imm
  return None

# fixed hardware constants in L8..L10, up to 4 SFPCONFIG-programmed ones in L11..L14
def _assign_const_regs(
  nodes: Sequence[UOp],
  *,
  preserve_l11: bool = False,
  allow_non_default_cfg: bool = True,
  min_uses_for_cfg: int = 1,
) -> tuple[dict[UOp, int], bool]:
  counts: dict[UOp, int] = {}
  for u in nodes:
    immediate = _iadd_immediate(u)
    for idx, s in enumerate(u.src):
      if s.op is not Ops.CONST: continue
      if u.op in (Ops.SHL, Ops.SHR) and idx == 1: continue
      if immediate and s is immediate[1]: continue
      counts[s] = counts.get(s, 0) + 1

  const_regs: dict[UOp, int] = {}
  prog_candidates: list[UOp] = []
  for c in counts:
    if (hw_r := _hw_const_reg(c)) is not None: const_regs[c] = hw_r
    else: prog_candidates.append(c)

  prog_slots = [12, 13, 14] if preserve_l11 else [11, 12, 13, 14]
  if (neg_one := next((c for c in prog_candidates if c.dtype.is_float and _const_u32(c) == 0xBF800000), None)) is not None:
    const_regs[neg_one] = 11
    if 11 in prog_slots: prog_slots.remove(11)
    prog_candidates.remove(neg_one)

  l11_repurposed = False
  if allow_non_default_cfg:
    eligible = [c for c in prog_candidates if counts[c] >= min_uses_for_cfg]
    eligible.sort(key=lambda c: (0 if not _is_bf16_exact(c) else 1, -counts[c], _const_u32(c)))
    for c, slot in zip(eligible, prog_slots):
      const_regs[c] = slot
      if slot == 11: l11_repurposed = True
  return const_regs, l11_repurposed

# Pass C: Single-pass physical L0..L7 register allocation & Tensix SFPU emission

class _OutOfRegs(Exception):
  pass

class _DstAliasConflict(Exception):
  pass

@dataclass(frozen=True)
class CompiledSfpuPass:
  prologue: tuple[int, ...]
  body: tuple[int, ...]
  epilogue: tuple[int, ...]
  inputs: dict[UOp, int]
  outputs: dict[UOp, int]
  l11_used: bool
  peak_regs: int
  reg_inputs: dict[UOp, int] = field(default_factory=dict)
  reg_outputs: dict[UOp, int] = field(default_factory=dict)
  footprints: int = 32

  def to_uops(self, role: str = "trisc1", *, axis: int = 0) -> list[UOp]:
    """Emit this SFPU pass as a flat list[UOp] of Tensix UOp.ins + RV32 footprint RANGE/END."""
    from .isa.tensix import tt_ins
    dec = lambda w: tt_ins(isa.decode(w), role=role)
    out: list[UOp] = [dec(w) for w in self.prologue]
    if self.body:
      out.append(tt_ins(isa.SETRWC(mask=0xF), role=role))
      if self.footprints == 1:
        out.extend(dec(w) for w in self.body)
      else:
        rng = UOp.range(self.footprints, axis, "fp")
        out.append(rng)
        out.extend(dec(w) for w in self.body)
        out.append(tt_ins(isa.INCRWC(dst=2), role=role))
        out.append(UOp.noop().end(rng))
      out.append(tt_ins(isa.SETRWC(mask=0xF), role=role))
    out.extend(dec(w) for w in self.epilogue)
    return out

@dataclass(frozen=True)
class CompiledSfpu:
  passes: tuple[CompiledSfpuPass, ...]
  dst_tiles: int
  output_tiles: dict[UOp, int]
  root_tiles: tuple[int, ...] = ()

  def to_linear(self, role: str = "trisc1") -> UOp:
    uops: list[UOp] = []
    for i, p in enumerate(self.passes):
      uops.extend(p.to_uops(role=role, axis=i))
    return UOp.linear(*uops, arg=role)

@dataclass(frozen=True)
class CompiledSfpuLoop:
  loop: UOp
  init_passes: tuple[CompiledSfpuPass, ...]
  body_passes: tuple[CompiledSfpuPass, ...]
  dst_carries: dict[UOp, int]
  reg_carries: dict[UOp, int]
  dst_tiles: int

def _is_direct_cmp(u: UOp) -> bool:
  return u.op in GroupOp.Comparison or (u.op is Ops.NOT and u.dtype is dtypes.bool and u.src[0].op in GroupOp.Comparison)

def _verify_dst_store_load_order(body: Sequence[int], *, retryable: bool = False) -> None:
  written: set[int] = set()
  for idx, w in enumerate(body):
    match w >> 24:
      case 0x72: written.add((w & 0x3FF) // DST_TILE_ROWS)
      case 0x70:
        if (t := (w & 0x3FF) // DST_TILE_ROWS) in written:
          cls = _DstAliasConflict if retryable else SfpuCompileError
          raise cls(f"Dst tile {t} read by SFPLOAD at word {idx} after already overwritten by SFPSTORE")

def _verify_compiled_pass(
  pro: Sequence[int],
  body: Sequence[int],
  epi: Sequence[int],
  *,
  footprints: int = 32,
  pinned_ro: set[int] = frozenset(),
) -> None:
  is_loop = footprints > 1
  verify_sfpu_words(pro)
  verify_sfpu_words(body, is_loop=is_loop)
  verify_sfpu_words(epi)
  verify_sfpu_words(list(pro) + list(body) + list(epi))
  _verify_dst_store_load_order(body)
  if pinned_ro:
    ro_mask = 0
    for r in pinned_ro: ro_mask |= 1 << r
    for idx, w in enumerate(body):
      if (info := sfpu_decode(w)) is not None and (hit := info.writes & ro_mask):
        reg = (hit & -hit).bit_length() - 1
        raise SfpuCompileError(f"word {idx} ({info.op}) clobbers read-only pinned register L{reg}")

class _PassLowerer:

  def __init__(
    self,
    nodes: Sequence[UOp],
    dst_inputs: dict[UOp, int],
    outputs: dict[UOp, int],
    const_regs: dict[UOp, int],
    *,
    reg_inputs: dict[UOp, int] | None = None,
    reg_outputs: dict[UOp, int] | None = None,
    max_regs: int = 8,
    addr_mode: int = 0,
    footprints: int = 32,
  ):
    if not (1 <= max_regs <= 8): raise ValueError(f"max_regs must be in 1..8, got {max_regs}")
    self.nodes = tuple(nodes)
    self.node_set = set(self.nodes)
    self.dst_inputs = dst_inputs
    self.outputs = outputs
    self.reg_inputs = dict(reg_inputs or {})
    self.reg_outputs = dict(reg_outputs or {})
    self.const_regs = const_regs
    self.max_regs = max_regs
    self.addr_mode = addr_mode
    self.footprints = footprints

    # In a multi-footprint sweep, any reg_input NOT overwritten as a reg_output must stay intact for later footprints.
    out_reg_set = set(self.reg_outputs.values())
    self.pinned_ro: set[int] = {r for r in self.reg_inputs.values() if r not in out_reg_set} if footprints > 1 else set()

    self.reg: dict[UOp, int] = {}
    self.owner: dict[int, UOp] = {}
    self.free: list[int] = list(range(max_regs))
    self.peak_regs: int = 0
    self.body: list[int] = []
    self._stored: set[UOp] = set()
    self._written_tiles: set[int] = set()

    for u, r in self.reg_inputs.items():
      if not (0 <= r < max_regs): raise ValueError(f"reg_input L{r} outside max_regs={max_regs}")
      if r in self.owner and self.owner[r] is not u:
        raise ValueError(f"distinct reg_inputs assigned to the same register L{r}")
      if r in self.free: self.free.remove(r)
      self.bind(u, r)
    self._touch_peak()

    # Fuse single-use comparisons directly into WHERE predication.
    raw_uses: dict[UOp, int] = {}
    for u in self.nodes:
      for s in u.src: raw_uses[s] = raw_uses.get(s, 0) + 1
    for out_u in (*outputs, *self.reg_outputs):
      raw_uses[out_u] = raw_uses.get(out_u, 0) + 1

    self.fused_cmps: set[UOp] = set()
    all_outs = set(outputs) | set(self.reg_outputs)
    for u in self.nodes:
      if u.op is Ops.WHERE and u.src[0] in self.node_set and u.src[0] not in all_outs:
        cond = u.src[0]
        if raw_uses.get(cond, 0) == 1 and _is_direct_cmp(cond):
          if cond.op is Ops.NOT:
            inner = cond.src[0]
            if inner in self.node_set and inner not in all_outs and raw_uses.get(inner, 0) == 1:
              self.fused_cmps |= {cond, inner}
          else:
            self.fused_cmps.add(cond)

    self.uses: dict[UOp, int] = {}
    for u in self.nodes:
      if u in self.fused_cmps: continue
      for s in self._effective_srcs(u):
        self.uses[s] = self.uses.get(s, 0) + 1
    for out_u in (*outputs, *self.reg_outputs):
      self.uses[out_u] = self.uses.get(out_u, 0) + 1

  def _effective_srcs(self, u: UOp) -> tuple[UOp, ...]:
    if u.op is Ops.WHERE and u.src[0] in self.fused_cmps:
      cond = u.src[0]
      cmp_u = cond.src[0] if cond.op is Ops.NOT else cond
      return (*cmp_u.src, u.src[1], u.src[2])
    return u.src

  # ---- register pool ----

  def _touch_peak(self):
    self.peak_regs = max(self.peak_regs, self.max_regs - len(self.free))

  def _evict_one(self, protect: set[int]) -> bool:
    for r in range(self.max_regs):
      u = self.owner.get(r)
      if u is None or r in protect or r in self.pinned_ro or u in self.reg_inputs: continue
      can_reload = u in self.dst_inputs and self.dst_inputs[u] not in self._written_tiles
      if can_reload or u.op is Ops.CONST:
        self.reg.pop(u, None)
        self.owner.pop(r, None)
        self.free.append(r)
        self.free.sort()
        return True
    return False

  def alloc(self, protect: set[int] | None = None, *, prefer: int | None = None) -> int:
    if not self.free and not self._evict_one(protect or set()):
      raise _OutOfRegs()
    if prefer is not None and prefer in self.free:
      self.free.remove(prefer)
      r = prefer
    else:
      r = self.free.pop(0)
    self._touch_peak()
    return r

  def bind(self, u: UOp, r: int):
    assert 0 <= r < self.max_regs
    self.reg[u] = r
    self.owner[r] = u

  def free_reg(self, r: int):
    if 0 <= r < self.max_regs and r not in self.pinned_ro:
      u = self.owner.pop(r, None)
      if u is not None and self.reg.get(u) == r: self.reg.pop(u, None)
      if r not in self.free:
        self.free.append(r)
        self.free.sort()

  def drop_use(self, u: UOp):
    if u not in self.uses: return
    self.uses[u] -= 1
    if self.uses[u] <= 0 and u in self.reg:
      self.free_reg(self.reg[u])

  def is_last_use(self, u: UOp, count: int = 1) -> bool:
    return self.uses.get(u, 0) <= count

  def ensure(self, u: UOp, protect: set[int], *, need_writable: bool = False, need_lt12: bool = False) -> tuple[int, bool]:
    if u in self.reg: return self.reg[u], False
    if u.op is Ops.CONST:
      cr = self.const_regs.get(u)
      if cr is not None and (not need_writable) and (not need_lt12 or cr < 12):
        return cr, False
      r = self.alloc(protect)
      _emit_loadi32(self.body, r, u)
      if self.uses.get(u, 0) > 1 and not need_writable:
        self.bind(u, r)
        return r, False
      return r, True
    if u in self.dst_inputs:
      tile = self.dst_inputs[u]
      r = self.alloc(protect)
      self.body.append(isa.SFPLOAD(lreg=r, format=_sfpu_fmt(u.dtype), addr=tile * DST_TILE_ROWS))
      self.bind(u, r)
      return r, False
    raise SfpuCompileError(f"operand {u.op.name} not available in pass")

  # never clobbers a live or pinned_ro register
  def _writable_copy(
    self, u: UOp, src_r: int, src_is_temp: bool, protect: set[int], count: int = 1, prefer: int | None = None,
  ) -> tuple[int, bool]:
    if src_is_temp and src_r < 8 and src_r not in self.pinned_ro:
      return src_r, True
    if src_r < 8 and src_r not in self.pinned_ro and u in self.reg and self.reg[u] == src_r and self.is_last_use(u, count):
      self.owner.pop(src_r, None)
      self.reg.pop(u, None)
      return src_r, True
    dst_r = self.alloc(protect | {src_r}, prefer=prefer)
    self.body.append(isa.SFPMOV(src=src_r, dest=dst_r))
    return dst_r, True

  def _release(self, srcs: Sequence[UOp], regs: Sequence[int], temps: Sequence[bool], keep: set[int] = frozenset()):
    for r, is_t in zip(regs, temps):
      if is_t and r not in keep: self.free_reg(r)
    for s in srcs: self.drop_use(s)

  # ---- predication ----

  def _int_order_key(self, value: UOp, src: int, dst: int):
    if value.dtype.is_signed and (value.op is Ops.LANE_ID or (value.op is Ops.CONST and 0 <= value.arg < 2**31)):
      self.body.append(isa.SFPMOV(src=src, dest=dst))
      return
    self.body.append(isa.SFPSHFT(imm=(-31) & 0xFFF, src=src, dest=dst, mode=7))
    self.body.append(isa.SFPSHFT(imm=(-1) & 0xFFF, src=dst, dest=dst, mode=5))
    if not value.dtype.is_signed: self.body.append(isa.SFPNOT(src=dst, dest=dst))
    self.body.append(isa.SFPXOR(src=src, dest=dst))

  def _emit_cmp_set_cc(self, cmp_u: UOp, invert: bool, protect: set[int]) -> None:
    op, (a, b) = cmp_u.op, cmp_u.src
    prot = set(protect)
    if op in (Ops.CMPEQ, Ops.CMPNE):
      mod = 6 if ((op is Ops.CMPEQ) ^ invert) else 2
      if b.op is Ops.CONST and _const_u32(b) == 0:
        ra, ta = self.ensure(a, prot)
        self.body.append(isa.SFPSETCC(src=ra, mode=mod))
        if ta: self.free_reg(ra)
      elif a.op is Ops.CONST and _const_u32(a) == 0:
        rb, tb = self.ensure(b, prot)
        self.body.append(isa.SFPSETCC(src=rb, mode=mod))
        if tb: self.free_reg(rb)
      else:
        ra, ta = self.ensure(a, prot)
        rb, tb = self.ensure(b, prot | {ra})
        diff = self.alloc(prot | {ra, rb})
        if a.dtype.is_float:
          self.body.append(isa.SFPADD(a=isa.LReg.ONE, b=ra, c=rb, dest=diff, mode=2))
        else:
          self.body.append(isa.SFPMOV(src=ra, dest=diff))
          self.body.append(isa.SFPXOR(src=rb, dest=diff))
        self.body.append(isa.SFPSETCC(src=diff, mode=mod))
        self.free_reg(diff)
        if ta: self.free_reg(ra)
        if tb: self.free_reg(rb)
      return

    assert op is Ops.CMPLT
    if a.dtype.is_float:
      ra, ta = self.ensure(a, prot)
      rb, tb = self.ensure(b, prot | {ra}, need_lt12=True)
      self.body.append(isa.SFPLE(src=ra, dest=rb, mode=1) if invert else isa.SFPGT(src=ra, dest=rb, mode=1))
      if ta: self.free_reg(ra)
      if tb: self.free_reg(rb)
    else:
      ra, ta = self.ensure(a, prot)
      rb, tb = self.ensure(b, prot | {ra})
      sm_a = self.alloc(prot | {ra, rb})
      sm_b = self.alloc(prot | {ra, rb, sm_a})
      self._int_order_key(a, ra, sm_a)
      self._int_order_key(b, rb, sm_b)
      self.body.append(isa.SFPLE(src=sm_a, dest=sm_b, mode=1) if invert else isa.SFPGT(src=sm_a, dest=sm_b, mode=1))
      self.free_reg(sm_b)
      self.free_reg(sm_a)
      if ta: self.free_reg(ra)
      if tb: self.free_reg(rb)

  def _emit_cmp_mask(self, u: UOp, prefer: int | None) -> int:
    op, (a, b) = u.op, u.src
    if op is Ops.CMPLT and a.dtype.is_float:
      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      vd, _ = self._writable_copy(b, rb, tb, {ra}, count=(2 if a is b else 1), prefer=prefer)
      self.body.append(isa.SFPGT(src=ra, dest=vd, mode=8))
      self._release((a, b), (ra, rb), (ta, False if vd == rb else tb), keep={vd})
      return vd
    if op is Ops.CMPLT:
      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      sm_a = self.alloc({ra, rb})
      sm_b = self.alloc({ra, rb, sm_a}, prefer=prefer)
      self._int_order_key(a, ra, sm_a)
      self._int_order_key(b, rb, sm_b)
      self.body.append(isa.SFPGT(src=sm_a, dest=sm_b, mode=8))
      self.free_reg(sm_a)
      self._release((a, b), (ra, rb), (ta, tb), keep={sm_b})
      return sm_b
    rd = self.alloc(prefer=prefer)
    self.body.append(isa.SFPMOV(src=isa.LReg.ZERO, dest=rd))
    self.body.append(isa.SFPENCC(imm=1, mode=2))
    self._emit_cmp_set_cc(u, False, {rd})
    self.body.append(isa.SFPLOADI(lreg=rd, mode=isa.LoadImm.SHORT, imm=0xFFFF))
    self.body.append(isa.SFPENCC(mode=2))
    self.drop_use(a)
    self.drop_use(b)
    return rd

  # ---- horizontal lane reduction ----

  def _emit_reduce_lanes(self, u: UOp, prefer: int | None) -> int:
    red_op, scope = u.arg
    x = u.src[0]
    if not u.dtype.is_float and red_op is not Ops.ADD:
      raise SfpuCompileError(f"REDUCE_LANES {red_op.name} requires float dtype")
    rx, tx = self.ensure(x, set())
    vd, _ = self._writable_copy(x, rx, tx, set(), prefer=prefer)
    self._release((x,), (rx,), (False if vd == rx else tx,), keep={vd})

    def combine(dst_r: int, src_r: int):
      match red_op:
        case Ops.ADD if u.dtype.is_float: self.body.append(isa.SFPADD(a=isa.LReg.ONE, b=dst_r, c=src_r, dest=dst_r))
        case Ops.ADD: self.body.append(isa.SFPIADD(src=src_r, dest=dst_r, mode=4))
        case Ops.MAX: self.body.append(isa.SFPSWAP(src=src_r, dest=dst_r, mode=9))
        case Ops.MIN: self.body.append(isa.SFPSWAP(src=src_r, dest=dst_r, mode=1))

    # Stage 1: reduce each 8-lane physical row via rotate-right butterfly (4, 2, 1).
    tmp = self.alloc({vd})
    for shift in (4, 2, 1):
      self.body.append(isa.SFPMOV(src=vd, dest=tmp))
      for _ in range(shift): self.body.append(isa.SFPSHFT2(src=tmp, dest=tmp, mode=3))
      combine(vd, tmp)
    self.free_reg(tmp)
    if scope == "row8": return vd

    # Stage 2 ("all"): transpose across the 4 physical rows via SFPTRANSP (clobbers L0..L7!).
    while self._evict_one({vd}): pass
    if self.max_regs < 4 or self.pinned_ro or any(r != vd for r in self.owner):
      raise _OutOfRegs()
    if vd != 0:
      self.body.append(isa.SFPMOV(src=vd))
      self.free_reg(vd)
      self.free.remove(0)
      vd = 0
    for r in (1, 2, 3): self.body.append(isa.SFPMOV(dest=r))
    self.body.append(isa.SFPTRANSP())
    combine(0, 1)
    combine(2, 3)
    combine(0, 2)
    self.peak_regs = max(self.peak_regs, 4)
    return 0

  # ---- main per-UOp emitter ----

  def emit_uop(self, u: UOp) -> int:
    op, dt, src, arg = u.op, u.dtype, u.src, u.arg
    prefer = self.reg_outputs.get(u)

    match op:
      case Ops.BITCAST:
        ra, ta = self.ensure(src[0], set())
        if ta and ra not in self.pinned_ro:
          self.drop_use(src[0])
          return ra
        if ra < 8 and ra not in self.pinned_ro and self.is_last_use(src[0]):
          self.owner.pop(ra, None)
          self.reg.pop(src[0], None)
          self.uses[src[0]] -= 1
          return ra
        rd = self.alloc({ra}, prefer=prefer)
        self.body.append(isa.SFPMOV(src=ra, dest=rd))
        self.drop_use(src[0])
        return rd

      case Ops.LANE_ID:
        rd = self.alloc(prefer=prefer)
        self.body.append(isa.SFPSHFT(imm=(-1) & 0xFFF, src=isa.LReg.LANE_X2, dest=rd, mode=5))
        return rd

      case Ops.REDUCE_LANES:
        return self._emit_reduce_lanes(u, prefer)

      case Ops.WHERE:
        cond, a, b = src
        if cond not in self.fused_cmps and b.op is Ops.CONST and _const_u32(b) == 0:
          rm, tm = self.ensure(cond, set())
          ra, ta = self.ensure(a, {rm})
          rd = self.alloc({rm, ra}, prefer=prefer)
          self.body.append(isa.SFPAND(imm=ra, src=rm, dest=rd, mode=1))
          self._release((cond, a, b), (rm, ra), (tm, ta), keep={rd})
          return rd

        fused = cond in self.fused_cmps
        if fused:
          invert = cond.op is Ops.NOT
          cmp_u = cond.src[0] if invert else cond
          dep_srcs, rm, tm = cmp_u.src, None, False
        else:
          rm, tm = self.ensure(cond, set())
          dep_srcs = (cond,)
        ra, ta = self.ensure(a, {rm} if rm is not None else set())
        rb, tb = self.ensure(b, ({rm} if rm is not None else set()) | {ra})
        all_srcs = (*dep_srcs, a, b)
        prot = ({rm} if rm is not None else set()) | {ra} | {self.reg[s] for s in dep_srcs if s in self.reg}
        b_occ = sum(1 for s in all_srcs if s is b)
        if tb and rb < 8 and rb not in prot and rb not in self.pinned_ro:
          rd = rb
        elif rb < 8 and rb not in prot and rb not in self.pinned_ro and self.reg.get(b) == rb and self.is_last_use(b, b_occ):
          self.owner.pop(rb, None)
          self.reg.pop(b, None)
          rd = rb
        else:
          rd = self.alloc(prot | {rb}, prefer=prefer)
          self.body.append(isa.SFPMOV(src=rb, dest=rd))
        self.body.append(isa.SFPENCC(imm=1, mode=2))
        if fused: self._emit_cmp_set_cc(cmp_u, invert, prot | {rd})
        else: self.body.append(isa.SFPSETCC(src=rm, mode=2))
        self.body.append(isa.SFPMOV(src=ra, dest=rd))
        self.body.append(isa.SFPENCC(mode=2))
        if tm and rm is not None: self.free_reg(rm)
        if ta: self.free_reg(ra)
        if tb and rb != rd: self.free_reg(rb)
        for s in all_srcs: self.drop_use(s)
        return rd

      case Ops.CMPLT | Ops.CMPEQ | Ops.CMPNE:
        return self._emit_cmp_mask(u, prefer)

      case Ops.MULACC:
        a, b, c = src
        neg_ab, neg_c = arg if isinstance(arg, tuple) else (False, False)
        ra, ta = self.ensure(a, set())
        rb, tb = self.ensure(b, {ra})
        rc, tc = self.ensure(c, {ra, rb})
        self._release((a, b, c), (ra, rb, rc), (ta, tb, tc))
        rd = self.alloc(prefer=prefer)
        self.body.append(isa.SFPMAD(a=ra, b=rb, c=rc, dest=rd, mode=(1 if neg_ab else 0) | (2 if neg_c else 0)))
        return rd

      case Ops.ADD | Ops.SUB | Ops.MUL if dt.is_float:
        a, b = src
        if op in (Ops.ADD, Ops.MUL):
          for var, cst in ((a, b), (b, a)):
            if cst.op is Ops.CONST and cst not in self.const_regs and _is_bf16_exact(cst) and var.op is not Ops.CONST:
              rv, tv = self.ensure(var, set())
              can_steal = (rv < 8 and rv not in self.pinned_ro
                           and (tv or (self.reg.get(var) == rv and self.is_last_use(var))))
              if can_steal:
                rd, _ = self._writable_copy(var, rv, tv, set(), prefer=prefer)
                imm16 = (_const_u32(cst) >> 16) & 0xFFFF
                self.body.append(isa.SFPADDI(imm=imm16, dest=rd) if op is Ops.ADD else isa.SFPMULI(imm=imm16, dest=rd))
                self.drop_use(var)
                self.drop_use(cst)
                return rd
        ra, ta = self.ensure(a, set())
        rb, tb = self.ensure(b, {ra})
        self._release((a, b), (ra, rb), (ta, tb))
        rd = self.alloc(prefer=prefer)
        match op:
          case Ops.ADD: self.body.append(isa.SFPADD(a=isa.LReg.ONE, b=ra, c=rb, dest=rd))
          case Ops.SUB: self.body.append(isa.SFPADD(a=isa.LReg.ONE, b=ra, c=rb, dest=rd, mode=2))
          case Ops.MUL: self.body.append(isa.SFPMUL(a=ra, b=rb, c=isa.LReg.ZERO, dest=rd))
        return rd

      case Ops.ADD | Ops.SUB if dt.is_int:
        a, b = src
        if immediate := _iadd_immediate(u):
          var, const, imm = immediate
          rv, temp = self.ensure(var, set())
          self._release((var, const), (rv,), (temp,))
          rd = self.alloc(prefer=prefer)
          self.body.append(isa.SFPIADD(imm=imm & 0xFFF, src=rv, dest=rd, mode=5))
          return rd
        ra, ta = self.ensure(a, set())
        rb, tb = self.ensure(b, {ra})
        vd, _ = self._writable_copy(b, rb, tb, {ra}, count=(2 if a is b else 1), prefer=prefer)
        self.body.append(isa.SFPIADD(src=ra, dest=vd, mode=4 if op is Ops.ADD else 6))
        self._release((a, b), (ra, rb), (ta, False if vd == rb else tb), keep={vd})
        return vd

      case Ops.MIN | Ops.MAX:
        if not dt.is_float: raise SfpuCompileError(f"integer {op.name} requires sign-mag conversion")
        a, b = src
        ra, ta = self.ensure(a, set())
        rb, tb = self.ensure(b, {ra})
        mod1 = 1 if op is Ops.MIN else 9
        if (ra >= 8) ^ (rb >= 8):
          if ra >= 8: a, b, ra, rb, ta, tb = b, a, rb, ra, tb, ta
          vd, _ = self._writable_copy(a, ra, ta, {rb}, prefer=prefer)
          self.body.append(isa.SFPSWAP(src=rb, dest=vd, mode=mod1))
          self._release((a, b), (ra, rb), (False if vd == ra else ta, tb), keep={vd})
          return vd
        vd, _ = self._writable_copy(a, ra, ta, {rb}, count=(2 if a is b else 1), prefer=prefer)
        vc, _ = self._writable_copy(b, rb, tb, {vd}, count=(2 if a is b else 1))
        self.body.append(isa.SFPSWAP(src=vc, dest=vd, mode=mod1))
        self.free_reg(vc)
        self._release((a, b), (ra, rb), (False if vd == ra else ta, False if vc == rb else tb), keep={vd})
        return vd

      case Ops.NEG:
        ra, ta = self.ensure(src[0], set())
        if dt.is_float:
          self._release(src, (ra,), (ta,))
          rd = self.alloc(prefer=prefer)
          self.body.append(isa.SFPMOV(src=ra, dest=rd, mode=1))
          return rd
        vd, _ = self._writable_copy(src[0], ra, ta, set(), prefer=prefer)
        self.body.append(isa.SFPIADD(src=isa.LReg.ZERO, dest=vd, mode=6))
        self._release(src, (ra,), (False if vd == ra else ta,), keep={vd})
        return vd

      case Ops.ABS | Ops.NOT:
        ra, ta = self.ensure(src[0], set())
        self._release(src, (ra,), (ta,))
        rd = self.alloc(prefer=prefer)
        self.body.append(isa.SFPABS(src=ra, dest=rd, mode=1 if dt.is_float else 0) if op is Ops.ABS else isa.SFPNOT(src=ra, dest=rd))
        return rd

      case Ops.AND | Ops.OR:
        a, b = src
        ra, ta = self.ensure(a, set())
        rb, tb = self.ensure(b, {ra})
        self._release((a, b), (ra, rb), (ta, tb))
        rd = self.alloc(prefer=prefer)
        self.body.append(isa.SFPAND(imm=ra, src=rb, dest=rd, mode=1) if op is Ops.AND else isa.SFPOR(imm=ra, src=rb, dest=rd, mode=1))
        return rd

      case Ops.XOR:
        a, b = src
        ra, ta = self.ensure(a, set())
        rb, tb = self.ensure(b, {ra})
        vd, _ = self._writable_copy(a, ra, ta, {rb}, count=(2 if a is b else 1), prefer=prefer)
        self.body.append(isa.SFPXOR(src=rb, dest=vd))
        self._release((a, b), (ra, rb), (False if vd == ra else ta, tb), keep={vd})
        return vd

      case Ops.SHL | Ops.SHR:
        a, b = src
        if b.op is Ops.CONST:
          amt = int(b.arg)
          imm = (amt if op is Ops.SHL else -amt) & 0xFFF
          mod = 7 if (op is Ops.SHR and dt.is_signed) else 5
          ra, ta = self.ensure(a, set())
          self._release((a, b), (ra,), (ta,))
          rd = self.alloc(prefer=prefer)
          self.body.append(isa.SFPSHFT(imm=imm, src=ra, dest=rd, mode=mod))
          return rd
        ra, ta = self.ensure(a, set())
        rb, tb = self.ensure(b, {ra})
        vd, _ = self._writable_copy(a, ra, ta, {rb}, count=(2 if a is b else 1), prefer=prefer)
        if op is Ops.SHL:
          self.body.append(isa.SFPSHFT(src=rb, dest=vd))
        else:
          neg_b = self.alloc({vd, rb})
          self.body.append(isa.SFPMOV(src=rb, dest=neg_b))
          self.body.append(isa.SFPIADD(src=isa.LReg.ZERO, dest=neg_b, mode=6))
          self.body.append(isa.SFPSHFT(src=neg_b, dest=vd, mode=2 if dt.is_signed else 0))
          self.free_reg(neg_b)
        self._release((a, b), (ra, rb), (False if vd == ra else ta, tb), keep={vd})
        return vd

      case Ops.CAST:
        x = src[0]
        rx, tx = self.ensure(x, set())
        if x.dtype == dt:
          if tx and rx not in self.pinned_ro:
            self.drop_use(x)
            return rx
          rd = self.alloc({rx}, prefer=prefer)
          self.body.append(isa.SFPMOV(src=rx, dest=rd))
          self.drop_use(x)
          return rd
        self._release(src, (rx,), (tx,))
        rd = self.alloc(prefer=prefer)
        match (x.dtype, dt):
          case (sx, _) if sx.is_int and dt.is_float:
            self.body.append(isa.SFPCAST(src=rx, dest=rd, mode=3))
            self.body.append(isa.SFPCAST(src=rd, dest=rd))
          case (dtypes.fp32, dtypes.bf16):
            self.body.append(isa.SFP_STOCH_RND(b=isa.LReg.ZERO, src=rx, dest=rd, mode=1))
          case (dtypes.bf16, dtypes.fp32):
            self.body.append(isa.SFPMOV(src=rx, dest=rd))
          case (sx, _) if sx.is_float and dt.is_int:
            self.body.append(isa.SFP_STOCH_RND(rounding=2, b=isa.LReg.ZERO, src=rx, dest=rd, mode=7))
            self.body.append(isa.SFPCAST(src=rd, dest=rd, mode=3))
          case _:
            raise SfpuCompileError(f"unsupported SFPU cast {x.dtype} -> {dt}")
        return rd

      case Ops.SFPU:
        assert isinstance(arg, SfpuPrim)
        match arg.op:
          case "ARECIP" | "EXEXP" | "EXMAN" | "DIVP2" | "CAST_SM2F" | "CAST_TC2SM":
            rx, tx = self.ensure(src[0], set())
            self._release(src, (rx,), (tx,))
            rd = self.alloc(prefer=prefer)
            match arg.op:
              case "ARECIP": word = isa.SFPARECIP(src=rx, dest=rd, mode=arg.mod)
              case "EXEXP": word = isa.SFPEXEXP(src=rx, dest=rd, mode=arg.mod)
              case "EXMAN": word = isa.SFPEXMAN(src=rx, dest=rd, mode=arg.mod)
              case "DIVP2": word = isa.SFPDIVP2(imm=arg.imm & 0xFF, src=rx, dest=rd, mode=arg.mod)
              case "CAST_SM2F" | "CAST_TC2SM": word = isa.SFPCAST(src=rx, dest=rd, mode=0 if arg.op == "CAST_SM2F" else 3)
            self.body.append(word)
            return rd
          case "SETEXP":
            if arg.mod & 1:
              rc, tc = self.ensure(src[0], set())
              self._release(src, (rc,), (tc,))
              rd = self.alloc(prefer=prefer)
              self.body.append(isa.SFPSETEXP(imm=arg.imm & 0xFF, src=rc, dest=rd, mode=1))
              return rd
            re, te = self.ensure(src[0], set())
            rm, tm = self.ensure(src[1], {re})
            vd, _ = self._writable_copy(src[0], re, te, {rm}, count=(2 if src[0] is src[1] else 1), prefer=prefer)
            self.body.append(isa.SFPSETEXP(src=rm, dest=vd, mode=arg.mod))
            self._release(src, (re, rm), (False if vd == re else te, tm), keep={vd})
            return vd
          case "SHFT_VAR":
            rv, tv = self.ensure(src[0], set())
            rs, ts = self.ensure(src[1], {rv})
            vd, _ = self._writable_copy(src[0], rv, tv, {rs}, count=(2 if src[0] is src[1] else 1), prefer=prefer)
            self.body.append(isa.SFPSHFT(src=rs, dest=vd, mode=arg.mod))
            self._release(src, (rv, rs), (False if vd == rv else tv, ts), keep={vd})
            return vd
          case "TRANSP":
            raise SfpuCompileError("TRANSP needs four explicit register inputs and a result selector")
          case _:
            raise SfpuCompileError(f"unknown SfpuPrim {arg.op!r}")

      case _:
        raise SfpuCompileError(f"unsupported SFPU UOp {op.name}")

  def _tile_has_pending_readers(self, tile: int, except_u: UOp | None = None) -> bool:
    for inp, t in self.dst_inputs.items():
      if t != tile: continue
      rem = self.uses.get(inp, 0) - (1 if inp is except_u else 0)
      if rem > 0: return True
    return False

  def _emit_store(self, u: UOp, r: int, tile: int):
    if r >= 12:
      tmp = self.alloc({r})
      self.body.append(isa.SFPMOV(src=r, dest=tmp))
      self.body.append(isa.SFPSTORE(lreg=tmp, format=_sfpu_fmt(u.dtype), addr=tile * DST_TILE_ROWS))
      self.free_reg(tmp)
    else:
      self.body.append(isa.SFPSTORE(lreg=r, format=_sfpu_fmt(u.dtype), addr=tile * DST_TILE_ROWS))
    self._stored.add(u)
    self._written_tiles.add(tile)

  def _store_if_ready(self, u: UOp, *, is_final: bool = False):
    if u not in self.outputs or u in self._stored: return
    if not is_final and self.uses.get(u, 0) > (1 + (1 if u in self.reg_outputs else 0)): return
    tile = self.outputs[u]
    if not is_final and self._tile_has_pending_readers(tile, except_u=u): return
    r, is_t = self.ensure(u, set())
    self._emit_store(u, r, tile)
    if is_t: self.free_reg(r)
    self.drop_use(u)

  def _place_reg_outputs(self):
    if not self.reg_outputs: return
    loc: dict[UOp, int] = {}
    prot: set[int] = set()
    for u in self.reg_outputs:
      r, _ = self.ensure(u, prot, need_writable=True)
      if r >= 8:
        dst_r = self.alloc(prot | {r}, prefer=self.reg_outputs[u])
        self.body.append(isa.SFPMOV(src=r, dest=dst_r))
        r = dst_r
      loc[u] = r
      prot.add(r)

    # Emit moves into free/unoccupied target registers first; break remaining cycles with 1-insn SFPSWAP(mod=0).
    pending = {u: tgt for u, tgt in self.reg_outputs.items() if loc[u] != tgt}
    while pending:
      occupied = set(loc.values())
      ready = next(((u, tgt) for u, tgt in pending.items() if tgt not in occupied), None)
      if ready is not None:
        u, tgt = ready
        self.body.append(isa.SFPMOV(src=loc[u], dest=tgt))
        loc[u] = tgt
        pending.pop(u)
      else:
        u, tgt = next(iter(pending.items()))
        src_r = loc[u]
        # Swap src_r <-> tgt in place (updates any other output currently sitting in tgt!).
        self.body.append(isa.SFPSWAP(src=src_r, dest=tgt))
        for k, v in list(loc.items()):
          if v == src_r: loc[k] = tgt
          elif v == tgt: loc[k] = src_r
        pending = {k: t for k, t in self.reg_outputs.items() if loc[k] != t}
    self.peak_regs = max(self.peak_regs, max(self.reg_outputs.values()) + 1)

  def run(self) -> tuple[list[int], int]:
    for u in self.nodes:
      if u in self.fused_cmps: continue
      rd = self.emit_uop(u)
      if self.uses.get(u, 0) > 0:
        self.bind(u, rd)
        self._store_if_ready(u)
      else:
        self.free_reg(rd)

    # Flush remaining Dst outputs safely (handles parallel copy/swap cycles without overwriting unread Dst inputs!).
    pending = {u: t for u, t in self.outputs.items() if u not in self._stored}
    saved: dict[UOp, int] = {}
    while pending:
      unread = {self.dst_inputs[u] for u in pending if u in self.dst_inputs and u not in self.reg and u not in saved}
      ready = next((u for u, t in pending.items() if t not in unread), None)
      if ready is None:
        u = next(u for u in pending if u in self.dst_inputs and u not in self.reg and u not in saved)
        saved[u], _ = self.ensure(u, set(saved.values()))
        continue
      tile = pending.pop(ready)
      r, is_t = self.ensure(ready, set(saved.values()))
      self._emit_store(ready, r, tile)
      saved.pop(ready, None)
      if is_t: self.free_reg(r)
      self.drop_use(ready)

    self._place_reg_outputs()

    # Attach addr_mod (e.g. dst+=2) to the final SFPSTORE or SFPLOAD in multi-footprint sweeps.
    if self.addr_mode and self.footprints > 1:
      for i in range(len(self.body) - 1, -1, -1):
        if (self.body[i] >> 24) in (0x72, 0x70):
          inst = isa.decode(self.body[i])
          assert inst is not None
          self.body[i] = inst.replace(addr_mod=self.addr_mode)
          break
    return self.body, self.peak_regs

def _try_lower_pass(
  nodes: Sequence[UOp],
  dst_inputs: dict[UOp, int],
  outputs: dict[UOp, int],
  *,
  reg_inputs: dict[UOp, int] | None = None,
  reg_outputs: dict[UOp, int] | None = None,
  max_regs: int = 8,
  preserve_l11: bool = False,
  addr_mode: int = 0,
  footprints: int = 32,
) -> tuple[list[int], list[int], list[int], dict[UOp, int], bool, int]:
  rin = dict(reg_inputs or {})
  rout = dict(reg_outputs or {})
  live_in_regs = set(rin.values())
  can_save_l0 = (0 not in live_in_regs) or any(r not in live_in_regs for r in range(1, max_regs))
  const_regs, l11_used = _assign_const_regs(
    nodes,
    preserve_l11=preserve_l11,
    allow_non_default_cfg=can_save_l0,
    min_uses_for_cfg=(2 if footprints == 1 else 1),
  )
  low = _PassLowerer(
    nodes, dst_inputs, outputs, const_regs,
    reg_inputs=rin, reg_outputs=rout, max_regs=max_regs, addr_mode=addr_mode, footprints=footprints,
  )
  raw_body, peak = low.run()
  prologue = _emit_prologue_consts(const_regs, live_in_regs, max_regs)
  body = fix_sfpu_hazards(raw_body, is_loop=(footprints > 1))
  _verify_dst_store_load_order(body, retryable=True)
  return prologue, body, [], const_regs, l11_used, peak

# ---------------------------------------------------------------------------------------------------------------------
# Pass B: Sethi-Ullman ordering & Dst-intermediate pass splitting
# ---------------------------------------------------------------------------------------------------------------------

def _ershov_order(roots: Sequence[UOp], stop: set[UOp]) -> list[UOp]:
  rank: dict[UOp, int] = {}
  all_nodes: list[UOp] = []
  seen: set[UOp] = set()

  def collect(u: UOp):
    if u in seen or u in stop or u.op is Ops.CONST: return
    seen.add(u)
    for s in u.src: collect(s)
    all_nodes.append(u)

  for r in roots: collect(r)
  for u in all_nodes:
    child_ranks = sorted((rank.get(s, 1) for s in u.src if s not in stop and s.op is not Ops.CONST), reverse=True)
    rank[u] = 1 if not child_ranks else max(cr + i for i, cr in enumerate(child_ranks))

  order: list[UOp] = []
  emitted: set[UOp] = set()

  def visit(u: UOp):
    if u in emitted or u in stop or u.op is Ops.CONST: return
    emitted.add(u)
    for s in sorted(u.src, key=lambda x: -rank.get(x, 0)): visit(s)
    order.append(u)

  for r in roots: visit(r)
  return order

def partition_sfpu(
  roots: Sequence[UOp],
  dst_inputs: dict[UOp, int],
  *,
  reg_inputs: dict[UOp, int] | None = None,
  reg_outputs: dict[UOp, int] | None = None,
  max_regs: int = 8,
  dst_budget: int = 8,
  output_tiles: dict[UOp, int] | Sequence[int | None] | None = None,
  preserve_l11: bool = False,
  addr_mode: int = 0,
  footprints: int | None = None,
) -> CompiledSfpu:
  roots_t = tuple(roots)
  rin = dict(reg_inputs or {})
  rout = dict(reg_outputs or {})
  if not (1 <= max_regs <= 8) or not (1 <= dst_budget <= 8):
    raise ValueError("FP32 SFPU passes require 1..8 writable registers and 1..8 Dst tiles")
  for label, rmap in (("reg_inputs", rin), ("reg_outputs", rout)):
    seen_r: dict[int, UOp] = {}
    for u, r in rmap.items():
      if not (0 <= r < max_regs): raise ValueError(f"{label} L{r} outside max_regs={max_regs}")
      if r in seen_r and seen_r[r] is not u: raise ValueError(f"distinct {label} requested the same register L{r}")
      seen_r[r] = u

  # Normalize requested Dst output tiles per root position (roots in reg_outputs only do not require a Dst tile!).
  if output_tiles is None:
    req_per_root: list[int | None] = [None] * len(roots_t)
    explicit_dst_roots = {r for r in roots_t if r not in rout}
  elif isinstance(output_tiles, dict):
    req_per_root = [output_tiles.get(r) for r in roots_t]
    explicit_dst_roots = {r for r in roots_t if r in output_tiles or r not in rout}
  else:
    if len(output_tiles) != len(roots_t):
      raise ValueError(f"output_tiles length {len(output_tiles)} != roots length {len(roots_t)}")
    req_per_root = list(output_tiles)
    explicit_dst_roots = {r for r, t in zip(roots_t, req_per_root) if t is not None or r not in rout}

  requested = {t: r for r, t in zip(roots_t, req_per_root) if t is not None}
  for t in (*dst_inputs.values(), *requested):
    if not (0 <= t < dst_budget): raise ValueError(f"Dst tile {t} outside budget {dst_budget}")
  if any(t is not None and requested[t] is not r for r, t in zip(roots_t, req_per_root)):
    raise ValueError("distinct SFPU results requested the same Dst tile")

  if footprints is None:
    footprints = 32 if (dst_inputs or explicit_dst_roots) else 1

  preferred_out: dict[UOp, int] = {}
  for r, t in zip(roots_t, req_per_root):
    if t is not None and r not in preferred_out: preferred_out[r] = t

  live_dst: dict[UOp, int] = dict(dst_inputs)
  stop_leaves = set(dst_inputs) | set(rin)
  remaining = _ershov_order(roots_t, stop_leaves)
  req_vals = [t for t in req_per_root if t is not None]
  max_dst_used = max(list(live_dst.values()) + req_vals + [0]) + 1 if (live_dst or req_vals) else 0
  compiled_passes: list[CompiledSfpuPass] = []

  def boundary_outputs(cand: Sequence[UOp], rest: Sequence[UOp]) -> tuple[list[UOp], dict[UOp, int]]:
    cand_set = set(cand)
    needed_later = {s for n in rest for s in n.src if s in cand_set}
    pass_reg_outs = {u: rout[u] for u in cand if u in rout and not rest} if not rest else {}
    dst_bouts = [u for u in cand if u in explicit_dst_roots or u in needed_later or (u in rout and u not in pass_reg_outs)]
    return dst_bouts, pass_reg_outs

  def dst_still_needed(rest: Sequence[UOp], extra_keep: set[UOp]) -> set[int]:
    needed = set(extra_keep) | {s for n in rest for s in n.src if s in live_dst}
    return {live_dst[u] for u in needed if u in live_dst}

  def assign_output_tiles(
    bouts: Sequence[UOp], rest: Sequence[UOp], pass_inputs: dict[UOp, int], *, allow_inplace: bool,
  ) -> dict[UOp, int] | None:
    keep = {r for r in explicit_dst_roots if r in live_dst and r not in bouts}
    used = dst_still_needed(rest, keep)
    if not allow_inplace: used |= set(pass_inputs.values())
    assigned: dict[UOp, int] = {}
    for u in bouts:
      if (t := preferred_out.get(u)) is not None and t not in used:
        assigned[u] = t
        used.add(t)
    for u in bouts:
      if u in assigned: continue
      if (free_t := next((t for t in range(dst_budget) if t not in used), None)) is None: return None
      assigned[u] = free_t
      used.add(free_t)
    return assigned

  placed_reg_outs: set[UOp] = set()
  while remaining:
    best = None
    fail_streak = 0
    for k in itertools.chain((len(remaining),), range(1, len(remaining))):
      cand, rest = remaining[:k], remaining[k:]
      bouts, pass_reg_outs = boundary_outputs(cand, rest)
      used_inputs = {s: live_dst[s] for n in cand for s in n.src if s in live_dst}
      # Every reg_input stays bound in every pass: a pinned LReg (e.g. a loop carry read only by a later pass) must
      # not be used as scratch or as the SFPCONFIG staging register by an earlier pass.
      used_rin = dict(rin)
      # Try in-place Dst reuse first (zero scratch tiles for single/multi-tile accumulators!), fallback to scratch.
      modes = (True, False) if (not rest or len(bouts) == 1) else (False,)
      lowered = None
      for allow_ip in modes:
        out_map = assign_output_tiles(bouts, rest, used_inputs, allow_inplace=allow_ip)
        if out_map is None: continue
        try:
          res = _try_lower_pass(
            cand, used_inputs, out_map, reg_inputs=used_rin, reg_outputs=pass_reg_outs,
            max_regs=max_regs, preserve_l11=preserve_l11, addr_mode=addr_mode, footprints=footprints,
          )
          lowered = (out_map, res)
          break
        except (_OutOfRegs, _DstAliasConflict):
          continue
      if lowered is None:
        if rest:
          fail_streak += 1
          if fail_streak >= 4: break
        continue
      out_map, res = lowered
      fail_streak = 0
      score = (k - 4 * len(bouts), -len(bouts), k)
      if best is None or score > best[0]:
        best = score, rest, used_inputs, used_rin, out_map, pass_reg_outs, res
      if not rest: break
    if best is None:
      raise SfpuCompileError(f"cannot schedule {remaining[0].op.name} within {max_regs} LRegs and {dst_budget} Dst tiles")
    _, rest, used_inputs, used_rin, out_map, pass_reg_outs, (pro, body, epi, _, l11_used, peak) = best
    if out_map: max_dst_used = max(max_dst_used, max(out_map.values()) + 1)
    ro_regs = {r for r in used_rin.values() if r not in pass_reg_outs.values()} if footprints > 1 else set()
    _verify_compiled_pass(pro, body, epi, footprints=footprints, pinned_ro=ro_regs)
    compiled_passes.append(CompiledSfpuPass(
      tuple(pro), tuple(body), tuple(epi), used_inputs, out_map, l11_used, peak,
      reg_inputs=used_rin, reg_outputs=pass_reg_outs, footprints=footprints,
    ))
    placed_reg_outs |= set(pass_reg_outs)
    written_tiles = set(out_map.values())
    live_dst = {u: t for u, t in live_dst.items() if t not in written_tiles}
    live_dst.update(out_map)
    remaining = rest

  # Materialize CONST roots, move mismatched Dst outputs, and duplicate CSE-collapsed roots.
  final_root_tiles: list[int] = []
  homes = dict(preferred_out)
  used_final = set(requested)
  for r in roots_t:
    if r in explicit_dst_roots and r not in homes and r in live_dst and live_dst[r] not in used_final:
      homes[r] = live_dst[r]
      used_final.add(homes[r])
  pending_copies: list[tuple[UOp, int]] = []
  for r, req_t in zip(roots_t, req_per_root):
    if r not in explicit_dst_roots: continue
    if r not in homes:
      if (tile := next((t for t in range(dst_budget) if t not in used_final), None)) is None:
        raise SfpuCompileError(f"exceeded Dst tile budget ({dst_budget} tiles) for outputs")
      homes[r] = tile
      used_final.add(tile)
    tile = homes[r] if req_t is None else req_t
    final_root_tiles.append(tile)
    if live_dst.get(r) != tile and (r, tile) not in pending_copies:
      pending_copies.append((r, tile))

  # LRegs still holding live values (unconsumed reg_inputs, placed reg_outputs): cleanup passes must not clobber them.
  placed_regs = {rout[u] for u in placed_reg_outs}
  live_regs = {**{u: r for u, r in rin.items() if r not in placed_regs}, **{u: rout[u] for u in placed_reg_outs}}

  while pending_copies:
    batch: dict[UOp, int] = {}
    rest_copies: list[tuple[UOp, int]] = []
    for src_u, dst_t in pending_copies:
      if src_u not in batch: batch[src_u] = dst_t
      else: rest_copies.append((src_u, dst_t))
    in_map = {u: live_dst[u] for u in batch if u in live_dst}
    r_in = {**live_regs, **{u: rin[u] for u in batch if u in rin}}
    try:
      pro, body, epi, _, l11_used, peak = _try_lower_pass(
        (), in_map, batch, reg_inputs=r_in, max_regs=max_regs,
        preserve_l11=preserve_l11, addr_mode=addr_mode, footprints=footprints,
      )
    except _OutOfRegs as exc:
      raise SfpuCompileError(f"parallel output copies exceed {max_regs} LRegs") from exc
    _verify_compiled_pass(pro, body, epi, footprints=footprints)
    compiled_passes.append(CompiledSfpuPass(
      tuple(pro), tuple(body), tuple(epi), in_map, batch, l11_used, peak,
      reg_inputs=r_in, footprints=footprints,
    ))
    live_dst.update(batch)
    max_dst_used = max(max_dst_used, max(batch.values()) + 1)
    pending_copies = rest_copies

  # Materialize any reg_outputs that weren't placed yet (e.g. CONST init, reg-to-reg move, or spilled Dst -> LReg).
  missing_routs = {u: r for u, r in rout.items() if u not in placed_reg_outs}
  if missing_routs:
    in_map = {u: live_dst[u] for u in missing_routs if u in live_dst}
    r_in = {u: rin[u] for u in missing_routs if u in rin}
    r_in = {**{u: r for u, r in live_regs.items() if r not in missing_routs.values()}, **r_in}
    pass_fp = 1 if not in_map else footprints
    pro, body, epi, _, l11_used, peak = _try_lower_pass(
      (), in_map, {}, reg_inputs=r_in, reg_outputs=missing_routs,
      max_regs=max_regs, preserve_l11=preserve_l11, addr_mode=addr_mode, footprints=pass_fp,
    )
    _verify_compiled_pass(pro, body, epi, footprints=pass_fp)
    compiled_passes.append(CompiledSfpuPass(
      tuple(pro), tuple(body), tuple(epi), in_map, {}, l11_used, peak,
      reg_inputs=r_in, reg_outputs=missing_routs, footprints=pass_fp,
    ))

  if final_root_tiles: max_dst_used = max(max_dst_used, max(final_root_tiles) + 1)
  dst_roots = [r for r in roots_t if r in explicit_dst_roots]
  final_output_tiles = {r: t for r, t in zip(dst_roots, final_root_tiles)}
  return CompiledSfpu(tuple(compiled_passes), max_dst_used, final_output_tiles, tuple(final_root_tiles))

def compile_sfpu(
  roots: UOp | Sequence[UOp],
  dst_inputs: dict[UOp, int] | None = None,
  *,
  reg_inputs: dict[UOp, int] | None = None,
  reg_outputs: dict[UOp, int] | None = None,
  precision: DType = dtypes.fp32,
  max_regs: int = 8,
  dst_budget: int = 8,
  output_tiles: dict[UOp, int] | Sequence[int | None] | None = None,
  preserve_l11: bool = False,
  addr_mode: int = 0,
  footprints: int | None = None,
) -> CompiledSfpu:
  roots_list = [roots] if isinstance(roots, UOp) else list(roots)
  din = dict(dst_inputs or {})
  rin = dict(reg_inputs or {})
  rout = dict(reg_outputs or {})

  # Hide resident Dst and LReg inputs behind opaque leaves during Pass A so FMA/decomp cannot reach across stages.
  leaves = {
    **{u: sfpu_prim("DST_INPUT", u.dtype, imm=i, space=Space.DST) for i, u in enumerate(din)},
    **{u: sfpu_prim("REG_INPUT", u.dtype, imm=i, space=Space.LREG) for i, u in enumerate(rin)},
  }
  sink_in = UOp.sink(*roots_list).substitute(leaves)
  lowered_roots = lower_sfpu_uops(sink_in, precision=precision).substitute({leaf: u for u, leaf in leaves.items()}).src
  root_remap = dict(zip(roots_list, lowered_roots))

  out_tiles_arg: dict[UOp, int] | list[int | None] | None = None
  if output_tiles is not None:
    if isinstance(output_tiles, dict):
      out_tiles_arg = {root_remap.get(r, r): t for r, t in output_tiles.items()}
    else:
      out_tiles_arg = list(output_tiles)
  reg_outs_mapped = {root_remap.get(r, r): reg for r, reg in rout.items()}

  return partition_sfpu(
    lowered_roots, din,
    reg_inputs=rin, reg_outputs=reg_outs_mapped,
    max_regs=max_regs, dst_budget=dst_budget,
    output_tiles=out_tiles_arg, preserve_l11=preserve_l11,
    addr_mode=addr_mode, footprints=footprints,
  )

def compile_sfpu_loop(
  loop_or_get: UOp,
  dst_inputs: dict[UOp, int] | None = None,
  *,
  reg_inputs: dict[UOp, int] | None = None,
  dst_carries: dict[int, int] | None = None,
  reg_carries: dict[int, int] | None = None,
  precision: DType = dtypes.fp32,
  max_regs: int = 8,
  dst_budget: int = 8,
  preserve_l11: bool = False,
  addr_mode: int = 0,
) -> CompiledSfpuLoop:
  """Compile a Layer 1 Ops.LOOP (or Ops.REDUCE) with Space.DST / Space.LREG carried accumulators.

  Returns init passes (run once before the outer loop) and body passes (run each outer iteration with
  carried Dst slots updated in-place and carried LReg slots pinned across all footprints and iterations).
  """
  orig = loop_or_get
  u = lower_reduce_to_loop(loop_or_get) if loop_or_get.op is Ops.REDUCE else loop_or_get
  lp = u.src[0] if u.op is Ops.GET else u
  if lp.op is not Ops.LOOP:
    raise SfpuCompileError(f"compile_sfpu_loop expects LOOP, GET(LOOP), or REDUCE, got {loop_or_get.op.name}")

  din = dict(dst_inputs or {})
  rin = dict(reg_inputs or {})
  carries = lp.src[1::2]
  nexts = lp.src[2::2]

  used_dst = set(din.values())
  used_reg = set(rin.values())
  carry_dst: dict[int, int] = {}
  carry_reg: dict[int, int] = {}
  for idx, c in enumerate(carries):
    if c.space is Space.DST:
      slot = dst_carries[idx] if (dst_carries and idx in dst_carries) else next(
        (t for t in range(dst_budget) if t not in used_dst), None
      )
      if slot is None: raise SfpuCompileError(f"exceeded Dst budget ({dst_budget}) pinning loop carry {idx}")
      carry_dst[idx] = slot
      used_dst.add(slot)
    elif c.space is Space.LREG:
      reg = reg_carries[idx] if (reg_carries and idx in reg_carries) else next(
        (r for r in range(max_regs) if r not in used_reg), None
      )
      if reg is None: raise SfpuCompileError(f"exceeded LReg budget ({max_regs}) pinning loop carry {idx}")
      carry_reg[idx] = reg
      used_reg.add(reg)
    else:
      raise SfpuCompileError(f"SFPU loop carry {idx} must be DST or LREG, got {c.space}")

  # Compile init passes (run once before outer loop): 1-shot LReg inits + 32-footprint Dst inits.
  init_passes: list[CompiledSfpuPass] = []
  max_dst_used = max(used_dst) + 1 if used_dst else 0
  if carry_reg:
    lreg_inits = [carries[i].src[0] for i in carry_reg]
    lreg_init_out = {carries[i].src[0]: r for i, r in carry_reg.items()}
    ci_reg = compile_sfpu(
      lreg_inits, reg_inputs=rin, reg_outputs=lreg_init_out,
      precision=precision, max_regs=max_regs, dst_budget=dst_budget,
      preserve_l11=preserve_l11, footprints=1,
    )
    init_passes.extend(ci_reg.passes)
  if carry_dst:
    dst_inits = [carries[i].src[0] for i in carry_dst]
    dst_init_tiles = [carry_dst[i] for i in carry_dst]
    ci_dst = compile_sfpu(
      dst_inits, {k: v for k, v in din.items() if any(k in init.toposort() for init in dst_inits)},
      reg_inputs=rin, output_tiles=dst_init_tiles,
      precision=precision, max_regs=max_regs, dst_budget=dst_budget,
      preserve_l11=preserve_l11, addr_mode=addr_mode, footprints=32,
    )
    init_passes.extend(ci_dst.passes)
    max_dst_used = max(max_dst_used, ci_dst.dst_tiles)

  # Compile body passes: each carry input & next output are pinned to the same Dst slot / LReg!
  body_din = {**din, **{carries[i]: t for i, t in carry_dst.items()}}
  body_rin = {**rin, **{carries[i]: r for i, r in carry_reg.items()}}
  body_out_tiles = {nexts[i]: t for i, t in carry_dst.items()}
  body_reg_outs = {nexts[i]: r for i, r in carry_reg.items()}
  cb = compile_sfpu(
    nexts, body_din,
    reg_inputs=body_rin, reg_outputs=body_reg_outs,
    output_tiles=(body_out_tiles or None),
    precision=precision, max_regs=max_regs, dst_budget=dst_budget,
    preserve_l11=preserve_l11, addr_mode=addr_mode,
  )
  max_dst_used = max(max_dst_used, cb.dst_tiles)

  # Map the caller's post-loop value(s) to their pinned homes.
  if orig.op is Ops.REDUCE:
    out_dst_carries = {orig: carry_dst[0]} if 0 in carry_dst else {}
    out_reg_carries = {orig: carry_reg[0]} if 0 in carry_reg else {}
  else:
    out_dst_carries = {UOp(Ops.GET, carries[i].dtype, (lp,), i): t for i, t in carry_dst.items()}
    out_reg_carries = {UOp(Ops.GET, carries[i].dtype, (lp,), i): r for i, r in carry_reg.items()}

  return CompiledSfpuLoop(lp, tuple(init_passes), cb.passes, out_dst_carries, out_reg_carries, max_dst_used)
