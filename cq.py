from dataclasses import dataclass
from struct import Struct
from typing import ClassVar
import os, time
from firmware.consts import (
  Core, Rect, ALIGN, MAX_WRITE_SIZE, MAX_RECORD_SIZE, PAGE_SIZE,
  CQ_STATE, PREFETCH_DOORBELL, PREFETCH_PCIE_BASE, PREFETCH_READ_PTR,
  PREFETCH_DISPATCH_READ, DISPATCH_PUBLISHED, DRAM_BRISC_READY, DRAM_NCRISC_READY,
  HOST_ISSUE_SIZE, HOST_COMPLETION_SIZE, Op, PacketLayout,
)
from pcie import TLBWindow, Allocator
from firmware.consts import HOST_TRACE_SIZE, HOST_LIVE_SIZE, DISPATCH_RING_PAGES, PREFETCH_TRACE_ACTIVE


@dataclass(frozen=True)
class Timestamp:
  """A device clock value decoded from an HCQSignal's field at +8."""
  cycles: int
  STRUCT: ClassVar[Struct] = Struct("<Q")

  @property
  def us(self): return self.cycles / 1350

  @property
  def seconds(self): return self.cycles / 1_350_000_000

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
  param_template: int = 0

  def lower(self) -> bytes:
    cores = tuple(self.cores)
    if not 0 <= self.param_template < 1 << 24:
      raise ValueError("RUN parameter-template address must fit in 24 bits")
    rects = rectangles(cores)
    targets = b"".join(
      PacketLayout.MCAST_TARGET.pack(*mcast_coords(rect)) for rect in rects
    )
    total_size = _align(PacketLayout.RUN_TARGETS + len(targets))
    header = PacketLayout.HEADER.pack(
      Op.RUN, len(rects), total_size, 0, len(cores),
    )
    template = self.param_template.to_bytes(4, "little") + bytes(4)
    return (header + template + targets).ljust(total_size, b"\0")

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
    stamp = PacketLayout.HEADER.pack(Op.TIMESTAMP, 0, ALIGN, (self.addr + 8) & 0xFFFFFFFF, (self.addr + 8) >> 32)
    return stamp.ljust(ALIGN, b"\0") + (header + Struct("<Q").pack(self.value)).ljust(ALIGN, b"\0")

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
    if self.bank_start:
      raise ValueError("llama3 CQ firmware supports only bank prefixes; use Device transfers for other ranges")
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
  def __init__(self, pcie, *, trace_size=0):
    self.trace_allocator = None
    if trace_size:
      self.trace = pcie.sysmem.alloc(trace_size, PAGE_SIZE)
      self.trace_allocator = Allocator(self.trace, self.trace + trace_size, ALIGN)
      self.live = pcie.sysmem.alloc(HOST_LIVE_SIZE, PAGE_SIZE)
      for name, offset, size in (("trace", self.trace, trace_size), ("live", self.live, HOST_LIVE_SIZE)):
        start = pcie.sysmem.noc_addr + offset
        if start >> 32 != (start + size - 1) >> 32:
          raise ValueError(f"{name} sysmem region crosses a 4 GiB NoC aperture")
      pcie.sysmem.write(self.live, bytes(HOST_LIVE_SIZE))
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
    self.prefetch.write(PREFETCH_TRACE_ACTIVE, 0)
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

  def _timeout(self, event):
    return TimeoutError(f"CQ completion {event} timed out")

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

  @property
  def issue_write(self): return self.put % HOST_ISSUE_SIZE


  def capture_trace(self, records, dispatch_sizes=None):
    if self.trace_allocator is None:
      raise RuntimeError("this command queue has no trace arena")
    records = tuple(bytes(record) for record in records)
    if not records:
      raise ValueError("trace requires at least one CQ record")
    if dispatch_sizes is None:
      dispatch_sizes = tuple(map(len, records))
    else:
      dispatch_sizes = tuple(dispatch_sizes)
    if len(records) != len(dispatch_sizes):
      raise ValueError("trace records and dispatch sizes differ")
    if any(
      len(record) > MAX_RECORD_SIZE or len(record) % ALIGN
      for record in records
    ):
      raise ValueError("trace records must be aligned and at most 64 KiB")
    if any((size + PAGE_SIZE - 1) // PAGE_SIZE > DISPATCH_RING_PAGES
           for size in dispatch_sizes):
      raise ValueError("trace record exceeds dispatch ring")
    offsets, cursor = [], 0
    for record in records:
      offsets.append(cursor)
      cursor += len(record)
    # Signal lowers to a timestamp record followed by the value record.
    completion = Signal(self.signal_addr, 0).lower()
    final_signal_offset = cursor + len(completion) - ALIGN + PacketLayout.SIGNAL_VALUE
    records = (*records, completion)
    blob = b"".join(records)
    offset = self.trace_allocator.alloc(len(blob), ALIGN)
    self.pcie.sysmem.write(offset, blob)
    return CQTrace(
      offset, len(blob), final_signal_offset, tuple(offsets),
    )


  def patch_trace(self, trace, offset, data):
    data = bytes(data)
    if not 0 <= offset <= trace.size - len(data):
      raise ValueError("trace patch is outside the trace")
    self.pcie.sysmem.write(trace.offset + offset, data)


  def replay_trace(self, trace, timeout=10.0, *, wait=True):
    started = time.perf_counter_ns()
    event = self.event + 1
    self.patch_trace(
      trace, trace.final_signal_offset, event.to_bytes(8, "little"),
    )
    patched = time.perf_counter_ns()
    self._publish(Trace(self.pcie.sysmem.noc_addr + trace.offset, trace.size).lower())
    submitted = time.perf_counter_ns()
    self.event = event
    if not wait:
      self.last_replay_profile = {
        "event_patch_us": (patched - started) / 1e3,
        "doorbell_us": (submitted - patched) / 1e3,
        "device_wait_us": 0.0,
      }
      return event
    # Decode traces are short and latency-sensitive. Poll their pinned signal
    # directly instead of adding a scheduler wake-up to every token.
    result = self.wait(event, timeout=timeout, poll_interval=0.0)
    completed = time.perf_counter_ns()
    self.last_replay_profile = {
      "event_patch_us": (patched - started) / 1e3,
      "queue_slot_wait_us": 0.0,
      "doorbell_us": (submitted - patched) / 1e3,
      "device_wait_us": (completed - submitted) / 1e3,
      "descriptor_drain_us": 0.0,
    }
    return result



@dataclass(frozen=True)
class Wait:
  addr: int
  value: int
  eq: bool = False

  def lower(self):
    return (PacketLayout.HEADER.pack(Op.WAIT, 0, ALIGN, self.addr & 0xffffffff, self.addr >> 32) +
            Struct('<QI').pack(self.value, self.eq)).ljust(ALIGN, b'\0')

@dataclass(frozen=True)
class Indirect:
  addr: int
  size: int

  def lower(self):
    if self.size <= 0 or self.size % ALIGN: raise ValueError('indirect size must be positive and aligned')
    if (self.addr >> 32) != ((self.addr + self.size - 1) >> 32): raise ValueError('indirect crosses NoC aperture')
    return (PacketLayout.HEADER.pack(Op.INDIRECT, 0, ALIGN, self.addr & 0xffffffff, self.addr >> 32) +
            Struct('<I').pack(self.size)).ljust(ALIGN, b'\0')

@dataclass(frozen=True)
class Dma:
  dest: int
  src: int
  size: int

  def lower(self):
    if not 0 < self.size < 1 << 32: raise ValueError('DMA size must fit u32')
    return (PacketLayout.HEADER.pack(Op.DMA, 0, ALIGN, 0, 0) + Struct('<QQI').pack(self.src, self.dest, self.size)).ljust(ALIGN, b'\0')


@dataclass(frozen=True)
class DramRecord:
  """Reference an immutable, already-lowered CQ record in device DRAM."""
  addr: int
  coord: int
  size: int

  def lower(self) -> bytes:
    if self.addr < 0 or self.addr >= 1 << 32:
      raise ValueError("DRAM CQ record address must fit in 32 bits")
    if not 0 < self.coord < 1 << 12:
      raise ValueError("DRAM CQ record coordinate must fit in 12 bits")
    if not 0 < self.size <= MAX_RECORD_SIZE or self.size % ALIGN:
      raise ValueError("cached DRAM CQ record must be aligned and at most 64 KiB")
    total_size = ALIGN
    header = PacketLayout.HEADER.pack(
      Op.DRAM_RECORD, 0, total_size, self.addr, self.size,
    )
    return (header + self.coord.to_bytes(4, "little")).ljust(
      total_size, b"\0",
    )

@dataclass(frozen=True)
class Trace:
  """Reference an immutable CQ record stream in pinned host memory."""
  addr: int
  size: int

  def lower(self) -> bytes:
    if not 0 <= self.addr < 1 << 64:
      raise ValueError("trace address must fit in 64 bits")
    if not 0 < self.size < 1 << 32 or self.size % ALIGN:
      raise ValueError("trace size must be positive, aligned, and fit in 32 bits")
    header = PacketLayout.HEADER.pack(
      Op.TRACE, 0, ALIGN, self.addr & 0xFFFFFFFF, self.addr >> 32,
    )
    return (header + Struct("<I").pack(self.size)).ljust(ALIGN, b"\0")

@dataclass(frozen=True)
class CQTrace:
  offset: int
  size: int
  final_signal_offset: int
  record_offsets: tuple[int, ...]
