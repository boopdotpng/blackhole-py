import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'play')
import kprof, fw
from llama3 import ChatTokenizer
m = kprof.ProfiledLlama3("1b", 0, profile=True)
try:
  ids = ChatTokenizer(m.checkpoint).chat([{"role": "user", "content": "Hi"}])
  m.generate(ids, 2); m.arm(); m.generate(ids, 1, start=len(ids) - 1)
  ev, _ = m.collect()
  names = {i: n for n, i in m.prog_ids.items()}
  core = (2, 3)
  t0 = ev[core][0][1]
  print("launch seq:", [n for n, _ in m.launches][:8])
  for h, t in ev[core][:70]:
    print(f"{t - t0:8d} {names.get(h >> 7, h >> 7):10} {fw.ROLES[h >> 4 & 7] if (h >> 4 & 7) < 5 else h >> 4 & 7:7} {'END' if h >> 3 & 1 else 'start'}  raw={h:#x}")
finally: m.close()
