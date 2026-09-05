"""Minimal hardware runner for handwritten Blackhole RISC-V kernels.

This module deliberately does not import ``program.py`` or anything from
``ttk``.  Tests own all five worker instruction streams and all device-side
data movement.  The harness only boots the resident firmware, writes bytes to
L1/DRAM, starts workers, and copies result bytes back from DRAM.
"""

from dataclasses import dataclass
from struct import Struct
import time

from cq import (
  DRAM_BRISC_READY, DRAM_NCRISC_READY, CommandQueue, DramCopy, McastWrite,
  MAX_WRITE_SIZE, Run, UnicastWrite,
)
from fw import c_firmware
from fw.consts import (
  Firmware, FirmwareControl, KERNEL_ROLES, RunState, TensixL1, TensixMMIO,
)
from isa import R, RV32
from pcie import Allocator, PCIDevice, TLBWindow


PARAM_STRUCT = Struct(f"<{TensixL1.PARAM_SLOTS}I")
_PLACEHOLDER_IMAGES = {
  role: RV32().jal(
    R.ZERO, Firmware.TEXT[role][0] - TensixL1.WORKER_TEXT_BASE[role],
  ).to_bytes(4, "little")
  for role in KERNEL_ROLES
}


def _rectangles(cores):
  """Cover a set of worker coordinates with exact multicast rectangles."""
  rows = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  active, result, previous_y = {}, [], None
  for y in sorted(rows):
    runs = []
    for x in sorted(rows[y]):
      if runs and x == runs[-1][1] + 1:
        runs[-1] = (runs[-1][0], x)
      else:
        runs.append((x, x))
    if previous_y is None or y != previous_y + 1:
      result.extend(active.values())
      active = {}
    following = {}
    for run in runs:
      if run in active:
        following[run] = (active[run][0], (run[1], y))
      else:
        following[run] = ((run[0], y), (run[1], y))
    result.extend(rect for run, rect in active.items() if run not in following)
    active, previous_y = following, y
  result.extend(active.values())
  return tuple(result)


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


class RawDevice:
  """Command-queue runtime with no tensor, kernel, or TTK abstractions."""

  def __init__(self, index=0, sysmem_size=1 << 30):
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
        for start, end in _rectangles(self.pcie.cores):
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
      for core in (self.pcie.prefetch_core, self.pcie.dispatch_core):
        service_write(
          core, TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
          TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN,
        )
      service_write(
        self.pcie.dram_core, TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0,
        TensixMMIO.SOFT_RESET_BRISC_ONLY_RUN,
      )
      window.target(0, self.pcie.dram_core)

      deadline = time.monotonic() + 5.0
      while (
        int.from_bytes(window.read(DRAM_BRISC_READY, 4), "little") != 1 or
        int.from_bytes(window.read(DRAM_NCRISC_READY, 4), "little") != 1
      ):
        if time.monotonic() >= deadline:
          raise TimeoutError("raw-test command-queue firmware did not start")
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
    """Upload raw images and launch all selected Tensix worker tiles once.

    ``core_images`` maps each worker coordinate to a role-to-bytes mapping.
    ``params`` maps each coordinate to up to 12 raw u32 parameter words.
    ``l1`` maps L1 addresses to bytes copied identically to all selected tiles.
    """
    if self.cq is None:
      raise RuntimeError("boot() must be called first")
    core_images = {core: dict(images) for core, images in core_images.items()}
    cores = tuple(core_images)
    if not cores:
      raise ValueError("a raw launch requires at least one worker tile")
    if len(set(cores)) != len(cores) or any(core not in self.cores for core in cores):
      raise ValueError("raw launch contains an unavailable worker tile")

    commands = []
    required_roles = set(KERNEL_ROLES)
    for images in core_images.values():
      missing = required_roles - set(images)
      unknown = set(images) - required_roles
      if missing or unknown:
        raise ValueError(
          f"each tile must supply exactly the five RISC roles; "
          f"missing={sorted(missing)}, unknown={sorted(unknown)}",
        )
    for role in KERNEL_ROLES:
      groups = {}
      for core, images in core_images.items():
        image = bytes(images[role])
        if not image or len(image) % 4:
          raise ValueError(f"{role} image must contain complete instructions")
        if len(image) > TensixL1.WORKER_TEXT_SIZE[role]:
          raise ValueError(f"{role} image exceeds its worker text partition")
        groups.setdefault(image, []).append(core)
      for image, image_cores in groups.items():
        for offset in range(0, len(image), MAX_WRITE_SIZE):
          chunk = image[offset:offset + MAX_WRITE_SIZE]
          if len(image_cores) == 1:
            commands.append(UnicastWrite(
              tuple(image_cores),
              TensixL1.WORKER_TEXT_BASE[role] + offset,
              (chunk,),
            ))
          else:
            commands.append(McastWrite(
              _rectangles(image_cores),
              TensixL1.WORKER_TEXT_BASE[role] + offset,
              chunk,
            ))

    params = {} if params is None else dict(params)
    unknown_param_cores = set(params) - set(cores)
    if unknown_param_cores:
      raise ValueError("parameters were supplied for a tile outside the launch")
    tables = []
    for core in cores:
      words = tuple(params.get(core, ()))
      if len(words) > TensixL1.PARAM_SLOTS:
        raise ValueError("raw parameter table has more than 12 words")
      if any(type(word) is not int or not 0 <= word < 1 << 32 for word in words):
        raise ValueError("raw parameters must be u32 integers")
      tables.append(PARAM_STRUCT.pack(*(words + (0,) * (TensixL1.PARAM_SLOTS - len(words)))))
    commands.append(UnicastWrite(cores, TensixL1.PARAM_BASE, tuple(tables)))

    for address, data in ({} if l1 is None else dict(l1)).items():
      data = bytes(data)
      if not data:
        raise ValueError("raw L1 initialization cannot be empty")
      if not 0 <= address or address + len(data) > TensixL1.SIZE:
        raise ValueError("raw L1 initialization is outside worker L1")
      for offset in range(0, len(data), MAX_WRITE_SIZE):
        commands.append(McastWrite(
          _rectangles(cores), address + offset,
          data[offset:offset + MAX_WRITE_SIZE],
        ))

    commands.append(Run(cores))
    return self.cq.submit(tuple(commands), timeout=timeout)

  def close(self):
    if self.pcie.fd < 0:
      return
    try:
      with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as window:
        address = TensixMMIO.RISCV_DEBUG_REG_SOFT_RESET_0
        base = address & -TLBWindow.SIZE
        for start, end in _rectangles(self.pcie.cores):
          window.target(base, start, end)
          window.write(address - base, TensixMMIO.SOFT_RESET_ALL)
    finally:
      if self.cq is not None:
        self.cq.close()
        self.cq = None
      self.pcie.close()


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
