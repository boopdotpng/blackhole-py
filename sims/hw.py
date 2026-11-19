"""Blackhole hardware facts for TTRV lowering and static timing analysis. DRAFT (scratch, not installed).

Every timing fact carries a provenance tag:
  DOC   tt-isa-documentation/BlackholeA0 states it (path given)
  MEAS  hardware measurement we can still reproduce (probe + date given)
  HINT  boop-docs number whose raw evidence is missing or whose method can't separate the effect: not trusted
  TODO  unknown; the analyzer must refuse to estimate (or bracket) code that depends on it

Cycle unit: AICLK, fixed at 1350 MHz by our firmware (fw/__init__.py AICLK_MHZ). Convert with ns = cycles / 1.35.
Convention: an op issued at t with latency L has its result readable at t + L; L=1 means the next instruction.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------- MMIO and firmware ABI (unchanged from ttrv/hw.py)

PRIVATE, CONFIG, FIFO = 0xFFB00000, 0xFFEF0000, 0xFFE40000
PC_BUFFER = 0xFFE80000
SYNC, MOP_SYNC, SEMAPHORE = PC_BUFFER + 4, PC_BUFFER + 8, PC_BUFFER + 32
UNPACK_CREDIT = SEMAPHORE + 5 * 4
STREAM = 0xFFB40000
NOC = {"brisc": 0xFFB20000, "ncrisc": 0xFFB30000}
CORE = {"x": 0x8A0, "y": 0x8A4, "id": 0x8A8}  # fw/abi.h WORKER_X/Y/ID
DEBUG_TIMESTAMP = 0xFFB121FC  # kperf/stamps.py: one store appends {token, u64 wall clock} to the L1 ring

AICLK_MHZ = 1350


def bases(role):
  """Center each base in its block so signed RV32 load/store offsets reach 4 KiB."""
  second = NOC.get(role, CONFIG if role == "trisc0" else PC_BUFFER)
  return {3: PRIVATE + 2048, 4: second + 2048} | ({5: PC_BUFFER + 2048} if role == "trisc0" else {})


@dataclass(frozen=True)
class T:
  value: object
  src: str  # "DOC" | "MEAS" | "HINT" | "TODO"
  ref: str = ""


ISA = "tt-isa-documentation/BlackholeA0/TensixTile/TensixCoprocessor/"

# ---------------------------------------------------------------- SFPU: issue, latency, stalls, hazards
#
# MEAS 2026-11-18, card 1 core (1,2), TRISC1, fusion on, prefetch 0x11F (old-firmware boot, same cfg0):
#   sims/probes/test_sfpu_matrix.py    -> results/2026-11-18-sfpu-matrix-card1.jsonl     46 producer x 70 consumer
#                                         variants: loop slope at gap 0 / 1 SFPNOP, and value correct vs wrong
#   sims/probes/test_sfpu_hazards.py   -> results/2026-11-18-sfpu-hazards-card{0,1}.jsonl
#   sims/probes/test_sfpu_loadmacro.py -> results/2026-11-18-sfpu-loadmacro-card1.jsonl
#   sims/probes/test_sfpu_dst.py       -> results/2026-11-18-sfpu-dst-card1.jsonl
# sims/test_sfpu_model.py replays every record through the code below and requires exact agreement.
#
# Rules (all MEAS; DOC where the ISA manual agrees):
#   * One SFPU instruction issues per cycle per thread stream. Every SFPU op has 1-cycle result latency except the
#     MAD column (MAD MUL ADD ADDI MULI MUL24 LUT LUTFP32): 2 cycles.
#   * SWAP (every mode) and SHFT2 modes 2,3,4 occupy two cycles: the next non-SFPNOP SFPU instruction waits one.
#   * A 2-cycle producer at t, consumer at t+1: the thread stalls 1 cycle iff the stall logic's view of the
#     consumer's reads (seen_r) meets the producer's seen writes. If the consumer really reads the register but the
#     stall logic does not see it, there is no stall and the consumer gets the OLD value (or garbage for half-word
#     writes). One instruction of any kind in between (SFPNOP, TTNOP, anything) fixes it.
#   * An SFPNOP costs 0 cycles if it sits in a cycle the thread would have stalled anyway, else 1.
#   * WAW (2-cycle producer then a 1-cycle writer of the same reg) needs nothing: final value is the later write.
#   * Values never depend on data: no SFPU timing difference was seen across operand values.

SFPU_ISSUE = T(1, "MEAS", "one SFPU instruction per cycle; loop control hidden by fusion (nop slope 1.000)")
SFPU_OPS = {0x7d: "ABS", 0x85: "ADD", 0x75: "ADDI", 0x7e: "AND", 0x99: "ARECIP", 0x90: "CAST", 0x8b: "COMPC",
            0x91: "CONFIG", 0x76: "DIVP2", 0x8a: "ENCC", 0x77: "EXEXP", 0x78: "EXMAN", 0x97: "GT", 0x79: "IADD",
            0x96: "LE", 0x70: "LOAD", 0x71: "LOADI", 0x93: "LOADMACRO", 0x73: "LUT", 0x95: "LUTFP32", 0x81: "LZ",
            0x84: "MAD", 0x7c: "MOV", 0x86: "MUL", 0x98: "MUL24", 0x74: "MULI", 0x8f: "NOP", 0x80: "NOT", 0x7f: "OR",
            0x88: "POPC", 0x87: "PUSHC", 0x7b: "SETCC", 0x82: "SETEXP", 0x83: "SETMAN", 0x89: "SETSGN", 0x7a: "SHFT",
            0x94: "SHFT2", 0x72: "STORE", 0x92: "SWAP", 0x8c: "TRANSP", 0x8d: "XOR", 0x8e: "STOCHRND"}
MAD_COLUMN = frozenset({"MAD", "MUL", "ADD", "ADDI", "MULI", "MUL24", "LUT", "LUTFP32"})
SFPU_LATENCY = {op: T(2 if op in MAD_COLUMN else 1, "MEAS", "matrix: every producer x 70 consumers")
                for op in SFPU_OPS.values() if op not in ("NOP", "LOADMACRO", "COMPC", "ENCC", "POPC", "PUSHC")}
# Ops measured only for issue rate (no LReg result): COMPC ENCC POPC PUSHC SETCC -> 1/cycle, DOC lane-flag semantics.
SFPU_BLOCKING = T({"SWAP": "all modes", "SHFT2": "modes 2,3,4"}, "MEAS", "next non-SFPNOP SFPU op waits 1 cycle")

# Undetected (no stall, stale read) cases. MEAS = observed wrong value at gap 0 and right at gap 1.
SFPU_UNDETECTED = {
  "IADD reg forms (mod1&1==0): VD read": "MEAS",
  "SHFT register-shift (mod1&1==0): VD read": "MEAS  (ISA says every SHFT form; the imm forms are detected)",
  "AND/OR USE_VB: VB read": "MEAS",
  "SETEXP/SETMAN/SETSGN without ARG_IMM: VD read": "MEAS",
  "ARECIP COND_RECIP: VB read": "MEAS",
  "SWAP modes != 0: VC/VD compare read": "MEAS  (mode 0 reads only in its 2nd cycle: no hazard, no stall)",
  "SHFT2 modes 2,3,4: VC (and L1-L3 for mode 2)": "MEAS",
  "SHFT2 modes 5,6: VB read": "MEAS",
  "CONFIG without IMM16_IS_VALUE: L0 read": "MEAS (LReg[12] destination)",
  "LOADI mod0 8/10, LOAD mod0 14/15 half writes": "MEAS: whole LReg corrupted, not only the preserved half",
}
# Extra stalls the stall logic invents (cost cycles, never values):
SFPU_CONSERVATIVE = {
  "LUTFP32 Mod1Mirror INDIRECT_VD": "MEAS: treated as writing every LReg -> next reader of anything stalls",
  "LUTFP32 (mirror clear)": "DOC/MEAS: treated as reading every LReg but L7",
  "STOCHRND without UseImm5": "MEAS: VB treated as read in every mode (FP modes too) -> stalls after a MAD to VB",
  "MAD-column INDIRECT_VA / INDIRECT_VD": "DOC: reads / writes every LReg",
}

ALL_LREGS = frozenset(range(16))
LREGS = frozenset(range(8))


@dataclass(frozen=True)
class SfpuInsn:
  op: str
  reads: frozenset   # LRegs read at issue
  writes: frozenset
  seen_r: frozenset  # what the stall logic believes it reads
  seen_w: frozenset  # what the stall logic believes a 2-cycle op writes
  lat: int
  block: int         # 1: next cycle accepts only SFPNOP
  unit: str          # load / simple / mad / round / store (SFPLOADMACRO sub-unit columns)


SUBUNIT = {**{op: "simple" for op in ("ABS", "AND", "ARECIP", "CAST", "COMPC", "CONFIG", "DIVP2", "ENCC", "EXEXP",
                                       "EXMAN", "GT", "IADD", "LE", "LZ", "MOV", "NOT", "OR", "POPC", "PUSHC", "SETCC",
                                       "SETEXP", "SETMAN", "SETSGN", "SHFT", "SWAP", "TRANSP", "XOR")},
           **{op: "mad" for op in MAD_COLUMN}, "SHFT2": "round", "STOCHRND": "round", "STORE": "store",
           "LOAD": "load", "LOADI": "load", "LOADMACRO": "load", "NOP": "load"}


def sfpu_decode(w):
  """SfpuInsn for an unrotated Tensix word, or None if it is not an SFPU instruction."""
  op = SFPU_OPS.get(w >> 24)
  if op is None: return None
  vd, vc, vb, va, mod = w >> 4 & 15, w >> 8 & 15, w >> 12 & 15, w >> 16 & 15, w & 15
  ld_vd, mod0 = w >> 20 & 15, w >> 16 & 15
  f = frozenset
  r = s = wr = f()
  seen_w = None
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
    mirror = w >> 16 & 15
    r, wr = f(range(7)), f({vd})
    s = ALL_LREGS if mirror & 8 else ALL_LREGS - {7}
    if mirror & 8: seen_w = ALL_LREGS
  elif op in ("MOV", "ABS", "NOT", "LZ", "EXEXP", "EXMAN", "CAST", "DIVP2"):
    r = s = f({vc})
    wr = f({vd})
  elif op == "IADD":
    r, s, wr = (f({vc}) if mod & 1 else f({vc, vd})), f({vc}), f({vd})
  elif op == "SHFT":
    r = f({vc}) if mod & 5 == 5 else f({vd}) if mod & 1 else f({vc, vd})
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
    r = f({vc}) | (f({vb}) if mod & 7 in (4, 5) and not mod & 8 else f())
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
    wr = f({ld_vd & 3 | (w & 1) << 2})
  if seen_w is None: seen_w = wr if lat == 2 else f()
  return SfpuInsn(op, r, wr, s, seen_w, lat, block, SUBUNIT[op])


def sfpu_cost(prev, w, macros=None):
  """Issue one Tensix word of a thread's stream.

  prev: state returned by the previous call (None at start).
  macros: {slot: Sequence word} as configured with SFPCONFIG 4..7, needed only to track SFPLOADMACRO schedules.
  Returns (stall_cycles, hazard_or_None, new_state). Non-SFPU words cost one issue slot and are a valid gap.
  hazard: ("stale", reg) a read the stall logic misses, or ("dropped", subunit) a regular instruction discarded
  because an SFPLOADMACRO-scheduled one executes on the same sub-unit that cycle."""
  t_prev, blocked, pending, sched = prev or (-10, -10, (), ())
  t = t_prev + 1
  i = sfpu_decode(w)
  if i is None or i.op == "NOP":
    return 0, None, (t, blocked, tuple(p for p in pending if p[0] > t), tuple(s for s in sched if s[1] >= t))
  t0 = t
  while t == blocked or any(ready > t and seen & i.seen_r for ready, seen, _ in pending):
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
    for unit, delay, l16 in loadmacro_units(macros.get(w >> 22 & 3, 0)):
      at = t + 1 + delay
      sched += ((unit, at),)
      if unit != "store":
        live += ((at + (2 if unit == "mad" else 1), frozenset(), frozenset({16 if l16 else x})),)
  return t - t0, hazard, (t, t + 1 if i.block else blocked, live, sched)


def sfpu_cycles(words, repeat=1, macros=None):
  """Cycles from the first issue to the last issue (inclusive) of `words` repeated `repeat` times."""
  state, start = None, None
  for _ in range(repeat):
    for w in words:
      _, _, state = sfpu_cost(state, w, macros)
      if start is None: start = state[0]
  return state[0] - start + 1


def sfpu_slope(words, macros=None):
  """Steady-state cycles per repetition of `words`: the quantity the loop probes measure."""
  return (sfpu_cycles(words, 64, macros) - sfpu_cycles(words, 32, macros)) / 32


def sfpu_hazards(words, macros=None):
  """[(index, hazard)] for every stale read or dropped instruction in a straight-line stream."""
  state, out = None, []
  for n, w in enumerate(words):
    _, hz, state = sfpu_cost(state, w, macros)
    if hz: out.append((n, hz))
  return out


# ---------------------------------------------------------------- SFPLOADMACRO

LOADMACRO = {
  "issue": T(1, "MEAS", "one SFPLOADMACRO per cycle with 0..4 sub-units scheduled (5 SFPU ops/cycle); "
                        "a regular op between two macros costs its own cycle and nothing more"),
  "exec_cycle": T("t + 1 + delay", "MEAS", "simple delay 0-3, mad delay 0-2 (DOC agrees)"),
  "visible_simple": T("t + 2 + delay", "MEAS"),
  "visible_mad": T("t + 3 + delay", "MEAS", "no automatic stall: regular readers before that see the old value"),
  "same_subunit_collision": T("regular instruction silently dropped, no stall", "MEAS", "simple, mad, store (DOC agrees)"),
  "other_subunit_same_cycle": T("both execute", "MEAS"),
  "config_then_macro": T("SFPNOP between SFPCONFIG of Sequence/Misc/Template and the next SFPLOADMACRO", "DOC"),
  "config_then_backdoor": T("SFPNOP between SFPCONFIG of a template and a VD>=12 backdoor write", "DOC"),
  "swap_in_simple": T("MAD sub-unit idle that cycle, simple+round idle the next", "DOC"),
  "shft2_subvec_in_round": T(">=1 idle cycle after, else UndefinedBehavior", "DOC"),
  "delay_kind_elapsed_instructions": T(None, "TODO", "Misc.UnitDelayKind bits not probed; model assumes cycles"),
}


def loadmacro_units(sequence):
  """[(unit, delay, writes_l16)] scheduled by one SFPLOADMACRO for a Sequence word (8 bits per sub-unit)."""
  out = []
  for n, unit in enumerate(("simple", "mad", "round", "store")):
    b = sequence >> 8 * n & 0xFF
    if b & 7: out.append((unit, b >> 3 & 7, bool(b & 0x40)))
  return out


# ---------------------------------------------------------------- SFPU <-> Dst, FPU

FPU_LATENCY = T(5, "DOC", "FPU arithmetic result latency; 1 instr/cycle issue")
# MEAS 2026-11-18 (results/2026-11-18-sfpu-dst-card1.jsonl, ELWMUL into FP32 Dst, one thread): the ISA's ">=3
# unrelated instructions between an FPU Dst write and an SFPLOAD of it" is not needed for correctness here. An
# SFPLOAD right after ELWMUL reads the new value; the hardware interlocks on the Dst half (tiles 0-3 | 4-7 in FP32).
FPU_TO_SFPLOAD_GAP = T(0, "MEAS", "interlocked; ISA asks for 3. Only ELWMUL/FP32/single thread probed")
# Steady cycles per (ELWMUL + one SFPU Dst access), b pairs batched as b FPU then b SFPU instructions, one thread.
# SFPLOAD and SFPSTORE identical; same rows and different rows of the same half identical.
DST_HALF_SAME = T({1: 8.0, 2: 8.0, 4: 5.0, 8: 3.5, 16: 2.75}, "MEAS", "per pair; = (2b + 12) / b for b >= 2, 8 at b = 1")
DST_HALF_OTHER = T(2.0, "MEAS", "per pair at every batch size: no penalty, one issue each")
DST_SFPU_NO_DST = T(2.0, "MEAS", "ELWMUL + register-only SFPMAD: no penalty")
DST_GAP_INSNS = T({"TTNOP": 0.0, "SFPNOP": 0.5}, "MEAS", "extra cycles per gap instruction inside a same-half b=1 pair")


def dst_half_pair_cycles(b, same_half):
  """Cycles for b ELWMUL followed by b SFPLOAD/SFPSTORE (one thread) in a steady loop."""
  if not same_half: return 2.0 * b
  return 8.0 if b == 1 else 2.0 * b + 12
# TODO: two threads (boop-docs HINT: 2 same half / 1 other), MVMUL and other FPU ops, 16-bit Dst half boundary,
#       SFPU -> FPU direction in isolation, SFPNOP's 0.5-cycle effect, SFPLOADMACRO on a half the FPU is using.

# ---------------------------------------------------------------- Tensix frontend (instruction delivery)

FRONTEND = {
  "fifo": T((32, 28), "DOC", "capacity 32, backpressure above 28"),
  "dequeue": T(1, "DOC", "1 instruction/thread/cycle"),
  "fusion": T(4, "DOC", ".ttinsn fusion: up to 4 enqueued per RISC cycle. ON for TRISCs in both firmwares"),
  "loop_overhead_hidden": T(True, "MEAS", "16x SFPNOP + addi/bne loop = 1.000/op with fusion on (not 1.125)"),
  "mop_transition": T(1, "HINT", "MOP->non-MOP transition 1 cycle where not hidden"),
}
# cfg0 (CSR 0x7c0) as set by blackhole-py/fw/hw.h configure_csr: bit 3 DisLowCash SET (L0 data cache off, all roles),
# bit 18 DisTriscCache CLEAR on TRISCs (fusion on), SET on BRISC/NCRISC, bit 2 DisIcPrefetch clear.
# The analyzer assumes this config (fusion on, prefetch on). The L0 data cache is a separate question (see RISCV).

# ---------------------------------------------------------------- instruction cache (always on; only prefetch is configurable)

ICACHE = {
  "prefetch_ctrl": T(0x11F, "DOC", "blackhole-py fw/hw.h: Tensix cfg reg 208, all five RISCs, max 8 in flight; not writable by NCRISC"),
  "invalidated_per_launch": T(True, "DOC", "fw invalidate_icache(); every kernel starts cold"),
  # MEAS 2026-11-18, all five roles, straight-line loop body of N insns, prefetch on:
  "steady_per_insn": T({"N<=128": 1.00, "160": 1.025, "256": 1.016, "480-512": 1.007, "1024": 1.03}, "MEAS",
                       "same knee on every role incl. BRISC, so the WH 2 KiB/512 B capacity table is not what we see"),
  "cold_first_pass": T("~35 + ~0.17*N cycles", "MEAS", "fit to first-pass excess; +-15 cycle scatter"),
  "launch_jitter": T(0.015, "MEAS", "RISC-fetch-bound loops vary up to ~1.5% launch to launch; SFPU-bound loops <0.1%"),
}
# TODO: knee mechanism (capacity vs prefetch window); branchy code (only straight-line loops measured);
#       contention with NoC/unpack traffic on the L1 port that fetch uses.

# ---------------------------------------------------------------- RISC-V (all five roles identical: MEAS 2026-09-09)

RISCV = {
  "alu": T(1, "MEAS"), "mul": T(2, "MEAS"), "div": T((2, 33), "MEAS", "2 for /1, 33 for 0xffffffff/3; operand dependent"),
  "fpu": T(2, "MEAS", "fadd/fmul/fmadd dependent chain"), "branch_taken_ok": T(1, "DOC"),
  "mispredict": T(4, "DOC", "+fetch miss possible"), "csr": T(4, "MEAS"), "fence_empty": T(4, "MEAS"),
  "load_local": T(2, "DOC"), "load_l1": T(8, "MEAS", "dependent chain, L0 off"), "store": T(1, "MEAS"),
}
# TODO: branch predictor model (what's predicted?); MMIO load/store latency to CONFIG/PC_BUFFER/NOC regs;
#       load latency under L1 bank contention from NoC/unpack; I-cache/fetch from L1.

# ---------------------------------------------------------------- Tensix scalar / config / sync

SCALAR = {
  "dmareg_alu": T((3, 4), "MEAS", "3 same 4-GPR bank or imm, 4 cross bank; issuing thread blocked"),
  "SETDMAREG": T(1, "MEAS"), "DMANOP": T(1, "MEAS"), "NOP": T(1, "MEAS"),
  "SETC16": T(1, "DOC"), "WRCFG": T((1, 2), "DOC", "issue 1, latency 2"), "RMWCIB": T(1, "DOC"),
  "CFGSHIFTMASK": T((2, 2), "DOC"), "sem_op": T(1, "DOC", "uncontended"),
}

# ---------------------------------------------------------------- unpack / pack / NoC: mostly unknown

UNPACK = {"addr_calc": T(2, "DOC"), "rate_bytes_per_cycle": T((16, 32, 64), "DOC", "x1/x2/x4; two unpackers interfere"),
          "tile_cycles": T(None, "TODO", "per format/tile shape; this dominates matmul kernels")}
PACK = {"admission": T(1, "DOC", "<=1 command start/cycle"), "tile_cycles": T(None, "TODO")}
NOC_COST = {
  "read_2k_depth1": T(7309 / 32, "HINT", "noc-output-and-drisc-dma.md: 65536 B in 7309 cycles = ~228 cyc/2 KiB"),
  "write_2k_depth1": T(3998 / 32, "HINT", "same doc"),
  "issue": T(None, "TODO", "cycles to program one NOC_CMD (register writes) per role"),
  "latency_by_hops": T(None, "TODO", "unloaded latency vs Manhattan hops, both NoCs"),
  "dram": T(None, "TODO", "per-bank bandwidth/latency; contention model across 88 workers"),
  "multicast": T(None, "TODO"),
  "atomic": T(None, "TODO"),
}
