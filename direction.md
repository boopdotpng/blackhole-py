# `blackhole-py-rewrite` — Architecture & Lowering Direction

A Tensix UOp compiler and bare-metal megakernel runtime for Tenstorrent Blackhole, replacing `ttrv`.

---

## 1. Goals & Core Principles

1. **Replace `ttrv` without sacrificing hardware performance**:
   - `ttrv` can express the full Blackhole hardware, but iterating on algorithms (2D multicast, SUMMA, StreamK, multi-tile `Dst` residency, fused epilogues) is slow because every kernel requires hand-maintaining 5 synchronized RISC programs, CB counters, credit/flag state machines, `addr_mod` tables, `replay` blocks, `mop` configs, and `sfp.nop` hazards.
   - Automate away all of that boilerplate while keeping full hardware control (explicit memory spaces, tile shapes, pipelining depths, and optional `replay`/`mop` overrides).
2. **Tinygrad-compatible lower layers, megakernel-native upper layer**:
   - The per-core engine IR and backend are designed to eventually sit at the lowest layer of tinygrad (receiving scheduled kernel ASTs from tinygrad's frontend).
   - Because tinygrad is still kernel-launch-oriented, `blackhole-py-rewrite` keeps a lightweight tinygrad-like frontend for **whole-model megakernels**: tracking activations that stay in L1 between stages, letting cores run ahead asynchronously, and inserting in-kernel all-core sync points only when cores must agree on a shared/redistributed buffer.
3. **Bare-metal execution (no function table, no worker C runtime)**:
   - Upload the entire compiled megakernel (5 RISC images wrapped by tiny position-independent `fw/boot.c` stubs) directly to worker L1 and release `SOFT_RESET`.
   - Static buffer addresses (weights, KV cache, L1 arenas) are baked in at compile time; dynamic per-step state (`pos`, `token_id`, history) lives in DRAM/L1 updated by the megakernel itself.
   - Zero-stall host I/O: workers stream outputs (e.g. generated tokens) directly into pinned host sysmem (`HostStream`) via NoC PCIe writes without ever pausing or syncing the megakernel. Only the 1 dedicated DMA core runs C firmware (`fw/service.c`) for high-throughput Host $\leftrightarrow$ DRAM copies.

---

## 2. Where UOps Work vs. Where We Exit UOps

- **Use UOps above resource allocation** (value-oriented SSA DAG):
  - Whole-chip tensor graphs, sharding/index algebra, multicast detection, loop-invariant hoisting, epilogue fusion, SFPU transcendental decomposition, and per-core tile dataflow.
  - Hash-consing is an asset here because every operation represents a logical value at distinct coordinates.
- **Exit UOps at linearization / resource binding** (structured imperative IR: `Loop`, `If`, `Inst`):
  - Below resource binding, hardware instructions mutate implicit state (`RWC` counters, `SrcA`/`SrcB` 2-bank rings, `Dst` halves, `L0..L7`, CB cursors, NIU command buffers).
  - Stacking identical stateful instructions (e.g. repeated `MVMUL addr=mm_b`) fights UOp deduplication unless you thread dummy `.after()` tokens everywhere. Switching to an ordered imperative IR makes auto-sync, 5-RISC splitting, `ADDR_MOD` synthesis, `SFPLOADMACRO`, `REPLAY`, and `MOP` simple and direct.
- **Escape hatch for explicit `REPLAY` / `MOP` from UOps**:
  - When manual micro-kernel control is wanted inside a UOp graph, a `replay(...)` or `mop(...)` definition stores its ordered Tensix instruction sequence as an immutable tuple in `UOp.arg` (never deduping internal steps against each other, while deduping identical buffer definitions), and its invocation UOp carries dataflow edges (`srca`, `srcb`, `dst`, loop `RANGE`) so auto-sync and 5-RISC splitting still work around it.

---

## 3. The Minimal Non-Boilerplate Op Set

Across all real Blackhole kernels, everything you genuinely need to describe reduces to 7 primitives; everything else is boilerplate:

| Area | What You Describe | Automated Away |
|---|---|---|
| **1. Grid & Control** | `grid`, `core.id/x/y`, `RANGE`, `IF`, `REDUCE`, scalar/DRAM/L1 buffers | Duplicating loops across 5 RISCs, dead-loop pruning, RV32 regalloc |
| **2. NoC Movement** | `noc_read`, `noc_write`, `noc_mcast(rect, sender)`, `noc_gather`/`allgather` *(with `depth`, `stages`, `cap`, `port` hints)* | Command buffers, TIDs, `noc.wait`, `b_ready`/`b_sent` credit/flag protocols, `fence`s, BRISC vs NCRISC assignment |
| **3. Unpack** | `unpack(l1 -> SRCA\|SRCB\|DST, fmt, shape, transpose)` | `TileDescriptor`, `base_addr`, `reset_zw`, `dvalid`, `srca_clr`/`srcb_clr` stalls, `tensix.wait`, `cb.wait`/`pop` |
| **4. FPU** | `mvmul(srcb, srca -> dst, tile, fidelity)`, `fpu_elw(add\|sub\|mul\|max)`, `fpu_copy` | `ZEROACC`, `ADDR_MOD` slots `0..7`, face/half unrolling, `SETRWC`/`release`, `REPLAY`, `MOP`, `math.fmt` |
| **5. SFPU** | Standard UOp expressions on `DST` (`+`, `*`, `neg`, `abs`, `max`, `where`, `cmplt`, bit ops, `lane_id`, `exp`, `sin`, `sqrt`, `rsqrt`, `recip`, `reduce_row`, `argmax`) | `L0..L7`/`L12..L14` reg management, `Dst` intermediate spills, `sfp.nop` hazards, predicate stack (`SFPENCC`/`SFPPUSHC`), `SFPLOADMACRO`, `REPLAY`, `MOP` |
| **6. Pack** | `pack(dst -> l1, fmt, shape, l1_acc)` | `math_pack` semaphores, `dst_offset` double-buffering, `pack.fmt`/`edge`, `tensix.wait`, `cb.reserve`/`push` |
| **7. Residency** | Where loop-carried state / intermediates live: `DST` (accumulators, `(O,m,l)`), `L1` (`Pack_L1_Acc`, persistent cross-stage slabs), `DRAM`, or `SCALAR` (RV32 glue) | L1 arena layout & alignment, CB allocation & page sizing, multi-tile `Dst` slot indexing |

---

## 4. Lowering Pipeline (4 Layers)

```text
[Layer 0] Whole-Chip / Megakernel API (tinygrad-like UOp frontend, written for all 119/139 cores)
            Expresses full kernels or multi-stage model graphs without core_id math.
                │
                ▼  Sharding, Multicast Detection, L1 Residency & Selective Sync
[Layer 1] Per-Core Engine UOp Graph (pure SSA using the 7 minimal primitives)
            Can also be authored directly for manual algorithmic schedules.
                │
                ▼  SFPU UOp Decomp & Dst-Partitioning -> Linearize -> Bind -> Auto-Sync -> Split
[Layer 2] 5 Per-RISC Imperative Streams (brisc, ncrisc, trisc0, trisc1, trisc2)
            Structured Loop / If / Inst IR (NOT UOps); verifiable in a fast Python simulator.
                │
                ▼  Per-RISC Lowering, Hardware Compression & Codegen
[Layer 3] 5 RISC Binaries -> fw.pack_megakernel -> Bare-Metal L1 Upload & Run
```

### Layer 0 $\to$ Layer 1: Whole-Chip Sharding, Multicast & Megakernel Residency
- **Full-grid sharding by default**: attempt to use all workers (119 on p100a, 139 on p150) unless the buffer is genuinely tiny.
  - Elementwise: 1D tile split across all cores (shrink chunk below 1024 only for tiny tensors/tails).
  - Reductions: shard outer axes first; if `outer < num_workers`, enable `Split-K` (`PEERS`) + peer gather/reduce.
  - Matmul `(M, N, K)`: 1D `N` (+ `Split-K`) when `M <= 32`; 2D `(R x C)` grid balancing `MT/R`, `NT/C`, and resident `Dst` panels when `M > 32`.
- **Automatic NoC Multicast detection**:
  - After substituting core coordinates `(core_y, core_x)` into each `LOAD`'s index UOp, check which grid coordinate is absent:
    - `core_y` absent (`R > 1`) $\implies$ all cores in a column read identical data $\to$ **Column Multicast (NoC1)** with rotating senders.
    - `core_x` absent (`C > 1`) $\implies$ all cores in a row read identical data $\to$ **Row Multicast (NoC0)**.
  - Trigger multicast whenever `redundancy * bytes` exceeds the small-buffer threshold (eliminating `R`x redundant DRAM weight reads).
- **Megakernel L1 residency & selective sync**:
  - Track `(space, layout, sharding)` across stages of a model graph.
  - Matching sharding + fits L1 $\implies$ keep in L1 across stages with **zero global sync** (cores run ahead locally).
  - Sharding change / cross-core visibility $\implies$ insert an in-kernel subgroup or all-core barrier (and/or L1-to-L1 redistribution).

### Layer 1 $\to$ Layer 2: SFPU Expression Compiler
FPU ops (`MVMUL`, `ELW*`) are direct and map cleanly to `ADDR_MOD` + `REPLAY` + `MOP`. SFPU has only 8 vector regs (`L0..L7`) and complex hazard/macro rules, so it gets a dedicated compiler pass:
1. **UOp decomposition**: expand `exp2`, `log2`, `sin`, `cos`, `sqrt`, `rsqrt`, `recip`, `tanh`, `silu`, `gelu`, `where` into primitive SFPU UOps (getting free CSE and constant folding).
2. **`Dst`-intermediate partitioning**: pin hardware constants to `L9..L11` and hot constants to `L12..L14`. Split deep expressions into stages that fit in the physical register budget (4 regs/row for 2x even/odd row interleaving, or up to 8 regs), materializing intermediates to scratch `Dst` tiles between passes rather than attempting full virtual regalloc.
3. **Macro fusion & hazard scheduling** (in Layer 3): fuse eligible `load -> {simple, mad, round} -> store` chains into 1–2 `SFPLOADMACRO`s, interleave even/odd rows to hide MAD latency, insert minimal exact-latency `sfp.nop`s, and pack into `REPLAY` + `MOP`.

### Layer 2 $\to$ Layer 3: Linearize, Auto-Sync, Split & Compress
1. **Linearize & Resource Bind** (still 1 sequential stream over all 5 RISCs):
   - Every edge crossing RISC boundaries becomes a typed channel: Local `CB`, `CollectiveCB` (ring + credit/flag), `SrcA`/`SrcB` dvalid pair, or `Dst` semaphore half.
   - Allocate L1 arena addresses (via lifetime intervals), `Dst` tile slots, `L0..L7`, and NoC TIDs.
2. **Auto-Sync & 5-RISC Split**:
   - Insert `cb.reserve/push/wait/pop`, collective credit/flag handshakes, `dvalid`/`STALLWAIT`/`SETRWC`, `math_pack` semaphores, and `noc.wait` from explicit per-inst resource reads/writes.
   - Project the single stream onto `brisc`, `ncrisc`, `trisc0`, `trisc1`, `trisc2`, pruning empty loops per RISC.
3. **Per-TRISC Hardware Compression & Binary Emit** (reverse pipeline order):
   - Expand FPU/SFPU tile ops $\to$ synthesize `ADDR_MOD` (slots `0..7`) $\to$ `SFPLOADMACRO` fusion $\to$ `REPLAY` packing (32-word budget) $\to$ `MOP` loop synthesis $\to$ RV32IM regalloc ([compiler/regalloc.py](compiler/regalloc.py)) + encoding ([hw/isa.py](hw/isa.py)).

---

## 5. Vertical Build Plan (Verified on Silicon at Every Step)

1. **Slice 1 — UOp Core + SFPU Elementwise End-to-End** (e.g. `out = silu(a) * b` across all workers)
   - Implement `uop.py`, minimal engine ops, linearize/bind/sync/split, SFPU expression compiler (`Dst` partitioning + `SFPLOADMACRO` + `REPLAY` + `MOP`), NoC/Unpack/Pack/RV32 codegen. Verify against NumPy on p100a.
2. **Slice 2 — FPU Matmul + Auto-Sharding + Automatic NoC Multicast** (`(M, K) @ (K, N)`)
   - Add `MVMUL` lowering, auto `ADDR_MOD` + `REPLAY` + `MOP`, `SrcA`/`SrcB` dvalid double-buffering, multi-tile `Dst` residency, `Pack_L1_Acc`, and automatic Row/Col Multicast + Split-K from index-invariance analysis.
3. **Slice 3 — Multi-Stage Megakernel** (e.g. `RMSNorm -> Projection -> SiLU` + autonomous decode loop)
   - Add whole-graph L1 activation lifetime allocation, core run-ahead with selective in-kernel all-core barriers, and continuous token streaming via `HostStream`.
