"""Matrix unit (FPU) timing probes (k_fpu.c, fpu.h). See FPU.md for the plan, hypotheses and risks.

  python3 sims/probes/run.py --device 1 --output sims/results/<date>-fpu-card1.jsonl fpu [-k mvmul]
  python3 sims/probes/fpu.py --list                 # case ids by group
  python3 sims/probes/fpu.py --build                # compile every image (no card)
  python3 sims/probes/fpu.py --disasm <id>          # timed loop of a case, Tensix words decoded

Every case runs one launch on TILE. Each role runs k_fpu.c: a setup program (L1 records, interpreted by the
kernel), then for each iteration count in COUNTS, SAMPLES timed runs of `repeat n { BODY }` closed by a bounded
fence (the first sample per count is warmup), then a check program that zeroes the accumulator rows, runs the body
CHECK_ITERS times and reads Dst back through the RISC window (0xFFBD8000). A small functional model below predicts
the read-back values; `check` is 'ok', 'MISMATCH' or 'none' (no prediction) and never fails the run.

Src operands never come from the unpacker probes: UNPACR_NOP(zero, set dvalid) gives each bank to the matrix unit
(old hardware-verified recipe), the RISC writes A and B values into Dst rows 512..639 (16-bit view), and
MOVD2A/MOVD2B copy them into SrcA/SrcB. The timed region sees only the body words.
"""
import argparse, struct, subprocess, sys, tempfile
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(HERE), str(ROOT)):
  if p not in sys.path: sys.path.insert(0, p)
from ttrv import isa  # noqa: E402
from tile import LAYOUT, build  # noqa: E402

TILE = (1, 2)
COUNTS = (64, 128, 256)
SAMPLES = 8          # 1 warmup + 7 measured per count
CHECK_ITERS = 2
SEM = {"trisc0": 4, "trisc1": 6, "trisc2": 3}
BARRIER, FLAGS = 0x4F000, 0x4F100  # two-thread rendezvous / handoff words (free L1 below the trisc0 area)
SITES = {1: "fence", 2: "barrier"}

# formats (ALU_FORMAT_SPEC codes)
FP32, FP16, BF16, BFP8, BFP4, FP8 = 0, 1, 5, 6, 7, 10  # FP8 = Lf8 code used for e4m3 (TileDescriptor 0x1A & 0xF)
FP16_STYLE = {FP16, FP8}
FMT_NAME = {BF16: "bf16", BFP8: "bfp8", BFP4: "bfp4", FP8: "fp8"}
A_ROW, B_ROW = 512, 576  # Dst16b rows holding the A / B operand rows (upper half)
ACC_ROWS = 128           # accumulator rows zeroed before timing and before the check

OP = dict(PUSH=1, CFG=2, MOPCFG=3, FENCE=4, MOPSYNC=5, DST32=6, DST16=7, DSTRAND16=8, READ32=9, READ16=10, RUN=11,
          STAMP=12, FLAG=13, WAITFLAG=14, DELAY=15)


class Prog:
  """Setup / check program for k_fpu.c: records {op, a, b, c}."""
  def __init__(self): self.recs, self.reads = [], []
  def _(self, op, a=0, b=0, c=0): self.recs.append((OP[op], a & 0xFFFFFFFF, b & 0xFFFFFFFF, c & 0xFFFFFFFF)); return self
  def push(self, *ws):
    for w in ws: self._("PUSH", w)
    return self
  def cfg(self, word, mask, value): return self._("CFG", word, mask, value)
  def mopcfg(self, words):
    self._("MOPSYNC")
    for i, w in enumerate(words): self._("MOPCFG", i, w)
    return self
  def fence(self): return self._("FENCE")
  def dst32(self, row, n, bits): return self._("DST32", row, n, bits)
  def dst16(self, row, n, bits): return self._("DST16", row, n, bits)
  def rand16(self, row, n, seed): return self._("DSTRAND16", row, n, seed)
  def read32(self, row, col): self.reads.append((row, col, 32)); return self._("READ32", row, col)
  def read16(self, row, col): self.reads.append((row, col, 16)); return self._("READ16", row, col)
  def run(self, n): return self._("RUN", n)
  def stamp(self): return self._("STAMP")
  def flag(self, addr, v): return self._("FLAG", addr, v)
  def waitflag(self, addr, v): return self._("WAITFLAG", addr, v)
  def delay(self, cycles): return self._("DELAY", cycles)
  def blob(self): return b"".join(struct.pack("<4I", *r) for r in self.recs)


# ---------------------------------------------------------------- encodings

def f32bits(x): return struct.unpack("<I", struct.pack("<f", x))[0]
def bits_f32(b): return struct.unpack("<f", struct.pack("<I", b))[0]
def bf16bits(x): return f32bits(x) >> 16  # values used here are exact in bf16
def fp16bits(x): return struct.unpack("<H", struct.pack("<e", x))[0]


def setc16(reg, v): return isa.SETC16(reg, v)
def ab(a_incr=0, a_cr=0, a_clr=0, b_incr=0, b_cr=0, b_clr=0):
  return a_incr | a_cr << 6 | a_clr << 7 | b_incr << 8 | b_cr << 14 | b_clr << 15
def dstm(incr=0, cr=0, clr=0, c2cr=0, fid_incr=0, fid_clr=0):
  return incr | cr << 10 | clr << 11 | c2cr << 12 | fid_incr << 13 | fid_clr << 15

# Address modifiers every case gets unless it overrides them: (AB, DST) per slot.
ADDR_MODS = {0: (0, 0), 1: (0, dstm(incr=8)), 2: (0, dstm(clr=1)), 3: (0, dstm(fid_incr=1)), 4: (0, dstm(fid_clr=1)),
             5: (0, 0), 6: (0, 0), 7: (0, 0)}
AM_D8, AM_DCLR, AM_FID, AM_FIDCLR = 1, 2, 3, 4

NOP = isa.NOP()
def UNP_GIVE(u):
  """Zero the unpacker's current bank and give it to the matrix unit. WaitLikeUnpacr (Stall_Clr_Cntrl) set: wait for
  the unpacker's own bank (BH UNPACR_NOP.md); with it clear the wait is on the matrix unit's bank, which deadlocks
  when the second bank is given while the matrix unit owns the first."""
  return isa.UNPACR_NOP(Unpacker_Select=u, Set_Dvalid=1, Stall_Clr_Cntrl=1, Unpack_Pop=1)
def SETRWC_ALL(): return isa.SETRWC(BitMask=0xF)
def SETRWC_D0(): return isa.SETRWC(BitMask=4)
def FLIP(release=3): return isa.SETRWC(clear_ab_vld=release)
def STALL(stall, wait): return isa.STALLWAIT(stall, wait)
def MV(row, am=0, flip=0): return isa.MVMUL(clear_dvalid=flip, addr_mode=am, dst=row)


# ---------------------------------------------------------------- setup programs

def math_setup(fmt=BF16, dst32=True, a=1.0, b=1.0, *, banks=1, data="const", addr_mods=None, keep_flip=False,
               role="trisc1", extra=None, lregs=()):
  """Config, Src banks with A/B data, accumulators zeroed. Leaves RWCs at 0 and the thread fenced.

  keep_flip: leave CLR_DVALID_SrcA/B_Disable set, so SETRWC/MVMUL bank flips keep both banks with the matrix unit."""
  fp16 = fmt in FP16_STYLE
  sec = int(role[-1])
  fill_fmt = 2 if fp16 else 3      # RISC_DEST_ACCESS fmt for the 16-bit fill: fp16 / bf16
  acc16 = FP16 if fp16 else BF16    # what a 16-bit Dst holds for this Src style
  enc = fp16bits if fp16 else bf16bits
  p = Prog().fence()
  p.cfg(0, 0x3FF, fmt | 1 << 4 | fmt << 5 | 1 << 9)                       # ALU_FORMAT_SPEC_REG Src A/B val+override
  p.cfg(1, 0xFFFE0000, fmt << 17 | fmt << 21 | acc16 << 25 | 1 << 30)       # REG0/1/2, 16-bit Dst, SFPU fp32
  p.cfg(72, 0xF, fmt).cfg(120, 0xF, fmt)                                    # unpacker out formats (implied fmt)
  p.cfg(2, 0x2, 0x2)  # Zero_Flag_disabled_dst: MOVD2A/B read the RISC-written rows even if their valid bits are clear
  p.cfg(3, 7 << (16 + 5 * sec), fill_fmt << (16 + 5 * sec))                 # this thread's RISC Dst window
  p.push(setc16(2, 1), setc16(3, 1), setc16(7, 0))                          # use configured formats; flips release
  if data == "const":
    p.dst16(A_ROW, 64, enc(a)).dst16(B_ROW, 64, enc(b))
  elif data == "rand":
    hi = 0x3C00 if fp16 else 0x3F00
    p.rand16(A_ROW, 64, hi << 16 | 0x1234).rand16(B_ROW, 64, hi << 16 | 0x5678)
  for _ in range(banks): p.push(UNP_GIVE(0), UNP_GIVE(1))
  p.push(STALL(isa.Stall.MATH, isa.Wait.SRCA_VLD | isa.Wait.SRCB_VLD))
  mov = [isa.MOVD2A(src=4 * i, instr_mod=2, dst=A_ROW + 4 * i) for i in range(16)] + \
        [isa.MOVD2B(src=4 * i, instr_mod=2, dst=B_ROW + 4 * i) for i in range(16)]
  if data != "zero":
    p.push(mov[0], *mov)  # the first move after the Zero_Flag change may still use the old setting (ZEROACC.md)
    if banks == 2:
      p.push(setc16(7, 3), FLIP(3), STALL(isa.Stall.MATH, isa.Wait.SRCA_VLD | isa.Wait.SRCB_VLD), *mov, FLIP(3))
      if not keep_flip: p.push(setc16(7, 0))
  elif keep_flip:
    p.push(setc16(7, 3))
  p.fence()
  p.cfg(2, 0x2, 0)
  p.cfg(1, 0xFFFE0000, fmt << 17 | fmt << 21 | (0 if dst32 else acc16) << 25 | int(dst32) << 29 | 1 << 30)
  p.cfg(3, 7 << (16 + 5 * sec), (0 if dst32 else fill_fmt) << (16 + 5 * sec))
  mods = {**ADDR_MODS, **(addr_mods or {})}
  for i, (abv, dv) in mods.items(): p.push(setc16(12 + i, abv), setc16(28 + i, dv), setc16(47 + i, 0))
  p.push(setc16(11, 0), SETRWC_ALL())
  for reg, bits16 in lregs: p.push(isa.SFPLOADI(lreg_ind=reg, instr_mod0=0, imm16=bits16))
  zero_acc(p, dst32)
  if extra: extra(p)
  return p.fence()


def zero_acc(p, dst32):
  (p.dst32 if dst32 else p.dst16)(0, ACC_ROWS, 0)


def load_replay(p, start, words):
  """REPLAY load (Load=1, Exec=0) pushed with plain sw (the interpreter), never fused .ttinsn (PushTensixInstruction.md)."""
  p.push(isa.REPLAY(start_idx=start, len=len(words), load_mode=1), *words)


def mop1(outer=1, inner=1, start=NOP, end0=NOP, end1=NOP, loop=NOP, loop1=NOP, last=None, last1=None):
  return [outer, inner, start, end0, end1, loop, loop1, loop if last is None else last, loop if last1 is None else last1]


def expand_mop(cfg):
  outer, inner, start, end0, end1, loop, loop1, last0, last1 = cfg
  out, flip = [], 0 if loop1 == NOP else loop ^ loop1
  if flip: inner *= 2
  for j in range(outer):
    if start != NOP: out.append(start)
    op = loop
    for i in range(inner):
      out.append(op if i != inner - 1 else (last1 if j != outer - 1 else last0))
      op ^= flip
    if end0 != NOP:
      out.append(end0)
      if end1 != NOP: out.append(end1)
  return out


# ---------------------------------------------------------------- functional model (expected Dst values)

def fid_bits(x, phase, src):
  """SrcAFidelityBits / SrcBFidelityBits (MatrixUnit.md)."""
  u = f32bits(x)
  if src == "a": return bits_f32(u & 0xFFF80000) if phase & 1 == 0 else x - bits_f32(u & 0xFFF83FFF)
  return bits_f32(u & 0xFFFE0000) if phase & 2 == 0 else x - bits_f32(u & 0xFFFE1FFF)


def prod(a, b, phase): return fid_bits(a, phase, "a") * fid_bits(b, phase, "b")


def f32(x): return bits_f32(f32bits(x))


class Model:
  """Dst rows as floats (None = unknown). Constant A and B everywhere, so a row is one value."""
  def __init__(self, a, b, mods, dst32=True):
    self.a, self.b, self.mods, self.dst32 = a, b, mods, dst32
    self.rows = {r: 0.0 for r in range(ACC_ROWS)}
    self.d = self.dcr = self.fid = 0
    self.replay, self.mop, self.l0 = [], None, None

  def am(self, i):
    _, dv = self.mods[i]
    incr, cr, clr, c2cr, fi, fc = dv & 0x3FF, dv >> 10 & 1, dv >> 11 & 1, dv >> 12 & 1, dv >> 13 & 3, dv >> 15 & 1
    if clr: self.d = self.dcr = 0
    elif c2cr: self.d += incr; self.dcr = self.d
    elif cr: self.dcr += incr; self.d = self.dcr
    else: self.d += incr
    self.d &= 0x3FF; self.dcr &= 0x3FF
    self.fid = 0 if fc else (self.fid + fi) & 3

  def acc(self, base, n, inc, assign=False):
    for r in range(base, base + n):
      old = self.rows.get(r)
      self.rows[r] = None if (old is None and not assign) or inc is None else f32(inc if assign else old + inc)

  def step(self, w):
    name, f = isa.tensix_decode(w)
    a, b = self.a, self.b
    if name == "REPLAY":
      if f["load_mode"]: raise ValueError("replay load inside a body")
      for x in self.replay[f["start_idx"]:f["start_idx"] + f["len"]]: self.step(x)
      return
    if name == "MOP":
      for x in expand_mop(self.mop): self.step(x)
      return
    if name == "SFPLOAD" and f["lreg_ind"] == 0:
      self.l0 = self.rows.get(f["dest_reg_addr"] & ~3)
    if name == "SETRWC":
      if f["BitMask"] & 4: self.d = self.dcr = f["rwc_d"]
      if f["BitMask"] & 8: self.fid = 0
      return
    if name == "INCRWC":
      self.d = (self.d + f["rwc_d"]) & 0x3FF
      return
    row = (f.get("dst", 0) + self.d) & 0x3FF
    if name == "MVMUL": self.acc(row & ~7, 8, 16 * prod(a, b, self.fid))
    elif name == "GAPOOL": self.acc(row & ~3, 4, 16 * prod(a, b, self.fid))
    elif name == "ELWMUL": self.acc(row & ~7, 8, prod(a, b, self.fid))
    elif name in ("ELWADD", "ELWSUB"):
      v = a + b if name == "ELWADD" else a - b
      self.acc(row & ~7, 8, v, assign=not f["dest_accum_en"])
    elif name == "GMPOOL":
      r0 = row & ~3
      scale = 2.0 ** (f32bits(b) >> 23 & 0xFF) / 2.0 ** 127
      old = self.rows.get(r0)
      self.rows[r0] = None if old is None else max(old, a * scale)
      for r in range(r0 + 1, r0 + 4): self.rows[r] = 0.0
    elif name == "MOVA2D":
      n = 8 if f["instr_mod"] == 2 else 1
      self.acc(row & ~(n - 1), n, a, assign=True)
    elif name == "MOVB2D":
      m = f["movb2d_instr_mod"]
      n = 4 if m & 4 else 8 if m & 2 else 1
      self.acc(row & ~(n - 1), n, b, assign=True)
    elif name == "ZEROACC":
      for r in range(ACC_ROWS): self.rows[r] = None
    elif name in ("NOP", "MOVD2A", "MOVD2B", "MOVB2A", "ZEROSRC", "STALLWAIT") or name.startswith("SFP") or name == "UNPACR_NOP":
      pass
    else: raise ValueError(f"model: {name}")
    if name == "SFPSTORE": raise ValueError("model: SFPSTORE in a modelled body")
    if name == "MVMUL" and f["clear_dvalid"]: pass  # bank flips keep both banks (keep_flip) in modelled cases
    am = f.get("addr_mode", f.get("pool_addr_mode", 0))
    if not name.startswith("SFP") and name not in ("NOP", "STALLWAIT", "UNPACR_NOP", "ZEROSRC"): self.am(am & 7)


# ---------------------------------------------------------------- case building

def rot(make, n=8, length=16): return [make(8 * (i % n)) for i in range(length)]

SPECS = {}


def case(cid, group, roles, unit, note="", **meta):
  """roles: {role: dict(body=[words], prog=Prog, check=Prog|None, model=callable|None)}."""
  SPECS[cid] = roles
  return dict(id=cid, group=group, unit=unit, note=note, tiles=[TILE], **meta)


def mathcase(cid, group, body, *, unit=None, fmt=BF16, dst32=True, a=None, b=None, banks=1, data="const",
             addr_mods=None, keep_flip=False, extra=None, model=True, replay=None, mop=None, lregs=(), check_extra=None,
             want=None, note="", hw="", expect=None):
  """Single-thread case on trisc1. unit = counted operations per loop iteration (default: body length)."""
  if a is None: a, b = default_ab(fmt, dst32)
  mods = {**ADDR_MODS, **(addr_mods or {})}
  def ext(p):
    if replay: load_replay(p, 0, replay)
    if mop: p.mopcfg(mop)
    if extra: extra(p)
  prog = math_setup(fmt, dst32, a, b, banks=banks, data=data, addr_mods=addr_mods, keep_flip=keep_flip, extra=ext,
                    lregs=lregs)
  chk = Prog().fence()
  zero_acc(chk, dst32)
  chk.push(SETRWC_ALL()).run(CHECK_ITERS).fence()
  if check_extra: check_extra(chk)
  predict = None
  if model and data == "const":
    def predict():
      m = Model(a, b, mods, dst32)
      m.replay, m.mop = list(replay or []), mop
      for _ in range(CHECK_ITERS):
        for w in body: m.step(w)
      return {**m.rows, **({256: m.l0} if m.l0 is not None else {})}
  elif want:
    predict = lambda: want(a, b)  # noqa: E731
  for r in READ_ROWS:
    (chk.read32 if dst32 else chk.read16)(r, 0)
    (chk.read32 if dst32 else chk.read16)(r, 15)
  roles = {"trisc1": dict(body=body, prog=prog, check=chk, predict=predict, dst32=dst32, fp16=fmt in FP16_STYLE)}
  return case(cid, group, roles, unit or len(body), note=note, fmt=FMT_NAME.get(fmt, fmt), dst="fp32" if dst32 else
              ("fp16" if fmt in FP16_STYLE else "bf16"), hw=hw, expect=expect)


READ_ROWS = list(range(0, ACC_ROWS, 8))


def touched(body, replay=None):
  """Distinct 8-row block starts the body writes (for read-back): from dst fields, ignoring RWCs."""
  out = []
  for w in [*body, *(replay or [])]:
    d = isa.tensix_decode(w)
    if d and d[0] in ("MVMUL", "ELWMUL", "ELWADD", "ELWSUB", "GAPOOL", "GMPOOL", "MOVA2D", "MOVB2D") and "dst" in d[1]:
      r = d[1]["dst"] & ~3 if d[0] in ("GAPOOL", "GMPOOL") else d[1]["dst"] & ~7
      if r < ACC_ROWS and r not in out: out.append(r)
  return out or [0, 8, 16, 24]


def default_ab(fmt, dst32):
  if fmt == BF16: return 1 + 2 ** -5, 1 + 2 ** -7   # phase 1 bits in A, phase 2 bits in B: fidelity is visible
  if fmt in FP16_STYLE: return (1.125, 1.25) if dst32 else (0.125, 0.125)  # e4m3-exact; small for an fp16 Dst
  return 1.5, 1.25                                   # bfp8 / bfp4: few mantissa bits


def fidelity_body(op, n, inner):
  """n fidelity phases over 8 blocks. inner: phases back to back on one block (dependent); else phase-outer."""
  out = []
  if inner:
    for blk in range(8):
      for ph in range(n): out.append(op(8 * blk, AM_FIDCLR if ph == n - 1 else AM_FID))
  else:
    for ph in range(n):
      for blk in range(8):
        last = blk == 7
        out.append(op(8 * blk, (AM_FIDCLR if ph == n - 1 else AM_FID) if last else 0))
  return out


def _cases():
  C = []
  mv = lambda r, am=0: MV(r, am)  # noqa: E731
  # ---------------- throughput: independent 8x16 blocks rotating over 8 (no Dst RAW), direct push
  for fmt in (BF16, BFP8, BFP4, FP8):
    C.append(mathcase(f"tput-mvmul-lofi-{FMT_NAME[fmt]}-dst32", "tput", rot(mv), fmt=fmt, hw="FPU_LATENCY issue",
                      expect="1.0/op (DOC MatrixUnit.md; compute-only peak 1.0 fp16 HINT)"))
  C.append(mathcase("tput-mvmul-lofi-fp8-dst16", "tput", rot(mv), fmt=FP8, dst32=False, expect="1.0/op"))
  for n in (2, 3, 4):
    C.append(mathcase(f"tput-mvmul-hifi{n}-outer-bf16-dst32", "tput", fidelity_body(mv, n, False), expect="1.0/op",
                      note="fidelity loop outer, Dst blocks inner (Dst.md recommendation)"))
    C.append(mathcase(f"dep-mvmul-hifi{n}-inner-bf16-dst32", "dep", fidelity_body(mv, n, True),
                      expect="~5-6/op if each phase waits for the previous (Dst.md: 5-cycle block hazard)",
                      note="fidelity phases back to back on the same block"))
  el = lambda r, am=0: isa.ELWMUL(addr_mode=am, dst=r)  # noqa: E731
  C.append(mathcase("tput-elwmul-lofi-bf16-dst32", "tput", rot(el), expect="1.0/op"))
  C.append(mathcase("tput-elwmul-hifi2-outer-bf16-dst32", "tput", fidelity_body(el, 2, False), expect="1.0/op"))
  C.append(mathcase("tput-elwmul-lofi-fp8-dst32", "tput", rot(el), fmt=FP8, expect="1.0/op"))
  ea = lambda acc: (lambda r, am=0: isa.ELWADD(dest_accum_en=acc, addr_mode=am, dst=r))  # noqa: E731
  C.append(mathcase("tput-elwadd-bf16-dst32", "tput", rot(ea(0)), expect="1.0/op", note="Dst = A + B (llama o/down)"))
  C.append(mathcase("tput-elwadd-acc-bf16-dst32", "tput", rot(ea(1)), expect="1.0/op", note="Dst += A + B"))
  C.append(mathcase("tput-elwadd-bf16-dst16", "tput", rot(ea(0)), dst32=False, a=1.5, b=1.25, expect="1.0/op",
                    note="llama o/down: ELWADD MOP after Fp32_enabled=0 (16-bit bf16 Dst)"))
  C.append(mathcase("tput-elwsub-bf16-dst32", "tput", rot(lambda r: isa.ELWSUB(dst=r)), expect="1.0/op",
                    note="not used by llama; model assumes SrcA - SrcB"))
  C.append(mathcase("tput-gapool-bf16-dst32", "tput", rot(lambda r: isa.GAPOOL(instr_mod19=1, dst=r)),
                    expect="1.0/op (DOC: same IPC as MVMUL, half the work)", note="not used by llama"))
  C.append(mathcase("tput-gmpool-bf16-dst32", "tput", rot(lambda r: isa.GMPOOL(instr_mod19=1, dst=r)),
                    expect="1.0/op", note="not used by llama"))
  ma = lambda r: isa.MOVA2D(src=r % 64, instr_mod=2, dst=r)  # noqa: E731
  C.append(mathcase("tput-mova2d-8row-bf16-dst32", "tput", rot(ma), expect="1.0/op (DOC: latency 4)"))
  C.append(mathcase("tput-mova2d-8row-fp8-dst32", "tput", rot(ma), fmt=FP8, model=True,
                    note="llama fp8 gate/qkv/lm: FP16-style SrcA into fp32 Dst; value check informational"))
  C.append(mathcase("tput-mova2d-8row-fp8-dst16", "tput", rot(ma), fmt=FP8, dst32=False))
  C.append(mathcase("tput-mova2d-1row-bf16-dst32", "tput", [isa.MOVA2D(src=i, instr_mod=0, dst=i) for i in range(16)],
                    note="llama argmax uses single MOVA2D (mod 2); 1-row form for comparison"))
  C.append(mathcase("tput-movb2d-4row-bf16-dst32", "tput",
                    [isa.MOVB2D(src=4 * (i % 16), movb2d_instr_mod=4, dst=4 * i) for i in range(16)]))
  C.append(mathcase("tput-movb2d-bcast8-bf16-dst32", "tput", rot(lambda r: isa.MOVB2D(src=r % 64, movb2d_instr_mod=2, dst=r))))
  C.append(mathcase("tput-movd2a-4row-bf16-dst32", "tput",
                    [isa.MOVD2A(src=4 * (i % 16), instr_mod=2, dst=256 + 4 * i) for i in range(16)], model=False,
                    expect="1.0/op (DOC: only MOVD2A may follow within 2 cycles)"))
  C.append(mathcase("tput-movd2b-4row-bf16-dst32", "tput",
                    [isa.MOVD2B(src=4 * (i % 16), instr_mod=2, dst=256 + 4 * i) for i in range(16)], model=False,
                    expect="1.0/op (DOC: only MOVD2B may follow within 3 cycles)"))
  C.append(mathcase("tput-movb2a-4row-bf16-dst32", "tput",
                    [isa.MOVB2A(srca=4 * (i % 16), instr_mod=2, srcb=4 * ((i + 3) % 16)) for i in range(16)],
                    model=False, note="no arithmetic in the body (MOVB2A 3 cycles after MVMUL etc. is UB)"))
  zl = lambda mode, where=lambda i: 0: [isa.ZEROACC(clear_mode=mode, use_32_bit_mode=1, where=where(i)) for i in range(16)]  # noqa: E731
  C.append(mathcase("tput-zeroacc-face-dst32", "tput", zl(1, lambda i: i % 4), model=False,
                    note="llama per-face clear encoding (clear_mode 1, bit 18 set), addr_mode 0"))
  C.append(mathcase("tput-zeroacc-all-dst32", "tput", zl(3), model=False, note="llama attention encoding"))
  C.append(mathcase("tput-zeroacc-half-dst32", "tput", zl(2), model=False))
  C.append(mathcase("tput-zeroacc-row-dst32", "tput", zl(0, lambda i: i), model=False))
  C.append(mathcase("tput-zerosrc-matrixbank", "tput", [isa.ZEROSRC(write_mode=1, src_mask=3)] * 16, model=False,
                    note="not used by llama; clears the matrix unit's current SrcA/SrcB banks"))
  C.append(mathcase("tput-setrwc", "tput", [SETRWC_D0()] * 16, model=False, expect="1.0/op (DOC)"))
  C.append(mathcase("tput-incrwc", "tput", [isa.INCRWC(rwc_d=2)] * 16, model=False, expect="1.0/op (DOC)"))
  C.append(mathcase("tput-setrwc-flip-noclear", "tput", [FLIP(3)] * 16, banks=2, keep_flip=True, model=False,
                    note="bank flip with CLR_DVALID disabled: both banks stay with the matrix unit"))
  C.append(mathcase("tput-nop", "tput", [NOP] * 16, model=False, expect="1.0/op (MEAS NOP_default)"))
  # ---------------- dependencies: same-block chains, MOV->FPU, FPU<->SFPU
  for n in (1, 2, 3, 4, 5, 6, 8):
    C.append(mathcase(f"dep-mvmul-chain-n{n}", "dep", rot(mv, n, 20 if n == 5 else 24), hw="FPU_LATENCY",
                      expect="max(1, 6/n) if 'five cycles unreadable' means issue+6 (Dst.md); n>=6 -> 1.0"))
  for n in (1, 2, 3, 6):
    C.append(mathcase(f"dep-elwmul-chain-n{n}", "dep", rot(el, n, 24), hw="FPU_LATENCY", expect="as MVMUL chain"))
  for n in (1, 2, 6):
    C.append(mathcase(f"dep-elwadd-acc-chain-n{n}", "dep", rot(ea(1), n, 24), hw="FPU_LATENCY"))
  C.append(mathcase("dep-gapool-chain-n1", "dep", rot(lambda r: isa.GAPOOL(instr_mod19=1, dst=r), 1, 16)))
  C.append(mathcase("dep-gmpool-chain-n1", "dep", rot(lambda r: isa.GMPOOL(instr_mod19=1, dst=r), 1, 16)))
  C.append(mathcase("dep-mova2d-mvmul-same", "dep",
                    [w for k in range(8) for w in (isa.MOVA2D(instr_mod=2, dst=8 * k), MV(8 * k))], unit=16,
                    expect="DOC: MVMUL after MOVA2D auto-stalls ~3 cycles regardless of rows"))
  C.append(mathcase("dep-mova2d-mvmul-other", "dep",
                    [w for k in range(8) for w in (isa.MOVA2D(instr_mod=2, dst=8 * k), MV(8 * ((k + 4) % 8) + 64))],
                    unit=16, note="MVMUL into rows 64..127, MOVA2D into 0..63"))
  # FPU -> SFPLOAD on the same rows, g TTNOPs between; the check stores the last SFPLOAD's L0 to row 256.
  def sfp_check(p):
    p.push(isa.SFPSTORE(lreg_ind=0, instr_mod0=3, dest_reg_addr=256)).fence().read32(256, 0)
  for producer, mk in (("mvmul", lambda: MV(0)), ("elwmul", lambda: isa.ELWMUL(dst=0)), ("mova2d", lambda: isa.MOVA2D(instr_mod=2, dst=0))):
    for g in ((0, 1, 2, 3, 4, 6) if producer == "mvmul" else (0, 3)):
      body = [w for _ in range(4) for w in (mk(), *[NOP] * g, isa.SFPLOAD(lreg_ind=0, instr_mod0=3, dest_reg_addr=0))]
      C.append(mathcase(f"dep-{producer}-sfpload-gap{g}", "dep", body, unit=4, check_extra=sfp_check,
                        hw="FPU_TO_SFPLOAD_GAP, DST_HALF_SAME", note="unit = FPU+SFPLOAD pair; row 256 = last load",
                        expect="ELWMUL measured 8/pair at gap 0, value new (2026-11-18 sfpu-dst)"))
  body = [w for _ in range(4) for w in (MV(0), isa.SFPLOAD(lreg_ind=0, instr_mod0=3, dest_reg_addr=256))]
  C.append(mathcase("dep-mvmul-sfpload-otherhalf", "dep", body, unit=4, expect="2/pair (DST_HALF_OTHER)"))
  one = (1, 0x3F80)
  body = [w for _ in range(4) for w in (isa.SFPSTORE(lreg_ind=1, instr_mod0=3, dest_reg_addr=0), MV(0))]
  C.append(mathcase("dep-sfpstore-mvmul-same", "dep", body, unit=4, lregs=[one], model=False,
                    want=lambda a, b: {(0, 0): f32(1.0 + 16 * prod(a, b, 0)), (0, 15): 4 * CHECK_ITERS * 16 * prod(a, b, 0)},
                    note="SFPSTORE (even columns of rows 0-3) then MVMUL on block 0: col 0 ends at 1 + 16ab if the MVMUL sees the store; col 15 is never stored"))
  body = [w for _ in range(4) for w in (isa.SFPSTORE(lreg_ind=1, instr_mod0=3, dest_reg_addr=256), MV(0))]
  C.append(mathcase("dep-sfpstore-mvmul-otherhalf", "dep", body, unit=4, lregs=[one], model=False))
  for where, row in (("samehalf", 64), ("otherhalf", 256)):
    body = [MV(8 * i) for i in range(8)] + [isa.SFPLOAD(lreg_ind=i % 4, instr_mod0=3, dest_reg_addr=row + 4 * i) for i in range(8)]
    C.append(mathcase(f"dep-mvmul8-sfpload8-{where}", "dep", body, unit=8, model=False,
                      expect="same half: 2+12/8 = 3.5/pair (MEAS ELWMUL batch 8); other: 2/pair",
                      note="batch 8 FPU then 8 SFPLOAD on one thread"))
  # ---------------- issue paths: the same expanded stream S = 8 x MVMUL(Dst+8) + SETRWC(Dst=0)
  S = [MV(0, AM_D8)] * 8 + [SETRWC_D0()]
  iss = dict(unit=18, hw="FRONTEND mop_transition, replay", model=True)
  C.append(mathcase("issue-direct", "issue", S * 2, **iss, expect="18/18 = 1.0 per instruction"))
  C.append(mathcase("issue-replay9", "issue", [isa.REPLAY(start_idx=0, len=9)] * 2, replay=S, **iss))
  for n in (1, 2, 4, 8):
    body = ([isa.REPLAY(start_idx=0, len=n)] * (8 // n) + [SETRWC_D0()]) * 2
    C.append(mathcase(f"issue-replay-len{n}", "issue", body, replay=[MV(0, AM_D8)] * n, **iss,
                      note="REPLAY of n MVMULs, RISC pushes 8/n REPLAYs + SETRWC per 9 instructions"))
  mopS = mop1(inner=8, loop=MV(0, AM_D8), end0=SETRWC_D0())
  C.append(mathcase("issue-mop", "issue", [isa.MOP(mop_type=1)] * 2, mop=mopS, **iss,
                    expect="1.0 (MOP->MOP has no transition)"))
  C.append(mathcase("issue-mop-then-direct", "issue", [isa.MOP(mop_type=1), *S], mop=mopS, **iss,
                    expect="(18+1)/18 if the 1-cycle MOP->non-MOP penalty shows (DOC MOPExpander.md)"))
  mopR = mop1(inner=1, loop=isa.REPLAY(start_idx=0, len=8), end0=SETRWC_D0())
  C.append(mathcase("issue-mop-replay", "issue", [isa.MOP(mop_type=1)] * 2, mop=mopR, replay=[MV(0, AM_D8)] * 8,
                    **iss, note="llama shape: MOP whose loop op is a REPLAY"))
  C.append(mathcase("issue-mop-replay-then-direct", "issue", [isa.MOP(mop_type=1), *S], mop=mopR,
                    replay=[MV(0, AM_D8)] * 8, **iss, expect="1.0 (DOC: a REPLAY inside the MOP hides the penalty)"))
  # llama attention: MOP inner 2 alternating two 8-MVMUL replays, then SETRWC (here: Dst back to 0, no bank release)
  mopA = lambda p: (load_replay(p, 8, [MV(0, AM_D8)] * 8),  # noqa: E731
                    p.mopcfg(mop1(inner=1, loop=isa.REPLAY(start_idx=0, len=8), loop1=isa.REPLAY(start_idx=8, len=8),
                                  last=isa.REPLAY(start_idx=8, len=8), end0=SETRWC_D0())))
  C.append(mathcase("issue-mop-alt-replay", "issue", [isa.MOP(mop_type=1)] * 2, extra=mopA,
                    replay=[MV(0, AM_D8)] * 8, unit=34, model=False,
                    note="llama attention shape (LoopOp/LoopOp1 = two REPLAYs of 8 MVMUL)"))
  # llama o/down/gate: HiFi2 ELWMUL MOP, outer 2 x inner 2, last op releases banks (flip only here: keep_flip)
  o_mods = {0: (ab(8, b_incr=8), dstm(incr=8)), 2: (ab(a_clr=1, b_clr=1), dstm(cr=1, fid_incr=1)),
            3: (ab(a_clr=1, b_clr=1), dstm(incr=8, c2cr=1, fid_clr=1))}
  o_mop = mop1(outer=2, inner=2, loop=isa.ELWMUL(addr_mode=0), last=isa.ELWMUL(clear_dvalid=3, addr_mode=3),
               last1=isa.ELWMUL(addr_mode=2))
  C.append(mathcase("issue-llama-o-elwmul-mop", "issue", [isa.MOP(mop_type=1)] * 4 + [SETRWC_ALL()], unit=17,
                    mop=o_mop, addr_mods=o_mods, banks=2, keep_flip=True, model=False,
                    note="exact template and ADDR_MODs of llama-1b o/trisc1; bank release replaced by flip"))
  for k in (1, 2, 4, 8, 16):
    C.append(mathcase(f"issue-loop-nop{k}", "issue", [NOP] * k, model=False,
                      expect="1.0/op once the body hides addi/bne (MEAS: 16 NOPs -> 1.000)", hw="FRONTEND loop_overhead_hidden"))
  # ---------------- Src bank handoff
  for k in (1, 4):
    body = [w for i in range(8 // k * 2) for w in ([MV(8 * ((i * k + j) % 8)) for j in range(k)] + [FLIP(3)])]
    C.append(mathcase(f"src-flip-ready-k{k}", "src", body, unit=sum(1 for w in body if w >> 24 == 0x26), banks=2,
                      keep_flip=True, note="k MVMUL then SETRWC flip; both banks hold data (no release)"))
  C.append(mathcase("src-mvmul-flip-inline", "src", rot(lambda r: MV(r, flip=3)), banks=2, keep_flip=True,
                    note="every MVMUL flips both banks (clear_dvalid=3, release disabled)"))
  C += handoff_cases()
  C += multithread_cases()
  C += overhead_cases(o_mop, o_mods)
  # ---------------- data dependence
  C.append(mathcase("data-mvmul-lofi-bf16-zero", "data", rot(mv), data="zero", model=False))
  C.append(mathcase("data-mvmul-lofi-bf16-rand", "data", rot(mv), data="rand", model=False))
  C.append(mathcase("data-elwmul-lofi-bf16-zero", "data", rot(el), data="zero", model=False))
  C.append(mathcase("data-elwmul-lofi-bf16-rand", "data", rot(el), data="rand", model=False))
  return C


def handoff_cases():
  """Two threads: trisc1 consumes Src banks (MVMUL, then SETRWC releasing both), trisc0 gives zeroed banks back with
  UNPACR_NOP. Totals match exactly per sample, so neither side is left waiting (FPU.md, risks)."""
  out = []
  for k, r in ((1, 4), (4, 4), (16, 1)):
    t1 = [w for _ in range(r) for w in ([MV(8 * (j % 8)) for j in range(k)] + [FLIP(3)])]
    t0 = [w for _ in range(r) for w in (UNP_GIVE(0), UNP_GIVE(1))]
    roles = {"trisc1": dict(body=t1, prog=math_setup(data="zero"), check=None, predict=None),
             "trisc0": dict(body=t0, prog=Prog().fence(), check=None, predict=None)}
    out.append(case(f"src-handoff-stream-k{k}", "src", roles, unit=k * r, barrier=True,
                    note="unit = MVMUL per iteration; one release + one give per k MVMUL"))
  # single-shot latency: give after the consumer is already blocked
  reps, F = 8, FLAGS
  p1 = math_setup(data="zero")
  for i in range(reps):  # control: bank present
    p1.stamp().push(MV(0)).fence().stamp()
  for i in range(reps):
    p1.push(FLIP(3)).stamp().push(MV(0)).flag(F, i + 1).fence().stamp()
  p0 = Prog().fence()
  for i in range(reps):
    p0.waitflag(F, i + 1).delay(2000).stamp().push(UNP_GIVE(0), UNP_GIVE(1)).fence()
  roles = {"trisc1": dict(body=[NOP], prog=p1, check=None, predict=None, counts=(0, 0, 0)),
           "trisc0": dict(body=[NOP], prog=p0, check=None, predict=None, counts=(0, 0, 0))}
  out.append(case("src-handoff-latency", "src", roles, unit=1, reps=reps, l1_zero={F: 4},
                  note="t1 stamps: 8 x (push, done) bank present, then 8 x (push, done) blocked; t0: give stamps"))
  return out


def multithread_cases():
  out = []
  t1 = math_setup()
  mvb = [MV(8 * (i % 8)) for i in range(16)]
  for name, t0body in (("sfpload-otherhalf", [isa.SFPLOAD(lreg_ind=i % 4, instr_mod0=3, dest_reg_addr=256 + 4 * i) for i in range(16)]),
                       ("sfpload-samehalf", [isa.SFPLOAD(lreg_ind=i % 4, instr_mod0=3, dest_reg_addr=64 + 4 * i) for i in range(16)]),
                       ("sfpmad", [isa.SFPMAD(lreg_src_a=10, lreg_src_b=10, lreg_src_c=i % 4, lreg_dest=i % 4) for i in range(16)]),
                       ("mvmul", [MV(64 + 8 * (i % 8)) for i in range(16)])):
    p0 = Prog().fence()
    if name == "mvmul":
      p0.push(*[x for i in range(8) for x in (setc16(12 + i, 0), setc16(28 + i, 0), setc16(47 + i, 0))], SETRWC_ALL())
    roles = {"trisc1": dict(body=mvb, prog=t1, check=None, predict=None),
             "trisc0": dict(body=t0body, prog=p0.fence(), check=None, predict=None)}
    out.append(case(f"mt-mvmul-t1-{name}-t0", "mt", roles, unit=16, barrier=True,
                    note="trisc1 MVMUL rows 0..63; trisc0 stream; unit = ops per thread per iteration",
                    expect="other half / register-only: no interference; same half: Dst-half arbitration"))
  return out



def overhead_cases(o_mop, o_mods):
  """Per-tile math-thread overhead, built from the exact words of llama-1b o/trisc1 (o.ttrv:248-262) on one thread.
  Src banks stay valid (two banks, flips do not release), MATH_PACK (semaphore 1) is posted and taken back at once.
  unit = 1 per loop iteration, so the slope is cycles per iteration."""
  C = []
  sfpu = [isa.SFPLOAD(lreg_ind=0, instr_mod0=3, sfpu_addr_mode=0, dest_reg_addr=0),
          isa.SFPMAD(lreg_src_a=0, lreg_src_b=10, lreg_src_c=7, lreg_dest=7, instr_mod1=0), isa.INCRWC(rwc_d=2)]
  ext = lambda p: load_replay(p, 0, sfpu)  # noqa: E731
  MOP = isa.MOP(mop_type=1)
  stall_vld = isa.STALLWAIT(64, 384)           # o.ttrv:253 STALLWAIT(MATH, SRCA_VLD|SRCB_VLD) before each MOP
  fpu_to_sfpu = isa.STALLWAIT(256, 16)         # o.ttrv:254 block SFPU until MATH idle
  end_sync = isa.STALLWAIT(2, 2064)            # o.ttrv:262
  semwait = isa.SEMWAIT(stall_res=322, sem_sel=2, wait_sem_cond=2)
  zero4 = [isa.ZEROACC(clear_mode=1, use_32_bit_mode=1, addr_mode=1, where=i) for i in range(4)]
  rwc_all, rwc_face, rwc_d0 = isa.SETRWC(BitMask=15), isa.SETRWC(rwc_cr=4, rwc_d=8, BitMask=4), isa.SETRWC(BitMask=4)
  sfpu_faces = [w for _ in range(4) for w in [isa.REPLAY(start_idx=0, len=3)] * 8 + [rwc_face, rwc_face]]
  pass_ = zero4 + [rwc_all] + [stall_vld, MOP] * 4 + [fpu_to_sfpu, rwc_all] + sfpu_faces + [rwc_d0, end_sync]
  sem = [semwait, isa.SEMPOST(sem_sel=2), isa.SEMGET(sem_sel=2)]
  kw = dict(unit=1, mop=o_mop, addr_mods=o_mods, banks=2, keep_flip=True, model=False, extra=ext)
  bodies = {
    "ovh-mop4": [MOP] * 4,
    "ovh-stallvld-mop4": [stall_vld, MOP] * 4,
    "ovh-zeroacc4": zero4 + [rwc_all],
    "ovh-mop4-drain": [MOP] * 4 + [fpu_to_sfpu, rwc_all],
    "ovh-sfpu-faces": sfpu_faces + [rwc_d0],
    "ovh-sfpu-faces-sync": sfpu_faces + [rwc_d0, end_sync],
    "ovh-sem": sem,
    "ovh-setc16-dest-mop": [isa.SETC16(1, 0), MOP, isa.SETC16(1, 64), MOP, isa.SETC16(1, 128), MOP, isa.SETC16(1, 192), MOP],
    "ovh-o-pass": pass_,
    "ovh-o-pass-sem": [semwait] + pass_ + [isa.SEMPOST(sem_sel=2), isa.SEMGET(sem_sel=2)],
  }
  for cid, body in bodies.items():
    C.append(mathcase(cid, "ovh", body, **kw, note="cycles per iteration; words from llama-1b o/trisc1"))
  return C

CASES = _cases()


# ---------------------------------------------------------------- run

def images(case):
  out = {}
  for role, spec in SPECS[case["id"]].items():
    body = "".join(f"TTINSN({w:#010x}u);" for w in spec["body"])
    out[role] = build("k_fpu.c", role, BODY=body, TT_SEM=SEM[role])
  return out


def params_l1(case):
  params, l1 = {}, {}
  roles = SPECS[case["id"]]
  for role, spec in roles.items():
    lay = LAYOUT[role]
    prog_at, chk_at = lay["log"] + 0xC000, lay["log"] + 0xE000
    chk = spec["check"] or Prog()
    l1[prog_at], l1[chk_at] = spec["prog"].blob(), chk.blob()
    assert len(l1[prog_at]) <= 0x2000 and len(l1[chk_at]) <= 0x2000
    me = int(role[-1])
    peer = next((int(r[-1]) for r in roles if r != role), me)
    counts = spec.get("counts", COUNTS)
    params[role] = [prog_at, len(spec["prog"].recs), chk_at, len(chk.recs), *counts, SAMPLES,
                    BARRIER if case.get("barrier") else 0, me, peer]
  if case.get("barrier"): l1[BARRIER] = bytes(16)
  for addr, n in (case.get("l1_zero") or {}).items(): l1[addr] = bytes(n)
  return params, l1


def decode_read(raw, bits, fp16):
  if bits == 32: return bits_f32(raw)
  if fp16: return struct.unpack("<e", struct.pack("<H", raw & 0xFFFF))[0]
  return bits_f32((raw & 0xFFFF) << 16)


def _s32(x): return x - (1 << 32) if x >= 1 << 31 else x


def run(card, case, timeout):
  imgs = images(case)
  params, l1 = params_l1(case)
  card.run([(TILE, imgs, params, l1)], timeout, SITES)
  raw = {}
  for role in SPECS[case["id"]]:
    n_time, n_setup = card.aux(TILE, 2, role)
    n_chk = card.iface.read32(TILE, LAYOUT[role]["res"] + 8)
    w = card.log(TILE, 512 + n_setup, role)
    raw[role] = dict(stamps=list(w[:n_time]), check=list(w[256:256 + n_chk]), setup=list(w[512:512 + n_setup]))
  return analyse(case, raw)


def _d(a, b): return _s32((b - a) & 0xFFFFFFFF)


def analyse(case, raw):
  """raw: {role: {stamps: [t0, t1, ...], check: [Dst words], setup: [setup-program stamps]}} -> result record."""
  roles = SPECS[case["id"]]
  rec, u = dict(roles=sorted(roles)), case["unit"]
  def slopes(per):
    med = {c: median(v[1:]) for c, v in per.items()}
    cs = sorted(med)
    return dict(medians={str(c): m for c, m in med.items()},
                slopes=[(med[y] - med[x]) / ((y - x) * u) for x, y in zip(cs, cs[1:])],
                slope=(med[cs[-1]] - med[cs[0]]) / ((cs[-1] - cs[0]) * u))
  spans = {}
  for role, spec in roles.items():
    st, r = raw[role]["stamps"], {}
    counts = [c for c in spec.get("counts", COUNTS) if c]
    per, k = {}, 0
    for c in counts:
      pairs = [(st[k + 2 * s], st[k + 2 * s + 1]) for s in range(SAMPLES)]
      per[c] = [_d(t0, t1) for t0, t1 in pairs]
      spans[role, c] = pairs
      k += 2 * SAMPLES
    if per: r.update(samples={str(c): v for c, v in per.items()}, **slopes(per))
    if raw[role]["setup"]: r["setup_log"] = raw[role]["setup"]
    chk = spec["check"]
    if chk is not None:
      vals = [decode_read(x, bits, spec.get("fp16")) for x, (_, _, bits) in zip(raw[role]["check"], chk.reads)]
      r["dst"] = [[row, col, v] for (row, col, _), v in zip(chk.reads, vals)]
      r["check"] = "none"
      if spec.get("predict"):
        want = spec["predict"]()
        tol = 0.0 if spec.get("dst32", True) else 1 / 64
        exp = [want.get((row, col), want.get(row)) for row, col, _ in chk.reads]
        bad = [[row, col, v, e] for (row, col, _), v, e in zip(chk.reads, vals, exp)
               if e is not None and abs(v - e) > tol * max(1.0, abs(e))]
        r["check"] = "MISMATCH" if bad else "ok"
        r["expected"] = exp
        if bad: r["bad"] = bad[:8]
    rec[role] = r
  if "slope" in rec.get("trisc1", {}):
    rec["median"] = round(rec["trisc1"]["slope"], 4)
    if "check" in rec["trisc1"]: rec["check"] = rec["trisc1"]["check"]
  if case.get("barrier"):
    # both threads on one wall clock: earliest start to latest end per sample
    per = {c: [_d(min(spans[r, c][s][0] for r in roles), max(spans[r, c][s][1] for r in roles))
               for s in range(SAMPLES)] for c in COUNTS}
    rec["union"] = dict(samples={str(c): v for c, v in per.items()}, **slopes(per))
  if "reps" in case:
    s1, s0, n = rec["trisc1"]["setup_log"], rec["trisc0"]["setup_log"], case["reps"]
    rec["ready_push_to_done"] = [_d(s1[2 * i], s1[2 * i + 1]) for i in range(n)]
    blk = s1[2 * n:]
    rec["blocked_push_to_done"] = [_d(blk[2 * i], blk[2 * i + 1]) for i in range(n)]
    rec["give_to_done"] = [_d(s0[i], blk[2 * i + 1]) for i in range(n)]
    rec["median"] = median(rec["give_to_done"]) - median(rec["ready_push_to_done"])
  return rec


# ---------------------------------------------------------------- tools (no card)

def disasm(cid, role="trisc1"):
  """Disassemble the image and mark the timed loop (body_loop): RISC-V around it, Tensix words decoded."""
  case = next(c for c in CASES if c["id"] == cid)
  img = images(case)[role]
  words = struct.unpack(f"<{len(img) // 4}I", img[:len(img) // 4 * 4])
  body = SPECS[cid][role]["body"]
  first = isa.inline(body[0])
  starts = [i for i in range(len(words) - len(body) + 1) if [isa.outline(x) for x in words[i:i + len(body)]] == body]
  with tempfile.TemporaryDirectory() as d:
    Path(d, "k.bin").write_bytes(img)
    subprocess.run(["llvm-objcopy", "-I", "binary", "-O", "elf32-littleriscv", "--rename-section=.data=.text,code",
                    f"{d}/k.bin", f"{d}/k.elf"], check=True)
    dis = subprocess.run(["llvm-objdump", "-d", "--triple=riscv32", "--mattr=+m", f"{d}/k.elf"], check=True,
                         capture_output=True, text=True).stdout.splitlines()
  assert starts and words[starts[0]] == first, "body not found contiguous in the image"
  lo, hi = 4 * starts[0] - 8, 4 * (starts[0] + len(body)) + 12
  print(f"{cid} {role}: {len(img)} bytes, body at {4 * starts[0]:#x} ({len(body)} words)")
  for line in dis:
    try: addr = int(line.split(":")[0], 16)
    except ValueError: continue
    if not lo <= addr < hi: continue
    if lo + 8 <= addr < hi - 12 and addr % 4 == 0:
      w = isa.outline(words[addr // 4])
      d = isa.tensix_decode(w)
      print(f"  {addr:5x}: {words[addr // 4]:08x}  .ttinsn {w:08x}  {d[0]} {d[1]}")
    elif not (lo + 8 <= addr < hi - 12):
      print(" ", line.strip())


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--list", action="store_true")
  ap.add_argument("--build", action="store_true")
  ap.add_argument("--disasm")
  ap.add_argument("--role", default="trisc1")
  a = ap.parse_args()
  if a.list:
    groups = {}
    for c in CASES: groups.setdefault(c["group"], []).append(c["id"])
    for g, ids in groups.items(): print(f"{g} ({len(ids)}):", *ids, sep="\n  ")
    print(f"total {len(CASES)}")
  if a.build:
    for c in CASES:
      for role, img in images(c).items(): print(f"{c['id']:44s} {role} {len(img)} B")
      params_l1(c)
  if a.disasm: disasm(a.disasm, a.role)


if __name__ == "__main__":
  main()
