# TTIR Spec

TTIR is the small IR needed to describe Tenstorrent programs before emitting
`blackhole-py` kernels. It is not a generic tensor IR. Its job is to represent:

- program inputs, outputs, and storage;
- core/tile work distribution;
- tile loads, tile stores, and circular-buffer movement;
- FPU/SFPU tile math;
- within-tile lane domains for partial work;
- planned high-reuse kernels such as matmul.

The IR has one node type:

```python
@dataclass(frozen=True)
class TTUOp:
  op: TTOp
  dtype: DType = void
  src: tuple["TTUOp", ...] = ()
  arg: object = None
  tag: object = None
```

Derived properties:

```text
dtype   scalar, tile, pointer, cb, or void
shape   scalar (), tile, tile-grid shape, or void
place   host, dram, l1, cb, dst, lreg, reg, null
bounds  optional interval for index/special values
```

## Program Objects

```python
@dataclass(frozen=True)
class ProgramIR:
  name: str
  graph: TTUOp
  launch: LaunchSpec
  buffers: tuple[BufferSpec, ...] = ()
  cbs: tuple[CBSpec, ...] = ()
  semaphores: int = 0

@dataclass(frozen=True)
class LaunchSpec:
  grid: tuple[tuple[int, ...], tuple[int, ...]] | None = None
  num_cores: int | None = None
  tiles_per_core: int | None = None
```

`grid` is a physical core grid when a program needs explicit placement. Simple
1D programs may use `num_cores` and `tiles_per_core`.

```python
@dataclass(frozen=True)
class BufferSpec:
  name: str
  dtype: DType
  shape: tuple[int, ...]
  place: Literal["host", "dram", "l1"]
  address: int | None = None

@dataclass(frozen=True)
class CBSpec:
  index: int
  dtype: DType
  tile_size: int
  pages: int
```

## Core Ops

### Sources

| Op | `src` | `arg` | Meaning |
| --- | --- | --- | --- |
| `BUFFER` | `()` | `BufferSpec` | Named backing storage. |
| `PARAM` | `()` | slot, dtype, shape/place | Runtime argument. |
| `CONST` | `()` | value | Scalar constant. |
| `SPECIAL` | `(bound,)` | name | Hardware/schedule id with known bounds. |

Required `SPECIAL` names:

```text
core_id
core_x
core_y
```

Example:

```text
core = SPECIAL(num_cores, "core_id")
i = RANGE(tiles_per_core, axis="tile_loop")
tile_id = core * tiles_per_core + i
```

### Control And Effects

| Op | `src` | `arg` | Meaning |
| --- | --- | --- | --- |
| `RANGE` | `(bound,)` | axis kind | Loop induction value. |
| `END` | `(body, range)` | none | Close a loop. |
| `GUARD` | `(pred, body)` | none | Conditional execution. |
| `AFTER` | `(value, deps...)` | none | Return value after side effects. |
| `GROUP` | `(effects...)` | none | Merge effects. |
| `SINK` | `(effects...)` | name | Program root. |

Axis kinds:

```text
tile_loop       per-core output tile loop
reduce          reduction/K loop
subblock        matmul/output subblock loop
role_loop       reader/writer/compute internal loop
```

## Tile Memory Ops

| Op | `src` | `arg` | Meaning |
| --- | --- | --- | --- |
| `TILE_INDEX` | `(buffer, i0, i1, ...)` | layout | Pointer/view to a logical tile. |
| `LOAD_TILE` | `(tile_ptr,)` | none | Logical tile load. |
| `STORE_TILE` | `(tile_ptr, value, gate?)` | none | Logical tile store. |
| `COPY` | `(value,)` | destination place | Move between places. |

These are still logical. Scheduling lowers them to NOC reads/writes, CB waits,
unpack, pack, and role-specific code.

## Within-Tile Domains

Partial indexing, slicing, and partial reductions need a domain below tile
granularity. The SFPU executes in 32-lane vector chunks; per-element precision is
implemented through lane predicates, but execution still advances by vector
steps.

```python
@dataclass(frozen=True)
class TileSlice:
  tile_id: int | TTUOp
  vector_start: int
  vector_count: int
  lane_start: int = 0
  lane_count: int = 32

@dataclass(frozen=True)
class LanePredicate:
  kind: Literal["all", "range", "mask"]
  start: int = 0
  count: int = 32
  mask: int | None = None
```

For a contiguous 1D region, lowering computes:

```text
tile_elems = 1024
sfpu_width = 32

tile_id       = index // tile_elems
in_tile_index = index % tile_elems
vector_id     = in_tile_index // sfpu_width
lane_id       = in_tile_index % sfpu_width
```

Example: first 100 elements in one tile:

```text
vector 0: lanes 0..31  all
vector 1: lanes 0..31  all
vector 2: lanes 0..31  all
vector 3: lanes 0..3   range predicate
```

The scheduled SFPU path emits condition-code operations such as:

```text
SFPSETCC
SFPENCC
SFPPUSHC
SFPPOPC
SFPCOMPC
```

Do not materialize user-visible mask tiles for simple contiguous partial
domains. Use tile slices and lane predicates.

## Math Ops

Canonical math ops are hardware-neutral until legalization chooses FPU or SFPU.

| Class | Ops |
| --- | --- |
| Unary | `NEG`, `RECIPROCAL`, `EXP2`, `LOG2`, `SQRT`, `TRUNC`, `CAST`, `BITCAST` |
| Binary | `ADD`, `SUB`, `MUL`, `MAX`, `CMPLT`, `CMPNE`, `CMPEQ`, `AND`, `OR`, `XOR`, `SHL`, `SHR` |
| Ternary | `WHERE`, `MULACC` |
| Structural | `REDUCE`, `MATMUL` |

`REDUCE` is one op:

```text
REDUCE(value, op=ADD, axis/domain=...)
```

If the domain is partial, the reduce is partial. There is no separate canonical
`PARTIAL_REDUCE` op.

### FPU Candidates

Tile FPU/DST instructions in `dsl.py`:

| Pattern | Instruction candidates |
| --- | --- |
| `ADD(tile, tile)` | `TTELWADD` |
| `SUB(tile, tile)` | `TTELWSUB` |
| `MUL(tile, tile)` | `TTELWMUL` |
| dot/matrix inner work | `TTDOTPV`, `TTMVMUL` |
| pooling/reduce-like kernels | `TTGAPOOL`, `TTGMPOOL`, `TTAPOOL3S*`, `TTMPOOL3S*` |
| convolution kernels | `TTCONV3S*`, `TTMFCONV3S1` |

Use FPU paths for full-tile math when operands are in the right tile/DST form.

### SFPU Candidates

SFPU instructions in `dsl.py`:

| Pattern | Instruction candidates |
| --- | --- |
| load/store LREG | `TTSFPLOAD`, `TTSFPLOADI`, `TTSFPSTORE`, `TTSFPLOADMACRO` |
| add | `TTSFPADD`, `TTSFPADDI` |
| multiply | `TTSFPMUL`, `TTSFPMULI`, `TTSFPMUL24` |
| multiply-add | `TTSFPMAD` |
| integer add/shift | `TTSFPIADD`, `TTSFPSHFT`, `TTSFPSHFT2` |
| reciprocal/divide power-of-two | `TTSFPARECIP`, `TTSFPDIVP2` |
| exponent/mantissa | `TTSFPEXEXP`, `TTSFPEXMAN`, `TTSFPSETEXP`, `TTSFPSETMAN` |
| sign/absolute | `TTSFPSETSGN`, `TTSFPABS` |
| logical | `TTSFPAND`, `TTSFPOR`, `TTSFPXOR`, `TTSFPNOT` |
| predicates/conditions | `TTSFPSETCC`, `TTSFPENCC`, `TTSFPCOMPC`, `TTSFPLE`, `TTSFPGT`, `TTSFPPUSHC`, `TTSFPPOPC` |
| casts/rounding | `TTSFPCAST`, `TTSFPSTOCHRND` |
| LUT/nonlinear | `TTSFPLUT`, `TTSFPLUTFP32` |
| transpose/swizzle | `TTSFPTRANSP`, `TTSFPSWAP` |

Use SFPU paths for scalar constants, nonlinear ops, casts, lane predicates, and
partial tile work.

## Scheduled Ops

Scheduled TTIR is role-specific and close to generated kernels.

### Kernel Roles

```text
brisc       reader / input data movement
ncrisc      writer / output data movement
trisc0      compute
trisc1      compute
trisc2      compute
trisc_all   same logical compute body for all TRISCs
```

### Circular Buffers

| Op | `src` | `arg` |
| --- | --- | --- |
| `DEFINE_CB` | `()` | `CBSpec` |
| `CB_RESERVE` | `(cb,)` | tile count |
| `CB_PUSH` | `(cb,)` | tile count |
| `CB_WAIT` | `(cb,)` | tile count |
| `CB_POP` | `(cb,)` | tile count |

### NOC

| Op | `src` | Meaning |
| --- | --- |
| `NOC_READ_TILE` | `(tensor, tile_index, cb)` |
| `NOC_WRITE_TILE` | `(cb, tensor, tile_index)` |
| `NOC_READ_BARRIER` | `()` |
| `NOC_WRITE_BARRIER` | `()` |
| `NOC_MULTICAST` | `(src_l1, dst_rect, bytes)` |
| `NOC_SEMAPHORE_WAIT` | `(sem, value)` |
| `NOC_SEMAPHORE_SET` | `(sem, value)` |

### DST / Pack / Unpack

| Op | `src` | Meaning |
| --- | --- |
| `TILE_REGS_ACQUIRE` | `()` |
| `TILE_REGS_COMMIT` | `()` |
| `TILE_REGS_WAIT` | `()` |
| `TILE_REGS_RELEASE` | `()` |
| `COPY_TILE` | `(cb, cb_tile, dst_index)` |
| `PACK_TILE` | `(dst_index, cb)` |
| `UNPACK_TILE` | `(cb, cb_tile, dst_index)` |

## Planned Matmul

`MATMUL` is a special planned op, not a generic elementwise op.

```python
@dataclass(frozen=True)
class MatmulSpec:
  M: int
  K: int
  N: int
  dtype_in: DType
  dtype_acc: DType
  transpose_b: bool = False

@dataclass(frozen=True)
class MatmulPlan:
  mt: int
  kt: int
  nt: int
  core_grid: tuple
  per_core_m: int
  per_core_n: int
  in0_block_w: int
  num_blocks: int
  out_subblock_h: int
  out_subblock_w: int
  in0_block_num_tiles: int
  in1_block_num_tiles: int
  out_block_num_tiles: int
  cb0_pages: int
  cb1_pages: int
  cb16_pages: int
  cb24_pages: int
```

Required behavior:

```text
assign each core a rectangle of C tiles
stream K in blocks
reuse A across N-side cores
reuse B across M-side cores
accumulate in DST
optionally pack/reload partial C through an accumulator CB
pack final C through output CB
```

Scheduled outline:

```text
reader A:
  read A block from DRAM
  optionally multicast block
  push cb0

reader/writer B:
  read B block from DRAM
  optionally multicast block
  push cb1
  write final C blocks

compute:
  mm_block_init(...)
  for k_block in num_blocks:
    wait cb0/cb1
    for output subblock:
      tile_regs_acquire()
      optionally reload partial C
      for inner in in0_block_w:
        matmul_block(cb0, cb1, ...)
      tile_regs_commit()
      pack final C to cb16 or partial C to cb24
      tile_regs_release()
```

Other high-reuse kernels, such as convolution or attention, should follow this
model later: special semantic op plus explicit plan object.

## Examples

### Add One

```text
core = SPECIAL(num_cores, "core_id")
i = RANGE(tiles_per_core, axis="tile_loop")
tile_id = core * tiles_per_core + i
valid = tile_id < num_tiles

x = LOAD_TILE(TILE_INDEX(src, tile_id))
y = ADD(x, CONST(1.0))
STORE_TILE(TILE_INDEX(out, tile_id), y, valid)
```

Implementation choice:

```text
ADD(tile, tile)  -> FPU TTELWADD
ADD(tile, const) -> SFPU scalar add path
```

### Partial Reduce

```text
domain = (
  TileSlice(tile_id=0, vector_start=1, vector_count=1,
            lane_start=13, lane_count=10),
)
out = REDUCE(src, op=ADD, domain=domain)
```

Implementation choice:

```text
full vectors      -> normal SFPU vector accumulation
partial vector    -> SFPU condition-code lane predicate
multi-tile domain -> per-tile partials plus combine stage
```

## Validation

The verifier checks:

1. Buffer and CB specs are well-formed.
2. Tile indices are in bounds or guarded.
3. `SPECIAL` and `RANGE` carry finite bounds.
4. Within-tile domains use valid vector/lane ranges.
5. FPU/SFPU implementation supports the dtype, place, and domain.
6. CB page size and page count match scheduled use.
7. Each scheduled CB has one producer and one consumer.
8. `CB_RESERVE/PUSH` and `CB_WAIT/POP` are balanced.
9. DST values are used only inside acquire/release regions.
10. Role-specific ops appear only in legal kernel roles.
