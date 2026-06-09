# Blackhole Wall Clock Skew

Goal: check whether `WALL_CLOCK_L/H` is stable enough across cores for
cross-core event timing.

The harness lives in `examples/riscv_wall_clock_skew.py`. It launches two
same-row BRISCs running the same timestamp loop and compares sample-by-sample
timestamp deltas from their per-core L1 result buffers.

## Observation

For `1,2` and `2,2`, 4096 samples produced a constant `B - A` delta of `-144`
cycles with zero delta span. For `1,2` and `14,2`, 4096 samples produced a
constant `B - A` delta of `623` cycles with zero delta span.

That does not prove simultaneous reads return identical values, because launch
and instruction-stream alignment create a constant offset. It does show the
cross-core clock source is stable enough to compare event timestamps if we care
about deltas on the order of many cycles.

