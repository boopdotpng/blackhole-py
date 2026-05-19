from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from dsl import Reg, t0, t1, t2, t3, t4, t5, t6, zero

NCRISC_STACK_TOP = 0xFFB01FF0
NCRISC_TEXT_BASE = 0x5440
NCRISC_LOCAL_DATA_BASE = 0xA2B0
NCRISC_LOCAL_DATA_SIZE = 0x864
SUBORDINATE_SYNC = 0x68
LAUNCH_MSG_RD_PTR = 0x6C
CORE_INFO_ABSOLUTE_LOGICAL_X = 0x940
CORE_INFO_ABSOLUTE_LOGICAL_Y = 0x941
RUN_SYNC_MSG_GO = 0x80
RUN_SYNC_MSG_LOAD = 0x01
RUN_SYNC_MSG_DONE = 0x00

LAUNCH = 0x70
LAUNCH_MSG_SIZE = 96
LAUNCH_KERNEL_CONFIG_BASE = 0
LAUNCH_SEM_OFFSET = 12
LAUNCH_LOCAL_CB_OFFSET = 18
LAUNCH_REMOTE_CB_OFFSET = 20
LAUNCH_RTA_OFFSET = 22
LAUNCH_KERNEL_TEXT_OFFSET = 44
LAUNCH_LOCAL_CB_MASK = 64
LAUNCH_ENABLES = 76
LAUNCH_MIN_REMOTE_CB_START_INDEX = 82
LAUNCH_SUB_DEVICE_ORIGIN_X = 92
LAUNCH_SUB_DEVICE_ORIGIN_Y = 93

# NCRISC firmware symbol addresses from the C++ NCRISC ELF used for kernel
# linking in blackhole-py-old.
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

NOC_REGS_START_ADDR = 0xFFB20000
NOC_CMD_BUF_OFFSET_BIT = 11
NOC_INSTANCE_OFFSET_BIT = 16
NOC_CFG_BASE = NOC_REGS_START_ADDR + 0x100
NOC_ID_LOGICAL = 0x12
NOC_NODE_ID_MASK = 0x3F
NOC_ADDR_NODE_ID_BITS = 6
MEM_BANK_TO_NOC_SCRATCH = 0x112B0
P100_NUM_DRAM_BANKS = 7
P100_NUM_L1_BANKS = 120
P100_DRAM_BANK_TO_NOC_SIZE = 2 * P100_NUM_DRAM_BANKS * 2
P100_L1_BANK_TO_NOC_SIZE = 2 * P100_NUM_L1_BANKS * 2
P100_BANK_TO_DRAM_OFFSET_SIZE = P100_NUM_DRAM_BANKS * 4
P100_BANK_TO_L1_OFFSET_SIZE = P100_NUM_L1_BANKS * 4

LOCAL_CB_INTERFACE_SIZE = 32
LOCAL_CB_CONFIG_SIZE = 16
CB_SYNC_TILES_ACKED_BASE = 0xFFB48020
CB_SYNC_TILES_RECEIVED_BASE = 0xFFB48028
CB_SYNC_STRIDE = 0x1000


def wait_subordinate_load_or_go(fw: Kernel, role: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  loop = fw._new_label("wait_subordinate")
  done = fw._new_label("subordinate_ready")
  fw.li(ptr, SUBORDINATE_SYNC + role - 1)
  fw.label(loop)
  fw.lbu(actual, ptr, 0)
  fw.li(expected, RUN_SYNC_MSG_GO)
  fw.beq(actual, expected, done)
  fw.li(expected, RUN_SYNC_MSG_LOAD)
  fw.beq(actual, expected, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  fw.fence()
  return fw


def init_risc_noc_coords(fw: Kernel, *, noc_id: Reg = t0, coord: Reg = t1, tmp: Reg = t2):
  for noc in range(2):
    fw.read32(noc_id, fw.noc_cmd_addr(noc, 0, NOC_CFG_BASE + NOC_ID_LOGICAL * 4), tmp_addr=tmp)
    fw.andi(coord, noc_id, NOC_NODE_ID_MASK)
    fw.write8(MY_X + noc, coord, tmp_addr=tmp)
    fw.srli(coord, noc_id, NOC_ADDR_NODE_ID_BITS)
    fw.andi(coord, coord, NOC_NODE_ID_MASK)
    fw.write8(MY_Y + noc, coord, tmp_addr=tmp)
  return fw


def init_bank_tables(fw: Kernel):
  fw.copy_words(
    DRAM_BANK_TO_NOC_XY,
    MEM_BANK_TO_NOC_SCRATCH,
    P100_DRAM_BANK_TO_NOC_SIZE + P100_L1_BANK_TO_NOC_SIZE +
    P100_BANK_TO_DRAM_OFFSET_SIZE + P100_BANK_TO_L1_OFFSET_SIZE,
  )
  return fw


def init_ncrisc_mailbox_globals(fw: Kernel, *, value: Reg = t0, tmp: Reg = t1):
  fw.read8(value, CORE_INFO_ABSOLUTE_LOGICAL_X, tmp_addr=tmp)
  fw.write8(MY_LOGICAL_X, value, tmp_addr=tmp)
  fw.read8(value, CORE_INFO_ABSOLUTE_LOGICAL_Y, tmp_addr=tmp)
  fw.write8(MY_LOGICAL_Y, value, tmp_addr=tmp)
  return fw


def init_ncrisc_kernel_config(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                              off: Reg = t2, addr: Reg = t3, tmp: Reg = t4):
  fw.current_launch_ptr(launch=launch, tmp=tmp)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)

  for i in range(3):
    fw.lhu(off, launch, LAUNCH_SEM_OFFSET + 2 * i)
    fw.add(addr, config_base, off)
    fw.write32(SEM_L1_BASE + 4 * i, addr, tmp_addr=tmp)

  fw.lhu(off, launch, LAUNCH_RTA_OFFSET + 4)
  fw.add(addr, config_base, off)
  fw.write32(RTA_L1_BASE_PTR, addr, tmp_addr=tmp)

  fw.lhu(off, launch, LAUNCH_RTA_OFFSET + 6)
  fw.add(addr, config_base, off)
  fw.write32(CRTA_L1_BASE_PTR, addr, tmp_addr=tmp)
  return fw


def init_ncrisc_launch_globals(fw: Kernel, *, launch: Reg = t0, value: Reg = t1,
                               tmp: Reg = t2, origin: Reg = t3):
  fw.current_launch_ptr(launch=launch, tmp=tmp)
  fw.read8(value, MY_LOGICAL_X, tmp_addr=tmp)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_X)
  fw.sub(value, value, origin)
  fw.write8(MY_RELATIVE_X, value, tmp_addr=tmp)
  fw.read8(value, MY_LOGICAL_Y, tmp_addr=tmp)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_Y)
  fw.sub(value, value, origin)
  fw.write8(MY_RELATIVE_Y, value, tmp_addr=tmp)
  return fw


def setup_local_cbs_from_mask(fw: Kernel, cb_config: Reg, cb_if: Reg, mask: Reg, *,
                              size: Reg = t5, fifo: Reg = t6, tmp: Reg = t0):
  fw.li(tmp, CB_SYNC_TILES_ACKED_BASE)
  fw.li(t1, CB_SYNC_TILES_RECEIVED_BASE)
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
  fw.sw(zero, tmp, 0)
  fw.sw(zero, t1, 0)
  fw.label(skip)
  fw.addi(cb_config, cb_config, LOCAL_CB_CONFIG_SIZE)
  fw.addi(cb_if, cb_if, LOCAL_CB_INTERFACE_SIZE)
  fw.li(size, CB_SYNC_STRIDE)
  fw.add(tmp, tmp, size)
  fw.add(t1, t1, size)
  fw.srli(mask, mask, 1)
  fw.j(loop)
  fw.label(done)
  return fw


def setup_local_cbs(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                    cb_config: Reg = t2, cb_if: Reg = t3, mask: Reg = t4):
  fw.current_launch_ptr(launch=launch, tmp=mask)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
  fw.lhu(cb_config, launch, LAUNCH_LOCAL_CB_OFFSET)
  fw.add(cb_config, config_base, cb_config)
  fw.li(cb_if, CB_INTERFACE)
  fw.lw(mask, launch, LAUNCH_LOCAL_CB_MASK)
  setup_local_cbs_from_mask(fw, cb_config, cb_if, mask)
  return fw


def build() -> Kernel:
  fw = Kernel(base_addr=NCRISC_TEXT_BASE)
  fw.segment(NCRISC_LOCAL_DATA_BASE, b"\x68".ljust(NCRISC_LOCAL_DATA_SIZE, b"\0"), label="local_data")
  fw.setup_stack(NCRISC_STACK_TOP)
  fw.configure_csr()
  init_bank_tables(fw)
  init_risc_noc_coords(fw)
  init_ncrisc_mailbox_globals(fw)
  fw.signal_subordinate_done(1)
  fw.label("run_loop")
  wait_subordinate_load_or_go(fw, 1)
  init_ncrisc_kernel_config(fw)
  setup_local_cbs(fw)
  init_ncrisc_launch_globals(fw)
  fw.wait8(SUBORDINATE_SYNC, RUN_SYNC_MSG_GO)
  fw.run_launch_kernel(1)
  fw.signal_subordinate_done(1)
  fw.j("run_loop")
  return fw
