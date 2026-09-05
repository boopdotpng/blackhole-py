"""Pytest helpers for the byte-buffer runtime in device.py."""

from fw.consts import TensixL1
from pcie import TLBWindow
from program import RETURN_KERNEL as _PLACEHOLDER_IMAGES


class RawHarness:
  """Small pytest-facing facade; execution remains sequential by design."""

  def __init__(self, device, timeout=10.0, core_index=0):
    self.device = device
    self.timeout = timeout
    self.core_index = core_index

  @property
  def core(self):
    return self.device.cores[self.core_index]

  def dram_buffer(self, size, *, bank=0, initial=None):
    buffer = self.device.alloc_dram(size, bank=bank)
    initial = bytes(size) if initial is None else bytes(initial)
    if len(initial) != size:
      raise ValueError("initial DRAM bytes have the wrong size")
    self.device.write_dram(buffer, initial, timeout=self.timeout)
    return buffer

  def interleaved_dram_buffer(self, size, *, page_size=2048, banks=None,
                              bank_start=0, initial=None):
    buffer = self.device.alloc_interleaved_dram(
      size, page_size=page_size, banks=banks, bank_start=bank_start,
    )
    initial = bytes(size) if initial is None else bytes(initial)
    if len(initial) != size:
      raise ValueError("initial interleaved DRAM bytes have the wrong size")
    self.device.write_dram(buffer, initial, timeout=self.timeout)
    return buffer

  def dram_coordinates(self, noc=0, banks=None, bank_start=0):
    if noc not in (0, 1):
      raise ValueError("NoC index must be zero or one")
    endpoints = self.device.pcie.dram_endpoints
    banks = len(endpoints) if banks is None else banks
    if type(banks) is not int or not 0 < banks <= len(endpoints):
      raise ValueError("DRAM bank count exceeds the enabled banks")
    if (type(bank_start) is not int or bank_start < 0 or
        bank_start + banks > len(endpoints)):
      raise ValueError("DRAM bank range exceeds the enabled banks")
    selected = endpoints[bank_start:bank_start + banks]
    return tuple(x | y << 6 for x, y in (pair[noc] for pair in selected))

  def launch(self, images, *, params=(), l1=None, core=None, profiler=None):
    """Launch supplied RISC roles; missing roles immediately return to firmware."""
    core = self.core if core is None else core
    images = {**_PLACEHOLDER_IMAGES, **dict(images)}
    if profiler is not None: profiler._validate(l1)
    result = self.device.launch(
      {core: images}, params={core: tuple(params)}, l1=l1,
      timeout=self.timeout,
    )
    if profiler is not None:
      profiler._report(self.device, core, self.timeout)
    return result

  def launch_many(self, images, *, cores, params=None, l1=None):
    """Launch one raw five-RISC image set on several worker tiles.

    ``params`` may map each core to its own tuple, which is what interleaved
    DRAM shards need: every tile gets a distinct per-bank base address while
    running identical direct RISC-V code.
    """
    cores = tuple(cores)
    images = {**_PLACEHOLDER_IMAGES, **dict(images)}
    if params is None:
      params = {core: () for core in cores}
    else:
      params = {core: tuple(words) for core, words in dict(params).items()}
    return self.device.launch(
      {core: images for core in cores}, params=params, l1=l1,
      timeout=self.timeout,
    )

  def launch_many_mapped(self, images, *, params=None, l1=None):
    """Launch a potentially different raw image set on every selected tile."""
    core_images = {
      core: {**_PLACEHOLDER_IMAGES, **dict(core_roles)}
      for core, core_roles in dict(images).items()
    }
    if params is None:
      params = {core: () for core in core_images}
    else:
      params = {core: tuple(words) for core, words in dict(params).items()}
    return self.device.launch(
      core_images, params=params, l1=l1, timeout=self.timeout,
    )

  def read_l1(self, core, address, size):
    """Read a small post-kernel result record directly from one worker L1."""
    if core not in self.device.cores:
      raise ValueError("L1 read targets an unavailable worker tile")
    if not 0 <= address or size <= 0 or address + size > TensixL1.SIZE:
      raise ValueError("L1 read is outside worker L1")
    base = address & -TLBWindow.SIZE
    with TLBWindow(self.device.pcie.fd, core) as window:
      window.target(base, core)
      return window.read(address - base, size)

  def read(self, buffer):
    return self.device.read_dram(buffer, timeout=self.timeout)

  def write(self, buffer, data):
    return self.device.write_dram(buffer, data, timeout=self.timeout)
