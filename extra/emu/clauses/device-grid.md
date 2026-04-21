# device-grid

**Source:** [`device-grid.md`](../specs/device-grid.md) · **Emulator:** `blackhole-py/extra/emu/device.py`

## Tensix layout

### `GRID.P100A.X_COLUMNS`
§2 P100A Tensix Tile Coordinates / X columns

> P100A Tensix X columns: west band 1-7, east band 10-14. Total 12 columns.

### `GRID.P100A.Y_ROWS`
§2 P100A Tensix Tile Coordinates / Y rows

> Tensix Y rows are 2 through 11 inclusive (10 rows).

### `GRID.P100A.CORE_COUNT`
§2 P100A / Core count

> 12 columns × 10 rows = 120 Tensix cores on P100A.

### `GRID.DRAM.WEST_COLUMN`
§4 DRAM Bank Tile Coordinates / Translated coordinates

> P100A: 4 DRAM banks on translated column x=17 (west).

### `GRID.DRAM.EAST_COLUMN`
§4 DRAM Bank Tile Coordinates / Translated coordinates

> P100A: 3 DRAM banks on translated column x=18 (east).

### `GRID.DRAM.BASE_Y`
§4 DRAM Bank Tile Coordinates / Port Y range

> P100A DRAM banks start at base Y=12. Bank k's base_y = 12 + k*3. Each bank occupies 3 consecutive Y values.

### `GRID.DRAM.BANK_PORT_SELECTION`
_§4 Port selection per NOC / BANK_PORT_

> BANK_PORT[bank][noc] selects the port offset (0, 1, or 2) from base_y. E.g., bank 0 NOC0 uses offset +2 (y0+2=14), NOC1 uses offset +1 (y0+1=13).

### `GRID.PCIE.COORDINATE`
§5 PCIe Endpoint

> PCIe endpoint is at NOC coordinate (x=19, y=24). Packed: (24<<6)|19 = 0x613.

## Tile registration

### `GRID.TILE.L1_SHARED`
§8 Emulator Setup / Step 1

> All 5 RISC-V cores on a tile share the same L1 Memory object.

### `GRID.TILE.NOC_BOTH_NETWORKS`
§8 Emulator Setup / Step 1

> Each tile is registered in both NOC0 and NOC1 networks at its (x,y) coordinate.

### `GRID.TILE.NIU_PREPOPULATED`
§8 Emulator Setup / Step 4

> Before firmware boots, NOC_ID_LOGICAL (offset 0x148 from NIU base) and NOC_NODE_ID (offset 0x44) must be pre-populated with (y<<6)|x for each tile.

### `GRID.HARVEST.DRAM_SINGLE`
§7 Harvesting / DRAM bank harvesting

> P100A has exactly 1 of 8 physical DRAM banks disabled.

### `GRID.HARVEST.TENSIX_COLUMN`
§7 Harvesting / Tensix column harvesting

> If a Tensix column is harvested, the corresponding X value must not appear in tensix_x and those 10 cores must not be registered.

