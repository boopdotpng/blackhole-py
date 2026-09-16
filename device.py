"""Byte-buffer runtime: C firmware boot, DRAM transfers, and raw program launches."""

from dataclasses import dataclass
import time

from cq import DRAM_BRISC_READY, DRAM_NCRISC_READY, CommandQueue, DramCopy
from fw import build as firmware
from fw.consts import Firmware, FirmwareControl, RunState, TensixL1, TensixMMIO
from isa import R, RV32
from pcie import Allocator, PCIDevice, TLBWindow
from program import Program


@dataclass(frozen=True)
class DramBuffer:
  """One dense allocation in one physical DRAM bank."""

  address: int
  size: int
  physical_size: int
  page_size: int
  page_count: int
  bank: int
  coordinate: int


@dataclass(frozen=True)
class InterleavedDramBuffer:
  """Dense logical pages striped over a contiguous physical bank range."""

  address: int
  size: int
  physical_size: int
  page_size: int
  page_count: int
  banks: int
  bank_start: int = 0


class Device:
  """Command-queue runtime with no tensor, kernel, or TTK abstractions."""

  DEFAULT_INDEX = 0
  command_queue_type = CommandQueue

  def __init__(self, index=None, sysmem_size=None):
    index = self.DEFAULT_INDEX if index is None else index
    self.pcie = PCIDevice(index, sysmem_size)
    self.cq = None
    self._dram = Allocator(0x40, 1 << 32, 64)

  @property
  def cores(self):
    return tuple(self.pcie.cores)

  def boot(self, images=None):
    images = firmware.build() if images is None else images
    resident = b"".join(image.ljust(size, b"\0")
      for (_, size), image in zip(Firmware.TEXT.values(), images.workers))
    firmware_base = Firmware.TEXT["brisc"][0]
    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as window:
      # Resident firmware runs on all 120 tiles,
      # including the three service tiles, and GO enters the service loops.
      def broadcast(address, value):
        base = address & -TLBWindow.SIZE
        window.target(base, (1, 2), (14, 11))
        window.write(address - base, value)

      broadcast(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_ALL)
      broadcast(firmware_base, resident)
      broadcast(TensixL1.BOOT, RV32().jal(R.ZERO, firmware_base + 4).to_bytes(4, "little"))
      broadcast(FirmwareControl.GO_SIGNAL & -4, 0)
      broadcast(TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0, TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN)
      for core, role_images in (
        (self.pcie.prefetch_core, {"brisc": images.prefetch}),
        (self.pcie.dispatch_core, {"brisc": images.dispatch}),
        (self.pcie.dram_core, {"brisc": images.dram_brisc, "ncrisc": images.dram_ncrisc}),
      ):
        window.target(0, core)
        for role, image in role_images.items():
          window.write(TensixL1.WORKER_TEXT_BASE[role], image)
      window.target(0, self.pcie.dram_core)
      window.write(DRAM_BRISC_READY, bytes(8))
      from fw.abi import BOOT_PCIE_MID, BOOT_BANKS, BOOT_COORDS
      for core in (self.pcie.prefetch_core, self.pcie.dispatch_core, self.pcie.dram_core):
        window.target(0, core)
        window.write(BOOT_PCIE_MID, self.pcie.sysmem.noc_addr >> 32)
        window.write(BOOT_BANKS, len(self.pcie.dram_endpoints))
        for niu in range(2):
          for bank, endpoints in enumerate(self.pcie.dram_endpoints):
            x, y = endpoints[niu]
            window.write(BOOT_COORDS + niu * 32 + bank * 4, x | y << 6)
      self.cq = self.command_queue_type(self.pcie)
      for core in (self.pcie.prefetch_core, self.pcie.dispatch_core, self.pcie.dram_core):
        window.target(0, core)
        window.write(FirmwareControl.GO_SIGNAL, int(RunState.GO), bytes=1)
      window.target(0, self.pcie.dram_core)
      deadline = time.monotonic() + 5.0
      while (int.from_bytes(window.read(DRAM_BRISC_READY, 4), "little") != 1 or
             int.from_bytes(window.read(DRAM_NCRISC_READY, 4), "little") != 1):
        if time.monotonic() >= deadline:
          raise TimeoutError("CQ DRAM engines did not start")
        time.sleep(0)

  def alloc_dram(self, size, *, bank=0):
    if type(size) is not int or size <= 0:
      raise ValueError("DRAM result size must be a positive integer")
    if not 0 <= bank < len(self.pcie.dram_endpoints):
      raise ValueError("DRAM bank is not enabled on this device")
    if size <= 16 * 1024:
      page_size = (size + 15) & -16
      page_count = 1
    else:
      page_size = 16 * 1024
      page_count = (size + page_size - 1) // page_size
    physical_size = page_size * page_count
    address = self._dram.alloc(physical_size)
    x, y = self.pcie.dram_endpoints[bank][0]
    return DramBuffer(
      address, size, physical_size, page_size, page_count, bank, x | y << 6,
    )

  def alloc_interleaved_dram(self, size, *, page_size=2048, banks=None,
                             bank_start=0):
    if type(size) is not int or size <= 0:
      raise ValueError("DRAM result size must be a positive integer")
    if type(page_size) is not int or not 0 < page_size <= 16 * 1024 or page_size % 16:
      raise ValueError("interleaved DRAM page size must be 16-byte aligned and at most 16 KiB")
    banks = len(self.pcie.dram_endpoints) if banks is None else banks
    if type(banks) is not int or not 0 < banks <= len(self.pcie.dram_endpoints):
      raise ValueError("interleaved DRAM bank count exceeds the enabled banks")
    if (type(bank_start) is not int or bank_start < 0 or
        bank_start + banks > len(self.pcie.dram_endpoints)):
      raise ValueError("interleaved DRAM bank range exceeds the enabled banks")
    page_count = (size + page_size - 1) // page_size
    physical_size = page_count * page_size
    rows = (page_count + banks - 1) // banks
    address = self._dram.alloc(rows * page_size)
    return InterleavedDramBuffer(
      address, size, physical_size, page_size, page_count, banks, bank_start,
    )

  def _copy_dram(self, buffer, *, write, data=b"", timeout=10.0):
    if self.cq is None:
      raise RuntimeError("boot() must be called first")
    interleaved = isinstance(buffer, InterleavedDramBuffer)
    bank_start = buffer.bank_start if interleaved else buffer.bank
    # The unchanged llama3 descriptor addresses a prefix of banks. Preserve
    # the raw-buffer API's other bank ranges and small pages through PCIe.
    if bank_start or buffer.page_size % 64:
      return self._copy_dram_pcie(buffer, write=write, data=data, timeout=timeout)
    if buffer.physical_size > self.cq.dram_size:
      raise MemoryError("DRAM transfer exceeds the host staging region")
    if write:
      data = bytes(data)
      if len(data) != buffer.size:
        raise ValueError("DRAM write size does not match the allocation")
      self.pcie.sysmem.write(
        self.cq.dram, data.ljust(buffer.physical_size, b"\0"),
      )
    interleaved = isinstance(buffer, InterleavedDramBuffer)
    command = DramCopy(
      buffer.address,
      self.pcie.sysmem.noc_addr + self.cq.dram,
      buffer.page_size,
      buffer.page_count,
      buffer.banks if interleaved else 1,
      int(not write),
      buffer.bank_start if interleaved else buffer.bank,
    )
    self.cq.submit((command,), timeout=timeout)
    if not write:
      return self.pcie.sysmem.read(self.cq.dram, buffer.size)

  def _copy_dram_pcie(self, buffer, *, write, data, timeout):
    if write:
      data = bytes(data)
      if len(data) != buffer.size:
        raise ValueError("DRAM write size does not match the allocation")
      data = data.ljust(buffer.physical_size, b"\0")
    else:
      data = bytearray(buffer.physical_size)
    self.cq.submit((), timeout=timeout)
    interleaved = isinstance(buffer, InterleavedDramBuffer)
    banks = buffer.banks if interleaved else 1
    start = buffer.bank_start if interleaved else buffer.bank
    with TLBWindow(self.pcie.fd, self.pcie.dram_endpoints[start][0]) as window:
      for bank in range(banks):
        pages = range(bank, buffer.page_count, banks)
        dense = (b"".join(data[page * buffer.page_size:(page + 1) * buffer.page_size]
          for page in pages) if write else bytearray(len(pages) * buffer.page_size))
        offset = 0
        while offset < len(dense):
          address = buffer.address + offset
          base = address & -TLBWindow.SIZE
          size = min(len(dense) - offset, TLBWindow.SIZE - (address - base))
          window.target(base, self.pcie.dram_endpoints[start + bank][0])
          if write:
            window.write(address - base, dense[offset:offset + size])
          else:
            dense[offset:offset + size] = window.read(address - base, size)
          offset += size
        if not write:
          for row, page in enumerate(pages):
            data[page * buffer.page_size:(page + 1) * buffer.page_size] = dense[row * buffer.page_size:(row + 1) * buffer.page_size]
    if not write:
      return bytes(data[:buffer.size])

  def write_dram(self, buffer, data, timeout=10.0):
    self._copy_dram(buffer, write=True, data=data, timeout=timeout)

  def read_dram(self, buffer, timeout=10.0):
    return self._copy_dram(buffer, write=False, timeout=timeout)

  def launch(self, core_images, *, params=None, l1=None, timeout=10.0):
    return self.run(Program(core_images), params=params, l1=l1, timeout=timeout)

  def run(self, program, *, params=None, l1=None, timeout=10.0):
    if self.cq is None: raise RuntimeError("boot() must be called first")
    if any(core not in self.cores for core in program.cores):
      raise ValueError("launch contains an unavailable worker tile")
    return self.cq.submit(program.commands(params=params, l1=l1), timeout=timeout)

  def close(self):
    if self.pcie.fd < 0:
      return
    try:
      with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as window:
        address = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0
        base = address & -TLBWindow.SIZE
        window.target(base, (1, 2), (14, 11))
        window.write(address - base, TensixMMIO.SOFT_RESET_ALL)
    finally:
      if self.cq is not None:
        self.cq.close()
        self.cq = None
      self.pcie.close()
