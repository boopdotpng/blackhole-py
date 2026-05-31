from __future__ import annotations

from asm import KernelBase, cond
from dsl import a0, a1, a2, a3, a4, a5, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, t0, t1, t2, t3, t4, t5, t6
from ttk import Cb, Noc
from ttk.mailbox import Firmware, NcriscMailbox as NM
from ttk.noc import NOC


class DramTransferKernel(KernelBase, Noc, Cb):
  def load_args(self):
    return self.read_rta_from(NM.RTA_L1_BASE_PTR, (s0, s1, s2, s3, s4, s5, s6, s7))

  def sysmem_addr(self, tile_id=s9, out_lo=a3, out_mid=a4, tmp=t0):
    self.mul(tmp, tile_id, s6)
    self.add(out_lo, s2, tmp)
    return self.mv(out_mid, s3)

  def dram_addr(self, tile_id=s9):
    self.mv(a0, s0)
    self.mv(a1, tile_id)
    self.mv(a2, s7)
    return self.dram_tile_addr_from(NM.DRAM_BANK_TO_NOC_XY, s7)


def _loop(fw: DramTransferKernel, body):
  fw.load_args()
  fw.li(s8, 0)
  with fw.while_(cond(s8, "<u", s5)):
    fw.add(s9, s4, s8)
    body()
    fw.addi(s8, s8, 1)
  return fw.ret()


def build_fill() -> KernelBase:
  fw = DramTransferKernel(base_addr=Firmware.TEXT_BASE["ncrisc"])

  def body():
    fw.cb_reserve_back(NM.CB_INTERFACE, 0)
    fw.cb_write_ptr(NM.CB_INTERFACE, 0, out=t5)
    fw.sysmem_addr(out_lo=a3, out_mid=a4, tmp=t0)
    fw.local_noc0_coord(a5, x_addr=NM.MY_X, y_addr=NM.MY_Y)

    fw.read32(s10, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
    fw.addi(s10, s10, 1)
    fw.noc_read(1, 1, a3, a4, s1, t5, s6, ret_coord=a5, a=t0, v=t1)
    fw.noc_reads_flushed(1, s10, addr=t0, val=t1)

    fw.dram_addr()
    fw.read32(s10, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
    fw.addi(s10, s10, 1)
    fw.noc_write(1, 0, t5, a0, 0, a2, s6, a=t0, v=t1)
    fw.noc_write_barrier(1, s10, addr=t0, val=t1)

    fw.cb_push_back(NM.CB_INTERFACE, 0)
    fw.cb_wait_front(NM.CB_INTERFACE, 0)
    fw.cb_pop_front(NM.CB_INTERFACE, 0)

  return _loop(fw, body)


def build_drain() -> KernelBase:
  fw = DramTransferKernel(base_addr=Firmware.TEXT_BASE["ncrisc"])

  def body():
    fw.cb_reserve_back(NM.CB_INTERFACE, 0)
    fw.cb_write_ptr(NM.CB_INTERFACE, 0, out=t5)
    fw.dram_addr()
    fw.local_noc0_coord(a5, x_addr=NM.MY_X, y_addr=NM.MY_Y)

    fw.read32(s10, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
    fw.addi(s10, s10, 1)
    fw.noc_read(1, 1, a0, 0, a2, t5, s6, ret_coord=a5, a=t0, v=t1)
    fw.noc_reads_flushed(1, s10, addr=t0, val=t1)

    fw.sysmem_addr(out_lo=a3, out_mid=a4, tmp=t0)
    fw.read32(s10, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (1 << NOC.INSTANCE_OFFSET_BIT), tmp_addr=t0)
    fw.addi(s10, s10, 1)
    fw.noc_write(1, 0, t5, a3, a4, s1, s6, a=t0, v=t1)
    fw.noc_write_barrier(1, s10, addr=t0, val=t1)

    fw.cb_push_back(NM.CB_INTERFACE, 0)
    fw.cb_wait_front(NM.CB_INTERFACE, 0)
    fw.cb_pop_front(NM.CB_INTERFACE, 0)

  return _loop(fw, body)
