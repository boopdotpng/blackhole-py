from __future__ import annotations

from collections.abc import Iterable

from dsl import Reg, a0, a1, a2, a5, t0, t1, t2, t3, t4, t5, t6, zero
from ttk.addrs import L1_ALIGN, P100BankTable, noc_xy
from ttk.mailbox import BriscMailbox as BM
from ttk.tensix import TensixL1, TensixMMIO


class NOC:
  REGS_START_ADDR = 0xFFB20000
  STATUS_BASE = 0xFFB20200
  CMD_BUF_OFFSET_BIT = 11
  INSTANCE_OFFSET_BIT = 16
  CFG_BASE = REGS_START_ADDR + 0x100

  TARG_ADDR_LO = REGS_START_ADDR + 0x00
  TARG_ADDR_MID = REGS_START_ADDR + 0x04
  TARG_ADDR_COORDINATE = REGS_START_ADDR + 0x08
  RET_ADDR_LO = REGS_START_ADDR + 0x0C
  RET_ADDR_MID = REGS_START_ADDR + 0x10
  RET_ADDR_COORDINATE = REGS_START_ADDR + 0x14
  CTRL = REGS_START_ADDR + 0x1C
  AT_LEN_BE = REGS_START_ADDR + 0x20
  AT_LEN_BE_1 = REGS_START_ADDR + 0x24
  AT_DATA = REGS_START_ADDR + 0x28
  CMD_CTRL = REGS_START_ADDR + 0x40

  CTRL_SEND_REQ = 1
  PCIE_MID = 0x10000000
  COORD_MASK = 0xFFFFFF

  CMD_CPY = 0
  CMD_AT = 1
  CMD_WR = 1 << 1
  CMD_WR_INLINE = 1 << 3
  CMD_RESP_MARKED = 1 << 4
  CMD_BRCST_PACKET = 1 << 5
  CMD_VC_LINKED = 1 << 6
  CMD_VC_STATIC = 1 << 7
  CMD_PATH_RESERVE = 1 << 8
  CMD_STATIC_VC_1 = 1 << 13
  CMD_STATIC_VC_5 = 5 << 13

  CMD_RD_FIELD = CMD_CPY | CMD_RESP_MARKED | CMD_VC_STATIC | CMD_STATIC_VC_1
  CMD_WR_FIELD = CMD_CPY | CMD_WR | CMD_RESP_MARKED | CMD_VC_STATIC | CMD_STATIC_VC_1
  CMD_WR_POSTED_FIELD = CMD_CPY | CMD_WR | CMD_VC_STATIC | CMD_STATIC_VC_1
  CMD_WR_MCAST_UNLINK_FIELD = (
    CMD_CPY | CMD_WR | CMD_RESP_MARKED | CMD_VC_STATIC |
    CMD_STATIC_VC_5 | CMD_BRCST_PACKET | CMD_PATH_RESERVE
  )
  CMD_WR_MCAST_LINKED_FIELD = CMD_WR_MCAST_UNLINK_FIELD | CMD_VC_LINKED
  CMD_INLINE_FIELD = CMD_WR_FIELD | CMD_WR_INLINE
  CMD_AT_INC_FIELD = CMD_AT | CMD_RESP_MARKED | CMD_VC_STATIC | CMD_STATIC_VC_1

  AT_INS_INCR_GET = 0x1
  AT_INS_SHIFT = 12
  AT_WRAP_SHIFT = 2
  AT_INCR_GET = (AT_INS_INCR_GET << AT_INS_SHIFT) | (31 << AT_WRAP_SHIFT)

  MAX_BURST_SIZE = 16 * 1024

  NIU_MST_ATOMIC_RESP_RECEIVED = 0x00
  NIU_MST_WR_ACK_RECEIVED = 0x04
  NIU_MST_RD_RESP_RECEIVED = 0x08
  NIU_MST_NONPOSTED_WR_REQ_SENT = 0x28
  NIU_MST_POSTED_WR_REQ_SENT = 0x2C


class NocCfg:
  NIU_CFG_0 = 0x0
  ROUTER_CFG_0 = 0x1
  ID_LOGICAL = 0x12
  NODE_ID_MASK = 0x3F
  ADDR_NODE_ID_BITS = 6
  ADDR_COORD_SHIFT = 36
  COORDINATE_MASK = 0xFFFFFF
  PCIE_MASK = 0x1000000F
  INLINE_WRITE_POSTED_FIELD = (1 << 7) | (1 << 13) | (1 << 1) | (1 << 3)
  STREAM_REG_SPACE_SIZE = 0x1000
  MEM_NOC_ATOMIC_RET_VAL_ADDR = 0x04
  NCRISC_WR_CMD_BUF = 0
  NCRISC_RD_CMD_BUF = 1
  NCRISC_WR_REG_CMD_BUF = 2
  NCRISC_AT_CMD_BUF = 3
  RD_CMD_FIELD = (1 << 4) | (1 << 7) | (1 << 13)
  NIU_MST_ATOMIC_RESP_RECEIVED_WORD = 0x0
  NIU_MST_WR_ACK_RECEIVED_WORD = 0x1
  NIU_MST_RD_RESP_RECEIVED_WORD = 0x2
  NIU_MST_NONPOSTED_WR_REQ_SENT_WORD = 0xA
  NIU_MST_POSTED_WR_REQ_SENT_WORD = 0xB

class Noc:
  def init_risc_noc_coords(self, my_x_addr: int, my_y_addr: int, *,
                           id_reg: Reg = t0, coord: Reg = t1, tmp_addr: Reg = t2):
    # Read each NOC's logical node id and stash MY_X/MY_Y into the mailbox.
    for noc in range(2):
      self.read32(id_reg, self.noc_cmd_addr(noc, 0, NOC.CFG_BASE + NocCfg.ID_LOGICAL * 4), tmp_addr=tmp_addr)
      self.andi(coord, id_reg, NocCfg.NODE_ID_MASK)
      self.write8(my_x_addr + noc, coord, tmp_addr=tmp_addr)
      self.srli(coord, id_reg, NocCfg.ADDR_NODE_ID_BITS)
      self.andi(coord, coord, NocCfg.NODE_ID_MASK)
      self.write8(my_y_addr + noc, coord, tmp_addr=tmp_addr)
    return self

  def init_bank_tables(self, dram_bank_to_noc_xy: int):
    # Copy the DRAM/L1 bank->NOC translation tables from the fw scratch region.
    return self.copy_words(
      dram_bank_to_noc_xy,
      TensixL1.MEM_BANK_TO_NOC_SCRATCH,
      P100BankTable.TOTAL_SIZE,
    )

  def noc_coord(self, out: Reg, x: int | Reg, y: int | Reg, *, tmp: Reg = t0):
    if isinstance(x, int) and isinstance(y, int):
      return self.li(out, noc_xy(x, y))
    if isinstance(y, int):
      self.li(out, y)
    else:
      self.mv(out, y)
    self.slli(out, out, 6)
    if isinstance(x, int):
      self.li(tmp, x)
      return self.or_(out, out, tmp)
    return self.or_(out, out, x)

  def noc_mcast_coord(self, out: Reg, x_start: int | Reg, y_start: int | Reg,
                      x_end: int | Reg, y_end: int | Reg, *, tmp: Reg = t0,
                      reverse: bool = False):
    if reverse:
      x_start, x_end = x_end, x_start
      y_start, y_end = y_end, y_start
    self.noc_coord(out, x_end, y_end, tmp=tmp)
    if isinstance(x_start, int) and isinstance(y_start, int):
      self.li(tmp, noc_xy(x_start, y_start))
    else:
      self.noc_coord(tmp, x_start, y_start)
    self.slli(tmp, tmp, 12)
    return self.or_(out, out, tmp)

  def sem_addr(self, sem_l1_base: int, sem_id: int | Reg, *, out: Reg = t6, tmp: Reg = t0):
    if isinstance(sem_id, int):
      self.read32(out, sem_l1_base, tmp_addr=tmp)
      return self.addi(out, out, sem_id * L1_ALIGN)
    off = tmp
    if int(off) == int(sem_id):
      off = t5 if int(sem_id) != int(t5) and int(out) != int(t5) else t4
    self.slli(off, sem_id, 4)
    self.read32(out, sem_l1_base, tmp_addr=out)
    return self.add(out, out, off)

  def noc_semaphore_set(self, sem_addr: Reg, value: int | Reg, *, tmp: Reg = t0):
    if isinstance(value, int):
      self.li(tmp, value)
      value = tmp
    self.sw(value, sem_addr, 0)
    return self.fence()

  def noc_semaphore_wait(self, sem_addr: Reg, value: int | Reg, *, actual: Reg = t0, expected: Reg = t1):
    if isinstance(value, int):
      self.li(expected, value)
      value = expected
    loop = self._new_label("noc_sem_wait")
    done = self._new_label("noc_sem_done")
    self.label(loop)
    self.fence()
    self.lw(actual, sem_addr, 0)
    self.beq(actual, value, done)
    self.j(loop)
    self.label(done)
    return self.fence()

  def local_noc0_coord(self, out: Reg = a5, *, x_addr: int = BM.MY_X, y_addr: int = BM.MY_Y):
    self.read8(t0, x_addr, tmp_addr=t2)
    self.read8(t1, y_addr, tmp_addr=t2)
    self.slli(t1, t1, 6)
    return self.or_(out, t0, t1)

  def local_noc_coord(self, noc: int, out: Reg = a5, *, x_addr: int = BM.MY_X, y_addr: int = BM.MY_Y):
    return self.local_noc0_coord(out, x_addr=x_addr + noc, y_addr=y_addr + noc)

  def dram_tile_addr_from(self, table_base: int, noc_table_offset: int | Reg = 0):
    self.mv(t0, a1)
    self.remu(a1, t0, a2)
    self.divu(t0, t0, a2)
    self.slli(t0, t0, 11)
    self.add(a0, a0, t0)
    if isinstance(noc_table_offset, int):
      self.addi(t1, a1, noc_table_offset)
    else:
      self.add(t1, a1, noc_table_offset)
    self.slli(t1, t1, 1)
    self.li(t2, table_base)
    self.add(t2, t2, t1)
    return self.lhu(a2, t2, 0)

  def dram_tile_addr_static(self, bank_coords: list[int]):
    self.mv(t0, a1)
    self.remu(a1, t0, a2)
    self.divu(t0, t0, a2)
    self.slli(t0, t0, 11)
    self.add(a0, a0, t0)
    self.li(a2, bank_coords[0])
    for bank, coord in enumerate(bank_coords[1:], start=1):
      next_bank = self._new_label("dram_static_bank")
      self.li(t1, bank)
      self.bne(a1, t1, next_bank)
      self.li(a2, coord)
      self.label(next_bank)
    return self

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

  def noc_reads_flushed(self, noc: int, target: Reg, *, addr: Reg = t0, val: Reg = t1):
    self.li(addr, NOC.STATUS_BASE + NOC.NIU_MST_RD_RESP_RECEIVED + (noc << NOC.INSTANCE_OFFSET_BIT))
    loop = self._new_label("rd_flush")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bltu(val, target, loop)
    return self.fence()

  def noc_nonposted_writes_flushed(self, noc: int, target: Reg, *, addr: Reg = t0, val: Reg = t1):
    self.li(addr, NOC.STATUS_BASE + NOC.NIU_MST_NONPOSTED_WR_REQ_SENT + (noc << NOC.INSTANCE_OFFSET_BIT))
    loop = self._new_label("np_wr_flush")
    self.label(loop)
    self.lw(val, addr, 0)
    self.bltu(val, target, loop)
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
                     incr: Reg | int, ret_coord: int | Reg, *, a: Reg = t0, v: Reg = t1):
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

  def noc_semaphore_inc(self, noc: int, buf: int, sem_addr: Reg, sem_coord: int | Reg,
                        incr: int | Reg = 1, *, ret_coord: int | Reg = 0, a: Reg = t0, v: Reg = t1):
    return self.noc_atomic_inc(noc, buf, sem_addr, sem_coord, incr, ret_coord, a=a, v=v)

  def noc_semaphore_set_multicast(self, noc: int, buf: int, sem_addr: Reg, sem_coord: Reg,
                                  value: int | Reg, num_dests: int | Reg, *,
                                  a: Reg = t0, v: Reg = t1):
    if not isinstance(value, int):
      self.sw(value, sem_addr, 0)
    else:
      self.li(v, value)
      self.sw(v, sem_addr, 0)
    length = t5 if int(v) == int(t2) else t2
    self.li(length, L1_ALIGN)
    self.noc_write(noc, buf, sem_addr, sem_addr, 0, sem_coord, length, mcast=True, a=a, v=v)
    return self
