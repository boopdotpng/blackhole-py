from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from dsl import Reg, t0, t1, t2, t3, t4, t5, t6, zero
from ttk.addrs import (
  CircularBuffer as CB, Firmware, Launch, Mailbox, NcriscMailbox as NM,
  NocCfg, P100BankTable, RunSync, TensixL1,
)
from ttk.hw.noc import NOC

def wait_subordinate_load_or_go(fw: Kernel, role: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
  loop = fw._new_label("wait_subordinate")
  done = fw._new_label("subordinate_ready")
  fw.li(ptr, Mailbox.SUBORDINATE_SYNC + role - 1)
  fw.label(loop)
  fw.lbu(actual, ptr, 0)
  fw.li(expected, RunSync.GO)
  fw.beq(actual, expected, done)
  fw.li(expected, RunSync.LOAD)
  fw.beq(actual, expected, done)
  fw.fence()
  fw.j(loop)
  fw.label(done)
  fw.fence()
  return fw

def init_risc_noc_coords(fw: Kernel, *, noc_id: Reg = t0, coord: Reg = t1, tmp: Reg = t2):
  for noc in range(2):
    fw.read32(noc_id, fw.noc_cmd_addr(noc, 0, NOC.CFG_BASE + NocCfg.ID_LOGICAL * 4), tmp_addr=tmp)
    fw.andi(coord, noc_id, NocCfg.NODE_ID_MASK)
    fw.write8(NM.MY_X + noc, coord, tmp_addr=tmp)
    fw.srli(coord, noc_id, NocCfg.ADDR_NODE_ID_BITS)
    fw.andi(coord, coord, NocCfg.NODE_ID_MASK)
    fw.write8(NM.MY_Y + noc, coord, tmp_addr=tmp)
  return fw

def init_ncrisc_mailbox_globals(fw: Kernel, *, value: Reg = t0, tmp: Reg = t1):
  fw.read8(value, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_X, tmp_addr=tmp)
  fw.write8(NM.MY_LOGICAL_X, value, tmp_addr=tmp)
  fw.read8(value, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_Y, tmp_addr=tmp)
  fw.write8(NM.MY_LOGICAL_Y, value, tmp_addr=tmp)
  return fw

def init_ncrisc_kernel_config(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                              off: Reg = t2, addr: Reg = t3, tmp: Reg = t4):
  fw.current_launch_ptr(launch=launch, tmp=tmp)
  fw.lw(config_base, launch, Launch.KERNEL_CONFIG_BASE)

  for i in range(3):
    fw.lhu(off, launch, Launch.SEM_OFFSET + 2 * i)
    fw.add(addr, config_base, off)
    fw.write32(NM.SEM_L1_BASE + 4 * i, addr, tmp_addr=tmp)

  fw.lhu(off, launch, Launch.RTA_OFFSET + 4)
  fw.add(addr, config_base, off)
  fw.write32(NM.RTA_L1_BASE_PTR, addr, tmp_addr=tmp)

  fw.lhu(off, launch, Launch.RTA_OFFSET + 6)
  fw.add(addr, config_base, off)
  fw.write32(NM.CRTA_L1_BASE_PTR, addr, tmp_addr=tmp)
  return fw

def init_ncrisc_launch_globals(fw: Kernel, *, launch: Reg = t0, value: Reg = t1,
                               tmp: Reg = t2, origin: Reg = t3):
  fw.current_launch_ptr(launch=launch, tmp=tmp)
  fw.read8(value, NM.MY_LOGICAL_X, tmp_addr=tmp)
  fw.lbu(origin, launch, Launch.SUB_DEVICE_ORIGIN_X)
  fw.sub(value, value, origin)
  fw.write8(NM.MY_RELATIVE_X, value, tmp_addr=tmp)
  fw.read8(value, NM.MY_LOGICAL_Y, tmp_addr=tmp)
  fw.lbu(origin, launch, Launch.SUB_DEVICE_ORIGIN_Y)
  fw.sub(value, value, origin)
  fw.write8(NM.MY_RELATIVE_Y, value, tmp_addr=tmp)
  return fw

def setup_local_cbs_from_mask(fw: Kernel, cb_config: Reg, cb_if: Reg, mask: Reg, *,
                              size: Reg = t5, fifo: Reg = t6, tmp: Reg = t0):
  fw.li(tmp, CB.SYNC_TILES_ACKED_BASE)
  fw.li(t1, CB.SYNC_TILES_RECEIVED_BASE)
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
  fw.addi(cb_config, cb_config, CB.LOCAL_CONFIG_SIZE)
  fw.addi(cb_if, cb_if, CB.LOCAL_INTERFACE_SIZE)
  fw.li(size, CB.SYNC_STRIDE)
  fw.add(tmp, tmp, size)
  fw.add(t1, t1, size)
  fw.srli(mask, mask, 1)
  fw.j(loop)
  fw.label(done)
  return fw

def setup_local_cbs(fw: Kernel, *, launch: Reg = t0, config_base: Reg = t1,
                    cb_config: Reg = t2, cb_if: Reg = t3, mask: Reg = t4):
  fw.current_launch_ptr(launch=launch, tmp=mask)
  fw.lw(config_base, launch, Launch.KERNEL_CONFIG_BASE)
  fw.lhu(cb_config, launch, Launch.LOCAL_CB_OFFSET)
  fw.add(cb_config, config_base, cb_config)
  fw.li(cb_if, NM.CB_INTERFACE)
  fw.lw(mask, launch, Launch.LOCAL_CB_MASK)
  setup_local_cbs_from_mask(fw, cb_config, cb_if, mask)
  return fw

def build() -> Kernel:
  fw = Kernel(base_addr=Firmware.TEXT_BASE["ncrisc"])
  fw.segment(Firmware.LOCAL_DATA_BASE["ncrisc"], b"\x68".ljust(Firmware.LOCAL_DATA_SIZE["ncrisc"], b"\0"), label="local_data")
  fw.setup_stack(Firmware.NCRISC_STACK_TOP)
  fw.configure_csr()
  # init_bank_tables
  fw.copy_words(
    NM.DRAM_BANK_TO_NOC_XY,
    TensixL1.MEM_BANK_TO_NOC_SCRATCH,
    P100BankTable.DRAM_BANK_TO_NOC_SIZE + P100BankTable.L1_BANK_TO_NOC_SIZE +
    P100BankTable.BANK_TO_DRAM_OFFSET_SIZE + P100BankTable.BANK_TO_L1_OFFSET_SIZE,
  )
  init_risc_noc_coords(fw)
  init_ncrisc_mailbox_globals(fw)
  fw.signal_subordinate_done(1)
  fw.label("run_loop")
  wait_subordinate_load_or_go(fw, 1)
  init_ncrisc_kernel_config(fw)
  setup_local_cbs(fw)
  init_ncrisc_launch_globals(fw)
  fw.wait8(Mailbox.SUBORDINATE_SYNC, RunSync.GO)
  fw.run_launch_kernel(1)
  fw.signal_subordinate_done(1)
  fw.j("run_loop")
  return fw
