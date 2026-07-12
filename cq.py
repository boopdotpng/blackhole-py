"""Host/CQ-firmware command contract.

Python performs all grouping, coordinate packing, and multicast rectangle
selection. Prefetch forwards these records and dispatch executes them directly.
"""

from dataclasses import dataclass
from enum import IntEnum
from struct import Struct
from typing import Tuple
import time

Core = Tuple[int, int]  # (x, y)
Rect = Tuple[Core, Core]  # inclusive (start, end)

ALIGN = 64  # PCIe NoC reads require every issue record to start on a cache line.
MAX_WRITE_SIZE = 16 * 1024
MAX_RECORD_SIZE = 64 * 1024
PAGE_SIZE = 4096

# Shared host/prefetch/dispatch transport map. The two CQ cores have separate
# L1s, so state addresses may intentionally coincide.
CQ_STATE = 0x1000
PREFETCH_QUEUE = CQ_STATE + 0x100
PREFETCH_QUEUE_ENTRIES = 256
PREFETCH_PCIE_READ = CQ_STATE + 0x00
PREFETCH_PCIE_BASE = CQ_STATE + 0x04
PREFETCH_PCIE_END = CQ_STATE + 0x08
PREFETCH_CREDITS = CQ_STATE + 0x0C
PREFETCH_STAGING = 0x2000
DISPATCH_PUBLISHED = CQ_STATE + 0x00
DISPATCH_COMPLETION_WRITE = CQ_STATE + 0x04
DISPATCH_COMPLETION_BASE = CQ_STATE + 0x08
DISPATCH_COMPLETION_END = CQ_STATE + 0x0C
DISPATCH_COMPLETION_HOST_PTR = CQ_STATE + 0x10
DISPATCH_RING_BASE = 0x20000
DISPATCH_RING_PAGES = 320
DISPATCH_RING_END = DISPATCH_RING_BASE + DISPATCH_RING_PAGES * PAGE_SIZE
DISPATCH_SCRATCH = DISPATCH_RING_END
DISPATCH_GO = DISPATCH_SCRATCH + 0x40
DISPATCH_DONE_COUNT = DISPATCH_SCRATCH + 0x50
DISPATCH_COMPLETION_PUBLISH = DISPATCH_SCRATCH + 0x60
DISPATCH_CREDIT_RETURN = DISPATCH_SCRATCH + 0x70

HOST_ISSUE_SIZE = 64 << 20
HOST_COMPLETION_SIZE = 1 << 20

class Op(IntEnum):
  PAD = 0
  UNICAST_WRITE = 1
  MCAST_WRITE = 2
  RUN = 3
  FENCE = 4

class Packet:
  """Fixed command header followed by targets and optional payload data."""

  # op, padding, target_count, total_size, destination/event, payload_size.
  HEADER = Struct("<BxHIII")
  RESULT_ADDRESS = Struct("<Q")       # follows a Run header
  UNICAST_TARGET = Struct("<I")       # packed unicast NoC coordinate
  MCAST_TARGET = Struct("<II")        # packed rectangle, destination count

  OP = 0
  TARGET_COUNT = 2
  TOTAL_SIZE = 4
  ADDRESS = 8
  RUN_EVENT = ADDRESS
  DATA_SIZE = 12
  WRITE_TARGETS = HEADER.size
  RUN_RESULT_ADDRESS = HEADER.size
  RUN_TARGETS = HEADER.size + RESULT_ADDRESS.size

class RunResult:
  """Host-visible timestamps; dispatch publishes the event word last."""

  STRUCT = Struct("<QQI4x")
  START = 0
  END = 8
  EVENT = 16

def _align(value: int): return (value + ALIGN - 1) & -ALIGN

def _check_u32(name: str, value: int):
  if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
    raise ValueError(f"{name} must fit in an unsigned 32-bit integer")
  return value

def _check_u64(name: str, value: int):
  if type(value) is not int or not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
    raise ValueError(f"{name} must fit in an unsigned 64-bit integer")
  return value

def _core(core: Core):
  if (not isinstance(core, tuple) or len(core) != 2 or
      any(type(coordinate) is not int for coordinate in core)):
    raise TypeError("core must be an (x, y) tuple of Python integers")
  x, y = core
  if not 0 <= x < 64 or not 0 <= y < 64:
    raise ValueError("NoC coordinates must satisfy 0 <= x,y < 64")
  return x, y

def noc_coord(core: Core):
  """Pack an ``(x, y)`` core into a unicast NoC coordinate."""
  x, y = _core(core)
  return x | y << 6

def mcast_coord(rect: Rect):
  """Pack an inclusive rectangle and return its destination count."""
  if not isinstance(rect, tuple) or len(rect) != 2:
    raise TypeError("rectangle must be ((start_x, start_y), (end_x, end_y))")
  (start_x, start_y), (end_x, end_y) = _core(rect[0]), _core(rect[1])
  if start_x > end_x or start_y > end_y:
    raise ValueError("multicast rectangle start must not exceed its end")
  packed = start_x | start_y << 6 | end_x << 12 | end_y << 18
  count = (end_x - start_x + 1) * (end_y - start_y + 1)
  return packed, count

def _payload(data: bytes):
  if not isinstance(data, bytes): raise TypeError("write payloads must be bytes")
  if not 0 < len(data) <= MAX_WRITE_SIZE:
    raise ValueError(f"write payload size must be in [1, {MAX_WRITE_SIZE}]")
  return data

def _write_record(op: Op, targets: bytes, target_count: int, address: int,
                  data_size: int, payload: bytes):
  if not 0 < target_count <= 0xFFFF: raise ValueError("target count must be in [1, 65535]")
  target_end = Packet.HEADER.size + len(targets)
  payload_start = _align(target_end)
  total_size = _align(payload_start + len(payload))
  if total_size > MAX_RECORD_SIZE: raise ValueError("CQ record exceeds the 64 KiB staging buffer")
  _check_u32("command size", total_size)
  header = Packet.HEADER.pack(op, target_count, total_size, address, data_size)
  return header + targets + bytes(payload_start - target_end) + payload + bytes(total_size - payload_start - len(payload))

@dataclass(frozen=True)
class UnicastWrite:
  """Write one equally-sized payload per explicit core."""

  cores: tuple[Core, ...]
  addr: int
  data: tuple[bytes, ...]

  def lower(self) -> bytes:
    """Encode this write as one prefetch record."""
    cores = tuple(self.cores)
    if not cores: raise ValueError("unicast write requires at least one core")
    _check_u32("write address", self.addr)
    targets = b"".join(Packet.UNICAST_TARGET.pack(noc_coord(core)) for core in cores)
    blobs = tuple(self.data)
    if len(blobs) != len(cores): raise ValueError("per-core write needs one payload per core")
    blobs = tuple(_payload(blob) for blob in blobs)
    size = len(blobs[0])
    if any(len(blob) != size for blob in blobs): raise ValueError("per-core payload sizes must match")
    stride = _align(size)
    payload = b"".join(blob.ljust(stride, b"\0") for blob in blobs)
    return _write_record(Op.UNICAST_WRITE, targets, len(cores), self.addr, size, payload)

@dataclass(frozen=True)
class McastWrite:
  """Write shared bytes to precomputed inclusive multicast rectangles."""

  rects: tuple[Rect, ...]
  addr: int
  data: bytes
  counts: tuple[int, ...] | None = None

  def lower(self) -> bytes:
    """Encode this multicast write as one prefetch record."""
    rects = tuple(self.rects)
    if not rects: raise ValueError("multicast write requires at least one rectangle")
    _check_u32("write address", self.addr)
    data = _payload(self.data)
    encoded = tuple(mcast_coord(rect) for rect in rects)
    if self.counts is not None:
      counts = tuple(self.counts)
      if len(counts) != len(rects) or any(type(count) is not int or count <= 0 for count in counts):
        raise ValueError("multicast counts must contain one positive integer per rectangle")
      encoded = tuple((coordinate, count) for (coordinate, _), count in zip(encoded, counts))
    targets = b"".join(Packet.MCAST_TARGET.pack(*target) for target in encoded)
    return _write_record(Op.MCAST_WRITE, targets, len(rects), self.addr, len(data), data)

@dataclass(frozen=True)
class Run:
  """Run explicit worker cores and publish timing/completion to ``result_addr``."""

  cores: tuple[Core, ...]
  result_addr: int
  event: int = 0

  def lower(self) -> bytes:
    """Encode this run as one prefetch record."""
    cores = tuple(self.cores)
    if not cores: raise ValueError("run requires at least one core")
    _check_u64("result address", self.result_addr)
    if self.result_addr == 0: raise ValueError("result address must be nonzero")
    _check_u32("event", self.event)
    if self.event == 0: raise ValueError("event must be nonzero")
    targets = b"".join(Packet.UNICAST_TARGET.pack(noc_coord(core)) for core in cores)
    total_size = _align(Packet.RUN_TARGETS + len(targets))
    header = Packet.HEADER.pack(Op.RUN, len(cores), total_size, self.event, 0)
    result = Packet.RESULT_ADDRESS.pack(self.result_addr)
    return (header + result + targets).ljust(total_size, b"\0")


@dataclass(frozen=True)
class Fence:
  result_addr: int
  event: int

  def lower(self):
    _check_u64("result address", self.result_addr); _check_u32("event", self.event)
    if not self.result_addr or not self.event: raise ValueError("fence result address and event must be nonzero")
    total = _align(Packet.HEADER.size + Packet.RESULT_ADDRESS.size)
    header = Packet.HEADER.pack(Op.FENCE, 0, total, self.event, 0)
    return (header + Packet.RESULT_ADDRESS.pack(self.result_addr)).ljust(total, b"\0")


Command = UnicastWrite | McastWrite | Run | Fence

def lower(commands: list[Command] | tuple[Command, ...]) -> bytes:
  """Lower commands into the raw, self-framing byte stream read by prefetch."""
  return b"".join(command.lower() for command in commands)


class CommandQueue:
  """Host side of the stable prefetch/dispatch transport."""

  def __init__(self, pcie):
    from pcie import TLBWindow
    self.pcie = pcie
    self.issue = pcie.sysmem.alloc(HOST_ISSUE_SIZE, PAGE_SIZE)
    self.completion = pcie.sysmem.alloc(HOST_COMPLETION_SIZE, PAGE_SIZE)
    self.completion_base = self.completion + PAGE_SIZE
    self.completion_end = self.completion + HOST_COMPLETION_SIZE
    dram_base = _align(pcie.sysmem.allocator.next)
    self.dram_size = pcie.sysmem.allocator.end - dram_base
    if self.dram_size < PAGE_SIZE: raise MemoryError("sysmem has no DRAM staging region")
    self.dram = pcie.sysmem.alloc(self.dram_size, ALIGN)
    self.issue_write = self.queue_index = self.dispatch_page = self.event = 0
    self.completion_read = 0
    self.completion_toggle = 0
    pcie.sysmem.write(self.issue, bytes(HOST_ISSUE_SIZE))
    pcie.sysmem.write(self.completion, bytes(HOST_COMPLETION_SIZE))
    pcie.sysmem.write(self.completion, self.completion_read.to_bytes(4, "little"))
    pcie.sysmem.flush()
    self.prefetch = TLBWindow(pcie.fd, pcie.prefetch_core)
    self.dispatch = TLBWindow(pcie.fd, pcie.dispatch_core)
    self.prefetch.target(0, pcie.prefetch_core)
    self.dispatch.target(0, pcie.dispatch_core)
    self.noc = pcie.sysmem.noc_addr & 0xFFFFFFFF
    self.prefetch.write(PREFETCH_PCIE_READ, self.noc + self.issue)
    self.prefetch.write(PREFETCH_PCIE_BASE, self.noc + self.issue)
    self.prefetch.write(PREFETCH_PCIE_END, self.noc + self.issue + HOST_ISSUE_SIZE)
    self.prefetch.write(PREFETCH_QUEUE, bytes(PREFETCH_QUEUE_ENTRIES * 4))
    self.dispatch.write(DISPATCH_PUBLISHED, 0)
    self.completion_read = (self.noc + self.completion_base) >> 4
    self.dispatch.write(DISPATCH_COMPLETION_WRITE, self.completion_read)
    self.dispatch.write(DISPATCH_COMPLETION_BASE, self.completion_read)
    self.dispatch.write(DISPATCH_COMPLETION_END, (self.noc + self.completion_end) >> 4)
    self.dispatch.write(DISPATCH_COMPLETION_HOST_PTR, self.noc + self.completion)
    pcie.sysmem.write(self.completion, self.completion_read.to_bytes(4, "little"))
    pcie.sysmem.flush()

  def _slot_free(self, index, timeout=5.0):
    deadline = time.monotonic() + timeout
    addr = PREFETCH_QUEUE + index * 4
    while int.from_bytes(self.prefetch.read(addr, 4), "little"):
      if time.monotonic() >= deadline: raise TimeoutError(f"CQ prefetch slot {index} did not drain")

  @staticmethod
  def _padding(size=ALIGN):
    size = _align(size)
    return Packet.HEADER.pack(Op.PAD, 0, size, 0, 0).ljust(size, b"\0")

  def _write_record(self, record: bytes):
    if len(record) > MAX_RECORD_SIZE or len(record) % ALIGN:
      raise ValueError("CQ issue records must be aligned and at most 64 KiB")
    if self.issue_write + len(record) > HOST_ISSUE_SIZE:
      while self.issue_write < HOST_ISSUE_SIZE:
        self._publish(self._padding(min(MAX_RECORD_SIZE, HOST_ISSUE_SIZE - self.issue_write)), pad_ring=False)
      # A free slot proves prefetch completed the corresponding PCIe read.
      for index in range(PREFETCH_QUEUE_ENTRIES): self._slot_free(index)
      self.issue_write = 0
    addr = self.issue + self.issue_write
    self.pcie.sysmem.write(addr, record)
    self.pcie.sysmem.flush()
    index = self.queue_index
    self._slot_free(index)
    self.prefetch.write(PREFETCH_QUEUE + index * 4, len(record) >> 4)
    self.queue_index = (index + 1) % PREFETCH_QUEUE_ENTRIES
    self.issue_write += len(record)

  def _publish(self, record: bytes, *, pad_ring=True):
    pages = (len(record) + PAGE_SIZE - 1) // PAGE_SIZE
    if pages > DISPATCH_RING_PAGES: raise ValueError("record exceeds dispatch ring")
    if pad_ring:
      while self.dispatch_page and pages > DISPATCH_RING_PAGES - self.dispatch_page:
        self._publish(self._padding(), pad_ring=False)
    self._write_record(record)
    self.dispatch_page = (self.dispatch_page + pages) % DISPATCH_RING_PAGES

  def submit(self, commands, *, timeout=10.0):
    self.event += 1
    commands = tuple(commands)
    if not commands: raise ValueError("CQ submission cannot be empty")
    if isinstance(commands[-1], Run):
      run = commands[-1]
      commands = (*commands[:-1], Run(run.cores, 1, self.event))
    elif not isinstance(commands[-1], Fence):
      commands = (*commands, Fence(1, self.event))
    for command in commands: self._publish(command.lower())
    return self.wait(self.event, timeout=timeout)

  def wait(self, event, *, timeout=10.0):
    deadline = time.monotonic() + timeout
    expected = event & 0xFFFFFFFF
    while True:
      raw = int.from_bytes(self.pcie.sysmem.read(self.completion, 4), "little")
      if raw != (self.completion_read | self.completion_toggle << 31):
        offset = (self.completion_read << 4) - self.noc
        result = RunResult.STRUCT.unpack(self.pcie.sysmem.read(offset, RunResult.STRUCT.size))
        if result[2] == expected:
          self.completion_read = raw & 0x7FFFFFFF
          self.completion_toggle = raw >> 31
          return result
      if time.monotonic() >= deadline: raise TimeoutError(f"CQ completion {event} timed out")
      time.sleep(0.0002)

  def close(self):
    self.prefetch.close()
    self.dispatch.close()
