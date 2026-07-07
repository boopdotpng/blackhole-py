from __future__ import annotations

from dsl import Reg, t0, t1, t2, t3, t4, t5, t6, zero
from dsl import TTSETDMAREG, TTSTALLWAIT, TTSTOREREG
from asm import with_scope
from ttk.tensix import Launch, TensixRegs


class CircularBuffer:
  LOCAL_INTERFACE_SIZE = 32
  LOCAL_CONFIG_SIZE = 16
  SYNC_TILES_ACKED_BASE = 0xFFB48020
  SYNC_TILES_RECEIVED_BASE = 0xFFB48028
  SYNC_STRIDE = 0x1000
  NUM_CIRCULAR_BUFFERS = 32


CB = CircularBuffer

class Cb:
  def _load_count(self, count: int | Reg, out: Reg):
    if isinstance(count, int):
      return self.li(out, count)
    return self.mv(out, count)

  def cb_iface(self, interface_base: int, cb_index: int, *, out: Reg = t6):
    return self.li(out, interface_base + cb_index * CB.LOCAL_INTERFACE_SIZE)

  def setup_local_cbs(self, interface_base: int, *, trisc_id: int | None = None):
    """Emit the per-launch local circular-buffer interface setup loop.

    ``trisc_id is None`` produces the BRISC/NCRISC worker layout (byte units,
    plus a SYNC_TILES received/acked reset per CB). ``trisc_id in (0, 2)``
    produces the TRISC pack/unpack layout (16B units, no SYNC reset, with the
    trisc-specific field offsets). ``interface_base`` is the CB interface base
    for the calling RISC.
    """
    self.current_launch_ptr(launch=t0, tmp=t4)
    self.lw(t1, t0, Launch.KERNEL_CONFIG_BASE)
    self.lhu(t2, t0, Launch.LOCAL_CB_OFFSET)
    self.add(t2, t1, t2)
    self.li(t3, interface_base)
    self.lw(t4, t0, Launch.LOCAL_CB_MASK)
    if trisc_id is None:
      self.li(t0, CB.SYNC_TILES_ACKED_BASE)
      self.li(t1, CB.SYNC_TILES_RECEIVED_BASE)
    setup_cb_loop = self._new_label("setup_cb")
    skip_cb = self._new_label("skip_cb")
    done_cb = self._new_label("done_cb")
    self.label(setup_cb_loop)
    self.beq(t4, zero, done_cb)
    if trisc_id is None:
      self.andi(t5, t4, 1)
      self.beq(t5, zero, skip_cb)
      self.lw(t5, t2, 4)
      self.lw(t6, t2, 0)
      self.sw(t5, t3, 0)
      self.add(t5, t6, t5)
      self.sw(t5, t3, 4)
      self.lw(t5, t2, 12)
      self.sw(t5, t3, 8)
      self.lw(t5, t2, 8)
      self.sw(t5, t3, 12)
      self.sw(t6, t3, 16)
      self.sw(t6, t3, 20)
      self.sw(zero, t3, 24)
      self.sw(zero, t3, 28)
      self.sw(zero, t0, 0)
      self.sw(zero, t1, 0)
    else:
      self.andi(t1, t4, 1)
      self.beq(t1, zero, skip_cb)
      self.lw(t5, t2, 4)
      self.lw(t6, t2, 0)
      self.lw(t0, t2, 12)
      self.srli(t5, t5, 4)
      self.srli(t6, t6, 4)
      self.srli(t0, t0, 4)
      self.sw(t5, t3, 0)
      self.add(t5, t6, t5)
      self.sw(t5, t3, 4)
      self.sw(t0, t3, 8)
      if trisc_id == 0:
        self.sw(t6, t3, 16)
      else:
        self.lw(t1, t2, 8)
        self.sw(t1, t3, 12)
        self.sw(t6, t3, 20)
      self.sw(zero, t3, 24)
      if trisc_id == 2:
        self.sw(zero, t3, 28)
    self.label(skip_cb)
    self.addi(t2, t2, CB.LOCAL_CONFIG_SIZE)
    self.addi(t3, t3, CB.LOCAL_INTERFACE_SIZE)
    if trisc_id is None:
      self.li(t5, CB.SYNC_STRIDE)
      self.add(t0, t0, t5)
      self.add(t1, t1, t5)
    self.srli(t4, t4, 1)
    self.j(setup_cb_loop)
    self.label(done_cb)
    return self

  def cb_counter_low(self, out: Reg, counter_reg: Reg):
    self.slli(out, counter_reg, 16)
    return self.srli(out, out, 16)

  def cb_counter_high(self, out: Reg, counter_reg: Reg):
    return self.srli(out, counter_reg, 16)

  @with_scope
  def cb_reserve_back(self, interface_base: int, cb_index: int, count: int | Reg = 1):
    iface, received, acked, free_pages, num_pages, need = self.tmp(6)
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
    self._load_count(count, need)
    self.bge(free_pages, need, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  def cb_push_back(self, interface_base: int, cb_index: int, count: int | Reg = 1, *, tensix_received: bool = False):
    iface, ptr, tmp, counter, acked, received = t6, t5, t4, t3, t2, t1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(ptr, iface, 20)
    self.lw(tmp, iface, 8)
    if isinstance(count, int) and count == 1:
      self.add(ptr, ptr, tmp)
    else:
      self._load_count(count, counter)
      self.mul(tmp, tmp, counter)
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
    if isinstance(count, int) and count == 1:
      self.addi(received, received, 1)
    else:
      self._load_count(count, tmp)
      self.add(received, received, tmp)
    self.slli(received, received, 16)
    self.or_(counter, received, acked)
    self.sw(counter, iface, 24)
    self.srli(received, received, 16)
    if not tensix_received:
      # Mirror of the tensix_ack rule in cb_pop_front: with tensix_received
      # the consumer must only see `received` advance via the deferred
      # STOREREG (ordered behind the pack), never via an eager RISC store.
      self.li(tmp, CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE)
      self.sw(received, tmp, 0)
    if tensix_received:
      self.slli(tmp, received, 8)
      self.li(ptr, TTSETDMAREG(0, 0, 0, 48).raw_word())
      self.add(tmp, tmp, ptr)
      self.write32(TensixRegs.INSTRN_BUF_BASE, tmp, tmp_addr=ptr, tmp_val=t0)
      self.emit(TTSTALLWAIT(32, 8))
      self.push_tensix(
        TTSTOREREG(24, ((CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE) >> 2) & 0x3FFFF),
      )
    return self.fence()

  def cb_wait_front(self, interface_base: int, cb_index: int, count: int | Reg = 1):
    iface, counter, acked, received, available, need = t6, t5, t4, t3, t2, t1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(counter, iface, 24)
    self.cb_counter_low(acked, counter)
    self._load_count(count, need)
    loop = self._new_label("cb_wait_front")
    done = self._new_label("cb_wait_front_done")
    self.label(loop)
    self.li(received, CB.SYNC_TILES_RECEIVED_BASE + cb_index * CB.SYNC_STRIDE)
    self.lhu(received, received, 0)
    self.sub(available, received, acked)
    self._load_count(count, need)
    self.bgeu(available, need, done)
    self.fence()
    self.j(loop)
    self.label(done)
    return self.fence()

  def cb_pop_front(self, interface_base: int, cb_index: int, count: int | Reg = 1, *, tensix_ack: bool = False):
    iface, ptr, tmp, counter, acked, received = t6, t5, t4, t3, t2, t1
    self.cb_iface(interface_base, cb_index, out=iface)
    self.lw(counter, iface, 24)
    self.cb_counter_low(acked, counter)
    self.cb_counter_high(received, counter)
    if isinstance(count, int) and count == 1:
      self.addi(acked, acked, 1)
    else:
      self._load_count(count, tmp)
      self.add(acked, acked, tmp)
    self.cb_counter_low(acked, acked)
    self.slli(received, received, 16)
    self.or_(counter, received, acked)
    self.sw(counter, iface, 24)
    if not tensix_ack:
      # Publish the ack to the producer immediately. With tensix_ack the
      # release MUST come only from the deferred STOREREG below (ordered
      # behind the unpack in the Tensix FIFO); an eager RISC store here
      # frees pages before the unpack consumed them — producer wraps and
      # math-bound streams compute tile i+CB_DEPTH (microbenching/todo.md).
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
    if isinstance(count, int) and count == 1:
      self.add(ptr, ptr, tmp)
    else:
      self._load_count(count, counter)
      self.mul(tmp, tmp, counter)
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
