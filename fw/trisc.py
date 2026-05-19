from __future__ import annotations
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from dsl import Reg, gp, t0, t1, t2, t3, t4, t5, t6, zero

TRISC_GLOBAL_POINTER = 0xFFB007F0
TRISC_STACK_TOP = 0xFFB00FF0
TRISC_TEXT_BASE = {
  0: 0x5A40,
  1: 0x6040,
  2: 0x6640,
}
TRISC_LOCAL_DATA_BASE = {
  0: 0xC2B0,
  1: 0xD2B0,
  2: 0xE2B0,
}
SUBORDINATE_SYNC = 0x68
LAUNCH_MSG_RD_PTR = 0x6C
RUN_SYNC_MSG_GO = 0x80
RUN_SYNC_MSG_INIT_SYNC_REGISTERS = 0x03
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
LAUNCH_MIN_REMOTE_CB_START_INDEX = 70
LAUNCH_SUB_DEVICE_ORIGIN_X = 92
LAUNCH_SUB_DEVICE_ORIGIN_Y = 93

CORE_INFO_ABSOLUTE_LOGICAL_X = 0x940
CORE_INFO_ABSOLUTE_LOGICAL_Y = 0x941
REGFILE_BASE = 0xFFE00000
TENSIX_CFG_BASE = 0xFFEF0000
PRNG_SEED_Seed_Val_ADDR32 = 186
PC_BUF_SYNC = 0xFFE80004
CB_SYNC_TILES_ACKED_BASE = 0xFFB48020
CB_SYNC_TILES_RECEIVED_BASE = 0xFFB48028
CB_SYNC_STRIDE = 0x1000
NUM_CIRCULAR_BUFFERS = 32
LOCAL_CB_INTERFACE_SIZE = 32
LOCAL_CB_CONFIG_SIZE = 16
FW_DEBUG = 0x19000

TRISC_DATA_COMMON = {
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

TRISC1_DATA = {
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

TRISC_LOCAL_END = {
  0: 0xFFB00820,
  1: 0xFFB0001C,
  2: 0xFFB00820,
}

TRISC_LOCAL_DATA_SIZE = {
  0: 1056,
  1: 28,
  2: 1056,
}


def setup_gp(fw: Kernel):
  return fw.li(gp, TRISC_GLOBAL_POINTER)


def zero_regfile(fw: Kernel, *, ptr: Reg = t0, count: Reg = t1):
  fw.li(ptr, REGFILE_BASE)
  fw.li(count, 64)
  loop = fw._new_label("zero_regfile")
  done = fw._new_label("zero_regfile_done")
  fw.label(loop)
  fw.beq(count, zero, done)
  fw.sw(zero, ptr, 0)
  fw.addi(ptr, ptr, 4)
  fw.addi(count, count, -1)
  fw.j(loop)
  fw.label(done)
  return fw


def init_local_data(fw: Kernel, trisc_id: int):
  return fw.copy_words(
    0xFFB00000,
    TRISC_LOCAL_DATA_BASE[trisc_id],
    TRISC_LOCAL_DATA_SIZE[trisc_id],
  )


def init_common_state(fw: Kernel, data: dict[str, int]):
  fw.write32(data["dest_offset_id"], 0)
  fw.write32(data["op_info_offset"], 0)
  fw.write32(data["cfg_state_id"], 0)
  fw.write32(TENSIX_CFG_BASE + PRNG_SEED_Seed_Val_ADDR32 * 4, 0)
  fw.delay_cycles(600)
  fw.read8(t1, CORE_INFO_ABSOLUTE_LOGICAL_X, tmp_addr=t0)
  fw.write8(data["my_logical_x"], t1, tmp_addr=t0)
  fw.read8(t1, CORE_INFO_ABSOLUTE_LOGICAL_Y, tmp_addr=t0)
  fw.write8(data["my_logical_y"], t1, tmp_addr=t0)
  return fw


def wait_trisc_message(fw: Kernel, trisc_id: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  loop = fw._new_label("wait_trisc")
  done = fw._new_label("trisc_go")
  init_sync = fw._new_label("trisc_init_sync")
  fw.li(ptr, SUBORDINATE_SYNC + trisc_id + 1)
  fw.label(loop)
  fw.lbu(actual, ptr, 0)
  if trisc_id == 0:
    fw.write32(FW_DEBUG + 4, actual, tmp_addr=expected)
  fw.li(expected, RUN_SYNC_MSG_GO)
  fw.beq(actual, expected, done)
  if trisc_id == 0:
    fw.li(expected, RUN_SYNC_MSG_INIT_SYNC_REGISTERS)
    fw.beq(actual, expected, init_sync)
  fw.fence()
  fw.j(loop)
  if trisc_id == 0:
    fw.label(init_sync)
    fw.write32(FW_DEBUG + 8, 0x7015C003, tmp_addr=actual, tmp_val=expected)
    init_sync_registers(fw)
    fw.li(ptr, SUBORDINATE_SYNC + trisc_id + 1)
    fw.write8(ptr, RUN_SYNC_MSG_DONE, tmp_addr=actual, tmp_val=expected)
    fw.write32(FW_DEBUG + 12, 0x7015C004, tmp_addr=actual, tmp_val=expected)
    fw.j(loop)
  fw.label(done)
  if trisc_id == 0:
    fw.write32(FW_DEBUG + 16, 0x7015C080, tmp_addr=actual, tmp_val=expected)
  fw.fence()
  return fw


def init_sync_registers(fw: Kernel, *, recv: Reg = t0, ack: Reg = t1, count: Reg = t2, stride: Reg = t3):
  fw.li(recv, CB_SYNC_TILES_RECEIVED_BASE)
  fw.li(ack, CB_SYNC_TILES_ACKED_BASE)
  fw.li(count, NUM_CIRCULAR_BUFFERS)
  fw.li(stride, CB_SYNC_STRIDE)
  loop = fw._new_label("init_cb_sync")
  done = fw._new_label("init_cb_sync_done")
  fw.label(loop)
  fw.beq(count, zero, done)
  fw.sw(zero, recv, 0)
  fw.sw(zero, ack, 0)
  fw.add(recv, recv, stride)
  fw.add(ack, ack, stride)
  fw.addi(count, count, -1)
  fw.j(loop)
  fw.label(done)
  return fw


def setup_local_cbs_from_mask(fw: Kernel, trisc_id: int, cb_config: Reg, cb_if: Reg, mask: Reg, *,
                              size: Reg = t5, fifo: Reg = t6, page: Reg = t0, tmp: Reg = t1):
  loop = fw._new_label("setup_cb")
  skip = fw._new_label("skip_cb")
  done = fw._new_label("done_cb")
  fw.label(loop)
  fw.beq(mask, zero, done)
  fw.andi(tmp, mask, 1)
  fw.beq(tmp, zero, skip)
  fw.lw(size, cb_config, 4)
  fw.lw(fifo, cb_config, 0)
  fw.lw(page, cb_config, 12)
  fw.srli(size, size, 4)
  fw.srli(fifo, fifo, 4)
  fw.srli(page, page, 4)
  fw.sw(size, cb_if, 0)
  fw.add(size, fifo, size)
  fw.sw(size, cb_if, 4)
  fw.sw(page, cb_if, 8)
  if trisc_id == 0:
    fw.sw(fifo, cb_if, 16)
  else:
    fw.lw(tmp, cb_config, 8)
    fw.sw(tmp, cb_if, 12)
    fw.sw(fifo, cb_if, 20)
  fw.sw(zero, cb_if, 24)
  if trisc_id == 2:
    fw.sw(zero, cb_if, 28)
  fw.label(skip)
  fw.addi(cb_config, cb_config, LOCAL_CB_CONFIG_SIZE)
  fw.addi(cb_if, cb_if, LOCAL_CB_INTERFACE_SIZE)
  fw.srli(mask, mask, 1)
  fw.j(loop)
  fw.label(done)
  return fw


def setup_local_cbs(fw: Kernel, trisc_id: int, data: dict[str, int], *, launch: Reg = t0, config_base: Reg = t1,
                    cb_config: Reg = t2, cb_if: Reg = t3, mask: Reg = t4):
  fw.current_launch_ptr(launch=launch, tmp=mask)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
  fw.lhu(cb_config, launch, LAUNCH_LOCAL_CB_OFFSET)
  fw.add(cb_config, config_base, cb_config)
  fw.li(cb_if, data["cb_interface"])
  fw.lw(mask, launch, LAUNCH_LOCAL_CB_MASK)
  setup_local_cbs_from_mask(fw, trisc_id, cb_config, cb_if, mask)
  return fw


def init_trisc_kernel_config(fw: Kernel, trisc_id: int, data: dict[str, int], *,
                             launch: Reg = t0, config_base: Reg = t1, off: Reg = t2,
                             addr: Reg = t3, value: Reg = t4, origin: Reg = t5):
  fw.current_launch_ptr(launch=launch, tmp=value)
  fw.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)

  rta_slot = 2 + trisc_id
  fw.lhu(off, launch, LAUNCH_RTA_OFFSET + 4 * rta_slot)
  fw.add(addr, config_base, off)
  fw.write32(data["rta_l1_base"], addr, tmp_addr=value)

  fw.lhu(off, launch, LAUNCH_RTA_OFFSET + 4 * rta_slot + 2)
  fw.add(addr, config_base, off)
  fw.write32(data["crta_l1_base"], addr, tmp_addr=value)

  fw.read8(value, data["my_logical_x"], tmp_addr=addr)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_X)
  fw.sub(value, value, origin)
  fw.write8(data["my_relative_x"], value, tmp_addr=addr)

  fw.read8(value, data["my_logical_y"], tmp_addr=addr)
  fw.lbu(origin, launch, LAUNCH_SUB_DEVICE_ORIGIN_Y)
  fw.sub(value, value, origin)
  fw.write8(data["my_relative_y"], value, tmp_addr=addr)
  return fw


def tensix_sync(fw: Kernel):
  fw.write32(PC_BUF_SYNC, 0)
  fw.read32(t0, PC_BUF_SYNC)
  fw.and_(zero, zero, t0)
  return fw


def build(trisc_id: int) -> Kernel:
  if trisc_id not in (0, 1, 2):
    raise ValueError(f"unknown TRISC id {trisc_id!r}")
  role = 2 + trisc_id
  data = TRISC1_DATA if trisc_id == 1 else TRISC_DATA_COMMON
  fw = Kernel(base_addr=TRISC_TEXT_BASE[trisc_id])
  fw.segment(TRISC_LOCAL_DATA_BASE[trisc_id], b"\0" * TRISC_LOCAL_DATA_SIZE[trisc_id], label="local_data")
  setup_gp(fw)
  fw.setup_stack(TRISC_STACK_TOP)
  fw.configure_csr()
  init_local_data(fw, trisc_id)
  zero_regfile(fw)
  init_common_state(fw, data)
  fw.signal_subordinate_done(role)
  fw.label("run_loop")
  wait_trisc_message(fw, trisc_id)
  if trisc_id in (0, 2):
    setup_local_cbs(fw, trisc_id, data)
  init_trisc_kernel_config(fw, trisc_id, data)
  fw.run_launch_kernel(2 + trisc_id)
  tensix_sync(fw)
  fw.signal_subordinate_done(role)
  fw.j("run_loop")
  return fw

def build_trisc0() -> Kernel:
  return build(0)

def build_trisc1() -> Kernel:
  return build(1)

def build_trisc2() -> Kernel:
  return build(2)
