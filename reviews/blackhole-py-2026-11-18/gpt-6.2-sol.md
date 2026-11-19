# Blackhole-py cleanup review

Reviewed `blackhole-py` at `2cab0be`. The pure-Python TTRV suite passed 18 tests. I also built every example in memory with default defines and tried `FP8=1` where declared. A benchmark CLI invocation unexpectedly reached device initialization, which raised during construction. Its traceback was truncated, so I cannot verify how far initialization got. I ran no hardware tests or benchmarks to completion. No repository files were edited.

## TL;DR

1. Add a build matrix for every shipped kernel and model configuration. Five of seven default example sources fail to build today.
2. Give compute and DMA independent completion counters, then add explicit dependencies where data crosses queues.
3. Replace the eight startup zero images with a native kernel. This removes the one in-tree tool that imports the predecessor.
4. Replace the positional bridge in `Llama3._install` with named compiler bindings and preflight the manifest, checkpoint and topology before starting firmware.
5. Port FP8 O/down and switch the validated embedding and BF16 projection paths to compiler output. Treat LM/argmax as one migration unit.
6. Drop the duplicated profiler scripts after carrying their remaining useful outputs into kperf.
7. Use a unique temporary file for each firmware cache publication and include toolchain identity in the cache key.
8. Archive the sync experiments with their exact image revision. Generate listings, binaries and profiler captures outside the source tree.
9. Replace profiling's global file-read monkeypatch with a loader transform, then emit stamps in the compiler.
10. Use one device lifecycle and shared flags for inference, bench and profiling. Keep telemetry and reset available without booting the runtime.

## Bugs

### Confirmed by build or source inspection

- **Five example kernels fail the default build.** `docs/examples/llama3_argmax.ttrv:88` produces `parse.syntax` at the inline predicate body. Attention at line 183, gate at 167, LM at 124 and QKV at 163 fail at `alias`. The FP8 attempts for argmax, gate, LM and QKV hit the same first errors. `docs/examples/llama3_o.ttrv:191` fails with `type.assign` under `FP8=1` because `v` holds `bf16*` and receives `e4m3*`. Embedding and default O build. `test_ttrv.py:155` exercises embedding and two BF16 O dimensions, allowing the other sources to regress without tripping the host suite.
- **Completion events can satisfy the wrong wait.** `ops_blackhole.py:83,171,223–227` uses one signal for independent queue producers. Submit compute A and issue a DMA upload B while A runs. If B finishes first, its higher value retires A falsely. If A later stores its lower value, the counter can move backward. The ordinary sequential inference path masks this, but the asynchronous graph and allocator API permits the overlap. A fake queue test can drive each ordering.
- **Firmware cache publication races across processes.** `fw/__init__.py:56–69` uses the same key-derived `.tmp` path in all writers. Two misses can open the same temporary inode, publish while another writer is still writing, or get a missing-source error at rename. The key also ignores the selected clang and objcopy identities. A unique temp in the cache directory and atomic rename fix publication.
- **Grid fast path skips program validation.** `ops_blackhole.py:115–133` checks image length, alignment and argument size for per-core builds only. A grid caller can supply an image beyond its role slot or an unaligned argument size and still construct a descriptor. Share validation and group construction before any upload.
- **Chat reports a token cap as context exhaustion.** `llama3.py:283` forwards the CLI cap but drops generation status. `chat/server.py:69–73` labels every non-EOS finish as `context`. Return a stop reason with the token result.
- **User text is tokenized as control syntax.** `llama3.py:37–41` concatenates raw message content with template markers and enables every special token across the whole string. Literal marker text in a message changes the token structure. Encode role delimiters explicitly and encode message bodies as ordinary text.
- **A ring timeout can leave a prefix committed.** `ops_blackhole.py:97–108` publishes each chunk separately. A later timeout leaves earlier commands visible, while retrying the same blob submits them again. Define partial-submission behavior and poison a failed queue unless the caller has reliable progress information. Even a single-chunk graph submit reserves a timeline value before publication at line 83, so a timeout can leave `synchronize()` waiting for a value with no producer.

### Suspected or hardware-dependent

- `ops_blackhole.py:200–205` counts enabled columns and reconstructs a fixed contiguous layout around x=8/9. The count alone cannot identify holes or translated coordinates. Confirm what the p150 firmware and driver guarantee and check manifest core placement against that topology before boot.
- `ops_blackhole.py:106–108` relies on host ring stores becoming visible before the uncached write pointer store. Check the supported host architectures, TLB ordering and DMA coherency contract. Python statement order supplies no portable device barrier.
- `ops_blackhole.py:235–242` skips unpin and munmap if reset raises. Whether the fd close safely quiesces and unpins outstanding DMA depends on the driver. A teardown protocol needs to establish device quiescence before releasing pins and account for failure to establish it.
- `docs/ttrv_gaps.md` items 11, 17 and 19 describe partial-write alignment, FP32 merge-state precision and the application of Dst offset to MVMUL. Resolve with targeted hardware tests before enabling compiled attention. I did not verify these behaviors on a card.

## Delete / merge / move list

| Action | Files | Dependency to handle first |
|---|---|---|
| Delete duplicates | `play/observer_dbg.c`, `play/observer_dram.c`, `play/observer.py`, `play/kbench.py`, `play/kprof.py`, `play/kprof_sample.py`, `play/kprof_dump.py` | Debug C copies are byte-identical. DRAM C copies differ. Keep kperf's collector and observer, and preserve the Chrome/Perfetto export from `play/kprof.py` if used. |
| Move selected probes | `play/{dram_niu_probe,dram_timeline,l1_highwater,pc_probe,ts_probe}.py`, `play/ts_kernel.c` | Keep any ongoing hardware characterization in lab tooling. Point moved probes at the shared observer and session API. |
| Archive the experiment together | `sync/{ablate,census,summarize}.py`, `sync/census.json`, `sync/results/*.json`, `sync/{README,results}.md` | The ablator patches instruction words using listing addresses and copies legacy images. Preserve the tested image revision and retain a short summary of actionable synchronization results. |
| Generate | `kernels/llama3-*/*/*.S`, then `*.bin` as each operation switches | kview reads binaries directly. Route both viewers and the profiler to the build output and retain source maps. Delete startup exporter and its eight bins after zeroing parity. |
| Curate docs | `docs/ttrv_port_review.md`, `docs/ttrv_gaps.md`, legacy reproduction sections of `docs/kernels.md` | Archive historical measurements and estimates. Keep one current compiler support matrix and one live list of unresolved hardware semantics. |

There are no tracked `.npz` files at this revision. The tracked JSON includes the 27 sync artifacts, six kernel manifests/reference fixtures and five kview decoder tables. The latter two groups have active consumers. Keep compact golden inputs and outputs and ship decoder data with its notices if kview moves. Move kperf/kview together into optional tooling if the core repo is intended to ship only runtime and compiler. Keep their capture format versioned across that move.

## Leaving blackhole-py-old: dependency inventory + migration plan

- **Direct import.** `kernels/zero/export.py:8–12` imports the predecessor's Asm, register enum, NoC helpers and P150 DRAM endpoint map. `llama3.py:93–102` loads its eight outputs independently of the `ttrv` switch.
- **Copied definitions.** `ttrv/isa.py:386–425` identifies its field enums as predecessor ttko values. It imports no ttko at runtime. Re-derive needed fields from the Blackhole ISA docs and hardware definitions, document provenance, and verify encoded words against small fixtures. The generic emit/decode table is the boundary for the remaining kernel encodings.
- **Exported execution ABI and data.** The predecessor's `tools/rewrite_export/export_llama3.py:203,241–264` writes role binaries, RoPE tables and the manifest. The three model directories carry per-core variants, launch order, uniforms, static/table storage, weight and KV addresses and program bytes. `llama3.py:108–145,155–169` reuses that plan. References are golden fixtures with their own lifecycle. `llama3.py:292–293` substitutes them into normal CLI inference, which should instead use the chosen tokenizer and checkpoint.
- **Current compiled coverage.** The default loads all exported images. `--ttrv` uses embedding for all models and O/down only for 1B and 8B BF16. Down reuses the O source with `INPUT_TILES`. QKV, attention, gate, LM and argmax still load predecessor binaries throughout. FP8 O/down remains legacy. The benchmark and collector have no corresponding switch.

Migration order:

1. Stabilize the test seam. Use compiler manifests and named bindings with checked page size, ABI words, role mask, scratch usage and core count. Add compile-only CI for every model profile, including attention partition/head defines, FP8 variants and 8B down dimensions. Record numerical and timing baselines against current images.
2. Replace startup zeroing. Use a BRISC TTRV source with bank/worker mapping and bulk zero writes if it can express bank selection and bounded L1 fill. A small C firmware primitive is sufficient if those operations would otherwise require bespoke language extensions. Validate all banks and the final stripe. Switch embedding and BF16 O/down after their parity runs.
3. Complete FP8 O/down and deploy them with the correct page and scale bindings. Audit quantization and accumulation before comparing throughput. Keep the algorithm variant and the NoC assignment explicit.
4. Bring QKV and gate through compiler and hardware tests now that the projection protocol and quantization pieces exist. Verify Q/K RoPE and V directly, and compare gate/up plus SwiGLU against reference tensors. Check scale and weight shape against the checkpoint before opening a session.
5. Migrate LM and argmax together. `docs/ttrv_gaps.md` documents the new dense logits layout, while the old pair exchanges compact per-core tiles. Bind argmax's full host endpoint and use explicit launch scalars. Test tie breaking, padding, final context slot and EOS. Switch the pair only after the shared layout lands.
6. Finish attention and switch it once cache append, persistent state and split merge pass boundary and long-context checks. Cover all supported partition geometries, 32-token transitions, back-to-back launches and cross-model dimensions. Move the graph, memory plan and RoPE generation to native model configuration. Remove exported manifests and images when a clean checkout can build and run each model without the predecessor.

Keep a small RV encoder for reset and return trampolines (`fw/__init__.py:86–92`) and minimal C startup, barriers, CSR access and Tensix bootstrap (`fw/worker.h:10`, `fw/hw.h:13–15,63–67,128–137`). Remove hand-coded per-kernel instructions, sync binary patching and profiler word construction from the maintained path. Generate profiler entry/exit instructions before final relocation, including before compiler-emitted returns.

## Runtime/flags/firmware consolidation proposal

| Module | Responsibility and public surface |
|---|---|
| `blackhole.device` | `discover()`, `read_telemetry(index)`, `Device.open(index)` as a context manager. Own fd and lock, topology, reset and power, TLB mappings and pinned memory. |
| `blackhole.runtime` | `device.allocate()`, `copy_in()`, `copy_out()`, `install(kernel)`, `submit(graph, bindings, dependencies=()) -> Fence`. Own packet encoding, per-queue completion and bounded resource allocation. |
| `blackhole.firmware` | `build(toolchain, cache_dir)` and private boot/install primitives. Generate or verify C and Python constants from the same ABI description. Resolve firmware images before acquiring the device where practical. |
| `blackhole.llama` | `ModelSpec`, `Llama3.load(device, spec, checkpoint)` and `generate(ids, max_new_tokens, ...)`. Own weights, graph binding, KV reuse and results. |
| `blackhole.cli` | Subcommands `run`, `chat`, `bench`, `profile`, `smi`. Shared `--device`, `--model`, `--weights` and transition-only `--kernel-backend`. Keep bench prefill length, trace output, server and reset flags on the relevant subcommands. |

Today `llama3.py:262–272` exposes model/weights/backend, `bench.py:44–52` has positional model lists and no weights/backend selection, and `kperf/collect.py:196–204` has a second model/device default and another launch count surface. Share the selection/config parser, retain multi-model benchmark selection, and normalize inferred defaults in one place. `smi.py:42–79` reimplements ioctl, device enumeration and PCI/sysfs handling. Share discovery and ABI helpers with `system.py` while permitting telemetry-only access. `llama3.py:93–102`, `ops_blackhole.py:214–218` and profiler/probe code all repeat setup, argument upload, dispatch and synchronization. A session should own these resources and a fence should identify the queue it waits on.

## Code quality simplifications

- Collapse the two program installers around validated `core -> role -> image` and a grouped multicast packer. The grid helper can populate the common representation. Validate descriptor capacity and multicast geometry before uploading to the bump arena.
- Replace `kperf/stamps.py:40–52`'s process-wide `Path.read_bytes` mutation with an explicit image transform during the transition. Compile-time instrumentation lets kperf work with generated images. A suffix appended after `fw.ret` would be unreachable.
- Treat staged memory and DRAM addresses as typed regions with explicit size and page geometry. This removes duplicated bit packing between `ops_blackhole.py:9` and `ttrv/__init__.py:75–82`, and removes the positional compatibility shortcut in `llama3.py:125–126`.
- Resolve a typed model plan once. Keep checkpoint sizes and upload kinds distinct, treat unexpected kinds as errors, and validate required tensor shape and format before device setup. `llama3.py:82–89` currently classifies every unrecognized upload kind as zero fill and accepts undersized tensors.
- Extract benchmark policy from mutable model metadata. `bench.py:24,36–39` mutates EOS and preloads fabricated KV state through private methods. Make synthetic context and fixed decode length explicit harness inputs. Report actual streamed bytes consistently across bench and sync analysis.
- Retire the decode path's global statistic labels in favor of a result with token IDs, stop reason and timing. Use that result in chat, bench and run. Keep timestamp storage and mutable launch words owned by the request or serialize generation at the model entry point.

## TTRV language ideas

Start with implementable syntax and diagnostics for current sources. The build matrix should exercise both branches of every shipped compile-time specialization across model profiles. The snippets below show prospective syntax where marked.

### Compound SFPU predicates

Current argmax bounds masking, `docs/examples/llama3_argmax.ttrv:88–89`:

```ttrv
sfp.if l5 < l6 { sfp.mov l1, zero }
sfp.if l5 >= l7 { sfp.mov l1, zero }
```

Proposed:

```ttrv
sfp.if l5 < l6 || l5 >= l7 {
    sfp.mov l1, zero
}
```

Implement and test simple inline/block predicates first. Model the compound predicate over the active lane mask, preserve outer CC and validate template size after lowering. Reuse a mask-producing compare where the ISA can implement this efficiently. The change removes duplicate bodies even if some compound cases need the original schedule.

### Name the tile walk and allow a statement body

Current FP8 O conversion, `docs/examples/llama3_o.ttrv:234–240` excerpt:

```ttrv
math.rwc reset
tensix.stall math, srca_vld
repeat 8 { math.mova2d dst[0], addr=copy }
math.rwc reset, release=a
tensix.stall sfpu, math
repeat 32 { replay.run to_fp8 }
math.rwc dst=0
```

Proposed final portion with an ordinary library macro that accepts a hygienic statement body:

```ttrv
tensix.stall sfpu, math
over_fp32_tile! {
    replay.run to_fp8
}
```

The macro expands to 32 footprints and a Dst reset, and declares that the body advances Dst by two rows. Reuse it for inline SFPU bodies and replay bodies while leaving cross-engine barriers visible. Do not hide publication or infer lifetime from register syntax. Add per-TRISC replay occupancy reporting first. O already documents 26 of 32 words consumed by its FP8 replays.

### Remove repeated transfer mechanics at the library level

Current embedding, `docs/examples/llama3_embedding.ttrv:17–18` (the aligned read and following scalar extraction):

```ttrv
noc.read ids, history[i & ~15], n=16, wait
token = ids[i & 15]
```

Proposed hygienic macro using a caller-owned temporary and an explicit result:

```ttrv
token = read_aligned_word!(history, i, ids)
```

The library expansion validates a 16-word `u32` scratch buffer and issues the same 64-byte read. Keep this a macro until enough kernels use it to warrant a builtin. Likewise, use constant tables for the repeated attention chunk offsets from gap item 6, with no runtime array or register allocation.

### Keep the language small

- Keep replay, MOP and SFPU macro scheduling visible because they have different hardware state and budgets. Defer automatic packing of replay lifetimes and implicit cross-engine scheduling.
- Defer device-side graph publication and multi-consumer CB semantics. Host-bound values already solve the scalar launch use case. Add shared CB lifetimes when an actual retained payload needs two independent consumers.
- Check how much `shared` launch-derived expressions save before expanding their semantics. The spec reserves registers for the whole entry function and re-evaluates expressions on consumers. Prefer explicit per-role derived values when long-lived register pressure outweighs line savings.
- Keep typed parameters, explicit address modifiers and static specialization. They encode real ABI and scheduling distinctions. Improve diagnostics and examples before adding new register aliases and general pointer reinterprets. Where an alias is required by the shipped examples, define its scope and validate it in the compiler.

## Open questions for the owner

- Which p150 layouts and host architectures are release targets, and what driver contract covers coherent ring writes and reset quiescence?
- Which numerical tolerances and decode throughput budgets gate the migration per model and context length?
- Is mixed old/compiled mode needed after the new path passes acceptance, and for how long?
- Which sync results and kperf exports still inform decisions? Where should the historical data and tools live?
- Should production defaults use a latency-oriented BF16/FP8 graph or keep model-specific variants where ports or resource limits differ?
