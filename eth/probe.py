# Read-only look at one Ethernet tile: reset state, ERISC PCs, base FW heartbeat, and L1 we plan to use.
import sys, time
sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from system import PCIIface
ETH_X = [1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10]
card, ch = int(sys.argv[1]), int(sys.argv[2])
core = (ETH_X[ch], 1)
d = PCIIface(card)
try:
  r = lambda a: d.read32(core, a)
  hb = r(0x7CC70)
  print(f"card {card} ch {ch} core {core}")
  print(f"soft_reset {r(0xFFB121B0):#x}  erisc0_pc {r(0xFFB14000):#x}  erisc1_pc {r(0xFFB14008):#x}")
  print(f"pcs_status {r(0xFFB9800C):#x}  port_status {r(0x7CC04):#x}  heartbeat {hb:#x}", end="")
  time.sleep(0.05); print(f" -> {r(0x7CC70):#x}")
  print("mailboxes", [hex(r(0x7D000 + 16 * i)) for i in range(4)])
  for base in (0x8000, 0x20000, 0x30000):
    words = [r(base + 4 * i) for i in range(8)]
    print(f"{base:#x}:", " ".join(f"{w:08x}" for w in words))
finally:
  d.close()
