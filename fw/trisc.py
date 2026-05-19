from __future__ import annotations
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from dsl import Reg, gp, t0, t1, t2, t3, t4, t5, t6, zero
from ttk.addrs import CircularBuffer as CB, Firmware, Launch, Mailbox, RunSync, Tensix, TensixMMIO, TriscMailbox as TM

def setup_gp(fw: Kernel):
  return fw.li(gp, Firmware.TRISC_GLOBAL_POINTER)

def zero_regfile(fw: Kernel, *, ptr: Reg = t0, count: Reg = t1):
  fw.li(ptr, Tensix.REGFILE_BASE)
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
    TensixMMIO.LOCAL_RAM_START,
    Firmware.TRISC_LOCAL_DATA_BASE[trisc_id],
    Firmware.TRISC_LOCAL_DATA_SIZE[trisc_id],
  )

def init_common_state(fw: Kernel, data: dict[str, int]):
  fw.write32(data["dest_offset_id"], 0)
  fw.write32(data["op_info_offset"], 0)
  fw.write32(data["cfg_state_id"], 0)
  fw.write32(Tensix.CFG_BASE + Tensix.PRNG_SEED_SEED_VAL_ADDR32 * 4, 0)
  fw.delay_cycles(600)
  fw.read8(t1, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_X, tmp_addr=t0)
  fw.write8(data["my_logical_x"], t1, tmp_addr=t0)
  fw.read8(t1, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_Y, tmp_addr=t0)
  fw.write8(data["my_logical_y"], t1, tmp_addr=t0)
  return fw

def wait_trisc_message(fw: Kernel, trisc_id: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  loop = fw._new_label("wait_trisc")
  done = fw._new_label("trisc_go")
  init_sync = fw._new_label("trisc_init_sync")
  fw.li(ptr, Mailbox.SUBORDINATE_SYNC + trisc_id + 1)
  fw.label(loop)
  fw.lbu(actual, ptr, 0)
  if trisc_id == 0:
    fw.write32(Firmware.FW_DEBUG + 4, actual, tmp_addr=expected)
  fw.li(expected, RunSync.GO)
  fw.beq(actual, expected, done)
  if trisc_id == 0:
    fw.li(expected, RunSync.INIT_SYNC_REGISTERS)
    fw.beq(actual, expected, init_sync)
  fw.fence()
  fw.j(loop)
  if trisc_id == 0:
    fw.label(init_sync)
    fw.write32(Firmware.FW_DEBUG + 8, 0x7015C003, tmp_addr=actual, tmp_val=expected)
    init_sync_registers(fw)
    fw.li(ptr, Mailbox.SUBORDINATE_SYNC + trisc_id + 1)
    fw.write8(ptr, RunSync.DONE, tmp_addr=actual, tmp_val=expected)
    fw.write32(Firmware.FW_DEBUG + 12, 0x7015C004, tmp_addr=actual, tmp_val=expected)
    fw.j(loop)
  fw.label(done)
  if trisc_id == 0:
    fw.write32(Firmware.FW_DEBUG + 16, 0x7015C080, tmp_addr=actual, tmp_val=expected)
  fw.fence()
  return fw

def init_sync_registers(fw: Kernel, *, recv: Reg = t0, ack: Reg = t1, count: Reg = t2, stride: Reg = t3):
  fw.li(recv, CB.SYNC_TILES_RECEIVED_BASE)
  fw.li(ack, CB.SYNC_TILES_ACKED_BASE)
  fw.li(count, CB.NUM_CIRCULAR_BUFFERS)
  fw.li(stride, CB.SYNC_STRIDE)
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
  fw.addi(cb_config, cb_config, CB.LOCAL_CONFIG_SIZE)
  fw.addi(cb_if, cb_if, CB.LOCAL_INTERFACE_SIZE)
  fw.srli(mask, mask, 1)
  fw.j(loop)
  fw.label(done)
  return fw

def setup_local_cbs(fw: Kernel, trisc_id: int, data: dict[str, int], *, launch: Reg = t0, config_base: Reg = t1,
                    cb_config: Reg = t2, cb_if: Reg = t3, mask: Reg = t4):
  fw.current_launch_ptr(launch=launch, tmp=mask)
  fw.lw(config_base, launch, Launch.KERNEL_CONFIG_BASE)
  fw.lhu(cb_config, launch, Launch.LOCAL_CB_OFFSET)
  fw.add(cb_config, config_base, cb_config)
  fw.li(cb_if, data["cb_interface"])
  fw.lw(mask, launch, Launch.LOCAL_CB_MASK)
  setup_local_cbs_from_mask(fw, trisc_id, cb_config, cb_if, mask)
  return fw

def init_trisc_kernel_config(fw: Kernel, trisc_id: int, data: dict[str, int], *,
                             launch: Reg = t0, config_base: Reg = t1, off: Reg = t2,
                             addr: Reg = t3, value: Reg = t4, origin: Reg = t5):
  fw.current_launch_ptr(launch=launch, tmp=value)
  fw.lw(config_base, launch, Launch.KERNEL_CONFIG_BASE)

  rta_slot = 2 + trisc_id
  fw.lhu(off, launch, Launch.RTA_OFFSET + 4 * rta_slot)
  fw.add(addr, config_base, off)
  fw.write32(data["rta_l1_base"], addr, tmp_addr=value)

  fw.lhu(off, launch, Launch.RTA_OFFSET + 4 * rta_slot + 2)
  fw.add(addr, config_base, off)
  fw.write32(data["crta_l1_base"], addr, tmp_addr=value)

  fw.read8(value, data["my_logical_x"], tmp_addr=addr)
  fw.lbu(origin, launch, Launch.SUB_DEVICE_ORIGIN_X)
  fw.sub(value, value, origin)
  fw.write8(data["my_relative_x"], value, tmp_addr=addr)

  fw.read8(value, data["my_logical_y"], tmp_addr=addr)
  fw.lbu(origin, launch, Launch.SUB_DEVICE_ORIGIN_Y)
  fw.sub(value, value, origin)
  fw.write8(data["my_relative_y"], value, tmp_addr=addr)
  return fw

def tensix_sync(fw: Kernel):
  fw.write32(Tensix.PC_BUF_SYNC, 0)
  fw.read32(t0, Tensix.PC_BUF_SYNC)
  fw.and_(zero, zero, t0)
  return fw

def build(trisc_id: int) -> Kernel:
  if trisc_id not in (0, 1, 2):
    raise ValueError(f"unknown TRISC id {trisc_id!r}")
  role = 2 + trisc_id
  data = TM.DATA1 if trisc_id == 1 else TM.DATA_COMMON
  fw = Kernel(base_addr=Firmware.TRISC_TEXT_BASE[trisc_id])
  fw.segment(Firmware.TRISC_LOCAL_DATA_BASE[trisc_id], b"\0" * Firmware.TRISC_LOCAL_DATA_SIZE[trisc_id], label="local_data")
  setup_gp(fw)
  fw.setup_stack(Firmware.TRISC_STACK_TOP)
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
