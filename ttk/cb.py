from __future__ import annotations

from dsl import Reg, t0, t1, t2, t3, t4, t5, t6, zero
from dsl import TTSETDMAREG, TTSTALLWAIT, TTSTOREREG
from ttk.addrs import CircularBuffer as CB
from ttk.tensix import TensixRegs

class Cb:
  def cb_iface(self, interface_base: int, cb_index: int, *, out: Reg = t6):
    return self.li(out, interface_base + cb_index * CB.LOCAL_INTERFACE_SIZE)

  def cb_counter_low(self, out: Reg, counter_reg: Reg):
    self.slli(out, counter_reg, 16)
    return self.srli(out, out, 16)

  def cb_counter_high(self, out: Reg, counter_reg: Reg):
    return self.srli(out, counter_reg, 16)

  def cb_reserve_back(self, interface_base: int, cb_index: int):
    iface, received, acked, free_pages, num_pages = t6, t5, t4, t3, t2
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(received, iface, 24)
    self.cb_counter_high(received, received)
    loop = self._new_label("cb_reserve")
    done = self._new_label("cb_reserve_done")
    self.label(loop)
    self.li(acked, CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE)
    self.lhu(acked, acked, 0)
    self.sub(free_pages, received, acked)
    self.lw(num_pages, iface, 12)
    self.sub(free_pages, num_pages, free_pages)
    self.li(num_pages, 1)
    self.bge(free_pages, num_pages, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  def cb_push_back(self, interface_base: int, cb_index: int):
    iface, ptr, tmp, counter, acked, received = t6, t5, t4, t3, t2, t1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(ptr, iface, 20)
    self.lw(tmp, iface, 8)
    self.add(ptr, ptr, tmp)
    self.lw(tmp, iface, 4)
    no_wrap = self._new_label("cb_push_no_wrap")
    self.bltu(ptr, tmp, no_wrap)
    self.lw(tmp, iface, 0)
    self.sub(ptr, ptr, tmp)
    self.label(no_wrap)
    self.sw(ptr, iface, 20)

    self.lw(counter, iface, 24)
    self.cb_counter_low(acked, counter)
    self.cb_counter_high(received, counter)
    self.addi(received, received, 1)
    self.slli(received, received, 16)
    self.or_(counter, received, acked)
    self.sw(counter, iface, 24)
    self.srli(received, received, 16)
    self.li(tmp, CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE)
    self.sw(received, tmp, 0)
    return self.fence()

  def cb_wait_front(self, interface_base: int, cb_index: int):
    iface, counter, acked, received, available, need = t6, t5, t4, t3, t2, t1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(counter, iface, 24)
    self.cb_counter_low(acked, counter)
    loop = self._new_label("cb_wait_front")
    done = self._new_label("cb_wait_front_done")
    self.label(loop)
    self.li(received, CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE)
    self.lhu(received, received, 0)
    self.sub(available, received, acked)
    self.li(need, 1)
    self.bgeu(available, need, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  def cb_pop_front(self, interface_base: int, cb_index: int, *, tensix_ack: bool = False):
    iface, ptr, tmp, counter, acked, received = t6, t5, t4, t3, t2, t1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(counter, iface, 24)
    self.cb_counter_low(acked, counter)
    self.cb_counter_high(received, counter)
    self.addi(acked, acked, 1)
    self.cb_counter_low(acked, acked)
    self.slli(received, received, 16)
    self.or_(counter, received, acked)
    self.sw(counter, iface, 24)
    self.li(tmp, CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE)
    self.sw(acked, tmp, 0)
    if tensix_ack:
      self.slli(tmp, acked, 8)
      self.li(ptr, TTSETDMAREG(0, 0, 0, 8).raw_word())
      self.add(tmp, tmp, ptr)
      self.write32(TensixRegs.INSTRN_BUF_BASE, tmp, tmp_addr=ptr, tmp_val=t0)
      self.emit(TTSTALLWAIT(32, 6))
      self.push_tensix(
        TTSTOREREG(4, ((CB.SYNC_TILES_ACKED_BASE + cb_index * CB.SYNC_STRIDE) >> 2) & 0x3FFFF),
      )

    self.lw(ptr, iface, 16)
    self.lw(tmp, iface, 8)
    self.add(ptr, ptr, tmp)
    self.lw(tmp, iface, 4)
    no_wrap = self._new_label("cb_pop_no_wrap")
    self.bltu(ptr, tmp, no_wrap)
    self.lw(tmp, iface, 0)
    self.sub(ptr, ptr, tmp)
    self.label(no_wrap)
    self.sw(ptr, iface, 16)
    return self.fence()

  def cb_write_ptr(self, interface_base: int, cb_index: int, *, out: Reg = t5, shift_to_bytes: bool = False):
    self.cb_iface(interface_base, cb_index, out=t6)
    self.lw(out, t6, 20)
    if shift_to_bytes:
      self.slli(out, out, 4)
    return self

  def cb_read_ptr(self, interface_base: int, cb_index: int, *, out: Reg = t5, shift_to_bytes: bool = False):
    self.cb_iface(interface_base, cb_index, out=t6)
    self.lw(out, t6, 16)
    if shift_to_bytes:
      self.slli(out, out, 4)
    return self

  def clear_cb_sync_registers(self, tiles_received_base: int, tiles_acked_base: int, count: int = 64,
                              *, ptr: Reg = t0, remaining: Reg = t1):
    from asm import cond

    self.li(ptr, tiles_received_base)
    self.li(remaining, count)
    with self.loop():
      self.break_(cond(remaining, "==", zero))
      self.sw(zero, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(remaining, remaining, -1)

    self.li(ptr, tiles_acked_base)
    self.li(remaining, count)
    with self.loop():
      self.break_(cond(remaining, "==", zero))
      self.sw(zero, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(remaining, remaining, -1)
    return self
