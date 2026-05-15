from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import FIRMWARE_TEXT_BASE, Kernel
from dsl import Reg, ra, sp, t0, t1, t2, t3, t4, t5, t6, zero

BRISC_STACK_TOP = 0xFFB01FF0
NCRISC_RESET_PC = 0xFFB12238
TRISC0_RESET_PC = 0xFFB12228
TRISC1_RESET_PC = 0xFFB1222C
TRISC2_RESET_PC = 0xFFB12230
TRISC_RESET_PC_OVERRIDE = 0xFFB12234
NCRISC_RESET_PC_OVERRIDE = 0xFFB1223C
SOFT_RESET_0 = 0xFFB121B0
RISCV_TDMA_REG_CLK_GATE_EN = 0xFFB11024
RISCV_DEBUG_REG_DEST_CG_CTRL = 0xFFB12240
INSTRN_BUF_BASE = 0xFFE40000
TENSIX_CFG_BASE = 0xFFEF0000
RISCV_IC_INVALIDATE_INVALIDATE_ALL = TENSIX_CFG_BASE + 185 * 4
RISCV_IC_ALL_MASK = 0x1F
INSTRN_NOP = 0x02000000
INSTRN_ZEROACC = 0x10000000
INSTRN_SFPLOADI = 0x71000000
INSTRN_SFPENCC = 0x8A000000
INSTRN_SFPCONFIG = 0x91000000
INSTRN_SEMINIT = 0xA3000000
SEM_MATH_PACK = 1
SEM_UNPACK_TO_DEST = 2
SEM_MATH_DONE = 7

# These addresses must match the old BRISC ELF that blackhole-py-old uses to
# link BRISC kernels. They are not the newer firmware/disasm symbol layout.
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
NOC_STATUS_BASE = 0xFFB20200
NOC_REGS_START_ADDR = 0xFFB20000
NOC_CMD_BUF_OFFSET_BIT = 11
NOC_INSTANCE_OFFSET_BIT = 16
NOC_TARG_ADDR_LO = NOC_REGS_START_ADDR + 0x00
NOC_TARG_ADDR_MID = NOC_REGS_START_ADDR + 0x04
NOC_TARG_ADDR_COORDINATE = NOC_REGS_START_ADDR + 0x08
NOC_RET_ADDR_LO = NOC_REGS_START_ADDR + 0x0C
NOC_RET_ADDR_MID = NOC_REGS_START_ADDR + 0x10
NOC_RET_ADDR_COORDINATE = NOC_REGS_START_ADDR + 0x14
NOC_CTRL = NOC_REGS_START_ADDR + 0x1C
NOC_AT_LEN_BE = NOC_REGS_START_ADDR + 0x20
NOC_AT_DATA = NOC_REGS_START_ADDR + 0x28
NOC_CMD_CTRL = NOC_REGS_START_ADDR + 0x40
NOC_CFG_BASE = NOC_REGS_START_ADDR + 0x100
NIU_CFG_0 = 0x0
ROUTER_CFG_0 = 0x1
NOC_ID_LOGICAL = 0x12
NOC_NODE_ID_MASK = 0x3F
NOC_ADDR_NODE_ID_BITS = 6
NOC_ADDR_COORD_SHIFT = 36
NOC_COORDINATE_MASK = 0xFFFFFF
NOC_PCIE_MASK = 0x1000000F
NOC_CMD_WR = 1 << 1
NOC_CMD_WR_INLINE = 1 << 3
NOC_CMD_VC_STATIC = 1 << 7
NOC_CMD_STATIC_VC_1 = 1 << 13
NOC_CTRL_SEND_REQ = 1
NOC_INLINE_WRITE_POSTED_FIELD = NOC_CMD_VC_STATIC | NOC_CMD_STATIC_VC_1 | NOC_CMD_WR | NOC_CMD_WR_INLINE
NOC_STREAM_REG_SPACE_SIZE = 0x1000
DISPATCH_MESSAGE_ADDR = 0xFFB70438
REMOTE_DEST_BUF_WORDS_FREE_INC = 6
DISPATCH_DONE_WORD = 1 << REMOTE_DEST_BUF_WORDS_FREE_INC
MEM_NOC_ATOMIC_RET_VAL_ADDR = 0x04
MEM_BANK_TO_NOC_SCRATCH = 0x112B0
P100_NUM_DRAM_BANKS = 7
P100_NUM_L1_BANKS = 120
P100_DRAM_BANK_TO_NOC_SIZE = 2 * P100_NUM_DRAM_BANKS * 2
P100_L1_BANK_TO_NOC_SIZE = 2 * P100_NUM_L1_BANKS * 2
P100_BANK_TO_DRAM_OFFSET_SIZE = P100_NUM_DRAM_BANKS * 4
P100_BANK_TO_L1_OFFSET_SIZE = P100_NUM_L1_BANKS * 4
NCRISC_WR_CMD_BUF = 0
NCRISC_RD_CMD_BUF = 1
NCRISC_WR_REG_CMD_BUF = 2
NCRISC_AT_CMD_BUF = 3
NOC_RD_CMD_FIELD = (1 << 4) | (1 << 7) | (1 << 13)
NIU_MST_ATOMIC_RESP_RECEIVED = 0x0
NIU_MST_WR_ACK_RECEIVED = 0x1
NIU_MST_RD_RESP_RECEIVED = 0x2
NIU_MST_NONPOSTED_WR_REQ_SENT = 0xA
NIU_MST_POSTED_WR_REQ_SENT = 0xB

GO_SIGNAL = 0x373
GO_MESSAGES = 0x370
GO_MESSAGE_INDEX = 0x3A0
NCRISC_HALT_RESUME_ADDR = 0x60
LAUNCH_MSG_RD_PTR = 0x6C
SUBORDINATE_SYNC = 0x68
CORE_INFO_ABSOLUTE_LOGICAL_X = 0x940
CORE_INFO_ABSOLUTE_LOGICAL_Y = 0x941
RUN_MSG_GO = 0x80
RUN_MSG_RESET_READ_PTR = 0xC0
RUN_MSG_RESET_READ_PTR_FROM_HOST = 0xE0
RUN_MSG_REPLAY_TRACE = 0xF0
RUN_MSG_DONE = 0x00
RUN_SYNC_MSG_GO = 0x80
RUN_SYNC_MSG_LOAD = 0x01
RUN_SYNC_MSG_INIT_SYNC_REGISTERS = 0x03
RUN_SYNC_MSG_DONE = 0x00

LAUNCH = 0x70
LAUNCH_KERNEL_CONFIG_BASE = 0
LAUNCH_SEM_OFFSET = 12
LAUNCH_LOCAL_CB_OFFSET = 18
LAUNCH_RTA_OFFSET = 22
LAUNCH_MODE = 42
LAUNCH_KERNEL_TEXT_OFFSET = 44
LAUNCH_LOCAL_CB_MASK = 64
LAUNCH_BRISC_NOC_ID = 68
LAUNCH_BRISC_NOC_MODE = 69
LAUNCH_SUB_DEVICE_ORIGIN_X = 92
LAUNCH_SUB_DEVICE_ORIGIN_Y = 93
LAUNCH_PRELOAD = 95
LAUNCH_ENABLES = 76
DISPATCH_MODE_DEV = 0
LOCAL_CB_INTERFACE_SIZE = 32
LOCAL_CB_CONFIG_SIZE = 16


def write32(fw: Kernel, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sw(value, addr, 0)


def read32(fw: Kernel, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  return fw.lw(rd, addr, 0)


def read16(fw: Kernel, rd: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  return fw.lhu(rd, addr, 0)


def write8(fw: Kernel, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
  if isinstance(addr, int):
    fw.li(tmp_addr, addr)
    addr = tmp_addr
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sb(value, addr, 0)


def wait8(fw: Kernel, addr: int, value: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  fw.li(ptr, addr)
  fw.li(expected, value)
  start = fw._new_label("wait8")
  fw.label(start)
  fw.lbu(actual, ptr, 0)
  fw.bne(actual, expected, start)
  return fw


def setup_stack(fw: Kernel):
  return fw.li(sp, BRISC_STACK_TOP)


def set_subordinate_reset_pcs(fw: Kernel, text_base: dict[str, int] = FIRMWARE_TEXT_BASE):
  write32(fw, NCRISC_RESET_PC, text_base["ncrisc"])
  write32(fw, TRISC0_RESET_PC, text_base["trisc0"])
  write32(fw, TRISC1_RESET_PC, text_base["trisc1"])
  write32(fw, TRISC2_RESET_PC, text_base["trisc2"])
  write32(fw, TRISC_RESET_PC_OVERRIDE, 0b111)
  write32(fw, NCRISC_RESET_PC_OVERRIDE, 1)
  return fw


def deassert_all_riscs(fw: Kernel):
  return write32(fw, SOFT_RESET_0, 0)


def invalidate_all_risc_icaches(fw: Kernel):
  return write32(fw, RISCV_IC_INVALIDATE_INVALIDATE_ALL, RISCV_IC_ALL_MASK)


def push_tensix_word(fw: Kernel, word: int, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
  return write32(fw, INSTRN_BUF_BASE, word, tmp_addr=tmp_addr, tmp_val=tmp_val)


def tensix_sem_init(fw: Kernel, sem: int, max_value: int, init_value: int):
  instrn = INSTRN_SEMINIT | (1 << (sem + 2)) | (init_value << 16) | (max_value << 20)
  return push_tensix_word(fw, instrn)


def enable_noc_clock_gating(fw: Kernel, *, addr: Reg = t0, value: Reg = t1):
  for noc in range(2):
    for reg in (NIU_CFG_0, ROUTER_CFG_0):
      cfg = NOC_CFG_BASE + reg * 4 + (noc << NOC_INSTANCE_OFFSET_BIT)
      fw.li(addr, cfg)
      fw.lw(value, addr, 0)
      fw.ori(value, value, 1)
      fw.sw(value, addr, 0)
  return fw


def device_setup(fw: Kernel):
  write32(fw, RISCV_DEBUG_REG_DEST_CG_CTRL, 0)
  write32(fw, RISCV_TDMA_REG_CLK_GATE_EN, 0x3F)
  enable_noc_clock_gating(fw)
  push_tensix_word(fw, INSTRN_ZEROACC | (3 << 19))
  push_tensix_word(fw, INSTRN_SFPENCC | (3 << 12) | 10)
  push_tensix_word(fw, INSTRN_NOP)
  push_tensix_word(fw, INSTRN_SFPLOADI | 0xBF80)
  push_tensix_word(fw, INSTRN_SFPCONFIG | (11 << 4))
  tensix_sem_init(fw, SEM_MATH_PACK, 1, 0)
  tensix_sem_init(fw, SEM_UNPACK_TO_DEST, 1, 0)
  tensix_sem_init(fw, SEM_MATH_DONE, 1, 0)
  return fw


def signal8(fw: Kernel, addr: int, value: int):
  return write8(fw, addr, value)


def wait_go(fw: Kernel, *, ptr: Reg = t0, signal: Reg = t1, expected: Reg = t2):
  loop = fw._new_label("wait_go")
  check_reset_host = fw._new_label("check_reset_host")
  check_replay = fw._new_label("check_replay")
  reset_ptr = fw._new_label("reset_launch_ptr")
  done = fw._new_label("go_seen")
  fw.li(ptr, GO_SIGNAL)
  fw.label(loop)
  fw.lbu(signal, ptr, 0)
  fw.li(expected, RUN_MSG_GO)
  fw.beq(signal, expected, done)
  fw.li(expected, RUN_MSG_RESET_READ_PTR)
  fw.beq(signal, expected, reset_ptr)
  fw.label(check_reset_host)
  fw.li(expected, RUN_MSG_RESET_READ_PTR_FROM_HOST)
  fw.beq(signal, expected, reset_ptr)
  fw.label(check_replay)
  fw.li(expected, RUN_MSG_REPLAY_TRACE)
  fw.beq(signal, expected, reset_ptr)
  fw.j(loop)
  fw.label(reset_ptr)
  write32(fw, LAUNCH_MSG_RD_PTR, 0, tmp_addr=ptr, tmp_val=expected)
  fw.li(ptr, GO_SIGNAL)
  fw.j(loop)
  fw.label(done)
  return fw


def signal_done(fw: Kernel):
  return signal8(fw, GO_SIGNAL, RUN_MSG_DONE)


def signal_subordinate_go(fw: Kernel, role: int):
  return signal8(fw, SUBORDINATE_SYNC + role - 1, RUN_SYNC_MSG_GO)


def signal_subordinate_load(fw: Kernel, role: int):
  return signal8(fw, SUBORDINATE_SYNC + role - 1, RUN_SYNC_MSG_LOAD)


def signal_subordinate_if_enabled(fw: Kernel, role: int, value: int, *,
                                  enabled: Reg = t0, mask: Reg = t1):
  skip = fw._new_label("skip_subordinate_signal")
  launch_kernel_enabled(fw, role, enabled=enabled, mask=mask)
  fw.beq(enabled, zero, skip)
  signal8(fw, SUBORDINATE_SYNC + role - 1, value)
  fw.label(skip)
  return fw


def signal_trisc0_init_sync_registers(fw: Kernel):
  return signal8(fw, SUBORDINATE_SYNC + 1, RUN_SYNC_MSG_INIT_SYNC_REGISTERS)


def wait_subordinate_done(fw: Kernel, role: int):
  return wait8(fw, SUBORDINATE_SYNC + role - 1, RUN_SYNC_MSG_DONE)


def launch_kernel_enabled(fw: Kernel, role: int, *, enabled: Reg = t0, mask: Reg = t1):
  read32(fw, enabled, LAUNCH + LAUNCH_ENABLES)
  fw.li(mask, 1 << role)
  return fw.and_(enabled, enabled, mask)


def init_risc_noc_coords(fw: Kernel, *, noc_id: Reg = t0, coord: Reg = t1, tmp: Reg = t2):
  for noc in range(2):
    read32(fw, noc_id, noc_cmd_buf_addr(noc, 0, NOC_CFG_BASE + NOC_ID_LOGICAL * 4), tmp_addr=tmp)
    fw.andi(coord, noc_id, NOC_NODE_ID_MASK)
    write8(fw, MY_X + noc, coord, tmp_addr=tmp)
    fw.srli(coord, noc_id, NOC_ADDR_NODE_ID_BITS)
    fw.andi(coord, coord, NOC_NODE_ID_MASK)
    write8(fw, MY_Y + noc, coord, tmp_addr=tmp)
  return fw


def init_brisc_mailbox_globals(fw: Kernel, *, value: Reg = t0, tmp: Reg = t1):
  write32(fw, LAUNCH_MSG_RD_PTR, 0, tmp_addr=tmp, tmp_val=value)
  write8(fw, NOC_INDEX, 0, tmp_addr=tmp, tmp_val=value)
  write8(fw, BRISC_NOC_MODE, 0, tmp_addr=tmp, tmp_val=value)
  fw.li(tmp, CORE_INFO_ABSOLUTE_LOGICAL_X)
  fw.lbu(value, tmp, 0)
  write8(fw, MY_LOGICAL_X, value, tmp_addr=tmp)
  fw.li(tmp, CORE_INFO_ABSOLUTE_LOGICAL_Y)
  fw.lbu(value, tmp, 0)
  write8(fw, MY_LOGICAL_Y, value, tmp_addr=tmp)
  write32(fw, NCRISC_HALT_RESUME_ADDR, 0, tmp_addr=tmp, tmp_val=value)
  return fw


def init_brisc_kernel_config(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                             off: Reg = t2, addr: Reg = t3, tmp: Reg = t4):
  fw.li(launch, LAUNCH)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)

  for i in range(3):
    fw.lhu(off, launch, LAUNCH_SEM_OFFSET + 2 * i)
    fw.add(addr, config_base, off)
    write32(fw, SEM_L1_BASE + 4 * i, addr, tmp_addr=tmp)

  fw.lhu(off, launch, LAUNCH_RTA_OFFSET)
  fw.add(addr, config_base, off)
  write32(fw, RTA_L1_BASE_PTR, addr, tmp_addr=tmp)

  fw.lhu(off, launch, LAUNCH_RTA_OFFSET + 2)
  fw.add(addr, config_base, off)
  write32(fw, CRTA_L1_BASE_PTR, addr, tmp_addr=tmp)
  return fw


def init_brisc_launch_globals(fw: Kernel, *, launch: Reg = t0, value: Reg = t1,
                              tmp: Reg = t2, origin: Reg = t3):
  keep = fw._new_label("keep_launch_noc")
  fw.li(launch, LAUNCH)
  fw.lbu(value, launch, LAUNCH_BRISC_NOC_ID)
  fw.bne(value, zero, keep)
  read32(fw, value, LAUNCH + LAUNCH_ENABLES, tmp_addr=tmp)
  fw.andi(value, value, 1 << 1)
  fw.beq(value, zero, keep)
  fw.li(value, 1)
  fw.label(keep)
  fw.sb(value, launch, LAUNCH_BRISC_NOC_ID)
  write8(fw, NOC_INDEX, value, tmp_addr=tmp)
  fw.lbu(value, launch, LAUNCH_BRISC_NOC_MODE)
  write8(fw, BRISC_NOC_MODE, value, tmp_addr=tmp)
  fw.li(tmp, CORE_INFO_ABSOLUTE_LOGICAL_X)
  fw.lbu(value, tmp, 0)
  write8(fw, MY_LOGICAL_X, value, tmp_addr=tmp)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_X)
  fw.sub(value, value, origin)
  write8(fw, MY_RELATIVE_X, value, tmp_addr=tmp)
  fw.li(tmp, CORE_INFO_ABSOLUTE_LOGICAL_Y)
  fw.lbu(value, tmp, 0)
  write8(fw, MY_LOGICAL_Y, value, tmp_addr=tmp)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_Y)
  fw.sub(value, value, origin)
  write8(fw, MY_RELATIVE_Y, value, tmp_addr=tmp)
  return fw


def copy_words(fw: Kernel, dst: int, src: int, byte_count: int, *,
               dst_reg: Reg = t0, src_reg: Reg = t1, value: Reg = t2,
               count: Reg = t3):
  fw.li(dst_reg, dst)
  fw.li(src_reg, src)
  fw.li(count, byte_count // 4)
  loop = fw._new_label("copy_words")
  done = fw._new_label("copy_done")
  fw.label(loop)
  fw.beq(count, zero, done)
  fw.lw(value, src_reg, 0)
  fw.sw(value, dst_reg, 0)
  fw.addi(src_reg, src_reg, 4)
  fw.addi(dst_reg, dst_reg, 4)
  fw.addi(count, count, -1)
  fw.j(loop)
  fw.label(done)
  return fw


def init_bank_tables(fw: Kernel):
  src = MEM_BANK_TO_NOC_SCRATCH
  copy_words(fw, DRAM_BANK_TO_NOC_XY, src, P100_DRAM_BANK_TO_NOC_SIZE)
  src += P100_DRAM_BANK_TO_NOC_SIZE
  copy_words(fw, L1_BANK_TO_NOC_XY, src, P100_L1_BANK_TO_NOC_SIZE)
  src += P100_L1_BANK_TO_NOC_SIZE
  copy_words(fw, BANK_TO_DRAM_OFFSET, src, P100_BANK_TO_DRAM_OFFSET_SIZE)
  src += P100_BANK_TO_DRAM_OFFSET_SIZE
  copy_words(fw, BANK_TO_L1_OFFSET, src, P100_BANK_TO_L1_OFFSET_SIZE)
  return fw


def init_noc_local_state(fw: Kernel, *, launch: Reg = t0, noc_id: Reg = t1,
                         noc_shift: Reg = t2, status: Reg = t3,
                         dest: Reg = t4, value: Reg = t5):
  fw.li(launch, LAUNCH)
  fw.lbu(noc_id, launch, LAUNCH_BRISC_NOC_ID)
  fw.slli(noc_shift, noc_id, 16)

  for counter, base in [
    (NIU_MST_RD_RESP_RECEIVED, NOC_READS_NUM_ISSUED),
    (NIU_MST_NONPOSTED_WR_REQ_SENT, NOC_NONPOSTED_WRITES_NUM_ISSUED),
    (NIU_MST_WR_ACK_RECEIVED, NOC_NONPOSTED_WRITES_ACKED),
    (NIU_MST_ATOMIC_RESP_RECEIVED, NOC_NONPOSTED_ATOMICS_ACKED),
    (NIU_MST_POSTED_WR_REQ_SENT, NOC_POSTED_WRITES_NUM_ISSUED),
  ]:
    fw.li(status, NOC_STATUS_BASE + counter * 4)
    fw.add(status, status, noc_shift)
    fw.lw(value, status, 0)
    fw.slli(status, noc_id, 2)
    fw.li(dest, base)
    fw.add(dest, dest, status)
    write32(fw, dest, value)
  return fw


def noc_cmd_buf_addr(noc: int, cmd_buf: int, reg: int) -> int:
  return reg + (cmd_buf << NOC_CMD_BUF_OFFSET_BIT) + (noc << NOC_INSTANCE_OFFSET_BIT)


def wait_noc_cmd_buf_ready(fw: Kernel, noc: Reg, *, addr: Reg = t0, value: Reg = t1):
  fw.li(addr, NOC_CMD_CTRL + (NCRISC_AT_CMD_BUF << NOC_CMD_BUF_OFFSET_BIT))
  fw.add(addr, addr, noc)
  loop = fw._new_label("wait_noc_cmd_buf")
  fw.label(loop)
  fw.lw(value, addr, 0)
  fw.bne(value, zero, loop)
  return fw


def write_noc_cmd_reg(fw: Kernel, noc: Reg, reg: int, value: int | Reg, *,
                      addr: Reg = t0, tmp_val: Reg = t1):
  fw.li(addr, reg + (NCRISC_AT_CMD_BUF << NOC_CMD_BUF_OFFSET_BIT))
  fw.add(addr, addr, noc)
  if isinstance(value, int):
    fw.li(tmp_val, value)
    value = tmp_val
  return fw.sw(value, addr, 0)


def notify_dispatch_core_done(fw: Kernel, *, launch: Reg = t0, mode: Reg = t1,
                              go_index: Reg = t2, go_addr: Reg = t3,
                              dispatch_addr: Reg = t4, coord: Reg = t5,
                              noc_shift: Reg = t6):
  skip = fw._new_label("skip_dispatch_notify")
  fw.li(launch, LAUNCH)
  fw.lbu(mode, launch, LAUNCH_MODE)
  fw.li(coord, DISPATCH_MODE_DEV)
  fw.bne(mode, coord, skip)

  read32(fw, go_index, GO_MESSAGE_INDEX, tmp_addr=go_addr)
  fw.slli(go_index, go_index, 2)
  fw.li(go_addr, GO_MESSAGES)
  fw.add(go_addr, go_addr, go_index)

  fw.lbu(dispatch_addr, go_addr, 0)
  fw.slli(dispatch_addr, dispatch_addr, 12)
  fw.li(coord, DISPATCH_MESSAGE_ADDR)
  fw.add(dispatch_addr, dispatch_addr, coord)

  fw.lbu(coord, go_addr, 2)
  fw.slli(coord, coord, 6)
  fw.lbu(mode, go_addr, 1)
  fw.or_(coord, coord, mode)

  fw.li(noc_shift, 0)
  fw.lbu(noc_shift, launch, LAUNCH_BRISC_NOC_ID)
  fw.slli(noc_shift, noc_shift, NOC_INSTANCE_OFFSET_BIT)
  wait_noc_cmd_buf_ready(fw, noc_shift, addr=go_addr, value=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC_AT_DATA, DISPATCH_DONE_WORD, addr=go_addr, tmp_val=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC_CTRL, NOC_INLINE_WRITE_POSTED_FIELD, addr=go_addr, tmp_val=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC_TARG_ADDR_LO, dispatch_addr, addr=go_addr)
  # C++ firmware writes (dispatch_addr >> 32) & NOC_PCIE_MASK here. For the
  # local dispatch stream register address used by this path, those mid bits
  # are zero; setting the low nibble to 0xF targets the wrong NOC address.
  write_noc_cmd_reg(fw, noc_shift, NOC_TARG_ADDR_MID, 0, addr=go_addr, tmp_val=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC_TARG_ADDR_COORDINATE, coord, addr=go_addr)
  write_noc_cmd_reg(fw, noc_shift, NOC_AT_LEN_BE, 0xF, addr=go_addr, tmp_val=mode)
  write_noc_cmd_reg(fw, noc_shift, NOC_CMD_CTRL, NOC_CTRL_SEND_REQ, addr=go_addr, tmp_val=mode)

  write32(fw, LAUNCH + LAUNCH_ENABLES, 0, tmp_addr=go_addr, tmp_val=mode)
  write8(fw, LAUNCH + LAUNCH_PRELOAD, 0, tmp_addr=go_addr, tmp_val=mode)
  read32(fw, mode, LAUNCH_MSG_RD_PTR, tmp_addr=go_addr)
  fw.addi(mode, mode, 1)
  fw.andi(mode, mode, 7)
  write32(fw, LAUNCH_MSG_RD_PTR, mode, tmp_addr=go_addr)

  fw.label(skip)
  return fw


def noc_init(fw: Kernel, *, noc_id: Reg = t0, coord: Reg = t1,
             tmp_addr: Reg = t2, tmp_val: Reg = t3):
  for noc in range(2):
    read32(fw, noc_id, noc_cmd_buf_addr(noc, 0, NOC_CFG_BASE + NOC_ID_LOGICAL * 4), tmp_addr=tmp_addr)
    fw.andi(coord, noc_id, NOC_NODE_ID_MASK)
    fw.srli(noc_id, noc_id, NOC_ADDR_NODE_ID_BITS)
    fw.andi(noc_id, noc_id, NOC_NODE_ID_MASK)
    fw.slli(noc_id, noc_id, NOC_ADDR_NODE_ID_BITS)
    fw.or_(coord, coord, noc_id)

    write32(fw, noc_cmd_buf_addr(noc, NCRISC_WR_CMD_BUF, NOC_TARG_ADDR_MID), 0, tmp_addr=tmp_addr, tmp_val=tmp_val)
    write32(
      fw,
      noc_cmd_buf_addr(noc, NCRISC_WR_CMD_BUF, NOC_TARG_ADDR_COORDINATE),
      coord,
      tmp_addr=tmp_addr,
    )
    write32(fw, noc_cmd_buf_addr(noc, NCRISC_WR_REG_CMD_BUF, NOC_TARG_ADDR_MID), 0, tmp_addr=tmp_addr, tmp_val=tmp_val)
    write32(
      fw,
      noc_cmd_buf_addr(noc, NCRISC_WR_REG_CMD_BUF, NOC_TARG_ADDR_COORDINATE),
      coord,
      tmp_addr=tmp_addr,
    )
    write32(
      fw,
      noc_cmd_buf_addr(noc, NCRISC_AT_CMD_BUF, NOC_RET_ADDR_LO),
      MEM_NOC_ATOMIC_RET_VAL_ADDR,
      tmp_addr=tmp_addr,
      tmp_val=tmp_val,
    )
    write32(fw, noc_cmd_buf_addr(noc, NCRISC_AT_CMD_BUF, NOC_RET_ADDR_MID), 0, tmp_addr=tmp_addr, tmp_val=tmp_val)
    write32(
      fw,
      noc_cmd_buf_addr(noc, NCRISC_AT_CMD_BUF, NOC_RET_ADDR_COORDINATE),
      coord,
      tmp_addr=tmp_addr,
    )
    write32(
      fw,
      noc_cmd_buf_addr(noc, NCRISC_RD_CMD_BUF, NOC_CTRL),
      NOC_RD_CMD_FIELD,
      tmp_addr=tmp_addr,
      tmp_val=tmp_val,
    )
    write32(fw, noc_cmd_buf_addr(noc, NCRISC_RD_CMD_BUF, NOC_RET_ADDR_MID), 0, tmp_addr=tmp_addr, tmp_val=tmp_val)
    write32(
      fw,
      noc_cmd_buf_addr(noc, NCRISC_RD_CMD_BUF, NOC_RET_ADDR_COORDINATE),
      coord,
      tmp_addr=tmp_addr,
    )
  return fw


def setup_local_cbs(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                    cb_config: Reg = t2, cb_if: Reg = t3, mask: Reg = t4,
                    size: Reg = t5, fifo: Reg = t6):
  fw.li(launch, LAUNCH)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
  fw.lhu(cb_config, launch, LAUNCH_LOCAL_CB_OFFSET)
  fw.add(cb_config, config_base, cb_config)
  fw.li(cb_if, CB_INTERFACE)
  fw.lw(mask, launch, LAUNCH_LOCAL_CB_MASK)

  loop = fw._new_label("setup_cb")
  skip = fw._new_label("skip_cb")
  done = fw._new_label("done_cb")
  fw.label(loop)
  fw.beq(mask, zero, done)
  fw.andi(size, mask, 1)
  fw.beq(size, zero, skip)
  fw.lw(size, cb_config, 4)
  fw.lw(fifo, cb_config, 0)
  fw.sw(size, cb_if, 0)
  fw.add(size, fifo, size)
  fw.sw(size, cb_if, 4)
  fw.lw(size, cb_config, 12)
  fw.sw(size, cb_if, 8)
  fw.lw(size, cb_config, 8)
  fw.sw(size, cb_if, 12)
  fw.sw(fifo, cb_if, 16)
  fw.sw(fifo, cb_if, 20)
  fw.sw(zero, cb_if, 24)
  fw.sw(zero, cb_if, 28)
  fw.label(skip)
  fw.addi(cb_config, cb_config, LOCAL_CB_CONFIG_SIZE)
  fw.addi(cb_if, cb_if, LOCAL_CB_INTERFACE_SIZE)
  fw.srli(mask, mask, 1)
  fw.j(loop)
  fw.label(done)
  return fw


def run_launch_kernel(fw: Kernel, role: int, *, launch: Reg = t0, config_base: Reg = t1,
                      offset: Reg = t2, entry: Reg = t3, enabled: Reg = t4):
  skip = fw._new_label("skip_kernel")
  launch_kernel_enabled(fw, role, enabled=enabled, mask=offset)
  fw.beq(enabled, zero, skip)
  fw.li(launch, LAUNCH)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
  fw.lw(offset, launch, LAUNCH_KERNEL_TEXT_OFFSET + 4 * role)
  fw.add(entry, config_base, offset)
  fw.jalr(ra, entry, 0)
  fw.label(skip)
  return fw


def build(*, text_base: dict[str, int] = FIRMWARE_TEXT_BASE) -> Kernel:
  fw = Kernel.firmware("brisc")
  setup_stack(fw)
  set_subordinate_reset_pcs(fw, text_base)
  device_setup(fw)
  init_risc_noc_coords(fw)
  invalidate_all_risc_icaches(fw)
  deassert_all_riscs(fw)
  for role in (1, 2, 3, 4):
    wait_subordinate_done(fw, role)
  signal_done(fw)
  init_bank_tables(fw)
  init_brisc_mailbox_globals(fw)
  noc_init(fw)
  init_noc_local_state(fw)
  signal_trisc0_init_sync_registers(fw)

  fw.label("run_loop")
  wait_go(fw)
  wait_subordinate_done(fw, 2)
  init_brisc_kernel_config(fw)
  init_brisc_launch_globals(fw)
  noc_init(fw)
  init_noc_local_state(fw)
  invalidate_all_risc_icaches(fw)
  signal_subordinate_if_enabled(fw, 1, RUN_SYNC_MSG_LOAD)
  for role in (2, 3, 4):
    signal_subordinate_if_enabled(fw, role, RUN_SYNC_MSG_GO)
  setup_local_cbs(fw)
  signal_subordinate_if_enabled(fw, 1, RUN_SYNC_MSG_GO)
  run_launch_kernel(fw, 0)
  for role in (1, 2, 3, 4):
    wait_subordinate_done(fw, role)
  signal_trisc0_init_sync_registers(fw)
  notify_dispatch_core_done(fw)
  signal_done(fw)
  fw.j("run_loop")
  return fw


def write_artifacts(out_dir: Path | str | None = None) -> Path:
  out = Path(__file__).resolve().parent / "build" if out_dir is None else Path(out_dir)
  out.mkdir(parents=True, exist_ok=True)
  segments = build().compile()
  manifest = {"kind": "brisc", "segments": []}
  # The generic firmware compile path pads local data out to the whole reserved
  # local-memory region. This standalone BRISC does not use local globals, and
  # uploading that synthetic zero segment would clobber old blackhole-py's
  # launch/config L1 area. Keep the real text bytes only.
  artifact_segments = [seg for seg in segments if seg.label.endswith(".text")]
  for i, seg in enumerate(artifact_segments):
    name = f"brisc.seg{i}.bin"
    (out / name).write_bytes(seg.data)
    manifest["segments"].append({
      "label": seg.label,
      "addr": f"0x{seg.addr:x}",
      "bin": name,
      "filesz": len(seg.data),
      "memsz": len(seg.data),
      "flags": 5 if seg.label.endswith(".text") else 6,
    })
  manifest_path = out / "brisc.json"
  manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
  return manifest_path


if __name__ == "__main__":
  print(write_artifacts())
