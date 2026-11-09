# blackhole-py audit: merged master list (Fable 5.1 + GPT-6 Astra + GPT-6.1 Sol)

Merged 2026-11-05 from three independent audits of `/home/boop/tenstorrent/blackhole-py` at HEAD `dd4f882`:

- **Fable**: `fable-5.1.md`, 95 findings (IDs CQ-, DEV-, PRG-, TTK-, LL-, TL-, TS-, XC-)
- **Astra**: `gpt-6-astra.md`, 103 findings (A001–A103)
- **Sol**: `gpt-6.1-sol.md`, 101 findings (F001–F101)

All 299 source findings are mapped below. Every source ID appears in at least one merged finding. A few broad source findings feed two merged findings and are marked "(part)". The result is **176 merged findings**.

Merge rules:
- **Severity** is the highest any model gave. The spread is noted when the models disagreed.
- **Status** is verified if any model verified it. "Verified" means confirmed in source or reproduced offline. No model reproduced anything on hardware.
- **Goal tags** are the union across models.
- Findings that are related but not identical stay separate and point at each other with "See".
- Line numbers come from the reports. Where the merger re-checked them, the corrected numbers are used (see §3).
- During the merge, code was read but no device was opened. One attempt to run a pure-Python encode microbenchmark was blocked by the sandbox, so no new numbers were produced.

---

## 1. Consensus top priorities (ranked)

The ranking weighs how many models flagged each theme, how severe they rated it, and whether it was in their own top ten. F, A and S below stand for Fable, Astra and Sol.

| # | Theme | Models | Severity | Merged IDs |
|---|---|---|---|---|
| 1 | **A real tensor model.** Separate the logical tensor/view (shape, strides, M/N/K, batch and sequence axes) from physical layout, page geometry, storage and placement, and drop the "everything is one 32×32 tile" unit. | 3/3, in all three top-3s | high ×3 | M-055, M-056, M-057, M-058, M-059 |
| 2 | **One blocked M>1 matmul in the shared path.** The decode projection is a single-vector GEMV. The working blocked, multicast, double-buffered matmul lives in `matmul_peak` behind a separate ABI. Bring it into the shared path, with GEMV as its M=1 schedule. | 3/3, all top-3 | high ×3 | M-110, M-071, M-072, M-081–M-084 |
| 3 | **Batch- and sequence-aware attention and KV state.** Today attention rows hold GQA heads, KV is one fixed sequence, and nothing tracks KV validity. | 3/3 | high ×3 | M-113, M-115, M-116, M-111, M-112 |
| 4 | **Derived or verified synchronization and resource allocation.** CB credits, semaphores, replay/MOP, Dst, L1 aliasing and NIU TIDs are all placed by hand today, with no program-wide verifier. | 3/3 | high ×3 | M-067, M-076, M-077, M-092, M-104, M-079 |
| 5 | **A typed per-launch argument ABI.** Today there are 24 untyped u32 slots and 8 trace slots that must be uniform across cores, bound by string name or object identity, and nothing checks the signature. | 3/3 | high ×3 | M-014, M-063, M-061, M-062, M-022 |
| 6 | **Freeable memory and incremental residency.** DRAM, L1, trace, template and kernel arenas are bump-only, and the caches install once. Training cannot run on this. | 3/3 | high ×3 | M-025, M-042, M-015, M-016, M-043 |
| 7 | **Offline-first testing.** Ship a fake transport/CQ backend, numpy references per op, a protocol interpreter, and a prefill/bs-n/backward/AdamW numerical matrix. | 3/3, all top-10 | high ×3 | M-155, M-156, M-157, M-140, M-139 |
| 8 | **NoC as a planned, validated model.** Routing policy is per-kernel folklore with a known card-hanging combination. "Wait" on a posted write does not mean the data arrived. The address path costs division plus a branch per tile. | 3/3 | high (Fable low–med on parts) | M-103, M-105, M-106, M-107, M-074 |
| 9 | **Execution lifetime safety.** Async replay patches a trace still in flight. Captured staging can be recycled. A timeout does not poison state. Timestamps are shared. Reads are not ordered with programs. | 3/3 (Fable med, Astra/Sol high) | high | M-001, M-002, M-007, M-008, M-003, M-021 |
| 10 | **A training execution contract.** Saved activations or recompute, gradients, FP32 master and optimizer state, explicit precision policy, checkpoint save. | Astra + Sol high; Fable via XC-01/TTK-12 | high | M-128, M-127, M-087, M-138 |
| 11 | **One kernel toolkit and frontend.** ttk is absent, and ttko mixes encoders, protocols and ops while carrying two parallel CB/NoC/config stacks. | 3/3 | high | M-070, M-068, M-069, M-088 |
| 12 | **Core identity as runtime data.** `specialize()` clones whole programs per core variant: 192–276 images and 1.2–4.2 s of build. The resident arena is 72 % full, text partitions are exceeded, and there is no persistent cache. | 3/3 (Fable high, others med) | high | M-032, M-026, M-027, M-031, M-033 |
| 13 | **Dispatch overhead.** Each launch is a whole-chip barrier with a DMA-idle probe per command. Trace records are fetched over PCIe twice. Tensix is reset per launch. There is one doorbell per record. | Fable high; Astra/Sol med on parts | high | M-010, M-019, M-020, M-011, M-012 |
| 14 | **A real prefill entry path.** Prompts are ingested one decode per token, and each prompt token also runs the LM head and argmax. | 3/3 | high | M-117, M-118, M-119 |
| 15 | **Device ownership and lifecycle.** The card lock exists only in pytest. Init and cleanup can leak. Mapped memory reads and writes have no bounds checks. | Astra/Sol high, Fable low | high | M-036, M-037, M-038, M-040 |

---

## 2. Master findings list

Each finding gives severity (with the spread if the models disagreed), category, goal tags, status, sources, evidence, and the merged issue and recommendation.

### 2.1 Dispatch, command queue, traces, execution lifetime

**M-001 — Async `replay(wait=False)` patches a trace the device may still be reading**
- Severity: **high** (Fable med, Astra high, Sol high) · Category: correctness · Goals: [bs-n] [training] [general] · Status: verified (race not exercised on HW)
- Sources: Fable CQ-10; Astra A001; Sol F050
- Evidence: device.py:408-432 (runtime record patch); cq.py:352-389 (final-signal patch, replay_trace).
- Issue: each replay patches the runtime record and the completion value in the same pinned trace. With `wait=False`, nothing fences the previous replay. Rec: give each submission an immutable parameter/signal block (double-buffer), or fence on the prior event before patching. Test with delayed fake prefetch.

**M-002 — Captured transfers retain recyclable staging addresses**
- Severity: **high** · correctness · [prefill] [training] [general] · verified
- Sources: Astra A002
- Evidence: device.py:532-546, 805-810, 859-884, 904-925.
- Issue: `capture_trace` rejects readbacks but accepts queued uploads whose DramCopy sources point into `cq.dram` staging, then resets `_staging_next`. A later upload overwrites bytes the replay expects. Rec: reject transient transfer records in capture, or pin dedicated staging for the trace's lifetime.

**M-003 — Completion timestamps are shared, not per event**
- Severity: **med** · correctness · [training] [general] · verified
- Sources: Astra A003; Sol F051
- Evidence: cq.py:230-231, 278-317; device.py:969-975.
- Issue: all completions overwrite one signal/timestamp slot, so `wait(N)` after N+1 completes returns the newer timestamp. `TensorDevice.run` enqueues the whole batch before reading per-program timestamps. Rec: per-event timestamp slots, or return an explicit queue-watermark timestamp. Separate profiling markers from completion values.

**M-004 — UnicastWrite accepts missing or unequal payloads**
- Severity: **high** · correctness · [general] · verified (offline repro by both)
- Sources: Astra A004; Sol F055
- Evidence: cq.py:86-98 (`size = len(blobs[0])`, no cardinality check); firmware/dispatch.c:62-74.
- Issue: two targets with one payload serialize to 128 B, and unequal payloads to 192 B. The firmware strides one payload per target and can read past the record. Rec: require non-empty unique targets, exactly one payload per target, and equal lengths. Add packet round-trip tests.

**M-005 — RUN permits duplicate core identities**
- Severity: **med** · correctness · [general] [bs-n] · verified
- Sources: Astra A005
- Evidence: cq.py:51-76, 125-141.
- Issue: the expected done-count is `len(cores)`, and rectangles are built without a uniqueness check, so duplicates mean repeated GOs and ambiguous completion. Rec: canonicalize or reject. See M-006.

**M-006 — Tensor launches bypass the raw launch's worker validation**
- Severity: **high** (Astra high, Sol med) · correctness · [general] [prefill] [bs-n] · verified
- Sources: Astra A006; Sol F064
- Evidence: device.py:230-234 vs 503-506, 951-969; program.py:368-385.
- Issue: `Device.run` checks available workers, but `TensorDevice.queue/run` do not. `TensorProgram` accepts arbitrary, duplicate or service cores. Rec: one launch validator for raw, tensor, grid, cached and traced launches.

**M-007 — A CQ timeout does not put the device or stream into a failed (poisoned) state**
- Severity: **high** · correctness · [training] [general] · verified
- Sources: Astra A007; Sol F057
- Evidence: cq.py:254-259, 290-317; device.py:951-979; contrast device.py:335-344 (upload stream does poison); tools/chat.py:82-84.
- Issue: after a timeout, queues and staging stay populated and device work may still be running. A retry can re-submit in-place updates, which is dangerous for optimizer steps. Rec: an explicit failed state that retains in-flight memory, blocks submission and requires explicit recovery. See M-008 and M-151.

**M-008 — Hang diagnostics name only an event number; unknown opcodes spin forever**
- Severity: **med** · ergonomics · [general] [training] · verified
- Sources: Fable CQ-06; Astra A012
- Evidence: cq.py:262-268, 290-301; firmware/dispatch.c:129-130; firmware/dma.c:200-201; device.py:236-249 (recovery = full close/reset).
- Issue: with 83–195 launches per token, the failing launch, core and RISC are unknown, and recovery means rebooting and re-uploading weights. Rec: tag traces with command/program IDs. On timeout, read each core's GO/sync bytes and PCs, then map them back to the program and source line. Bounded firmware error records, per-launch timeouts, and a soft recovery that keeps DRAM.

**M-009 — The CQ and trace APIs have no concurrency/ownership contract**
- Severity: **high** · design · [bs-n] [training] [general] · verified
- Sources: Astra A008
- Evidence: cq.py:270-292, 365-389; device.py:503-506, 805-925.
- Issue: queues, staging cursors, trace bytes and template dicts are all mutable with no lock or single-owner check. Chat serializes requests locally, but the framework does not enforce it. Rec: a single submission owner or documented stream objects, and fail early on violations.

**M-010 — Every RUN is a whole-chip barrier, and every non-DRAM command probes the DMA core**
- Severity: **high** (Fable high, Astra med) · perf/design · [general] [prefill] [bs-n] [training] · verified
- Sources: Fable CQ-02; Astra A009
- Evidence: firmware/dispatch.c:52-57 (`wait_dram_idle()` before every op except DRAM_COPY/SIGNAL/TIMESTAMP/DMA; re-checked by the merger), 93-114 (RUN waits for `DISPATCH_DONE_COUNT`); brisc.c:36-38, 109-117.
- Issue: 83–195 serialized launches per token, with no overlap even on disjoint cores and an in-chip round trip per command. Backward passes have real cross-launch dependencies that could overlap. Rec: event/semaphore dependencies between launches, and a DMA-idle probe only when the command touches staging. Astra: keep serial replay as the baseline but record dependencies and resource footprints so overlap can be added later. Fable: optional persistent kernels for layer loops.

**M-011 — One doorbell MMIO write and one space poll per published record**
- Severity: **med** (Fable low, Astra/Sol med) · perf · [general] [prefill] [training] · verified
- Sources: Fable CQ-07; Astra A010; Sol F054
- Evidence: cq.py:261-292.
- Issue: `cache_kernels` publishes about 952–961 records at startup. Uncaptured training/optimizer work pays this per command. Rec: reserve and publish a batch of records with one doorbell, keeping wrap handling.

**M-012 — The host busy-spins in Python while waiting for completion**
- Severity: **med** (Fable low) · perf · [general] [bs-n] [training] · verified
- Sources: Fable CQ-15; Astra A011; Sol F053 (part)
- Evidence: cq.py:293-314, 376-378 (`poll_interval=0.0`), 390-405.
- Issue: good for latency, but the thread and GIL are tied up, which does not scale to several request streams or host-side work at bs-n. Rec: configurable spin-then-sleep, native or eventfd wait, or a waiter thread. Measure CPU cost and latency separately.

**M-013 — Per-replay host overhead: the record is re-encoded and profiling runs unconditionally**
- Severity: **med** (Fable/Astra low, Sol med) · perf · [general] [bs-n] [training] · verified (measured)
- Sources: Fable CQ-16; Astra A013; Sol F053 (part)
- Evidence: device.py:390-440 (validate, dict, pack, `McastWrite.lower()`, `_record_profile` every replay); cq.py:365-405; examples/llama3/generate.py:55-67 (stores every token profile even with profile=False).
- Issue: Fable measured a 34–40 µs host median per token, of which 20–25 µs was encode. Astra measured about 9.15 µs per replay. See §3 C3 and §4. Rec: pre-lower the record and memmove the 24 changed bytes, make detailed profiling opt-in, and keep cheap counters.

**M-014 — Trace runtime parameters: 8 u32 slots matched by string name and uniform across all cores**
- Severity: **high** · design · [prefill] [bs-n] [training] · verified
- Sources: Fable CQ-04; Astra A014; Sol F061
- Evidence: firmware/consts.py:59-60 (`RUNTIME_PARAM_SLOTS = 8`); device.py:721-789 (uniformity check 775-782), 814-826, 423-430.
- Issue: per-sequence positions and lengths, per-core ranges, batch cache pointers and training controls cannot be expressed. Shapes become capture-time constants, so every new shape is a new trace (M-022). Rec: a typed per-launch descriptor or argument block (e.g. 256 B) addressed by the RUN record, written by the host or by a previous kernel. Per-core values derived from rank. Scoped typed parameter IDs instead of display names. See M-063.

**M-015 — The trace arena and parameter templates are bump-only and never retired**
- Severity: **med** · design · [bs-n] [training] [general] · verified
- Sources: Fable CQ-08; Astra A015; Sol F058 (part)
- Evidence: cq.py:197-199, 320-355; firmware/consts.py:160 (`HOST_TRACE_SIZE = 256 MiB`); device.py:757-768, 853-857.
- Issue: every capture and template install consumes arena forever, so recapture per shape or step eventually fills it. Rec: refcounted trace and plan handles with event-delayed reclamation and explicit budgets. See M-025.

**M-016 — Resident param templates live in the kernel arena, one per launch per core, with an install-order constraint**
- Severity: **med** · design · [training] [prefill] · verified
- Sources: Fable CQ-09
- Evidence: device.py:637-638, 721-803; firmware/consts.py:49-54 (160 B stride). The 8B split trace has 195 templates, about 30.5 KiB per core.
- Issue: templates and kernels share one immutable arena, and "kernels before templates" leaks into the public API. Rec: keep per-launch arguments out of worker L1, or in a separate ring (M-014).

**M-017 — Packet validation is inconsistent across record types**
- Severity: **med** (Astra low, Sol med) · correctness · [general] · verified
- Sources: Astra A016; Sol F056
- Evidence: cq.py:76-83, 106-129, 320-345, 397-438.
- Issue: empty target sets and empty records are accepted, Wait and Dma lack the address checks that Signal has, and Indirect checks only the aperture. Rec: one schema-backed ABI validator (counts, ranges, alignment, aperture, zero-length), shared with firmware decode tests.

**M-018 — Traces cannot contain readbacks, loops or conditionals; WAIT and INDIRECT records are unused**
- Severity: **med** · design · [training] · verified
- Sources: Fable CQ-05
- Evidence: device.py:809-810; cq.py:391-421 (Wait/Indirect never used, Dma used by one test); dispatch.c:116-127 (OP_WAIT polls PCIe only).
- Issue: a training step (loss readback, LR schedule, early stop) needs a host round trip per launch group. Rec: device-side WAIT on L1/DRAM signals, trace-local counted loops, and readback-to-sysmem inside traces.

**M-019 — Trace replay fetches every record from host sysmem with two serial PCIe reads; the DRAM-record path is unused**
- Severity: **high** · perf · [general] [prefill] [training] · verified (magnitude suspected)
- Sources: Fable CQ-01
- Evidence: firmware/prefetch.c:36 (64 B header read), 46-51 (re-reads the whole record from offset 0). Fable cited 184/194-198; the merger corrected these. cq.py:345-349, 366 (traces live in sysmem); device.py:548-622 (`cache_programs`/`DramRecord` have no callers outside device.py/cq.py, re-checked).
- Issue: 85–197 records per token × 2 blocking PCIe reads, estimated at 0.2–0.8 ms per token, with no prefetch pipelining. Rec: keep traces and kernels in device DRAM or dispatcher L1, fetch per page rather than per record, and let prefetch run ahead.

**M-020 — Worker firmware resets Tensix on every launch**
- Severity: **med** · perf · [general] [prefill] · verified (cost suspected)
- Sources: Fable CQ-03
- Evidence: firmware/brisc.c:19-34, 40-53, 55-73.
- Issue: about 300 MMIO stores per core per launch (zeroing 186+69 config words, 10 Tensix pushes, 32 CB counter resets, I-cache invalidate) × 83–195 launches. It also forces each kernel to rebuild all config. Rec: reset once per boot, let kernels declare the config they need, and have the backend emit only the diff.

**M-021 — Queued reads are not ordered with programs**
- Severity: **med** · correctness · [training] [general] · verified
- Sources: Astra A027; Sol F065
- Evidence: device.py:934-943, 957.
- Issue: `queue(op1); queue_read(x); queue(op2)` reads x after op2 has run, and tiled versus raw readbacks snapshot differently. Rec: one ordered compute/transfer command graph, or explicit end-of-batch snapshot semantics.

**M-022 — One trace per shape: split attention is a second whole trace**
- Severity: **med** · design · [prefill] [bs-n] · verified
- Sources: Fable LL-08
- Evidence: examples/llama3/runtime.py:400-415 (163 vs 195 launches), 422-425.
- Issue: variable M, batch or sequence length would multiply traces. Rec: runtime shape arguments (M-014).

**M-023 — Packet layout constants are hand-expanded in C**
- Severity: **low** · design · [general] · verified
- Sources: Fable CQ-14
- Evidence: firmware/dispatch.c:117-118; firmware/dma.c:117-121; firmware/__init__.py:222-231 generates only scalar `#define`s.
- Rec: generate struct definitions from `PacketLayout`.

**M-024 — Calling boot again does not invalidate host allocations, caches or traces**
- Severity: **med** · correctness · [general] · verified
- Sources: Sol F067
- Evidence: device.py:68-115, 477-494; cq.py:198-213.
- Issue: TensorDevice keeps its cache, templates and queues, and the sysmem bump allocator keeps its old CQ allocations. Rec: make boot single-use, or add a device generation that invalidates every handle.

### 2.2 Residency, kernel caches, build artifacts

**M-025 — Device residency is append-only: caches install once and reject L1 constants**
- Severity: **high** · design · [training] [prefill] [bs-n] [general] · verified
- Sources: Fable DEV-01; Astra A038; Sol F058
- Evidence: device.py:566-569 (program cache immutable), 624-638 ("resident kernels can only be installed once", templates after kernels, `_l1_constants` rejected), 763-765; ttko/ops.py:31-39 (helpers allocate L1 constants); tools/chat.py:59-65 (a model switch means close and reboot).
- Issue: backward, optimizer and prefill variants cannot be added after the first install. Rec: versioned executable handles, incremental and refcounted installation, code and constant relocations, eviction after completion, and residency budgets. See M-042 for the allocators.

**M-026 — The resident-kernel arena takes a third of L1 and is already 72 % full**
- Severity: **high** · perf/design · [prefill] [training] · verified (measured)
- Sources: Fable DEV-02
- Evidence: firmware/consts.py:42-43, 58-61 (0x12000–0x90000 = 504 KiB code+templates; data 0x90000–0x17FFE0 ≈ 960 KiB). Max resident per core: 157 KB (1B), 340 KB (8B BF16), 374 KB (8B FP8), plus about 30 KiB of templates.
- Issue: a prefill matmul wants ≥1 MiB of L1 for blocks and FP32 partials, so decode and new kernels cannot coexist. Rec: a few parametric images (M-032), a paged kernel cache with eviction, and data space covering all of L1 minus a small header.

**M-027 — Worker text partitions are fixed, unequal and already exceeded by production kernels**
- Severity: **high** · design · [general] [prefill] · verified (measured)
- Sources: Fable PRG-11
- Evidence: firmware/consts.py:25-38 (brisc/ncrisc/trisc0/1/2 = 24/8/12/8/4 KiB, re-checked); program.py:465-466 raises. Measured 8B FP8: attention BRISC 33,144 B, attention_split BRISC 57,580 B, gate TRISC1 21,380 B, and others (§4).
- Issue: `TensorDevice.run(program)` cannot launch production kernels; only the resident path works. Rec: size text per kernel from a shared arena, and use loops instead of unrolling (the attention BRISC is 7–14K instructions of unrolled gathers).

**M-028 — Cache installation mutates host state before the device install succeeds**
- Severity: **med** · correctness · [general] [training] · verified
- Sources: Astra A039; Sol F060
- Evidence: device.py:647-676, 698-711, 762-802.
- Issue: resident and template dicts and their cursors advance before capacity checks and submit. A retry then reports "already installed" or reuses templates that were never uploaded. Rec: plan, validate, upload, then commit atomically. Poison the device on an ambiguous failure.

**M-029 — Resident relocation blindly rewrites an image's final word**
- Severity: **high** (Fable/Astra med, Sol high) · correctness · [general] [prefill] [training] · verified
- Sources: Fable DEV-08; Astra A040; Sol F059
- Evidence: device.py:651-670; asm.py:336-339, 354-366 (lower appends return jump); program.py:383-386 (raw `images=` accepted).
- Issue: this is an implicit contract. A raw or nonconforming image loses its last instruction, and absolute jumps earlier in the image are not relocated. Rec: artifacts carry an entry, a return site and a relocation list, or return through a fixed trampoline word. Reject raw images whose relocations cannot be validated.

**M-030 — Firmware is recompiled with clang on every boot**
- Severity: **med** (Fable low) · perf · [general] · verified (measured)
- Sources: Fable DEV-09; Astra A035; Sol F074
- Evidence: device.py:68-69; firmware/__init__.py:139-214, 234-248 (nine compile/link/extract pipelines); `firmware/__main__.py pack` has no consumer.
- Issue: 0.24–0.38 s per boot (§4), and `chat.py` and every `tensor_device` test pay it. Rec: cache validated images by source, ABI, linker, toolchain and target fingerprint, with atomic writes and a bypass. Keep the ELF layout checks.

**M-031 — No persistent or content-keyed kernel/program cache**
- Severity: **med** (Fable low) · perf · [prefill] [bs-n] [training] [general] · verified (measured)
- Sources: Fable PRG-14; Astra A036; Sol F075
- Evidence: program.py:415-428 (memoized per object only); ttko/shard.py:32-45; examples/llama3/runtime.py:277-280.
- Issue: every process and every model switch rebuilds, taking 1.2–4.2 s. Rec: key immutable artifacts by op IR, shape bucket, layout, dtype, schedule, topology, ABI and compiler version, kept separate from device residency.

**M-032 — Per-core variation is done by cloning whole programs (`specialize`), giving 192–276 images**
- Severity: **high** (Fable high; Sol med; Fable LL-11 med) · design/perf · [general] [prefill] [bs-n] · verified (measured)
- Sources: Fable PRG-01, LL-11; Sol F076
- Evidence: program.py:423-428; ttko/shard.py:32-45, 267-280; examples/llama3/kernels.py:141-156 (keys = row counts, route, rotation), 848-851 (per-head attention variants).
- Issue: there is no runtime core rank, so every per-core constant is baked into code. Build time, arena use and upload all scale with cores × variants. Rec: one image per role, with core rank, grid position and work ranges as runtime data (GridProgram already writes `(ri, ci)` at `GRID_RANK_BASE`). Specialize only where it is proven free, and budget the variant count.

**M-033 — `specialize` combines variants without checking their shared metadata**
- Severity: **med** · correctness · [general] [prefill] [bs-n] [training] · verified
- Sources: Fable PRG-06; Astra A037; Sol F090
- Evidence: ttko/shard.py:32-45; program.py:381-384, 406-415; examples/llama3/kernels.py:1126-1129 (authors pad allocations so CB addresses match); device.py:631-634.
- Issue: the max-key variant owns params, CBs, constants and launch metadata, the other variants supply only `_kernels`, and `zip` truncates silently. Rec: compute the shared ABI and resource layout first, or compare variants and reject mismatches.

**M-034 — Mutable program objects behind identity-keyed caches**
- Severity: **med** · correctness · [training] [general] · verified
- Sources: Sol F066
- Evidence: program.py:378-389, 423-428; device.py:481-485, 647-676.
- Rec: freeze a compiled artifact plus signature, key caches by content or version, and reject builder mutation after finalization. See M-098.

**M-035 — The raw launch path re-lowers and re-uploads every image on every call**
- Severity: **low** · perf · [general] · verified
- Sources: Fable DEV-13
- Evidence: device.py:227-234 → `program.commands()` → `_writes`.

### 2.3 Device, PCIe, ownership, transfers, allocation

**M-036 — Card ownership is enforced only in pytest, and two arbiters exist**
- Severity: **high** (Fable low, Astra/Sol high) · correctness · [general] · verified
- Sources: Fable TS-07; Astra A017; Sol F068
- Evidence: tests/conftest.py:30-45 (`/tmp` flock in CardOwner); pcie.py:276-296; device.py:68-85, 236-244; tools/chat.py:18, 107, 127-140.
- Issue: open, boot and close reset the card, but the runtime, tools and CLI do not take the lock, and the docs tell users to use `tt-device-queue` instead. Two jobs can reset each other. Rec: exclusive ownership in the transport/session layer, compatible with `tt-device-queue` and used by every tool and test.

**M-037 — An initialization failure can leak an opened device**
- Severity: **high** (Astra med, Sol high) · correctness · [general] · verified
- Sources: Astra A018; Sol F018
- Evidence: examples/llama3/runtime.py:109-125 (`init_device` before try/close); tests/conftest.py:47-52 (`CardOwner.raw` boots before recording ownership).
- Rec: context-managed construction or ExitStack from PCIe open through boot, allocation and upload. Fault-inject each stage with fakes.

**M-038 — Cleanup stops at the first cleanup error**
- Severity: **med** · correctness · [general] · verified
- Sources: Astra A019; Sol F070
- Evidence: pcie.py:227-234, 263-270, 332-339; device.py:245-249; cq.py:308-310, 319-321.
- Rec: nested finally or ExitStack, aggregate errors, and an idempotent close.

**M-039 — CommandQueue construction can leak partially acquired TLB windows**
- Severity: **med** · correctness · [general] · verified
- Sources: Sol F071
- Evidence: cq.py:234-243; device.py:105.
- Rec: an exception-safe factory that transfers ownership only on full success. See M-038.

**M-040 — Raw host-memory and TLB reads/writes have no bounds or closed-state checks**
- Severity: **high** · correctness · [general] · verified
- Sources: Astra A020; Sol F069
- Evidence: pcie.py:223-225, 253-260; checks exist only in tests/isa/record.py:58-76.
- Rec: a bounded region type with offset+length and liveness checks, plus an internal unchecked hot path only where measurement justifies it.

**M-041 — The allocator accepts invalid alignments**
- Severity: **med** (Astra med, Sol low) · correctness · [general] [training] · verified (repro)
- Sources: Astra A021; Sol F030
- Evidence: pcie.py:191-200. `Allocator(5,100).alloc(4,3)` returns 5. Zero alignment can move the cursor backwards, and zero-size allocations alias.
- Rec: require a positive power-of-two alignment and define empty-allocation behavior.

**M-042 — DRAM and L1 are bump-only arenas with no free and no lifetime planning**
- Severity: **high** · design · [training] [prefill] [bs-n] [general] · verified
- Sources: Fable DEV-01 (part); Astra A022; Sol F026
- Evidence: pcie.py:191-200 (no `free`); program.py:326-368, 379-384 (per-program L1 bump); device.py:62, 476.
- Issue: training temporaries, saved activations, optimizer state, prefill activations and changing sequence slots all need reuse. Rec: separate persistent (model/optimizer), transient-step and staging arenas, with live-range planning, completion-delayed reclamation and peak per-bank/L1 reports. See M-025.

**M-043 — Allocation metadata cannot prove device ownership or alias safety**
- Severity: **high** · design · [training] [general] · verified
- Sources: Astra A023
- Evidence: program.py:143-160, 235-241; device.py:25-48, 117-153.
- Issue: buffers have no allocation ID, owning device, generation or extent, and `dataclasses.replace` builds unchecked aliases. Rec: Storage handles with owner/generation/extent plus typed views, with aliases validated.

**M-044 — The single bump pointer ignores per-bank pressure**
- Severity: **med** · design · [training] [general] · verified
- Sources: Sol F027
- Evidence: device.py:62, 129, 150; program.py:329-336, 364-365.
- Issue: single-bank and interleaved allocations advance one common 32-bit cursor even when only one bank is used. Rec: per-bank extents and reservations, with capacity and fragmentation reports. See M-046.

**M-045 — Two DRAM allocation worlds share one allocator**
- Severity: **med** · design · [general] · verified
- Sources: Fable DEV-06
- Evidence: device.py:117-225 (`alloc_dram`/`alloc_interleaved_dram`/`read_dram`/`write_dram`, used by tests) vs program.py:328-369 (`TensorDevice.dram`), aliased at device.py:476. `DramBuffer`/`InterleavedDramBuffer` vs `Buffer`.
- Rec: one allocator and one buffer type with a page-size field.

**M-046 — Pinned sysmem, staging and DRAM capacity are fixed constants, not derived from need or from the card**
- Severity: **med** (Fable low, Astra med) · design · [training] [general] · verified
- Sources: Fable DEV-11; Astra A024
- Evidence: examples/llama3/runtime.py:109 (2 GiB if 8B else 1 GiB); device.py:62 (`Allocator(0x40, 1<<32, 64)` regardless of card); cq.py:210-233 (staging = all remaining sysmem); device.py:470-480.
- Rec: size bounded pinned pools from the upload/workload plan with backpressure, and read DRAM capacity from telemetry.

**M-047 — Raw and tensor transfers fail if the whole buffer exceeds staging**
- Severity: **med** · design/ergonomics · [prefill] [training] · verified
- Sources: Astra A025; Sol F072
- Evidence: device.py:155-185, 508-516, 934-943.
- Issue: only the specialized upload stream chunks. Large activation, gradient or checkpoint readbacks cannot stream. Rec: range-based chunked upload and download with events, sharing the upload stream's lifetime rules.

**M-048 — DramCopy supports only bank prefixes, and anything else falls back to a synchronous PCIe/TLB path**
- Severity: **med** (Fable low) · perf/design · [prefill] [training] [general] · verified
- Sources: Fable CQ-12; Astra A026; Sol F073
- Evidence: cq.py:176-189 (error message "llama3 CQ firmware supports only bank prefixes"); device.py:158-163, 173 (duplicate `interleaved =`), 187-219 (`_copy_dram_pcie`), 303-311, 521-522.
- Rec: one DMA descriptor taking an arbitrary bank list, start phase, stride and page tail. Keep the PCIe fallback as an explicit debug path or delete it.

**M-049 — Topology is fixed to the P100 worker list: on a 140-core P150 the extra Tensix stay idle**
- Severity: **med** (Fable med, Astra low) · design/perf · [general] [prefill] [training] · verified
- Sources: Fable DEV-05; Astra A028
- Evidence: pcie.py:41-44 (`P100_WORKER_CORES` = 12 columns × 10 rows − 3 service = **117 workers**), 67-82 (P150 140-core only moves `service_x` to 16; "The extra tiles stay idle"); program.py:334; examples/llama3/kernels.py:851, 869, 1421, 1501; runtime.py:195.
- Rec: derive the worker grid from the enabled-column mask, and let plans opt into all validated workers. See M-124 and §3 C1.

**M-050 — Telemetry reads can cross the mapped 2 MiB TLB aperture**
- Severity: **low** · correctness · [general] · suspected
- Sources: Astra A029
- Evidence: pcie.py:305-329.
- Rec: validate telemetry extents and read through a remapping helper.

**M-051 — Implicit layout conversion on tiled read/write rebuilds a conversion program every time and keeps per-buffer scratch forever**
- Severity: **med** (Fable low) · perf/design · [prefill] [training] [general] · verified
- Sources: Fable DEV-07; Astra A041; Sol F028
- Evidence: device.py:928-944; ttko/layout.py:14-83, 524-572 (scalar BRISC permutation program per call; a readback shadow bump-allocated per Buffer identity and never freed).
- Rec: do tilize/untilize explicitly, as unpack/pack modes or host numpy. Cache conversion plans by layout and pool scratch by event lifetime. No hidden kernels in `write`/`read`.

**M-052 — Generic upload padding materializes several whole host arrays**
- Severity: **med** · perf · [prefill] [training] [general] · verified
- Sources: Sol F029
- Evidence: program.py:285-306; device.py:535-544.
- Rec: stream directly into the target physical pages with bounded host memory.

**M-053 — Weight upload is Python-driven, and the safetensor file is reopened for every 4 MiB chunk**
- Severity: **med** (Fable DEV-03 med; LL-16, A077, F077 low) · perf · [general] [training] · verified for the reopen, suspected for the throughput impact
- Sources: Fable DEV-03, LL-16; Astra A077; Sol F077
- Evidence: device.py:252-345 (two 4 MiB slots, Python `fill` callback, `ctypes.memmove`); st.py:143-160 (`readinto` opens, seeks and closes per call); examples/llama3/runtime.py:215-266 (serial `_stage_weights`). 8B BF16 is about 4000 chunks.
- Rec: a context-managed reader with persistent fds or pread and bounded read-ahead, or pin the mmapped safetensor directly. Two engines or queues in parallel. Keep the bounded direct `readinto` and the strict lifetimes. No throughput measurement exists yet.

**M-054 — Device state errors are strings, and boot has two names**
- Severity: **low** · ergonomics · [general] · verified
- Sources: Fable DEV-10
- Evidence: 8 "must be called first/before" `RuntimeError` sites: device.py:157, 231, 269, 511, 555, 627, 808, 953 (Fable said "six"; re-counted by the merger). `init_device` wraps `boot` (device.py:493-494). `reset_cores` duplicates close's reset (487-491).

### 2.4 Tensors, layout, buffers, parameter binding

**M-055 — `Buffer` conflates tensor semantics, layout, sharding, placement and host conversion**
- Severity: **high** · design · [general] [prefill] [bs-n] [training] · verified
- Sources: Fable PRG-05; Astra A030; Sol F019
- Evidence: program.py:140-306 (15 fields, derived attributes via `object.__setattr__`, `_raw_global` special case at 201-207); hand-built views with 10 positional args (examples/llama3/kernels.py:195-199, 1881-1887; runtime.py:163-167, 342-347).
- Issue: there is no tensor (dtype, shape, strides, placement) separate from a view separate from a shard plan. Kernels receive the whole bundle and reinterpret its fields. Rec: immutable Storage + logical Tensor/View (shape/strides/offset) + physical LayoutMap (exact index→byte) + a separate Sharding plan computed by the launcher, with explicit conversions. See M-056–M-058.

**M-056 — The 32×32 tile is the unit of everything; layouts cannot express general matrices, strides, transposes or subviews**
- Severity: **high** (Astra A054 med) · design · [prefill] [bs-n] [training] · verified
- Sources: Fable PRG-03; Sol F020; Astra A054
- Evidence: program.py:149-153, 165-171 (1024-element items, one boolean face-major flag), 280-306; ttko/cb.py:9-19, 33-44, 180-193 (`tile_size = 1024*itemsize`, CB page = tile); ttko/__init__.py:27-43 (Dst in whole tiles); ttko/l1.py:23-52; cq.py:166, device.py:122-127 (DRAM pages); examples/matmul_peak.py:48-69 (variable CB pages hand-built outside the registry).
- Issue: there are no tiny tiles for decode rows, no (M,N) blocks, no row-major pages wider than a tile row, and no transposed or strided views for backward. Rec: `Tile(dtype, rows, cols, layout)` + `Storage(space, tile, count, depth)`, a composable index-map/view layer with bounds, byte extents, tile order, transpose, slices and tail masks used by both transfers and kernels, and CB item extent decoupled from the tile.

**M-057 — Address low bits secretly encode a DRAM bank**
- Severity: **med** · design · [prefill] [bs-n] [training] · verified
- Sources: Sol F021; Fable PRG-05 (part), XC-03 (example)
- Evidence: program.py:220-226; ttko/noc.py:365-377 (device clears the low three bits).
- Rec: a typed descriptor with separate base/page/bank fields, or an explicitly named encoded ABI with checked construction.

**M-058 — Paged projection storage is a model-local Buffer subclass that redefines `tile_size`**
- Severity: **med** · design · [prefill] [training] [general] · verified
- Sources: Astra A043; Sol F023; Fable PRG-05 (part)
- Evidence: examples/llama3/runtime.py:31-60 (`PagedProjectionWeight`); examples/llama3/kernels.py:144-145, 362-396 (`getattr(page_tiles, ...)`); ttko/noc.py:375-377.
- Rec: separate DRAM page geometry from compute-tile geometry as a generic layout object with forward and inverse addressing.

**M-059 — Buffer accepts impossible descriptors (negative/zero shape, zero banks)**
- Severity: **med** · correctness · [general] [prefill] [training] · verified (repro by both)
- Sources: Astra A031; Sol F022
- Evidence: program.py:156-211, 346-364. `shape=(0,)`, `(-1,)` and `banks=0` all construct and report 2048 B. No checks on alignment, endpoints, duplicate cores or allocation bounds.
- Rec: validate at construction and define empty-tensor semantics. See M-060.

**M-060 — `Buffer.cores` is silently truncated when items < cores**
- Severity: **low** · correctness · [general] · verified
- Sources: Fable DEV-12
- Evidence: program.py:173 (`cores = cores[:min(max(1, items), len(cores))]`).
- Issue: a program built for N cores can receive a buffer that quietly lives on fewer.

**M-061 — Parameter rebinding checks neither the tensor signature nor the per-core cardinality**
- Severity: **high** (Fable med, Astra/Sol high) · correctness/ergonomics · [general] [prefill] [bs-n] [training] · verified
- Sources: Fable PRG-12; Astra A033; Sol F024, F063
- Evidence: program.py:314-325, 431-454; examples/llama3/runtime.py:285-290 (O projection compiled with Q's weight as placeholder), 360-385 (`{template_buffer: layer_buffer}` dicts), 371-374.
- Issue: binding is by object identity and substitutes addresses only. Nothing checks dtype, shape, page size, banks or topology. Per-core lists and tuples are not length-checked, and unknown override keys are silently ignored. Rec: named, typed kernel parameters defined independently of exemplar buffers, with compatibility and length validation before enqueue.

**M-062 — Duplicate parameter names silently collapse slots**
- Severity: **high** · correctness · [general] [training] · verified (repro by both)
- Sources: Astra A032; Sol F062
- Evidence: program.py:368-379, 437-453. Two `Const('x')` give two slots but a one-word table, and only the second value is emitted.
- Rec: reject duplicate names and identities, and use one canonical ordered signature for both codegen and serialization.

**M-063 — Launch parameters are 24 untyped u32 slots shared by pointers, scalars and pre-encoded instruction words**
- Severity: **high** · design · [prefill] [bs-n] [training] · verified
- Sources: Fable PRG-04
- Evidence: firmware/consts.py:17 (`PARAM_SLOTS = 24`, "FP8 projections need 24 argument slots"); program.py:376-379; examples/llama3/kernels.py:201-212 (qkv-FP8 uses 19 slots), 780-792.
- Issue: a prefill matmul (M, N, K, strides, batch, 3 pointers, scales) does not fit. Rec: a typed argument struct per kernel generated from its signature, with a larger region and floats passed as floats. See M-014 and M-123.

**M-064 — BF16 conversion rounds differently on different host paths**
- Severity: **med** (Fable low) · correctness · [training] [general] · verified
- Sources: Fable PRG-13; Astra A042; Sol F025
- Evidence: program.py:228-235 (`Buffer.from_numpy` truncates with `>> 16`); examples/llama3/runtime.py:510-514 (RoPE tables round to nearest even); tests/compute/fpu/test_llama_attention.py:17-19 (references reproduce truncation).
- Rec: centralized conversions with a named rounding/NaN/subnormal policy and bit-exact tests, shared by references, initializers, parameters and training state.

**M-065 — Kernel signatures are not validated; the `check_buffer` helper is unused**
- Severity: **med** · testing/correctness · [prefill] [bs-n] [training] · verified
- Sources: Astra A064
- Evidence: ttko/check.py:15-36 (only reference is its own docstring, re-checked); examples/llama3/kernels.py:69-84, 125-147, 181-199.
- Issue: new M/N/K cases can be silently flattened or truncated. Rec: first-class kernel signatures validating rank, dtype, layout, divisibility, tails and aliasing. See M-171 and M-061.

**M-066 — Raw L1 initialization can overwrite firmware, entries, parameter slots or resident kernels**
- Severity: **med** · correctness · [general] · verified
- Sources: Astra A034; Sol F089
- Evidence: program.py:70-82, 130-136; firmware/consts.py:17-60.
- Rec: region reservations, plus an explicitly named unsafe raw-write API for probes.

### 2.5 ttko, kernel authoring, synchronization, assembler

**M-067 — Kernel authors hand-write five instruction streams and hand-place all synchronization, with no verifier**
- Severity: **high** · ergonomics/design · [general] [prefill] [bs-n] [training] · verified
- Sources: Fable PRG-02; Astra A047; Sol F031
- Evidence: program.py:389-404; ttko/cb.py:117-165; ttko/sync.py:22-49; examples/llama3/kernels.py:214-217, 855-1107 (the attention program is about 250 lines of interleaved BRISC/NCRISC/TRISC code), 874-884. Fable counted 16 raw `stall/sem_*` calls, 47 calls into ttko private `_` methods and 27 `exclude=` register lists in kernels.py.
- Issue: every kernel re-derives CB credits, semaphore pairs, Dst ownership and stall masks, and errors show up as hangs on the card. Backward triples the surface. Rec: a storage/effect IR with depth and INDEX/AFTER edges. Fable wants sync **derived** (the ttk-v2 design). Astra and Sol want it **derived or verified**, keeping annotated fixed schedules. Either way: a verifier for balance, producer/consumer mismatch, alias hazards and cyclic waits, plus a raw `CUSTOM` escape with declared effects.

**M-068 — ttko mixes ISA encoders, register maps, runtime protocols, allocation and composite ops (scope creep, layering cycles)**
- Severity: **high** (Astra high, Sol med) · design · [prefill] [bs-n] [training] [general] · verified
- Sources: Astra A045; Sol F037
- Evidence: ttko/isa.py; ttko/registers.py:1-5; ttko/cb.py:25-342; ttko/noc.py:163-181, 498-759; ttko/ops.py:1-104; ttko/layout.py:9 imports `program`, which imports ttko (program.py:13-20, 368-402).
- Rec: split into pure hardware definitions, assembler/backend, runtime storage/dispatch and an operator library, with a one-way dependency graph. See M-069 and M-094.

**M-069 — Two parallel toolkits: CB, NoC, Tensix config and unpack/math/pack each exist twice (TensorProgram family vs TT-Metal-style fixed-register mixins)**
- Severity: **high** (Fable high, Sol med) · design/duplication · [prefill] [training] [general] · verified
- Sources: Fable TTK-01 (part); Sol F091
- Evidence: `cb.py:218-324 CB` vs `cb.py:326-489 CircularBufferOps`; `noc.py:163-495 NoC/Transaction` vs `noc.py:497-759 NOC/NocCfg/NocOps`; `unpack.py:99-532` vs `557-649 BlockedUnpack`; `fpu.py:49-410` vs `415-465 BlockedMath`; `pack.py:33-157` vs `180-275 BlockedPack`; `tensix.py TensixOps`. The only user of the mixins is examples/matmul_peak_kernel (kernel.py:11-13).
- Rec: one semantic layer and one lowering implementation, with thin adapters during migration and shared invariant tests. Do not delete the mixins blindly, because matmul still uses them (Astra A096). See M-071 and M-088.

**M-070 — ttk (the graph frontend) is absent; it was removed rather than finished, and its docs describe a trace-only frontend**
- Severity: **high** (Fable med) · design · [general] [prefill] [bs-n] [training] · verified
- Sources: Fable XC-04; Astra A046; Sol F038
- Evidence: git `6c0e0be Remove ttk` (earlier `e5e6759` added it; re-checked); no `ttk/` in the tree; boop-docs/blackhole-py/ttk.md:1-5, 168-170; ttk-v2-design.md:1-6 (draft); program.py:389-404 uses Asm/ttko directly.
- Issue: the seed claim "ttk is useless or nonfunctional" is best stated as "no executable frontend exists", not as a compiler defect. Rec: each frontend milestone must compile and execute a representative op (an M>1 matmul or norm) against an offline reference. Graph tracing alone does not count.

**M-071 — The blocked M>1 matmul exists only in `matmul_peak`, behind a separate assembler, ABI, CB layout and context**
- Severity: **high** · design · [prefill] [bs-n] [training] · verified
- Sources: Fable TTK-01 (part); Astra A082; Sol F039
- Evidence: examples/matmul_peak.py:46-105; examples/matmul_peak_kernel/asm.py:15-62 (own `KernelBase` re-initializing TT-Metal mailboxes and CB interfaces); kernel.py:7-20, 344-379; program.py:88-139 (GridProgram), 368-483.
- Issue: the only blocked, multicast, double-buffered matmul with K-blocking, FP32 L1 partials, half-Dst double buffering and native tilize cannot be called from a TensorProgram or the model runtime. Rec: extract its planner, schedule and blocked storage into the shared operator layer as the first-class contract primitive, including backward transpose cases. Preserve the working schedules.

**M-072 — Matmul building depends on mutable module globals and import-time environment variables**
- Severity: **med** · correctness · [prefill] [training] [general] · verified
- Sources: Astra A083; Sol F040; Fable TTK-01 (part)
- Evidence: examples/matmul_peak.py:72-98, 167, 240-262; examples/matmul_peak_kernel/asm.py:7-43 (`CONTEXT`); kernel.py:22-55, 126 (env knobs).
- Rec: an immutable schedule/build context passed explicitly and included in cache keys. Freeze env config at the application boundary.

**M-073 — Matmul input storage pads columns to multiples of 1024 elements**
- Severity: **med** · perf · [prefill] [bs-n] [training] · verified
- Sources: Astra A084
- Evidence: examples/matmul_peak_kernel/kernel.py:338-341.
- Issue: head-dim attention matrices and narrow backward problems pay heavy padding. Rec: stride-aware row layouts and block-local padding.

**M-074 — Multicast rectangle construction is duplicated and assumes topology**
- Severity: **med** · design · [prefill] [bs-n] [training] [general] · verified
- Sources: Astra A085; Sol F041
- Evidence: cq.py:39-76 (host rectangles); ttko/noc.py:197-218 (second encoder); examples/matmul_peak_kernel/args.py:39-62, 74-78 (A-row multicast split by hand at column 8, B-column by first/last row).
- Rec: one topology/collective planner producing exact recipient sets, rectangles, endpoint order and completion counts. Property-test sparse and harvested grids. See M-075.

**M-075 — Multicast sender inclusion and recipient sets are not explicit operands**
- Severity: **med** · ergonomics · [prefill] [bs-n] [training] · verified
- Sources: Sol F048
- Evidence: ttko/noc.py:163-170, 198-217, 310-320; cq.py:47-69.
- Rec: a recipient-set object resolved against placement, shared by the data and synchronization paths. See M-074 and M-103.

**M-076 — Semaphores are a global enum with fixed semantic roles**
- Severity: **high** (Fable low, Astra/Sol high) · design · [general] [prefill] [training] · verified
- Sources: Fable TTK-19; Astra A055; Sol F035
- Evidence: ttko/sync.py:22-25, 121-129 (`FPU_SFPU, MATH_PACK, UNPACK_TO_DEST, ... MATH_DONE`); ttko/fpu.py:107-116; examples/llama3/kernels.py:294, 1079-1082.
- Issue: fusing pipelines creates hidden sharing and collisions. Rec: the backend allocates semaphores per derived producer→consumer edge, with declared live ranges and exhaustion diagnostics.

**M-077 — Replay buffer and MOP ownership is manual, shared through private state, and falls back silently**
- Severity: **high** (via Astra A055; Fable/Sol med) · design · [general] [prefill] [training] · verified
- Sources: Fable TTK-09, TTK-10; Sol F036; Astra A055 (part)
- Evidence: ttko/fpu.py:52, 283-298 (grabs replay slots 16..32 lazily); ttko/sfpu.py:547, 598-612 (second `Mop(kernel,1)` on TRISC1's single MOP; inline fallback with no warning when replay is full); ttko/mop.py:56-80; examples/llama3/kernels.py:475, 485-488, 667-668, 874-875 (`p.sfpu._mop.state.replay.used.update(range(16,32))`, private `_issue`).
- Rec: replay and MOP allocation as a backend decision with a reported plan, and an error rather than a silent fallback. Stable reservation APIs.

**M-078 — Model code reaches into ttko private APIs and passes encoded instruction words as parameters**
- Severity: **med** · ergonomics · [prefill] [training] · verified
- Sources: Astra A063
- Evidence: examples/llama3/kernels.py:875, 1254 (`_mop`, `_dram_tile`); runtime.py:396 (`_sfpu_float_words`); ttko/layout.py:55.
- Rec: expose typed scalar constants, block movement, replay reservations and layout views, and lower instruction words inside the backend. See M-067 (Fable's count of 47 private calls), M-077 and M-123.

**M-079 — L1 and Dst allocation has no live-range or alias contract**
- Severity: **high** · design · [prefill] [training] · verified
- Sources: Sol F033
- Evidence: program.py:380-415; ttko/__init__.py:27-43; examples/matmul_peak.py:54-69 (hand-written aliases).
- Rec: allocate by storage lifetime and declared alias rules, with per-mode Dst footprints, and reject overlap at compile time.

**M-080 — `require_fp32()` mutates the program-wide Dst mode after capacity-dependent code may already be emitted**
- Severity: **med** · correctness/design · [general] [training] · verified (Fable); hardware effect suspected (Sol)
- Sources: Fable TTK-13; Sol F034
- Evidence: ttko/fpu.py:193-201, 249-251; ttko/unpack.py:306; ttko/__init__.py:27-43 (capacity 16→8); program.py:397-401; examples/llama3/kernels.py:356-357 (authors build a second `Fpu`/`Pack` with `Dst(False)` to escape it).
- Rec: freeze the mode per region, or verify all accesses after mode inference.

**M-081 — Dst is handed over whole, so math and pack never overlap**
- Severity: **high** · design/perf · [prefill] · verified
- Sources: Fable TTK-04
- Evidence: single `Sem.MATH_PACK` (ttko/fpu.py:107-117; pack.py:127-139); `_release_dst` ZEROACCs all of Dst. Half-sync exists only hand-rolled in examples/rmsnorm_hybrid.py and in matmul_peak.
- Rec: Dst regions as storage with depth, where the packer releases a region rather than the whole register.

**M-082 — Unpack reconfigures and fully drains on every tile**
- Severity: **high** · perf · [prefill] · verified (measured)
- Sources: Fable TTK-02
- Evidence: ttko/unpack.py:174-199, 228-248 ("This stateless path fully drains each move", line 192). 208 RISC-V words per `move_matmul` (138 with `configure_format=False`).
- Rec: configure once per phase, update only addresses per tile via ADC counters or MOP, drain at phase boundaries, and ping-pong both config contexts.

**M-083 — `Fpu.matmul` is one tile with full reconfiguration**
- Severity: **high** · perf · [prefill] [bs-n] · verified (measured)
- Sources: Fable TTK-03
- Evidence: ttko/fpu.py:249-307 (5×3 SETC16, ZEROACC, MOP rewrite plus `mop_sync` per call). 72 words on the first call, 7 cached straight-line, 53 per loop iteration.
- Rec: a blocked matmul with the K loop inside the MOP, subblock Dst tiling, double-buffered Dst halves, and config diffed once per block. See M-071.

**M-084 — Pack costs 163–168 RISC-V words per tile**
- Severity: **high** · perf · [prefill] · verified (measured)
- Sources: Fable TTK-05
- Evidence: ttko/pack.py:67-125.
- Rec: configure once per phase, update only the L1 destination per tile via a counter-driven MOP, and no `sync` per tile.

**M-085 — Build-time Tensix state caches rely on the author's `local=True` promise and are applied inconsistently**
- Severity: **med** · correctness · [general] · verified
- Sources: Fable PRG-09
- Evidence: asm.py:196-206; ttko/fpu.py:59-62 and sfpu.py:578-581 skip SETC16 on a cache hit, while unpack.py:107-108 and pack.py:50-51 never skip; mop.py:531-550.
- Issue: a loop label resets the cache, so all config is re-emitted every iteration (7 vs 53 words). A mislabeled `local=True` silently drops a required write. Rec: derive config state from control flow (dominators), or diff in the backend.

**M-086 — SFPU code is split between a tiny SSA builder and raw word lists, and transcendentals exist twice**
- Severity: **med** · design · [general] [training] · verified
- Sources: Fable TTK-11
- Evidence: ttko/sfpu.py:121-542 (8 LRegs, manual NOPs, no predication or loops), 390-517 vs examples/llama3/kernels.py:609-639 (exp/recip/rsqrt twice); raw words at kernels.py:510-543, 574-686, 1264-1376.
- Issue: backward needs silu′, softmax-backward, rsqrt′, AdamW's sqrt/div, clipping and casts. Rec: SSA SFPU with WHERE predication and library transcendentals, with the backend inserting NOPs and LOADMACRO.

**M-087 — Dtype handling is ad hoc**
- Severity: **med** · design · [training] · verified
- Sources: Fable TTK-12
- Evidence: ttko/__init__.py:4-25 (`FP8 = 26` software flag); ttko/unpack.py:178 (F32 silently becomes BF16), 296-308; ttko/pack.py:67-70.
- Issue: there are no TF32/FP16/INT paths and no FP32 Dst→L1 round trip outside matmul_peak. Rec: formats on edges only, a dtype table generated from the ISA docs, and FP32 end to end for training. See M-127.

**M-088 — Register maps are duplicated, with decimal magic addresses**
- Severity: **med** · design · [general] · verified
- Sources: Fable TTK-15
- Evidence: ttko/registers.py:9-88 (`ALU = 4293853188`), 140-157 vs firmware/consts.py:103-117; ttko/unpack.py:17-28; ttko/pack.py:12-22; ttko/noc.py:21-58 vs 498-578.
- Rec: the rewrite's typed `config.py` fields as the single source, with codegen choosing SW/RMWCIB/WRCFG/SETC16.

**M-089 — Tile layout math is implemented three times**
- Severity: **med** · design · [general] [prefill] · verified
- Sources: Fable TTK-16
- Evidence: host numpy program.py:280-306; scalar RISC-V ttko/l1.py:23-53, ttko/layout.py:524-543, kernels.py:1830-1846; Python constants kernels.py:1849-1858.
- Rec: one layout description shared by host conversions, unpack/pack address modes and view lowering. See M-056.

**M-090 — Hidden mutable state hangs off the assembler object**
- Severity: **med** · design · [general] · verified
- Sources: Fable TTK-07
- Evidence: ttko/noc.py:177-181 (`_noc_tid_allocators` via setattr); ttko/cb.py:236-246; asm.py:79.
- Rec: an explicit per-kernel context owned by the program. See M-104.

**M-091 — The CB protocol is TT-Metal's: page = tile, local only, no remote or multicast CB**
- Severity: **med** · design · [prefill] [bs-n] · verified
- Sources: Fable TTK-08
- Evidence: ttko/cb.py:180-193, 219-221; the only prototype is in tests/movement/remote_cb.py.
- Issue: operand broadcast (A rows across a grid row, x across 88 cores) has no abstraction. Rec: storage with a declared producer core, and credits returned by NoC atomic.

**M-092 — CB reserve/push/wait/pop counts and wrap safety are unchecked**
- Severity: **high** (Astra high, Sol med) · correctness · [prefill] [training] [general] · verified
- Sources: Astra A052; Sol F032
- Evidence: ttko/cb.py:105-165 (`_advance` subtracts capacity only once).
- Rec: validate static counts against depth, model producer/consumer ownership, check balance over loop bounds, handle split wrap spans explicitly, and test 16-bit rollover offline.

**M-093 — Legacy `CircularBufferOps` counters do not mask at the 16-bit wrap**
- Severity: **med** · correctness · [training] [prefill] · suspected (the merger confirmed the missing mask in code; runtime effect untested)
- Sources: Astra A053
- Evidence: ttko/cb.py:124-125, 150-152 mask with `slli/srli 16`; 195-209, 270-275 (`cb_reserve_back`/`cb_wait_front`) subtract without masking.
- Rec: unify on tested modular arithmetic. 65,536 transfers is realistic in training loops.

**M-094 — Model-specific code lives inside the framework package**
- Severity: **low** · design · [general] · verified
- Sources: Fable TTK-18
- Evidence: ttko/argmax.py (llama argmax), ttko/shard.py (llama sharding), ttko/layout.py (test-only conversion).

**M-095 — Register allocation has two policies, no spilling, and helpers that assume physical registers**
- Severity: **med** · ergonomics · [general] [prefill] [training] · verified
- Sources: Fable PRG-08 (part); Astra A048; Sol F092
- Evidence: asm.py:25-29, 64-75, 85-147 (`@scoped` helpers consume caller registers), 172-186, 248-301 (linear scan that fails on pressure and globally excludes used physical registers); program.py:389-394 (TensorProgram forces scoped physical registers); ttko/l1.py:30-40; ttko/noc.py:31-44.
- Rec: one virtual-register abstraction with spilling or structured loop-local values, every helper audited for VReg support, and pressure diagnostics. See M-096.

**M-096 — NoC helpers reject the assembler's default virtual registers**
- Severity: **med** · correctness · [prefill] [training] [general] · verified (offline repro)
- Sources: Sol F101
- Evidence: asm.py:64-68, 172-177; ttko/noc.py:31, 373-374 (`_dram_tile` recognizes only `R`); compare asm.py:101-106 (`is_reg`). The repro fails with `TypeError: unsupported operand type(s) for &=: 'VReg' and 'int'`.
- Issue: TensorProgram's forced physical mode hides this. Rec: a shared register protocol, with every public helper tested in both modes. See M-095.

**M-097 — No persistent source map; errors name instruction indices**
- Severity: **med** · ergonomics · [general] [training] · verified
- Sources: Fable PRG-08 (part); Astra A049
- Evidence: asm.py:149-166, 296-298, 323-352; tools/viewer/capture.py:33-44, 76-106 (the viewer recovers sources by monkeypatching `_emit` and walking stacks).
- Rec: carry source spans through IR, lowering, relocation and disassembly, and report the originating op, role, resource and line.

**M-098 — A lowering failure leaves the assembler and program half-finalized**
- Severity: **low** · correctness/ergonomics · [general] · verified
- Sources: Astra A050; Sol F093
- Evidence: asm.py:354-366 (`_lowered` set before assembly can fail); program.py:415-427 (scopes closed before every role lowers).
- Rec: transactional finalization into a separate immutable artifact, keeping the failed IR inspectable.

**M-099 — Literal jumps and labels bypass the finalized-state guard**
- Severity: **low** · correctness · [general] · verified
- Sources: Astra A051
- Evidence: asm.py:149-150, 234-236 (`j(int)` appends to `items` directly).

**M-100 — Assembler passes are quadratic**
- Severity: **low** · perf · [general] · verified
- Sources: Fable PRG-10
- Evidence: asm.py:273-283 (liveness fixpoint over sets), 307-321 (branch relaxation over all items per pass). Fine at 14K instructions, but prefill unrolls will grow.

**M-101 — `Asm.range` is a generator loop and `switch` is a branch chain**
- Severity: **low** · ergonomics · [general] · verified
- Sources: Fable PRG-15
- Evidence: asm.py:238-246 (labels left open if the body raises), 491-497; used per tile for bank selection (ttko/noc.py:380-384).

**M-102 — Kernels cannot `ret`; `lower()` appends the firmware return**
- Severity: **low** · ergonomics · [general] · verified
- Sources: Fable PRG-16
- Evidence: asm.py:354-356; program.py:23-26 (`RETURN_KERNEL`). See M-029.

### 2.6 NoC routing, transactions, multicast semantics

**M-103 — NoC routing policy is per-kernel folklore, and a known card-hanging combination is unchecked**
- Severity: **high** (Fable LL-06 med and TTK-17 low; Astra/Sol high) · design · [general] [prefill] [bs-n] [training] · verified
- Sources: Fable LL-06, TTK-17; Astra A057; Sol F043
- Evidence: ttko/noc.py:163-171 ("Deliberately hardcoded request policy": VCs, posted-only multicast, no `include_sender`/linked); pcie.py:37-40; examples/llama3/kernels.py:159-170 (`_projection_route`: NoC 0 with port rotation `index % 3`, or a spatial split at `noc_split_x`; "spatially split NoCs with rotated ports hung both p150a cards"); config.py:61-68; runtime.py:313-321.
- Issue: there is no model of NoC topology, VC allocation or DRAM port load. Constants are found by experiment, and a bad mix hangs the card instead of failing a check. Rec: a routing planner taking (core set, banks, bytes per core) that assigns NoC, VC and port, encodes the measured boop-docs rules as constraints, and rejects unsafe combinations before launch. Kernels take the plan as data.

**M-104 — NoC transaction IDs are allocated per instruction stream, not per physical NIU**
- Severity: **high** · correctness · [prefill] [bs-n] [training] [general] · verified
- Sources: Astra A056; Sol F042
- Evidence: ttko/noc.py:173-181; examples/llama3/kernels.py:159-177 (the writer is placed on the opposite NoC to avoid collisions).
- Rec: allocate TIDs and command buffers program-wide across both data-movement RISCs, or use a validated partition. See M-090.

**M-105 — "Wait" on a posted write or multicast drains only the source; it does not mean remote visibility**
- Severity: **high** · ergonomics/correctness · [prefill] [training] [general] · verified
- Sources: Astra A058; Sol F044
- Evidence: ttko/noc.py:103-115, 137-160, 310-320, 484-486.
- Rec: distinct source-reusable, remote-visible and consumer-ready tokens, and explicit completion protocols in collective builders.

**M-106 — Public inline-write and atomic options contradict the documented Blackhole constraints**
- Severity: **high** (Astra high, Sol med) · correctness · [general] [training] · suspected (the doc contradiction is verified; silicon failure untested)
- Sources: Astra A059; Sol F049
- Evidence: ttko/noc.py:124-135, 323-342 (`inline_write` defaults to posted=True, `atomic_inc` accepts posted=True); boop-docs/blackhole-py/ttk-v2-design.md §9 (inline L1 writes unsafe, atomics must be non-posted).
- Rec: a hardware capability/errata validation layer that routes unsupported forms to safe sequences, plus focused conformance tests.

**M-107 — The NoC issue path is synchronous and single-tile, does division plus an 8-way branch per address, and rewrites every descriptor word per request**
- Severity: **high** (Fable high; Sol med; Astra low) · perf · [general] [prefill] [training] · verified (measured)
- Sources: Fable TTK-06; Astra A062; Sol F045, F046
- Evidence: ttko/noc.py:29-44, 71-79 (Transaction creation polls two counters), 220-227 (`_local_coordinate` re-read per command, `initialize()` never called by llama), 268-283 (`_submit` spins before and after), 345-351 (every `read_tile`/`read_into_cb`/`write_from_cb` is fully synchronous), 357-385 (`remu`, `divu`, `mul` and an 8-way `beq` per tile), 405-418. One of four command buffers is used. examples/llama3/kernels.py:362-437 (custom reader escapes this path), 391 (one tile per transaction). Measured: 151 words per `read_into_cb`, 244 for two tiles.
- Rec: affine/strided iterators with precomputed bank tables and shifts, N requests batched per transaction by default, all four command buffers, stable command state kept across requests, and a cached local coordinate. Keep the checked generic form as a fallback, and measure code size as well as throughput.

**M-108 — NoC transactions allow use after release, and TID misuse gives incidental errors**
- Severity: **med** (Astra med, Sol low) · correctness · [general] [training] · verified
- Sources: Astra A060; Sol F047
- Evidence: ttko/noc.py:60-69, 96-135, 151-161 (`_closed` not checked; exhaustion via `min(empty)`; a requested TID that is unavailable fails with a set-remove error).
- Rec: linear, single-use transaction handles, and validated TID range and ownership with owner context in errors. See M-109.

**M-109 — NoC scalar range validation is incomplete**
- Severity: **med** · correctness · [general] · verified
- Sources: Astra A061
- Evidence: ttko/noc.py:64-67, 173-181, 192-203, 285-342 (NoC index, ordinary coordinates, packet lengths and TID range are unchecked; multicast endpoints are checked).
- Rec: checked coordinate, address, length and TID types, plus an explicit unsafe encoder layer.

### 2.7 Llama runtime, model state, KV cache, weights

**M-110 — The projection kernel is a single-vector GEMV that erases the token/batch dimension**
- Severity: **high** · design/correctness · [prefill] [bs-n] [training] · verified
- Sources: Fable LL-01; Astra A065; Sol F002
- Evidence: examples/llama3/kernels.py:119-135, 185-199 (K from `x.shape[1]`, flat `decode_token` view), 291-313 (one scalar per row through `scalar_cb`), 448-507 (ELWMUL weight-row × x, SFPU lane sums, 32-lane butterfly); runtime.py:173-190.
- Issue: it neither rejects M>1 nor computes a matmul. For bs-n or prefill the projection must become Y[M,N] = X[M,K]·Wᵀ with blocking and a different output layout. Rec: one blocked GEMM interface (M/N/K, transposes, strides, tails, epilogues). Fable wants tiny tiles at M=1 so that no separate kernel is needed. Astra and Sol want to keep GEMV as the M=1 *schedule* of the same interface. See M-071 and §6.

**M-111 — Activations, hidden state and context are allocated for exactly one token**
- Severity: **high** · design · [prefill] [bs-n] · verified
- Sources: Sol F001
- Evidence: examples/llama3/runtime.py:173-190; config.py:114-116.
- Rec: logical `[batch, sequence, features]` lowered to explicit tile views with runtime valid extents. See M-112.

**M-112 — Compact projection outputs encode core placement into tensor semantics**
- Severity: **high** · design · [prefill] [bs-n] [training] · verified
- Sources: Astra A066
- Evidence: examples/llama3/runtime.py:140-143, 179-191; kernels.py:119-123 (compact = one tile per core holding its rows), 1861-1887 (attention gathers features from shards).
- Rec: placement-independent logical outputs plus explicit sharded layout views, with the plan inserting conversions. See M-110 and M-120.

**M-113 — Attention packs GQA heads into rows and has no query-length, batch or mask dimension**
- Severity: **high** · design · [prefill] [bs-n] [training] · verified
- Sources: Fable LL-02; Astra A067; Sol F003
- Evidence: examples/llama3/kernels.py:824 (`GQA_ROW_CHUNKS`), 827-872 (head→core, scalar position/blocks/tail), 1037-1068, 1110-1119, 1155-1193 (BRISC gathers 128 2-byte values per head and builds RoPE tiles by scalar stores), 1226-1261 (single-position append, 16-element writes), 1264-1376; runtime.py:426-432.
- Issue: 28 of 32 score rows sit idle. Causal multi-query prefill, ragged batches and attention backward cannot be expressed. Rec: explicit batch/head/query/key dims with per-query causal bounds and ragged lengths, KV append separated from the attention contract (fusable), RoPE as an SFPU tile op, and attention as Contract+Scan over (query rows, KV blocks).

**M-114 — Norm, activation and quantization fusion is vector-specific and tied to the projection builder**
- Severity: **high** · ergonomics/design · [prefill] [bs-n] [training] · verified
- Sources: Sol F004
- Evidence: examples/llama3/kernels.py:125-134, 246, 549-550, 688; ttko/ops.py:41-83.
- Rec: independently testable row norm, activation and reduction operators composed as epilogues over a common M>1 block interface. See M-120.

**M-115 — The KV cache is one monolithic fixed-capacity sequence per layer**
- Severity: **high** · design · [bs-n] [prefill] [training] · verified
- Sources: Fable LL-03; Astra A068; Sol F010
- Evidence: examples/llama3/config.py:52-60, 112-116 (`(kv_heads, max_tokens/32 × head_tiles, 1024)`, 8192 tokens); runtime.py:198-210, 417-437, 447-469; tools/chat.py:19, 50-85 (prefix reuse is a Python token list in the tool).
- Rec: a KV/sequence manager with slots or a block table (`(batch_or_page, kv_head, block, tile)`), per-sequence lengths in the argument block, an allocate/free/reuse API and prefix ownership. Keep training's saved activations separate from inference KV.

**M-116 — The runtime does not track which KV prefix is valid**
- Severity: **high** (Astra med, Sol high) · correctness · [bs-n] [prefill] [general] · verified
- Sources: Astra A070; Sol F011
- Evidence: examples/llama3/runtime.py:417-433, 447-469; tools/chat.py:50-62.
- Issue: `decode(position)` checks only the range, and `load_tokens(start=...)` trusts the caller's prefix claim, so stale or uninitialized KV can be attended. Rec: runtime-owned committed lengths and generations, with suffixes invalidated on edit and committed atomically after completion.

**M-117 — Prompt ingestion is token-by-token decode**
- Severity: **high** · perf · [prefill] · verified
- Sources: Fable LL-15
- Evidence: examples/llama3/generate.py:72-76; tools/chat.py:81-85 (one `decode()` per prompt token, 6–33 ms each); README states it.
- Issue: this is the headline prefill motivation, blocked by M-110, M-113 and M-082–M-084. See M-118.

**M-118 — Every prompt token also runs the LM head and argmax**
- Severity: **high** · perf · [prefill] [general] · verified
- Sources: Astra A069; Sol F013
- Evidence: examples/llama3/runtime.py:400-415, 417-437; generate.py:71-76.
- Issue: `logits=False` only skips the host read, and `append=False` only flips a flag. The vocab projection and reduction still run every time. Rec: separate forward-only/prefill and sampling plans, with logits optional at the final position. See M-117.

**M-119 — KV caches are zeroed by uploading host zeros: 1 GiB for 8B, 256 MiB for 1B**
- Severity: **med** · perf · [general] [bs-n] [prefill] · verified (size computed)
- Sources: Fable DEV-04; Astra A072; Sol F012
- Evidence: examples/llama3/runtime.py:231-241; config.py:112-114. This is currently needed because masked columns still multiply stale V rows (kernels.py:1058-1059).
- Rec: a device-side fill (multicast zero tile or packer-zero), or masking so stale rows are never read. Separate validity from initialization, and add poison-tail tests.

**M-120 — Activation traffic: 88 cores each re-read the whole x, RMSNorm and residual are recomputed per core, and outputs are scattered in ≤16-element writes**
- Severity: **med** · perf · [general] [bs-n] · verified
- Sources: Fable LL-04
- Evidence: examples/llama3/kernels.py:226-270, 259-261, 714-774 (`_scatter_dense`).
- Rec: multicast x once per grid row or column, keep the residual stream resident on its owning cores, and produce row-major outputs via pack untilize.

**M-121 — Attention workers sharing a KV head each repeat the same KV append**
- Severity: **low** · perf · [bs-n] [prefill] · verified
- Sources: Astra A071
- Evidence: examples/llama3/kernels.py:1119-1120, 1226-1261.
- Rec: one owner per KV head and sequence publishes readiness, or a dedicated or fused append stage.

**M-122 — Weights are consumed as row-major rows, but prefill needs tile-major or unpack-tilize**
- Severity: **med** · design · [prefill] · verified
- Sources: Fable LL-05
- Evidence: examples/llama3/runtime.py:146-153 (`tilized=False`, 2-tile pages); kernels.py:362-445.
- Rec: one DRAM layout (row-major, tile-row pages) plus an unpack-tilize mode for W. boop-docs measured a loss of ≤5.5 % for FP8.

**M-123 — FP8 scales are passed as SFPLOADI instruction words and must be uniform per fused launch**
- Severity: **med** · design · [training] [general] · verified
- Sources: Fable LL-07
- Evidence: examples/llama3/kernels.py:780-799 (words written to INSTRN_BUF at runtime); runtime.py:387-396 (identical input scales required).
- Rec: floats in the argument block, a library load op, and per-channel scales as tensors. See M-078 and M-063.

**M-124 — Llama placement constants ignore the device**
- Severity: **low** · design · [general] · verified
- Sources: Fable LL-10
- Evidence: `P100_WORKER_CORES[:32]`, `[:8]`, `[:attention_cores]` at runtime.py:195 and kernels.py:851, 869, 1421, 1501. See M-049.

**M-125 — One config mixes model facts, checkpoint, placement and tuning**
- Severity: **med** (Fable low) · design · [prefill] [bs-n] [training] [general] · verified
- Sources: Fable LL-13; Astra A073; Sol F006
- Evidence: examples/llama3/config.py:32-79 (`projection_cores`, `attention_cores`, `noc_split_x`, `fp8_page_tiles`, `split_attention_from`; many are unannotated class attributes).
- Rec: split ModelConfig, ExecutionShape, PrecisionPolicy, ScheduleConfig and checkpoint format, validated independently, with resolved plans serialized.

**M-126 — Kernel dimensions silently assume powers of two and exact divisibility**
- Severity: **med** · correctness · [prefill] [bs-n] [training] · verified
- Sources: Astra A074; Sol F005
- Evidence: examples/llama3/config.py:99-114; kernels.py:185-186, 862, 967-974, 1137-1139, 1238-1240, 1704-1708 (`bit_length()-1` shifts, the argmax 32-token block).
- Rec: validate preconditions centrally, use generic tail and index lowering, and test odd M/N/K and ragged lengths.

**M-127 — Inference precision choices are baked into builders that look reusable**
- Severity: **high** · design · [training] [general] · verified
- Sources: Sol F009
- Evidence: examples/llama3/runtime.py:157-162, 176-190, 208-211; kernels.py:205-218.
- Rec: compute, accumulation, storage, rounding and gradient precision in operator signatures, with validated combinations. See M-087 and M-064.

**M-128 — No training execution contract: no saved activations or recompute, gradients, master weights, optimizer state or update ordering**
- Severity: **high** · design · [training] · verified (capability gap)
- Sources: Astra A044; Sol F007, F008
- Evidence: examples/llama3/runtime.py:173-211 (two residual buffers and shared intermediates overwritten every layer), 215-265, 351-396; program.py:143-160, 315-321; ttko/ops.py:1-104. A search found no backward, Adam or gradient code.
- Rec: operators declare backward-required values. An explicit forward/backward/optimizer plan (tape or schedule) with activation checkpointing, typed parameter/state groups, FP32 master and moments, gradient accumulation, tied-weight identity, deterministic update ordering and mutation/version contracts. A general autograd engine is not required (Sol). Sol split this into two findings.

**M-129 — Token history has two writers, and token upload bypasses the CQ and transfer layer**
- Severity: **med** (Fable low, Sol med) · design · [prefill] [bs-n] [general] · verified
- Sources: Fable LL-12; Sol F016
- Evidence: examples/llama3/runtime.py:458-469 (drains, opens its own TLB window, rebuilds bank addressing) vs kernels.py:1669-1687 (device RMW of a 4 KiB page per token).
- Rec: bounded async slice writes through the transfer layer, ordered with compute.

**M-130 — Generated-token results are tied to the fixed 128 KiB CQ live region (8192 × 16 B)**
- Severity: **med** (Fable low, Sol med) · design/correctness · [bs-n] [general] · verified
- Sources: Fable LL-14; Sol F015
- Evidence: firmware/consts.py:161 (`HOST_LIVE_SIZE = 128 KiB`, re-checked); config.py:55 (`max_tokens = 8192`); runtime.py:327-330, 439-445; kernels.py:1660-1667. `decode()` also has a fixed 30 s timeout.
- Rec: typed result buffers or futures per submission or sequence, with capacity validated independently of context size.

**M-131 — The host API cannot reach the final cache position**
- Severity: **low** · correctness · [general] · verified
- Sources: Sol F014
- Evidence: examples/llama3/runtime.py:420-421 (`position < max_tokens - 1`), 453-454 (re-checked).
- Rec: separate the consume-position limit from the append/result limit.

**M-132 — Runtime-state update logic is duplicated between host and device**
- Severity: **med** · design · [bs-n] [general] · verified
- Sources: Sol F094
- Evidence: examples/llama3/runtime.py:408-410, 426-432 vs kernels.py:1690-1715 (argmax mirrors field order and position math with raw L1 writes).
- Rec: a generated runtime-state schema with a single description of state transitions. See M-133.

**M-133 — Argmax computes and multicasts an "autonomous" next-token runtime update that every replay overwrites**
- Severity: **low** · dead-code · [general] · verified
- Sources: Fable LL-09 (part); Sol F095
- Evidence: examples/llama3/kernels.py:1690-1716; runtime.py:426-433; cq.py:359-378.
- Rec: choose host-driven or autonomous control explicitly, and keep autonomous only with a tested loop.

**M-134 — Unused decode allocations obscure the actual forward storage**
- Severity: **low** · dead-code · [general] [training] · verified
- Sources: Fable LL-09; Astra A080
- Evidence: examples/llama3/runtime.py:178-188 (`normalized`, `k_heads`, `v_heads`, `hidden` allocated and never consumed; `q_heads` only a placeholder param), 291-339; vulture flags `host_result_reads` and `decode_launch_count`.
- Rec: derive allocations from the plan and distinguish metadata-only views from allocated storage.

**M-135 — Checkpoint and model validation happen after device init and partly after upload**
- Severity: **med** · correctness/ergonomics · [general] [training] · verified
- Sources: Astra A076; Sol F017
- Evidence: examples/llama3/runtime.py:85-96, 109-125, 215-265, 387-396.
- Rec: validate an offline load plan (all tensors, ties, scales, bytes, topology fit, memory budget) before acquiring the card. See M-136.

**M-136 — The FP8 checkpoint scale schema is only partly validated**
- Severity: **med** · correctness · [general] [training] · verified
- Sources: Astra A075
- Evidence: examples/llama3/runtime.py:87-96 (mode detected from one scale name), 387-396 (first FP32 element read without dtype, shape, positivity or finiteness checks).

**M-137 — Safetensor parsing has no header size bound or duplicate-key rejection**
- Severity: **low** · correctness · [general] · verified
- Sources: Astra A078; Sol F096
- Evidence: st.py:58-84, 93-124 (`json.loads` keeps the last of any duplicate key; an unhashable dtype gives a bare TypeError; shard index trusted; gaps and trailing data unchecked).
- Rec: bound metadata, reject duplicates, and fuzz with malformed files. Keep the existing overlap and range checks.

**M-138 — Checkpoint support is read-only, with no training persistence**
- Severity: **med** · design · [training] · verified
- Sources: Astra A079
- Evidence: st.py:49-160; examples/llama3/runtime.py:215-265.
- Rec: streaming, atomic checkpoint writes at a completed-step event, covering optimizer state, tied weights, RNG and step, with round-trip restore tests.

**M-139 — The runtime constructor couples checkpoint, boot, upload, build and capture, so offline planning is impossible**
- Severity: **med** · testing/ergonomics · [general] [prefill] [bs-n] [training] · verified
- Sources: Astra A081; Sol F100
- Evidence: examples/llama3/runtime.py:82-125, 277-280; tools/bench_llama_upload.py:14-15 (subclasses to suppress builds); tools/viewer/capture.py:28-30. All three audits had to use `__new__` and synthetic devices.
- Rec: pure plan, build, checkpoint-prepare, install and execute stages with dependency-injected transport.

### 2.8 Tools (viewer, benchmarks, chat)

**M-140 — Offline capture is a monkeypatch convention, not a supported backend**
- Severity: **med** · testing · [general] · verified
- Sources: Fable TL-01; Sol F084
- Evidence: tools/viewer/capture.py:21-33 (`PCIDevice.__init__`, `TLBWindow.__init__` and `Device.__init__` replaced), 44-69 (`OfflineDevice`), 117-121.
- Rec: a `Transport` interface (read/write/doorbell/wait) with a shipped fake and documented capabilities. Keep partial capture clearly distinct from a passed numerical test. See M-141.

**M-141 — The viewer's fake harness no longer implements its owner interface, so `h.core` raises immediately**
- Severity: **med** · correctness · [general] · verified (Astra reproduced it offline; the merger confirmed it in code)
- Sources: Astra A086
- Evidence: tools/viewer/capture.py:47-60 (`OfflineDevice` has no `raw()`, and `__getattr__` raises `HardwareBoundary`), 63-65 (`CaptureHarness.launch` uses `self.core` when `core=None`); tests/harness.py:17-23 (`RawHarness.device` → `self._card.raw()`).
- Rec: a shared device-provider protocol, implemented by the fake, plus an offline smoke test. See §3 C2.

**M-142 — Viewer fixture substitution does not cover the `card` dependency**
- Severity: **med** · testing · [general] · suspected
- Sources: Astra A087
- Evidence: tools/viewer/capture.py:116-121, 177-179; tests/conftest.py:63-84 (`bh` depends on session `card`, which skips without `--bh-hardware`).
- Rec: override the whole card/bh provider chain.

**M-143 — The viewer cache fingerprint ignores firmware C, header and linker files**
- Severity: **low** · correctness · [general] · verified
- Sources: Astra A088
- Evidence: tools/viewer/server.py:25-30; firmware/__init__.py:217-218.

**M-144 — The viewer re-crawls the source tree on every catalog or case request**
- Severity: **low** · perf · [general] · verified
- Sources: Astra A089
- Evidence: tools/viewer/server.py:25-30, 44-58.

**M-145 — `device_us` is a host-observed busy-wait interval, and `wall_us` excludes the result read**
- Severity: **med** · ergonomics/correctness · [general] · verified
- Sources: Astra A090; Sol F052; Sol F078 (part)
- Evidence: device.py:433-439; cq.py:378-405; tools/bench_llama_decode.py:72-86; examples/llama3/generate.py:113-119; runtime.py:434-437.
- Rec: report host submit, host wait, full API latency and device-timestamp interval separately, using trace markers for device time.

**M-146 — Benchmark results lack the provenance needed for rewrite comparisons**
- Severity: **med** · testing · [general] · verified
- Sources: Astra A091; Sol F078
- Evidence: tools/bench_llama_decode.py:72-91; tools/bench_llama_upload.py:25-37; tests/isa/record.py:18-27 (ISA recorder hashes omit examples).
- Rec: a benchmark manifest with source hash and dirty state, firmware/toolchain fingerprint, checkpoint identity, topology, warmup policy, distributions and numerical metrics.

**M-147 — The benchmark keeps a fragile legacy `--source` compatibility branch**
- Severity: **low** · dead-code · [general] · verified
- Sources: Fable TL-02; Sol F079
- Evidence: tools/bench_llama_decode.py:39-50 (the legacy branch sets `cfg = Llama3Kernels(...)` and line 50 then reads `cfg.checkpoint`; whether old sources have it is unverified). Fable cited lines 198-215, but the file is only 97 lines; see §3 C9. tools/bench_llama_upload.py:14-15.
- Rec: test supported historical adapters or delete them.

**M-148 — Result JSONs live under tools/**
- Severity: **low** · dead-code · [general] · verified
- Sources: Fable TL-03
- Evidence: tools/llama_argmax_results.json, tools/llama_fp8_speedup_results.json (boop-docs is the stated home for measurements).

**M-149 — Chat owns one global model and cache, and rejects concurrent requests with 409**
- Severity: **med** (Fable low) · design · [bs-n] [general] · verified
- Sources: Fable TL-04; Astra A094
- Evidence: tools/chat.py:15-25, 36-62, 106-107, 130.
- Rec: separate model residency from request/session objects, and queue requests into compatible batches with per-sequence cancellation and cache ownership.

**M-150 — Chat binds 0.0.0.0 with no authentication**
- Severity: **med** · correctness/security · [general] · verified
- Sources: Astra A093
- Evidence: tools/chat.py:97-118, 127-140.
- Rec: default to loopback, and make remote serving an explicit policy with auth and request budgets.

**M-151 — A chat error or client disconnect can leave a failed runtime in use**
- Severity: **med** · correctness · [bs-n] [general] · verified
- Sources: Sol F097
- Evidence: tools/chat.py:57-84, 114-120 (generator close bypasses `except Exception` cleanup).
- Rec: a runtime fault state (M-007) plus generation-scoped cleanup.

**M-152 — Tokenization normalization is duplicated and inconsistent**
- Severity: **low** · correctness · [general] · suspected
- Sources: Astra A092
- Evidence: examples/llama3/generate.py:27-34; tools/chat.py:44-46; tools/bench_llama_decode.py:60-65.

**M-153 — Benchmark context validation has edge inconsistencies**
- Severity: **low** · correctness · [general] · verified
- Sources: Sol F099
- Evidence: tools/bench_llama_decode.py:60-64 (`--context 0` bypasses the truthiness check, re-checked); generate.py:37-43 (different capacity boundary).

**M-154 — The dependency and install contract omits test tooling**
- Severity: **low** · ergonomics · [general] · verified
- Sources: Astra A095
- Evidence: requirements.txt:1-3; tests/conftest.py:4; README.

### 2.9 Tests and harness

**M-155 — Almost no offline tests of the host runtime; nearly every test file needs the card**
- Severity: **high** · testing · [general] [prefill] [bs-n] [training] · verified
- Sources: Fable TS-01; Astra A097; Sol F080
- Evidence: 81 `test_*.py` files. Only tests/isa/test_encoding.py, tests/isa/test_audit.py and tests/test_llama_paged_weights.py avoid hardware fixtures (the merger re-counted; Fable also listed test_profiler.py, but it takes `bh`). Sol ran 9,540 offline tests, which pass but cover encodings and paging metadata. Nothing offline exercises CQ record lowering, `rectangles`, pad/unpad, `TensorProgram.commands`, capture/patch, relocation, Asm allocation, delayed CQ consumption, async trace reuse, partial install or poisoned retries.
- Rec: a deterministic fake transport/CQ with controllable progress and failure, golden-record and image tests, and lifetime/ordering/rollback tests. Fable showed the whole llama build/capture/replay runs on a fake CQ.

**M-156 — No reference model or interpreter for kernel-program semantics**
- Severity: **high** · testing · [training] [prefill] [bs-n] · verified
- Sources: Fable TS-02; Astra A098
- Evidence: hardware-only numerics (tests/compute/fpu/test_llama_attention.py:23-80, tests/compute/sfpu/test_llama_argmax.py); ttko/ops.py:1-104; ttk-v2-design.md §10 proposes an interpreter; blackhole-py-rewrite/interactive/*.js has packer/unpacker models.
- Rec: numpy references per op (forward and backward), plus a small executor for views, transfers, effects, CB/semaphore/Dst state and precision boundaries that can catch hangs and layout errors. This is not a cycle-accurate simulator (Astra).

**M-157 — Numerical tests do not cover prefill, bs-n, backward or the optimizer**
- Severity: **high** · testing · [prefill] [bs-n] [training] · verified
- Sources: Astra A099; Sol F081
- Evidence: tests/compute/fpu/test_llama_attention.py:22-80 (one query position, fixed 32/8 heads); tests/compute/sfpu/test_llama_argmax.py:18-19; examples/llama3/__init__.py:1.
- Rec: M=1 vs M>1 equivalence, batch vs independent runs, ragged masks, odd tails, finite-difference and analytic gradients, and multi-step AdamW with checkpoint resume. Sol's first acceptance slice: one 1B layer at M=1 and M=32, ragged batch decode, backward checked against a CPU reference, then several AdamW steps.

**M-158 — The long-context unsplit attention test relaxes its accuracy assertion**
- Severity: **med** · testing · [prefill] [training] [general] · verified
- Sources: Astra A100; Sol F082
- Evidence: tests/compute/fpu/test_llama_attention.py:73-80 (at 4096 tokens only finiteness and split improvement are checked).
- Rec: declare per-op, per-length error envelopes, and mark unsupported schedules explicitly.

**M-159 — Regression tests are mixed with experiments, and some scripts open the card at import**
- Severity: **med** · testing · [general] · verified
- Sources: Fable TS-03; Sol F087
- Evidence: tests/probes/, tests/movement/dram_patterns/ (scripts plus about 30 result JSONs), tests/timing/evidence/*.jsonl, tests/isa/evidence/*.json; tests/movement/dram_patterns/wallclock.py:5 (`d = Device(0)` at module level); tests/compute/fpu/bench_matmul_compute_only.py:97; tests/movement/bench_dram_bandwidth.py:149.
- Rec: `tests/` holds deterministic regression only and `experiments/` holds probes. Hardware scripts go behind `main`, with a static check that collection never opens the card.

**M-160 — Every `tensor_device` test reboots the device (including the clang build)**
- Severity: **med** · testing · [general] · verified
- Sources: Fable TS-04
- Evidence: tests/conftest.py:96-107.

**M-161 — The harness wraps only the raw Device, and the profiler's L1 is not reserved**
- Severity: **low** · testing · [general] · verified
- Sources: Fable TS-05
- Evidence: tests/harness.py (`RawHarness` over `alloc_dram`/`launch`); tests/profiler.py:12-13 (uses `DATA_BUFFER_SPACE_END - 32`, next to `RUNTIME_PARAM_BASE`, with no allocator reservation).

**M-162 — Test fixtures clone internal device dicts**
- Severity: **low** · testing · [general] · verified
- Sources: Astra A101
- Evidence: tests/movement/test_upload_stream.py:11-23 (`Device.__new__` plus a copied `__dict__`).

**M-163 — The hardware test lock can block indefinitely**
- Severity: **low** · ergonomics · [general] · verified
- Sources: Astra A102
- Evidence: tests/conftest.py:40-44, 73-79 (blocking flock with no timeout or owner info). See M-036.

**M-164 — The paged-weight tests declare 8 banks but pass the 7-bank P100 endpoint list**
- Severity: **low** · testing · [general] · verified (the merger re-checked)
- Sources: Sol F083
- Evidence: tests/test_llama_paged_weights.py:4, 10-12, 30-32, 37-39; pcie.py:15-19.

**M-165 — The hardware fixture cannot recover from a failed kernel**
- Severity: **med** · testing · [general] · verified
- Sources: Sol F085
- Evidence: tests/conftest.py:47-56, 82-92; tests/harness.py:18-19, 57-68.
- Rec: propagate the fault state and add controlled owner recovery between tests.

**M-166 — Zero initialization can hide missing device writes**
- Severity: **med** · testing · [training] [general] · verified
- Sources: Sol F086
- Evidence: tests/harness.py:25-40; tests/compute/fpu/test_llama_attention.py:37.
- Rec: poison fills, canaries, redzones and checks on the written region.

**M-167 — Tests and tools depend on private or example implementation state**
- Severity: **med** · ergonomics · [prefill] [training] [general] · verified
- Sources: Sol F088
- Evidence: tests/compute/fpu/test_llama_attention.py:6, 49-60; examples/matmul_peak_kernel/prepare.py:15-16, 32-35; tools/viewer/capture.py:76-106.
- Rec: stable artifacts, source maps, resource plans and operator contracts.

### 2.10 Dead code, duplication, cross-cutting

**M-168 — Two near-identical capture/replay code paths (compact vs legacy PARAM patching)**
- Severity: **med** · dead-code · [general] · verified
- Sources: Fable CQ-11
- Evidence: device.py:408-464, 814-926 (two branches of about 55 lines). Llama uses only the compact path.

**M-169 — Stale, unused CQ and firmware-build symbols and compatibility surfaces**
- Severity: **low** · dead-code · [general] · verified
- Sources: Fable CQ-13; Astra A096
- Evidence: cq.py:5, 12 (unused imports `CQ_STATE`, `DRAM_*_READY`, `HOST_TRACE_SIZE`); `Timestamp.us`, `issue_write`, `pcie_mid` (vulture); firmware/consts.py:171 (`INDIRECT = TRACE` alias); firmware/__init__.py:234-236 (ignored `pcie_mid`/`dram_endpoints` arguments); cq.py:203, 411-438 (the Command union omits Wait/Indirect/Dma/DramRecord/Trace); ttko/tensix.py:22-40 (unused `trisc_id` params).
- Rec: inventory callers, delete or deprecate, and unify command typing. Migrate the live legacy helpers that matmul still uses deliberately.

**M-170 — Dead and duplicated program code**
- Severity: **med** · dead-code · [general] · verified
- Sources: Fable PRG-07
- Evidence: `Ops` is attached to every program (program.py:402) with no callers in examples or tests. `GridProgram` is used only by matmul_peak. `Program.commands`, `GridProgram.commands` and `TensorProgram.static_commands` each re-implement entry, text and param writes (program.py:46-85, 119-135, 456-480). `Buffer.storage_shape`, `from_safetensor`, `bind` and `cbs` are unused. `from_numpy` is used only by tests (see §3 C6).

**M-171 — Dead and duplicated ttko code**
- Severity: **low** · dead-code · [general] · verified
- Sources: Fable TTK-14; Astra A096 (part: re-export shadowing)
- Evidence: ttko/ops.py (no callers outside `program.py:402`); ttko/check.py (no callers); `CB.reset_counters` (firmware already does this, brisc.c:11-17); `Fpu.copy_a`; `Broadcast.ROW`. Ruff reports F811 ×19 and F401 ×22 (re-exports from registers.py, unpack.py:8-9, pack.py:8-9, fpu.py:7-8, cb.py:3-5). layout.py has circular imports (9, 558).

**M-172 — Static analysis debt**
- Severity: **low** · dead-code · [general] · verified (measured)
- Sources: Fable TS-06
- Evidence: ruff (F, E9, B, PLW, PLE) 89 findings: 22 unused imports, 19 redefinitions, 21 B023 loop closures, 16 `zip` without strict, and more. pyflakes 42. vulture about 110 symbols.

**M-173 — Docs and evidence lack source-version linkage**
- Severity: **low** · testing/dead-code · [general] · verified
- Sources: Astra A103; Sol F098
- Evidence: boop-docs/blackhole-py/runtime.md:3-5 (older snapshot); ttk.md:1-5, 168-170 (absent package); ttk-v2-design.md:1-6; examples/llama3/runtime.py:10-12, 351-352 ("same five kernels" is stale); tests/isa/test_encoding.py:14-18.
- Rec: a machine-readable source/ABI fingerprint on docs and artifacts, and CI checks on examples and API links.

**M-174 — Errors are untyped `ValueError` strings at build time and hangs at run time**
- Severity: **med** · ergonomics · [general] · verified
- Sources: Fable XC-02
- Evidence: about 150 `raise ValueError(...)` across the host layer. Run-time faults hang (M-008).
- Rec: an error hierarchy: BuildError with source location, LaunchTimeout with per-core state, LayoutError.

**M-175 — Invariants are documented in comments next to the hack instead of being checked**
- Severity: **low** · ergonomics · [general] · verified
- Sources: Fable XC-03
- Evidence: program.py:224-226; examples/llama3/kernels.py:1126-1128, 159-170; ttko/unpack.py:236-238.
- Rec: turn them into verifier checks.

**M-176 — Prefill, backward and optimizer kernels cannot be written until the core dependency chain is fixed**
- Severity: **high** · design · [prefill] [bs-n] [training] · verified
- Sources: Fable XC-01
- Issue: the dependency graph:
  - The tile model (M-056) and the argument model (M-063, M-014) decide the tensor API.
  - The blocked matmul (M-083) needs pipelined unpack/pack (M-082, M-084) and Dst regions (M-081).
  - bs-n needs the KV layout (M-115) and attention rows (M-113).
  - Training needs freeable resources (M-025, M-042) and FP32 typed paths (M-087).

---

## 3. Conflicts between the reports, and how they were resolved

Each conflict was checked against the code at `dd4f882` by reading only. No device was opened and no runtime was executed. The merger tried one pure-Python microbenchmark (C3), but the sandbox blocked it.

**C1. How many cores, and how many sit idle.** Fable (DEV-05) speaks of "the 120-core P100 layout" and says a 140-core p150 leaves "20 cores idle". Astra measured with "the standard 117-worker set" (A028, §3).
- Resolution: **both are right; they count different things.** `pcie.py:41-44` builds `P100_WORKER_CORES` from 12 columns × 10 rows minus `(14,2),(14,3),(14,4)`, which gives **117 workers**. The board has 120 Tensix: 117 workers plus 3 service cores.
- On a 140-core P150, `pcie.py:67-82` keeps the 117 workers and moves the service cores to x=16. That leaves 17 new Tensix at x=15/16 and the 3 old x=14 service slots unused: **20 idle Tensix**.

**C2. Does offline viewer capture work?** Fable TL-01 describes the viewer as getting "offline captures" by monkeypatching three constructors. Sol F080 says the fake "stops before reading results". Astra A086 says even `h.core` raises before any launch.
- Resolution: **Astra is right.** `tests/harness.py:17-23` makes `RawHarness.device` return `self._card.raw()`. `OfflineDevice` (`tools/viewer/capture.py:47-60`) has no `raw` and its `__getattr__` raises `HardwareBoundary`. `CaptureHarness.launch` falls back to `self.core` when `core=None` (line 63), which goes through `device`.
- So any capture that touches `h.core` or `h.device` stops immediately. Fable's description matches the design intent and Sol's matches only the `read_dram` boundary. All three agree it is not a real backend (merged as M-140; the bug is M-141).

**C3. Host overhead per token.** Fable measured a median of 34.4–40.4 µs per `decode()`, of which `runtime_encode_us` was 20.2–24.9 µs. Astra measured 9.15 µs per `DeviceTrace.replay()`, and that figure includes the encode.
- Resolution: **the two do not measure the same thing, and the encode sub-number is not reconciled.**
  - Fable timed the full `Llama3Decode.decode(pos, logits=False)` through a real `CommandQueue` over ctypes fake sysmem: patch_trace, event patch, doorbell to a fake TLB, profiling. Its encode figure is `last_profile`, a **single sample** from the last replay (fable-scratch/host_overhead.py).
  - Astra timed `DeviceTrace.replay` alone, with a stub `replay_trace` returning None, 6 parameters and 88-core rectangles, as a warm 1000-iteration median (astra-scratch/measure.py:43-57).
- The code path (device.py:409-430: set diff, dict, tuple, type check, `McastWrite(...).lower()`) is the same in both. Astra's warm median is the more reliable estimate of encode cost; Fable's single sample likely includes noise. Fable's real llama rectangle set may also differ from Astra's.
- Both agree on the conclusions: host replay is well under 1 % of a 6.2 ms token, and pre-lowering the record is cheap to do. An offline microbenchmark to settle the number was blocked by the sandbox.

**C4. Firmware build time.** Fable: 0.38 s. Astra: 245.3 and 241.1 ms. Sol: 255.9 and 250.1 ms.
- Resolution: **not a code conflict.** Astra and Sol set `CCACHE_DISABLE=1` and `TMPDIR` to the scratch dir. Fable did not record its environment. All three agree on the finding: nine images rebuilt on every boot, with no cache.

**C5. Program construction time.** 1B/8B-BF16/8B-FP8: Fable 1.17/3.39/4.19 s; Astra 1.183/3.404/4.089 s; Sol 1.185/3.491/4.001 s.
- Resolution: **consistent within run-to-run noise.** Unique image counts (192/262/276) and bytes (1,461,552 / 4,239,456 / 4,847,624) match exactly across all three.
- On interpretation, Astra and Sol are right that these summed bytes are not per-core residency. Fable's summary line "4.8 MB of resident code" uses the summed figure. Fable's separate per-core numbers (157/340/374 KB max resident per core) are the residency figures.

**C6. Is `Buffer.from_numpy` dead?** Fable PRG-07 lists it as unused (vulture). Astra A042 and Sol F025 treat it as the public conversion path that truncates BF16.
- Resolution: **partly both.** It has no production callers, but tests/compute/fpu/test_llama_attention.py:41,46 uses it. The truncation is confirmed at program.py:235 (`>> 16`). Not dead code, but test-only.

**C7. How many test files run offline.** Fable TS-01: 77 of 81 need the card, and the offline files include tests/test_profiler.py.
- Resolution: **3 of 81 are offline, so 78 need the card.** tests/test_profiler.py:11 takes the `bh` fixture. The merger's grep found only test_encoding.py, test_audit.py and test_llama_paged_weights.py without hardware fixtures. Sol's "9,540 passed" covers two of these modules, so it is consistent.

**C8. Number of "boot first" error sites.** Fable DEV-10 says "six" but lists eight lines.
- Resolution: **8 sites**: device.py:157, 231, 269, 511, 555, 627, 808, 953. The wording varies ("boot() must be called first" vs "init_device() must be called before ...").

**C9. Line-number disagreements; the claims themselves hold.**
- Fable CQ-01 cites `prefetch.c:184, 194-198`, but prefetch.c is 101 lines. The header read is at line 36 and the full re-read at 46-51. The double-read claim is correct.
- Fable TL-02 cites `bench_llama_decode.py:198-215`, but the file is 97 lines. The legacy branch is at 43-49, and Sol's 39-50 is correct.
- UnicastWrite: Astra cites cq.py:98-110 and Sol 91-98. The class is at cq.py:86-98.

**C10. Severity disagreements.** These are not factual conflicts; the merged list keeps the highest rating and notes the spread. The largest gaps:

| Merged | Topic | Fable | Astra | Sol |
|---|---|---|---|---|
| M-001 | Async replay race | med | high | high |
| M-036 | Card ownership | low | high | high |
| M-076 | Semaphore global IDs | low | high | high |
| M-107 | NoC issue path | high | low | med |
| M-010 | RUN barrier | high | med | — |
| M-061 | Binding checks | med | high | high |
| M-070 | ttk absent | med | high | high |

Fable rates perf and dispatch issues higher. Astra and Sol rate correctness and safety issues higher.

**C11. Points that looked like conflicts but were confirmed consistent.**
- Fable says ttk was "removed rather than finished"; Astra and Sol say it is "absent". Git has `6c0e0be Remove ttk` after `e5e6759 Add experimental TTK graph frontend`, so both hold.
- Fable CQ-02 says the DMA-idle probe runs before every non-DRAM command, and Astra A009 mentions only the RUN barrier. dispatch.c:52-57 confirms Fable, and Astra does not contradict it.
- Fable CQ-01 says `cache_programs`/`DramRecord` are unused. Confirmed: no references outside device.py and cq.py.
- Astra's suspected A053 (legacy CB wrap): the missing 16-bit mask is confirmed in code at cb.py:195-209 and 270-275.

---

## 4. Measured numbers (all offline; none on hardware)

| Quantity | Value | Source | Method |
|---|---|---|---|
| `_allocate` (metadata) 1B / 8B-BF16 / 8B-FP8 | 10 / 19 / 21 ms | Fable | fake TensorDevice over ctypes sysmem and fake TLBs (fable-scratch/host_overhead.py) |
| same | 10.32 / 19.41 / 21.31 ms | Astra | `object.__new__` Llama3Decode, SimpleNamespace device with real `Dram`, synthetic 8-bank P150, 117 workers (astra-scratch/measure.py) |
| same | 10.22 / 18.99 / 20.69 ms | Sol | same approach plus an audit hook blocking /dev and /sys tenstorrent opens (sol-scratch/offline.py) |
| `_create_programs` 1B / 8B-BF16 / 8B-FP8 | 1.17 / 3.39 / 4.19 s | Fable | as above |
| same | 1.183 / 3.404 / 4.089 s | Astra | as above |
| same | 1.185 / 3.491 / 4.001 s | Sol | as above (run order 1B, 8B-FP8, 8B-BF16) |
| Subsequent `lower()` (mostly memoized) | 3.52 / 4.07 / 3.69 ms (Astra); 3.39 / 3.85 / 3.38 ms (Sol) | Astra, Sol | per-program `.lower()` after create |
| Programs | 8 (1B) / 10 (8B) | Astra | count |
| Unique (role, image) | 192 / 262 / 276 | all three | dedup by image bytes |
| Unique image bytes (summed across variants; not per-core) | 1,461,552 / 4,239,456 / 4,847,624 | Astra, Sol (Fable: 1.46 / 4.24 / 4.85 MB) | sum |
| Max resident bytes per core | 157 KB / 340 KB / 374 KB | Fable | `cache_kernels` stats on fake device |
| Resident arena / use | 504 KiB (0x12000–0x90000); 8B FP8 uses 72 % plus about 30.5 KiB templates (split trace) | Fable | computed from consts and stats |
| L1 data arena | 983,008 B | Fable | computed |
| Common per-bank allocator high-water | 343,027,776 / 2,142,681,152 / 1,270,282,304 B (1B / 8B-BF16 / 8B-FP8) | Astra, Sol | allocator cursor; starts at 64; not physical use |
| `cache_kernels` host time | 0.01 / 0.02 / 0.02 s | Fable | fake device |
| Trace capture host time | 0.03 / 0.12 / 0.16 s | Fable | fake device |
| Launches per token | 83 (1B); 163, or 195 with split (8B) | Fable | trace record counts |
| Records published by `cache_kernels` | about 952–961 | Fable | fake CQ |
| Largest images vs partitions (8B FP8, bytes) | attention brisc 33,144 / ncrisc 8,624 / trisc2 4,876; attention_split brisc 57,580 / ncrisc 11,080 / trisc2 5,616; attention_merge ncrisc 9,748 / trisc1 10,060; down brisc 25,424; gate trisc1 21,380; qkv trisc1 16,864 (limits 24,576 / 8,192 / 12,288 / 8,192 / 4,096). 1B attention brisc 27,596. | Fable | fable-scratch/build_time.py |
| Per-token host overhead, full `decode()` replay path, device faked | median 40.4 / 39.2 / 34.4 µs; min 38.0 / 36.8 / 32.1 µs; `runtime_encode_us` 24.9 / 23.7 / 20.2 µs (single last sample) | Fable | 200 `decode()` calls on fake CQ |
| `DeviceTrace.replay()` alone | 9.10–9.56 µs per call, median 9.15 µs | Astra | 7 × 1000 replays, 6 params, 88-core rects, stub CQ |
| `_read_token` | 2.8 µs | Fable | 1000 calls on fake sysmem |
| Host share of a 6.23 ms (1B) token | about 0.6 % | Fable | the above vs README |
| `firmware.build()` | 0.38 s | Fable | clang + ld + objcopy, 9 images, environment unrecorded |
| same | 245.3 ms, 241.1 ms | Astra | two runs, `CCACHE_DISABLE=1` |
| same | 255.88 ms, 250.12 ms | Sol | two runs, `CCACHE_DISABLE=1` |
| Firmware image sizes | workers 1068/128/188/188/188 B, prefetch 1280, dispatch 1476, DMA 2632/2404 B | Fable | build output |
| Packed firmware blob | 9,596 B | Astra, Sol | `firmware/__main__.py` pack |
| `import device` | 47.5 ms (numpy dominates); `import examples.llama3` +2.8 ms | Fable | timing |
| Guarded import sequence | 50.8 ms | Astra | not cold-cache |
| Per-tile RISC-V words: `unpack.move_matmul` | 208 first / 138 with `configure_format=False` | Fable | emit and count on a TensorProgram, BF16, FP32 Dst |
| `fpu.matmul` | 72 first / 7 cached straight-line / 53 per `range()` iteration | Fable | same |
| `pack.move` | 163 straight-line / 168 in `range()` | Fable | same |
| `noc.read_into_cb` / `read_tiles_into_cb` (2 tiles) | 151 / 244 | Fable | same |
| KV zero upload | 1.0 GiB (8B) / 0.25 GiB (1B) | Fable | computed from config |
| Static analysis | ruff 89 findings; pyflakes 42; vulture about 110 symbols at ≥60 % confidence | Fable | tool runs |
| Offline pytest | 9,540 passed in 2.43 s (test_encoding.py + test_llama_paged_weights.py) | Sol | `pytest -p no:cacheprovider` |
| Offline pytest | test_llama_paged_weights.py: 6 passed | Astra | same |
| Repro: UnicastWrite 2 targets / 1 payload | accepted, 128 B record | Astra, Sol | pure packet lowering |
| Repro: unequal payloads | accepted, 192 B record | Astra, Sol | same |
| Repro: `Allocator(5,100).alloc(4,3)` | returns 5 | Astra, Sol | pure |
| Repro: `Buffer(shape=(0,))`, `(-1,)`, `banks=0` | all report 2048 B | Astra (shapes), Sol (negative, banks=0) | pure |
| Repro: two `Const('x')` | two slots, one-word table | Astra, Sol | pure |
| Repro: viewer `CaptureHarness.core` | raises `HardwareBoundary` | Astra | pure |
| Repro: VReg into `_dram_tile` | `TypeError` (VReg &= int) | Sol | pure codegen (sol-scratch/virtual_noc.py) |
| Checked, no defect | GridProgram entry order with reversed dict insertion: matches | Astra | pure |

Not measured by anyone (needs the card): PCIe read latency per trace record, the per-launch dispatch gap, weight upload rate, the cost of the per-launch Tensix reset, and NoC routing behavior.

---

## 5. Architecture recommendations (merged)

All three reports propose a layered stack with a single executable path. The layers below are listed bottom up.

1. **Transport.** All three agree. Open, pin, TLB, doorbell and signal wait sit behind an interface, with a shipped deterministic fake (controllable progress and failure) so everything above runs offline. Add exclusive device leasing that is compatible with `tt-device-queue` (Astra, Sol), and exception-safe acquisition (Astra, Sol).
2. **Queues and execution.**
   - Agreed: keep compact trace replay, but give every submission immutable parameter and signal storage, per-event completion metadata, one ordered compute/transfer graph, and explicit failed/poisoned states with recovery.
   - **Divergence:** Fable wants to go further now. Records and kernel images in device DRAM, a prefetcher that streams pages, launch packets carrying kernel handle, core-set handle, argument-block pointer and dependency signal, addressable signals so launches can depend on each other device-side, and persistent kernels for layer loops.
   - Astra is cautious: "keep serial replay as the baseline, but represent dependencies and resource footprints so overlap can be added later". It explicitly declines to claim that concurrency always helps on one card.
   - Sol sits between the two (trace residency management plus immutable submissions).
   - Only Fable proposes removing the per-launch Tensix reset in favor of declared-config diffs.
3. **Memory.** All three agree. A DRAM allocator with free, separate persistent (model/optimizer), transient-step and staging arenas, completion-delayed reclamation, and peak and per-bank reports. Traces and kernels become refcounted handles with eviction.
   - Fable adds that L1 should be a per-program plan (header + argument block + storages) with **no fixed kernel arena**.
   - Astra and Sol add device-owned Storage handles with generation and extent.
4. **Kernel ABI and artifacts.** All three agree on immutable artifacts (role binaries, relocations, source maps, a typed parameter schema, resource plan, topology requirements) and content-keyed host caches kept separate from device residency, with transactional incremental install.
   - Fable is the most specific: one image per role, with core rank and grid shape in the header, return through a fixed trampoline, and an argument block generated from the kernel signature.
   - Sol: "separate runtime rank/data from compile constants".
5. **Tensor model.** All three agree on separating the logical view (shape/strides/dtype, batch and sequence as ordinary axes) from storage, physical layout or index map, and placement.
   - Fable phrases it as `Tensor` + `View` + `Tile(dtype, rows, cols, layout)` + `Storage(space, tile, count, depth, producer)`, covering L1, SrcA/B, Dst and REG, with row-major DRAM in tile-row pages.
   - Astra and Sol phrase it as `TensorView` + `Storage` + `LayoutMap`.
   - Fable's version reaches further down: it models SrcA, SrcB and Dst as storages too.
6. **Frontend / IR.** This is the **main divergence**.
   - Fable: implement the ttk-v2 UOp graph (DEFINE/INDEX/AFTER/RANGE/IF, engine effects, SFPU SSA with WHERE). A verifier checks occupancy, Dst capacity, formats and producers, and the backend **derives** CB credits, semaphores, stalls, MOP/replay and NoC batching. `CUSTOM` is the escape hatch.
   - Astra: a "verified kernel IR" that describes effects and per-thread resources and verifies CB/semaphore/replay/Dst/NIU ownership, keeping explicit schedule knobs. "An executable vertical slice is the milestone; do not defer every backend until after an expansive frontend."
   - Sol: a "block/effect compiler" with structured loops, static checks and a reference interpreter, starting with **naive lowering** and keeping optimized raw escapes with declared effects.
   - Net: all want an effect/storage IR with verification. Fable leans to full derivation from day one; Astra and Sol lean to verify-first, a vertical slice, and naive lowering.
7. **Operator library.** All three want blocked `matmul(M,N,K)` (from matmul_peak's schedule), attention with online softmax and split-KV merge, rmsnorm, swiglu/activations, rope, argmax, their backward forms, and AdamW (Fable: a Map over four FP32 tensors).
   - **Divergence on decode:** Fable wants one matmul with tiny tiles (1×32 or 8×32) at M=1, so there is no separate GEMV kernel. Astra and Sol want the GEMV kept as the M=1 *schedule* of the same interface.
   - Fable and Astra want routing from a planner that takes the core set, banks and bytes and applies measured NoC/DRAM rules as constraints. Sol says "placement and route planning explicit and validated against topology".
8. **Model state.** Astra and Sol, with Fable implicitly: a KV/sequence manager (slots or pages, per-sequence lengths, prefix ownership) that supplies batch descriptors, and a training plan with saved or recomputed activations, gradient accumulation, FP32 AdamW state and consistent checkpoint events. Both share the same storage, dispatch and operator contracts.
9. **Testing and verification gates.** All three agree: numpy reference per op (forward and backward), an interpreter for the lowered program's semantics (Astra: not cycle timing), golden packet and image tests, fake-transport failure tests on every change, and hardware tests separated from experiments.
   - Sol gives a concrete first acceptance slice: one 1B layer at M=1 and M=32 on the same interfaces, ragged batch decode, backward against a CPU reference, then several AdamW steps.
10. **Preserve what works.** Astra and Sol are explicit; Fable is implicit. Keep:
    - from Astra and Sol: direct bounded `readinto` checkpoint streaming, two-slot upload overlap, compact trace parameters, resident-kernel dedup, topology discovery, assembler role checks and branch relaxation, ELF layout validation, the ISA encoding inventories (9,540 offline tests), explicit hardware opt-in in tests, and the existing split-attention and paged-weight work;
    - from Fable: the matmul_peak schedule and the rewrite's `config.py` field model.

---

## 6. Coverage

Counted over the 176 merged findings by which models appear in each finding's Sources line.

| Bucket | Merged findings |
|---|---|
| Unique to Fable | 42 |
| Unique to Astra | 24 |
| Unique to Sol | 19 |
| **Unique total (1 model)** | **85** |
| Shared by Astra + Sol | 35 |
| Shared by Fable + Astra | 10 |
| Shared by Fable + Sol | 10 |
| **Shared by exactly 2** | **55** |
| **Shared by all 3** | **36** |
| **Total** | **176** |

Severity of the merged findings (highest rating any model gave): **high 57, med 86, low 33**.

Source totals: Fable 95, Astra 103 and Sol 101, all mapped. Some broad source findings are split across two merged items and marked "(part)": Fable DEV-01, TTK-01, PRG-05, PRG-08, LL-09, XC-03; Astra A055, A096; Sol F053, F058, F078.

Character of each model's unique findings:
- **Fable:** device-side perf and dispatch (per-tile word counts, PCIe trace fetch, Tensix reset, arena and partition limits), the ttko internals (unpack/pack/Dst/SFPU/dtype/register maps), and dead-code inventory.
- **Astra:** lifetime and safety edges (staging recycle during capture, concurrency contract, telemetry bounds, chat exposure, viewer breakage), plus training checkpoint persistence.
- **Sol:** model-level ABI gaps (single-token activations, norm fusion, precision policy), allocator per-bank pressure, test hygiene (zero-init masking, fixture recovery, bad test topology), and the VReg/NoC codegen bug.
