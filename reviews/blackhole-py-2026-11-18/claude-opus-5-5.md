# blackhole-py review (claude-opus-5-5, 2026-11-18)

Read-only review of `~/tenstorrent/blackhole-py` at `2cab0be`. Nothing touched the device. What I ran:
- `python3 test_ttrv.py`: all 15 tests pass.
- `python3 -m ttrv build` on every `docs/examples/*.ttrv`, into the scratchpad.
- Read-only `cmp` and `du` on `weights/`.

Paths below are relative to the repo root unless they are absolute.

Two sub-investigations were delegated and then spot-checked by me:
- the tooling inventory (kperf, play, sync, kview, chat, smi);
- the TTRV compiler internals.

Their claims are marked **[verified]** where I re-read the code. Otherwise they are attributed and left as reported.

---

## TL;DR: top 10 actions, ranked by payoff/effort

1. **Make the commit message, README and docs say what is actually true.**
   - Commit `2cab0be` says "Port all Llama 3 kernels to TTRV". Only `llama3_embedding.ttrv` and `llama3_o.ttrv` build. qkv, attention, gate and lm fail at `alias`; argmax fails at `sfp.if` (`llama3_argmax.ttrv:88:20`).
   - `llama3.py` runs 5 of 8 programs (6 of 8 on FP8) from blackhole-py-old exports even with `--ttrv`.
   - Add a test that builds every example at every `-D` variant, so "ported" means "compiles" (this is gap A5).
   - Effort: minutes. Payoff: removes a false sense of progress.
2. **Fix or delete the profiler, which is broken today.**
   - `kperf/collect.py:50` and `play/kbench.py:45` use `model.args_stride`.
   - `play/kprof.py:186` and `play/kprof_sample.py:117` use `model._timestamps`.
   - Both attributes were removed in `2cab0be`, so all four crash with AttributeError. **[verified]**
   - Then delete `play/`: it is an older copy of `kperf/` (byte-identical `observer_dbg.c`, near-copies of the observer, stamps and collect code). Move the 3–4 unique probes to `kperf/probes/`.
3. **Delete ~32 GB of duplicate weights.** `weights/archive/{fp8-source-bf16,speculative-source-bf16}` are copies of `weights/llama3-8b-bf16`: same sizes, and `cmp` of shard 4 is identical. They are separate inodes, not hardlinks.
4. **Stop committing generated artifacts.**
   - `kernels/**/*.S`: 114 files, 5.2 MB, which is 29% of the tracked bytes. They are listings of `.bin` files that `kview` can regenerate.
   - `kernels/*/rope_{cos,sin}.bf16`: 10.5 MB. Compute them on the host from `config.json`.
   - `sync/census.json` and `sync/results/*.json`.
   - Add `sync/variants/` to `.gitignore`.
5. **Replace the `kernels/zero` exporter with no kernel at all.** It is the only code that still *imports* blackhole-py-old. Zero the KV caches with DMA-queue COPYs from one zeroed pinned staging slot (details under Leaving blackhole-py-old, step 1). That deletes `kernels/zero/` and `export.py`.
6. **Implement `alias`, the §10 SFPU instructions, `sfp.if` and `math.mova2d` in the compiler.**
   - This one item unblocks qkv, gate, lm, argmax, FP8 o/down and attention.
   - It is the critical path off blackhole-py-old. The language is not the bottleneck; the backend is.
7. **Replace the exported `manifest.json` with a Python launch plan.**
   - Buffers come from the allocator by name; launch arguments are bound by name through `Kernel.bind`.
   - Today the TTRV kernels must reproduce the old exporter's argument *word order* by convention (`llama3.py:125-126`), and nothing checks it.
   - The TTRV attention port already has a different interface: `start_pos` only, while the manifest passes `kv_blocks, valid_columns, start_pos`. So this step is a prerequisite for porting attention.
8. **Make `fw/abi.h` the single source of the ABI.**
   - Parse it in `fw/__init__.py`, the way `kview/decode.py:461-473` already does.
   - Delete the hand mirror (`fw/__init__.py:10-33`) and `ttrv/hw.py`'s copies.
   - Add `L1_SIZE = 0x180000`. That literal is spelled out in 4 places (`ops_blackhole.py:212`, `ttrv/__init__.py:30,101`, `ttrv/layout.py:24`) plus kview and play.
9. **Make the runtime API public and smaller.**
   - Make `alloc`, `copyin` and `copyout` public. The private `allocator._copyin/_copyout/_alloc` are called 21 times outside the class.
   - Collapse `blackhole_build_program` and `blackhole_build_grid_program` into one function. Move `Kernel.install` out of the compiler and into the device.
   - Add `dev.run(q)` for the "signal + submit + synchronize" idiom, and make `Device` a context manager.
   - One shared `add_device_args(ap)` for `--device` and `--model`.
10. **Add a TTRV standard library (`import`), checked macro clobbers, and automatic `sfp.nop`.**
    - These three language changes remove the most text from the kernels:
      - identical macros are copy-pasted into 4–5 files;
      - there are 83 hand-written `; sfp.nop` hazard pads;
      - register clobbers are documented only in comments.

---

## Bugs

### Confirmed (read and traced)

| # | Where | What and why |
|---|---|---|
| B1 | `kperf/collect.py:50`, `play/kbench.py:45` | `model.args_stride` no longer exists: `llama3.py:160-170` now holds one argument set rebound per run. AttributeError on every `kperf` collection. Even with the fix, `collect.py:77` records `position = len(ids)-1`, but the bound args are those of the *last* position run. **[verified]** |
| B2 | `play/kprof.py:186`, `play/kprof_sample.py:117` | `model._timestamps` was removed in the same commit; AttributeError. **[verified]** |
| B3 | `docs/examples/*` vs the commit message, README:11-12 and `docs/README.md:4` | Five of seven examples do not parse: qkv:163, attention:183, gate:167 and lm:124 at `alias`, argmax:88 at `sfp.if … {`. `llama3_o.ttrv` with `FP8=1` needs `math.mova2d` and SFPU ops the compiler lacks (see the file's own header, line 4). README is honest; the commit message and `docs/ttrv_port_review.md:68,95` are not. |
| B4 | `fw/queue.c:175-177` (`queue_signal_op`) | An unknown op, e.g. a COPY pushed to the CQ, or EXEC/CALL pushed to the DMA queue, falls into `for (;;) {}`. The queue hangs silently and the host sees only a 10 s timeout. `HWQueue.q()` (`ops_blackhole.py:43`) lets any `Op` go to either queue. Fix: give each queue subclass an allowed-op set, and have firmware store an error code in its state block instead of hanging. |
| B5 | `ops_blackhole.py:77-84` (`BlackholeGraph.submit`) vs `:223` | The device comment says "one timeline for both queues: every submitter waits for its work, so signals land in order". `Graph.submit` deliberately does *not* wait. Any DMA submit before the graph retires can store N+1, which the compute queue then overwrites with N: OP_STORE is a plain store, not a max. Every later `wait(N+1)` then times out. Examples are `allocator.upload` and `_copyin`, i.e. anything that builds a program. Today `llama3.py` always calls `_retire` first, so this is latent, but the public API invites it. Fix: two signals, one per queue, or make `next_timeline` assert that nothing is in flight. |
| B6 | `ttrv/__init__.py:51-56` (`Kernel.arguments`) | A missing binding gives zeros, so an unbound DRAM buffer becomes address 0, which is legal DRAM. The spec (§4) says every parameter is supplied each launch. `bind()` deliberately allows partial rebinding, but `arguments()` should require `bindings.keys() == params.keys()`. **[verified]** |
| B7 | `ttrv/expand.py:264`, `:282-284`, `ttrv/codegen.py:152` | (Reported by the compiler sub-review.) `~i32(5)` is rejected as out of range; `u32(0x100000001)` silently folds to 1; bare oversized literals in `const` and `grid` skip `_fit`. All three violate spec §5's "no silent truncation". |
| B8 | `ttrv/noc.py:120-121` | (Reported by the compiler sub-review.) Host endpoints are `Index` remotes, so they skip the 16384-byte request limit. `noc.write h[0], a, n=65536` builds as one oversized request. |
| B9 | `ttrv/__init__.py:28-43` | Keep-storage bookkeeping:<br>• Reinstalling a `keep` kernel lowers `dev.ttrv_keep_base` again and leaks the old region.<br>• The overlap check knows only TTRV kernels. Exported kernels in the same process use L1 from `l1_data_base` (0x12000) up as scratch, so a TTRV `keep` region placed under 0x180000 is silently clobbered by them.<br>• kperf's timestamp ring at 0x100000–0x180000 (`kperf/stamps.py:22`) collides with the same region.<br>No shipped kernel uses `keep` with `--ttrv` today, so this is latent. |
| B10 | `chat/server.py:73` | When generation stops at the `--tokens` limit it reports `stop="context"`. **[verified]** |
| B11 | `play/pc_probe.py:12` | `DebugObserver.stop()` returns two dicts, so `np.diff` of a dict raises. (Reported by the inventory sub-review.) |
| B12 | `.gitignore` | `sync/ablate.py:157` writes ~7 MB per model into `sync/variants/`, which is not ignored, contrary to `sync/README.md:294`. |

### Suspected (plausible from the code; needs a probe or a doc check)

| # | Where | Suspicion |
|---|---|---|
| S1 | `fw/dispatch.c:17-22, 41-45` | **The GO multicast may overtake the code and params multicast.** The code says "Everything goes out on NoC0, so the flush before the GO covers it". `noc_mcast_flush` waits only for `OUTGOING` (data has left L1), not for delivery. The code multicasts use *different rectangles and exclusion masks* from the GO, which uses the header's rect and exclude. A posted NoC write keeps order with a later one only if both take the same route on the same VC, and multicasts to different rectangles need not share a path to a given core. If GO lands first, a worker can fetch stale code from its slot (the icache invalidate doesn't help). tt-metal's dispatcher uses acked/non-posted multicast before a go signal. Probe: launch many tiny programs with distinct images and verify each one's output; or switch the code multicast to acked and measure the cost. |
| S2 | `ops_blackhole.py:200-205`, `fw/init.c:247-249` | **Harvested columns are assumed contiguous.** Only the *count* of enabled columns (`bit_count`) is used; workers are assumed to be x=1..2+cols minus 8 and 9, and `init.c` computes `WORKER_ID` with a hard-coded `x -= 1 + 2*(x>=10)`. This is right only if NoC translation is on and packs harvested columns to the right. The DRAM coordinates (17/18, y 12–23) suggest translation is on, but nothing asserts it. `system.py:73` also rejects everything except p150a/p150b, so the 12-column branch is dead code. Use the actual column mask, or delete the 12-column path. |
| S3 | `ops_blackhole.py:252,256-261` | `self.all = ((1,2),(right,11))` multicasts SOFT_RESET and firmware images over columns 8 and 9 (L2CPU/DRAM). The `cover()` docstring asserts this is "free"; it is worth one line of evidence or an exclude. |
| S4 | `fw/worker_brisc.c:226-229` | The DONE atomic goes out on **NIU 1** to a coordinate the dispatcher read as `noc_coord(0)` (NoC0 frame, `dispatch.c:91`). This is only correct if translated coordinates are NoC-agnostic. `noc.h:165` itself says the NoC1 exclude anchor "mirrors", so the two frames *do* differ somewhere. Assert it, or send the done count on NoC0. |
| S5 | `fw/__init__.py:60` | The firmware cache key hashes sources and flags but not the `clang` version or path. A toolchain upgrade silently reuses stale images. Add `clang --version` output to the key. |
| S6 | `llama3.py:59` | The allocator's `dram_top` is set to `round_up(8 * manifest.dram_top, 1 GiB)` because the manifest hard-codes DRAM addresses. Any allocation made before this line (none today) would overlap the manifest buffers. Item 7 of the TL;DR removes this. |
| S7 | `llama3.py:85` | Uploads only check `t.nbytes <= b["size"]`. There is no dtype or shape check, so a wrong checkpoint (e.g. BF16 weights for the FP8 manifest) uploads garbage without error, and the unused tail is left un-zeroed. |
| S8 | `ttrv/ops.py:122` | e4m3 and e5m2 share format code 10 (sub-review); this is fine only if the config bits that distinguish them are always written. |
| S9 | `smi.py:114` | (Inventory sub-review.) If a telemetry tag is missing, `s["aiclk"]` is None and the `>` comparison raises TypeError. |

---

## Delete / merge / move list

Counts are tracked bytes. Total tracked: 17.9 MB, 375 files.

**Delete**
- `play/kprof.py`, `play/kprof_sample.py`, `play/kbench.py`, `play/kprof_dump.py`, `play/observer.py`, `play/observer_dbg.c` (identical to the kperf copy), `play/observer_dram.c`, `play/pc_probe.py`. All are superseded by kperf, and three of them crash (B1, B2, B11).
- The untracked `play/*.json|*.npz|*.folded` files (~99 MB on disk).
- `kperf/bundles/old/` and every bundle recorded before `2cab0be`: they cannot be regenerated by the current code.
- `kernels/**/*.S` (5.2 MB). They are generated listings: regenerate on demand with kview, or cache them under `~/.cache`.
- `kernels/*/rope_{cos,sin}.bf16` (10.5 MB). That is ~10 lines of numpy, including Llama 3.1's rope scaling, run at load time.
- `kernels/zero/` (8 `.bin` files and `export.py`). Replace with DMA zero-fill.
- `weights/archive/` (~32 GB of duplicates; untracked, but it is on disk in the repo tree).
- `ttrv/isa.py` dead weight. Per the sub-review, 98.6 KB of the 143.5 KB are 137 per-instruction wrapper functions that are never called, and 4 of the 7 ttko enums are unused while the code hard-codes their values. Keep the table, `rv`, `tensix`, the decoders and the enums that are actually used.
- `test_graph.py:10`: the comment refers to `GRAPH_CHUNK`, which no longer exists in `ops_blackhole.py`. Fix the comment.

**Move**
- Keep `play/dram_timeline.py`, `play/ts_probe.py` + `ts_kernel.c`, `play/dram_niu_probe.py` and `play/l1_highwater.py`, but move them to `kperf/probes/`.
- Move `sync/` to `docs/archive/sync.md` and keep the scripts only if you will run them again. Its premise ("blackhole-py runs the images blackhole-py-old generated") stops being true with item 6.
- Move `kview/`, `kperf/` and `smi.py` under `tools/`, so the top level is runtime + model + compiler.
- Move `docs/examples/*.ttrv` to `kernels/llama3/*.ttrv`. They are the production kernel sources, not examples, and `llama3.py:118` loads them from `docs/`.

**Merge**
- `bench.py:34-36` and `kperf/collect.py:41-44`: identical random-KV-fill code; make it `Llama3.fill_kv_random()`.
- `docs/ttrv_port_review.md`, `docs/ttrv_gaps.md` and `docs/kernels.md`:
  - merge into one "status and open questions" doc;
  - drop the parts that are now false (port_review :68 and :95, kernels.md :159 and :183 "assembler" framing);
  - drop kernels.md's absolute `/home/boop/...` links (:179, :181).
- `docs/ttrv_cfg.md` (886 lines): it says it was generated from `cfg_defines.h`, but no generator exists. Either commit the generator or delete the doc and point at tt-llk.
- `docs/ttrv_pack_unpack.md`: uses `unpack.cfg/pack.cfg` syntax that exists neither in the spec nor in the compiler (§3–6), and cites `Device.boot()` and `tt-smi`. Fold its measured facts into spec §9 and drop the syntax.

---

## Leaving blackhole-py-old: dependency inventory and migration plan

### Inventory

| Dependency | Kind | Where |
|---|---|---|
| `kernels/zero/export.py` | **direct import** of `asm.Asm`, `ttko.isa.R`, `ttko.noc.NoC`, `pcie.P150_DRAM_ENDPOINTS` | the only live code import |
| `kernels/llama3-*/{qkv,attention,gate,lm,argmax}/*.bin`, plus `o`/`down` on FP8 and `embedding` without `--ttrv` | prebuilt images | Exported by `blackhole-py-old/tools/rewrite_export/export_llama3.py` from `examples/llama3/kernels.py` (see the `.S` headers). There are `.v0`/`.v1` variants for down. |
| `kernels/llama3-*/manifest.json` | **the whole model plan** | Fixed DRAM addresses, per-core parameter tables at `DATA_BASE + 0x40*k`, per-launch argument word lists, persistent L1 state addresses, `dram_top`, `static_base`/`l1_param_base` asserted against fw (`llama3.py:108`). All generated by the old exporter. |
| `rope_{cos,sin}.bf16`, `reference.json` | data from the old exporter and the old `tools.bench_llama_decode` | `reference.json` gates the "matches blackhole-py" line in `llama3.py:312-317` |
| Frozen fw L1 layout | ABI | `fw/abi.h:104-105`: firmware cannot grow because the exported kernels have `L1_PARAM_BASE`/`DATA_BASE` compiled in |
| PCIe mid address | ABI | `llama3.py:158`: the exported argmax has `0x10000000` compiled in |
| `ttrv/isa.py:20,386` | borrowed enums | `Stall`, `Wait`, `SemWait`, `LReg`, `SfpuFormat`, `LoadImm`, `Broadcast` from ttko. The encoders came from tt-llk, which is fine. |
| Hardware evidence | probes | Spec §8/§9 rules cite `blackhole-py-old/tests/probes/*` (`ttrv_spec.md:672,718,816`; `ttrv_pack_unpack.md:8,261,319`). If old goes away, so does the evidence for the CFG shared-word rule and the SrcB release rule. |
| `sync/` | analysis of the exported `.S` | `sync/census.py` |
| docs links | text only | `docs/kernels.md:113,134-135,179,181`, `docs/ttrv_port_review.md:17-20` |

### Migration order

0. **Build gate first.** `test_ttrv.py` builds every example at every variant: 1B/8B BF16/FP8 × EMBED_TILES etc. CI is red until each kernel compiles; this is the honest progress meter.
1. **zero → no kernel.** Add `Device.fill_zero(addr, n)`. It is a loop of DMA `COPY dst+i*S ← stage_zero` with one zeroed 8 MiB pinned slot, reused as the source, with no host memcpy. The 8B KV cache (~1 GiB) takes a fraction of a second.
   - This deletes `kernels/zero` and `export.py`, the last *import* of old.
   - Alternative: a 10-line `zero.ttrv` (`for i in 0..n { noc.write cache[...], z, n=8192, wait }`).
2. **Launch plan in Python, not the manifest.**
   - `llama3/plan.py` derives buffers from `config.json` (sizes and page sizes) and allocates them with the allocator.
   - It names launches with TTRV param names and binds them through `Kernel.bind`.
   - Exported programs keep working through a thin "legacy program" adapter that maps names to their word order. Write it once, from the manifest, during the transition.
   - Compute RoPE tables on the host.
   - This decouples every later step from the exporter's ABI. TTRV attention needs it, since its parameters differ.
3. **Compiler features, in this order:**
   - `alias` (parse only);
   - the missing §10 SFPU instructions (sub-review list: abs, and/or/xor/not, iadd/isub, shl/shr/sar/shift, minmax, exexp/exman/setexp/setsgn, cast, recip, if, …);
   - `math.mova2d`;
   - the sfpmacro install (§12 item 8).
   Each one is mechanical against the existing encoder table.
4. **Kernels, easiest first, each gated by a CPU reference in `test_ttrv_hardware.py` and the end-to-end token match:**
   - argmax (scalar + `sfp.if`);
   - lm (BF16 projection + `alias`/`sfpmacro`);
   - FP8 o/down (mova2d + round_e4m3);
   - qkv (rmsnorm, rope, `sfpmacro`);
   - gate (rmsnorm, exp, recip, silu);
   - attention last (handles, partial writes, merge, persistent counters).
5. **Port the probes the spec relies on to TTRV hardware tests:** cfg shared word, SrcB release, pack-one, unpack contexts. Keep the evidence in this repo.
6. **Delete.**
   - `kernels/llama3-*/` except whatever replaces `reference.json`. Regenerate references with the new runtime; keep the old numbers in a doc table.
   - Remove the `static_base`/`l1_param_base` assert and the abi.h "frozen" comment.
   - Move the `ttrv/isa.py` enums to a local definition (cite tt-isa-documentation instead of ttko).
   - Delete `sync/`, or archive it as a doc.
   - Remove `--ttrv`: TTRV becomes the only path.
7. **Then free the L1 layout.** Re-pick `DATA_BASE`, `L1_PARAM_BASE` and the TRISC code sizes for the fw's needs. They are no longer pinned by binaries.

---

## Hand assembly that should not be hand assembly

| Where | What | Owner |
|---|---|---|
| `fw/__init__.py:86-92` | `ret()` (jalr) and `jal()` encoders by bit-twiddling, used by `ttrv/codegen.py:512` and `ops_blackhole.py:260` | `isa.rv("jalr", …)` / `isa.rv("jal", …)` |
| `kperf/stamps.py:29-32` (and `play/kprof.py:36-38`) | Hand-encodes `lui`/`addi`/`sw` to stamp the timestamper, then splices the stamps around images by monkeypatching `Path.read_bytes` globally (`stamps.py:42-52`) | TTRV `prologue`/`epilogue` hook, or `isa.rv` plus an `_install` hook in `Llama3` |
| `kernels/zero/export.py` | `Asm` from old | delete (step 1) |
| `fw/hw.h:265-301` | `TTINSN(w)` and seven magic Tensix words (`ZEROACC_ALL 0x10180000`, `SFPENCC_RESET`, `SEMINIT_ALL`, …) | Generate a `fw/tensix_words.h` from `ttrv.isa` at fw build time (fw is already built from Python), so one encoder owns every word |
| `ttrv/movement.py:105-106,155-156`, `ttrv/ops.py:363-366`, `ttrv/sfpmacro.py:98` | Instruction fields packed with literal shifts outside the table (sub-review) | Generalise `ops.runtime_word` (`ops.py:208`) to several fields |
| `ttrv/ops.py:172-202,327,527`, `sfpmacro.py:9,92-93,123-124` | Magic values for LReg ONE/ZERO, LoadImm modes, SfpuFormat, Broadcast and SemWait, even though `isa.py` has the enums | use the enums |
| `kperf/observer*.c`, `play/observer*.c` | Redefine the NIU base and the command-buffer layout (copies of `fw/noc.c:10-16`) | Move those definitions from `noc.c` into `fw/noc.h` and `#include` it |

---

## Runtime / flags / firmware consolidation

### What is duplicated or scattered today

- **Device open:** `system.PCIIface` and `smi.py:51-77` each have their own ioctl wrapper, CHIP_IN_USE lock, SET_POWER_STATE and telemetry walk. `ops_blackhole.py:244-250` walks the table a third way.
- **Program install, three entry points:**
  - `blackhole_build_program` (`ops_blackhole.py:115`);
  - `blackhole_build_grid_program` (`:126`);
  - `ttrv.Kernel.install` (`ttrv/__init__.py:19-46`), which imports the runtime and mutates `dev.ttrv_keep_base`, `dev.ttrv_scratch_end` and `dev.descriptor_top` indirectly.
  - Plus raw launches that bypass the dispatcher entirely (`kperf/observer.py:25-29,93-97`).
  - The LAUNCH role mask is computed three times (`ops_blackhole.py:123,131,268`).
- **Submit idiom:** `Q().….signal(dev.timeline_signal, dev.next_timeline()).submit(dev); dev.synchronize()` appears in `ops_blackhole.py:171,217`, `llama3.py:101`, README and kperf.
- **Allocator internals used outside the class:** `_alloc`, `_copyin` and `_copyout` from `llama3.py`, `bench.py`, kperf and both tests (21 call sites). Tests also set `allocator.dram_top` directly (`test_graph.py:18`, `test_ttrv_hardware.py:77`).
- **L1 arena state spread across the device:** `dev.ttrv_keep_base`, `ttrv_scratch_end` and `descriptor_top`, plus magic `0x180000`.
- **ABI constants copied by hand:**
  - `fw/__init__.py` mirrors `fw/abi.h`;
  - `ttrv/hw.py` and `ttrv/noc.py` copy `fw/abi.h`, `hw.h` and `noc.c` (WORKER_X/Y/ID, the NIU offsets 0x148/0x240/0x280, the DRAM and PCIe coordinates);
  - kview *parses* abi.h, which is the right approach.
- **Flags differ across scripts** (full table from the inventory):
  - `--device` is an int in llama3, bench, kperf and the tests; repeatable `-d` in smi; positional in `play/ts_probe.py`; missing (hard-coded 0) in five play scripts. `BlackholeDevice` itself takes the string `"BLACKHOLE:N"`.
  - `--model` is `choices=MODELS` in llama3 and kperf, a positional list in bench, and free text with a different default (`8b-fp8`) in `sync/ablate.py`.
  - `--tokens` defaults are None, 3, 6, 24 and 64.
  - The output flag is `--out`, `--name`, or `--json`/`--trace` depending on the script.
  - All three servers bind `0.0.0.0` by default; `127.0.0.1` is the safer default.
- **The DRAM peak rate has three values:**
  - 512e9 in `bench.py:10`;
  - 514.6 GB/s in `kperf/collect.py:32` and `play/dram_timeline.py:34`;
  - 506 GB/s in `sync/results.md`.

### Target layout

```
bh/                      # runtime (≈ system.py + helpers.py + ops_blackhole.py, ~450 lines)
  pci.py                 # ioctl table (named), PCIIface, Sysmem, telemetry(tag)  ← smi.py imports this
  device.py              # Device, Queue, DMAQueue, Graph, Program, L1Arena, DRAM allocator
fw/                      # C + __init__.py; ABI parsed from abi.h (one source)
ttrv/                    # compiler only: build(source, defines) -> Kernel (no runtime import)
llama3/
  model.py               # Llama3: plan + weights + graph + generate
  plan.py                # buffers & launches from config.json (replaces manifest.json)
  tokenizer.py
  kernels/*.ttrv         # was docs/examples
tools/  smi.py  bench.py  kperf/  kview/  chat/
cli.py                   # add_device_args(ap), add_model_args(ap)
```

### Public API sketch

```python
with Device(0) as dev:                          # int index; context manager closes/resets
  buf = dev.alloc(nbytes, page=2048)            # DRAM, bump; dev.alloc_host(n) for pinned
  dev.write(buf, data); dev.read(buf, out)      # staged DMA (was allocator._copyin/_copyout)
  dev.fill_zero(buf, nbytes)                    # DMA from a zero slot (replaces kernels/zero)
  prog = dev.install(kernel)                    # ttrv.Kernel or {core: {role: bytes}}; one path
  args = prog.args(); prog.bind(args, x=buf, pos=3)   # name-checked, all params required at first bind
  dev.run(Queue().exec(prog, args))             # submit + signal + synchronize
  g = dev.graph(q); g.submit(); g.wait()        # async; Device tracks in-flight per queue (fixes B5)
```

`L1Arena` owns `scratch_base`, `keep_top` and the descriptor arena. Exported/legacy programs register their L1 footprint with it so that B9 becomes impossible.

Firmware build and load stay as they are (cached clang build, boot, then two queue programs, then `init` on the workers), but with these changes:
- `fw.images()` returns a dataclass instead of a dict keyed by strings like `"worker_brisc"`;
- the role-mask helper lives in `fw`;
- the cache key includes the clang version (S5).

---

## Code-quality simplifications

- **Naming.**
  - Rename `BlackholeDevice`, `BlackholeComputeQueue`, `BlackholeDMAQueue`, `BlackholeGraph`, `BlackholeProgramData`, `blackhole_build_program` and the rest to `Device`, `Queue`, `DMAQueue`, `Graph`, `Program`, `install`. The prefix carries no information in a Blackhole-only repo.
  - `HWQueue.q()` → `packet()`.
  - `fw.ret()` returns *bytes* but is used as a word (`codegen.py:512` converts it back to an int).
  - The compiler's `Generator.condition()` evaluates any scalar; rename it `scalar()`.
- **`BlackholeAllocator`** mixes DRAM bump allocation with staged host↔device copies. Split them:
  - the allocator becomes 10 lines;
  - copy moves to `Device.write/read`.
  - `_copyout` synchronizes every chunk (`ops_blackhole.py:189`); use the same two-slot pipeline as `_copyin`.
- **`blackhole_build_program` and `blackhole_build_grid_program`** become one `install(images: dict[core, dict[role, bytes]])`, plus a helper `grid(n, roles)` that returns that dict. `_install_program` already accepts either shape.
- **`Llama3.__init__`** opens the device, uploads weights, installs and builds the graph in one constructor. Split it into `Llama3.load(dev, model)` so tests and kperf can reuse an open device. kperf's `ProfiledLlama3` subclass then wouldn't need to monkeypatch `Path.read_bytes`.
- **`Llama3._install`** has three code paths (TTRV, exported, persistent). After the migration it is one loop: `for name, k in kernels.items(): prog[name] = dev.install(k)`.
- **`llama3.py:200-202`** recomputes dynamic args from a hard-coded dict of seven names on every position. With TTRV params, have one `bind(token_pos=pos)` and derive the rest in the kernels' `shared {}` blocks. The attention port already does this.
- **`fw/__init__.py:10-33`** hand-mirrors abi.h with a few spot asserts. Replace it with `ABI = parse_defines(HERE / "abi.h")`; the evaluator already exists in `kview/decode.py`.
- **`fw/noc.c` / `ttrv/noc.py`:** make the NIU register map one header (`noc.h`). The Python compiler can read it the same way as abi.h.
- **Compiler** (from the sub-review, which I agree with):
  - The drain pattern is written three times (`codegen.py:120-123`, `ops.py:450-451`, `movement.py:245-246`); make it one `g.drain()`.
  - The 32-bit SFPLOADI pair is written three times; make it one helper.
  - There are three option parsers (`ops.bind`, `layout.options`, and inline scans); unify them.
  - `math.addrmod` and `math.rwc` share one branchy loop (`ops.py:223-301`); split them and drive them from a table.
  - `args_size` recomputes slots that the layout already knows (`ttrv/__init__.py:59-61`).
  - The listing prints Python dict reprs (`emit.py:62`).
- **`smi.py`** imports nothing on purpose, so it won't power the card. Keep that property, but give `bh/pci.py` a `power=False` open mode so the ioctl and telemetry code exists once.

---

## TTRV language ideas

Usage counts across the seven kernels:
- user-defined non-entry `fn`: **0**
- `cb.read`: **0**
- `sfpmacro`: 5, in 3 files
- `; sfp.nop`: 83
- `alias`: 40
- `cb.reserve`/`cb.push` pairs: 34
- `cb.wait`/`cb.pop` pairs: ~37
- `math.rwc dst=cr+8` written twice in a row: 16 pairs
- byte-identical macro bodies (md5): `unpack_pair` and `pack_dst` in 4 files each; `accumulate` in 4 files, in two variants

### 1. `import` a kernel library (the biggest win)

Spec §3 says "There are no includes", but every projection carries the same 30–60 lines.

Before (identical in qkv, gate, lm and o):
```ttrv
macro unpack_pair(left, right) {
    repeat face in 0..4 {
        unpack.move a, left + face * 256, n=256, dvalid
        unpack.move b, right + face * 256, n=256, dvalid
    }
}
macro pack_dst(q) {
    sem.stall tdma|pack|sync, dst_full, nonzero
    p = cb.reserve q
    pack.move p, dst[0]
    tensix.stall sync, pack0
    tensix.wait
    cb.push q
    sem.dec dst_full
}
replay accumulate { sfp.load l0, dst[0], fmt=fp32; sfp.mad l7, l0, one, l7; math.rwc dst+=2 }
macro reduce_lanes(sum) { ... 14 lines ... }
```
After:
```ttrv
import "lib/dot.ttrv"      // unpack_pair, pack_dst, accumulate, dot_face, reduce_lanes
import "lib/sfpu.ttrv"     // exp, recip, rsqrt, round_e4m3
```
Rules:
- Only file-level `const`, `type`, `macro`, `mop`, `replay` and `sfpmacro` can be imported. `param`, `cb`, `l1`, `sem` and `fn` cannot.
- Names are file-scoped, with no transitive re-export.
- `-D` does not reach into the imported file.

This keeps "no textual substitution" while killing the copy-paste. It also means a fix to `round_e4m3` (gate) reaches o's `to_fp8`, which is the same algorithm written a second time with different registers (`llama3_o.ttrv:88-108` vs `llama3_gate.ttrv:212-232`).

### 2. Macros declare what they use and what they clobber (turn the comments into checks)

Before (`llama3_gate.ttrv`):
```ttrv
// l0 = 1 / sqrt(l0) for finite positive FP32 l0; clobbers l1-l6.
macro rsqrt() {
    alias v = l6
    alias y = l1
    alias t = l2
    alias c1 = l3
    alias c2 = l4
    alias half = l5
    ...
```
After:
```ttrv
macro rsqrt(x: l0) clobbers l1..l6 {
    sfp.temps v, y, t, c1, c2, half    // allocated from the clobber set, in order; listing shows the mapping
    ...
```
The compiler checks that:
- the body writes no SFPU register outside the clobber set;
- at each call site, nothing live (an `alias`ed or declared-needed register such as `exp`'s "needs l4 = 127.0, l12 = log2(e)") is in that set.

That is a cheap lexical check, not register allocation. It removes 40 `alias` lines, and it catches the most likely class of SFPU bug: a `round_e4m3` that silently trashes `l7` used by the caller's `accumulate`.

### 3. Insert hazard `sfp.nop`s (or at least reject missing ones)

Spec §10 says "The compiler inserts no `sfp.nop`". The hazard table *is* in the spec (mad-family result read by iadd, and/or, minmax, shft2, SFPCONFIG reading L0, …), and the compiler already knows every instruction's operands. The authors already treat these pads as mechanical: they write `; sfp.nop` after every mad-family op regardless of the reader.

Before (`llama3_o.ttrv:121-135`):
```ttrv
repeat 4 >> stage { sfp.shft2 l1, l1, rotate; sfp.nop }
sfp.add l0, l0, l1; sfp.nop
...
sfp.add l0, l0, l1; sfp.nop
sfp.add l0, l0, l2; sfp.nop
sfp.add l0, l0, l3; sfp.nop
```
After:
```ttrv
repeat 4 >> stage { sfp.shft2 l1, l1, rotate }
sfp.add l0, l0, l1
...
sfp.add l0, l0, l1
sfp.add l0, l0, l2
sfp.add l0, l0, l3
```
The listing marks each inserted NOP with the hazard that caused it. Several of the hand-written pads above are probably unnecessary: a mad-family result read by another `sfp.add` auto-stalls. If inserting stays off the table on principle, at least ship the checker now in reject-only mode. That is the half §10 already promises.

### 4. Scoped CB blocks

Before (`llama3_o.ttrv:171-177`):
```ttrv
for batch in 0..INPUT_TILES / BATCH_TILES {
    w = cb.reserve weights, n=BATCH_TILES
    noc.read w, matrix[row * INPUT_DIM + batch * BATCH_TILES * 1024], n=BATCH_TILES * 1024, port=core.id % 3, wait
    cb.push weights, n=BATCH_TILES
}
```
After:
```ttrv
for batch in 0..INPUT_TILES / BATCH_TILES {
    with w = cb.reserve weights, n=BATCH_TILES {      // push n at the closing brace
        noc.read w, matrix[(row * INPUT_TILES + batch * BATCH_TILES) * 1024], n=w.elems, port=core.id % 3, wait
    }
}
```
`with y = cb.wait q, n=k { ... }` pops k at the closing brace. Early `return`/`break` inside the block is an error. The block removes ~70 lines and the mismatched-`n` bug class (`cb.pop keys, n=HEAD_TILES` must match the `cb.wait`). `w.elems` (pages × page elements) removes the repeated count arithmetic.

### 5. Chunked requests on one handle (fixes gap C12 without "handle declarations")

Before (`llama3_attention.ttrv:386-394`):
```ttrv
kr = noc.read kp, key_cache[first], n=1024, port=0
vr = noc.read vp, value_cache[first], n=1024, port=HEAD_TILES % 3
for f in 1..HEAD_TILES {
    noc.read kp + f * 1024, key_cache[first + f * 1024], n=1024, port=f % 3, tid=kr
    noc.read vp + f * 1024, value_cache[first + f * 1024], n=1024, port=(f + HEAD_TILES) % 3, tid=vr
}
noc.wait kr, vr
```
After:
```ttrv
kr = noc.read kp, key_cache[first], n=HEAD_TILES * 1024, chunk=1024, port=rotate
vr = noc.read vp, value_cache[first], n=HEAD_TILES * 1024, chunk=1024, port=rotate(HEAD_TILES)
noc.wait kr, vr
```
`chunk=` splits the transfer into requests of that many elements on one handle. `port=rotate(k)` cycles the three ports starting at k. This also fixes B8: host/remote transfers over 16 KiB become chunked instead of oversized. The same option shortens `o`/`gate`'s `port=core.id % 3` streaming loops.

### 6. Let `math.rwc` take any increment and split it

Before (16 pairs, e.g. `llama3_o.ttrv:240-241`):
```ttrv
math.rwc dst=cr+8
math.rwc dst=cr+8
```
After: `math.rwc dst=cr+16`. The compiler emits ⌈n/15⌉ SETRWC/INCRWC instructions and the listing shows them. The spec already allows "select instruction forms". It also lets the `faces` macro below lose a line.

### 7. Statement-block macro arguments (gap F30)

Before (`llama3_gate.ttrv`, plus the inline copy in `o:trisc1`):
```ttrv
macro faces(body, runs) {
    repeat 4 {
        repeat runs { replay.run body }
        math.rwc dst=cr+8
        math.rwc dst=cr+8
    }
    math.rwc dst=0
    tensix.stall sync, math|sfpu
}
```
After:
```ttrv
macro faces(runs) block {
    repeat 4 { repeat runs { block }; math.rwc dst=cr+16 }
    math.rwc dst=0
    tensix.stall sync, math|sfpu
}
faces!(8) { replay.run accumulate }
faces!(8) { silu_combine!() }          // inline bodies too, not only replays
```

### 8. Conditional types and declarations as one line

Before: `if FP8 { type W = e4m3 } else { type W = bf16 }` and `if FP8 { param scales: fp32[] }`.

After: `type W = FP8 ? e4m3 : bf16` and `param scales: fp32[] if FP8`. This is small, but `if FP8` appears 34 times, and most of them guard a single declaration.

### 9. Compound SFPU predicates (gap E23)

Before (`llama3_argmax.ttrv:87-88`):
```ttrv
sfp.if l5 < l6 { sfp.mov l1, zero }
sfp.if l5 >= l7 { sfp.mov l1, zero }
```
After: `sfp.if !(l6 <= l5 < l7) { sfp.mov l1, zero }`. The chained form lowers to two compares under one predication push/pop, so a datum costs one `if` instead of two.

### Spec features that cost more than they pay (for v1)

- **Non-entry `fn` with multi-return and call-site register reservation (§5 Functions/Registers).** It is used **zero times** in the seven kernels; macros do everything. The sub-review hit `register.full` with a 3-deep chain, and the resolve pass has fragile entry-function handling (`codegen.py:534,548`). Drop it from v1 or freeze it at "leaf functions only".
- **`sfpmacro` (§11).** It has 5 uses, an unresolved install form (§12 item 8), and collision/clobber rules the compiler does not implement (only simple vs round within one macro, `sfpmacro.py:102-105`). Keep it as an explicitly unchecked escape hatch until the RMSNorm path needs it, and don't spec rules you don't check.
- **`-D` overriding floats and types, and constants declared only inside untaken branches (§3).** That is a lot of resolution machinery for 3 overrides in practice (`EMBED_TILES`, `INPUT_TILES`, `FP8`). Limit `-D` to integer `const`s declared at file level.
- **Positional-or-named operands with an "everything after a named one must be named" rule (§2 rule 3).** That rule is the hardest thing to explain in the syntax. Choose one form per operand; the examples nearly always use the positional form.
- **`cb.read q, pushed|popped`:** unused. Remove it until a kernel needs non-blocking CB protocol.
- **`unpack.ctx`** is implemented (`ttrv/movement.py:213`) but not in the spec. Either spec it or remove it.

---

## Open questions for the owner

1. **Is the 12-column (p100/harvested) path a goal?** If not, delete `cols in (12, 14)` and the related comments. If yes, S2 must be resolved with the real column mask first.
2. **Ordering evidence for S1:** is there a measurement showing GO cannot overtake differently-shaped code multicasts? If none, are you willing to pay for an acked multicast (or one rectangle for code, mirroring the GO's) to remove the risk?
3. **Byte-exact replacement or numerically equivalent?** Should the TTRV kernels reproduce the exported kernels bit-for-bit (`reference.json` token match), or is "matches a CPU reference within tolerance" enough? This decides how much of the old schedule each port must copy, and whether `reference.json` survives.
4. **May the TTRV attention kernel define the launch ABI** (`start_pos` only), with `manifest.json` retired, before the other kernels are ported? This is item 7 of the TL;DR and it gates attention.
5. **May `fw` get an `L1_SIZE` and a re-laid-out L1 once the exports are gone?** The 0x9000 code ceiling and the TRISC 6 KiB slots were sized for the exported attention.
6. **Is it acceptable for the compiler to insert hazard NOPs**, as listed ops with reasons? Or must the source stay complete, with a checker only? Same question for splitting `math.rwc` increments.
7. **Is `sync/` worth keeping as code,** or only as a write-up? Its premise ends with the migration.
8. **`weights/archive/` is 32 GB of byte-identical copies:** safe to delete, or are the directory names (fp8-source, speculative-source) used by some external script?
