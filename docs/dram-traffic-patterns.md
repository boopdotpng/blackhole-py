# DRAM traffic patterns on Blackhole p150a: reaching ~512 GB/s read+write

Experiments run 2026-11-02 / 11-03 on both local p150a cards (140 Tensix, 8 GDDR6
controllers, AICLK 1350 MHz). Scripts, case lists and raw JSON live in
[`tests/movement/dram_patterns/`](../tests/movement/dram_patterns/). This document
explains what was tried, in order, what each result means, and what it implies for
changing blackhole-py globally.

## TL;DR

* Each GDDR6 controller alone sustains ~63.3–63.9 GB/s of reads *or* writes (≈99% of
  pin rate). The controllers were never the bottleneck for single-direction traffic.
* The current blackhole-py pattern (384 GB/s at 50/50, 345 write-only) loses bandwidth
  in three independent places:
  1. **NoC routing direction.** NoC0 writes and NoC1 reads do their vertical leg *inside
     the DRAM column*; every worker's traffic shares those few links. The code alternates
     NoCs per core, so half of all traffic takes the bad route.
  2. **One port per controller.** Each controller has 3 NoC tiles; the endpoint table pins
     one tile per NoC, so a controller's whole ~63 GB/s enters through one row.
  3. **Read/write mixing in a controller.** Every controller sees both directions all the
     time, costing ~12% (GDDR6 bus turnaround plus scheduler effects).
* Fixes and what each buys (117 workers, 50/50 read+write unless noted):

  | Arrangement | GB/s |
  |---|---:|
  | Current repo pattern | 384 |
  | Reads on NoC0, writes on NoC1, rotate 3 ports, interleaved over all 8 banks | 423–448 |
  | + reads on banks 0–3, writes on banks 4–7 (no pacing) | 495–508 |
  | + wall-clock pacing at the controller rate | **510.6–511.0** |
  | Synchronized rotation of the write-bank set (works at **any** read:write ratio) | 506 |
  | Single direction: reads only / writes only (fixed routing) | 491–497 / 475 |

* True pin rate is **514.6 GB/s** (GDDR clock is 2.01 GHz, not 2.0), so 510.6 is 99.2%.
* 117 vs 137 workers: identical. The controllers saturate at ~80–96 workers; the extra
  tiles on 140-core cards add nothing for DRAM-bound work, but they don't hurt either.
  Results apply equally to 120-core cards.

## 1. Background

### 1.1 Chip layout (physical coordinates)

* Tensix columns 1–7 and 10–16; DRAM columns at **x = 0 and x = 9**, 12 DRAM tiles per
  column, rows 0–11.
* 8 controllers, **3 NoC tiles (ports) each**, in different rows (tt-metal
  `blackhole_140_arch.yaml`): bank 0 = rows {0, 1, 11}, bank 1 = {2, 10, 3}, bank 2 =
  {9, 4, 8}, bank 3 = {5, 7, 6}; banks 4–7 repeat this in column 9. Any port reaches the
  whole controller.
* Virtual (translated) coordinates used by software: bank `b`, port `p` →
  `(17 + b // 4, 12 + 3 * (b % 4) + p)`. The repo's `P150_DRAM_ENDPOINTS` picks one of
  these per bank per NoC.
* Runtime workers: 117 (120-core layout minus 3 service tiles). On a 140-core card, 20
  more tiles exist; 137 are usable once the 3 service tiles are excluded.

### 1.2 NoC routing (from `tt-isa-documentation/BlackholeA0/NoC`)

Each NoC is a one-way torus with dimension-order routing:

* **NoC0: right first, then down.**
* **NoC1: up first, then left.**

Data direction is what matters: a **write carries data core → DRAM**; a **read** sends a
small request and the **data returns DRAM → core**.

| | NoC0 | NoC1 |
|---|---|---|
| Write data (core → DRAM) | along core's row, then **down the DRAM column** ✗ | **up the core's own column**, then along the DRAM tile's row ✓ |
| Read data (DRAM → core) | along DRAM tile's row, then **down the core's column** ✓ | **up the DRAM column**, then along the core's row ✗ |

On the ✗ routes, every flow headed for a column's 4 controllers (~250 GB/s) shares that
column's vertical links. On the ✓ routes the vertical leg is spread over all ~12 worker
columns, and the data arrives at the DRAM tile along that tile's own row.

### 1.3 The DRAM itself

Provided separately (decoded from MRISC firmware and live controller memory):

* Samsung C-die GDDR6, 16 Gbps, **clamshell** (2 × 16 Gb x8 devices per controller,
  forming 2 × x16 channels), 32 GB total.
* Command clock 2.01 GHz → 64.3 GB/s per controller, **514.6 GB/s chip pin rate**.
* CL 33, WL 8, tRCD 36 (read) / 20 (write), tRFCab 245 / tRFCpb 125, tREFI 3700 tCK.
  tWTR is a low-confidence label (20 tCK).
* Estimated write→read turnaround ≈ 26 ns, so about 4 KB per channel per direction is
  needed before switching for ~90% efficiency.

### 1.4 Method common to all experiments

* Emitter: the validated standalone NIU emitter in `tests/movement/noc.py`
  (`emit_interleaved_dram_to_l1` / `emit_l1_to_interleaved_dram`), unchanged except for
  the `noc2.py` fork, which adds `dram_stride` (see §5.2).
* One stream per RISC: BRISC = slot 0, NCRISC = slot 1. Each slot gets its own NIU
  command buffer (`1 + slot`) and transaction ID.
* 2 KiB pages, issue batch 32, 2 MiB per stream (4 MiB per stream in the phase
  experiments), static VC 1, non-posted writes, unless noted.
* Timing: global tile wall clock, from the earliest stream start to the latest stream
  end (non-posted write acks included). Median of 3 launches. GB/s is decimal; mixed
  traffic counts read and write bytes once each.
* The wall-clock timebase was checked against the host clock (§5.5): device and host
  agree to within dispatch overhead.

## 2. Experiments, in order

Each step lists the hypothesis, the result, and the conclusion. File names refer to
`tests/movement/dram_patterns/`.

### E0 — Reproduce the existing baseline (`bench_dram_bandwidth.py`, results/baseline.json)

117 workers, both RISCs: **read 473.5, write 345.6, mixed 383.1**. This matches
`tests/movement/dram_bandwidth_results.md`.

### E1 — Is a single controller the limit? (exp1_ports.py, results/e1_*.json)

12 workers hammer one bank through port 0, 1, 2, or all three, on NoC0, NoC1, or both.

| | Reads | Writes |
|---|---:|---:|
| Any single port | 60–63 | 54–63 |
| 3 ports spread, NoC1 | 55–63 | **63.0–63.3 on every bank** |
| 3 ports spread, NoC0 | **62.8–63.3 on every bank** | 58–62 |

**Conclusion:** every controller absorbs ~99% of its pin rate in either direction.
8 × 63 ≈ 505, so the full-chip deficit is a fabric/placement problem. This matches
boop-docs `noc-dram-endpoint-matrix.md`: "single-source endpoint variation is small …
aggregate differences come from fabric/placement saturation".

### E2/E3 — Full-chip NoC and port policy (exp2_chip.py, exp3.py, results/e2b.json, e3_*.json)

117 workers, 2 streams per worker.

| Pattern | Read | Write | Total |
|---|---:|---:|---:|
| Repo default (NoC alternates per core, fixed port table): read / write / mixed | 470 | 345 | 384 (mixed) |
| **Writes all NoC1, rotate 3 ports** | – | **475** | 475 |
| Writes all NoC1, any single port per bank | – | ~300 | 300 |
| Writes all NoC0, rotate 3 ports | – | 179 | 179 |
| **Reads all NoC0, rotate 3 ports** | **490–492** | – | 491 |
| Reads all NoC0, one port per bank | 389–400 | – | ~390 |
| Reads all NoC1, rotate 3 ports | 232 | – | 232 |
| Mixed, R NoC0 / W NoC1, rotated ports, all 8 banks | 217 | 217 | 434 |
| **Mixed, reads only on banks 0–3, writes only on 4–7** | 247 | 247 | **495** |
| Same, any other 4/4 bank split ({0,1,4,5} / {2,3,6,7}, even/odd) | | | 493–495 |
| Mixed, read:write skewed 1.25:0.75 or 0.75:1.25 (interleaved) | | | 446–448 |

VC and priority (`noc2`/`InterleavedConfig.static_vc`, `.priority`):

| Setting | Write-only | Mixed |
|---|---:|---:|
| Dynamic VC (`static_vc=None`) | **243** | 412 |
| Static VC 0 / 1 / 2 / 3 | 473–476 | 431–435 |
| Arbitration priority 1 / 8 / 15 on reads or on writes | – | 431–436 (no effect) |

**Conclusions:**

* Routing direction is the dominant effect, exactly as §1.2 predicts.
* Rotating across the 3 ports is required: a single port caps writes at ~300 and reads
  at ~390, whichever port is used.
* Keeping reads and writes on separate controllers removes the remaining ~12%.
* Static VC is required (dynamic allocation halves write bandwidth); the VC number and
  arbitration priority don't matter.
* Posted vs non-posted writes: no difference (474.6 vs 474.7).

### E4 — Core count and page size (results/e4a.json, e4b.json)

| Cores | Write, repo default | Write, NoC1 + 3 ports | Read, NoC0 + 3 ports | Segregated mixed |
|---:|---:|---:|---:|---:|
| 16 | 282 | 153 | 177 | 322 |
| 32 | 351 | 287 | 291 | 467 |
| 48 | 353 | 397 | 386 | 489 |
| 64 | 349 | 452 | 452 | 483 |
| 80 | 348 | 473 | 461 | **499** |
| 96 | 344 | **482** | 483 | 497 |
| 117 | 345 | 473 | 491 | 498 |

* With the repo routing, writes saturate at ~32 cores (fabric-bound). With fixed routing
  they scale to ~80–96 cores, then dip slightly; this is the "~80 writers" knee seen in
  practice.
* Page size: 4 KiB helps reads slightly (496), hurts writes (438 at 4 KiB, 402 at
  8 KiB). Segregated mixed: 498 at 4 KiB, 490 at 8 KiB.

**Correctness check** (validate.py): segregated pattern, every written byte in banks 4–7
checked after poisoning, all 117 read staging buffers checked → all OK.

### E5 — 140-core cards and read:write ratio (results/e5_140.json, e5_ratio.json)

**140 cores.** `cores140.py` appends the 20 extra tiles to the worker list. Boot already
broadcasts firmware out to x = 16.

| Pattern | 96 | 117 | 128 | 137 |
|---|---:|---:|---:|---:|
| Write, repo default | 345 | 346 | 343 | 346 |
| Write, NoC1 + 3 ports | 481 | 474 | 470 | 477 |
| Read, NoC0 + 3 ports | 481 | 489 | 494 | 497 |
| Segregated 4R/4W | 496 | 495 | 496 | 499 |

**Ratio.** f is the write fraction of bytes. "Overlapped" means reads use all 8 banks
while writes are confined to k banks.

| f | Interleaved | Matched split (8−k reads / k writes) | Worst mismatched split |
|---|---:|---:|---:|
| 1/32 | 467 | 481 (overlapped, writes on 4) | 262 (4R/4W) |
| 1/8 | 457 | **496** (7R/1W) | 240 (overlapped, writes on 1) |
| 1/4 | 445 | **495** (6R/2W) | 171 |
| 3/8 | 435 | **494** (5R/3W) | 134 |
| 1/2 | 423 | **486** (4R/4W) | 109 |

**Conclusion:** a fixed split only works when k ≈ 8f; a mismatched split runs at the
speed of whichever side runs out of controllers. Interleaving (with fixed routing) is
the safe default; it degrades smoothly with f.

### E6 — Separate directions in time instead of by controller (phase.py, results/e6*.json)

Each RISC reads its share and then writes it, either once (one long phase each) or in
4 or 16 alternating rounds. No synchronization between cores.

| f | 1 round, in phase | 1 round, anti-phase | 16 rounds |
|---|---:|---:|---:|
| 1/32 | 490 | 488 | (invalid row, see notes) |
| 1/8 | 472 | 473 | 457–459 |
| 1/4 | 460 | 455 | 439–442 |
| 1/2 | 453 | 437 | 397–401 |

**Conclusion:** coarse phases work at any ratio but cap below the controller split, and
finer alternation without sync degrades below plain interleaving.

### E7/E8 — Unsynchronized phase schedules (rot.py, results/e7*.json, e8*.json)

Motivated by the turnaround model in §1.3: give controllers long same-direction runs
while keeping all 8 busy. Each stream sends S bytes to one bank per phase, then moves on.
Three schedules, same code:

* **rotate:** each bank serves reads for 4 phases, then writes for 4.
* **mixed:** every bank always sees both directions.
* **static:** reads stay on banks 0–3, writes on 4–7.

| S per phase | rotate | mixed | static |
|---|---:|---:|---:|
| 2 KiB | 425 | 416–420 | 495–501 |
| 8 KiB | 418–424 | 419–427 | 483–489 |
| 32 KiB | 386–392 | 392 | 397–399 |
| 128 KiB | 361–363 | 360–372 | 354–363 |
| 256 KiB | 359–360 | 357–370 | 348–354 |

`adj` layout (E8) makes concurrent streams interleave page by page in the same DRAM rows
(`noc2.py dram_stride`); it produced the same curve.

**Conclusions:**

* rotate ≈ mixed at every S, so rotation without sync gains nothing.
* Even static degrades with long per-stream phases, so the loss isn't turnaround, and
  (per E8) it isn't row locality either.
* Explanation: nothing keeps streams in step. Faster streams catch up with slower ones,
  streams bunch onto the same banks, and per-controller load goes lopsided. Bigger S
  makes the clumps last longer.

### E9–E11 — Wall-clock-synchronized phases (sync.py, syncrot.py, results/e9*–e11*.json)

* Tile wall clocks share one timebase (host reads of two distant tiles show one
  continuous 1350 MHz count; see wallclock.py).
* The host reads a tile's clock and broadcasts `t0 = now + 5 ms`. Each stream spins until
  `t0 + p·T` before starting phase p. This is a free global barrier with no NoC traffic.
* T = margin × ideal, where ideal = time for N streams × S bytes over 4 banks at
  62 GB/s per bank.
* **Interpreting the numbers:** if every phase fits its window, total time = phases × T,
  so the result reads 496 / margin. A result of 496/m therefore means "fits", i.e. the
  controllers sustained ≥ 62/m GB/s each. Margin < 0.969 needs more than the pin rate
  and must overrun.

**flip:** even phases reads → banks 0–3 and writes → 4–7; odd phases swap. 50/50, 117
workers.

| margin (GB/s per controller needed) | static (never flips) | flip, 15–60 µs windows | flip, 3.8 µs windows |
|---|---:|---:|---:|
| 0.97 (63.9) | **510 fits** | overrun (460–466) | overrun |
| 0.98 (63.3) | 506 fits | **506 fits** | overrun |
| 0.99 (62.6) | 501 fits | 501 fits | overrun |
| 1.0 (62.0) | 496 fits | 496 fits (also 250 µs windows) | 496 fits |
| no sync | 501–507 | 433–444 | 442 |

* Synchronized flipping reaches **506 GB/s with all 8 controllers serving both
  directions** (unsynchronized: ~441).
* A flip costs ~1% at ≥15 µs windows and 1–3% at 3.8 µs windows, i.e. ~0.1–0.3 µs per
  flip chip-wide, which is mostly pipeline drain and refill.
* The ~26 ns GDDR turnaround can't be seen at these window sizes: even 3.8 µs windows
  give each controller ~240 KB per direction. Software sync cannot probe the 1–16 KB
  region of the turnaround curve.

**Ratio-agnostic rotation (syncrot.py `rot`):** 8 phases per cycle. In phase p, banks
`{p … p+k−1} mod 8` take writes and the rest take reads, with k = 8f. Per-stream bytes
are sized so every controller carries equal load.

| f | Synced rotation (m = 0.98) | Static matched split (no sync) | Interleaved, fixed routing |
|---|---:|---:|---:|
| 1/8 | 505.5 | 508.4 | 486.4 |
| 1/4 | 506.0 | 506.5 | 471.8 |
| 3/8 | 505.9 | 507.6 | 457.6 |
| 1/2 | 506.1 | 505.9 | 447.5 |

(Interleaved here is higher than in E5 because syncrot.py uses the row-adjacent `adj`
address layout and 4 MiB streams.)

### E12/E13 — Final comparison at 137 and 117 workers (results/e12_card*.json, e13_card*.json)

Every worker reads (BRISC, NoC0) and writes (NCRISC, NoC1), 50/50, on both cards.

| Arrangement | 117 (card 0 / 1) | 137 (card 0 / 1) |
|---|---:|---:|
| Repo default | 384 | 387 |
| Interleaved, fixed routing | 448 / 447 | 449 / 450 |
| Static 4R/4W, unpaced | 504–508 / 503 | 505 / 505 |
| Synced rotation, m = 0.98 (also 506 at f = 1/8, 1/4) | 506 / 506 | 506 / 506 |
| **Static 4R/4W, paced m = 0.97** | **511.0 / 510.6** | **510.6 / 510.5** |
| Synced rotation, m = 0.97 / 0.975 | overrun 452–454 / 474–489 | overrun 461 / 485–487 |

## 3. The best arrangement, precisely

1. BRISC streams **reads on NoC0**; NCRISC streams **writes on NoC1**. Never the reverse.
2. Each stream stripes pages across its bank set, with the starting bank rotated per
   stream (`rot = j % len(banks)`).
3. Each page goes to port `(j + bank) % 3` of its controller, so all 24 DRAM tiles are
   used.
4. Concurrent streams' DRAM addresses interleave page by page: stream j's k-th page in a
   bank is at `base + (k·N + j)·page` (`dram_stride = N·page`).
5. Bank sets: reads on 0–3, writes on 4–7 for 50/50. For other ratios, either a static
   split with k = round(8f) write banks, or synchronized rotation of the write set.
6. Static VC (any number), 2 KiB pages, non-posted writes are fine.
7. Optional: wall-clock pacing at ~63.9 GB/s per controller (+1%, 505 → 510.6). Required
   for rotation.

## 4. Implications for changing blackhole-py globally

Where DRAM NoC traffic is decided today:

* `pcie.py` `P150_DRAM_ENDPOINTS` / `P100_DRAM_ENDPOINTS`: **one port per bank per NoC.**
  This table is copied into kernels via `program.py` (`dram_endpoints`), the
  `mailbox.DRAM_BANK_TO_NOC_XY` table (`examples/matmul_peak_kernel/asm.py:43`,
  `kernel.py:822,864`, `epilogue.py:269`), and `ttko/noc.py:_dram_tile`.
* NoC choice per transfer: e.g. `examples/llama3.py` uses `read_noc` per op and writes on
  `1 - read_noc`, so writes on NoC0 happen whenever `read_noc = 1`.
  `tests/movement/bench_dram_bandwidth.py` alternates per core.

Suggested order, cheapest first:

1. **Routing policy (ratio-agnostic, no planning).** DRAM reads on NoC0 and DRAM writes on
   NoC1 everywhere. Write-only 345 → 475, read-only 470 → 491, mixed 384 → 423–448.
2. **Port rotation.** Replace the single (noc0, noc1) endpoint per bank with all 3 ports
   per bank and choose `(stream + bank) % 3`, or `(tile + bank) % 3` in `_dram_tile`.
   The `DRAM_BANK_TO_NOC_XY` table would grow from 2 × 8 to 3 × 8 entries, or be
   computed from the virtual-coordinate formula in §1.1. Required to get the numbers
   above; a single port caps reads at ~390 and writes at ~300.
3. **Static VC everywhere** (already the default in `noc.py`; audit other paths).
4. **Placement (per-op, optional, ~+10–15% on write-heavy ops).** `alloc_interleaved_dram`
   already supports a contiguous `banks` / `bank_start` range. For write-heavy ops
   (prefill matmul, f ≈ 1/3) put outputs on k = round(8f) banks and inputs on the rest.
   Decode (f ≈ 0) needs nothing: keep weights interleaved on all 8 banks. A wrong k is
   worse than interleaving, so it needs an accurate ratio.
5. **Synchronized rotation (research).** Ratio-agnostic 506 GB/s, but each phase must
   read data that lives in that phase's read banks and write wherever writes are going.
   That means reordering K-tile reads and keeping an output address map, and compute has
   to keep pace with the clock.

On the 140-core cards, using the extra 20 workers doesn't help DRAM-bound kernels.

## 5. Things that went wrong / caveats (so the numbers can be trusted)

1. **Harness bug → card 1 hang.** The first full-chip run put both RISCs of a core on the
   same NIU with the same command buffer and TID (`r0w1` policy), which corrupted
   commands. Fixed (command buffer and TID = `1 + slot`); card 1 was reset with
   `tt-smi -r 1`. Rows from that run (`results/e2.json`) before the hang are valid.
2. **`dram_stride` fork.** `noc2.py` is `tests/movement/noc.py` plus one change: the
   per-stripe DRAM address step is `dram_stride` instead of `page_bytes`. Runs using it
   (rot.py `adj`, sync.py, syncrot.py) were **not byte-validated**; only the address step
   differs from the validated emitter.
3. **Paced results are window-bound** (§E9): read them as "fits at margin m", i.e. a lower
   bound of 62/m GB/s per controller. The real ceiling lies between 510.6 and 514.6.
4. **phase.py f = 1/32, 16 rounds** rows are invalid: the write chunk rounded up to one
   8-bank unit, making f = 0.125.
5. **Synthetic placement.** Every stream owns its own region; real kernels' tensor
   placement and compute stalls are not modelled.
6. **Unrolled phase code** overflowed NCRISC's text partition at 16 rounds; phase.py,
   rot.py, sync.py and syncrot.py use a runtime loop with the counter in L1.
7. `tt-device-queue` was down; experiments ran directly on `/dev/tenstorrent/0` and `/1`,
   in parallel (one process per card). Card 1's slow PCIe link only affects uploads, not
   on-device timing.
8. Single-controller clock check (clockcheck.py): device clock 63.6 GB/s; host wall clock
   60.7 GB/s including ~120 µs dispatch overhead. The ~99% per-controller efficiency
   therefore implies refresh is largely hidden (per-bank refresh is the likely
   explanation; not confirmed from registers).

## 6. Reproduce

From `blackhole-py/`, with `PY=../.venv/bin/python` and `D=tests/movement/dram_patterns`.
Every script takes `<device> <out.json> [cases.json]`. Use `-I` so only the script's own
directory and the repo root are on the import path.

```sh
$PY -I $D/exp1_ports.py 0 0,1,2,3,4,5,6,7 /tmp/e1.json       # E1 per-controller survey
$PY -I $D/exp3.py 0 /tmp/e3.json $D/cases/c_mixed.json        # E3 mixed patterns
$PY -I $D/exp3.py 1 /tmp/e3r.json $D/cases/c_readvc.json      # E3 reads, VC, priority
$PY -I $D/exp3.py 0 /tmp/e4.json $D/cases/c_sweep_a.json      # E4 core sweep (also _b)
$PY -I $D/run140.py 0 /tmp/e5.json $D/cases/c_140.json        # E5 up to 137 workers
$PY -I $D/exp3.py 1 /tmp/e5r.json $D/cases/c_ratio.json       # E5 ratio sweep
$PY -I $D/phase.py 0 /tmp/e6.json $D/cases/c_ph_a.json        # E6 time phases (also _b)
$PY -I $D/rot.py 0 /tmp/e8.json $D/cases/c_rot2_a.json        # E7/E8 unsynced rotation
$PY -I $D/sync.py 0 /tmp/e10.json $D/cases/c_sync2_a.json     # E9/E10 paced flip
$PY -I $D/syncrot.py 0 /tmp/e11.json $D/cases/c_sr_a.json     # E11 ratio-agnostic rotation
$PY -I $D/run140sr.py 0 /tmp/e12.json $D/cases/c_137.json     # E12 137 workers
$PY -I $D/syncrot.py 0 /tmp/e13.json $D/cases/c_117.json      # E13 117 workers
$PY -I $D/validate.py 0                                       # correctness spot check
```

Pipe exp2/exp3 output through `fmt.py` / `fmt3.py` for tables. Run one process per card;
running both cards in parallel is fine.

## 7. File index (`tests/movement/dram_patterns/`)

| File | Purpose |
|---|---|
| `dramx.py` | Core harness: endpoint formula `ep(bank, port)`, per-stream plans, timing |
| `exp1_ports.py` | E1 per-controller / per-port survey |
| `exp2_chip.py` | E2 first full-chip NoC/port matrix (superseded by exp3) |
| `exp3.py` | General full-chip patterns: per-slot NoC, ports, banks, VC, priority, page |
| `cores140.py`, `run140.py`, `run140sr.py` | Append the 20 extra tiles on 140-core cards |
| `phase.py` | E6 time-phased read-then-write |
| `noc2.py` | Fork of `tests/movement/noc.py` adding `dram_stride` |
| `rot.py` | E7/E8 unsynchronized rotate / mixed / static schedules |
| `sync.py` | E9/E10 wall-clock-paced flip / static |
| `syncrot.py` | E11–E13 paced rotation for any ratio, static, interleaved |
| `validate.py` | Byte-level check of the segregated pattern |
| `clockcheck.py`, `wallclock.py` | Device timebase vs host clock; host read of the wall clock |
| `cases/*.json` | Exact case lists used |
| `results/*.json` | Raw results (see the section headers above for the mapping) |
