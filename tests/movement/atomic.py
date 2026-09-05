"""Direct RISC-V NoC atomic-increment proof for Blackhole.

This module is intentionally test-local and does not import ``ttk``.  The
worker RISC programs one NIU command buffer directly.  The destination is a
32-bit word in another Tensix tile's L1; DRAM is not an atomic target.

Blackhole cannot safely use a genuinely posted atomic under memory-port
contention.  Both modes therefore retain RESP_MARKED in the packet.  The
returning form routes the old value to this tile and drains the response TID.
The fire-and-forget semaphore form routes the unused response to coordinate
zero and relies on the receiver's counter for end-to-end completion.
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

ATOMIC = 1 << 0
RESPONSE_MARKED = 1 << 4
VC_STATIC = 1 << 7
VC_SHIFT = 13
PRIORITY_SHIFT = 27
TID_SHIFT = 10

INCR_GET = 1 << 12
WRAP_32 = 31 << 2


def _word_aligned(value, name):
  if type(value) is not int or value < 0 or value % 4:
    raise ValueError(f"{name} must be a non-negative, 4-byte-aligned integer")
  return value


@dataclass(frozen=True)
class AtomicIncrementConfig:
  """Static NIU choices for a remote 32-bit fetch-add or semaphore signal."""

  noc: int = 0
  tid: int = 1
  command_slot: int = 3
  return_value: bool = True
  return_address: int = TensixL1.DATA_BUFFER_SPACE_BASE
  static_vc: int = 1
  priority: int = 0

  def __post_init__(self):
    if self.noc not in (0, 1):
      raise ValueError("NoC index must be zero or one")
    if type(self.tid) is not int or not 0 <= self.tid <= 15:
      raise ValueError("NoC transaction id must be in [0, 15]")
    if type(self.command_slot) is not int or not 0 <= self.command_slot < COMMAND_BUFFER_COUNT:
      raise ValueError("NoC command-buffer slot must be in [0, 3]")
    if type(self.return_value) is not bool:
      raise ValueError("return_value must be a bool")
    _word_aligned(self.return_address, "atomic return address")
    if self.return_address + 4 > TensixL1.SIZE:
      raise ValueError("atomic return address is outside L1")
    if type(self.static_vc) is not int or not 0 <= self.static_vc <= 3:
      raise ValueError("atomic static VC must be in [0, 3]")
    if type(self.priority) is not int or not 0 <= self.priority <= 15:
      raise ValueError("NoC arbitration priority must be in [0, 15]")

  @property
  def niu(self):
    return NIU0 + self.noc * NIU_STRIDE

  @property
  def command(self):
    return self.niu + self.command_slot * COMMAND_BUFFER_STRIDE

  @property
  def control(self):
    # Do not clear RESPONSE_MARKED on Blackhole: truly posted atomics can hang.
    return (
      ATOMIC | RESPONSE_MARKED | VC_STATIC | self.static_vc << VC_SHIFT |
      self.priority << PRIORITY_SHIFT
    )


def _store_word(k: Asm, base: Reg, offset: int, value: int | Reg,
                scratch: Reg):
  if is_reg(value):
    k.sw(value, base, offset)
  elif value == 0:
    k.sw(R.ZERO, base, offset)
  else:
    k.li(scratch, value)
    k.sw(scratch, base, offset)


def _wait_command_ready(k: Asm, command: Reg):
  busy = k.reg()
  again = k._new_label("atomic_command_ready")
  k.label(again)
  k.lw(busy, command, COMMAND_SEND)
  k.bne(busy, R.ZERO, again)


def _wait_zero(k: Asm, base: Reg, offset: int):
  current = k.reg()
  again = k._new_label("atomic_response_wait")
  k.label(again)
  k.lw(current, base, offset)
  k.bne(current, R.ZERO, again)
  k.fence()


def _parameter(k: Asm, slot: int):
  if type(slot) is not int or not 0 <= slot < TensixL1.PARAM_SLOTS:
    raise ValueError("atomic parameter slot is outside the raw parameter table")
  address, value = k.reg(2)
  k.li(address, TensixL1.PARAM_BASE + slot * 4)
  k.lw(value, address)
  return value


def _check_word_alignment(k: Asm, address: Reg):
  low = k.reg()
  invalid = k._new_label("invalid_atomic_address")
  valid = k._new_label("valid_atomic_address")
  k.andi(low, address, 3)
  k.bne(low, R.ZERO, invalid)
  k.j(valid)
  k.label(invalid)
  k.j(invalid)
  k.label(valid)


def _local_coordinate(k: Asm, config: AtomicIncrementConfig):
  coordinate, address = k.reg(2)
  k.li(address, config.niu + NIU_CONFIG + LOGICAL_NODE_ID)
  k.lw(coordinate, address)
  k.slli(coordinate, coordinate, 20)
  k.srli(coordinate, coordinate, 20)
  return coordinate


def emit_atomic_increment(k: Asm, config: AtomicIncrementConfig,
                          target_coordinate_param=0,
                          target_address_param=1, increment_param=2,
                          count_param=3):
  """Emit ``count`` atomic increments against one remote L1 word.

  Runtime parameters are packed target coordinate, target L1 byte address,
  unsigned 32-bit increment, and request count.  In returning mode the final
  old value is left at ``config.return_address`` after every response for the
  TID has arrived.  A caller that consumes every ticket should issue one at a
  time and read that word between calls.

  In no-return mode this helper only waits until the final command has left the
  command buffer.  A receiver-side counter wait is the completion barrier.
  """
  if k.role not in ("brisc", "ncrisc"):
    raise ValueError("only BRISC and NCRISC can issue NoC atomics")

  target_coordinate = _parameter(k, target_coordinate_param)
  target_address = _parameter(k, target_address_param)
  increment = _parameter(k, increment_param)
  remaining = _parameter(k, count_param)
  _check_word_alignment(k, target_address)

  niu, command = k.reg(2)
  k.li(niu, config.niu)
  k.li(command, config.command)
  if config.return_value:
    _wait_zero(
      k, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4,
    )

  # INCR_GET addresses one of four words in a 16-byte region.  The target
  # address remains intact while bits [1:0] of AT_LEN_BE select its word.
  selector, instruction = k.reg(2)
  k.andi(selector, target_address, 12)
  k.srli(selector, selector, 2)
  k.li(instruction, INCR_GET | WRAP_32)
  k.or_(instruction, instruction, selector)
  return_coordinate = _local_coordinate(k, config) if config.return_value else R.ZERO

  scratch = k.reg()
  words = (
    target_address, 0, target_coordinate,
    config.return_address, 0, return_coordinate,
    config.tid << TID_SHIFT, config.control, instruction, 0, increment, 0,
  )
  for index, word in enumerate(words):
    _store_word(k, command, index * 4, word, scratch)

  send = k.reg()
  k.li(send, 1)
  loop = k._new_label("atomic_increment")
  done = k._new_label("atomic_increment_done")
  k.label(loop)
  k.beq(remaining, R.ZERO, done)
  _wait_command_ready(k, command)
  k.sw(send, command, COMMAND_SEND)
  k.addi(remaining, remaining, -1)
  k.j(loop)
  k.label(done)

  # Command-ready proves the last request was accepted, not remotely visible.
  _wait_command_ready(k, command)
  if config.return_value:
    _wait_zero(
      k, niu, STATUS + REQUESTS_OUTSTANDING + config.tid * 4,
    )
  return k


def emit_wait_for_counter(k: Asm, counter_address: int, expected_param=0):
  """Poll a local L1 counter until it equals the runtime expected value."""
  _word_aligned(counter_address, "atomic counter address")
  if counter_address + 4 > TensixL1.SIZE:
    raise ValueError("atomic counter address is outside L1")
  expected = _parameter(k, expected_param)
  address, observed = k.reg(2)
  k.li(address, counter_address)
  again = k._new_label("atomic_counter_wait")
  k.label(again)
  k.lw(observed, address)
  k.beq(observed, expected, again + "_done")
  k.fence()
  k.j(again)
  k.label(again + "_done")
  k.fence()
  return k
