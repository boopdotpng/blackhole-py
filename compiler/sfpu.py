"""Blackhole SFPU compiler: UOp decomposition, Dst-intermediate pass splitting, L0..L7/L11..L14 allocation, and hazards.

Pipeline (Layer 1 Space.DST UOps -> verified Blackhole SFPU Tensix instruction streams):
  Pass A  lower_sfpu_uops()   Pure UOp PatternMatcher + graph_rewrite (EXP2, RECIP, RSQRT, SQRT, LOG2, SIN, MULACC).
  Pass B  partition_sfpu()    Constant tiering (L8..L15 / L11..L14) + exact-budget Dst-intermediate pass splitting.
  Pass C  compile_sfpu_pass() Per-pass L0..L7 register assignment, predication (WHERE/SFPGT/SFPLE/SFPENCC), isa emit.
  Pass D  fix_sfpu_hazards()  Silicon-measured hazard model (boop-docs/probes/model.py) + hard register/backdoor checks.

Late compression passes (2x even/odd interleaving, SFPLOADMACRO, REPLAY, MOP) intentionally live in Layer 3.
"""
from __future__ import annotations
import itertools, math, struct
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Sequence
from hw import isa
from .ops import pm_simplify
from .uop import DType, GroupOp, Ops, PatternMatcher, Space, UOp, UPat, dtypes, graph_rewrite

# ---------------------------------------------------------------------------------------------------------------------
# Silicon-measured SFPU timing & hazard model (ported from boop-docs/probes/model.py, Blackhole A0 card 1)
# ---------------------------------------------------------------------------------------------------------------------

SFPU_OPS: dict[int, str] = {
  0x7D: "ABS", 0x85: "ADD", 0x75: "ADDI", 0x7E: "AND", 0x99: "ARECIP", 0x90: "CAST", 0x8B: "COMPC",
  0x91: "CONFIG", 0x76: "DIVP2", 0x8A: "ENCC", 0x77: "EXEXP", 0x78: "EXMAN", 0x97: "GT", 0x79: "IADD",
  0x96: "LE", 0x70: "LOAD", 0x71: "LOADI", 0x93: "LOADMACRO", 0x73: "LUT", 0x95: "LUTFP32", 0x81: "LZ",
  0x84: "MAD", 0x7C: "MOV", 0x86: "MUL", 0x98: "MUL24", 0x74: "MULI", 0x8F: "NOP", 0x80: "NOT", 0x7F: "OR",
  0x88: "POPC", 0x87: "PUSHC", 0x7B: "SETCC", 0x82: "SETEXP", 0x83: "SETMAN", 0x89: "SETSGN", 0x7A: "SHFT",
  0x94: "SHFT2", 0x72: "STORE", 0x92: "SWAP", 0x8C: "TRANSP", 0x8D: "XOR", 0x8E: "STOCHRND",
}
MAD_COLUMN = frozenset({"MAD", "MUL", "ADD", "ADDI", "MULI", "MUL24", "LUT", "LUTFP32"})
SUBUNIT: dict[str, str] = {
  **{op: "simple" for op in (
    "ABS", "AND", "ARECIP", "CAST", "COMPC", "CONFIG", "DIVP2", "ENCC", "EXEXP", "EXMAN", "GT", "IADD",
    "LE", "LZ", "MOV", "NOT", "OR", "POPC", "PUSHC", "SETCC", "SETEXP", "SETMAN", "SETSGN", "SHFT",
    "SWAP", "TRANSP", "XOR",
  )},
  **{op: "mad" for op in MAD_COLUMN},
  "SHFT2": "round", "STOCHRND": "round", "STORE": "store",
  "LOAD": "load", "LOADI": "load", "LOADMACRO": "load", "NOP": "load",
}
ALL_LREGS = frozenset(range(16))
LREGS = frozenset(range(8))
DST_TILE_ROWS = 64  # FP32 Dst tile stride (64 rows x 16 cols = 1024 elements)


@dataclass(frozen=True)
class SfpuInsn:
  op: str
  reads: frozenset[int]   # LRegs actually read at issue
  writes: frozenset[int]  # LRegs written
  seen_r: frozenset[int]  # what hardware stall logic believes it reads
  seen_w: frozenset[int]  # what hardware stall logic believes a 2-cycle op writes
  lat: int                # 2 for MAD-column, 1 for everything else
  block: int              # 1 for SWAP / SHFT2 modes 2..4 (holds issue slot 1 extra cycle)
  unit: str               # load | simple | mad | round | store


def loadmacro_units(sequence: int) -> list[tuple[str, int, bool]]:
  """[(unit, delay, writes_l16)] scheduled by one SFPLOADMACRO for a Sequence word."""
  out: list[tuple[str, int, bool]] = []
  for n, unit in enumerate(("simple", "mad", "round", "store")):
    b = (sequence >> (8 * n)) & 0xFF
    if b & 7: out.append((unit, (b >> 3) & 7, bool(b & 0x40)))
  return out


@lru_cache(maxsize=8192)
def sfpu_decode(w: int) -> SfpuInsn | None:
  """SfpuInsn for an unrotated Tensix word, or None if it is not an SFPU instruction."""
  op = SFPU_OPS.get(w >> 24)
  if op is None: return None
  vd, vc, vb, va, mod = (w >> 4) & 15, (w >> 8) & 15, (w >> 12) & 15, (w >> 16) & 15, w & 15
  ld_vd, mod0 = (w >> 20) & 15, (w >> 16) & 15
  f = frozenset
  r: frozenset[int] = f()
  s: frozenset[int] = f()
  wr: frozenset[int] = f()
  seen_w: frozenset[int] | None = None
  lat = 2 if op in MAD_COLUMN else 1
  block = 0
  if op in ("MAD", "MUL", "ADD", "MUL24"):
    r = f({va, vb, vc}) | (f({7}) if mod & 12 else f())
    s = ALL_LREGS if mod & 4 else r
    wr = LREGS if mod & 8 else f({vd})
  elif op in ("ADDI", "MULI"):
    r = s = f({vd}) | (f({7}) if mod & 8 else f())
    wr = LREGS if mod & 8 else f({vd})
  elif op == "LUT":
    r = s = f({0, 1, 2, 3}) | (f({7}) if mod0 & 8 else f())
    wr = LREGS if mod0 & 8 else f({ld_vd})
  elif op == "LUTFP32":
    mirror = (w >> 16) & 15
    r, wr = f(range(7)), f({vd})
    s = ALL_LREGS if mirror & 8 else ALL_LREGS - {7}
    if mirror & 8: seen_w = ALL_LREGS
  elif op in ("MOV", "ABS", "NOT", "LZ", "EXEXP", "EXMAN", "CAST", "DIVP2"):
    r = s = f({vc})
    wr = f({vd})
  elif op == "IADD":
    r, s, wr = (f({vc}) if mod & 1 else f({vc, vd})), f({vc}), f({vd})
  elif op == "SHFT":
    r = f({vc}) if (mod & 5) == 5 else f({vd}) if mod & 1 else f({vc, vd})
    s, wr = (r if mod & 1 else f({vc})), f({vd})
  elif op in ("AND", "OR"):
    r, s, wr = f({vc, vb if mod & 1 else vd}), f({vc, vd}), f({vd})
  elif op == "XOR":
    r = s = f({vc, vd})
    wr = f({vd})
  elif op in ("SETEXP", "SETMAN", "SETSGN"):
    imm = mod & 1
    r, s, wr = (f({vc}) if imm else f({vc, vd})), (f({vc, vd}) if imm else f({vc})), f({vd})
  elif op == "ARECIP":
    r, s, wr = (f({vc, vb}) if mod == 1 else f({vc})), (f({vc, vd}) if mod == 1 else f({vc})), f({vd})
  elif op == "STOCHRND":
    r = f({vc}) | (f({vb}) if (mod & 7) in (4, 5) and not (mod & 8) else f())
    s, wr = f({vc}) | (f() if mod & 8 else f({vb})), f({vd})
  elif op == "SETCC":
    r = s = f({vc})
  elif op in ("GT", "LE"):
    r = s = f({vc, vd})
    wr = f({vd}) if mod & 8 else f()
  elif op == "SWAP":
    wr, block = f({vc, vd}), 1
    r = f() if mod == 0 else f({vc, vd})
  elif op == "SHFT2":
    if mod in (0, 1, 2): wr = f({0, 1, 2, 3})
    if mod == 0: r = s = f({1, 2, 3, vc})
    elif mod == 1: r = s = f({0, 1, 2, 3, vc})
    elif mod == 2: r, block = f({1, 2, 3, vc}), 1
    elif mod in (3, 4): r, wr, block = f({vc}), f({vd}), 1
    elif mod == 5: r, s, wr = f({vb, vc}), f({vc, vd}), f({vd})
    elif mod == 6: r, s, wr = f({vb}), f({vd}), f({vd})
  elif op == "TRANSP":
    r = s = wr = LREGS
  elif op == "STORE":
    r = s = f({ld_vd})
  elif op == "CONFIG":
    r = f() if mod & 1 else f({0})
    if 11 <= vd < 15: wr = f({vd})
  elif op in ("LOADI", "LOAD"):
    half = (op == "LOADI" and mod0 in (8, 10)) or (op == "LOAD" and mod0 in (14, 15))
    r, wr = (f({ld_vd}) if half else f()), f({ld_vd})
  elif op == "LOADMACRO":
    wr = f({(ld_vd & 3) | ((w & 1) << 2)})
  if seen_w is None: seen_w = wr if lat == 2 else f()
  return SfpuInsn(op, r, wr, s, seen_w, lat, block, SUBUNIT[op])


def sfpu_cost(prev, w: int, macros: dict[int, int] | None = None):
  """Issue one unrotated Tensix word. Returns (stall_cycles, hazard_or_None, new_state)."""
  t_prev, blocked, pending, sched = prev or (-10, -10, (), ())
  t = t_prev + 1
  i = sfpu_decode(w)
  if i is None or i.op == "NOP":
    return 0, None, (t, blocked, tuple(p for p in pending if p[0] > t), tuple(s for s in sched if s[1] >= t))
  t0 = t
  while t == blocked or any(ready > t and (seen & i.seen_r) for ready, seen, _ in pending):
    t += 1
  hazard = None
  for ready, _, writes in pending:
    if ready > t and (hit := writes & i.reads): hazard = ("stale", min(hit))
  if any(u == i.unit and c == t for u, c in sched): hazard = ("dropped", i.unit)
  live = tuple(p for p in pending if p[0] > t)
  if i.lat == 2 and i.writes: live += ((t + 2, i.seen_w, i.writes),)
  sched = tuple(s for s in sched if s[1] >= t)
  if i.op == "LOADMACRO" and macros:
    x = next(iter(i.writes))
    for unit, delay, l16 in loadmacro_units(macros.get((w >> 22) & 3, 0)):
      at = t + 1 + delay
      sched += ((unit, at),)
      if unit != "store":
        live += ((at + (2 if unit == "mad" else 1), frozenset(), frozenset({16 if l16 else x})),)
  return t - t0, hazard, (t, t + 1 if i.block else blocked, live, sched)


def sfpu_cycles(words: Sequence[int], repeat: int = 1, macros: dict[int, int] | None = None) -> int:
  """Cycles from first issue to last issue (inclusive) of `words` repeated `repeat` times."""
  if not words or repeat <= 0: return 0
  state, start = None, None
  for _ in range(repeat):
    for w in words:
      _, _, state = sfpu_cost(state, w, macros)
      if start is None: start = state[0]
  return state[0] - start + 1


def sfpu_slope(words: Sequence[int], macros: dict[int, int] | None = None) -> float:
  """Steady-state cycles per repetition of `words`."""
  if not words: return 0.0
  return (sfpu_cycles(words, 64, macros) - sfpu_cycles(words, 32, macros)) / 32.0


def sfpu_hazards(words: Sequence[int], macros: dict[int, int] | None = None) -> list[tuple[int, tuple]]:
  """[(index, hazard)] for every stale read or dropped instruction in a straight-line stream."""
  state, out = None, []
  for n, w in enumerate(words):
    _, hz, state = sfpu_cost(state, w, macros)
    if hz: out.append((n, hz))
  return out


def fix_sfpu_hazards(words: Sequence[int], macros: dict[int, int] | None = None, *, is_loop: bool = False) -> list[int]:
  """Insert minimal SFPNOPs for every undetected RAW hazard (and documented SFPCONFIG macro/backdoor gaps).
  When `is_loop=True`, also ensures no hazard occurs across the wrap-around from the last instruction to the first."""
  nop = isa.SFPNOP()
  out: list[int] = []
  state = None
  prev_cfg_macro_or_lane = False
  for w in words:
    # Documented requirement: SFPNOP after SFPCONFIG changing macro templates/sequences/misc or LaneConfig.
    if prev_cfg_macro_or_lane and (sfpu_decode(w) is not None and sfpu_decode(w).op != "NOP"):
      _, _, state = sfpu_cost(state, nop, macros)
      out.append(nop)
      prev_cfg_macro_or_lane = False
    _, hz, nxt = sfpu_cost(state, w, macros)
    if hz is not None and hz[0] == "stale":
      _, _, state = sfpu_cost(state, nop, macros)
      out.append(nop)
      _, hz2, nxt = sfpu_cost(state, w, macros)
      if hz2 is not None:
        raise SfpuCompileError(f"unresolvable SFPU hazard {hz2} on {isa.tensix_decode(w)}")
    elif hz is not None:
      raise SfpuCompileError(f"SFPU hazard {hz} on {isa.tensix_decode(w)}")
    state = nxt
    out.append(w)
    dec = sfpu_decode(w)
    if dec is not None and dec.op == "CONFIG":
      cfg_dest = (w >> 4) & 15
      prev_cfg_macro_or_lane = cfg_dest <= 8 or cfg_dest == 15
    else:
      prev_cfg_macro_or_lane = False
  if is_loop and out and sfpu_hazards(out + out, macros):
    out.append(nop)
    if sfpu_hazards(out + out, macros):
      raise SfpuCompileError(f"unresolvable SFPU loop wrap-around hazard: {sfpu_hazards(out + out, macros)}")
  return out


class SfpuCompileError(RuntimeError):
  pass


def verify_sfpu_words(
  words: Sequence[int],
  *,
  allow_backdoor: bool = False,
  macros: dict[int, int] | None = None,
  is_loop: bool = False,
) -> None:
  """Verify Blackhole SFPU hardware invariants on an unrotated Tensix word stream."""
  check_stream = list(words) + list(words) if (is_loop and words) else list(words)
  hz = sfpu_hazards(check_stream, macros)
  if hz:
    idx, err = hz[0]
    w = check_stream[idx]
    raise SfpuCompileError(f"SFPU hazard at word {idx} ({isa.tensix_decode(w)}): {err}")
  for idx, w in enumerate(words):
    info = sfpu_decode(w)
    if info is None: continue
    op = info.op
    # Hardware invariant: with DISABLE_BACKDOOR_LOAD=0 (default), VD >= 12 turns non-CONFIG/LOADMACRO ops
    # into silent template writes instead of executing!
    if not allow_backdoor and op not in ("CONFIG", "LOADMACRO", "NOP"):
      vd = ((w >> 20) & 15) if op in ("LOAD", "LOADI", "STORE", "LUT") else ((w >> 4) & 15)
      if vd >= 12:
        raise SfpuCompileError(f"word {idx} ({op}) has VD={vd} >= 12 (silent backdoor template write)")
    # Only L0..L7 (and L11..L14 via SFPCONFIG) are writable.
    # For SFPSWAP, hardware ignores writes to VC >= 8 (only VD must be < 8).
    if op == "SWAP":
      vd = (w >> 4) & 15
      if vd >= 8:
        raise SfpuCompileError(f"word {idx} (SWAP) writes illegal VD register L{vd}")
    elif op != "CONFIG":
      for r in info.writes:
        if r >= 8:
          raise SfpuCompileError(f"word {idx} ({op}) writes read-only/const register L{r}")


def _verify_dst_store_load_order(body: Sequence[int]) -> None:
  """Ensure no SFPSTORE overwrites a Dst tile that a later SFPLOAD in the same footprint still reads."""
  written_tiles: set[int] = set()
  for idx, w in enumerate(body):
    opcode = w >> 24
    if opcode == 0x72:  # SFPSTORE
      written_tiles.add((w & 0x3FF) // DST_TILE_ROWS)
    elif opcode == 0x70:  # SFPLOAD
      t = (w & 0x3FF) // DST_TILE_ROWS
      if t in written_tiles:
        raise SfpuCompileError(f"Dst tile {t} read by SFPLOAD at word {idx} after already overwritten by SFPSTORE")


def disasm_sfpu(words: Sequence[int]) -> str:
  """Human-readable disassembly of unrotated SFPU Tensix words."""
  lines = []
  for i, w in enumerate(words):
    dec = isa.tensix_decode(w)
    if dec is None: lines.append(f"{i:3d}: 0x{w:08x}")
    else:
      name, fields = dec
      fstr = ", ".join(f"{k}={v}" for k, v in fields.items() if v != 0)
      lines.append(f"{i:3d}: {name}({fstr})")
  return "\n".join(lines)


# ---------------------------------------------------------------------------------------------------------------------
# Pass A: Pure UOp lowering (PatternMatcher + graph_rewrite)
# ---------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class SfpuPrim:
  """Low-level Blackhole SFPU primitive arg for Ops.SFPU UOps."""
  op: str
  mod: int = 0
  imm: int = 0


def sfpu_prim(op: str, dtype: DType, *srcs: UOp, mod: int = 0, imm: int = 0) -> UOp:
  return UOp(Ops.SFPU, dtype, srcs, SfpuPrim(op, mod, imm))


def mulacc(a: UOp, b: UOp, c: UOp, *, neg_ab: bool = False, neg_c: bool = False) -> UOp:
  return UOp(Ops.MULACC, a.dtype, (a, b, c), (neg_ab, neg_c))


ARECIP_ERR = 0.0056       # SFPARECIP: worst-case relative error ~0.0056
RSQRT_SEED_ERR = 2.1e-5   # magic + quadratic seed relative error ~2.02e-5

# BF16 exp2: 2^(f1 - 1) minimax in f1 = 1 + frac(z) in [1.0, 2.0) (deg 2, rel < 2.3e-3, strict [1, 2)).
_EXP2_POLY_BF16 = (0.6918017864227295, -0.03182661160826683, 0.34228965640068054)
# FP32 exp2: 2^f minimax directly in f = x - round(x) in [-0.5, 0.5] (deg 5, rel < 3e-7 across [-126, 127], c0=1.0 -> L10!).
_EXP2_POLY_FP32 = (
  1.0, 0.6931471824645996, 0.2402210682630539,
  0.055503569543361664, 0.009676031768321991, 0.0013390863314270973,
)

# log2(m) = t * P(t^2) for m in [1, 2), t = (m - 1)/(m + 1) in [0, 1/3]
_LOG2_POLY_BF16 = (2.885390043258667, 0.9618448615074158, 0.5733158588409424)
_LOG2_POLY_FP32 = (2.885390043258667, 0.9618448615074158, 0.5733158588409424, 0.48057064414024353)

# sin(r) = r * P(r^2) for r in [-pi/2, pi/2]
_SIN_POLY_BF16 = (1.0, -0.16666658222675323, 0.008333049714565277, -0.0001980901724891737)
_SIN_POLY_FP32 = (1.0, -0.16666658222675323, 0.008333049714565277, -0.0001980901724891737, 2.6051077384181553e-06)


def newton_terms(seed_err: float, bits: int) -> int:
  """Terms of y*(1 + e + e^2 + ...) to reach `bits` + 3 guard bits from seed error `seed_err`."""
  k = 1
  while seed_err ** (k + 1) > 2.0 ** -(bits + 3): k += 1
  return k


def _horner(x: UOp, coeffs: Sequence[float]) -> UOp:
  dt = x.dtype
  acc = UOp.const(dt, coeffs[-1])
  for c in reversed(coeffs[:-1]):
    acc = acc * x + UOp.const(dt, c)
  return acc


def _decomp_exp2(x: UOp, bits: int) -> UOp:
  dt = x.dtype
  if bits <= 11:
    # Fast BF16 path (same structure as exp_l0): z = min(x + 127, 254), split via EXEXP/EXMAN/SHFT.
    z = (x + UOp.const(dt, 127.0)).minimum(UOp.const(dt, 254.0))
    e = sfpu_prim("EXEXP", dtypes.i32, z, mod=0)
    m = sfpu_prim("EXMAN", dtypes.u32, z, mod=0)
    s = sfpu_prim("SHFT_VAR", dtypes.u32, m, e, mod=0)
    f1 = sfpu_prim("SETEXP", dt, s, mod=1, imm=127)
    poly = _horner(f1, _EXP2_POLY_BF16)
    raw = sfpu_prim("SETEXP", dt, s, poly, mod=2)
    return (z < UOp.const(dt, 1.0)).where(UOp.const(dt, 0.0), raw)
  # Full-precision FP32 path: range-reduce via magic 1.5*2^23 so f = x - round(x) in [-0.5, 0.5] loses 0 mantissa bits.
  x_c = x.minimum(UOp.const(dt, 127.0)).maximum(UOp.const(dt, -126.0))
  magic = UOp.const(dt, 12582912.0)
  u = x_c + magic
  n_f = u - magic
  f = x_c - n_f
  e = u.bitcast(dtypes.i32) + UOp.const(dtypes.i32, 127)
  scale = sfpu_prim("SETEXP", dt, e, UOp.const(dt, 1.0), mod=0)  # exact 2^n
  raw = scale * _horner(f, _EXP2_POLY_FP32)
  return (x < UOp.const(dt, -126.0)).where(UOp.const(dt, 0.0), raw)


def _decomp_recip(x: UOp, bits: int) -> UOp:
  dt = x.dtype
  y = sfpu_prim("ARECIP", dt, x, mod=0)
  e = mulacc(x, y, UOp.const(dt, 1.0), neg_ab=True)  # 1 - x*y
  terms = newton_terms(ARECIP_ERR, bits)
  c = e
  for _ in range(terms - 1):
    c = mulacc(c, e, e)
  c = c.minimum(UOp.const(dt, 1.0))                  # prevents 0 / inf from turning into NaN
  return mulacc(c, y, y)


def _rsqrt_seed(x: UOp) -> UOp:
  dt = x.dtype
  xi = x.bitcast(dtypes.u32)
  y_bits = UOp.const(dtypes.u32, 0x5F1110A0) - (xi >> UOp.const(dtypes.u32, 1))
  y = y_bits.bitcast(dt)
  t = -(x * y) * y
  t = mulacc(t, t + UOp.const(dt, 2.2533049), UOp.const(dt, 2.2825186))
  return y * t


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
  e_tc = sfpu_prim("EXEXP", dtypes.i32, x, mod=0)
  e_f = e_tc.cast(dt)
  m = sfpu_prim("SETEXP", dt, x, mod=1, imm=127)     # m in [1.0, 2.0)
  t = (m - UOp.const(dt, 1.0)) * _decomp_recip(m + UOp.const(dt, 1.0), bits)
  poly = _horner(t * t, _LOG2_POLY_BF16 if bits <= 11 else _LOG2_POLY_FP32)
  return mulacc(t, poly, e_f)


# 3-part Cody-Waite split of pi (12-bit hi parts => exact n*pi_1, n*pi_2 for |n| < 4096, <2e-7 err on |x| <= 5000)
_PI_CW1 = 3.1416015625
_PI_CW2 = -8.907169103622437e-06
_PI_CW3 = -1.741103261565513e-09


def _decomp_sin(x: UOp, bits: int) -> UOp:
  dt = x.dtype
  # n = round(x / pi) via FP32 magic 1.5 * 2^23 (valid for |x/pi| < 2^21); bit 0 of u is parity of n.
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
  dst_f = (dtypes.fp32, dtypes.bf16)
  return pm_simplify + PatternMatcher([
    # Algebraic cleanup (DST float): collapse chained const muls & division -> reciprocal multiply.
    # NOTE: intentionally do NOT re-associate float additions ((x + c1) + c2) so (x + magic) - magic rounding is safe!
    (UPat(Ops.DIV, dtype=dst_f, space=Space.DST, src=(UPat.var("a"), UPat.var("b"))),
     lambda a, b: a * b.recip()),
    (UPat(Ops.MUL, dtype=dst_f, space=Space.DST,
          src=[UPat(Ops.MUL, src=[UPat.var("x"), UPat.const("c1")]), UPat.const("c2")]),
     lambda x, c1, c2: x * UOp.const(x.dtype, float(c1.arg) * float(c2.arg))),
    (UPat(Ops.ADD, dtype=dst_f, space=Space.DST, src=[UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),))]),
     lambda a, b: a - b),
    (UPat(Ops.SUB, dtype=dst_f, space=Space.DST, src=(UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),)))),
     lambda a, b: a + b),
    (UPat((Ops.MIN, Ops.MAX), dtype=(dtypes.i32, dtypes.u32), space=Space.DST,
          src=(UPat.var("a"), UPat.var("b")), name="u"),
     lambda u, a, b: (a < b).where(a, b) if u.op is Ops.MIN else (a < b).where(b, a)),
    # Transcendental decompositions on Space.DST
    (UPat(Ops.EXP2,  dtype=dst_f, space=Space.DST, src=(UPat.var("x"),)), lambda x: _decomp_exp2(x, bits)),
    (UPat(Ops.RECIP, dtype=dst_f, space=Space.DST, src=(UPat.var("x"),)), lambda x: _decomp_recip(x, bits)),
    (UPat(Ops.RSQRT, dtype=dst_f, space=Space.DST, src=(UPat.var("x"),)), lambda x: _decomp_rsqrt(x, bits)),
    (UPat(Ops.SQRT,  dtype=dst_f, space=Space.DST, src=(UPat.var("x"),)), lambda x: _decomp_sqrt(x, bits)),
    (UPat(Ops.LOG2,  dtype=dst_f, space=Space.DST, src=(UPat.var("x"),)), lambda x: _decomp_log2(x, bits)),
    (UPat(Ops.SIN,   dtype=dst_f, space=Space.DST, src=(UPat.var("x"),)), lambda x: _decomp_sin(x, bits)),
  ])


def _is_sfpu_mul(u: UOp) -> bool:
  return u.op is Ops.MUL and u.space is Space.DST and not u.is_fpu and u.dtype.is_float


pm_sfpu_fma = pm_simplify + PatternMatcher([
  # Fuse a*b + c -> MULACC(a, b, c) (single SFPMAD). Skip FPU (SrcA/SrcB) muls.
  (UPat(Ops.ADD, space=Space.DST, src=[UPat(Ops.MUL, src=(UPat.var("a"), UPat.var("b"))).named("m"), UPat.var("c")]),
   lambda m, a, b, c: mulacc(a, b, c) if _is_sfpu_mul(m) and c.dtype.is_float else None),
  (UPat(Ops.SUB, space=Space.DST, src=(UPat(Ops.MUL, src=(UPat.var("a"), UPat.var("b"))).named("m"), UPat.var("c"))),
   lambda m, a, b, c: mulacc(a, b, c, neg_c=True) if _is_sfpu_mul(m) and c.dtype.is_float else None),
  (UPat(Ops.SUB, space=Space.DST, src=(UPat.var("c"), UPat(Ops.MUL, src=(UPat.var("a"), UPat.var("b"))).named("m"))),
   lambda m, a, b, c: mulacc(a, b, c, neg_ab=True) if _is_sfpu_mul(m) and c.dtype.is_float else None),
  (UPat(Ops.NEG, space=Space.DST, src=(UPat(Ops.MUL, src=(UPat.var("a"), UPat.var("b"))).named("m"),)),
   lambda m, a, b: mulacc(a, b, UOp.const(a.dtype, 0.0), neg_ab=True) if _is_sfpu_mul(m) else None),
  # Fold negations into MULACC flags
  (UPat(Ops.MULACC, space=Space.DST, src=(UPat(Ops.NEG, src=(UPat.var("a"),)), UPat.var("b"), UPat.var("c")), name="u"),
   lambda u, a, b, c: mulacc(a, b, c, neg_ab=not u.arg[0], neg_c=u.arg[1])),
  (UPat(Ops.MULACC, space=Space.DST, src=(UPat.var("a"), UPat(Ops.NEG, src=(UPat.var("b"),)), UPat.var("c")), name="u"),
   lambda u, a, b, c: mulacc(a, b, c, neg_ab=not u.arg[0], neg_c=u.arg[1])),
  (UPat(Ops.MULACC, space=Space.DST, src=(UPat.var("a"), UPat.var("b"), UPat(Ops.NEG, src=(UPat.var("c"),))), name="u"),
   lambda u, a, b, c: mulacc(a, b, c, neg_ab=u.arg[0], neg_c=not u.arg[1])),
])


def lower_sfpu_uops(root: UOp, *, precision: DType = dtypes.fp32) -> UOp:
  """Pass A: expand Space.DST transcendentals and fuse MULACC/SFPMAD in pure UOps (with free CSE)."""
  bits = 8 if precision is dtypes.bf16 else 24
  if bits == 8:
    # Small approximation errors can select an entirely different branch. Keep
    # explicit FP32 predicate inputs at FP32 accuracy, including their other uses.
    comparisons = [u for u in root.toposort() if u.op in GroupOp.Comparison and u.src[0].dtype is dtypes.fp32]
    sensitive = [u for u in UOp.sink(*comparisons).toposort()
                 if u.dtype is dtypes.fp32 and u.op in (Ops.DIV, Ops.EXP2, Ops.LOG2, Ops.RECIP, Ops.RSQRT, Ops.SQRT, Ops.SIN)]
    if sensitive:
      precise = graph_rewrite(UOp.sink(*sensitive), _make_pm_sfpu_decomp(24))
      root = root.substitute(dict(zip(sensitive, precise.src, strict=True)))
  u = graph_rewrite(root, _make_pm_sfpu_decomp(bits))
  return graph_rewrite(u, pm_sfpu_fma)


# ---------------------------------------------------------------------------------------------------------------------
# Constant encoding & hardware LReg classification (L8..L15)
# ---------------------------------------------------------------------------------------------------------------------

def _const_u32(u: UOp) -> int:
  if u.dtype.is_float: return struct.unpack("<I", struct.pack("<f", float(u.arg)))[0]
  if u.dtype is dtypes.bool: return 0xFFFFFFFF if u.arg else 0
  return int(u.arg) & 0xFFFFFFFF


def _is_bf16_exact(u: UOp) -> bool:
  return u.dtype.is_float and (_const_u32(u) & 0xFFFF) == 0


def _hw_const_reg(u: UOp) -> int | None:
  """Return fixed read-only hardware LReg (L8/L9/L10) if `u` matches exactly."""
  bits = _const_u32(u)
  if bits == 0: return int(isa.LReg.ZERO)                     # L9: 0 / +0.0 (all types)
  if u.dtype.is_float and bits == 0x3F800000: return int(isa.LReg.ONE)           # L10: 1.0f
  if u.dtype.is_float and bits == 0x3F56594B: return int(isa.LReg.CONST_0_8373)  # L8: 0.8373f
  return None


def _emit_loadi32(out: list[int], rd: int, u: UOp) -> None:
  """Load any 32-bit constant into L0..L7 without triggering MAD -> half-word corruption.
  Using FLOATB (full write of hi16<<16) + LOWER (1 cycle after FLOATB, which is 1-cycle) is always hazard-free."""
  assert 0 <= rd < 8, f"SFPLOADI requires L0..L7, got L{rd}"
  bits = _const_u32(u)
  hi, lo = (bits >> 16) & 0xFFFF, bits & 0xFFFF
  if not u.dtype.is_float and 0 <= bits <= 0xFFFF:
    out.append(isa.SFPLOADI(rd, isa.LoadImm.USHORT, bits))
  elif not u.dtype.is_float and -0x8000 <= (bits - (1 << 32) if bits >= (1 << 31) else bits) < 0:
    out.append(isa.SFPLOADI(rd, isa.LoadImm.SHORT, bits & 0xFFFF))
  elif lo == 0:
    out.append(isa.SFPLOADI(rd, isa.LoadImm.FLOATB, hi))
  else:
    out.append(isa.SFPLOADI(rd, isa.LoadImm.FLOATB, hi))
    out.append(isa.SFPLOADI(rd, isa.LoadImm.LOWER, lo))


def _emit_sfpconfig_const(out: list[int], reg: int, u: UOp) -> None:
  """Emit SFPCONFIG to initialize programmable constant L11..L14 (clobbers L0 unless default imm matches)."""
  assert 11 <= reg <= 14, f"SFPCONFIG constant reg must be L11..L14, got L{reg}"
  bits = _const_u32(u)
  defaults = {11: 0xBF800000, 12: 0x3B000000, 13: 0xBF2CC4C7, 14: 0xBEB08FF9}
  if defaults.get(reg) == bits:
    out.append(isa.SFPCONFIG(0, reg, 1))
  else:
    _emit_loadi32(out, 0, u)
    out.append(isa.SFPCONFIG(0, reg, 0))


def _store_fmt(dt: DType) -> isa.SfpuFormat:
  """Avoid FP32 denormal flush destroying integers and boolean masks on Dst spill/store."""
  return isa.SfpuFormat.FP32 if dt.is_float else isa.SfpuFormat.INT32


def _load_fmt(dt: DType) -> isa.SfpuFormat:
  return isa.SfpuFormat.FP32 if dt.is_float else isa.SfpuFormat.INT32


# ---------------------------------------------------------------------------------------------------------------------
# Pass C: Single-pass physical L0..L7 register allocation & Tensix SFPU emission
# ---------------------------------------------------------------------------------------------------------------------

class _OutOfRegs(Exception):
  pass


@dataclass(frozen=True)
class CompiledSfpuPass:
  prologue: tuple[int, ...]       # SFPCONFIG / hoisted setup (once before 32-footprint loop)
  body: tuple[int, ...]           # 1 footprint (32 lanes), hazard-fixed (incl. loop wrap-around)
  epilogue: tuple[int, ...]       # post-pass cleanup
  inputs: dict[UOp, int]
  outputs: dict[UOp, int]
  l11_used: bool
  peak_regs: int
  cycles_per_footprint: float


@dataclass(frozen=True)
class CompiledSfpu:
  passes: tuple[CompiledSfpuPass, ...]
  dst_tiles: int
  output_tiles: dict[UOp, int]
  root_tiles: tuple[int, ...] = ()


def _is_direct_cmp(u: UOp) -> bool:
  if u.op in (Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE): return True
  if u.op is Ops.NOT and u.dtype is dtypes.bool and u.src[0].op in (Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE): return True
  return False


def _iadd_immediate(u: UOp) -> tuple[UOp, UOp, int] | None:
  if not u.dtype.is_int or u.op not in (Ops.ADD, Ops.SUB): return None
  var, const = u.src
  if u.op is Ops.ADD and var.op is Ops.CONST: var, const = const, var
  if const.op is Ops.CONST:
    imm = int(const.arg) if u.op is Ops.ADD else -int(const.arg)
    if -2048 <= imm < 2048: return var, const, imm
  return None


def _assign_const_regs(
  nodes: Sequence[UOp],
  *,
  preserve_l11: bool = False,
) -> tuple[dict[UOp, int], bool]:
  """Tier constants into free hardware regs (L8..L10) and up to 4 programmable SFPCONFIG regs (L11..L14)."""
  counts: dict[UOp, int] = {}
  # Also track constants that can be folded directly as immediates (shift imm, iadd imm12, etc.)
  for u in nodes:
    immediate = _iadd_immediate(u)
    for idx, s in enumerate(u.src):
      if s.op is not Ops.CONST: continue
      # Skip shift counts and iadd 12-bit immediates that don't need a register
      if u.op in (Ops.SHL, Ops.SHR) and idx == 1: continue
      if immediate and s is immediate[1]: continue
      counts[s] = counts.get(s, 0) + 1

  const_regs: dict[UOp, int] = {}
  prog_candidates: list[UOp] = []
  for c in counts:
    hw_r = _hw_const_reg(c)
    if hw_r is not None:
      const_regs[c] = hw_r
    else:
      prog_candidates.append(c)

  # Prioritize full 32-bit constants (cost 2 SFPLOADIs to rematerialize), then frequency, then deterministic bit key.
  # If -1.0f is used and we want it in L11, put it first so L11 gets its 1-insn default.
  prog_slots = [12, 13, 14] if preserve_l11 else [11, 12, 13, 14]
  neg_one_uop = next((c for c in prog_candidates if c.dtype.is_float and _const_u32(c) == 0xBF800000), None)
  if neg_one_uop is not None and (not preserve_l11):
    const_regs[neg_one_uop] = 11
    prog_slots.remove(11)
    prog_candidates.remove(neg_one_uop)
  elif neg_one_uop is not None and preserve_l11:
    # L11 is already -1.0f when preserved!
    const_regs[neg_one_uop] = 11
    prog_candidates.remove(neg_one_uop)

  prog_candidates.sort(key=lambda c: (0 if not _is_bf16_exact(c) else 1, -counts[c], _const_u32(c)))
  l11_repurposed = False
  for c, slot in zip(prog_candidates, prog_slots):
    const_regs[c] = slot
    if slot == 11: l11_repurposed = True
  return const_regs, l11_repurposed


class _PassLowerer:
  """Lowers one SfpuPass to exact physical L0..L7 Tensix SFPU instructions (hard <= max_regs limit)."""

  def __init__(
    self,
    nodes: Sequence[UOp],
    dst_inputs: dict[UOp, int],
    outputs: dict[UOp, int],
    const_regs: dict[UOp, int],
    *,
    max_regs: int = 8,
    addr_mode: int = 0,
  ):
    if not (1 <= max_regs <= 8): raise ValueError(f"max_regs must be in 1..8, got {max_regs}")
    self.nodes = tuple(nodes)
    self.node_set = set(self.nodes)
    self.dst_inputs = dst_inputs
    self.outputs = outputs
    self.const_regs = const_regs
    self.max_regs = max_regs
    self.addr_mode = addr_mode

    self.reg: dict[UOp, int] = {}           # live UOp -> L0..L7
    self.owner: dict[int, UOp] = {}         # L0..L7 -> UOp currently stored there
    self.free: list[int] = list(range(max_regs))
    self.peak_regs: int = 0
    self.body: list[int] = []
    self._stored: set[UOp] = set()
    self._written_tiles: set[int] = set()

    # Identify single-use comparisons fused directly into WHERE (avoiding a materialized mask reg!)
    # Only fuse if the comparison is inside this pass and not itself an output.
    raw_uses: dict[UOp, int] = {}
    for u in self.nodes:
      for s in u.src: raw_uses[s] = raw_uses.get(s, 0) + 1
    for out_u in outputs:
      raw_uses[out_u] = raw_uses.get(out_u, 0) + 1

    self.fused_cmps: set[UOp] = set()
    for u in self.nodes:
      if u.op is Ops.WHERE and u.src[0] in self.node_set and u.src[0] not in outputs:
        cond = u.src[0]
        if raw_uses.get(cond, 0) == 1 and _is_direct_cmp(cond):
          # If cond is NOT(cmp), also fuse the inner cmp if single-use and not an output
          if cond.op is Ops.NOT:
            inner = cond.src[0]
            if inner in self.node_set and inner not in outputs and raw_uses.get(inner, 0) == 1:
              self.fused_cmps.add(cond)
              self.fused_cmps.add(inner)
          else:
            self.fused_cmps.add(cond)

    # Effective remaining use counts (counting fused comparison operands on the consuming WHERE!)
    self.uses: dict[UOp, int] = {}
    for u in self.nodes:
      if u in self.fused_cmps: continue
      for s in self._effective_srcs(u):
        self.uses[s] = self.uses.get(s, 0) + 1
    for out_u in outputs:
      self.uses[out_u] = self.uses.get(out_u, 0) + 1

  def _effective_srcs(self, u: UOp) -> tuple[UOp, ...]:
    if u.op is Ops.WHERE and u.src[0] in self.fused_cmps:
      cond = u.src[0]
      cmp_u = cond.src[0] if cond.op is Ops.NOT else cond
      return (*cmp_u.src, u.src[1], u.src[2])
    return u.src

  # ---- register pool management ----

  def _touch_peak(self):
    used = self.max_regs - len(self.free)
    if used > self.peak_regs: self.peak_regs = used

  def alloc(self, protect: set[int] | None = None) -> int:
    if not self.free:
      # Before giving up, evict any rematerializable resident value (un-overwritten Dst input or CONST) not in `protect`.
      prot = protect or set()
      for r in range(self.max_regs):
        u = self.owner.get(r)
        if u is None or r in prot: continue
        can_reload_dst = u in self.dst_inputs and self.dst_inputs[u] not in self._written_tiles
        if can_reload_dst or u.op is Ops.CONST:
          self.reg.pop(u, None)
          self.owner.pop(r, None)
          self.free.append(r)
          self.free.sort()
          break
    if not self.free: raise _OutOfRegs()
    r = self.free.pop(0)
    self._touch_peak()
    return r

  def bind(self, u: UOp, r: int):
    assert 0 <= r < self.max_regs
    self.reg[u] = r
    self.owner[r] = u

  def free_reg(self, r: int):
    if 0 <= r < self.max_regs:
      u = self.owner.pop(r, None)
      if u is not None and self.reg.get(u) == r:
        self.reg.pop(u, None)
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
    """Ensure `u` is in an LReg. Returns (lreg, is_temp) where is_temp=True means caller must free_reg(r)."""
    if u.op is Ops.CONST:
      cr = self.const_regs.get(u)
      if cr is not None and (not need_writable) and (not need_lt12 or cr < 12):
        return cr, False
      if u in self.reg:
        return self.reg[u], False
      r = self.alloc(protect)
      _emit_loadi32(self.body, r, u)
      if self.uses.get(u, 0) > 1 and not need_writable:
        self.bind(u, r)
        return r, False
      return r, True

    if u in self.reg:
      return self.reg[u], False

    if u in self.dst_inputs:
      tile = self.dst_inputs[u]
      r = self.alloc(protect)
      self.body.append(isa.SFPLOAD(r, _load_fmt(u.dtype), 0, tile * DST_TILE_ROWS))
      self.bind(u, r)
      return r, False

    raise SfpuCompileError(f"operand {u.op.name} not available in pass")

  def _materialize_writable_copy(self, u: UOp, src_r: int, src_is_temp: bool, protect: set[int], count: int = 1) -> tuple[int, bool]:
    """Get a writable L0..L7 holding `u` that can be overwritten in-place without clobbering a live value."""
    if src_is_temp and src_r < 8:
      return src_r, True
    if src_r < 8 and u in self.reg and self.reg[u] == src_r and self.is_last_use(u, count):
      # Take ownership of the dying register!
      self.owner.pop(src_r, None)
      self.reg.pop(u, None)
      return src_r, True
    dst_r = self.alloc(protect | {src_r})
    self.body.append(isa.SFPMOV(0, src_r, dst_r, 0))
    return dst_r, True

  def _release_srcs(self, srcs: Sequence[UOp], regs: Sequence[int], temps: Sequence[bool], keep_regs: set[int] = frozenset()):
    for r, is_t in zip(regs, temps):
      if is_t and r not in keep_regs:
        self.free_reg(r)
    for s in srcs:
      self.drop_use(s)

  # ---- predication helpers ----

  def _integer_order_key(self, value: UOp, src: int, dst: int):
    # SFPGT orders sign-magnitude bit patterns, including -0 immediately before +0.
    # Ordinary nonnegative signed values already have the same representation.
    if value.dtype.is_signed and (value.op is Ops.LANE_ID or (value.op is Ops.CONST and 0 <= value.arg < 2**31)):
      self.body.append(isa.SFPMOV(0, src, dst, 0))
      return
    self.body.append(isa.SFPSHFT((-31) & 0xfff, src, dst, 7))
    self.body.append(isa.SFPSHFT((-1) & 0xfff, dst, dst, 5))
    if not value.dtype.is_signed:
      self.body.append(isa.SFPNOT(0, dst, dst, 0))
    self.body.append(isa.SFPXOR(0, src, dst, 0))

  def _emit_cmp_set_cc(self, cmp_u: UOp, invert: bool, protect: set[int]) -> None:
    """Emit comparison setting LaneFlags[0..31] (assumes SFPENCC already enabled!)."""
    op = cmp_u.op
    a, b = cmp_u.src
    prot = set(protect)
    # Handle CMPEQ / CMPNE via SFPSETCC on (a - b) or (a ^ b)
    if op in (Ops.CMPEQ, Ops.CMPNE):
      want_eq = (op is Ops.CMPEQ) ^ invert
      mod = 6 if want_eq else 2  # SFPSETCC: 6 == 0, 2 != 0
      if b.op is Ops.CONST and _const_u32(b) == 0:
        ra, ta = self.ensure(a, prot)
        self.body.append(isa.SFPSETCC(0, ra, 0, mod))
        if ta: self.free_reg(ra)
      elif a.op is Ops.CONST and _const_u32(a) == 0:
        rb, tb = self.ensure(b, prot)
        self.body.append(isa.SFPSETCC(0, rb, 0, mod))
        if tb: self.free_reg(rb)
      else:
        ra, ta = self.ensure(a, prot)
        rb, tb = self.ensure(b, prot | {ra})
        diff = self.alloc(prot | {ra, rb})
        if a.dtype.is_float:
          self.body.append(isa.SFPADD(int(isa.LReg.ONE), ra, rb, diff, 2))  # ra - rb
        else:
          self.body.append(isa.SFPMOV(0, ra, diff, 0))
          self.body.append(isa.SFPXOR(0, rb, diff, 0))
        self.body.append(isa.SFPSETCC(0, diff, 0, mod))
        self.free_reg(diff)
        if ta: self.free_reg(ra)
        if tb: self.free_reg(rb)
      return

    # CMPLT(a, b): a < b  <=>  b > a (SFPGT vc=a, vd=b, mod1=1)
    # Inverted:    a >= b <=>  b <= a (SFPLE vc=a, vd=b, mod1=1)
    assert op is Ops.CMPLT
    if a.dtype.is_float:
      ra, ta = self.ensure(a, prot)
      rb, tb = self.ensure(b, prot | {ra}, need_lt12=True)
      if invert:
        self.body.append(isa.SFPLE(0, ra, rb, 1))
      else:
        self.body.append(isa.SFPGT(0, ra, rb, 1))
      if ta: self.free_reg(ra)
      if tb: self.free_reg(rb)
    else:
      # Convert both inputs to keys ordered by SFPGT/SFPLE.
      ra, ta = self.ensure(a, prot)
      rb, tb = self.ensure(b, prot | {ra})
      sm_a = self.alloc(prot | {ra, rb})
      sm_b = self.alloc(prot | {ra, rb, sm_a})
      self._integer_order_key(a, ra, sm_a)
      self._integer_order_key(b, rb, sm_b)
      self.body.append(isa.SFPLE(0, sm_a, sm_b, 1) if invert else isa.SFPGT(0, sm_a, sm_b, 1))
      self.free_reg(sm_b)
      self.free_reg(sm_a)
      if ta: self.free_reg(ra)
      if tb: self.free_reg(rb)

  def _emit_cmp_mask(self, u: UOp) -> int:
    """Materialize a 0xFFFFFFFF / 0 boolean mask UOp into a fresh L0..L7."""
    op = u.op
    a, b = u.src
    if op is Ops.CMPLT and a.dtype.is_float:
      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      # SFPGT mod1=8 computes (vd > vc) ? -1 : 0, writing into vd (must be L0..L7)
      vd, _ = self._materialize_writable_copy(b, rb, tb, {ra}, count=(2 if a is b else 1))
      self.body.append(isa.SFPGT(0, ra, vd, 8))
      self._release_srcs((a, b), (ra, rb), (ta, False if vd == rb else tb), keep_regs={vd})
      return vd

    if op is Ops.CMPLT and not a.dtype.is_float:
      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      sm_a = self.alloc({ra, rb})
      sm_b = self.alloc({ra, rb, sm_a})
      self._integer_order_key(a, ra, sm_a)
      self._integer_order_key(b, rb, sm_b)
      self.body.append(isa.SFPGT(0, sm_a, sm_b, 8))
      self.free_reg(sm_a)
      self._release_srcs((a, b), (ra, rb), (ta, tb), keep_regs={sm_b})
      return sm_b

    # CMPEQ / CMPNE: build 0xFFFFFFFF / 0 via SFPENCC + SFPSETCC + SFPLOADI(-1)
    rd = self.alloc()
    self.body.append(isa.SFPMOV(0, int(isa.LReg.ZERO), rd, 0))
    self.body.append(isa.SFPENCC(1, 0, 0, 2))
    self._emit_cmp_set_cc(u, False, {rd})
    self.body.append(isa.SFPLOADI(rd, isa.LoadImm.SHORT, 0xFFFF))  # -1 = 0xFFFFFFFF in enabled lanes
    self.body.append(isa.SFPENCC(0, 0, 0, 2))
    self.drop_use(a)
    self.drop_use(b)
    return rd

  # ---- main per-UOp emitter ----

  def emit_uop(self, u: UOp) -> int:
    op, dt, src, arg = u.op, u.dtype, u.src, u.arg

    # Zero-cost bitcast alias
    if op is Ops.BITCAST:
      ra, ta = self.ensure(src[0], set())
      if ta:
        self.drop_use(src[0])
        return ra
      if ra < 8 and self.is_last_use(src[0]):
        self.owner.pop(ra, None)
        self.reg.pop(src[0], None)
        self.uses[src[0]] -= 1
        return ra
      rd = self.alloc({ra})
      self.body.append(isa.SFPMOV(0, ra, rd, 0))
      self.drop_use(src[0])
      return rd

    # LANE_ID: L15 holds lane*2 -> shift right logical by 1
    if op is Ops.LANE_ID:
      rd = self.alloc()
      self.body.append(isa.SFPSHFT((-1) & 0xFFF, int(isa.LReg.LANE_X2), rd, 5))
      return rd

    # WHERE(cond, a, b)
    if op is Ops.WHERE:
      cond, a, b = src
      if cond in self.fused_cmps:
        invert = cond.op is Ops.NOT
        cmp_u = cond.src[0] if invert else cond
        cx, cy = cmp_u.src
        # Load a and b; copy/reuse b into rd (disjoint from a and comparison inputs!)
        ra, ta = self.ensure(a, set())
        rb, tb = self.ensure(b, {ra})
        # Count how many times b appears in (cx, cy, a, b) so we don't clobber an operand needed for cmp/mov!
        b_occ = sum(1 for s in (cx, cy, a, b) if s is b)
        # Ensure rd cannot alias ra, cx, or cy
        prot = {ra}
        if cx in self.reg: prot.add(self.reg[cx])
        if cy in self.reg: prot.add(self.reg[cy])
        if tb and rb < 8 and rb not in prot:
          rd = rb
        elif rb < 8 and b in self.reg and self.reg[b] == rb and self.is_last_use(b, b_occ) and rb not in prot:
          self.owner.pop(rb, None)
          self.reg.pop(b, None)
          rd = rb
        else:
          rd = self.alloc(prot | {rb})
          self.body.append(isa.SFPMOV(0, rb, rd, 0))
        self.body.append(isa.SFPENCC(1, 0, 0, 2))
        self._emit_cmp_set_cc(cmp_u, invert, prot | {rd})
        self.body.append(isa.SFPMOV(0, ra, rd, 0))
        self.body.append(isa.SFPENCC(0, 0, 0, 2))
        if ta: self.free_reg(ra)
        if tb and rb != rd: self.free_reg(rb)
        for s in (cx, cy, a, b): self.drop_use(s)
        return rd

      # Materialized mask fast path: WHERE(mask, a, 0) -> single 3-address SFPAND!
      if b.op is Ops.CONST and _const_u32(b) == 0:
        rm, tm = self.ensure(cond, set())
        ra, ta = self.ensure(a, {rm})
        rd = self.alloc({rm, ra})
        self.body.append(isa.SFPAND(ra, rm, rd, 1))  # VD = VB & VC (Blackhole 3-address)
        self._release_srcs((cond, a, b), (rm, ra), (tm, ta), keep_regs={rd})
        return rd

      # Materialized mask general path
      rm, tm = self.ensure(cond, set())
      ra, ta = self.ensure(a, {rm})
      rb, tb = self.ensure(b, {rm, ra})
      b_occ = sum(1 for s in (cond, a, b) if s is b)
      prot = {rm, ra}
      if tb and rb < 8 and rb not in prot:
        rd = rb
      elif rb < 8 and b in self.reg and self.reg[b] == rb and self.is_last_use(b, b_occ) and rb not in prot:
        self.owner.pop(rb, None)
        self.reg.pop(b, None)
        rd = rb
      else:
        rd = self.alloc(prot | {rb})
        self.body.append(isa.SFPMOV(0, rb, rd, 0))
      self.body.append(isa.SFPENCC(1, 0, 0, 2))
      self.body.append(isa.SFPSETCC(0, rm, 0, 2))
      self.body.append(isa.SFPMOV(0, ra, rd, 0))
      self.body.append(isa.SFPENCC(0, 0, 0, 2))
      if tm: self.free_reg(rm)
      if ta: self.free_reg(ra)
      if tb and rb != rd: self.free_reg(rb)
      for s in (cond, a, b): self.drop_use(s)
      return rd

    # Materialized comparisons
    if op in (Ops.CMPLT, Ops.CMPEQ, Ops.CMPNE):
      return self._emit_cmp_mask(u)

    # MULACC(a, b, c, (neg_ab, neg_c)) -> SFPMAD
    if op is Ops.MULACC:
      a, b, c = src
      neg_ab, neg_c = arg if isinstance(arg, tuple) else (False, False)
      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      rc, tc = self.ensure(c, {ra, rb})
      # Free dying sources only after emitting (or reuse a dying non-aliased source reg as rd!)
      # SFPMAD is 3-address: rd may safely alias any source register!
      self._release_srcs((a, b, c), (ra, rb, rc), (ta, tb, tc))
      rd = self.alloc()
      mod1 = (1 if neg_ab else 0) | (2 if neg_c else 0)
      self.body.append(isa.SFPMAD(ra, rb, rc, rd, mod1))
      return rd

    # Float arithmetic: ADD, SUB, MUL (with BF16 immediate SFPADDI/SFPMULI when operand dies!)
    if op in (Ops.ADD, Ops.SUB, Ops.MUL) and dt.is_float:
      a, b = src
      # Try BF16 immediate fast path (0 constant regs!) when constant is not in L8..L14 and the variable dies here
      if op in (Ops.ADD, Ops.MUL):
        for var, cst in ((a, b), (b, a)):
          if (cst.op is Ops.CONST and cst not in self.const_regs and _is_bf16_exact(cst)
              and var.op is not Ops.CONST):
            rv, tv = self.ensure(var, set())
            if (tv and rv < 8) or (rv < 8 and var in self.reg and self.reg[var] == rv and self.is_last_use(var)):
              rd, _ = self._materialize_writable_copy(var, rv, tv, set())
              imm16 = (_const_u32(cst) >> 16) & 0xFFFF
              if op is Ops.ADD: self.body.append(isa.SFPADDI(imm16, rd, 0))
              else: self.body.append(isa.SFPMULI(imm16, rd, 0))
              self.drop_use(var)
              self.drop_use(cst)
              return rd

      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      self._release_srcs((a, b), (ra, rb), (ta, tb))
      rd = self.alloc()
      if op is Ops.ADD:
        self.body.append(isa.SFPADD(int(isa.LReg.ONE), ra, rb, rd, 0))
      elif op is Ops.SUB:
        self.body.append(isa.SFPADD(int(isa.LReg.ONE), ra, rb, rd, 2))
      else:
        self.body.append(isa.SFPMUL(ra, rb, int(isa.LReg.ZERO), rd, 0))
      return rd

    # Integer arithmetic: ADD, SUB (two's-complement SFPIADD)
    if op in (Ops.ADD, Ops.SUB) and dt.is_int:
      a, b = src
      if immediate := _iadd_immediate(u):
        var, const, imm = immediate
        rv, temp = self.ensure(var, set())
        self._release_srcs((var, const), (rv,), (temp,))
        rd = self.alloc()
        self.body.append(isa.SFPIADD(imm & 0xfff, rv, rd, 5))
        return rd
      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      # SFPIADD: mod=4 -> VD = VC + VD; mod=6 -> VD = VC - VD (note: VC is first operand a, VD is second b!)
      vd, _ = self._materialize_writable_copy(b, rb, tb, {ra}, count=(2 if a is b else 1))
      self.body.append(isa.SFPIADD(0, ra, vd, 4 if op is Ops.ADD else 6))
      self._release_srcs((a, b), (ra, rb), (ta, False if vd == rb else tb), keep_regs={vd})
      return vd

    # MIN / MAX via SFPSWAP (mod1=1: VD=min, VC=max; mod1=9: VD=max, VC=min)
    if op in (Ops.MIN, Ops.MAX):
      a, b = src
      if dt.is_float:
        ra, ta = self.ensure(a, set())
        rb, tb = self.ensure(b, {ra})
        # If one operand is a constant in L8..L11 (< 12), put it in VC and variable in VD:
        # HW ignores writes to VC >= 8, so SFPSWAP writes only VD = min/max(VD, VC) with 0 extra regs!
        mod1 = 1 if op is Ops.MIN else 9
        if rb >= 8 and ra < 8:
          vd, _ = self._materialize_writable_copy(a, ra, ta, {rb})
          self.body.append(isa.SFPSWAP(0, rb, vd, mod1))
          self._release_srcs((a, b), (ra, rb), (False if vd == ra else ta, tb), keep_regs={vd})
          return vd
        if ra >= 8 and rb < 8:
          vd, _ = self._materialize_writable_copy(b, rb, tb, {ra})
          self.body.append(isa.SFPSWAP(0, ra, vd, mod1))
          self._release_srcs((a, b), (ra, rb), (ta, False if vd == rb else tb), keep_regs={vd})
          return vd
        # Both in L0..L7 (or both consts): SFPSWAP writes BOTH VC and VD, so protect any live reg!
        vd, _ = self._materialize_writable_copy(a, ra, ta, {rb}, count=(2 if a is b else 1))
        vc, _ = self._materialize_writable_copy(b, rb, tb, {vd}, count=(2 if a is b else 1))
        self.body.append(isa.SFPSWAP(0, vc, vd, mod1))
        self.free_reg(vc)
        self._release_srcs((a, b), (ra, rb), (False if vd == ra else ta, False if vc == rb else tb), keep_regs={vd})
        return vd
      raise SfpuCompileError(f"integer {op.name} requires sign-mag conversion (not yet lowered)")

    # Unary ops: NEG, ABS, NOT
    if op is Ops.NEG:
      ra, ta = self.ensure(src[0], set())
      if dt.is_float:
        self._release_srcs(src, (ra,), (ta,))
        rd = self.alloc()
        self.body.append(isa.SFPMOV(0, ra, rd, 1))  # flip bit 31 (1 cycle!)
        return rd
      # Two's-complement integer negation: 0 - a
      vd, _ = self._materialize_writable_copy(src[0], ra, ta, set())
      self.body.append(isa.SFPIADD(0, int(isa.LReg.ZERO), vd, 6))
      self._release_srcs(src, (ra,), (False if vd == ra else ta,), keep_regs={vd})
      return vd

    if op is Ops.ABS:
      ra, ta = self.ensure(src[0], set())
      self._release_srcs(src, (ra,), (ta,))
      rd = self.alloc()
      self.body.append(isa.SFPABS(0, ra, rd, 1 if dt.is_float else 0))
      return rd

    if op is Ops.NOT:
      ra, ta = self.ensure(src[0], set())
      self._release_srcs(src, (ra,), (ta,))
      rd = self.alloc()
      self.body.append(isa.SFPNOT(0, ra, rd, 0))
      return rd

    # Bitwise ops: AND, OR (3-address on Blackhole!), XOR (2-address in-place)
    if op in (Ops.AND, Ops.OR):
      a, b = src
      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      self._release_srcs((a, b), (ra, rb), (ta, tb))
      rd = self.alloc()
      if op is Ops.AND: self.body.append(isa.SFPAND(ra, rb, rd, 1))
      else: self.body.append(isa.SFPOR(ra, rb, rd, 1))
      return rd

    if op is Ops.XOR:
      a, b = src
      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      vd, _ = self._materialize_writable_copy(a, ra, ta, {rb}, count=(2 if a is b else 1))
      self.body.append(isa.SFPXOR(0, rb, vd, 0))
      self._release_srcs((a, b), (ra, rb), (False if vd == ra else ta, tb), keep_regs={vd})
      return vd

    # Shifts: SHL, SHR
    if op in (Ops.SHL, Ops.SHR):
      a, b = src
      if b.op is Ops.CONST:
        amt = int(b.arg)
        imm = (amt if op is Ops.SHL else -amt) & 0xFFF
        mod = 7 if (op is Ops.SHR and dt.is_signed) else 5  # non-destructive VD = VC shift imm
        ra, ta = self.ensure(a, set())
        self._release_srcs((a, b), (ra,), (ta,))
        rd = self.alloc()
        self.body.append(isa.SFPSHFT(imm, ra, rd, mod))
        return rd
      ra, ta = self.ensure(a, set())
      rb, tb = self.ensure(b, {ra})
      vd, _ = self._materialize_writable_copy(a, ra, ta, {rb}, count=(2 if a is b else 1))
      if op is Ops.SHL:
        self.body.append(isa.SFPSHFT(0, rb, vd, 0))
      else:
        neg_b = self.alloc({vd, rb})
        self.body.append(isa.SFPMOV(0, rb, neg_b, 0))
        self.body.append(isa.SFPIADD(0, int(isa.LReg.ZERO), neg_b, 6))
        self.body.append(isa.SFPSHFT(0, neg_b, vd, 2 if dt.is_signed else 0))
        self.free_reg(neg_b)
      self._release_srcs((a, b), (ra, rb), (False if vd == ra else ta, tb), keep_regs={vd})
      return vd

    # CAST
    if op is Ops.CAST:
      x = src[0]
      rx, tx = self.ensure(x, set())
      if x.dtype == dt:
        if tx:
          self.drop_use(x)
          return rx
        rd = self.alloc({rx})
        self.body.append(isa.SFPMOV(0, rx, rd, 0))
        self.drop_use(x)
        return rd
      self._release_srcs(src, (rx,), (tx,))
      rd = self.alloc()
      if x.dtype.is_int and dt.is_float:
        self.body.append(isa.SFPCAST(rx, rd, 3))  # two's-comp -> sign-mag
        self.body.append(isa.SFPCAST(rd, rd, 0))  # sign-mag -> fp32
      elif x.dtype is dtypes.fp32 and dt is dtypes.bf16:
        # Always pass VB=LReg.ZERO so HW stall logic never invents a false stall on L0!
        self.body.append(isa.SFP_STOCH_RND(0, 0, int(isa.LReg.ZERO), rx, rd, 1))
      elif x.dtype is dtypes.bf16 and dt is dtypes.fp32:
        self.body.append(isa.SFPMOV(0, rx, rd, 0))
      elif x.dtype.is_float and dt.is_int:
        self.body.append(isa.SFP_STOCH_RND(2, 0, int(isa.LReg.ZERO), rx, rd, 7))
        self.body.append(isa.SFPCAST(rd, rd, 3))
      else:
        raise SfpuCompileError(f"unsupported SFPU cast {x.dtype} -> {dt}")
      return rd

    # Low-level Blackhole SFPU primitives (Ops.SFPU)
    if op is Ops.SFPU:
      assert isinstance(arg, SfpuPrim)
      p = arg.op
      if p in ("ARECIP", "EXEXP", "EXMAN", "DIVP2", "CAST_SM2F", "CAST_TC2SM"):
        rx, tx = self.ensure(src[0], set())
        self._release_srcs(src, (rx,), (tx,))
        rd = self.alloc()
        match p:
          case "ARECIP": word = isa.SFPARECIP(0, rx, rd, arg.mod)
          case "EXEXP": word = isa.SFPEXEXP(0, rx, rd, arg.mod)
          case "EXMAN": word = isa.SFPEXMAN(0, rx, rd, arg.mod)
          case "DIVP2": word = isa.SFPDIVP2(arg.imm & 0xFF, rx, rd, arg.mod)
          case "CAST_SM2F" | "CAST_TC2SM": word = isa.SFPCAST(rx, rd, 0 if p == "CAST_SM2F" else 3)
        self.body.append(word)
        return rd
      if p == "SETEXP":
        if arg.mod & 1:  # immediate exponent: VD = setexp(imm, VC) (non-destructive)
          rc, tc = self.ensure(src[0], set())
          self._release_srcs(src, (rc,), (tc,))
          rd = self.alloc()
          self.body.append(isa.SFPSETEXP(arg.imm & 0xFF, rc, rd, 1))
          return rd
        # Register exponent: src = (exp_src, mant_src); in-place on VD=exp_src, VC=mant_src
        re, te = self.ensure(src[0], set())
        rm, tm = self.ensure(src[1], {re})
        vd, _ = self._materialize_writable_copy(src[0], re, te, {rm}, count=(2 if src[0] is src[1] else 1))
        self.body.append(isa.SFPSETEXP(0, rm, vd, arg.mod))
        self._release_srcs(src, (re, rm), (False if vd == re else te, tm), keep_regs={vd})
        return vd
      if p == "SHFT_VAR":
        # src = (val, shift_amt); in-place on VD=val, VC=shift_amt
        rv, tv = self.ensure(src[0], set())
        rs, ts = self.ensure(src[1], {rv})
        vd, _ = self._materialize_writable_copy(src[0], rv, tv, {rs}, count=(2 if src[0] is src[1] else 1))
        self.body.append(isa.SFPSHFT(0, rs, vd, arg.mod))
        self._release_srcs(src, (rv, rs), (False if vd == rv else tv, ts), keep_regs={vd})
        return vd
      if p == "TRANSP":
        raise SfpuCompileError("TRANSP needs four explicit register inputs and a result selector")
      raise SfpuCompileError(f"unknown SfpuPrim {p!r}")

    raise SfpuCompileError(f"unsupported SFPU UOp {op.name}")

  def _store_if_ready(self, u: UOp, is_final: bool = False):
    if u not in self.outputs or u in self._stored: return
    # Only store eagerly once all in-pass uses are done (or at end of pass)
    if not is_final and self.uses.get(u, 0) > 1: return
    tile = self.outputs[u]
    r, is_t = self.ensure(u, set())
    # Backdoor invariant: never SFPSTORE directly from L12..L15!
    if r >= 12:
      tmp = self.alloc({r})
      self.body.append(isa.SFPMOV(0, r, tmp, 0))
      self.body.append(isa.SFPSTORE(tmp, _store_fmt(u.dtype), 0, tile * DST_TILE_ROWS))
      self.free_reg(tmp)
    else:
      self.body.append(isa.SFPSTORE(r, _store_fmt(u.dtype), 0, tile * DST_TILE_ROWS))
    if is_t: self.free_reg(r)
    self._stored.add(u)
    self._written_tiles.add(tile)
    self.drop_use(u)

  def run(self) -> tuple[list[int], int]:
    if not self.nodes and self.outputs:
      # Parallel copies. Write unneeded destinations first. Break each cycle by
      # holding one old tile in a register until its destination becomes free.
      pending = dict(self.outputs)
      saved: dict[UOp, int] = {}
      while pending:
        unread = {self.dst_inputs[u] for u in pending if u in self.dst_inputs and u not in saved}
        ready = next((u for u, t in pending.items() if t not in unread), None)
        if ready is None:
          u = next(u for u in pending if u in self.dst_inputs and u not in saved)
          saved[u], _ = self.ensure(u, set(saved.values()))
          continue
        tile = pending.pop(ready)
        r, temporary = self.ensure(ready, set(saved.values()))
        self.body.append(isa.SFPSTORE(r, _store_fmt(ready.dtype), 0, tile * DST_TILE_ROWS))
        self._written_tiles.add(tile)
        saved.pop(ready, None)
        if temporary: self.free_reg(r)
        self.drop_use(ready)
    else:
      for u in self.nodes:
        if u in self.fused_cmps: continue
        rd = self.emit_uop(u)
        if self.uses.get(u, 0) > 0:
          self.bind(u, rd)
          self._store_if_ready(u)
        else:
          self.free_reg(rd)
      # Flush any outputs that were inputs/consts or still pending
      for out_u in self.outputs:
        self._store_if_ready(out_u, is_final=True)
    # Attach sfpu_addr_mode (e.g. sfp_step dst+=2) to the final SFPSTORE in the pass body
    if self.addr_mode:
      for i in range(len(self.body) - 1, -1, -1):
        if (self.body[i] >> 24) == 0x72:  # SFPSTORE
          dec = isa.tensix_decode(self.body[i])
          assert dec is not None
          f = dict(dec[1])
          f["sfpu_addr_mode"] = self.addr_mode
          self.body[i] = isa.SFPSTORE(**f)
          break
    return self.body, self.peak_regs


def _try_lower_pass(
  nodes: Sequence[UOp],
  dst_inputs: dict[UOp, int],
  outputs: dict[UOp, int],
  *,
  max_regs: int = 8,
  preserve_l11: bool = False,
  addr_mode: int = 0,
) -> tuple[list[int], list[int], list[int], dict[UOp, int], bool, int]:
  const_regs, l11_used = _assign_const_regs(nodes, preserve_l11=preserve_l11)
  low = _PassLowerer(nodes, dst_inputs, outputs, const_regs, max_regs=max_regs, addr_mode=addr_mode)
  raw_body, peak = low.run()
  prologue: list[int] = []
  for c, r in sorted(const_regs.items(), key=lambda kv: kv[1]):
    if 11 <= r <= 14:
      _emit_sfpconfig_const(prologue, r, c)
  prologue = fix_sfpu_hazards(prologue)
  body = fix_sfpu_hazards(raw_body, is_loop=True)
  return prologue, body, [], const_regs, l11_used, peak


# ---------------------------------------------------------------------------------------------------------------------
# Pass B: Sethi-Ullman ordering & Dst-intermediate pass splitting
# ---------------------------------------------------------------------------------------------------------------------

def _ershov_order(roots: Sequence[UOp], stop: set[UOp]) -> list[UOp]:
  """Topological order minimizing peak register pressure (evaluate heavier subtree first)."""
  # Compute Ershov register estimate bottom-up
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
    if not child_ranks: rank[u] = 1
    else: rank[u] = max(cr + i for i, cr in enumerate(child_ranks))

  order: list[UOp] = []
  emitted: set[UOp] = set()

  def visit(u: UOp):
    if u in emitted or u in stop or u.op is Ops.CONST: return
    emitted.add(u)
    # Visit heavier subtrees first
    for s in sorted(u.src, key=lambda x: -rank.get(x, 0)):
      visit(s)
    order.append(u)

  for r in roots: visit(r)
  return order


def _verify_compiled_pass(pro: Sequence[int], body: Sequence[int], epi: Sequence[int]) -> None:
  verify_sfpu_words(pro)
  verify_sfpu_words(body, is_loop=True)
  verify_sfpu_words(epi)
  verify_sfpu_words(list(pro) + list(body) + list(epi))
  _verify_dst_store_load_order(body)


def partition_sfpu(
  roots: Sequence[UOp],
  dst_inputs: dict[UOp, int],
  *,
  max_regs: int = 8,
  dst_budget: int = 8,
  output_tiles: dict[UOp, int] | Sequence[int | None] | None = None,
  preserve_l11: bool = False,
  addr_mode: int = 0,
) -> CompiledSfpu:
  """Pass B + C + D: split a lowered SFPU UOp DAG into <= max_regs passes with Dst scratch spills,
  compile each pass to hazard-free Blackhole Tensix words, and verify all hardware invariants."""
  roots_t = tuple(roots)
  root_set = set(roots_t)

  # Normalize requested output tiles per root position (handles duplicate/CSE-collapsed roots cleanly!)
  if output_tiles is None:
    req_per_root: list[int | None] = [None] * len(roots_t)
  elif isinstance(output_tiles, dict):
    req_per_root = [output_tiles.get(r) for r in roots_t]
  else:
    if len(output_tiles) != len(roots_t):
      raise ValueError(f"output_tiles length {len(output_tiles)} != roots length {len(roots_t)}")
    req_per_root = list(output_tiles)

  if not 1 <= max_regs <= 8 or not 1 <= dst_budget <= 8:
    raise ValueError("FP32 SFPU passes require 1..8 writable registers and 1..8 Dst tiles")
  requested = {t: r for r, t in zip(roots_t, req_per_root) if t is not None}
  for t in (*dst_inputs.values(), *requested):
    if not 0 <= t < dst_budget:
      raise ValueError(f"Dst tile {t} outside budget {dst_budget}")
  if any(t is not None and requested[t] is not r for r, t in zip(roots_t, req_per_root)):
    raise ValueError("distinct SFPU results requested the same Dst tile")

  # First requested tile per unique root UOp (used as preferred home during compute); extras handled by copy pass
  preferred_out: dict[UOp, int] = {}
  for r, t in zip(roots_t, req_per_root):
    if t is not None and r not in preferred_out:
      preferred_out[r] = t

  live_dst: dict[UOp, int] = dict(dst_inputs)
  remaining = _ershov_order(roots_t, set(dst_inputs))
  req_vals = [t for t in req_per_root if t is not None]
  max_dst_used = max(list(live_dst.values()) + req_vals + [0]) + 1 if (live_dst or req_vals) else 0
  compiled_passes: list[CompiledSfpuPass] = []

  def boundary_outputs(cand: Sequence[UOp], rest: Sequence[UOp]) -> list[UOp]:
    cand_set = set(cand)
    needed_later: set[UOp] = set()
    for n in rest:
      for s in n.src:
        if s in cand_set: needed_later.add(s)
    return [u for u in cand if u in root_set or u in needed_later]

  def dst_still_needed(rest: Sequence[UOp], extra_keep: set[UOp]) -> set[int]:
    needed_uops = set(extra_keep)
    for n in rest:
      for s in n.src:
        if s in live_dst: needed_uops.add(s)
    return {live_dst[u] for u in needed_uops if u in live_dst}

  def assign_output_tiles(
    bouts: Sequence[UOp],
    cand: Sequence[UOp],
    rest: Sequence[UOp],
    pass_inputs: dict[UOp, int],
  ) -> dict[UOp, int] | None:
    keep_uops = {r for r in root_set if r in live_dst and r not in bouts}
    reserved = dst_still_needed(rest, keep_uops)
    # Safety invariant (Bug #1 fix): never overwrite any Dst input tile of this pass UNLESS
    # this is a single-output pass whose sole output is computed last (stored after all loads).
    can_reuse_input_tile = (len(bouts) == 1 and bool(cand) and bouts[0] is cand[-1])
    used_here: set[int] = set(reserved)
    if not can_reuse_input_tile:
      used_here |= set(pass_inputs.values())

    assigned: dict[UOp, int] = {}
    for u in bouts:
      if u in preferred_out:
        t = preferred_out[u]
        if t not in used_here:
          assigned[u] = t
          used_here.add(t)

    for u in bouts:
      if u in assigned: continue
      free_t = next((t for t in range(dst_budget) if t not in used_here), None)
      if free_t is None: return None
      assigned[u] = free_t
      used_here.add(free_t)

    return assigned

  while remaining:
    # Try a single pass first. Otherwise trade prefix length against the number
    # of spilled outputs. Trial the actual Dst addresses so reloads see aliases.
    best = None
    fail_streak = 0
    for k in itertools.chain((len(remaining),), range(1, len(remaining))):
      cand, rest = remaining[:k], remaining[k:]
      bouts = boundary_outputs(cand, rest)
      used_inputs = {s: live_dst[s] for n in cand for s in n.src if s in live_dst}
      out_map = assign_output_tiles(bouts, cand, rest, used_inputs)
      if out_map is None: continue
      try:
        result = _try_lower_pass(cand, used_inputs, out_map, max_regs=max_regs,
                                 preserve_l11=preserve_l11, addr_mode=addr_mode)
      except _OutOfRegs:
        if rest:
          fail_streak += 1
          if fail_streak >= 4: break
        continue
      fail_streak = 0
      score = (k - 4 * len(bouts), -len(bouts), k)
      if best is None or score > best[0]:
        best = score, rest, used_inputs, out_map, result
      if not rest: break
    if best is None:
      raise SfpuCompileError(f"cannot schedule {remaining[0].op.name} within {max_regs} LRegs and {dst_budget} Dst tiles")
    _, rest, used_inputs, out_map, (pro, body, epi, _, l11_used, peak) = best
    max_dst_used = max(max_dst_used, max(out_map.values()) + 1)
    _verify_compiled_pass(pro, body, epi)
    compiled_passes.append(CompiledSfpuPass(
      prologue=tuple(pro),
      body=tuple(body),
      epilogue=tuple(epi),
      inputs=used_inputs,
      outputs=out_map,
      l11_used=l11_used,
      peak_regs=peak,
      cycles_per_footprint=sfpu_slope(body),
    ))
    written_tiles = set(out_map.values())
    live_dst = {u: t for u, t in live_dst.items() if t not in written_tiles}
    live_dst.update(out_map)
    remaining = rest

  # Materialize any CONST roots, move any root whose tile differs from requested, and duplicate CSE-collapsed roots!
  # Collect per-root final tile assignments.
  final_root_tiles: list[int] = []
  homes = dict(preferred_out)
  used_final = set(requested)
  for r in roots_t:
    if r not in homes and r in live_dst and live_dst[r] not in used_final:
      homes[r] = live_dst[r]
      used_final.add(homes[r])
  pending_copies: list[tuple[UOp, int]] = []
  for r, req_t in zip(roots_t, req_per_root):
    if r not in homes:
      tile = next((t for t in range(dst_budget) if t not in used_final), None)
      if tile is None:
        raise SfpuCompileError(f"exceeded Dst tile budget ({dst_budget} tiles) for outputs")
      homes[r] = tile
      used_final.add(tile)
    tile = homes[r] if req_t is None else req_t
    final_root_tiles.append(tile)
    if live_dst.get(r) != tile and (r, tile) not in pending_copies:
      pending_copies.append((r, tile))

  # Emit copy / const-fill passes cleanly (batching disjoint dest tiles, supporting duplicate sources via separate pass)
  while pending_copies:
    batch: dict[UOp, int] = {}
    rest_copies: list[tuple[UOp, int]] = []
    for src_u, dst_t in pending_copies:
      if src_u not in batch:
        batch[src_u] = dst_t
      else:
        rest_copies.append((src_u, dst_t))
    in_map = {u: live_dst[u] for u in batch if u in live_dst}
    try:
      pro, body, epi, _, l11_used, peak = _try_lower_pass(
        (), in_map, batch, max_regs=max_regs, preserve_l11=preserve_l11, addr_mode=addr_mode,
      )
    except _OutOfRegs as exc:
      raise SfpuCompileError(f"parallel output copies exceed {max_regs} LRegs") from exc
    _verify_compiled_pass(pro, body, epi)
    compiled_passes.append(CompiledSfpuPass(
      tuple(pro), tuple(body), tuple(epi), in_map, batch, l11_used, peak, sfpu_slope(body),
    ))
    live_dst.update(batch)  # Later duplicates read the new home, even after a cyclic swap.
    max_dst_used = max(max_dst_used, max(batch.values()) + 1)
    pending_copies = rest_copies

  if final_root_tiles:
    max_dst_used = max(max_dst_used, max(final_root_tiles) + 1)
  final_output_tiles = {r: t for r, t in zip(roots_t, final_root_tiles)}
  return CompiledSfpu(tuple(compiled_passes), max_dst_used, final_output_tiles, tuple(final_root_tiles))


def compile_sfpu(
  roots: UOp | Sequence[UOp],
  dst_inputs: dict[UOp, int],
  *,
  precision: DType = dtypes.fp32,
  max_regs: int = 8,
  dst_budget: int = 8,
  output_tiles: dict[UOp, int] | Sequence[int | None] | None = None,
  preserve_l11: bool = False,
  addr_mode: int = 0,
) -> CompiledSfpu:
  """End-to-end SFPU compiler: Layer 1 Space.DST UOp(s) -> verified multi-pass Blackhole SFPU Tensix streams."""
  roots_list = [roots] if isinstance(roots, UOp) else list(roots)
  # Lower each root through Pass A (sharing hash-consed UOps & CSE across all roots!)
  # A resident input can itself be an expression from an earlier stage. Hide its
  # producer from decomposition and FMA matching until the pass boundary is bound.
  leaves = {u: sfpu_prim("DST_INPUT", u.dtype, imm=i) for i, u in enumerate(dst_inputs)}
  sink_in = UOp.sink(*roots_list).substitute(leaves)
  lowered_sink = lower_sfpu_uops(sink_in, precision=precision)
  lowered_roots = lowered_sink.substitute({leaf: u for u, leaf in leaves.items()}).src
  out_tiles_pos: list[int | None] | None = None
  if output_tiles is not None:
    if isinstance(output_tiles, dict):
      out_tiles_pos = [output_tiles.get(r) for r in roots_list]
    else:
      out_tiles_pos = list(output_tiles)
  return partition_sfpu(
    lowered_roots,
    dst_inputs,
    max_regs=max_regs,
    dst_budget=dst_budget,
    output_tiles=out_tiles_pos,
    preserve_l11=preserve_l11,
    addr_mode=addr_mode,
  )
