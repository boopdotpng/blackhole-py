# Instruction Cache

Each baby RISC-V has an L0 instruction cache between it and L1. This is separate from the L0 data cache (see `blackhole-emulator-spec.md` §3.5).

## Capacity

| Core   | I-cache size |
|--------|-------------|
| BRISC  | 2 KiB       |
| TRISC0 | 2 KiB       |
| TRISC1 | 512 bytes   |
| TRISC2 | 2 KiB       |
| NCRISC | 512 bytes   |

Capacity = 4 bytes × max instructions held. Tag storage is additional and not counted.

## Behavior

- Instructions are fetched into the cache on demand. A hardware prefetcher also pulls instructions speculatively.
- Maximum bandwidth is 1 instruction (32-bit) per cycle.
- In TRISC cores, the cache can fuse up to 4 adjacent `.ttinsn` instructions into a single 64/96/128-bit instruction executed in one cycle.
- No `Zifencei` support — `fence.i` is treated as `nop` (non-contractual). Software cannot flush the I-cache with a fence.

## Invalidation

Invalidation is done by writing a per-core bitmask to `RISCV_IC_INVALIDATE_InvalidateAll` at config register index 185 (`TENSIX_CFG_BASE + 0x2E4`):

| Bit | Core   |
|-----|--------|
| 0   | BRISC  |
| 1   | TRISC0 |
| 2   | TRISC1 |
| 3   | TRISC2 |
| 4   | NCRISC |

Writing `0x1F` invalidates all 5 cores. This is what firmware does during `device_setup()`.

Constraints:
- The register is in Tensix backend config space — **NCRISC cannot access it**, so NCRISC cannot invalidate its own or anyone else's I-cache.
- Invalidation clears the cache but **not the pipeline** — up to ~20 already-fetched instructions may still execute from stale contents.
- Also cleared on soft reset.

When writing new instructions to L1 and then invalidating, memory ordering matters — the L1 write must complete before the invalidation. The canonical sequence from the ISA docs:

```
sw t0, 0(t1)   # write new instruction to L1
lw t2, 0(t1)   # read back from same address (forces ordering)
addi x0, t2, 0 # consume result of load
sw t3, 0(t4)   # write to RISCV_IC_INVALIDATE_InvalidateAll
```

## Prefetcher Configuration

These registers control the prefetcher. All live in Tensix backend config space:

| Register | Scope |
|----------|-------|
| `RISC_PREFETCH_CTRL_Enable_Brisc` | BRISC prefetcher enable |
| `RISC_PREFETCH_CTRL_Enable_Trisc` | TRISC0/1/2 prefetcher enable (3 bits, one per core) |
| `RISC_PREFETCH_CTRL_Enable_NocRisc` | NCRISC prefetcher enable |
| `RISC_PREFETCH_CTRL_Max_Req_Count` | Max in-flight prefetches (shared by all 5 cores) |
| `BRISC_END_PC_PC` | BRISC prefetch limit address |
| `RISC_END_PC_SEC0_PC` | TRISC0 prefetch limit address |
| `RISC_END_PC_SEC1_PC` | TRISC1 prefetch limit address |
| `RISC_END_PC_SEC2_PC` | TRISC2 prefetch limit address |
| `NOC_RISC_END_PC_PC` | NCRISC prefetch limit address |

If the limit address is non-zero, the prefetcher only fetches instructions at addresses ≤ the limit.

The `cfg0` CSR bit 2 (`DisIcPrefetch`) can also disable the prefetcher from the core side.

## Emulator Implications

**The I-cache does not need to be modeled.** It is functionally transparent — a pure performance optimization that does not change program semantics. Unlike the L0 data cache (which is non-coherent and creates observable behavioral differences), the I-cache only serves code that is explicitly loaded and invalidated by software.

What the emulator should do:
- **Accept writes to `RISCV_IC_INVALIDATE_InvalidateAll`** (`TENSIX_CFG_BASE + 0x2E4`) — treat as a no-op, since the emulator fetches instructions directly from the L1 backing store.
- **Accept writes to prefetcher config registers** — treat as no-ops.
- **Accept reads/writes to `cfg0` bit 2 (`DisIcPrefetch`)** — store the bit but take no action.

The only scenario where the I-cache would matter is self-modifying code (write new instructions to L1, then jump to them). Since the emulator fetches directly from L1, this works naturally without any cache to invalidate.
