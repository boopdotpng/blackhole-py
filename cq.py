from dataclasses import dataclass
from enum import IntEnum
from struct import Struct
from typing import ClassVar, Tuple
import time

Core = Tuple[int, int]
Rect = Tuple[Core, Core]

ALIGN = 64; MAX_WRITE_SIZE = 16 * 1024; MAX_RECORD_SIZE = 64 * 1024; PAGE_SIZE = 4096

CQ_STATE = 0x1000; PREFETCH_QUEUE = CQ_STATE + 0x100; PREFETCH_QUEUE_ENTRIES = 256
PREFETCH_PCIE_READ = CQ_STATE; PREFETCH_PCIE_BASE = CQ_STATE + 4; PREFETCH_PCIE_END = CQ_STATE + 8
PREFETCH_CREDITS = CQ_STATE + 0xC; PREFETCH_STAGING = 0x2000
DISPATCH_PUBLISHED = CQ_STATE; DISPATCH_COMPLETION_WRITE = CQ_STATE + 4; DISPATCH_COMPLETION_BASE = CQ_STATE + 8
DISPATCH_COMPLETION_END = CQ_STATE + 0xC; DISPATCH_COMPLETION_HOST_PTR = CQ_STATE + 0x10
DISPATCH_RING_BASE = 0x20000; DISPATCH_RING_PAGES = 320
DISPATCH_RING_END = DISPATCH_RING_BASE + DISPATCH_RING_PAGES * PAGE_SIZE
DISPATCH_SCRATCH = DISPATCH_RING_END; DISPATCH_GO = DISPATCH_SCRATCH + 0x40; DISPATCH_DONE_COUNT = DISPATCH_SCRATCH + 0x50
DISPATCH_COMPLETION_PUBLISH = DISPATCH_SCRATCH + 0x60; DISPATCH_CREDIT_RETURN = DISPATCH_SCRATCH + 0x70
HOST_ISSUE_SIZE = 64 << 20; HOST_COMPLETION_SIZE = 1 << 20

class Op(IntEnum):
  PAD = 0
  UNICAST_WRITE = 1
  MCAST_WRITE = 2
  RUN = 3

class PacketLayout:
  HEADER = Struct("<BxHIII")
  RESULT_ADDRESS = Struct("<Q")
  UNICAST_TARGET = Struct("<I")
  MCAST_TARGET = Struct("<II")

  OP = 0
  TARGET_COUNT = 2
  TOTAL_SIZE = 4
  ADDRESS = 8
  RUN_EVENT = ADDRESS
  DATA_SIZE = 12
  WRITE_TARGETS = HEADER.size
  RUN_TARGETS = HEADER.size + RESULT_ADDRESS.size

@dataclass(frozen=True)
class Timestamp:
  start: int
  end: int
  event: int
  STRUCT: ClassVar[Struct] = Struct("<QQI4x")
  START: ClassVar[int] = 0
  END: ClassVar[int] = 8
  EVENT: ClassVar[int] = 16

  @property
  def cycles(self): return self.end - self.start

  @property
  def us(self): return self.cycles / 1350

  @property
  def seconds(self): return self.cycles / 1_350_000_000

  @classmethod
  def unpack(cls, data): return cls(*cls.STRUCT.unpack(data))

def _align(value: int): return (value + ALIGN - 1) & -ALIGN

def noc_coord(core: Core):
  x, y = core
  return x | y << 6

def mcast_coord(rect: Rect):
  (start_x, start_y), (end_x, end_y) = rect
  packed = start_x | start_y << 6 | end_x << 12 | end_y << 18
  count = (end_x - start_x + 1) * (end_y - start_y + 1)
  return packed, count

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
  rects: tuple[Rect, ...]
  addr: int
  data: bytes
  counts: tuple[int, ...] | None = None

  def lower(self) -> bytes:
    rects = tuple(self.rects)
    data = _payload(self.data)
    encoded = tuple(mcast_coord(rect) for rect in rects)
    if self.counts is not None:
      counts = tuple(self.counts)
      if len(counts) != len(rects) or any(type(count) is not int or count <= 0 for count in counts):
        raise ValueError("multicast counts must contain one positive integer per rectangle")
      encoded = tuple((coordinate, count) for (coordinate, _), count in zip(encoded, counts))
    targets = b"".join(PacketLayout.MCAST_TARGET.pack(*target) for target in encoded)
    return _write_record(Op.MCAST_WRITE, targets, len(rects), self.addr, len(data), data)

@dataclass(frozen=True)
class Run:
  cores: tuple[Core, ...]
  result_addr: int
  event: int = 0

  def lower(self) -> bytes:
    cores = tuple(self.cores)
    targets = b"".join(PacketLayout.UNICAST_TARGET.pack(noc_coord(core)) for core in cores)
    total_size = _align(PacketLayout.RUN_TARGETS + len(targets))
    header = PacketLayout.HEADER.pack(Op.RUN, len(cores), total_size, self.event, 0)
    result = PacketLayout.RESULT_ADDRESS.pack(self.result_addr)
    return (header + result + targets).ljust(total_size, b"\0")

Command = UnicastWrite | McastWrite | Run

def lower(commands: list[Command] | tuple[Command, ...]) -> bytes:
  return b"".join(command.lower() for command in commands)

class CommandQueue:
  def __init__(self, pcie):
    from pcie import TLBWindow
    self.pcie = pcie
    self.issue = pcie.sysmem.alloc(HOST_ISSUE_SIZE, PAGE_SIZE, "cq_issue")
    self.completion = pcie.sysmem.alloc(HOST_COMPLETION_SIZE, PAGE_SIZE, "cq_completion")
    self.completion_base = self.completion + PAGE_SIZE
    self.completion_end = self.completion + HOST_COMPLETION_SIZE
    dram_base = _align(pcie.sysmem.allocator.next)
    self.dram_size = pcie.sysmem.allocator.end - dram_base
    if self.dram_size < PAGE_SIZE: raise MemoryError("sysmem has no DRAM staging region")
    self.dram = pcie.sysmem.alloc(self.dram_size, ALIGN, "dram_staging")
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
    return PacketLayout.HEADER.pack(Op.PAD, 0, size, 0, 0).ljust(size, b"\0")

  def _write_record(self, record: bytes):
    if len(record) > MAX_RECORD_SIZE or len(record) % ALIGN:
      raise ValueError("CQ issue records must be aligned and at most 64 KiB")
    if self.issue_write + len(record) > HOST_ISSUE_SIZE:
      while self.issue_write < HOST_ISSUE_SIZE:
        self._publish(self._padding(min(MAX_RECORD_SIZE, HOST_ISSUE_SIZE - self.issue_write)), pad_ring=False)

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
    run = commands[-1]
    commands = (*commands[:-1], Run(run.cores, 1, self.event))
    for command in commands: self._publish(command.lower())
    return self.wait(self.event, timeout=timeout)

  def wait(self, event, *, timeout=10.0):
    deadline = time.monotonic() + timeout
    expected = event & 0xFFFFFFFF
    while True:
      raw = int.from_bytes(self.pcie.sysmem.read(self.completion, 4), "little")
      if raw != (self.completion_read | self.completion_toggle << 31):
        offset = (self.completion_read << 4) - self.noc
        result = Timestamp.unpack(self.pcie.sysmem.read(offset, Timestamp.STRUCT.size))
        if result.event == expected:
          self.completion_read = raw & 0x7FFFFFFF
          self.completion_toggle = raw >> 31
          return result
      if time.monotonic() >= deadline: raise TimeoutError(f"CQ completion {event} timed out")
      time.sleep(0.0002)

  def close(self):
    self.prefetch.close()
    self.dispatch.close()
