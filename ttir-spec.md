# TTIR Spec

TTIR is a small, explicit IR for writing Tenstorrent programs. It is not a
general tensor graph and it is not an optimizer IR.

The core design rule:

```text
There is one way to write any TTIR program.
```

TTIR should describe the program the hardware will run: reader movement,
compute, writer movement, loops, guards, circular buffers, DST usage, and
within-tile SFPU predicates. It should not rely on discovering a schedule from a
large DAG of algebraic possibilities.

## Shape

TTIR is a structured statement program plus a tiny expression language.

```python
@dataclass(frozen=True)
class ProgramIR:
  name: str
  buffers: tuple[BufferSpec, ...]
  cbs: tuple[CBSpec, ...]
  semaphores: int
  kernels: tuple[KernelIR, ...]

@dataclass(frozen=True)
class KernelIR:
  role: Role
  stmts: tuple[Stmt, ...]
```

Statements are ordered. Expressions are small trees used only for indices,
guards, counts, addresses, and simple scalar formulas.

```text
Program = ordered kernels
Kernel  = ordered statements
Stmt    = hardware/program action
Expr    = restricted scalar/index expression
```

No program values are hidden in metadata. If a statement depends on a dynamic
value, that value is an `Expr` argument to the statement.

## Program Objects

```python
Role = Literal["brisc", "ncrisc", "compute"]
Place = Literal["host", "dram", "l1", "cb", "dst", "lreg", "reg"]

@dataclass(frozen=True)
class BufferSpec:
  name: str
  dtype: DType
  shape: tuple[int, ...]
  place: Literal["host", "dram", "l1"]
  address: int | None = None

@dataclass(frozen=True)
class CBSpec:
  name: str
  index: int
  dtype: DType
  tile_size: int
  pages: int
```

There is one logical `compute` role. Lowering may split it across the TRISC
pipeline, but TTIR does not expose `trisc0`, `trisc1`, and `trisc2` as
independent programmable cores.

## Expression Language

Expressions are only for scalar/index values. They are deliberately restricted
so bounds checking is decidable.

```python
@dataclass(frozen=True)
class Expr:
  op: ExprOp
  args: tuple[Expr | int | str, ...]
```

Allowed expression ops:

| Op | Meaning |
| --- | --- |
| `CONST(value)` | Integer/scalar constant. |
| `VAR(name)` | Loop variable or assigned scalar. |
| `SPECIAL(name)` | Hardware id such as `core_id`, `core_x`, `core_y`. |
| `ADD(a, b)` | Addition. |
| `SUB(a, b)` | Subtraction. |
| `MUL_CONST(a, c)` | Multiply by static integer constant. |
| `FLOORDIV_CONST(a, c)` | Floor-divide by static positive integer constant. |
| `MOD_CONST(a, c)` | Modulo static positive integer constant. |
| `LT(a, b)` | Less-than predicate. |
| `LE(a, b)` | Less-or-equal predicate. |
| `EQ(a, b)` | Equality predicate. |
| `AND(a, b)` | Boolean and. |
| `OR(a, b)` | Boolean or. |
| `NOT(a)` | Boolean not. |

Disallowed in index/guard expressions:

```text
dynamic * dynamic
dynamic division by dynamic value
arbitrary nonlinear functions
floating point address/index formulas
```

This keeps index expressions affine or affine-plus-static-div/mod. That is
enough for tile ids, rows, columns, strides, block ids, and tail guards.

### Specials

Required specials:

```text
SPECIAL("core_id")  in [0, num_cores - 1]
SPECIAL("core_x")   in [0, grid_x - 1]
SPECIAL("core_y")   in [0, grid_y - 1]
```

## Bounds Algebra

Every index expression has an interval bound:

```text
expr.bounds = [min, max]
```

Base rules:

```text
CONST(c)              -> [c, c]
VAR(loop_i)           -> loop range bound
SPECIAL(bound, name)  -> [0, bound - 1]
```

Arithmetic rules:

```text
ADD([a,A], [b,B]) -> [a+b, A+B]
SUB([a,A], [b,B]) -> [a-B, A-b]

MUL_CONST([a,A], c >= 0) -> [a*c, A*c]
MUL_CONST([a,A], c < 0)  -> [A*c, a*c]

FLOORDIV_CONST([a,A], c > 0) -> [floor(a/c), floor(A/c)]
MOD_CONST(_, c > 0)          -> [0, c-1]
```

Predicate folding:

```text
LT(x, y) is always true  iff max(x) < min(y)
LT(x, y) is always false iff min(x) >= max(y)
```

Guard elimination:

```text
IF(tile_id < num_tiles)
```

may be removed only when:

```text
max(tile_id) < min(num_tiles)
```

If the validator cannot prove an index is in bounds, a guard must remain.

## Statements

Statements are ordered and may contain nested statement bodies.

```python
@dataclass(frozen=True)
class Stmt:
  op: StmtOp
  args: tuple[object, ...]
  body: tuple["Stmt", ...] = ()
```

`args` may contain inert metadata, `Expr`s, buffer names, CB names, and static
integers. `args` must not contain hidden statements or graph nodes.

### Control

| Statement | Arguments | Meaning |
| --- | --- | --- |
| `FOR` | var, start, end, axis | Structured loop. |
| `IF` | predicate expr | Structured guard. |
| `ASSIGN` | name, expr | Name a scalar/index expression. |

Preferred printed form:

```text
FOR i in [0, tiles_per_core) axis=tile_loop:
  ASSIGN tile_id = core_id * tiles_per_core + i
  IF tile_id < num_tiles:
    ...
```

Axis names:

```text
tile_loop
reduce
subblock
role_loop
```

## Tile Memory Statements

| Statement | Arguments | Meaning |
| --- | --- | --- |
| `TILE_INDEX` | name, buffer, indices..., layout | Assign logical tile pointer/index. |
| `LOAD_TILE` | dst, tile_ptr | Load logical tile into compute-visible value. |
| `STORE_TILE` | tile_ptr, value | Store logical tile. |

Example:

```text
TILE_INDEX xptr, src, tile_id
LOAD_TILE x, xptr
TILE_INDEX yptr, out, tile_id
STORE_TILE yptr, y
```

Scheduling lowers these to NOC, CB, unpack, pack, and role-specific statements.

## Circular Buffer Statements

| Statement | Arguments |
| --- | --- |
| `CB_RESERVE` | cb, count |
| `CB_PUSH` | cb, count |
| `CB_WAIT` | cb, count |
| `CB_POP` | cb, count |

CB producer/consumer validation is scoped per physical core's CB instance.
Logical multicast fan-out is allowed: one source may multicast data to many
cores, each with its own local CB instance.

## NOC Statements

| Statement | Arguments |
| --- | --- |
| `NOC_READ_TILE` | buffer, tile_id expr, cb |
| `NOC_WRITE_TILE` | cb, buffer, tile_id expr |
| `NOC_READ_BARRIER` | |
| `NOC_WRITE_BARRIER` | |
| `NOC_MULTICAST` | src_l1, dst_rect, byte_count |
| `NOC_SEMAPHORE_WAIT` | semaphore, value |
| `NOC_SEMAPHORE_SET` | semaphore, value |
| `NOC_SEMAPHORE_INC` | semaphore_addr, value |

## DST / Pack / Unpack Statements

| Statement | Arguments |
| --- | --- |
| `TILE_REGS_ACQUIRE` | |
| `TILE_REGS_COMMIT` | |
| `TILE_REGS_WAIT` | |
| `TILE_REGS_RELEASE` | |
| `COPY_TILE` | cb, cb_tile, dst_index |
| `PACK_TILE` | dst_index, cb |
| `UNPACK_TILE` | cb, cb_tile, dst_index |

DST occupancy is a validated resource.

```python
@dataclass(frozen=True)
class DstUsage:
  dtype: DType
  slots: int
```

The validator must prove that live DST slots inside an acquire/release region do
not exceed hardware capacity.

Example:

```text
out_subblock_h * out_subblock_w <= dst_capacity(dtype_acc)
```

## Within-Tile Domains

Partial indexing, slicing, and partial reductions use explicit within-tile
domains. These are not mask tensors.

```python
@dataclass(frozen=True)
class TileDomain:
  tile_id: Expr
  vector_start: int
  vector_count: int
  lane_predicate: LanePredicate

@dataclass(frozen=True)
class LanePredicate:
  kind: Literal["all", "range", "mask"]
  start: int = 0
  count: int = 32
  mask: int | None = None
```

`tile_id` is an `Expr`, not hidden metadata. Bounds analysis sees it.

SFPU granularity:

```text
tile = 32 x 32 elements
SFPU vector width = 32 lanes
tile = 32 SFPU vector steps
```

Example: 100 contiguous elements from the start of a tile:

```text
TileDomain(tile_id=t, vector_start=0, vector_count=3, predicate=all)
TileDomain(tile_id=t, vector_start=3, vector_count=1, predicate=range(0, 4))
```

Scheduled SFPU code uses condition-code statements/instructions:

```text
SFPSETCC
SFPENCC
SFPPUSHC
SFPPOPC
SFPCOMPC
```

## Math Statements

Math statements name explicit hardware-facing operations. They are not a
general algebra graph.

### Tile FPU

| Statement | Meaning | Candidate instruction |
| --- | --- | --- |
| `FPU_ADD_TILE` | tile + tile | `TTELWADD` |
| `FPU_SUB_TILE` | tile - tile | `TTELWSUB` |
| `FPU_MUL_TILE` | tile * tile | `TTELWMUL` |
| `FPU_MATMUL_STEP` | matrix/tile inner step | `TTMVMUL`, `TTDOTPV`, matmul APIs |

### SFPU

| Statement | Candidate instructions |
| --- | --- |
| `SFPU_LOAD` | `TTSFPLOAD`, `TTSFPLOADI`, `TTSFPLOADMACRO` |
| `SFPU_STORE` | `TTSFPSTORE` |
| `SFPU_ADD` | `TTSFPADD`, `TTSFPADDI` |
| `SFPU_MUL` | `TTSFPMUL`, `TTSFPMULI`, `TTSFPMUL24` |
| `SFPU_MAD` | `TTSFPMAD` |
| `SFPU_RECIP` | `TTSFPARECIP`, `TTSFPDIVP2` |
| `SFPU_CAST` | `TTSFPCAST`, `TTSFPSTOCHRND` |
| `SFPU_LOGICAL` | `TTSFPAND`, `TTSFPOR`, `TTSFPXOR`, `TTSFPNOT` |
| `SFPU_PREDICATE` | `TTSFPSETCC`, `TTSFPENCC`, `TTSFPCOMPC`, `TTSFPPUSHC`, `TTSFPPOPC`, `TTSFPLE`, `TTSFPGT` |

Use FPU statements for full-tile operations when the hardware path exists. Use
SFPU statements for scalar constants, nonlinear ops, casts, predicates, and
partial-lane work.

## Reductions

Cross-tile reductions are explicit loops and combine stages. They are not a
single magic graph node.

Within-tile or within-domain reduction may be represented by a statement:

| Statement | Arguments |
| --- | --- |
| `REDUCE_DOMAIN` | dst, src, op, `TileDomain` |

Example partial reduce over ten lanes:

```text
REDUCE_DOMAIN acc, src, ADD,
  TileDomain(tile_id=t, vector_start=1, vector_count=1,
             lane_predicate=range(13, 10))
```

A large tensor sum is written as explicit program structure:

```text
FOR tile in assigned_tiles:
  LOAD_TILE x, src[tile]
  REDUCE_DOMAIN partial, x, ADD, full_tile_domain(tile)
  STORE_TILE partials[partial_id], partial

combine stage:
  FOR partial in partials:
    accumulate partial
```

The exact combine strategy is a program/planner choice.

## Planned Programs

High-reuse kernels are emitted as explicit TTIR programs. A planner may choose
parameters, but the IR contains the resulting statements, not an opaque plan
object.

Matmul planner choices include:

```text
core grid
per-core M/N output tile block
K block width
output subblock shape
CB page counts
multicast rectangles
accumulator reload strategy
```

After planning, the TTIR program is ordinary statements:

```text
reader A:
  NOC_READ_TILE / NOC_MULTICAST / CB_PUSH

reader-writer B/C:
  NOC_READ_TILE / NOC_MULTICAST / CB_PUSH
  NOC_WRITE_TILE final C

compute:
  CB_WAIT
  TILE_REGS_ACQUIRE
  FPU_MATMUL_STEP
  PACK_TILE partial/final
```

The plan is not part of TTIR. It is an input to TTIR generation.

## Example: Add One

```text
kernel brisc:
  FOR i in [0, tiles_per_core) axis=tile_loop:
    ASSIGN tile_id = SPECIAL("core_id") * tiles_per_core + i
    IF tile_id < num_tiles:
      CB_RESERVE cb0, 1
      NOC_READ_TILE src, tile_id, cb0
      NOC_READ_BARRIER
      CB_PUSH cb0, 1

kernel compute:
  FOR i in [0, tiles_per_core) axis=tile_loop:
    ASSIGN tile_id = SPECIAL("core_id") * tiles_per_core + i
    IF tile_id < num_tiles:
      CB_WAIT cb0, 1
      TILE_REGS_ACQUIRE
      COPY_TILE cb0, 0, dst0
      SFPU_ADD dst0, dst0, CONST(1.0)
      TILE_REGS_COMMIT
      TILE_REGS_WAIT
      CB_RESERVE cb16, 1
      PACK_TILE dst0, cb16
      TILE_REGS_RELEASE
      CB_PUSH cb16, 1
      CB_POP cb0, 1

kernel ncrisc:
  FOR i in [0, tiles_per_core) axis=tile_loop:
    ASSIGN tile_id = SPECIAL("core_id") * tiles_per_core + i
    IF tile_id < num_tiles:
      CB_WAIT cb16, 1
      NOC_WRITE_TILE cb16, out, tile_id
      NOC_WRITE_BARRIER
      CB_POP cb16, 1
```

## Validation

The validator checks:

1. All index and guard expressions belong to the restricted expression language.
2. Expression bounds are propagated for `CONST`, `VAR`, `SPECIAL`, add/sub,
   multiply/divide/mod by constants, and boolean predicates.
3. Tile indices are statically in bounds or protected by a guard.
4. Guards are removed only when interval algebra proves them true.
5. CB page size and page count match scheduled use.
6. CB reserve/push and wait/pop are balanced per core-local CB instance.
7. Multicast fan-out targets valid cores and does not violate semaphore protocol.
8. DST acquire/release regions are balanced.
9. Live DST occupancy never exceeds hardware capacity for the accumulator dtype.
10. SFPU lane predicates use valid vector/lane ranges.
11. Role-specific statements appear only in legal roles.
