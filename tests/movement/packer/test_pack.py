from struct import pack, unpack

import pytest

from asm import Asm
from fw.consts import TensixL1, TensixMMIO
from isa import Tensix as TT, TensixWord
from tests.movement.packer.pack import emit_pack_dst_to_cb, initialize_prng
from tests.movement.unpacker.unpack import (
  BF16, BF16_TILE_BYTES, F32, F32_TILE_BYTES, TILE_ELEMENTS,
  emit_direct_dst_math_handshake, emit_unpack_to_dst,
)
from tests.profiler import Profiler


INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
OUTPUT = INPUT + F32_TILE_BYTES
CB_PAGES = (OUTPUT, OUTPUT + 0x1000, OUTPUT + 0x2000)
ROUNDING_DEBUG = OUTPUT + 0x3000


def _f32_bf16_exact_tile():
  return pack(
    f"<{TILE_ELEMENTS}I",
    *((0x3F000000 + (index % 0x80) * 0x10000) for index in range(TILE_ELEMENTS)),
  )


def _runtime_word(k, slot):
  address, value = k.reg(2)
  k.li(address, TensixL1.PARAM_BASE + slot * 4)
  k.lw(value, address)
  return value


def _images(
  tile, count, offset=0, output=OUTPUT, *, label="Dst to CB", relu_mode=0,
  relu_threshold=0, stochastic=False, seed=0x12345678,
  output_format=BF16, debug_rounding=False,
):
  trisc0 = Asm("trisc0")
  load_bytes = _runtime_word(trisc0, 0)
  emit_unpack_to_dst(
    trisc0, INPUT, load_bytes, tile, 0,
    pack_stochastic=stochastic,
  )

  trisc1 = Asm("trisc1")
  if stochastic:
    initialize_prng(trisc1, seed)
  emit_direct_dst_math_handshake(trisc1, tile)

  trisc2 = Asm("trisc2")
  runtime_count = _runtime_word(trisc2, 1)
  profile = Profiler(trisc2)
  profile.record(label)
  emit_pack_dst_to_cb(
    trisc2, tile, output, runtime_count, dst_element_offset=offset,
    relu_mode=relu_mode, relu_threshold=relu_threshold,
    stochastic=stochastic, output_format=output_format,
  )
  profile.record(label)
  if debug_rounding:
    config = trisc2.reg()
    trisc2.read(config, TensixMMIO.CFG_BASE + 4)
    trisc2.write(ROUNDING_DEBUG, config)
  return {
    "trisc0": trisc0.lower(),
    "trisc1": trisc1.lower(),
    "trisc2": trisc2.lower(),
  }, profile


@pytest.mark.parametrize(("tile", "output_format", "count", "offset", "output"), [
  (0, BF16, 1, 0, CB_PAGES[0]),
  (1, BF16, 7, 16, CB_PAGES[1]),
  (2, BF16, 16, 0, CB_PAGES[2]),
  (3, BF16, 17, 32, CB_PAGES[0]),
  (4, BF16, 128, 16, CB_PAGES[1]),
  (5, BF16, 137, 144, CB_PAGES[2]),
  (6, BF16, 512, 128, CB_PAGES[0]),
  (7, BF16, TILE_ELEMENTS, 0, CB_PAGES[1]),
  (0, F32, 1, 0, CB_PAGES[2]),
  (3, F32, 17, 16, CB_PAGES[0]),
  (5, F32, 137, 144, CB_PAGES[1]),
  (7, F32, TILE_ELEMENTS, 0, CB_PAGES[2]),
])
def test_pack_runtime_rows_from_dst_to_row_major_cb(
  bh, tile, output_format, count, offset, output,
):
  source = _f32_bf16_exact_tile()
  words = unpack(f"<{TILE_ELEMENTS}I", source)
  if output_format == BF16:
    expected = pack(
      f"<{count}H", *(word >> 16 for word in words[offset:offset + count]),
    )
  else:
    expected = source[offset * 4:(offset + count) * 4]
  label = f'Dst to CB {"BF16" if output_format == BF16 else "F32"}'
  images, profile = _images(
    tile, count, offset, output, label=label, output_format=output_format,
  )
  output_bytes = BF16_TILE_BYTES if output_format == BF16 else F32_TILE_BYTES
  sentinel = b"\xA5" * output_bytes
  bh.launch(
    images, params=(F32_TILE_BYTES, count),
    l1={INPUT: source, output: sentinel}, profiler=profile,
  )
  actual = bh.read_l1(bh.core, output, output_bytes)
  assert actual[:len(expected)] == expected
  padding_end = actual.find(b"\xA5", len(expected))
  if padding_end < 0:
    padding_end = len(actual)
  assert padding_end - len(expected) <= 64
  assert actual[len(expected):padding_end] == bytes(padding_end - len(expected))
  assert actual[padding_end:] == sentinel[padding_end:]
  assert profile.last[label] > 0


def _bf16_nearest(value):
  bits = unpack("<I", pack("<f", value))[0]
  return ((bits + 0x8000) >> 16) & 0xFFFF


@pytest.mark.parametrize(("mode", "upper", "output_format", "count", "offset"), [
  ("relu", None, BF16, 17, 16),
  ("relu", None, F32, 137, 32),
  ("clamp", 1.5, BF16, 137, 32),
  ("clamp", 1.5, F32, 17, 16),
])
def test_packer_activation_is_a_standalone_partial_kernel(
  bh, mode, upper, output_format, count, offset,
):
  boundary = (-2.0, -0.25, 0.0, 0.5, 1.0, 1.5, 2.0, 8.0)
  values = tuple(boundary[index % len(boundary)] for index in range(TILE_ELEMENTS))
  source = pack(f"<{TILE_ELEMENTS}f", *values)
  if mode == "relu":
    relu_mode, threshold = 1, 0
    transformed = (max(value, 0.0) for value in values[offset:offset + count])
  else:
    relu_mode, threshold = 3, _bf16_nearest(upper)
    transformed = (
      min(max(value, 0.0), upper) for value in values[offset:offset + count]
    )
  transformed = tuple(transformed)
  expected = (
    pack(f"<{count}H", *(_bf16_nearest(value) for value in transformed))
    if output_format == BF16 else pack(f"<{count}f", *transformed)
  )
  format_name = "BF16" if output_format == BF16 else "F32"
  label = f"packer {mode} {format_name}"
  images, profile = _images(
    4, count, offset, label=label, relu_mode=relu_mode,
    relu_threshold=threshold, output_format=output_format,
  )
  output_bytes = BF16_TILE_BYTES if output_format == BF16 else F32_TILE_BYTES
  sentinel = b"\xA5" * output_bytes
  bh.launch(
    images, params=(F32_TILE_BYTES, count),
    l1={INPUT: source, OUTPUT: sentinel}, profiler=profile,
  )
  actual = bh.read_l1(bh.core, OUTPUT, output_bytes)
  assert actual[:len(expected)] == expected
  padding_end = actual.find(b"\xA5", len(expected))
  if padding_end < 0:
    padding_end = len(actual)
  assert padding_end - len(expected) <= 64
  assert actual[len(expected):padding_end] == bytes(padding_end - len(expected))
  assert actual[padding_end:] == sentinel[padding_end:]
  assert profile.last[label] > 0


def _rounding_source():
  words = tuple(
    ((0x3F00 + index % 0x70) << 16) |
    ((index * 40503 + 0x1234) & 0xFFFF)
    for index in range(TILE_ELEMENTS)
  )
  # Include positive/negative halfway values with even and odd retained LSBs.
  words = (0x3F008000, 0x3F018000, 0xBF008000, 0xBF018000) + words[4:]
  return words, pack(f"<{TILE_ELEMENTS}I", *words)


def _run_rounding(bh, source, *, stochastic, seed, label):
  images, profile = _images(
    6, TILE_ELEMENTS, 0, CB_PAGES[0], label=label,
    stochastic=stochastic, seed=seed, output_format=BF16,
    debug_rounding=True,
  )
  bh.launch(
    images, params=(F32_TILE_BYTES, TILE_ELEMENTS),
    l1={
      INPUT: source,
      CB_PAGES[0]: bytes(BF16_TILE_BYTES),
      ROUNDING_DEBUG: bytes(4),
    },
    profiler=profile,
  )
  rounding_config = unpack("<I", bh.read_l1(bh.core, ROUNDING_DEBUG, 4))[0]
  return (
    unpack(
      f"<{TILE_ELEMENTS}H",
      bh.read_l1(bh.core, CB_PAGES[0], BF16_TILE_BYTES),
    ),
    profile.last[label],
    rounding_config,
  )


def test_deterministic_and_stochastic_bf16_format_conversion(bh):
  words, source = _rounding_source()
  deterministic, deterministic_cycles, deterministic_config = _run_rounding(
    bh, source, stochastic=False, seed=0, label="deterministic rounding",
  )
  # With pack/gasket stochastic rounding disabled, the supported gasket path
  # performs round-to-nearest with ties away from zero (not ties to even).
  expected = tuple(
    ((word + 0x8000) >> 16) & 0xFFFF
    for word in words
  )
  assert deterministic == expected

  stochastic_a, stochastic_cycles, stochastic_config = _run_rounding(
    bh, source, stochastic=True, seed=0x13579BDF,
    label="stochastic rounding",
  )
  stochastic_repeat, _, _ = _run_rounding(
    bh, source, stochastic=True, seed=0x13579BDF,
    label="stochastic rounding repeat",
  )
  stochastic_b, _, _ = _run_rounding(
    bh, source, stochastic=True, seed=0x2468ACE0,
    label="stochastic rounding second seed",
  )
  neighbors = tuple(
    ({word >> 16} if (word & 0xFFFF) == 0 else
     {word >> 16, (word >> 16) + 1})
    for word in words
  )
  assert all(value in allowed for value, allowed in zip(stochastic_a, neighbors))
  assert deterministic_config & 0x6 == 0
  assert stochastic_config & 0x6 == 0x6
  assert stochastic_a != deterministic, "stochastic mode did not change any value"
  assert stochastic_repeat == stochastic_a
  assert stochastic_b != stochastic_a
  assert deterministic_cycles > 0
  assert stochastic_cycles > 0


def test_runtime_pack_codegen_has_constant_pacr_count():
  trisc2 = Asm("trisc2")
  count = _runtime_word(trisc2, 1)
  emit_pack_dst_to_cb(trisc2, 7, OUTPUT, count, dst_element_offset=32)
  opcodes = [
    int(word) >> 24 for word in trisc2.items if isinstance(word, TensixWord)
  ]
  # PACR lives only in MOP configuration. The two literal MOP sites cover a
  # runtime full-row loop and the optional final partial row.
  assert opcodes.count(0x41) == 0
  assert opcodes.count(0x01) == 2
  assert trisc2.lower()


def test_prng_initialization_repeats_sfpnop_with_mop():
  trisc1 = Asm("trisc1")
  initialize_prng(trisc1, 0x13579BDF)
  words = [
    int(word) for word in trisc1.items if isinstance(word, TensixWord)
  ]
  assert int(TT.TTSFPNOP()) not in words
  assert sum(word >> 24 == 0x01 for word in words) == 1
  assert trisc1.lower()
