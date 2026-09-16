# matmul_peak FP8/FP16 stall profile — Card 1, 2026-09-16

All runs: 5000^3, 110-core 10x11 grid, K block 10 unless noted, 5 timed runs,
validation passed on every run. "compute" = trisc1 duration (start of math to
final pack), "total" = completion-inclusive kernel time. MVMUL-only floor for
this shape is 424 us (tests/compute/fpu/matmul_compute_only.md).

## Stall counters (new, env `MATMUL_PROFILE_COUNTERS=1|2`, default off)

`kernel.py`'s previously no-op `emit_profile_accum_*` hooks now accumulate
wall-clock cycles per core into `PROFILE_COUNTER_BASE`; `matmul_peak.py --profile`
zeroes them per run and prints max / mean / interior-core mean in us. Level 1
(per-block / per-subblock hooks) perturbs total time by ~3%; level 2 adds the
per-row TRISC0 unpack-context wait and perturbs FP8 by ~19% (BF16 by <1%).

FP8 2x4, level 1 (total 759 us, compute 637 us):

| counter | us | meaning |
|---|---:|---|
| trisc0_cb_in | 21 | unpacker waiting for input blocks (A/B via NoC) — **3%** |
| trisc0_unpack_body | 568 | TRISC0 inside unpack subblocks: 75 cycles per 5-tile row |
| trisc1_pack_room | 5 | math waiting for a free Dst half (packer too slow) — **~0** |
| trisc2_pack_data | 5 | packer waiting for math — ~0 |
| trisc1_math_sync | 77 | commit: after last MOP issue until tensix_sync(1) returns |
| ncrisc_output | 176 max / 103 mean | output phase; unhidden tail after last pack ~120 us |

Input feed is not a bottleneck; the packer is not a bottleneck; the output
write is exposed only because every output tile is written after the final K
block (DRAM write bandwidth ~344 GB/s for 57.7 MB padded output = ~168 us,
of which ~120 us is not overlapped with compute).

## Zero-code variants (counters off)

| variant | total us | compute us | compute / 424 | cycles per subblock (8 tiles) |
|---|---:|---:|---:|---:|
| 2x4 (default) | 738 | 617 | 1.46 | 1627 |
| 1x8 | 731 | 611 | 1.44 | 1611 |
| 2x2 | 945 | 838 | 1.98 | 1105 (4 tiles) |
| 2x4, K block 5 | 772 | 633 | 1.49 | 1669 |
| 2x4, no commit sync | 730 | 610 | 1.44 | 1608 |
| 1x8, no commit sync | **712** | **591** | **1.39** | 1558 |
| 1x8, no sync, +2 NOP/tile-op | 738 | 618 | 1.46 | 1629 |
| 1x8, no sync, +4 NOP/tile-op | 764 | 645 | 1.52 | 1700 |
| BF16 LoFi (1 phase) 1x8, no sync | 982 | 866 | 2.04 | 1353 (K block 6) |

`MATMUL_NO_COMMIT_SYNC=1` drops the RISC-blocking `tensix_sync(1)` in
`emit_math_subblock_commit`; validation passes (PCC 0.999999, same rel_l2).
`MATMUL_EXTRA_NOPS=n` and `MATMUL_LOFI=1` are diagnostic knobs only.

## Interpretation

1. **Math-thread instruction issue is the binding limit.** Each extra NOP per
   tile-op costs exactly one cycle per tile-op (40,960 tile-ops/core x 2 slots
   = 36k cycles = 27 us observed). The current per-tile-op stream is
   `SETC16(dest offset) ; MOP -> NOP, REPLAY x16 MVMUL, SETRWC ; MOP transition`
   = ~20 issue slots per 16 MVMUL cycles, i.e. the 1.25x floor seen for every
   subblock shape and K block. The compute-only bench reaches 1.0 MVMUL/cycle
   because it issues one MOP per 256 x 32 MVMULs with no per-tile instructions.
   2x2 is worse (1.98x) because TRISC0's ~55 RISC-V cycles per unpack row then
   exceed 32 math cycles per row.
2. **Unpacker is the next wall, ~10% behind.** Per unpacked tile: ~16.3 cycles
   FP8 (1 KB), ~20.3 cycles BF16 (2 KB) => ~12 cycles fixed per tile (the
   RDCFG/ADDDMAREG/STALLWAIT/WRCFG base-address round trip inside the unpack
   replay) + ~4 cycles/KB. 1x8 needs 9 unpacks per 8 tile-ops = 147 cycles per
   128 MVMUL cycles (1.15x); 2x4 needs 10 per 8 = 163 (1.27x). BF16 at one
   fidelity phase is unpack-bound outright (866 us).
3. **Per-subblock commit drain** (tensix_sync(1)) costs ~50 cycles/subblock =
   3%; the remaining commit cost is the CFG-stall before the next SETC16.
4. **Output tail** ~120 us = 16% of total, DRAM-write-bandwidth bound, only
   fixable by starting writes earlier (split each core's output into passes).

Reproduce (from blackhole-py, queue 1):

```sh
~/.local/bin/tt-device-queue run --device 1 --cwd "$PWD" -- 'MATMUL_PROFILE_COUNTERS=1 ../.venv/bin/python examples/matmul_peak.py 5000 5000 5000 --dtype fp8 --run --device 1 --runs 5 --profile'
~/.local/bin/tt-device-queue run --device 1 --cwd "$PWD" -- 'MATMUL_NO_COMMIT_SYNC=1 ../.venv/bin/python examples/matmul_peak.py 5000 5000 5000 --dtype fp8 --run --device 1 --runs 5 --profile --subblock 1 8'
```
