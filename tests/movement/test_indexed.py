from statistics import median
from struct import Struct, pack

import pytest

from asm import Asm
from fw.consts import TensixL1, TensixMMIO
from tests.movement.indexed import (
  IndexedConfig, emit_indexed_gather, emit_indexed_scatter,
)


PAGE_BYTES = 2048
ROW_BYTES = 768
VOCAB_ROWS = 24
LOOKUP_COUNT = 4
INDICES_ADDRESS = TensixL1.DATA_BUFFER_SPACE_BASE
ROWS_ADDRESS = INDICES_ADDRESS + 4096
TIMING_ADDRESS = TensixL1.DATA_BUFFER_SPACE_END - 16
TIMING_RECORD = Struct("<4I")
GATHER_IDS = (21, 2, 21, 16)
SCATTER_IDS = (22, 1, 22, 17)

LLAMA_VOCAB_ROWS = 128256
LLAMA_EMBED_ELEMENTS = 2048
LLAMA_ROW_BYTES = LLAMA_EMBED_ELEMENTS * 2
BENCHMARK_COUNTS = (1, 4, 16, 64)
BENCHMARK_REPEATS = 7
CLOCK_GHZ = 1.35


def _matrix(rows, seed=0):
  return b"".join(
    bytes((seed + row * 29 + byte) & 0xff for byte in range(ROW_BYTES))
    for row in range(rows)
  )


def _indices(values):
  return pack(f"<{len(values)}I", *values)


def _config(bh=None, *, row_count=LOOKUP_COUNT, row_bytes=ROW_BYTES):
  coordinates = (
    tuple(range(8)) if bh is None else bh.dram_coordinates(noc=0, banks=8)
  )
  return IndexedConfig(
    coordinates, INDICES_ADDRESS, ROWS_ADDRESS, row_count, row_bytes,
    PAGE_BYTES,
  )


def _record_clock(kernel, address):
  low, high, high_again, clock, output = kernel.reg(5)
  retry = kernel._new_label("indexed_clock_retry")
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


def _elapsed_cycles(bh):
  lo0, hi0, lo1, hi1 = TIMING_RECORD.unpack(
    bh.read_l1(bh.core, TIMING_ADDRESS, TIMING_RECORD.size),
  )
  return (lo1 | hi1 << 32) - (lo0 | hi0 << 32)


def test_indexed_configuration_and_lowering():
  config = _config()
  gather, scatter = Asm("brisc"), Asm("brisc")
  emit_indexed_gather(gather, config)
  emit_indexed_scatter(scatter, config)
  assert gather.lower() and scatter.lower()
  with pytest.raises(ValueError, match="overlap"):
    IndexedConfig(tuple(range(8)), ROWS_ADDRESS, ROWS_ADDRESS, 4, PAGE_BYTES)
  with pytest.raises(ValueError, match="16-byte-aligned"):
    IndexedConfig(tuple(range(8)), INDICES_ADDRESS, ROWS_ADDRESS, 4, 18)


def test_brisc_indexed_gather_with_duplicate_ids(bh):
  matrix = _matrix(VOCAB_ROWS)
  table = bh.interleaved_dram_buffer(
    len(matrix), page_size=PAGE_BYTES, banks=8, initial=matrix,
  )
  kernel = Asm("brisc")
  emit_indexed_gather(kernel, _config(bh))
  bh.launch(
    {"brisc": kernel.lower()}, params=(table.address,),
    l1={
      INDICES_ADDRESS: _indices(GATHER_IDS),
      ROWS_ADDRESS: bytes(LOOKUP_COUNT * ROW_BYTES),
    },
  )

  expected = b"".join(
    matrix[index * ROW_BYTES:(index + 1) * ROW_BYTES]
    for index in GATHER_IDS
  )
  assert bh.read_l1(bh.core, ROWS_ADDRESS, len(expected)) == expected


def test_brisc_indexed_scatter_last_duplicate_wins(bh):
  initial = bytes([0xA5]) * (VOCAB_ROWS * ROW_BYTES)
  table = bh.interleaved_dram_buffer(
    len(initial), page_size=PAGE_BYTES, banks=8, initial=initial,
  )
  source = _matrix(LOOKUP_COUNT, seed=73)
  kernel = Asm("brisc")
  emit_indexed_scatter(kernel, _config(bh))
  bh.launch(
    {"brisc": kernel.lower()}, params=(table.address,),
    l1={
      INDICES_ADDRESS: _indices(SCATTER_IDS),
      ROWS_ADDRESS: source,
    },
  )

  expected = bytearray(initial)
  for source_row, destination_row in enumerate(SCATTER_IDS):
    start = source_row * ROW_BYTES
    destination = destination_row * ROW_BYTES
    expected[destination:destination + ROW_BYTES] = source[
      start:start + ROW_BYTES
    ]
  assert bh.read(table) == expected


def test_llama3_embedding_gather_benchmark(bh):
  """Time Llama 3.2 1B BF16[128256, 2048] indexed row reads."""
  table = bh.device.alloc_interleaved_dram(
    LLAMA_VOCAB_ROWS * LLAMA_ROW_BYTES,
    page_size=PAGE_BYTES, banks=8,
  )
  rows = []
  for count in BENCHMARK_COUNTS:
    ids = tuple((17 + index * 7919) % LLAMA_VOCAB_ROWS for index in range(count))
    config = _config(bh, row_count=count, row_bytes=LLAMA_ROW_BYTES)
    kernel = Asm("brisc")
    _record_clock(kernel, TIMING_ADDRESS)
    emit_indexed_gather(kernel, config)
    _record_clock(kernel, TIMING_ADDRESS + 8)
    image = kernel.lower()
    samples = []
    for _ in range(BENCHMARK_REPEATS):
      bh.launch(
        {"brisc": image}, params=(table.address,),
        l1={INDICES_ADDRESS: _indices(ids)},
      )
      samples.append(_elapsed_cycles(bh))
    cycles = median(samples)
    byte_count = count * LLAMA_ROW_BYTES
    rows.append((
      count, cycles, cycles / (CLOCK_GHZ * 1000),
      byte_count * CLOCK_GHZ / cycles,
    ))

  print(
    "\nLlama 3.2 1B embedding gather on BRISC/NoC0 "
    "(BF16[128256, 2048], median of 7)\n"
    "lookups | bytes | cycles | latency us | effective GB/s"
  )
  for count, cycles, latency_us, gb_s in rows:
    print(
      f"{count:7d} | {count * LLAMA_ROW_BYTES:5d} | {cycles:6.0f} | "
      f"{latency_us:10.3f} | {gb_s:14.2f}"
    )
