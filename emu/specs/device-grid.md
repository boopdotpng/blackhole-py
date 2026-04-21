# Blackhole Device Grid Topology — Emulator Specification

This document describes the NOC grid layout for the Blackhole P100A and P150 boards as the emulator must model it. All coordinates are in the translated NOC coordinate space that firmware uses. Source of truth is `blackhole-py/hw.py` and `blackhole-py/device.py`.

---

## 1. Grid Overview

Blackhole has a 2D NOC grid with several classes of tile. Not every grid position is a Tensix compute tile; some columns and rows are occupied by DRAM controllers, the PCIe endpoint, and ARC/router tiles, or are harvested.

| Tile class | Description |
|---|---|
| Tensix compute | Worker cores with 5 RISC-V processors, L1, and Tensix FPU |
| DRAM controller | DDR controller tiles; each physical bank has 3 NOC ports |
| PCIe endpoint | Single tile that bridges to host system memory |
| ARC / router | Management processor; defined in `TileGrid.ARC = (8, 0)` |

The full NOC grid is 32 columns × 32 rows in the physical address space, but most of that area is routing fabric. Only the tiles enumerated in this document are functional nodes the emulator must register.

---

## 2. P100A Tensix Tile Coordinates

Source: `device.py` `P100 = BoardConfig(tensix_x=(*range(1, 8), *range(10, 15)), ...)`

### X columns (Tensix)

P100A has two non-contiguous bands of Tensix columns:

| Band | X values |
|---|---|
| West band | 1, 2, 3, 4, 5, 6, 7 |
| East band | 10, 11, 12, 13, 14 |

Total: 12 Tensix columns.

Columns 0, 8, 9, 15–18 are not Tensix columns on P100A. Columns 17 and 18 are the DRAM controller columns (see section 4). Column 0 is the western NOC edge / router. Column 8 is ARC. Column 9 is a router / NOC bridge column.

### Y rows (Tensix)

Source: `hw.py` `worker_cores()`:
```python
def worker_cores(tensix_x: tuple[int, ...]) -> list[Core]:
    return [(x, y) for x in tensix_x for y in range(2, 12)]
```

Y rows are **2 through 11**, inclusive (10 rows).

Rows 0 and 1 are edge/router rows not used for compute. Rows 12 and above are in the DRAM controller area.

### Core count

12 columns × 10 rows = **120 Tensix cores** on P100A (before any Tensix column harvesting).

### Dispatch cores

When fast-dispatch is enabled, two cores in the east band are reserved for the command queue (CQ) infrastructure and are not available for user kernels:

| Role | Coordinate (x, y) |
|---|---|
| Prefetch core | (14, 2) |
| Dispatch core | (14, 3) |

Both sit in the last east-band column (x=14). Cores (14, 4) through (14, 11) remain available for compute. The prefetch core reads the command ring buffer from host sysmem via PCIe; the dispatch core writes launch messages to worker tile L1.

User-visible worker count with fast-dispatch: 120 − 2 = **118 cores**.

---

## 3. P150 Tensix Tile Coordinates

Source: `device.py` `P150 = BoardConfig(tensix_x=(*range(1, 8), *range(10, 17)), ...)`

### X columns (Tensix)

| Band | X values |
|---|---|
| West band | 1, 2, 3, 4, 5, 6, 7 |
| East band | 10, 11, 12, 13, 14, 15, 16 |

Total: 14 Tensix columns. The east band is two columns wider than P100A, extending to x=16.

### Y rows (Tensix)

Same as P100A: rows **2 through 11** (10 rows).

### Core count

14 columns × 10 rows = **140 Tensix cores** on P150.

### Dispatch cores

| Role | Coordinate (x, y) |
|---|---|
| Prefetch core | (16, 2) |
| Dispatch core | (16, 3) |

Both sit at x=16 (the last east-band column on P150). User-visible worker count with fast-dispatch: 140 − 2 = **138 cores**.

---

## 4. DRAM Bank Tile Coordinates

Source: `hw.py` `class Dram`

### Physical layout constants

```python
BANK_COUNT   = 8           # physical banks total
TILES_PER_BANK = 3         # NOC port tiles per bank

BANK_X = {b: 0 if b < 4 else 9 for b in range(8)}
# Physical NOC column: banks 0-3 at x=0 (west), banks 4-7 at x=9 (east)
# Note: these are physical coordinates. build_bank_noc_table() assigns
# translated coordinates (x=17 west, x=18 east) to the active banks.

BANK_TILE_YS = {
    0: (0, 1, 11),
    1: (2, 3, 10),
    2: (4, 8, 9),
    3: (5, 6, 7),
    4: (0, 1, 11),
    5: (2, 3, 10),
    6: (4, 8, 9),
    7: (5, 6, 7),
}
# Three physical Y coordinates (the 3 NOC ports) for each physical bank.
# East and west banks share the same Y pattern.
```

### Translated coordinates used in firmware

`build_bank_noc_table()` assigns **translated** coordinates from the `x=17` (west) and `x=18` (east) columns, not the raw physical ones above. Each bank gets a base Y and occupies 3 consecutive Y values (the 3 ports). The 7-bank P100A layout always places 4 banks on x=17 and 3 on x=18:

| Software bank ID | Column | Base Y (y₀) | Port Y range |
|---|---|---|---|
| 0 | 17 | 12 | 12, 13, 14 |
| 1 | 17 | 15 | 15, 16, 17 |
| 2 | 17 | 18 | 18, 19, 20 |
| 3 | 17 | 21 | 21, 22, 23 |
| 4 | 18 | 12 | 12, 13, 14 |
| 5 | 18 | 15 | 15, 16, 17 |
| 6 | 18 | 18 | 18, 19, 20 |

The 8-bank P150 layout (no harvested bank) uses the same scheme but fills both x=17 and x=18 with 4 banks each:

| Software bank ID | Column | Base Y (y₀) | Port Y range |
|---|---|---|---|
| 0 | 17 | 12 | 12, 13, 14 |
| 1 | 17 | 15 | 15, 16, 17 |
| 2 | 17 | 18 | 18, 19, 20 |
| 3 | 17 | 21 | 21, 22, 23 |
| 4 | 18 | 12 | 12, 13, 14 |
| 5 | 18 | 15 | 15, 16, 17 |
| 6 | 18 | 18 | 18, 19, 20 |
| 7 | 18 | 21 | 21, 22, 23 |

### Port selection per NOC (`BANK_PORT`)

Firmware does not use all 3 ports simultaneously. `build_bank_noc_table()` selects one port per bank per NOC using this table:

```python
BANK_PORT = [[2,1],[0,1],[0,1],[0,1],[2,1],[2,1],[2,1],[2,1]]
# Index:  bank 0  1    2    3    4    5    6    7
# [noc0_port_offset, noc1_port_offset]
# Port offset is added to the bank's base Y.
```

The actual NOC coordinate firmware targets for a given bank and NOC is `(x, y₀ + BANK_PORT[bank][noc])`.

For P100A 7-bank layout the active port coordinates are:

| SW bank | Base (x, y₀) | NOC 0 port | NOC 1 port |
|---|---|---|---|
| 0 | (17, 12) | (17, 14) — offset +2 | (17, 13) — offset +1 |
| 1 | (17, 15) | (17, 15) — offset +0 | (17, 16) — offset +1 |
| 2 | (17, 18) | (17, 18) — offset +0 | (17, 19) — offset +1 |
| 3 | (17, 21) | (17, 21) — offset +0 | (17, 22) — offset +1 |
| 4 | (18, 12) | (18, 14) — offset +2 | (18, 13) — offset +1 |
| 5 | (18, 15) | (18, 17) — offset +2 | (18, 16) — offset +1 |
| 6 | (18, 18) | (18, 20) — offset +2 | (18, 19) — offset +1 |

All 3 port tiles per bank alias the same physical DDR controller and the same backing memory in the emulator.

---

## 5. PCIe Endpoint

Source: `hw.py` `class Sysmem`

```python
PCIE_NOC_XY = (24 << 6) | 19  # = 0x613 = 1555 decimal
```

| Field | Value |
|---|---|
| X coordinate | 19 |
| Y coordinate | 24 |
| Packed uint16 `(y << 6) \| x` | `0x0613` (1555) |

The PCIe endpoint is a single NOC node. Transactions targeting it must also set **bit 60** of the 64-bit NOC address, which appears as **bit 28 of `NOC_TARG_ADDR_MID`** (value `0x10000000`). See `niu.md` §4 and `dram.md` §3 for the full PCIe transaction encoding.

---

## 6. Bank-to-NOC Table

Before firmware boots, the emulator must write a bank-to-NOC lookup table to every worker tile's L1 at:

```
MEM_BANK_TO_NOC_SCRATCH = 0x0116B0    (from TensixL1 in hw.py)
```

Firmware's `noc_bank_table_init()` reads this table during the BRISC/NCRISC/TRISC init phase and copies it into core-private LDM (see `firmware-upload.md` §BRISC Init). The table must be present and correct before any RISC-V core exits reset.

### Table layout

All fields are little-endian. The table is produced by `build_bank_noc_table()` in `hw.py`.

```
Offset from 0x0116B0    Size                    Contents
─────────────────────────────────────────────────────────────────────
+0x000                  NUM_NOCS × NUM_DRAM_BANKS × 2 bytes    dram_bank_to_noc_xy  (uint16[])
                        (continues)             NUM_NOCS × NUM_L1_BANKS × 2 bytes    l1_bank_to_noc_xy    (uint16[])
+0x400                  NUM_DRAM_BANKS × 4 bytes                bank_to_dram_offset  (uint32[])
                        (continues)             NUM_L1_BANKS × 4 bytes                bank_to_l1_offset    (uint32[])
```

Constants for P100A with 1 harvested bank:

| Constant | Value |
|---|---|
| `NUM_NOCS` | 2 |
| `NUM_DRAM_BANKS` | 7 (8 physical − 1 harvested) |
| `NUM_L1_BANKS` | number of active worker cores (120 for P100A, or 118 with fast-dispatch) |

For P150 (no harvested bank): `NUM_DRAM_BANKS = 8`.

### Entry encoding

Each `uint16` NOC XY entry is packed as:

```
entry = (y << 6) | x
```

matching the `noc_xy()` helper in `hw.py`:
```python
def noc_xy(x: int, y: int) -> int:
    return ((y << 6) | x) & 0xFFFF
```

### `dram_bank_to_noc_xy` layout

The DRAM section is laid out as `[noc][bank]` order:

```
NOC 0: bank 0 xy, bank 1 xy, ..., bank 6 xy   (7 × uint16 = 14 bytes)
NOC 1: bank 0 xy, bank 1 xy, ..., bank 6 xy   (7 × uint16 = 14 bytes)
```

Each entry is the translated port coordinate selected by `BANK_PORT[bank][noc]`.

### `l1_bank_to_noc_xy` layout

The L1 section assigns one NOC coordinate per logical L1 bank. `build_bank_noc_table()` iterates worker cores in column-major order (all rows of column 0, then all rows of column 1, etc.):

```python
cols = sorted({x for x, _ in worker_cores})
for _ in range(NOCS):
    for i in range(num_l1_banks):
        l1.append(noc_xy(cols[i % len(cols)], 2 + (i // len(cols)) % 10))
```

Both NOC 0 and NOC 1 sections use identical coordinate values for L1.

### `bank_to_dram_offset` and `bank_to_l1_offset`

Both offset arrays are filled with zeros in the current implementation:

```python
struct.pack(f"<...{num_dram_banks + num_l1_banks}i", ..., *([0] * (num_dram_banks + num_l1_banks)))
```

The per-bank offset fields exist to allow non-zero base addresses within a bank's address space. In practice they are unused and the emulator can initialize them to zero.

---

## 7. Harvesting

### DRAM bank harvesting

P100A chips have exactly **1 of 8 physical DRAM banks disabled** (harvested). The harvested bank varies per chip and is reported in the ARC telemetry tag `TAG_GDDR_ENABLED` (tag 36, an 8-bit mask where bit N = 0 means bank N is harvested). The default enabled mask is `0xFF` (all 8 banks enabled); a chip with bank 2 harvested would report `0xFB`.

`build_bank_noc_table()` handles this remap: it takes `harvested_dram_banks: list[int]` and ensures the 7 active banks occupy software IDs 0–6 contiguously. The harvested bank's "mirror" (the bank on the opposite column at the equivalent controller position) is pushed to the last slot of its column so that the 4+3 split is maintained.

From `hw.py`:
```python
if len(harvested_dram_banks) == 1:
    h = harvested_dram_banks[0]
    half = 4
    mirror = h + half - 1 if h < half else h - half
    if h < half:
        right = list(range(half - 1))
        left = [b for b in range(half - 1, Dram.BANK_COUNT - 1) if b != mirror] + [mirror]
    else:
        left = [b for b in range(half) if b != mirror] + [mirror]
        right = list(range(half, Dram.BANK_COUNT - 1))
```

The emulator must query the harvesting mask before constructing the bank table. In a software emulator without real hardware, default to bank 7 harvested (or any single bank, consistently) unless the spec under test requires a specific bank.

### Tensix column harvesting

The ARC tag `TAG_TENSIX_ENABLED_COL` (tag 34) is a 14-bit mask of enabled Tensix columns. The default is `0x3FFF` (all 14 columns enabled). If a column is disabled, the corresponding X value should not appear in the `tensix_x` tuple and those 10 cores should not be registered.

Active Tensix core count from mask:
```python
def active_tensix_core_count(enabled_col_mask: int) -> int:
    return (enabled_col_mask & Arc.DEFAULT_TENSIX_ENABLED).bit_count() * 10
```

---

## 8. Emulator Setup

The emulator must perform the following steps before releasing any RISC-V core from reset.

### Step 1 — Register Tensix tiles

For each `(x, y)` in `worker_cores(tensix_x)`:
- Allocate 1.5 MB (`TensixL1.SIZE = 0x180000`) of L1 backing memory.
- Register the tile in the NOC routing table at coordinate `(x, y)`.
- Pre-populate both NIU instances (NOC 0 and NOC 1):
  - `NOC_ID_LOGICAL` at `NIU_base + 0x148` = `(y << 6) | x`
  - `NOC_NODE_ID` at `NIU_base + 0x44` = `(y << 6) | x`
  - All status counters initialized to 0.

The `NOC_ID_LOGICAL` register is what firmware reads in `noc_init()` to discover its own coordinates (see `niu.md` §5 and §9).

### Step 2 — Register DRAM controller nodes

For each active software bank (0 through `NUM_DRAM_BANKS − 1`):
- Allocate a single backing buffer (e.g. 64 MiB) for the bank.
- Register all 3 port coordinates `(x, y₀ + 0)`, `(x, y₀ + 1)`, `(x, y₀ + 2)` in the NOC routing table, all pointing to the same backing buffer.

Total NOC entries for DRAM: 7 banks × 3 ports = **21 NOC coordinates** on P100A, or 8 × 3 = **24** on P150.

Reads and writes to any port of a bank address into the same flat `bytearray`. There is no data striping across ports.

### Step 3 — Register PCIe endpoint

Register NOC coordinate `(19, 24)` in the routing table as the PCIe endpoint node with a separate host-sysmem backing buffer.

When a NIU transaction targets `(19, 24)` with `NOC_TARG_ADDR_MID` bit 28 set (the PCIe flag), route it to this buffer at the address given by the low 36 bits.

### Step 4 — Pre-populate `NOC_ID_LOGICAL`

For every registered Tensix tile, write the packed coordinate `(y << 6) | x` into the `NOC_ID_LOGICAL` configuration register (at offset `0x148` from each NIU base). This is done for both NOC 0 (`NIU_base = 0xFFB20000`) and NOC 1 (`NIU_base = 0xFFB30000`).

On real hardware, ARC firmware programs this before releasing Tensix cores. In the emulator, it must be set before `SOFT_RESET_0` is cleared.

### Step 5 — Write bank-to-NOC tables to L1

For every registered Tensix tile (including the dispatch and prefetch cores), write the output of `build_bank_noc_table(harvested_dram_banks, all_worker_cores)` to that tile's L1 at offset `MEM_BANK_TO_NOC_SCRATCH = 0x0116B0`.

The same byte blob is written identically to every tile's L1 — the table content does not vary per tile.

```python
bank_table = build_bank_noc_table(harvested_dram_banks, all_worker_cores)
for tile in all_worker_cores:
    tile.l1[TensixL1.MEM_BANK_TO_NOC_SCRATCH :
            TensixL1.MEM_BANK_TO_NOC_SCRATCH + len(bank_table)] = bank_table
```

### Step 6 — Write boot JAL and go_message

As documented in `firmware-upload.md`:
- Write JAL instruction to L1 offset `0x000` (jump to `BRISC_FIRMWARE_BASE = 0x3840`).
- Write `go_msg.signal = RUN_MSG_INIT = 0x40` to L1 offset `0x373`.

---

## 9. Source References

| File | Contents relevant to this spec |
|---|---|
| `blackhole-py/hw.py` | `Dram.BANK_COUNT`, `BANK_TILE_YS`, `BANK_X`, `build_bank_noc_table()`, `BANK_PORT`, `noc_xy()`, `Sysmem.PCIE_NOC_XY`, `TensixL1.MEM_BANK_TO_NOC_SCRATCH`, `TileGrid.ARC`, `worker_cores()` |
| `blackhole-py/device.py` | `P100` and `P150` `BoardConfig` (tensix_x, prefetch, dispatch), `_worker_cores()`, `harvested_dram_banks`, `build_bank_noc_table()` call site |
| `emu-specs/niu.md` | `NOC_ID_LOGICAL` register offset, XY encoding, status counters, firmware boot sequence |
| `emu-specs/dram.md` | DRAM bank interleaving, `InterleavedAddrGenFast`, PCIe address encoding, bank table population detail |
| `emu-specs/firmware-upload.md` | Boot JAL, go_message initialization, `noc_bank_table_init()` call in BRISC/NCRISC init |
| `tt-metal/hw/inc/internal/firmware_common.h` | `noc_bank_table_init()` implementation |
| `tt-metal/hw/inc/internal/tt-1xx/blackhole/dev_mem_map.h` | `MEM_BANK_TO_NOC_SCRATCH`, table size constants, `NUM_DRAM_BANKS`, `NUM_L1_BANKS` |
