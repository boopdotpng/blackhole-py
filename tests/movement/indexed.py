"""Direct RISC-V indexed interleaved-DRAM movement proofs.

These helpers are not embedding operations. They implement the lower-level
row gather/scatter pattern: load a u32 index from L1, turn its logical byte
offset into an interleaved bank and bank-local address, and issue ordinary NoC
reads or writes. An embedding forward kernel is one consumer of gather.

Scatter is an overwrite operation. Requests are drained after each row so a
repeated index deterministically leaves the last source row. Scatter-add is a
separate reduction and is intentionally not implied here.
"""

from dataclasses import dataclass

from asm import Asm
from fw.consts import TensixL1
from isa import R, Reg


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
RESPONSE_MARKED = 1 << 4
VC_STATIC = 1 << 7
VC_SHIFT = 13
TID_SHIFT = 10
MAX_PACKET_BYTES = 16 * 1024


def _aligned(value, name, alignment):
  if type(value) is not int or value < 0 or value % alignment:
    raise ValueError(
      f"{name} must be a non-negative, {alignment}-byte-aligned integer",
    )
  return value


@dataclass(frozen=True)
class IndexedConfig:
  """Static layout for one generated indexed row-transfer loop."""

  dram_coordinates: tuple[int, ...]
  indices_l1_address: int
  rows_l1_address: int
  row_count: int
  row_bytes: int
  page_bytes: int = 2048
  noc: int = 0
  tid: int = 2
  command_slot: int = 0
  static_vc: int = 1

  def __post_init__(self):
    coordinates = tuple(self.dram_coordinates)
    if not 1 <= len(coordinates) <= 8:
      raise ValueError("indexed movement requires between one and eight banks")
    if any(type(value) is not int or not 0 <= value < 1 << 12
           for value in coordinates):
      raise ValueError("DRAM coordinates must be packed 12-bit coordinates")
    _aligned(self.indices_l1_address, "index-list address", 4)
    _aligned(self.rows_l1_address, "row-buffer address", 16)
    if type(self.row_count) is not int or self.row_count <= 0:
      raise ValueError("indexed row count must be positive")
    _aligned(self.row_bytes, "row size", 16)
    if self.row_bytes == 0:
      raise ValueError("row size must be positive")
    _aligned(self.page_bytes, "interleaved page size", 16)
    if not 0 < self.page_bytes <= MAX_PACKET_BYTES:
      raise ValueError("page size must be in [16, 16384]")
    index_end = self.indices_l1_address + self.row_count * 4
    rows_end = self.rows_l1_address + self.row_count * self.row_bytes
    if index_end > TensixL1.DATA_BUFFER_SPACE_END:
      raise ValueError("index list does not fit in usable L1")
    if rows_end > TensixL1.DATA_BUFFER_SPACE_END:
      raise ValueError("indexed row buffer does not fit in usable L1")
    if not (index_end <= self.rows_l1_address or
            rows_end <= self.indices_l1_address):
      raise ValueError("index list and row buffer overlap")
    if self.noc not in (0, 1):
      raise ValueError("NoC index must be zero or one")
    if type(self.tid) is not int or not 0 <= self.tid <= 15:
      raise ValueError("NoC transaction id must be in [0, 15]")
    if type(self.command_slot) is not int or not 0 <= self.command_slot < 4:
      raise ValueError("NoC command-buffer slot must be in [0, 3]")
    if type(self.static_vc) is not int or not 0 <= self.static_vc <= 5:
      raise ValueError("static VC must be in [0, 5]")
    object.__setattr__(self, "dram_coordinates", coordinates)

  @property
  def niu(self):
    return NIU0 + self.noc * NIU_STRIDE

  @property
  def command(self):
    return self.niu + self.command_slot * COMMAND_BUFFER_STRIDE


def _parameter(k: Asm, slot: int):
  if type(slot) is not int or not 0 <= slot < TensixL1.PARAM_SLOTS:
    raise ValueError("indexed parameter slot is outside the raw parameter table")
  address, value = k.reg(2)
  k.li(address, TensixL1.PARAM_BASE + slot * 4)
  k.lw(value, address)
  return value


def _check_aligned(k: Asm, value: Reg):
  low = k.reg()
  invalid = k._new_label("indexed_unaligned_base")
  valid = k._new_label("indexed_aligned_base")
  k.andi(low, value, 15)
  k.bne(low, R.ZERO, invalid)
  k.j(valid)
  k.label(invalid)
  k.j(invalid)
  k.label(valid)


def _coordinate_table(k: Asm, coordinates):
  address = k.local.alloc(4 * len(coordinates))
  for index, coordinate in enumerate(coordinates):
    k.initialize_local(address + index * 4, coordinate)
  return address


def _select_coordinate(k: Asm, bank: Reg, table: Reg):
  address, coordinate = k.reg(2)
  k.slli(address, bank, 2)
  k.add(address, address, table)
  k.lw(coordinate, address)
  return coordinate


def _local_coordinate(k: Asm, config: IndexedConfig):
  address, coordinate = k.reg(2)
  k.li(address, config.niu + NIU_CONFIG + LOGICAL_NODE_ID)
  k.lw(coordinate, address)
  k.slli(coordinate, coordinate, 20)
  k.srli(coordinate, coordinate, 20)
  return coordinate


def _wait_command(k: Asm, command: Reg):
  busy = k.reg()
  again = k._new_label("indexed_command_ready")
  k.label(again)
  k.lw(busy, command, COMMAND_SEND)
  k.bne(busy, R.ZERO, again)


def _wait_zero(k: Asm, niu: Reg, offset: int):
  value = k.reg()
  again = k._new_label("indexed_completion")
  k.label(again)
  k.lw(value, niu, offset)
  k.bne(value, R.ZERO, again)
  k.fence()


def _submit(k: Asm, command: Reg, source_address: Reg,
            source_coordinate: Reg, target_address: Reg,
            target_coordinate: Reg, byte_count: Reg):
  _wait_command(k, command)
  k.sw(source_address, command, 0)
  k.sw(source_coordinate, command, 8)
  k.sw(target_address, command, 12)
  k.sw(target_coordinate, command, 20)
  k.sw(byte_count, command, 32)
  send = k.reg()
  k.li(send, 1)
  k.sw(send, command, COMMAND_SEND)


def _emit_indexed_rows(k: Asm, config: IndexedConfig, dram_base_param: int,
                       *, write: bool):
  if k.role != "brisc":
    raise ValueError("the indexed movement POC runs on BRISC")

  dram_base = _parameter(k, dram_base_param)
  _check_aligned(k, dram_base)
  local = _local_coordinate(k, config)
  coordinate_table, niu, command = k.reg(3)
  k.li(coordinate_table, _coordinate_table(k, config.dram_coordinates))
  k.li(niu, config.niu)
  k.li(command, config.command)
  _wait_zero(
    k, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4,
  )
  if write:
    _wait_zero(k, niu, STATUS + WRITES_OUTGOING + config.tid * 4)

  control = (
    RESPONSE_MARKED | (WRITE if write else 0) | VC_STATIC |
    config.static_vc << VC_SHIFT
  )
  scratch = k.reg()
  for offset, value in (
    (4, 0), (16, 0), (24, config.tid << TID_SHIFT),
    (28, control), (36, 0), (40, 0), (44, 0),
  ):
    if value:
      k.li(scratch, value)
      k.sw(scratch, command, offset)
    else:
      k.sw(R.ZERO, command, offset)

  index_pointer, row_pointer, rows_remaining = k.reg(3)
  k.li(index_pointer, config.indices_l1_address)
  k.li(row_pointer, config.rows_l1_address)
  k.li(rows_remaining, config.row_count)
  page_bytes, bank_count, row_bytes = k.reg(3)
  k.li(page_bytes, config.page_bytes)
  k.li(bank_count, len(config.dram_coordinates))
  k.li(row_bytes, config.row_bytes)
  if not write:
    # Bound marked read responses well below the eight-bit TID counter wrap.
    # The starting logical offset can make one row touch one more page than
    # ceil(row_bytes / page_bytes), so size the batch conservatively.
    max_chunks = (
      config.row_bytes + 2 * config.page_bytes - 17
    ) // config.page_bytes
    gather_batch_rows = max(1, 128 // max_chunks)
    batch_rows_remaining = k.reg()
    k.li(batch_rows_remaining, gather_batch_rows)

  row_loop = k._new_label("indexed_row")
  all_done = k._new_label("indexed_rows_done")
  k.label(row_loop)
  k.beq(rows_remaining, R.ZERO, all_done)
  index, logical_offset = k.reg(2)
  k.lw(index, index_pointer)
  k.mul(logical_offset, index, row_bytes)
  remaining, l1_address = k.reg(2)
  k.mv(remaining, row_bytes)
  k.mv(l1_address, row_pointer)

  chunk_loop = k._new_label("indexed_chunk")
  row_done = k._new_label("indexed_row_done")
  k.label(chunk_loop)
  k.beq(remaining, R.ZERO, row_done)
  logical_page, within_page, bank, bank_row = k.reg(4)
  k.divu(logical_page, logical_offset, page_bytes)
  k.remu(within_page, logical_offset, page_bytes)
  k.remu(bank, logical_page, bank_count)
  k.divu(bank_row, logical_page, bank_count)
  remote_address, remote_offset = k.reg(2)
  k.mul(remote_offset, bank_row, page_bytes)
  k.add(remote_address, dram_base, remote_offset)
  k.add(remote_address, remote_address, within_page)
  remote_coordinate = _select_coordinate(
    k, bank, coordinate_table,
  )

  chunk = k.reg()
  k.sub(chunk, page_bytes, within_page)
  have_chunk = k._new_label("indexed_have_chunk")
  k.bltu(chunk, remaining, have_chunk)
  k.mv(chunk, remaining)
  k.label(have_chunk)
  if write:
    _submit(
      k, command, l1_address, local, remote_address, remote_coordinate,
      chunk,
    )
  else:
    _submit(
      k, command, remote_address, remote_coordinate, l1_address, local,
      chunk,
    )
  k.add(logical_offset, logical_offset, chunk)
  k.add(l1_address, l1_address, chunk)
  k.sub(remaining, remaining, chunk)
  k.j(chunk_loop)

  k.label(row_done)
  if write:
    # This gives repeated scatter destinations deterministic last-write-wins
    # ordering. Duplicate-free lowering may use a less restrictive variant.
    _wait_command(k, command)
    _wait_zero(k, niu, STATUS + WRITES_OUTGOING + config.tid * 4)
    _wait_zero(
      k, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4,
    )
  else:
    continue_rows = k._new_label("indexed_gather_continue")
    k.addi(batch_rows_remaining, batch_rows_remaining, -1)
    k.bne(batch_rows_remaining, R.ZERO, continue_rows)
    _wait_command(k, command)
    _wait_zero(
      k, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4,
    )
    k.li(batch_rows_remaining, gather_batch_rows)
    k.label(continue_rows)
  k.addi(index_pointer, index_pointer, 4)
  k.add(row_pointer, row_pointer, row_bytes)
  k.addi(rows_remaining, rows_remaining, -1)
  k.j(row_loop)
  k.label(all_done)
  if not write:
    _wait_command(k, command)
    _wait_zero(
      k, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4,
    )
  return k


def emit_indexed_gather(k: Asm, config: IndexedConfig, dram_base_param=0):
  """Gather indexed interleaved-DRAM rows into dense row-major L1."""
  return _emit_indexed_rows(k, config, dram_base_param, write=False)


def emit_indexed_scatter(k: Asm, config: IndexedConfig, dram_base_param=0):
  """Scatter dense L1 rows into indexed interleaved-DRAM rows."""
  return _emit_indexed_rows(k, config, dram_base_param, write=True)
