# Cycle accuracy — what we know, what we need

Audit of the cycle / latency information available to build a cycle-accurate (≤5%) timing
model for the Blackhole emulator at `blackhole-py/emu/`.

## Status of the emulator today

**No cycle info is modeled.** The only timing state in the code is:

- `device cycle counters` (`device.py:292, 443`) — a free-running integer advanced by one per
  simulator cycle. It is mirrored to `WALL_CLOCK_L/H` MMIO (`device.py:445`) so
  firmware reading the wall clock sees a monotonic value.
- `WaitGate._one_cycle_hold` (`tensix/frontend.py:256-293`) — a 1-bit "pseudo-timer"
  that enforces the ISA-mandated one-cycle post-`STALLWAIT` block.
- `MOPExpander` returns `None` once on expansion end (`tensix/frontend.py:54`) to imitate
  the 1-cycle transition penalty.

Everything else completes synchronously in the same outer step as it was issued.
Instruction FIFO depth (32/thread) and PCBuf depth (16) exist as capacity constants only —
they imply backpressure but carry no cycle cost.

## Timebase recommendation

Keep the existing `device cycle counters` as the single global tick counter (all units already
serialize through `run_until`). Extend each backend unit with a `busy_until: int`
threshold in that same timebase. The per-unit agent reports list the exact hook points.

## The five domain docs

| File | Covers |
|---|---|
| [`control-plane.md`](control-plane.md) | Baby RISC-V cores, Tensix frontend / MOP / Replay, Sync unit, Config unit |
| [`compute-units.md`](compute-units.md) | FPU / Matrix unit + SFPU / Vector unit |
| [`data-path.md`](data-path.md) | Unpacker(s), Packer(s), TDMA / XMOV / Mover / ThCon |
| [`interconnect.md`](interconnect.md) | NoC, DRAM, L1 / streams / CBs / PCBufs / mailboxes, clock domains |
| this file | Executive summary + prioritized microbench list |

Every domain doc has the same two-section structure: **`Cycle info we have`** (quoted ISA
source with `path:line` citations) and **`Needs microbenching`** (what's unknown and how
to measure it).

## Executive summary — what the ISA docs give us

The Tenstorrent ISA docs are **the primary source**
(`tt-isa-documentation/BlackholeA0/` plus `WormholeB0/` as fallback — most of the
Tensix µarch is inherited). They contain:

- **Per-instruction IPC and latency tables** for: Matrix Unit, Vector Unit (SFPU),
  Sync Unit, Configuration Unit. These cover every instruction in those units.
- **Load-latency tiers** for the baby RISC-V cores (2 / ≥3 / ≥4 / ≥7 / ≥8 / ≥12
  cycles depending on address range and cache state).
- **NoC per-hop latency** (~5 cyc NIU↔router, 9 cyc router↔router; 512 b/cycle/link).
- **L1 structure** (16 banks × 128-bit, 5-cycle narrow-write RMW) — documented for WH
  only; BH's `L1.md` is a dead link and says only "more L1 bandwidth."
- **Dst read hazards** (4-cycle blackout per 8×16 block after FPU write).
- **Instruction-FIFO / PCBuf / Mailbox capacities** (32 / 16 / 4 entries).
- **Clock frequencies**: AICLK = 1.35 GHz (Tensix, NoC, baby RV, Ethernet tile most);
  AXICLK = 960 MHz (PCIe NIU crossing); ARCCLK = 800 MHz; REFCLK = 50 MHz.

The ISA docs do **not** give us:

- **Unpacker and Packer end-to-end cycle counts per (instruction × format)** — the
  biggest single gap. Only bandwidth tiers and a 2-cycle setup are published.
- **NoC multi-hop empirical data** — but `tt-metal/tt_metal/impl/experimental/noc_estimator/latencies/noc_latencies.yaml`
  has **390 Blackhole-specific measured entries** across payloads 64 B – 64 KiB and
  access patterns (unicast r/w, mcast, DRAM). This is gold and we should import it.
- **DRAM controller internal latency** (tRCD/tRP/tCL in AICLK cycles) — the BH firmware
  has a binary config blob, no symbolic names.
- **Cross-clock-domain FIFO depths** (PCIe↔AXI, AXI↔AI, L2CPU↔AI).
- **Packer BFP shared-exponent stage cost**, **ThCon L1-limited throughput breakdowns**,
  and **MOP expansion startup latency**.

## Prioritized microbench punch-list

Ranked by how much they move the needle on a 5% cycle-accurate model. Each item cites
the domain doc(s) where the detailed measurement plan lives.

### Tier 1 — blocking, every workload hits these

1. **Unpacker: full (instruction × format) latency table.**
   Issue a single UNPACR of 1 tile for each of {BF16, FP16, FP32, TF32, BFP8, BFP8a,
   BFP4, BFP4a, BFP2, BFP2a, INT8, INT32}, wrap with `STALLWAIT(STALL_UNPACK, 0)` and
   read `WALL_CLOCK_L` deltas. Sweep `Throttle_mode` x1/x2/x4 and compressed vs.
   uncompressed. ([`data-path.md`](data-path.md))

2. **Packer: full (instruction × dest format) latency table.**
   Same pattern for PACR with each target format. Also sweep BFP8/4/2 to measure the
   shared-exponent stage overhead (vs. BF16 at same datum count). Use
   `PACKER_BUSY` and `AVAILABLE_MATH` performance counters. ([`data-path.md`](data-path.md))

3. **Blackhole Matrix Unit clock (absolute cycles/ns).** All published TFLOP/s figures
   are normalized to WH's 1 GHz. Confirm BH runs MVMUL at AICLK = 1.35 GHz by
   running a long MVMUL loop (5 distinct Dst blocks to dodge the 4-cycle hazard) and
   dividing `mcycle` by instruction count. ([`compute-units.md`](compute-units.md))

4. **DRAM read round-trip in AICLK cycles vs. payload size and bank state.**
   Isolate DRAM controller latency from NoC transit using a Tensix tile adjacent to the
   DRAM tile (zero intermediate router hops). Sweep payloads 64 B – 16 KiB and access
   pattern (same bank sequential, bank-switching, random).
   ([`interconnect.md`](interconnect.md))

5. **NoC cross-chip / Ethernet-routed latency.** None of the 390 BH entries in the
   `noc_latencies.yaml` cover inter-chip. Needed for multi-chip emulator fidelity.
   ([`interconnect.md`](interconnect.md))

### Tier 2 — matters for realistic kernel scheduling

6. **Back-to-back FPU dependent-op latency confirmation on BH.** MVMUL → MVMUL
   accumulating onto the same 8×16 Dst block should see the documented 4-cycle stall.
   Also: MOVD2A → MVMUL (2-cycle ‡), MOVD2B / MOVB2D (3-cycle hazard), MOVB2A
   (3-cycle hazard). ([`compute-units.md`](compute-units.md))

7. **SFPU 2-cycle latency auto-stall confirmation.** ISA says SFPMAD / SFPADD / SFPMUL /
   SFPMULI / SFPADDI / SFPLUT / SFPLUTFP32 / SFPMUL24 are 2-cycle latency IPC-1. GCC
   inserts 1 NOP on dependency. Confirm hardware auto-stalls (doesn't silently
   corrupt) on a back-to-back dependent issue. ([`compute-units.md`](compute-units.md))

8. **SEMPOST → SEMWAIT cross-thread propagation cycles.** Not a published number; we
   need T_A SEMPOST timestamp vs. T_B's first post-SEMWAIT instruction timestamp.
   ([`control-plane.md`](control-plane.md))

9. **ATCAS / ATINCGET real latency**, and **ATGETM contention penalty** (docs say "0, 1,
   or 2 extra cycles — maybe"). ([`control-plane.md`](control-plane.md))

10. **WRCFG → consumer (non-Config) hazard.** LLK comments say "1 NOP suffices" but
    only in contexts where a prior SETDMAREG already consumed a cycle. Confirm the
    minimum gap for WRCFG → UNPACR. ([`control-plane.md`](control-plane.md))

### Tier 3 — edge cases and corner behaviors

11. **FIFO backpressure onset at 28 entries (not 32)** — the BH-specific Auto-TTSync
    tracking makes the effective push threshold 28. Measure stall onset with
    `ncrisc.cc`-style tight `sw` loops into `INSTRN_BUF_BASE`.
    ([`control-plane.md`](control-plane.md))

12. **MOP expansion startup latency** (1 cycle to first emission? or same-cycle?).
    ([`control-plane.md`](control-plane.md))

13. **Mover (XMOV) actual startup stall when queue is busy.** ISA says "automatically
    stalled until the mover is able to start" with no cycle count.
    ([`data-path.md`](data-path.md))

14. **L1 port arbitration: NoC vs. packer/unpacker contention**, and **L1 bank conflict
    penalty** (docs say "more than 8 cycles" with no number).
    ([`interconnect.md`](interconnect.md))

15. **AXI↔AI crossing latency** (PCIe, L2CPU x280 cores). Synchronizer depths
    undocumented. ([`interconnect.md`](interconnect.md))

16. **`mcycle` CSR clock identity.** Almost certainly AICLK, but not stated. Cross-check
    `mcycle` delta against `WALL_CLOCK_L` delta over a fixed loop.
    ([`control-plane.md`](control-plane.md))

### Tier 4 — nice-to-have polish

17. Branch-predictor characterization (BH = 4-cycle bubble, WH = 2; predictor policy
    undocumented). Exact `fence` cost. Exact `csrr mcycle` cost.
    ([`control-plane.md`](control-plane.md))

18. CB push/pop round-trip (stream-register polling overhead).
    ([`interconnect.md`](interconnect.md))

19. BH L1 bank count and width confirmation (WH = 16 × 128 b; BH says only "more BW").
    ([`interconnect.md`](interconnect.md))

20. Ethernet SerDes / MAC timing and cross-chip link latency.
    ([`interconnect.md`](interconnect.md))

## Existing measured data worth importing

- **`tt-metal/tt_metal/impl/experimental/noc_estimator/latencies/noc_latencies.yaml`** —
  390 BH-specific NoC entries; unicast r/w, multicast, DRAM interleaved reads; payloads
  64 B – 64 KiB; 1 and 64 transactions/barrier; same-axis and different-axis. Import as a
  lookup table for the emulator's NoC model — this alone gets us most of the way to a
  useful interconnect timing model.
- **`sfpi/gcc/gcc/config/riscv/tt/rvtt.md`** — GCC machine description with
  `xtt_delay_bh` attributes per SFPU instruction (none/static/dynamic). This tells us
  exactly which SFPU ops the compiler considers 1 vs. 2 cycle latency. Matches
  `VectorUnit.md` but useful for cross-checking.
- **`tt-llk/docs/performance_counters/performance_counters.md`** — the hardware
  performance counters available on BH (PACKER_BUSY, AVAILABLE_MATH, etc.). These are
  the signals our microbenches should read.

## Clock-frequency table (for cycle ↔ ns conversion)

| Domain | Frequency | Source |
|---|---|---|
| AICLK (Tensix, NoC, most of Ethernet tile, baby RV) | 1,350 MHz | `BlackholeA0/NoC/README.md:44`, `TensixTile/BabyRISCV/README.md:3`, `EthernetTile/BabyRISCV/README.md:3` |
| AXICLK (PCIe ↔ AI NIU bridge) | 960 MHz | `tt-zephyr-platforms/.../pll.c:192` |
| ARCCLK (management µC) | 800 MHz | `pll.c:191` |
| APBCLK | 100 MHz | `pll.c:195` |
| MACCLK (Ethernet MAC/PCS) | 850 MHz | `pll.c:205` |
| GDDRMEMCLK | 750 MHz init (→ 875 MHz at 14 Gbps trained) | `pll.c:217`, `gddr.h` |
| GDDR6 data rate | 12–20 Gbps (14–16 typical) | `gddr.h:13-15` |
| L2CPUCLK (SiFive x280) | 800 MHz init, raised post-reset | `pll.c:229-232`, `L2CPUTile/README.md:33` |
| REFCLK (PLL reference, ARC wall timer) | 50 MHz → 20 ns/tick | `bh_arc/timer.h:11-13` |
| DebugTimestamper / WALL_CLOCK | 1 tick per AICLK cycle | `TensixTile/DebugTimestamper.md:4` |

All Tensix / NoC timing below is in AICLK cycles (= 0.741 ns each).
