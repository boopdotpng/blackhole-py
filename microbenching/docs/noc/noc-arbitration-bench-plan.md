# Blackhole NoC Arbitration & Topology Benchmark Plan

Goal: recover the *structural* behavior of the Blackhole NoC — per-hop router
latency, arbitration policy, routing dimension order, torus-vs-mesh topology,
virtual-channel separation, and bisection bandwidth — by inferring them from
on-device timing and per-stream NIU counters under controlled contention.

This is the "what does the verilog roughly look like" bench. The existing NoC
microbenches (`riscv_noc_bench`, `riscv_noc_hop_sweep`, `riscv_noc_stream_sweep`,
`riscv_noc_aggregate`, `riscv_noc_dual_*`) characterize *throughput* and
*latency* of single streams and undifferentiated aggregates. None of them
isolate *how a router arbitrates* when streams collide, and the hop sweep came
back distance-independent. This plan fixes both.

## Hardware Model Under Test

Working hypothesis for the fabric (this is what the experiments confirm or
refute, not assumed fact):

- A 2D **torus** of routers, one router per grid node. The router grid is larger
  than the Tensix worker grid: DRAM, PCIe (`(19,24)`), Ethernet, and L2CPU nodes
  sit on the same NoC and packets route *through* them.
- **Two physically independent NoCs running in opposite directions.** Every
  existing bench encodes "NoC0 = ascending (right/down), NoC1 = descending
  (left/up)". That convention is the fingerprint of **dimension-ordered routing
  on unidirectional rings** — to travel "backward" you wrap the torus or use the
  other NoC.
- A **NIU** (NoC interface unit) per node with separate command buffers and
  master counters for requests-sent / acks-received / responses-received.
- Separate **virtual channels** are real and selectable (`NOC_CMD` exposes
  `CMD_VC_STATIC`, `CMD_STATIC_VC_1/5`, `CMD_VC_LINKED`).

### Physical grid (P100a, from `pcie.py`)

- Worker columns `x ∈ {1..7, 10..14}` — **gap at x=8,9** (PCIe/ETH/L2CPU/DRAM
  column region).
- Worker rows `y ∈ 2..11` (rows 0,1 reserved).
- `device.cores` returns these **physical** NoC coordinates directly; there is no
  logical→physical remap for Tensix cores, so `noc_xy(x,y)` packs the real
  routing coordinate.

### Open questions to recover

1. **Per-hop router latency** (cyc/hop), and whether X-hops cost the same as
   Y-hops.
2. **Arbitration policy** when injected traffic meets through-traffic at a router
   (fair round-robin? injection-priority? through-priority? positional bias?).
3. **Routing dimension order** — X-then-Y or Y-then-X, and where packets turn.
4. **Torus vs mesh** — do physical wraparound links exist, or does "backward"
   force the long way / the other NoC?
5. **Virtual-channel separation** — do reads (req/resp) and writes share buffers
   and links, or are they isolated?
6. **Bisection bandwidth** — how many/wide are the links across the chip midline.

## Methodology: Why The Hop Sweep Was Flat, And The Fix

`riscv_noc_hop_sweep` measured ~230 cyc independent of x-distance. Two confounds,
both of which this bench must eliminate:

1. **Fixed cost dominates a single round-trip.** One read ≈ NIU command setup +
   request + response + ack ≈ 230 cyc; per-hop is buried (~1 cyc/hop). A single
   serialized transfer can never expose it.
   - *Fix:* measure steady-state throughput under saturation (many requests in
     flight), or use a long **dependent pointer-chase** across NoC and fit a line
     over many iterations to extract cyc/hop as the slope.

2. **Logical distance ≠ physical hops.** The sweep counted x-steps, but the
   x=8,9 gap and possible torus wrap mean dx=5 is not 5 routers.
   - *Fix:* build a host-side physical-path model (below) and label every result
     by *true router-hop count*.

3. **A single stream never exercises arbitration.** Arbitration is only
   observable when ≥2 streams contend for one link.
   - *Fix:* deliberately route multiple streams through a shared link (below) and
     read the policy off the *distribution* of per-stream bandwidth.

## Prerequisite: Host-Side Physical Path Model

Before any experiment, write a pure-Python helper (verifiable offline against the
known grid, no device needed):

```
noc_path(src_xy, dst_xy, noc) -> [router_xy, ...]   # ordered nodes traversed
noc_hops(src_xy, dst_xy, noc) -> int                # true hop count
shared_link(streamA, streamB, noc) -> bool | link   # do two paths overlap?
```

Encodes: dimension order (assume X-then-Y first, then let experiment D correct
it), the x=8,9 column gap, NoC0-ascending / NoC1-descending direction, and torus
wrap (assume wrap exists, let experiment C correct it). This model is what makes
every downstream result interpretable and lets us *choose* source/target sets
that share exactly one link.

## Experiment Matrix

Each experiment isolates one hardware question. Every sender records its own
start/end `WALL_CLOCK` and its own NIU counter deltas, so per-stream bandwidth is
measured independently.

### A. Fair-share / injection arbitration  *(start here)*

- **Setup:** K senders in one row, all writing rightward on NoC0 to targets
  clustered at the far end, so the last link carries all K streams.
- **Measure:** each sender's individual B/cyc; the *distribution* across senders.
- **Reveals (Q2):**
  - Equal shares (~link_bw/K) → fair round-robin arbiter.
  - Near-the-sink senders favored → through-traffic priority (injected packets
    yield to packets already on the ring).
  - Far senders favored → injection priority.
- **Axes:** K = 2,3,4,6,8,…; NoC 0/1; packet bytes (4096, 16384); posted vs
  nonposted writes; read vs write.
- This is the closest extension of `riscv_noc_aggregate` and the single highest
  information-per-effort experiment.

### B. Crossing-traffic / victim test

- **Setup:** one long "victim" stream; a second stream that *injects at an
  intermediate router* on the victim's path. Sweep the injection point along the
  path.
- **Measure:** victim throughput vs injection position.
- **Reveals (Q2):** whether arbitration is positional, and how badly a single
  crossing flow can starve a through flow.

### C. Torus-wrap detection

- **Setup:** write from high-x to low-x on NoC0 (the "wrong" direction for an
  ascending ring). Compare latency/bw to the equivalent short forward path.
- **Reveals (Q4):** match → real wraparound link (true torus). Dramatically worse
  / only works on NoC1 → effectively a mesh, direction mandatory.

### D. Routing dimension order

- **Setup:** diagonal send (x0,y0)→(x1,y1). Place a crossing stream on the X-leg,
  then separately on the Y-leg.
- **Measure:** which leg's crossing stream interferes with the diagonal stream.
- **Reveals (Q3):** the leg that interferes is the leg the packet actually
  travels → X-then-Y vs Y-then-X. Feeds back into the path model.

### E. Virtual-channel isolation (read vs write)

- **Setup:** saturate a write stream on a path, then run a read stream on the
  same path.
- **Measure:** does the read slow down?
- **Reveals (Q5):** slowdown → shared VC/buffers; no slowdown → req/resp on
  separate virtual channels. Optionally sweep `CMD_STATIC_VC_*` selections.

### F. Bisection bandwidth

- **Setup:** left half of the worker grid → right half across the vertical
  midline; aggregate.
- **Measure:** cross-section aggregate bandwidth ÷ single-link bandwidth.
- **Reveals (Q6):** approximate number of links crossing the bisection →
  confirms torus width.

### (Aux) Per-hop latency

- **Setup:** dependent NoC pointer-chase (each read target depends on the prior
  read's result, so it cannot pipeline), swept over true hop count from the path
  model.
- **Measure:** total / iters, fit a line; slope = cyc/hop, intercept = fixed NIU
  cost.
- **Reveals (Q1):** the per-hop number the original flat sweep could not see.

## Suggested Order

1. Path model (offline, prerequisite).
2. **A** — fair-share (extends the aggregate bench; reads off the core arbiter).
3. **C** + **D** — nail the topology and routing order; correct the path model.
4. **E**, **F**, and the per-hop aux measurement.

## Harness Shape

Model on `microbenching/noc/riscv_noc_aggregate.py` (many senders, one `Run` broadcast, per-core
wall-clock window) plus the chunked 16 KiB command train from
`microbenching/noc/riscv_noc_stream_sweep.py`.

- Allocate per-core L1 source/dest segments via `Program.layout(core_xy=...)`,
  one per participating core, then a single `Run(target_cores)`.
- Senders push `NOC.MAX_BURST_SIZE` (16 KiB) chunks until a target byte count.
- Each sender brackets its loop with `read_wall_clock` and snapshots
  `NIU_MST_WR_ACK_RECEIVED` / `RD_RESP_RECEIVED` / `NONPOSTED_WR_REQ_SENT`
  (`emit_counter_read`).
- Report **per-stream** bandwidth (the distribution is the result), not just an
  aggregate.

### Reachable today (assembly of existing parts)

- `ttk/noc.py`: `noc_read` / `noc_write` (NoC0/1 select, `posted=`, `mcast=`),
  `noc_xy(x,y)` physical coords, NIU counters at `NOC.STATUS_BASE`, completion
  helpers `noc_reads_flushed` / `noc_write_barrier`.
- `riscv_core_bench.read_wall_clock`, the 16 KiB burst chunking, and the
  multi-core `layout` + `Run` launch path from the aggregate bench.

### Two additions needed

1. **Physical-path model** (host-side Python) — the prerequisite above.
2. **Wall-clock start gate.** Today the aggregate bench leans on cross-core clock
   alignment from a single `Run` broadcast — too sloppy when K streams must
   genuinely overlap to saturate one link. Add: host writes a future
   `WALL_CLOCK` threshold into each sender's L1; each sender spins
   (`read_wall_clock` ≥ threshold) before its first push. `riscv_wall_clock_skew`
   already proved the clock is stable enough. A counting semaphore barrier
   (`noc_semaphore_*`) is the fallback.

## Limitations / Honest Caveats

- **No router-status / per-port congestion register decode exists in the tree** —
  only the NIU *master* counters (requests sent / acks / responses received). So
  arbitration and routing are inferred from **timing + per-stream throughput**,
  not read out of a register. Conclusions are behavioral, not a register dump.
  - A separate spike could try reading `NocCfg.ROUTER_CFG_0` / `NIU_CFG_0`
    (indices already defined) for ground truth, but that is out of scope here.
- Cross-core wall-clock has a constant nonzero offset between cores
  (`wall-clock-skew`); the start gate removes launch skew but per-stream windows
  should still be compared as *deltas on the same core*, not raw cross-core
  timestamps.
- Multicast is intentionally excluded (hang risk; covered separately by
  `microbench_noc_mcast_mixed`). These experiments use unicast only.
- The path model's initial assumptions (X-then-Y, torus wrap) are corrected by
  experiments D and C respectively — early A/B results may need re-labeling once
  the topology is confirmed.

## Expected Relevance

`examples/matmul_peak.py` runs BRISC/NoC0 A-reads + A-multicast across columns
and NCRISC/NoC1 B-reads + B-multicast across rows + C-writeback on NoC1
simultaneously. Whether those overlapping flows fairly share links, and where
they collide, is exactly what experiments A/B/D measure — so this bench feeds
both the static timing model (a proper resource-queue NoC model instead of one
fitted constant) and the architectural understanding of the chip.
