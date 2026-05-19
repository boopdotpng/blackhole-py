from __future__ import annotations

from collections.abc import Iterable

from dsl import Reg, t0, t1, t2, t3, t4, t5, zero
from ttk.addrs import NOC, TensixMMIO

class NocMixin:
  def write_reg(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    return self.write32(addr, value, tmp_addr=tmp_addr, tmp_val=tmp_val)

  def read_reg(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    return self.read32(dst, addr, tmp_addr=tmp_addr)

  def noc_write_reg(self, addr: int | Reg, value: int | Reg, *, tmp_addr: Reg = t0, tmp_val: Reg = t1):
    return self.write_reg(addr, value, tmp_addr=tmp_addr, tmp_val=tmp_val)

  def noc_read_reg(self, dst: Reg, addr: int | Reg, *, tmp_addr: Reg = t0):
    return self.read_reg(dst, addr, tmp_addr=tmp_addr)

  def noc_set_active_instance(self, noc: int):
    self.active_noc = noc
    return self

  def set_subordinate_reset_pcs(self, *, ncrisc: int, trisc0: int, trisc1: int, trisc2: int):
    self.write_reg(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC, ncrisc)
    self.write_reg(TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC, trisc0)
    self.write_reg(TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC, trisc1)
    self.write_reg(TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC, trisc2)
    self.write_reg(TensixMMIO.RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE, 0b111)
    self.write_reg(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE, 1)
    return self

  def deassert_all_riscs(self):
    return self.write_reg(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_NONE)

  def noc_cmd_addr(self, noc: int, buf: int, reg: int) -> int:
    return reg + (buf << NOC.CMD_BUF_OFFSET_BIT) + (noc << NOC.INSTANCE_OFFSET_BIT)

  def noc_cmd_reg(self, noc: int, buf: int, reg: int, value: int | Reg, *, addr: Reg = t0, tmp: Reg = t1):
    return self.write32(self.noc_cmd_addr(noc, buf, reg), value, tmp_addr=addr, tmp_val=tmp)

  def noc_init_cmd_bufs(self, noc: int, coord: Reg, *, atomic_ret_addr: int,
                        read_ctrl: int, wr_buf: int = 0, rd_buf: int = 1,
                        wr_reg_buf: int = 2, at_buf: int = 3,
                        tmp_addr: Reg = t0, tmp_val: Reg = t1):
    self.noc_cmd_reg(noc, wr_buf, NOC.TARG_ADDR_MID, 0, addr=tmp_addr, tmp=tmp_val)
    self.noc_cmd_reg(noc, wr_buf, NOC.TARG_ADDR_COORDINATE, coord, addr=tmp_addr, tmp=tmp_val)
    self.noc_cmd_reg(noc, wr_reg_buf, NOC.TARG_ADDR_MID, 0, addr=tmp_addr, tmp=tmp_val)
    self.noc_cmd_reg(noc, wr_reg_buf, NOC.TARG_ADDR_COORDINATE, coord, addr=tmp_addr, tmp=tmp_val)
    self.noc_cmd_reg(noc, at_buf, NOC.RET_ADDR_LO, atomic_ret_addr, addr=tmp_addr, tmp=tmp_val)
    self.noc_cmd_reg(noc, at_buf, NOC.RET_ADDR_MID, 0, addr=tmp_addr, tmp=tmp_val)
    self.noc_cmd_reg(noc, at_buf, NOC.RET_ADDR_COORDINATE, coord, addr=tmp_addr, tmp=tmp_val)
    self.noc_cmd_reg(noc, rd_buf, NOC.CTRL, read_ctrl, addr=tmp_addr, tmp=tmp_val)
    self.noc_cmd_reg(noc, rd_buf, NOC.RET_ADDR_MID, 0, addr=tmp_addr, tmp=tmp_val)
    self.noc_cmd_reg(noc, rd_buf, NOC.RET_ADDR_COORDINATE, coord, addr=tmp_addr, tmp=tmp_val)
    return self

  def noc_snapshot_status_counters(self, noc_id: Reg, noc_shift: Reg,
                                   counters: Iterable[tuple[int, int]], *,
                                   status: Reg = t2, dest: Reg = t3,
                                   value: Reg = t4, offset: Reg = t5):
    for counter, local_base in counters:
      self.li(status, NOC.STATUS_BASE + counter * 4)
      self.add(status, status, noc_shift)
      self.lw(value, status, 0)
      self.slli(offset, noc_id, 2)
      self.li(dest, local_base)
      self.add(dest, dest, offset)
      self.write32(dest, value)
    return self

  def noc_wait_cmd_ready(self, noc: int, buf: int, *, addr: Reg = t0, val: Reg = t1):
    self.li(addr, self.noc_cmd_addr(noc, buf, NOC.CMD_CTRL))
    loop = self._new_label("noc_ready")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bne(val, zero, loop)
    return self

  def noc_wait_write_acks(self, noc: int, target: Reg, *, addr: Reg = t0, val: Reg = t1):
    self.li(addr, NOC.STATUS_BASE + NOC.NIU_MST_WR_ACK_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT))
    loop = self._new_label("wr_ack")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bltu(val, target, loop)
    return self

  def noc_write_barrier(self, noc: int, target: Reg, *, addr: Reg = t0, val: Reg = t1):
    self.noc_wait_write_acks(noc, target, addr=addr, val=val)
    return self.fence()

  def noc_read(self, noc: int, buf: int, src_lo: Reg, src_mid: int | Reg, src_coord: int | Reg,
               dst: Reg, length: Reg, *, ret_coord: int | Reg = 0, a: Reg = t0, v: Reg = t1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_RD_FIELD, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, dst, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, ret_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, src_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, src_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, src_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self

  def noc_write(self, noc: int, buf: int, src: Reg, dst_lo: Reg, dst_mid: int | Reg, dst_coord: Reg,
                length: Reg, *, mcast: bool = False, mcast_linked: bool = False,
                num_dests: Reg | None = None, posted: bool = False, a: Reg = t0, v: Reg = t1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    if mcast:
      ctrl = NOC.CMD_WR_MCAST_LINKED_FIELD if mcast_linked else NOC.CMD_WR_MCAST_UNLINK_FIELD
    else:
      ctrl = NOC.CMD_WR_POSTED_FIELD if posted else NOC.CMD_WR_FIELD
    self.noc_cmd_reg(noc, buf, NOC.CTRL, ctrl, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, src, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, dst_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, length, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self

  def noc_inline_write(self, noc: int, buf: int, value: Reg, dst_lo: Reg,
                       dst_mid: int | Reg, dst_coord: Reg, *, a: Reg = t0, v: Reg = t1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_DATA, value, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_INLINE_FIELD, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, dst_mid, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, 0xF, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self

  def noc_wait_atomic_responses(self, noc: int, target: Reg, *, addr: Reg = t0, val: Reg = t1):
    self.li(addr, NOC.STATUS_BASE + NOC.NIU_MST_ATOMIC_RESP_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT))
    loop = self._new_label("atomic_resp")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bltu(val, target, loop)
    return self

  def noc_atomic_inc(self, noc: int, buf: int, dst_lo: Reg, dst_coord: int | Reg,
                     incr: Reg | int, ret_coord: int, *, a: Reg = t0, v: Reg = t1):
    self.noc_wait_cmd_ready(noc, buf, addr=a, val=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_LO, 4, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.RET_ADDR_COORDINATE, ret_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_LO, dst_lo, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_MID, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.TARG_ADDR_COORDINATE, dst_coord, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CTRL, NOC.CMD_AT_INC_FIELD, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE, NOC.AT_INCR_GET, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_LEN_BE_1, 0, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.AT_DATA, incr, addr=a, tmp=v)
    self.noc_cmd_reg(noc, buf, NOC.CMD_CTRL, NOC.CTRL_SEND_REQ, addr=a, tmp=v)
    return self
