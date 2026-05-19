from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel
from dsl import t0, t1, t2, t3, t4, t5, t6, zero
from ttk.addrs import (
  CircularBuffer as CB, Firmware, Launch, Mailbox, NcriscMailbox as NM,
  NocCfg, P100BankTable, RunSync, TensixL1,
)
from ttk.hw.noc import NOC

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

  # init_risc_noc_coords
  for noc in range(2):
    fw.read32(t0, fw.noc_cmd_addr(noc, 0, NOC.CFG_BASE + NocCfg.ID_LOGICAL * 4), tmp_addr=t2)
    fw.andi(t1, t0, NocCfg.NODE_ID_MASK)
    fw.write8(NM.MY_X + noc, t1, tmp_addr=t2)
    fw.srli(t1, t0, NocCfg.ADDR_NODE_ID_BITS)
    fw.andi(t1, t1, NocCfg.NODE_ID_MASK)
    fw.write8(NM.MY_Y + noc, t1, tmp_addr=t2)

  # init_ncrisc_mailbox_globals
  fw.read8(t0, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_X, tmp_addr=t1)
  fw.write8(NM.MY_LOGICAL_X, t0, tmp_addr=t1)
  fw.read8(t0, Mailbox.CORE_INFO_ABSOLUTE_LOGICAL_Y, tmp_addr=t1)
  fw.write8(NM.MY_LOGICAL_Y, t0, tmp_addr=t1)

  fw.signal_subordinate_done(1)
  fw.label("run_loop")

  # wait_subordinate_load_or_go
  wait_sub_loop = fw._new_label("wait_subordinate")
  subordinate_ready = fw._new_label("subordinate_ready")
  fw.li(t0, Mailbox.SUBORDINATE_SYNC)
  fw.label(wait_sub_loop)
  fw.lbu(t1, t0, 0)
  fw.li(t2, RunSync.GO)
  fw.beq(t1, t2, subordinate_ready)
  fw.li(t2, RunSync.LOAD)
  fw.beq(t1, t2, subordinate_ready)
  fw.fence()
  fw.j(wait_sub_loop)
  fw.label(subordinate_ready)
  fw.fence()

  # init_ncrisc_kernel_config
  fw.current_launch_ptr(launch=t0, tmp=t4)
  fw.lw(t1, t0, Launch.KERNEL_CONFIG_BASE)
  for i in range(3):
    fw.lhu(t2, t0, Launch.SEM_OFFSET + 2 * i)
    fw.add(t3, t1, t2)
    fw.write32(NM.SEM_L1_BASE + 4 * i, t3, tmp_addr=t4)
  fw.lhu(t2, t0, Launch.RTA_OFFSET + 4)
  fw.add(t3, t1, t2)
  fw.write32(NM.RTA_L1_BASE_PTR, t3, tmp_addr=t4)
  fw.lhu(t2, t0, Launch.RTA_OFFSET + 6)
  fw.add(t3, t1, t2)
  fw.write32(NM.CRTA_L1_BASE_PTR, t3, tmp_addr=t4)

  # setup_local_cbs
  fw.current_launch_ptr(launch=t0, tmp=t4)
  fw.lw(t1, t0, Launch.KERNEL_CONFIG_BASE)
  fw.lhu(t2, t0, Launch.LOCAL_CB_OFFSET)
  fw.add(t2, t1, t2)
  fw.li(t3, NM.CB_INTERFACE)
  fw.lw(t4, t0, Launch.LOCAL_CB_MASK)
  # setup_local_cbs_from_mask
  fw.li(t0, CB.SYNC_TILES_ACKED_BASE)
  fw.li(t1, CB.SYNC_TILES_RECEIVED_BASE)
  setup_cb_loop = fw._new_label("setup_cb")
  skip_cb = fw._new_label("skip_cb")
  done_cb = fw._new_label("done_cb")
  fw.label(setup_cb_loop)
  fw.beq(t4, zero, done_cb)
  fw.andi(t5, t4, 1)
  fw.beq(t5, zero, skip_cb)
  fw.lw(t5, t2, 4)
  fw.lw(t6, t2, 0)
  fw.sw(t5, t3, 0)
  fw.add(t5, t6, t5)
  fw.sw(t5, t3, 4)
  fw.lw(t5, t2, 12)
  fw.sw(t5, t3, 8)
  fw.lw(t5, t2, 8)
  fw.sw(t5, t3, 12)
  fw.sw(t6, t3, 16)
  fw.sw(t6, t3, 20)
  fw.sw(zero, t3, 24)
  fw.sw(zero, t3, 28)
  fw.sw(zero, t0, 0)
  fw.sw(zero, t1, 0)
  fw.label(skip_cb)
  fw.addi(t2, t2, CB.LOCAL_CONFIG_SIZE)
  fw.addi(t3, t3, CB.LOCAL_INTERFACE_SIZE)
  fw.li(t5, CB.SYNC_STRIDE)
  fw.add(t0, t0, t5)
  fw.add(t1, t1, t5)
  fw.srli(t4, t4, 1)
  fw.j(setup_cb_loop)
  fw.label(done_cb)

  # init_ncrisc_launch_globals
  fw.current_launch_ptr(launch=t0, tmp=t2)
  fw.read8(t1, NM.MY_LOGICAL_X, tmp_addr=t2)
  fw.lbu(t3, t0, Launch.SUB_DEVICE_ORIGIN_X)
  fw.sub(t1, t1, t3)
  fw.write8(NM.MY_RELATIVE_X, t1, tmp_addr=t2)
  fw.read8(t1, NM.MY_LOGICAL_Y, tmp_addr=t2)
  fw.lbu(t3, t0, Launch.SUB_DEVICE_ORIGIN_Y)
  fw.sub(t1, t1, t3)
  fw.write8(NM.MY_RELATIVE_Y, t1, tmp_addr=t2)

  fw.wait8(Mailbox.SUBORDINATE_SYNC, RunSync.GO)
  fw.run_launch_kernel(1)
  fw.signal_subordinate_done(1)
  fw.j("run_loop")
  return fw
