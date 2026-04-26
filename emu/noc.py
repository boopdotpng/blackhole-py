from __future__ import annotations

import math
import struct

from .memory import (
  Memory, NOC0_BASE, NOC1_BASE, NIU_CMD_BUF_STRIDE, NIU_TARG_ADDR_LO,
  NIU_TARG_ADDR_MID, NIU_TARG_ADDR_HI, NIU_RET_ADDR_LO, NIU_RET_ADDR_MID,
  NIU_RET_ADDR_HI, NIU_CTRL, NIU_AT_LEN_BE, NIU_AT_DATA, NIU_CMD_CTRL,
  NIU_NODE_ID, NIU_ID_LOGICAL, NIU_CMD_BUF_AVAIL, NIU_L1_ACC_AT_INSTRN,
  NIU_MST_ATOMIC_RESP_RECEIVED, NIU_MST_WR_ACK_RECEIVED,
  NIU_MST_RD_RESP_RECEIVED, NIU_MST_NONPOSTED_WR_REQ_SENT,
  NIU_MST_POSTED_WR_REQ_SENT, NIU_MST_RD_REQ_SENT, NOC_CTRL_AT, NOC_CTRL_WR,
  NOC_CTRL_WR_INLINE, NOC_CTRL_RESP_MARKED, NOC_CTRL_BRCST,
  NOC_CTRL_BRCST_SRC_INCLUDE, NOC_CTRL_L1_ACC_AT_EN,
)
from .sim import Simulator

M32 = 0xFFFFFFFF


def noc_key(x, y):
  return (y << 6) | x


class StreamRegisters(Memory):
  pass


class TimedNOC:
  """Small timed NIU model.

  Register programming is synchronous. Writing CMD_CTRL=1 snapshots the command and
  schedules the data movement/counter update for a later simulator cycle.
  """

  def __init__(self, noc_id: int, l1: Memory, network: dict[int, Memory],
               x: int, y: int, sim: Simulator):
    self.noc_id = noc_id
    self.base = NOC0_BASE if noc_id == 0 else NOC1_BASE
    self.regs = Memory()
    self.l1 = l1
    self.network = network
    self.x = x
    self.y = y
    self.sim = sim

  def pre_populate(self):
    xy = noc_key(self.x, self.y)
    self.regs.write32(NIU_ID_LOGICAL, xy)
    for buf in range(4):
      self.regs.write32(buf * NIU_CMD_BUF_STRIDE + NIU_NODE_ID, xy)
    self.regs.write32(NIU_CMD_BUF_AVAIL, 0x1F1F1F1F)

  def read8(self, addr): return self.regs.read8(addr - self.base)
  def read16(self, addr): return self.regs.read16(addr - self.base)
  def read32(self, addr): return self.regs.read32(addr - self.base)
  def write8(self, addr, val): self.regs.write8(addr - self.base, val)
  def write16(self, addr, val): self.regs.write16(addr - self.base, val)

  def write32(self, addr, val):
    off = addr - self.base
    self.regs.write32(off, val)
    if (off & 0x7FF) == NIU_CMD_CTRL and val == 1:
      self._schedule(off >> 11)

  def _reg(self, buf, off):
    return self.regs.read32(buf * NIU_CMD_BUF_STRIDE + off)

  def _inc(self, off, n=1):
    self.regs.write32(off, (self.regs.read32(off) + n) & M32)

  @staticmethod
  def _xy(raw):
    return raw & 0x3F, (raw >> 6) & 0x3F

  @staticmethod
  def _rect(raw):
    return ((raw >> 12) & 0x3F, (raw >> 18) & 0x3F,
            raw & 0x3F, (raw >> 6) & 0x3F)

  def _targets(self, raw, is_mcast, include_src):
    if not is_mcast:
      return [self._xy(raw)]
    sx, sy, ex, ey = self._rect(raw)
    return [
      (x, y)
      for y in range(sy, ey + 1)
      for x in range(sx, ex + 1)
      if include_src or x != self.x or y != self.y
    ]

  def _mem(self, x, y):
    return self.network[noc_key(x, y)]

  def _read(self, x, y, addr, n):
    mem = self._mem(x, y)
    return bytes(mem.read8(addr + i) for i in range(n))

  def _write(self, x, y, addr, data):
    mem = self._mem(x, y)
    for i, b in enumerate(data):
      mem.write8(addr + i, b)

  def _schedule(self, buf):
    tx = _Tx.from_noc(self, buf)
    self.sim.schedule(self.sim.cycle + self._latency(tx),
                      lambda _ctx: self._complete(tx),
                      f"noc{self.noc_id}:buf{buf}")

  def _latency(self, tx: "_Tx") -> int:
    coords = tx.targets or [self._xy(tx.targ_xy)]
    farthest = max(abs(self.x - x) + abs(self.y - y) for x, y in coords)
    byte_count = 4 if tx.is_at or tx.inline else tx.length
    payload = max(1, math.ceil(max(byte_count, 1) / 64))
    return 10 + 18 * farthest + payload

  def _complete(self, tx: "_Tx"):
    self.regs.write32(tx.buf * NIU_CMD_BUF_STRIDE + NIU_CMD_CTRL, 0)
    if tx.is_at:
      self._complete_atomic(tx)
    elif tx.is_wr:
      self._complete_write(tx)
    else:
      self._complete_read(tx)

  def _complete_read(self, tx: "_Tx"):
    sx, sy = self._xy(tx.targ_xy)
    data = self._read(sx, sy, tx.targ_addr, tx.length)
    for i, b in enumerate(data):
      self.l1.write8(tx.ret_addr + i, b)
    self._inc(NIU_MST_RD_RESP_RECEIVED)
    self._inc(NIU_MST_RD_REQ_SENT)

  def _complete_write(self, tx: "_Tx"):
    data = struct.pack("<I", tx.at_data) if tx.inline else bytes(
      self.l1.read8(tx.targ_addr + i) for i in range(tx.length)
    )
    for x, y in tx.targets:
      self._write(x, y, tx.ret_addr, data)
    if tx.is_resp:
      self._inc(NIU_MST_WR_ACK_RECEIVED, len(tx.targets))
      self._inc(NIU_MST_NONPOSTED_WR_REQ_SENT)
    else:
      self._inc(NIU_MST_POSTED_WR_REQ_SENT)

  def _complete_atomic(self, tx: "_Tx"):
    for x, y in tx.targets:
      mem = self._mem(x, y)
      old = mem.read32(tx.targ_addr)
      opcode = ((tx.l1_acc_instrn >> 12) & 0xF) if tx.l1_acc else ((tx.length >> 12) & 0xF)
      match opcode:
        case 0x1:  # INCR_GET
          mem.write32(tx.targ_addr, (old + tx.at_data) & M32)
        case 0x2:  # INCR_GET_PTR
          incr = (tx.length >> 6) & 0xF or 1
          wrap = (tx.length >> 2) & 0xF
          new = old + incr
          mem.write32(tx.targ_addr, 0 if wrap and new >= wrap else new & M32)
        case 0x3:  # SWAP halfword lanes in 16B block
          base = tx.targ_addr & ~0xF
          mask = (tx.length >> 4) & 0xFF
          for lane in range(8):
            if (mask >> lane) & 1:
              mem.write16(base + lane * 2, (tx.at_data >> ((lane & 1) * 16)) & 0xFFFF)
        case 0x4:  # CAS low 16b
          if (old & 0xFFFF) == (tx.at_data & 0xFFFF):
            mem.write32(tx.targ_addr, (old & 0xFFFF0000) | ((tx.at_data >> 16) & 0xFFFF))
        case 0x6:  # STORE_IND
          mem.write32(old, tx.at_data & M32)
        case 0x7:  # SWAP_4B
          mem.write32(tx.targ_addr, tx.at_data & M32)
        case _:
          pass
      if tx.is_resp:
        self.l1.write32(tx.ret_addr, old)
        self._inc(NIU_MST_ATOMIC_RESP_RECEIVED)


class _Tx:
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

  @classmethod
  def from_noc(cls, noc: TimedNOC, buf: int):
    ctrl = noc._reg(buf, NIU_CTRL)
    targ_addr = noc._reg(buf, NIU_TARG_ADDR_LO) | ((noc._reg(buf, NIU_TARG_ADDR_MID) & 0xF) << 32)
    ret_addr = noc._reg(buf, NIU_RET_ADDR_LO) | ((noc._reg(buf, NIU_RET_ADDR_MID) & 0xF) << 32)
    is_mcast = bool(ctrl & NOC_CTRL_BRCST)
    include_src = bool(ctrl & NOC_CTRL_BRCST_SRC_INCLUDE)
    target_xy = noc._reg(buf, NIU_TARG_ADDR_HI)
    ret_xy = noc._reg(buf, NIU_RET_ADDR_HI)
    is_wr = bool(ctrl & NOC_CTRL_WR)
    xy_for_targets = target_xy if bool(ctrl & NOC_CTRL_AT) or bool(ctrl & NOC_CTRL_WR_INLINE) else ret_xy
    targets = noc._targets(xy_for_targets, is_mcast, include_src)
    return cls(
      buf=buf,
      ctrl=ctrl,
      targ_xy=target_xy,
      ret_xy=ret_xy,
      targ_addr=targ_addr,
      ret_addr=ret_addr,
      length=noc._reg(buf, NIU_AT_LEN_BE),
      at_data=noc._reg(buf, NIU_AT_DATA),
      l1_acc_instrn=noc._reg(buf, NIU_L1_ACC_AT_INSTRN),
      l1_acc=bool(ctrl & NOC_CTRL_L1_ACC_AT_EN),
      is_at=bool(ctrl & NOC_CTRL_AT),
      is_wr=is_wr,
      inline=bool(ctrl & NOC_CTRL_WR_INLINE),
      is_resp=bool(ctrl & NOC_CTRL_RESP_MARKED),
      targets=targets,
    )
