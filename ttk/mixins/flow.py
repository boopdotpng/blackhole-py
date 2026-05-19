from __future__ import annotations

from dsl import Reg, ra, sp, t0, t1, t2, t3, t4, zero
from ttk.addrs import Launch, Mailbox, RunMsg

class FlowMixin:
  def wait8(self, addr: int, value: int, *, ptr: Reg = t0, actual: Reg = t1, expected: Reg = t2):
    self.li(ptr, addr)
    self.li(expected, value)
    start = self._new_label("wait8")
    done = self._new_label("wait8_done")
    self.label(start)
    self.lbu(actual, ptr, 0)
    self.beq(actual, expected, done)
    self.fence()
    self.j(start)
    self.label(done)
    self.fence()
    return self

  def wait32(self, addr: int, value: int, *, actual: Reg = t0, expected: Reg = t1):
    self.li(expected, value)
    loop = self._new_label("wait32")
    self.label(loop)
    self.read32(actual, addr)
    self.bne(actual, expected, loop)
    return self

  def signal8(self, addr: int, value: int):
    return self.write8(addr, value)

  def invalidate_l1_cache(self):
    return self.fence()

  def setup_stack(self, stack_top: int):
    return self.li(sp, stack_top)

  def current_launch_ptr(self, launch: Reg = t0, tmp: Reg = t1):
    return self.li(launch, Launch.BASE)

  def configure_csr(self, *, value: Reg = t0):
    self.li(value, 2)
    self.csrrs(zero, value, 0x7C0)
    self.li(value, 1)
    self.slli(value, value, 18)
    self.fence()
    self.csrrs(zero, value, 0x7C0)
    self.li(value, 2)
    self.csrrc(zero, value, 0x7C0)
    self.fence()
    self.fence()
    self.li(value, 8)
    self.csrrs(zero, value, 0x7C0)
    return self

  def wait_go(self):
    return self.wait8(Mailbox.GO_SIGNAL, RunMsg.GO)

  def signal_done(self):
    return self.signal8(Mailbox.GO_SIGNAL, RunMsg.DONE)

  def signal_subordinate_go(self, role_index: int):
    return self.signal8(Mailbox.SUBORDINATE_SYNC + role_index - 1, RunMsg.GO)

  def signal_subordinate_done(self, role_index: int):
    return self.signal8(Mailbox.SUBORDINATE_SYNC + role_index - 1, RunMsg.DONE)

  def wait_subordinate_go(self, role_index: int):
    return self.wait8(Mailbox.SUBORDINATE_SYNC + role_index - 1, RunMsg.GO)

  def wait_subordinate_done(self, role_index: int):
    return self.wait8(Mailbox.SUBORDINATE_SYNC + role_index - 1, RunMsg.DONE)

  def launch_kernel_enabled(self, role_index: int, *, enabled: Reg = t0, mask: Reg = t1):
    self.current_launch_ptr(enabled)
    self.lw(enabled, enabled, Launch.ENABLES)
    self.li(mask, 1 << role_index)
    return self.and_(enabled, enabled, mask)

  def run_launch_kernel(self, role_index: int, *, launch: Reg = t0, config_base: Reg = t1,
                        offset: Reg = t2, entry: Reg = t3, enabled: Reg = t4):
    skip = self._new_label("skip_kernel")
    self.launch_kernel_enabled(role_index, enabled=enabled, mask=offset)
    self.beq(enabled, zero, skip)
    self.current_launch_ptr(launch)
    self.lw(config_base, launch, Launch.KERNEL_CONFIG_BASE)
    self.lw(offset, launch, Launch.KERNEL_TEXT_OFFSET + 4 * role_index)
    self.add(entry, config_base, offset)
    self.jalr(ra, entry, 0)
    self.label(skip)
    return self
