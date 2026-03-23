"""Blackhole worker-tile debug register definitions."""

from __future__ import annotations

TLB_2M = 1 << 21


def tlb_align(addr: int) -> tuple[int, int]:
  base = addr & ~(TLB_2M - 1)
  return base, addr - base


DEBUG_REGS_BASE = 0xFFB12000
DEBUG_TLB_BASE, DEBUG_TLB_OFFSET = tlb_align(DEBUG_REGS_BASE)

RISC_DBG_CNTL_0 = DEBUG_REGS_BASE | 0x80
RISC_DBG_CNTL_1 = DEBUG_REGS_BASE | 0x84
RISC_DBG_STATUS_0 = DEBUG_REGS_BASE | 0x88
RISC_DBG_STATUS_1 = DEBUG_REGS_BASE | 0x8C

CNTL0_TRIGGER = 1 << 31
STATUS0_READ_VALID = 1 << 30

RISC_SEL = {
  "brisc": 0,
  "trisc0": 1,
  "trisc1": 2,
  "trisc2": 3,
}


def cntl0_value(risc: str, dr_addr: int, is_write: bool, trigger: bool) -> int:
  return ((1 if trigger else 0) << 31) | ((1 if is_write else 0) << 16) | (RISC_SEL[risc] << 17) | (dr_addr & 0x7FF)


DR_STATUS = 0
DR_COMMAND = 1
DR_COMMAND_ARG_0 = 2
DR_COMMAND_ARG_1 = 3
DR_COMMAND_RETURN_VALUE = 4
DR_WATCHPOINT_SETTINGS = 5
DR_WATCHPOINT_BASE = 10

STATUS_HALTED = 0x1
STATUS_PC_WATCHPOINT_HIT = 0x2
STATUS_MEM_WATCHPOINT_HIT = 0x4
STATUS_EBREAK_HIT = 0x8

CMD_HALT = 0x00000001
CMD_STEP = 0x00000002
CMD_CONTINUE = 0x00000004
CMD_READ_REGISTER = 0x00000008
CMD_WRITE_REGISTER = 0x00000010
CMD_READ_MEMORY = 0x00000020
CMD_WRITE_MEMORY = 0x00000040
CMD_DEBUG_MODE = 0x80000000

WP_DISABLED = 0
WP_PC_BREAK = 8
WP_MEM_READ = 9
WP_MEM_WRITE = 10
WP_MEM_READ_WRITE = 11
WP_MASK = 0xF

GPR_PC = 32
GPR_COUNT = 32

DEST_BASE = 0xFFBD8000
DEST_SIZE = 32768
DEST_TILE_BYTES_BF16 = 32 * 32 * 2

DBG_BUS_CTRL = DEBUG_REGS_BASE | 0x54
DBG_BUS_RD_DATA = DEBUG_REGS_BASE | 0x5C


def dbg_bus_cntl(sig_sel: int, daisy_sel: int, rd_sel: int) -> int:
  return (1 << 29) | (rd_sel << 25) | (daisy_sel << 16) | sig_sel


DBG_ARRAY_RD_EN = DEBUG_REGS_BASE | 0x60
DBG_ARRAY_RD_CMD = DEBUG_REGS_BASE | 0x64
DBG_ARRAY_RD_DATA = DEBUG_REGS_BASE | 0x6C

ARRAY_ID_SRCA = 0
ARRAY_ID_SRCB = 1
ARRAY_ID_DEST = 2

DEST_ROWS_PER_TILE = 64        # 4 faces x 16 rows
DEST_CHUNKS_PER_ROW = 8        # 8 x 32-bit chunks = 256 bits = 32 bytes per row
DEST_TOTAL_ROWS = 1024
DEST_HALF_ROWS = 512
DEST_ROW_BYTES = 32            # 16 elements x 2 bytes (BF16) = 32 bytes
DEST_FP32_ELEMS_PER_ROW = 8   # 32 bytes / 4 bytes

PC_SIGNALS = {
  "brisc": {"sig_sel": 11, "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
  "trisc0": {"sig_sel": 13, "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
  "trisc1": {"sig_sel": 15, "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
  "trisc2": {"sig_sel": 17, "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
  "ncrisc": {"sig_sel": 25, "daisy_sel": 7, "rd_sel": 1, "mask": 0x3FFFFFFF},
}
