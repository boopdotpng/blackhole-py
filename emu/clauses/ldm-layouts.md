# ldm-layouts

**Source:** [`ldm-layouts.md`](../specs/ldm-layouts.md) · **Emulator:** `blackhole-py/emu/core.py`

## LDM isolation

### `LDM.ISOLATION.PER_CORE`
§Overview ¶1

> The hardware memory router silently redirects each core's accesses to its own physical bank — there is no aliasing between cores.

### `LDM.SIZE.BRISC_8K`
§Overview / All five cores address their LDM

> BRISC has 8 KiB LDM (0xFFB00000–0xFFB01FFF).

### `LDM.SIZE.NCRISC_8K`
§NCRISC LDM (8 KiB)

> NCRISC has 8 KiB LDM (0xFFB00000–0xFFB01FFF).

### `LDM.SIZE.TRISC0_4K`
§TRISC0/TRISC2 LDM (4 KiB)

> TRISC0 has 4 KiB LDM (0xFFB00000–0xFFB00FFF).

### `LDM.SIZE.TRISC1_4K`
§TRISC1 LDM (4 KiB)

> TRISC1 has 4 KiB LDM (0xFFB00000–0xFFB00FFF).

### `LDM.SIZE.TRISC2_4K`
§TRISC0/TRISC2 LDM (4 KiB)

> TRISC2 has 4 KiB LDM (0xFFB00000–0xFFB00FFF).

### `LDM.L1.SHARED_ALL_CORES`
§Overview ¶1

> All five cores share a single L1 SRAM. A write from one core is immediately visible to any other core reading the same L1 address.

### `LDM.SLOW_PATH.BRISC_BASE`
§Address Space §4 Core-Private SRAM — Slow/Cross-Core Path

> BRISC's LDM is accessible at 0xFFB14000–0xFFB15FFF (slow path) from any core.

### `LDM.SLOW_PATH.NCRISC_BASE`
§Address Space §4 / NCRISC

> NCRISC's LDM is accessible at 0xFFB16000–0xFFB17FFF (slow path).

### `LDM.SLOW_PATH.TRISC0_BASE`
§Address Space §4 / TRISC0

> TRISC0's LDM is accessible at 0xFFB18000–0xFFB18FFF (slow path).

### `LDM.SLOW_PATH.TRISC1_BASE`
§Address Space §4 / TRISC1

> TRISC1's LDM is accessible at 0xFFB1A000–0xFFB1AFFF (slow path).

### `LDM.SLOW_PATH.TRISC2_BASE`
§Address Space §4 / TRISC2

> TRISC2's LDM is accessible at 0xFFB1C000–0xFFB1CFFF (slow path).

### `LDM.SLOW_PATH.WRITE_VISIBLE_FAST`
§Emulator Implementation Notes §Slow path

> A write through the slow-path address (e.g. 0xFFB14000+offset for BRISC) and a read through the fast-path address (0xFFB00000+offset for BRISC) are the same physical memory — writes are immediately visible cross-path.

### `LDM.SLOW_PATH.TRISC_PADDING`
§Address Space §4 ¶stride

> Stride between slow-path slots is 0x2000 (8 KiB) for uniform address decoding. TRISC cores only use the first 4 KiB; the upper 4 KiB is unmapped padding.

### `LDM.NOC_COUNTERS.PER_CORE_NOT_GLOBAL`
§NOC Counter Arrays ¶Emulator note

> NOC counter arrays (noc_reads_num_issued, etc.) must be per-core LDM state, not shared global state. Each core tracks its own outstanding NOC transactions independently.
