# address-space

**Source:** [`address-space.md`](../specs/address-space.md) · **Emulator:** `blackhole-py/extra/emu/router.py`

## Router basics

### `ADDR.ROUTER.FIRST_MATCH_WINS`
_router.py::Router._find_

> The address router iterates registered ranges in insertion order; the first matching range wins. This is the "first-match" routing policy.

### `ADDR.ROUTER.DEFAULT_FALLBACK`
_router.py::Router._find_

> Addresses that do not match any registered range fall through to the default handler (router.default).

### `ADDR.L1.RANGE`
§2 L1 Shared Tile Memory

> L1 shared tile memory spans 0x00000000–0x0017FFFF (1.5 MiB).

### `ADDR.L1.SHARED_ALL_CORES`
§2 L1 / All 5 cores on the tile share a single L1 SRAM

> All 5 cores on the tile share a single L1 SRAM. Reads and writes from any core go to the same physical memory.

### `ADDR.LDM.FAST_PATH_BASE`
§3 Core-Private SRAM (LDM) — Fast Path

> LDM fast path starts at 0xFFB00000. BRISC/NCRISC have 8 KiB (end 0xFFB01FFF); TRISC0/1/2 have 4 KiB (end 0xFFB00FFF).

### `ADDR.LDM.FAST_PATH_PER_CORE`
§3 ¶hardware routes each core's accesses to its own physical SRAM bank

> BRISC writing to 0xFFB00100 and TRISC0 writing to 0xFFB00100 write to completely different physical memory. Each core sees only its own LDM at the fast-path address.

### `ADDR.LDM.SLOW_PATH_BRISC`
§4 Core-Private SRAM — Slow / Cross-Core Path

> BRISC slow-path address: 0xFFB14000–0xFFB15FFF.

### `ADDR.LDM.SLOW_PATH_NCRISC`
§4 / NCRISC

> NCRISC slow-path address: 0xFFB16000–0xFFB17FFF.

### `ADDR.LDM.SLOW_PATH_TRISC0`
§4 / TRISC0

> TRISC0 slow-path address: 0xFFB18000–0xFFB18FFF.

### `ADDR.LDM.SLOW_PATH_TRISC1`
§4 / TRISC1

> TRISC1 slow-path address: 0xFFB1A000–0xFFB1AFFF.

### `ADDR.LDM.SLOW_PATH_TRISC2`
§4 / TRISC2

> TRISC2 slow-path address: 0xFFB1C000–0xFFB1CFFF.

### `ADDR.NIU.NOC0_BASE`
§6 NIU Registers / NoC0

> NOC0 NIU registers are at 0xFFB20000, 64 KiB.

### `ADDR.NIU.NOC1_BASE`
§6 NIU Registers / NoC1

> NOC1 NIU registers are at 0xFFB30000, 64 KiB.

### `ADDR.DEBUG.SOFT_RESET_ADDR`
_§5b Debug/Control Registers / SOFT_RESET_0_

> SOFT_RESET_0 is at 0xFFB121B0.

### `ADDR.DEBUG.WALL_CLOCK_ADDR`
_§5b Debug/Control Registers / WALL_CLOCK_

> WALL_CLOCK_L is at 0xFFB121F0; WALL_CLOCK_H is at 0xFFB121F8.

### `ADDR.INSTRN_BUF.T0_BASE`
§11 Tensix Instruction Buffer FIFOs

> T0 instruction buffer FIFO is at 0xFFE40000 (64 KiB).

### `ADDR.INSTRN_BUF.NCRISC_NO_PUSH`
§11 Tensix Instruction Buffer FIFOs / Emulator note

> NCRISC has no Tensix instruction push capability. Any store from NCRISC to the instruction buffer address range should be flagged as an error.

### `ADDR.TENSIX_CFG.BASE`
§14 Tensix Backend Config Registers

> Tensix backend config registers are at 0xFFEF0000, 64 KiB.

### `ADDR.MAILBOX.BASE`
§15 L1 Mailbox Layout

> The mailboxes_t structure begins at L1 offset 0x60. go_messages[0] is at L1 offset 0x370; signal byte is at 0x373.

### `ADDR.MAILBOX.SUBORDINATE_SYNC`
_§15 L1 Mailbox Layout / subordinate_sync_

> subordinate_sync is at L1 offset 0x68 (4 bytes: byte 0 = NCRISC, 1 = TRISC0, 2 = TRISC1, 3 = TRISC2).
