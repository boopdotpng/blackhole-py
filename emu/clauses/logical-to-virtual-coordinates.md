# logical-to-virtual-coordinates

**Source:** [`logical-to-virtual-coordinates.md`](../specs/logical-to-virtual-coordinates.md)

## Coordinate systems

### `L2V.SYSTEMS.THREE_COORD`
§1 Coordinate Systems

> Three coordinate systems exist: Physical (NOC0 wire), Virtual (post-NIU-translation, what firmware writes to TARG_ADDR_HI), and Logical (sequential, harvesting-agnostic).

### `L2V.SYSTEMS.CHAIN`
§1 Coordinate Systems / translation chain

> Translation chain: Logical → Virtual (SW table in LDM) → Physical (NIU hardware).

## L1 scratch layout

### `L2V.SCRATCH.BASE_ADDR`
§3 L1 Scratch Region

> Translation arrays are written to L1 offset 0x11EB0 (MEM_BANK_TO_NOC_SCRATCH + 2048).

### `L2V.SCRATCH.COL_SIZE`
§3 L1 Scratch Region / layout

> worker_logical_col_to_virtual_col: 20 bytes (noc_size_x=17 rounded up to 20).

### `L2V.SCRATCH.ROW_SIZE`
§3 L1 Scratch Region / layout

> worker_logical_row_to_virtual_row: 12 bytes (noc_size_y=12).

### `L2V.MAP.P100A_COL`
§2 LDM Translation Arrays / unharvested

> Unharvested P100A: logical col 0→x=1, 1→2, ..., 6→7, 7→10, 8→11, 9→12, 10→13, 11→14. Indices 12–19 zero-padded.

### `L2V.MAP.ROW_RANGE`
§2 LDM Translation Arrays / row table

> Logical row 0 maps to virtual y=2, row 1→3, ..., row 9→11. Indices 10–11 zero-padded.

### `L2V.MAP.HARVESTED_COL_SKIP`
§2 LDM Translation Arrays / harvested example

> When column x=3 is harvested: col_table[2]=4 (skipping 3). All higher entries shift left.

### `L2V.NIU.TRANSLATE_EN`
§7 NIU Hardware Translation Tables

> NIU hardware performs virtual→physical translation on every NOC transaction when NIU_CFG_0 bit 14 (NOC_ID_TRANSLATE_EN) is set.

### `L2V.NIU.NOC1_MIRROR`
§7 NIU Hardware Translation Tables / NOC1

> NOC1 translation: noc1_x[i] = NOC_X_SIZE - noc0_x[i] - 1 (mirror of NOC0).

## Per-core identity

### `L2V.IDENTITY.LOGICAL_XY`
§6 Per-Core Logical Identity

> Each core's logical coordinates are stored in core_info_msg_t.absolute_logical_x/y in the L1 mailbox structure, written by the host before boot.

