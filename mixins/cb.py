from __future__ import annotations

from dsl import Reg, t0, t1, zero


class CbMixin:
  def clear_cb_sync_registers(self, tiles_received_base: int, tiles_acked_base: int, count: int = 64,
                              *, ptr: Reg = t0, remaining: Reg = t1):
    self.li(ptr, tiles_received_base)
    self.li(remaining, count)
    with self.loop():
      from asm import cond

      self.break_(cond(remaining, "==", zero))
      self.sw(zero, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(remaining, remaining, -1)

    self.li(ptr, tiles_acked_base)
    self.li(remaining, count)
    with self.loop():
      from asm import cond

      self.break_(cond(remaining, "==", zero))
      self.sw(zero, ptr, 0)
      self.addi(ptr, ptr, 4)
      self.addi(remaining, remaining, -1)
    return self
