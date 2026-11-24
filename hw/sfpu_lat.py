"""Blackhole A0 SFPU pipeline timing, register usage, hazard fixing, and hardware invariant verification.

Timing and undetected-RAW hazard rules are silicon-measured on Blackhole A0 (ported from boop-docs/probes/model.py).
Register sets are 17-bit masks (bits 0..15 = L0..L15, bit 16 = L16 macro pipeline reg).
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence
from . import isa

ALL_LREGS = 0xFFFF      # L0..L15
WRITABLE_LREGS = 0x00FF # L0..L7


class SfpuError(RuntimeError):
  pass


@dataclass(frozen=True, slots=True)
class SfpuInsn:
  op: str        # Tensix mnemonic from hw.isa (e.g. "SFPMAD", "SFPLOAD")
  reads: int     # bitmask of LRegs actually read at issue
  writes: int    # bitmask of LRegs written
  seen_r: int    # bitmask of LRegs hardware stall logic believes are read
  seen_w: int    # bitmask of LRegs hardware stall logic believes a 2-cycle op writes
  lat: int       # 2 for MAD-column, 1 otherwise
  block: int     # 1 for SWAP / SHFT2 modes 2..4 (holds issue slot 1 extra cycle)
  unit: str      # load | simple | mad | round | store


def _mask(*regs: int) -> int:
  m = 0
  for r in regs: m |= 1 << r
  return m


def _lowest_reg(mask: int) -> int:
  return (mask & -mask).bit_length() - 1


def loadmacro_units(sequence: int) -> list[tuple[str, int, bool]]:
  """[(unit, delay, writes_l16)] scheduled by one SFPLOADMACRO for a Sequence word."""
  out: list[tuple[str, int, bool]] = []
  for n, unit in enumerate(("simple", "mad", "round", "store")):
    b = (sequence >> (8 * n)) & 0xFF
    if b & 7: out.append((unit, (b >> 3) & 7, bool(b & 0x40)))
  return out


@lru_cache(maxsize=8192)
def sfpu_decode(w: int) -> SfpuInsn | None:
  """Decode an unrotated Tensix word into SFPU timing/register metadata, or None if not SFPU."""
  op = isa._TENSIX_BY_OP.get(w >> 24)
  if op is None or not op.startswith("SFP"): return None

  vd, vc, vb, va, mod = (w >> 4) & 15, (w >> 8) & 15, (w >> 12) & 15, (w >> 16) & 15, w & 15
  ld_vd, mod0 = (w >> 20) & 15, (w >> 16) & 15
  r = s = wr = block = 0
  seen_w: int | None = None
  lat, unit = 1, "simple"

  match op:
    case "SFPMAD" | "SFPADD" | "SFPMUL" | "SFPMUL24":
      r = _mask(va, vb, vc) | (1 << 7 if mod & 12 else 0)
      s = ALL_LREGS if mod & 4 else r
      wr = WRITABLE_LREGS if mod & 8 else 1 << vd
      lat, unit = 2, "mad"
    case "SFPADDI" | "SFPMULI":
      r = s = (1 << vd) | (1 << 7 if mod & 8 else 0)
      wr = WRITABLE_LREGS if mod & 8 else 1 << vd
      lat, unit = 2, "mad"
    case "SFPLUT":
      r = s = 0x0F | (1 << 7 if mod0 & 8 else 0)
      wr = WRITABLE_LREGS if mod0 & 8 else 1 << ld_vd
      lat, unit = 2, "mad"
    case "SFPLUTFP32":
      mirror = (w >> 16) & 15
      r, wr = 0x7F, 1 << vd
      s = ALL_LREGS if mirror & 8 else ALL_LREGS & ~(1 << 7)
      seen_w = ALL_LREGS if mirror & 8 else wr
      lat, unit = 2, "mad"
    case "SFPMOV" | "SFPABS" | "SFPNOT" | "SFPLZ" | "SFPEXEXP" | "SFPEXMAN" | "SFPCAST" | "SFPDIVP2":
      r = s = 1 << vc
      wr = 1 << vd
    case "SFPIADD":
      r, s, wr = ((1 << vc) if mod & 1 else _mask(vc, vd)), 1 << vc, 1 << vd
    case "SFPSHFT":
      r = (1 << vc) if (mod & 5) == 5 else (1 << vd) if mod & 1 else _mask(vc, vd)
      s, wr = (r if mod & 1 else 1 << vc), 1 << vd
    case "SFPAND" | "SFPOR":
      r, s, wr = _mask(vc, vb if mod & 1 else vd), _mask(vc, vd), 1 << vd
    case "SFPXOR":
      r = s = _mask(vc, vd)
      wr = 1 << vd
    case "SFPSETEXP" | "SFPSETMAN" | "SFPSETSGN":
      imm = mod & 1
      r = (1 << vc) if imm else _mask(vc, vd)
      s = _mask(vc, vd) if imm else 1 << vc
      wr = 1 << vd
    case "SFPARECIP":
      r = _mask(vc, vb) if mod == 1 else 1 << vc
      s = _mask(vc, vd) if mod == 1 else 1 << vc
      wr = 1 << vd
    case "SFP_STOCH_RND":
      r = (1 << vc) | (1 << vb if (mod & 7) in (4, 5) and not (mod & 8) else 0)
      s = (1 << vc) | (0 if mod & 8 else 1 << vb)
      wr, unit = 1 << vd, "round"
    case "SFPSETCC":
      r = s = 1 << vc
    case "SFPGT" | "SFPLE":
      r = s = _mask(vc, vd)
      wr = (1 << vd) if mod & 8 else 0
    case "SFPSWAP":
      r = 0 if mod == 0 else _mask(vc, vd)
      wr, block = _mask(vc, vd), 1
    case "SFPSHFT2":
      unit = "round"
      match mod:
        case 0: r = s = 0x0E | (1 << vc); wr = 0x0F
        case 1: r = s = 0x0F | (1 << vc); wr = 0x0F
        case 2: r, wr, block = 0x0E | (1 << vc), 0x0F, 1
        case 3 | 4: r, wr, block = 1 << vc, 1 << vd, 1
        case 5: r, s, wr = _mask(vb, vc), _mask(vc, vd), 1 << vd
        case 6: r, s, wr = 1 << vb, 1 << vd, 1 << vd
    case "SFPTRANSP":
      r = s = wr = WRITABLE_LREGS
    case "SFPSTORE":
      r = s = 1 << ld_vd
      unit = "store"
    case "SFPCONFIG":
      r = 0 if mod & 1 else 1
      wr = (1 << vd) if 11 <= vd < 15 else 0
    case "SFPLOADI" | "SFPLOAD":
      half = (op == "SFPLOADI" and mod0 in (8, 10)) or (op == "SFPLOAD" and mod0 in (14, 15))
      r, wr, unit = ((1 << ld_vd) if half else 0), 1 << ld_vd, "load"
    case "SFPLOADMACRO":
      wr, unit = 1 << ((ld_vd & 3) | ((w & 1) << 2)), "load"
    case "SFPNOP":
      unit = "load"
    case "SFPENCC" | "SFPPUSHC" | "SFPPOPC" | "SFPCOMPC":
      pass
    case _:
      return None

  if seen_w is None: seen_w = wr if lat == 2 else 0
  return SfpuInsn(op, r, wr, s, seen_w, lat, block, unit)


def sfpu_cost(prev, w: int, macros: dict[int, int] | None = None):
  """Issue one unrotated Tensix word. Returns (stall_cycles, hazard_or_None, new_state)."""
  t_prev, blocked, pending, sched = prev or (-10, -10, (), ())
  t = t_prev + 1
  i = sfpu_decode(w)
  if i is None or i.op == "SFPNOP":
    return 0, None, (t, blocked, tuple(p for p in pending if p[0] > t), tuple(s for s in sched if s[1] >= t))
  t0 = t
  while t == blocked or any(ready > t and (seen & i.seen_r) for ready, seen, _ in pending):
    t += 1
  hazard = None
  for ready, _, writes in pending:
    if ready > t and (hit := writes & i.reads): hazard = ("stale", _lowest_reg(hit))
  if any(u == i.unit and c == t for u, c in sched): hazard = ("dropped", i.unit)
  live = tuple(p for p in pending if p[0] > t)
  if i.lat == 2 and i.writes: live += ((t + 2, i.seen_w, i.writes),)
  sched = tuple(s for s in sched if s[1] >= t)
  if i.op == "SFPLOADMACRO" and macros:
    x = _lowest_reg(i.writes)
    for unit, delay, l16 in loadmacro_units(macros.get((w >> 22) & 3, 0)):
      at = t + 1 + delay
      sched += ((unit, at),)
      if unit != "store":
        live += ((at + (2 if unit == "mad" else 1), 0, 1 << (16 if l16 else x)),)
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
  return (sfpu_cycles(words, 64, macros) - sfpu_cycles(words, 32, macros)) / 32.0 if words else 0.0


def sfpu_hazards(words: Sequence[int], macros: dict[int, int] | None = None) -> list[tuple[int, tuple]]:
  """[(index, hazard)] for every stale read or dropped instruction in a straight-line stream."""
  state, out = None, []
  for n, w in enumerate(words):
    _, hz, state = sfpu_cost(state, w, macros)
    if hz: out.append((n, hz))
  return out


def fix_sfpu_hazards(words: Sequence[int], macros: dict[int, int] | None = None, *, is_loop: bool = False) -> list[int]:
  """Insert minimal SFPNOPs for every undetected RAW hazard (and documented SFPCONFIG macro/backdoor gaps)."""
  nop = isa.SFPNOP()
  out: list[int] = []
  state = None
  prev_cfg_macro_or_lane = False
  for w in words:
    dec = sfpu_decode(w)
    if prev_cfg_macro_or_lane and (dec is not None and dec.op != "SFPNOP"):
      _, _, state = sfpu_cost(state, nop, macros)
      out.append(nop)
      prev_cfg_macro_or_lane = False
    _, hz, nxt = sfpu_cost(state, w, macros)
    match hz:
      case ("stale", _):
        _, _, state = sfpu_cost(state, nop, macros)
        out.append(nop)
        _, hz2, nxt = sfpu_cost(state, w, macros)
        if hz2 is not None: raise SfpuError(f"unresolvable SFPU hazard {hz2} on {isa.tensix_decode(w)}")
      case None:
        pass
      case _:
        raise SfpuError(f"SFPU hazard {hz} on {isa.tensix_decode(w)}")
    state = nxt
    out.append(w)
    prev_cfg_macro_or_lane = dec is not None and dec.op == "SFPCONFIG" and (((w >> 4) & 15) <= 8 or ((w >> 4) & 15) == 15)
  if is_loop and out and sfpu_hazards(out + out, macros):
    out.append(nop)
    if sfpu_hazards(out + out, macros):
      raise SfpuError(f"unresolvable SFPU loop wrap-around hazard: {sfpu_hazards(out + out, macros)}")
  return out


def verify_sfpu_words(
  words: Sequence[int],
  *,
  allow_backdoor: bool = False,
  macros: dict[int, int] | None = None,
  is_loop: bool = False,
) -> None:
  """Verify Blackhole SFPU hardware invariants on an unrotated Tensix word stream."""
  check_stream = list(words) + list(words) if (is_loop and words) else list(words)
  if hz := sfpu_hazards(check_stream, macros):
    idx, err = hz[0]
    raise SfpuError(f"SFPU hazard at word {idx} ({isa.tensix_decode(check_stream[idx])}): {err}")
  for idx, w in enumerate(words):
    info = sfpu_decode(w)
    if info is None: continue
    op = info.op
    # With DISABLE_BACKDOOR_LOAD=0 (default), VD >= 12 on non-CONFIG/LOADMACRO turns into a silent template write.
    if not allow_backdoor and op not in ("SFPCONFIG", "SFPLOADMACRO", "SFPNOP"):
      vd = ((w >> 20) & 15) if op in ("SFPLOAD", "SFPLOADI", "SFPSTORE", "SFPLUT") else ((w >> 4) & 15)
      if vd >= 12:
        raise SfpuError(f"word {idx} ({op}) has VD={vd} >= 12 (silent backdoor template write)")
    # Only L0..L7 (and L11..L14 via SFPCONFIG) are writable. SFPSWAP ignores writes to VC >= 8 (only VD must be < 8).
    if op == "SFPSWAP":
      if (vd := (w >> 4) & 15) >= 8:
        raise SfpuError(f"word {idx} (SFPSWAP) writes illegal VD register L{vd}")
    elif op != "SFPCONFIG" and (bad := info.writes & ~WRITABLE_LREGS):
      raise SfpuError(f"word {idx} ({op}) writes read-only/const register L{_lowest_reg(bad)}")


def disasm_sfpu(words: Sequence[int]) -> str:
  """Human-readable disassembly of unrotated SFPU Tensix words."""
  lines = []
  for i, w in enumerate(words):
    if (dec := isa.tensix_decode(w)) is None: lines.append(f"{i:3d}: 0x{w:08x}")
    else:
      name, fields = dec
      fstr = ", ".join(f"{k}={v}" for k, v in fields.items() if v != 0)
      lines.append(f"{i:3d}: {name}({fstr})")
  return "\n".join(lines)
