"""Time-phased R/W: each RISC alternates read chunk (NoC0) and write chunk (NoC1),
`rounds` times, all 8 banks, rotated 3 ports. Same region is re-read/re-written each round.
order: 'inphase' (all cores read first) | 'anti' (odd cores write first).
Args: device out.json cases.json  (case: name, f, rounds, order, cores, total_per_core)"""
import sys, json, struct
from statistics import median
sys.path.insert(0, __import__('os').path.dirname(__file__))
import cores140
from dramx import Bench, ep, pack, ROLES
from asm import Asm
from cq import Run
from pcie import TLBWindow
from program import Program
from tests.movement import test_noc as n
from tests.movement.noc import InterleavedConfig, emit_interleaved_dram_to_l1, emit_l1_to_interleaved_dram
from tests.movement.profile_matmul_fp8 import clock_mhz

dev, out, cases = int(sys.argv[1]), sys.argv[2], json.load(open(sys.argv[3]))
b = Bench(dev)
PG, BT = 2048, 32
rows = []


def image(slot, k, rounds, write_first):
  a = Asm(ROLES[slot])
  stamp = n.TIMING_L1_ADDRESS + slot * 16
  n._record_clock(a, stamp)
  rc = tuple(pack(ep(bk, (k + bk) % 3)) for bk in range(8))
  wc = tuple(pack(ep(bk, (k + 1 + bk) % 3)) for bk in range(8))
  base = n.CB_ADDRESS + slot * 2 * BT * PG
  rcfg = InterleavedConfig(rc, base, BT, PG, 0, command_slot=1 + slot, tid=1 + slot, batch_pages=BT, standalone=True)
  wcfg = InterleavedConfig(wc, base + BT * PG, BT, PG, 1, command_slot=1 + slot, tid=3 + slot, batch_pages=BT, standalone=True)
  p = slot * 4
  from ttko.isa import R as RR
  ctr = n.TIMING_L1_ADDRESS + 32 + slot * 4
  t, ad = a.reg(2)
  a.li(t, rounds); a.li(ad, ctr); a.sw(t, ad)
  top = a._new_label('round'); done = a._new_label('rounds_done')
  a.label(top)
  seq = [('w', wcfg, p + 2, p + 3), ('r', rcfg, p, p + 1)] if write_first else [('r', rcfg, p, p + 1), ('w', wcfg, p + 2, p + 3)]
  for d, cfg, s0, s1 in seq:
    (emit_l1_to_interleaved_dram if d == 'w' else emit_interleaved_dram_to_l1)(a, cfg, s0, s1)
  t, ad = a.reg(2)
  a.li(ad, ctr); a.lw(t, ad); a.addi(t, t, -1); a.sw(t, ad)
  a.beq(t, RR.ZERO, done); a.j(top); a.label(done)
  n._record_clock(a, stamp + 8)
  return a.lower()


try:
  base = b.region(160 << 20)
  for case in cases:
    N = case.get('cores', 117); rounds = case['rounds']; f = case['f']
    tot = case.get('total_per_core', 4 << 20) // 2  # per RISC
    unit = 8 * PG
    rbytes = int(tot * (1 - f) / rounds) // unit * unit
    wbytes = max(unit, int(tot * f / rounds) // unit * unit)
    images, params, cache = {}, {}, {}
    k = 0
    for i, core in enumerate(b.cores[:N]):
      wf = case['order'] == 'anti' and i % 2 == 1
      im, words = {}, []
      for slot in (0, 1):
        key = (slot, k % 3, rounds, wf)
        if key not in cache: cache[key] = image(slot, k % 3, rounds, wf)
        im[ROLES[slot]] = cache[key]
        ra = base + (k * 2) * (tot // 8 + unit)
        words += [ra, rbytes, ra + tot // 8 + unit, wbytes]
        k += 1
      images[core] = im; params[core] = tuple(words)
    l1 = {n.CB_ADDRESS: bytes(range(256)) * (4 * BT * PG // 256)}
    cores = tuple(images)
    b.d.cq.submit(Program(images).commands(params=params, l1=l1), timeout=20)
    total = N * 2 * rounds * (rbytes + wbytes)
    samples = []
    with TLBWindow(b.d.pcie.fd, cores[0]) as w:
      mhz = clock_mhz(w)
      for _ in range(3):
        b.d.cq.submit((Run(cores),), timeout=30)
        st = []
        for core in cores:
          w.target(0, core); st += list(zip(*[iter(struct.unpack('<4Q', w.read(n.TIMING_L1_ADDRESS, 32)))] * 2))
        samples.append(total * mhz / (max(e for _, e in st) - min(s for s, _ in st)) / 1000)
    row = dict(label=case['name'], gb_s=round(median(samples), 1),
               write_frac=round(wbytes / (rbytes + wbytes), 3), chunk_kib=(rbytes + wbytes) * N * 2 >> 10)
    print(json.dumps(row), flush=True); rows.append(row)
    json.dump(rows, open(out, 'w'), indent=1)
finally:
  b.close()
