# instruction-cache

**Source:** [`instruction-cache.md`](../specs/instruction-cache.md) · **Emulator:** `blackhole-py/emu/core.py`

## Capacities

### `ICACHE.CAPACITY.BRISC_2K`
§Capacity table / BRISC

> BRISC I-cache: 2 KiB (holds up to 512 instructions).

### `ICACHE.CAPACITY.TRISC0_2K`
§Capacity table / TRISC0

> TRISC0 I-cache: 2 KiB.

### `ICACHE.CAPACITY.TRISC1_512B`
§Capacity table / TRISC1

> TRISC1 I-cache: 512 bytes (holds up to 128 instructions).

### `ICACHE.CAPACITY.TRISC2_2K`
§Capacity table / TRISC2

> TRISC2 I-cache: 2 KiB.

### `ICACHE.CAPACITY.NCRISC_512B`
§Capacity table / NCRISC

> NCRISC I-cache: 512 bytes.

### `ICACHE.BEHAVIOR.NO_ZIFENCEI`
§Behavior ¶4

> No Zifencei support — fence.i is treated as nop (non-contractual). Software cannot flush the I-cache with a fence.

### `ICACHE.BEHAVIOR.TRANSPARENT_IN_EMULATOR`
§Emulator Implications ¶1

> The I-cache does not need to be modeled. It is functionally transparent. The emulator fetches instructions directly from the L1 backing store.

### `ICACHE.BEHAVIOR.SELF_MODIFYING_CODE`
§Emulator Implications ¶last

> The only scenario where the I-cache would matter is self-modifying code (write new instructions to L1, then jump to them). Since the emulator fetches directly from L1, this works naturally.

### `ICACHE.INVALIDATE.REGISTER_ADDR`
§Invalidation

> Invalidation is done by writing a per-core bitmask to RISCV_IC_INVALIDATE_InvalidateAll at TENSIX_CFG_BASE + 0x2E4 (config register index 185). Writing 0x1F invalidates all 5 cores.

### `ICACHE.INVALIDATE.NOOP_IN_EMULATOR`
_§Emulator Implications / Accept writes to RISCV_IC_INVALIDATE_

> The emulator should accept writes to RISCV_IC_INVALIDATE_InvalidateAll and treat them as a no-op since it fetches instructions directly from L1.

### `ICACHE.INVALIDATE.NCRISC_CANNOT`
§Invalidation ¶Constraints

> The invalidation register is in Tensix backend config space — NCRISC cannot access it, so NCRISC cannot invalidate its own or anyone else's I-cache.

### `ICACHE.INVALIDATE.PIPELINE_NOT_CLEARED`
§Invalidation ¶Constraints

> Invalidation clears the cache but not the pipeline — up to ~20 already-fetched instructions may still execute from stale contents.

### `ICACHE.PREFETCH.ACCEPT_CONFIG_WRITES`
§Emulator Implications / Accept writes to prefetcher config registers

> The emulator should accept writes to prefetcher config registers (RISC_PREFETCH_CTRL_*, BRISC_END_PC_PC, etc.) as no-ops.

### `ICACHE.PREFETCH.CFG0_DIS_PREFETCH_BIT`
§Prefetcher Configuration / cfg0 bit 2 DisIcPrefetch

> cfg0 CSR bit 2 (DisIcPrefetch) can disable the prefetcher from the core side. The emulator stores the bit but takes no action.
