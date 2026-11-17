"""Step 0: does the Blackhole debug timestamper work, with all five RISCs writing at once? What does a stamp cost?"""
import struct, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fw
from ops_blackhole import BlackholeDevice, BlackholeComputeQueue, blackhole_build_program

TSREG, CNTL, STATUS, B0S, B0E, B1S, B1E = 0xFFB121FC, 0xFFB12200, 0xFFB12204, 0xFFB12208, 0xFFB1220C, 0xFFB12210, 0xFFB12214
RING, RING_SIZE, RESULT = 0x170000, 0x10000, 0x16F000
N, K = 64, 256

def configure(io, core, base=RING, size=RING_SIZE):
  io.write32(core, CNTL, 1 << 31 | 1); io.write32(core, CNTL, 1)   # pulse reset_streams, buf0 valid only
  io.write32(core, STATUS, 0x33)                                   # clear full/overflow, zero position
  io.write32(core, B0S, base // 16); io.write32(core, B0E, (base + size) // 16 - 1)
  io.write(core, base, bytes(size))

def read_ring(io, core, base=RING):
  st = io.read32(core, STATUS); pos = st >> 14
  raw = io.read(core, base, pos * 16)
  ev = [struct.unpack_from("<4I", raw, 16 * i) for i in range(pos)]
  return st, [(h, lo | hi << 32) for h, lo, hi, _ in ev]

def main(device=0):
  dev = BlackholeDevice(f"BLACKHOLE:{device}")
  try:
    core = dev.workers[0]
    imgs = {r: fw.program({r: ([str(HERE / "ts_kernel.c")], ["-O2", f"-DROLE={i}", f"-DN={N}", f"-DK={K}", f"-DRESULT={RESULT:#x}",
                                f"-DRET={fw.RETURN[r]:#x}"])})[r] for i, r in enumerate(fw.ROLES)}
    configure(dev.iface, core)
    prg = blackhole_build_program(dev, {core: imgs})
    BlackholeComputeQueue().exec(prg).signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
    dev.synchronize()
    st, ev = read_ring(dev.iface, core)
    print(f"status {st:#x}: position {st >> 14} x16B, full {st & 1}, overflow {st >> 4 & 1}; {len(ev)} events")
    by = {}
    for h, t in ev: by.setdefault(h >> 24, []).append((h >> 3 & 0x1FFFFF, t, h & 7))
    for role, xs in sorted(by.items()):
      seq = [s for s, _, _ in xs if s != 0xFFF]; ts = [t for _, t, _ in xs]
      print(f"  {fw.ROLES[role]:7} events {len(xs):4} seq ok {seq == list(range(N))} ts monotonic {ts == sorted(ts)} "
            f"first {ts[0] - ev[0][1]:6} last {ts[-1] - ev[0][1]:6} low bits {set(x for *_, x in xs)}")
    for i, r in enumerate(fw.ROLES):
      a, b = struct.unpack("<2I", dev.iface.read(core, RESULT + 16 * i, 8))
      print(f"  {r:7} {K} stamps {a} cycles ({a / K:.2f}/stamp), {K} nops {b} cycles")
    w = dev.iface.read32(core, 0xFFB121F0)
    print("ring timestamps vs wall clock now:", w - (ev[-1][1] & 0xFFFFFFFF), "cycles ago")
  finally:
    dev.close()

if __name__ == "__main__": main(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
