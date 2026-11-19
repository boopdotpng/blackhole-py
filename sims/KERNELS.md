# Llama 3 kernels on the card: ground truth for the simulator (card 1, p150, 2026-11-18)

The simulator's target: predict these numbers within 3%. Probe `sims/probes/kernels.py`, data
`sims/results/2026-11-18-kernels-{1b,8b-bf16,8b-fp8}-card1.jsonl`.

Every EXEC carries the dispatcher's profile pair: its wall clock when it starts the EXEC (before it fetches and installs
the code) and when the last core's done-increment has arrived. Cycles are dispatcher-tile AICLK (1.35 GHz), so start
and end come from the same clock and need no tile offset (`clocks.md`).

**The exact bytes that ran are kept next to each result:** `sims/results/2026-11-18-kernels-<model>-card1/<kernel>/`
holds `{brisc,ncrisc,trisc0,trisc1,trisc2}.bin` (what was multicast to the workers, after any relink at install),
`manifest.json`, `listing.json` (ttrv's annotated listing per role) and `args0.bin` (layer 0's argument block). A
simulator can run exactly those images and compare with the spans below.

## Record kinds

| kind | what | fields |
|---|---|---|
| `kernel` | one per distinct kernel | `grid` (cores), `image_bytes` per role, `sha` |
| `step` | the whole decode step queued as plain EXECs (same order and prefetch as the graph replay), at positions 0, 127, 1023, 4095, 5 reps each | per EXEC `start`, `end` (relative to the first start), `span` = end - start, `total` |
| `graph` | the same step through the graph CALL that `examples/llama3.py` runs, stamped around it | `total` |
| `single` | layer 0's launch alone (EXEC, signal, wait), 6 runs (first is warm-up) at position 1023 | `spans`, `median` |
| `b2b` | the same launch queued 16 times back to back | `starts`, `ends`, `period` (median end-to-end) |

`span` covers code fetch and multicast as well as the run. In a step the next EXEC's code is fetched and multicast
while the current one runs, so the gap between one EXEC's end and the next one's start is the fixed **154 cycles**
(139-168; a few outliers up to ~4200 in the 8B runs). `single` has no overlap; `b2b` overlaps like a step.

## Results at position 0 (median over 5 reps; "share" = sum over layers / step total)

### llama3-1b (16 layers): step 8,545,652 cycles (6.33 ms), rep spread 0.08%; graph CALL 8,529,563

| kernel | grid | span | share | spread of one launch over 5 reps | spread across layers | single (pos 1023) | b2b period |
|---|---|---|---|---|---|---|---|
| embedding | 1 | 6,413 | 0.1% | 11.8% | 0.0% | 4,966 | 3,509 |
| qkv | 88 | 51,630 | 9.7% | 3.4% | 2.1% | 54,814 | 51,581 |
| attention | 64 | 44,223 | 8.3% | 0.5% | 0.3% | 59,562 | 56,362 |
| o | 88 | 34,968 | 6.6% | 3.3% | 2.6% | 37,434 | 34,730 |
| gate | 88 | 196,012 | 36.7% | 1.4% | 0.8% | 199,157 | 195,990 |
| down | 88 | 112,536 | 21.1% | 1.2% | 0.7% | 115,262 | 112,633 |
| lm | 88 | 1,481,131 | 17.3% | 0.2% | 0.0% | 1,477,156 | 1,474,133 |
| argmax | 88 | 8,492 | 0.1% | 1.6% | 0.0% | 11,299 | 8,647 |

### llama3-8b-bf16 (32 layers): step 45,982,879 (34.1 ms), rep spread 0.16%; graph 45,927,101

| kernel | grid | span | share | one launch, 5 reps | across layers | single | b2b |
|---|---|---|---|---|---|---|---|
| embedding | 1 | 6,503 | 0.0% | 10.5% | 0.0% | 5,466 | 3,508 |
| qkv | 88 | 159,644 | 11.1% | 1.5% | 1.1% | 162,421 | 160,192 |
| attention | 64 | 83,823 | 5.8% | 0.4% | 0.2% | 106,720 | 103,145 |
| o | 88 | 106,838 | 7.4% | 1.5% | 3.2% | 109,668 | 106,636 |
| gate | 88 | 647,724 | 45.0% | 1.2% | 0.8% | 650,519 | 648,506 |
| down | 88 | 346,848 | 24.1% | 1.0% | 0.6% | 347,615 | 346,977 |
| lm | 88 | 2,911,793 | 6.3% | 0.1% | 0.0% | 2,905,922 | 2,902,669 |
| argmax | 88 | 8,499 | 0.0% | 0.5% | 0.0% | 11,459 | 8,747 |

### llama3-8b-fp8 (32 layers): step 35,472,874 (26.3 ms), rep spread 0.01%; graph 35,439,513

| kernel | grid | span | share | one launch, 5 reps | across layers | single | b2b |
|---|---|---|---|---|---|---|---|
| embedding | 1 | 6,598 | 0.0% | 9.1% | 0.0% | 5,550 | 3,508 |
| qkv | 96 | 147,776 | 13.3% | 1.7% | 2.1% | 151,116 | 148,011 |
| attention | 64 | 83,798 | 7.6% | 0.3% | 0.2% | 105,913 | 102,757 |
| o | 88 | 103,862 | 9.4% | 0.8% | 3.3% | 106,892 | 104,058 |
| gate | 96 | 339,443 | 30.6% | 1.0% | 1.1% | 341,803 | 338,429 |
| down | 88 | 344,577 | 31.1% | 0.5% | 0.2% | 347,236 | 344,534 |
| lm | 96 | 2,794,208 | 7.9% | 0.2% | 0.0% | 2,798,864 | 2,794,763 |
| argmax | 96 | 8,687 | 0.0% | 0.5% | 0.0% | 11,697 | 8,892 |

### Attention and step total by position (median)

| position | 1b attention | 1b step | 8b-bf16 attention | 8b-bf16 step | 8b-fp8 attention | 8b-fp8 step |
|---|---|---|---|---|---|---|
| 0 | 44,223 | 8,545,652 | 83,823 | 45,982,879 | 83,798 | 35,472,874 |
| 127 | 47,574 | 8,597,314 | 88,418 | 46,118,781 | 88,335 | 35,623,157 |
| 1023 | 56,313 | 8,739,275 | 103,262 | 46,579,470 | 103,092 | 36,075,516 |
| 4095 | 76,372 | 9,059,145 | 147,352 | 48,020,996 | 138,310 | 37,211,089 |

## What this means for the 3% target

- **A whole step repeats within 0.01-0.16%.** Single launches of the DRAM-bound kernels (qkv, o, gate, down) vary
  1-3.4% from run to run, and identical launches in different layers differ by up to 3.3%. That is the DRAM refresh
  phase and arbitration (`noc_findings.md`). For short kernels the 3% has to be measured against the median of
  several runs, not one run.
- `embedding` (1 core, ~5k cycles) varies by ~10%. It is 0.1% of a step.
- **gate + down + lm take 65-75% of the step and are DRAM-bandwidth bound.** For example 1b `lm` streams
  128256 x 2048 bf16 = 525 MB in 1.48M cycles = 355 B/c, the 88-core NoC0 ceiling measured in `noc_findings.md`.
  So getting the step within 3% depends first on the DRAM/NoC model, then on the compute pipeline.
- Dispatch is about 3.5k cycles per launch back to back (`embedding` b2b period 3,508 for a 1-core kernel), or about
  5k alone. That fits `noc_findings.md` (Dispatch).

## Not covered

- **Per-core and per-RISC times.** The stamps give each launch's span on the dispatcher only. Breaking a span down by
  core needs the kernels to log their own start and end (a ttrv build option), which would show the 4x core-to-core
  unfairness directly.
- Card 0 and other cards; only card 1 was used.
- Prefill: the kernels only implement decode.
