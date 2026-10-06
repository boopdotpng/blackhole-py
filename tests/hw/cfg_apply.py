"""Apply config.py objects inside a blackhole-py Asm kernel (probe helper, not the real lowering)."""
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))  # after blackhole-py, which owns pcie.py
from config import Space
from firmware.consts import TensixMMIO

def apply(k, *configs):
  """RISC-V sw (whole words) or lw/and/or/sw (partial words) for every SHARED write."""
  for c in configs:
    for (space, _, addr), (value, mask) in c.writes().items():
      assert space is Space.SHARED, f"probe helper only writes SHARED config, got {space}"
      at = TensixMMIO.CFG_BASE + 4 * addr
      if mask == 0xFFFFFFFF:
        k.write(at, value); continue
      word, tmp = k.reg(2)
      k.read(word, at)
      k.li(tmp, ~mask & 0xFFFFFFFF); k.and_(word, word, tmp)
      k.li(tmp, value); k.or_(word, word, tmp)
      k.write(at, word)
