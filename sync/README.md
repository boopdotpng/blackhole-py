# Synchronization in the Llama 3 decode kernels

Scope: the exported kernels in `blackhole-py/kernels/llama3-*` and the generator that produced them
(`blackhole-py-old/ttko/{sync,unpack,fpu,sfpu,pack,cb}.py`, `blackhole-py-old/examples/llama3/kernels.py`).
The two repos have the same sync behaviour: `blackhole-py` runs the images `blackhole-py-old` generated.

Measurements: p150a cards 0 and 1, 2026-11-13, 24 decode tokens after the reference prompt, device clock, `--profile`
per-launch timestamps. Hardware facts cite `tt-isa-documentation/BlackholeA0` (BH) and `WormholeB0` (WH).

Files:
- `census.py` counts every sync site per kernel and RISC, with loop depth (`python sync/census.py [model kernel]`).
  The output is in `census.json`.
- `ablate.py` patches exported `.bin` images in place (same-size words, so no pc moves) and runs the real decode
  (`--model --variant --device`). Variants can be combined with `+`.
- `summarize.py` builds `results.md` from `results/*.json`.

## TL;DR

1. **Per-tile syncs are not where the time goes.**
   - The decode projections stream at 93–99% of achievable DRAM bandwidth in their steady state.
   - Removing the two per-tile syncs (TRISC0's drain and TRISC1's FPU/SFPU barrier) changes real decode time by 0.0%
     on all three models.
   - Removing them in a compute-only run (no DRAM traffic) speeds the pipeline up by 0–5%.
2. **The cost is in latency chains, about 12–16 µs per projection launch and about 48 µs per attention+merge.**
   - These are serial chains: launch, DRAM latency, the RMSNorm/FP8 prologue, pack→L1→unpack handoffs, the
     epilogue, the scatter writes, and the end-of-launch barrier.
   - Together they are 3.9 ms of 19.8 ms per token on 8B FP8 (20%), 3.7 of 33.4 ms on 8B BF16 (11%) and 1.4 of
     6.3 ms on 1B (22%). This is the real target.
3. **The compute-only ceiling is about 75% of DRAM time for FP8,** roughly 180–195 cycles per weight tile.
   - It is set by TRISC0's RISC-V bookkeeping: 86 RISC-V instructions per tile, 18 of them MMIO.
   - It is not set by Tensix syncs or by FPU/SFPU work: removing *all* SFPU reduce work saves 7%.
   - This headroom is small, so any delay in starting the weight stream turns into tail time. That is why `down` is
     28 µs over its streaming bound.
4. **One sync protocol is broken but harmless.**
   - TRISC0's UNPACK_SYNC semaphore protocol does nothing: its SEMGET is not ordered after the unpack, because the
     STALLWAIT before it blocks only B3 and not B1.
   - The per-tile PC_BUF_SYNC drain is what actually provides safety.
   - Adding B1 to that STALLWAIT makes the semaphore protocol correct and the drain redundant
     (`t0semfix`: 24/24 tokens on all models). Removing the drain without that fix gives wrong tokens (`t0nodrain`: 0/24).
5. **Dst runs full-sync, not half-sync.** Firmware initializes MATH_PACK with max 1 (`fw/hw.h:65,84`). Half-sync
   would not shorten any measured critical path here. The long paths are true data dependencies through L1, such as
   P in attention and the normalized x, which a Dst split cannot overlap.

## 1. How many syncs

### Static census (8B FP8; all models in `census.json`)

Each instruction that waits on or signals another agent counts once. A polling loop counts once.

| kernel | brisc | ncrisc | trisc0 (Tensix + RISC) | trisc1 | trisc2 |
|---|---:|---:|---:|---:|---:|
| qkv | 22 | 17 | 24 + 25 | 87 + 6 | 12 + 12 |
| attention | 19 | 19 | 28 + 50 | 84 + 6 | 17 + 18 |
| attention_merge | 13 | 11 | 8 + 7 | 73 + 2 | 6 + 6 |
| o | 16 | 16 | 24 + 29 | 35 + 5 | 18 + 18 |
| gate | 19 | 19 | 40 + 39 | 100 + 7 | 18 + 18 |
| down | 16 | 16 | 24 + 29 | 35 + 5 | 18 + 18 |
| lm | 16 | 11 | 24 + 25 | 59 + 5 | 12 + 12 |
| argmax | 30 | – | 16 + 12 | 19 + 0 | 6 + 6 |

Most static sites are in setup paths. What matters is what runs per tile and per row.

### Dynamic: the projection GEMV hot path

`gate`, `qkv`, `o`, `down` and `lm` share one structure. For each row and each of its 1024-element weight tiles:
TRISC0 unpacks the weight to SrcA and x to SrcB, TRISC1 runs ELWMUL into Dst tile 0, and the SFPU sums the products
into 32 lane accumulators. Per row, the SFPU reduces to one scalar, TRISC2 packs it and NCRISC places it.

| where | per **tile** | per **row** |
|---|---|---|
| TRISC0, Tensix | STALLWAIT[UNPACK←SRCA_CLR\|SRCB_CLR], STALLWAIT[UNPACK←TRISC_CFG], STALLWAIT[UNPACK←UNPACK0\|1], SEMGET[UNPACK_SYNC] | |
| TRISC0, RISC | 2× UNPACK_SYNC poll, 1 UNPACK_SYNC post, CB wait_front poll, **PC_BUF_SYNC drain**, CB ack store, 2 fences | |
| TRISC1 | STALLWAIT[MATH←SRCA_VLD\|SRCB_VLD], STALLWAIT[SFPU←MATH], STALLWAIT[SYNC←MATH\|SFPU] (+4 ZEROACC) | SEMWAIT[MATH_PACK], STALLWAIT[SYNC←MATH\|SFPU], SEMPOST[MATH_PACK] |
| TRISC2 | | SEMWAIT[MATH_PACK], 3× STALLWAIT (CFG/PACK), **PC_BUF_SYNC drain**, ZEROACC, SEMGET, CB reserve poll + publish |
| BRISC | | CB reserve poll, tid-idle waits ×2, read barrier (wait for every read of the row), 3 NoC polls per 2 KB page, CB publish |
| NCRISC | | CB wait poll, CB pop |

**Totals for 8B FP8.** Per core per layer that is about 2,200 tiles and 450 rows, roughly 19k Tensix sync
instructions plus about 15k RISC-side sync operations. Across 96 cores × 32 layers plus the LM head, that is about
**60M Tensix sync instructions per token**, about 650k per core.

**What one costs.** An already-satisfied STALLWAIT or SEMWAIT costs one cycle plus a one-cycle release lag
(BH/STALLWAIT.md:30). The Sync Unit issues one per cycle across all threads (BH/SyncUnit.md:65). Since these are spread
over three threads that overlap each other, the measured cost below is the only reliable number.

## 2. How much time is spent syncing (measured)

`results.md` has every run. Achievable streaming is taken as 506 GB/s, the rate measured by `lm`, a single launch
that reads the 1.05 GB BF16 LM head.

### 8B FP8, µs per launch

| kernel | real | streaming bound | excess | compute only (`nodram`) | compute only, per-tile syncs removed |
|---|---:|---:|---:|---:|---:|
| qkv | 63.3 | 49.7 | +13.6 | 51.9 | 49.9 |
| o | 47.3 | 33.2 | +14.1 | 40.2 | 38.9 |
| gate | 248.3 | 232.1 | +16.2 | 187.2 | 178.2 |
| down | 144.3 | 116.0 | +28.3 | 97.3 | 92.2 |
| attention + merge | 48.5 | ~0 | +48.5 | 48.5 | |

The excess is almost the same for every projection on every model (8B BF16: +13.5/+14.4/+16.8/+21.6; 1B:
+13.3/+12.6/+13.9/+11.6). That makes it a fixed per-launch latency, not a per-tile cost.

### Ablations

| variant | what it removes | real decode | compute-only ceiling | tokens |
|---|---|---|---|---|
| `t0semfix` | TRISC0 per-tile PC_BUF_SYNC drain (with the B1 fix) | 0.0% on all models | −2% (FP8), 0% (BF16, 1B) | 24/24 on all models |
| `t1nosync` | TRISC1 per-tile STALLWAIT[SYNC←MATH\|SFPU] | 0.0% | −0.5% | 24/24 on all models (see note) |
| both | | 0.0% | −5% FP8 gate, 0% BF16 gate | 24/24 |
| `t0nodrain` | the drain alone, semaphore protocol unfixed | 0.0% | −2% | **0/24, wrong** |
| `nodram+t1nosfpu` | probe: every SFPU reduce replay → NOP | | −7% | (garbage) |
| `nobarrier` | probe: BRISC per-row read barrier | **+35% slower** (NoC/DRAM congestion) | 0% | (racy) |
| `t0loose` | drain removed, poll left at "sem < 2" | **hung both cards** (reset with tt-smi) | | |

**Note on `t1nosync`.** It passes, but it relies on the Blackhole Dst half-interlock and in-order issue, which
BH/Dst.md:114 says do "not replace scheduling rules". At 0.5% it is not worth keeping out.

**How to read `nodram`.** The BRISC weight reader issues 64 B per page instead of 2 KB. Every CB, semaphore and
NoC handshake still runs; only the bytes disappear. That isolates the five-RISC pipeline from DRAM. In that mode:
- the per-row read barrier changes nothing (`nodram+nobarrier`);
- SFPU work matters little (−7% for all of it);
- per-tile Tensix syncs matter little (−5%).

What is left is TRISC0's loop of 97 words per tile: 86 RISC-V instructions, 18 MMIO loads/stores, 19 instructions in
three polling loops, and one unpack MOP. That loop costs about 180 cycles per tile.

## 3. The kinds of sync, and whether each is needed

| kind | where it is used | needed? |
|---|---|---|
| **SrcA/SrcB dvalid**: UNPACR SetDatValid → math STALLWAIT[*_VLD]; SETRWC/ELWMUL clear_dvalid → unpacker STALLWAIT[*_CLR] | every unpack/FPU pair | Yes. This is the hardware handshake. The explicit STALLWAITs are partly redundant: math instructions that read Src already wait at the Wait Gate, and UNPACR waits per datum (WH/WaitGate.md:11, MVMUL.md:49). |
| **MATH_PACK semaphore** (SEMWAIT/SEMPOST/SEMGET) | math↔pack ownership of Dst | Yes. It runs full-sync (max 1). |
| **STALLWAIT[SYNC←MATH\|SFPU] before SEMPOST** | math publishing to pack | Yes. Without B1 the post can fire before the math finishes (SEMPOST.md). |
| **STALLWAIT[SFPU←MATH]** | FPU wrote Dst, SFPU reads it | Yes. This is a RAW hazard across units. |
| **STALLWAIT[CFG←…] before WRCFG/RMWCIB/SETC16** | Dst offset, ALU format, packer config | Yes. In-flight consumers read config live (MVMUL.md:101, UNPACR_Regular.md:792). Some sites rewrite an unchanged value; `Fpu._configure_dst` re-RMWs `Fp32_enabled` on every call. Cheap. |
| **STALLWAIT[UNPACK←TRISC_CFG]** | RISC-V MMIO config writes before the unpack MOP | Yes, unless Auto TTSync is enabled (BR/AutoTTSync.md). |
| **PC_BUF_SYNC drain** (RISC waits for its Tensix thread to go idle) | TRISC0 per tile, TRISC2 per row, setup | TRISC0: no, once B1 is fixed (`t0semfix`). TRISC2: yes as written, because the RISC publishes the CB counter after the pack. The Tensix-side `STOREREG` publish in `cb.py` (`tensix_received=True`) removes that need. |
| **PC_BUF_MOP_SYNC** (MOP expander idle) | before every MOP config rewrite | Yes, when a MOP template is rewritten. It is avoidable by keeping templates resident, as the dot loop already does with REPLAY. |
| **UNPACK_SYNC semaphore**: RISC poll + post, Tensix SEMGET | TRISC0 per tile | As written it is broken (above) and redundant with the drain. Fixed, it is the right mechanism, but only worth it with **two config contexts**, so the RISC can write tile n+1's base while tile n unpacks. That is tt-llk's `wait_for_next_context` / `switch_config_context`. The second poll per tile always passes. |
| **CB counters** (RISC polls/stores on the tiles_received/acked registers) | every RISC↔RISC hop | Yes, as the cross-RISC protocol. TRISC0 pops before the unpack has read the tile; this is safe in practice only because the CB is deep (see below). |
| **NoC polls** (cmd-buffer ready, outstanding < 129, tid idle, read barrier) | BRISC/NCRISC | The per-row read barrier looks like a serializer (one row, 4–8 KB, in flight per core). Removing it made decode 35% *slower*, so the throttling is load-bearing. Per-row transaction IDs could keep two rows in flight without flooding the NoC; not tested. |
| **fence** | after every MMIO poll and publish | Mostly yes (BR/AutoTTSync.md:46). A few follow a poll whose value is already consumed. |
| **Launch boundary** (implicit global barrier; 195 launches per token on 8B, 99 on 1B) | between every kernel | Dispatch alone is 1.6 µs per launch, 1.6% of the token. The fill and drain around each boundary are the larger part of the 12–16 µs excess. |

**Is the codegen too liberal?** By instruction count, somewhat: there are redundant polls, a drain that a one-bit fix
removes, config rewrites with unchanged values, and explicit dvalid waits that the hardware already enforces. By
time, no: removing all of the per-tile ones is worth 0% in real decode and at most 5% of the compute ceiling. The
syncs that do cost time sit on the serial chains of each launch. That calls for restructuring, not deleting.

**Note on TRISC0's CB pop.** TRISC0 pops the CB before its unpack has read the tile. This is currently safe only
because BRISC's DRAM round trip (about 1 µs) is longer than an unpack. With `t0semfix` the pop should move after the
next iteration's semaphore poll.

## 4. Granularity: what the hardware allows

From BH/STALLWAIT.md:186-200, BH/SyncUnit.md, WH/SrcASrcB.md, BH/Dst.md and tt-llk.

### SrcA/SrcB

- **The finest handoff is one UNPACR.** Ownership (`AllowedClient`) is per bank, and there are 2 banks of 64×16.
  You can hand over each face (SetDatValid on every face UNPACR, with math clearing per face), but you then get only
  one face of lookahead and one flip per face.
- **There is no row-level or partial-bank valid**, and no way for MVMUL or ELW* to skip the Src wait.

Ways around whole-bank sync:
- **The math thread writes Src itself.** MOVD2A, MOVD2B and MOVB2A do not take part in the dvalid handshake. Ordering
  is program order inside T1, so no cross-thread sync is needed. They must not race an unpacker on the same bank: use
  `STALLWAIT B6+C7` (WH/MOVB2A.md:92, MOVD2A.md:155).
  - This is the way to feed attention's P from Dst into the PV matmul without the pack→L1→unpack round trip, which is
    one of the serial hops in the 40 µs attention.
- **Unpack straight to Dst** (UNPACK_TO_DEST, synchronized by semaphore at any granularity) for operands that only
  the SFPU needs.
  - RMSNorm currently does unpack→SrcA→MOVA2D per tile, with a drain each time.
  - Hazard: unpack-to-Dst and FPU Dst writes share one write port (BH/Dst.md:118).
- **Keep an operand resident instead of re-unpacking it.** Clearing only SrcA (ELWMUL `clear_dvalid=1`) keeps SrcB.
  The GEMV re-unpacks the same x tile into SrcB for every row: half the unpack traffic and one of the two per-tile
  config writes are redundant.

### Dst

- **No hardware Dst dvalid on Blackhole.** It exists on Quasar only (`tt_llk_quasar` `p_cleardvalid`).
- **Hardware interlock** at half granularity: rows 0–511 and 512–1023, one client per access (BH/Dst.md:114).
- **Software sync** through semaphores (4-bit counter; silicon saturates at 15) plus `DEST_TARGET_REG_CFG_MATH_Offset`
  and the packer offset. That can be per tile or per face. Each section switch costs a STALLWAIT plus SETC16/WRCFG, and
  math and pack in the same 512-row half still serialize on the interlock, so finer than half buys little real overlap.
- **Half-sync here:** firmware sets MATH_PACK max = 1 (full sync). Half-sync (max 2, alternating offsets 0/512)
  would let math start row n+1 while pack drains row n's scalar. Math is not the limiter in the projections, so the
  expected gain is small. In attention, RMSNorm and the epilogues the next math depends on the packed data, so half-sync
  cannot overlap those either.

### Thread level

- **STALLWAIT conditions are whole-unit busy bits** ("has an instruction of this thread in flight"). There is no
  per-instruction scoreboard. The Wait Gate holds one latched wait per thread, and nothing passes a blocked
  instruction (BH/STALLWAIT.md:178).
- **RISC side, from coarsest to finest:** PC_BUF_SYNC (full thread drain), then PC_BUF_MOP_SYNC (MOP expander only),
  then semaphore reads (≥3 cycles; "effectively free").

## 5. Bank switching in the decode path

Yes, it happens automatically: two banks each for SrcA and SrcB, and TRISC0 waits for `SRCA_CLR|SRCB_CLR` (its next
bank free), not for math to finish. In the GEMV, though, the lookahead is only one tile, for three reasons:
- TRISC1 is in order and runs FPU then SFPU on the same Dst tile, with `STALLWAIT[SFPU←MATH]` and
  `STALLWAIT[SYNC←MATH|SFPU]` per tile. ELWMUL for tile n+1 therefore cannot run, and release its banks, until the
  SFPU has reduced tile n.
- TRISC0's RISC drained the unpacker on every tile.
- The real limiter is TRISC0's ~180-cycle bookkeeping loop, so the banks are rarely both full.

In attention, Q is kept resident across K tiles (`consume_left=False`), and P is unpacked once per block and kept
resident across the V feature tiles.

## 6. What would actually move the number

Ordered by measured headroom.

1. **Per-launch latency chains** (12–16 µs × 4 projections × layers, plus 48 µs per attention+merge; 11–22% of token
   time).
   - Fewer launches: fused or persistent layers, so weights for launch n+1 stream while launch n finishes.
   - A deeper BF16 weight CB: currently 2 rows, so BRISC stalls almost immediately while the RMSNorm prologue runs.
     FP8 has 16 rows.
   - Prologue without L1 round trips: unpack-to-Dst for x and gamma.
   - In attention: P via MOVD2A/MOVD2B instead of pack→L1→unpack.
2. **TRISC0 per-tile overhead** (the ~180-cycle compute ceiling). A higher ceiling shortens tails after any late
   start: `down` FP8 is +28 µs over streaming against a 97 µs ceiling.
   - Write each unpacker base once per row and let the address counters advance.
   - One MOP per row, not per tile.
   - Keep CB state in registers instead of reloading it from local memory.
   - Keep x resident in SrcB.
   - Two config contexts plus the fixed UNPACK_SYNC protocol, so the RISC runs a tile ahead.
3. **Per-tile sync cleanup** (`t0semfix`, dedupe config RMWs, drop the second semaphore poll). It is correct and free,
   but worth ≤5% of the compute ceiling and 0% of decode today. Do it for hygiene, or as part of item 2.

## 7. Follow-ups: unpacker config contexts and per-row read IDs

### Unpacker config contexts (unused today)

Every TRISC0 unpack runs on config context 0. The FP8 `gate/trisc0.S` hot loop (pc `0x6c0`–`0x744`) does the following
every tile:
- writes the same base address to `THCON_SEC0_REG3_Base_address` and `Base_cntx1_address` (`sw x20,0(x21)` /
  `sw x20,4(x21)`), and the same again for SEC1;
- sets `UNPACK_MISC_CFG_CfgContextOffset_0 = 0`;
- runs UNPACRs with `CfgContextCntInc=0, CfgContextId=0`.

So the RISC can only rewrite the base once the previous unpack is finished. Today the per-tile PC_BUF_SYNC drain
enforces that.

The tt-llk pattern (`wait_for_next_context` / `switch_config_context`):
1. The RISC waits for UNPACK_SYNC < 2.
2. It writes tile n+1's base into the *other* context.
3. It posts UNPACK_SYNC.
4. The UNPACR flips the context (`CfgContextCntInc`).
5. The Tensix SEMGETs after the unpack completes.

We already emit the "< 2" poll, the post and the SEMGET: half the pattern, without the context flip.

To finish it:
- **Alternate contexts:** write `Base_address` or `Base_cntx1_address` by parity, and enable the context increment in
  the MOP's UNPACRs.
- **Order the SEMGET:** add B1 to the STALLWAIT in front of it (`t0semfix`), so it happens after the unpack.
- **Move the CB pop** after the next iteration's poll.

This lets the RISC run one tile ahead. It targets the ~180-cycle-per-tile compute ceiling, not current decode
throughput.

Do not try "< 2" with a single context: that is `t0loose`, which hung both cards.

### Per-row transaction IDs for weight reads (untested)

BRISC issues each weight row under one NoC transaction ID. It waits for that ID's outstanding reads to reach zero
(`NIU+0x244` polls) before `push_back` and before issuing the next row. Each core therefore has exactly one row in
flight: 4 KB for FP8, 8 KB for BF16.

Proposed:
- Put row n on ID `n % K`.
- After issuing row n, wait only for row n−1's ID, then push row n−1.

That keeps K rows in flight with exact completion tracking.

`nobarrier` is not this experiment. It dropped the waits entirely, lost track of completion, let reads pile up
uncapped, and was 35% slower. Gate already streams at about 93%, so the expected gain is mainly in short launches,
where the first rows' latency is exposed.

## Reproduce

```sh
cd blackhole-py
python sync/census.py                                    # static census, all models
python sync/census.py 8b-fp8 gate                        # per-site listing with loop depth
../.venv/bin/python sync/ablate.py --model 8b-fp8 --variant nodram+t0semfix --device 0
../.venv/bin/python sync/summarize.py > sync/results.md
```

`ablate.py` copies the kernel set into `sync/variants/<variant>/` (git-ignorable, about 7 MB per model) and asserts
each patched word against the `.S` listing. `t0loose` hangs the device; recover with `tt-smi -r /dev/tenstorrent/N`.
