# Blackhole Math MVMUL Microbenchmark

Goal: time Tensix matmul/MVMUL work inside the smallest real
unpack -> math -> pack triangle, so math rows can run without the isolated
Src/Dest backpressure that makes repeated standalone MVMUL rows hang.

The harness lives in `microbenching/tensix/microbench_math_mvmul.py`.

## Scope

- one Tensix core, with TRISC0/TRISC1/TRISC2 active
- TRISC0 unpacks BF16 source tiles from L1 scratch into SrcA/SrcB
- TRISC1 issues the math body and records `WALL_CLOCK`
- TRISC2 waits on `MATH_PACK` and packs Dest to runtime-configured CB0
- result records in L1 at `0x12d000`
- control counters in L1 at `0x12e000`
- math setup uses the `examples/matmul_peak.py` addr-mod, replay, MOP, and pack
  sequences
- rows are run as fresh device launches to reduce cross-row state leakage

Hardware-touching runs from Codex must go through the Tenstorrent device queue.

## How To Run

From `blackhole-py`:

```sh
PYTHONPATH=. python3 microbenching/tensix/microbench_math_mvmul.py --build-only --iters 2
timeout 40 env PYTHONPATH=. TT_USB=1 BLACKHOLE_RUN_TIMEOUT_S=3 python3 microbenching/tensix/microbench_math_mvmul.py --iters 1 --only empty mvmul_latency --no-report
timeout 40 env PYTHONPATH=. TT_USB=1 BLACKHOLE_RUN_TIMEOUT_S=3 python3 microbenching/tensix/microbench_math_mvmul.py --iters 2 --only empty mvmul_throughput subblock2x2_throughput
```

When run by an agent, submit the hardware commands with `tt-device-queue` rather
than invoking them directly.

Useful options:

- `--core X,Y`: choose the logical Tensix core.
- `--iters N`: iteration count for issue and throughput rows; latency rows force
  one iteration.
- `--only ...`: run a small subset. `empty` is inserted automatically if absent.
- `--build-only`: compile/layout all selected Programs without opening the
  device.
- `--no-report`: print without appending this document.

## Methodology

The benchmark reports the three numbers from the backend plan:

- **Issue cost**: timestamp before math body emission, timestamp immediately
  after the body is queued, then drain and pack outside the timed window.
- **Completion latency**: timestamp before one math body, drain with
  `TTSTALLWAIT(SYNC, MATH|SFPU)` plus `PC_BUF_SYNC`, then timestamp.
- **Steady-state throughput**: loop over unpacked inputs, math body, completion
  drain, and pack consumption. This is the practical in-scaffold throughput
  number; it intentionally keeps the pack consumer live so Dest does not
  backpressure.

Adjusted rows subtract the `empty` loop cost. Cycle counts are primary; the
current shared-card clock is 800 MHz, so 1 cycle is 1.25 ns for any derived time
figures.

`cycles/MVMUL` in the printed table is an **encoded-instruction denominator**:
the throttle0 path uses `MATMUL_MATH_REPLAY_LOAD_THROTTLE0`, whose replay payload
contains 16 encoded `TTMVMUL(...)` slots per output tile. This is not the same
unit as the architecture-model shorthand in `matmul-bf16-ceiling.md`, which says
a `32x32 @ 32x32` tile product decomposes into eight `16x16x16` MVMULs. Stated
another way:

- architectural model: `8` high-level `16x16x16` MVMUL products per output-tile
  K step
- current code denominator: `16` encoded `TTMVMUL` replay slots per output-tile
  K step

The static reconciliation is therefore a factor of two between the high-level
model unit and the encoded replay-slot unit in this BF16 throttle0 sequence.
Until the MOP expander's exact retirement semantics are decoded, the safest
headline numbers are the raw output-tile/subblock cycle counts; the per-MVMUL
column should be read as cycles per nominal encoded replay slot, not as cycles
per architectural `16x16x16` product.

## Interpretation

The scaffold is deliberately a real producer/consumer triangle, not a fake-token
math-only loop:

- TRISC0 publishes an L1 `PRODUCED_COUNT` after each unpacked subblock.
- TRISC1 waits for produced input before entering the timed math row.
- TRISC1 posts `MATH_PACK` only after the math completion drain.
- TRISC2 consumes the semaphore and packs the Dest subblock into CB0.

That means issue rows are the cleanest estimate of RISC instruction push cost,
latency rows are the cleanest one-op completion edge, and throughput rows are
the best "does this keep running without wedging" scaffold result.

## Current Results

No stable hardware timing numbers yet. Non-device validation completed:

```sh
PYTHONPATH=. python3 -m py_compile microbenching/tensix/microbench_math_mvmul.py
PYTHONPATH=. python3 microbenching/tensix/microbench_math_mvmul.py --build-only --iters 2
```

Both commands succeeded for all rows.

Queue smoke attempts:

| date | command | result |
|---|---|---|
| 2026-06-09 | `timeout 120 env PYTHONPATH=. TT_USB=1 python3 microbenching/tensix/microbench_math_mvmul.py --iters 1 --only empty mvmul_latency --no-report` | initial version failed before execution because slow dispatch tried to preload CB16 sync-register segments outside the TLB window |
| 2026-06-09 | same command after switching to runtime CB0 setup | `empty` completed, `mvmul_latency` timed out waiting for core `(1,2)` |
| 2026-06-09 | same command after moving the TRISC0/TRISC2 release flag until after TRISC1 math init | `empty` completed, `mvmul_latency` still timed out waiting for core `(1,2)` |
| 2026-06-09 | job `51bb07ee`: `timeout 40 env PYTHONPATH=. TT_USB=1 BLACKHOLE_RUN_TIMEOUT_S=3 python3 microbenching/tensix/microbench_math_mvmul.py --iters 1 --only empty mvmul_latency --no-report` after adding real BRISC release/init barriers | `empty` completed; `mvmul_latency` timed out waiting for core `(1,2)`. L1 snapshot: header status was DONE, `ready=1 produced=1 math_done=1 packed=0`, so TRISC0 and TRISC1 completed one tile and TRISC2 did not finish pack. The breadcrumb values were invalid because both breadcrumb and runtime CB setup used `t0` as value and address scratch, so they stored the target address instead of the intended value. The code now uses a separate address scratch (`tmp_addr=t1`) for those writes; per stop-on-first-failure instruction this corrected version has not been rerun on hardware. |
| 2026-06-09 | job `b10c57bc`: queue-python wrapper for `python3 microbenching/tensix/microbench_math_mvmul.py --iters 1 --only empty mvmul_latency --no-report` with `BLACKHOLE_RUN_TIMEOUT_S=3` after fixing the `t0` clobber | Did not reach benchmark execution. `Device()` failed immediately with `ARC not ready after 2.0s (boot_status=0xffffffff)`. |
| 2026-06-09 | reset job `d08d6495` | Queue-owned reset also failed with `ARC not ready after 2.0s (boot_status=0xffffffff)`. Hardware was stopped here; no further benchmark runs were attempted. |

The device was reset through `tt-device-queue reset` after each timeout.

Final queued measurement jobs after the runtime-CB0 clobber fix and
matmul-style TRISC release/init barrier:

| job | row | iters | adjusted cycles | cycles/tile | cycles/encoded TTMVMUL slot | produced | packed |
|---|---|---:|---:|---:|---:|---:|---:|
| `5e2accd9` | `mvmul_issue` | 1 | 19.00 | 19.00 | 1.19 | 1 | 1 |
| `b8193106` | `mvmul_latency` | 1 | 90.00 | 90.00 | 5.62 | 1 | 1 |
| `923041b9` | `mvmul_throughput` | 2 | 147.00 | 147.00 | 9.19 | 2 | 2 |
| `1e21db8f` | `subblock2x2_issue` | 1 | 32.00 | 8.00 | 0.50 | 1 | 1 |
| `f485f98f` | `subblock2x2_latency` | 1 | 187.00 | 46.75 | 2.92 | 1 | 1 |
| `4e6d48c9` | `subblock2x2_throughput` | 2 | 244.00 | 61.00 | 3.81 | 2 | 2 |

At 800 MHz, multiply cycles by 1.25 ns/cycle. For example, one-tile latency is
`90 cycles ~= 112.5 ns`, and true 2x2 subblock latency is
`187 cycles ~= 233.75 ns`.

Using the architecture-model denominator from `matmul-bf16-ceiling.md` instead
of the encoded replay-slot denominator gives:

| row | adjusted cycles | cycles/architectural MVMUL |
|---|---:|---:|
| `mvmul_issue` | 19.00 | 2.38 |
| `mvmul_latency` | 90.00 | 11.25 |
| `mvmul_throughput` | 147.00 | 18.38 |
| `subblock2x2_issue` | 32.00 | 1.00 |
| `subblock2x2_latency` | 187.00 | 5.84 |
| `subblock2x2_throughput` | 244.00 | 7.62 |

Interpretation notes:

- The scaffold now validates that all three roles complete for every measured
  row (`produced == iters`, `packed == iters`).
- The one-tile latency number is `90` cycles. Dividing by the eight
  architectural MVMULs from the model gives `11.25` cycles per architectural
  MVMUL; dividing by the 16 encoded replay slots in this code gives `5.62`
  cycles per replay slot. Neither exactly matches the plan's 16-cycle claim,
  which means this scaffold is measuring the full synchronized tile-K body in a
  producer/consumer triangle, not an isolated architectural-MVMUL retirement
  counter.
- The true 2x2 subblock latency is 187 cycles, and the two-iteration
  in-scaffold throughput row amortizes to 244 cycles/subblock.

## Open Issues

- `cycles/MVMUL` remains a naming hazard: the program prints cycles per encoded
  `TTMVMUL` replay slot. The architectural model uses eight high-level
  `16x16x16` MVMUL products per tile. Keep both denominators visible until the
  MOP expander and fidelity-phase semantics are documented more formally.
- The earlier TRISC2 hang was caused by runtime CB0 setup using `value=t0` with
  default `tmp_addr=t0`, clobbering the value register with the destination
  address. This is fixed, and the final measured rows all completed through
  pack.
- Throughput rows include one completion drain per subblock so TRISC2 can pack
  safely. A future variant can try a multi-body single-drain burst once the
  scaffold rows are known not to hang.
- There is no output-value validation here; pack is present as a drainer, not as
  a correctness oracle.
