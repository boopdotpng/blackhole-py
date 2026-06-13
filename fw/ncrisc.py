from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Kernel, KernelBase
from dsl import t0, t1, t2, t3, t4
from ttk import Cb, Noc
from ttk.mailbox import Firmware, NcriscMailbox as NM
from ttk.tensix import Launch, Mailbox, RunSync

def build() -> KernelBase:
  fw = Kernel(Noc, Cb, base_addr=Firmware.TEXT_BASE["ncrisc"])
  fw.segment(Firmware.LOCAL_DATA_BASE["ncrisc"], b"\x68".ljust(Firmware.LOCAL_DATA_SIZE["ncrisc"], b"\0"), label="local_data")
  fw.setup_stack(Firmware.NCRISC_STACK_TOP)
  fw.configure_csr()
  # init_risc_noc_coords
  fw.init_risc_noc_coords(NM.MY_X, NM.MY_Y)

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
  fw.setup_local_cbs(NM.CB_INTERFACE)

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
