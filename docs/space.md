# ttk — API specification and sync model

## Goals

1. Support row-major, untilized tensors end to end. No tilize/untilize in the
   unpacker or packer.
2. FPU and SFPU are programmed explicitly via high-level primitives, but the
   framework guarantees correctness: no hangs, no silent data races, correct
   SFPU NOP insertion, correct Dst ownership barriers.
3. CB pointer management is fully automated. The kernel author never calls
   `reserve_back`, `push_back`, `wait_front`, or `pop_front`.
4. MOP/replay generation is automated. Repeated instruction sequences are
   detected and collapsed into `TTMOP` + replay buffer loads when they fit.
5. Lowering target for tinygrad. tinygrad's renderer produces a linear
   `Ops.INS` sequence (TensixOps IR); ttk splits it across threads and inserts
   all synchronization.
6. First milestone: port `examples/llama3.py` to row-major using ttk. Second
   milestone: tinygrad backend.

---

## Module layout

```
ttk/
  noc.py      — NoC transactions (DONE, needs partial-tile element counts)
  cb.py       — byte-based circular buffers, auto-managed pointers
  fpu.py      — FPU instruction emission + SETADC face/row/col config
  sfpu.py     — SFPU instruction emission + NOP scoreboard + butterfly/replay
  unpack.py   — unpacker config + row-major stride setup
  pack.py     — packer config + CB write-back
  sync.py     — barrier primitives (stall, publish, sem) + Dst state machine
  mop.py      — MOP/replay detection and generation
  codegen.py  — Program builder, thread splitting, sync insertion
  reduce.py   — cross-core reduction patterns
```

---

## NoC (`ttk/noc.py` — mostly done)

Already supports: `transaction.read`, `transaction.write`,
`transaction.multicast_write`, `transaction.inline_write`,
`transaction.atomic_inc`, with TID-based completion tracking.

### Addition: partial-tile element counts

```python
class Transaction:
    def read(self, source_address, source_coordinate, target_address,
             element_count, dtype, source_middle_address=0): ...
    def write(self, source_address, target_address, target_coordinate,
              element_count, dtype, target_middle_address=0, posted=True): ...
```

`element_count * dtype.itemsize` replaces the old `packet_bytes`. The NoC
already handles arbitrary byte counts — this is just a units change at the API
level so callers think in elements, not bytes.

For CB-bound reads/writes (see below), the CB layer wraps this.

---

## Circular buffers (`ttk/cb.py`)

### Design

- Allocated in **bytes**, not tile-depth. A CB owns a contiguous L1 region.
- Each slot records its valid **element count** (not always a full tile).
- Producer/consumer pointer management is fully automated. The kernel author
  declares data movement intent; the framework inserts `reserve_back`/
  `push_back`/`wait_front`/`pop_front` at the right points.

### API

```python
class CB:
    addr: int           # L1 base address
    capacity: int       # total bytes
    dtype: DType        # element type (for size math)

def p.cb(dtype: DType, capacity: int | None = None,
         element_count: int | None = None) -> CB
```

If `capacity` is None, it defaults to `element_count * dtype.itemsize`. If
neither is given, it defaults to one tile (1024 elements for BF16/F32).

### Producer side (BRISC / NCRISC)

```python
# Read from DRAM into CB — one call, fully automated
k.noc.read_to_cb(buffer, tile_index, cb)
k.noc.read_elements_to_cb(buffer, element_index, cb, count)
# Framework emits:
#   CB.reserve_back(cb)
#   noc.transaction.read(buf_addr, buf_coord, cb_write_ptr, count*itemsize)
#   CB.push_back(cb)

# Write from CB to DRAM — one call, fully automated
k.noc.write_from_cb(cb, buffer, tile_index)
k.noc.write_elements_from_cb(cb, buffer, element_index, count)
# Framework emits:
#   CB.wait_front(cb)
#   noc.transaction.write(cb_read_ptr, buf_addr, buf_coord, count*itemsize)
#   CB.pop_front(cb)
```

### Consumer side (unpack / pack — automated)

Unpack and pack calls automatically consume/produce CB slots. The framework
tracks CB state and inserts the right `wait_front`/`pop_front` on the unpack
side and `reserve_back`/`push_back` on the pack side. The author never touches
CB pointers directly.

---

## Unpacker (`ttk/unpack.py`)

### Row-major without tilize

The unpacker has config registers for source row stride. Row-major L1 data is
read directly into SrcA/SrcB faces — no tilize instruction.

Standard face layout for row-major data with row stride `S` (in elements):

```
Face 0 (16×16): rows  0..15,  cols  0..15
Face 1 (16×16): rows 16..31,  cols  0..15
Face 2 (16×16): rows  0..15,  cols 16..31    (if S > 16)
Face 3 (16×16): rows 16..31,  cols 16..31
```

For decode (16-element rows), only faces 0+1 are used. For 32-element rows,
all 4 faces. The unpacker config (`SRC_ROW_STRIDE`, `FACE_DIM`) is set
automatically based on the declared data layout.

### API

```python
# Unpack from CB into SrcA or SrcB
k.unpack(cb, target="A" | "B")

# Unpack from L1 directly (for weights/gamma that live in L1, not CB)
k.unpack_l1(addr, dtype, target="A" | "B")

# Unpack a sub-region (for tails / partial tiles)
k.unpack(cb, target="A", rows=16, cols=4, dst_row_offset=0)

# Matmul unpack: SrcA = left matrix, SrcB = right matrix (transposed stride)
k.unpack_matmul(cb_a, cb_b, right_transpose=True)
```

The framework emits `TTUNPACR` with the right `AddrMode`, `CfgContextId`, and
stride config. For repeated unpack sequences, MOP detection (see below) may
collapse them into a replay.

### Layout per op type

| Op | SrcA | SrcB | Notes |
|---|---|---|---|
| Eltwise (mul/add) | row-major data | row-major data | same layout both sides |
| GEMV (weight @ x) | weight rows | input vector broadcast | `TTMVMUL` |
| Matmul (A @ B) | A rows | B columns (transposed stride) | `TTMVMUL` × N |
| Broadcast | full data | stride=0 on broadcast axis | `TTELWMUL` |
| Reduction | full data | unused (SrcB = 1.0) | `TTELWMUL` + SFPU reduce |

---

## FPU (`ttk/fpu.py`)

### Granular sub-tile operation

The FPU operates on SrcA/SrcB (4 faces of 16×16 = 1024 elements). The
`SETADCXY`/`SETADCZW` counters control which sub-region it iterates over. The
FPU API exposes `rows`, `cols`, and `dst_row_offset` and internally programs
SETADC.

### API

```python
# Eltwise binary: Dst = SrcA OP SrcB
k.fpu.binary("mul", dst=0)                         # full 32×32
k.fpu.binary("mul", dst=0, rows=16, cols=16)       # face 0 only
k.fpu.binary("add", dst=0, rows=32, cols=4)        # 32 rows × 4 cols (tail)
k.fpu.binary("add", dst=0, accumulate=True)        # accumulate into existing Dst

# Copy SrcA to Dst (broadcast SrcA without computing)
k.fpu.copy_a(dsts=(0, 1, 2, 3))                    # broadcast to 4 Dst tiles
k.fpu.copy_a(dsts=(0,), rows=16, cols=16)          # partial copy

# Matrix multiply: Dst = SrcA × SrcB (SrcB transposed)
k.fpu.matmul(dst=0, right_transpose=True)
k.fpu.matmul(dst=0, accumulate=True, right_transpose=True)

# Zero a Dst tile (TTZEROACC)
k.fpu.zero(dst=0)
k.fpu.zero(dst=0, rows=16, cols=16)                # zero only face 0
```

### SETADC programming

Internally, `rows`/`cols`/`dst_row_offset` translate to:

```
SETADCXY  CntSetMask=0x7, Ch0_Y=rows, Ch0_X=cols, ...
SETADCZW  CntSetMask=0x7, Ch0_Z=..., Ch0_W=..., ...
```

The framework computes the face decomposition from `rows`/`cols` and emits
the right `SETADC` sequence before the FPU instruction. Default is full
32×32 (all 4 faces).

### FPU sync — no per-instruction NOPs

The FPU pipeline has no per-instruction latency tracking (unlike SFPU). All
FPU synchronization is at phase boundaries, handled by the Dst tile state
machine (see Sync below). The author never calls `stall()` for FPU.

---

## SFPU (`ttk/sfpu.py`)

### NOP scoreboard — automatic 1-cycle latency tracking

The SFPU has a 1-cycle result latency: if instruction N writes a lane
register and instruction N+1 reads it, a `TTSFPNOP` must be inserted between
them. The framework tracks this automatically.

```python
class SfpuScoreboard:
    # last_writer[LReg] = instruction index that last wrote LReg
    def issue(self, instr):
        for src in instr.srcs:
            if src in self.last_writer:
                if self.last_writer[src] == self.count - 1:
                    self.emit(TTSFPNOP)        # auto-insert
        self.emit(instr)
        for dst in instr.dsts:
            self.last_writer[dst] = self.count
        self.count += 1
```

Independent chains (loads into different regs, stores, `TTSFPLOADI` sequences)
do not trigger NOPs. The author writes logical sequences and the framework
inserts NOPs where needed.

### API

```python
# Load a float32 constant into a lane register (2× TTSFPLOADI)
k.sfpu.load_float(reg, value)

# Load from / store to Dst tile
k.sfpu.load(reg, offset)
k.sfpu.store(reg, offset)

# Arithmetic (NOPs auto-inserted)
k.sfpu.mul(a, b, into=c)
k.sfpu.add(a, b, into=c)
k.sfpu.mad(a, b, c, into=d)          # d = a*b + c
k.sfpu.mov(src, into=dst)

# Lane operations
k.sfpu.shft2(reg, amount=3)           # cyclic lane rotate
k.sfpu.transp()                       # transpose 4 row-groups
k.sfpu.swap(a, b)                     # max(a,b) -> a, min -> b (for online softmax)

# Higher-level primitives (expand to instruction sequences)
k.sfpu.sum_lanes(reg)                 # 32-lane butterfly reduction -> broadcast
k.sfpu.rsqrt(reg)                     # Newton-Raphson reciprocal sqrt
k.sfpu.exp(reg)                       # polynomial exp
k.sfpu.reciprocal(reg)                # polynomial reciprocal
k.sfpu.neg(reg, into=reg)
k.sfpu.round_bf16(reg)                # rounding store to BF16

# Tile selection (automated — see Dst state machine)
# The author does NOT call _configure_dst or stall(SFPU, MATH) manually.

# MOP replay for repeated per-face operations
k.sfpu.map(program, tile=0, faces=4, iterations=8)
# Framework: loads program into replay SRAM, emits TTREPLAY + TTMOP,
#            emits TTSETRWC, inserts stall(SYNC, MATH|SFPU)
```

### Butterfly reduction — one primitive, not inlined

```python
def k.sfpu.sum_lanes(reg):
    """Reduce 32 lanes of `reg` into a broadcast value in `reg`."""
    # Stage 1: reduce within each 8-lane subgroup (rotations 4, 2, 1)
    for rotations in (4, 2, 1):
        k.sfpu.mov(reg, into=tmp)
        for _ in range(rotations):
            k.sfpu.shft2(tmp, amount=3)
        k.sfpu.add(reg, tmp, into=reg)
    # Stage 2: reduce across 4 row subgroups via transpose
    k.sfpu.mov(reg, into=L1)
    k.sfpu.mov(reg, into=L2)
    k.sfpu.mov(reg, into=L3)
    k.sfpu.transp()
    k.sfpu.add(reg, L1, into=reg)
    k.sfpu.add(reg, L2, into=reg)
    k.sfpu.add(reg, L3, into=reg)
```

Used in: RMSNorm (`_rms_finalize_scale`), dot product (`_dot_finalize`),
GQA online softmax sum. Currently copy-pasted 3× in llama3.py.

---

## Packer (`ttk/pack.py`)

### API

```python
# Pack one Dst tile to CB
k.pack(dst=0, cb=output_cb)

# Pack multiple Dst tiles to CB
k.pack_tiles(dsts=(1, 2), cb=output_cb)

# Pack with Dst retention (for GQA-style persistent accumulators)
k.pack(dst=0, cb=p_cb, retain=True)
# Framework emits: sem_wait(MATH_PACK, STALL_ON_ZERO, TDMA)
#                   _move_acquired(cb, 0, retain=True)
#                   sem_get(MATH_PACK)

# Pack a scalar (single element from Dst tile 0)
k.pack_scalar(cb=scalar_cb, dst=0)
```

The framework handles `TTPACR` config, `publish()` calls, and semaphore
management automatically based on the Dst tile state machine.

---

## Sync — the core problem

### Three levels of synchronization

```
Level 1: Intra-core      — Dst tile ownership between unpack/fpu/sfpu/pack
Level 2: Cross-core       — producer/consumer CBs, reductions, broadcasts
Level 3: Cross-kernel     — host CQ barriers between Program launches
```

### Level 1: Intra-core — Dst tile state machine (fully automated)

Each Dst tile has a state. The framework tracks transitions and inserts
barriers automatically. The author never calls `stall()`, `publish()`,
`sem_wait()`, or `sem_get()`.

```
States:  FREE → UNPACKING → MATH → SFPU → PACKING → FREE
                                                ↘ RETAINED → MATH (next iteration) → ...
```

| Transition | Barrier inserted |
|---|---|
| UNPACKING → MATH | none (hardware: FPU stalls on unpack) |
| MATH → SFPU | `TTSTALLWAIT(SFPU, MATH)` — wait for FPU to finish writing Dst |
| SFPU → MATH | `TTSTALLWAIT(SYNC, MATH\|SFPU)` — full barrier |
| SFPU → PACKING | `publish()` — signal packer Dst is ready |
| PACKING → FREE | none (packer releases Dst) |
| PACKING → RETAINED | `sem_wait` + `_move_acquired(retain=True)` + `sem_get` |
| RETAINED → MATH | none (math already holds Dst) |

### API — tile context manager

```python
# Standard tile lifecycle: unpack → fpu → sfpu → pack → release
with k.tile(dst=0) as t:
    t.unpack(cb_in, target="A")
    t.unpack(cb_w, target="B")
    t.fpu.binary("mul")
    t.sfpu.mul(t.reg("x"), scale, into=t.reg("x"))
    t.pack(cb_out)

# Persistent accumulator (GQA online softmax)
with k.tile(dst=1, retain=True) as acc:
    acc.fpu.zero()
    for block in range(kv_blocks):
        acc.fpu.matmul(accumulate=True)
        acc.sfpu.online_update(...)
        acc.pack(cb_p, retain=True)       # pack P, keep Dst1 alive
    acc.pack(cb_ctx)                       # final pack, release Dst1
```

The framework validates that you don't write a tile you don't own, and that
you don't read a tile that's being packed.

### Level 2: Cross-core — within a single Program

Cross-core sync within a kernel uses three patterns. Each is a ttk primitive
that generates NoC transactions + L1 semaphores automatically.

#### Pattern A: Remote CB (producer on core A, consumer on core B)

One core produces data that another core needs. Instead of a DRAM round-trip,
the producer writes directly into the consumer's CB via NoC.

```python
# Producer side (core A):
k.noc.send_to_cb(cb_local, dst_core=consumer_core, dst_cb_addr, count)

# Consumer side (core B):
# The CB wait_front / pop_front already handles this — the producer's NoC
# write increments the CB's push counter via atomic_inc.
k.unpack(cb, target="A")   # automatically waits for remote producer
```

Under the hood: producer does `noc.write(local_l1, consumer_l1, consumer_coord,
count*itemsize)` + `noc.atomic_inc(consumer_cb_push_counter, consumer_coord)`.
Consumer's CB layer polls the push counter (same as a local push_back).

#### Pattern B: Reduction (all cores → root core)

Partial results from all cores are combined on a root core.

```python
# Every core:
k.reduce(root=core_0, op="max" | "sum" | "argmax",
         src=local_result_l1, src_count=n,
         dst=partials_l1_on_root, dst_stride=slot_size)
# Framework emits:
#   noc.write(local_result, root_partials + core_index * stride, root_coord, ...)
#   noc.atomic_inc(root_ready_flag + core_index, root_coord, 1)

# Root core additionally:
k.reduce_finalize(root=core_0, op="max" | "sum" | "argmax",
                  partials=partials_l1, n_cores=117,
                  dst=output_l1)
# Framework emits:
#   for each core: poll ready_flag, read partial, combine
```

This is exactly the argmax pattern in llama3.py (lines 580–626), abstracted.

#### Pattern C: Broadcast (root core → all cores)

Root core sends the same data to all cores.

```python
# Root core:
k.broadcast(src=runtime_l1, dst_addr=target_l1_on_all_cores,
            cores=all_cores, count=n)
# Framework emits:
#   noc.multicast_write(src, dst, mcast_start, mcast_end, count*itemsize)
```

This is the argmax runtime-state multicast in llama3.py (lines 680–684).

### When does cross-core sync happen?

The framework needs to know **which cores depend on each other**. Two sources:

1. **Explicit declaration** (for hand-written kernels like llama3):

```python
p = Program(cores, ...)
p.reduce(root=cores[0], op="argmax", ...)   # declares cross-core dependency
p.broadcast(src=..., cores=cores, ...)       # declares cross-core dependency
```

2. **Derived from the IR** (for tinygrad lowering — see below):

The tinygrad renderer knows the full DAG. If op B consumes op A's output and
they're scheduled on different cores in the same Program, the framework
inserts a remote CB transfer. If they're in different Programs, it's a DRAM
round-trip (Level 3).

### Level 3: Cross-kernel — host CQ barriers (already done)

Each `Program` launch is atomic: the host CQ ensures all cores complete before
the next Program starts. This is the existing `device.queue(program)` +
`device.run()` model in `device.py`. No change needed.

Between kernels, data flows through DRAM. The NoC write in kernel A must
complete before kernel B's NoC read — this is guaranteed by the CQ barrier.

---

## MOP automation (`ttk/mop.py`)

### Problem

The current code manually hardcodes replay buffer loads (`_configure_replay_mop`,
`_run_faces`). This is fragile and opaque.

### Solution

The framework detects repeated instruction sequences and collapses them into
`TTMOP` + replay buffer loads.

```python
# Author writes a loop:
with k.tile(dst=0) as t:
    for i in range(8):
        t.unpack(cb_in, target="A", rows=16, cols=16)
        t.unpack(cb_w, target="B", rows=16, cols=16)
        t.fpu.binary("mul")
        t.pack(cb_out)

# Framework detects: 8 iterations of (unpack, unpack, fpu, pack)
# Checks: does the body fit in replay SRAM? (~8 instructions for TRISC)
# If yes: emits TTREPLAY load + TTMOP(loop_count=8) + TTINCRWC
# If no:  falls back to RISC-V loop (asm.py's range/loop)
```

### Replay body construction

The replay body must include `TTINCRWC` (counter increment) so each iteration
advances CB/Dst pointers. The framework inserts this automatically. The body
is loaded into replay SRAM via `TTREPLAY` config, then one `TTMOP` triggers
N hardware iterations.

### Detection rules

1. The loop body must be a fixed sequence of Tensix instructions (no branches).
2. The loop count must be known at codegen time (constant or kernarg).
3. The body must fit in the replay buffer (~8 instructions).
4. The only side effect between iterations is counter increments (CB/Dst
   pointers advancing).

If any condition fails, fall back to a RISC-V loop. No correctness impact —
just a performance difference.

---

## Expected lowering — tinygrad integration

### Two-phase lowering

```
tinygrad UOp DAG
       │
       ▼  (Phase 1: isel — in tinygrad/renderer/isa/tensix.py)
TensixOps IR (linear Ops.INS sequence)
       │
       ▼  (Phase 2: codegen — in ttk/codegen.py)
Multi-thread binary (BRISC + TRISC0 + TRISC1 + TRISC2 + NCRISC)
```

### Phase 1: tinygrad UOps → TensixOps IR

Define a `TensixOps` enum as the IR. isel matchers lower UOps to `Ops.INS`
nodes with `TensixOps` args:

```python
class TensixOps(FastEnum):
    NOC_READ    = auto()   # DRAM → L1/CB
    NOC_WRITE   = auto()   # L1/CB → DRAM
    UNPACK      = auto()   # CB/L1 → SrcA/SrcB
    FPU_ELTWISE = auto()   # TTELWMUL / TTELWADD
    FPU_MATMUL  = auto()   # TTMVMUL
    FPU_COPY    = auto()   # copy SrcA → Dst
    SFPU_OP     = auto()   # SFPU operation (exp, rsqrt, mul, add, ...)
    SFPU_REDUCE = auto()   # 32-lane butterfly reduce
    PACK        = auto()   # Dst → CB
    SYNC        = auto()   # barrier (derived, not explicit in UOps)
```

isel matchers:

```python
# Mul(a, b) → FPU_ELTWISE(op=mul, dst=auto, src_a=..., src_b=...)
# Add(a, b) → FPU_ELTWISE(op=add, ...)
# Reduce(Sum, axis) → FPU_ELTWISE(op=mul, src_b=1) + SFPU_REDUCE
# WMMA(a, b) → FPU_MATMUL
# Load(buf) → NOC_READ + UNPACK
# Store(buf) → PACK + NOC_WRITE
```

Each `Ops.INS` node carries metadata: CB id, Dst tile, row/col range, dtype.
The sequence is linear and single-threaded but explicit about data movement.

### Phase 2: TensixOps → multi-thread binary (ttk/codegen.py)

The codegen takes the linear IR and splits it across threads:

| TensixOps | Thread | Notes |
|---|---|---|
| NOC_READ | BRISC | pushes into CB |
| UNPACK | TRISC0 | consumes from CB, writes SrcA/SrcB |
| FPU_* | TRISC1 | reads SrcA/SrcB, writes Dst |
| SFPU_* | TRISC1 | reads/writes Dst (same thread as FPU) |
| PACK | TRISC2 | reads Dst, pushes into CB |
| NOC_WRITE | NCRISC | consumes from CB |

Sync insertion rules (mechanical, derived from data dependencies):

1. **FPU after UNPACK on same tile** — no sync (hardware stalls FPU on unpack).
2. **SFPU after FPU on same Dst tile** — insert `stall(SFPU, MATH)`.
3. **FPU after SFPU on same Dst tile** — insert `stall(SYNC, MATH|SFPU)`.
4. **PACK after FPU/SFPU on same Dst tile** — insert `publish()`.
5. **PACK with retain** — insert `sem_wait` + `_move_acquired(retain=True)` + `sem_get`.
6. **UNPACK after PACK released the tile** — no sync (tile is FREE).
7. **NOC_READ before UNPACK** — CB wait_front (automated by CB layer).
8. **PACK before NOC_WRITE** — CB wait_front (automated by CB layer).

The codegen builds a Dst tile dependency graph from the IR, determines the
state machine transitions, and inserts the right barriers. No human judgment
required.

### Cross-core sync in the IR

When tinygrad's scheduler assigns different ops to different cores within the
same Program, the IR includes cross-core data flow:

```python
# Core A produces, core B consumes — same Program
TensixOps.NOC_READ(...)     # core A: DRAM → CB_A
TensixOps.UNPACK(...)       # core A: CB_A → SrcA
TensixOps.FPU_ELTWISE(...)  # core A: SrcA × SrcB → Dst
TensixOps.PACK(...)         # core A: Dst → CB_A
# --- cross-core transfer ---
TensixOps.REMOTE_SEND(...)  # core A: CB_A → core B's CB_B (via NoC)
TensixOps.UNPACK(...)       # core B: CB_B → SrcA
TensixOps.FPU_ELTWISE(...)  # core B: ...
```

The codegen detects `REMOTE_SEND` and emits the NoC write + atomic_inc pattern.
The consumer's CB layer automatically waits for the remote push.

When ops are in different Programs, data flows through DRAM and the CQ barrier
handles sync (Level 3).

### Custom kernels (GQA, fused attention)

For ops that don't map to standard UOps (online softmax, persistent
accumulators), two options:

1. **Hand-written via ttk directly** — call `k.tile(dst=1, retain=True)`,
   `k.sfpu.sum_lanes()`, etc. The framework still handles sync.
2. **Fused op in the IR** — define `TensixOps.FUSED_ATTENTION` with a known
   expansion. The codegen has a pattern match for it. Better for tinygrad's
   optimizer (single DAG node).

Option 1 is the path for the llama3 port. Option 2 comes later.

---

## Hardware semaphores (`ttk/sync.py`)

The Tensix has 8 hardware semaphores per core. The framework manages them
internally — the author never touches semaphore indices.

### Semaphore allocation

```python
class SemaphoreAllocator:
    # 8 semaphores per core, reference-counted
    sems: list[set[int]]  # per-core free set

    def acquire(self, core, name) -> int: ...
    def release(self, core, sem_id) -> None: ...
```

### Named semaphores

The framework uses named semaphores internally:

| Name | Purpose | Used by |
|---|---|---|
| `MATH_PACK` | Dst tile handoff (math → pack) | Dst state machine |
| `CB_PUSH_{N}` | CB push counter (for remote CBs) | CB layer |
| `REDUCE_READY_{N}` | Reduction partial ready flag | reduce.py |
| `CUSTOM_{N}` | User-defined semaphores (if needed) | explicit |

The author never calls `TTSEMINIT`, `TTSEMPOST`, `TTSEMWAIT`, `TTSEMGET`
directly. These are all framework-internal.

---

## What the kernel author writes (llama3 port example)

```python
def rmsnorm_rowmajor(x, weight, output):
    p = Program(x.cores, x, weight, output, fp32_dst=True)
    cb_x = p.cb(BF16, element_count=2048)        # full embedding
    cb_out = p.cb(BF16, element_count=2048)
    gamma_l1 = p.l1(2048 * 2, alignment=16)      # BF16 gamma weights

    # BRISC: read gamma into L1, read x into CB
    p.brisc.noc.read_to_cb(weight, 0, gamma_l1)   # not a CB, raw L1
    p.brisc.noc.read_to_cb(x, 0, cb_x)

    # TRISC0: unpack x and gamma into SrcA/SrcB
    p.unpack(cb_x, target="A", rows=64, cols=16)  # 64 rows × 16 elements
    p.unpack_l1(gamma_l1, BF16, target="B")

    # TRISC1: copy SrcA to Dst, then SFPU normalize
    with p.tile(dst=0) as t:
        t.fpu.copy_a(rows=64, cols=16)
        # SFPU: square, sum, rsqrt, scale by gamma
        t.sfpu.square_and_accumulate(reset=True)   # L7 = sum(x^2)
        t.sfpu.sum_lanes(L7)                        # broadcast sum
        t.sfpu.rsqrt(L7)                            # L0 = 1/sqrt(mean+eps)
        t.sfpu.apply_scale_gamma()                  # Dst = x * gamma * L0
        t.pack(cb_out)

    # NCRISC: write CB to DRAM
    p.ncrisc.noc.write_from_cb(cb_out, output, 0)
    return p
```

No `stall()`, no `publish()`, no `sem_wait()`, no `CB.reserve_back()`, no
`TTSFPNOP`, no `_configure_dst`, no `_bf16_tile_byte_offset`. The framework
handles all of it.

---

## Implementation order

1. **`ttk/cb.py`** — byte-based CBs with auto pointer management
2. **`ttk/sync.py`** — Dst tile state machine + semaphore allocator
3. **`ttk/sfpu.py`** — NOP scoreboard + load_float + butterfly + rsqrt/exp/reciprocal
4. **`ttk/fpu.py`** — binary/matmul/copy_a with SETADC granularity
5. **`ttk/unpack.py`** — row-major stride config + CB/L1 sources
6. **`ttk/pack.py`** — pack/pack_tiles/pack_scalar with retain
7. **`ttk/mop.py`** — replay detection and generation
8. **`ttk/reduce.py`** — cross-core reduce/broadcast/send_to_cb
9. **`ttk/codegen.py`** — Program builder, thread splitting, IR lowering
10. Port llama3 to row-major using ttk
11. tinygrad `renderer/isa/tensix.py` — Phase 1 isel
12. tinygrad backend — Phase 2 codegen integration

---

## Open questions

1. **Overlay streams** — current approach (BRISC/NCRISC do NoC, TRISC does
   compute) works. Overlay streams would overlap NoC and compute on the same
   thread, but add complexity. Defer until profiling shows it's needed.

2. **SFPU macro backdoor** — the RMSNorm macro (multiply-by-L0 template) is a
   hardware feature exposed as raw config writes. Should the framework expose
   this, or hide it behind `sfpu.apply_scale_gamma()`? Lean toward hiding.

3. **MOP for SFPU** — SFPU replay is more complex than TRISC replay (faces,
   iterations, `TTSETRWC`). The `sfpu.map()` API abstracts this, but the
   detection rules may need tuning.

4. **tinygrad scheduler** — how does tinygrad decide which ops fuse into one
   Program vs. separate Programs? This affects whether we use remote CBs
   (fast, same Program) or DRAM round-trips (slower, separate Programs).
   Need to understand tinygrad's fusion rules.

5. **Dst tile count** — 16 Dst tiles. GQA uses 6 (O×2, m, l, alpha, scores).
   The framework needs to track Dst tile allocation across the full Program
   to avoid running out. This is a register-allocation problem.
