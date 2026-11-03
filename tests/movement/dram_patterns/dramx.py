"""Flexible DRAM traffic-pattern experiments on Blackhole p150a.

Each worker runs up to two streams (BRISC slot 0, NCRISC slot 1). A stream is
(direction, noc, endpoint coordinate list, dram base, bytes, posted). Endpoints
are virtual coords: bank b, port p -> x = 17 + b//4, y = 12 + 3*(b%4) + p.
Reuses the validated emitter in tests/movement/noc.py unchanged.
"""
import json, struct, sys, time
from pathlib import Path
from statistics import median
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from asm import Asm
from cq import Run
from device import Device
from pcie import TLBWindow
from program import Program
from tests.movement import test_noc as n
from tests.movement.noc import InterleavedConfig, emit_interleaved_dram_to_l1, emit_l1_to_interleaved_dram
from tests.movement.profile_matmul_fp8 import clock_mhz

ROLES = ('brisc', 'ncrisc')


def ep(bank, port):
  return (17 + bank // 4, 12 + 3 * (bank % 4) + port)


def pack(xy):
  return xy[0] | xy[1] << 6


class Bench:
  def __init__(self, device_id, page=2048, batch=32):
    self.d = Device(device_id)
    self.d.boot()
    self.page, self.batch = page, batch
    self.cores = self.d.cores
    self.buf = None
    self._cache = {}

  def close(self):
    self.d.close()

  def region(self, per_bank_bytes):
    """Same base address valid in every bank, per_bank_bytes long."""
    if self.buf is None or self.buf_per_bank < per_bank_bytes:
      self.buf = self.d.alloc_interleaved_dram(per_bank_bytes * 8, page_size=self.page)
      self.buf_per_bank = per_bank_bytes
    return self.buf.address

  def image(self, slot, direction, noc, coords, posted):
    key = (slot, direction, noc, coords, posted)
    if key not in self._cache:
      cfg = InterleavedConfig(tuple(pack(c) for c in coords),
                              n.CB_ADDRESS + slot * self.batch * self.page, self.batch, self.page,
                              noc, command_slot=1 + slot, tid=1 + slot,
                              batch_pages=self.batch, standalone=True, posted_write=posted)
      a = Asm(ROLES[slot])
      stamp = n.TIMING_L1_ADDRESS + slot * 16
      n._record_clock(a, stamp)
      (emit_interleaved_dram_to_l1 if direction == 'read' else emit_l1_to_interleaved_dram)(a, cfg, slot * 2, slot * 2 + 1)
      n._record_clock(a, stamp + 8)
      self._cache[key] = a.lower()
    return self._cache[key]

  def run(self, plan, runs=3, label=None):
    """plan: {core: [stream dicts with slot, dir, noc, coords, addr, bytes, posted]}"""
    images, params, l1 = {}, {}, {}
    rd = wr = 0
    for core, streams in plan.items():
      im, words = {}, [0, 0, 0, 0]
      for s in streams:
        im[ROLES[s['slot']]] = self.image(s['slot'], s['dir'], s['noc'], tuple(s['coords']), s.get('posted', False))
        words[s['slot'] * 2] = s['addr']; words[s['slot'] * 2 + 1] = s['bytes']
        if s['dir'] == 'read': rd += s['bytes']
        else: wr += s['bytes']
      images[core] = im
      params[core] = tuple(words)
    for slot in (0, 1):
      l1[n.CB_ADDRESS + slot * self.batch * self.page] = bytes(range(256)) * (self.batch * self.page // 256)
    cores = tuple(plan)
    self.d.cq.submit(Program(images).commands(params=params, l1=l1), timeout=20)
    samples = []
    with TLBWindow(self.d.pcie.fd, cores[0]) as w:
      mhz = clock_mhz(w)
      for _ in range(runs):
        self.d.cq.submit((Run(cores),), timeout=20)
        st = []
        per = {}
        for core, streams in plan.items():
          w.target(0, core)
          raw = struct.unpack('<4Q', w.read(n.TIMING_L1_ADDRESS, 32))
          for s in streams:
            a, b = raw[s['slot'] * 2], raw[s['slot'] * 2 + 1]
            st.append((a, b))
            per.setdefault(s.get('tag', s['dir']), []).append((a, b, s['bytes']))
        cyc = max(b for _, b in st) - min(a for a, _ in st)
        samples.append(dict(gb_s=(rd + wr) * mhz / cyc / 1000, us=cyc / mhz,
                            tags={k: sum(x[2] for x in v) * mhz / (max(x[1] for x in v) - min(x[0] for x in v)) / 1000
                                  for k, v in per.items()}))
    best = median(s['gb_s'] for s in samples)
    tags = {k: round(median(s['tags'][k] for s in samples), 1) for k in samples[0]['tags']}
    row = dict(label=label, gb_s=round(best, 1), read_bytes=rd, write_bytes=wr,
               read_gb_s=round(best * rd / (rd + wr), 1), write_gb_s=round(best * wr / (rd + wr), 1),
               tags=tags, mhz=mhz, us=round(median(s['us'] for s in samples), 1))
    print(json.dumps(row), flush=True)
    return row
