# NoC, DRAM and dispatch: measured on card 1 (p150, 14 columns), 2026-11-18

Raw data: `sims/results/2026-11-18-{noc-events,ping,traffic,issue,launch}-card1.jsonl`. Probes: `sims/probes/`
(`run.py <probe>`). All cycles are the tile wall clock (AICLK, 1.35 GHz). Timing resolution is about 5–10 cycles:
one bounded poll of an NIU register takes that long.

Scope: only what the Llama 3 kernels use (see `goals.md`). They use BRISC reads on NoC0 (2–4 KiB DRAM pages,
interleaved over 8 banks through a per-core port), NCRISC non-posted writes on NoC1, non-posted atomics
(attention), one host write (argmax), one command buffer, one transaction id, VC static 1. Dispatch multicasts
programs and GO.

## Clocks
- **Tile wall clocks are not synchronized.** Offset relative to (1,2) depends on the column, in steps of about
  140 cycles: x = 1,2,16 → 0; 3,14,15 → −148; 4,5,12,13 → −288; 6,7,11 → −420; 10 → −552 (a few edge tiles
  take the neighbouring level). One-way latencies corrected by these offsets match 32 + 9 × hops, so the offsets are
  real. Anything comparing timestamps across tiles (kperf traces) must correct for them. Full table, method and
  caveats: `clocks.md`.

## Issue (RISC → command buffer)
- The command rate is RISC-loop bound. Per command: ~41 cycles for a bare loop (ready poll, clock read, CMD_CTRL
  store); +7 to rewrite address and coordinate; with a fence on each side, 49 (bare) / 59 (with the rewrite).
  This is the same for every op and size.
- The original timed polling loop measured 22 cycles fenced and 32 unfenced. A single status load on card 0
  resolved the command-buffer acceptance interval. After the strobe, loads issued one through four instructions
  later see busy. The fifth sees ready. A fence before the load also suffices.
  [Single-read probe results](results/2026-11-19-cmd-accept-card0.jsonl.gz)
- **More command buffers don't help.** 2 or 4 buffers on one NoC give exactly the 1-buffer rate, because the RISC
  is the limit. With large packets they share the NIU's injection (16 KiB posted: 1 buffer 59.8 B/c, 2 buffers 59.1 total).
- **Separate NoCs and separate RISCs do help.** One RISC using both NoCs: 120 B/c (2 × 60). BRISC on NoC0 and
  NCRISC on NoC1 each run at their full single-RISC rate, so reads and writes don't interfere at the tile.
- NIU injection: ~61 B/c per NoC (posted 16 KiB stream).

## Tile ↔ tile
- One-way write: 32 + 9 × hops (unidirectional torus: x ring 17, y ring 12; NoC0 right/down, NoC1 left/up).
- Ack and read response come back the rest of the way around the ring, so the round trip depends only on
  which dimensions differ: y only 12 hops, x only 17, both 29. 64 B round trip: 159 / 199 / 309, about
  49 + 9 × ring hops. Each extra 64 B flit adds about 1 cycle; ack and read response behave the same.
- "Sent" counters: 20 cycles up to 256 B, then about +1 per flit. A read request counts as sent after 20 cycles.
- Non-posted atomic increment round trip = read round trip + 12 (211 vs 199 at 1 x hop). Atomic visibility at the target
  (posted or non-posted) equals the inline-write one-way latency.

## DRAM (endpoints x = 17,18, y = 12–23; 3 ports per bank)
- **Latency doesn't depend on the endpoint or the NoC.** From a worker every DRAM endpoint differs in both x and y,
  so the round trip is always the full 29-hop ring.
  - Read: 429 (64 B), 439 (256), 459–469 (1 KiB), 479–489 (2 KiB), 529 (4 KiB), 789 (16 KiB). That is the tile round trip
    plus ~120, then ~1.4 cycles per extra flit.
  - Non-posted write ack: 319 (64 B) … 359 (2 KiB), 389 (4 KiB), 609 (16 KiB). That is the tile round trip plus ~10:
    the controller acks writes early.
- **DRAM refresh stalls reads.** Every **2497.5 cycles (1850 ns, matching the GDDR6 refresh interval)** a window
  of ~120–150 cycles (~100 ns) blocks reads. A read that reaches the controller inside the window waits for it to
  end: +140–150 at the window's start, tapering to +50 near its end. Writes are never delayed (acked before they
  reach DRAM).
  - The phase is perfectly regular (phase concentration 1.000 over 3800 reads). Banks 0 and 4 have the same period;
    whether all channels share one phase is not measured yet.
  - At a random arrival time a read has a ~5% chance of being caught (the multi-bank pattern measured 4.4–5.3%). The
    "every 5th read" and "13%" seen earlier were the probes' read spacing aliasing against the period (5 × 499 ≈ 2497).
  - Under a deep stream (2 KiB pages over 8 banks, uncapped) refresh barely shows: about 16 response gaps over
    200 cycles in 270k cycles (~1%). The controller hides most of it behind the other banks' queued work.
  - Model: per channel, reads blocked during [phase + k × 2497.5, + ~150); a blocked read completes at the window's
    end + its normal latency. Data: `results/2026-11-18-dram-outliers-card1.jsonl` (dtrace, dseq, dchain).
- One core, one stream: bandwidth ≈ min(outstanding × size / latency, issue rate, ~60). Eight outstanding requests
  saturate one core for pages ≥ 4 KiB. With the lean loop (72 cycles per command), uncapped: 2 KiB 27 B/c, 4 KiB 54,
  8 KiB 60. All 3 ports and both NoCs give the same.
- **Many cores, reads on NoC0 (llama's pattern, 2 KiB pages, port = i % 3):** 1→29, 6→173, 12→284, 24→320,
  44→335, 88→350 B/c (4 KiB pages: 352). It saturates at about **350 B/c**.
  - **Unfair:** at 88 cores the fastest core finishes in 65k cycles and the slowest in 264k (4×).
- **Reads on NoC1 are far worse:** 12 cores 80 B/c, 44 → 140, 88 → 163. Splitting cores between the NoCs gives 276.
  **Cause (tested, `routes.py`): link contention from dimension order, not hop count.** NoC1 routes y first (it
  mirrors NoC0's x-then-y), so read responses climb north *inside the DRAM column* (physical x = 0 for banks 0–3,
  x = 9 for banks 4–7) before turning toward their cores, and share those few vertical links. NoC0 sends them east
  along each endpoint's own row first, so they spread out.
  - Direct test: 4 cores each read their own bank in the x = 0 column. With each core in its endpoint's row: NoC0
    176 B/c, NoC1 177. With all 4 cores in row 2: NoC0 176, **NoC1 63** (one link's capacity: 4 MiB in 66.8k cycles).
    The same-row NoC1 case has far more data hops (~15 to reach x = 2, against 2 on NoC0) and still runs at full speed.
  - Link-load model (61 B/c × cores ÷ busiest link) for llama's 88-core pattern: NoC1 81 / 153 / 194 predicted, 80 / 140 /
    163 measured; busiest link (0,10)→(0,9), carrying 27.6 cores' worth at 88 cores.
  - NoC1 *writes* go north up the core's own column, then west along a DRAM row, so they spread out (338 B/c).
  - For llama, `down` puts 40 cores' reads on NoC1, which runs straight into this. Keeping all weight reads on NoC0
    should be faster (88 cores: NoC0 350 B/c, split 276).
- **Routing and links (tested, 12 tile-to-tile flow pairs chosen so the alternative ordering predicts the opposite):**
  NoC0 is x-first (+x, then +y), NoC1 is y-first (−y, then −x); every pair matched. A link carries **~63 B/c**. Two flows
  on one link split it 50/50 (31.5 each); without a shared link each gets ~60. How more flows share a link: see
  Arbitration.
- **The NoC0 ceiling (~350 B/c at 88 cores) is the DRAM banks**: 8 banks at ~44 B/c each under llama's 88-stream
  load, against ~47 for a clean stream. Bank model below.
  - Physical DRAM positions come from tt-umd's soc descriptor (`blackhole_140_arch.yaml`) and
    `BlackholeCoordinateManager::map_dram_banks`: translated y = 12 + 3 × (bank % 4) + port.
  - For the simulator, a hop-count formula misses all of this. Route each flow over real links in the correct order
    with ~63 B/c per link, and model each DRAM bank as in the bank model below.
- Writes on NoC1 (88 cores): 338 B/c, also unfair (72k–273k).
  - Reads plus writes at 8:1: total 319, reads 283.

## DRAM bank model (`bank.py`, bank 0, readers placed so no NoC link limits; `results/2026-11-18-bank-card1.jsonl`)
- **Data rate: ~47.3 B/c per bank, reads or writes** (sequential, one stream: read 47.2, write 47.4). That is about
  the raw GDDR6 rate, if the p150 is 512 GB/s over 8 banks (64 GB/s = 47.4 B/c at 1.35 GHz; spec value from memory,
  not checked). Refresh costs a streaming read essentially nothing: the controller works around it, and it only
  shows on isolated single reads (above).
  - Correction: the earlier "one bank ≈ 44 B/c" came from a probe bug that read each address 8 times in a row.
- **Request floor: ~18 cycles per request** (12 readers, staggered addresses: 256 B 18.2, 512 B 19.6, 1 KiB 23.4,
  2 KiB 45.3 cycles). So time per request ≈ max(~18, size / 47.4). Small reads (attention's 128 B–1 KiB) are
  request-bound below about 850 B.
- **Aligned concurrent streams conflict.** 12 streams whose start addresses differ by multiples of 2 MiB: 33 cycles
  per small request, and 2 KiB reads drop to 38.5 B/c. The same streams with starts offset by an odd multiple of
  256 B: 18 cycles, 45.2 B/c. A 64 KiB stride costs 14% (40.3 vs 47); 4–16 KiB and scattered (0x51000) strides cost
  nothing. This is DRAM internal-bank/row conflicts driven by address bits, so where llama's per-core weight slices
  start matters.
- **More independent streams cost a little:** 1→47.0, 2→46.3, 3→45.4, 4→45.6 B/c (separate 8 MiB windows). With
  the same 2 or 4 streams interleaved in one window: 47.2–47.3. Llama's 88 streams per bank: ~44.
- **Reads and writes on one bank:** both unthrottled (≈1:1), 43.3 B/c total (−8%, read/write turnaround); about
  2:1 read-heavy, 44.7 (−5%). An unthrottled pair splits the bank about evenly (22 read / 21 write).
- **Ports don't add bandwidth:** the bank is the unit. 3 readers through 3 ports: 42.6, against 45.4 through one.
- **Shares between readers of one bank are unequal and set by topology:** 4 readers in a row got 11.4 / 11.4 / 14 /
  18.4 B/c, and 4 writers 23.5 / 15.7 / 11.8 / 11.7. The share depends on where request streams merge on the way to
  the endpoint (same effect as the link merging above).
- **Refresh is staggered per bank, at fixed offsets** (`phase` cases, 8 banks read at once, tile clocks corrected).
  All banks share one period (2497.5 cycles), so they run off one timer. The absolute phase changes from run to run;
  the offsets between banks don't (two runs agree to ~3 cycles). Relative to bank 0: bank 1 +942, 2 +2267, 3 +659,
  4 +485, 5 +291, 6 +694, 7 +87 cycles. The banks are never all refreshing at once.
- **Which addresses conflict** (`align` cases: 12 small-read streams on one bank, starts 2^k apart): no conflict at
  offsets of 256 B–8 KiB (~17.4 cycles per request); slight at 16–32 KiB (18.5–19); partial at 64 KiB (24); full
  from 128 KiB up (33). So streams whose addresses agree in bits 0–16 land on the same DRAM internal bank in different
  rows. That fits GDDR6's 16 internal banks being selected by about bits 13–16, with the row above bit 16; the exact
  mapping (including any XOR hashing) isn't pinned down. Practical rule: concurrent streams a multiple of 128 KiB
  apart conflict. The 88-core test gave each core a 1 MiB-aligned region, exactly that case, which probably
  explains part of llama's ~44 vs 47.
- Simulator model per bank: a server at ~47.3 B/c with an ~18-cycle minimum per request; + ~8% when reads and writes
  interleave about evenly; extra time per request when concurrent streams' addresses align (up to ~33 cycles
  minimum); refresh window every 2497.5 cycles that only delays a request arriving inside it when the bank has no
  other work.

## Arbitration (`arb.py`, posted tile-to-tile writes, concurrent rates sampled by each source's NCRISC; `results/2026-11-18-arb2-card1.jsonl`)
- **Rule: each router output alternates whole packets among its input ports that have a packet waiting.**
  Inputs are local injection and the neighbouring routers. It is round-robin per input port, not per flow and not
  per flit, and it is work-conserving. Merges nest: a flow's share is a product of ½s (or ⅓s at a 3-input merge)
  along its path, weighted by packet size.
- Chain of N sources joining one row (NoC0 and NoC1 alike): 2 → 30.2 / 30.2; 4 → 30.5 / 15.3 / 7.6 / 7.6 B/c
  (½ / ¼ / ⅛ / ⅛, the source joining last getting the most).
- Three-way merge into one link (turning from x, straight through in y, local): 20.3 each (⅓).
- Packet size counts: 16 KiB packets against 4 KiB on one link → 48.1 / 12.0 (4 : 1). Equal packet turns, so bytes
  follow packet size.
- One 512 B-packet source upstream of three 8 KiB sources: measured 0.54 / 8.58 / 17.1 / 34.1, predicted by the rule
  0.53 / 8.55 / 17.1 / 34.2. Small-packet traffic merging with big-packet traffic is nearly starved.
- This is also why shares are unequal at a shared DRAM bank (requests and responses merge the same way) and why llama's
  88 cores finish up to 4× apart. A simulator must model packets and per-port round-robin at every router;
  per-flow fair sharing would get per-core times badly wrong.

## Host (PCIe; card 1's link is gen3 x1, so these numbers are specific to this card)
- Non-posted write ack: 399 (16–64 B), 1804 (2 KiB), 5054 (4 KiB): limited by the x1 link. Read: ~2049 + size.

## L1 contention
- A DRAM read stream into L1 (53 B/c) is unchanged while the other RISC hammers the same L1 with loads or stores.
  Seen from NCRISC: ~5.7 cycles per load, ~3 per store, loop included.
- Contention from the unpacker or packer, and its effect on RISC loads: measured since (see Still open, item 2).

## Dispatch (one EXEC through fw/dispatch.c, do-nothing kernels)
- Launch to launch (period): 1 core, no code 1559; 88 cores no code 1903; 88 cores × 5 roles × 1 KiB 2265;
  × 4 KiB 3155; 138 cores × 4 KiB 3349.
  - The EXEC span (start → all done) is the period minus ~150.
- Roughly: ~1550 + ~4 per core + program bytes over the multicast. The next program's install overlaps the current
  launch.

## Still open, for llama only
1. The exact DRAM address mapping (bit-level, including any hashing), only needed if llama's slice starts fall
   between the measured cases.
2. ~~Unpacker/packer L1 contention with NoC traffic~~ **done** (card 1, 2026-11-18). NoC traffic into or out of a
   tile's L1 slows that tile's unpacker by up to ~1.9x on raw streams (`probes/UNPACK.md`, contention group) and its
   packer by up to ~20% (`probes/PACK.md`, contend group). The ttrv `move` lowering hardly changes (563 → 568-579 per
   tile), because it is RISC-bound. RISC loads and instruction fetch are not slowed (≤ 2%, `probes/RISCSYNC.md`).
