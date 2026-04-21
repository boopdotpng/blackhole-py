# dram

**Source:** [`dram.md`](../specs/dram.md) · **Emulator:** `blackhole-py/extra/emu/device.py`

## Bank geometry

### `DRAM.GEO.BANK_COUNT`
§2.1 Physical Geometry (P100A)

> Blackhole P100A has 7 active DRAM banks (1 of 8 physical banks harvested).

### `DRAM.GEO.PORTS_PER_BANK`
§2.1 Physical Geometry / 3 ports

> Each bank is fronted by 3 DRAM tiles — three NOC ports aliasing the same DDR controller.

### `DRAM.GEO.COLUMNS`
§2.1 Physical Geometry / layout

> P100A: 4 banks on west column x=17, 3 banks on east column x=18.

### `DRAM.PORT.ALIAS_SAME_MEM`
§4.1 DRAM Controller Nodes / Backing

> All 3 port tiles per bank alias the same backing memory; no data striping across ports.

### `DRAM.INTERLEAVE.BANK_INDEX`
§2.4 Bank Interleaving

> bank_index = page_id % num_banks; bank_offset_index = page_id // num_banks.

### `DRAM.INTERLEAVE.ADDR_FORMULA`
§2.4 Bank Interleaving

> addr = base_addr + (page_id // num_banks) * tile_bytes within the selected bank.

### `DRAM.INTERLEAVE.WRITE_READ_ROUNDTRIP`
§2.4 Bank Interleaving

> write_interleaved then read_interleaved returns the same bytes.

### `DRAM.HARVEST.SINGLE_BANK`
§2.2 Harvesting

> P100A has exactly 1 of 8 physical DRAM banks disabled. Remaining 7 banks are assigned software IDs 0–6 contiguously.

### `DRAM.HARVEST.MIRROR_REORDER`
§2.2 Harvesting / mirror

> When bank h is harvested, its mirror (h+4 or h-4) is pushed to the last slot of its column so the 4+3 split is maintained.

### `DRAM.HARVEST.BOUNDARY`
§2.2 Harvesting

> With bank 0 harvested, _compute_bank_xy returns 7 entries; bank 0 is absent, banks 1..7 are mapped.

### `DRAM.BANK_TABLE.ENCODING`
§4.2 Bank Table Population

> Each uint16 NOC XY entry is packed as (y<<6)|x.

### `DRAM.BANK_TABLE.DRAM_NOC_ORDER`
_§6 Bank-to-NOC Table / dram_bank_to_noc_xy layout_

> dram_bank_to_noc_xy is laid out as [noc][bank]: NOC0 entries first, then NOC1.

### `DRAM.BANK_TABLE.OFFSETS_ZERO`
_§6 bank_to_dram_offset_

> bank_to_dram_offset and bank_to_l1_offset arrays are initialized to zero.

### `DRAM.NOC.WRITE_ROUTED`
§4.3 NIU Routing Extension

> A NOC write targeting a DRAM bank's NOC coordinate writes to that bank's backing memory at the specified address.

### `DRAM.NOC.READ_ROUTED`
§4.3 NIU Routing Extension

> A NOC read targeting a DRAM bank's NOC coordinate reads from that bank's backing memory at the specified address.
