from __future__ import annotations

import ctypes
import os
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


class TensixL1:
  SIZE = 0x180000
  LAUNCH = 0x70
  GO_MSG = 0x370
  GO_MSG_INDEX = 0x3A0
  KERNEL_CONFIG_BASE = 0x86B0
  BRISC_FIRMWARE_BASE = 0x3840
  DATA_BUFFER_SPACE_BASE = 0x37000
  TIMING_CONTROL = 0x9C0

  FW_INIT_SCRATCH_BASE = 0x82B0
  BRISC_INIT_LOCAL_L1_BASE_SCRATCH = 0x82B0
  NCRISC_INIT_LOCAL_L1_BASE_SCRATCH = 0xA2B0
  TRISC0_INIT_LOCAL_L1_BASE_SCRATCH = 0xC2B0
  TRISC1_INIT_LOCAL_L1_BASE_SCRATCH = 0xD2B0
  TRISC2_INIT_LOCAL_L1_BASE_SCRATCH = 0xE2B0
  NCRISC_INIT_IRAM_L1_BASE_SCRATCH = 0xF2B0
  MEM_BANK_TO_NOC_SCRATCH = 0x112B0
  LOGICAL_TO_VIRTUAL_SCRATCH = 0x11AB0


class TensixMMIO:
  LOCAL_RAM_START = 0xFFB00000
  LOCAL_RAM_END = 0xFFB01FFF
  NCRISC_HALT_RESUME_ADDR = 0x60
  RISCV_DEBUG_REG_SOFT_RESET_0 = 0xFFB121B0
  RISCV_TDMA_REG_CLK_GATE_EN = 0xFFB11024
  RISCV_DEBUG_REG_WALL_CLOCK_L = 0xFFB121F0
  RISCV_DEBUG_REG_WALL_CLOCK_H = 0xFFB121F8
  RISCV_DEBUG_REG_TRISC0_RESET_PC = 0xFFB12228
  RISCV_DEBUG_REG_TRISC1_RESET_PC = 0xFFB1222C
  RISCV_DEBUG_REG_TRISC2_RESET_PC = 0xFFB12230
  RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE = 0xFFB12234
  RISCV_DEBUG_REG_NCRISC_RESET_PC = 0xFFB12238
  RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE = 0xFFB1223C
  RISCV_DEBUG_REG_DEST_CG_CTRL = 0xFFB12240
  SOFT_RESET_ALL = 0x47800
  SOFT_RESET_BRISC_ONLY_RUN = 0x47000


class Arc:
  NOC_BASE = 0x80000000
  RESET_UNIT_OFFSET = 0x30000
  SCRATCH_RAM_12 = RESET_UNIT_OFFSET + 0x430
  SCRATCH_RAM_13 = RESET_UNIT_OFFSET + 0x434
  TAG_TENSIX_ENABLED_COL = 34
  DEFAULT_TENSIX_ENABLED = 0x3FFF
  TAG_GDDR_ENABLED = 36
  DEFAULT_GDDR_ENABLED = 0xFF


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


class Firmware:
  BRISC_STACK_TOP = 0xFFB01FF0
  NCRISC_STACK_TOP = 0xFFB01FF0
  TRISC_STACK_TOP = 0xFFB00FF0
  TRISC_GLOBAL_POINTER = 0xFFB007F0

  TEXT_BASE = {
    "brisc": 0x3840,
    "ncrisc": 0x5440,
    "trisc0": 0x5A40,
    "trisc1": 0x6040,
    "trisc2": 0x6640,
  }
  TRISC_TEXT_BASE = {
    0: TEXT_BASE["trisc0"],
    1: TEXT_BASE["trisc1"],
    2: TEXT_BASE["trisc2"],
  }
  LOCAL_DATA_BASE = {
    "brisc": 0x82B0,
    "ncrisc": 0xA2B0,
    "trisc0": 0xC2B0,
    "trisc1": 0xD2B0,
    "trisc2": 0xE2B0,
  }
  TRISC_LOCAL_DATA_BASE = {
    0: LOCAL_DATA_BASE["trisc0"],
    1: LOCAL_DATA_BASE["trisc1"],
    2: LOCAL_DATA_BASE["trisc2"],
  }
  LOCAL_DATA_SIZE = {
    "brisc": 0x878,
    "ncrisc": 0x864,
    "trisc0": 1056,
    "trisc1": 28,
    "trisc2": 1056,
  }
  TRISC_LOCAL_DATA_SIZE = {
    0: LOCAL_DATA_SIZE["trisc0"],
    1: LOCAL_DATA_SIZE["trisc1"],
    2: LOCAL_DATA_SIZE["trisc2"],
  }

  FW_DEBUG = 0x19000


class Launch:
  BASE = 0x70
  MSG_SIZE = 96
  KERNEL_CONFIG_BASE = 0
  SEM_OFFSET = 12
  LOCAL_CB_OFFSET = 18
  REMOTE_CB_OFFSET = 20
  RTA_OFFSET = 22
  MODE = 42
  KERNEL_TEXT_OFFSET = 44
  LOCAL_CB_MASK = 64
  BRISC_NOC_ID = 68
  BRISC_NOC_MODE = 69
  NCRISC_MIN_REMOTE_CB_START_INDEX = 82
  TRISC_MIN_REMOTE_CB_START_INDEX = 70
  ENABLES = 76
  SUB_DEVICE_ORIGIN_X = 92
  SUB_DEVICE_ORIGIN_Y = 93
  PRELOAD = 95


class RunMsg:
  GO = 0x80
  RESET_READ_PTR = 0xC0
  RESET_READ_PTR_FROM_HOST = 0xE0
  REPLAY_TRACE = 0xF0
  DONE = 0x00


class RunSync:
  GO = 0x80
  LOAD = 0x01
  INIT = 0x40
  ALL_INIT = 0x40404040
  INIT_SYNC_REGISTERS = 0x03
  DONE = 0x00


class Mailbox:
  SUBORDINATE_SYNC = 0x68
  LAUNCH_MSG_RD_PTR = 0x6C
  CORE_INFO_ABSOLUTE_LOGICAL_X = 0x940
  CORE_INFO_ABSOLUTE_LOGICAL_Y = 0x941
  GO_SIGNAL = 0x373
  GO_MESSAGES = 0x370
  GO_MESSAGE_INDEX = 0x3A0


class Tensix:
  INSTRN_BUF_BASE = 0xFFE40000
  REGFILE_BASE = 0xFFE00000
  PC_BUF_SYNC = 0xFFE80004
  CFG_BASE = 0xFFEF0000
  RISCV_IC_INVALIDATE_INVALIDATE_ALL = CFG_BASE + 185 * 4
  RISCV_IC_ALL_MASK = 0x1F
  PRNG_SEED_SEED_VAL_ADDR32 = 186


class TensixInsn:
  NOP = 0x02000000
  ZEROACC = 0x10000000
  SFPLOADI = 0x71000000
  SFPENCC = 0x8A000000
  SFPCONFIG = 0x91000000
  SEMINIT = 0xA3000000


class TensixSem:
  MATH_PACK = 1
  UNPACK_TO_DEST = 2
  MATH_DONE = 7


class CircularBuffer:
  LOCAL_INTERFACE_SIZE = 32
  LOCAL_CONFIG_SIZE = 16
  SYNC_TILES_ACKED_BASE = 0xFFB48020
  SYNC_TILES_RECEIVED_BASE = 0xFFB48028
  SYNC_STRIDE = 0x1000
  NUM_CIRCULAR_BUFFERS = 32


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


class NocCfg:
  NIU_CFG_0 = 0x0
  ROUTER_CFG_0 = 0x1
  ID_LOGICAL = 0x12
  NODE_ID_MASK = 0x3F
  ADDR_NODE_ID_BITS = 6
  ADDR_COORD_SHIFT = 36
  COORDINATE_MASK = 0xFFFFFF
  PCIE_MASK = 0x1000000F
  INLINE_WRITE_POSTED_FIELD = (1 << 7) | (1 << 13) | (1 << 1) | (1 << 3)
  STREAM_REG_SPACE_SIZE = 0x1000
  MEM_NOC_ATOMIC_RET_VAL_ADDR = 0x04
  NCRISC_WR_CMD_BUF = 0
  NCRISC_RD_CMD_BUF = 1
  NCRISC_WR_REG_CMD_BUF = 2
  NCRISC_AT_CMD_BUF = 3
  RD_CMD_FIELD = (1 << 4) | (1 << 7) | (1 << 13)
  NIU_MST_ATOMIC_RESP_RECEIVED_WORD = 0x0
  NIU_MST_WR_ACK_RECEIVED_WORD = 0x1
  NIU_MST_RD_RESP_RECEIVED_WORD = 0x2
  NIU_MST_NONPOSTED_WR_REQ_SENT_WORD = 0xA
  NIU_MST_POSTED_WR_REQ_SENT_WORD = 0xB


class Dispatch:
  MODE_DEV = 0
  MESSAGE_ADDR = 0xFFB70438
  REMOTE_DEST_BUF_WORDS_FREE_INC = 6
  DONE_WORD = 1 << REMOTE_DEST_BUF_WORDS_FREE_INC


class BriscMailbox:
  MY_Y = 0xFFB00004
  MY_X = 0xFFB00008
  CRTA_L1_BASE_PTR = 0xFFB00014
  RTA_L1_BASE_PTR = 0xFFB00018
  SEM_L1_BASE = 0xFFB0086C
  CB_INTERFACE = 0xFFB00048
  NOC_INDEX = 0xFFB00046
  BRISC_NOC_MODE = 0xFFB00013
  MY_LOGICAL_Y = 0xFFB00044
  MY_LOGICAL_X = 0xFFB00045
  MY_RELATIVE_X = 0xFFB00012
  MY_RELATIVE_Y = 0xFFB00011
  DRAM_BANK_TO_NOC_XY = 0xFFB00448
  L1_BANK_TO_NOC_XY = 0xFFB00464
  BANK_TO_DRAM_OFFSET = 0xFFB00644
  BANK_TO_L1_OFFSET = 0xFFB00660
  NOC_POSTED_WRITES_NUM_ISSUED = 0xFFB0001C
  NOC_NONPOSTED_ATOMICS_ACKED = 0xFFB00024
  NOC_NONPOSTED_WRITES_ACKED = 0xFFB0002C
  NOC_NONPOSTED_WRITES_NUM_ISSUED = 0xFFB00034
  NOC_READS_NUM_ISSUED = 0xFFB0003C


class NcriscMailbox:
  MY_Y = 0xFFB0002C
  MY_X = 0xFFB00030
  MY_RELATIVE_Y = 0xFFB00032
  MY_RELATIVE_X = 0xFFB00033
  CRTA_L1_BASE_PTR = 0xFFB00034
  RTA_L1_BASE_PTR = 0xFFB00038
  MY_LOGICAL_Y = 0xFFB0003C
  MY_LOGICAL_X = 0xFFB0003D
  DRAM_BANK_TO_NOC_XY = 0xFFB00040
  L1_BANK_TO_NOC_XY = 0xFFB0005C
  BANK_TO_DRAM_OFFSET = 0xFFB0023C
  BANK_TO_L1_OFFSET = 0xFFB00258
  SEM_L1_BASE = 0xFFB00458
  CB_INTERFACE = 0xFFB00464


class TriscMailbox:
  DATA_COMMON = {
    "dest_offset_id": 0xFFB00000,
    "op_info_offset": 0xFFB00004,
    "my_relative_y": 0xFFB0000C,
    "my_relative_x": 0xFFB0000D,
    "crta_l1_base": 0xFFB00010,
    "rta_l1_base": 0xFFB00014,
    "my_logical_y": 0xFFB00018,
    "my_logical_x": 0xFFB00019,
    "cfg_state_id": 0xFFB0001C,
    "cb_interface": 0xFFB00020,
  }
  DATA1 = {
    "dest_offset_id": 0xFFB00000,
    "op_info_offset": 0xFFB00004,
    "my_relative_y": 0xFFB00008,
    "my_relative_x": 0xFFB00009,
    "crta_l1_base": 0xFFB0000C,
    "rta_l1_base": 0xFFB00010,
    "my_logical_y": 0xFFB00014,
    "my_logical_x": 0xFFB00015,
    "cfg_state_id": 0xFFB00018,
  }
  LOCAL_END = {
    0: 0xFFB00820,
    1: 0xFFB0001C,
    2: 0xFFB00820,
  }


class Sysmem:
  PCIE_NOC_XY = (24 << 6) | 19

  def __init__(self, dev, size: int = 1 << 30):
    from pcie import LibCAnonMap

    if size > 1 << 30:
      raise ValueError(f"Sysmem size {size} exceeds 1 GiB iATU aperture limit")
    self.dev = dev
    page_size = os.sysconf("SC_PAGE_SIZE")
    self.size = (size + page_size - 1) & ~(page_size - 1)
    self.buf = LibCAnonMap(self.size)
    self.noc_addr = dev.pin_pages(self.buf)

  def close(self):
    self.dev.unpin_pages(self.buf, self.noc_addr)
    self.buf.close()


def worker_cores(tensix_x: tuple[int, ...]) -> list[Core]:
  return [(x, y) for x in tensix_x for y in range(2, 12)]


def active_tensix_core_count(enabled_col_mask: int) -> int:
  return (enabled_col_mask & Arc.DEFAULT_TENSIX_ENABLED).bit_count() * 10


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
