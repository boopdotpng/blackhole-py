from enum import IntEnum

class TensixL1:
  SIZE = 0x180000

  BOOT = 0; BOOT_SIZE = 4; MEM_ZEROS_BASE = 0x32E0; MEM_ZEROS_SIZE = 0x200
  PARAM_BASE = 0x4200; PARAM_SIZE = 0xF00; PARAM_SLOTS = PARAM_SIZE // 4

  WORKER_TEXT_BASE = {
    "brisc": 0x05100,
    "ncrisc": 0x0F000,
    "trisc0": 0x18F00,
    "trisc1": 0x22E00,
    "trisc2": 0x2CD00,
  }
  WORKER_TEXT_SIZE = 0x9F00; WORKER_TEXT_END = 0x36C00; DATA_BUFFER_SPACE_BASE = 0x37000

class Firmware:
  BRISC_STACK_TOP = NCRISC_STACK_TOP = 0xFFB01FF0
  TRISC_STACK_TOP = 0xFFB00FF0; TRISC_GLOBAL_POINTER = 0xFFB007F0

  TEXT_BASE = {
    "brisc": 0x3840,
    "ncrisc": 0x3EB0,
    "trisc0": 0x3F88,
    "trisc1": 0x4050,
    "trisc2": 0x4118,
  }

  TEXT_SIZE = {
    "brisc": 0x0670,
    "ncrisc": 0x00D8,
    "trisc0": 0x00C8,
    "trisc1": 0x00C8,
    "trisc2": 0x00C8,
  }
  TEXT_END = 0x41E0

class BriscLocalState:
  MY_Y = 0xFFB00004; MY_X = 0xFFB00008

class NcriscLocalState:
  MY_Y = 0xFFB0002C; MY_X = 0xFFB00030

class RunMsg(IntEnum):
  DONE = 0x00; GO = 0x80

class RunSync(IntEnum):
  DONE = 0x00; BOOT_READY = 0x02; LOAD = 0x01; INIT_SYNC_REGISTERS = 0x03
  INIT = 0x40; GO = 0x80; ALL_INIT = 0x40404040

class FirmwareControl:
  SUBORDINATE_SYNC = 0x0068
  GO_SIGNAL = 0x0373

class CQ:
  PCIE_MID = 0x10000000; PCIE_COORD = (1 << 24) | (24 << 6) | 19
  PREFETCH_CORE = (14, 2); DISPATCH_CORE = (14, 3)
  PREFETCH_COORD = (2 << 6) | 14; DISPATCH_COORD = (3 << 6) | 14

class TensixMMIO:
  LOCAL_RAM_START = 0xFFB00000; LOCAL_RAM_END = 0xFFB01FFF
  NCRISC_HALT_RESUME_ADDR = 0x60; RISCV_DEBUG_REG_SOFT_RESET_0 = 0xFFB121B0
  RISCV_DEBUG_REG_WALL_CLOCK_L = 0xFFB121F0; RISCV_DEBUG_REG_WALL_CLOCK_H = 0xFFB121F8
  RISCV_TDMA_REG_CLK_GATE_EN = 0xFFB11024; RISCV_DEBUG_REG_TRISC0_RESET_PC = 0xFFB12228
  RISCV_DEBUG_REG_TRISC1_RESET_PC = 0xFFB1222C; RISCV_DEBUG_REG_TRISC2_RESET_PC = 0xFFB12230
  RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE = 0xFFB12234; RISCV_DEBUG_REG_NCRISC_RESET_PC = 0xFFB12238
  RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE = 0xFFB1223C; RISCV_DEBUG_REG_DEST_CG_CTRL = 0xFFB12240
  SOFT_RESET_ALL = 0x47800; SOFT_RESET_BRISC_ONLY_RUN = 0x47000

def _validate_l1_layout():
  roles = tuple(Firmware.TEXT_BASE)
  assert roles == tuple(Firmware.TEXT_SIZE) == tuple(TensixL1.WORKER_TEXT_BASE)
  for role, next_role in zip(roles, roles[1:]):
    assert Firmware.TEXT_BASE[role] + Firmware.TEXT_SIZE[role] <= Firmware.TEXT_BASE[next_role]
    assert TensixL1.WORKER_TEXT_BASE[role] + TensixL1.WORKER_TEXT_SIZE <= TensixL1.WORKER_TEXT_BASE[next_role]
  assert Firmware.TEXT_BASE[roles[-1]] + Firmware.TEXT_SIZE[roles[-1]] == Firmware.TEXT_END
  assert Firmware.TEXT_END <= TensixL1.PARAM_BASE
  assert TensixL1.PARAM_BASE + TensixL1.PARAM_SIZE <= TensixL1.WORKER_TEXT_BASE[roles[0]]
  assert TensixL1.WORKER_TEXT_BASE[roles[-1]] + TensixL1.WORKER_TEXT_SIZE == TensixL1.WORKER_TEXT_END
  assert TensixL1.WORKER_TEXT_END <= TensixL1.DATA_BUFFER_SPACE_BASE < TensixL1.SIZE

_validate_l1_layout()

__all__ = [name for name in globals() if not name.startswith("_")]
