from enum import IntEnum
from struct import Struct
from typing import Literal

Core = tuple[int, int]
Rect = tuple[Core, Core]
KernelRole = Literal["brisc", "ncrisc", "trisc0", "trisc1", "trisc2"]
KERNEL_ROLES: tuple[KernelRole, ...] = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")

class TensixL1:
  SIZE = 0x180000

  # Device-owned boot/control state and a 512-byte zero page precede firmware.
  BOOT = 0; BOOT_SIZE = 4; MEM_ZEROS_BASE = 0x32E0; MEM_ZEROS_SIZE = 0x200

  # FP8 projections need 24 argument slots; place them before the zero page.
  PARAM_BASE = 0x3280; PARAM_SIZE = 0x60; PARAM_SLOTS = PARAM_SIZE // 4

  # Launch-owned entry addresses and logical grid identity. These are data,
  # read by firmware and kernels respectively, never per-core instructions.
  WORKER_ENTRY_BASE = 0x380
  GRID_RANK_BASE = 0x3A0  # ri, ci (u32 each); 16-byte-aligned NoC destination

  # Direct launches overwrite one fixed, independently sized slot per RISC.
  WORKER_TEXT_BASE = {
    "brisc": 0x04000,
    "ncrisc": 0x0A000,
    "trisc0": 0x0C000,
    "trisc1": 0x0F000,
    "trisc2": 0x11000,
  }
  WORKER_TEXT_SIZE = {
    "brisc": 0x6000,
    "ncrisc": 0x2000,
    "trisc0": 0x3000,
    "trisc1": 0x2000,
    "trisc2": 0x1000,
  }

  # Resident kernels grow upward per core; deduplicated parameter templates
  # follow the fullest core. Both must fit in this persistent program arena.
  KERNEL_CACHE_BASE = 0x12000
  KERNEL_CACHE_END = 0x90000

  # Traced launches keep their immutable parameter tables resident in worker
  # L1 alongside the resident kernels. Dispatch puts the selected
  # template address in the low 24 bits of the GO word; BRISC resolves the few
  # dynamic slots from RUNTIME_PARAM_BASE before releasing the other RISCs.
  PARAM_TEMPLATE_ALIGNMENT = 32
  PARAM_TEMPLATE_STRIDE = 160
  PARAM_TEMPLATE_MAX_PARAMS = 24
  PARAM_TEMPLATE_VALUES = 4
  PARAM_TEMPLATE_IDS = 100
  PARAM_TEMPLATE_KERNELS = 124

  # CBs, L1 constants, and other program-owned storage share all remaining L1.
  # The final words stay fixed so traced launches can patch runtime values.
  DATA_BUFFER_SPACE_BASE = KERNEL_CACHE_END
  RUNTIME_PARAM_BASE = 0x17FFE0
  RUNTIME_PARAM_SLOTS = 8
  DATA_BUFFER_SPACE_END = RUNTIME_PARAM_BASE

class Firmware:
  BRISC_STACK_TOP = NCRISC_STACK_TOP = 0xFFB01FF0
  TRISC_STACK_TOP = 0xFFB00FF0; TRISC_GLOBAL_POINTER = 0xFFB007F0

  # Firmware stores NoC 0/1 coordinates as bytes at each X/Y base plus the NoC index.
  NOC_COORDINATE_BASE = {
    "brisc": (0xFFB00008, 0xFFB00004),
    "ncrisc": (0xFFB00030, 0xFFB0002C),
  }

  LOCAL_MEMORY = {
    "brisc": (0xFFB00878, 0xFFB01F00),
    "ncrisc": (0xFFB00864, 0xFFB01F00),
    "trisc0": (0xFFB00820, 0xFFB00F40),
    "trisc1": (0xFFB00140, 0xFFB00F40),
    "trisc2": (0xFFB008C0, 0xFFB00F00),
  }

  # Packed back-to-back in worker L1; the final image ends at 0x3FD0.
  TEXT = {
    "brisc": (0x34E0, 0x07C0),
    "ncrisc": (0x3CA0, 0x00D8),
    "trisc0": (0x3D78, 0x00C8),
    "trisc1": (0x3E40, 0x00C8),
    "trisc2": (0x3F08, 0x00C8),
  }

class RunState(IntEnum):
  DONE = 0x00; BOOT_READY = 0x02; GO = 0x80; ALL_INIT = 0x40404040

class FirmwareControl:
  SUBORDINATE_SYNC = 0x0068
  GO_SIGNAL = 0x0373

class CQConfig:
  PCIE_MID = 0x10000000; PCIE_COORD = (1 << 24) | (24 << 6) | 19
  PREFETCH_CORE = (14, 2); DISPATCH_CORE = (14, 3); DRAM_CORE = (14, 4)
  PREFETCH_COORD = (2 << 6) | 14; DISPATCH_COORD = (3 << 6) | 14
  DRAM_COORD = (4 << 6) | 14

class TensixMMIO:
  LOCAL_RAM_START = 0xFFB00000; LOCAL_RAM_END = 0xFFB01FFF
  REGFILE_BASE = 0xFFE00000; INSTRN_BUF_BASE = 0xFFE40000
  PC_BUF_SYNC = 0xFFE80004; PC_BUF_MOP_SYNC = 0xFFE80008
  CFG_BASE = 0xFFEF0000
  ECC_SCRUBBER = CFG_BASE + 0xC
  PRNG_SEED_SEED_VAL = CFG_BASE + 186 * 4
  RISCV_IC_INVALIDATE = CFG_BASE + 185 * 4; RISCV_IC_ALL_MASK = 0x1F
  NCRISC_HALT_RESUME_ADDR = 0x60; RISCV_DEBUG_REG_SOFT_RESET_0 = 0xFFB121B0
  RISCV_DEBUG_REG_WALL_CLOCK_L = 0xFFB121F0; RISCV_DEBUG_REG_WALL_CLOCK_H = 0xFFB121F8
  RISCV_TDMA_REG_CLK_GATE_EN = 0xFFB11024; RISCV_DEBUG_REG_TRISC0_RESET_PC = 0xFFB12228
  RISCV_DEBUG_REG_TRISC1_RESET_PC = 0xFFB1222C; RISCV_DEBUG_REG_TRISC2_RESET_PC = 0xFFB12230
  RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE = 0xFFB12234; RISCV_DEBUG_REG_NCRISC_RESET_PC = 0xFFB12238
  RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE = 0xFFB1223C; RISCV_DEBUG_REG_DEST_CG_CTRL = 0xFFB12240
  SOFT_RESET_ALL = 0x47800; SOFT_RESET_BRISC_ONLY_RUN = 0x47000


# Command-queue packets and firmware service memory layout.
ALIGN = 64; MAX_WRITE_SIZE = 16 * 1024; MAX_RECORD_SIZE = 64 * 1024; PAGE_SIZE = 4096

CQ_STATE = 0x1000
PREFETCH_DOORBELL = CQ_STATE
PREFETCH_PCIE_BASE = CQ_STATE + 0x08
PREFETCH_READ_PTR = CQ_STATE + 0x0C
PREFETCH_DISPATCH_READ = CQ_STATE + 0x10
PREFETCH_TRACE_ACTIVE = CQ_STATE + 0x14
PREFETCH_TRACE_CURSOR = CQ_STATE + 0x18
PREFETCH_TRACE_END = CQ_STATE + 0x1C
PREFETCH_RECORD_SIZE = CQ_STATE + 0x20
PREFETCH_READ_PUBLISH = CQ_STATE + 0x30  # Scalar NoC sources are 16-byte aligned.
# The largest CQ record is 64 KiB. Keep staging clear of the BRISC firmware
# image and the small CQ state area below 0x2000.
PREFETCH_STAGING = 0x20000
DISPATCH_PUBLISHED = CQ_STATE
DISPATCH_RING_BASE = 0x20000; DISPATCH_RING_PAGES = 320
DISPATCH_RING_END = DISPATCH_RING_BASE + DISPATCH_RING_PAGES * PAGE_SIZE
DISPATCH_SCRATCH = DISPATCH_RING_END
DISPATCH_GO = DISPATCH_SCRATCH + 0x40
DISPATCH_DONE_COUNT = DISPATCH_SCRATCH + 0x50
DISPATCH_READ_PUBLISH = DISPATCH_SCRATCH + 0x60
DISPATCH_SIGNAL = DISPATCH_SCRATCH + 0x70
DISPATCH_DRAM_PUT = DISPATCH_SCRATCH + 0x80
DISPATCH_DRAM_READ = DISPATCH_SCRATCH + 0x90  # NoC read destination must be 16-byte aligned.
DRAM_PUBLISHED = CQ_STATE
DRAM_NCRISC_READ = CQ_STATE + 4
DRAM_BRISC_READY = CQ_STATE + 8
DRAM_NCRISC_READY = CQ_STATE + 0xC
DRAM_READ_PUBLISH = CQ_STATE + 0x60
DRAM_QUEUE_BASE = 0x2000
DRAM_QUEUE_ENTRIES = 32
DRAM_BRISC_STAGING = 0x20000
DRAM_NCRISC_STAGING = 0x30000
HOST_ISSUE_SIZE = 4 << 20
HOST_COMPLETION_SIZE = PAGE_SIZE
HOST_TRACE_SIZE = 256 << 20
HOST_LIVE_SIZE = 128 << 10

class Op(IntEnum):
  PAD = 0
  UNICAST_WRITE = 1
  MCAST_WRITE = 2
  RUN = 3
  DRAM_RECORD = 4
  SIGNAL = 5
  TRACE = 6
  DRAM_COPY = 7
  WAIT = 8
  TIMESTAMP = 9
  DMA = 10

class PacketLayout:
  HEADER = Struct("<BxHIII")
  UNICAST_TARGET = Struct("<I")
  MCAST_TARGET = Struct("<II")

  OP = 0
  TARGET_COUNT = 2
  TOTAL_SIZE = 4
  ADDRESS = 8
  DATA_SIZE = 12
  DRAM_COORD = HEADER.size
  SIGNAL_TARGET_LO = ADDRESS
  SIGNAL_TARGET_MID = DATA_SIZE
  SIGNAL_VALUE = HEADER.size
  TRACE_SOURCE_LO = ADDRESS
  TRACE_SOURCE_MID = DATA_SIZE
  TRACE_SIZE = HEADER.size
  COPY_SOURCE_LO = HEADER.size
  COPY_SOURCE_MID = COPY_SOURCE_LO + 4
  COPY_TILE_COUNT = COPY_SOURCE_MID + 4
  COPY_BANKS = COPY_TILE_COUNT + 4
  COPY_DIRECTION = COPY_BANKS + 4
  WRITE_TARGETS = HEADER.size
  RUN_TEMPLATE = HEADER.size
  RUN_TARGETS = HEADER.size + 8


BOOT_PCIE_MID = CQ_STATE + 0x80
BOOT_BANKS = CQ_STATE + 0x84
BOOT_COORDS = CQ_STATE + 0xA0
DMA_PAGE_SIZE = 2048
