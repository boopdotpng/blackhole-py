"""Rotating bank-direction schedule. Slot0 (BRISC) = read stream on NoC0, slot1 (NCRISC) =
write stream on NoC1. Stream j visits one bank per phase (S bytes), 8 phases per cycle,
`cycles` cycles via a runtime loop. Bank for phase p:
  mode rotate : read (p + j%4) % 8          write (p + 4 + j%4) % 8   -> per-bank long runs
  mode mixed  : read (p + j%8) % 8          write (p + j%8 + 3) % 8   -> every bank always mixed
  mode static : read (p + j) % 4            write 4 + (p + j) % 4      -> fixed segregation
Port = (j + bank) % 3. Same DRAM offset in every bank (per-stream region j*S)."""
import sys, json, struct
from statistics import median
sys.path.insert(0, __import__('os').path.dirname(__file__))
from dramx import Bench, ep, pack, ROLES
from asm import Asm
from cq import Run
from pcie import TLBWindow
from program import Program
from ttko.isa import R as RR
from tests.movement import test_noc as n
from noc2 import InterleavedConfig, emit_interleaved_dram_to_l1, emit_l1_to_interleaved_dram
from tests.movement.profile_matmul_fp8 import clock_mhz

dev, out, cases = int(sys.argv[1]), sys.argv[2], json.load(open(sys.argv[3]))
b = Bench(dev)
PG, BT = 2048, 32


def bank_of(mode, d, j, p):
  if mode == 'rotate': return (p + j % 4 + (4 if d == 'w' else 0)) % 8
  if mode == 'mixed': return (p + j % 8 + (3 if d == 'w' else 0)) % 8
  if mode == 'static': return (p + j) % 4 + (4 if d == 'w' else 0)


def image(slot, mode, j, cycles, batch, stride=0):
  d = 'r' if slot == 0 else 'w'
  a = Asm(ROLES[slot])
  stamp = n.TIMING_L1_ADDRESS + slot * 16
  n._record_clock(a, stamp)
  ctr = n.TIMING_L1_ADDRESS + 32 + slot * 4
  t, ad = a.reg(2)
  a.li(t, cycles); a.li(ad, ctr); a.sw(t, ad)
  top = a._new_label('cyc'); done = a._new_label('cyc_done')
  a.label(top)
  for p in range(8):
    bk = bank_of(mode, d, j, p)
    cfg = InterleavedConfig((pack(ep(bk, (j + bk) % 3)),), n.CB_ADDRESS + slot * BT * PG, batch, PG,
                            0 if d == 'r' else 1, command_slot=1 + slot, tid=1 + slot,
                            batch_pages=batch, standalone=True, dram_stride=stride)
    (emit_interleaved_dram_to_l1 if d == 'r' else emit_l1_to_interleaved_dram)(a, cfg, slot * 2, slot * 2 + 1)
  t, ad = a.reg(2)
  a.li(ad, ctr); a.lw(t, ad); a.addi(t, t, -1); a.sw(t, ad)
  a.beq(t, RR.ZERO, done); a.j(top); a.label(done)
  n._record_clock(a, stamp + 8)
  return a.lower()


rows = []
try:
  base = b.region(80 << 20)
  for case in cases:
    N = case.get('cores', 117); S = case['S']; mode = case['mode']
    per_stream = case.get('per_stream', 4 << 20)
    cycles = max(1, per_stream // (8 * S))
    batch = min(BT, S // PG)
    lay = case.get('layout', 'adj')
    images, params, cache = {}, {}, {}
    for j, core in enumerate(b.cores[:N]):
      im = {}
      for slot in (0, 1):
        key = (slot, lay, mode, j % 12 if mode != 'mixed' else j % 24, cycles, batch)
        # j only matters mod lcm(4 or 8, 3) for bank/port choice
        if key not in cache: cache[key] = image(slot, mode, j, cycles, batch, N * PG if lay == 'adj' else 0)
        im[ROLES[slot]] = cache[key]
      images[core] = im
      params[core] = ((base + j * PG, S, base + (40 << 20) + j * PG, S) if lay == 'adj' else (base + j * S, S, base + (40 << 20) + j * S, S))
    l1 = {n.CB_ADDRESS: bytes(range(256)) * (2 * BT * PG // 256)}
    cores = tuple(images)
    b.d.cq.submit(Program(images).commands(params=params, l1=l1), timeout=20)
    total = N * 2 * cycles * 8 * S
    samples, rd, wr = [], [], []
    with TLBWindow(b.d.pcie.fd, cores[0]) as w:
      mhz = clock_mhz(w)
      for _ in range(3):
        b.d.cq.submit((Run(cores),), timeout=30)
        st = []
        for core in cores:
          w.target(0, core); st.append(struct.unpack('<4Q', w.read(n.TIMING_L1_ADDRESS, 32)))
        t0 = min(min(x[0], x[2]) for x in st); t1 = max(max(x[1], x[3]) for x in st)
        samples.append(total * mhz / (t1 - t0) / 1000)
        rd.append((max(x[1] for x in st) - t0) / mhz); wr.append((max(x[3] for x in st) - t0) / mhz)
    row = dict(label=f"{mode} {lay} S={S >> 10}KiB", mode=mode, S=S, cycles=cycles, gb_s=round(median(samples), 1),
               reads_done_us=round(median(rd), 1), writes_done_us=round(median(wr), 1))
    print(json.dumps(row), flush=True); rows.append(row)
    json.dump(rows, open(out, 'w'), indent=1)
finally:
  b.close()
