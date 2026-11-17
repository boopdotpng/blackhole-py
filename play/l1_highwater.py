"""Poison high worker L1, decode a few tokens, report the highest byte any kernel wrote (per program set)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llama3 import Llama3, ChatTokenizer
LO, HI, PAT = 0x0C0000, 0x180000, b"\xa5"
model = Llama3(sys.argv[1] if len(sys.argv) > 1 else "1b", 0)
try:
  io, workers = model.dev.iface, model.dev.workers
  for c in workers: io.write(c, LO, PAT * (HI - LO))
  ids = ChatTokenizer(model.checkpoint).chat([{"role": "user", "content": "Hi"}])
  model.generate(ids, 4)
  top = {}
  for c in workers:
    raw = io.read(c, LO, HI - LO)
    dirty = [i for i in range(0, len(raw), 4096) if raw[i:i + 4096] != PAT * len(raw[i:i + 4096])]
    if dirty:
      last = dirty[-1]; blk = raw[last:last + 4096]
      top[c] = LO + last + max(i for i in range(len(blk)) if blk[i] != 0xA5)
  hw = max(top.values()) if top else None
  print(f"{len(top)}/{len(workers)} cores wrote above {LO:#x}; highest byte written {hw and hex(hw)}; free above {hw and hex((hw | 0xFFF) + 1)}")
finally:
  model.close()
