# Microbenching TODO

Open measurements, blocked items, and re-enable plans. Status keywords:
**OPEN** = not started · **GATED** = waiting on validation/device · **QUARANTINED** = wedge risk, needs re-enable checklist · **MODEL** = no device needed.

## NoC

- [ ] **Per-hop router latency — the single biggest hole.** Hop sweep is flat (~230 cyc round-trip dominated by fixed NIU/cmd cost). Pointer-chase per-hop probes timed out and are PAUSED. Restart with one tiny K=2 chase, short timeout, queue-only. Without per-hop slope, all NoC routing inferences stay coarse. GATED
- [ ] **Arbitration full matrix (Experiment A).** Gated until a K=2 smoke gets bad counters=0 AND bad sentinels=0 (currently always bad sentinels=2 — likely host-readback bug, not fabric). Debug the sentinel encoding before any matrix run. GATED
- [ ] **Bisection bandwidth at scale (Exp F).** 4 left→right pairs gave only 1.585× — likely NIU-bound. Repeat with many rows, both directions, NoC0+NoC1, to estimate true bisection. OPEN
- [ ] **Dual-NoC aggregate ceiling.** 60-pair dual-DM stops at ~961 B/cyc vs 3450 single-NoC; routing direction was flipped for NoC1. Rerun dual-DM with NoC1-correct pair direction; goal: prove or refute 2× fabric. Moderate/full dual-aggregate sweeps QUARANTINED (wedged card off PCIe bus). QUARANTINED
- [ ] **Mcast NoC1 row anomaly.** NoC1 row mcast 1.5–1.6× slower than NoC0; column equal. Sweep dest-count vs direction; test mcast scaling >3 dests. Linked mcast stays excluded (hang risk). OPEN
- [ ] **Read/write VC isolation follow-up.** Reads 1.43–1.48× slower under write saturation in every config — find shared resource (NIU? router port? L1 banks?). Try src/dst on disjoint tiles, smaller writes. OPEN
- [ ] **All-NoC bidirectional ceiling per receiver.** 3464 B/cyc was 60 disjoint pairs; max into one tile / one column not yet measured. OPEN
- [ ] **Logical→physical coordinate map.** x=8,9 gap + harvested rows assumed not confirmed; needed for hop counts. Use topology probe + wrap-link timing. OPEN

## DRAM

- [ ] **Chase the GDDR roof.** Worker-NoC harness tops ~305 GB/s vs ≥448 GB/s theoretical. Port the DRISC `gddr_dma.h` path (255 outstanding reads, 262 kB transfers): needs DRAM-core/DRISC launch support in blackhole-py. OPEN — biggest BW upside
- [ ] **Non-monotonic core scaling.** Reads peak 376 GB/s @56 cores, drop ~300 @118. Sweep core count finely; find contention point (controller queue vs NoC). OPEN
- [ ] **Per-controller verification.** ~61–73 GB/s/controller × 7 ≈ 430–510 GB/s ≠ ~300 observed. Measure 7 disjoint controller×core sets simultaneously. OPEN
- [ ] **DRISC dual-stream DMA.** Two-stream microkernel never produced a valid run. OPEN
- [ ] **DRISC overlap modes** (`dma2`, `serial`, `pipe`, `pipe2`) timed out in-kernel. Debug minimal version. OPEN

## Tensix backend

- [ ] **Dest readback minimal re-enable** — prerequisite for SFPU + pack validation. 64-row walk only (256 rows corrupted pack rel_l2=1.0); no-readback control → readback → re-validate pack. QUARANTINED (checklist in docs/tensix/dest-readback.md)
- [ ] **SFPU timing (exp, rsqrt, recip, sigmoid, silu).** No validated numbers; readback gave 0x007f007f (selector/format issue). Highest leverage: unblocks llama rmsnorm/softmax/swiglu modeling. QUARANTINED behind dest-readback
- [ ] **SFPU transcendental harness** (`microbench_sfpu_transcendental.py`) — never run on hardware. GATED
- [ ] **Pack isolation.** Pack ~5265–7425 cyc/subblock from perturbed failed-validation runs vs ~924 whole-kernel fit — 6–8× contradiction unresolved; pack is the #1 unexplained pipeline number. Standalone pack rows hang without unpack/math companion. GATED
- [ ] **Resolve MVMUL 2× gap + 16-cyc claim.** Encoded slots 16/tile-K vs architectural 8/tile-K; issue 2.38 vs latency 11.25 cyc/arch-MVMUL vs claimed 16. Multi-body single-drain burst. OPEN
- [ ] **XMOV movers** TTMOVA2D/D2A/D2B + debug moves. QUARANTINED (`ttmova2d` wedge); DMA-reg family done
- [ ] **Multi-subblock steady state in one launch** — math hangs without TRISC0; needs minimal triangle scaffold. OPEN
- [ ] **Producer/consumer blocking-wait timing** (TTSEMWAIT, CB waits) with known release timing. OPEN
- [ ] **TTMOP/replay-expander cost model.** OPEN

## RISC-V loose ends

- [ ] NCRISC L1-load anomaly (5.165 vs 5.0 cyc; ind4 1.292) — repeat across tiles. OPEN
- [ ] TRISC2 LDM pair anomaly (2.0 vs 1.5); RMW asymmetry (B/N/T0 ~14.5 vs T1/T2 ~10.5 all-five) — port priority? OPEN
- [ ] All-pairs contention matrix (`--all-pairs`, 16 groups). OPEN
- [ ] Cross-LDM interconnect topology (5×5 pair latency under load). OPEN

## Model / no device needed

- [ ] Resource-queue overlap model (RISC, NoC0/1, DRAM ctrl, unpack/math/pack, L1 ports, sems) in program_timing_model. MODEL
- [ ] Close 0.42 vs 24.88 TFLOP/s gap budget at 384³ from clean constants; predict 5000³. MODEL
- [ ] Normalize all docs to cycles (800 vs 1350 MHz μs mismatches). MODEL
- [ ] Dedupe noc_topology helper vs probe fallback (`shared_links` API). MODEL

## Process

Device wedges: ARC `boot_status=0xffffffff`, core-(1,2) waits, PCIe drop (cold boot to recover, warm reboot insufficient). Quarantined runs only via queue, build-only first, one short job, stop on first anomaly.
