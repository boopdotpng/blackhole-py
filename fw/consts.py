from enum import IntEnum
from typing import Literal

Core = tuple[int, int]
KernelRole = Literal["brisc", "ncrisc", "trisc0", "trisc1", "trisc2"]
KERNEL_ROLES: tuple[KernelRole, ...] = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")

class TensixL1:
  SIZE = 0x180000

  # Device-owned boot/control state and a 512-byte zero page precede firmware.
  BOOT = 0

  # Firmware.TEXT is packed immediately below this direct-launch argument table.
  PARAM_BASE = 0x3FD0; PARAM_SIZE = 0x30; PARAM_SLOTS = PARAM_SIZE // 4

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

  # Preserve the C firmware's reserved regions; raw kernels use the space between.
  DATA_BUFFER_SPACE_BASE = 0x42000
  DATA_BUFFER_SPACE_END = 0x17FFE0

class Firmware:
  BRISC_STACK_TOP = NCRISC_STACK_TOP = 0xFFB01FF0
  TRISC_STACK_TOP = 0xFFB00FF0; TRISC_GLOBAL_POINTER = 0xFFB007F0

  LOCAL_MEMORY = {
    "brisc": (0xFFB00878, 0xFFB01F00),
    "ncrisc": (0xFFB00864, 0xFFB01F00),
    "trisc0": (0xFFB00820, 0xFFB00F40),
    "trisc1": (0xFFB00140, 0xFFB00F40),
    "trisc2": (0xFFB008C0, 0xFFB00F00),
  }

  # Non-code C ELF sections get 0x100 bytes per RISC in addition to the
  # original code budget. Images stay packed back-to-back below PARAM_BASE.
  ELF_DATA_SIZE = 0x100
  TEXT_CODE_SIZE = {
    "brisc": 0x07C0,
    "ncrisc": 0x00D8,
    "trisc0": 0x0180,
    "trisc1": 0x0180,
    "trisc2": 0x0180,
  }
  TEXT = {
    "brisc": (0x2DB8, TEXT_CODE_SIZE["brisc"] + ELF_DATA_SIZE),
    "ncrisc": (0x3678, TEXT_CODE_SIZE["ncrisc"] + ELF_DATA_SIZE),
    "trisc0": (0x3850, TEXT_CODE_SIZE["trisc0"] + ELF_DATA_SIZE),
    "trisc1": (0x3AD0, TEXT_CODE_SIZE["trisc1"] + ELF_DATA_SIZE),
    "trisc2": (0x3D50, TEXT_CODE_SIZE["trisc2"] + ELF_DATA_SIZE),
  }

class RunState(IntEnum):
  DONE = 0x00; BOOT_READY = 0x02; GO = 0x80; ALL_INIT = 0x40404040

class FirmwareControl:
  GO_SIGNAL = 0x0373

class TensixMMIO:
  REGFILE_BASE = 0xFFE00000; INSTRN_BUF_BASE = 0xFFE40000
  PC_BUF_SYNC = 0xFFE80004; PC_BUF_MOP_SYNC = 0xFFE80008
  CFG_BASE = 0xFFEF0000
  PRNG_SEED_SEED_VAL = CFG_BASE + 186 * 4
  RISCV_DEBUG_REG_SOFT_RESET_0 = 0xFFB121B0
  RISCV_DEBUG_REG_WALL_CLOCK_L = 0xFFB121F0; RISCV_DEBUG_REG_WALL_CLOCK_H = 0xFFB121F8
  SOFT_RESET_ALL = 0x47800; SOFT_RESET_BRISC_ONLY_RUN = 0x47000
