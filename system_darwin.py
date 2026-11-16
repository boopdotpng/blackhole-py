# macOS: no tt-kmd. The TTGPU DriverKit extension (ttgpu-dext) owns the PCI device and, with allow-any-userclient-access,
# lets this process open it directly: IOConnectMapMemory64 type 0-5 maps a BAR into our address space, type >= 6 allocates
# that many bytes of DMA-prepared host memory. What tt-kmd 2.12.0 does in the kernel is done here: TLB window registers
# (blackhole.c configure_tlb_2M), outbound iATU regions for pinned memory (memory.c setup_noc_dma,
# blackhole.c configure_outbound_atu) and ARC messages (msgqueue.c arc_msg_send_sync, blackhole_set_power_state).
# BARs are device memory (uncached, no unaligned or wide accesses), so MMIO goes through aligned u32 views only.
from __future__ import annotations
import ctypes, fcntl, os, plistlib, struct, subprocess, tempfile, time
from helpers import view_at

TLB_SIZE = 1 << 21
TLB_2M_COUNT, TLB_REG_SIZE, TLB_REGS = 202, 12, 0x1FC00000   # 4G windows (BAR4) don't map over Thunderbolt: 2M only
# no tt-kmd hands out TLBs here, so fixed owners: the last window for ARC (as tt-kmd), then smi.py, then the TTGPU driver
ARC_TLB, SMI_TLB, DEXT_TLB = TLB_2M_COUNT - 1, TLB_2M_COUNT - 2, TLB_2M_COUNT - 3
LOCK_PATH = os.path.join(tempfile.gettempdir(), "blackhole-py-0.lock")  # held while a PCIDevice is open
TLB_STRIDED_COUNT, TLB_STRIDED_REGS = 32, 0x1FC00000 + (202 + 8) * 12
TT_NOC_ORDERING_STRICT = 1
IATU_BASE, IATU_STRIDE, IATU_REGIONS = 0x1000, 0x100, 16  # BAR2; outbound region r at IATU_BASE + 2*r*IATU_STRIDE
IATU_CTRL1, IATU_CTRL2, IATU_LOWER_BASE, IATU_UPPER_BASE, IATU_LOWER_LIMIT = 0x00, 0x04, 0x08, 0x0C, 0x10
IATU_LOWER_TARGET, IATU_UPPER_TARGET, IATU_CTRL3, IATU_UPPER_LIMIT = 0x14, 0x18, 0x1C, 0x20
IATU_INCREASE_REGION_SIZE, IATU_REGION_EN = 1 << 13, 1 << 31
NOC_PCIE_OFFSET = 4 << 58  # NOC address of iATU input address 0 (tt-kmd noc_pcie_offset)
ARC = (8, 0)
def RESET_SCRATCH(n): return 0x80030400 + 4 * n
ARC_BOOT_STATUS, ARC_MSG_QCB_PTR, ARC_TELEMETRY_DATA, ARC_TELEMETRY_PTR = RESET_SCRATCH(2), RESET_SCRATCH(11), RESET_SCRATCH(12), RESET_SCRATCH(13)
ARC_MSG_ASIC_STATE0, ARC_MSG_POWER_SETTING = 0xA0, 0x21
TELEMETRY_BOARD_ID = 1
CARDS = {0x36: "p100", 0x40: "p150a", 0x41: "p150b", 0x42: "p150c", 0x43: "p100a"}  # tt-kmd tt_sysfs_show_card_type
TT_POWER_FLAG_MAX_AI_CLK, TT_POWER_FLAG_MRISC_PHY_WAKEUP, TT_POWER_FLAG_TENSIX_ENABLE = 1, 2, 4
TT_POWER_VALIDITY = 15 | 0 << 4  # 15 flags, 0 settings: what tt-kmd sends for a single client
# the dext writes [addr, len, ..., 0, 0] at the start of each DMA buffer: WriteDMASegments passes IOVMPageSize as
# CreateMapping's length and alignment (the signature is options, address, offset, length, alignment), so offset is 0
DMA_TABLE_OFFSET, DMA_TABLE_SIZE = 0, 16 << 10

class IOKit:
  lib = ctypes.CDLL("/System/Library/Frameworks/IOKit.framework/IOKit")
  task = ctypes.c_uint.in_dll(ctypes.CDLL("/usr/lib/libSystem.B.dylib"), "mach_task_self_").value
  lib.IOServiceNameMatching.restype, lib.IOServiceNameMatching.argtypes = ctypes.c_void_p, [ctypes.c_char_p]
  lib.IOServiceGetMatchingService.restype, lib.IOServiceGetMatchingService.argtypes = ctypes.c_uint, [ctypes.c_uint, ctypes.c_void_p]
  lib.IOServiceOpen.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
  lib.IOServiceClose.argtypes = [ctypes.c_uint]
  lib.IOObjectRelease.argtypes = [ctypes.c_uint]
  lib.IOConnectMapMemory64.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint64),
                                       ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint]
  lib.IOConnectUnmapMemory64.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint64]
  lib.IOConnectCallScalarMethod.argtypes = [ctypes.c_uint, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint32,
                                            ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint32)]
  for f in (lib.IOServiceOpen, lib.IOServiceClose, lib.IOConnectMapMemory64, lib.IOConnectUnmapMemory64,
            lib.IOConnectCallScalarMethod): f.restype = ctypes.c_int
  kIOMapAnywhere = 1
  RPC_READ_CFG, RPC_WRITE_CFG, RPC_RESET, RPC_PREPARE_DMA, RPC_ARC_MSG = 0, 1, 2, 3, 4  # UserClient ExternalMethod selectors

  class CallError(RuntimeError):
    def __init__(self, sel, kr): super().__init__(f"driver call {sel} failed: {kr:#x}"); self.kr = kr

  def _call(self, sel:int, *args:int, outputs:int=2) -> list[int]:
    inp, out, n = (ctypes.c_uint64 * max(len(args), 1))(*args), (ctypes.c_uint64 * outputs)(), ctypes.c_uint32(outputs)
    if (kr := self.lib.IOConnectCallScalarMethod(self.conn, sel, inp, len(args), out, ctypes.byref(n))):
      raise self.CallError(sel, kr & 0xFFFFFFFF)
    return list(out)
  def arc_msg(self, header:int, payload:tuple[int, ...]=()) -> tuple[int, ...]:
    """The driver sends it, serialized across processes. 0x21 power messages are this connection's vote: the driver ORs
    every open connection's and drops this one's when the connection closes, however the process ends."""
    return tuple(w & 0xFFFFFFFF for w in self._call(self.RPC_ARC_MSG, header, *payload, outputs=8))
  def cfg_read(self, off:int, size:int=4) -> int: return self._call(self.RPC_READ_CFG, off, size)[0]
  def cfg_write(self, off:int, val:int, size:int=4): self._call(self.RPC_WRITE_CFG, off, size, val)
  def reset_link(self): self._call(self.RPC_RESET)  # dext ResetDevice: PCIe function reset, else hot reset

  def __init__(self, name:bytes=b"ttgpu"):
    svc = self.lib.IOServiceGetMatchingService(0, self.lib.IOServiceNameMatching(name))
    if not svc:
      raise RuntimeError(f"no '{name.decode()}' IOService: is the card connected and the TTGPU driver enabled? "
                         "(systemextensionsctl list; ioreg -n ttgpu)")
    conn = ctypes.c_uint()
    try:
      if (kr := self.lib.IOServiceOpen(svc, self.task, 0, ctypes.byref(conn))): raise RuntimeError(f"IOServiceOpen failed: {kr:#x}")
    finally: self.lib.IOObjectRelease(svc)
    self.conn, self.maps = conn.value, []

  def map(self, kind:int) -> tuple[int, int]:
    """kind 0-5: that BAR; kind >= 6: a new DMA buffer of kind bytes. Returns (address, size) in this process."""
    addr, size = ctypes.c_uint64(), ctypes.c_uint64()
    if (kr := self.lib.IOConnectMapMemory64(self.conn, kind, self.task, ctypes.byref(addr), ctypes.byref(size), self.kIOMapAnywhere)):
      raise RuntimeError(f"IOConnectMapMemory64({kind:#x}) failed: {kr:#x}")
    self.maps.append((kind, addr.value))
    return addr.value, size.value

  def close(self):
    for kind, addr in self.maps: self.lib.IOConnectUnmapMemory64(self.conn, kind, self.task, addr)
    self.maps = []
    self.lib.IOServiceClose(self.conn)  # the dext completes and releases this client's DMA buffers

def mmio_write(dst32:memoryview, word:int, data:bytes):
  """Store data at u32 index word of a BAR view, one aligned 32-bit store at a time."""
  data = bytes(data)
  if tail := len(data) % 4:  # read-modify-write the last partial word so the bytes after data are kept
    data += struct.pack("<I", dst32[word + len(data) // 4])[tail:]
  for i, w in enumerate(memoryview(data).cast("I")): dst32[word + i] = w
def mmio_read(src32:memoryview, word:int, n:int) -> bytes:
  return b"".join(struct.pack("<I", src32[word + i]) for i in range(-(-n // 4)))[:n]

class PCIDevice:
  def __init__(self, index=0):
    if index != 0: raise RuntimeError("macOS: the TTGPU driver exposes one device, index 0")
    self.lock = os.open(LOCK_PATH, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o666)
    try: fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
      os.close(self.lock)
      raise RuntimeError("the card is in use by another blackhole-py process") from None
    self.io, self.iatus, self.powered = IOKit(), {}, False
    try:
      addr, size = self.io.map(0)
      if size < TLB_REGS + 0x1000: raise RuntimeError(f"BAR0 is {size:#x} bytes, expected 512 MiB")
      self.bar0 = view_at(addr, size).cast("I")
      addr, size = self.io.map(2)
      self.bar2 = view_at(addr, size).cast("I")
      self.free_tlbs = [t for t in range(TLB_2M_COUNT) if t not in (ARC_TLB, SMI_TLB, DEXT_TLB)]
      self.arc_tlb, self.arc_base = ARC_TLB, None  # the window tt-kmd keeps for itself, used for ARC here
      self.tlb_id, self.tlb_cfg, self.windows = self.free_tlbs.pop(0), None, []
      self.tlb32 = self._window_view(self.tlb_id)
      self._arc_msg(ARC_MSG_ASIC_STATE0)  # tt-kmd blackhole_init_hardware: bring the ASIC to A0
      self.card = os.environ.get("BH_CARD") or self._card()
      if self.card not in ("p100a", "p150a", "p150b"): raise RuntimeError(f"unsupported card {self.card}, only p100a and p150")
      self._set_power(TT_POWER_FLAG_MAX_AI_CLK | TT_POWER_FLAG_MRISC_PHY_WAKEUP | TT_POWER_FLAG_TENSIX_ENABLE)
      self.powered = True
    except BaseException:
      self.io.close(); os.close(self.lock)
      raise

  @property
  def fd(self): raise AttributeError("macOS has no tt-kmd fd; pass the PCIDevice to Sysmem")

  def close(self):
    if self.io is None: return  # already closed (close() and the exit hook can both get here)
    try:
      if self.powered: self.power_off()
    finally:
      for region in list(self.iatus): self._iatu(region, 0, 0, 0)
      self.tlb32 = self.bar0 = self.bar2 = None
      self.io.close(); self.io = None
      os.close(self.lock)  # releases the flock

  def power_off(self):
    self._set_power(0)
    self.powered = False

  # ---- TLB windows (tt-kmd blackhole_configure_tlb_2M) ----

  def _window_view(self, tlb:int) -> memoryview: return self.bar0[tlb * TLB_SIZE // 4:(tlb + 1) * TLB_SIZE // 4]

  def _configure_tlb(self, tlb:int, addr:int, x0:int, y0:int, x1:int, y1:int, mcast:int=0, ordering:int=TT_NOC_ORDERING_STRICT):
    assert addr % TLB_SIZE == 0 and 0 <= tlb < TLB_2M_COUNT
    v = addr >> 21 | x1 << 43 | y1 << 49 | x0 << 55 | y0 << 61 | 0 << 67 | mcast << 69 | ordering << 70
    reg = (TLB_REGS + tlb * TLB_REG_SIZE) // 4
    self.bar0[reg], self.bar0[reg + 1], self.bar0[reg + 2] = v & 0xFFFFFFFF, v >> 32 & 0xFFFFFFFF, v >> 64 & 0xFFFFFFFF
    if tlb < TLB_STRIDED_COUNT: self.bar0[TLB_STRIDED_REGS // 4 + tlb] = 0

  def window(self, core) -> memoryview:
    """u32 view of core's L1 through a TLB of its own, so polling it never retargets the shared one."""
    if not self.free_tlbs: raise RuntimeError("no free 2M TLB windows")
    tlb = self.free_tlbs.pop(0)
    self._configure_tlb(tlb, 0, *core, *core)
    self.windows.append(tlb)
    return self._window_view(tlb)

  def _target(self, core, addr):
    base = addr & -TLB_SIZE
    if self.tlb_cfg != (core, base):
      mcast = isinstance(core[0], tuple)
      (x0, y0), (x1, y1) = core if mcast else (core, core)
      self._configure_tlb(self.tlb_id, base, x0, y0, x1, y1, mcast=int(mcast))
      self.tlb_cfg = (core, base)
    return addr - base

  def write(self, core, addr, data):
    data = memoryview(data).cast("B")
    assert addr % 4 == 0, "MMIO writes must be 4-byte aligned"
    while len(data):
      off = self._target(core, addr)
      n = min(len(data), TLB_SIZE - off)
      mmio_write(self.tlb32, off // 4, data[:n])
      addr, data = addr + n, data[n:]

  def read(self, core, addr, n):
    out = bytearray()
    while len(out) < n:
      at = addr + len(out)
      off = self._target(core, at & ~3)
      k = min(n - len(out), TLB_SIZE - off - (at & 3))
      out += mmio_read(self.tlb32, off // 4, (at & 3) + k)[at & 3:]
    return bytes(out)

  def write32(self, core, addr, v): self.tlb32[self._target(core, addr) // 4] = v
  def read32(self, core, addr): return self.tlb32[self._target(core, addr) // 4]

  # ---- ARC (tt-kmd msgqueue.c, blackhole.c), through the reserved TLB ----

  def _arc_word(self, addr:int) -> int:
    base = addr & -TLB_SIZE
    if self.arc_base != base:
      self._configure_tlb(self.arc_tlb, base, *ARC, *ARC)
      self.arc_base = base
    return (self.arc_tlb * TLB_SIZE + addr - base) // 4
  def _arc_read32(self, addr:int) -> int:
    if (v := self.bar0[self._arc_word(addr)]) == 0xFFFFFFFF:
      raise RuntimeError(f"ARC read of {addr:#x} returned all ones: NoC hung or device gone")
    return v
  def _arc_write32(self, addr:int, v:int): self.bar0[self._arc_word(addr)] = v & 0xFFFFFFFF

  def _card(self) -> str:
    table, data = self._arc_read32(ARC_TELEMETRY_PTR), self._arc_read32(ARC_TELEMETRY_DATA)
    n = self._arc_read32(table + 4)
    assert 0 < n <= 256, f"bad ARC telemetry entry count {n}"
    for i in range(n):
      if (e := self._arc_read32(table + 8 + 4 * i)) & 0xFFFF == TELEMETRY_BOARD_ID:
        kind = self._arc_read32(data + 4 * (e >> 16)) >> 4 & 0xFFFF
        return CARDS.get(kind, f"unknown board type {kind:#x}")
    raise RuntimeError("ARC telemetry has no board id")

  def _arc_msg(self, header:int, payload:tuple[int, ...]=()) -> tuple[int, ...]:
    """Sent by the TTGPU driver (it owns the ARC queue, like tt-kmd); 0x21 is this connection's power vote."""
    try: resp = self.io.arc_msg(header, payload)
    except IOKit.CallError as e: raise RuntimeError(f"ARC message {header & 0xFF:#x} failed in the driver: {e.kr:#x}") from None
    if (status := resp[0] & 0xFF) >= 240: raise RuntimeError(f"ARC message {header & 0xFF:#x} failed with status {status:#x}")
    return resp

  def _set_power(self, flags:int):  # tt-kmd blackhole_set_power_state, power_settings all zero
    self._arc_msg(ARC_MSG_POWER_SETTING | TT_POWER_VALIDITY << 8 | flags << 16)

  # ---- pinned memory: outbound iATU regions (tt-kmd memory.c setup_noc_dma, configure_outbound_atu) ----

  def _iatu(self, region:int, base:int, limit:int, target:int):
    regs = ((IATU_LOWER_BASE, base), (IATU_UPPER_BASE, base >> 32), (IATU_LOWER_TARGET, target), (IATU_UPPER_TARGET, target >> 32),
            (IATU_LOWER_LIMIT, limit), (IATU_UPPER_LIMIT, limit >> 32), (IATU_CTRL1, IATU_INCREASE_REGION_SIZE),
            (IATU_CTRL2, IATU_REGION_EN if limit else 0), (IATU_CTRL3, 0))
    for reg, v in regs: self.bar2[(IATU_BASE + 2 * region * IATU_STRIDE + reg) // 4] = v & 0xFFFFFFFF
    if limit: self.iatus[region] = (base, limit)
    else: self.iatus.pop(region, None)

  def map_segments(self, segments:list[tuple[int, int]]) -> tuple[int, list[int]]:
    """Map DMA segments back to back in NoC space, one iATU region each. Returns (noc address, regions)."""
    free = [r for r in range(IATU_REGIONS) if r not in self.iatus]
    if len(segments) > len(free):
      raise RuntimeError(f"pinned buffer came back in {len(segments)} DMA segments; only {len(free)} free iATU regions")
    base = max((limit + 1 for _, limit in self.iatus.values()), default=0)
    start, regions = base, []
    for (addr, size), region in zip(segments, free):
      self._iatu(region, base, base + size - 1, addr)
      regions.append(region)
      base += size
    return NOC_PCIE_OFFSET + start, regions

  def unmap_regions(self, regions:list[int]):
    for r in regions: self._iatu(r, 0, 0, 0)

class Sysmem:
  """Host memory the device can DMA: an IOBufferMemoryDescriptor the dext allocated and prepared, mapped here.
  It stays prepared until the device is closed (the dext has no per-buffer free)."""
  def __init__(self, dev:PCIDevice, size:int):
    assert size >= DMA_TABLE_SIZE and size % DMA_TABLE_SIZE == 0
    self.dev = dev
    addr, mapped = dev.io.map(size)
    self.size, self.addr, self.mem = size, addr, view_at(addr, size)
    table, segments = self.mem[DMA_TABLE_OFFSET:DMA_TABLE_OFFSET + DMA_TABLE_SIZE].cast("Q"), []
    while table[2 * len(segments) + 1]: segments.append((table[2 * len(segments)], table[2 * len(segments) + 1]))
    table.release()
    self.mem[DMA_TABLE_OFFSET:DMA_TABLE_OFFSET + 16 * (len(segments) + 1)] = bytes(16 * (len(segments) + 1))
    if (covered := sum(n for _, n in segments)) < size: raise RuntimeError(f"DMA segments cover {covered} of {size} bytes")
    self.segments = segments
    self.noc_addr, self.regions = dev.map_segments(segments)

  def close(self):
    self.dev.unmap_regions(self.regions)  # the mapping itself is released when the device closes

# ---- reset: tt-kmd's in-place ASIC reset (RESET_DEVICE ASIC_RESET, then POST_RESET), done through config space ----
PCI_COMMAND, PCI_COMMAND_PARITY = 0x04, 0x40  # tt-kmd uses the parity bit as a reset marker; the chip's reset clears it
INTERFACE_TIMER_CONTROL, INTERFACE_TIMER_TARGET = 0x930, 0x934  # pcie.c pcie_timer_interrupt
INTERFACE_TIMER_EN, INTERFACE_FORCE_PENDING = 0x1, 0x10
TT_VENDOR = 0x1e52

def arc_only(tlb:int=SMI_TLB) -> PCIDevice:
  """A PCIDevice that only talks to ARC, through one TLB window, without A0, power votes or the lock. tlb=SMI_TLB is
  safe next to a running blackhole-py process; close() just releases the mappings."""
  d = PCIDevice.__new__(PCIDevice)
  d.io, d.iatus, d.powered, d.lock = IOKit(), {}, False, None
  addr, size = d.io.map(0); d.bar0 = view_at(addr, size).cast("I")
  d.free_tlbs, d.arc_tlb, d.arc_base, d.windows = [], tlb, None, []
  d.close = lambda: d.io.close()
  return d

def in_use() -> bool:
  with open(LOCK_PATH, "a") as f:
    try: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: return True
    fcntl.flock(f, fcntl.LOCK_UN)
    return False

def pcie_link() -> tuple[tuple[int|None, int|None], tuple[int|None, int|None]]:
  """((gen, width), (max gen, max width)) of the card's link, from the I/O registry (no sysfs on macOS)."""
  try: devs = plistlib.loads(subprocess.run(["ioreg", "-r", "-a", "-c", "IOPCIDevice", "-l"], capture_output=True, check=True).stdout)
  except (subprocess.CalledProcessError, plistlib.InvalidFileException): return (None, None), (None, None)
  def walk(nodes):
    for n in nodes:
      if n.get("vendor-id", b"")[:2] == bytes.fromhex("521e"): return n
      if (r := walk(n.get("IORegistryEntryChildren", []))): return r
  if not (dev := walk(devs if isinstance(devs, list) else [devs])): return (None, None), (None, None)
  status, caps = dev.get("IOPCIExpressLinkStatus"), dev.get("IOPCIExpressLinkCapabilities")
  link = lambda v: (None, None) if v is None else (v & 0xF, v >> 4 & 0x3F)
  return link(status), link(caps)

def _arc_boot_status() -> int:
  """Read-only: ARC boot status through the reserved TLB, without the A0/power messages PCIDevice sends."""
  d = arc_only(ARC_TLB)
  try: return d._arc_read32(ARC_BOOT_STATUS)
  finally: d.close()

def reset(timeout:float=30.0):
  """Reset the ASIC even if ARC is hung (the timer interrupt doesn't need firmware), then restore config space."""
  io = IOKit()
  try:
    saved = [io.cfg_read(off) for off in range(0, 0x40, 4)]  # standard header: command, BARs, interrupt line
    if saved[0] & 0xFFFF != TT_VENDOR: raise RuntimeError(f"config space doesn't look like a Tenstorrent card: {saved[0]:#x}")
    # smi.py -r order: reset the PCIe link first (unsticks a card whose firmware is hung), restore, then the ASIC reset
    try:
      io.reset_link(); time.sleep(0.5)
      for off in range(0x10, 0x28, 4): io.cfg_write(off, saved[off // 4])
      io.cfg_write(0x3C, saved[0x3C // 4]); io.cfg_write(PCI_COMMAND, saved[1] & 0xFFFF & ~PCI_COMMAND_PARITY, 2)
      print("PCIe link reset done")
    except RuntimeError as e: print(f"PCIe link reset failed, continuing: {e}")
    io.cfg_write(PCI_COMMAND, (saved[1] & 0xFFFF) | PCI_COMMAND_PARITY, 2)
    io.cfg_write(INTERFACE_TIMER_TARGET, 1)
    io.cfg_write(INTERFACE_TIMER_CONTROL, INTERFACE_TIMER_EN | INTERFACE_FORCE_PENDING)
    print("reset issued")
    time.sleep(2)
    deadline = time.monotonic() + timeout
    while True:
      try:
        if io.cfg_read(0) & 0xFFFF == TT_VENDOR and not io.cfg_read(PCI_COMMAND, 2) & PCI_COMMAND_PARITY: break
      except RuntimeError: pass  # link retraining
      if time.monotonic() > deadline: raise TimeoutError("reset marker never cleared; power-cycle the enclosure")
      time.sleep(0.05)
    # pci_restore_state order: BARs and the rest of the header first, command last
    for off in range(0x10, 0x28, 4): io.cfg_write(off, saved[off // 4])
    io.cfg_write(0x3C, saved[0x3C // 4])
    io.cfg_write(PCI_COMMAND, saved[1] & 0xFFFF & ~PCI_COMMAND_PARITY, 2)
  finally: io.close()
  deadline = time.monotonic() + 15
  while not (status := _arc_boot_status()) & 1:  # ARC_BOOT_STATUS_READY_FOR_MSG
    if time.monotonic() > deadline: raise TimeoutError(f"ARC didn't come back after reset (boot status {status:#x})")
    time.sleep(0.05)
  print(f"card back, ARC boot status {status:#x}")

if __name__ == "__main__":
  import sys
  if sys.argv[1:] == ["-r"]: reset()
  else: print(f"usage: {sys.argv[0]} -r   # reset the card (macOS smi.py -r)")
