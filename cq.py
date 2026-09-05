from dataclasses import dataclass
from enum import IntEnum
from struct import Struct
from typing import ClassVar
import os, time
from fw.consts import Core
from pcie import TLBWindow

Rect = tuple[Core, Core]

ALIGN = 64; MAX_WRITE_SIZE = 16 * 1024; MAX_RECORD_SIZE = 64 * 1024; PAGE_SIZE = 4096

CQ_STATE = 0x1000
PREFETCH_DOORBELL = CQ_STATE
PREFETCH_PCIE_BASE = CQ_STATE + 0x08
PREFETCH_READ_PTR = CQ_STATE + 0x0C
PREFETCH_DISPATCH_READ = CQ_STATE + 0x10
DISPATCH_PUBLISHED = CQ_STATE
DRAM_BRISC_READY = CQ_STATE + 8
DRAM_NCRISC_READY = CQ_STATE + 0xC
HOST_ISSUE_SIZE = 4 << 20
HOST_COMPLETION_SIZE = PAGE_SIZE
CQ_BREADCRUMB = CQ_STATE + 0xA0
CQ_BREADCRUMB_STRUCT = Struct("<5I")
CQ_BREADCRUMB_STAGES = {
  0x100: "prefetch boot",
  0x102: "prefetch read header",
  0x103: "prefetch record",
  0x104: "prefetch wait dispatch space",
  0x105: "prefetch copy to dispatch",
  0x106: "prefetch advance issue",
  0x107: "prefetch publish dispatch",
  0x200: "dispatch boot",
  0x201: "dispatch wait published",
  0x202: "dispatch command",
  0x203: "dispatch wait DRAM idle",
  0x204: "dispatch enqueue DRAM",
  0x205: "dispatch unicast",
  0x206: "dispatch multicast",
  0x208: "dispatch wait workers",
  0x209: "dispatch command done",
  0x2FF: "dispatch bad command",
  0x300: "DRAM BRISC boot",
  0x301: "DRAM BRISC wait published",
  0x302: "DRAM BRISC command",
  0x303: "DRAM BRISC copy descriptor",
  0x304: "DRAM BRISC bank",
  0x305: "DRAM BRISC device to host",
  0x306: "DRAM BRISC host to device",
  0x307: "DRAM BRISC wait NCRISC",
  0x308: "DRAM BRISC publish",
  0x309: "DRAM BRISC signal",
  0x3FF: "DRAM BRISC bad command",
  0x400: "DRAM NCRISC boot",
  0x401: "DRAM NCRISC wait published",
  0x402: "DRAM NCRISC command",
  0x403: "DRAM NCRISC copy descriptor",
  0x404: "DRAM NCRISC bank",
  0x405: "DRAM NCRISC device to host",
  0x406: "DRAM NCRISC host to device",
  0x409: "DRAM NCRISC signal",
  0x4FF: "DRAM NCRISC bad command",
}

class Op(IntEnum):
  PAD = 0
  UNICAST_WRITE = 1
  MCAST_WRITE = 2
  RUN = 3
  SIGNAL = 5
  DRAM_COPY = 7

class PacketLayout:
  HEADER = Struct("<BxHIII")
  UNICAST_TARGET = Struct("<I")
  MCAST_TARGET = Struct("<II")

  RUN_TARGETS = HEADER.size + 8

@dataclass(frozen=True)
class Timestamp:
  """A device clock value decoded from an HCQSignal's field at +8."""
  cycles: int
  STRUCT: ClassVar[Struct] = Struct("<Q")

  @classmethod
  def unpack(cls, data): return cls(*cls.STRUCT.unpack(data))

def _align(value: int): return (value + ALIGN - 1) & -ALIGN

def noc_coord(core: Core):
  x, y = core
  if any(type(value) is not int or not 0 <= value < 64 for value in core):
    raise ValueError("NoC coordinate components must be integers in [0, 63]")
  return x | y << 6

def _check_mcast_endpoint(core: Core):
  if core[0] in (8, 9): raise ValueError("multicast start/end cannot use NoC columns 8 or 9")

def mcast_coords(rect: Rect):
  start, end = rect
  _check_mcast_endpoint(start); _check_mcast_endpoint(end)
  if start[0] > end[0] or start[1] > end[1]: raise ValueError("multicast start must precede end")
  return noc_coord(start), noc_coord(end)

def rectangles(cores):
  rows = {}
  for x, y in cores: rows.setdefault(y, []).append(x)
  active, result, previous_y = {}, [], None
  for y in sorted(rows):
    runs = []
    for x in sorted(rows[y]):
      if runs and x == runs[-1][1] + 1:
        runs[-1] = (runs[-1][0], x)
      else:
        runs.append((x, x))
    if previous_y is None or y != previous_y + 1:
      result.extend(active.values()); active = {}
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

def _payload(data: bytes):
  if not 0 < len(data) <= MAX_WRITE_SIZE:
    raise ValueError(f"write payload size must be in [1, {MAX_WRITE_SIZE}]")
  return data

def _write_record(op: Op, targets: bytes, target_count: int, address: int,
                  data_size: int, payload: bytes):
  target_end = PacketLayout.HEADER.size + len(targets)
  payload_start = _align(target_end)
  total_size = _align(payload_start + len(payload))
  if total_size > MAX_RECORD_SIZE: raise ValueError("CQ record exceeds the 64 KiB staging buffer")
  header = PacketLayout.HEADER.pack(op, target_count, total_size, address, data_size)
  return header + targets + bytes(payload_start - target_end) + payload + bytes(total_size - payload_start - len(payload))

@dataclass(frozen=True)
class UnicastWrite:
  cores: tuple[Core, ...]
  addr: int
  data: tuple[bytes, ...]

  def lower(self) -> bytes:
    cores = tuple(self.cores)
    targets = b"".join(PacketLayout.UNICAST_TARGET.pack(noc_coord(core)) for core in cores)
    blobs = tuple(_payload(blob) for blob in self.data)
    size = len(blobs[0])
    stride = _align(size)
    payload = b"".join(blob.ljust(stride, b"\0") for blob in blobs)
    return _write_record(Op.UNICAST_WRITE, targets, len(cores), self.addr, size, payload)

@dataclass(frozen=True)
class McastWrite:
  rects: tuple[Rect, ...]
  addr: int
  data: bytes

  def lower(self) -> bytes:
    rects = tuple(self.rects)
    data = _payload(self.data)
    targets = b"".join(PacketLayout.MCAST_TARGET.pack(*mcast_coords(rect)) for rect in rects)
    return _write_record(Op.MCAST_WRITE, targets, len(rects), self.addr, len(data), data)

@dataclass(frozen=True)
class Run:
  cores: tuple[Core, ...]

  def lower(self) -> bytes:
    cores = tuple(self.cores)
    rects = rectangles(cores)
    targets = b"".join(
      PacketLayout.MCAST_TARGET.pack(*mcast_coords(rect)) for rect in rects
    )
    total_size = _align(PacketLayout.RUN_TARGETS + len(targets))
    header = PacketLayout.HEADER.pack(
      Op.RUN, len(rects), total_size, 0, len(cores),
    )
    return (header + bytes(8) + targets).ljust(total_size, b"\0")

@dataclass(frozen=True)
class Signal:
  """Set one HCQ-shaped 64-bit signal and its timestamp."""
  addr: int
  value: int

  def lower(self) -> bytes:
    if not 0 <= self.addr < 1 << 64:
      raise ValueError("signal address must fit in 64 bits")
    if not 0 <= self.value < 1 << 64:
      raise ValueError("signal value must fit in 64 bits")
    header = PacketLayout.HEADER.pack(
      Op.SIGNAL, 0, ALIGN, self.addr & 0xFFFFFFFF,
      self.addr >> 32,
    )
    return (header + Struct("<Q").pack(self.value)).ljust(ALIGN, b"\0")

@dataclass(frozen=True)
class DramCopy:
  """Copy dense byte pages between pinned sysmem and interleaved device DRAM."""
  addr: int
  source: int
  page_size: int
  page_count: int
  banks: int
  direction: int = 0  # 0: sysmem -> DRAM, 1: DRAM -> sysmem
  bank_start: int = 0

  def lower(self) -> bytes:
    if not 0 <= self.addr < 1 << 32:
      raise ValueError("DRAM copy address must fit in 32 bits")
    if not 0 <= self.source < 1 << 64:
      raise ValueError("DRAM copy sysmem address must fit in 64 bits")
    if not 0 < self.page_size <= 16 * 1024 or self.page_size % 16:
      raise ValueError(
        "DRAM copy page size must be 16-byte aligned and at most 16 KiB",
      )
    if not 0 < self.page_count < 1 << 32:
      raise ValueError("DRAM copy page count must fit in 32 bits")
    if not 0 < self.banks <= 8:
      raise ValueError("DRAM copy bank count must be in [1, 8]")
    if self.direction not in (0, 1):
      raise ValueError("DRAM copy direction must be 0 or 1")
    if not 0 <= self.bank_start or self.bank_start + self.banks > 8:
      raise ValueError("DRAM copy bank range must be within [0, 8)")
    header = PacketLayout.HEADER.pack(
      Op.DRAM_COPY, 0, ALIGN, self.addr, self.page_size,
    )
    descriptor = header + Struct("<6I").pack(
      self.source & 0xFFFFFFFF, self.source >> 32, self.page_count,
      self.banks, self.direction, self.bank_start,
    )
    return descriptor.ljust(ALIGN, b"\0")

Command = UnicastWrite | McastWrite | Run | Signal | DramCopy

def lower(commands: list[Command] | tuple[Command, ...]) -> bytes:
  return b"".join(command.lower() for command in commands)

class CommandQueue:
  def __init__(self, pcie):
    self.pcie = pcie
    self.issue = pcie.sysmem.alloc(HOST_ISSUE_SIZE, PAGE_SIZE)
    self.completion = pcie.sysmem.alloc(HOST_COMPLETION_SIZE, PAGE_SIZE)
    self.read_ptr = self.completion + 16
    dram_base = _align(pcie.sysmem.allocator.next)
    self.dram_size = pcie.sysmem.allocator.end - dram_base
    if self.dram_size < PAGE_SIZE: raise MemoryError("sysmem has no DRAM staging region")
    self.dram = pcie.sysmem.alloc(self.dram_size, ALIGN)

    base = pcie.sysmem.noc_addr
    regions = (
      ("issue", self.issue, HOST_ISSUE_SIZE),
      ("completion", self.completion, HOST_COMPLETION_SIZE),
      ("dram", self.dram, self.dram_size),
    )
    for name, offset, size in regions:
      start, end = base + offset, base + offset + size - 1
      if start >> 32 != end >> 32:
        raise ValueError(f"{name} sysmem region crosses a 4 GiB NoC aperture")
    if os.getenv("BLACKHOLE_DEBUG"):
      print(f"sysmem noc_addr=0x{base:016x} size=0x{pcie.sysmem.size:x}")

    self.noc = base & 0xFFFFFFFF
    self.pcie_mid = base >> 32
    self.signal_addr = base + self.completion
    self.put = self.event = 0
    pcie.sysmem.write(self.issue, bytes(HOST_ISSUE_SIZE))
    pcie.sysmem.write(self.completion, bytes(HOST_COMPLETION_SIZE))
    self.prefetch = TLBWindow(pcie.fd, pcie.prefetch_core)
    self.dispatch = TLBWindow(pcie.fd, pcie.dispatch_core)
    self.prefetch.target(0, pcie.prefetch_core)
    self.dispatch.target(0, pcie.dispatch_core)
    self.prefetch.write(PREFETCH_DOORBELL, bytes(8))
    self.prefetch.write(PREFETCH_PCIE_BASE, self.noc + self.issue)
    self.prefetch.write(PREFETCH_READ_PTR, self.noc + self.read_ptr)
    self.prefetch.write(PREFETCH_DISPATCH_READ, 0)
    self.dispatch.write(DISPATCH_PUBLISHED, 0)

  def _read_u64(self, offset):
    return int.from_bytes(self.pcie.sysmem.read(offset, 8), "little")

  @staticmethod
  def _padding(size):
    if size < ALIGN or size % ALIGN:
      raise ValueError("CQ padding must be a positive multiple of 64 bytes")
    return PacketLayout.HEADER.pack(Op.PAD, 0, size, 0, 0).ljust(ALIGN, b"\0")

  def _wait_for_space(self, following, timeout=5.0):
    deadline = time.monotonic() + timeout
    while following - self._read_u64(self.read_ptr) > HOST_ISSUE_SIZE:
      if time.monotonic() >= deadline:
        raise TimeoutError("CQ issue ring did not drain")
      time.sleep(0)

  def _publish(self, record: bytes):
    if len(record) > MAX_RECORD_SIZE or len(record) % ALIGN:
      raise ValueError("CQ issue records must be aligned and at most 64 KiB")

    offset = self.put % HOST_ISSUE_SIZE
    padding = HOST_ISSUE_SIZE - offset if offset + len(record) > HOST_ISSUE_SIZE else 0
    following = self.put + padding + len(record)
    self._wait_for_space(following)
    if padding:
      self.pcie.sysmem.write(self.issue + offset, self._padding(padding))
      self.put += padding
      offset = 0
    self.pcie.sysmem.write(self.issue + offset, record)
    self.put += len(record)
    # Record bytes are visible before this UC MMIO doorbell store.
    self.prefetch.write(PREFETCH_DOORBELL, self.put.to_bytes(8, "little"))

  def enqueue(self, commands, *, completion=True):
    event = self.event + 1 if completion else 0
    for command in commands:
      self._publish(command.lower())
    if completion:
      self._publish(Signal(self.signal_addr, event).lower())
      self.event = event
    return event

  def submit(self, commands, timeout=10.0):
    return self.wait(self.enqueue(commands), timeout=timeout)

  def _firmware_breadcrumbs(self):
    slots = (
      ("prefetch", self.pcie.prefetch_core, CQ_BREADCRUMB),
      ("dispatch", self.pcie.dispatch_core, CQ_BREADCRUMB),
      ("dram_brisc", self.pcie.dram_core, CQ_BREADCRUMB),
      ("dram_ncrisc", self.pcie.dram_core, CQ_BREADCRUMB + 0x20),
    )
    result = {}
    with TLBWindow(self.pcie.fd, self.pcie.cores[0]) as window:
      for name, core, address in slots:
        window.target(0, core)
        words = CQ_BREADCRUMB_STRUCT.unpack(
          window.read(address, CQ_BREADCRUMB_STRUCT.size),
        )
        stage, *values = words
        result[name] = {
          "stage": CQ_BREADCRUMB_STAGES.get(stage, f"unknown {stage:#x}"),
          "values": tuple(f"{value:#x}" for value in values),
        }
    return result

  def _timeout(self, event):
    try:
      breadcrumbs = self._firmware_breadcrumbs()
    except Exception as error:
      breadcrumbs = f"unavailable: {error}"
    return TimeoutError(
      f"CQ completion {event} timed out; firmware breadcrumbs: {breadcrumbs}",
    )

  def wait(self, event, timeout=10.0, poll_interval=0.0002):
    deadline = time.monotonic() + timeout
    polls = 0
    while self._read_u64(self.completion) < event:
      polls += 1
      if poll_interval:
        if time.monotonic() >= deadline:
          raise self._timeout(event)
        time.sleep(poll_interval)
      elif polls & 0xff == 0 and time.monotonic() >= deadline:
        raise self._timeout(event)
    return Timestamp.unpack(
      self.pcie.sysmem.read(self.completion + 8, Timestamp.STRUCT.size),
    )

  def close(self):
    self.prefetch.close()
    self.dispatch.close()
