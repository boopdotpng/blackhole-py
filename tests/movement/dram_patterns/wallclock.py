import sys, struct, time
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[3]))
from device import Device
from pcie import TLBWindow
d = Device(0)
A = 0xFFB121F0
with TLBWindow(d.pcie.fd, d.cores[0]) as w:
  for core in (d.cores[0], d.cores[-1]):
    w.target(A & -w.SIZE, core)
    a = struct.unpack('<I', w.read(A - (A & -w.SIZE), 4))[0]; t = time.perf_counter()
    time.sleep(0.01)
    b_ = struct.unpack('<I', w.read(A - (A & -w.SIZE), 4))[0]; t2 = time.perf_counter()
    print(core, a, b_, 'MHz est', (b_ - a) / (t2 - t) / 1e6)
