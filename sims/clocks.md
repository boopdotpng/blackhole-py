# Tile wall clocks are not synchronized

Every Tensix tile has its own wall clock (`WALL_CLOCK_L` at `0xFFB121F0`, AICLK cycles). **The clocks on different
tiles do not read the same value at the same instant.** Each tile is offset by a fixed amount of up to ~550 cycles.
The offset depends mostly on the tile's column.

What this means for anyone writing a simulator or comparing timestamps:

- **Timestamps from one tile** (time between two events on that tile) are exact. No correction is needed.
- **Timestamps from different tiles** (one-way NoC latency, a kperf trace across cores, "who started first",
  synchronized starts) are wrong by up to ~550 cycles unless each tile's offset is subtracted first.
- **A simulator** that keeps one global clock must add the offset to the values it returns for a tile's
  `WALL_CLOCK_L`. Otherwise kernels that read the clock, and traces compared against hardware traces, disagree with
  the card.

## Measured offsets (card 1, p150, 14 columns, 2026-11-18)

`clock(tile) − clock((1,2))`, in cycles. NoC coordinates as the host and `NOC_ID_LOGICAL` see them; x = 8, 9 are
not Tensix columns.

| y \ x | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 0 | 0 | -148 | -148 | -288 | -420 | -420 | -552 | -420 | -288 | -288 | -148 | 0 | 0 |
| 3 | 0 | 0 | -148 | -148 | -288 | -420 | -420 | -552 | -420 | -288 | -288 | -148 | -148 | 0 |
| 4 | 0 | 0 | -148 | -288 | -288 | -420 | -420 | -552 | -420 | -288 | -288 | -148 | -148 | 0 |
| 5 | 0 | 0 | -148 | -288 | -288 | -420 | -420 | -552 | -420 | -420 | -288 | -148 | -148 | 0 |
| 6 | 0 | 0 | -148 | -288 | -288 | -420 | -552 | -552 | -420 | -420 | -288 | -148 | -148 | 0 |
| 7 | 0 | 0 | -148 | -288 | -288 | -420 | -552 | -552 | -420 | -420 | -288 | -148 | -148 | 0 |
| 8 | 0 | 0 | -148 | -288 | -288 | -420 | -420 | -552 | -420 | -420 | -288 | -148 | -148 | 0 |
| 9 | 0 | 0 | -148 | -288 | -288 | -420 | -420 | -552 | -420 | -288 | -288 | -148 | -148 | 0 |
| 10 | 0 | 0 | -148 | -148 | -288 | -420 | -420 | -552 | -420 | -288 | -288 | -148 | -148 | 0 |
| 11 | 0 | 0 | -148 | -148 | -288 | -420 | -420 | -552 | -420 | -288 | -288 | -148 | 0 | 0 |

- **Levels.** There are five: 0, −148, −288, −420, −552, about 140 cycles apart. The edge columns are at 0 and
  x = 10 is lowest, so the pattern looks like the clocks being started column by column from both edges towards
  the middle. Edge rows at x = 4, 7, 12 and 15 sometimes take the neighbouring level, so a per-column constant is
  close but not exact. Use the per-tile table.
- **Precision.** Within ±0.5 cycle of the levels above: repeated pairs agree to 0.25–0.5 cycles.
- **The offsets survive a card reset** (card 1, 2026-11-18: `smi.py -r 1`, then remeasured). Over all 140 tiles the
  largest change was 1.25 cycles (mean +0.03), no more than the scatter between two runs without a reset (1.0).
  Data: `results/2026-11-18-clockmap-{prereset,postreset}-card1.jsonl`.
- **Not yet known:** whether they survive a full power cycle, and whether other cards (card 0, other p150s, p100)
  have the same offsets. Until someone checks, measure them on the card in use.

## How it was measured

`sims/probes/ping.py` (kernel `k_ping.c`): tile A sends an inline 4-byte write of its own clock to tile B on NoC0,
and B logs its clock when the word lands. Then B sends to A on NoC1. NoC1 runs in the mirror direction of NoC0, so
the two paths have the same hop counts and the same latency (32 + 9 × hops), and:

```
d_ab   = t_seen(B clock) − t_fire(A clock)   (NoC0, A → B)
d_ba   = t_seen(A clock) − t_fire(B clock)   (NoC1, B → A)
offset = clock(B) − clock(A) = (d_ab − d_ba) / 2
one-way latency              = (d_ab + d_ba) / 2
```

Medians of 30 pings each way. The one-way latencies this gives match the 32 + 9 × hops model to about a cycle,
which is the check that the offsets are real and not a routing asymmetry.

Rerun on the card in use (needs nothing else running on it, about 0.1 s):

```
python3 sims/probes/run.py --device N --output sims/results/<date>-ping-cardN.jsonl ping -k clockmap
```

In probe code, `ping.offset(card, tile)` measures and caches one tile's offset for a session.
`traffic.py` uses it to start many tiles at the same instant: start skew was ≤ 10 cycles across 88 tiles.
