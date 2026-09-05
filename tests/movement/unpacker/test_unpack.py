from struct import pack

import pytest

from asm import Asm
from fw.consts import TensixL1
from isa import TensixWord
from tests.movement.unpacker.unpack import (
  BF16, BF16_TILE_BYTES, F32, F32_TILE_BYTES, TILE_ELEMENTS,
  UnpackTarget, clear_sources, emit_copy_src_to_dst,
  emit_direct_dst_math_handshake, emit_pack_dst, emit_unpack_pair,
  emit_unpack_to_dst, emit_unpack_to_src,
  finish_pack, publish_dst,
)
from tests.profiler import Profiler


INPUT_A = TensixL1.DATA_BUFFER_SPACE_BASE
INPUT_B = INPUT_A + F32_TILE_BYTES
OUTPUT_A = INPUT_B + F32_TILE_BYTES
OUTPUT_B = OUTPUT_A + F32_TILE_BYTES


def _bf16_tile(seed):
  # Finite normalized BF16 values with unique, exactly preserved bit patterns.
  return pack(
    f"<{TILE_ELEMENTS}H",
    *((0x3F00 + ((index * 37 + seed) % 0x70)) for index in range(TILE_ELEMENTS)),
  )


def _f32_tile(seed):
  return pack(
    f"<{TILE_ELEMENTS}I",
    *((0x3F000000 + ((index * 0x10101 + seed) & 0x007FFFFF))
      for index in range(TILE_ELEMENTS)),
  )


def _runtime_word(k, slot):
  address, value = k.reg(2)
  k.li(address, TensixL1.PARAM_BASE + slot * 4)
  k.lw(value, address)
  return value


def _direct_images(tile, offset, profile):
  trisc0 = profile.kernel
  byte_count = _runtime_word(trisc0, 0)
  profile.record("unpack to Dst")
  emit_unpack_to_dst(trisc0, INPUT_A, byte_count, tile, offset)
  profile.record("unpack to Dst")

  trisc1 = Asm("trisc1")
  emit_direct_dst_math_handshake(trisc1, tile)

  trisc2 = Asm("trisc2")
  emit_pack_dst(trisc2, tile, OUTPUT_A, F32)
  finish_pack(trisc2)
  return {
    "trisc0": trisc0.lower(),
    "trisc1": trisc1.lower(),
    "trisc2": trisc2.lower(),
  }


@pytest.mark.parametrize("tile", range(8))
def test_unpack_f32_row_major_to_each_dst_tile(bh, tile):
  source = _f32_tile(tile * 97)
  profile = Profiler(Asm("trisc0"))
  images = _direct_images(tile, 0, profile)
  bh.launch(
    images, params=(F32_TILE_BYTES,),
    l1={INPUT_A: source, OUTPUT_A: bytes(F32_TILE_BYTES)},
    profiler=profile,
  )
  assert bh.read_l1(bh.core, OUTPUT_A, F32_TILE_BYTES) == source
  assert profile.last["unpack to Dst"] > 0


@pytest.mark.parametrize(("element_count", "offset"), [
  (16, 0),
  (128, 16),
  (256, 256),
  (512, 128),
  (768, 32),
])
def test_partial_unpack_to_dst_uses_a_runtime_bounded_mop(
  bh, element_count, offset,
):
  if offset + element_count > TILE_ELEMENTS:
    pytest.skip("case does not fit in one Dst tile")
  source = _f32_tile(0x1234)
  profile = Profiler(Asm("trisc0"))
  images = _direct_images(3, offset, profile)
  bh.launch(
    images, params=(element_count * 4,),
    l1={INPUT_A: source, OUTPUT_A: b"\xA5" * F32_TILE_BYTES},
    profiler=profile,
  )
  actual = bh.read_l1(bh.core, OUTPUT_A, F32_TILE_BYTES)
  start, end = offset * 4, (offset + element_count) * 4
  assert actual[:start] == bytes(start)
  assert actual[start:end] == source[:element_count * 4]
  assert actual[end:] == bytes(F32_TILE_BYTES - end)
  assert profile.last["unpack to Dst"] > 0


@pytest.mark.parametrize("bank", [UnpackTarget.SRCA, UnpackTarget.SRCB])
def test_unpack_bf16_row_major_tile_to_source_bank(bh, bank):
  source = _bf16_tile(11 + int(bank))
  trisc0 = Asm("trisc0")
  profile = Profiler(trisc0)
  clear_sources(trisc0)
  profile.record(f"unpack {bank.name}")
  emit_unpack_to_src(trisc0, INPUT_A, bank)
  profile.record(f"unpack {bank.name}")

  trisc1 = Asm("trisc1")
  emit_copy_src_to_dst(trisc1, bank, 0)
  publish_dst(trisc1)

  trisc2 = Asm("trisc2")
  emit_pack_dst(trisc2, 0, OUTPUT_A, BF16)
  finish_pack(trisc2)
  bh.launch(
    {
      "trisc0": trisc0.lower(),
      "trisc1": trisc1.lower(),
      "trisc2": trisc2.lower(),
    },
    l1={INPUT_A: source, OUTPUT_A: bytes(BF16_TILE_BYTES)},
    profiler=profile,
  )
  assert bh.read_l1(bh.core, OUTPUT_A, BF16_TILE_BYTES) == source
  assert profile.last[f"unpack {bank.name}"] > 0


def test_parallel_unpack_places_two_row_major_tiles_in_srca_and_srcb(bh):
  source_a, source_b = _bf16_tile(3), _bf16_tile(91)
  trisc0 = Asm("trisc0")
  profile = Profiler(trisc0)
  clear_sources(trisc0)
  profile.record("parallel SrcA/SrcB")
  emit_unpack_pair(trisc0, INPUT_A, INPUT_B)
  profile.record("parallel SrcA/SrcB")

  trisc1 = Asm("trisc1")
  emit_copy_src_to_dst(trisc1, UnpackTarget.SRCA, 0, release=1)
  emit_copy_src_to_dst(
    trisc1, UnpackTarget.SRCB, 1, release=2, wait_for_dst=False,
  )
  publish_dst(trisc1)

  trisc2 = Asm("trisc2")
  emit_pack_dst(trisc2, 0, OUTPUT_A, BF16)
  emit_pack_dst(
    trisc2, 1, OUTPUT_B, BF16, configure=False, wait_for_dst=False,
  )
  finish_pack(trisc2)
  bh.launch(
    {
      "trisc0": trisc0.lower(),
      "trisc1": trisc1.lower(),
      "trisc2": trisc2.lower(),
    },
    l1={
      INPUT_A: source_a,
      INPUT_B: source_b,
      OUTPUT_A: bytes(BF16_TILE_BYTES),
      OUTPUT_B: bytes(BF16_TILE_BYTES),
    },
    profiler=profile,
  )
  assert bh.read_l1(bh.core, OUTPUT_A, BF16_TILE_BYTES) == source_a
  assert bh.read_l1(bh.core, OUTPUT_B, BF16_TILE_BYTES) == source_b
  assert profile.last["parallel SrcA/SrcB"] > 0


def _single_source_images(bank, address, label):
  trisc0 = Asm("trisc0")
  profile = Profiler(trisc0)
  clear_sources(trisc0)
  profile.record(label)
  emit_unpack_to_src(trisc0, address, bank)
  profile.record(label)

  trisc1 = Asm("trisc1")
  # SrcA-only unpack also raises SrcB dvalid as required by the hardware, so
  # each independent run releases both source-valid flags before returning.
  emit_copy_src_to_dst(trisc1, bank, 0, release=3)
  publish_dst(trisc1)

  trisc2 = Asm("trisc2")
  emit_pack_dst(trisc2, 0, OUTPUT_A, BF16)
  finish_pack(trisc2)
  return {
    "trisc0": trisc0.lower(),
    "trisc1": trisc1.lower(),
    "trisc2": trisc2.lower(),
  }, profile


def test_benchmark_parallel_unpack_against_two_individual_unpacks(bh, capsys):
  source_a, source_b = _bf16_tile(7), _bf16_tile(73)
  individual = []
  for bank, address, source in (
    (UnpackTarget.SRCA, INPUT_A, source_a),
    (UnpackTarget.SRCB, INPUT_B, source_b),
  ):
    label = f"individual {bank.name}"
    images, profile = _single_source_images(bank, address, label)
    bh.launch(
      images,
      l1={address: source, OUTPUT_A: bytes(BF16_TILE_BYTES)},
      profiler=profile,
    )
    assert bh.read_l1(bh.core, OUTPUT_A, BF16_TILE_BYTES) == source
    individual.append(profile.last[label])

  # Use the same complete producer/consumer pipeline as the correctness test;
  # the profile markers enclose only the dual-unpacker portion on trisc0.
  trisc0 = Asm("trisc0")
  profile = Profiler(trisc0)
  clear_sources(trisc0)
  profile.record("parallel")
  emit_unpack_pair(trisc0, INPUT_A, INPUT_B)
  profile.record("parallel")
  trisc1 = Asm("trisc1")
  emit_copy_src_to_dst(trisc1, UnpackTarget.SRCA, 0, release=1)
  emit_copy_src_to_dst(
    trisc1, UnpackTarget.SRCB, 1, release=2, wait_for_dst=False,
  )
  publish_dst(trisc1)
  trisc2 = Asm("trisc2")
  emit_pack_dst(trisc2, 0, OUTPUT_A, BF16)
  emit_pack_dst(
    trisc2, 1, OUTPUT_B, BF16, configure=False, wait_for_dst=False,
  )
  finish_pack(trisc2)
  bh.launch(
    {
      "trisc0": trisc0.lower(),
      "trisc1": trisc1.lower(),
      "trisc2": trisc2.lower(),
    },
    l1={
      INPUT_A: source_a,
      INPUT_B: source_b,
      OUTPUT_A: bytes(BF16_TILE_BYTES),
      OUTPUT_B: bytes(BF16_TILE_BYTES),
    },
    profiler=profile,
  )
  assert bh.read_l1(bh.core, OUTPUT_A, BF16_TILE_BYTES) == source_a
  assert bh.read_l1(bh.core, OUTPUT_B, BF16_TILE_BYTES) == source_b

  sequential = sum(individual)
  parallel = profile.last["parallel"]
  relation = "faster" if parallel < sequential else "slower"
  print(
    f"parallel unpack is {relation}: {parallel} cycles vs "
    f"{sequential} cycles for two individual unpacks ({individual[0]} + "
    f"{individual[1]})"
  )
  assert parallel > 0
  assert all(cycles > 0 for cycles in individual)


def test_runtime_partial_dst_codegen_has_constant_unpack_instruction_count():
  trisc0 = Asm("trisc0")
  byte_count = _runtime_word(trisc0, 0)
  emit_unpack_to_dst(trisc0, INPUT_A, byte_count, 7, 32)
  unpack_opcodes = [
    int(word) >> 24 for word in trisc0.items if isinstance(word, TensixWord)
  ]
  # One UNPACR lives in Replay. Runtime sizes select MOP loop counts and a tail,
  # never one literal UNPACR per copied value.
  assert unpack_opcodes.count(0x42) == 1
  assert unpack_opcodes.count(0x01) == 2
  assert any(
    unpack_opcodes[index:index + 3] == [0x04, 0x42, 0xA2]
    for index in range(len(unpack_opcodes) - 2)
  ), "direct-Dst Replay must contain UNPACR followed by STALLWAIT"
  assert trisc0.lower()
