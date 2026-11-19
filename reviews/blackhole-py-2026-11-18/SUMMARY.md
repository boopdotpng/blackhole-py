# blackhole-py review: combined summary (2026-11-18, at 2cab0be)

Reviewers: gpt-6.2-astra, gpt-6.2-sol, claude-fable-5-2, claude-opus-5-5. Full reports are in this directory.
"4/4" means all four reviewers found it on their own.

## Where all four agree

1. **Only 2 of the 7 Llama kernels compile from TTRV** (4/4). Embedding and BF16 O/down build. qkv, attention, gate and lm stop at `alias`, and argmax stops at `sfp.if` (`docs/examples/llama3_argmax.ttrv:88`). `llama3_o.ttrv:191` fails the type check with `-D FP8=1`. `test_ttrv.py` only builds embedding and O, so these failures don't show up in the tests. Commit 2cab0be's title ("Port all Llama 3 kernels") claims more than the code delivers.
2. **Compute and DMA share one timeline signal** (4/4). If the two queues overlap, one queue's signal can retire the other's work. A queue can also store a lower value and move the counter backwards. `llama3.py` always calls `synchronize()` first, which hides this today. `BlackholeGraph.submit` is async and exposes it. Fix: give each queue its own fence value.
3. **The real tie to blackhole-py-old is `manifest.json`, not the `.bin` files** (4/4). It fixes the DRAM layout, the order of launch words, per-core tables, image variants and FP8 scales (stored as encoded SFPLOADI words; fable). `--ttrv` only works because the TTRV `param` order happens to match the exporter's word order (`llama3.py:125`).
4. **`kernels/zero` plus `export.py` is the only code that still imports the old repo** (4/4). Replace it with one TTRV zero kernel, or with DMA copies from a zeroed pinned buffer.
5. **`play/` is mostly an older copy of `kperf/`** (4/4). `observer_dbg.c` is byte-identical. Delete it and keep only the trace export from `kprof.py` if you use it.

## Confirmed bugs (re-read by me or by two or more reviewers)

| Bug | Where | Found by |
|---|---|---|
| Profiler crashes: `model.args_stride` and `model._timestamps` were removed in 2cab0be | `kperf/collect.py:50`, `play/kbench.py:45`, `play/kprof.py:186`, `play/kprof_sample.py:117` | opus, fable |
| Firmware cache: every builder writes the same `{out}.tmp`, so concurrent builds race. The cache key also omits the clang/objcopy version | `fw/__init__.py:68` | astra, sol |
| `Allocator.upload` reserves `len(blob)` bytes but copies `cast("B")` bytes. A numpy array overruns the next allocation. Latent: every current caller passes bytes | `ops_blackhole.py:192-194` | astra |
| `next_timeline()` advances before the ring push. If the push times out, `synchronize()` waits for a value nothing will store. Multi-chunk pushes can leave a prefix committed | `ops_blackhole.py:83,97-108` | astra, sol |
| Firmware hangs silently on an unknown packet op | `fw/queue.c:175-177` | opus |
| `Kernel.arguments()` turns a missing binding into address 0 | `ttrv/__init__.py:51-56` | opus |
| The grid installer skips the image-size, alignment and argument-size checks that the per-core path does | `ops_blackhole.py:115-133` | sol |
| `math.zero` emits ZEROACC with `addr_mode=1`. Safe only because `rwc reset` always follows it | `ttrv/ops.py:315` | fable |
| Host NoC transfers over 16 KiB are accepted and emitted as a single request | `ttrv/noc.py:120` | fable |
| FP8 blobs use cores (14,10)/(14,11), which are service cores on a 12-column card. The failure is a bare assert after a 9.5 GB upload | `ops_blackhole.py:201` | fable |
| `alloc_host` accepts negative sizes; graph patches accept unaligned or negative offsets | `ops_blackhole.py:229,74` | astra |
| Chat labels every non-EOS stop as "context"; user text is tokenized with special tokens enabled (template injection) | `chat/server.py:69-73`, `llama3.py:37-41` | sol |

Suspected, needs a hardware probe: dispatch sends GO before the code multicast has arrived (opus). Harvested columns are assumed to be contiguous (all). Ring stores vs. the MMIO doorbell need a barrier (astra, sol). `AICLK_MHZ=1350` is hard-coded (fable). The kperf stamp ring overlaps TTRV `keep` storage (fable).

## Cuts

- `weights/archive/`: about 32 GB of copies of 8B BF16 (opus checked one shard byte-for-byte).
- 114 `kernels/**/*.S` listings (5.2 MB, 29% of tracked bytes). Only `sync/` reads them.
- RoPE tables (10.5 MB): about ten lines of numpy on the host.
- `ttrv/isa.py`: about 1,700 of its 2,147 lines are wrappers or RVV encoders that nothing calls.
- `sync/`: archive it with the image revision it ran against, and keep its README as a note. `sync/variants/` is missing from `.gitignore`.
- `docs/ttrv_cfg.md` duplicates `kview/data/registers_full.json`. `kview/` can go once TTRV emits its own source-mapped listings.
- Ranged CALL, graph patches and OP_WAIT have no production caller since 2cab0be (fable).

## Consolidation

- One `Device` session with `load`/`run`/`graph`/`fence`. The launch-and-wait line appears 12 times, and there are 3 install functions and 2 program dataclasses.
- One CLI (`run | chat | bench | profile | smi`) with shared `--device/--model/--weights`. Today `bench.py`, `kperf/collect.py` and `llama3.py` each parse their own flags. `smi.py` reimplements the ioctl and enumeration code from `system.py`.
- Each hardware constant in one place. DRAM endpoints are defined in 5 places, NIU offsets in 4 and the ABI in 3.
- Replace `manifest.json` with a Python model plan that binds kernel arguments by name.

## Migration order off blackhole-py-old (common to all four)

1. A/B parity harness: compiled vs. exported, per kernel, compared against `reference.json`. Add a build-matrix test for every kernel and define.
2. Zero kernel and RoPE on the host, which removes the only import of the old repo.
3. Model plan with named bindings, replacing the manifest.
4. Compiler work: `alias`, SFPU ops as a table instead of the if/elif chain in `ops.py:sfp()` (18 of the 21 missing ops are one-instruction wrappers), `sfp.if`, `math.mova2d`, float constants, `dst.tile`.
5. Port in this order: lm+argmax (one unit), qkv, gate, attention, then FP8 O/down. Make `--ttrv` the default and then delete it.
6. Port the hardware probes cited in the spec out of `blackhole-py-old/tests/probes/`, then delete the old repo.

## TTRV language ideas

- `use`/`import` for a prelude: `pack_dst`, `unpack_pair` and `accumulate` are each copied into 4 kernels (opus, fable).
- Macros declare which SFPU registers they clobber, and the compiler checks it. This replaces about 40 `alias` lines (opus).
- The compiler inserts hazard `sfp.nop`s, or at least rejects missing ones. 83 are hand-written today (opus).
- Make `fmt=fp32` the default for `sfp.load`/`store`; it is redundant on 94 of 96 lines (fable).
- Defaults per role for the four stall idioms, which cover 75 of the 102 stall statements (fable).
- Scoped `with cb.reserve/cb.wait` blocks; chunked `noc.read ... chunk=, port=rotate` (opus).
- Compile-time tuple iteration for attention face offsets (astra).
- Candidates to cut from v1, since no Llama kernel uses them: non-entry `fn`, `cb.read`, `sem.init`, `pack.gather`, `noc.status`, `unpack.ctx`, mask MOPs, and most of `sfpmacro` (opus, fable).

## Owner questions (merged)

- Is the 12-column card a target?
- Must ported kernels match the exported ones bit-for-bit, or only within a tolerance?
- May the compiler insert NOPs and stalls on its own?
- Keep `kview/` and `sync/` in-tree or archive them?
- Delete `weights/archive/`?
