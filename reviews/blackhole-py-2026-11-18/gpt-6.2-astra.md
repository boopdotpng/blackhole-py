# Blackhole Python cleanup review

## TL;DR

Ranked by expected payoff relative to implementation effort.

1. Give compute and DMA independent completion counters. Async graph submission invalidates the shared timeline's ordering assumption.
2. Publish compiled firmware through a unique temporary file per builder.
3. Reserve uploads by byte count. Typed buffers currently let DMA overwrite subsequent DRAM allocations.
4. Make graph submission commit its completion ticket only after the doorbell succeeds.
5. Keep one observer and launch collector in kperf. Archive the ablation runs outside the runtime checkout.
6. Replace the eight startup zero images with one parameterized TTRV program and bank mapping.
7. Make embedding and BF16 O/down source builds mandatory after parity checks. Keep one source for O and down.
8. Migrate the model layout and argument schema alongside the remaining kernels. Removing binaries alone leaves the exporter-defined memory map intact.
9. Route profiling, benchmarking and inference through one device/session and launch API.
10. Add compile-time tuple iteration for attention face offsets before adding more special-purpose SFPU syntax.

## Bugs

**Confirmed by control flow or arithmetic**

- ops_blackhole.py:83,171,223 and fw/queue.c (OP_STORE). Submit a long compute graph with ticket N, then upload on DMA with ticket N+1. DMA can finish first. A waiter for N accepts N+1 while compute still runs. Compute can subsequently store N and make a waiter for the already-completed DMA transfer time out. This requires only one host thread. Use a (queue, sequence) fence, and wait on both queue tails for device synchronization.
- ops_blackhole.py:83,101,227. A timeout waiting for ring space happens after next_timeline advances. The graph's CALL and STORE fit in one chunk, so neither is published on this failure. synchronize now waits for a nonexistent ticket. Reserve and commit separately. For larger multi-chunk pushes also specify partial-submission recovery.
- ops_blackhole.py:193 versus 176. upload allocates len(blob) bytes and copies memoryview(blob).cast("B") bytes. For a 1 Mi-element uint32 array these are 1 MiB and 4 MiB respectively, much larger than stripe rounding. The next allocation can overlap live data. Derive both quantities from one byte view.
- fw/__init__.py:68. Independent cold builders of the same key copy into the same .tmp pathname. One rename can remove the other's source or expose an inode the other process still writes. Create each temp in CACHE with a unique name and replace after closing it.
- ops_blackhole.py:229. alloc_host(-64) moves the heap backwards, allowing reuse of a live allocation. Validate size and positive alignment before updating the cursor.
- ops_blackhole.py:74. A graph patch at byte offset 1 modifies word 0, and a negative offset indexes from the end. Validate word alignment and command payload bounds before applying patches.

**Suspected or hardware-dependent**

- ops_blackhole.py:200 infers coordinates entirely from enabled-column population. Verify KMD's translated-coordinate contract for both supported boards and all harvest masks before changing it. Population alone cannot identify a disabled physical column.
- ops_blackhole.py:108 assumes host ring stores reach the device before the MMIO doorbell. Verify this against the supported architectures, mapping types and KMD ordering contract. Python statement order alone establishes no PCIe visibility guarantee.

## Delete / merge / move list

- Remove play/observer_dbg.c after repointing callers. It is byte-identical to kperf/observer_dbg.c. Diff play/observer_dram.c and play/observer.py against their kperf counterparts before retiring them because those pairs differ.
- Merge play/kbench.py into kperf/collect.py. Both select kernel/layer, allocate 32 bytes of stamps per launch and build the repeated compute queue. Preserve folded/trace export as a bundle conversion if used.
- Move play/{dram_niu_probe,dram_timeline,l1_highwater,pc_probe,ts_probe}.py and ts_kernel.c into an external hardware experiments collection together with the matching firmware revision. Archive sync/ as one reproducibility unit including scripts, census, results and findings.
- play/*.npz, *.folded and trace/span JSON observed locally are absent from git ls-files play. Removing them from a user's checkout yields no tracked reduction. sync/results/*.json and sync/census.json are tracked.
- Move validated docs/examples kernels into a production source directory and link the documentation there. docs/ttrv_gaps.md still says scalar params use old forms, while embedding already declares token_pos. Record implementation status per kernel/variant and retire resolved entries after migration. Preserve reference.json as parity fixtures and kview/data as decoder inputs.

## Leaving blackhole-py-old

kernels/zero/export.py:8–12 directly imports Asm, R, NoC and P150_DRAM_ENDPOINTS. ttrv/isa.py:386 contains copied enum values, a provenance dependency independent of import paths. Re-derive required fields from authoritative ISA definitions and verify golden instruction words. fw/ workers and services are independently compiled from local C.

llama3.py:53–60,95,111–146 establish three other dependencies. Every model reads an exported manifest, places new allocations above its per-bank high-water mark and installs startup zero BRISC images. Default decode loads manifest-selected role/variant binaries for embedding, qkv, attention, o, gate, down, lm and argmax. With --ttrv only embedding switches on FP8, and embedding/o/down switch on BF16. Remaining launch metadata includes per-core tables, persistent state, uniform argument order, buffer addresses and launch order. RoPE files are data and need their own generation or documented provenance.

1. Freeze reference token sequences and intermediate buffer comparisons for 1B, 8B BF16 and FP8. Keep historical binaries as temporary comparison fixtures outside production once replaced.
2. Port zero first. Preserve the per-bank byte unit, startup scratch lifetime and acknowledged completion. Test first and last cache pages on each bank.
3. Promote working source variants. Build all supported define sets offline, check both execution slots, argument widths and scratch bounds, then compare outputs at multiple positions.
4. Port BF16 qkv/gate/lm around shared projection routines, then FP8 projection variants including O/down. Check quantization/scales and accumulation separately. Port argmax with padded vocabulary and tie cases. Port attention with persistent state, partition reductions, cache reuse and nonzero positions. Keep per-kernel parity gates during mixed execution.
5. Generate allocations, argument bindings, launch order and scratch/keep intervals from an owned model description. Compare generated binding/layout reports against fixtures before removing the last manifest reader. Remove exporter, role blobs and backend switch when all model variants pass cold boot and repeated decode with the predecessor checkout absent.

## Runtime/flags/firmware consolidation

Keep system.py as the private KMD mapping/ownership layer, fw/ as service source and ABI owner, and ops_blackhole.py as the single session/allocator/queue implementation. Put model variant, buffer and launch recipes beside the production kernels. Keep CLI parsing at entry points. Proposed caller flow:

~~~python
with Device.open(index=opts.device) as dev:
    model = Llama3.load(dev, variant=opts.model, weights=opts.weights)
    fence = model.graph.submit(start=pos, count=n)
    fence.wait(timeout)
~~~

Expose alloc/upload/download and a timed repeated-launch method. play/ts_probe.py:26–33 manually opens a device, builds a program and emits its own completion signal. kperf/collect.py:51–64 and play/kbench.py:46–57 duplicate allocation and queue construction. Share these operations below CLI level. Keep bench's multi-model iteration while sharing device, variant, weights and transitional source selection with llama3.py and kperf. bench.py:46–48 has its own model choices and lacks the source switch, making source-vs-image comparisons easy to mislabel.

Build firmware independently of device opening. Keep the existing two-slot link comparison. Include compiler/linker identity in the disk cache key and pass the resulting image set into boot. Put the checked reset-vector JAL and role return encoding in one small RV32 encoding layer used by boot and TTRV. Remove exported-image return patching with the legacy loader. Avoid pulling the kernel language frontend into PCI setup.

## Code quality simplifications

- Represent buffer layout once with page size, byte length and interleaved address. llama3.py:75 converts per-bank units while ops_blackhole.py:9 packs tags. Make conversions at the manifest boundary.
- Replace the compiled-name set, source alias and define conditionals at llama3.py:111–123 with per-variant kernel recipes shared by installation and compiler tests.
- Separate queue encoding from submit-and-signal. Centralize ticket ownership, timeout propagation and partial-submit handling. DMA submit currently drops the caller's timeout at ops_blackhole.py:65.
- Validate upload kinds explicitly at llama3.py:88. Today any unknown kind becomes a zero request. Check file byte length against its destination capacity as well.

## TTRV language ideas

Attention repeatedly composes the same four face offsets. Replace arithmetic in llama3_attention.ttrv:292 with a compile-time sequence.

~~~text
// Current
repeat i in 0..4 { sfp.store dst[M + (i & 1) * ODD + (i >> 1) * RIGHT], m_new, fmt=fp32 }
// Proposed
const CHUNKS = (0, ODD, RIGHT, RIGHT + ODD)
repeat off in CHUNKS { sfp.store dst[M + off], m_new, fmt=fp32 }
~~~

Embedding contains a reusable aligned scalar gather idiom. Give it a library helper with explicit scratch and transfer width so the traffic remains visible.

~~~text
// Current
noc.read ids, history[i & ~15], n=16, wait
token = ids[i & 15]
// Proposed
token = read_element(history, i, scratch=ids, block=16)
~~~

Require power-of-two block length and enough scratch, with a bounds contract for the entire aligned read. Expand to the same read/wait and scalar load. Neither feature needs runtime tuples or dynamic endpoint dispatch. Defer general cross-macro scheduling and clobber inference (§11) until exercised by a second independent kernel pattern. Start with named verified macro recipes for existing RMSNorm, preserving hazard checks and explicit loading.

## Open questions for the owner

- Which profiler export formats have external consumers, and where should historical measurements be archived?
- Which p150/KMD and host CPU combinations define the supported ordering and harvest contracts?
- What numerical tolerances and intermediate tensors should gate FP8 and attention migration?

Validation comprised source inspection, tracked-file inventory, observer comparison and the CPU-only test_ttrv.py suite. Hardware-specific hypotheses and migration parity remain unverified.
