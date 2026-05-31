from __future__ import annotations

import ctypes
import struct

Core = tuple[int, int]
L1_ALIGN = 16
PCIE_ALIGN = 64

def align_up(value: int, align: int) -> int:
  return (value + align - 1) // align * align

def align_down(value: int, alignment: int) -> tuple[int, int]:
  base = value & ~(alignment - 1)
  return base, value - base

def as_bytes(obj) -> bytes:
  return ctypes.string_at(ctypes.addressof(obj), ctypes.sizeof(obj))

def noc_xy(x: int, y: int) -> int:
  return ((y << 6) | x) & 0xFFFF

class S(ctypes.LittleEndianStructure):
  def __init__(self, **kw):
    super().__init__()
    for k, v in kw.items():
      setattr(self, k, v)

class Dram:
  BANK_COUNT = 8
  TILES_PER_BANK = 3
  WRITE_OFFSET = 0x40
  BARRIER_BASE = 0x0
  ALIGNMENT = 64
  BARRIER_FLAGS = (0xAA, 0xBB)
  BANK_TILE_YS = {
    0: (0, 1, 11), 1: (2, 3, 10), 2: (4, 8, 9), 3: (5, 6, 7),
    4: (0, 1, 11), 5: (2, 3, 10), 6: (4, 8, 9), 7: (5, 6, 7),
  }
  BANK_X = {b: 0 if b < 4 else 9 for b in range(8)}

class P100BankTable:
  NUM_DRAM_BANKS = 7
  NUM_L1_BANKS = 120
  DRAM_BANK_TO_NOC_SIZE = 2 * NUM_DRAM_BANKS * 2
  L1_BANK_TO_NOC_SIZE = 2 * NUM_L1_BANKS * 2
  BANK_TO_DRAM_OFFSET_SIZE = NUM_DRAM_BANKS * 4
  BANK_TO_L1_OFFSET_SIZE = NUM_L1_BANKS * 4
  TOTAL_SIZE = (
    DRAM_BANK_TO_NOC_SIZE + L1_BANK_TO_NOC_SIZE +
    BANK_TO_DRAM_OFFSET_SIZE + BANK_TO_L1_OFFSET_SIZE
  )

def build_bank_noc_table(harvested_dram_bank: int | None, worker_cores: list[Core]) -> bytes:
  num_dram_banks = Dram.BANK_COUNT if harvested_dram_bank is None else Dram.BANK_COUNT - 1
  num_l1_banks = len(worker_cores)
  nocs, ports = 2, 3
  bank_port = [[2, 1], [0, 1], [0, 1], [0, 1], [2, 1], [2, 1], [2, 1], [2, 1]]

  if harvested_dram_bank is None:
    bank_xy = {b: (17 if b < 4 else 18, 12 + (b % 4) * ports) for b in range(Dram.BANK_COUNT)}
  else:
    h = harvested_dram_bank
    half = 4
    mirror = h + half - 1 if h < half else h - half
    if h < half:
      right = list(range(half - 1))
      left = [b for b in range(half - 1, Dram.BANK_COUNT - 1) if b != mirror] + [mirror]
    else:
      left = [b for b in range(half) if b != mirror] + [mirror]
      right = list(range(half, Dram.BANK_COUNT - 1))
    bank_xy = {b: (18, 12 + i * ports) for i, b in enumerate(right)}
    bank_xy.update({b: (17, 12 + i * ports) for i, b in enumerate(left)})

  dram = []
  for noc in range(nocs):
    for b in range(num_dram_banks):
      x, y0 = bank_xy[b]
      dram.append(noc_xy(x, y0 + bank_port[b][noc]))

  cols = sorted({x for x, _ in worker_cores})
  l1 = []
  for _ in range(nocs):
    for i in range(num_l1_banks):
      l1.append(noc_xy(cols[i % len(cols)], 2 + (i // len(cols)) % 10))

  return struct.pack(f"<{len(dram)}H{len(l1)}H{num_dram_banks + num_l1_banks}i", *dram, *l1, *([0] * (num_dram_banks + num_l1_banks)))
