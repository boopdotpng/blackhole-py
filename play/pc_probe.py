import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'play')
import numpy as np, fw
from collections import Counter
from llama3 import Llama3, ChatTokenizer
from observer import DebugObserver, PC_SIGNALS, STALL_SIGNALS, PC_MASK
m = Llama3("1b", 0)
try:
  ids = ChatTokenizer(m.checkpoint).chat([{"role": "user", "content": "Hi"}]); m.generate(ids, 2)
  targets = [(x, 3) for x in (1, 2, 3, 4, 5, 6, 7, 10)]
  obs = DebugObserver(m.dev, (15, 3), targets, {**PC_SIGNALS, **STALL_SIGNALS})
  obs.start(); m.generate(ids, 2, start=len(ids) - 1); t, v = obs.stop()
  print(f"{len(t)} sweeps, period {np.diff(t).mean() / 1350:.2f} us")
  for r in fw.ROLES:
    pcs = v[r][:, 0] & PC_MASK
    print(r, "top PCs", [(hex(int(p)), c) for p, c in Counter(pcs.tolist()).most_common(6)])
  for th in STALL_SIGNALS: print(th, "top words", [(hex(int(p)), c) for p, c in Counter(v[th][:, 0].tolist()).most_common(5)])
finally: m.close()
