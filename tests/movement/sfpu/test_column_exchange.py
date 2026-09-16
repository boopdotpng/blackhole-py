"""Check SFPU column overrides against independently unpacked/packed Dst data."""
from struct import pack, unpack

import pytest

from asm import Asm
from ttko.isa import Tensix as TT
from tests.movement.sfpu.test_load_lanes import INPUT, OUTPUT
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, Sem, SemWait, Stall, Wait, _set_thread_cfg, configure_fp32_dst,
  emit_unpack_to_dst, pc_sync, publish_dst, sem_get, sem_post, sem_wait, stall,
)


def set_column_exchange(math, mask, bit):
  # Clear both exchange bits, preserving unrelated LaneConfig settings.
  math.emit(TT.TTSFPCONFIG(0xFF3F, 15, 5))  # Immediate bitwise AND.
  if mask:
    math.emit(TT.TTSFPLOADI(0, 2, 1 << bit))  # Raw integer in L0.
    # SFPCONFIG's lane mask uses bits 0, 2, ..., 14 for the eight pairs.
    lane_mask = sum(1 << (2 * pair) for pair in range(8) if mask & (1 << pair))
    math.emit(TT.TTSFPCONFIG(lane_mask, 15, 10))  # Masked OR from L0.
  math.emit(TT.TTSFPNOP())


@pytest.mark.parametrize("operation", ("load", "store"))
@pytest.mark.parametrize("low_address", range(4))
@pytest.mark.parametrize("mask", (0, 0xFF, 0x55, 0xAA, *(1 << i for i in range(8))),
                         ids=lambda mask: f"mask-{mask:02x}")
def test_column_exchange(bh, operation, low_address, mask):
  loader, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  # Unique source values identify every row/column; sentinel guards surround
  # the output window at rows 32..35. The packer observes Dst independently.
  initial = list(range(1, 257)) + [-100] * 768
  size = loader.reg()
  loader.li(size, 1024 * 4)
  emit_unpack_to_dst(loader, INPUT, size, 0, 0)
  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(math, Stall.SYNC, Wait.MATH)
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  configure_fp32_dst(math, 0)
  for register in (12, 28, 47):
    _set_thread_cfg(math, register, 0)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  math.emit(TT.TTSFPENCC(0, 0, 0, 2))
  set_column_exchange(math, mask, 6 if operation == "load" else 7)
  # Only one direction has exchange enabled: a load/store round trip with
  # matching overrides could conceal an incorrect mapping. These also check
  # that the read bit cannot affect stores, and the write bit cannot affect loads.
  math.emit(TT.TTSFPLOAD(1, 3, 0, 4 + (low_address if operation == "load" else 0)))
  math.emit(TT.TTSFPSTORE(1, 3, 0, 32 + (low_address if operation == "store" else 0)))
  stall(math, Stall.SYNC, Wait.SFPU)
  set_column_exchange(math, 0, 6)
  pc_sync(math)
  publish_dst(math)

  count = packer.reg()
  packer.li(count, 1024)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=F32)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT: pack("<1024f", *initial), OUTPUT: b"\xA5" * 4160})
  result = unpack("<1024f", bh.read_l1(bh.core, OUTPUT, 4096))
  expected = initial.copy()
  for row in range(4):
    for pair in range(8):
      # The override forces odd, even when the address already selects odd.
      column = 2 * pair + int(bool(low_address & 2 or mask & (1 << pair)))
      source_column = column if operation == "load" else 2 * pair
      output_column = column if operation == "store" else 2 * pair
      expected[(32 + row) * 16 + output_column] = initial[(4 + row) * 16 + source_column]
  assert sum(a != b for a, b in zip(result, initial)) == 32
  for index, (actual, wanted) in enumerate(zip(result, expected)):
    assert actual == wanted, f"Dst row {index // 16}, column {index % 16}: {actual} != {wanted}"
  assert bh.read_l1(bh.core, OUTPUT + 4096, 64) == b"\xA5" * 64
