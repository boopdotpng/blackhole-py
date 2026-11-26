from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from . import isa

ALL_LREGS, WRITABLE_LREGS = 0xFFFF, 0x00FF
_SFP_OPS = {op.value: op.name for op in isa.TensixOp if op.name.startswith("SFP")}

class SfpuError(RuntimeError): pass

@dataclass(frozen=True, slots=True)
class SfpuInsn:
  op: str; reads: int; writes: int; seen_r: int; seen_w: int; lat: int; block: int; unit: str

def _mask(*regs: int) -> int: return sum(1 << r for r in set(regs))
def _lowest_reg(mask: int) -> int: return (mask & -mask).bit_length() - 1

def loadmacro_units(sequence: int) -> list[tuple[str, int, bool]]:
  bs = [(u, sequence >> (8 * n) & 0xFF) for n, u in enumerate(("simple", "mad", "round", "store"))]
  return [(u, b >> 3 & 7, bool(b & 0x40)) for u, b in bs if b & 7]

@lru_cache(maxsize=8192)
def sfpu_decode(w: int) -> SfpuInsn | None:
  if (op := _SFP_OPS.get(w >> 24)) is None: return None
  vd, vc, vb, va, mod = w >> 4 & 15, w >> 8 & 15, w >> 12 & 15, w >> 16 & 15, w & 15
  ld, mod0 = w >> 20 & 15, w >> 16 & 15
  r = s = wr = block = 0
  seen_w, lat, unit = None, 1, "simple"
  match op:
    case "SFPMAD" | "SFPADD" | "SFPMUL" | "SFPMUL24":
      r = _mask(va, vb, vc) | (0x80 if mod & 12 else 0)
      s, wr, lat, unit = ALL_LREGS if mod & 4 else r, WRITABLE_LREGS if mod & 8 else 1 << vd, 2, "mad"
    case "SFPADDI" | "SFPMULI":
      r = s = 1 << vd | (0x80 if mod & 8 else 0)
      wr, lat, unit = WRITABLE_LREGS if mod & 8 else 1 << vd, 2, "mad"
    case "SFPLUT":
      r = s = 0x0F | (0x80 if mod0 & 8 else 0)
      wr, lat, unit = WRITABLE_LREGS if mod0 & 8 else 1 << ld, 2, "mad"
    case "SFPLUTFP32":
      r, wr, lat, unit = 0x7F, 1 << vd, 2, "mad"
      s, seen_w = (ALL_LREGS, ALL_LREGS) if va & 8 else (ALL_LREGS & ~0x80, wr)
    case "SFPMOV" | "SFPABS" | "SFPNOT" | "SFPLZ" | "SFPEXEXP" | "SFPEXMAN" | "SFPCAST" | "SFPDIVP2": r, s, wr = 1 << vc, 1 << vc, 1 << vd
    case "SFPIADD": r, s, wr = (1 << vc) if mod & 1 else _mask(vc, vd), 1 << vc, 1 << vd
    case "SFPSHFT":
      r = (1 << vc) if mod & 5 == 5 else (1 << vd) if mod & 1 else _mask(vc, vd)
      s, wr = r if mod & 1 else 1 << vc, 1 << vd
    case "SFPAND" | "SFPOR": r, s, wr = _mask(vc, vb if mod & 1 else vd), _mask(vc, vd), 1 << vd
    case "SFPXOR": r, s, wr = _mask(vc, vd), _mask(vc, vd), 1 << vd
    case "SFPSETEXP" | "SFPSETMAN" | "SFPSETSGN":
      r, s = ((1 << vc), _mask(vc, vd)) if mod & 1 else (_mask(vc, vd), 1 << vc)
      wr = 1 << vd
    case "SFPARECIP": r, s, wr = (_mask(vc, vb), _mask(vc, vd), 1 << vd) if mod == 1 else (1 << vc, 1 << vc, 1 << vd)
    case "SFP_STOCH_RND":
      r = 1 << vc | (1 << vb if mod & 7 in (4, 5) and not mod & 8 else 0)
      s, wr, unit = 1 << vc | (0 if mod & 8 else 1 << vb), 1 << vd, "round"
    case "SFPSETCC": r = s = 1 << vc
    case "SFPGT" | "SFPLE": r, s, wr = _mask(vc, vd), _mask(vc, vd), (1 << vd) if mod & 8 else 0
    case "SFPSWAP": r, wr, block = 0 if mod == 0 else _mask(vc, vd), _mask(vc, vd), 1
    case "SFPSHFT2":
      unit = "round"
      match mod:
        case 0: r = s = 0x0E | 1 << vc; wr = 0x0F
        case 1: r = s = 0x0F | 1 << vc; wr = 0x0F
        case 2: r, wr, block = 0x0E | 1 << vc, 0x0F, 1
        case 3 | 4: r, wr, block = 1 << vc, 1 << vd, 1
        case 5: r, s, wr = _mask(vb, vc), _mask(vc, vd), 1 << vd
        case 6: r, s, wr = 1 << vb, 1 << vd, 1 << vd
    case "SFPTRANSP": r = s = wr = WRITABLE_LREGS
    case "SFPSTORE": r, s, unit = 1 << ld, 1 << ld, "store"
    case "SFPCONFIG": r, wr = 0 if mod & 1 else 1, (1 << vd) if 11 <= vd < 15 else 0
    case "SFPLOADI" | "SFPLOAD":
      half = mod0 in ((8, 10) if op == "SFPLOADI" else (14, 15))
      r, wr, unit = (1 << ld) if half else 0, 1 << ld, "load"
    case "SFPLOADMACRO": wr, unit = 1 << ((ld & 3) | (w & 1) << 2), "load"
    case "SFPNOP": unit = "load"
    case "SFPENCC" | "SFPPUSHC" | "SFPPOPC" | "SFPCOMPC": pass
    case _: return None
  return SfpuInsn(op, r, wr, s, (wr if lat == 2 else 0) if seen_w is None else seen_w, lat, block, unit)

def sfpu_cost(prev, w: int, macros: dict[int, int] | None = None):
  t_prev, blocked, pending, sched = prev or (-10, -10, (), ())
  t = t0 = t_prev + 1
  i = sfpu_decode(w)
  if i is None or i.op == "SFPNOP":
    return 0, None, (t, blocked, tuple(p for p in pending if p[0] > t), tuple(s for s in sched if s[1] >= t))
  while t == blocked or any(ready > t and seen & i.seen_r for ready, seen, _ in pending): t += 1
  hazard = None
  for ready, _, writes in pending:
    if ready > t and (hit := writes & i.reads): hazard = ("stale", _lowest_reg(hit))
  if any(u == i.unit and c == t for u, c in sched): hazard = ("dropped", i.unit)
  live = tuple(p for p in pending if p[0] > t) + (((t + 2, i.seen_w, i.writes),) if i.lat == 2 and i.writes else ())
  sched = tuple(s for s in sched if s[1] >= t)
  if i.op == "SFPLOADMACRO" and macros:
    x = _lowest_reg(i.writes)
    for unit, delay, l16 in loadmacro_units(macros.get(w >> 22 & 3, 0)):
      sched += ((unit, at := t + 1 + delay),)
      if unit != "store": live += ((at + (2 if unit == "mad" else 1), 0, 1 << (16 if l16 else x)),)
  return t - t0, hazard, (t, t + 1 if i.block else blocked, live, sched)

def sfpu_hazards(words: Sequence[int], macros: dict[int, int] | None = None) -> list[tuple[int, tuple]]:
  state, out = None, []
  for n, w in enumerate(words):
    _, hz, state = sfpu_cost(state, w, macros)
    if hz: out.append((n, hz))
  return out

def fix_sfpu_hazards(words: Sequence[int], macros: dict[int, int] | None = None, *, is_loop: bool = False) -> list[int]:
  nop, out, state, cfg_gap = isa.SFPNOP(), [], None, False
  for w in words:
    dec = sfpu_decode(w)
    if cfg_gap and dec is not None and dec.op != "SFPNOP":
      _, _, state = sfpu_cost(state, nop, macros)
      out.append(nop)
    _, hz, nxt = sfpu_cost(state, w, macros)
    if hz is not None:
      if hz[0] != "stale": raise SfpuError(f"SFPU hazard {hz} on {isa.decode(w)}")
      _, _, state = sfpu_cost(state, nop, macros)
      out.append(nop)
      _, hz, nxt = sfpu_cost(state, w, macros)
      if hz is not None: raise SfpuError(f"unresolvable SFPU hazard {hz} on {isa.decode(w)}")
    state = nxt
    out.append(w)
    cfg_gap = dec is not None and dec.op == "SFPCONFIG" and (w >> 4 & 15) in (*range(9), 15)  # macro or lane config
  if is_loop and out and sfpu_hazards(out + out, macros):
    out.append(nop)
    if hz := sfpu_hazards(out + out, macros): raise SfpuError(f"unresolvable SFPU loop wrap-around hazard: {hz}")
  return out

def verify_sfpu_words(words: Sequence[int], *, macros: dict[int, int] | None = None, is_loop: bool = False) -> None:
  stream = list(words) * (2 if is_loop else 1)
  if hz := sfpu_hazards(stream, macros):
    idx, err = hz[0]
    raise SfpuError(f"SFPU hazard at word {idx} ({isa.decode(stream[idx])}): {err}")
  for idx, w in enumerate(words):
    if (info := sfpu_decode(w)) is None: continue
    op = info.op
    if op not in ("SFPCONFIG", "SFPLOADMACRO", "SFPNOP"):
      vd = w >> 20 & 15 if op in ("SFPLOAD", "SFPLOADI", "SFPSTORE", "SFPLUT") else w >> 4 & 15
      if vd >= 12: raise SfpuError(f"word {idx} ({op}) has VD={vd} >= 12 (silent backdoor template write)")
    if op == "SFPSWAP":
      if (vd := w >> 4 & 15) >= 8: raise SfpuError(f"word {idx} (SFPSWAP) writes illegal VD register L{vd}")
    elif op != "SFPCONFIG" and (bad := info.writes & ~WRITABLE_LREGS):
      raise SfpuError(f"word {idx} ({op}) writes read-only/const register L{_lowest_reg(bad)}")

def disasm_sfpu(words: Sequence[int]) -> str:
  return "\n".join(f"{i:3d}: {dec!r}" if (dec := isa.decode(w)) else f"{i:3d}: 0x{w:08x}" for i, w in enumerate(words))
