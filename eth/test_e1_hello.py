# Step 1: E1 on one channel runs our code. Usage: test_e1_hello.py CARD CH [--leave]  (--leave: exit without stop(),
# so the KMD's close-time cleanup is what parks E1; check with probe.py afterwards)
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e1 import E1, build, SOFT_RESET
from system import PCIIface

card, ch, leave = int(sys.argv[1]), int(sys.argv[2]), "--leave" in sys.argv
S = 0x30000
img = build("e1_hello.c")
print(f"image {len(img)} bytes")
d = PCIIface(card)
try:
  e = E1(d, ch)
  r = lambda a: d.read32(e.core, a)
  hb0 = r(0x7CC70)
  d.write(e.core, S, bytes(16))
  e.start(img)
  time.sleep(0.01)
  c0 = r(S + 4); time.sleep(0.1); c1 = r(S + 4)
  d.write32(e.core, S + 8, 41); time.sleep(0.001)
  print(f"magic {r(S):#x}  counter {c0} -> {c1} in 100 ms  echo {r(S + 12)}")
  print(f"soft_reset {r(SOFT_RESET):#x}  pcs {r(0xFFB9800C):#x}  base fw heartbeat {hb0:#x} -> {r(0x7CC70):#x}")
  ok = r(S) == 0xE1A1C0DE and c1 > c0 and r(S + 12) == 42
  if not leave: e.stop(); time.sleep(0.01); print(f"stopped: soft_reset {r(SOFT_RESET):#x}")
  print("PASS" if ok else "FAIL")
finally:
  d.close()
