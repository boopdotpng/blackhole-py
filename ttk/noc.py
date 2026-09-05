"""Small direct-RISC-V Blackhole NoC interface.

This module emits four complete logical operations: ``read``, ``write``,
``send``, and ``atomic_inc``. It deliberately does not batch operations or
remember configuration across calls. A later whole-kernel lowering pass can
fuse compatible calls, hoist repeated command words, overlap requests, and
coalesce contiguous payloads without changing this interface.
"""

from dataclasses import dataclass

from isa import R, Reg, is_reg
from ttk.cb import CB, CBSyncSlot


Value = int | Reg
Core = tuple[int, int]

NIU0 = 0xFFB20000
NIU_STRIDE = 0x10000
COMMAND_BUFFER_STRIDE = 0x800
NIU_CONFIG = 0x100
LOGICAL_NODE_ID = 0x48
COMMAND_SEND = 0x40
STATUS = 0x200
REQUESTS_OUTSTANDING = 0x40
WRITES_OUTGOING = 0x80

WRITE = 1 << 1
WRITE_INLINE = 1 << 3
RESPONSE_MARKED = 1 << 4
MULTICAST = 1 << 5
VC_STATIC = 1 << 7
VC_SHIFT = 13
PRIORITY_SHIFT = 27
TID_SHIFT = 10

ATOMIC = 1 << 0
INCR_GET = 1 << 12
WRAP_32 = 31 << 2
MAX_PACKET_BYTES = 16 * 1024


def _static_aligned(value, name, alignment=16):
  if type(value) is not int or value < 0 or value % alignment:
    raise ValueError(
      f"{name} must be a non-negative, {alignment}-byte-aligned integer",
    )
  return value


def _coordinate(core: Core):
  if not isinstance(core, tuple) or len(core) != 2:
    raise TypeError("NoC core must be an (x, y) tuple")
  if any(type(axis) is not int or not 0 <= axis < 64 for axis in core):
    raise ValueError("NoC coordinate components must be integers in [0, 63]")
  return core[0] | core[1] << 6


def _rectangles(cores):
  """Cover a static core set with exact non-overlapping rectangles."""
  rows = {}
  for x, y in cores:
    rows.setdefault(y, []).append(x)
  active, result, previous_y = {}, [], None
  for y in sorted(rows):
    runs = []
    for x in sorted(rows[y]):
      if runs and x == runs[-1][1] + 1:
        runs[-1] = runs[-1][0], x
      else:
        runs.append((x, x))
    if previous_y is None or y != previous_y + 1:
      result.extend(active.values())
      active = {}
    following = {}
    for run in runs:
      if run in active:
        following[run] = active[run][0], (run[1], y)
      else:
        following[run] = (run[0], y), (run[1], y)
    result.extend(rect for run, rect in active.items() if run not in following)
    active, previous_y = following, y
  result.extend(active.values())
  return tuple(result)


@dataclass(frozen=True, slots=True)
class Interleaved:
  """Addressing configuration for a logical interleaved DRAM buffer."""

  base: Value
  coordinates: tuple[int, ...]
  page_bytes: int = 2048

  def __post_init__(self):
    if type(self.base) is int:
      _static_aligned(self.base, "DRAM base")
    elif not is_reg(self.base):
      raise TypeError("DRAM base must be an integer or RISC register")
    coordinates = tuple(self.coordinates)
    if not 1 <= len(coordinates) <= 8:
      raise ValueError("interleaved DRAM requires between one and eight banks")
    if any(type(value) is not int or not 0 <= value < 1 << 12
           for value in coordinates):
      raise ValueError("DRAM coordinates must be packed 12-bit coordinates")
    _static_aligned(self.page_bytes, "DRAM page size")
    if self.page_bytes > MAX_PACKET_BYTES:
      raise ValueError("DRAM page size cannot exceed 16 KiB")
    object.__setattr__(self, "coordinates", coordinates)


class NoC:
  """Emit standalone NoC operations on one BRISC or NCRISC instance."""

  def __init__(self, kernel, index=0, *, command_slot=0, tid=1,
               static_vc=1, priority=0):
    if kernel.role not in ("brisc", "ncrisc"):
      raise ValueError("only BRISC and NCRISC can issue NoC requests")
    if index not in (0, 1):
      raise ValueError("NoC index must be zero or one")
    if type(command_slot) is not int or not 0 <= command_slot < 4:
      raise ValueError("NoC command-buffer slot must be in [0, 3]")
    if type(tid) is not int or not 0 <= tid <= 15:
      raise ValueError("NoC transaction id must be in [0, 15]")
    if type(static_vc) is not int or not 0 <= static_vc <= 5:
      raise ValueError("static VC must be in [0, 5]")
    if type(priority) is not int or not 0 <= priority <= 15:
      raise ValueError("NoC priority must be in [0, 15]")
    self.kernel = kernel
    self.index = index
    self.command_slot = command_slot
    self.tid = tid
    self.static_vc = static_vc
    self.priority = priority

  @property
  def niu(self):
    return NIU0 + self.index * NIU_STRIDE

  @property
  def command(self):
    return self.niu + self.command_slot * COMMAND_BUFFER_STRIDE

  def _reg(self, value: Value):
    if is_reg(value):
      return value
    if type(value) is not int or value < 0:
      raise TypeError("NoC values must be non-negative integers or registers")
    result = self.kernel.reg()
    self.kernel.li(result, value)
    return result

  def _check_aligned(self, value: Value, name, alignment=16):
    if type(value) is int:
      return _static_aligned(value, name, alignment)
    if not is_reg(value):
      raise TypeError(f"{name} must be an integer or RISC register")
    low = self.kernel.reg()
    invalid = self.kernel._new_label("noc_unaligned")
    valid = self.kernel._new_label("noc_aligned")
    self.kernel.andi(low, value, alignment - 1)
    self.kernel.bne(low, R.ZERO, invalid)
    self.kernel.j(valid)
    self.kernel.label(invalid)
    self.kernel.j(invalid)
    self.kernel.label(valid)
    return value

  def _store(self, command: Reg, offset: int, value: Value, scratch: Reg):
    if is_reg(value):
      self.kernel.sw(value, command, offset)
    elif value:
      self.kernel.li(scratch, value)
      self.kernel.sw(scratch, command, offset)
    else:
      self.kernel.sw(R.ZERO, command, offset)

  def _wait_ready(self, command: Reg):
    busy = self.kernel.reg()
    again = self.kernel._new_label("noc_command_ready")
    self.kernel.label(again)
    self.kernel.lw(busy, command, COMMAND_SEND)
    self.kernel.bne(busy, R.ZERO, again)

  def _wait_zero(self, niu: Reg, offset: int):
    value = self.kernel.reg()
    again = self.kernel._new_label("noc_completion")
    self.kernel.label(again)
    self.kernel.lw(value, niu, offset)
    self.kernel.bne(value, R.ZERO, again)
    self.kernel.fence()

  def _local_coordinate(self):
    address, coordinate = self.kernel.reg(2)
    self.kernel.li(address, self.niu + NIU_CONFIG + LOGICAL_NODE_ID)
    self.kernel.lw(coordinate, address)
    self.kernel.slli(coordinate, coordinate, 20)
    self.kernel.srli(coordinate, coordinate, 20)
    return coordinate

  def _coordinate_table(self, coordinates):
    address = self.kernel.local.alloc(4 * len(coordinates))
    for index, coordinate in enumerate(coordinates):
      self.kernel.initialize_local(address + index * 4, coordinate)
    result = self.kernel.reg()
    self.kernel.li(result, address)
    return result

  def _select_coordinate(self, bank: Reg, table: Reg):
    address, coordinate = self.kernel.reg(2)
    self.kernel.slli(address, bank, 2)
    self.kernel.add(address, address, table)
    self.kernel.lw(coordinate, address)
    return coordinate

  def _configure(self, command: Reg, control: int):
    self._wait_ready(command)
    scratch = self.kernel.reg()
    for offset, value in (
      (4, 0), (16, 0), (24, self.tid << TID_SHIFT),
      (28, control), (36, 0), (40, 0), (44, 0),
    ):
      self._store(command, offset, value, scratch)

  def _submit(self, command: Reg, source_address: Reg,
              source_coordinate: Reg, target_address: Reg,
              target_coordinate: Reg, byte_count: Reg):
    self._wait_ready(command)
    self.kernel.sw(source_address, command, 0)
    self.kernel.sw(source_coordinate, command, 8)
    self.kernel.sw(target_address, command, 12)
    self.kernel.sw(target_coordinate, command, 20)
    self.kernel.sw(byte_count, command, 32)
    send = self.kernel.reg()
    self.kernel.li(send, 1)
    self.kernel.sw(send, command, COMMAND_SEND)

  def _control(self, *, write=False, multicast=False, inline=False,
               vc=None):
    vc = self.static_vc if vc is None else vc
    return (
      (WRITE if write else 0) |
      (WRITE_INLINE if inline else 0) |
      (MULTICAST if multicast else 0) |
      VC_STATIC | vc << VC_SHIFT | self.priority << PRIORITY_SHIFT
    )

  def _transfer(self, memory: Interleaved, logical_offset: Value,
                l1_address: Value, byte_count: Value, *, write: bool):
    """Emit one complete exact-range interleaved transfer."""
    if not isinstance(memory, Interleaved):
      raise TypeError("read/write require an Interleaved DRAM buffer")
    self._check_aligned(memory.base, "DRAM base")
    self._check_aligned(logical_offset, "logical DRAM offset")
    self._check_aligned(l1_address, "L1 address")
    base = self._reg(memory.base)
    offset = self._reg(logical_offset)
    local_address = self._reg(l1_address)
    remaining = self._reg(byte_count)
    page, banks = self.kernel.reg(2)
    self.kernel.li(page, memory.page_bytes)
    self.kernel.li(banks, len(memory.coordinates))
    table = self._coordinate_table(memory.coordinates)
    local = self._local_coordinate()
    niu, command = self.kernel.reg(2)
    self.kernel.li(niu, self.niu)
    self.kernel.li(command, self.command)
    self._wait_zero(
      niu, STATUS + REQUESTS_OUTSTANDING + self.tid * 4,
    )
    if write:
      self._wait_zero(niu, STATUS + WRITES_OUTGOING + self.tid * 4)
    self._configure(
      command, self._control(write=write) | RESPONSE_MARKED,
    )

    loop = self.kernel._new_label("noc_interleaved_range")
    done = self.kernel._new_label("noc_interleaved_done")
    self.kernel.label(loop)
    self.kernel.beq(remaining, R.ZERO, done)
    logical_page, within_page, bank, bank_row = self.kernel.reg(4)
    self.kernel.divu(logical_page, offset, page)
    self.kernel.remu(within_page, offset, page)
    self.kernel.remu(bank, logical_page, banks)
    self.kernel.divu(bank_row, logical_page, banks)
    remote_address, remote_offset = self.kernel.reg(2)
    self.kernel.mul(remote_offset, bank_row, page)
    self.kernel.add(remote_address, base, remote_offset)
    self.kernel.add(remote_address, remote_address, within_page)
    remote = self._select_coordinate(bank, table)
    chunk = self.kernel.reg()
    self.kernel.sub(chunk, page, within_page)
    have_chunk = self.kernel._new_label("noc_interleaved_chunk")
    self.kernel.bltu(chunk, remaining, have_chunk)
    self.kernel.mv(chunk, remaining)
    self.kernel.label(have_chunk)
    if write:
      self._submit(
        command, local_address, local, remote_address, remote, chunk,
      )
    else:
      self._submit(
        command, remote_address, remote, local_address, local, chunk,
      )
    self.kernel.add(offset, offset, chunk)
    self.kernel.add(local_address, local_address, chunk)
    self.kernel.sub(remaining, remaining, chunk)
    self.kernel.j(loop)
    self.kernel.label(done)
    self._wait_ready(command)
    if write:
      self._wait_zero(niu, STATUS + WRITES_OUTGOING + self.tid * 4)
    self._wait_zero(
      niu, STATUS + REQUESTS_OUTSTANDING + self.tid * 4,
    )
    return self

  def read(self, memory: Interleaved, logical_offset: Value,
           destination: Value, byte_count: Value):
    """Read an exact logical interleaved DRAM range into contiguous L1."""
    return self._transfer(
      memory, logical_offset, destination, byte_count, write=False,
    )

  def write(self, memory: Interleaved, logical_offset: Value,
            source: Value, byte_count: Value):
    """Write contiguous L1 bytes to an exact logical interleaved DRAM range."""
    return self._transfer(
      memory, logical_offset, source, byte_count, write=True,
    )

  def _rectangle_coordinate(self, start, end):
    low, high = (end, start) if self.index == 0 else (start, end)
    return _coordinate(low) | _coordinate(high) << 12

  def _send_packet(self, command: Reg, local: Reg, source: Reg,
                   target: Reg, byte_count: Reg, rectangle, *, inline=False,
                   inline_value=None):
    multicast = rectangle[0] != rectangle[1]
    coordinate = (
      self._rectangle_coordinate(*rectangle) if multicast else
      _coordinate(rectangle[0])
    )
    self._wait_ready(command)
    scratch = self.kernel.reg()
    words = (
      target if inline else source, 0,
      coordinate if inline else local,
      0 if inline else target, 0,
      0 if inline else coordinate,
      self.tid << TID_SHIFT,
      self._control(
        write=True, multicast=multicast, inline=inline,
        vc=4 if multicast else self.static_vc,
      ),
      0xF if inline else byte_count, 0,
      inline_value if inline else 0, 0,
    )
    for index, word in enumerate(words):
      self._store(command, index * 4, word, scratch)
    self._store(command, COMMAND_SEND, 1, scratch)

  def send(self, cb: CB, destinations, page_count: Value,
           last_page_bytes: Value, sync: CBSyncSlot):
    """Send one ready CB prefix and publish it to remote CB consumers.

    Contiguous bytes are limited to 16 KiB packets. This validated POC form
    assumes launch-local zeroed remote counters; repeated-send credit tracking
    belongs to later stream lowering.
    """
    if not isinstance(cb, CB):
      raise TypeError("send requires a CB")
    if not isinstance(sync, CBSyncSlot):
      raise TypeError("send requires a physical CB synchronization slot")
    destinations = tuple(destinations)
    if not destinations or len(set(destinations)) != len(destinations):
      raise ValueError("send destinations must be non-empty and unique")
    for core in destinations:
      _coordinate(core)
    rectangles = _rectangles(destinations)
    for start, end in rectangles:
      if start != end and (start[0] in (8, 9) or end[0] in (8, 9)):
        raise ValueError("multicast endpoints cannot use NoC columns 8 or 9")
    if cb.item_bytes > MAX_PACKET_BYTES:
      raise ValueError("CB page size cannot exceed 16 KiB")
    pages = self._reg(page_count)
    tail = self._reg(last_page_bytes)
    page = self.kernel.reg()
    self.kernel.li(page, cb.item_bytes)
    invalid = self.kernel._new_label("noc_invalid_send")
    nonempty = self.kernel._new_label("noc_nonempty_send")
    empty = self.kernel._new_label("noc_empty_send")
    valid = self.kernel._new_label("noc_valid_send")
    self.kernel.bne(pages, R.ZERO, nonempty)
    self.kernel.bne(tail, R.ZERO, invalid)
    self.kernel.j(empty)
    self.kernel.label(nonempty)
    depth = self.kernel.reg()
    self.kernel.li(depth, cb.depth)
    self.kernel.bltu(depth, pages, invalid)
    self.kernel.beq(tail, R.ZERO, invalid)
    self.kernel.bltu(page, tail, invalid)
    complete, byte_count = self.kernel.reg(2)
    self.kernel.addi(complete, pages, -1)
    self.kernel.mul(byte_count, complete, page)
    self.kernel.add(byte_count, byte_count, tail)
    self.kernel.j(valid)
    self.kernel.label(invalid)
    self.kernel.j(invalid)
    self.kernel.label(valid)

    niu, command, source, target = self.kernel.reg(4)
    self.kernel.li(niu, self.niu)
    self.kernel.li(command, self.command)
    self.kernel.li(source, cb.address)
    self.kernel.li(target, cb.address)
    local = self._local_coordinate()
    self._wait_zero(niu, STATUS + WRITES_OUTGOING + self.tid * 4)
    remaining, limit = self.kernel.reg(2)
    self.kernel.mv(remaining, byte_count)
    self.kernel.li(limit, MAX_PACKET_BYTES)
    loop = self.kernel._new_label("noc_send_payload")
    payload_done = self.kernel._new_label("noc_send_payload_done")
    self.kernel.label(loop)
    self.kernel.beq(remaining, R.ZERO, payload_done)
    chunk = self.kernel.reg()
    self.kernel.mv(chunk, remaining)
    have_chunk = self.kernel._new_label("noc_send_chunk")
    self.kernel.bltu(remaining, limit, have_chunk)
    self.kernel.mv(chunk, limit)
    self.kernel.label(have_chunk)
    for rectangle in rectangles:
      self._send_packet(
        command, local, source, target, chunk, rectangle,
      )
    self.kernel.add(source, source, chunk)
    self.kernel.add(target, target, chunk)
    self.kernel.sub(remaining, remaining, chunk)
    self.kernel.j(loop)
    self.kernel.label(payload_done)
    self._wait_ready(command)
    self._wait_zero(niu, STATUS + WRITES_OUTGOING + self.tid * 4)
    received = self._reg(sync.received_address)
    for rectangle in rectangles:
      self._send_packet(
        command, local, source, received, pages, rectangle,
        inline=True, inline_value=pages,
      )
    self._wait_ready(command)
    self.kernel.label(empty)
    return self

  def atomic_inc(self, destination: Core | Value, address: Value,
                 increment: Value, *, return_value=False,
                 return_address=None):
    """Atomically add to a remote 32-bit L1 word, optionally returning old."""
    if type(return_value) is not bool:
      raise TypeError("return_value must be a bool")
    if isinstance(destination, tuple):
      destination = _coordinate(destination)
    target_coordinate = self._reg(destination)
    self._check_aligned(address, "atomic address", 4)
    target_address = self._reg(address)
    addend = self._reg(increment)
    if return_value:
      if return_address is None:
        raise ValueError("returning atomic_inc requires an L1 return address")
      self._check_aligned(return_address, "atomic return address", 4)
      result_address = self._reg(return_address)
      result_coordinate = self._local_coordinate()
    else:
      result_address = self._reg(0)
      result_coordinate = R.ZERO

    niu, command = self.kernel.reg(2)
    self.kernel.li(niu, self.niu)
    self.kernel.li(command, self.command)
    if return_value:
      self._wait_zero(
        niu, STATUS + REQUESTS_OUTSTANDING + self.tid * 4,
      )
    selector, instruction = self.kernel.reg(2)
    self.kernel.andi(selector, target_address, 12)
    self.kernel.srli(selector, selector, 2)
    self.kernel.li(instruction, INCR_GET | WRAP_32)
    self.kernel.or_(instruction, instruction, selector)
    control = (
      ATOMIC | RESPONSE_MARKED | VC_STATIC |
      min(self.static_vc, 3) << VC_SHIFT |
      self.priority << PRIORITY_SHIFT
    )
    scratch = self.kernel.reg()
    for index, word in enumerate((
      target_address, 0, target_coordinate,
      result_address, 0, result_coordinate,
      self.tid << TID_SHIFT, control, instruction, 0, addend, 0,
    )):
      self._store(command, index * 4, word, scratch)
    self._wait_ready(command)
    self._store(command, COMMAND_SEND, 1, scratch)
    self._wait_ready(command)
    if not return_value:
      return None
    self._wait_zero(
      niu, STATUS + REQUESTS_OUTSTANDING + self.tid * 4,
    )
    result = self.kernel.reg()
    self.kernel.lw(result, result_address)
    return result
