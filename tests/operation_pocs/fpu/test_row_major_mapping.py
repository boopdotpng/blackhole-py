"""Expose native matrix coordinates with raw sequential BF16 input bytes.

Two adjacent A128 slots form one A[16,16]; one B128 slot is B[8,16].
No host tilization or unpack transpose is used. Observe FP32 Dst to avoid
output rounding obscuring the integer matrix products.
"""
from struct import pack, unpack

import pytest

from tests.operation_pocs.fpu.fixture import INPUT, INPUT_A, INPUT_B, OUTPUT, images


@pytest.mark.parametrize("op,b_kind", [
    ("mvmul", "arange"), ("gapool", "arange"),
    ("gapool", "ones"), ("gmpool", "ones"),
    ("mvmul", "select-top"), ("mvmul", "select-bottom"),
], ids=("mvmul-arange", "gapool-arange", "gapool-column-sum", "gmpool-column-max",
        "mvmul-select-top", "mvmul-select-bottom"))
@pytest.mark.parametrize("a_slot,b_slot,dst_slot", [(0, 0, 0), (6, 7, 63)])
@pytest.mark.parametrize("seed", [0., 1048576.], ids=("zero-dst", "accumulate"))
def test_row_major_matrix_mapping(bh, op, b_kind, a_slot, b_slot, dst_slot, seed):
    a = list(range(256))
    b = [1] * 128 if b_kind == "ones" else list(range(128))
    if b_kind.startswith("select-"):
        first = 8 if b_kind == "select-bottom" else 0
        b = [int(c == r + first) for r in range(8) for c in range(16)]
    banks = [[-17.] * 1024, [-19.] * 1024]
    banks[0][a_slot * 128:a_slot * 128 + 256] = a
    banks[1][b_slot * 128:b_slot * 128 + 128] = b
    initial = [-1234.] * 1024
    offset = (dst_slot % 8) * 128
    initial[offset:offset + 128] = [seed] * 128
    expected = initial.copy()
    if op == "gmpool":
        # B=1 gives unscaled column maxima. GMPOOL also clears three rows.
        expected[offset:offset + 16] = [max(seed, max(a[k * 16 + c] for k in range(16))) for c in range(16)]
        expected[offset + 16:offset + 64] = [0.] * 48
    else:
        for r in range(8 if op == "mvmul" else 4):
            for c in range(16):
                expected[offset + r * 16 + c] = seed + sum(b[r * 16 + k] * a[k * 16 + c] for k in range(16))
    data = {INPUT: pack("<1024f", *initial), OUTPUT: b"\xa5" * 4160}
    for address, bank in zip((INPUT_A, INPUT_B), banks):
        data[address] = pack("<1024H", *(unpack("<I", pack("<f", v))[0] >> 16 for v in bank))
    code, profile = images(op, a_slot, b_slot, dst_slot, repeats=1)
    bh.launch(code, l1=data, profiler=profile)
    actual = unpack("<1024f", bh.read_l1(bh.core, OUTPUT, 4096))
    errors = [(i, x, y) for i, (x, y) in enumerate(zip(actual, expected)) if x != y]
    # HiFi2 arange measurements have up to 4 absolute error for MVMUL and
    # 1 for GAPOOL. This is a layout test, not a bit-exact FPU model. Only
    # those product outputs get tolerance; selectors, pooling and guards
    # must match exactly. Selector cases expose every A coordinate exactly.
    active = 128 if op == "mvmul" else 64
    tolerance = (4 if op == "mvmul" else 1) if b_kind == "arange" else 0
    assert all(abs(x - y) <= (tolerance if offset <= i < offset + active else 0)
               for i, x, y in errors), errors[:16]
    assert bh.read_l1(bh.core, OUTPUT + 4096, 64) == b"\xa5" * 64
    if (a_slot, b_slot, dst_slot, seed) == (0, 0, 0, 0.):
        print(f"{op} B={b_kind}: max_abs_error={max((abs(x-y) for _, x, y in errors), default=0)}; Dst rows="
              f"{[list(actual[r * 16:(r + 1) * 16]) for r in range(8)]}")
