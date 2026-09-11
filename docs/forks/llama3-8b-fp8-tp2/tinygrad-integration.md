# tinygrad integration

Working design for turning blackhole-py into a tinygrad backend.

This document is organized around the backend layers sketched on the whiteboard.
References to tinygrad are against `4b62c82a8`; avoid depending on exact line
numbers because that tree moves quickly.

The main architectural decision is:

> Every tinygrad-visible and persistent device buffer is ordinary dense
> row-major data with its exact logical size. The backend never tilizes a
> tensor. Tensix faces, vector tails, FPU panels, and Dst layout exist only as
> transient addressing decisions inside a generated kernel.

There is no graph-visible `pad -> realize -> shrink` layout protocol. A TT tensor
does not need persistent `padded_shape` or `tilized` metadata. The allocator may
reserve aligned physical slack, as every GPU allocator does, but that slack is
not part of tensor semantics. Copy-in, inter-kernel storage, and copy-out all
use the same dense row-major byte order.

---

## 1. Execution model: SFPU baseline, FPU fast path

Blackhole has two useful compute personalities.

| engine | hardware operation | compiler role |
|---|---|---|
| SFPU | 32 lanes of 32-bit arithmetic | complete, slower SIMD fallback |
| FPU `ELW*` | aligned `8x16` elementwise block | optional elementwise fast path |
| FPU `MVMUL` | `SrcB[8x16] @ SrcA[16x16] -> Dst[8x16]` | tensor-core-style matmul fast path |

The MVMUL result is `8x16`, not `16x16`. A software sequence commonly combines
multiple instructions into a `16x16` face or a `32x32` tile, but that larger
shape is not the atomic instruction.

### 1.1 The smallest unit we must support

The smallest **logical** computation is one scalar. The smallest general-purpose
**physical issue** is one 32-lane SFPU instruction.

The SFPU has per-lane enable state. Codegen can therefore execute a vector with
`1..32` live lanes and ignore the others. A normal dense kernel becomes:

```text
for each full group of 32 outputs:
    load/stage 32 values
    run SFPU program with 32 active lanes
    store 32 values

for the final partial group:
    load/stage N values, 1 <= N < 32
    run the same program with lanes [0, N) active
    store N values
```

This gives a correctness path for arbitrary tinygrad shapes without making
`32x32` part of the tensor layout.

`SFPLOAD` is not an arbitrary gather: it moves up to 32 values from a fixed
`4x8` footprint in Dst (even or odd columns of four rows). Codegen must stage
irregular loads into L1/Dst first. Contiguous lanes should become one NoC span;
irregular lanes may initially become several small spans. That can be slow and
still be correct, which is the right baseline.

### 1.2 FPU blocks are optimizations

The FPU is the Tensix analogue of a GPU tensor core:

- `ELWADD`, `ELWSUB`, and `ELWMUL` consume aligned `8x16` blocks.
- `MVMUL` has `M=8`, `N=16`, `K=16`.
- Fidelity phases affect both numerical behavior and cost.
- Dst accumulation, SrcA/SrcB bank ownership, and explicit zeroing are part of
  instruction selection.

Codegen should select an FPU block only when it can prove the appropriate
alignment and operand layout. Edge panels can be staged with local identities:

- zero for sum, add, and matmul;
- `-inf` for max reductions;
- one for product reductions;
- an inactive SFPU lane when no identity materialization is needed.

This padding exists only in L1, Src, or Dst scratch. It never changes the global
buffer shape.

### 1.3 What remains of the 32x32 tile

A `32x32` tile remains useful as:

- a transfer or circular-buffer page;
- a convenient Dst allocation unit;
- a hand-written kernel scheduling unit;
- a matmul macro composed from smaller FPU instructions.

It is not the minimum allocation, minimum computation, or required tinygrad
layout. In new APIs, use **page** for a storage/transport chunk and **block** or
**vector** for an execution footprint; reserve **tile** for an explicitly
`32x32` Tensix object.

### 1.4 Proven row-major execution

`examples/row_major_mvmul.py` validates the important feasibility result on
Blackhole:

```text
dense BF16 left  [64, 16]
dense BF16 right [64, 16]
    -> left @ right.T
dense BF16 output [64, 64]
```

All three DRAM buffers use the row-major-only buffer API. There is no host
permutation and no device layout-conversion pass. The unpacker performs the
ordinary per-panel transpose needed by the RHS of MVMUL, and NCRISC scatters the
naturally face-organized Dst result directly into dense output rows. The
complete result matches the CPU BF16 reference; the repeated HiFi2 sequence
reaches approximately 97% of the ideal MVMUL issue rate.

This establishes the backend rule:

```text
global row-major bytes
  -> row-major-aware NoC/unpack/address schedule
  -> transient SrcA/SrcB/Dst organization
  -> row-major-aware pack/NoC schedule
  -> global row-major bytes
```

The transient middle is analogous to register-lane or tensor-core fragment
layout on a conventional GPU. It is not a tensor representation and does not
justify a tilize operation.

---

## 2. Backend layers and file layout

### 2.1 PCIe and raw transport

Target: `tinygrad/runtime/support/tt/pcie.py`

Responsibilities:

- device discovery and BAR mappings;
- power-state ioctls;
- pinning and freeing host pages;
- TLB allocation, configuration, and release;
- small MMIO reads/writes;
- mapping pinned sysmem for command queues and signals.

Start from blackhole-py's `pcie.py`, but use tinygrad's existing system helpers
where possible. `tinygrad/runtime/support/system.py` and the interface classes
in `runtime/support/hcq.py` already cover much of the mmap/ioctl plumbing used by
AMD and other backends.

This layer knows addresses and bytes. It does not know tensor shapes, dtypes, or
Tensix tiles.

### 2.2 Device initialization and boot

Target: `tinygrad/runtime/support/tt/chip.py`

Responsibilities:

- harvesting and card information;
- DRAM-bank and usable-core enumeration;
- NoC coordinate translation;
- reset and boot of worker firmware;
- boot of the command-queue/prefetch/dispatch firmware;
- initialization of pinned sysmem, signals, and issue rings.

Keep using known-good blackhole-py firmware during the first backend bring-up.
Rewriting firmware in UOps is valuable, but it should happen after the renderer
and queue can already launch and debug a compute program.

### 2.3 HCQ

Targets:

- `tinygrad/runtime/support/tt/cq.py`
- `tinygrad/runtime/ops_tt.py`

Use tinygrad's current HCQ v1 abstraction first:

- `HWQueue` for copy, execute, wait, and signal packets;
- `HCQSignal` for host/device timeline values;
- `HCQCompiled` for the device integration;
- the existing blackhole-py issue ring and resident prefetch/dispatch firmware
  below the `HWQueue` interface.

Tenstorrent differs from AMD/NVIDIA in where the command processor lives: we
supply firmware that interprets our packet stream. That difference is below
HCQ. The host abstraction is still:

| tinygrad HCQ | TT implementation |
|---|---|
| `exec(program, args, global, local)` | enqueue `RUN` |
| `copy(dst, src, size)` | enqueue DRAM/sysmem or NoC copy |
| `wait(signal, value)` | queue/device wait |
| `signal(signal, value)` | queue/device signal |
| queue submit | publish the issue-ring put pointer |

`hcq2.py` is the likely long-term target because it represents command buffers
as UOps and derives more dependencies, but it is still AMD-only and opt-in in
the current tree. Do not block the first TT backend on it.

Open design point: map tinygrad launch geometry onto the participating Tensix
cores. This may use `Ops.SPECIAL`, explicit program metadata, or both. Do not
pretend a Tensix core is a conventional GPU thread until the mapping is defined.

### 2.4 Allocator

Target: the allocator owned by `TTDevice` in `runtime/ops_tt.py`.

The allocator receives a byte count. That is sufficient under the dense-buffer
design:

```text
tinygrad-visible size = exact requested bytes
physical reservation = round_up(requested bytes, allocator/page alignment)
```

The buffer needs only the normal device-buffer state:

- base virtual/device address;
- requested byte size;
- physical allocation handle/capacity;
- optional host mapping or TLB information.

It does **not** need:

- real versus padded tensor dimensions;
- a minimum compute shape;
- a `tilized` flag;
- dtype-dependent face layout;
- a hidden shrink view.

Weights can later be prepacked into a separate optimized buffer, just like a GPU
backend may cache a tensor-core weight layout. That is an optimization with an
explicit producer/consumer, not the representation of every TT tensor.

### 2.5 Renderer and ISA

Target: `tinygrad/renderer/isa/tensix.py`

This file owns representation and encoding:

- the Blackhole Baby RISC-V subset used by BRISC/NCRISC/TRISC;
- Tensix coprocessor instruction words;
- register classes and instruction constraints;
- pre-isel, isel, pre-regalloc, and post-regalloc matchers;
- branch fixups and long-jump expansion;
- dependency NOP insertion;
- final byte encoding.

Keep RV32 and Tensix words in one renderer because TRISC instruction streams
interleave them.

SFPU registers are vector registers, not ordinary RV registers:

- `L0..L7` are writable `32 x 32-bit` registers, 128 bytes each;
- the higher LRegs include read-only and configurable constants, lane IDs, and
  the load-macro register;
- spills should use Dst or compiler-owned L1 scratch;
- tinygrad can perform liveness and spill placement once the renderer describes
  the register class and implements `spill`/`fill`.

Initial matcher structure:

```text
high-level UOps
  -> TT scheduling/rewrite
  -> abstract Ops.INS for RV32, SFPU, FPU, unpack, pack, and sync
  -> per-stream register allocation
  -> post-regalloc dependency/NOP pass
  -> instruction bytes
```

The SFPU needs explicit latency tracking. For example, a two-cycle SFPU result
cannot be consumed immediately without a NOP or independent instruction.

### 2.6 TT-specific codegen

Target: `tinygrad/codegen/tensix.py`

This file owns choices rather than encodings:

- dense index lowering into DRAM byte spans;
- coalescing and gathering into L1;
- SFPU vectorization and tail masks;
- FPU block recognition and fidelity selection;
- Dst allocation;
- SrcA/SrcB and Dst ownership;
- CB assignment and credit protocols;
- pack/unpack region sizing;
- assignment to five instruction streams;
- insertion of cross-stream dependency edges and semaphores.

The present `ttk/fpu.py`, `ttk/sfpu.py`, `ttk/unpack.py`, and `ttk/pack.py`
combine selection with emission. Porting means splitting those responsibilities:
codegen decides *what* and *when*; the ISA renderer decides *how it is encoded*.

### 2.7 Runtime device

Target: `tinygrad/runtime/ops_tt.py`

Owns:

- `TTDevice`;
- allocator construction;
- renderer registration;
- program loading;
- kernel argument binding;
- compute/copy queue creation;
- device synchronization and profiling hooks.

Registration requires only the normal tinygrad naming convention:
`runtime/ops_tt.py` containing `TTDevice`.

---

## 3. Dense storage and byte-page NoC addressing

### 3.1 Storage pages are not compute tiles

Use one fixed, dtype-independent byte stripe for DRAM interleaving. The initial
size can be conservative and tuned later. A logical buffer is:

```text
full stripe, full stripe, ..., final partial stripe
```

For stripe size `S`, logical byte offset `o`, and a seven-bank rotation:

```python
stripe, within = divmod(o, S)
bank = (first_bank + stripe) % 7
bank_local = base + (stripe // 7) * S + within
span = min(remaining, S - within)
```

A request crossing a stripe boundary becomes multiple NoC spans. This replaces
the current assumption in `ttk/noc.py::_dram_tile` that every address is
`tile_index * dtype_dependent_tile_size`.

The low-level NoC interface already accepts a byte count. Blackhole length-based
L1/DRAM reads and writes support short transfers and up to 16 KiB per packet.
Add high-level helpers shaped like:

```python
read_span(buffer, byte_offset, byte_count, l1_address)
write_span(l1_address, buffer, byte_offset, byte_count)
```

These helpers split at DRAM stripes and the hardware packet limit.

### 3.2 Tails

There are three independent granularities:

| boundary | granularity | tail treatment |
|---|---:|---|
| global buffer | byte | exact logical size |
| host DRAM CQ | 16 bytes | aligned bounce plus explicit valid-byte count |
| worker NoC | byte-counted packet | split transfer and preserve valid-byte count |
| SFPU | 32 values | predicate up to 31 lanes |
| packer to L1 | aligned 16-byte writes | flush into scratch, then NoC-write exact bytes |
| FPU elementwise | 128 values | use SFPU tail or local identity fill |

The packer can be programmed with a datum count; its output FIFO writes aligned
16-byte chunks to L1. For a partial final group:

1. pack the valid datums into aligned L1 scratch;
2. allow the packer to zero-fill its final 16-byte flush;
3. NoC-write only `valid_count * itemsize` bytes to the dense buffer.

Thus even packer alignment does not become tensor padding.

### 3.3 Arbitrary tinygrad indexing

A single ragged final page describes dense storage, but not every kernel access.
Views, broadcasts, reductions, and gathers can give every lane a different input
index. Codegen must preserve the validity predicate attached to each load/store:

- contiguous indices: one coalesced NoC read;
- regularly strided indices: a strided unpack or several coalesced spans;
- irregular indices: gather through compiler-owned L1/Dst staging;
- invalid tail lane: no global read or write.

The first implementation may use small transfers for irregular access. Later
passes can recognize transpose, broadcast, and shared-input patterns.

### 3.4 Remove tilization entirely

Tilization is not part of the tinygrad backend, including as a hidden copy-in or
copy-out transformation. Persistent tensors, weights, activations, cache state,
and kernel boundaries all use exact dense row-major bytes.

Generated kernels may still use:

- unpacker address generators to select or transpose dense panels;
- row-major-aware SrcA/SrcB row-counter sequences;
- compiler-owned L1 scratch for a partial block;
- Dst/SFPU movement instructions;
- direct scatter from pack/L1 into dense output rows.

Do not call these operations tilization. They do not create another tensor
layout and do not require buffer metadata. They are local instruction selection
and addressing, and disappear at the kernel boundary.

Immutable weights may eventually have an explicitly cached prepacked copy if a
measured kernel benefits from one. Such a copy is a separate optimization
object with an explicit producer and consumer, never the canonical tensor.

Blackhole-py now has no `Buffer.tilized` flag, host `tile_data` permutation, or
logical tail padding. `Buffer.size` is exactly `prod(shape) * itemsize`, and its
storage byte stream is the original dense row-major byte stream. Full
1024-element pages rotate across DRAM banks; the last page carries an explicit
short byte count. Sharding is metadata and does not reorder or expand storage.

The host-to-DRAM CQ has a 16-byte transfer floor. It uses an internal aligned
bounce only for the final short transaction and returns only the valid bytes;
this does not change the buffer size or introduce readable tensor elements.
Kernels receive the valid tail count and must handle it explicitly.

The llama3 kernels still need to be migrated one at a time from face-oriented
pack/unpack assumptions and explicitly padded per-core compact shapes to dense
inter-kernel outputs. Until their stores honor the valid tail count, end-to-end
decode is intentionally unsupported: an old full-page store can overwrite the
following exact allocation, producing garbage or a CQ timeout.

### 3.5 Row-major FPU broadcasts

FPU elementwise broadcasts apply only to SrcB and operate on one `8x16` issue:

| hardware mode | SrcB selection | logical broadcast |
|---|---|---|
| `NONE` | `B[i,j]` | full operand |
| `COLUMN` | `B[i,0]` | `[M,1] -> [M,N]` |
| `ROW` | `B[selected_row,j]` | `[1,N] -> [M,N]` |
| `SCALAR` | `B[selected_row,0]` | scalar |

Ordinary elementwise operations can consume two equally permuted physical
blocks, so their local layout cancels. Broadcasts are different: only part of
SrcB is reused, so codegen must preserve the logical axis explicitly.

Lower broadcasts from tinygrad index relationships rather than exposing the raw
hardware enum:

- for `[M,1]`, present the logical values in SrcB column zero and reuse them
  across output-column panels;
- for `[1,N]`, present each 16-value segment as a selected SrcB row and reuse it
  across output-row panels;
- for a scalar, retain one known SrcB row/column-zero value;
- swap operands for commutative add/multiply when that places the broadcast
  operand in SrcB; lower subtraction with its operand order preserved.

The existing `ttk` implementation is only partially suitable. Its specialized
`move_pair_rows` plus `Broadcast.COLUMN` path works. The generic
`Broadcast.ROW` walk selects a new SrcB row every eight physical output rows,
which is not a logical whole-tensor row broadcast, and the scalar orchestration
also needs rework. Redesign these as logical-shape operations with coordinated
unpack, FPU, and row-counter schedules.

SFPU has no equivalent SrcB broadcast flag. Immediate constants are naturally
lane-wide. Runtime values require explicit loads and lane shuffles, but this is
independent of global tilization. The compiler must remember the four groups of
eight lanes when lowering dynamic SFPU reductions and broadcasts.

### 3.6 Compact decode tensors and GEMV

For single-token decode, the logical device state can be:

```text
active token id:  U32[1]
embedding output: BF16[1, 2048]
```

The token-history/KV-cache state is separate from the active token input. Do not
represent `U32[1]` as a padded token tile, and do not represent `[1,2048]` as a
tilized activation. A transport implementation may split 2048 values into
multiple byte pages, but those pages are not logical tensors or layout changes.

The current llama3 decode projection is GEMV:

```text
weight[out_features, 2048] @ token[2048]
```

It currently lowers each output row to FPU `ELWMUL` followed by an SFPU dot
reduction. It does not use MVMUL. That is a valid row-major implementation once
its page/tile assumptions are removed.

MVMUL remains an optional GEMV optimization: a core can batch eight output rows
and use `SrcB[8x16] @ SrcA[16x16] -> Dst[8x16]` panels while accumulating K.
Codegen should choose between ELWMUL+SFPU reduction and batched MVMUL based on
sharding, available rows, and measured cost. Neither path requires persistent
tilization.

The two activation buffers used for layer ping-pong or residual liveness are a
separate scheduling choice. Dense storage removes layout duplication; it does
not by itself prove that every ping-pong buffer can be eliminated.

### 3.7 Reductions

Masked elementwise tails can simply suppress invalid lanes. Reductions need an
identity:

| reduction | invalid-lane value |
|---|---:|
| sum / matmul K tail | `0` |
| max | `-inf` |
| product | `1` |

Materialize the identity in L1/Dst or select it with SFPU predication before the
reduction. This is a codegen property of the reduction, not allocator metadata.

---

## 4. Early TT rewrite and kernel boundaries

### 4.1 Why the normal final matcher is too late

TT scheduling needs information that generic lowering eventually destroys:

- reduction axes;
- symbolic index and validity expressions;
- broadcast relationships;
- opportunities to form `M=8, N=16, K=16` FPU panels;
- values that should remain resident in Dst across a loop;
- producer/consumer relationships needed for CBs and semaphores.

`Renderer.extra_matcher` runs near the end of generic codegen. It is useful for
ordinary instruction decomposition but too late to recover these structures.

Add a small renderer/device hook around `full_rewrite_to_sink`, defaulting to the
current path. The TT implementation can reuse the early generic simplification
passes, diverge before reductions and ranges become unrecoverable, then rejoin
at control-flow lowering and instruction selection.

Call this TT path `tt_rewrite_to_sink` until the exact API is settled.

This should be the only codegen-specific tinygrad core change. No new UOp is
required: hardware instructions can be represented by `Ops.INS`.

### 4.2 Do not force Tensix into generic `TensorCore`

Tinygrad's `TensorCore` model assumes a warp of threads collectively constructs
the result. Tensix MVMUL is issued by a control core into a matrix engine and
does not have that thread mapping.

Match the matmul reduction directly and lower it to an abstract TT FPU block:

```text
reduce_k(a[m,k] * b[k,n])
  -> TT_MVMUL_BLOCK(M=8, N=16, K=16, fidelity=...)
```

`OptOps.PADTO` may still be useful for rounding a loop range inside the fast
path, but it must not resize the global buffer or create the old physical-layout
protocol.

### 4.3 Fusion and buffer-count limits

Study tinygrad's current callification and kernel-fusion boundary before adding a
separate TT graph compiler. Prefer an additional matcher chain over a fork of
the scheduler.

TT kernels have finite parameter slots and local staging resources. Tinygrad
already has `MAX_KERNEL_BUFFERS` and a Metal rule limiting kernels to roughly 32
buffers. Add a TT device limit once the real command ABI is fixed, and let the
existing rangeify split machinery enforce it where possible.

---

## 5. Five-stream kernel compiler

A Tensix program contains:

- BRISC;
- NCRISC;
- TRISC0 (unpack);
- TRISC1 (FPU/SFPU math);
- TRISC2 (pack).

The compiler should first build one TT kernel/dependency graph while tensor
relationships are still visible. Then:

1. choose L1 staging and circular buffers;
2. assign operations to engines and streams;
3. insert cross-stream CB, semaphore, and ownership edges;
4. reproduce loop/control structure in every participating stream;
5. split into five stream-local graphs;
6. linearize and register-allocate each stream independently;
7. insert stream-local latency NOPs and encode bytes.

Registers are not live across processors; hardware resources are. Therefore the
global pass tracks Dst/Src/CB ownership, while ordinary register allocation runs
after the stream split.

Tinygrad currently expects one program object. The TT renderer/runtime can place
the five binaries in a small container:

```text
header
brisc offset/size
ncrisc offset/size
trisc0 offset/size
trisc1 offset/size
trisc2 offset/size
payloads...
```

`TTProgram` parses the container and uploads each stream to its firmware-defined
address.

---

## 6. Explicit synchronization and ownership

The TT scheduler must model at least:

- NoC read completion before an unpack consumes L1;
- NoC write source completion before L1 reuse;
- CB reserve/push/wait/pop and page counters;
- retained versus last-consuming CB reads;
- unpack configuration and completion;
- SrcA/SrcB valid, clear, and bank-flip state;
- Dst row validity;
- Dst ownership transitions between math, SFPU, and pack;
- FPU-to-SFPU and SFPU-to-pack visibility delays;
- SFPU register producer/consumer latency;
- unpack-to-Dst serialization;
- pack completion and output FIFO flush;
- the finite hardware semaphore inventory;
- loop-carried resources across generated loops.

Represent ordering in the compiler graph first. Lower graph edges to the
appropriate combination of:

- `Ops.AFTER` for compiler ordering;
- CB protocol operations;
- `STALLWAIT`;
- `SEMWAIT`, `SEMPOST`, and semaphore get;
- explicit NOPs for fixed pipeline hazards.

`Ops.BARRIER` is not a substitute for these resource-specific protocols.

---

## 7. Firmware in UOps

Porting the resident queue firmware to UOps is viable:

- RV register allocation replaces the manual `fw.reg()` scopes;
- ranges and branches represent the dispatch loop;
- volatile loads represent issue-ring and signal polling;
- the same RISC-V encoder serves firmware and compute streams.

Do it after one end-to-end compute kernel works with the existing firmware.
Otherwise a renderer bug can hang the firmware needed to diagnose the renderer.

Longer term, graph-specialized dispatch firmware may remove generic queue
overhead. That is the point where firmware UOps become more than a cleanup.

---

## 8. Validation plan

### 8.1 Storage and tails

1. Allocate exact logical sizes from 1 byte through several storage stripes.
2. Round-trip host copy-in/out without tilization.
3. Exercise NoC reads/writes ending at every byte offset around 16- and 64-byte
   boundaries.
4. Verify span splitting across all seven DRAM banks.
5. Confirm no final write modifies the following allocation.

### 8.2 SFPU baseline

1. Run one 32-lane add/multiply program.
2. Sweep active lanes from 1 through 32.
3. Verify disabled lanes do not read or write global memory.
4. Test a non-contiguous gather through L1/Dst staging.
5. Test spill/fill of an LReg through Dst and L1.
6. Validate generated dependency NOPs against documented latencies.

### 8.3 Pack and unpack

1. Unpack variable datum counts into SrcA, SrcB, and Dst.
2. Pack `N` datums for `N in {1, 7, 8, 15, 16, 17, 31, 32, 127, 128, 255, 256}`.
3. Inspect raw L1 bytes for headers and 16-byte flush padding.
4. Verify that pack output is contiguous for the requested Dst range.
5. NoC-write only the valid bytes and round-trip the result.
6. Compare direct dense addressing with explicit compiler-owned staging.

### 8.4 FPU

1. Validate one `8x16` ELW block for add, subtract, and multiply.
2. Validate one `8x16 @ 16x16 -> 8x16` MVMUL.
3. Validate dense row-major `64x16 @ 64x16.T -> 64x64` without a tilize pass.
4. Validate `[M,1]`, `[1,N]`, and scalar broadcasts from dense buffers.
5. Sweep fidelity phases and record numerical error and cycle cost.
6. Test M/N/K edge panels using local identity fill.
7. Verify Dst32 address swizzling and FPU/SFPU handoff.

### 8.5 Scheduling

1. Deliberately test every CB retain/consume ordering.
2. Double-buffer NoC read against unpack/math.
3. Switch Dst ownership math -> SFPU -> pack -> math.
4. Exhaust and recycle the semaphore allocation strategy.
5. Compile a five-stream loop and verify every stream takes the same iteration
   count and reaches compatible synchronization points.

### 8.6 Numerical conventions

Decide and test:

- BF16 truncation versus round-to-nearest-even;
- denormal handling;
- NaN/infinity behavior;
- reduction identities;
- integer sign-magnitude conversions in Dst.

Do not let host conversion and device conversion silently use different BF16
rounding conventions.

---

## 9. Bring-up order

1. **PCIe:** map BARs, pin sysmem, and perform safe MMIO.
2. **Boot:** enumerate harvested hardware and start existing firmware.
3. **Allocator:** exact-sized dense byte buffers; host round-trip only.
4. **HCQ v1:** launch an existing hand-written blackhole-py kernel.
5. **RV renderer:** compile a scalar control/NoC kernel to Baby RISC-V.
6. **One SFPU vector:** dense 32-element add with existing pack/unpack helpers.
7. **SFPU tails:** active counts `1..32`, exact final NoC writes.
8. **Generic elementwise backend:** ordinary tinygrad shapes and views through
   the SFPU fallback.
9. **Reductions:** masked tails and correct identities.
10. **FPU blocks:** row-major ELW and logical broadcasts, then optional MVMUL
    matmul/GEMV lowering.
11. **Five-stream scheduler:** generated CBs, semaphores, and ownership edges.
12. **Decode projection:** first meaningful model kernel.
13. **Firmware UOps and HCQ2:** after correctness and profiling infrastructure
    are reliable.

---

## 10. Open questions

- What fixed DRAM stripe size gives the best balance of bank parallelism and
  span-splitting overhead?
- Can pack/unpack variable-count operation be made fast enough for every tail,
  or should very small tails use RISC Dst access?
- Which irregular access patterns deserve dedicated coalescing/transpose rules?
- What is the correct tinygrad hook for `tt_rewrite_to_sink` with the smallest
  maintainable core change?
- Where should TT-specific fusion boundaries live relative to callify/rangeify?
- What kernel buffer/parameter limit should TT publish?
- How should core launch geometry and sharding map to `Ops.SPECIAL` and
  `Ops.MULTI`?
- How many hardware semaphores are safely available to generated programs after
  firmware reservations?
- Can Dst allocation and spill placement be expressed as a conventional
  register-allocation problem, or does it need a separate interval allocator?
- When is immutable weight prepacking profitable, and how should the cache be
  invalidated?
- How should BFP formats and their shared exponent streams be represented if
  tinygrad does not expose the dtype?
- What fidelity mode should the cost model use for BF16 MVMUL and ELWMUL?

The first backend does not need all of these answers. Dense buffers plus the
masked SFPU path establish ordinary GPU semantics; everything else can then be
added as a measured optimization.
