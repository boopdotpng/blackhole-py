from struct import Struct

import pytest

from asm import Asm
from fw.consts import TensixL1, TensixMMIO
from isa import R
from tests.harness import _rectangles
from tests.movement.remote_cb import (
  RemoteCBConfig, emit_send_pages, emit_wait_and_pop_pages,
)


CB_ADDRESS = TensixL1.DATA_BUFFER_SPACE_BASE
TILE_BYTES = 2048
DEPTH = 8
TAIL_BYTES = 4
TIMING_ADDRESS = TensixL1.DATA_BUFFER_SPACE_END - 16
VALIDATION_ADDRESS = TIMING_ADDRESS - 4
TIMING_RECORD = Struct("<4I")
CLOCK_GHZ = 1.35
FIRST_WORD = 0x51CB0001
LAST_WORD = 0x51CBFFFF
GUARD_WORD = 0xC0FFEE55


def _record_clock(kernel, address):
  low, high, high_again, clock, output = kernel.reg(5)
  retry = kernel._new_label("remote_cb_clock_retry")
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


def _seed_source(kernel, config):
  address, last_address, first, last, remaining, stride = kernel.reg(6)
  kernel.li(address, config.l1_address)
  kernel.li(first, FIRST_WORD)
  kernel.li(last, LAST_WORD)
  kernel.li(remaining, config.depth)
  kernel.li(stride, config.page_bytes)
  loop = kernel._new_label("seed_remote_cb")
  done = kernel._new_label("seed_remote_cb_done")
  kernel.label(loop)
  kernel.beq(remaining, R.ZERO, done)
  kernel.sw(first, address)
  kernel.add(last_address, address, stride)
  kernel.addi(last_address, last_address, -4)
  kernel.sw(last, last_address)
  kernel.add(address, address, stride)
  kernel.addi(remaining, remaining, -1)
  kernel.j(loop)
  kernel.label(done)
  kernel.fence()


def _timing(bh, core):
  lo0, hi0, lo1, hi1 = TIMING_RECORD.unpack(
    bh.read_l1(core, TIMING_ADDRESS, TIMING_RECORD.size),
  )
  return lo0 | hi0 << 32, lo1 | hi1 << 32


def _images(config, *, guard_offset=None, check_offset=None,
            consumer_delay=0):
  sender = Asm("brisc")
  _seed_source(sender, config)
  _record_clock(sender, TIMING_ADDRESS)
  emit_send_pages(sender, config)
  _record_clock(sender, TIMING_ADDRESS + 8)

  receiver = Asm("ncrisc")
  if guard_offset is not None:
    receiver.write(config.l1_address + guard_offset, GUARD_WORD)
    receiver.fence()
  _record_clock(receiver, TIMING_ADDRESS)
  emit_wait_and_pop_pages(receiver, config, delay_cycles=consumer_delay)
  if check_offset is not None:
    observed, address = receiver.reg(2)
    receiver.li(address, config.l1_address + check_offset)
    receiver.lw(observed, address)
    receiver.li(address, VALIDATION_ADDRESS)
    receiver.sw(observed, address)
    receiver.fence()
  _record_clock(receiver, TIMING_ADDRESS + 8)
  return {"brisc": sender.lower()}, {"ncrisc": receiver.lower()}


def test_remote_cb_configuration_and_lowering():
  config = RemoteCBConfig(((1, 2), (2, 2)), CB_ADDRESS, 2)
  assert config.page_bytes == TILE_BYTES
  assert config.rectangles == (((1, 2), (2, 2)),)
  sender, receiver = _images(config)
  assert sender["brisc"] and receiver["ncrisc"]
  with pytest.raises(ValueError, match="at least one destination"):
    RemoteCBConfig((), CB_ADDRESS, 2)
  with pytest.raises(ValueError, match="16-byte-aligned"):
    RemoteCBConfig(((1, 2),), CB_ADDRESS + 1, 2)


@pytest.mark.parametrize("noc", (0, 1))
def test_send_pages_remote_cb_unicast_and_multicast(bh, noc):
  producer = bh.device.cores[0]
  tail_receiver = bh.device.cores[1]
  tail_config = RemoteCBConfig(
    (tail_receiver,), CB_ADDRESS, 1, TILE_BYTES, noc,
    sync_slot=noc * 8,
  )
  guard_offset = (TAIL_BYTES + 3) & -4
  sender_image, receiver_image = _images(
    tail_config, guard_offset=guard_offset, check_offset=0,
  )
  bh.launch_many_mapped(
    {producer: sender_image, tail_receiver: receiver_image},
    params={producer: (1, TAIL_BYTES), tail_receiver: (1,)},
    l1={CB_ADDRESS: bytes(TILE_BYTES),
        TIMING_ADDRESS: bytes(TIMING_RECORD.size)},
  )
  assert int.from_bytes(
    bh.read_l1(tail_receiver, CB_ADDRESS, 4), "little",
  ) == FIRST_WORD
  assert int.from_bytes(
    bh.read_l1(tail_receiver, CB_ADDRESS + guard_offset, 4), "little",
  ) == GUARD_WORD
  assert int.from_bytes(
    bh.read_l1(tail_receiver, VALIDATION_ADDRESS, 4), "little",
  ) == FIRST_WORD

  destination_cases = (
    ("unicast", tuple(bh.device.cores[1:2])),
    ("multicast", tuple(bh.device.cores[1:9])),
  )
  rows = []
  cases = tuple(
    (name, receivers, pages)
    for name, receivers in destination_cases
    for pages in (1, DEPTH)
  )
  for case_index, (name, receivers, pages) in enumerate(cases, start=1):
    config = RemoteCBConfig(
      receivers, CB_ADDRESS, DEPTH, TILE_BYTES, noc,
      sync_slot=noc * 8 + case_index,
    )
    sender_image, receiver_image = _images(
      config, check_offset=pages * TILE_BYTES - 4,
    )
    images = {producer: sender_image}
    images.update((core, receiver_image) for core in receivers)
    params = {producer: (pages, TILE_BYTES)}
    params.update((core, (pages,)) for core in receivers)
    bh.launch_many_mapped(
      images, params=params,
      l1={CB_ADDRESS: bytes(DEPTH * TILE_BYTES),
          TIMING_ADDRESS: bytes(TIMING_RECORD.size)},
    )

    for core in receivers:
      assert int.from_bytes(
        bh.read_l1(core, VALIDATION_ADDRESS, 4), "little",
      ) == LAST_WORD
      for offset, expected in (
        (0, FIRST_WORD), (TILE_BYTES - 4, LAST_WORD),
        ((pages - 1) * TILE_BYTES, FIRST_WORD),
        (pages * TILE_BYTES - 4, LAST_WORD),
      ):
        assert int.from_bytes(
          bh.read_l1(core, CB_ADDRESS + offset, 4), "little",
        ) == expected

    producer_start, _ = _timing(bh, producer)
    receiver_end = max(_timing(bh, core)[1] for core in receivers)
    cycles = receiver_end - producer_start
    source_bytes = pages * TILE_BYTES
    rectangles = _rectangles(receivers)
    rows.append((
      name, pages, len(receivers), len(rectangles), cycles,
      source_bytes * CLOCK_GHZ / cycles,
      source_bytes * len(receivers) * CLOCK_GHZ / cycles,
    ))

  print(
    f"\nremote CB send_pages on NoC{noc}\n"
    "mode      | tiles | cores | rects | cycles | source GB/s | delivered GB/s"
  )
  for (name, pages, count, rectangles, cycles, source_gbps,
       delivered_gbps) in rows:
    print(
      f"{name:9s} | {pages:5d} | {count:5d} | {rectangles:5d} | "
      f"{cycles:6d} | "
      f"{source_gbps:11.2f} | {delivered_gbps:14.2f}"
    )
