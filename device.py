import mmap, struct, time
import fw
from cq import CopyQueue, Ring
from pcie import ALL, CORES, PAGE, PCIDevice, addressof, round_up

# The arena is the one sysmem range pinned for the device's lifetime: the two rings, the signal slots, then a heap for
# what the CPU writes and the card reads (kernel programs, kernargs). Tensors never live here, they are pinned in place.
ARENA_SIZE = 16 << 20
COMPUTE_RING, COPY_RING, SIGNALS = 0, fw.RING_SIZE, 2 * fw.RING_SIZE
HEAP = SIGNALS + PAGE  # a page of signals: 256 slots of [value, timestamp]
TRANSFER_SIGNAL = 255  # the last slot is copyin/copyout's
DRAM_BANK_SIZE = 4 << 30

class Device:
  def __init__(self, index:int=0):
    self.pcie = PCIDevice(index, ARENA_SIZE)
    self.workers = [c for c in CORES if c not in (fw.CQ_CORE, fw.DMA_CORE)]
    self.heap, self.transfers, self.dram_top = HEAP, 0, 0
    self.dram_size = len(self.pcie.dram) * DRAM_BANK_SIZE
    self.upload_firmware()

  def close(self):
    self.pcie.reset()  # stop the queue loops before their rings in sysmem are unpinned
    self.pcie.close()
  def __enter__(self): return self
  def __exit__(self, *exc): self.close()

  def upload_firmware(self):
    """Worker firmware on every core (one multicast), then the queue loops start as kernels on the two service cores."""
    dev, images = self.pcie, fw.build(len(self.pcie.dram))
    dev.reset()
    dev.write32(ALL, fw.GO_SIGNAL, 0)  # L1 survives reset: a stale GO would launch whatever is in the kernel slots
    dev.boot({ALL: {"brisc": (fw.FW["brisc"][0], images["workers"])}})
    self.compute, self.copy = Ring(dev, fw.CQ_CORE, COMPUTE_RING), Ring(dev, fw.DMA_CORE, COPY_RING)
    dev.sysmem.mem[SIGNALS:HEAP] = bytes(HEAP - SIGNALS)
    for core in (fw.CQ_CORE, fw.DMA_CORE):
      for risc in ("brisc", "ncrisc"): dev.write(core, fw.KERNEL[risc][0], images[(core, risc)])
      for risc in ("trisc0", "trisc1", "trisc2"):  # nothing to run: return to firmware straight away
        dev.write(core, fw.KERNEL[risc][0], fw.return_stub(risc))
      dev.write32(core, fw.GO_SIGNAL, 0x80)

  # ---- the arena ----
  def sysmem(self, offset:int) -> int: return self.pcie.sysmem.noc_addr + offset
  def alloc(self, size:int, align:int=64) -> int:
    """Arena bytes for the CPU to write and the card to read, returned as an offset (see sysmem(), write())."""
    offset = round_up(self.heap, align)
    if offset + size > ARENA_SIZE: raise MemoryError(f"arena is full: {size} bytes requested, {ARENA_SIZE - offset} left")
    self.heap = offset + size
    return offset
  def write(self, offset:int, data:bytes): self.pcie.sysmem.mem[offset:offset + len(data)] = data

  def signal(self, i:int) -> int: return self.sysmem(SIGNALS + 16 * i)
  def read_signal(self, i:int) -> tuple[int, int]: return struct.unpack_from("<QQ", self.pcie.sysmem.mem, SIGNALS + 16 * i)
  def wait(self, i:int, value:int, timeout=10.0) -> int:
    """Wait for signal i to reach value, return its timestamp."""
    deadline = time.monotonic() + timeout
    while (v := self.read_signal(i))[0] < value:
      if time.monotonic() > deadline: raise TimeoutError(f"signal {i} is {v[0]}, waiting for {value}")
    return v[1]

  # ---- DRAM ----
  def alloc_dram(self, size:int) -> int:
    """Interleaved DRAM for cq.dram(offset, page), bump-allocated and never freed. A buffer covers whole rows of
    DRAM_PAGE_MAX across the banks, so whatever its page size it is bytes [offset / banks, end / banks) of every bank."""
    offset, end = self.dram_top, self.dram_top + round_up(size, len(self.pcie.dram) * fw.DRAM_PAGE_MAX)
    if end > self.dram_size: raise MemoryError(f"DRAM is full: {size} bytes requested, {self.dram_size - offset} left")
    self.dram_top = end
    return offset

  # ---- host memory the card reads and writes in place ----
  def pin(self, addr:int, size:int) -> int: return self.pcie.pin(addr, size)  # for host buffers kept pinned
  def unpin(self, addr:int, size:int): self.pcie.unpin(addr, size)

  def _transfer(self, addr:int, size:int, dev:int, upload:bool, timeout:float):
    """Move host <-> dev through the host memory itself: the DMA queue copies each chunk as soon as it is pinned, and
    a chunk is unpinned once the transfer signal says its copy is done."""
    base = self.transfers
    for h, noc, n in self.pcie.pinned(addr, size, lambda i: self.wait(TRANSFER_SIGNAL, base + i + 1, timeout)):
      d = dev + h - addr
      self.transfers += 1
      q = CopyQueue().copy(d, noc, n) if upload else CopyQueue().copy(noc, d, n)
      q.signal(self.signal(TRANSFER_SIGNAL), self.transfers).submit(self.copy)

  def _host(self, host, upload:bool, dev:int, timeout:float):
    host = memoryview(host).cast("B")
    assert dev % 64 == 0, "device addresses must be 64-byte aligned"
    if not len(host): return
    if not host.readonly and (addr := addressof(host)) % 64 == 0:
      return self._transfer(addr, len(host), dev, upload, timeout)
    # read-only or not 64-byte aligned: bounce through a page-aligned copy (one host memcpy)
    bounce = mmap.mmap(-1, len(host))
    if upload: bounce[:] = host
    self._transfer(addressof(bounce), len(host), dev, upload, timeout)
    if not upload: host[:] = bounce

  def copyin(self, dev:int, host, timeout=60.0):
    """host bytes -> device address dev (64-byte aligned). A 64-byte aligned writable host buffer is read in place."""
    self._host(host, True, dev, timeout)
  def copyout(self, host, dev:int, timeout=60.0):
    """device address dev (64-byte aligned) -> host buffer. A 64-byte aligned host buffer is written in place."""
    self._host(host, False, dev, timeout)
