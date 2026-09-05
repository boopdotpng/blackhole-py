"""Compare source distances while preserving each arithmetic instruction's footprint."""
from statistics import median
from struct import pack, unpack

import pytest

from tests.compute.fpu.test_elwmul_slots import INPUT, INPUT_A, INPUT_B, OUTPUT, REPEATS, SAMPLES, _images

CASES = (
  ("contiguous", (0, 2), (0, 1)),
  ("opposite ends", (0, 6), (0, 7)),
  ("opposite mismatched", (0, 6), (7, 0)),
  ("contiguous mismatched", (0, 2), (6, 7)),
)


def _inputs(operation, a_slots, b_slots):
  a_size = 128 if operation == "ELWADD" else 256
  a = [[1 + ((i * 13 + block * 29) % 128) / 128 for i in range(a_size)] for block in range(2)]
  b = [[0.5 + ((i * 37 + block * 11) % 64) / 128 for i in range(128)] for block in range(2)]
  if operation == "GMPOOL": b = [[1.] * 128 for _ in range(2)]
  initial = [1 + (i % 16) / 16 for i in range(256)]
  expected = initial.copy()
  for block in range(2):
    offset = block * 128
    if operation == "ELWADD":
      for i in range(128): expected[offset+i] += REPEATS * (a[block][i] + b[block][i])
    elif operation in ("MVMUL", "GAPOOL"):
      rows = 8 if operation == "MVMUL" else 4
      for row in range(rows):
        for col in range(16):
          expected[offset+row*16+col] += REPEATS * sum(b[block][row*16+k] * a[block][k*16+col] for k in range(16))
    else:
      for col in range(16): expected[offset+col] = max(initial[offset+col], *(a[block][row*16+col] for row in range(16)))
      expected[offset+16:offset+64] = [0.] * 48
  data = {INPUT: pack("<1024f", *initial, *([0.] * 768)), OUTPUT: b"\xA5" * 1088}
  for address, blocks, slots in ((INPUT_A, a, a_slots), (INPUT_B, b, b_slots)):
    physical = [0x4100 + i % 128 for i in range(1024)]
    for values, slot in zip(blocks, slots):
      physical[slot*128:slot*128+len(values)] = [unpack("<I", pack("<f", x))[0] >> 16 for x in values]
    data[address] = pack("<1024H", *physical)
  return data, pack("<256f", *expected)


@pytest.mark.parametrize("operation,name,a_slots,b_slots", [
  pytest.param(op, name, a, b, id=f"{op}-{name}")
  for op in ("ELWADD", "MVMUL", "GAPOOL", "GMPOOL") for name, a, b in CASES
] + [
  pytest.param(op, "odd counter rounds down", (1, 5), (7, 0), id=f"{op}-odd-counter-rounds-down")
  for op in ("MVMUL", "GAPOOL")
])
def test_arithmetic_source_slot_placement(bh, operation, name, a_slots, b_slots):
  if operation == "ELWADD":
    a_slots = (0, 1) if a_slots == (0, 2) else (0, 7)
  images, profile = _images(a_slots, b_slots, operation)
  # A uses aligned 16-row blocks on Blackhole, including MVMUL/GAPOOL.
  physical_a = tuple(slot & ~1 for slot in a_slots) if name == "odd counter rounds down" else a_slots
  data, expected = _inputs(operation, physical_a, b_slots)
  samples = []
  for _ in range(SAMPLES):
    bh.launch(images, l1=data, profiler=profile)
    actual = bh.read_l1(bh.core, OUTPUT, 1024)
    assert unpack("<256f", actual) == unpack("<256f", expected)
    assert bh.read_l1(bh.core, OUTPUT + 1024, 64) == b"\xA5" * 64
    samples.append(profile.last["HiFi2 accumulate"] / REPEATS)
  print(f"{operation} {name}: A={a_slots}, B={b_slots}; cycles per pair "
        f"median={median(samples):.3f}, min={min(samples):.3f}, max={max(samples):.3f}")
