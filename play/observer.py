"""Observer cores: spare Tensix tiles (outside every program's multicast rectangle) that sample chip state over the NoC
while a workload runs, logging {wall clock, values} to their own L1. Started directly by the host, like the queue loops.
"""
import struct, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fw

CFG, LOG, LOG_END = 0x14000, 0x20000, 0x170000
DRAM_EPS = [(x, y) for x in (17, 18) for y in range(12, 24)]
SLV_RD_DATA_WORD_SENT = 0x2CC

def noc_coord(c): return c[0] | c[1] << 6

class Observer:
  def __init__(self, dev, core, targets, period_cycles=1350):
    """targets: [(core, 64-bit address)] of 32-bit registers to sample every period_cycles."""
    self.dev, self.core, self.targets, io = dev, core, targets, dev.iface
    img = fw.program({"brisc": ([str(HERE / "observer_dram.c")], ["-O2", f"-DCFG={CFG:#x}"])})["brisc"]
    words = [len(targets), LOG, LOG_END, period_cycles, 0, 0, 0, 0]
    for c, a in targets: words += [a & 0xFFFFFFFF, a >> 32, noc_coord(c), 0]
    io.write(core, CFG, struct.pack(f"<{len(words)}I", *words))
    io.write(core, fw.CODE["brisc"], img + fw.ret("brisc"))
    io.write32(core, fw.LAUNCH, 1)
    self.rec = 8 + 4 * len(targets)

  def start(self): self.dev.iface.write32(self.core, fw.GO_SIGNAL, 0x80)

  def stop(self):
    io = self.dev.iface
    io.write32(self.core, CFG + 16, 1)
    n = io.read32(self.core, CFG + 20)
    raw = np.frombuffer(io.read(self.core, LOG, n * self.rec), "<u4").reshape(n, -1)
    t = raw[:, 0].astype(np.int64) | raw[:, 1].astype(np.int64) << 32
    return t, raw[:, 2:].astype(np.int64)

def dram_read_targets():  # NoC0 and NoC1 NIUs of all 24 DRAM endpoints
  return [(e, base + SLV_RD_DATA_WORD_SENT) for base in (0x100_FFB2_0000, 0x100_FFB3_0000) for e in DRAM_EPS]

def clean(v, max_step=1 << 20):
  """Counters only move forward, and a DRAM port moves < 1M 64-byte words per sample. Measured: NoC1-NIU counters on
  DRAM tiles occasionally read back a foreign value for one sample (clustered at launch boundaries); hold the last good
  value instead. Returns (cleaned, number of rejected reads)."""
  v, bad = v.copy(), 0
  for i in range(1, len(v)):
    d = (v[i] - v[i - 1]) % (1 << 32)
    m = d > max_step
    bad += int(m.sum())
    v[i, m] = v[i - 1, m]
  return v, bad

def bandwidth(t, v):
  """-> (time midpoints, GB/s) from wrapping 32-bit word counters (64 B per word)."""
  dv = np.diff(v, axis=0) % (1 << 32)
  dt = np.diff(t) / (fw.AICLK_MHZ * 1e6)
  return (t[1:] + t[:-1]) // 2, dv.sum(1) * 64 / dt / 1e9

# ---- debug-bus sampling (signal descriptors from tt-exalens hardware/blackhole/functional_worker_debug_bus_signals.py)
def dbg_select(rd_sel, daisy_sel, sig_sel): return 1 << 29 | rd_sel << 25 | daisy_sel << 16 | sig_sel
PC_SIGNALS = {"brisc": dbg_select(1, 7, 11), "ncrisc": dbg_select(1, 7, 25), "trisc0": dbg_select(1, 7, 13),
              "trisc1": dbg_select(1, 7, 15), "trisc2": dbg_select(1, 7, 17)}
PC_MASK = 0x3FFFFFFF
# One word per Tensix thread with its frontend 'stalled_*' bits (sig_sel 12/8/4 for T0/T1/T2, rd_sel 0, daisy 1)
STALL_SIGNALS = {"t0": dbg_select(0, 1, 12), "t1": dbg_select(0, 1, 8), "t2": dbg_select(0, 1, 4)}
STALL_BITS = {"math": 0x2000000, "sync": 0x100000, "unpack": 0xC000000, "pack": 0x10000000, "cfg": 0x80000,
              "sfpu": 0x40000, "thcon": 0x200000, "move": 0x800000}

class DebugObserver:
  def __init__(self, dev, core, targets, signals):
    assert len(targets) <= 32 and len(signals) <= 24
    self.dev, self.core, self.targets, self.signals, io = dev, core, targets, signals, dev.iface
    img = fw.program({"brisc": ([str(HERE / "observer_dbg.c")], ["-O2", f"-DCFG={CFG:#x}"])})["brisc"]
    words = [len(targets), len(signals), LOG, LOG_END, 0, 0, 0, 0] + [noc_coord(c) for c in targets]
    words += [0] * (40 - len(words)) + list(signals.values())
    io.write(core, CFG, struct.pack(f"<{len(words)}I", *words))
    io.write(core, fw.CODE["brisc"], img + fw.ret("brisc"))
    io.write32(core, fw.LAUNCH, 1)
    self.rec = 8 + 4 * (len(targets) + 1) * len(signals)

  def start(self): self.dev.iface.write32(self.core, fw.GO_SIGNAL, 0x80)

  def stop(self):
    """-> ({signal name: times (sweeps,)}, {signal name: values (sweeps, targets)}); times are when that signal was read"""
    io = self.dev.iface
    io.write32(self.core, CFG + 16, 1)
    n = io.read32(self.core, CFG + 20)
    raw = np.frombuffer(io.read(self.core, LOG, n * self.rec), "<u4").reshape(n, -1)
    t0 = raw[:, 0].astype(np.int64) | raw[:, 1].astype(np.int64) << 32
    body = raw[:, 2:].reshape(n, len(self.signals), len(self.targets) + 1)
    ts = {name: t0 + ((body[:, i, 0].astype(np.int64) - (t0 & 0xFFFFFFFF)) % (1 << 32)) for i, name in enumerate(self.signals)}
    return ts, {name: body[:, i, 1:] for i, name in enumerate(self.signals)}
