import ctypes, ctypes.util, mmap, os, sys

TLB_SIZE = 1 << 21
SUPPORTED = ("p100a", "p150a", "p150b")
ARC = (8, 0)
TELEMETRY_DATA, TELEMETRY_PTR = 0x80030430, 0x80030434
TELEMETRY_BOARD_ID = 1
CARDS = {0x36: "p100", 0x40: "p150a", 0x41: "p150b", 0x42: "p150c", 0x43: "p100a"}  # telemetry board id -> name

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int64]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

def view_at(addr:int, n:int) -> memoryview: return memoryview((ctypes.c_uint8 * n).from_address(addr)).cast("B")

def map_memory(size:int, fd:int=-1, offset:int=0, flags:int=mmap.MAP_SHARED) -> int:
  if fd == -1: flags |= mmap.MAP_ANONYMOUS
  if (addr := libc.mmap(None, size, mmap.PROT_READ | mmap.PROT_WRITE, flags, fd, offset)) in (None, 2**64 - 1):
    raise OSError(ctypes.get_errno(), f"mmap of {size} bytes failed: {os.strerror(ctypes.get_errno())}")
  return addr

class Py_buffer(ctypes.Structure):
  _fields_ = [("buf", ctypes.c_void_p), ("obj", ctypes.c_void_p), ("len", ctypes.c_ssize_t), ("itemsize", ctypes.c_ssize_t),
              ("readonly", ctypes.c_int), ("ndim", ctypes.c_int), ("format", ctypes.c_char_p), ("shape", ctypes.c_void_p),
              ("strides", ctypes.c_void_p), ("suboffsets", ctypes.c_void_p), ("internal", ctypes.c_void_p)]

def buffer_address(obj) -> int:
  view = Py_buffer()
  ctypes.pythonapi.PyObject_GetBuffer(ctypes.py_object(obj), ctypes.byref(view), 0)
  try: return view.buf or 0
  finally: ctypes.pythonapi.PyBuffer_Release(ctypes.byref(view))

def rect(core) -> tuple[int, int, int, int, int]:
  # (x, y) or a multicast ((x0, y0), (x1, y1)) -> (x0, y0, x1, y1, mcast)
  return (*core[0], *core[1], 1) if isinstance(core[0], tuple) else (*core, *core, 0)

def telemetry_table(rd) -> dict[int, int]:
  # ARC telemetry: tag -> address of its value. rd reads one ARC word.
  table, data = rd(TELEMETRY_PTR), rd(TELEMETRY_DATA)
  if not table or rd(table) >> 16 & 0xFF > 1 or not 0 < (n := rd(table + 4)) <= 256: raise OSError("bad ARC telemetry table")
  return {e & 0xFFFF: data + 4 * (e >> 16) for e in (rd(table + 8 + 4 * i) for i in range(n))}

class Card:
  # A backend sets name and tlb_id and implements power(flags), window(core) -> u32-indexed view of a core's L1,
  # alloc_host(size) -> HostMemory (mem, addr, size, noc_addr, close()), close(), and the TLB primitives below.
  # Backends with can_pin also implement pin(va, size, read_only) -> NoC address and unpin(va, size).
  can_pin, tlb_cfg = False, None

  def _configure(self, tlb:int, core, addr:int): raise NotImplementedError  # point TLB `tlb` at core (or rect), addr
  def _wread(self, off:int, n:int) -> bytes: raise NotImplementedError     # access at `off` in TLB tlb_id
  def _wwrite(self, off:int, data): raise NotImplementedError
  def _wread32(self, off:int) -> int: raise NotImplementedError
  def _wwrite32(self, off:int, v:int): raise NotImplementedError

  def _target(self, core, addr:int) -> int:
    base = addr & -TLB_SIZE
    if self.tlb_cfg != (core, base):
      self._configure(self.tlb_id, core, base)
      self.tlb_cfg = (core, base)
    return addr - base

  def write(self, core, addr:int, data):
    data = memoryview(data).cast("B")
    while len(data):
      off = self._target(core, addr)
      n = min(len(data), TLB_SIZE - off)
      self._wwrite(off, data[:n])
      addr, data = addr + n, data[n:]

  def read(self, core, addr:int, n:int) -> bytes:
    out = bytearray()
    while len(out) < n:
      off = self._target(core, addr + len(out))
      out += self._wread(off, min(n - len(out), TLB_SIZE - off))
    return bytes(out)

  def write32(self, core, addr:int, v:int): self._wwrite32(self._target(core, addr), v)
  def read32(self, core, addr:int) -> int: return self._wread32(self._target(core, addr))
  def arc_read32(self, addr:int) -> int: return self.read32(ARC, addr)

  def telemetry(self, tag:int) -> int:
    if (addr := telemetry_table(self.arc_read32).get(tag)) is None: raise RuntimeError(f"ARC telemetry has no tag {tag}")
    return self.arc_read32(addr)

class Monitor:
  # Read-only NoC access for tools like smi that run beside the process holding the card. A backend implements
  # noc_read(addr, xy) -> u32, in_use() and close(); reads raise OSError when the card is gone.
  table: dict[int, int] | None = None

  def noc_read(self, addr:int, xy=ARC) -> int: raise NotImplementedError

  def telemetry(self, tags:dict[str, int]) -> dict[str, int | None]:
    if self.table is None: self.table = telemetry_table(self.noc_read)
    return {k: self.noc_read(self.table[t]) if t in self.table else None for k, t in tags.items()}

  def board_type(self) -> str:
    kind = self.telemetry({"board": TELEMETRY_BOARD_ID})["board"]
    return "?" if kind is None else CARDS.get(kind >> 4 & 0xFFFF, f"{kind >> 4 & 0xFFFF:#x}")

def open_card(index:int=0) -> Card:
  if sys.platform == "darwin": from pci_macos import MacCard as backend
  else: from pci_linux import LinuxCard as backend
  return backend(index)

def open_monitor(index:int=0) -> Monitor:
  if sys.platform == "darwin": from pci_macos import MacMonitor as backend
  else: from pci_linux import LinuxMonitor as backend
  return backend(index)
