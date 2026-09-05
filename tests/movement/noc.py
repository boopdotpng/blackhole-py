"""Direct RISC-V emitters for the movement NoC proofs.

This is deliberately test-local and deliberately does not import ``ttk``.
Every NoC request below is built by writing the Blackhole NIU command buffer
from the worker RISC.
"""

from dataclasses import dataclass

from asm import Asm
from fw.consts import TensixL1
from isa import R, Reg, is_reg


NIU0 = 0xFFB20000
NIU_STRIDE = 0x10000
COMMAND_BUFFER_STRIDE = 0x800
COMMAND_BUFFER_COUNT = 4
NIU_CONFIG = 0x100
LOGICAL_NODE_ID = 0x48

COMMAND_SEND = 0x40
STATUS = 0x200
REQUESTS_OUTSTANDING = 0x40
WRITES_OUTGOING = 0x80

CB_ACKED = 0xFFB48020
CB_RECEIVED = 0xFFB48028
CB_SYNC_STRIDE = 0x1000

TID = 1
VC_STATIC = 1 << 7
VC_SHIFT = 13
PRIORITY_SHIFT = 27
RESPONSE_MARKED = 1 << 4
WRITE = 1 << 1


def _aligned(value, name):
  if type(value) is not int or value < 0 or value % 16:
    raise ValueError(f"{name} must be a non-negative, 16-byte-aligned integer")
  return value


@dataclass(frozen=True)
class InterleavedConfig:
  """Static portion of one interleaved DRAM/L1 movement kernel.

  Logical pages are striped over ``dram_coordinates``. Page ``i`` lives at
  coordinate ``i % banks`` and address ``dram_base + i // banks * page_bytes``.
  The L1 side is a dense, contiguous CB payload region.
  """

  dram_coordinates: tuple[int, ...]
  l1_address: int
  depth: int = 2
  page_bytes: int = 2048
  noc: int = 0
  tid: int = TID
  sync_slot: int = 0
  command_slot: int = 0
  batch_pages: int | None = None
  posted_write: bool = False
  static_vc: int | None = 1
  priority: int = 0
  standalone: bool = False

  def __post_init__(self):
    coordinates = tuple(self.dram_coordinates)
    if not 1 <= len(coordinates) <= 8:
      raise ValueError("movement proof supports between one and eight banks")
    if any(type(coord) is not int or not 0 <= coord < 1 << 12 for coord in coordinates):
      raise ValueError("DRAM coordinates must be packed 12-bit NoC coordinates")
    _aligned(self.l1_address, "L1 address")
    if type(self.depth) is not int or self.depth <= 0 or self.depth >= 1 << 16:
      raise ValueError("CB depth must be in [1, 65535]")
    _aligned(self.page_bytes, "DRAM page size")
    if self.page_bytes == 0:
      raise ValueError("DRAM page size must be positive")
    if self.page_bytes > 16 * 1024:
      raise ValueError("DRAM page size cannot exceed the 16 KiB NoC burst size")
    if self.l1_address + self.l1_bytes > TensixL1.DATA_BUFFER_SPACE_END:
      raise ValueError("CB payload does not fit in the usable L1 data arena")
    if self.noc not in (0, 1):
      raise ValueError("NoC index must be zero or one")
    if type(self.tid) is not int or not 0 <= self.tid <= 15:
      raise ValueError("NoC transaction id must be in [0, 15]")
    if type(self.sync_slot) is not int or not 0 <= self.sync_slot < 32:
      raise ValueError("physical CB synchronization slot must be in [0, 31]")
    if type(self.command_slot) is not int or not 0 <= self.command_slot < COMMAND_BUFFER_COUNT:
      raise ValueError("NoC command-buffer slot must be in [0, 3]")
    if self.batch_pages is not None and (
      type(self.batch_pages) is not int or
      not 0 < self.batch_pages <= min(self.depth, 128)
    ):
      raise ValueError("issue batch must be in [1, min(CB depth, 128)]")
    if type(self.posted_write) is not bool:
      raise ValueError("posted_write must be a bool")
    if self.static_vc is not None and (
      type(self.static_vc) is not int or not 0 <= self.static_vc <= 5
    ):
      raise ValueError("static VC must be None or in [0, 5]")
    if type(self.priority) is not int or not 0 <= self.priority <= 15:
      raise ValueError("NoC arbitration priority must be in [0, 15]")
    if type(self.standalone) is not bool:
      raise ValueError("standalone must be a bool")
    object.__setattr__(self, "dram_coordinates", coordinates)

  @property
  def niu(self): return NIU0 + self.noc * NIU_STRIDE

  @property
  def command(self): return self.niu + self.command_slot * COMMAND_BUFFER_STRIDE

  @property
  def l1_bytes(self): return self.depth * self.page_bytes

  @property
  def issue_depth(self):
    return min(self.depth, 128) if self.batch_pages is None else self.batch_pages


def _store_word(k: Asm, command: Reg, offset: int, value: int | Reg,
                scratch: Reg):
  if is_reg(value):
    k.sw(value, command, offset)
  elif value == 0:
    k.sw(R.ZERO, command, offset)
  else:
    k.li(scratch, value); k.sw(scratch, command, offset)


def _wait_zero(k: Asm, command: Reg, offset: int):
  current = k.reg()
  again = k._new_label("noc_wait_zero")
  k.label(again)
  k.lw(current, command, offset)
  k.bne(current, R.ZERO, again)
  k.fence()


def _local_coordinate(k: Asm, config: InterleavedConfig):
  coordinate, address = k.reg(2)
  k.li(address, config.niu + NIU_CONFIG + LOGICAL_NODE_ID)
  k.lw(coordinate, address)
  k.slli(coordinate, coordinate, 20)
  k.srli(coordinate, coordinate, 20)
  return coordinate


def _coordinate_table(k: Asm, coordinates: tuple[int, ...]):
  tables = getattr(k, "_movement_coordinate_tables", None)
  if tables is None:
    tables = k._movement_coordinate_tables = {}
  if coordinates not in tables:
    address = k.local.alloc(4 * len(coordinates))
    for index, coordinate in enumerate(coordinates):
      k.initialize_local(address + index * 4, coordinate)
    tables[coordinates] = address
  return tables[coordinates]


def _select_coordinate(k: Asm, bank: Reg, table: Reg):
  coordinate, address = k.reg(2)
  k.slli(address, bank, 2)
  k.add(address, address, table)
  k.lw(coordinate, address)
  return coordinate


def _wait_command_ready(k: Asm, command: Reg):
  busy = k.reg()
  ready = k._new_label("noc_command_ready")
  k.label(ready)
  k.lw(busy, command, COMMAND_SEND)
  k.bne(busy, R.ZERO, ready)


def _initialize_command(k: Asm, command: Reg, control: int, tid: int):
  """Write the invariant NIU words once before the transfer loop."""
  scratch = k.reg()
  for index, word in enumerate((0, 0, 0, 0, 0, 0,
                                tid << 10, control, 0, 0, 0, 0)):
    _store_word(k, command, index * 4, word, scratch)


def _control(config: InterleavedConfig, *, write: bool):
  control = WRITE if write else RESPONSE_MARKED
  if write and not config.posted_write:
    control |= RESPONSE_MARKED
  if config.static_vc is not None:
    control |= VC_STATIC | config.static_vc << VC_SHIFT
  return control | config.priority << PRIORITY_SHIFT


def _submit(k: Asm, command: Reg, *, source_address: Reg,
            source_coordinate: Reg, target_address: Reg,
            target_coordinate: Reg, byte_count: Reg):
  """Update five request-dependent words and submit one request.

  The next submission waits before reusing the slot. The caller waits once
  more after the final submission before inspecting completion counters. This
  avoids the redundant second ready-register read on every request while still
  making the last command visible to the counter drain.
  """
  _wait_command_ready(k, command)

  k.sw(source_address, command, 0)
  k.sw(source_coordinate, command, 8)
  k.sw(target_address, command, 12)
  k.sw(target_coordinate, command, 20)
  k.sw(byte_count, command, 32)
  send = k.reg()
  k.li(send, 1)
  k.sw(send, command, COMMAND_SEND)


def _check_runtime_address(k: Asm, dram: Reg):
  """Refuse to issue NoC traffic from an unaligned dynamic DRAM base."""
  alignment = k.reg()
  invalid = k._new_label("invalid_movement_args")
  valid = k._new_label("valid_movement_args")
  k.andi(alignment, dram, 15)
  k.bne(alignment, R.ZERO, invalid)
  k.j(valid)
  k.label(invalid)
  k.j(invalid)
  k.label(valid)


def _cb_counter(config: InterleavedConfig, received: bool):
  # The POC defaults to physical slot zero. Later lowering will allocate this
  # exactly as it allocates other scarce hardware resources.
  base = CB_RECEIVED if received else CB_ACKED
  return base + config.sync_slot * CB_SYNC_STRIDE


def _wait_issue_capacity(k: Asm, niu: Reg, config: InterleavedConfig,
                         count: Reg):
  """Keep a marked-response TID below the safe half of its 8-bit range."""
  current, limit = k.reg(2)
  again = k._new_label("noc_issue_capacity")
  ready = k._new_label("noc_issue_capacity_ready")
  k.label(again)
  k.lw(current, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4)
  k.li(limit, 129)
  k.sub(limit, limit, count)
  k.bltu(current, limit, ready)
  k.fence()
  k.j(again)
  k.label(ready)


def _wait_cb(k: Asm, config: InterleavedConfig, counter: Reg, count: Reg,
             *, producer: bool):
  """Wait for ``count`` producer/consumer credits in the hardware counters."""
  other, difference, depth, available, address = k.reg(5)
  k.li(address, _cb_counter(config, received=not producer))
  again = k._new_label("cb_reserve" if producer else "cb_wait")
  ready = k._new_label("cb_reserved" if producer else "cb_ready")
  k.label(again)
  k.lhu(other, address)
  k.sub(difference, counter, other) if producer else k.sub(difference, other, counter)
  k.slli(difference, difference, 16)
  k.srli(difference, difference, 16)
  if producer:
    k.li(depth, config.depth)
    k.sub(available, depth, difference)
    k.bgeu(available, count, ready)
  else:
    k.bgeu(difference, count, ready)
  k.fence()
  k.j(again)
  k.label(ready)
  k.fence()


def _publish_cb(k: Asm, config: InterleavedConfig, counter: Reg, count: Reg,
                *, producer: bool):
  address = k.reg()
  k.add(counter, counter, count)
  k.slli(counter, counter, 16)
  k.srli(counter, counter, 16)
  k.li(address, _cb_counter(config, received=producer))
  k.sw(counter, address)
  k.fence()


def emit_interleaving_benchmark(k: Asm, config: InterleavedConfig,
                                dram_param=0, byte_count_param=1):
  """Emit the page-to-bank/address loop without issuing NoC requests.

  Put one ordinary profiler interval around this helper. It executes the same
  dynamic bank selection, partial-page sizing, and address rollover as the real
  transfer without adding timestamp stores between live NoC requests.
  """
  dram, remaining, bank, page, banks, parameter, coordinates = k.reg(7)
  k.li(parameter, TensixL1.PARAM_BASE + dram_param * 4)
  k.lw(dram, parameter)
  k.li(parameter, TensixL1.PARAM_BASE + byte_count_param * 4)
  k.lw(remaining, parameter)
  k.li(bank, 0)
  k.li(page, config.page_bytes)
  k.li(banks, len(config.dram_coordinates))
  k.li(coordinates, _coordinate_table(k, config.dram_coordinates))

  loop = k._new_label("interleaving_benchmark")
  done = k._new_label("interleaving_benchmark_done")
  have_chunk = k._new_label("interleaving_benchmark_chunk")
  next_page = k._new_label("interleaving_benchmark_next")
  k.label(loop)
  k.beq(remaining, R.ZERO, done)
  chunk = k.reg()
  k.mv(chunk, remaining)
  k.bltu(remaining, page, have_chunk)
  k.mv(chunk, page)
  k.label(have_chunk)
  _select_coordinate(k, bank, coordinates)
  k.sub(remaining, remaining, chunk)
  k.addi(bank, bank, 1)
  k.bltu(bank, banks, next_page)
  k.li(bank, 0)
  k.add(dram, dram, page)
  k.label(next_page)
  k.j(loop)
  k.label(done)
  return k


def _emit_interleaved_transfer(k: Asm, config: InterleavedConfig,
                               dram_param: int, byte_count_param: int,
                               *, write: bool):
  if k.role not in ("brisc", "ncrisc"):
    raise ValueError("only BRISC and NCRISC can issue NoC requests")
  for slot in (dram_param, byte_count_param):
    if type(slot) is not int or not 0 <= slot < TensixL1.PARAM_SLOTS:
      raise ValueError("movement parameter slot is outside the raw parameter table")

  dram, remaining, l1, bank, page, banks, niu, command, coordinates = k.reg(9)
  parameter = k.reg()
  k.li(parameter, TensixL1.PARAM_BASE + dram_param * 4)
  k.lw(dram, parameter)
  k.li(parameter, TensixL1.PARAM_BASE + byte_count_param * 4)
  k.lw(remaining, parameter)
  _check_runtime_address(k, dram)

  local = _local_coordinate(k, config)
  k.li(l1, config.l1_address)
  k.li(bank, 0)
  k.li(page, config.page_bytes)
  k.li(banks, len(config.dram_coordinates))
  k.li(niu, config.niu)
  k.li(command, config.command)
  k.li(coordinates, _coordinate_table(k, config.dram_coordinates))
  cb_counter = k.reg()
  if config.standalone:
    # A standalone bandwidth stream owns its entire staging ring. Completion
    # is drained before each batch is recycled, so no peer credit counter is
    # needed and no compute RISC has to participate in the benchmark.
    k.li(cb_counter, 0)
  else:
    cb_counter_address = k.reg()
    k.li(cb_counter_address, _cb_counter(config, received=not write))
    k.lhu(cb_counter, cb_counter_address)

  # Begin from a fully drained TID. Later batches retain safe overlap while the
  # issue-capacity check keeps marked responses away from eight-bit wraparound.
  if not write or not config.posted_write:
    _wait_zero(k, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4)
  if write:
    _wait_zero(k, niu, STATUS + WRITES_OUTGOING + config.tid * 4)
  _initialize_command(
    k, command, _control(config, write=write), config.tid,
  )

  batch = k._new_label("interleaved_batch")
  done = k._new_label("interleaved_transfer_done")
  k.label(batch)
  k.beq(remaining, R.ZERO, done)

  # Exchange up to one configured issue batch at a time. All requests in the
  # batch are submitted before either side drains its source-completion state,
  # allowing banks to overlap while CB capacity remains independently tunable.
  batch_bytes, cb_bytes, batch_remaining, slots = k.reg(4)
  short_batch = k._new_label("short_cb_batch")
  have_batch = k._new_label("have_cb_batch")
  k.mv(batch_bytes, remaining)
  k.li(cb_bytes, config.issue_depth * config.page_bytes)
  k.bltu(remaining, cb_bytes, short_batch)
  k.mv(batch_bytes, cb_bytes)
  k.j(have_batch)
  k.label(short_batch)
  k.label(have_batch)
  page_minus_one = k.reg()
  k.addi(page_minus_one, page, -1)
  k.add(slots, batch_bytes, page_minus_one)
  k.divu(slots, slots, page)

  if not config.standalone:
    _wait_cb(k, config, cb_counter, slots, producer=not write)
  if write and not config.posted_write:
    _wait_issue_capacity(k, niu, config, slots)

  # Start this batch at the producer/consumer's monotonic ring position. The
  # two counters remain independent; their distance is the CB occupancy.
  ring_slot, depth, ring_offset, cb_end = k.reg(4)
  k.li(depth, config.depth)
  k.remu(ring_slot, cb_counter, depth)
  k.mul(ring_offset, ring_slot, page)
  k.li(l1, config.l1_address)
  k.add(l1, l1, ring_offset)
  k.li(cb_end, config.l1_address + config.l1_bytes)
  k.mv(batch_remaining, batch_bytes)
  issue = k._new_label("interleaved_issue")
  issued = k._new_label("interleaved_issued")
  k.label(issue)
  k.beq(batch_remaining, R.ZERO, issued)

  chunk = k.reg()
  have_chunk = k._new_label("interleaved_chunk")
  k.mv(chunk, batch_remaining)
  k.bltu(batch_remaining, page, have_chunk)
  k.mv(chunk, page)
  k.label(have_chunk)
  remote = _select_coordinate(k, bank, coordinates)

  if write:
    _submit(
      k, command,
      source_address=l1, source_coordinate=local,
      target_address=dram, target_coordinate=remote,
      byte_count=chunk,
    )
  else:
    _submit(
      k, command,
      source_address=dram, source_coordinate=remote,
      target_address=l1, target_coordinate=local,
      byte_count=chunk,
    )

  k.sub(batch_remaining, batch_remaining, chunk)
  k.add(l1, l1, chunk)
  l1_ready = k._new_label("interleaved_l1_ready")
  k.bne(l1, cb_end, l1_ready)
  k.li(l1, config.l1_address)
  k.label(l1_ready)
  k.addi(bank, bank, 1)
  next_page = k._new_label("interleaved_next_page")
  k.bltu(bank, banks, next_page)
  k.li(bank, 0)
  k.add(dram, dram, page)
  k.label(next_page)
  k.j(issue)

  k.label(issued)
  _wait_command_ready(k, command)
  if write:
    _wait_zero(k, niu, STATUS + WRITES_OUTGOING + config.tid * 4)
  else:
    _wait_zero(k, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4)
  if config.standalone:
    k.add(cb_counter, cb_counter, slots)
  else:
    _publish_cb(k, config, cb_counter, slots, producer=not write)
  k.sub(remaining, remaining, batch_bytes)
  k.j(batch)
  k.label(done)
  # Non-posted writes provide an end-to-end correctness fence. Only local
  # payload reads are drained per batch; remote acknowledgements overlap until
  # this final drain (with the issue-capacity check preventing TID wraparound).
  if write and not config.posted_write:
    _wait_zero(k, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4)
  return k


def emit_interleaved_dram_to_l1(k: Asm, config: InterleavedConfig,
                                dram_param=0, byte_count_param=1):
  """Emit interleaved DRAM -> dense L1 CB movement."""
  return _emit_interleaved_transfer(
    k, config, dram_param, byte_count_param, write=False,
  )


def emit_l1_to_interleaved_dram(k: Asm, config: InterleavedConfig,
                                dram_param=0, byte_count_param=1):
  """Emit dense L1 CB -> interleaved DRAM movement."""
  return _emit_interleaved_transfer(
    k, config, dram_param, byte_count_param, write=True,
  )


def _emit_cb_peer(k: Asm, config: InterleavedConfig, byte_count_param: int,
                  *, producer: bool):
  """Generate or discard CB pages without issuing NoC payload traffic."""
  if type(byte_count_param) is not int or not 0 <= byte_count_param < TensixL1.PARAM_SLOTS:
    raise ValueError("movement parameter slot is outside the raw parameter table")
  remaining, parameter, page, counter, counter_address = k.reg(5)
  k.li(parameter, TensixL1.PARAM_BASE + byte_count_param * 4)
  k.lw(remaining, parameter)
  k.li(page, config.page_bytes)
  k.li(counter_address, _cb_counter(config, received=not producer))
  k.lhu(counter, counter_address)

  loop = k._new_label("cb_generate" if producer else "cb_discard")
  done = k._new_label("cb_peer_done")
  k.label(loop)
  k.beq(remaining, R.ZERO, done)
  batch_bytes, limit, slots, page_minus_one = k.reg(4)
  k.mv(batch_bytes, remaining)
  k.li(limit, config.issue_depth * config.page_bytes)
  short = k._new_label("cb_peer_short")
  have_batch = k._new_label("cb_peer_batch")
  k.bltu(remaining, limit, short)
  k.mv(batch_bytes, limit)
  k.j(have_batch)
  k.label(short)
  k.label(have_batch)
  k.addi(page_minus_one, page, -1)
  k.add(slots, batch_bytes, page_minus_one)
  k.divu(slots, slots, page)
  _wait_cb(k, config, counter, slots, producer=producer)
  _publish_cb(k, config, counter, slots, producer=producer)
  k.sub(remaining, remaining, batch_bytes)
  k.j(loop)
  k.label(done)
  return k


def emit_cb_generate(k: Asm, config: InterleavedConfig, byte_count_param=1):
  """Act as a fast producer so an L1->DRAM stream can be timed alone."""
  return _emit_cb_peer(k, config, byte_count_param, producer=True)


def emit_cb_discard(k: Asm, config: InterleavedConfig, byte_count_param=1):
  """Act as a fast consumer so a DRAM->L1 stream can be timed alone."""
  return _emit_cb_peer(k, config, byte_count_param, producer=False)
