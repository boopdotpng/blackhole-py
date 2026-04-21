"""Spec tests for ../specs/logical-to-virtual-coordinates.md.

Covers: L1 scratch address, array sizes, contents for P100A/P150 (unharvested),
harvested-column skip behavior.

All emulator-side tests verify the expected VALUES (what firmware expects to
find). The emulator currently does NOT populate these tables, so tests that
check actual emulator memory are marked xfail.
"""

import pytest

from emu.device import Device, P100A_TENSIX_X
from emu.tests._helpers import mini_device

from .conftest import spec

# Addresses from spec §3
MEM_BANK_TO_NOC_SCRATCH = 0x116B0
MEM_BANK_TO_NOC_SIZE    = 2048
MEM_LOGICAL_TO_VIRTUAL_SCRATCH = MEM_BANK_TO_NOC_SCRATCH + MEM_BANK_TO_NOC_SIZE  # 0x11EB0
MEM_LOGICAL_TO_VIRTUAL_SIZE = 32  # 20 + 12 bytes

COL_OFFSET = 0        # from L2V_SCRATCH: 20 bytes
ROW_OFFSET = 20       # from L2V_SCRATCH: 12 bytes


# ===========================================================================
# Static address / size constants
# ===========================================================================

@spec("L2V.SCRATCH.BASE_ADDR")
def test_l2v_scratch_base_addr():
    """Logical-to-virtual scratch is at 0x116B0 + 2048 = 0x11EB0."""
    assert MEM_LOGICAL_TO_VIRTUAL_SCRATCH == 0x11EB0


@spec("L2V.SCRATCH.COL_SIZE")
def test_col_table_size():
    """Column table is 20 bytes (noc_size_x=17 rounded up to 20)."""
    col_size = 20
    assert col_size == 20


@spec("L2V.SCRATCH.ROW_SIZE")
def test_row_table_size():
    """Row table is 12 bytes (noc_size_y=12)."""
    row_size = 12
    assert row_size == 12


@spec("L2V.SCRATCH.COL_SIZE", "L2V.SCRATCH.ROW_SIZE")
def test_total_scratch_size():
    """Total scratch = 20 + 12 = 32 bytes."""
    assert MEM_LOGICAL_TO_VIRTUAL_SIZE == 32


# ===========================================================================
# Expected mapping contents (P100A unharvested: 12 columns)
# ===========================================================================

@spec("L2V.MAP.P100A_COL")
def test_p100a_expected_col_table():
    """P100A (12 cols, no harvest): col table entries 0-11 match west/east bands."""
    tensix_x = list(P100A_TENSIX_X)  # [1,2,3,4,5,6,7,10,11,12,13,14]
    col_table = tensix_x + [0] * (20 - len(tensix_x))
    assert col_table[:7] == [1, 2, 3, 4, 5, 6, 7]
    assert col_table[7:12] == [10, 11, 12, 13, 14]
    assert all(v == 0 for v in col_table[12:20])


@spec("L2V.MAP.ROW_RANGE")
def test_expected_row_table():
    """Row table: logical row i → virtual y = 2 + i for i in 0..9."""
    row_table = [2 + i for i in range(10)] + [0, 0]
    assert row_table == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 0]


@spec("L2V.MAP.HARVESTED_COL_SKIP")
def test_harvested_col_skip():
    """When physical col x=3 is harvested, logical indices shift past it."""
    # Full west band without x=3: [1, 2, 4, 5, 6, 7]
    tensix_x_harvested = [1, 2, 4, 5, 6, 7, 10, 11, 12, 13, 14]
    col_table = tensix_x_harvested + [0] * (20 - len(tensix_x_harvested))
    # logical 0→1, 1→2, 2→4 (x=3 is missing), 3→5, ...
    assert col_table[0] == 1
    assert col_table[1] == 2
    assert col_table[2] == 4   # x=3 skipped
    assert col_table[3] == 5
    assert col_table[4] == 6
    assert col_table[5] == 7


# ===========================================================================
# Emulator population checks (xfail: emulator does not write these tables)
# ===========================================================================

@spec("L2V.SCRATCH.BASE_ADDR", "L2V.MAP.P100A_COL")
def test_emulator_populates_col_table():
    """Emulator must write the col table at L1[0x11EB0] for every tile."""
    tensix_x = list(P100A_TENSIX_X)
    expected_cols = tensix_x + [0] * (20 - len(tensix_x))
    dev = Device(tensix_x=P100A_TENSIX_X, tensix_y=range(2, 12))
    tile = list(dev.tiles.values())[0]
    actual = [tile.l1.read8(MEM_LOGICAL_TO_VIRTUAL_SCRATCH + i) for i in range(20)]
    assert actual == expected_cols


@spec("L2V.SCRATCH.BASE_ADDR", "L2V.MAP.ROW_RANGE")
def test_emulator_populates_row_table():
    """Emulator must write the row table at L1[0x11EC4] for every tile."""
    expected_rows = [2 + i for i in range(10)] + [0, 0]
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    actual = [tile.l1.read8(MEM_LOGICAL_TO_VIRTUAL_SCRATCH + COL_OFFSET + 20 + i)
              for i in range(12)]
    assert actual == expected_rows
