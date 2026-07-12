# Porting notes

## Resident firmware policy

The rewrite ports hardware behavior, not TT-Metal's dynamic launch layout.
Firmware images, worker images, parameters, and circular-buffer interfaces all
have fixed host-owned addresses.  Resident firmware therefore does not copy or
walk a launch structure, relocate RTA/CRTA tables, or convert CB descriptors.
See `docs/l1.md` for the complete worker-L1 layout and `fw/consts.py` for its
checked executable definition.

The retained boot responsibilities are the ones required by hardware:

- The host uploads all five images, installs subordinate reset PCs, and only
  then releases BRISC.
- BRISC configures clock gating, clears the architectural zero region,
  invalidates every RISC instruction cache, resets Tensix, and initializes both
  of its NoC instances.
- NCRISC initializes both of its NoC instances from the hardware logical IDs.
- The five RISCs use four fixed synchronization bytes and one fixed host go
  byte; these are the complete control ABI.
- Per-program worker text and parameter words are written directly by the host.
  CB geometry is embedded in each specialized worker image; no CB descriptor or
  local-interface table exists at runtime.  BRISC invalidates instruction
  caches before each run.

Both BRISC and NCRISC NoC setup reads the per-core logical ID at runtime because
the same resident image is multicast to all workers.  The generated command
buffer addresses and local-state destinations are otherwise compile-time
constants.  Completion batches snapshot live NIU counters when they begin, so
the legacy per-launch counter copies are deliberately absent.

### Parity with `blackhole-py` resident firmware

The retained sequences match the old firmware in this order:

- BRISC: CSR, stack, clock controls, NoC clock-gating RMWs, zero region, cache
  invalidation, Tensix reset, saved NoC coordinates, NCRISC halt/resume clear,
  both NoC command-buffer initializers, cache invalidation, subordinate release.
- Before each run: Tensix reset, both NoC command-buffer initializers, cache
  invalidation, subordinate release, fixed BRISC worker call, completion wait.
- NCRISC: stack, CSR, saved coordinates for both NoCs, fixed NCRISC worker loop.
- Each TRISC: GP, stack, CSR, register-file clear, PRNG seed zero, 600-cycle
  delay, then a per-run register-file clear and fixed worker call.

Deliberately absent because kernels no longer read them: copied local-data
images, logical/relative coordinate shadows, launch pointers, semaphore/RTA
tables, CB interfaces and sync counters, `dest_offset_id`, `op_info_offset`,
`cfg_state_id`, and `TRISC0_UNPACK_CFG_CONTEXT`.  Unpack context selection is a
thread-configuration write emitted by `Unpack`; its first assignment is never
optimized away, even when selecting context zero.

## NoC clock gating

Clock gating is one-time resident BRISC initialization, not program or kernel
configuration. At boot, for both NoC 0 and NoC 1:

1. Read `NIU_CFG_0` and write it back with bit 0 set.
2. Read `ROUTER_CFG_0` and write it back with bit 0 set.

Use read-modify-write so every other configuration bit is preserved. TT-Metal
identifies bit 0 as clock-gating enable and bits 1–7 as gating hysteresis. The
public Blackhole ISA documentation currently labels these low bits reserved,
so reproduce the firmware sequence without exposing them as supported runtime
configuration.

Clock gating stops the NIU or router clock while that block is idle, reducing
dynamic power without powering the block off or losing its state. Hardware
resumes the clock for activity. TTSIM stores the two configuration registers
but does not model their power behavior.

References:

- `../tt-metal/tt_metal/hw/firmware/src/tt-1xx/brisc.cc` (`device_setup`)
- `../tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/noc/noc_parameters.h`
- `../tt-isa-documentation/BlackholeA0/NoC/MemoryMap.md`

## NoC completion policy

All ordinary and multicast writes are posted: they do not set
`NOC_CMD_RESP_MARKED` and do not generate destination acknowledgement packets.
Before releasing or reusing source CB pages, wait for
`NIU_MST_POSTED_WR_REQ_SENT` to advance by the expected packet count. This proves
the NIU consumed/injected the source payload, not that the destination stored
it. The NoC API represents this with `write_batch()` or a write stream's nested
`batch()` context.

Reads remain response-bearing because the response carries the requested data.
Atomic increments remain response-bearing where their completion is explicitly
needed. Matmul synchronization uses posted data writes followed by posted
data-ready semaphore writes; preserve their NoC ordering.

## NoC work remaining

Runtime-branch safety is handled by making every ordinary operation emit its
complete required command-register image. There is no ordinary `_buffers`
shadow or assumed zero/canonical initial image. Repeated reads and writes use
explicit stream contexts whose setup dominates every issue:

```py
with noc.read_stream(tile_bytes, return_coord=local) as reads:
  with reads.batch(count=tile_count):
    for tile in tiles:
      reads.issue(src, src_coord, dst)
```

The context exclusively owns its hardware command buffer. Every issue updates
all dynamic address fields, so runtime branches may skip issues safely; normal
operations cannot alter the invariant fields until the context exits. In the
current generated code this removes about 57--58% of the instructions across
eight repeated transfers.

The same applies to posted multicast:

```py
with noc.write_batch() as writes:
  writes.multicast(src, dst, rectangle, size)
noc.multicast_signal(...)
```

Required pieces:

- Completion batches use `(current - start) >=u count`, which is safe across
  32-bit wrap for batches smaller than 2^31 operations.
- `multicast()` now owns explicit 16 KiB chunking and the complete linked/path
  reservation sequence. Ordinary reads and writes reject oversized literals.
- Static and runtime coordinate packing are distinct APIs.
- Completion uses global per-NIU counters.

Regression tests should compare emitted command-register writes for:

- DRAM read batch completion.
- Posted DRAM write batch completion.
- Multi-chunk linked multicast followed by a data-ready signal.
- A runtime branch where the first operation is skipped.

The runtime-branch case guards against accidentally reintroducing an unsafe
ordinary command-buffer shadow.
