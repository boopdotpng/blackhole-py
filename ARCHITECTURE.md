# blackhole-py — decided architecture (own the whole stack)

No tt-metal, no tt-lang, no C++. tinygrad frontend → our TTIR → RISC-V on cores.
blackhole-py already launches/runs kernels with zero TT software.

```
tinygrad Tensor graph
   │  HACK: intercept PRE-RANGEIFY uops (Tensor.uop / before run_rangeify)
   │        (renderer/linearized level is too far gone: GPU address math, no tile intent)
   ▼
TTIR  — tile-native IR (this is kir/L2)
   │  ONE deterministic lowering per op (no beam/search — TT is non-tunable)
   ▼
RISC-V (brisc/ncrisc/trisc0/1/2) → Tensix words → CQ → device
```

## Why not the renderer level
Confirmed by tools/tg_dump.py on llama3: post-rangeify a kernel is
`STORE(INDEX(PARAM, RANGE))` — flat GPU indexing, no "tile"/"reduce". A
renderer→TT lowerer can't work for all kernels. Pre-rangeify keeps REDUCE(axis),
matmul=EXPAND+MUL+REDUCE, softmax=REDUCE(MAX)+EXP2+REDUCE(ADD). Cost: tinygrad's
uop path churns across versions, so the interceptor needs periodic fixups
(accepted).

## The atom is a TILE (32×32)
TT is ~99% tile-based. Lean in fully:
- TTIR values are `Tile` (or a `TileStream` over a CB), never scalars.
- Every op is tile→tile: unpack this tile, pack this tile, matmul these tiles,
  read/write these tiles from DRAM, "these tiles go there."
- ALL sync is tile-counting: a semaphore/CB credit = a number of tiles.
  "wait for N tiles" is the universal handshake.
- CB depth = N tiles; page = 1 tile = dtype.tile_bytes.

## Sub-tiles: the only place you go below a tile
Needed for intra-tile reductions/slicing, e.g. `x[45:55].sum()` over a 1024-lane
tile. Lowering: SFPU predicate (SETCC over lane index) + a loop that sums only
the selected lanes into DST. TRIGGER from tinygrad: a `SHRINK`/slice whose bounds
are NOT multiples of 32 → emit a `SubTileMask` op carrying the lane predicate.
Tile-aligned slices stay pure tile ops. This is the one leak; isolate it in one
op class.

## One deterministic path (no search)
There is exactly one good way to write ~90% of kernels — non-tunable, unlike a
GPU. So the lowerer is a PURE TABLE: `dict[TTIROp -> fixed RISC-V template]`. No
Kernel opt / beam / autotune layer exists. The "compiler" is tiny; correctness,
not speed-search, is the whole game.

## Reverse-engineering the primitives (the real work)
copy_tile / cb_wait_front / cb_push_back / NOC packets depend on an intricate
semaphore+stall dance. We do NOT read TT source — we mine the WORKING hand
kernels (rmsnorm, matmul_peak) with the tooling already built: `kir.lift()` +
`kir/sem.py` extract the exact instruction/semaphore template for each primitive.
RE = "for each TTIR op, find its instruction template in a known-good kernel."

## Two sync tiers
1. Intra-core: unpack→math→pack via Tensix semaphores (MATH_PACK etc.) — the
   contract we already model + check (kir/synccheck.py).
2. Inter-core: 118 cores = 118 coordinated units. Tiles are sharded across the
   grid; cross-core tile movement (all-gather / reduce-scatter / broadcast) is
   NOC + L1 mailbox handshakes. A HARD fusion boundary lives here. This tier is
   TODO; it's what makes rmsnorm 5 launches (cross-core mean) vs 1 (redundant
   local).

## Layer map to existing code
- kir/ir.py, cfg.py  = L1 (instruction nodes, CFG) — analysis rung, keep.
- kir/sem.py, synccheck.py, regcheck.py = optional passes over kir.
- kir/IR_DESIGN.md   = the L2 TTIR spec (Tensor metadata + Program builder).
- TTIR (L2)          = tile-native ops + Tensor(layout/shard) + Program.lower().
- tools/tg_dump.py   = the pre-rangeify uop inspector.
```
