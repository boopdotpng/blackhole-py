# LDM (Local Data Memory) Per-Core Layouts

## Overview

Each Tensix tile on Blackhole contains five RISC-V cores: BRISC (data-movement manager), NCRISC (NOC/DRAM data-mover), and three Tensix co-processor cores TRISC0 (unpack), TRISC1 (math), and TRISC2 (pack). Each core has a private SRAM region called Local Data Memory (LDM) that holds per-core state: NOC counters, bank lookup tables, circular-buffer interface descriptors, coordinate variables, and the stack.

All five cores address their LDM at the same virtual base address `0xFFB00000`. The hardware memory router silently redirects each core's accesses to its own physical bank — there is no aliasing between cores. BRISC and NCRISC each have 8 KiB (`0xFFB00000`–`0xFFB01FFF`); TRISC0, TRISC1, and TRISC2 each have 4 KiB (`0xFFB00000`–`0xFFB00FFF`).

The layouts below are verified against Blackhole-compiled ELFs. Offsets are from the `0xFFB00000` base. Sizes are in bytes. Fields at non-obvious offsets are a consequence of the C/C++ struct layout rules applied by the RISC-V `rv32i` toolchain (4-byte natural alignment, no padding inserted by the linker script beyond what the compiler produces).

---

## BRISC LDM (8 KiB: `0xFFB00000`–`0xFFB01FFF`)

| Offset | Symbol | Size | Description |
|--------|--------|------|-------------|
| `0x0000` | `subordinate_sync` | 4 | Pointer to `mailboxes_t.subordinate_sync` in L1 |
| `0x0004` | `my_y[NUM_NOCS]` | 2 | NOC Y coordinate; index 0 = NOC0, index 1 = NOC1 |
| `0x0008` | `my_x[NUM_NOCS]` | 2 | NOC X coordinate |
| `0x000A` | `prev_noc_mode` | 1 | Previous NOC mode (private, updated by NOC mode switch helpers) |
| `0x000B` | `my_relative_y_` | 1 | Relative Y within sub-device |
| `0x000C` | `my_relative_x_` | 1 | Relative X within sub-device |
| `0x000D` | `noc_mode` | 1 | Current NOC mode (private) |
| `0x000E` | (padding) | 2 | Alignment gap |
| `0x0010` | `crta_l1_base` | 4 | Common RTA L1 base address |
| `0x0014` | `rta_l1_base` | 4 | Per-core RTA L1 base address |
| `0x0018` | `noc_posted_writes_num_issued[2]` | 8 | Posted writes issued, per NOC |
| `0x0020` | `noc_nonposted_atomics_acked[2]` | 8 | Nonposted atomics acknowledged, per NOC |
| `0x0028` | `noc_nonposted_writes_acked[2]` | 8 | Nonposted writes acknowledged, per NOC |
| `0x0030` | `noc_nonposted_writes_num_issued[2]` | 8 | Nonposted writes issued, per NOC |
| `0x0038` | `noc_reads_num_issued[2]` | 8 | Reads issued, per NOC |
| `0x0040` | `my_logical_y_` | 1 | Logical Y coordinate |
| `0x0041` | `my_logical_x_` | 1 | Logical X coordinate |
| `0x0042` | `noc_index` | 1 | Active NOC index for this core |
| `0x0043` | (padding) | 1 | Alignment gap |
| `0x0044` | `active_noc_instance` | 4 | Active NOC instance (private) |
| `0x0048` | `dram_bank_to_noc_xy[2][8]` | 32 | DRAM bank → NOC XY table (2 NOCs × 8 banks × `uint16_t`) |
| `0x0068` | `l1_bank_to_noc_xy[2][140]` | 560 | L1 bank → NOC XY table (2 NOCs × 140 banks × `uint16_t`) |
| `0x0298` | `bank_to_dram_offset[8]` | 32 | Per-DRAM-bank byte offset (`uint32_t` × 8) |
| `0x02B8` | `bank_to_l1_offset[140]` | 560 | Per-L1-bank byte offset (`uint32_t` × 140) |
| `0x04E8` | `worker_logical_col_to_virtual_col[20]` | 20 | Logical-to-virtual column translation (`uint8_t` × 20) |
| `0x04FC` | `worker_logical_row_to_virtual_row[12]` | 12 | Logical-to-virtual row translation (`uint8_t` × 12) |
| `0x0508` | `instrn_buf[3]` | 12 | Tensix instruction buffer pointers (private, `uint32_t` × 3) |
| `0x0514` | `sem_l1_base[3]` | 12 | Per-core-type semaphore L1 base (`uint32_t` × 3) |
| `0x0520` | `cb_interface[64]` | 2048 | CB interface array (64 × 32 bytes = `0x800`) |
| `0x0D20` | (BSS end) | — | End of initialized/zeroed data segment |
| `0x07F0` | `__global_pointer$` | — | RISC-V GP register value (set by CRT) |
| `0x2000` | `__stack_top` | — | SP initialized to `0xFFB01FF0` |

---

## NCRISC LDM (8 KiB: `0xFFB00000`–`0xFFB01FFF`)

| Offset | Symbol | Size | Description |
|--------|--------|------|-------------|
| `0x0000` | `ncrisc_run` | 4 | Pointer to `subordinate_sync` dm1 byte in L1 mailbox |
| `0x0004` | `noc_reads_num_issued[2]` | 8 | Reads issued, per NOC |
| `0x000C` | `noc_nonposted_writes_num_issued[2]` | 8 | Nonposted writes issued, per NOC |
| `0x0014` | `noc_nonposted_writes_acked[2]` | 8 | Nonposted writes acknowledged, per NOC |
| `0x001C` | `noc_nonposted_atomics_acked[2]` | 8 | Nonposted atomics acknowledged, per NOC |
| `0x0024` | `noc_posted_writes_num_issued[2]` | 8 | Posted writes issued, per NOC |
| `0x002C` | `my_y[2]` | 2 | NOC Y coordinate |
| `0x0030` | `my_x[2]` | 2 | NOC X coordinate |
| `0x0032` | `my_relative_y_` | 1 | Relative Y within sub-device |
| `0x0033` | `my_relative_x_` | 1 | Relative X within sub-device |
| `0x0034` | `crta_l1_base` | 4 | Common RTA L1 base address |
| `0x0038` | `rta_l1_base` | 4 | Per-core RTA L1 base address |
| `0x003C` | `my_logical_y_` | 1 | Logical Y coordinate |
| `0x003D` | `my_logical_x_` | 1 | Logical X coordinate |
| `0x003E` | (padding) | 2 | Alignment gap |
| `0x0040` | `dram_bank_to_noc_xy[2][8]` | 32 | DRAM bank → NOC XY table (2 NOCs × 8 banks × `uint16_t`) |
| `0x0060` | `l1_bank_to_noc_xy[2][140]` | 560 | L1 bank → NOC XY table (2 NOCs × 140 banks × `uint16_t`) |
| `0x0290` | `bank_to_dram_offset[8]` | 32 | Per-DRAM-bank byte offset (`uint32_t` × 8) |
| `0x02B0` | `bank_to_l1_offset[140]` | 560 | Per-L1-bank byte offset (`uint32_t` × 140) |
| `0x04E0` | `worker_logical_col_to_virtual_col[20]` | 20 | Logical-to-virtual column translation (`uint8_t` × 20) |
| `0x04F4` | `worker_logical_row_to_virtual_row[12]` | 12 | Logical-to-virtual row translation (`uint8_t` × 12) |
| `0x0500` | `sem_l1_base[3]` | 12 | Per-core-type semaphore L1 base (`uint32_t` × 3) |
| `0x050C` | `cb_interface[64]` | 2048 | CB interface array (64 × 32 bytes) |
| `0x0D0C` | (BSS end) | — | End of initialized/zeroed data segment |
| `0x07F0` | `__global_pointer$` | — | RISC-V GP register value (set by CRT) |
| `0x2000` | `__stack_top` | — | SP initialized to `0xFFB01FF0` |

---

## TRISC0 / TRISC2 LDM (Unpack / Pack — 4 KiB: `0xFFB00000`–`0xFFB00FFF`)

TRISC0 (unpack) and TRISC2 (pack) share an identical LDM layout. Both interact with circular buffers, so both carry a full `cb_interface[64]` array.

| Offset | Symbol | Size | Description |
|--------|--------|------|-------------|
| `0x0000` | `ckernel::dest_offset_id` | 4 | Current Dest register half (0 or 1) |
| `0x0004` | `ckernel::op_info_offset` | 4 | Op info offset |
| `0x0008` | `cb_l1_base` | 4 | Pointer to CB config in L1 |
| `0x000C` | `my_relative_y_` | 1 | Relative Y within sub-device |
| `0x000D` | `my_relative_x_` | 1 | Relative X within sub-device |
| `0x000E` | (padding) | 2 | Alignment gap |
| `0x0010` | `crta_l1_base` | 4 | Common RTA L1 base |
| `0x0014` | `rta_l1_base` | 4 | Per-core RTA L1 base |
| `0x0018` | `my_logical_y_` | 1 | Logical Y coordinate |
| `0x0019` | `my_logical_x_` | 1 | Logical X coordinate |
| `0x001A` | (padding) | 2 | Alignment gap |
| `0x001C` | `ckernel::cfg_state_id` | 4 | Active Tensix config state bank (0 or 1) |
| `0x0020` | `cb_interface[64]` | 2048 | CB interface array (64 × 32 bytes) |
| `0x0820` | (BSS end) | — | End of initialized/zeroed data segment |
| `0x07F0` | `__global_pointer$` | — | RISC-V GP register value (set by CRT) |
| `0x1000` | `__stack_top` | — | SP initialized to `0xFFB00FF0` |

---

## TRISC1 LDM (Math — 4 KiB: `0xFFB00000`–`0xFFB00FFF`)

TRISC1 (math) has no CB interface; the math core does not push or pop circular buffer entries directly.

| Offset | Symbol | Size | Description |
|--------|--------|------|-------------|
| `0x0000` | `ckernel::dest_offset_id` | 4 | Current Dest register half (0 or 1) |
| `0x0004` | `ckernel::op_info_offset` | 4 | Op info offset |
| `0x0008` | `my_relative_y_` | 1 | Relative Y within sub-device |
| `0x0009` | `my_relative_x_` | 1 | Relative X within sub-device |
| `0x000A` | (padding) | 2 | Alignment gap |
| `0x000C` | `crta_l1_base` | 4 | Common RTA L1 base |
| `0x0010` | `rta_l1_base` | 4 | Per-core RTA L1 base |
| `0x0014` | `my_logical_y_` | 1 | Logical Y coordinate |
| `0x0015` | `my_logical_x_` | 1 | Logical X coordinate |
| `0x0016` | (padding) | 2 | Alignment gap |
| `0x0018` | `ckernel::cfg_state_id` | 4 | Active Tensix config state bank (0 or 1) |
| `0x001C` | (BSS end) | — | End of initialized/zeroed data segment |
| `0x07F0` | `__global_pointer$` | — | RISC-V GP register value (set by CRT) |
| `0x1000` | `__stack_top` | — | SP initialized to `0xFFB00FF0` |

---

## NOC Counter Arrays

Each of the five per-NOC counter variables (`noc_reads_num_issued`, `noc_nonposted_writes_num_issued`, `noc_nonposted_writes_acked`, `noc_nonposted_atomics_acked`, `noc_posted_writes_num_issued`) is a `uint32_t[NUM_NOCS]` array with `NUM_NOCS = 2`. Total size is 8 bytes. Index 0 corresponds to NOC0 and index 1 to NOC1.

At boot, `noc_local_state_init()` reads the hardware NOC status-counter registers for each NOC and stores the values into these LDM arrays. Subsequent NOC operations increment the LDM copies; fence and barrier routines poll the hardware registers and compare against the stored values to determine when outstanding transactions are complete.

Emulator note: the emulator must implement these arrays as per-core LDM state, not as shared global state, because each core tracks its own outstanding NOC transactions independently.

---

## CB Interface Array (`cb_interface`)

The `cb_interface[64]` array stores the local (fast-path) state for up to 64 circular buffers. Each entry is a `LocalCBInterface` struct of exactly 32 bytes comprising 8 `uint32_t` fields:

| Field offset | Field | Description |
|-------------|-------|-------------|
| `+0x00` | `fifo_rd_ptr` | Read pointer (in units of 16 bytes) |
| `+0x04` | `fifo_wr_ptr` | Write pointer (in units of 16 bytes) |
| `+0x08` | `fifo_limit` | End-of-FIFO address (16-byte units) |
| `+0x0C` | `fifo_size` | FIFO size in 16-byte units |
| `+0x10` | `fifo_num_pages` | Number of pages allocated |
| `+0x14` | `fifo_page_size` | Page size in 16-byte units |
| `+0x18` | `tiles_acked` | Running count of tiles consumed by this core |
| `+0x1C` | `tiles_received` | Running count of tiles produced to this core |

Blackhole supports 64 CBs (`NUM_CIRCULAR_BUFFERS = 64`), double the 32-CB limit on Wormhole. The total array size is `64 × 32 = 2048` bytes (`0x800`). TRISC1 (math) does not carry this array because the math core reads operands from the Dest register file rather than CB L1 addresses.

---

## Bank Lookup Tables

`noc_bank_table_init()` runs during firmware boot on BRISC and NCRISC. It copies the bank lookup tables from a scratch region in L1 (`MEM_BANK_TO_NOC_SCRATCH = 0x0116B0`) into the corresponding LDM arrays. The L1 scratch region is pre-populated by the host before the cores are released from reset.

### Table dimensions (Blackhole)

| Constant | Value | Description |
|----------|-------|-------------|
| `NUM_DRAM_BANKS` | 8 | Physical DRAM channels |
| `NUM_L1_BANKS` | 140 | Addressable L1 worker tiles |
| `NUM_NOCS` | 2 | NOC0 and NOC1 |

### `dram_bank_to_noc_xy` and `l1_bank_to_noc_xy`

Type: `uint16_t[NUM_NOCS][NUM_BANKS]`. Each entry encodes a NOC coordinate as a packed 16-bit value:

```
entry = (noc_y << 6) | noc_x
```

Both `noc_x` and `noc_y` are 6-bit fields. The shift constant `6` matches the Blackhole NOC coordinate width. To decode: `x = entry & 0x3F`, `y = (entry >> 6) & 0x3F`.

### `bank_to_dram_offset` and `bank_to_l1_offset`

Type: `uint32_t[NUM_BANKS]`. Each entry is the byte offset added to the NOC base address for that bank to produce the canonical address of bank slot 0. Interleaved allocation uses these offsets plus a stride computed at runtime.

---

## Emulator Implementation Notes

The emulator must maintain five separate physical LDM banks, all mapped to the same virtual address `0xFFB00000` from the perspective of each core's address translation. Memory accesses by a core to `0xFFB00000`–`0xFFB01FFF` (BRISC/NCRISC) or `0xFFB00000`–`0xFFB00FFF` (TRISC0/1/2) must be dispatched to that core's private bank, never to any other core's bank.

Before releasing any core from reset, the emulator must pre-populate the L1 scratch region at `MEM_BANK_TO_NOC_SCRATCH` (`0x0116B0`) with the correct bank tables for the simulated topology. The firmware's `noc_bank_table_init()` routine will copy these into LDM; the emulator does not inject the tables directly into LDM.

The `__global_pointer$` symbol at `0x07F0` (relative to LDM base) is the value written to the `gp` register by the CRT startup code. The emulator must initialize `gp` to `0xFFB007F0` for all cores at reset so that GP-relative data accesses resolve correctly. Stack pointers initialize to `0xFFB01FF0` (BRISC/NCRISC) or `0xFFB00FF0` (TRISC0/1/2); the low 4 bytes are reserved by the RISC-V ABI red zone.

---

## Source References

| Symbol / file | Location in tt-metal / tt-llk-blackhole |
|---------------|----------------------------------------|
| `noc_local_state_init()` | `tt_metal/hw/inc/noc/noc_parameters.h`, `noc_overlay.h` |
| `noc_bank_table_init()` | `tt_metal/hw/inc/dataflow_api.h` |
| `MEM_BANK_TO_NOC_SCRATCH` | `tt_metal/hw/inc/blackhole/mem_layout.h` |
| `LocalCBInterface` struct | `tt_metal/hw/inc/circular_buffer.h` |
| `NUM_CIRCULAR_BUFFERS` | `tt_metal/hw/inc/blackhole/chlkc_params.h` |
| `NUM_DRAM_BANKS`, `NUM_L1_BANKS` | `tt_metal/hw/inc/blackhole/noc_parameters.h` |
| `ckernel::dest_offset_id`, `cfg_state_id` | `tt_llk_blackhole/llk_lib/llk_defs.h` |
| BRISC linker script | `tt_metal/hw/toolchain/brisc.ld` |
| NCRISC linker script | `tt_metal/hw/toolchain/ncrisc.ld` |
| TRISC linker scripts | `tt_metal/hw/toolchain/trisc0.ld`, `trisc1.ld`, `trisc2.ld` |
