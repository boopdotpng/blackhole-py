# tinygrad integration

Notes on porting blackhole-py to a tinygrad backend. Line references are against
tinygrad `3946df787` (clean master) unless stated otherwise.

The guiding constraint: **make as few changes to tinygrad core as possible.** The
conclusion below is that we need roughly one, in `codegen/__init__.py`.

---

## 1. Registration needs zero core edits

`device.py` contains no backend-specific code at all — no allocator, no device.
Registration is pure filename convention (`device.py:17`):

```python
self._devices = [x.stem[len("ops_"):].upper()
                 for x in (pathlib.Path(__file__).parent/"runtime").iterdir()
                 if x.stem.startswith("ops_")]
```

and `_Device.get_class` (`device.py:31`) imports `tinygrad.runtime.ops_{x}` and
picks the member whose lowercased name is `x + "device"`.

So `runtime/ops_tt.py` containing `class TTDevice` **is** the registration.

The only optional core edit here is appending `"TT"` to `ALL_DEVICES`
(`device.py:14`), which affects nothing but autodetect ordering and the
`enumerate_devices_str` banner.

Every real backend — AMD, NV, QCOM, CPU, RDMA — lives entirely in
`runtime/ops_*.py`. `device.py` is the abstract `Allocator` / `Buffer` /
`Compiled` contract only.

---

## 2. File layout

### `tinygrad/runtime/support/tt/`
Everything that talks to hardware, nothing that knows about kernels.

| file | from | contents |
|---|---|---|
| `pcie.py` | `pcie.py` | TLB windows, BAR mapping, physical allocator |
| `chip.py` | `device.py` | reset, harvesting, NOC coordinate translation, core enumeration |
| `cq.py` | `cq.py` | ring layout, `Op` enum, `PacketLayout`, host-side queue structure |
| `firmware.py` | `fw/` | prefetch / dispatch / core firmware (see §6) |

Read `runtime/support/system.py` before writing `pcie.py` — its generic
PCI/mmap/ioctl helpers may already cover the boring parts. Also
`hcq.py:15-57` (`MMIOInterface`, `FileIOInterface`) which is the standard
wrapper every backend uses for exactly this.

Skip autogen. AMD hand-writes plenty of its structs.

### `tinygrad/renderer/isa/tensix.py`
From `isa.py` + `asm.py`. Opcode enums (RV32 **and** Tensix words), encoders, the
five matcher slots, `is_two_address`, `stack_pointer`, `spill`/`fill`,
`asm_str`, `render`.

Structurally the `x86.py` analogue. Mirror its section boundaries:

```
  11-122   X86Ops enum
 123-160   extra_matcher
 162-199   pre_isel_matcher
 200-220   register definitions
 221-547   isel_matcher
 548-604   pre/post regalloc (lower_range / lower_end)
 605-800   encode
 802-880   X86Renderer class
```

**Naming: `tensix.py`, not `rv.py`.** A single trisc stream interleaves both
instruction families — `asm.py:166-177` shows Tensix words go inline in the RV32
stream on trisc0/1/2, and only brisc needs the MMIO store to
`INSTRN_BUF_BASE`. One renderer owns both.

Keep the RV32 encoder table (`_r`/`_i`/`_s`/`_b`/`_u`/`_j` from `isa.py`) as a
self-contained section inside the file. It's pure RISC-V with nothing Tensix
about it, so if a generic RISC-V backend is ever wanted, that section lifts out
into `rv.py` and `tensix.py` subclasses it. Don't do that split preemptively.

Renderer naming is derived from the class name: `_renderer_name` strips
`RENDERER` and the device prefix, so `TensixRenderer` with `device = "TT"`
becomes selectable as `DEV=TT:TENSIX`. Multiple renderers per device are
supported — `CPUDevice` registers four — so a readable debug renderer alongside
the real one is free.

### `tinygrad/codegen/tensix.py`
From `ttk/`. The part with **no upstream analogue**:

- pad to nearest 32-visible shape, tile-ification
- CB assignment and the reserve/push/wait/pop credit protocol
- the retain-vs-consume edge attribute (last consumer pops, earlier readers retain)
- engine assignment (unpack / FPU / SFPU / pack)
- the 5-stream split

`ttk/cb.py`, `ttk/sync.py`, `ttk/shard.py`, `ttk/l1.py` land here, as rewrite
rules rather than imperative builders.

**`ttk/fpu.py`, `ttk/sfpu.py`, `ttk/unpack.py`, `ttk/pack.py` split across the
two files.** The "which instruction, and how is it encoded" half goes to
`isa/tensix.py`; the "when do I choose this, and what does it cost" half goes to
`codegen/tensix.py`. Today these are fused — `fpu.py:matmul` both selects and
emits. Separating them is most of the porting work, and it's the thing that
keeps tile logic out of isel matchers where it can't be tested.

### `tinygrad/runtime/ops_tt.py`
From `program.py`. `TTDevice`, `TTAllocator`, `TTProgram`, `TTComputeQueue`,
`pm_lower`.

### `tinygrad/codegen/__init__.py`
The one core edit. See §5.

---

## 3. Host tilization goes in `_copyin`

The allocator contract (`device.py:238-241`):

```python
def _alloc(self, size:int, options:BufferSpec): ...
def _copyin(self, dest, src:memoryview): ...
```

Call site (`engine/realize.py:171`):

```python
dest.allocator._copyin(dest._buf, src.as_memoryview(allow_zero_copy=True))
```

`dest` is **whatever opaque `_alloc` returned** — AMD and CPU return their own
`HCQBuffer` dataclass. So `TTAllocator._alloc` returns a `TTBuffer` carrying
layout metadata, and `_copyin` reads it off `dest` and permutes on the way in.

`Buffer.tile_data` (`program.py:158+`) moves in verbatim. It's a pure
permutation on opaque bytes:

```python
element = np.dtype(f"V{self.dtype.itemsize}")   # never inspects values
tiles = physical.reshape(self.physical_tiles, 2, 2, 16, 16)
tiles = tiles.transpose(0, 1, 3, 2, 4).reshape(self.physical_tiles, 1024)
```

Nothing above the allocator can tell the difference. Keep numpy here — it's a
strided memcpy and tinygrad's CPU backend will not beat it.

### Why not a `BufferSpec` field

`BufferSpec` (`device.py:80`) *is* passed to `_alloc` and lands on
`Buffer.options`, so a `layout` field would work. But it's `frozen=True,
eq=True` and used as the LRU alloc cache key, so adding a field is a genuine
core edit. It'd be a *correct* one — two differently-tiled buffers genuinely
aren't interchangeable in the alloc cache — but it's avoidable.

The layout of a TT weight is a function of how the kernel consumes it, which we
know at schedule time, not at `Buffer.__init__`. Deriving it into our own
`TTBuffer` at `_alloc` keeps the diff at zero. Reach for the `BufferSpec` field
only if a case turns up where the user must state layout up front.

### Context: nothing in tinygrad models physical layout

`dtype` + `size` is the entire buffer model. `AddrSpace` is about *where*, not
*how arranged*. This is genuinely new ground, and hiding it behind `_copyin` is
the move precisely because it means not having to win an argument about the core
model before getting started.

### Known gotcha: bf16 rounding

`Buffer.from_numpy` (`program.py:122`) truncates:

```python
(values.view(np.uint32) >> 16).astype("<u2")
```

while `_bf16_rne_bytes` (used for the rope tables, `examples/llama3.py:1956`)
rounds to nearest even. Two conventions already live in one file. tinygrad's
bf16 cast is RNE, so routing conversion through tinygrad silently switches the
truncating path and shifts golden-test numerics by up to 1 ulp. Decide
deliberately.

Also `X86Renderer.supported_dtypes()` (`x86.py:879`) explicitly excludes
`bfloat16`. `ClangRenderer` / LLVM handle it fine.

---

## 4. HCQ — use v1, not v2

**HCQ = Hardware Command Queue. It is not AMD-specific.** `support/hcq.py` (644
lines) is the shared abstraction subclassed by **AMD, NV, QCOM, CPU, and
RDMA**: `HCQCompiled`, `HWQueue`, `HCQSignal`, `HCQProgram`, `HCQBuffer`. This
is the one to use.

`support/hcq2.py` is a separate in-progress rewrite and is barely live:

```python
HCQ_DEVS = frozenset(("AMD",))                          # hcq2.py:24
if getenv("HCQ2"): from extra.hcq2.ops_amd2 import *    # ops_amd.py:1104
```

AMD-only, opt-in by env var, device implementation out of tree in `extra/`.
`ops_cpu.py` carries three `# TODO: move to hcq2` comments — direction of
travel, not current state.

**Consequence:** hcq2's `DepsTracker`, which derives signal/wait automatically
from buffer read/write sets, is *not* available to us. On hcq v1 sync is
explicit — `HWQueue.signal(sig, val)` / `.wait(sig, val)` against timeline
signals. Still much better than hand-ordering, but we write the deps rather than
having them inferred.

### What hcq2 actually does

Not C generation. The UOps **are the command packets**. `make_cmdbuf`
(`hcq2.py:52`) walks the queue's `Ops.INS` operands and splits them:

```python
for s in (s for ins in lin.src for s in ins.src):
    if (ssimp:=s.simplify()).op is not Ops.CONST: patches.append((len(blob), ssimp))
    blob += struct.pack(...)
```

Constants bake into a literal blob; non-constants become *patches* — stores into
the command buffer resolved at link time. The packet stream compiles once and
only varying fields (buffer addresses, timeline values) get written per launch.

**That is our `DeviceTrace`.** `device.py:40-56` — `_TraceParam`,
`_TraceRuntime`, `DeviceTrace` — is the same mechanism: record once, patch the
varying fields on replay. We arrived at the same design independently, which is
a decent signal the eventual hcq2 port will feel natural. Not now.

### Our CQ vs. theirs

Structurally very close. One real difference: **where the command processor
lives.**

- Ours (`cq.py` + `fw/cq.py`): host writes records into a prefetch queue,
  on-device brisc firmware prefetches, dispatches to cores, writes completions.
  Our `Op` enum (`PAD`/`UNICAST_WRITE`/`MCAST_WRITE`/`RUN`/`DRAM_RECORD`) is a
  packet ISA interpreted by microcode we wrote.
- tinygrad's `HWQueue`: host builds the packet stream and rings a doorbell; a
  *hardware* command processor consumes it. AMD PM4 and NV methods are packet
  ISAs interpreted by fixed-function microcode.

So the only difference is that on Tenstorrent we supply the command processor.
That sits *below* `HWQueue`, which doesn't care — it only requires that
`_submit(dev)` gets bytes to the device and that a signal eventually becomes
visible to the host.

The mapping is nearly mechanical:

| `hcq.py` | ours |
|---|---|
| `HWQueue.q(*values)` | append a record to the issue ring |
| `HWQueue.exec(prg, args, gs, ls)` | `Op.RUN` |
| `HWQueue.copy(dest, src, sz)` | `Op.UNICAST_WRITE` / `Op.MCAST_WRITE` |
| `HWQueue._submit(dev)` | bump the prefetch queue write pointer |
| `HCQSignal` | `DISPATCH_DONE_COUNT` / completion ring |
| `HCQBuffer(va_addr, meta, view)` | `Allocator` + `TLBWindow` |

`HCQSignal` is the piece to look at hardest. It needs a monotonic 64-bit value
the device writes and the host polls, with `wait()` doing backoff
(`hcq.py:283`). Our `DISPATCH_COMPLETION_*` machinery is already that shape; it
mostly needs reframing as "a counter at an address" rather than a ring of
entries.

`fw/` stays exactly as it is — it sits below `HWQueue` and is invisible to
tinygrad.

### Bonus: `pm_lower` / `pm_bufferize` already exist

`Compiled.pm_lower` and `Compiled.pm_bufferize` (`device.py:330-331`) are
per-device `PatternMatcher` hooks. They fire on the **host command queue** path,
not kernel codegen — `CPUDevice.pm_lower` (`ops_cpu.py:163`) rewrites
`CUSTOM_FUNCTION("submit_cmdbuf")` into a store.

That's the hook for *"make dram uploads go through cq"* from `todo_today.md`.
Already device-overridable, zero core changes.

---

## 5. Where lowering hooks in

`to_program` is called from `engine/realize.py:246` with `Device[...].renderer`.
`do_to_program` (`codegen/__init__.py:424`) does:

```python
full_sink = full_rewrite_to_sink(ast, renderer, optimize=ast.tag is None)
prog_info = ProgramInfo.from_sink(full_sink, renderer.target)
if isinstance(renderer, ISARenderer):
    full_sink = graph_rewrite(full_sink, renderer.pre_isel_matcher, ...)
    full_sink = graph_rewrite(full_sink, renderer.isel_matcher, ...)
```

**There is no per-device override of `to_program`.** So an early divergence
needs either a branch here or a `Renderer`-level hook — e.g. giving `Renderer` a
`to_sink` classmethod defaulting to `full_rewrite_to_sink`. Realistically two or
three lines. **This is the one unavoidable core change; budget for it and
nothing more.**

### Why we need to diverge early

Diverge after `pm_simplify_ranges` (`codegen/__init__.py:277`), before
`expander2` (286) and "remove reduces" (289). At that point `Ops.REDUCE`,
`AxisType`-tagged RANGEs, shapes, and symbolic INDEX are all still intact. It is
also the same seam where tinygrad itself inserts WMMA
(`codegen/opt/postrange.py:219-312`), so it's a load-bearing seam, not a
convenient gap.

Rejoin at `pm_add_control_flow` → `linearize` → `regalloc` → `asm_str`.

Note the existing escape hatch: `optimize=ast.tag is None`. `ops_cpu.py:192`
builds its firmware programs as hand-written UOps with
`.sink(arg=KernelInfo(...), tag=1)` and pushes them straight through
`do_to_program`, skipping the optimizer entirely.

### Things settled earlier, recorded so they don't get re-litigated

- **No new UOps needed.** `Ops.INS` is unconstrained in `uop/spec.py:100`
  (`(UPat(Ops.INS), lambda: True)`). SFPSTORE, TTMVMUL etc. are all just `INS`
  with our opcode in `arg`.
- **`TensorCore` / `Ops.WMMA` cannot describe MVMUL.** `codegen/opt/tc.py`
  asserts `dims[0]*dims[1] == 2**(local_axes+upcast_axes)` and
  `2**local_axes == self.threads` — warp/thread-shaped, which Tensix isn't.
  Match `REDUCE(MUL(a,b))` directly in `pre_isel_matcher` instead.
- **`BARRIER` is not the sync primitive.** It's a symmetric rendezvous and it's
  in `PSEUDO_OPS` (`codegen/late/regalloc.py`), so it emits nothing on the ISA
  path. Use `Ops.AFTER` for graph ordering and `INS(TT.SEMWAIT/SEMPOST)` for
  emitted sync — the split hcq2 already uses (`hcq2.py:127,148,179`).
- **Loop-carried Dst liveness is already handled.** `codegen/late/regalloc.py:29-31`
  extends live ranges across RANGE. The persistent `O0/O1/M/L` state across
  kv_blocks in `gqa_attention_fused` does not need custom machinery.
- **`GroupOp.ALU`** is the IR's arithmetic op set (dtype-polymorphic, includes
  vectors). Unrelated to `AddrSpace.ALU`, which is a PARAM passed by value.
  Easy confusable.
- **Control flow must be replicated per stream.** In `gqa_attention_fused`,
  trisc0 (1551), trisc1 (1592), and trisc2 (1619) each run their own
  `for block in range(block_count)`. The stream split therefore happens **after**
  regalloc, because SrcA/Dst live ranges cross streams.
- **The isel decision that needs a rule:** `Ops.ADD` maps to two different
  Tensix instructions with different operand locations and costs — FPU
  `TTELWADD` (whole-tile, SrcA+SrcB→Dst) vs SFPU `TTSFPADD` (lane-wise,
  LReg→LReg). `WHERE`/`EXP2`/`RECIPROCAL` are SFPU-only. Start with a hard rule
  (SFPU iff transcendental, or the value is already Dst-resident) rather than a
  cost model.

---

## 6. Firmware in UOps — viable, and worth it, but not first

`fw/cq.py` is already an embedded RV32 DSL with **hand-rolled register
allocation**:

```python
fw = Asm("brisc")
with fw.scope(): _emit_prefetch(fw, fw.reg(12))
```

Twelve registers reserved by hand and threaded through as a tuple. Porting to
UOps deletes `fw.reg`, `fw.scope`, and all the manual liveness reasoning,
because `codegen/late/regalloc.py` does linear-scan with spill/fill and
RANGE-aware live-range extension. That isn't a code-sharing win, it's deleting a
category of bug.

The precedent is close to our use case: **read `signal_prog`, `wait_prog`,
`timestamp_prog`, `worker_prog` in `ops_cpu.py:25-60`.** `worker_prog` is a
firmware dispatch loop — spins on a semaphore, indexes a ring buffer, calls the
entry — in ~8 lines of UOps using `UOp.param(..., volatile=True)`, `UOp.range`,
`.after()`, `.end()`. Structurally our prefetch loop. This is also the best
existing demonstration that the scalar RISC-V side works via
`INS` + `RANGE` + `STORE` + `AFTER`.

Location: `runtime/support/tt/firmware.py`, matching ops_cpu keeping its
programs in the runtime file.

**Ordering warning.** Do not port firmware first. Debugging a miscompiled
register allocation on a hung Tensix core with no printf is a bad time, and the
firmware is the thing that would tell us what went wrong. Keep `fw/` as-is, get
one compute kernel end-to-end against working firmware, port firmware once the
RV32 encoder has been exercised.

The firmware is also a *fixed* artifact — it doesn't change per graph, so it
earns the least per unit of risk. That flips once we want to specialize the
dispatch loop per graph, which is the actual long-term prize.

---

## 7. The one structural mismatch: 5 streams, 1 binary

`TinyELF.lib` is a single `bytes`. `render(uops) -> str` returns one string.
`Program.__call__` launches one thing. Tensix needs five instruction streams
(brisc, ncrisc, trisc0/1/2) from one linearized list.

Escape: `obj.lib` is opaque to everything except our own `TTProgram.__init__`.
So `render` emits all five concatenated behind a header and `TTProgram` splits
them. Ugly but zero-diff — and x86 already cheats in the same direction
(`x86.py:865` returns `binary.hex()`, a binary pretending to be text).

---

## 8. Suggested order

1. **`TTAllocator`** (`_alloc`/`_copyin`/`_copyout`) against existing `pcie.py`,
   with `TTDevice` having no renderer at all. Target:
   `Tensor([1,2,3]).to("TT").numpy()` round-trips. Validates registration,
   allocator, and the tilize hook before any codegen exists.
2. **`HWQueue` subclass** over existing `cq.py` + `fw/`. Target: launching an
   existing hand-written kernel through tinygrad's queue.
3. **`TensixRenderer`** — RV32 encoding only at first, no Tensix words. Target:
   a scalar kernel (the mask/zero fill loop from
   `examples/llama3.py:1438-1494`, ~57 lines of hand-written brisc RISC-V) that
   currently exists in hand-written form.
4. **Tensix words + isel** for one op. `decode_projection` is the right first
   target: single bias-free `weight @ x`, already sharded over 118 cores, no
   softmax.
5. **`codegen/tensix.py`** — CB assignment, stream split — driven by whatever
   step 4 needs.
6. **Firmware in UOps**, last.

An earlier suggested probe, still worth doing at any point: write
`decode_projection` as a `Tensor.custom_kernel` (`tensor.py:160`, marked "alpha
and may change") and run it on CPU/CLANG to test whether the opt pipeline can be
constrained to 32×32 tiles without forking `codegen/opt/`. See
`test/backend/test_custom_kernel.py` — `custom_gemm`, `simple_qkv_kernel`,
`slice_sum_kernel` — which is the single highest-value file to read.

---

## 9. Open questions

- Can `codegen/opt/` be constrained to only ever emit 32×32 tiles, or does it
  need a fork? (Probe in §8.)
- Does the layout decision (which weights tilized, which not) belong on the
  buffer, or derived from consumers at schedule time? Currently the selectivity
  lives at the *upload call site* — `_upload_weights` (`examples/llama3.py:1944-1952`)
  passes `embedding_data` straight to `_stage_upload` with no `tile_data()`
  call — not in the `tilized` flag.
- `embedding_weight` and `lm_weight` are the **same buffer** (tied weights,
  `examples/llama3.py:1802-1809`) with two consumers. Both are row-oriented — a
  single-row gather in `decode_embedding`, and a GEMV in the LM head — so
  untilized is correct for both. Good evidence for treating layout as a
  scheduling decision. Note `lm_weight` is constructed with
  `tilized=self.embedding_weight.tilized`, i.e. the default `True`, while the
  bytes on device are unpermuted. The flag is only read inside `tile_data`
  (`program.py:162,193,199,228`) so it's inert today, but anyone calling
  `.tile_data()` on either buffer would silently permute already-flat data.
- Once layout is one index expression shared by host and device, the separate
  host/device tilization equivalence probe becomes structurally unnecessary.
