"""Are DRAM-tile NIU slave counters readable over NoC, and do they add up to the bytes a decode token reads?"""
import sys; sys.path.insert(0, '.')
from llama3 import Llama3, ChatTokenizer
DRAM_NIU = 0x100_FFB2_0000  # NoC0 NIU of a DRAM tile, per tt-isa-documentation BlackholeA0/NoC/MemoryMap.md
CNT = {"SLV_RD_DATA_WORD_SENT": 0x2CC, "SLV_RD_REQ_RECEIVED": 0x2D4, "SLV_NONPOSTED_WR_DATA_WORD_RECEIVED": 0x2E0, "SLV_POSTED_WR_DATA_WORD_RECEIVED": 0x2E4}
EPS = [(x, y) for x in (17, 18) for y in range(12, 24)]
m = Llama3("1b", 0)
try:
  io = m.dev.iface
  def snap(niu_off=0): return {(e, k): io.read32(e, DRAM_NIU + niu_off + o) for e in EPS for k, o in CNT.items()}
  ids = ChatTokenizer(m.checkpoint).chat([{"role": "user", "content": "Hi"}])
  m.generate(ids, 3)
  for niu, off in (("NoC0", 0), ("NoC1", 0x10000)):
    a = snap(off); m.generate(ids, 3, start=len(ids) - 1); b = snap(off)
    d = {k: (b[k] - a[k]) & 0xFFFFFFFF for k in a}
    for k in CNT:
      tot = sum(v for (e, kk), v in d.items() if kk == k)
      per = [d[(e, k)] for e in EPS]
      print(f"{niu} {k:38} total {tot:>12}  x64B = {tot * 64 / 1e9:7.3f} GB   per endpoint min/max {min(per)}/{max(per)}")
  print("expected weight bytes per 3 tokens ~", 3 * 2.47, "GB (1B BF16, LM head tied)")
finally: m.close()
