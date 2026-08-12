from dataclasses import dataclass
from enum import IntEnum
from struct import Struct
import time

from fw import Core
from pcie import Allocator, TLBWindow


PACKET_SIZE = 64
MAX_WRITE_SIZE = 16 * 1024
PAGE_SIZE = 4096

HOST_ISSUE_SIZE = 1 << 20
HOST_ISSUE_SLOTS = HOST_ISSUE_SIZE // PACKET_SIZE
HOST_COMPLETION_SIZE = PAGE_SIZE
HOST_INDIRECT_SIZE = 16 << 20
HOST_ARGS_SIZE = 4 << 20
HOST_COMMAND_DATA_SIZE = 16 << 20
HOST_LIVE_SIZE = 128 << 10

# Prefetch-core state. All queue pointers count 64-byte packets, not bytes.
CQ_STATE = 0x1000
PREFETCH_DOORBELL = CQ_STATE
PREFETCH_PCIE_BASE = CQ_STATE + 0x08
PREFETCH_READ_PTR = CQ_STATE + 0x0C
PREFETCH_DISPATCH_READ = CQ_STATE + 0x10
PREFETCH_INDIRECT_ACTIVE = CQ_STATE + 0x14
PREFETCH_INDIRECT_LO = CQ_STATE + 0x18
PREFETCH_INDIRECT_MID = CQ_STATE + 0x1C
PREFETCH_INDIRECT_INDEX = CQ_STATE + 0x20
PREFETCH_INDIRECT_COUNT = CQ_STATE + 0x24
PREFETCH_READ_PUBLISH = CQ_STATE + 0x30
PREFETCH_DISPATCH_PUBLISH = CQ_STATE + 0x40
PREFETCH_STAGING = 0x20000

# Dispatch has a fixed-slot L1 ring. Variable payloads remain out of line.
DISPATCH_PUBLISHED = CQ_STATE
DISPATCH_RING_BASE = 0x20000
DISPATCH_RING_SLOTS = 1024
DISPATCH_RING_END = DISPATCH_RING_BASE + DISPATCH_RING_SLOTS * PACKET_SIZE
DISPATCH_READ_PUBLISH = DISPATCH_RING_END
DISPATCH_DONE_COUNT = DISPATCH_RING_END + 0x10
DISPATCH_GO = DISPATCH_RING_END + 0x20
DISPATCH_SIGNAL = DISPATCH_RING_END + 0x40
DISPATCH_ARGS = DISPATCH_RING_END + 0x80
DISPATCH_TARGETS = DISPATCH_RING_END + 0x100
DISPATCH_DATA = DISPATCH_RING_END + 0x1000

# DMA-core mailbox. It is a separate engine, not a compute-queue opcode.
DMA_SUBMIT = CQ_STATE
DMA_COMPLETE = CQ_STATE + 0x04
DMA_BRISC_DONE = CQ_STATE + 0x08
DMA_NCRISC_DONE = CQ_STATE + 0x0C
DMA_BRISC_READY = CQ_STATE + 0x10
DMA_NCRISC_READY = CQ_STATE + 0x14
DMA_BANKS = CQ_STATE + 0x18
DMA_DESCRIPTOR = CQ_STATE + 0x40


class Op(IntEnum):
  WRITE = 1
  EXEC = 2
  SIGNAL = 3
  INDIRECT = 4


class PacketLayout:
  WORDS = Struct("<16I")

  OP = 0
  TARGET_COUNT = 4
  ADDRESS = 8
  BYTE_COUNT = 12
  SOURCE_LO = 16
  SOURCE_MID = 20
  TARGETS_LO = 24
  TARGETS_MID = 28

  EXEC_ARGS_LO = 8
  EXEC_ARGS_MID = 12
  EXEC_ARGS_SIZE = 16
  EXEC_EXPECTED = 20
  EXEC_TARGETS_LO = 24
  EXEC_TARGETS_MID = 28
  EXEC_ENTRY_POINTS = 32

  SIGNAL_TARGET_LO = 8
  SIGNAL_TARGET_MID = 12
  SIGNAL_VALUE = 16

  INDIRECT_SOURCE_LO = 8
  INDIRECT_SOURCE_MID = 12
  INDIRECT_COUNT = 16


def _u32(value, name):
  if type(value) is not int or not 0 <= value < 1 << 32:
    raise ValueError(f"{name} must fit in 32 bits")
  return value


def _u64(value, name):
  if type(value) is not int or not 0 <= value < 1 << 64:
    raise ValueError(f"{name} must fit in 64 bits")
  return value


def _packet(*words):
  if len(words) > 16: raise ValueError("packet has more than 16 words")
  return PacketLayout.WORDS.pack(*(tuple(words) + (0,) * (16 - len(words))))


def noc_coord(core: Core):
  if (
    type(core) is not tuple or len(core) != 2 or
    any(type(value) is not int or not 0 <= value < 64 for value in core)
  ):
    raise ValueError("NoC coordinate components must be integers in [0, 63]")
  return core[0] | core[1] << 6


@dataclass(frozen=True)
class Write:
  cores: tuple[Core, ...]
  addr: int
  data: bytes

  def encode(self, queue):
    cores, data = tuple(self.cores), bytes(self.data)
    if not cores: raise ValueError("write needs at least one target core")
    if not 0 < len(data) <= MAX_WRITE_SIZE:
      raise ValueError("write payload size must be in [1, 16 KiB]")
    source = queue.stage(data)
    targets = queue.stage(b"".join(noc_coord(core).to_bytes(4, "little") for core in cores))
    return _packet(
      Op.WRITE, len(cores), _u32(self.addr, "write address"), len(data),
      source & 0xFFFFFFFF, source >> 32, targets & 0xFFFFFFFF, targets >> 32,
    )


@dataclass(frozen=True)
class Exec:
  cores: tuple[Core, ...]
  entry_points: tuple[int, ...]
  args_addr: int = 0
  args_size: int = 0

  def encode(self, queue):
    cores = tuple(self.cores)
    if not cores: raise ValueError("exec needs at least one worker core")
    _u64(self.args_addr, "exec argument address")
    if not 0 <= self.args_size <= 48 or self.args_size % 4:
      raise ValueError("exec argument size must be a multiple of four up to 48 bytes")
    if bool(self.args_addr) != bool(self.args_size):
      raise ValueError("exec argument address and size must both be set or both be zero")
    entries = tuple(self.entry_points)
    if len(entries) != 5:
      raise ValueError("exec requires five worker entry points")
    for entry in entries: _u32(entry, "exec entry point")
    targets = queue.stage(b"".join(noc_coord(core).to_bytes(4, "little") for core in cores))
    return _packet(
      Op.EXEC, len(cores), self.args_addr & 0xFFFFFFFF, self.args_addr >> 32,
      self.args_size, len(cores), targets & 0xFFFFFFFF, targets >> 32,
      *entries,
    )


@dataclass(frozen=True)
class Signal:
  addr: int
  value: int

  def encode(self, queue):
    _u64(self.addr, "signal address"); _u64(self.value, "signal value")
    return _packet(
      Op.SIGNAL, 0, self.addr & 0xFFFFFFFF, self.addr >> 32,
      self.value & 0xFFFFFFFF, self.value >> 32,
    )


@dataclass(frozen=True)
class Indirect:
  addr: int
  count: int

  def encode(self, queue):
    _u64(self.addr, "indirect address")
    if not 0 < self.count < 1 << 32:
      raise ValueError("indirect packet count must fit in 32 bits")
    return _packet(
      Op.INDIRECT, 0, self.addr & 0xFFFFFFFF, self.addr >> 32, self.count,
    )


ComputeCommand = Write | Exec | Signal | Indirect


@dataclass(frozen=True)
class CommandBuffer:
  addr: int
  count: int


@dataclass(frozen=True)
class Copy:
  device_addr: int
  host_addr: int
  byte_count: int
  direction: int = 0  # 0: host -> DRAM, 1: DRAM -> host

  def encode(self):
    _u32(self.device_addr, "DMA device address")
    _u64(self.host_addr, "DMA host address")
    if not 0 < self.byte_count < 1 << 32:
      raise ValueError("DMA byte count must fit in 32 bits")
    if self.direction not in (0, 1): raise ValueError("DMA direction must be 0 or 1")
    return _packet(
      self.device_addr, self.host_addr & 0xFFFFFFFF, self.host_addr >> 32,
      self.byte_count, self.direction,
    )


class SubmissionMemory:
  """Pinned storage shared by the two submission engines."""

  def __init__(self, pcie):
    self.pcie = pcie
    sysmem = pcie.sysmem
    self.issue = sysmem.alloc(HOST_ISSUE_SIZE, PAGE_SIZE)
    self.completion = sysmem.alloc(HOST_COMPLETION_SIZE, PAGE_SIZE)
    self.read_ptr = self.completion + 16
    self.indirect = sysmem.alloc(HOST_INDIRECT_SIZE, PAGE_SIZE)
    self.indirect_allocator = Allocator(self.indirect, self.indirect + HOST_INDIRECT_SIZE, PACKET_SIZE)
    self.args = sysmem.alloc(HOST_ARGS_SIZE, PAGE_SIZE)
    self.args_allocator = Allocator(self.args, self.args + HOST_ARGS_SIZE, 64)
    self.command_data = sysmem.alloc(HOST_COMMAND_DATA_SIZE, PAGE_SIZE)
    self.command_data_allocator = Allocator(
      self.command_data, self.command_data + HOST_COMMAND_DATA_SIZE, 64,
    )
    self.live = sysmem.alloc(HOST_LIVE_SIZE, PAGE_SIZE)
    dma_base = (sysmem.allocator.next + PAGE_SIZE - 1) & -PAGE_SIZE
    self.dma_size = sysmem.allocator.end - dma_base
    if self.dma_size < PAGE_SIZE: raise MemoryError("sysmem has no DMA staging region")
    self.dma = sysmem.alloc(self.dma_size, PAGE_SIZE)

    base = sysmem.noc_addr
    for name, offset, size in (
      ("issue", self.issue, HOST_ISSUE_SIZE),
      ("completion", self.completion, HOST_COMPLETION_SIZE),
      ("indirect", self.indirect, HOST_INDIRECT_SIZE),
      ("args", self.args, HOST_ARGS_SIZE),
      ("command data", self.command_data, HOST_COMMAND_DATA_SIZE),
      ("live", self.live, HOST_LIVE_SIZE),
      ("DMA", self.dma, self.dma_size),
    ):
      start, end = base + offset, base + offset + size - 1
      if start >> 32 != end >> 32:
        raise ValueError(f"{name} sysmem region crosses a 4 GiB NoC aperture")

  def noc_address(self, offset): return self.pcie.sysmem.noc_addr + offset


class ComputeQueue:
  """Fixed-slot compute submission with no scheduling policy."""

  def __init__(self, pcie, memory: SubmissionMemory):
    self.pcie, self.memory = pcie, memory
    self.put = self.event = 0
    self.signal_addr = memory.noc_address(memory.completion)
    self._encoded = {}
    pcie.sysmem.write(memory.issue, bytes(HOST_ISSUE_SIZE))
    pcie.sysmem.write(memory.completion, bytes(HOST_COMPLETION_SIZE))
    pcie.sysmem.write(memory.live, bytes(HOST_LIVE_SIZE))
    self.prefetch = TLBWindow(pcie.fd, pcie.prefetch_core)
    self.dispatch = TLBWindow(pcie.fd, pcie.dispatch_core)
    self.prefetch.target(0, pcie.prefetch_core)
    self.dispatch.target(0, pcie.dispatch_core)
    self.prefetch.write(PREFETCH_DOORBELL, bytes(8))
    self.prefetch.write(PREFETCH_PCIE_BASE, memory.noc_address(memory.issue) & 0xFFFFFFFF)
    self.prefetch.write(PREFETCH_READ_PTR, memory.noc_address(memory.read_ptr) & 0xFFFFFFFF)
    self.prefetch.write(PREFETCH_DISPATCH_READ, 0)
    self.prefetch.write(PREFETCH_INDIRECT_ACTIVE, 0)
    self.dispatch.write(DISPATCH_PUBLISHED, 0)

  def stage(self, data):
    data = bytes(data)
    if not data: raise ValueError("cannot stage an empty command payload")
    offset = self.memory.command_data_allocator.alloc(len(data))
    self.pcie.sysmem.write(offset, data)
    return self.memory.noc_address(offset)

  def alloc_args(self, data):
    data = bytes(data)
    if not data: return 0
    if len(data) > 48 or len(data) % 4:
      raise ValueError("kernel arguments must be a multiple of four up to 48 bytes")
    offset = self.memory.args_allocator.alloc(len(data))
    self.pcie.sysmem.write(offset, data)
    return self.memory.noc_address(offset)

  def write_host(self, noc_address, data):
    offset = noc_address - self.pcie.sysmem.noc_addr
    data = bytes(data)
    if offset < 0 or offset + len(data) > self.pcie.sysmem.size:
      raise ValueError("host write is outside pinned sysmem")
    self.pcie.sysmem.write(offset, data)

  def encode(self, command):
    if isinstance(command, bytes):
      packet = bytes(command)
    else:
      try: packet = self._encoded[command]
      except (KeyError, TypeError):
        packet = command.encode(self)
        try: self._encoded[command] = packet
        except TypeError: pass
    if len(packet) != PACKET_SIZE:
      raise ValueError("compute queue entries must be exactly 64 bytes")
    return packet

  def capture(self, commands):
    packets = tuple(self.encode(command) for command in commands)
    if not packets: raise ValueError("indirect command buffer cannot be empty")
    blob = b"".join(packets)
    offset = self.memory.indirect_allocator.alloc(len(blob), PACKET_SIZE)
    self.pcie.sysmem.write(offset, blob)
    return CommandBuffer(self.memory.noc_address(offset), len(packets))

  def _read_u64(self, offset):
    return int.from_bytes(self.pcie.sysmem.read(offset, 8), "little")

  def _wait_for_space(self, following, timeout=5.0):
    deadline = time.monotonic() + timeout
    while following - self._read_u64(self.memory.read_ptr) > HOST_ISSUE_SLOTS:
      if time.monotonic() >= deadline: raise TimeoutError("compute issue ring did not drain")
      time.sleep(0)

  def submit(self, commands, signal=True):
    packets = [self.encode(command) for command in commands]
    event = 0
    if signal:
      event = self.event + 1
      packets.append(self.encode(Signal(self.signal_addr, event)))
    if not packets: raise ValueError("compute submission cannot be empty")
    self._wait_for_space(self.put + len(packets))
    for packet in packets:
      slot = self.put & (HOST_ISSUE_SLOTS - 1)
      self.pcie.sysmem.write(self.memory.issue + slot * PACKET_SIZE, packet)
      self.put += 1
    # Packet stores are visible before the uncached MMIO doorbell store.
    self.prefetch.write(PREFETCH_DOORBELL, self.put.to_bytes(8, "little"))
    if signal: self.event = event
    return event

  def replay(self, command_buffer: CommandBuffer):
    return self.submit((Indirect(command_buffer.addr, command_buffer.count),))

  def wait(self, event, timeout=10.0, poll_interval=0.0002):
    deadline = time.monotonic() + timeout
    polls = 0
    while self._read_u64(self.memory.completion) < event:
      polls += 1
      if poll_interval:
        if time.monotonic() >= deadline: raise TimeoutError(f"compute completion {event} timed out")
        time.sleep(poll_interval)
      elif polls & 0xFF == 0 and time.monotonic() >= deadline:
        raise TimeoutError(f"compute completion {event} timed out")
    return event

  def close(self):
    self.prefetch.close(); self.dispatch.close()


class DMAQueue:
  """One-deep descriptor mailbox for the independent DMA service core."""

  def __init__(self, pcie, memory: SubmissionMemory):
    self.pcie, self.memory, self.sequence = pcie, memory, 0
    self.banks = 0
    self.window = TLBWindow(pcie.fd, pcie.dma_core)
    self.window.target(0, pcie.dma_core)
    self.window.write(DMA_SUBMIT, bytes(0x1C))
    self.window.write(DMA_DESCRIPTOR, bytes(PACKET_SIZE))

  @property
  def staging_offset(self): return self.memory.dma

  @property
  def staging_size(self): return self.memory.dma_size

  @property
  def staging_address(self): return self.memory.noc_address(self.memory.dma)

  def wait_ready(self, timeout=5.0):
    deadline = time.monotonic() + timeout
    while (
      int.from_bytes(self.window.read(DMA_BRISC_READY, 4), "little") != 1 or
      int.from_bytes(self.window.read(DMA_NCRISC_READY, 4), "little") != 1
    ):
      if time.monotonic() >= deadline: raise TimeoutError("DMA engine did not start")
      time.sleep(0)
    self.banks = int.from_bytes(self.window.read(DMA_BANKS, 4), "little")
    if self.banks not in (7, 8):
      raise RuntimeError(f"DMA firmware discovered {self.banks} DRAM banks")

  def submit(self, command: Copy):
    if self.sequence: self.wait(self.sequence)
    self.sequence += 1
    self.window.write(DMA_DESCRIPTOR, command.encode())
    # Descriptor stores must land before publishing the new sequence.
    self.window.write(DMA_SUBMIT, self.sequence)
    return self.sequence

  def wait(self, sequence, timeout=30.0):
    deadline = time.monotonic() + timeout
    while int.from_bytes(self.window.read(DMA_COMPLETE, 4), "little") < sequence:
      if time.monotonic() >= deadline: raise TimeoutError(f"DMA completion {sequence} timed out")
      time.sleep(0)
    return sequence

  def close(self): self.window.close()


class CommandQueues:
  """Dumb ownership wrapper for the independent compute and DMA engines."""

  def __init__(self, pcie):
    self.memory = SubmissionMemory(pcie)
    self.compute = ComputeQueue(pcie, self.memory)
    self.dma = DMAQueue(pcie, self.memory)

  def close(self):
    self.compute.close(); self.dma.close()


def lower(commands, queue: ComputeQueue):
  return b"".join(queue.encode(command) for command in commands)
