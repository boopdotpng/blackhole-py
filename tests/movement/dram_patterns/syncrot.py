"""Wall-clock-synchronized direction flipping.
BRISC = read stream (NoC0), NCRISC = write stream (NoC1). Phase p starts at t0 + p*T
(global tile wall clock). Even phases: reads stripe banks 0-3, writes 4-7; odd: swapped
(mode 'flip'). mode 'static': never swap (upper bound, same code). T=0 => no sync.
Case: S (bytes/stream/phase), margin (T = margin * ideal), mode, f (write fraction; read and
write phase windows are equal length, but per-stream bytes scaled by f)."""
import sys, json, struct, time
from statistics import median
sys.path.insert(0, __import__('os').path.dirname(__file__))
from dramx import Bench, ep, pack, ROLES
from asm import Asm
from cq import Run
from pcie import TLBWindow
from program import Program
from ttko.isa import R as RR
from firmware.consts import TensixMMIO
from tests.movement import test_noc as n
from noc2 import InterleavedConfig, emit_interleaved_dram_to_l1, emit_l1_to_interleaved_dram
from tests.movement.profile_matmul_fp8 import clock_mhz

dev, out, cases = int(sys.argv[1]), sys.argv[2], json.load(open(sys.argv[3]))
b = Bench(dev)
PG, BT = 2048, 32
SCR = n.TIMING_L1_ADDRESS + 40   # per-slot 4-byte phase target (low 32 bits of wall clock)
LO, HI = [0, 1, 2, 3], [4, 5, 6, 7]


def wait_and_advance(a, slot, T):
  tgt, ad, clk, now, d, tr = a.reg(6)
  a.li(ad, SCR + slot * 4); a.lw(tgt, ad)
  a.li(clk, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L)
  spin = a._new_label('spin'); go = a._new_label('go')
  a.label(spin)
  a.lw(now, clk); a.sub(d, now, tgt); a.bge(d, RR.ZERO, go); a.j(spin)
  a.label(go)
  a.li(tr, T); a.add(tgt, tgt, tr); a.sw(tgt, ad)


def image(slot, j, mode, cycles, nbytes, T, N, k):
  d = 'r' if slot == 0 else 'w'
  a = Asm(ROLES[slot])
  stamp = n.TIMING_L1_ADDRESS + slot * 16
  n._record_clock(a, stamp)
  ctr = n.TIMING_L1_ADDRESS + 48 + slot * 4
  t, ad = a.reg(2)
  a.li(t, cycles); a.li(ad, ctr); a.sw(t, ad)
  top = a._new_label('cyc'); done = a._new_label('cyc_done')
  a.label(top)
  for p in range(8 if mode == 'rot' else 1):
    wb = [(p + i) % 8 for i in range(k)] if mode == 'rot' else list(range(8 - k, 8))
    banks = wb if d == 'w' else [x for x in range(8) if x not in wb]
    if mode == 'inter': banks = list(range(8))
    rot = j % len(banks); banks = banks[rot:] + banks[:rot]
    coords = tuple(pack(ep(bk, (j + bk) % 3)) for bk in banks)
    cfg = InterleavedConfig(coords, n.CB_ADDRESS + slot * BT * PG, BT, PG, 0 if d == 'r' else 1,
                            command_slot=1 + slot, tid=1 + slot, batch_pages=min(BT, nbytes // PG),
                            standalone=True, dram_stride=N * PG)
    if T: wait_and_advance(a, slot, T)
    (emit_interleaved_dram_to_l1 if d == 'r' else emit_l1_to_interleaved_dram)(a, cfg, slot * 2, slot * 2 + 1)
  t, ad = a.reg(2)
  a.li(ad, ctr); a.lw(t, ad); a.addi(t, t, -1); a.sw(t, ad)
  a.beq(t, RR.ZERO, done); a.j(top); a.label(done)
  n._record_clock(a, stamp + 8)
  return a.lower()


rows = []
last = None  # (max end stamp, host time when read)
try:
  base = b.region(80 << 20)
  with TLBWindow(b.d.pcie.fd, b.cores[0]) as w:
    mhz = clock_mhz(w)
  for case in cases:
    N = case.get('cores', 117); S = case['S']; mode = case['mode']; k = case['k']
    per_stream = case.get('per_stream', 4 << 20)
    rS = S // ((8 - k) * PG) * (8 - k) * PG
    wS = max(k * PG, round(rS * k / (8 - k) / (k * PG)) * k * PG)
    if mode == 'inter':
      k = 0
    ph = 8 if mode == 'rot' else 1
    cycles = max(1, per_stream // (ph * rS))
    ideal_cyc = int(N * rS / ((8 - case['k']) * 62e9) * mhz * 1e6)
    T = int(ideal_cyc * case['margin']) if case['margin'] else 0
    images, params, cache = {}, {}, {}
    for j, core in enumerate(b.cores[:N]):
      im = {}
      for slot in (0, 1):
        key = (slot, j)
        if key not in cache: cache[key] = image(slot, j, mode, cycles, rS if slot == 0 else wS, T, N, k)
        im[ROLES[slot]] = cache[key]
      images[core] = im
      params[core] = (base + j * PG, rS, base + (40 << 20) + j * PG, wS)
    l1 = {n.CB_ADDRESS: bytes(range(256)) * (2 * BT * PG // 256)}
    cores = tuple(images)
    b.d.cq.submit(Program(images).commands(params=params, l1=l1), timeout=20)
    total = N * cycles * ph * (rS + wS)
    samples = []
    with TLBWindow(b.d.pcie.fd, cores[0]) as w:
      for it in range(3):
        WC = TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L
        w.target(WC & -w.SIZE, cores[0])
        now = struct.unpack('<I', w.read(WC - (WC & -w.SIZE), 4))[0]
        t0 = (now + int(0.005 * mhz * 1e6)) & 0xFFFFFFFF
        w.target(SCR & -w.SIZE, (1, 2), b.d.pcie.tensix_end)  # broadcast to all tensix
        w.write(SCR - (SCR & -w.SIZE), struct.pack('<II', t0, t0))
        b.d.cq.submit((Run(cores),), timeout=30)
        st = []
        for core in cores:
          w.target(0, core); st.append(struct.unpack('<4Q', w.read(n.TIMING_L1_ADDRESS, 32)))
        end = max(max(x[1], x[3]) for x in st)
        last = (end, time.perf_counter())
        start = min(min(x[0], x[2]) for x in st)
        if T:
          # start of useful work = t0 (64-bit reconstruct from start stamp's high bits)
          t0_64 = (start & ~0xFFFFFFFF) | t0
          if t0_64 < start - (1 << 31): t0_64 += 1 << 32
          start = max(start, t0_64)
        samples.append(total * mhz / (end - start) / 1000)
    row = dict(label=f"{mode} f={wS/(rS+wS):.3f} k={case['k']} margin={case['margin']}", gb_s=round(median(samples), 1),
               cycles=cycles, T_us=round(T / mhz, 2), min=round(min(samples), 1), max=round(max(samples), 1))
    print(json.dumps(row), flush=True); rows.append(row)
    json.dump(rows, open(out, 'w'), indent=1)
finally:
  b.close()
