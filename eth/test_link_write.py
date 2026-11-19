# Step 2: E1 on card SRC ch CH sends over TT-link queue 2 into the peer Ethernet core's L1 on card DST.
# Usage: test_link_write.py [SRC=1] [DST=0] [CH=11]
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e1 import E1, build
from system import PCIIface

src_card, dst_card, ch = (int(a) for a in (sys.argv[1:] + ["1", "0", "11"][len(sys.argv) - 1:])[:3])
BOX, PAYLOAD, REMOTE, FLAG = 0x30000, 0x31000, 0x8000, 0x8400
OP_SEND, OP_REG = 1, 2

tx, rx = PCIIface(src_card), PCIIface(dst_card)
try:
  e = E1(tx, ch)
  peer = e.core  # straight-across cabling: same channel on the other card
  for a in (REMOTE, FLAG): assert not any(rx.read(peer, a, 64)), f"card {dst_card} {a:#x} is not empty"
  pcs0, hb0 = rx.read32(peer, 0xFFB9800C), rx.read32(peer, 0x7CC70)
  tx.write(e.core, BOX, bytes(64))
  e.start(build("e1_link.c"))
  r = lambda a: tx.read32(e.core, a)
  t = time.time()
  while r(BOX) != 0xE1A11E4C:
    assert time.time() - t < 1, "E1 did not start"
  req = [0]
  def cmd(op, src, dst, n, rep=1):
    for i, v in enumerate((op, src, dst, n, rep)): tx.write32(e.core, BOX + 16 + 4 * i, v)
    req[0] += 1; tx.write32(e.core, BOX + 8, req[0])
    t = time.time()
    while r(BOX + 12) != req[0]:
      assert time.time() - t < 1, f"E1 stuck on op {op}"
    return r(BOX + 36)

  pattern = bytes((i * 37 + 11) & 0xFF for i in range(256))
  tx.write(e.core, PAYLOAD, pattern)
  cyc = cmd(OP_SEND, PAYLOAD, REMOTE, len(pattern))
  cyc2 = cmd(OP_REG, 0, FLAG, 0x600DF00D)
  time.sleep(0.001)
  got, flag = rx.read(peer, REMOTE, len(pattern)), rx.read32(peer, FLAG)
  print(f"send {len(pattern)} B: {cyc} cycles; reg write: {cyc2} cycles")
  print(f"card {dst_card} {REMOTE:#x}: {'match' if got == pattern else 'MISMATCH ' + got[:32].hex()}  flag {flag:#x}")
  print(f"card {dst_card} pcs {pcs0:#x} -> {rx.read32(peer, 0xFFB9800C):#x}  heartbeat {hb0:#x} -> {rx.read32(peer, 0x7CC70):#x}")
  ok = got == pattern and flag == 0x600DF00D
  e.stop()
  rx.write(peer, REMOTE, bytes(len(pattern))); rx.write32(peer, FLAG, 0)  # leave card DST's L1 as we found it
  print("PASS" if ok else "FAIL")
finally:
  tx.close(); rx.close()
