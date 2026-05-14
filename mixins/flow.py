from __future__ import annotations

import dsl
from dsl import Reg, ra, t0, t1, t2, t3, t4, zero

GO_MSG = 0x370
GO_SIGNAL = GO_MSG + 3
LAUNCH = 0x70
SUBORDINATE_SYNC = 0x68

RUN_MSG_GO = 0x80
RUN_MSG_DONE = 0x00
RUN_SYNC_MSG_GO = 0x80
RUN_SYNC_MSG_DONE = 0x00

LAUNCH_KERNEL_CONFIG_BASE = 0
LAUNCH_KERNEL_TEXT_OFFSET = 44
LAUNCH_ENABLES = 76


class FirmwareFlowMixin:
  def wait32(self, addr: int, value: int, *, tmp: Reg = t0, expected: Reg = t1):
    self.li(expected, value)
    start = self._new_label("wait32")
    self.label(start)
    self.read32(tmp, addr)
    self.bne(tmp, expected, start)
    return self

  def wait8(self, addr: int, value: int, *, tmp_addr: Reg = t0, tmp: Reg = t1):
    from dsl import t2

    self.li(tmp_addr, addr)
    self.li(t2, value)
    start = self._new_label("wait8")
    self.label(start)
    self.lbu(tmp, tmp_addr, 0)
    self.bne(tmp, t2, start)
    return self

  def signal8(self, addr: int, value: int):
    return self.write8(addr, value)

  def invalidate_l1_cache(self):
    return self.fence()

  def setup_stack(self, stack_top: int):
    from dsl import sp

    return self.li(sp, stack_top)

  def wait_go(self):
    return self.wait8(GO_SIGNAL, RUN_MSG_GO)

  def signal_done(self):
    return self.signal8(GO_SIGNAL, RUN_MSG_DONE)

  def signal_subordinate_go(self, role_index: int):
    return self.signal8(SUBORDINATE_SYNC + role_index - 1, RUN_SYNC_MSG_GO)

  def signal_subordinate_done(self, role_index: int):
    return self.signal8(SUBORDINATE_SYNC + role_index - 1, RUN_SYNC_MSG_DONE)

  def wait_subordinate_go(self, role_index: int):
    return self.wait8(SUBORDINATE_SYNC + role_index - 1, RUN_SYNC_MSG_GO)

  def wait_subordinate_done(self, role_index: int):
    return self.wait8(SUBORDINATE_SYNC + role_index - 1, RUN_SYNC_MSG_DONE)

  def launch_kernel_enabled(self, role_index: int, *, enabled: Reg = t0, mask: Reg = t1):
    self.read32(enabled, LAUNCH + LAUNCH_ENABLES)
    self.li(mask, 1 << role_index)
    return self.emit(dsl.and_(enabled, enabled, mask))

  def run_launch_kernel(self, role_index: int, *, launch: Reg = t0, config_base: Reg = t1,
                        offset: Reg = t2, entry: Reg = t3, enabled: Reg = t4):
    skip = self._new_label("skip_kernel")
    self.launch_kernel_enabled(role_index, enabled=enabled, mask=offset)
    self.beq(enabled, zero, skip)
    self.li(launch, LAUNCH)
    self.lw(config_base, launch, LAUNCH_KERNEL_CONFIG_BASE)
    self.lw(offset, launch, LAUNCH_KERNEL_TEXT_OFFSET + 4 * role_index)
    self.add(entry, config_base, offset)
    self.jalr(ra, entry, 0)
    self.label(skip)
    return self
