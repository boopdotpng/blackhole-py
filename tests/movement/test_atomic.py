from dataclasses import dataclass
from struct import Struct

import pytest

from asm import Asm
from fw.consts import TensixL1, TensixMMIO
from tests.movement.atomic import (
  AtomicIncrementConfig, emit_atomic_increment, emit_wait_for_counter,
)


COUNTER_ADDRESS = TensixL1.DATA_BUFFER_SPACE_BASE
RETURN_ADDRESS = COUNTER_ADDRESS + 16
TIMING_ADDRESS = TensixL1.DATA_BUFFER_SPACE_END - 16
TIMING_RECORD = Struct("<4I")
CLOCK_GHZ = 1.35
ITERATIONS = 64
SENDER_COUNTS = (1, 8)


def _record_clock(kernel, address):
  low, high, high_again, clock, output = kernel.reg(5)
  retry = kernel._new_label("atomic_clock_retry")
  kernel.li(clock, TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H)
  kernel.label(retry)
  kernel.lw(high, clock)
  kernel.lw(low, clock, (
    TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_L -
    TensixMMIO.RISCV_DEBUG_REG_WALL_CLOCK_H
  ))
  kernel.lw(high_again, clock)
  kernel.bne(high, high_again, retry)
  kernel.li(output, address)
  kernel.sw(low, output)
  kernel.sw(high, output, 4)
  kernel.fence()


@dataclass(frozen=True)
class _Timing:
  start: int
  end: int

  @classmethod
  def read(cls, bh, core):
    lo0, hi0, lo1, hi1 = TIMING_RECORD.unpack(
      bh.read_l1(core, TIMING_ADDRESS, TIMING_RECORD.size),
    )
    return cls(lo0 | hi0 << 32, lo1 | hi1 << 32)

  @property
  def cycles(self):
    return (self.end - self.start) & ((1 << 64) - 1)


def _coordinate(core):
  x, y = core
  return x | y << 6


def _sender_image(config):
  kernel = Asm("brisc")
  _record_clock(kernel, TIMING_ADDRESS)
  emit_atomic_increment(kernel, config)
  _record_clock(kernel, TIMING_ADDRESS + 8)
  return {"brisc": kernel.lower()}


def _receiver_image():
  kernel = Asm("brisc")
  _record_clock(kernel, TIMING_ADDRESS)
  emit_wait_for_counter(kernel, COUNTER_ADDRESS)
  _record_clock(kernel, TIMING_ADDRESS + 8)
  return {"brisc": kernel.lower()}


def _read_word(bh, core, address):
  return int.from_bytes(bh.read_l1(core, address, 4), "little")


def test_atomic_increment_configuration_and_lowering():
  with pytest.raises(ValueError, match="NoC index"):
    AtomicIncrementConfig(noc=2)
  with pytest.raises(ValueError, match="4-byte-aligned"):
    AtomicIncrementConfig(return_address=RETURN_ADDRESS + 1)
  with pytest.raises(ValueError, match="static VC"):
    AtomicIncrementConfig(static_vc=4)

  for role in ("brisc", "ncrisc"):
    for return_value in (False, True):
      kernel = Asm(role)
      emit_atomic_increment(
        kernel,
        AtomicIncrementConfig(noc=0, return_value=return_value,
                              return_address=RETURN_ADDRESS),
      )
      assert len(kernel.lower()) > 0

  with pytest.raises(ValueError, match="only BRISC and NCRISC"):
    emit_atomic_increment(Asm("trisc0"), AtomicIncrementConfig())


@pytest.mark.parametrize("noc", (0, 1))
def test_two_core_atomic_fetch_add_returns_old_value(bh, noc):
  receiver, sender = bh.device.cores[:2]
  initial, increment = 7, 5
  config = AtomicIncrementConfig(
    noc=noc, tid=1, return_value=True, return_address=RETURN_ADDRESS,
  )
  images = {
    receiver: _receiver_image(),
    sender: _sender_image(config),
  }
  params = {
    receiver: (initial + increment,),
    sender: (_coordinate(receiver), COUNTER_ADDRESS, increment, 1),
  }
  bh.launch_many_mapped(
    images, params=params,
    l1={COUNTER_ADDRESS: initial.to_bytes(4, "little"),
        RETURN_ADDRESS: (0xDEADBEEF).to_bytes(4, "little"),
        TIMING_ADDRESS: bytes(TIMING_RECORD.size)},
  )

  assert _read_word(bh, receiver, COUNTER_ADDRESS) == initial + increment
  assert _read_word(bh, sender, RETURN_ADDRESS) == initial


def test_atomic_return_and_no_return_timing(bh):
  """Compare source completion and receiver-visible completion on both NoCs."""
  receiver = bh.device.cores[0]
  rows = []
  for noc in (0, 1):
    for sender_count in SENDER_COUNTS:
      for return_value in (True, False):
        senders = tuple(bh.device.cores[1:1 + sender_count])
        expected = len(senders) * ITERATIONS
        # The fire-and-forget form deliberately leaves no locally drainable
        # response. Give every launch its own TID so benchmark state cannot
        # leak between the one-sender and fan-in cases.
        tid = 2 + 2 * (sender_count == SENDER_COUNTS[-1]) + (not return_value)
        config = AtomicIncrementConfig(
          noc=noc, tid=tid, return_value=return_value,
          return_address=RETURN_ADDRESS,
        )
        sender_image = _sender_image(config)
        images = {receiver: _receiver_image()}
        images.update((core, sender_image) for core in senders)
        params = {receiver: (expected,)}
        params.update(
          (core, (_coordinate(receiver), COUNTER_ADDRESS, 1, ITERATIONS))
          for core in senders
        )
        bh.launch_many_mapped(
          images, params=params,
          l1={COUNTER_ADDRESS: bytes(4), RETURN_ADDRESS: bytes(4),
              TIMING_ADDRESS: bytes(TIMING_RECORD.size)},
        )

        assert _read_word(bh, receiver, COUNTER_ADDRESS) == expected
        sender_cycles = max(_Timing.read(bh, core).cycles for core in senders)
        visible_cycles = _Timing.read(bh, receiver).cycles
        rows.append((
          noc, sender_count, return_value, sender_cycles, visible_cycles,
          expected,
        ))

  print(
    "\nNoC atomic increment -> one remote L1 counter\n"
    "noc | senders | form      | sender cycles/op | visible cycles/op | "
    "visible Mops/s"
  )
  for (noc, sender_count, return_value, sender_cycles, visible_cycles,
       operations) in rows:
    form = "return" if return_value else "no-return"
    print(
      f" {noc}  | {sender_count:7d} | {form:9s} | "
      f"{sender_cycles / ITERATIONS:16.2f} | "
      f"{visible_cycles / operations:17.2f} | "
      f"{operations * CLOCK_GHZ * 1000 / visible_cycles:14.2f}"
    )
