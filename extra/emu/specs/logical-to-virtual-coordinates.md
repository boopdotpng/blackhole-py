# Logical-to-Virtual Coordinate Mapping

Blackhole firmware operates with three coordinate systems for Tensix worker tiles. This document specifies the runtime translation mechanism between them, including what the emulator must populate.

## 1. Coordinate Systems

| System | Description | Example (unharvested P150) |
|---|---|---|
| **Physical (NOC0)** | Hardware wire coordinates on the NOC0 mesh. Fixed by chip layout. | x=1..7, 10..16; y=2..11 |
| **Virtual (Translated)** | Post-NIU-translation coordinates. What firmware writes to `NOC_TARG_ADDR_HI`; the NIU hardware converts these to physical before routing. | Same as physical when translation is identity |
| **Logical** | Sequential, harvesting-agnostic index. Logical (0,0) is always the first active worker. Stable across harvesting configurations. | x=0..13; y=0..9 |

The translation chain:
```
Logical → Virtual (software table in LDM) → Physical (NIU hardware translate tables)
```

Firmware kernels receive logical coordinates from launch messages. The firmware converts them to virtual coordinates using per-core LDM lookup tables, then issues NOC transactions with virtual coordinates. The NIU hardware performs the final virtual-to-physical mapping transparently.


## 2. LDM Translation Arrays

Each BRISC and NCRISC core holds two translation arrays in LDM, copied from L1 at boot:

```c
uint8_t worker_logical_col_to_virtual_col[round_up_to_mult_of_4(noc_size_x)];  // [20] for BH
uint8_t worker_logical_row_to_virtual_row[round_up_to_mult_of_4(noc_size_y)];  // [12] for BH
```

Where `noc_size_x = 17` and `noc_size_y = 12` for Blackhole.

### LDM offsets

| Core | `col` array offset | `row` array offset |
|---|---|---|
| BRISC | `0x04E8` (20 bytes) | `0x04FC` (12 bytes) |
| NCRISC | `0x04E0` (20 bytes) | `0x04F4` (12 bytes) |

TRISC0/1/2 do not carry these arrays — they do not issue NOC transactions that require coordinate translation.

### Array contents (unharvested P150)

For an unharvested P150 (14 Tensix columns, 10 rows), the arrays map logical to virtual (= physical on NOC0 with identity translation):

```
worker_logical_col_to_virtual_col:
  [0]=1, [1]=2, [2]=3, [3]=4, [4]=5, [5]=6, [6]=7,   // west band
  [7]=10, [8]=11, [9]=12, [10]=13, [11]=14, [12]=15, [13]=16  // east band
  [14..19] = unused (zero-padded to 20 bytes)

worker_logical_row_to_virtual_row:
  [0]=2, [1]=3, [2]=4, [3]=5, [4]=6, [5]=7, [6]=8, [7]=9, [8]=10, [9]=11
  [10..11] = unused (zero-padded to 12 bytes)
```

When a Tensix column is harvested, the logical indices shift to skip it. For example, if physical column x=3 is harvested (P100A with 12 Tensix columns), the col array would be:

```
  [0]=1, [1]=2, [2]=4, [3]=5, [4]=6, [5]=7,   // west band, x=3 skipped
  [6]=10, [7]=11, [8]=12, [9]=13, [10]=14      // east band (P100A)
  [11..19] = unused
```

### Runtime usage

```c
// firmware_common.h
FORCE_INLINE coord_t get_virtual_coord_from_worker_logical_coord(
        uint8_t worker_x, uint8_t worker_y) {
    return {worker_logical_col_to_virtual_col[worker_x],
            worker_logical_row_to_virtual_row[worker_y]};
}
```

Firmware uses this to convert logical coordinates (from kernel launch messages) into virtual NOC coordinates for use in `NOC_TARG_ADDR_HI`/`NOC_RET_ADDR_HI`.


## 3. L1 Scratch Region

The host writes the translation arrays to a scratch area in each tile's L1 before boot. Firmware copies them into LDM during init.

```c
// dev_mem_map.h
#define MEM_LOGICAL_TO_VIRTUAL_SCRATCH  (MEM_BANK_TO_NOC_SCRATCH + MEM_BANK_TO_NOC_SIZE)
#define MEM_LOGICAL_TO_VIRTUAL_SIZE     ((20 + 12) * sizeof(uint8_t))  // 32 bytes
```

Resolved address: `0x116B0 + 2048 = 0x11EB0`.

### Scratch layout at `L1[0x11EB0]`

```
Offset  Size   Contents
0x00    20 B   worker_logical_col_to_virtual_col[0..19]
0x14    12 B   worker_logical_row_to_virtual_row[0..11]
```


## 4. Boot Initialization: `noc_worker_logical_to_virtual_map_init()`

Called by both BRISC and NCRISC during their init phase (after `noc_bank_table_init()`, before `risc_init()`).

```c
// firmware_common.h
inline void noc_worker_logical_to_virtual_map_init(uint64_t worker_logical_to_virtual_map_addr) {
    // Copy col table from L1 scratch into LDM
    l1_to_local_mem_copy(
        (uint*)worker_logical_col_to_virtual_col,
        (uint tt_l1_ptr*)(worker_logical_to_virtual_map_addr),
        sizeof(worker_logical_col_to_virtual_col) >> 2);  // 20/4 = 5 words

    // Copy row table from L1 scratch into LDM (immediately after col table)
    l1_to_local_mem_copy(
        (uint*)worker_logical_row_to_virtual_row,
        (uint tt_l1_ptr*)(worker_logical_to_virtual_map_addr
                          + sizeof(worker_logical_col_to_virtual_col)),
        sizeof(worker_logical_row_to_virtual_row) >> 2);  // 12/4 = 3 words
}
```

`l1_to_local_mem_copy` copies in 32-bit word units, which is why the array sizes are rounded up to multiples of 4.


## 5. Host-Side Population

The host builds the mapping from the SoC descriptor and multicasts it to all worker tile L1:

```cpp
// risc_firmware_initializer.cpp

// Step 1: Build the mapping
for (size_t x = 0; x < tensix_grid_size.x; x++) {
    worker_logical_col_to_virtual_col.push_back(
        soc_desc.translate_coord_to(
            {tt_xy_pair{x, 0}, CoreType::TENSIX, CoordSystem::LOGICAL},
            CoordSystem::TRANSLATED).x);
}
for (size_t y = 0; y < tensix_grid_size.y; y++) {
    worker_logical_row_to_virtual_row.push_back(
        soc_desc.translate_coord_to(
            {tt_xy_pair{0, y}, CoreType::TENSIX, CoordSystem::LOGICAL},
            CoordSystem::TRANSLATED).y);
}

// Step 2: NOC multicast to all tiles at MEM_LOGICAL_TO_VIRTUAL_SCRATCH
cluster_.noc_multicast_write(worker_logical_col_to_virtual_col.data(), ...);
cluster_.noc_multicast_write(worker_logical_row_to_virtual_row.data(), ...);
```

The same byte blob is written identically to every tile's L1 — the table content does not vary per tile (it describes the grid-wide mapping, not a per-tile view).


## 6. Per-Core Logical Identity

Each core's own logical coordinates are stored in `core_info_msg_t`, part of the `mailboxes_t` structure in L1:

```c
struct core_info_msg_t {
    // ... (NOC addresses, non-worker coords, etc.)
    volatile uint8_t absolute_logical_x;  // this core's logical X
    volatile uint8_t absolute_logical_y;  // this core's logical Y
    // ...
};
```

Firmware reads these after init:
```c
my_logical_x_ = mailboxes->core_info.absolute_logical_x;
my_logical_y_ = mailboxes->core_info.absolute_logical_y;
```

These per-core values are written by the host into each tile's L1 mailbox before boot, and are distinct per tile (unlike the translation arrays which are uniform).


## 7. NIU Hardware Translation Tables

Separate from the software logical-to-virtual mapping, the NIU hardware performs virtual-to-physical coordinate translation on every NOC transaction when `NIU_CFG_0[14]` (`NOC_ID_TRANSLATE_EN`) is set.

### Register layout

6 registers for X translation and 6 for Y, each holding up to 6 entries packed at 5 bits:

| Config index | Register | Entries |
|---|---|---|
| `0x06`–`0x0B` | `NOC_X_ID_TRANSLATE_TABLE_0..5` | X entries 0–31 |
| `0x0C`–`0x11` | `NOC_Y_ID_TRANSLATE_TABLE_0..5` | Y entries 0–31 |

Each 32-bit register holds 6 entries (6 x 5 = 30 bits):
```
bits [4:0]   = table_entry[reg*6 + 0]
bits [9:5]   = table_entry[reg*6 + 1]
bits [14:10] = table_entry[reg*6 + 2]
bits [19:15] = table_entry[reg*6 + 3]
bits [24:20] = table_entry[reg*6 + 4]
bits [29:25] = table_entry[reg*6 + 5]
```

The tables are indexed by **virtual (pre-translation)** coordinate and produce the **physical (post-translation)** coordinate. ARC firmware programs these during `ProgramNocTranslation()` before Tensix cores boot.

NOC1 translation tables are derived by mirroring NOC0: `noc1_x[i] = NOC_X_SIZE - noc0_x[i] - 1`.

### Additional translation registers

| Config index | Register | Purpose |
|---|---|---|
| `0x12` | `NOC_ID_LOGICAL` | This tile's logical coords: `(y << 6) \| x` |
| `0x14` | `NOC_ID_TRANSLATE_COL_MASK` | Which columns bypass translation |
| `0x15` | `NOC_ID_TRANSLATE_ROW_MASK` | Which rows bypass translation |

`NOC_ID_LOGICAL` is what firmware reads in `noc_init()` to discover "who am I." The emulator must pre-populate this (see `niu.md` §9).


## 8. Emulator Setup Requirements

Before releasing any RISC-V core from reset, the emulator must:

### Step 1 — Write translation arrays to L1

For every worker tile, write the logical-to-virtual mapping at `L1[0x11EB0]`:

```python
# Build col table: logical index → virtual NOC X
col_table = []
for logical_x in range(len(tensix_columns)):
    col_table.append(tensix_columns[logical_x])  # e.g., [1,2,3,4,5,6,7,10,11,12,13,14,15,16]
col_table += [0] * (20 - len(col_table))  # pad to 20 bytes

# Build row table: logical index → virtual NOC Y
row_table = []
for logical_y in range(10):  # 10 Tensix rows
    row_table.append(2 + logical_y)  # Y=2..11
row_table += [0] * (12 - len(row_table))  # pad to 12 bytes

# Write to every tile's L1
for tile in all_worker_tiles:
    tile.l1[0x11EB0 : 0x11EB0 + 20] = bytes(col_table)
    tile.l1[0x11EC4 : 0x11EC4 + 12] = bytes(row_table)
```

### Step 2 — Write per-core logical identity

For every worker tile at grid position `(virtual_x, virtual_y)`, compute its logical coordinates and write them to `core_info_msg_t.absolute_logical_x/y` in that tile's L1 mailbox.

```python
for logical_x, virtual_x in enumerate(tensix_columns):
    for logical_y in range(10):
        virtual_y = 2 + logical_y
        tile = tiles[(virtual_x, virtual_y)]
        core_info_offset = ...  # offset of core_info_msg_t within mailboxes_t
        tile.l1[core_info_offset + offsetof_absolute_logical_x] = logical_x
        tile.l1[core_info_offset + offsetof_absolute_logical_y] = logical_y
```

### Step 3 — Pre-populate `NOC_ID_LOGICAL`

Already documented in `niu.md` §9 and `device-grid.md` §8 step 4. Write `(y << 6) | x` to both NIU instances for each tile.

### NIU translate tables

For a basic emulator that does not model the NIU hardware translation layer (virtual == physical), the `NOC_X/Y_ID_TRANSLATE_TABLE` registers can be left as identity mappings or zeros. The emulator routes NOC transactions based on the virtual coordinates directly, bypassing the hardware translation step. If the emulator does model translation, program the same tables that ARC would program (see `tt-zephyr-platforms/lib/tenstorrent/bh_arc/noc_init.c`).


## 9. Source References

| File | Content |
|---|---|
| `tt-metal/tt_metal/hw/inc/internal/firmware_common.h` | `noc_worker_logical_to_virtual_map_init()`, `get_virtual_coord_from_worker_logical_coord()` |
| `tt-metal/tt_metal/hw/firmware/src/tt-1xx/brisc.cc` | Call site in BRISC `main()` |
| `tt-metal/tt_metal/hw/firmware/src/tt-1xx/ncrisc.cc` | Call site in NCRISC `main()` |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/dev_mem_map.h` | `MEM_LOGICAL_TO_VIRTUAL_SCRATCH`, `MEM_LOGICAL_TO_VIRTUAL_SIZE` |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/core_config.h` | `noc_size_x = 17`, `noc_size_y = 12` |
| `tt-metal/tt_metal/hw/inc/hostdev/dev_msgs.h` | `core_info_msg_t` with `absolute_logical_x/y` |
| `tt-metal/tt_metal/impl/device/firmware/risc_firmware_initializer.cpp` | Host-side mapping generation and L1 upload |
| `tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_parameters.h` | NIU translate table register defines |
| `tt-zephyr-platforms/lib/tenstorrent/bh_arc/noc_init.c` | ARC firmware: NIU translation table computation and programming |
| `emu-specs/ldm-layouts.md` | LDM offsets for col/row arrays |
| `emu-specs/niu.md` | `NOC_ID_LOGICAL` register, NIU config register map |
| `emu-specs/device-grid.md` | Grid topology, coordinate assignments |
