"""Apply config.py objects inside a blackhole-py Asm kernel (probe helper, not the real lowering)."""
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))  # after blackhole-py, which owns pcie.py
from config import Region, region, Space, CFG_BASE, CFG_BANK_STRIDE, CFG_DUAL_WRITE, THREAD_CFG_BASE
from firmware.consts import TensixMMIO

def apply(k, *configs):
  """RISC-V writes to the Config banks: sw for whole words (one ConfigDualWrite sw when both banks get the same word),
  lw/and/or/sw per bank for partial words (a dual-write RMW would copy bank 0's other bits into bank 1)."""
  for c in configs:
    writes = c.writes()
    for (space, _, addr), (value, mask) in writes.items():
      assert region((space, None, addr)) is Region.CONFIG, f"probe helper only writes the Config banks, got {space} {addr:#x}"
      full = mask == 0xFFFFFFFF
      in_bank0, in_bank1 = CFG_BASE <= addr < CFG_BASE + CFG_BANK_STRIDE, CFG_BASE + CFG_BANK_STRIDE <= addr < CFG_DUAL_WRITE
      if full and in_bank1 and writes.get((space, None, addr - CFG_BANK_STRIDE)) == (value, mask): continue  # bank 0 wrote both
      if full and in_bank0 and writes.get((space, None, addr + CFG_BANK_STRIDE)) == (value, mask):
        k.write(CFG_DUAL_WRITE + addr - CFG_BASE, value); continue
      if full:
        k.write(addr, value); continue
      word, tmp = k.reg(2)
      k.read(word, addr)
      k.li(tmp, ~mask & 0xFFFFFFFF); k.and_(word, word, tmp)
      k.li(tmp, value); k.or_(word, word, tmp)
      k.write(addr, word)
