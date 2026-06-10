"""Host-side DRISC launch/poll helpers shared by the examples.

These functions were copied near-verbatim across several DRISC example POCs
(``drisc_cb_direct_poc``, ``drisc_gddr_dma_poc``, ``drisc_gddr_to_worker_poc``,
``matmul_peak_drisc``).  The per-file copies differed only in the result magic
they polled for and whether they accepted a corrupt result header, so those are
exposed as parameters here.

The hardware addresses (``DRISC_FW_BASE`` etc.) and ``RegWindow`` are canonical
here; ``examples/drisc_hello.py`` re-exports them for the older POCs.
"""
from __future__ import annotations

import struct
import time

from pcie import PCIDevice, TLBWindow, TLB_2M_SIZE

DRISC_L1_NOC_ALIAS = 0x2000000000
DRISC_FW_BASE = 0x3260
REG_TLB = 191
SOFT_RESET_0 = 0xFFB121B0
DRISC_RESET_PC = 0xFFB14000
SOFT_RESET_BRISC = 0x800

# Mirror of the result-region layout in examples/drisc_gddr_dma_poc.py.
RESULT_ADDR = 0x1F000
RESULT_WORDS = 16
STATUS_DONE = 2
STATUS_TIMEOUT = 3


def pattern(size: int, seed: int) -> bytes:
  return bytes(((i * 37 + seed) ^ (i >> 3)) & 0xFF for i in range(size))


class RegWindow:
  def __init__(self, dev: PCIDevice, core: tuple[int, int]):
    self.dev = dev
    self.core = core
    self.mm = dev.tlb_window(REG_TLB)

  def _configure(self, addr: int) -> int:
    base = addr & ~(TLB_2M_SIZE - 1)
    x, y = self.core
    self.dev.configure_tlb(
      REG_TLB, addr,
      x_start=x, y_start=y, x_end=x, y_end=y,
      ordering=1,
    )
    return addr - base

  def read32(self, addr: int) -> int:
    return struct.unpack("<I", self.mm.read(self._configure(addr), 4))[0]

  def write32(self, addr: int, value: int):
    self.mm.write(self._configure(addr), struct.pack("<I", value & 0xFFFFFFFF))

  def close(self):
    self.mm.close()


def start_drisc(core, code: bytes, dev, *, result_addr: int = RESULT_ADDR, result_words: int = RESULT_WORDS):
  with TLBWindow(dev, start=core, addr=DRISC_L1_NOC_ALIAS) as l1:
    regs = RegWindow(dev, core)
    try:
      l1.write(result_addr, b"\0" * (result_words * 4))
      l1.write(DRISC_FW_BASE, code)
      reset_state = regs.read32(SOFT_RESET_0)
      regs.write32(SOFT_RESET_0, reset_state | SOFT_RESET_BRISC)
      regs.write32(DRISC_RESET_PC, DRISC_FW_BASE)
      time.sleep(0.01)
      regs.write32(SOFT_RESET_0, reset_state & ~SOFT_RESET_BRISC)
    finally:
      regs.close()


def wait_drisc(core, dev, timeout: float, *, magic: int, accept_corrupt: bool = False,
               result_addr: int = RESULT_ADDR, result_words: int = RESULT_WORDS,
               label: str = "DRISC feeder"):
  with TLBWindow(dev, start=core, addr=DRISC_L1_NOC_ALIAS) as l1:
    regs = RegWindow(dev, core)
    deadline = time.time() + timeout
    words = (0,) * result_words
    try:
      while time.time() < deadline:
        words = struct.unpack("<" + "I" * result_words, l1.read(result_addr, result_words * 4))
        if words[6] == STATUS_DONE and (words[0] == magic or accept_corrupt):
          break
        time.sleep(0.001)
      reset_state = regs.read32(SOFT_RESET_0)
      regs.write32(SOFT_RESET_0, reset_state | SOFT_RESET_BRISC)
      if words[6] != STATUS_DONE or (words[0] != magic and not accept_corrupt):
        raise TimeoutError(f"{label} did not finish on {core}; words={[hex(w) for w in words]}")
      return words
    finally:
      regs.close()


def read_drisc_words(core, dev, *, result_addr: int = RESULT_ADDR, result_words: int = RESULT_WORDS):
  with TLBWindow(dev, start=core, addr=DRISC_L1_NOC_ALIAS) as l1:
    return struct.unpack("<" + "I" * result_words, l1.read(result_addr, result_words * 4))


def launch_drisc(core, l1, regs, code: bytes, timeout: float, *, magic: int,
                 accept_timeout: bool = True, accept_corrupt: bool = False,
                 result_addr: int = RESULT_ADDR, result_words: int = RESULT_WORDS,
                 label: str = "DRISC kernel"):
  l1.write(result_addr, b"\0" * (result_words * 4))
  l1.write(DRISC_FW_BASE, code)
  reset_state = regs.read32(SOFT_RESET_0)
  regs.write32(SOFT_RESET_0, reset_state | SOFT_RESET_BRISC)
  regs.write32(DRISC_RESET_PC, DRISC_FW_BASE)
  time.sleep(0.01)
  regs.write32(SOFT_RESET_0, reset_state & ~SOFT_RESET_BRISC)

  done_states = (STATUS_DONE, STATUS_TIMEOUT) if accept_timeout else (STATUS_DONE,)
  status = 0
  deadline = time.time() + timeout
  while time.time() < deadline:
    words = struct.unpack("<" + "I" * result_words, l1.read(result_addr, result_words * 4))
    if (words[0] == magic or accept_corrupt) and words[6] in done_states:
      status = words[6]
      break
    time.sleep(0.001)

  final_reset_state = regs.read32(SOFT_RESET_0)
  regs.write32(SOFT_RESET_0, final_reset_state | SOFT_RESET_BRISC)
  if status == 0:
    words = struct.unpack("<" + "I" * result_words, l1.read(result_addr, result_words * 4))
    raise TimeoutError(f"{label} did not finish on {core}; words={[hex(w) for w in words]}")
  return struct.unpack("<" + "I" * result_words, l1.read(result_addr, result_words * 4))
