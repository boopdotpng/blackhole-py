from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from asm import KernelBase
from dsl import Reg, ra, s3, s5, sp, t0, t1, t2, zero
from ttk import Cb, Debug, Flow, Noc, Tensix
from ttk.addrs import TriscMailbox as TM


@dataclass(frozen=True)
class RiscSync:
  """L1 sync-word layout for the 5-RISC start/init handshake.

  - ``start``: byte-triplet base. BRISC writes ``0x00010101`` here to release
    the three TRISCs; TRISC ``i`` spins on byte ``start + i`` then clears it.
  - ``trisc_init``: base of three words used as the post-init barrier. TRISC
    ``i`` sets word ``i`` to 1, then waits for all three to be 1.
  """

  start: int
  trisc_init: int


class _RoleKernel(KernelBase):
  """Shared scaffolding for the per-thread role kernels: the standard
  ``count``-driven tile loop. Subclasses pick their own mixin set and override
  ``_loop_epilogue`` to emit the right return sequence."""

  def _loop_epilogue(self):
    return self.ret()

  @contextmanager
  def tile_loop(self, name: str, *, count: Reg = s3, counter: Reg = s5) -> Iterator[None]:
    """Emit ``for counter in range(count)`` around the yielded body, closing
    with the role's epilogue. ``count`` is loaded by the kernel prologue
    (typically the per-core tile count in s3)."""
    self.li(counter, 0)
    self.label(f"{name}_loop")
    self.beq(counter, count, f"{name}_done")
    yield
    self.addi(counter, counter, 1)
    self.j(f"{name}_loop")
    self.label(f"{name}_done")
    self._loop_epilogue()


class Trisc(_RoleKernel, Tensix, Cb, Flow, Debug):
  """Compute-thread kernel (unpack / math / pack). Composes the Tensix, CB and
  flow helpers — no NOC, since TRISCs never drive the NOC directly. Provides the
  prologue / init-barrier / tile-loop scaffolding common to every TRISC so a
  concrete kernel only fills in its op-specific config and loop body."""

  NUM_TRISC = 3

  def __init__(self, thread_id: int, sync: RiscSync, *, base_addr: int = 0):
    super().__init__(base_addr=base_addr)
    self.thread_id = thread_id
    self.sync = sync
    # DATA1 has a distinct mailbox layout; TRISC0/2 share DATA_COMMON.
    self.data = TM.DATA1 if thread_id == 1 else TM.DATA_COMMON

  def prologue(self):
    """Stack frame, load per-core tile count into s3, then wait for BRISC's
    start signal and clear it."""
    self.addi(sp, sp, -16)
    self.sw(ra, sp, 12)
    self.read32(t0, self.data["rta_l1_base"])
    self.lw(s3, t0, 0)
    self.wait8(self.sync.start + self.thread_id, 1)
    self.write8(self.sync.start + self.thread_id, 0)
    return self

  def init_barrier(self):
    """Publish this thread's init-done flag, then wait for all TRISCs."""
    self.write32(self.sync.trisc_init + self.thread_id * 4, 1)
    self.fence()
    self.li(t1, 1)
    for init_id in range(self.NUM_TRISC):
      self.wait_sync_value(self.sync.trisc_init + init_id * 4, t1, actual=t2)
    return self

  def _loop_epilogue(self):
    return self.ret_kernel()

  def tile_loop(self, *, count: Reg = s3, counter: Reg = s5) -> Iterator[None]:
    return super().tile_loop(f"trisc{self.thread_id}", count=count, counter=counter)


class Brisc(_RoleKernel, Noc, Cb, Flow, Debug):
  """Reader-thread kernel: NOC + CB + flow helpers, no Tensix config."""


class Ncrisc(_RoleKernel, Noc, Cb, Flow, Debug):
  """Writer-thread kernel: NOC + CB + flow helpers, no Tensix config."""
