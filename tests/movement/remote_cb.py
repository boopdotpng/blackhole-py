"""Direct RISC-V remote-CB send proof for Blackhole.

``emit_send_pages`` copies a contiguous run of ready local L1 CB pages into
the same CB address on one or more remote Tensix cores. One destination uses a unicast;
rectangular groups use hardware multicast; arbitrary static core lists are
decomposed into exact rectangles.

After the payload commands, a 4-byte inline NoC write publishes the new value
of each receiver's real ``tiles_received`` stream-register counter.  Receivers
therefore use the ordinary CB wait/pop counters rather than a side semaphore.
This POC is deliberately launch-local: resident firmware starts all CB
counters at zero, and one call publishes one contiguous CB prefix. Tensor
element counts are deliberately outside this low-level hardware interface.
"""

from dataclasses import dataclass

from asm import Asm
from fw.consts import TensixL1
from isa import R, Reg, is_reg


NIU0 = 0xFFB20000
NIU_STRIDE = 0x10000
COMMAND_BUFFER_STRIDE = 0x800
NIU_CONFIG = 0x100
LOGICAL_NODE_ID = 0x48
COMMAND_SEND = 0x40
STATUS = 0x200
WRITES_OUTGOING = 0x80

CB_ACKED = 0xFFB48020
CB_RECEIVED = 0xFFB48028
CB_SYNC_STRIDE = 0x1000

WRITE = 1 << 1
WRITE_INLINE = 1 << 3
MULTICAST = 1 << 5
VC_STATIC = 1 << 7
VC_SHIFT = 13
TID_SHIFT = 10
MAX_BURST_BYTES = 16 * 1024


def _aligned(value, name, alignment=16):
  if type(value) is not int or value < 0 or value % alignment:
    raise ValueError(
      f"{name} must be a non-negative, {alignment}-byte-aligned integer",
    )
  return value


def _coordinate(core):
  x, y = core
  if any(type(value) is not int or not 0 <= value < 64 for value in core):
    raise ValueError("NoC coordinate components must be integers in [0, 63]")
  return x | y << 6


def _rectangles(cores):
  """Cover an arbitrary core set with exact, non-overlapping rectangles."""
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


@dataclass(frozen=True)
class RemoteCBConfig:
  destinations: tuple[tuple[int, int], ...]
  l1_address: int
  depth: int
  page_bytes: int = 2048
  noc: int = 0
  sync_slot: int = 0
  command_slot: int = 0
  tid: int = 1

  def __post_init__(self):
    destinations = tuple(self.destinations)
    if not destinations:
      raise ValueError("remote CB requires at least one destination")
    if len(set(destinations)) != len(destinations):
      raise ValueError("remote CB destinations must be unique")
    for core in destinations:
      _coordinate(core)
    _aligned(self.l1_address, "remote CB L1 address")
    if type(self.depth) is not int or self.depth <= 0:
      raise ValueError("remote CB depth must be positive")
    _aligned(self.page_bytes, "remote CB page size")
    if not 0 < self.page_bytes <= MAX_BURST_BYTES:
      raise ValueError("remote CB page size must be in [16, 16384]")
    if self.l1_address + self.depth * self.page_bytes > TensixL1.DATA_BUFFER_SPACE_END:
      raise ValueError("remote CB payload does not fit in usable L1")
    if self.noc not in (0, 1):
      raise ValueError("NoC index must be zero or one")
    if type(self.sync_slot) is not int or not 0 <= self.sync_slot < 32:
      raise ValueError("physical CB synchronization slot must be in [0, 31]")
    if type(self.command_slot) is not int or not 0 <= self.command_slot < 4:
      raise ValueError("NoC command-buffer slot must be in [0, 3]")
    if type(self.tid) is not int or not 0 <= self.tid <= 15:
      raise ValueError("NoC transaction id must be in [0, 15]")
    for start, end in _rectangles(destinations):
      if start != end and (start[0] in (8, 9) or end[0] in (8, 9)):
        raise ValueError("multicast endpoints cannot use NoC columns 8 or 9")
    object.__setattr__(self, "destinations", destinations)

  @property
  def niu(self):
    return NIU0 + self.noc * NIU_STRIDE

  @property
  def command(self):
    return self.niu + self.command_slot * COMMAND_BUFFER_STRIDE

  @property
  def capacity_bytes(self):
    return self.depth * self.page_bytes

  @property
  def rectangles(self):
    return _rectangles(self.destinations)


def _store(k: Asm, base: Reg, offset: int, value: int | Reg, scratch: Reg):
  if is_reg(value):
    k.sw(value, base, offset)
  elif value:
    k.li(scratch, value)
    k.sw(scratch, base, offset)
  else:
    k.sw(R.ZERO, base, offset)


def _wait_ready(k: Asm, command: Reg):
  busy = k.reg()
  again = k._new_label("remote_cb_command_ready")
  k.label(again)
  k.lw(busy, command, COMMAND_SEND)
  k.bne(busy, R.ZERO, again)


def _wait_zero(k: Asm, base: Reg, offset: int):
  value = k.reg()
  again = k._new_label("remote_cb_counter_zero")
  k.label(again)
  k.lw(value, base, offset)
  k.bne(value, R.ZERO, again)
  k.fence()


def _local_coordinate(k: Asm, config: RemoteCBConfig):
  coordinate, address = k.reg(2)
  k.li(address, config.niu + NIU_CONFIG + LOGICAL_NODE_ID)
  k.lw(coordinate, address)
  k.slli(coordinate, coordinate, 20)
  k.srli(coordinate, coordinate, 20)
  return coordinate


def _rectangle_coordinate(config: RemoteCBConfig, start, end):
  low, high = (end, start) if config.noc == 0 else (start, end)
  return _coordinate(low) | _coordinate(high) << 12


def _is_multicast(rectangle):
  return rectangle[0] != rectangle[1]


def _control(multicast, inline=False):
  vc = 4 if multicast else 1
  return (
    WRITE | (WRITE_INLINE if inline else 0) |
    (MULTICAST if multicast else 0) | VC_STATIC | vc << VC_SHIFT
  )


def _submit_payload(k: Asm, config: RemoteCBConfig, command: Reg,
                    local: Reg, source: Reg, target: Reg, byte_count: Reg,
                    rectangle):
  multicast = _is_multicast(rectangle)
  coordinate = (
    _rectangle_coordinate(config, *rectangle) if multicast else
    _coordinate(rectangle[0])
  )
  _wait_ready(k, command)
  scratch = k.reg()
  for index, word in enumerate((
    source, 0, local, target, 0, coordinate,
    config.tid << TID_SHIFT, _control(multicast), byte_count, 0, 0, 0,
  )):
    _store(k, command, index * 4, word, scratch)
  _store(k, command, COMMAND_SEND, 1, scratch)


def _submit_received(k: Asm, config: RemoteCBConfig, command: Reg,
                     pages: Reg, rectangle):
  multicast = _is_multicast(rectangle)
  coordinate = (
    _rectangle_coordinate(config, *rectangle) if multicast else
    _coordinate(rectangle[0])
  )
  _wait_ready(k, command)
  scratch = k.reg()
  received = CB_RECEIVED + config.sync_slot * CB_SYNC_STRIDE
  for index, word in enumerate((
    received, 0, coordinate, 0, 0, 0,
    config.tid << TID_SHIFT, _control(multicast, inline=True), 0xF, 0,
    pages, 0,
  )):
    _store(k, command, index * 4, word, scratch)
  _store(k, command, COMMAND_SEND, 1, scratch)


def emit_send_pages(k: Asm, config: RemoteCBConfig, page_count_param=0,
                    last_page_bytes_param=1):
  """Send ready CB pages, copying only valid bytes from the final page."""
  if k.role not in ("brisc", "ncrisc"):
    raise ValueError("only BRISC and NCRISC can issue remote CB sends")
  for slot in (page_count_param, last_page_bytes_param):
    if type(slot) is not int or not 0 <= slot < TensixL1.PARAM_SLOTS:
      raise ValueError(
        "remote CB parameter slot is outside the raw parameter table",
      )

  parameter, pages, last_page_bytes = k.reg(3)
  k.li(parameter, TensixL1.PARAM_BASE + page_count_param * 4)
  k.lw(pages, parameter)
  k.li(parameter, TensixL1.PARAM_BASE + last_page_bytes_param * 4)
  k.lw(last_page_bytes, parameter)

  # Runtime contract: zero pages has a zero-byte tail. Otherwise page_count
  # fits the configured CB and the final page contains 1..page_bytes bytes.
  capacity, page, byte_count = k.reg(3)
  nonempty = k._new_label("remote_cb_nonempty")
  valid = k._new_label("remote_cb_size_valid")
  empty = k._new_label("remote_cb_empty")
  invalid = k._new_label("remote_cb_size_invalid")
  k.bne(pages, R.ZERO, nonempty)
  k.bne(last_page_bytes, R.ZERO, invalid)
  k.j(empty)
  k.label(nonempty)
  k.li(capacity, config.depth)
  k.bltu(capacity, pages, invalid)
  k.beq(last_page_bytes, R.ZERO, invalid)
  k.li(page, config.page_bytes)
  k.bltu(page, last_page_bytes, invalid)
  complete_pages = k.reg()
  k.addi(complete_pages, pages, -1)
  k.mul(byte_count, complete_pages, page)
  k.add(byte_count, byte_count, last_page_bytes)
  k.j(valid)
  k.label(invalid)
  k.j(invalid)
  k.label(valid)

  niu, command, source, target = k.reg(4)
  k.li(niu, config.niu)
  k.li(command, config.command)
  k.li(source, config.l1_address)
  k.li(target, config.l1_address)
  local = _local_coordinate(k, config)
  _wait_zero(k, niu, STATUS + WRITES_OUTGOING + config.tid * 4)

  remaining, burst = k.reg(2)
  k.mv(remaining, byte_count)
  # Coalesce whatever contiguous CB prefix the caller made available, up to
  # the hardware request limit. A one-page steady-state send is still one
  # request; an eight-page ready run can become one 16 KiB request.
  k.li(burst, MAX_BURST_BYTES)
  loop = k._new_label("remote_cb_payload")
  done = k._new_label("remote_cb_payload_done")
  k.label(loop)
  k.beq(remaining, R.ZERO, done)
  chunk = k.reg()
  have_chunk = k._new_label("remote_cb_chunk")
  k.mv(chunk, remaining)
  k.bltu(remaining, burst, have_chunk)
  k.mv(chunk, burst)
  k.label(have_chunk)
  for rectangle in config.rectangles:
    _submit_payload(
      k, config, command, local, source, target, chunk, rectangle,
    )
  k.add(source, source, chunk)
  k.add(target, target, chunk)
  k.sub(remaining, remaining, chunk)
  k.j(loop)
  k.label(done)
  _wait_ready(k, command)
  _wait_zero(k, niu, STATUS + WRITES_OUTGOING + config.tid * 4)

  # Payload and notification use the same per-target VC, so credit cannot pass
  # its data. Receiver observation is remote completion.
  for rectangle in config.rectangles:
    _submit_received(k, config, command, pages, rectangle)
  _wait_ready(k, command)
  k.label(empty)
  return k


def emit_wait_and_pop_pages(k: Asm, config: RemoteCBConfig,
                            page_count_param=0, delay_cycles=0):
  """Wait and pop one remote page at a time, with optional consumer delay."""
  if (type(page_count_param) is not int or
      not 0 <= page_count_param < TensixL1.PARAM_SLOTS):
    raise ValueError("remote CB receive parameter is outside the raw parameter table")
  if type(delay_cycles) is not int or delay_cycles < 0:
    raise ValueError("remote CB consumer delay must be non-negative")
  parameter, pages = k.reg(2)
  k.li(parameter, TensixL1.PARAM_BASE + page_count_param * 4)
  k.lw(pages, parameter)

  received_address = CB_RECEIVED + config.sync_slot * CB_SYNC_STRIDE
  acked_address = CB_ACKED + config.sync_slot * CB_SYNC_STRIDE
  received, acked, available, address = k.reg(4)
  k.li(address, acked_address)
  k.lhu(acked, address)
  consume = k._new_label("remote_cb_consume")
  done = k._new_label("remote_cb_consume_done")
  k.label(consume)
  k.beq(pages, R.ZERO, done)
  wait = k._new_label("remote_cb_wait")
  ready = k._new_label("remote_cb_ready")
  k.label(wait)
  k.li(address, received_address)
  k.lhu(received, address)
  k.sub(available, received, acked)
  k.slli(available, available, 16)
  k.srli(available, available, 16)
  one = k.reg()
  k.li(one, 1)
  k.bgeu(available, one, ready)
  k.fence()
  k.j(wait)
  k.label(ready)
  k.fence()
  if delay_cycles:
    delay = k.reg()
    delay_loop = k._new_label("remote_cb_consumer_delay")
    k.li(delay, delay_cycles)
    k.label(delay_loop)
    k.addi(delay, delay, -1)
    k.bne(delay, R.ZERO, delay_loop)
  k.addi(acked, acked, 1)
  k.slli(acked, acked, 16)
  k.srli(acked, acked, 16)
  k.li(address, acked_address)
  k.sw(acked, address)
  k.addi(pages, pages, -1)
  k.fence()
  k.j(consume)
  k.label(done)
  k.fence()
  return k
