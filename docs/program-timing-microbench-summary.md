# Program Timing Microbench Summary

This report collects the focused calibration runs for a static `Program` timing
estimator. Each hardware run was submitted through the Tenstorrent device queue.
The individual reports contain exact commands and raw output summaries.

## Repro Scripts

| area | script | report |
|---|---|---|
| Pack backend | `examples/microbench_pack_backend.py` | `docs/pack-backend-microbench.md` |
| Math backend | `examples/microbench_math_backend.py` | `docs/math-backend-microbench.md` |
| Unpack backend | `examples/microbench_unpack_backend.py` | `docs/unpack-backend-microbench.md` |
| Semaphores / CBs | `examples/microbench_sem_cb.py` | `docs/sem-cb-microbench.md` |
| NoC multicast / mixed | `examples/microbench_noc_mcast_mixed.py` | `docs/noc-mcast-mixed-microbench.md` |
| DRISC overlap / output | `examples/microbench_drisc_overlap_output.py` | `docs/drisc-overlap-output-microbench.md` |

All scripts compile with:

```sh
python3 -m py_compile \
  examples/microbench_pack_backend.py \
  examples/microbench_math_backend.py \
  examples/microbench_unpack_backend.py \
  examples/microbench_sem_cb.py \
  examples/microbench_noc_mcast_mixed.py \
  examples/microbench_drisc_overlap_output.py
```

## Clean Constants

These are the most directly reusable constants for `examples/program_timing_model.py`.

| constant | value | source |
|---|---:|---|
| `MATH_OUTPUT_TILE_K_THROTTLE0_CYCLES` | `49` | math backend |
| `MATH_OUTPUT_TILE_K_UNTHROTTLED_CYCLES` | `54` | math backend |
| `MATH_2X2_SUBBLOCK_PER_K_CYCLES` | `216` | math backend, `4 * 54` |
| `UNPACK_STEADY_ROW_CYCLES` | `37.5` | unpack backend |
| `UNPACK_2X2_BW4_CYCLES` | `300.0` | unpack backend |
| `UNPACK_2X2_BW6_CYCLES` | `487.4` | unpack backend short stable run |
| `UNPACK_RELOAD_2X2_CYCLES` | `273.9` | unpack backend |
| `UNPACK_CONTEXT_FLIP_CYCLES` | `9.5` | unpack backend |
| `CB_WAIT_FRONT_READY_CYCLES` | `22.0` | sem/CB |
| `CB_RESERVE_BACK_READY_CYCLES` | `23.0` | sem/CB |
| `CB_PUSH_BACK_CYCLES` | `31.0` | sem/CB |
| `CB_POP_FRONT_CYCLES` | `31.5` | sem/CB |
| `CB_PUSH_BACK_TENSIX_RECEIVED_CYCLES` | `41.0` | sem/CB |
| `CB_POP_FRONT_TENSIX_ACK_CYCLES` | `41.5` | sem/CB |
| `TTSEMWAIT_READY_SYNC_CYCLES` | `8.0` | sem/CB |
| `NOC_SEM_SET_CYCLES` | `12.0` | sem/CB |
| `NOC_SEM_WAIT_READY_CYCLES` | `19.1` | sem/CB |
| `NOC_SEM_INC_WAIT_CYCLES` | `99.0` | sem/CB |
| `NOC_MCAST_16K_BPC` | `30.752` | NoC multicast / mixed |
| `NOC_SEM_MCAST_CYCLES` | `103.375` | NoC multicast / mixed |
| `NOC_SEM_INC_ACK_CYCLES` | `213.750` | NoC multicast / mixed |
| `NOC_MIXED_RWM_16K_CYCLES` | `607.625` | NoC multicast / mixed |
| `DRISC_GDDR_READ_GBPS` | `59.4` | DRISC overlap / output |
| `DRISC_GDDR_WRITE_GBPS` | `64.0` | DRISC overlap / output |
| `DRISC_READ_2K_TILE_CYCLES` | `209` | DRISC overlap / output |
| `DRISC_WRITE_2K_TILE_CYCLES` | `103` | DRISC overlap / output |
| `WORKER_STATEFUL_OUTPUT_WRITE_2K_CYCLES` | `37.5` | DRISC overlap / output |
| `OUTPUT_TAIL_1024_TILES_CYCLES` | `38258` | DRISC overlap / output |

## Experimental Constants

The pack backend constants below came from real-pipeline profile counters and
standalone smoke attempts. Treat them as upper/perturbed bounds until the pack
path can be isolated without timeouts.

| constant | value | note |
|---|---:|---|
| `PACK_CB16_FINAL_L1ACC_OFF_CYCLES_PER_SUBBLOCK` | `5265` | validation failed in profiled run |
| `PACK_CB24_PARTIAL_L1ACC_OFF_CYCLES_PER_SUBBLOCK` | `7425` | validation failed in profiled run |
| `PACK_CB24_PARTIAL_L1ACC_ON_CYCLES_PER_SUBBLOCK` | `5265` | validation failed in profiled run |
| `PACK_COARSE_CYCLES_PER_SUBBLOCK` | `6345` | average suggested by pack report |

These numbers are much larger than the unperturbed fitted matmul subblock wall
of about `924 cycles/subblock`, so they should not replace the fitted constant
directly. They are still useful for identifying that standalone/profiled pack
is fragile and highly state-dependent.

## Matmul Interpretation

For the current `5000^3` DRISC matmul:

- `grid=10x10`
- `per_core=16x16`
- `bw=6`
- `num_blocks=27`
- `subblocks/core = 27 * 8 * 8 = 1728`
- `packed_tiles/core = 1728 * 4 = 6912`
- `final output tiles/core = 256`
- partial-pack multiplier is `27x`

Clean lower bounds per 2x2 subblock at `bw=6`:

| component | cycles/subblock |
|---|---:|
| math lower bound | `216` |
| unpack measured | `487` |
| ready CB/semaphore overhead | tens of cycles |

The unperturbed whole-kernel fit was about `924 cycles/subblock` for the TRISC
pipeline. That leaves roughly `200 cycles/subblock` for pack/synchronization and
pipeline interaction after math and unpack. This fits the profile-level picture:
MVMUL alone is not the wall, and raw NoC bandwidth is not the wall. The slow
part is the coupled unpack/math/pack pipeline, with repeated partial pack/reload
caused by `27` K blocks.

## Remaining Gaps

- Isolated pack still needs a stable, validated harness.
- Blocking semaphore and CB waits need producer/consumer variants with known
release timing.
- DRISC DMA plus NoC stage overlap modes are implemented but timed out in this
session.
- The estimator needs a resource-queue model for overlap: RISC issue, NoC0,
NoC1, DRAM bank/controller, unpacker, math, packer, dest, L1 ports, and
semaphores.
- `TTMOP` and replay expansion should be represented explicitly rather than as
one static instruction.

## Current Estimator Scaffold

`examples/program_timing_model.py` is the first scaffold. It accepts/builds a
`Program`, infers matmul shape from RTAs, prints per-core role estimates, and
currently uses a coarse fitted TRISC subblock constant. The next step is to
replace that single fitted constant with the component constants above and a
simple resource scheduler.
