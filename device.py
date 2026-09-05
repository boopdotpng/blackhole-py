"""Byte-buffer runtime: C firmware boot, DRAM transfers, and raw program launches."""

from dataclasses import dataclass
import time

from cq import DRAM_BRISC_READY, DRAM_NCRISC_READY, CommandQueue, DramCopy, rectangles
from fw import c_firmware
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

  def __init__(self, index=None, sysmem_size=1 << 30):
    index = self.DEFAULT_INDEX if index is None else index
    self.pcie = PCIDevice(index, sysmem_size)
    self.cq = None
    self._dram = Allocator(0x40, 1 << 32, 64)

  @property
  def cores(self):
    return tuple(self.pcie.cores)

  def boot(self):
    pcie_mid = self.pcie.sysmem.noc_addr >> 32
    images = c_firmware.build(pcie_mid, self.pcie.dram_endpoints)
    worker_firmware = b"".join(
      image.ljust(size, b"\0")
      for (_, size), image in zip(Firmware.TEXT.values(), images.workers)
    )
    firmware_base = Firmware.TEXT["brisc"][0]

    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as window:
      def worker_write(address, value, *, bytes=4):
        data = value.to_bytes(bytes, "little") if isinstance(value, int) else value
        base = address & -TLBWindow.SIZE
        for start, end in rectangles(self.pcie.cores):
          window.target(base, start, end)
          window.write(address - base, data)

      worker_write(
        TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
        TensixMMIO.SOFT_RESET_ALL,
      )
      worker_write(firmware_base, worker_firmware)
      boot = RV32().jal(R.ZERO, firmware_base + 4).to_bytes(4, "little")
      worker_write(TensixL1.BOOT, boot)
      worker_write(FirmwareControl.GO_SIGNAL & -4, 0)
      worker_write(
        TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
        TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN,
      )

      service_cores = (
        self.pcie.prefetch_core, self.pcie.dispatch_core, self.pcie.dram_core,
      )

      def service_write(core, address, value):
        base = address & -TLBWindow.SIZE
        window.target(base, core)
        window.write(address - base, value)

      for core in service_cores:
        service_write(
          core, TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
          TensixMMIO.SOFT_RESET_ALL,
        )
      for core, role_images in (
        (self.pcie.prefetch_core, {"brisc": images.prefetch}),
        (self.pcie.dispatch_core, {"brisc": images.dispatch}),
        (
          self.pcie.dram_core,
          {"brisc": images.dram_brisc, "ncrisc": images.dram_ncrisc},
        ),
      ):
        window.target(0, core)
        for role, image in role_images.items():
          window.write(TensixL1.WORKER_TEXT_BASE[role], image)
        entry = RV32().jal(
          R.ZERO, TensixL1.WORKER_TEXT_BASE["brisc"],
        ).to_bytes(4, "little")
        window.write(TensixL1.BOOT, entry)

      # These readiness words belong to the two service RISCs on the DRAM tile.
      window.target(0, self.pcie.dram_core)
      window.write(DRAM_BRISC_READY, bytes(8))
      self.cq = CommandQueue(self.pcie)
      for core in service_cores:
        window.target(0, core)
        window.write(FirmwareControl.GO_SIGNAL, int(RunState.GO), bytes=1)
      for core in service_cores:
        service_write(
          core, TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
          TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN,
        )
      window.target(0, self.pcie.dram_core)

      deadline = time.monotonic() + 5.0
      while (
        int.from_bytes(window.read(DRAM_BRISC_READY, 4), "little") != 1 or
        int.from_bytes(window.read(DRAM_NCRISC_READY, 4), "little") != 1
      ):
        if time.monotonic() >= deadline:
          raise TimeoutError("command-queue firmware did not start")
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
        for start, end in rectangles(self.pcie.cores):
          window.target(base, start, end)
          window.write(address - base, TensixMMIO.SOFT_RESET_ALL)
    finally:
      if self.cq is not None:
        self.cq.close()
        self.cq = None
      self.pcie.close()
