"""Separate hardware checks of masked arithmetic, loads, and stores."""
from struct import pack, unpack

import pytest

from asm import Asm
from isa import Tensix as TT
from tests.movement.sfpu.test_load_lanes import INPUT, OUTPUT
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, Sem, SemWait, Stall, Wait, _set_thread_cfg, configure_fp32_dst,
  emit_unpack_to_dst, pc_sync, publish_dst, sem_get, sem_post, sem_wait, stall,
)


@pytest.mark.parametrize("start", (64, 73))
@pytest.mark.parametrize("masked", ("add", "store", "load"))
def test_sfpu_predication(bh, start, masked):
  loader, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  size = loader.reg()
  loader.li(size, 128 * 4)
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

  for position in range(4):
    address = position * 2
    math.emit(TT.TTSFPENCC(0, 0, 0, 2))  # All lanes active.
    if masked == "load":
      math.emit(TT.TTSFPLOADI(0, 0, 0xC2C8))  # -100 sentinel in every lane.
    else:
      math.emit(TT.TTSFPLOAD(0, 3, 0, address))
    if masked == "store":
      math.emit(TT.TTSFPADDI(0x40A0, 0, 0))  # Compute x+5 in every lane.

    math.emit(TT.TTSFPENCC(3, 0, 0, 10))  # Enable predicates, initially all true.
    # L15=2*lane. Add the vector's logical offset, then compare index-start >= 0.
    offset = (position // 2) * 64 + position % 2 - start
    math.emit(TT.TTSFPIADD(offset & 0xFFF, 15, 1, 9))
    if masked == "load":
      math.emit(TT.TTSFPLOAD(0, 3, 0, address))
    elif masked == "add":
      math.emit(TT.TTSFPADDI(0x40A0, 0, 0))
    else:
      math.emit(TT.TTSFPSTORE(0, 3, 0, address))
    math.emit(TT.TTSFPENCC(0, 0, 0, 2))
    if masked != "store":
      # Unmasked store exposes whether inactive arithmetic/load lanes stayed intact.
      math.emit(TT.TTSFPSTORE(0, 3, 0, address))

  stall(math, Stall.SYNC, Wait.SFPU)
  pc_sync(math)
  publish_dst(math)
  count = packer.reg()
  packer.li(count, 256)  # Also verify the untouched next 128-element slot.
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=F32)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT: pack("<128f", *range(128)), OUTPUT: b"\xA5" * 1088})
  expected = ([i if i >= start else -100 for i in range(128)] if masked == "load"
              else [i + (5 if i >= start else 0) for i in range(128)])
  result = unpack("<256f", bh.read_l1(bh.core, OUTPUT, 1024))
  assert result == tuple(expected + [0] * 128)
  assert bh.read_l1(bh.core, OUTPUT+1024, 64) == b"\xA5" * 64
  print(f"masked {masked}, index >= {start}: exact result; inactive lanes and adjacent slot preserved")
