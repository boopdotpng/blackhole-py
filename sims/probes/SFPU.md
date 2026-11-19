# SFPU and I-cache probes

Ports of the old pytest probes (`test_sfpu_hazards.py`, `test_sfpu_matrix.py`, `test_sfpu_loadmacro.py`,
`test_sfpu_dst.py`, `test_icache.py`, `conftest.py`; built on blackhole-py 718843a^'s `Asm`/`Profiler` harness, which
no longer exists on disk) to the C probe harness (`probe.h`, `tile.py`, `run.py`). The old files are deleted; their
results stay in `sims/results/2026-11-18-{sfpu,icache}-*.jsonl` and every new case carries the matching old value as
`expect` (keyed `card0`/`card1`), so a rerun says `match: true/false` at once.

| file | what |
|---|---|
| `sfpu.py` | groups `hazards`, `matrix`, `loadmacro`, `dst` (3551 cases); builds every Tensix word in Python with the old field layouts |
| `icache.py` | 70 cases |
| `sfpu.h` | shared C: timed-region asm (`PROF_REC`, `PROF_DRAIN`), unpack-to-Dst, packer, semaphore polls, config recording |
| `k_sfpu_loop.c` | trisc1 loop timing (hazards, matrix, loadmacro timing) |
| `k_sfpu_value.c` | trisc0 unpack -> trisc1 SFPU -> trisc2 pack (hazards, matrix, loadmacro values) |
| `k_sfpu_dst.c` | trisc0 unpack A/B -> trisc1 ELWMUL + SFPU -> trisc2 pack (dst) |
| `k_icache.c` | any role, straight-line loop |

## Run

The cards must be free. One output file per group and card, as before:

```
python3 sims/probes/run.py --device 1 --output sims/results/<date>-sfpu-hazards-card1.jsonl sfpu -k hazards
python3 sims/probes/run.py --device 0 --output sims/results/<date>-sfpu-hazards-card0.jsonl sfpu -k hazards
python3 sims/probes/run.py --device 1 --output sims/results/<date>-sfpu-loadmacro-card1.jsonl sfpu -k loadmacro
python3 sims/probes/run.py --device 1 --output sims/results/<date>-sfpu-dst-card1.jsonl sfpu -k dst
python3 sims/probes/run.py --device 1 --output sims/results/<date>-sfpu-matrix-card1.jsonl sfpu -k matrix
python3 sims/probes/run.py --device 1 --output sims/results/<date>-icache-card1.jsonl icache
python3 sims/probes/run.py --device 0 --output sims/results/<date>-icache-card0.jsonl icache -k brisc   # card 0 ran brisc/ncrisc
```

Suggested order: `-k hazards-timing-nop` alone first (one trisc1, no other thread), then `-k hazards-value-mov_detected`
(first three-TRISC case), then `-k dst-fpu_to_sfpload-ttnop-gap0`, then the rest. `-k prefetchoff` selects the
prefetch-off variants. `matrix` is long: 3284 cases, 18 launches each (16 timing, 2 value), and 3 kernel builds per pair
(cached in `~/.cache/blackhole-py`); it resumes like every run.py probe. Records hold `match` (rerun vs `expect` for this
card; `null` when that card was never measured), raw samples, and `cfg` (below).

## Case map

Old pytest id -> new ids. Expected values are in each case's `expect`; the source file is the old result file for the
same group and variant.

| old test (pytest id) | new ids | n | expect from |
|---|---|---|---|
| `test_sfpu_hazards.py::test_pair_timing[<unit>]` (prefetch on) | `hazards-timing-<unit>` | 30 | `sfpu-hazards-card{0,1}` |
| same, prefetch off (old run without the prefetch fixture) | `hazards-timing-prefetchoff-<unit>` | 30 | `sfpu-hazards-prefetchoff-card1` |
| same, prefetch off, `TIMING_CLEAR_CFG0_BITS=0x40000` | `hazards-timing-prefetchoff-clr40000-<unit>` | 30 | `sfpu-hazards-prefetchoff-card0` |
| `test_hazard_values[<case>-<gap>]` | `hazards-value-<case>-gap<gap>` | 22 | `sfpu-hazards-card{0,1}` (+ `sfpu-minmax5-card1`) |
| same, prefetch off | `hazards-value-prefetchoff-<case>-gap<gap>` | 18 | `sfpu-hazards-prefetchoff-card1` |
| `test_sfpu_matrix.py::test_matrix[<P>]`: the single record | `matrix-single-<P>` | 44 | `sfpu-matrix-card1` (`kind: single`, `name: <P>`) |
| `test_matrix[<P>]`: one record per consumer | `matrix-pair-<P>-<C>` | 3168 | `sfpu-matrix-card1` (`kind: pair`) |
| `test_consumer_single[<C>]` | `matrix-consumer-<C>` | 72 | `sfpu-matrix-card1` (`name: C:<C>`) |
| `test_sfpu_loadmacro.py::test_throughput[<config>]`, unit u | `loadmacro-timing-<config>-<u>` | 40 | `sfpu-loadmacro-card1` |
| `test_execution_cycle`, (unit, delay d, k) | `loadmacro-exec-<unit>-d<d>-k<k>` | 42 | `sfpu-loadmacro-card1` |
| `test_collisions`, case c | `loadmacro-collision-<c>` | 6 | `sfpu-loadmacro-card1` |
| `test_sfpu_dst.py::test_fpu_to_sfpload[<kind>]`, gap g | `dst-fpu_to_sfpload-<kind>-gap<g>` | 14 | `sfpu-dst-card1` |
| `test_dst_half_sweep`, (sfpu, where, batch b) | `dst-half-<sfpu>-<where>-b<b>` | 35 | `sfpu-dst-card1` |
| `test_icache.py::test_icache[<role>-<kind>]`, size n | `icache-<role>-<kind>-n<n>` | 70 | `icache-card{0,1}` |

Old pytest cases that wrote several records became one new case per record (matrix, loadmacro, dst, icache), so a
rerun resumes and compares per record. Old cases ported: hazards 52/52 (+ the two old variants: 30 + 30 timing, 18
value), matrix 116/116 (3284 records), loadmacro 10/10 (88 records), dst 3/3 (49 records), icache 7/7 (70 records).

Not ported:
- `shft2_lreg_vb` (gap 0 and 1) in `sfpu-hazards-prefetchoff-card1.jsonl`: written by an earlier version of
  `test_sfpu_hazards.py` (source sha256 e0a74e66...) that defined it. That version was never committed; its consumer
  word is unknown, so the case cannot be rebuilt.
- `icache-trisc2-addi-n1024` has no expect: the old card-1 run never recorded it.
- The minmax5 cases only exist with prefetch on (they were added after the prefetch-off run).

Expected values, hazards (slopes at 64->128 / 128->256 iterations, cycles per unit; values: verdict and the one word
seen):

| unit | card0 | card1 | prefetch off, card1 | prefetch off + clear 0x40000, card0 |
|---|---|---|---|---|
| nop | 0.999023/1 | 1.00098/1 | 1/1 | 1/1 |
| mad_chain | 2/2 | 2/2 | 2/2 | 2/2 |
| mad_nop_chain | 2.00098/2.00098 | 2.00098/2 | 2/2.00146 | 2/2 |
| mad_ind4 | 0.999023/1 | 1/1 | 1/1 | 1/1 |
| mad_indep_mov | 1.99805/2 | 2.00098/2 | 2.00098/1.99951 | 2/2 |
| mad_dep_mov | 3/3 | 3/3 | 3/3 | 3/3 |
| mad_nop_dep_mov | 2.99902/3 | 2.99902/3.00146 | 2.99902/3 | 3/3.00146 |
| mad_nop_indep_mov | 3/2.99902 | 3/2.99951 | 3.00195/2.99902 | 3.00293/3.00049 |
| mad_iadd_vc | 3/3 | 3/3 | 3/3 | 3/3 |
| mad_iadd_vd | 2.00098/2 | 2.00195/1.99902 | 2/1.99951 | 2/2 |
| mad_setsgn_vd | 2/2.00049 | 2.00098/2 | 2/2.00146 | 2/2 |
| mad_and_vb | 1.99902/2.00049 | 2.00098/2 | 2.00098/1.99951 | 2/2 |
| mad_minmax | 3/3 | 3/3 | 3/3 | 3/3 |
| mad_nop_minmax | 4/4 | 4/4 | 4/4 | 4/4 |
| mad_swap | 3/3 | 3/3 | 3/3 | 3/3 |
| mad_shuf | 3/3 | 3/3 | 3/3 | 3/3 |
| mad_loadi_lo | 2/2 | 2.00098/2 | 2/1.99951 | 2/2 |
| swap_mov | 3/3 | 3/3 | 3/3 | 3/3 |
| swap_nop_mov | 3.00195/2.99902 | 2.99902/3 | 3.00098/2.99951 | 2.99902/3 |
| swap_nop2_mov | 3.99902/3.99951 | 4/4 | 4/4 | 4/4.00098 |
| shuf_mov | 3/3 | 3/3 | 3/3 | 3/3 |
| shuf_nop_mov | 2.99902/3.00049 | 3/3.00098 | 3/2.99902 | 3.00293/2.99854 |
| shft2_lreg_mov | 2.00098/2 | 2/2 | 2.00195/1.99902 | 2/2 |
| loadi_pair | 2/2 | 1.99707/2.00098 | 2.00098/2 | 1.99902/2 |
| sfpload | 1.00098/0.999512 | 1.00098/0.999512 | 0.999023/1 | 1/1 |
| sfpstore | 0.999023/1 | 1/1 | 1/1 | 1/1 |
| load_mad_store | 4/4 | 4/4 | 4/4 | 4/4 |
| load_mad_nop_store | 4/4 | 3.99902/4 | 4/4.00098 | 4/3.99951 |
| arecip_mad | 1.99902/2 | 2/2 | 2.00098/1.99951 | 2/2 |
| tt_nop_mad_dep | 3/3 | 2.99902/3.00098 | 3.00195/2.99951 | 3.00391/3 |

| case | gap | card0 | card1 | prefetch off, card1 |
|---|---|---|---|---|
| mov_detected | 0 | new 0xc0a00000 | new 0xc0a00000 | new 0xc0a00000 |
| mov_detected | 1 | new 0xc0a00000 | new 0xc0a00000 | new 0xc0a00000 |
| iadd_vd | 0 | old 0x3f800001 | old 0x3f800001 | old 0x3f800001 |
| iadd_vd | 1 | new 0xc0a00001 | new 0xc0a00001 | new 0xc0a00001 |
| iadd_vc_imm | 0 | new 0xc0a00001 | new 0xc0a00001 | new 0xc0a00001 |
| iadd_vc_imm | 1 | new 0xc0a00001 | new 0xc0a00001 | new 0xc0a00001 |
| and_vb | 0 | old 0x3f800000 | old 0x3f800000 | old 0x3f800000 |
| and_vb | 1 | new 0xc0a00000 | new 0xc0a00000 | new 0xc0a00000 |
| setsgn_vd | 0 | old 0x40400000 | old 0x40400000 | old 0x40400000 |
| setsgn_vd | 1 | new 0xc0400000 | new 0xc0400000 | new 0xc0400000 |
| minmax_min | 0 | new 0xc0a00000 | new 0xc0a00000 | new 0xc0a00000 |
| minmax_min | 1 | new 0xc0a00000 | new 0xc0a00000 | new 0xc0a00000 |
| minmax_max | 0 | new 0x40400000 | new 0x40400000 | new 0x40400000 |
| minmax_max | 1 | new 0x40400000 | new 0x40400000 | new 0x40400000 |
| shuffle | 0 | old 0x3f800000 | old 0x3f800000 | old 0x3f800000 |
| shuffle | 1 | new 0xc0a00000 | new 0xc0a00000 | new 0xc0a00000 |
| loadi_lower | 0 | other 0x0 | other 0x0 | other 0x0 |
| loadi_lower | 1 | new 0xc0a01234 | new 0xc0a01234 | new 0xc0a01234 |
| minmax5_min | 0 | old 0x40a00000 | old 0x40a00000 | - |
| minmax5_min | 1 | new 0x40400000 | new 0x40400000 | - |
| minmax5_max | 0 | old 0x40400000 | old 0x40400000 | - |
| minmax5_max | 1 | new 0x40a00000 | new 0x40a00000 | - |

## What changed from the old harness

Methodology is kept case for case: same loop bodies, same iteration counts (hazards 64/128/256, matrix and loadmacro
32/96, dst 16/48, icache 4/8/16 passes), one launch per sample with the first launch of each point discarded
(hazards 1 + 7, matrix/loadmacro/dst 1 + 3, icache 1 + 5), raw samples kept, the same slope formulas, the same
value checks (hazards: Dst slot 1 words; matrix: ref/noprod/gap0/gap1 variants, 2 launches; loadmacro: L0-L7 and Dst
row 0; dst: 3 launches of the value kernel).

Timed regions are instruction for instruction the old ones: the RISC part (`li t5, WALL_CLOCK_L; lw; li t5, slot; sw`,
the loop, `STALLWAIT; li; sw zero; lw; and zero` drains, the stop record, `fence`) is a single asm statement
(`sfpu.h` `PROF_REC`/`PROF_DRAIN`), and the Tensix words come from the same field layouts. Checked against the old
harness (rebuilt from 718843a^ in a scratch directory, old images assembled without hardware): for every hazards,
loadmacro, dst and icache case and every matrix single and pair, (1) the timed region's mnemonic + Tensix word
sequence from `llvm-objdump` of the new image equals the old one, (2) the loop body's Tensix words are equal, (3) the
whole kernel's Tensix word stream equals the old one (for the three-TRISC kernels, the old one as executed: dead
tail branches dropped), except for the three SEMWAITs listed below. No mismatches.

Differences that can move a baseline:

1. **Instruction prefetch.** The old `conftest.py` / `prefetch_on` fixtures re-applied `RISC_PREFETCH_CTRL = 0x11F`
   (cfg reg 208) with a BRISC launch per module, because the blackhole-py-old firmware did not set it. The current
   `fw/hw.h reset_tensix()` writes 0x11F at boot and after every launch, so the probes do not touch it. The old
   "prefetchoff" runs were the same tests without that fixture (prefetch at the old firmware's default, taken to be
   0). The ported prefetch-off variants write 0 to cfg reg 208 from the kernel itself, at entry (trisc1 for timing;
   all three TRISCs for values); the firmware restores 0x11F after the launch. So the kernel's first fetches still
   run with prefetch on; the timed loop is fetched after the write.
2. **cfg0 (CSR 0x7c0).** Old `Asm.configure_csr` and current `fw/hw.h configure_csr` set the same bits (bit 3 L0 data
   cache off everywhere; bit 18 clear on TRISCs = .ttinsn fusion on, set on BRISC/NCRISC). The `clr40000` variant
   clears bit 18 (as `TIMING_CLEAR_CFG0_BITS=0x40000` did) and restores it; on TRISCs it is already clear, so it is
   the same configuration (as it was in the old run). No old run had fusion off, and none is added: whether a
   `.ttinsn` word executes at all with bit 18 set is untested, so a fusion-off variant could trap.
3. **Recorded per result** (`cfg`, from the timed role's RES_AUX): `cfg0_entry`, `cfg0_timed` (after any clear),
   `prefetch` (cfg reg 208 read back inside the kernel, after any write; `null` on NCRISC, which cannot reach the
   Tensix config space), `dest_cg` (DEST_CG_CTRL) and `tdma_cg` (TDMA_CLK_GATE_EN). The old firmware wrote
   DEST_CG_CTRL = 0 and TDMA_CLK_GATE_EN = 0x3F at boot; `tile.py` only installs the worker firmware (those writes
   are in `fw/init.c`, which it does not run), so if a rerun shows other values, Dst/FPU timings (dst-*) may move.
4. **Per-launch reset.** Old: BRISC ran its reset_tensix before releasing each launch, TRISCs only zeroed their GPRs.
   Now: reset_tensix runs after the previous launch (and at boot), adds CLEARDVALID reset and SEMINITs all eight
   semaphores (old: 0, 1, 2, 7), and every TRISC runs `reset_thread()` (ThreadConfig 0-66 zeroed by SETC16, RWC/ADC
   reset) right before its kernel. These ~70 Tensix words drain before the first SETUP drain, outside every timed
   region. State the kernels set themselves (LOADMACRO templates/sequences, SFPU LREGs) is set again by every case,
   as before.
5. **Waits.** Old Tensix SEMWAITs on another thread's semaphore are RISC polls of the semaphore, bounded by
   WAIT_UNTIL (sites: unpack_config_sync, math_done, unpack_to_dest, math_pack; dst: unpack_config_a/b, ready,
   math_pack): unpack `SEMWAIT(UNPACK, MATH_DONE, ON_ZERO)` a6040201, math `SEMWAIT(SYNC, UNPACK_TO_DEST, ON_ZERO)`
   a6010011, pack `SEMWAIT(TDMA, MATH_PACK, ON_ZERO)` a6008009. Kept as Tensix waits because their condition holds
   when issued: unpack `SEMWAIT(UNPACK, UNPACK_TO_DEST, ON_MAX)` (the semaphore is 0 until this thread posts it),
   dst math `STALLWAIT(MATH, SRCA_VLD | SRCB_VLD)` (READY is written after the unpacker drained), and STALLWAITs on
   the issuing thread's own units. The old unbounded RISC polls (unpack config sync, dst READY) are WAIT_UNTIL.
   None of this is inside a timed region.
6. **L1.** INPUT/OUTPUT of the value kernels moved from 0x50000/0x60000 (now trisc0/trisc1 RES/LOG) to
   0x100000/0x110000; so the unpack base and pack destination config words differ from the old ones. Time stamps
   go to the timed role's LOG + 0xFC0/0xFC4 (old: one profiler block at 0x17FFC0), read over PCIe instead of a
   separate BRISC NoC export launch. dst keeps 0x40000-0x45040.
7. **Code placement.** Kernels sit at the current slot addresses (trisc1 0x6000 or slot 1), so the loop's offset in
   the instruction-cache lines differs from the old image. Fetch-bound loops (icache, SFPNOP/TTNOP bodies) may move
   slightly; SFPU-bound slopes should not.

## Risky cases

- Every value / dst case: three TRISCs and the first use of the ported unpack-to-Dst and packer sequences on this
  firmware. Run one (`-k hazards-value-mov_detected-gap0`, `-k dst-fpu_to_sfpload-ttnop-gap0`) before the rest. A
  stuck Tensix wait would make the PC_BUF drain (in the kernel or in `firmware_resume`) hang: a hard failure.
- `*-prefetchoff-*`: TRISC writes to cfg reg 208 were not exercised on the current firmware; the recorded
  `cfg.prefetch` shows whether the write took.
- `loadmacro-*`: LOADMACRO templates / sequence / misc config are not reset between launches (not by the old
  firmware either); each case writes slot 0 and misc itself, as the old one did.
- `matrix-pair-*` with `TRANSP`, `LUT*`, `CONFIG.L12` or `STORE` consumers touch SFPU state beyond LREG0-7 (the old
  run did the same, case for case).
- `icache-ncrisc-*`: NCRISC skips the config reads (cfg reg 208 and the clock-gating registers).

## Stale references (files I may not edit)

- `sims/hw.py` lines 46-51: the SFPU MEAS header names `sims/probes/test_sfpu_{matrix,hazards,loadmacro,dst}.py` and
  "old-firmware boot"; should name `sfpu.py -k <group>`. Line 47 says "46 producer x 70 consumer"; the probe has
  44 producers x 72 consumers (3168 pairs).
- `sims/test_sfpu_model.py` line 45: section comment "(test_sfpu_hazards.py)". It imports only `sims.hw` and still
  passes (12 tests).
- The deleted `conftest.py` docstring's run instructions (`sims/probes/sweep.py`, `pytest ... --bh-hardware
  --bh-device N --bh-timeout`, `TIMING_OUTPUT`, `BLACKHOLE_PY_OLD`) are referenced nowhere else in the repo; the
  run commands above replace them.
