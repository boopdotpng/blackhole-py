# blackhole-py review (claude-fable-5-2, 2026-11-18)

Scope: `~/tenstorrent/blackhole-py` at `2cab0be` (clean tree), read against `blackhole-py-old`, `tt-kmd/ioctl.h`,
`tt-isa-documentation` and `tt-llk`. Read-only; no device access. What I ran: `python3 test_ttrv.py` (15/15 ok),
`python3 -m ttrv build` on all seven `docs/examples/*.ttrv` into a scratch dir, small compiler probes, a brute-force of
`cover()` over every grid size, `pyflakes`, and decoding of manifest words with `ttrv.isa`. Everything marked
"confirmed" below was checked by reading the code path end to end or by executing it; "suspected" means I could not
prove it without hardware.

State of the tree in one paragraph: 375 tracked files, 18 MB. 249 of them (17 MB) are `kernels/` artifacts exported from
`blackhole-py-old`. The runtime proper is small and tight (`helpers.py` 40, `system.py` 97, `ops_blackhole.py` 270,
`fw/` ~700 lines C+py, `llama3.py` 341). The TTRV compiler is 5,550 lines of which 2,147 are `ttrv/isa.py`. Two of seven
Llama kernels compile from TTRV (embedding, O/down BF16); the other five do not parse yet (`alias`), and 21 of the 63
device operations they use have no backend. Tooling (`kperf/`, `play/`, `kview/`, `sync/`) is 4,000 lines that all
reverse-engineer or patch the exported blobs.

---

## TL;DR: top 10 actions, ranked by payoff / effort

1. **Delete `play/` and fix `kperf` (one line).** `play/` is the precursor of `kperf/` (same observer C files, same
   stamps, same collector) and four of its scripts are broken by `2cab0be` (`model.args_stride`, `model._timestamps` no
   longer exist). `kperf/collect.py:50` has the same `args_stride` bug: the collector crashes after the weights are
   uploaded. Fix: `args = model.args_base + ARGS * k`. Effort: minutes. Removes 13 files.
2. **Cut `ttrv/isa.py` from 2,147 to ~450 lines.** The 137 per-instruction wrapper functions (lines 586-2147) are never
   called (every caller uses `isa.tensix("NAME", ...)`), and the RVV/F/Zb encoders (lines ~62-360) are, by the file's own
   comment, "not used yet". The same field documentation already lives in `kview/data/isa.json`. Effort: an hour.
3. **Table-drive the SFPU/math lowering and add `alias`, float constants, `dst.tile`, `math.mova2d`.** This is the
   critical path out of `blackhole-py-old`: 18 of the 21 missing operations are one-instruction SFPU wrappers that become
   table rows once `ops.py:sfp()` stops being an if/elif chain. By my scan of the sources that set is everything
   `llama3_lm.ttrv` and BF16 `llama3_qkv.ttrv` lack; `sfp.if` and `sfp.index` then unlock argmax, gate and FP8.
4. **Replace `manifest.json` with an in-repo model plan and bind arguments by name.** Today `--ttrv` kernels receive the
   old exporter's positional argument words and only work because the parameter order happens to match
   (`llama3.py:125`). The plan (buffers, launches, bindings, ~150 lines of Python) is what actually removes the exporter;
   the blobs fall away kernel by kernel after it. It also fixes the FP8 problem in item 6.
5. **Two-hour kills of old-repo artifacts:** write the KV-zero kernel in TTRV (10 lines, `noc.write` only) and delete
   `kernels/zero/` + `export.py` (the only file that imports `blackhole-py-old`); generate the RoPE tables with numpy at
   startup and delete 10.5 MB of `rope_*.bf16`; delete the 114 `.S` listings (5.2 MB, read only by `sync/`).
6. **Fix the correctness bugs that are cheap:** `math.zero` applies address-modifier slot 1 (`ttrv/ops.py:315`);
   host NoC transfers over 16 KiB are not rejected (`ttrv/noc.py:120`); FP8 scales are baked into the manifest as
   pre-encoded `SFPLOADI` words so `--weights` silently uses the export checkpoint's scales; FP8 blobs cannot run on a
   12-column card but the device accepts one; compiler leaks `OverflowError`/`ValueError`. Details below.
7. **One device API: `dev.load(x)`, `dev.run(prog, args)`.** The line
   `BlackholeComputeQueue().exec(p, a).signal(dev.timeline_signal, dev.next_timeline()).submit(dev); dev.synchronize()`
   appears 12 times. Three program-install functions and two program dataclasses collapse to one each. `Kernel.install`
   moves out of the compiler package.
8. **One source of hardware constants.** DRAM endpoint coordinates exist in 5 places, NIU register offsets in 4, the L1
   size literal `0x180000` in 5, the ABI in 3 (`fw/abi.h`, the hand mirror in `fw/__init__.py`, `ttrv/hw.py`). `kview`
   already has a 12-line `parse_abi`; use it in `fw/__init__.py` and delete the mirror and its asserts.
9. **One CLI and a package.** Six entry scripts define `--device`/`--model` six different ways, three HTTP servers each
   default to `0.0.0.0`, and there are 19 `sys.path` inserts across 18 files. `python -m bh {run,chat,bench,smi,build,kperf,test}`
   with one shared parser. Move production kernel sources out of `docs/examples/`.
10. **TTRV: add `use` (shared prelude), make `fmt=` default to the configured format, role-default stall units, block
    macros; cut the features no Llama kernel uses.** Measured on the seven kernels: `pack_dst`/`unpack_pair`/
    `accumulate` are defined four times each; 94 of 96 `sfp.load`/`sfp.store` lines carry a redundant `fmt=fp32`; four
    stall idioms account for 75 of 102 stall statements; non-entry `fn`, mask MOPs, `pack.gather`, `noc.status`,
    `cb.read`, `sem.init`, `unpack.ctx`, `sfpmacro after=` are used by none of them.

---

## Bugs

### Confirmed

**B1. `kperf/collect.py:50`: `AttributeError: args_stride`.** `2cab0be` replaced per-position argument tables with
one argument set (`llama3.py:160-170`), and `Llama3` no longer has `args_stride`. `kperf.collect` uploads weights, runs
a generate, then dies. Same in `play/kbench.py:45`. `play/kprof.py:186` and `play/kprof_sample.py:117` call
`model._timestamps`, which also no longer exists. Fix for kperf: `args = model.args_base + ARGS * k` (the single
argument set holds the last position's values after `generate`).

**B2. `math.zero` has a hidden side effect: it applies address-modifier slot 1.** `ttrv/ops.py:315` emits
`ZEROACC(clear_mode=1, use_32_bit_mode, 0, addr_mode=1, face)`. I built `fn trisc1() { math.zero face=2, fmt=fp32 }` and
the listing shows `ZEROACC {'clear_mode': 1, ..., 'addr_mode': 1, 'where': 2}`. Per
`tt-isa-documentation/WormholeB0/TensixTile/TensixCoprocessor/ZEROACC.md` (Blackhole layout: AddrMod is bits 16:14),
`if (Mode == ONE_ROW || Mode == 16_ROWS) ApplyAddrMod(AddrMod)`. The `1` was inherited from ttko
(`TTZEROACC(1, 1, 0, 1, ...)`, `blackhole-py-old/ttko/fpu.py:220`), where it follows the tt-llk convention that
ADDR_MOD_1 is a no-op. In TTRV slot 1 is user-defined, and every example defines it as a stepping modifier
(`math.addrmod step, slot=1, srca+=8, srcb+=8, dst+=8`). So each `math.zero` advances SrcA, SrcB and Dst by 8. It is
harmless today only because every current use is followed by `math.rwc reset` (`llama3_o.ttrv:251-252`,
`llama3_attention.ttrv:531` via `product!`). It contradicts spec §10 ("uses `hold` when `addr=` is omitted", "nothing is
inserted"). Fix: `addr_mode=addr(g, d.get("addr", Num(0)))`.

**B3. FP8 quantization scales are frozen into `manifest.json` as instruction words.** In
`kernels/llama3-8b-fp8/manifest.json` the launch words named `input_scale_0/1`, `output_scale_*` are literal integers
such as `1902772224 = 0x716A0000`, which `ttrv.isa.tensix_decode` reads as `SFPLOADI l6, LOWER16, 0` and
`0x71684229 = SFPLOADI l6, UPPER16, 0x4229`. The exporter computed them from the checkpoint's `*.input_scale` /
`*.weight_scale` tensors (which are in `weights/llama3-8b-fp8/model.safetensors.index.json`). Consequences: (a)
`--weights` (`llama3.py:267`, "checkpoint directory") with any other FP8 checkpoint uploads new weights but decodes with
the export checkpoint's scales, silently; (b) hand-assembled Tensix instruction words travel as launch arguments. The
TTRV kernels already take `param scales: fp32[]`; the host must upload the scale tensors.

**B4. FP8 blobs need a 14-column card, but the device accepts 12.** `ops_blackhole.py:201` allows 12 or 14 enabled
columns and puts the CQ and DMA cores at the bottom of the last column, `(14,10)` and `(14,11)` on a 12-column card.
The FP8 `o/qkv/gate/down/lm` programs use `x in 1..7,10..14`, `y in 4..11`, which includes both service cores. I
recomputed `dev.workers` for both sizes: 1B and 8B-BF16 fit on 12 columns, FP8 does not. The failure is a bare
`assert ... set(images) <= set(dev.workers)` (`ops_blackhole.py:117`) raised from `_install`, which runs after the
9.5 GB weight upload (`llama3.py:61-64`). `docs/kernels.md` claims the exporter targeted "a 12-by-10 grid minus its two
service cores", so the old and new runtimes disagree about where the service cores are. Fix now: run `_install` (cheap)
before `_upload_weights` and raise a real error. Fix properly: TTRV grids (first-N, always fit or error at install).

**B5. Host NoC transfers above 16,384 bytes are accepted and emitted as one request.** `ttrv/noc.py:120-122` skips the
length check whenever the remote is an `Index`, which is true for host buffers as well as DRAM. Reproduced:
`param out: u32[], host; l1 buf: u32[8192]; noc.write out[0], buf, n=8192, wait` builds (288-byte image) with a single
request of length 32,768. Spec §7: "A remote or host transfer is one request of 1..16384 bytes". The same statement
with `remote(...)` is correctly rejected.

**B6. `docs/examples/llama3_o.ttrv` FP8 variant is not valid TTRV.** `-D FP8=1` fails at line 191
(`error[type.assign]: v holds bf16*, got e4m3*`): `v` is assigned `cb.wait x` and later `cb.wait xq`. The header says
FP8 is "not yet compiled: needs math.mova2d", but it fails the type rule of spec §5 first. Related: the HEAD commit is
titled "Port all Llama 3 kernels to TTRV", but `argmax` fails to parse at line 88 (`sfp.if`), and `attention`, `gate`,
`lm`, `qkv` at their first `alias`. The README is accurate about this; the commit title is not. No test builds the
non-default variants (gap 5 in `ttrv_gaps.md` says so).

**B7. Compiler lets Python exceptions escape instead of `ttrv.Error`.** `sfp.li l0, 1e40` raises `OverflowError` from
`ttrv/ops.py:186` (`struct.pack("<f")`); `-D A=1.5` on an integer const raises `ValueError` from `ttrv/expand.py:166`
(caught by `__main__` and printed without a location; propagates raw from `ttrv.build`).

**B8. `chat/server.py:73` reports the wrong stop reason.** With `--chat --tokens N`, a response cut by the token limit
is reported as `stop="context"`; only EOS and context are distinguished. `Llama3.generate` knows which of the three it
was (`llama3.py:309-311` recomputes it for the CLI).

**B9. `--ttrv` binds arguments positionally with no check.** `llama3.py:125-126` relies on the TTRV `param` order
equalling the old exporter's `uniform` list (I compared: `o` is `[context, matrix, output, residual]` on both sides,
embedding matches too) and on the manifest's per-bank address equalling TTRV's packed binding (true only for
stripe-aligned buffers whose `tile` equals the TTRV page). `Kernel.bind` validates page size, alignment and integer
ranges, but `llama3.py` never calls it. Reordering a `param` line in a `.ttrv` file silently swaps buffers.

**B10. Dead or duplicated code that is wrong about itself** (not runtime bugs, but they mislead):
`HWQueue.wait` / `OP_WAIT` has no caller anywhere; `BlackholeGraph(count, patches)` and the ranged `CALL` are used only
by `test_graph.py` since `2cab0be` ("No per-position argument tables or graphs"); `sync/README.md:40` cites
`fw/hw.h:65,84`, which are now unrelated lines; `fw/__init__.py:3` imports `struct` unused; `README.md` lists `clang` and
`llvm-objcopy` but the build also needs `ld.lld` (`-fuse-ld=lld`, `fw/__init__.py:42`).

### Suspected (not provable without hardware, or latent)

**S1. `AICLK_MHZ = 1350  # set at boot and never changed` (`fw/__init__.py:30`, used at `llama3.py:67`, `kperf`).**
Every device-clock number (README table, `period_us`, kperf axes) converts ticks with a constant. The ARC firmware's
clock arbiters do change AICLK (TDP, TDC, thermal, board power, GDDR thermal: `smi.py:38-39,118-119,170` exists
precisely to show "aiclk capped at N MHz by ..."). A throttled run reports optimistic tok/s with no warning. Fix: read
telemetry tag 14 after boot and after a run; use it, and warn if it moved.

**S2. One timeline shared by two queues, with non-monotonic `STORE` and `>=` waits (`ops_blackhole.py:223-227`).** The
invariant "every submitter waits for its work" holds on the normal paths (I walked `generate`, `_copyin`, bench, chat).
It breaks after any `TimeoutError`: `Llama3.in_flight` stays set, the next request's `_copyin` (DMA queue, still alive)
stores a larger timeline value, and `_retire` (`llama3.py:190`) is then satisfied by the DMA signal although the compute
run never retired; args are rebound and another CALL is pushed at a hung dispatcher. The chat server keeps the model
loaded after a timeout (`chat/server.py:117`), so every later request burns 10 s and fails. Conversely, if compute and
DMA work are ever in flight together, a late `STORE N` after `STORE N+1` moves the signal backwards and the waiter for
`N+1` hangs. Fix: per-queue signals, or mark the device dead on timeout and force a reload.

**S3. No hang diagnostics and no health check.** `fw/dispatch.c:53` spins forever on `DONE_COUNT`; the host reports
"signal is v, waiting for value" with no program, core or RISC. `docs/ttrv_pack_unpack.md` records that "`Device.boot()`'s
soft reset does not clear a wedged Tensix" and that the cure is `smi.py -r`; nothing in `BlackholeDevice._boot` detects
that state, so the next open can boot onto a wedged core. Cheap improvement: on timeout, read `GO_SIGNAL` and the four
`SUBORDINATE_SYNC` bytes of every worker in the launch through the TLB and print which RISCs never returned; have the
`init` program push one Tensix instruction and drain, with a short timeout that says "run ./smi.py -r".

**S4. DRAM offset 0 is used twice.** `BlackholeDevice.__init__` uploads the `init` program at allocator offset 0
(`ops_blackhole.py:216`); `Llama3.__init__` then moves `dram_top` above the manifest layout (`llama3.py:59`) and writes
manifest buffers at fixed addresses below it. It is safe only because the old layout starts at per-bank 4096 (the
`init` payload sits in the unused first 32 KiB) and `init` never runs again. Any new fixed buffer at offset 0 corrupts
nothing visibly but breaks the allocator's "allocations live until close" contract.

**S5. `kperf` timestamper ring vs TTRV `keep` storage.** `kperf/stamps.py:22` places the ring at
`[0x100000, 0x180000)` in every worker's L1 ("measured: no Llama kernel writes worker L1 above 0xC0000"). TTRV `keep`
storage grows down from `0x180000` (`ops_blackhole.py:212`, `ttrv/layout.py:53-54`). As soon as argmax or attention
(both use `keep`) are TTRV kernels, a profiled run overwrites their persistent counters, or vice versa.

**S6. Cache writes are not process-safe.** `llama3.py:28-29` writes the tokenizer pickle in place and `fw/__init__.py:68`
uses a fixed `{out}.tmp` name. Two processes starting together (two cards, or bench + chat) can read a torn pickle or
interleave the temp file. Use a unique temp name plus `os.replace` in both. The firmware cache key
(`fw/__init__.py:60`) also omits the clang version.

**S7. Weight upload error handling.** `llama3.py:79` raises a bare `StopIteration` when a checkpoint directory has no
safetensors file. `llama3.py:85` checks only `nbytes <= size`, never dtype: an fp16 checkpoint in a BF16 manifest uploads
and decodes garbage.

**S8. `assert noc >> 32 == 0x10000000` (`llama3.py:158`).** Argmax has the PCIe mid address compiled in, so the runtime
assumes the IOVA of the pinned buffer is below 4 GiB. That is tt-kmd/IOMMU allocator behaviour, not a contract. It
disappears with the TTRV `param tokens: u32[], host` (two words).

**S9. Abnormal exit leaves the firmware running against unpinned memory.** tt-kmd has `SET_NOC_CLEANUP` (ioctl 14) for
exactly this ("in case the host-side application terminates abnormally"); `system.py` does not register it. After a
SIGKILL the dispatcher can issue PCIe reads to an IOVA the driver has unmapped. The IOMMU contains it, and the next
`_boot` resets the tiles, but whether a NoC read that never gets a response leaves the NIU stuck across a soft reset is
unknown to me.

**S10. Expression temporaries are never recycled inside a statement** (`ttrv/codegen.py:54-62,86-94`). A 39-term
expression fails with `register.full`. By design per spec §5, but freeing an operand temporary as soon as `calc`/`imm`
consume it is a three-line change and removes a class of "split your expression" errors in address arithmetic like
`llama3_attention.ttrv:402`.

### Checked and found correct (so nobody re-audits them)

- Every ioctl struct in `system.py` and `smi.py` against `tt-kmd/ioctl.h`: PIN_PAGES (flags=NOC_DMA, extended out),
  UNPIN, LOCK_CTL (index 20), ALLOCATE_TLB (UC offset), CONFIGURE_TLB (`IIQ4HBBB21x`), SET_POWER_STATE (validity is a
  count), RESET_DEVICE, NOC_READ.
- `cover()` (`ops_blackhole.py:15-30`): brute-forced all grids 1..118 and 1..138 against a model of the exclusion
  word; every first-N set is covered exactly. All per-variant and per-mask groups of the exported programs also cover.
- Dispatcher memory map on the CQ and DMA cores (`fw/abi.h:91-105`): no overlaps. TIDs 1-6 in `fw/*.c` do not collide.
- Ring full/empty arithmetic (`ops_blackhole.py:101`), `queue_fetch`, the two-engine DMA handshake (`fw/dma.c:38-40`),
  the `installed`-pointer prefetch logic (`fw/dispatch.c:31-55`: the lookahead never crosses a chunk, so it cannot go
  stale), the 35-bit irregular-page division (`fw/noc.c:64-71`), `fw.jal`/`fw.ret` encodings.
- TTRV call lowering: callee registers are disjoint from every live caller register (I traced a three-level call in the
  listing); branch relaxation; CB counter wrap; DRAM bank/port tables in `ttrv/noc.py:171` match `fw/noc.c:4`.
- TTRV's unpack credit sequence already has the `t0semfix` ordering from `sync/README.md` (`STALLWAIT` blocks SYNC
  before `SEMGET`, `ttrv/movement.py:253-254`).

---

## Delete / merge / move list

Sizes are tracked bytes.

### Delete now (no dependency on the migration)

| Path | Size | Why |
| --- | ---: | --- |
| `play/` (13 files) | 54 KB | Superseded by `kperf/` file for file: `kprof.py` -> `kperf/stamps.py`, `kprof_sample.py` + `kbench.py` -> `kperf/collect.py` + `symbols.py`, `observer.py` + two `.c` -> `kperf/` (kperf has the newer read-window record format). `kbench`, `kprof`, `kprof_sample`, `kprof_dump` are broken (B1). If any probe is worth keeping (`ts_probe.py`, `l1_highwater.py`, `dram_niu_probe.py`), move it to `tests/hw/probes/`. |
| `ttrv/isa.py:586-2147` | ~100 KB | 137 unused wrapper functions. Keep `RV`, `rv`, `rv_decode`, `TENSIX`, `tensix`, `tensix_decode`, `inline`, `outline`, the enums. |
| `ttrv/isa.py` RVV/F/Zb section (~62-360) | ~25 KB | "None of these are used yet." Recover from git when a kernel needs them. |
| `kernels/**/*.S` (114 files) | 5.2 MB | Nothing in the runtime, kview or kperf reads them (`kview/serve.py`: "nothing is read from the .S listings"). Only `sync/census.py` and `sync/ablate.py` do. |
| `sync/` code, `census.json`, `results/*.json` (31 files) | 120 KB | A finished experiment on blobs that are going away. Keep the findings: move `sync/README.md` to `docs/notes/sync.md` (fix its stale `fw/hw.h:65,84` reference). `ablate.py` patches `.bin` words in place and monkeypatches `llama3.KERNELS`; in TTRV an ablation is a `-D` flag. |
| `docs/ttrv_cfg.md` | 50 KB | Generated table (820 fields from `cfg_defines.h`); the same data is `kview/data/registers_full.json`. Generate on demand or link to the JSON. |
| `OP_WAIT`, `HWQueue.wait`, `BlackholeGraph(count, patches)`, `call()` count/stride loop, `test_graph.py` | small | Unused since arguments are bound per run. Keep `CALL` of one buffer. Removes ~25 lines of firmware and the only reason `BlackholeGraph` uses numpy. |
| `kernels/*/rope_{cos,sin}.bf16` (6 files) | 10.5 MB | `cos`/`sin` of `pos * theta_i` in BF16: ten lines of numpy at startup. Largest single chunk of the repo. |
| `.git/objects/pack/tmp_pack_AjWLyl` | - | `git count-objects` reports it as garbage; `git gc --prune=now`. |

### Delete as each kernel moves to TTRV

| Path | Replaced by |
| --- | --- |
| `kernels/zero/` (`export.py` + 8 bins) | `kernels/zero.ttrv` (see migration step 1) |
| `kernels/llama3-*/<kernel>/*.bin` | `ttrv.build` at startup: I measured 10-20 ms per kernel, so no prebuilt images and no cache are needed |
| `kernels/llama3-*/manifest.json` (675 KB) | the Python model plan |
| `kernels/llama3-*/reference.json` | regenerate from the new runtime, or a CPU reference; today it compares against "blackhole-py examples/llama3 ... 2026-11-08", i.e. the old repo |
| `kview/` (450 KB: 1,105-line `decode.py`, 400 KB of JSON, web UI) | TTRV's source-mapped `.lst`. kview reconstructs meaning from blobs by constant propagation; a TTRV listing has the source line and macro chain for every word. Keep `data/registers_full.json` (cfg field names) and `data/isa.json` as the single ISA table (see consolidation). Retarget `kperf/symbols.py` at the listing's `loc`. |
| `docs/kernels.md` | Describes the exported kernels and how to re-export from the old repo. Archive with `sync/README.md` under `docs/notes/`. |
| `docs/ttrv_port_review.md` | Its own header says the assessment "predates the backend". Fold the Validation section into the spec; drop the rest. |
| `blackhole_build_program`, per-core `params`/`variants`/`persistent` handling in `llama3.py:127-145`, `Llama3.buffer` | grid install + `keep` |

### Move

- `docs/examples/llama3_*.ttrv` -> `kernels/llama3/*.ttrv`. They are loaded by production code (`llama3.py:118`) and
  by both test files; they are not documentation.
- `test_ttrv_hardware.py`, `test_graph.py` -> `tests/hw/`; `test_ttrv.py` -> `tests/`. Today a hardware regression and a
  pure unit test sit side by side with the same prefix.
- `smi.py` -> a subcommand sharing `kmd.py` (it duplicates `ioctl`, the fd open flags, the power vote and the telemetry
  walk of `system.py` / `ops_blackhole.py:244-250`).
- `chat/`, `kperf/` -> `tools/`.
- The load-bearing hardware probes from `blackhole-py-old/tests/probes/` (the spec cites three of them as evidence, see
  below) -> `tests/hw/probes/`, rewritten as TTRV sources.

### Not checked in, but worth knowing

`play/*.npz`, `play/*.json`, `play/*.folded` (99 MB) and `kperf/bundles/` (30 MB) are untracked and ignored by
`.gitignore`, so they are local clutter rather than repo weight. `sync/variants/` (written by `ablate.py`) is not
ignored.

---

## Leaving blackhole-py-old

### Dependency inventory

Direct import (one file):

- `kernels/zero/export.py:8-12` inserts `../blackhole-py-old` into `sys.path` and imports `asm.Asm`, `ttko.isa.R`,
  `ttko.noc.NoC`, `pcie.P150_DRAM_ENDPOINTS`.

Artifacts produced by `blackhole-py-old/tools/rewrite_export/export_llama3.py --rewrite ../blackhole-py`:

- 114 `.bin` images + 8 zero images, 114 `.S` listings, 3 `manifest.json`, 3 `reference.json`, 6 RoPE tables.
- `manifest.json` is not just a file list. It is the whole model: DRAM layout (`uploads`, `buffers`, `dram_top`,
  `history`), the launch graph (`launches`: 83 / 163 entries of positional argument words), per-core tables
  (`programs[*].per_core[*].params`, written to `static_base + 0x40 * k` on each core by `llama3.py:135`), per-core image
  variants (`down` has `brisc.v0/v1`), persistent L1 regions, FP8 scales as instruction words (B3), `eos`, `kv_block`,
  `max_tokens`. `llama3.py` is an interpreter for this schema.

ABI frozen by the blobs:

- `fw/abi.h:12-13`: "[0x20, L1_PARAM_BASE) is nearly full. Growing it means moving L1_PARAM_BASE and DATA_BASE, which
  the exported kernels have compiled in". `llama3.py:108` asserts `static_base == DATA_BASE` and
  `l1_param_base == L1_PARAM_BASE`.
- `fw/hw.h:99`: `SEMINIT_ALL` exists because "kernels spin on UNPACK_SYNC (5) < 2 at entry"; `reset_thread` zeroes 64
  Tensix GPRs because "kernels assume zeroed Tensix GPRs".
- `llama3.py:140` appends `fw.ret(role)` to each blob; `llama3.py:158` asserts the PCIe mid address argmax compiled in.
- Core placement: blobs use row-major 11x8 (BF16) or 12x8 at `y >= 4` (FP8) grids and a 64-core attention block; TTRV
  uses first-N column-major. Both coexist only because arguments are uniform.

Tooling that only understands blobs:

- `kview/` (decodes `.bin` with the manifest), `kperf/symbols.py` (through kview), `kperf/stamps.py:40-52`
  (monkeypatches `Path.read_bytes` to wrap `.bin` files as `Llama3._install` reads them), `kperf/collect.py:40,86`
  (`per_core`, `variants`), `sync/` (`.S` and `.bin` patching), `play/`.

Borrowed text (no import, provenance only):

- `ttrv/isa.py:386-427` enums "from blackhole-py-old ttko"; `kview/data/isa.json` "merges the Tensix encoders of
  blackhole-py's ttko/isa.py" (`kview/data/NOTICE`); `math.zero`'s encoding (B2) is a ttko recipe.

Documentation that points into the old tree:

- `docs/ttrv_spec.md:672` (`probe_cfg_shared_word.py`, the evidence for masked config writes being safe across
  TRISCs), `:718` (`probe_srcb_release.py`, the release rule), `:816` (`ttko/fpu.py` matmul as "reference recipe").
- `docs/ttrv_pack_unpack.md:8,261,319` (four probes, ~1,400 cases).
- `docs/ttrv_port_review.md:17-20`, `docs/kernels.md:113-135`, header comments of six example kernels, `sync/README.md`.

The spec's hardware claims rest on probes that live only in the repo being removed. Port them or lose the evidence.

### Migration plan

Ordering principle: build the thing that makes each later step verifiable first, and never delete a blob before its
TTRV replacement has been compared against it on hardware.

**Step 0. A/B harness (do this before anything is deleted).** Every exported kernel and its TTRV port read and write
DRAM buffers. `tests/hw/ab.py --model M --kernel K`: run the blob on real activations (after a short generate), copy its
output buffers out (`_copyout`), run the TTRV kernel on the same inputs, compare bit-exact or within a stated ULP bound.
Also record per-kernel input/output snapshots to `.npz` outside git, so comparisons remain possible after the blobs are
gone. This harness cannot be written later.

**Step 1. Zero and RoPE (hours; removes the only direct import).**
```text
grid 8
param cache: u32[], page=4            // 16 KiB pages
param pages: u32 in 0..1048576
l1 zeros: u32[4096]
fn brisc() {
    first, count = split(pages)
    for i in 0..4096 { zeros[i] = 0 }
    for p in first..first + count { noc.write cache[p * 4096], zeros, n=4096, wait }
}
```
Uses only what the backend has today. Open question below: whether the caches need zeroing at all. Generate RoPE
tables in numpy. Delete `kernels/zero/`, `rope_*.bf16`, `*.S`.

**Step 2. The model plan (the real exit from the exporter).** `llama3/plan.py`: from `config.json` and the dtype,
produce named buffers (allocated by `BlackholeAllocator`, no fixed addresses, no `dram_top` hack), the upload list, and
`launches = [(kernel, {param: buffer | Var})]`. Bind with `kernel.bind(mem, base, {...})` by name. Start by using it for
the three kernels that are already TTRV while the other five still come from the manifest; the plan can read the
manifest's buffer addresses for shared buffers during the transition. FP8 scales become `fp32[]` buffers uploaded from
the checkpoint's `input_scale`/`weight_scale` tensors (fixes B3).

**Step 3. Compiler features, in the order the kernels need them.** From a scan of the examples (`NO` = no backend):

| Feature | Needed by | Size |
| --- | --- | --- |
| Table-driven SFPU ops: `shr sar shl isub iadd and or xor not abs addi muli recip cast exexp exman setexp setsgn shift rnd minmax swap`, flags `neg neg_ab neg_c hidden= from= int|float` | all five | one table + one generic lowering; 18 of the 21 missing ops |
| `alias` | lm, qkv, gate, attention (40 uses) | parser statement + scope entry |
| float constants, `sqrt` | qkv, gate, attention | `expand.fold` |
| `dst.tile`, `dst.face` | lm, qkv, gate, attention, argmax | two constants |
| `math.mova2d` | all five | one op |
| `sfp.if` | argmax, gate, attention, FP8 paths | SFPENCC / SFPPUSHC / compare / SFPCOMPC / SFPPOPC |
| `sfp.index` | argmax | SFPCONFIG OR/AND |

**Step 4. Kernels, smallest dependency set first.**

1. `lm` + `argmax` together. They must switch as a pair: the TTRV `lm` writes dense row-major logits and the TTRV
   `argmax` reads them with `split(VOCAB)`; the exported pair uses per-core compact tiles. `lm` needs only the first
   five rows of the table. `argmax` additionally needs `sfp.if`, `sfp.index`, the integer pack rule (gap 16) and
   `keep`. Once argmax is TTRV, `llama3.py:158` and the `argmax_host_address` argument go.
2. `qkv` BF16. Same feature set as `lm`.
3. `gate` BF16. Adds the exp/reciprocal instruction rows.
4. `attention`. Blocked on two hardware audits the spec lists as open, not on the compiler: partial DRAM writes with
   mismatched offsets (§12 item 4, the KV append at `llama3_attention.ttrv:408`) and FP32 into Dst (§12 item 6). Do the
   two probes first.
5. FP8 variants of o/down, qkv, gate, lm. Fix B6 first. Need `sfp.if`, `abs`, `minmax`, E4M3 pack, grid 96.

After each kernel: A/B pass on all three models, switch the default, delete that kernel's blobs, re-run `bench.py`
(placement changes from row-major to column-major, so DRAM-port contention can move the numbers).

**Step 5. Unfreeze and clean.** Delete `manifest.json`, `reference.json`, `blackhole_build_program`, the per-core table
writer, `--ttrv`. Then the ABI is free: grow the BRISC firmware slot, fold `fw/init.c` into BRISC boot (removes the
`init` program and S4), drop `SEMINIT`/GPR-zeroing if TTRV does not need them, drop `SFPLOADI_MINUS1` if the spec stops
promising `neg_one`. Retarget `kperf` to TTRV listings and move its ring out of the `keep` range (S5); delete `kview`.
Port the probes. Remove every `blackhole-py-old` path from docs.

---

## Runtime / flags / firmware consolidation

### What is duplicated today

| Concern | Copies |
| --- | --- |
| Launch-and-wait boilerplate | 12 sites: `ops_blackhole.py:217`, `llama3.py:101`, `test_ttrv_hardware.py:50,95,125,144,175,217`, `test_graph.py:30`, `kperf/collect.py:66`, `play/` x2 |
| Program install | `blackhole_build_program` (per-core dict), `blackhole_build_grid_program` (first N), `_install_program`, `Kernel.install` (in the compiler package, imports the runtime lazily), plus the direct-start path written three times: `BlackholeDevice._create_queue`, `kperf/observer.py:Observer.__init__`, `DebugObserver.__init__` |
| Program handle | `BlackholeProgramData(addr, args_size)` and `InstalledKernel(addr, args_size, manifest)`; `exec` duck-types |
| Device open / ioctl | `system.PCIIface` and `smi.Card` (same open flags, same `ioctl` helper, same power-vote struct), telemetry table walk in `ops_blackhole.py:244-250` and `smi.py:64-72` |
| ABI | `fw/abi.h`; hand mirror + asserts in `fw/__init__.py:10-32`; `ttrv/hw.py:9` (`CORE = {"x": 0x770, ...}`); parsed copy in `kview/decode.py:460` |
| DRAM endpoints (p150) | `fw/noc.c:4`, `ttrv/noc.py:171`, `kview/decode.py:59`, `kperf/observer.py:12`, `blackhole-py-old/pcie.py` |
| NIU registers and command-buffer fields | `fw/noc.c:9-24`, `ttrv/noc.py` (bare offsets 0, 4, 8, 12, 20, 24, 28, 32, 64, 0x148, 0x240, 0x280 and control words 0x8080, 0x2080, 0x107C), `kperf/observer_dram.c`, `kperf/observer_dbg.c` |
| DRAM address tag | encoded in `ops_blackhole.dram`, decoded in `ttrv/__init__.py:76-82` and `fw/noc.c:56-71` |
| L1 size `0x180000` | `ops_blackhole.py:212`, `ttrv/__init__.py:30,97`, `ttrv/layout.py:23`, `kview/decode.py:21` |
| Tensix instruction words | literals in `fw/hw.h:69-75,104-109`, table in `ttrv/isa.py`, `kview/data/isa.json` |
| Config word indices | bare numbers in `ttrv/movement.py` (`sec + 9`, word 70, 71, 68, 12, 13, 28, 24, 37...), names in `kview/data/registers_full.json` and `docs/ttrv_cfg.md` |
| Stall-bit names | `kperf/observer.py:82` (dict) and `kperf/symbols.py:15` (list, different members) in the same package |
| 4K-context benchmark setup (random KV fill) | `bench.py:34-37`, `kperf/collect.py:41-46`, `play/kbench.py` |
| Default prompt string | `llama3.py:265`, `bench.py:26`, `kperf/collect.py:48` |
| HTTP server boilerplate | `chat/server.py`, `kview/serve.py`, `kperf/serve.py` |
| Hand-encoded RISC-V | `fw.ret`, `fw.jal` (`fw/__init__.py:86-92`), `kperf/stamps.py:30-32` (`lui/addi/sw/nop`), all of which `ttrv.isa.rv` already does |

### Flags as they are

| | `llama3.py` | `bench.py` | `test_ttrv_hardware.py` | `kperf.collect` | `smi.py` | `sync/ablate.py` | `play/*` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| device | `--device N` | `--device N` | `--device N` | `--device N` | `-d N` repeatable, default all | `--device N` | hard-coded 0 |
| model | `--model`, default `1b` | positional list, default all, own hard-coded tuple | `--tiles 2 4` | `--model` | - | `--model` | `argv[1]` or hard-coded |
| amount | `--tokens` | constant 64 | - | `--launches` | `-c` | - | `--tokens` |
| kernel source | `--ttrv` | none (always blobs) | always TTRV | always blobs | - | patched blobs | blobs |
| weights | `--weights` | none | - | none | - | none | none |
| serve | `--chat --host 0.0.0.0 --port 8000` | - | - | `serve.py --port 8140 --kview-port 8137` | - | - | - |

Inside the code the device is an `int` (`Llama3`, `PCIIface`), a tinygrad-style string `"BLACKHOLE:1"` parsed with
`split(":")` (`ops_blackhole.py:198`), and a sysfs index (`smi.py`). Timeouts are bare literals: 10.0 in five
signatures, 60.0 in four call sites.

### Target layout

```text
bh/
  kmd.py        ioctl table (named, one struct format each), Card: open/lock/power/tlb/pin/noc_read/telemetry
  hw.py         the only place with coordinates, NIU offsets, L1_SIZE, AICLK; abi = parse("fw/abi.h");
                TENSIX and CFG field tables loaded from data/*.json
  fw/           C sources; build.py (compile, cache); gen: tensix word #defines for hw.h from hw.TENSIX
  device.py     Device (ops_blackhole.py): boot, rings, allocators, load, run, graph
  ttrv/         parse, expand, layout, codegen, ops, noc, movement; no import of device.py; Kernel is pure data
  llama3/       plan.py (buffers + launches), model.py (Llama3.generate), tokenizer.py
  cli.py        python -m bh {run, chat, bench, smi, build, kperf, test}; one parent parser: --device --model --weights
kernels/        zero.ttrv, llama3/*.ttrv, lib.ttrv
tools/          kperf/, chat/
tests/          test_ttrv.py; hw/ (runtime, ttrv, ab, probes/)
```

### Public API sketch

```python
with Device(1) as dev:                       # int; closes, resets and unpins on exit
    w   = dev.dram(nbytes, page=2048)        # Buffer(addr, nbytes, page); .write(data) / .read(out)
    tok = dev.host(16 * n)                   # HostBuffer(addr, view): pinned, device-visible
    k   = ttrv.build(src, defines)           # pure: images, manifest, listing
    p   = dev.load(k)                        # Program(addr, args_size, manifest); also accepts {core: {role: bytes}}
    dev.run(p, {"matrix": w, "token_pos": 7})  # bind by name, exec, signal, wait
    g   = dev.graph([(p, bindings), ...], profile=False)   # recorded once; args in one pinned block
    g.bind(token_pos=pos); t = g.submit(); dev.wait(t)     # tinygrad-style rebinding
```

Concretely this means: `_alloc`/`_copyin`/`_copyout` become public `Buffer` methods (they are already the public API of
every test and tool); `dev.run` replaces the 12 boilerplate sites; `dev.load` replaces the three install functions and
`Kernel.install`; `dev.start(core, images)` replaces the three direct-start copies; `Graph.bind` replaces
`Llama3.dyn`/`self.args[cols] = val[name]`; `Llama3.fake_context(n)` replaces the three copies of the random-KV setup.

### Firmware build/load

- `fw/__init__.py`: replace lines 10-32 with `ABI = parse_abi(HERE / "abi.h")` (the function exists at
  `kview/decode.py:460`), and have `ttrv/hw.py` read `WORKER_X/Y/ID` from it.
- Generate the Tensix word constants of `fw/hw.h:69-75,104-109` from the ISA table at build time
  (`-DZEROACC_ALL=...` or a generated header), so the firmware and the compiler cannot disagree about an encoding.
- `fw/dispatch.c` reads the program descriptor as `d[0]..d[7]` and `t[0]..t[4]`. A `struct descriptor` in `abi.h`,
  packed by the same field list in Python, removes the index arithmetic on both sides.
- `compile()` shadows the builtin; `program()` builds a position-independent C kernel; `images()` builds everything.
  Suggest `build_image`, `build_kernel`, `firmware()`. Add the clang version to the cache key.
- After the migration, fold `init.c` into `worker_brisc.c:firmware_boot` (it only needs slot space that the frozen ABI
  currently denies).

---

## Code quality simplifications

1. **`ttrv/ops.py` is three if/elif chains that should be tables.** `sfp()` (lines 137-205), `math()` (223-330) and
   `lower()` (460-544) each open-code operand binding per mnemonic. A row such as
   `"mad": ("SFPMAD", "rd a b c", lambda r: (r.a, r.b, r.c, r.rd))` plus one generic function covers the eleven existing
   SFPU ops and the eighteen missing ones, and the spec's §10 table can be generated from it instead of maintained by
   hand.
2. **Positional Tensix fields.** `g.tt("UNPACR", i, 0x11 if bfp else 0, 0, ctx, 0, 1, int(...), 0, 0, 0, 0, 0, 1)`
   (`movement.py:252`), `g.tt("ZEROACC", 1, f, 0, 1, face)` (the source of B2), `g.tt("SFPMUL", a, b, 9, rd)`,
   `g.tt("UNPACR_NOP", i, 0, 0, 1, 0, 0, 0, 0, 1)`. Named fields only; B2 would have been visible in review.
3. **Config writes by number.** `movement.py` writes words `sec + 9`, 70, 71, 68, 12, 13, 28, 24, 56 + 2i, and
   ThreadConfig 37-39, 41, 5 as literals with shift/width triples. `kview/data/registers_full.json` has every name.
   `cfg(g, "THCON_SEC0_REG1_...", value)` with a lookup makes the 30 tuples self-describing and lets the "one writing
   RISC per field" rule of spec §8 be checked mechanically.
4. **`ttrv/noc.py:noc()` is one 280-line function** with five closures handling read/write/inc/mcast x DRAM/host/remote
   through flags (`atomic`, `multicast`, `write`, `dram`, `host`). Split into `endpoint(remote) -> (coord, addr, mid,
   pager)` and `request(kind, endpoint, local, length)`; the three endpoint kinds stop sharing mutable locals.
5. **Three functions that should be one**: `blackhole_build_program`, `blackhole_build_grid_program`,
   `_install_program`. The first two differ only in how `groups` is built; after the migration only the grid form
   remains, and it is `{(addr, image): workers}` in three lines.
6. **`Emitter.items` holds ints, tuples and `None`, with events in a side dict keyed by index**, and
   `resolve_registers` (`codegen.py:548-550`) renames registers by decoding each already-encoded word with `rv_decode`
   and re-encoding it. Emit `(op, rd, rs1, rs2, imm)` tuples and encode once in `finish()`; the rename becomes a dict
   lookup and no longer depends on "an inline Tensix word never has both low bits set".
7. **Non-entry functions are unused.** None of the seven Llama kernels defines a `fn` other than an entry (macros do
   all the factoring). The call machinery is `values()` lines 304-323, `call_sites`, `moves`, `resolve_registers`, and the
   cross-call part of `state.verify`, roughly 120 lines plus a page of spec. Decide whether calls stay in v1.
8. **`llama3.py`**: `self.args = np.zeros(...)` only to read `.nbytes` before being rebound (160-164); the expression
   `self.ts[1:2 * self.nts:2].astype(np.int64)` three times (192, 257, `play/`); `main()` is 80 lines of which 50 are
   report formatting; `dispatch_baseline` hides a lazily built graph behind `hasattr`. `Llama3.__init__` uploads weights
   before validating programs (B4).
9. **Names that mislead.** `blackhole_build_program` installs (uploads and writes a descriptor), it does not build.
   `HWQueue.q()` appends to `_q`. `BlackholeQueueDesc` is a ring writer with a doorbell. `Sysmem` is rings + signals +
   heap + staging. `_alloc`/`_copyin`/`_copyout` are underscore-private and called from six other files.
   `Llama3.host` is the token-slot offset, `Llama3.m` the manifest, `Llama3.dyn` the integer-argument columns.
   `helpers.safe_load` returns tensor locations, loads nothing. `fw.FW` (slot table) inside module `fw`.
   `Generator.tt` emits one inline Tensix word. `ttrv.state.verify`. `test_graph.py` needs a card. Every class in a
   Blackhole-only repo is prefixed `Blackhole`.
10. **Two formatting styles in one package.** `parse.py`/`expand.py` are dense two-space code with 150-column lines;
    `codegen.py`/`ops.py`/`noc.py`/`movement.py`/`__init__.py` are black-formatted, with function-local imports
    (`from .ops import lower`, `from .noc import init_buffers`, `from .state import verify`) to dodge import cycles
    between `codegen`, `ops`, `noc`, `sfpmacro`. Pick one style; break the cycle by passing the generator in.
11. **`BlackholeSignal.wait` and `push` spin in Python** with no pause. Fine for latency during decode, but
    `_copyin` of gigabytes also spins a core at 100%. A `time.sleep(0)` after N empty polls costs nothing measurable.
12. **`kperf/stamps.py:40-52` monkeypatches `Path.read_bytes` process-wide** to intercept blob reads. With `dev.load`
    taking images, profiling is `load(wrap(images))`.

---

## TTRV language ideas

Numbers below come from a scan of the seven sources in `docs/examples/` (2,462 lines).

### 1. `use "file"`: a shared prelude

Spec §3: "There are no includes." The result is that four kernels carry the same definitions:

| Definition | Defined in |
| --- | --- |
| `macro pack_dst`, `macro unpack_pair`, `replay accumulate` | gate, lm, o, qkv |
| `mop dot_face`, `replay square` | gate, lm, qkv |
| `macro reduce_l0` / `reduce_lanes` (same 13 lines, two names) | lm, qkv / gate, o |
| `macro rms_scale` (26 lines), `sfpmacro scale_x`, `replay apply_pair`, `macro over_tile` | lm, qkv |
| `macro stream_rows`, `macro copy_tile` | gate, qkv / attention, gate |
| the E4M3 round/clamp/flush sequence (18 instructions) | o (replay), qkv (macro), gate (macro) |

Before (`llama3_qkv.ttrv`, repeated verbatim in three other files):
```text
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
```
After:
```text
use "lib.ttrv"        // consts, types, macros and templates only
```
Rule: a used file may contain `const`, `type`, `macro`, `mop`, `replay`, `sfpmacro` and nothing that allocates (no
`grid`, `param`, `l1`, `cb`, `sem`, `fn`, `shared`). Templates cost hardware only when loaded, so unused ones are free.
Same single namespace, no textual substitution. Estimated effect: o 319 -> ~250, qkv 429 -> ~290, gate 505 -> ~380,
lm 287 -> ~190 lines, and a fix to `rsqrt` lands once.

### 2. `fmt=` on `sfp.load`/`sfp.store` should default to the configured format

`math.fmt dst=fp32, sfp=fp32` exists to set "the default SFPU transfer format" (§10), and the backend already encodes
an omitted `fmt` as mode 0, "configured". Yet 94 of the 96 `sfp.load`/`sfp.store` lines in the examples write
`fmt=fp32` (attention 53, gate 18, qkv 11, lm 7, o 4, argmax 1).

Before (`llama3_attention.ttrv`, `online_softmax`):
```text
sfp.load l0, dst[S], fmt=fp32; sfp.mul l0, l0, scale; sfp.nop; sfp.store dst[S], l0, fmt=fp32
sfp.load l1, dst[S + ODD], fmt=fp32; sfp.mul l1, l1, scale; sfp.nop; sfp.store dst[S + ODD], l1, fmt=fp32
```
After:
```text
sfp.load l0, dst[S]; sfp.mul l0, l0, scale; sfp.nop; sfp.store dst[S], l0
sfp.load l1, dst[S + ODD]; sfp.mul l1, l1, scale; sfp.nop; sfp.store dst[S + ODD], l1
```
This needs one probe: that mode 0 with `SFPU_DEST_FMT` set behaves identically to explicit FP32. If it does not, then
`sfp=` on `math.fmt` is the feature to delete, because nobody trusts it.

### 3. Role-default units for the four handoff idioms

The unit sets are a function of which TRISC issues the statement, and the kernels never vary them:

| Statement | Count |
| --- | ---: |
| `sem.stall math\|sfpu\|sync, S, notmax` | 17 |
| `tensix.stall sync, math\|sfpu` | 34 |
| `sem.stall tdma\|pack\|sync, S, nonzero` | 12 |
| `tensix.stall sync, pack0` followed by `tensix.wait` | 12 of 12 |

That is 75 of the 102 stall statements. Before (`llama3_o.ttrv`):
```text
// trisc1
sem.stall math|sfpu|sync, dst_full, notmax
...
tensix.stall sync, math|sfpu
sem.inc dst_full
// trisc2
sem.stall tdma|pack|sync, dst_full, nonzero
p = cb.reserve q
pack.move p, dst[0]
tensix.stall sync, pack0
tensix.wait
cb.push q
sem.dec dst_full
```
After:
```text
// trisc1
sem.acquire dst_full        // = sem.stall <this thread's units>, dst_full, notmax
...
sem.give dst_full           // = tensix.stall sync, <this thread's engines>; sem.inc dst_full
// trisc2
sem.take dst_full           // = sem.stall <this thread's units>, dst_full, nonzero
p = cb.reserve q
pack.move p, dst[0]
pack.wait                   // = tensix.stall sync, pack0; tensix.wait
cb.push q
sem.done dst_full           // = sem.dec dst_full
```
Each is a fixed expansion shown in the listing, so the "nothing is hidden" rule holds. The explicit forms stay for the
27 statements that are not one of these.

### 4. Block arguments for macros (gap 30, already identified)

`over_tile!(replay, n)` only works when the body is a replay; `qkv` needs a second copy, `round_fp8_tile`, for an
inline body, and `lm`, `gate` and `o` open-code the same walk.

Before (`llama3_qkv.ttrv`):
```text
macro over_tile(body, n) {
    math.rwc reset
    repeat 4 {
        repeat n { replay.run body }
        math.rwc dst=cr+8
        math.rwc dst=cr+8
    }
    math.rwc dst=0
}
macro round_fp8_tile() {
    math.rwc reset
    repeat 4 {
        loop 8 { round_fp8_step!() }
        math.rwc dst=cr+8
        math.rwc dst=cr+8
    }
    math.rwc dst=0
}
```
After:
```text
macro over_tile(n, body) {
    math.rwc reset
    repeat 4 { repeat n { body }; math.rwc dst=cr+16 }
    math.rwc dst=0
}
over_tile!(8) { replay.run square }
over_tile!(8) { round_fp8_step!() }
```
Two things in one: a trailing `{ }` binds to the macro's last parameter, and `math.rwc dst=cr+16` is allowed to lower
to two `SETRWC` (`math.rwc dst=cr+8` appears on 16 lines, always doubled, because the field is four bits wide).

### 5. Constant lists for `repeat`

Gap 6. The four SFPU addresses that cover tile rows 0-3 are recomputed inline 29 times in attention.

Before:
```text
repeat i in 0..4 { sfp.store dst[M + (i & 1) * ODD + (i >> 1) * RIGHT], m_new, fmt=fp32 }
repeat i in 0..4 { sfp.store dst[ALPHA + (i & 1) * ODD + (i >> 1) * RIGHT], delta, fmt=fp32 }
```
After (with idea 2):
```text
const QROWS = [0, 2, 16, 18]
repeat a in QROWS { sfp.store dst[M + a], m_new }
repeat a in QROWS { sfp.store dst[ALPHA + a], delta }
```
The same mechanism takes register lists (`repeat r in [l0, l1, l2, l3]`), which removes the four hand-unrolled
load/scale/store lines at the top of `online_softmax`.

### 6. `split` with alignment

Every projection and argmax starts with the same three lines:
```text
first, count = split(DIM)
lo = first & ~31
lead = first & 31
```
`first, count, lead = split(DIM, align=32)` (with `lo = first - lead` where needed). Five kernels, and it puts the
"same offset modulo 64 bytes" trick, currently explained in a comment in each file, in one documented place.

### 7. An SFPU expression form that stays one-to-one

The SFPU blocks are three-address code. A statement form where each assignment must match exactly one native
instruction keeps the "one statement, one instruction" rule and reads as arithmetic.

Before (`rsqrt`, in qkv, lm and gate):
```text
sfp.mul t, v, y; sfp.nop
sfp.mul t, y, t, neg
sfp.add c2, c2, t; sfp.nop
sfp.mad t, t, c2, c1; sfp.nop
sfp.mul y, y, t; sfp.nop
```
After:
```text
sfp {
    t = v * y;      nop
    t = -(y * t)
    c2 = c2 + t;    nop
    t = t * c2 + c1; nop
    y = y * t;      nop
}
```
`a * b`, `-(a * b)`, `a * b + c`, `a + b`, `a - b`, `a & b`, `a >> n` each map to one row of the §10 table; anything
that would need a temporary is an error. Lower priority than 1-5, and worth doing only after the table of idea 1 in the
code-quality section exists.

### 8. Let the compiler say which `sfp.nop` are needed

There are 84 `sfp.nop` in the examples. §10 Scheduling already contains the complete hazard table (which producers
auto-stall, which consumers are undetected). A checker that reports "missing nop" and "redundant nop" from that table
costs one pass over straight-line SFPU code. It inserts nothing, so the no-hidden-instructions rule holds, and after the
hazard probe (§12 item 1) most of the 84 can be deleted with evidence instead of being "kept until a probe shows they
are unneeded".

### Spec features that do not pay for themselves today

Used by none of the seven Llama kernels (some are exercised only by `test_ttrv_hardware.py`):

| Feature | Cost | Suggestion |
| --- | --- | --- |
| Non-entry `fn`, multiple results, the "compiled after its callers" register rule | ~120 lines of codegen, §5 Functions/Registers | Cut from v1 or mark experimental; macros cover every current use |
| Mask MOP (`mop m, mask`, labels `a b skip_a skip_b`, `mop.run n=, mask=`) | ~60 lines in `ops.py:350-366,408-429`, half of §11 | Cut until a kernel needs it |
| `sfpmacro` timing modes (`after=`), the "SFPU cycle N" state machine (`codegen.py:44-45`, `state.py:25-28`) | 148-line `sfpmacro.py` + state tracking | The kernels use one form (`mad: sfp.mul x, l0, x, delay=0`), and gap 28 says even that does not express the old CONFIG0 backdoor. Keep `delay=`, drop `after=` |
| `pack.gather` with `acc`/`step` and its footprint rules | 60 lines, the longest subsection of §9 | Either adopt it in o/qkv/gate/lm (it would delete the "full-tile pack plus NCRISC copy" path that `docs/kernels.md` and gap 18 call the main projection overhead) or cut it. Having it and not using it is the worst option |
| `noc.status`, `cb.read`, `sem.read` | small, but each is spec surface for "hand-written pumps" nobody wrote | Cut |
| `sem.init`, `sem ..., max=n` with n != 1 and the "initialized" checker facts | `ops.py:512-524` | Every kernel uses max=1. Cut |
| `unpack.ctx`, `ctx=`, `unpack.dvalid`, `shared_exp=`, `broadcast=`, `accumulate`, `math.elwsub`, `posted`, `align=`, `continue`, `i32`, `mulh`, `u64`, `e5m2`, `bfp4` | scattered | Move to an "available natively, unreviewed" appendix; §12 already says an unreviewed field is not supported just because it encodes |
| One transaction ID per request statement | 15 statements per RISC, and a macro expanded three times spends three | Allow `noc.handle h` declarations (gap 12) and make macro expansions share the statement's ID |

Separately, the spec (1,200 lines) mixes three things: what compiles and has run on a p150, what is designed, and open
hardware audits. A reader cannot tell which sentence is which without building. Split it into "implemented" (each rule
with the test that covers it) and "design", and generate the §10 instruction tables from the lowering table so they
cannot drift.

---

## Open questions for the owner

1. **Do the KV caches need zeroing at startup?** Attention masks columns beyond `valid_columns` and visits only
   `blocks` cache blocks, and `bench.py` decodes at position 4096 over random caches. If masking is complete, the zero
   kernel, its 8 images and the 60 s wait at `llama3.py:102` can go rather than be ported.
2. **Is a 12-column card a real target?** If yes, B4 matters now and the FP8 grid must change; if no, drop the 12 from
   `ops_blackhole.py:201` and from the spec's "118 on the smallest supported card".
3. **Where should FP8 scales come from?** The checkpoint has `*.input_scale` and `*.weight_scale` per projection. Is
   `output_scale = input_scale * weight_scale` the full rule the exporter used, and is the per-layer `[input, q, k, v]`
   buffer in `llama3_qkv.ttrv` the intended runtime form?
4. **Keep non-entry functions in TTRV v1?** Nothing uses them. Same question for mask MOPs and `pack.gather`.
5. **Is the row-major 11x8 placement of the exported projections a measured choice?** TTRV fixes first-N column-major.
   `docs/kernels.md` mentions 104 and 117 workers being slower from bandwidth saturation; if placement matters for
   DRAM-port contention, the spec's "placement tuned for NoC locality is a possible later addition" becomes a
   prerequisite for matching the README numbers.
6. **Does `kperf` survive the migration?** It is the only tool with a future, but its symbolizer is built on kview's
   reverse engineering. Retargeting to TTRV listings is small; is the web viewer worth keeping in this repo or should
   it move out with `chat/`?
7. **What happens to `blackhole-py-old/tests/probes/`?** The spec cites three probes as its evidence and
   `ttrv_pack_unpack.md` four more. Port to TTRV hardware tests, or copy their Findings docstrings into `docs/` before
   the old repo is archived?
8. **AICLK:** is 1350 MHz guaranteed on your cards under sustained 8B decode, or should bench record the telemetry
   value next to each number?
9. **Is the per-token host round trip acceptable long term?** Spec §12 item 7 leaves "the cost of one host round trip
   per token versus the old autonomous replay" as an audit. The answer decides whether ranged `CALL` and graph patches
   (which I list as dead) should instead come back.
10. **Should the history of `kernels/` be rewritten out of git** once the blobs are gone (the pack is 15 MiB, almost all
    of it re-exported images and RoPE tables), or is the history worth keeping as the record of the old kernels?
