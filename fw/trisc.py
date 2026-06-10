from __future__ import annotations
import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel, KernelBase
from dsl import Reg, gp, t0, t1, t2, t3, t4, t5, zero
from ttk import Cb, Tensix
from ttk.cb import CircularBuffer as CB
from ttk.mailbox import Firmware, TriscMailbox as TM
from ttk.tensix import Launch, Mailbox, RunSync, TensixMMIO, TensixRegs

def build(trisc_id: int) -> KernelBase:
  if trisc_id not in (0, 1, 2):
    raise ValueError(f"unknown TRISC id {trisc_id!r}")
  role = 2 + trisc_id
  data = TM.DATA1 if trisc_id == 1 else TM.DATA_COMMON
  fw = Kernel(Tensix, Cb, base_addr=Firmware.TRISC_TEXT_BASE[trisc_id])
  fw.segment(Firmware.TRISC_LOCAL_DATA_BASE[trisc_id], b"\0" * Firmware.TRISC_LOCAL_DATA_SIZE[trisc_id], label="local_data")
  # setup_gp
  fw.li(gp, Firmware.TRISC_GLOBAL_POINTER)
  fw.setup_stack(Firmware.TRISC_STACK_TOP)
  fw.configure_csr()
  # init_local_data
  fw.copy_words(
    TensixMMIO.LOCAL_RAM_START,
    Firmware.TRISC_LOCAL_DATA_BASE[trisc_id],
    Firmware.TRISC_LOCAL_DATA_SIZE[trisc_id],
  )

  # zero_regfile
  fw.li(t0, TensixRegs.REGFILE_BASE)
  fw.li(t1, 64)
  zero_regfile_loop = fw._new_label("zero_regfile")
  zero_regfile_done = fw._new_label("zero_regfile_done")
  fw.label(zero_regfile_loop)
  fw.beq(t1, zero, zero_regfile_done)
  fw.sw(zero, t0, 0)
  fw.addi(t0, t0, 4)
  fw.addi(t1, t1, -1)
  fw.j(zero_regfile_loop)
  fw.label(zero_regfile_done)

  # init_common_state
  fw.write32(data["dest_offset_id"], 0)
  fw.write32(data["op_info_offset"], 0)
  fw.write32(data["cfg_state_id"], 0)
  fw.write32(TensixRegs.CFG_BASE + TensixRegs.PRNG_SEED_SEED_VAL_ADDR32 * 4, 0)
  fw.delay_cycles(600)
  fw.read8(t1, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_X, tmp_addr=t0)
  fw.write8(data["my_logical_x"], t1, tmp_addr=t0)
  fw.read8(t1, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_Y, tmp_addr=t0)
  fw.write8(data["my_logical_y"], t1, tmp_addr=t0)

  fw.signal_subordinate_done(role)
  fw.label("run_loop")

  # wait_trisc_message
  wait_trisc_loop = fw._new_label("wait_trisc")
  trisc_go = fw._new_label("trisc_go")
  trisc_init_sync = fw._new_label("trisc_init_sync")
  fw.li(t0, Mailbox.SUBORDINATE_SYNC + trisc_id + 1)
  fw.label(wait_trisc_loop)
  fw.lbu(t1, t0, 0)
  fw.li(t2, RunSync.GO)
  fw.beq(t1, t2, trisc_go)
  if trisc_id == 0:
    fw.li(t2, RunSync.INIT_SYNC_REGISTERS)
    fw.beq(t1, t2, trisc_init_sync)
  fw.fence()
  fw.j(wait_trisc_loop)
  if trisc_id == 0:
    fw.label(trisc_init_sync)
    # init_sync_registers
    fw.li(t0, CB.SYNC_TILES_RECEIVED_BASE)
    fw.li(t1, CB.SYNC_TILES_ACKED_BASE)
    fw.li(t2, CB.NUM_CIRCULAR_BUFFERS)
    fw.li(t3, CB.SYNC_STRIDE)
    init_cb_sync_loop = fw._new_label("init_cb_sync")
    init_cb_sync_done = fw._new_label("init_cb_sync_done")
    fw.label(init_cb_sync_loop)
    fw.beq(t2, zero, init_cb_sync_done)
    fw.sw(zero, t0, 0)
    fw.sw(zero, t1, 0)
    fw.add(t0, t0, t3)
    fw.add(t1, t1, t3)
    fw.addi(t2, t2, -1)
    fw.j(init_cb_sync_loop)
    fw.label(init_cb_sync_done)
    fw.li(t0, Mailbox.SUBORDINATE_SYNC + trisc_id + 1)
    fw.write8(t0, RunSync.DONE, tmp_addr=t1, tmp_val=t2)
    fw.j(wait_trisc_loop)
  fw.label(trisc_go)
  fw.fence()

  if trisc_id in (0, 2):
    # setup_local_cbs
    fw.setup_local_cbs(data["cb_interface"], trisc_id=trisc_id)

  # init_trisc_kernel_config
  fw.current_launch_ptr(launch=t0, tmp=t4)
  fw.lw(t1, t0, Launch.KERNEL_CONFIG_BASE)
  rta_slot = 2 + trisc_id
  fw.lhu(t2, t0, Launch.RTA_OFFSET + 4 * rta_slot)
  fw.add(t3, t1, t2)
  fw.write32(data["rta_l1_base"], t3, tmp_addr=t4)
  fw.lhu(t2, t0, Launch.RTA_OFFSET + 4 * rta_slot + 2)
  fw.add(t3, t1, t2)
  fw.write32(data["crta_l1_base"], t3, tmp_addr=t4)
  fw.read8(t4, data["my_logical_x"], tmp_addr=t3)
  fw.lbu(t5, t0, Launch.SUB_DEVICE_ORIGIN_X)
  fw.sub(t4, t4, t5)
  fw.write8(data["my_relative_x"], t4, tmp_addr=t3)
  fw.read8(t4, data["my_logical_y"], tmp_addr=t3)
  fw.lbu(t5, t0, Launch.SUB_DEVICE_ORIGIN_Y)
  fw.sub(t4, t4, t5)
  fw.write8(data["my_relative_y"], t4, tmp_addr=t3)

  fw.run_launch_kernel(2 + trisc_id)

  fw.signal_subordinate_done(role)
  fw.j("run_loop")
  return fw

def build_trisc0() -> KernelBase:
  return build(0)

def build_trisc1() -> KernelBase:
  return build(1)

def build_trisc2() -> KernelBase:
  return build(2)
