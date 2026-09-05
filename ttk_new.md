# TTK hardware API

Status: implementation specification

## Contract

TTK is a procedural API for building Blackhole worker instruction streams. The
caller selects one Tensix core and one of BRISC, NCRISC, TRISC0, TRISC1, or
TRISC2, then calls TTK functions in program order. The five ordered streams are
retained until tile-local synchronization has been lowered.

TTK contains hardware views, instruction configuration, instruction issue,
Dst leases, CB address calculations, MOP/Replay, static validation, and typed
resource effects for tile-local synchronization.

TTK does not contain a general compute DAG, core placement, global scheduling,
or cross-core synchronization. It does not expose physical synchronization in
the public API. In particular, TTK calls must not directly emit:

- `TTSTALLWAIT`, `TTSTREAMWAIT`, semaphores, or mutex operations;
- CB reserve/wait/push/pop or CB counter updates;
- NoC completion waits or command-slot polling;
- physical barriers, ownership transfer, publication, or cross-RISC
  handshakes.

Each TTK call records its executor, ordered resource uses, and required
completion point before instruction encoding. A tile-synchronization pass
inserts the operations above from those semantic effects. It must not discover
dependencies by scanning generated instructions. Required SFPU dependency NOPs
are allowed because they are part of one local instruction sequence, not a
cross-engine handshake.

## Common types

```python
Value = int | R
Coordinate = tuple[Value, Value]

class DType(Enum):
    BF16; FP16; FP32; TF32
    INT8; UINT8; INT16; UINT16; INT32; UINT32
    BFP2; BFP4; BFP8; RAW

class Layout(Enum):
    ROW_MAJOR; FACE_TILIZED; SCALAR; BLOCK

class Rounding(Enum):
    NONE; TRUNCATE; RNE; STOCHASTIC

class Fidelity(Enum):
    LOFI; HIFI2; HIFI3; HIFI4

class Broadcast(Enum):
    NONE; ROW; COLUMN; SCALAR; MVMUL_ROW

class DstMode(Enum):
    FP32; B16

class DstSection(Enum):
    FULL; LOW; HIGH
```

Only expose formats and fidelity modes whose Blackhole encodings are verified.
Each `DType` records its storage size, legal routes, accumulator format,
rounding, saturation, and block-exponent layout.

## Views

`Value` parameters may be immediates or RISC registers. Constructors validate
alignment, extent, format, layout, and native hardware footprint.

```python
BufferView(buffer: Buffer, byte_offset: Value = 0, bytes: Value | None = None)
L1(address: Value, dtype: DType, elements: Value, layout=ROW_MAJOR,
   element_offset: Value = 0, strides: tuple[Value, ...] = ())
RemoteL1(local: L1, core: Coordinate)
SrcA(dtype: DType, row: int = 0, column: int = 0, elements: int = 1024)
SrcB(dtype: DType, row: int = 0, column: int = 0, elements: int = 1024)
LRegView(register: int, lane_offset: int = 0, lanes: int = 32)
```

## Tile-local synchronization

This section covers the five RISCs and Tensix engines on one core. Cross-core,
cross-device, and collective ordering are deliberately out of scope for now.
Firmware launch and join are also outside TTK: firmware releases the four
subordinate RISCs at kernel start and BRISC joins them at kernel return.

The program owns five ordered operation streams. Every operation carries
compiler-internal effects over logical resources; these are not hardware
semaphore numbers or encoded wait masks:

```python
ResourceUse(resource, access, completion)

class Access(Enum):
    READ; WRITE; ACQUIRE; RELEASE; PRODUCE; CONSUME

class Completion(Enum):
    ISSUED
    SOURCE_CONSUMED
    ENGINE_DONE
    VISIBLE
```

The tracked resources are:

- each CB's space credits, data credits, and ring generation;
- SrcA and SrcB free/valid generations;
- Dst lease versions, snapshot readiness, and snapshot acknowledgement;
- unpack, math, SFPU, pack, configuration, PC, MOP, and Replay engine state;
- NoC TID and source/remote completion state.

Normal dependencies come from typed operands. A move into a `CBWrite` produces
CB data; a move from a `CBRead` consumes it; unpack produces a Src generation;
FPU consumes it; FPU/SFPU produces a Dst version; and pack consumes a snapshot
of that version. A named tile event is allowed only for an ordering edge not
represented by a payload view, such as the row-major Llama kernels publishing
that persistent L1 data is ready. The event is logical: lowering may initially
implement it with a one-credit CB counter, but the program must not name that
implementation.

Current Llama kernels require these tile-local protocols:

| Producer | Consumer | Logical handoff | Current mechanism |
| --- | --- | --- | --- |
| BRISC | TRISC0 | input payload or persistent-L1 readiness | CB received/acked counters |
| TRISC0/unpack | TRISC1/math | SrcA/SrcB generation | source clear/valid scoreboard waits |
| TRISC1 math/SFPU | TRISC2/pack | Dst snapshot and acknowledgement | `MATH_PACK` semaphore |
| TRISC2/pack | NCRISC | packed output payload | CB received/acked counters |
| BRISC | NCRISC | persistent-L1 readiness in row-major kernels | one-credit CB event |

GQA additionally publishes Dst0 once per block for two retained probability
snapshots, waits for TRISC2 to acknowledge them, and continues accumulating in
Dst1-Dst5. Its final context snapshot releases ordinary full-Dst ownership.
This loop-carried snapshot/acknowledgement must be represented explicitly in
the Dst version model; it must not be reconstructed from adjacent pack and
math instructions.

Tile synchronization lowering performs these steps while loops and branches
are still structured:

1. Preserve program order within each RISC and version every logical resource.
2. Bind each CB producer and consumer, and verify single-producer/
   single-consumer use, balanced static rates, capacity, and Dst lifetimes.
3. Add acquire/release edges for hazards and explicit named tile events.
4. Select Blackhole protocols and allocate physical CB counters and semaphore
   slots.
5. Insert waits, completion drains, publications, and acknowledgements, then
   encode instructions.

The Blackhole protocol selection is target lowering. The existence and meaning
of an edge is an IR property. No synchronization pass may inspect encoded
instruction words or depend on incidental instruction adjacency.

`syncs.md` is the normative Blackhole protocol catalogue. TTK operations must
not restate those sequences ad hoc. Each operation produces a record with
enough information to select one of its named protocols:

```python
Operation(
    executor: Risc,
    setup: tuple[HardwareOp, ...],
    issue: tuple[HardwareOp, ...],
    requires: tuple[ResourceUse, ...],
    produces: tuple[ResourceUse, ...],
    releases: tuple[ResourceUse, ...],
    protocol: Protocol,
)
```

`setup` and `issue` remain typed until protocol expansion. This lets lowering
place a `TRISC_CFG` stall between unpack configuration and `UNPACR`, for
example; one opaque blob of already encoded words would be too late.

### Operation emission contract

TTK records the following for each operation family. The protocol expander,
not the public function, emits the waits and handoffs in the final column.

| operation family | TTK records | protocol expansion emits |
| --- | --- | --- |
| views, CB allocation, Dst lease | shape, address, layout, ownership and lifetime metadata | no instructions |
| RISC load/store/copy/fill/gather/scatter | ordered L1 reads/writes and exact byte ranges | RISC instructions; a fence only at a publication/MMIO boundary that requires it |
| DMA-register arithmetic/atomics | register inputs, outputs, widths, and local-memory effects | DMA-register instructions and required local ordering |
| NoC read | NIU, TID, endpoints, destination range, packet shape, and remote-completion result | command-slot/TID capacity waits, command setup/issue, and response drain before L1 visibility |
| NoC write/atomic | NIU, TID, source range, endpoints, posted policy, source-completion and optional remote-completion results | command-slot/TID waits, setup/issue, source drain before reuse, and remote drain when requested |
| produce a CB item | CB generation/count plus the operation that fills its window | reserve space before fill; wait for fill completion; publish received count |
| consume a CB item | CB generation/count plus the operation that reads its window | wait for data before read; wait until source is no longer used; publish acknowledged count |
| unpack to SrcA/SrcB | context, formats, descriptors, address/stride/ADC state, destination banks, and issue macro | wait for CB data and Src clear; acquire/commit context; configuration stall; issue/drain; release context and CB; produce Src valid |
| unpack directly to Dst | complete two-sided Dst mailbox protocol and per-face issue sequence | reject for now; when enabled, expand the empirical protocol in `syncs.md`, including every per-face `UNPACK0` drain |
| FPU | source generations and final-use policy, Dst footprint/version, define versus accumulate, mode, fidelity, address modifiers, counters, and issue macro | acquire Dst region; wait for Src valid; configure/issue; clear Src only on declared final use; drain at the first dependent reader or publication |
| SFPU | Dst/LReg reads and writes, Dst ownership region, lane config, Replay/MOP use, and fixed LReg latencies | wait for prior math when needed; configure/issue; insert static hazard NOPs; drain at the first dependent reader or publication |
| Dst snapshot | exact defined Dst version/views and retain/release policy | drain Dst writers; post `MATH_PACK`; create an acknowledgement edge back to the next mutation of a retained view |
| pack | snapshot read, output range/CB generation, formats, masks, strides, counters, destination, and retain/release policy | wait `MATH_PACK`; reserve output; drain old config users; configure/issue; drain `PACK0`/PC; publish output CB; acknowledge snapshot; clear Dst only on explicit release |
| MOP/Replay configure or run | template/slot ranges, users, expansion boundaries, and tested split points | PC/MOP synchronization before overwrite and the validated load/play sequence |
| shared configuration RMW | exact register fields and engines that may observe them | relevant engine drains and, where required, the assigned configuration mutex |
| kernel return | all live TIDs, CB items, contexts, source generations, Dst snapshots, engines, and mutexes | reject an unbalanced stream or emit only the documented final drains before returning to firmware |

For FPU source release, pack Dst clearing, Dst snapshot acknowledgement, and
NoC source completion, the operation record must say what is released. The
lowerer must not guess from the end of a helper or from the opcode selected
later. Conversely, engine drains may be delayed to the first dependent use and
coalesced when the operation records prove that this preserves the protocol.

## Circular buffers

A `CB` is an L1 ring description. A `CBRead` or `CBWrite` is a payload window;
it is not a reservation and does not assert that data or space is available.

```python
CB(id: int, dtype: DType, item_bytes: int, depth: int, address: Value,
   layout: Layout, alignment: int = 16, symmetric: bool = False)
CBRead(cb: CB, item: Value, items: Value = 1,
       valid_bytes: Value | None = None)
CBWrite(cb: CB, item: Value, items: Value = 1,
        valid_bytes: Value | None = None)
RemoteCBRead(local: CBRead, core: Coordinate)
RemoteCBWrite(local: CBWrite, cores: tuple[Coordinate, ...],
              multicast: bool = False)
```

Implement these creation and view functions:

```python
class CBRegistry:
    def create(self, dtype, item_bytes, depth, *, id=None, address=None,
               alignment=16, layout=FACE_TILIZED, symmetric=False) -> CB
    def internal(self, name, dtype, item_bytes, depth, *, id=None,
                 address=None, alignment=16, layout=FACE_TILIZED,
                 symmetric=False, lifetime=None) -> CB
    def bind(self, id, address, dtype, item_bytes, depth, *, alignment=16,
             layout=FACE_TILIZED, symmetric=False) -> CB
    def read(self, cb, item, items=1, *, valid_bytes=None) -> CBRead
    def write(self, cb, item, items=1, *, valid_bytes=None) -> CBWrite
    def remote_read(self, source, core) -> RemoteCBRead
    def remote_write(self, destination, cores, *, multicast=False) -> RemoteCBWrite
```

`create` allocates from the program L1 allocator when `address` is omitted.
`internal` is a named, reusable allocation for TTK routines. `bind` accepts a
runtime address. None of them initializes queue counters.

Windows may wrap; lowering splits them into contiguous payload commands.
Multicast requires the same CB address, shape, item, and ring generation at all
receivers. TTK checks the static properties. For a tile-local CB, the resource
effect tracker establishes the ring generation and lowering reserves, waits,
publishes, and acknowledges it. Remote publication is deferred with the rest of
cross-core synchronization.

## Movement

Use one operation for typed payload movement:

```python
def move(
    src: BufferView | L1 | RemoteL1 | CBRead | RemoteCBRead |
         SrcA | SrcB | DstView | LRegView,
    dst: BufferView | L1 | RemoteL1 | CBWrite | RemoteCBWrite |
         SrcA | SrcB | DstView | LRegView,
    *,
    elements: Value | None = None,
    bytes: Value | None = None,
    options: MoveOptions | None = None,
) -> Operation
```

At most one of `elements` and `bytes` is supplied. If neither is supplied, use
the source extent. The endpoint pair selects the engine:

| Source | Destination | Route |
| --- | --- | --- |
| `BufferView` | `L1`, `CBWrite` | NoC read |
| `L1`, `CBRead` | `BufferView` | NoC write |
| `L1`, `CBRead` | `RemoteL1`, `RemoteCBWrite` | NoC write/multicast |
| `RemoteL1`, `RemoteCBRead` | `L1`, `CBWrite` | NoC read |
| `L1`, `CBRead` | `L1`, `CBWrite` | local copy |
| `L1`, `CBRead` | `SrcA`, `SrcB`, `DstView` | unpack |
| `DstView` | `L1`, `CBWrite` | pack |
| `SrcA`, `SrcB`, `DstView` | `SrcA`, `SrcB`, `DstView` | FPU move |
| `DstView` | `LRegView` | SFPU load |
| `LRegView` | `DstView` | SFPU store |

`CBRead -> RemoteCBWrite` is the required core-to-core CB transfer. It copies
only payload. The later layer reserves the receiver, supplies the window,
waits for NoC completion, and publishes the receiver CB.

Movement options are plain data:

```python
LocalCopyOptions(allow_overlap: bool = False)
NocOptions(noc: int, tid: int, posted: bool = False,
           source_middle: Value = 0, target_middle: Value = 0,
           burst_bytes: int | None = None)
UnpackOptions(context: int, input_dtype=None, output_dtype=None,
              transpose=False, tilize=False, x_dim=None, strides=(), fill=None)
PackOptions(output_dtype: DType, layout: Layout, rounding=NONE,
            edge_mask=None, row_mask=None, strides=(), l1_accumulate=False)
FpuMoveOptions(broadcast=NONE, transpose=False, clear_source=True)
SfpuMoveOptions(dtype: DType, lane_mask: int = 0xFFFFFFFF)
```

One `move` records configuration, payload issue, and typed resource effects. It
does not itself wait, change CB counters, publish Dst, or clear Dst. Tile sync
lowering places those operations at the completion points required by its
effects.

## NoC

`move` is the normal payload API. Also expose the command-level API:

```python
class NoC:
    def dram_address(self, buffer, byte_offset) -> tuple[Value, Coordinate]
    def read(self, source_address, source_core, target_l1, bytes, *, noc, tid,
             source_middle=0) -> None
    def write(self, source_l1, target_address, target_core, bytes, *, noc, tid,
              posted=False, target_middle=0) -> None
    def multicast_write(self, source_l1, target_address, target_cores, bytes,
                        *, noc, tid, posted=False, target_middle=0) -> None
    def inline_write(self, value, target_address, target_core, *, noc, tid,
                     posted=False, target_middle=0) -> None
    def atomic_inc(self, target_address, target_core, value=1, *, noc, tid,
                   wrap=0, target_middle=0) -> None
```

Add a typed method for every other verified NoC atomic. These methods only
program and issue commands. TID ownership and completion are external.

## Local memory and DMA registers

```python
element_address(base, index, *, dtype, layout, shape=(), strides=()) -> Value
load(address, *, dtype) -> Value
store(address, value, *, dtype) -> None
copy(src, dst, bytes, *, allow_overlap=False) -> None
fill(dst, value, bytes, *, dtype=UINT8) -> None
gather(src, indices, dst, count, *, dtype, strides=()) -> None
scatter(src, dst, indices, count, *, dtype, strides=()) -> None

class DmaRegs:
    def add(self, a, b, out, *, b_is_constant=False) -> None
    def sub(self, a, b, out, *, b_is_constant=False) -> None
    def mul(self, a, b, out, *, b_is_constant=False) -> None
    def compare(self, op, a, b, out, *, b_is_constant=False) -> None
    def bitwise(self, op, a, b, out, *, b_is_constant=False) -> None
    def shift(self, op, a, b, out, *, b_is_constant=False) -> None
    def load_indirect(self, address_reg, data_reg, *, size, offset_reg=None,
                      auto_increment=False) -> None
    def store_indirect(self, address_reg, data_reg, *, size, offset_reg=None,
                       auto_increment=False) -> None
    def atomic_cas(self, address_reg, compare, swap, out, *, bits=32) -> None
    def atomic_inc_get(self, address_reg, increment, out, *, wrap=0,
                       bits=32) -> None
    def atomic_swap(self, address_reg, value, out, *, mask=None) -> None
```

Support 1-, 2-, and 4-byte accesses, runtime strides, dense and face-tilized
indexing, and exact tails.

## Dst

```python
DstView(lease: DstLease, tile: int, element_offset: int = 0,
        elements: int = 1024)

class DstAllocator:
    def lease(self, mode, *, tiles, section=FULL) -> DstLease

class DstLease:
    def view(self, tile, *, element_offset=0, elements=1024) -> DstView
    def mark_defined(self, view) -> None
    def mark_undefined(self, view) -> None
    def snapshot(self, views, *, retain=True) -> DstSnapshot
    def release(self) -> None
```

FP32 mode has eight logical tiles; B16 mode has sixteen. Leases are compile-time
bookkeeping only. `snapshot` creates a logical TRISC1-to-TRISC2 versioned
handoff; it emits nothing directly. `retain=True` requires an acknowledgement
before the producer may mutate a snapshotted view, while keeping the remaining
Dst state live. `release` emits nothing. Packing never clears Dst implicitly.
Explicit Dst retention and repeated snapshots are required by GQA, online
softmax, and FlashAttention.

## FPU

All methods configure and issue instructions but emit no waits or publication:

```python
class Fpu:
    def clear(self, dst: DstView) -> None
    def add(self, a, b, dst, *, accumulate=False, broadcast=NONE,
            clear_sources=True) -> None
    def sub(self, a, b, dst, *, accumulate=False, broadcast=NONE,
            clear_sources=True) -> None
    def mul(self, a, b, dst, *, accumulate=False, broadcast=NONE,
            fidelity=HIFI2, clear_sources=True) -> None
    def mvmul(self, left, right, dst, *, accumulate=False,
              right_transpose=False, fidelity=HIFI2, clear_sources=True,
              use_mop=True) -> None
    def dotpv(self, a, b, dst, *, accumulate=False, fidelity=HIFI2,
              clear_sources=True) -> None
    def gapool(self, a, scaler, dst, *, accumulate=False, fidelity=HIFI2,
               clear_sources=True) -> None
    def gmpool(self, a, scaler, dst, *, clear_sources=True) -> None

    def reduce_row_sum(self, a, scaler, dst) -> None
    def reduce_row_max(self, a, scaler, dst) -> None
    def reduce_scalar_sum(self, a, scaler, dst) -> None
    def reduce_scalar_max(self, a, scaler, dst) -> None

    def transpose_srca(self) -> None
    def transpose_srcb(self) -> None
    def shift_srca(self, amount) -> None
    def shift_srcb(self, amount, *, rotate=False) -> None
    def zero_srca(self, *, encoding=0) -> None
    def zero_srcb(self, *, encoding=0) -> None
    def reset_source_gates(self) -> None
```

`move` exposes MOVA2D, MOVB2D, MOVD2A, MOVD2B, and MOVB2A. Add verified
POOL3/CONV3 methods only after their Blackhole behavior is tested.

## SFPU

The SFPU builder is a linear instruction builder and LReg allocator, not a DAG.
It tracks only LReg allocation and required local hazard NOPs.

```python
class SfpuProgramBuilder:
    def vec(self, name=None) -> Vec
    def persistent_vec(self, register, name=None) -> Vec
    def free(self, value) -> None

    def load(self, offset=0, *, dtype, into=None) -> Vec
    def store(self, value, offset=0, *, dtype) -> None
    def load_float(self, value, *, into=None) -> Vec
    def load_int(self, value, *, into=None) -> Vec
    def constant(self, value, *, name=None) -> Vec
    def move(self, value, *, into=None) -> Vec

    def add(self, a, b, *, into=None) -> Vec
    def sub(self, a, b, *, into=None) -> Vec
    def mul(self, a, b, *, into=None) -> Vec
    def mad(self, a, b, c, *, into=None) -> Vec
    def neg(self, value, *, into=None) -> Vec
    def abs(self, value, *, into=None) -> Vec
    def reciprocal(self, value, *, into=None) -> Vec
    def rsqrt(self, value, *, into=None) -> Vec
    def exp(self, value, *, into=None) -> Vec

    def compare(self, op, a, b) -> Predicate
    def select(self, predicate, yes, no, *, into=None) -> Vec
    def minimum(self, a, b, *, into=None) -> Vec
    def maximum(self, a, b, *, into=None) -> Vec
    def clamp(self, value, low, high, *, into=None) -> Vec

    def bit_and(self, a, b, *, into=None) -> Vec
    def bit_or(self, a, b, *, into=None) -> Vec
    def bit_xor(self, a, b, *, into=None) -> Vec
    def bit_not(self, value, *, into=None) -> Vec
    def shift(self, value, amount, *, into=None) -> Vec
    def cast(self, value, dtype, *, into=None) -> Vec
    def round(self, value, dtype, mode, *, into=None) -> Vec
    def extract_exponent(self, value, *, into=None) -> Vec
    def extract_mantissa(self, value, *, into=None) -> Vec
    def set_exponent(self, value, exponent, *, into=None) -> Vec
    def set_mantissa(self, value, mantissa, *, into=None) -> Vec
    def set_sign(self, value, sign, *, into=None) -> Vec

    def rotate_lanes(self, value, amount, *, into=None) -> Vec
    def transpose_registers(self, values) -> None
    def shuffle(self, value, pattern, *, into=None) -> Vec
    def reduce_sum(self, value, *, subgroup=32, into=None) -> Vec
    def reduce_max(self, value, *, subgroup=32, into=None) -> Vec
    def reduce_min(self, value, *, subgroup=32, into=None) -> Vec

    def lut(self, value, table, *, into=None) -> Vec
    def load_macro(self, offset, macro, *, into=None) -> Vec
    def rand_fast(self, *, into=None) -> Vec
    def finish(self) -> SfpuProgram

class Sfpu:
    def seed(self, value) -> None
    def map(self, program, dst, *, elements=None, element_offset=0,
            lane_mask=None, use_mop=True) -> None
```

The allocator covers LReg 0-7, persistent values, and constant registers
12-14. Cross-lane reductions must work on subgroups and full 32-lane rows.
`map` must cover arbitrary ranges across leased Dst tiles without publishing.

## Unpack and pack

`move` is the normal API. Expose phases so configuration can be reused:

```python
class Unpack:
    def configure(self, src, dst, options: UnpackOptions) -> None
    def issue(self, src, dst, options: UnpackOptions) -> None
    def issue_pair(self, srca, srcb, dsta, dstb, options) -> None

class Pack:
    def configure(self, src, dst, options: PackOptions) -> None
    def set_destination(self, dst) -> None
    def issue(self, src, dst, options: PackOptions) -> None
```

Unpack must support SrcA, SrcB, verified direct-to-Dst, paired/matmul input,
broadcast and reduction formation, transpose, row-major and tiled layouts,
runtime strides, format conversion, fill, and exact tails.

Pack must support FP32/B16 Dst, scalar/row/face/tile/partial ranges, row-major
and tiled output, runtime destinations and strides, conversion and rounding,
edge masks, repeated Dst snapshots, and verified L1 accumulation.

## MOP and Replay

```python
class ReplayAllocator:
    def allocate(self, length, *, lower=0, upper=32) -> Replay
    def release(self, replay) -> None

class Mop:
    def configure(self, template: LoopTemplate | MaskTemplate) -> None
    def run(self, *, count: Value = 1, mask: Value = 0) -> None
    def load_replay(self, replay, words) -> None
    def play_replay(self, replay) -> None
```

These functions do not wait for PC or MOP buffers. Keep known-safe Replay split
points for MVMUL and SFPU until FIFO limits are measured.

## Low-level coverage

High-level routines must not make a verified worker instruction inaccessible:

```python
class Config:
    def read(self, register, out) -> None
    def write(self, register, value, *, bytes=4) -> None
    def rmw(self, register, byte, mask, value) -> None
    def set_dma_reg(self, register, value, *, bits=32) -> None

class AddressCounters:
    def set(self, counter, dimension, value, *, mask) -> None
    def increment(self, *, srca=0, srcb=0, dst=0, carry=0) -> None
    def set_base(self, *, srca=0, srcb=0, dst=0, carry=0, mask=0) -> None

class InstructionEmitter:
    def issue_tt(self, word, *, effects: HardwareEffects) -> Operation
    def issue_many(self, words, *, effects: HardwareEffects) -> Operation
```

Add typed wrappers for source halo controls, address modifiers, pack edges,
unpack contexts, XMOV, DMA-register operations, local atomics, LUT/macro setup,
and performance/debug counters. `InstructionEmitter` is the public escape hatch
for a verified non-sync opcode before its typed wrapper exists. It rejects sync,
semaphore, mutex, and wait opcodes, and it rejects an absent or incomplete
effect declaration. Escape-hatch instructions participate in the same resource
versioning and protocol expansion as typed wrappers.

## Implementation order

1. Add the structured per-RISC operation IR and typed resource effects.
2. Move waits, CB publication, Dst handoff, and implicit NoC completion out of
   individual TTK helpers and into tile synchronization lowering.
3. Add views, runtime/internal CB creation, Dst leases/snapshots, named tile
   events, and `move` routing.
4. Split NoC, unpack, pack, FPU, SFPU, MOP, and Replay into configure/issue
   operations with declared completion effects.
5. Complete formats, exact ranges, row-major paths, FPU modes, SFPU predicates,
   persistent LRegs, cross-lane reductions, LUT, and LOADMACRO.
6. Add remote CB pull, unicast push, and symmetric multicast payload paths;
   leave their cross-core publication protocol explicit and deferred.
7. Rebuild `matmul_peak`, Llama 3, online softmax, and FlashAttention using only
   public TTK functions.

## Acceptance

TTK is complete when:

- no public TTK function directly emits physical synchronization;
- all tile-local waits and handshakes are derived from typed resource effects or
  explicit named tile events before instruction encoding;
- synchronization lowering covers the BRISC-to-unpack, unpack-to-math,
  math-to-pack, and pack-to-NCRISC Llama pipelines, including GQA's repeated
  retained-Dst snapshots;
- current Llama uses no private TTK method or direct instruction emission;
- historical `matmul_peak` works with remote CB multicast, MOP/Replay, double
  buffering, Dst spill/reload, and exact tails;
- online softmax and FlashAttention retain FP32 Dst state, reduce rows, rescale
  running state, snapshot probabilities, and continue matmul;
- CB payload tests cover wrap, exact tails, remote pull, unicast, multicast,
  repeated generations, and canaries; separate tile-sync tests cover local CB
  publication, backpressure, wraparound, and event-only handoffs;
- every supported route, dtype, layout, range, broadcast, fidelity, and Dst mode
  has standalone and mixed-chain hardware tests.

The tile operation IR owns dependency meaning and validation. Target lowering
owns physical protocol selection, insertion, and synchronization tests.
