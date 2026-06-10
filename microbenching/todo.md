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
- [x] **SFPU timing (exp, rsqrt, recip, sigmoid, silu).** DONE 2026-06-09 via `microbench_sfpu_transcendental.py --iters 4096` (issue-side wall-clock loop on TRISC1, no dest-readback needed). bf16, 32-lane group: exp 40 cyc, recip 16, rsqrt(5 Newton) 58, sigmoid 59, silu 62 → ~1.25–1.94 cyc/elem (~1.3–2.0k cyc/tile). All five validated vs numpy (max_rel ≤0.74%). llama swiglu cost ≈16k cyc/token — negligible vs DRAM bound.
- [x] **SFPU transcendental harness** — first hardware runs 2026-06-09, correctness PASS (exp/recip/rsqrt/sigmoid/silu) jobs `0162bd90`, `08553072`; timing job `2410fbae`.
- [x] **SFPU reduce (sum/max/row-max).** DONE 2026-06-09 via `microbench_sfpu_reduce.py --iters 4096` (jobs `1144380b` correctness, `44766763`/`4dd826ce` timing, repeatable <0.03%). bf16: sum32 51 cyc/32-lane group (1.59 cyc/elem), max8x4 51 cyc/group, rowmax 293 cyc/tile (9.2 cyc/row, 0.29 cyc/elem). sum32==max8x4==51 despite 33 vs 27 instr bodies → RISC issue-bound, not SFPU-bound; helper contracts pinned: horizontal max is per-8-lane row (lane 0), reduce_row_max_tile clobbers odd cols, only col0 valid. Softmax row max+sum ≈ rowmax 293 + ~51×rows; rmsnorm sum-of-squares = sum32 + 1 mul.
- [x] **Eltwise binary (add/sub/mul) + broadcast (row/col/scalar).** DONE 2026-06-09 `microbench_eltwise_binary.py` / `microbench_eltwise_bcast.py` (jobs `b7e6f3bd`/`a8d3cc01`, `cf09dee8`/`a94e407c`). First two-operand pipeline: CB0→SrcA(SEC0) + CB1→SrcB(SEC1), LLK unpack_AB + eltwise MOPs. All 9 variants PASS; mul is LoFi (~3% low). Stream: ~1234 cyc/tile NONE-bcast, row 1226 / col 1242 / scalar 1234 — single-core DRAM-feed-bound (3 tiles × 2 KiB @ ~3.3 B/cyc), math (8 ELW ≈ 16 cyc) hidden. Gotchas: add1's SYNC_L1 at +0x10000 collides with a 3rd CB's data region (corrupted output tile 0; moved to +0x20000); LoFi mul mantissa-truncated. HiFi2 mul not benched. OPEN follow-up: math-isolated ELW throughput (no-pack drain).
- [x] **Softmax composite.** DONE 2026-06-09 `microbench_softmax.py` (jobs `b6fe7f37` correctness, `9c452b63` ×2 timing, repeatable 0.002%). Per-row softmax of a 32×32 tile, all-SFPU in dest (rowmax bcast → exp(x−max) → row-sum bcast → recip → mul), input intact via scratch tile at dest rows +64. 2738 cyc/tile = 85.6 cyc/row — math-bound (feed floor ~1234); ≈ sum of parts (rowmax 293 + 32×exp 40 + sum/recip/glue) → no composition surprise. Body run once per tile (not idempotent) via custom TRISC1; bands looped on RISC with offset-patched SFPLOAD/SFPSTORE words (3.6 KB IRAM vs ~1700 emits unrolled).
- [x] **cb_reserve_back never blocks when CB full.** FIXED 2026-06-09. Root cause was not reserve_back: `cb_pop_front(tensix_ack=True)` emitted BOTH the deferred SETDMAREG→STALLWAIT→STOREREG ack (ordered behind the unpack in the Tensix FIFO) AND an unconditional eager RISC `sw acked` to SYNC_TILES_ACKED — the eager store released pages at TRISC0 issue rate (which runs ahead of unpack/math), so BRISC always saw free pages and lapped CB0 (output tile i+CB_DEPTH; the late STOREREG then overwrote acked with the older value). Fix in ttk/cb.py: eager publish of acked/received gated on `not tensix_ack`/`not tensix_received` (the push_back side was the same latent bug, masked by slow drains); local iface counter unchanged. A/B on device: softmax no-throttle 64-tile stream FAIL pre-fix (`54ab77b1`) → PASS post-fix (`ee153e6f`), 2742 cyc/tile = same as throttled (flow control adds no overhead). Throttle workaround removed from softmax bench (default off; `--throttle` keeps legacy gate). Regressions PASS: add1 1180-tile grid, eltwise binary ×64 streams, matmul_peak 18.07 TFLOP/s (`c428246a`, `6f2a6625`).
- [x] **Skinny GEMV (M=1) DRAM-bound matmul.** DONE 2026-06-09
  `microbenching/matmul/microbench_skinny_gemv.py` (jobs `a9bdd139`, `88ae338f`,
  `ce7c3ffd`, `7b27f45c`, `2e43df82`). matmul_peak planner/dataflow at M=1 on a
  single core row (extra rows only write padded output; --rows 10 is *slower*,
  90→83 GB/s). bf16, llama 1B shapes, weight-GB/s metric: kv 76 / q 87 /
  gate 90 / down 96 / logits 94 GB/s = ~30% of the 305 GB/s roof → ~36 tok/s.
  Bottleneck: 11 NCRISC column readers, 1 block in flight each — chase via
  outstanding reads / DRISC GDDR path. Wedge: >6 differing-program launches per
  session hangs CQ wait_completion (also corrupts validation if it survives) —
  run one shape per process; multi-chunk shapes >1 run hit it too. CQ wedge
  ROOT-CAUSED 2026-06-09: prefetch FW splits multi-page records across the
  128-page dispatch-CB wrap (trim-to-end loop), but dispatch FW only wraps its
  cursor when it lands exactly on DISPATCH_CB_END — a straddling record makes
  dispatch parse past CB end into stale L1 (spurious packed writes = the
  corruption), then page-credit divergence deadlocks the semaphore (the hang).
  Launches are ~55–67 ring pages, so the wrap point drifts per differing
  launch until a multi-page mcast-binary record (8–13 pages) lands on it. Host
  fix in cq.py `_issue_write`: pad to ring boundary with 1-page unknown-cmd
  records (dispatch advance_page fallback) before any straddling record; also
  pad host issue buffer to exact 64 MiB end before wrapping (prefetch wraps
  only at end-exact — second latent desync). Sim: 1200 mixed launches / 87k
  records / ~340 ring wraps → 0 straddles, 0 desync. Device A/B 2026-06-10
  (jobs `52764ae6`/`b45aaa08`/`c891d722`/`0dbcb664`): ~660 differing-program
  launches, ZERO hangs (was >6); 405-launch alternating soak PASS. Ring grown
  512K→1.25M (320 pages, end 0x15A000; CMDDAT above; GO_SIGNAL_NOC_DATA →
  CQ_DEBUG+0x200) — pages single-sourced from cq.CQ_DISPATCH_CB_PAGES.
  Corruption was a SEPARATE bug, not CQ: deterministic (PCC=0.631127 exact
  repeat), triggered on the FIRST relaunch after a different K-block-count
  program (384 → 512 → 384; fresh ×40 identical relaunches clean). ROOT-CAUSED
  2026-06-10: TRISC firmware only initialized local launch state at boot, so
  kernels had to remember to reset dest/cfg/unpack context themselves; a
  3-block matmul left state that the following 2-block matmul inherited.
  Firmware fix in fw/trisc.py: reset Tensix regfile + TRISC local
  dest_offset/op_info/cfg_state and TRISC0 unpack context at every RunSync.GO,
  before per-launch CB setup. Device A/B direct (queue was stale on `f524d097`):
  384/512/384 repro PASS, then 60-launch validated 384/512/768 soak PASS, then
  400 alternating 384/512 fast-dispatch launches PASS with periodic validation
  (fails=0). OPEN follow: bfp8/bfp4 sweep (dtype missing).
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
