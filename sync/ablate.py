"""Sync ablations on the real decode graph by patching exported kernel images in place.

Every patch replaces one 32-bit word at a known pc with another of the same size, so no pc moves and branch targets
stay valid. The expected old word is checked against the .S listing before patching. Variants are written to
sync/variants/<variant>/ (a copy of kernels/ for one model plus kernels/zero) and run by pointing llama3.KERNELS at
that copy. Results go to sync/results/<model>-<variant>.json.

  ../.venv/bin/python sync/ablate.py --model 8b-fp8 --variant nodram --device 1

Variants (combine with '+', e.g. nodram+t0nodrain):
  base         unmodified kernels
  nodram       projection weight reads (BRISC read_pages) shrink to 64 B/page: DRAM traffic vanishes, the CB
               protocol and every sync stay. Measures the compute-pipeline ceiling. Output is garbage.
  t0nodrain    TRISC0 hot unpack loop: remove the per-tile PC_BUF_SYNC drain (RISC-V waits for the unpacker to go
               idle). The UNPACK_SYNC poll is tightened to "sem == 0", so the RISC still does not rewrite the unpack
               base address while an unpack is in flight. Overlaps RISC bookkeeping with the unpack.
  t0loose      as t0nodrain but keep the existing "sem < 2" poll: one unpack may be in flight while the RISC
               rewrites the (single-context) base address. Racy; an upper bound for double-buffered config contexts.
  t0semfix     t0nodrain, plus the STALLWAIT before SEMGET[UNPACK_SYNC] also blocks the Sync Unit (B1|B3 instead of
               B3), so the SEMGET really happens after the unpack completes. The semaphore then protects the base-
               address rewrite and the per-tile drain is redundant. (t0nodrain alone is wrong: see README.)
  t1nosync     TRISC1 dot loop: drop the per-tile STALLWAIT[SYNC<-MATH|SFPU]. Racy (next ZEROACC/ELWMUL may hit Dst
               while the SFPU still reads it); upper bound for double-buffering Dst inside the math thread.
"""
import argparse, json, re, shutil, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
import census

RV_NOP, TT_NOP = 0x00000013, 0x08000000
PROJECTIONS = ("qkv", "o", "gate", "down", "lm")

def addi(rd, rs1, imm): return (imm & 0xfff) << 20 | rs1 << 15 | rd << 7 | 0x13

def patch_word(data, pc, old, new):
  cur = int.from_bytes(data[pc:pc + 4], "little")
  assert cur == old, f"pc {pc:#x}: expected {old:#010x}, found {cur:#010x}"
  data[pc:pc + 4] = new.to_bytes(4, "little")

def listing(kdir, risc_file):
  insns = census.parse(kdir / risc_file)
  return insns, census.loops(insns)

def p_nodram(kdir, kernel, log):
  if kernel not in PROJECTIONS: return
  for s in sorted(kdir.glob("brisc*.S")):
    insns, _ = listing(kdir, s.name)
    by_pc = {i["pc"]: i for i in insns}
    data = bytearray((kdir / s.with_suffix(".bin").name).read_bytes())
    stores = [i for i in insns if i["mn"] == "sw" and re.search(r"noc[01]_regs \+ 0x20 ·", i["rest"])]
    # the weight reader is the last NoC length store in the image (read_pages subroutine)
    st = stores[-1]
    reg = int(re.match(r"x(\d+),", st["rest"])[1])
    prev = by_pc[st["pc"] - 4]
    assert prev["mn"] == "addi" and prev["rest"].startswith(f"x{reg}, x{reg}"), prev
    patch_word(data, prev["pc"], int(prev["word"], 16), addi(reg, 0, 64))
    (kdir / s.with_suffix(".bin").name).write_bytes(data)
    log.append(f"{kernel}/{s.stem}: read length {st['rest'].split('write ')[-1]} -> 64 B at {prev['pc']:#x}")

def hot_loop(insns, ls):
  """The innermost non-spin loop with the most Tensix drains: the per-tile unpack loop."""
  inner = [l for l in ls if not l["spin"]]
  best = max(inner, key=lambda l: (sum("PC_BUF_SYNC" in x["rest"] and x["mn"] == "lw" for x in l["body"]), -len(l["body"])))
  return best

def p_t0(kdir, kernel, log, strict, semfix=False):
  if kernel not in PROJECTIONS: return
  insns, ls = listing(kdir, "trisc0.S")
  loop = hot_loop(insns, ls)
  data = bytearray((kdir / "trisc0.bin").read_bytes())
  n = 0
  for x in loop["body"]:
    if x["mn"] in ("sw", "lw") and "TensixMMIO.PC_BUF_SYNC" in x["rest"]:
      patch_word(data, x["pc"], int(x["word"], 16), RV_NOP); n += 1
    if semfix and x["mn"] == "STALLWAIT" and x["word"] == "8810001a":  # Stall.UNPACK -> Stall.UNPACK|SYNC, so SEMGET waits
      patch_word(data, x["pc"], 0x8810001a, 0x8814001a); n += 1
    if strict and x["mn"] == "andi" and x["rest"].startswith("x21, x21, 254"):
      w = int(x["word"], 16); patch_word(data, x["pc"], w, (w & 0x000fffff) | (255 << 20)); n += 1
  assert n >= 2, (kernel, n)
  (kdir / "trisc0.bin").write_bytes(data)
  log.append(f"{kernel}/trisc0: hot loop {loop['start']:#x}-{loop['end']:#x}, {n} words patched ({'strict' if strict else 'loose'})")

def p_t1nosync(kdir, kernel, log):
  if kernel not in PROJECTIONS: return
  insns, ls = listing(kdir, "trisc1.S")
  data = bytearray((kdir / "trisc1.bin").read_bytes())
  n = 0
  # dot-row tile loop: STALLWAIT[SFPU<-MATH] ... STALLWAIT[SYNC<-MATH|SFPU] inside a loop that also waits SRCA|SRCB_VLD
  match = [l for l in ls if not l["spin"] and any("Wait.SRCA_VLD | Wait.SRCB_VLD" in x["rest"] for x in l["body"])
           and any(x["mn"] == "REPLAY" for x in l["body"])]
  for l in match:
    if any(o is not l and l["start"] <= o["start"] and o["end"] <= l["end"] for o in match): continue  # innermost only
    body = l["body"]
    syncs = [x for x in body if x["mn"] == "STALLWAIT" and "stall_res: Stall.SYNC;" in x["rest"] and "Wait.MATH | Wait.SFPU" in x["rest"]]
    for x in syncs[-1:]:
      patch_word(data, x["pc"], int(x["word"], 16), TT_NOP); n += 1
  if n:
    (kdir / "trisc1.bin").write_bytes(data)
    log.append(f"{kernel}/trisc1: {n} per-tile STALLWAIT[SYNC<-MATH|SFPU] -> NOP")

def p_nobarrier(kdir, kernel, log):
  """Probe, racy: BRISC weight-row loop stops waiting for the row's reads to land (NIU outstanding-reads == 0) before
  pushing the row and issuing the next one. TRISC0 may unpack a tile whose bytes are still in flight. Upper bound for
  keeping several rows in flight (per-row transaction IDs)."""
  if kernel not in PROJECTIONS: return
  for s in sorted(kdir.glob("brisc*.S")):
    insns, ls = listing(kdir, s.name)
    by_pc = {i["pc"]: i for i in insns}
    # subroutines that are exactly: lw <noc + 0x244>; beq; jal back; fence; jalr
    waits = {i["pc"] for i in insns if i["mn"] == "lui" and by_pc.get(i["pc"] + 8, {}).get("rest", "").find("regs + 0x244") >= 0
             and by_pc.get(i["pc"] + 0x18, {}).get("mn") == "jalr"}
    stores = [i for i in insns if i["mn"] == "sw" and re.search(r"noc[01]_regs \+ 0x20 ·", i["rest"])]
    # read_pages entry: the loop label containing the last length store; find calls to the subroutine holding it
    last = stores[-1]["pc"]
    entry = max(i["target"] for i in insns if i["mn"] == "jal" and i["rest"].startswith("x1,") and i["target"] is not None and i["target"] <= last)
    data = bytearray((kdir / s.with_suffix(".bin").name).read_bytes())
    n = 0
    for c in [i for i in insns if i["mn"] == "jal" and i["rest"].startswith("x1,") and i["target"] == entry]:
      for d in range(-0x30, 0x14, 4):  # the barrier calls bracketing the read_pages call
        x = by_pc.get(c["pc"] + d)
        if x and x["mn"] == "jal" and x["rest"].startswith("x1,") and x["target"] in waits:
          patch_word(data, x["pc"], int(x["word"], 16), RV_NOP); n += 1
    assert n, (kernel, s.name)
    (kdir / s.with_suffix(".bin").name).write_bytes(data)
    log.append(f"{kernel}/{s.stem}: {n} per-row read barriers -> NOP")

def p_t1halfsfpu(kdir, kernel, log, step=2):
  """Probe, not a fix: NOP every other SFPU REPLAY in the innermost dot loop (half the reduction work)."""
  if kernel not in PROJECTIONS: return
  insns, ls = listing(kdir, "trisc1.S")
  data = bytearray((kdir / "trisc1.bin").read_bytes())
  match = [l for l in ls if not l["spin"] and any("Wait.SRCA_VLD | Wait.SRCB_VLD" in x["rest"] for x in l["body"])
           and any(x["mn"] == "REPLAY" for x in l["body"])]
  n = 0
  for l in match:
    if any(o is not l and l["start"] <= o["start"] and o["end"] <= l["end"] for o in match): continue
    for x in [x for x in l["body"] if x["mn"] == "REPLAY"][step - 1::step]:
      patch_word(data, x["pc"], int(x["word"], 16), TT_NOP); n += 1
  (kdir / "trisc1.bin").write_bytes(data)
  log.append(f"{kernel}/trisc1: {n} dot-loop SFPU REPLAYs -> NOP")

PATCHES = {
  "nobarrier": p_nobarrier,
  "t1halfsfpu": p_t1halfsfpu,
  "t1nosfpu": lambda d, k, log: p_t1halfsfpu(d, k, log, step=1),
  "nodram": p_nodram,
  "t0nodrain": lambda d, k, log: p_t0(d, k, log, True),
  "t0loose": lambda d, k, log: p_t0(d, k, log, False),
  "t0semfix": lambda d, k, log: p_t0(d, k, log, True, semfix=True),
  "t1nosync": p_t1nosync,
}

def build(model, variant):
  out = HERE / "variants" / variant
  if out.exists(): shutil.rmtree(out)
  out.mkdir(parents=True)
  shutil.copytree(ROOT / "kernels" / "zero", out / "zero")
  shutil.copytree(ROOT / "kernels" / f"llama3-{model}", out / f"llama3-{model}")
  log = []
  for part in variant.split("+"):
    if part == "base": continue
    for kdir in sorted((out / f"llama3-{model}").iterdir()):
      if kdir.is_dir(): PATCHES[part](kdir, kdir.name, log)
  return out, log

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--model", default="8b-fp8")
  ap.add_argument("--variant", default="base")
  ap.add_argument("--device", type=int, default=0)
  ap.add_argument("--tokens", type=int, default=24)
  a = ap.parse_args()
  kroot, log = build(a.model, a.variant)
  for line in log: print("patch", line)
  import llama3
  llama3.KERNELS = kroot
  ref = json.loads((ROOT / "kernels" / f"llama3-{a.model}" / "reference.json").read_text())
  want = ref["generated_ids"]
  want = json.loads(want) if isinstance(want, str) else want
  model = llama3.Llama3(a.model, a.device, profile=True)
  try:
    gen, s = model.generate(ref["prompt_ids"], a.tokens)
  finally:
    model.close()
  match = next((i for i, (x, y) in enumerate(zip(gen, want)) if x != y), min(len(gen), len(want)))
  ks = {k: dict(us_per_launch=float(v.mean()), launches_per_token=len(v) // s["tokens"], us_per_token=float(v.sum() / s["tokens"]))
        for k, v in s["kernels"].items()}
  res = dict(model=a.model, variant=a.variant, device=a.device, tokens=s["tokens"], period_us=s["period_us"],
             tokens_match=f"{match}/{min(len(gen), len(want))}", patches=log, kernels=ks, when=time.strftime("%F %T"))
  (HERE / "results").mkdir(exist_ok=True)
  (HERE / "results" / f"{a.model}-{a.variant}.json").write_text(json.dumps(res, indent=1))
  print(f"{a.model} {a.variant}: {s['period_us'] / 1e3:.3f} ms/token, tokens match {res['tokens_match']}")
  for k, v in sorted(ks.items(), key=lambda kv: -kv[1]["us_per_token"]):
    print(f"  {k:<16}{v['us_per_launch']:9.1f} us/launch {v['us_per_token']:9.1f} us/token")

if __name__ == "__main__": main()
