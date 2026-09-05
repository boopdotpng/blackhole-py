"""HiFi2 ELWMUL source placement: contiguous, separated, and mismatched slots."""

from statistics import median
from struct import pack, unpack

import pytest

from asm import Asm
from fw.consts import TensixL1
from isa import Tensix as TT
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, F32_TILE_BYTES, Sem, SemWait, Stall, Wait, UNPACKER0, UNPACKER1,
  _mop_loop_words, _set_thread_cfg, _unpacr, configure_fp32_dst,
  configure_mop, configure_unpack_pair,
  emit_unpack_to_dst, load_replay, pc_sync, publish_dst, run_mop, sem_get, sem_post, sem_wait, stall,
)
from tests.profiler import Profiler


INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
INPUT_A = INPUT + F32_TILE_BYTES
INPUT_B = INPUT_A + 2048
OUTPUT = INPUT_B + 2048
REPEATS = 64
SAMPLES = 7
CASES = (
  ("contiguous", (0, 1), (0, 1)),
  ("opposite ends", (0, 7), (0, 7)),
  ("opposite mismatched", (0, 7), (7, 0)),
  ("contiguous mismatched", (0, 1), (6, 7)),
)


def _inputs(a_slots, b_slots):
  a = tuple(1 + (i % 128) / 128 for i in range(256))
  # HiFi2 covers both A phases but only the high B phase. Keep B's
  # significand within that phase; A still needs phase 1 for exact products.
  b = tuple(0.5 + ((i * 37 + 11) % 64) / 128 for i in range(256))
  initial = tuple(1 + i / 512 for i in range(256))
  data = {INPUT: pack("<1024f", *initial, *([0.0] * 768))}
  for address, values, slots in ((INPUT_A, a, a_slots), (INPUT_B, b, b_slots)):
    # Nonzero distractors ensure a wrong source row cannot accidentally pass.
    physical = [0x4100 + i % 128 for i in range(1024)]
    for block, slot in enumerate(slots):
      physical[slot * 128:(slot + 1) * 128] = [
        unpack("<I", pack("<f", x))[0] >> 16
        for x in values[block * 128:(block + 1) * 128]
      ]
    data[address] = pack("<1024H", *physical)
  # All values and all intermediate sums are exactly representable in FP32.
  expected = pack("<256f", *(c + REPEATS * x * y for c, x, y in zip(initial, a, b)))
  data[OUTPUT] = b"\xA5" * 1088
  return data, expected


def _images(a_slots, b_slots, operation="ELWMUL"):
  loader, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  size = loader.reg()
  loader.li(size, F32_TILE_BYTES)
  emit_unpack_to_dst(loader, INPUT, size, 0, 0)
  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(math, Stall.SYNC, Wait.MATH)
  sem_wait(math, Sem.MATH_DONE, SemWait.ON_MAX, Stall.SYNC)
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)

  # Load a complete bank in one UNPACR per source, with one bank handoff.
  # Unused slots hold distractors; input placement is outside the timer.
  configure_unpack_pair(loader, INPUT_A, INPUT_B)
  loader.emit(TT.TTSETADCXX(3, 1023, 0))
  stall(loader, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
  configure_mop(loader, _mop_loop_words(
    1, 1, start=_unpacr(UNPACKER0), loop=_unpacr(UNPACKER1),
    last=_unpacr(UNPACKER1), outer_last=_unpacr(UNPACKER1),
  ))
  run_mop(loader)
  stall(loader, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
  sem_get(loader, Sem.UNPACK_SYNC)
  pc_sync(loader)

  configure_fp32_dst(math, 0)
  _set_thread_cfg(math, 11, 0)  # FIDELITY_BASE: phases 0 and 1 are HiFi2
  da, db = ((slots[1] - slots[0]) * 8 for slots in (a_slots, b_slots))
  for index, a_step, b_step, fidelity in (
    (0, da, db, 0),
    (1, -da, -db, 1 << 13),  # phase 0 -> 1
    (2, -da, -db, 1 << 15),  # phase 1 -> 0
  ):
    _set_thread_cfg(math, 12 + index, (a_step & 63) | (b_step & 63) << 8)
    _set_thread_cfg(math, 28 + index, fidelity)
    _set_thread_cfg(math, 47 + index, 0)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  for _ in range(a_slots[0]):
    math.emit(TT.TTINCRWC(0, 0, 0, 8))
  for _ in range(b_slots[0]):
    math.emit(TT.TTINCRWC(0, 0, 8, 0))
  def instruction(modifier, dst):
    if operation == "ELWMUL": return TT.TTELWMUL(0, 0, 0, modifier, dst)
    if operation == "ELWADD": return TT.TTELWADD(0, 1, 0, modifier, dst)
    if operation == "MVMUL": return TT.TTMVMUL(0, 0, modifier, dst)
    if operation == "GAPOOL": return TT.TTGAPOOL(0, 0, modifier, 0, dst)
    if operation == "GMPOOL": return TT.TTGMPOOL(0, 1, modifier, 0, dst)
    raise ValueError(operation)

  words = ((instruction(0, 0), instruction(1, 8), instruction(0, 0), instruction(2, 8))
           if operation in ("ELWMUL", "MVMUL", "GAPOOL")
           else (instruction(0, 0), instruction(2, 8)))
  load_replay(math, 0, words)
  replay = TT.TTREPLAY(0, len(words), 0, 0)
  configure_mop(math, _mop_loop_words(1, REPEATS, loop=replay, last=replay))
  stall(math, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
  pc_sync(math)
  profile = Profiler(math)
  profile.record("HiFi2 accumulate")
  run_mop(math)
  stall(math, Stall.SYNC, Wait.MATH)
  pc_sync(math)
  profile.record("HiFi2 accumulate")
  math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  publish_dst(math)

  count = packer.reg()
  packer.li(count, 256)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=F32)
  return {k.role: k.lower() for k in (loader, math, packer)}, profile


@pytest.mark.parametrize("name,a_slots,b_slots", CASES, ids=[case[0] for case in CASES])
def test_hifi2_elwmul_source_slot_placement(bh, name, a_slots, b_slots):
  images, profile = _images(a_slots, b_slots)
  data, expected = _inputs(a_slots, b_slots)
  samples = []
  for _ in range(SAMPLES):
    bh.launch(images, l1=data, profiler=profile)
    assert bh.read_l1(bh.core, OUTPUT, 1024) == expected
    assert bh.read_l1(bh.core, OUTPUT + 1024, 64) == b"\xA5" * 64
    samples.append(profile.last["HiFi2 accumulate"] / REPEATS)
  print(f"{name}: A={a_slots}, B={b_slots}; cycles per 256-element HiFi2 accumulation "
        f"median={median(samples):.3f}, min={min(samples):.3f}, max={max(samples):.3f}")
