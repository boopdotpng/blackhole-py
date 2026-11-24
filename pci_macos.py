import fcntl, os, socket, struct, subprocess, sys, tempfile, time
from pci import SUPPORTED, TLB_SIZE, libc, map_memory, view_at

APP = "/Applications/TTGPU.app/Contents/MacOS/TTGPU"
SOCK_PATH = os.environ.get("TTGPU_SOCK", os.path.join(tempfile.gettempdir(), "ttgpu.sock"))
MAP_BAR, MAP_SYSMEM_FD, CFG_READ, CFG_WRITE, RESET, MMIO_READ, MMIO_WRITE, NOC_READ32 = 1, 2, 3, 4, 5, 6, 7, 13
REQ, RESP = struct.Struct("<BIIQQQ"), struct.Struct("<BQQ")
LOCK_PATH = os.path.join(tempfile.gettempdir(), "blackhole-py-0.lock")

TLB_2M_COUNT, TLB_REG_SIZE, TLB_REGS = 202, 12, 0x1FC00000
TLB_STRIDED_COUNT, TLB_STRIDED_REGS = 32, TLB_REGS + (TLB_2M_COUNT + 8) * TLB_REG_SIZE
ARC_TLB, NOC_TLB, DEXT_TLB = TLB_2M_COUNT - 1, TLB_2M_COUNT - 2, TLB_2M_COUNT - 3
IATU_BASE, IATU_STRIDE, IATU_REGIONS = 0x1000, 0x100, 16
IATU_CTRL1, IATU_CTRL2, IATU_LOWER_BASE, IATU_UPPER_BASE, IATU_LOWER_LIMIT = 0x00, 0x04, 0x08, 0x0C, 0x10
IATU_LOWER_TARGET, IATU_UPPER_TARGET, IATU_CTRL3, IATU_UPPER_LIMIT = 0x14, 0x18, 0x1C, 0x20
IATU_INCREASE_REGION_SIZE, IATU_REGION_EN = 1 << 13, 1 << 31
NOC_PCIE_OFFSET = 4 << 58
ARC = (8, 0)
ARC_BOOT_STATUS, ARC_MSG_QCB_PTR, ARC_TELEMETRY_DATA, ARC_TELEMETRY_PTR = 0x80030408, 0x8003042C, 0x80030430, 0x80030434
ARC_MSI_FIFO, ARC_MSG_QUEUE_HEADER = 0x800B0000, 32
ARC_MSG_ASIC_STATE0, ARC_MSG_POWER_SETTING = 0xA0, 0x21
TELEMETRY_BOARD_ID = 1
CARDS = {0x36: "p100", 0x40: "p150a", 0x41: "p150b", 0x42: "p150c", 0x43: "p100a"}
POWER_VALIDITY = 15

class Server:
  def __init__(self):
    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try: self._connect()
    except BaseException:
      self.sock.close()
      raise
    for opt in (socket.SO_SNDBUF, socket.SO_RCVBUF): self.sock.setsockopt(socket.SOL_SOCKET, opt, 8 << 20)

  def _connect(self):
    for i in range(100):
      try: return self.sock.connect(SOCK_PATH)
      except (ConnectionRefusedError, FileNotFoundError):
        if i == 0:
          if not os.path.exists(APP): raise RuntimeError(f"{APP} not found: install it with macos/ttgpu-dext/install.sh") from None
          with open(os.path.join(tempfile.gettempdir(), "ttgpu-server.log"), "ab") as log:
            subprocess.Popen([APP, "server", SOCK_PATH], stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        time.sleep(0.05)
    raise RuntimeError(f"couldn't connect to the TTGPU server at {SOCK_PATH}")

  def _recvall(self, n:int) -> bytes:
    data = bytearray()
    while len(data) < n:
      if not (chunk := self.sock.recv(n - len(data))): raise ConnectionError("TTGPU server closed the connection (card unplugged or system slept?)")
      data += chunk
    return bytes(data)

  def post(self, cmd:int, *args:int, bar:int=0, payload:bytes=b""):
    try: self.sock.sendall(REQ.pack(cmd, 0, bar, *(*args, 0, 0, 0)[:3]) + payload)
    except (BrokenPipeError, ConnectionResetError):
      self._check(cmd, self._recvall(RESP.size))
      raise

  def _check(self, cmd:int, resp:bytes) -> tuple[int, int]:
    status, r0, r1 = RESP.unpack(resp)
    if status: raise RuntimeError(f"TTGPU server: command {cmd} failed: {self._recvall(r0).decode(errors='replace')}")
    return r0, r1

  def rpc(self, cmd:int, *args:int, bar:int=0, payload:bytes=b"") -> tuple[int, int]:
    self.post(cmd, *args, bar=bar, payload=payload)
    return self._check(cmd, self._recvall(RESP.size))

  def map_bar(self, bar:int) -> int: return self.rpc(MAP_BAR, bar=bar)[1]
  def cfg_read(self, off:int, size:int=4) -> int: return self.rpc(CFG_READ, off, size)[0]
  def cfg_write(self, off:int, val:int, size:int=4): self.rpc(CFG_WRITE, off, size, val)
  def reset_link(self): self.rpc(RESET)
  def write(self, bar:int, off:int, data:bytes): self.post(MMIO_WRITE, off, len(data), bar=bar, payload=bytes(data))
  def read(self, bar:int, off:int, n:int) -> bytes:
    self.rpc(MMIO_READ, off, n, bar=bar)
    return self._recvall(n)
  def write32(self, bar:int, off:int, v:int): self.write(bar, off, struct.pack("<I", v & 0xFFFFFFFF))
  def read32(self, bar:int, off:int) -> int: return struct.unpack("<I", self.read(bar, off, 4))[0]

  def alloc_dma(self, size:int) -> tuple[int, int, int]:
    self.post(MAP_SYSMEM_FD, size)
    msg, fds, _, _ = socket.recv_fds(self.sock, RESP.size, 1)
    msg += self._recvall(RESP.size - len(msg)) if msg and len(msg) < RESP.size else b""
    if not msg: raise ConnectionError("TTGPU server closed the connection")
    try:
      r0, r1 = self._check(MAP_SYSMEM_FD, msg)
      if len(fds) != 1: raise RuntimeError(f"TTGPU server sent {len(fds)} fds for a DMA buffer")
    except BaseException:
      for fd in fds: os.close(fd)
      raise
    return fds[0], r0, r1

  def close(self): self.sock.close()

def lock(blocking:bool=False) -> int | None:
  fd = os.open(LOCK_PATH, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o666)
  try: fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
  except BlockingIOError:
    os.close(fd)
    return None
  return fd

class Noc:
  def __init__(self):
    self.io = Server()
    try: self.io.map_bar(0)
    except BaseException:
      self.io.close()
      raise
  def read32(self, addr:int, xy=ARC) -> int: return self.io.rpc(NOC_READ32, addr, xy[0] | xy[1] << 8)[0]
  def close(self): self.io.close()

class Window:
  def __init__(self, io:Server, base:int): self.io, self.base = io, base
  def __getitem__(self, i:int) -> int: return self.io.read32(0, self.base + 4 * i)
  def __setitem__(self, i:int, v:int): self.io.write32(0, self.base + 4 * i, v)

class Card:
  def __init__(self, index:int=0):
    if index != 0: raise RuntimeError("macOS: the TTGPU driver exposes one device, index 0")
    if (lk := lock()) is None: raise RuntimeError("the card is in use by another process")
    self.lock, self.iatus, self.powered, self.io = lk, {}, False, None
    try:
      self.io = Server()
      if (size := self.io.map_bar(0)) < TLB_REGS + 0x1000: raise RuntimeError(f"BAR0 is {size:#x} bytes, expected 512 MiB")
      self.io.map_bar(2)
      self.free_tlbs = [t for t in range(TLB_2M_COUNT) if t not in (ARC_TLB, NOC_TLB, DEXT_TLB)]
      self.arc_base, self.tlb_cfg = None, None
      self.tlb_id = self.free_tlbs.pop(0)
      self._arc_msg(ARC_MSG_ASIC_STATE0)
      self.name = os.environ.get("BH_CARD") or self._card()
      if self.name not in SUPPORTED: raise RuntimeError(f"unsupported card {self.name}, expected one of {SUPPORTED}")
      self.power(7)
    except BaseException:
      self.close()
      raise

  def close(self):
    try:
      if self.io is not None and self.powered: self.power(0)
    finally:
      try:
        for region in list(self.iatus): self._iatu(region, 0, 0, 0)
      except OSError: pass
      if self.io is not None: self.io.close()
      if self.lock is not None: os.close(self.lock)
      self.io = self.lock = None

  def power(self, flags:int):
    self._arc_msg(ARC_MSG_POWER_SETTING | POWER_VALIDITY << 8 | flags << 16)
    self.powered = bool(flags)

  def _configure_tlb(self, tlb:int, addr:int, x0:int, y0:int, x1:int, y1:int, mcast:int=0):
    assert addr % TLB_SIZE == 0 and 0 <= tlb < TLB_2M_COUNT
    v = addr >> 21 | x1 << 43 | y1 << 49 | x0 << 55 | y0 << 61 | mcast << 69 | 1 << 70
    self.io.write(0, TLB_REGS + tlb * TLB_REG_SIZE, struct.pack("<3I", v & 0xFFFFFFFF, v >> 32 & 0xFFFFFFFF, v >> 64))
    if tlb < TLB_STRIDED_COUNT: self.io.write32(0, TLB_STRIDED_REGS + 4 * tlb, 0)

  def window(self, core) -> Window:
    if not self.free_tlbs: raise RuntimeError("no free 2M TLB windows")
    tlb = self.free_tlbs.pop(0)
    self._configure_tlb(tlb, 0, *core, *core)
    return Window(self.io, tlb * TLB_SIZE)

  def _target(self, core, addr) -> int:
    base = addr & -TLB_SIZE
    if self.tlb_cfg != (core, base):
      mcast = isinstance(core[0], tuple)
      (x0, y0), (x1, y1) = core if mcast else (core, core)
      self._configure_tlb(self.tlb_id, base, x0, y0, x1, y1, int(mcast))
      self.tlb_cfg = (core, base)
    return self.tlb_id * TLB_SIZE + addr - base

  def write(self, core, addr, data):
    assert addr % 4 == 0, "MMIO writes must be 4-byte aligned"
    data = bytes(memoryview(data).cast("B"))
    if tail := len(data) % 4:
      assert not isinstance(core[0], tuple), "multicast writes must be a multiple of 4 bytes"
      last = addr + len(data) - tail
      data += struct.pack("<I", self.read32(core, last))[tail:]
    while data:
      off = self._target(core, addr)
      n = min(len(data), TLB_SIZE - off % TLB_SIZE)
      self.io.write(0, off, data[:n])
      addr, data = addr + n, data[n:]

  def read(self, core, addr, n) -> bytes:
    out, start, end = bytearray(), addr & ~3, -(-(addr + n) // 4) * 4
    while start + len(out) < end:
      off = self._target(core, start + len(out))
      out += self.io.read(0, off, min(end - start - len(out), TLB_SIZE - off % TLB_SIZE))
    return bytes(out[addr - start:addr - start + n])

  def write32(self, core, addr, v): self.io.write32(0, self._target(core, addr), v)
  def read32(self, core, addr): return self.io.read32(0, self._target(core, addr))

  def _arc_off(self, addr:int) -> int:
    base = addr & -TLB_SIZE
    if self.arc_base != base:
      self._configure_tlb(ARC_TLB, base, *ARC, *ARC)
      self.arc_base = base
    return ARC_TLB * TLB_SIZE + addr - base

  def _arc_read32(self, addr:int) -> int:
    if (v := self.io.read32(0, self._arc_off(addr))) == 0xFFFFFFFF:
      raise RuntimeError(f"ARC read of {addr:#x} returned all ones: NoC hung or device gone")
    return v

  def _arc_write32(self, addr:int, v:int): self.io.write32(0, self._arc_off(addr), v)

  def _card(self) -> str:
    table, data = self._arc_read32(ARC_TELEMETRY_PTR), self._arc_read32(ARC_TELEMETRY_DATA)
    assert 0 < (n := self._arc_read32(table + 4)) <= 256, f"bad ARC telemetry entry count {n}"
    for i in range(n):
      if (e := self._arc_read32(table + 8 + 4 * i)) & 0xFFFF == TELEMETRY_BOARD_ID:
        kind = self._arc_read32(data + 4 * (e >> 16)) >> 4 & 0xFFFF
        return CARDS.get(kind, f"unknown board type {kind:#x}")
    raise RuntimeError("ARC telemetry has no board id")

  def _arc_msg(self, header:int, payload:tuple[int, ...]=(), timeout:float=1.0) -> tuple[int, ...]:
    deadline = time.monotonic() + 0.5
    while not self._arc_read32(ARC_BOOT_STATUS) & 1:
      if time.monotonic() > deadline: raise RuntimeError("ARC isn't ready for messages")
      time.sleep(0.001)
    qcb = self._arc_read32(ARC_MSG_QCB_PTR)
    q, entries = self._arc_read32(qcb), self._arc_read32(qcb + 4) & 0xFF
    if not entries: raise RuntimeError("ARC message queue has no entries")
    wrap, responses = 2 * entries, q + ARC_MSG_QUEUE_HEADER + entries * 32

    def pop() -> tuple[int, ...] | None:
      rptr, wptr = self._arc_read32(q + 0x04), self._arc_read32(q + 0x14)
      if (wptr - rptr) % wrap == 0: return None
      slot = responses + rptr % entries * 32
      resp = tuple(self._arc_read32(slot + 4 * i) for i in range(8))
      self._arc_write32(q + 0x04, (rptr + 1) % wrap)
      return resp

    for _ in range(entries):
      if pop() is None: break
    wptr, rptr = self._arc_read32(q + 0x00), self._arc_read32(q + 0x10)
    if (wptr - rptr) % wrap >= entries: raise RuntimeError("ARC request queue is full")
    slot = q + ARC_MSG_QUEUE_HEADER + wptr % entries * 32
    for i, w in enumerate((header, *payload, 0, 0, 0, 0, 0, 0, 0)[:8]): self._arc_write32(slot + 4 * i, w)
    self._arc_write32(q + 0x00, (wptr + 1) % wrap)
    self._arc_write32(ARC_MSI_FIFO, 0)
    deadline = time.monotonic() + timeout
    while (resp := pop()) is None:
      if time.monotonic() > deadline: raise TimeoutError(f"ARC message {header & 0xFF:#x} timed out")
      time.sleep(0.0001)
    if (status := resp[0] & 0xFF) >= 240: raise RuntimeError(f"ARC message {header & 0xFF:#x} failed with status {status:#x}")
    return resp

  def _iatu(self, region:int, base:int, limit:int, target:int):
    regs = ((IATU_LOWER_BASE, base), (IATU_UPPER_BASE, base >> 32), (IATU_LOWER_TARGET, target), (IATU_UPPER_TARGET, target >> 32),
            (IATU_LOWER_LIMIT, limit), (IATU_UPPER_LIMIT, limit >> 32), (IATU_CTRL1, IATU_INCREASE_REGION_SIZE),
            (IATU_CTRL2, IATU_REGION_EN if limit else 0), (IATU_CTRL3, 0))
    for reg, v in regs: self.io.write32(2, IATU_BASE + 2 * region * IATU_STRIDE + reg, v)
    if limit: self.iatus[region] = (base, limit)
    else: self.iatus.pop(region, None)

  def map_segments(self, segments:list[tuple[int, int]]) -> tuple[int, list[int]]:
    free = [r for r in range(IATU_REGIONS) if r not in self.iatus]
    if len(segments) > len(free):
      raise RuntimeError(f"pinned buffer came back in {len(segments)} DMA segments; only {len(free)} free iATU regions")
    start = base = max((limit + 1 for _, limit in self.iatus.values()), default=0)
    for (addr, size), region in zip(segments, free):
      self._iatu(region, base, base + size - 1, addr)
      base += size
    return NOC_PCIE_OFFSET + start, free[:len(segments)]

  def unmap_regions(self, regions:list[int]):
    for r in regions: self._iatu(r, 0, 0, 0)

class HostMemory:
  def __init__(self, card:Card, size:int):
    self.card, self.addr = card, None
    fd, self.size, _ = card.io.alloc_dma(size)
    try: self.addr = map_memory(self.size, fd)
    finally: os.close(fd)
    try:
      self.mem = view_at(self.addr, self.size)
      table, segments = self.mem[:8192].cast("Q"), []
      while table[2 * len(segments) + 1]: segments.append((table[2 * len(segments)], table[2 * len(segments) + 1]))
      table.release()
      self.mem[:16 * (len(segments) + 1)] = bytes(16 * (len(segments) + 1))
      if (covered := sum(n for _, n in segments)) < size: raise RuntimeError(f"DMA segments cover {covered} of {size} bytes")
      self.noc_addr, self.regions = card.map_segments(segments)
    except BaseException:
      libc.munmap(self.addr, self.size)
      self.addr = None
      raise

  def close(self):
    if self.addr is None: return
    try:
      if self.card.io is not None: self.card.unmap_regions(self.regions)
    finally:
      libc.munmap(self.addr, self.size)
      self.addr = None

PCI_COMMAND, PCI_COMMAND_PARITY, PCI_CAP_PTR, PCI_CAP_EXP, PCI_EXP_DEVCTL, PCI_EXP_DEVCTL2 = 0x04, 0x40, 0x34, 0x10, 0x08, 0x28
INTERFACE_TIMER_CONTROL, INTERFACE_TIMER_TARGET = 0x930, 0x934
INTERFACE_TIMER_EN, INTERFACE_FORCE_PENDING = 0x1, 0x10
TT_VENDOR = 0x1e52

def _arc_boot_status() -> int:
  noc = Noc()
  try:
    if (v := noc.read32(ARC_BOOT_STATUS)) == 0xFFFFFFFF: raise RuntimeError("ARC boot status reads all ones")
    return v
  finally: noc.close()

def _pcie_cap(io:Server) -> int:
  cap = io.cfg_read(PCI_CAP_PTR, 1)
  while cap and io.cfg_read(cap, 1) != PCI_CAP_EXP: cap = io.cfg_read(cap + 1, 1)
  return cap

def reset(timeout:float=30.0, force:bool=False):
  if (lk := lock()) is None and not force:
    raise RuntimeError("the card is in use by another process")
  try: _reset(timeout)
  finally:
    if lk is not None: os.close(lk)

def _reset(timeout:float):
  io = Server()
  def restore(command:int):
    for off in range(0x10, 0x28, 4): io.cfg_write(off, saved[off // 4])
    io.cfg_write(0x3C, saved[0x3C // 4])
    for off, v in devctl.items(): io.cfg_write(off, v, 2)
    io.cfg_write(PCI_COMMAND, command, 2)
  try:
    saved = [io.cfg_read(off) for off in range(0, 0x40, 4)]
    if saved[0] & 0xFFFF != TT_VENDOR: raise RuntimeError(f"config space doesn't look like a Tenstorrent card: {saved[0]:#x}")
    cap = _pcie_cap(io)
    devctl = {off: io.cfg_read(off, 2) for off in (cap + PCI_EXP_DEVCTL, cap + PCI_EXP_DEVCTL2)} if cap else {}
    command = saved[1] & 0xFFFF & ~PCI_COMMAND_PARITY
    try:
      io.reset_link()
      time.sleep(0.5)
      restore(command)
      print("PCIe link reset done")
    except RuntimeError as e: print(f"PCIe link reset failed, continuing: {e}")
    io.cfg_write(PCI_COMMAND, command | PCI_COMMAND_PARITY, 2)
    io.cfg_write(INTERFACE_TIMER_TARGET, 1)
    io.cfg_write(INTERFACE_TIMER_CONTROL, INTERFACE_TIMER_EN | INTERFACE_FORCE_PENDING)
    print("reset issued")
    time.sleep(2)
    deadline = time.monotonic() + timeout
    while True:
      try:
        if io.cfg_read(0) & 0xFFFF == TT_VENDOR and not io.cfg_read(PCI_COMMAND, 2) & PCI_COMMAND_PARITY: break
      except RuntimeError: pass
      if time.monotonic() > deadline: raise TimeoutError("reset marker never cleared; power-cycle the enclosure")
      time.sleep(0.05)
    restore(command)
  finally: io.close()
  deadline = time.monotonic() + 15
  while True:
    try: status = _arc_boot_status()
    except RuntimeError: status = 0
    if status & 1: break
    if time.monotonic() > deadline: raise TimeoutError(f"ARC didn't come back after reset (boot status {status:#x})")
    time.sleep(0.05)
  print(f"card back, ARC boot status {status:#x}")

def park(force:bool=False):
  if (lk := lock()) is None and not force: raise RuntimeError("the card is in use by another process")
  card = Card.__new__(Card)
  card.io, card.arc_base, card.lock = Server(), None, lk
  try:
    card.io.map_bar(0)
    card._arc_msg(ARC_MSG_POWER_SETTING | POWER_VALIDITY << 8)
  finally:
    card.io.close()
    if lk is not None: os.close(lk)

def pcie_link(io:Server|None=None) -> tuple[tuple[int, int], tuple[int, int]]:
  own = io is None
  io = Server() if own else io
  try:
    if not (cap := _pcie_cap(io)): return (None, None), (None, None)
    lcap, lsta = io.cfg_read(cap + 0x0C), io.cfg_read(cap + 0x12, 2)
    return (lsta & 0xF, lsta >> 4 & 0x3F), (lcap & 0xF, lcap >> 4 & 0x3F)
  finally:
    if own: io.close()

if __name__ == "__main__":
  if sys.argv[1:] == ["-r"]: reset()
  else: print(f"usage: {sys.argv[0]} -r")
