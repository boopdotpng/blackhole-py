"""FPU/SFPU overlap probes: how much independent FPU and SFPU work overlaps, from one TRISC and from two.

Reuses the fpu.py harness (k_fpu.c, setup programs, slope analysis). FP32 Dst; the FPU writes rows 0..63 (8 rotating
8-row blocks, so no MVMUL accumulate chain), the SFPU works on rows 256.. (other Dst half) unless a case says
"samehalf" (rows 128.., same half, different rows).

  python3 sims/probes/run.py --device 1 --output sims/results/<date>-ovl-card1.jsonl ovl
  python3 sims/probes/ovl.py --list

Groups:
  base   each stream alone (per-instruction cost of every building block)
  il     one thread, FPU and SFPU interleaved in batches of b (b = 1..16), other half and same half
  item   one thread, a realistic SFPU item (LD, MAD, ST) with MVMULs mixed in
  fill   one thread, MVMULs placed in SFPU dependency bubbles
  rwc    one thread, Dst RWC shared by FPU and SFPU: SETRWC per switch; LLK-style switch (SETC16 + STALLWAIT)
  mt     two threads (T1 FPU, T0 SFPU), each with its own RWC and ADDR_MOD increments
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fpu  # noqa: E402
from fpu import isa, mathcase, case, math_setup, Prog, MV, NOP, SETRWC_D0, SETRWC_ALL, setc16, dstm, AM_D8  # noqa: E402

run = fpu.run
OTHER, SAME = 256, 128
AM_S4 = 5                                  # ADDR_MOD slot 5: Dst += 4 (one SFPLOAD/SFPSTORE row group)
MODS = {AM_S4: (0, dstm(incr=4))}


def mv(i): return MV(8 * (i % 8))
def ld(i, base=OTHER, r=None, am=0): return isa.SFPLOAD(lreg_ind=i % 4 if r is None else r, instr_mod0=3, sfpu_addr_mode=am, dest_reg_addr=base + 4 * (i % 16))
def st(i, base=OTHER, r=None, am=0): return isa.SFPSTORE(lreg_ind=i % 4 if r is None else r, instr_mod0=3, sfpu_addr_mode=am, dest_reg_addr=base + 4 * (i % 16))
def mad(r): return isa.SFPMAD(lreg_src_a=r, lreg_src_b=10, lreg_src_c=9, lreg_dest=r)  # r = r * 1.0 + 0.0
def setc_dest(v): return isa.SETC16(1, v)   # DEST_TARGET_REG_CFG_MATH_Offset (LLK set_dst_write_addr)
STALL_SFPU_ON_MATH = isa.STALLWAIT(isa.Stall.SFPU, isa.Wait.MATH)   # LLK _llk_math_eltwise_unary_sfpu_start_


def item_indep(k):  # four LD/MAD/ST items, stage-major: no dependent pair closer than 4 instructions
  return [ld(4 * k + j) for j in range(4)] + [mad(j) for j in range(4)] + [st(4 * k + j) for j in range(4)]


def item_dep(k):    # four LD/MAD/ST items, item-major: every instruction depends on the one before
  return [w for j in range(4) for w in (ld(4 * k + j, r=0), mad(0), st(4 * k + j, r=0))]


# one Dst face the LLK/SFPI way: 8 x (SFPLOAD, SFPMAD, dst_reg++ = INCRWC) then the face step (2 x SETRWC)
FACE_LLK = [w for _ in range(8) for w in (ld(0, base=OTHER, r=0), mad(0), isa.INCRWC(rwc_d=2))] + [SETRWC_D0()] * 2
# the same work addressed by immediates: no RWC instruction at all
FACE_IMM = [w for i in range(8) for w in (ld(i, base=OTHER, r=0), mad(0))]


def batched(fpu_ops, sfpu_ops, b):
  out = []
  for i in range(0, max(len(fpu_ops), len(sfpu_ops)), b):
    out += fpu_ops[i:i + b] + sfpu_ops[i:i + b]
  return out


def M(cid, group, body, unit, note="", **kw):
  return mathcase(cid, group, body, unit=unit, model=False, addr_mods=MODS, note=note, extra=clean, **kw)


def clean(p):
  """Firmware no longer resets the Tensix between launches: put back the per-thread Dst offset a previous case may
  have moved (the rwc-llk cases leave it at 256)."""
  p.push(isa.SETC16(1, 0), SETRWC_ALL())


def _cases():
  C = []
  MV16 = [mv(i) for i in range(16)]
  # ---------------- base
  C.append(M("ovl-base-mvmul", "base", MV16, 16))
  C.append(M("ovl-base-sfpload", "base", [ld(i) for i in range(16)], 16))
  C.append(M("ovl-base-sfpstore", "base", [st(i) for i in range(16)], 16))
  C.append(M("ovl-base-sfpmad-indep", "base", [mad(i % 4) for i in range(16)], 16))
  C.append(M("ovl-base-sfpmad-chain", "base", [mad(0)] * 16, 16, note="dependent chain on L0"))
  C.append(M("ovl-base-item-indep", "base", item_indep(0) + item_indep(1), 8, note="unit = LD/MAD/ST item"))
  C.append(M("ovl-base-item-dep", "base", item_dep(0) + item_dep(1), 8, note="unit = LD/MAD/ST item"))
  C.append(M("ovl-base-mvmul-walk", "base", ([MV(0, AM_D8)] * 8 + [SETRWC_D0()]) * 2, 16, note="18 words per 16 MVMUL"))
  C.append(M("ovl-base-sfpload-walk", "base", ([ld(0, am=AM_S4)] * 8 + [SETRWC_D0()]) * 2, 16, note="18 words per 16 SFPLOAD"))
  # ---------------- il: 16 MVMUL + 16 SFPx in batches of b; unit = FPU+SFPU pair
  for kind, mk in (("sfpload", ld), ("sfpstore", st), ("sfpmad", lambda i: mad(i % 4))):
    for b in (1, 2, 4, 8, 16):
      C.append(M(f"ovl-il-{kind}-b{b}", "il", batched(MV16, [mk(i) for i in range(16)], b), 16,
                 note="one thread; issue-bound expectation 2.0/pair"))
  for kind, mk in (("sfpload", lambda i: ld(i, SAME)), ("sfpstore", lambda i: st(i, SAME))):
    for b in (1, 4, 16):
      C.append(M(f"ovl-il-{kind}-samehalf-b{b}", "il", batched(MV16, [mk(i) for i in range(16)], b), 16,
                 note="control: SFPU rows 128.. share the FPU's Dst half"))
  # ---------------- item: 8 LD/MAD/ST items (24 SFPU instr) + 8 MVMUL; unit = item
  sf = item_indep(0) + item_indep(1)
  mv8 = [mv(i) for i in range(8)]
  C.append(M("ovl-item-indep-mv-after", "item", sf + mv8, 8, note="24 SFPU then 8 MVMUL"))
  C.append(M("ovl-item-indep-mv-fine", "item", [w for i in range(8) for w in sf[3 * i:3 * i + 3] + [mv8[i]]], 8,
             note="MVMUL after every third SFPU instruction"))
  sd = item_dep(0) + item_dep(1)
  C.append(M("ovl-item-dep-mv-after", "item", sd + mv8, 8))
  C.append(M("ovl-item-dep-mv-fine", "item", [w for i in range(8) for w in (sd[3 * i], mv8[i], *sd[3 * i + 1:3 * i + 3])], 8,
             note="LD, MVMUL, MAD, ST: MVMUL in the LD->MAD slot"))
  C.append(M("ovl-item-dep-mv-fine2", "item", [w for i in range(8) for w in (sd[3 * i], sd[3 * i + 1], mv8[i], sd[3 * i + 2])], 8,
             note="LD, MAD, MVMUL, ST: MVMUL in the MAD->ST slot"))
  # ---------------- fill: dependent SFPMAD chain with MVMULs in its latency slots
  for k in (1, 2):
    C.append(M(f"ovl-fill-madchain-mv{k}", "fill", [w for i in range(16) for w in (mad(0), *[mv(k * i + j) for j in range(k)])], 16,
               note=f"unit = SFPMAD; {k} MVMUL after each dependent SFPMAD"))
  # ---------------- rwc: one Dst RWC for both engines
  # FPU walks blocks by ADDR_MOD Dst+8, SFPU walks row groups by Dst+4; both need their own position, so each switch
  # rewrites the counter with SETRWC (here: back to 0; the SFPU base 256 is in its immediate).
  for b in (1, 2, 4, 8):
    fpu_b, sfpu_b = [MV(0, AM_D8)] * b, [ld(0, am=AM_S4)] * b
    body = ([SETRWC_D0()] + fpu_b + [SETRWC_D0()] + sfpu_b) * (16 // b)
    C.append(M(f"ovl-rwc-setrwc-b{b}", "rwc", body, 16, note="SETRWC before every batch; unit = pair"))
    # LLK sfpu_start/done around each SFPU batch: SETC16 Dst offset, STALLWAIT(SFPU, MATH), ..., SETRWC
    body = ([setc_dest(0)] + fpu_b + [SETRWC_D0(), setc_dest(256), STALL_SFPU_ON_MATH] + [ld(0, base=0, am=AM_S4)] * b
            + [SETRWC_D0()]) * (16 // b)
    C.append(M(f"ovl-rwc-llk-b{b}", "rwc", body, 16, note="LLK switch: SETC16 offset + STALLWAIT(SFPU on MATH) + SETRWC"))
    body = ([setc_dest(0)] + fpu_b + [SETRWC_D0(), setc_dest(256)] + [ld(0, base=0, am=AM_S4)] * b + [SETRWC_D0()]) * (16 // b)
    C.append(M(f"ovl-rwc-llk-nostall-b{b}", "rwc", body, 16, note="as llk without the STALLWAIT"))
  C.append(M("ovl-rwc-llk-b16", "rwc", [setc_dest(0)] + [MV(0, AM_D8)] * 8 + [SETRWC_D0()] + [MV(0, AM_D8)] * 8 +
             [SETRWC_D0(), setc_dest(256), STALL_SFPU_ON_MATH] + [ld(0, base=0, am=AM_S4)] * 16 + [SETRWC_D0()], 16))
  C.append(M("ovl-face-llk", "face", FACE_LLK, 1, note="unit = one face"))
  C.append(M("ovl-face-imm", "face", FACE_IMM, 1, note="unit = one face"))
  C.append(M("ovl-face-llk-mv16", "face", FACE_LLK + MV16, 1, note="one thread: face then 16 MVMUL"))
  C.append(M("ovl-face-imm-mv16", "face", FACE_IMM + MV16, 1, note="one thread: face then 16 MVMUL"))
  C.extend(mt_cases())
  return C


def t0_setup():
  """trisc0: its own ADDR_MODs (slot 5 = Dst+4), RWCs at 0, Dst offset 0."""
  p = Prog().fence()
  mods = {**fpu.ADDR_MODS, **MODS}
  for i, (abv, dv) in mods.items(): p.push(setc16(12 + i, abv), setc16(28 + i, dv), setc16(47 + i, 0))
  p.push(setc16(11, 0), setc_dest(0), SETRWC_ALL())
  return p.fence()


def mt_cases():
  out = []
  MV16 = [mv(i) for i in range(16)]
  walk = ([MV(0, AM_D8)] * 8 + [SETRWC_D0()]) * 2           # FPU walking with its own counter
  t0_bodies = {
    "sfpload": ([ld(i) for i in range(16)], MV16),
    "sfpload-samehalf": ([ld(i, SAME) for i in range(16)], MV16),
    "sfpstore": ([st(i) for i in range(16)], MV16),
    "sfpload-walk": (([ld(0, am=AM_S4)] * 8 + [SETRWC_D0()]) * 2, walk),   # both threads auto-increment their own RWC
    "item-indep": (item_indep(0) + item_indep(1), [mv(i) for i in range(8)]),
    "item-indep-x2fpu": (item_indep(0) + item_indep(1), MV16 + MV16),
    "item-dep": (item_dep(0) + item_dep(1), [mv(i) for i in range(8)]),
    # which "SFPU thread" words take the FPU's issue slot? (T1 alone: 1.0/MVMUL)
    "setrwc": ([SETRWC_D0()] * 16, MV16),
    "incrwc": ([isa.INCRWC(rwc_d=2)] * 16, MV16),
    "ttnop": ([NOP] * 16, MV16),
    "sfpnop": ([isa.SFPNOP()] * 16, MV16),
    "setc16": ([setc_dest(0)] * 16, MV16),
    "face-llk": (FACE_LLK, MV16),
    "face-imm": (FACE_IMM, MV16),
  }
  for name, (t0, t1) in t0_bodies.items():
    roles = {"trisc1": dict(body=t1, prog=math_setup(addr_mods=MODS, extra=clean), check=None, predict=None),
             "trisc0": dict(body=t0, prog=t0_setup(), check=None, predict=None)}
    unit = 8 if name.startswith("item") else 1 if name.startswith("face") else 16
    out.append(case(f"ovl-mt-{name}", "mt", roles, unit=unit, barrier=True,
                    note=f"trisc1 {len(t1)} FPU words, trisc0 {len(t0)} SFPU words per iteration; unit {unit}; see union"))
  return out


CASES = _cases()


if __name__ == "__main__":
  if "--list" in sys.argv:
    for c in CASES: print(f"{c['group']:5s} {c['id']:36s} {c['note']}")
    print(len(CASES), "cases")
