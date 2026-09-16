"""Trace records for the central command queue's existing firmware ABI."""
from dataclasses import dataclass
from struct import Struct
import time
from cq import (ALIGN, PAGE_SIZE, MAX_RECORD_SIZE, MAX_WRITE_SIZE, HOST_ISSUE_SIZE,
  DRAM_BRISC_READY, DRAM_NCRISC_READY, McastWrite, UnicastWrite, Signal,
  DramCopy, Timestamp, noc_coord, mcast_coords, rectangles, PacketLayout as RawPacketLayout,
  CommandQueue as RawCommandQueue, _align)
from pcie import Allocator
from fw.consts import Core
from enum import IntEnum
HOST_TRACE_SIZE = 256 << 20
HOST_LIVE_SIZE = 128 << 10
DISPATCH_RING_PAGES = 320
PREFETCH_TRACE_ACTIVE = 0x1014
_rectangles = rectangles
class Op(IntEnum):
  RUN = 3
  DRAM_RECORD = 4
  TRACE = 6
class PacketLayout(RawPacketLayout):
  SIGNAL_VALUE = RawPacketLayout.HEADER.size

@dataclass(frozen=True)
class Run:
  cores: tuple[Core, ...]
  param_template: int = 0

  def lower(self) -> bytes:
    cores = tuple(self.cores)
    if not 0 <= self.param_template < 1 << 24:
      raise ValueError("RUN parameter-template address must fit in 24 bits")
    rects = _rectangles(cores)
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

class CommandQueue(RawCommandQueue):
  def __init__(self, pcie):
    self.trace = pcie.sysmem.alloc(HOST_TRACE_SIZE, PAGE_SIZE)
    self.trace_allocator = Allocator(self.trace, self.trace + HOST_TRACE_SIZE, ALIGN)
    self.live = pcie.sysmem.alloc(HOST_LIVE_SIZE, PAGE_SIZE)
    for name, offset, size in (("trace", self.trace, HOST_TRACE_SIZE), ("live", self.live, HOST_LIVE_SIZE)):
      start = pcie.sysmem.noc_addr + offset
      if start >> 32 != (start + size - 1) >> 32:
        raise ValueError(f"{name} sysmem region crosses a 4 GiB NoC aperture")
    super().__init__(pcie)
    pcie.sysmem.write(self.live, bytes(HOST_LIVE_SIZE))
    self.prefetch.write(PREFETCH_TRACE_ACTIVE, 0)

  @property
  def issue_write(self): return self.put % HOST_ISSUE_SIZE

  def capture_trace(self, records, dispatch_sizes=None):
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
