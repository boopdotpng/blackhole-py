# Blackhole Backend Lowering Specification

This document is the explicit implementation blueprint for turning Layer 1 N-D kernel graphs (output of `compiler/rangeify.py:get_kernel_graph`) into 5-core Blackhole machine code (`Ops.PROGRAM` / `BH01` bundles). It turns the design decisions from [gemini-lowering-conversation.md](gemini-lowering-conversation.md) (Turns 10–21, Q1–Q8) into concrete IR types, pass ordering, invariants, and a worked end-to-end trace.

---

## 0. Core Invariants (Read Before Coding)

1. **No early instruction generation.** Do **not** emit raw `hw_isa.*` words (`UNPACR`, `MVMUL`, `PACR`, `SFPMAD`, `RMWCIB`, `SETC16`, NoC `SW`s) while still in the SSA DAG.
   - In the DAG (Passes 1–5), FPU and transfer ops are **abstract tile-level SSA nodes** (`UOp.ins(FpuOp / UnpackOp / PackOp / NocRead / NocWrite / SfpLoadOp / SfpStoreOp)`), while SFPU math stays as **plain core ALU `UOp`s** (`ADD`, `MUL`, `EXP2`, `RECIP`, `WHERE`, `CMPLT`, `CAST`, ...) in `Space.LREG` inside a `RANGE(fp)` footprint loop.
   - Concrete machine instructions (`hw_isa.Tensix`, `SfpSpec`, `RVOps`) and `L0..L7` / `x6..x29` register allocation happen **late**, per-core, in Passes 9–10 on each core's `list[UOp]` (`Ops.LINEAR`) — **while structured `RANGE`/`END` loops are still intact** so `SFPLOADMACRO → REPLAY → MOP` can compress both FPU and SFPU sequences cleanly before RV32 branch lowering.
2. **Linearize ONCE, sync on the linear list, then split 5 ways.**
   - Never insert CB/semaphore/stall syncs in the SSA DAG (hash-consing + side effects would force `AFTER` tokens on every op).
   - Never linearize 5 separate per-core DAGs.
   - Linearize the single unified tile DAG **once** into 1 joint sequential `list[UOp]` (Pass 6), insert matched producer/consumer sync pairs in one linear scan (Pass 7), and project into 5 per-core `Ops.LINEAR` streams (Pass 8).
3. **Zero new core `Ops` in `compiler/uop.py`.**
   - Every Blackhole tile op, transfer op, and sync op uses `UOp.ins(spec, srcs, dtype, role=...)` (= `Ops.CALL(Ops.NATIVE(NativeInfo(code=spec)), *srcs)`).
   - SFPU math uses the existing core ALU `Ops` (`ADD`, `MUL`, `MULACC`, `EXP2`, `WHERE`, ...) directly in `Space.LREG` — no `CALL(SINK(SfpuArg))` wrapper needed (`CALL(SINK)` remains strictly for real callable functions/kernels).
4. **Locked hardware policies (Q1–Q8):**
   - `fp32_dest_acc = 1` globally, always, zero mode switching. `Dst` has `512 × 16` fp32 rows = `64` slots of `8×16` (double-buffered: `32` slots per half, `sem math_pack max=2`; single-buffered fallback: `64` slots, `max=1`). **Never spill `Dst`.**
   - **Activations:** always `[..., M/8, N/16, 8, 16]` face-tiled (`M_TILE = 8`, `N_TILE = 16`).
   - **Weights:** always `[..., N/16, K/16, 16, 16]` face-tiled (`16×16`).
   - **No `32×32` Z-order anywhere.**
   - **No `FaceLayout` in the compiler.** Storage layout is a pure UOp index formula in Pass 4 (`(f_m * nc + f_n) * face_bytes`). Host boundary pad/tilize lives in `device.py` DMA staging (`copyin`/`copyout`); `PACR(DstAccessMode=1)` row-major untilize is used only on `host_out` buffers.
   - **FPU vs SFPU precision rule:**
     - `MVMUL`: inputs in `{bf16, bfp8, e4m3, bfp4, tf32}`, acc in `fp32 Dst`. Activation always in `SrcB` (`8×16`), weight in `SrcA` (`16×16`). `fp32` inputs unpack to `SrcB`/`SrcA` as TF32 with **4-byte Src strides (`row=64, face=1024`)**. `3` fidelity phases `{0,1,2}` for `bf16`/`tf32`, `2` for `bfp8`, `1` for `bfp4`.
     - `ELWADD`/`ELWSUB`/`ELWMUL`: FPU only when **both** operands are `<= bf16`; any `fp32` elementwise, norm, transcendental, mask, or reduction tail runs on **SFPU** (`UNPACR to_dest` → `Dst` → SFPU).
   - **Non-hybrid kernel boundary:** every kernel is either a **Tensix kernel** (RV32 does only integer/address/loop/NoC/CB/config + Tensix pushes, zero RV32 float math) or a **pure RV32/NoC kernel** (`ROLE_PC[trisc*] = 0`, e.g. Embedding gather, KV-cache row copy, tiny scalar tails).
   - **DRAM addressing:** flat 64-bit virtual DRAM pointers + resident `FN_NOC_READ` / `FN_NOC_WRITE` / `FN_NOC_WAIT` in `fw/boot.c` (default 4 KiB striping). Kernel codegen only computes a flat byte offset `off`.

---

## 1. Existing Repo Gaps to Fix First (Prerequisites)

Before implementing the backend passes, fix these 4 concrete issues already present in `blackhole-py`:

1. **`compiler/uop.py:linearize()` ([uop.py:1109-1137](../compiler/uop.py#L1109-L1137)):**
   - Currently keys nodes by `(len(ranges[u]), prio, pos)`. Two sibling loops at the same depth (`len == 1`) can interleave!
   - **Fix:** Key by the sorted tuple of active range axes (or emit loops via a recursive range-nesting tree walk) so every `RANGE ... END` body is guaranteed contiguous and sibling sequential loops (ordered by `AFTER` or independent) never interleave.
2. **`compiler/isa/tensix.py:split_roles()` ([tensix.py:226-257](../compiler/isa/tensix.py#L226-L257)):**
   - Currently copies every untagged UOp (including BRISC's DRAM address arithmetic!) into **all 5 cores**.
   - **Fix:** For each role `r`, start from hardware/sync ops owned by `r` plus `END`/`RANGE` loops enclosing them, then **backward-slice** only the pure scalar/index `UOp`s reachable from `r`'s ops (and from the bounds of `r`'s kept `RANGE`s). Only emit those into `buckets[r]`.
3. **`compiler/isa/rv32.py` ([rv32.py](../compiler/isa/rv32.py)):**
   - Add `SPECIAL` lowering (`SPECIAL("worker_id", N)` → `LW rd, 0x28(x0)`, `worker_x` → `0x20`, `worker_y` → `0x24`), runtime arg-block `PARAM` lowering (`LW rd, (0x80 + 8*slot)(x0)` for `u32` vars and `(lo, hi)` for `u64` DRAM pointers), `IF`/else lowering (needed for `if worker_id >= N: ret` and dynamic guards), signed `LB`/`LH` when `dtype.is_signed`, and long-branch relaxation (`±4 KiB` B-type branch → inverted branch + `JAL`).
4. **`compiler/sfpu.py` ([sfpu.py](../compiler/sfpu.py)):**
   - Port from the old typed `UOp` API (`Ops.SFPU`, `Ops.MIN`, `Ops.RSQRT`, `Ops.LOOP`, `Ops.GET`, `UOp(op, dtype, src, arg)`, `UOp.const(dtype, val)`, `lower_reduce_to_loop`) to the current dtype-free `UOp` core + `sfp_ins` (`SfpSpec`) + shared `regalloc` (`L0..L7`).
   - Keep the existing validated minimax decompositions (`exp2`, `log2`, `sin`, `recip`, `rsqrt`, `sqrt`), `L8..L14` constant tiering, and `SFPSETCC` / `WHERE` masking; replace raw `int` word emission with `list[UOp]` of `sfp_ins` / `tt_ins` targeting `8×16` `Dst` blocks (`4 × INCRWC dst+2` per `8×16` block) + `reduce_lanes` (`SFPSHFT2` + `SFPTRANSP`).
5. **`fw/boot.c` + `fw/park.c` + `fw/hw.h` ([fw/](../fw/)):**
   - Link `fw/noc.c` into `brisc`/`ncrisc` boot stubs and export fixed jump-table entry points `FN_NOC_READ`, `FN_NOC_WRITE`, `FN_NOC_WAIT` at `0x70..0x7F`.
   - Reserve L1 Arg Block `0x80..0xFF` (`16 × 8 B` slots: `u64` flat DRAM ptrs + `u32` runtime `Variable`s).
   - Upgrade `fw/park.c` completion barrier (subordinates drain `COPROCESSOR_DONE_CHECK` + `fence` → write `SUBORDINATE_SYNC`; `brisc` waits subordinates + NoC → atomic inc `LEADER_COORD`; leader waits `NUM_WORKERS` → writes sequence to `HOST_SIGNAL_ADDR`).

*(Also remove `compiler/layout.py` or keep only minimal host DMA staging pad/tilize in `device.py` — do not thread `FaceLayout` into compiler passes.)*

---

## 2. Complete 10-Pass Lowering Pipeline

```text
Layer 1 Kernel AST (N-D multi-axis INDEX on RESHAPE(PARAM/ALLOC), from rangeify.py)
│
├── PHASE I: TILE GRAPH (SSA DAG — pure values, ZERO machine words, ZERO syncs, ZERO AFTER spam)
│   ├── Pass 1: Kernel Classification      (Tensix vs Pure RV32/NoC)
│   ├── Pass 2: Shard + Face-Tile + PADTO  (SPECIAL("worker_id", N), 8x16/16x16 faces, N_BLK=8/6)
│   ├── Pass 3: Match FPU & Mark SFPU LReg (UOp.ins(FpuOp); SFPU stays plain ALU UOps in RANGE(fp))
│   ├── Pass 4: Mark Spaces & Insert Xfers (NocRead/Write, UnpackOp/PackOp, SfpLoadOp/SfpStoreOp)
│   └── Pass 5: Static Tile Resource Alloc (Dst 8x16 slots [no spill], CB stream IDs 0..31, L1 offsets)
│
├── PHASE II: JOINT LINEAR STREAM (Linearize ONCE -> Sync ONCE -> Split 5 ways)
│   ├── Pass 6: Joint Linearization        (1 sequential list[UOp] preserving loop nesting)
│   ├── Pass 7: Intra-Core Sync Insertion  (matched CB reserve/push/wait/pop, dvalid, STALLWAIT, SEM*)
│   └── Pass 8: 5-Core Projection          (backward-slice scalar math + loops per role -> 5 Ops.LINEAR)
│
└── PHASE III: LATE PER-CORE CODEGEN (Concrete instructions, StateTrackers, compression, assembly)
    ├── Pass 9:  Per-Core Recipe Expansion (StateTrackers, FPU unroll, sfpu.py isel + L0..L7 regalloc)
    │            + Optional TRISC Compress (SFPLOADMACRO -> REPLAY -> MOP, before RV32 branch lowering)
    └── Pass 10: Per-Core RV32 Lowering    (RV32 isel -> pre_regalloc -> regalloc -> hazards -> BH01 binary)
```

---

## 3. Abstract Tile & Sync Specs (`NativeInfo.code` Dataclasses)

All new backend specs live in `compiler/blackhole/specs.py` (frozen, hashable dataclasses stored in `NativeInfo(code=spec)` via `UOp.ins(...)`). Each spec defines its `.role` and space contract:

```python
class Space(Enum):
  DRAM = "dram"
  L1 = "l1"       # CB or kernel-local L1 stage
  SRCA = "srca"   # 16x16 weight / B-side FPU input
  SRCB = "srcb"   # 8x16 activation / A-side FPU input (higher fidelity)
  DST = "dst"     # 8x16 fp32 Dst slots (0..31 double-buf, 0..63 single-buf)
  LREG = "lreg"   # 32-lane SFPU vector register (L0..L7, allocated late in Pass 9)
  GPR = "gpr"     # RV32 scalar integer register

# --- Phase I: Tile-level SSA ops (NO machine instructions yet) ---

@dataclass(frozen=True)
class FpuOp:
  op: str                         # "MVMUL" | "ELWADD" | "ELWSUB" | "ELWMUL" | "GAPOOL" | "GMPOOL"
  m_blocks: int                   # number of 8x16 blocks along M (1 for decode, 1..2 for prefill)
  n_blocks: int                   # number of 8x16 blocks along N (e.g. N_BLK = 8 or 6 for MVMUL)
  k_faces: int = 1                # K faces per bank fill (e.g. 4 for 8x64 SrcB / 64x16 SrcA)
  fidelity: int = 3               # 3 (bf16/tf32), 2 (bfp8), 1 (bfp4)
  dst_slot: int | None = None     # assigned in Pass 5 (starting 8x16 slot index)
  role: str = "trisc1"

@dataclass(frozen=True)
class SfpLoadOp:                  # Space.DST -> Space.LREG boundary (1 footprint of 32 lanes)
  dst_slot: int | None = None     # base 8x16 slot assigned in Pass 5
  sub_row: int = 0                # optional row offset (0 or 1 for 2x-interleaved SFPLOADMACRO pairs)
  fmt: str = "fp32"               # "fp32" | "int32"
  role: str = "trisc1"

@dataclass(frozen=True)
class SfpStoreOp:                 # Space.LREG -> Space.DST boundary (1 footprint of 32 lanes)
  dst_slot: int | None = None     # base 8x16 slot assigned in Pass 5
  sub_row: int = 0
  fmt: str = "fp32"
  role: str = "trisc1"

@dataclass(frozen=True)
class SfpReduceLanes:             # Space.LREG -> Space.LREG horizontal 32-lane fold (SFPSHFT2 + SFPTRANSP)
  op: str                         # "add" | "max"
  role: str = "trisc1"

@dataclass(frozen=True)
class UnpackOp:
  target: Space                   # Space.SRCA | Space.SRCB | Space.DST (to_dest for fp32 SFPU)
  cb_id: int | None               # assigned in Pass 5 (0..31)
  src_dtype: DType                # format in L1 (bf16, fp32, bfp8, e4m3, bfp4)
  dst_dtype: DType                # format in Src/Dst (bf16, tf32, fp32)
  faces: int                      # consecutive faces unpacked before flipping dvalid (1..4)
  rows: int                       # 8 (activation) or 16 (weight)
  transpose: bool = False         # Haloize_mode=1 on Unpacker A
  dst_slot: int | None = None     # only when target == Space.DST
  role: str = "trisc0"

@dataclass(frozen=True)
class PackOp:
  cb_id: int | None               # assigned in Pass 5 (0..31)
  dst_dtype: DType                # format written to L1
  blocks: int                     # number of 8x16 Dst blocks packed
  dst_slot: int | None = None     # starting 8x16 slot assigned in Pass 5
  untilize: bool = False          # True ONLY for host_out buffers (PACR DstAccessMode=1)
  role: str = "trisc2"

@dataclass(frozen=True)
class NocRead:
  param_slot: int                 # DRAM PARAM slot (pointer loaded from L1 arg block 0x80 + 8*slot)
  cb_id: int | None               # target L1 CB stream ID (assigned in Pass 5)
  nbytes: int                     # bytes per transfer (or dynamic via src operand)
  tid: int = 0                    # NoC transaction ID
  role: str = "brisc"
  # UOp srcs: (flat_byte_offset_uop, [optional dynamic nbytes])

@dataclass(frozen=True)
class NocWrite:
  param_slot: int
  cb_id: int | None
  nbytes: int
  tid: int = 1
  role: str = "ncrisc"
  # UOp srcs: (packed_val_dep, flat_byte_offset_uop, [optional dynamic nbytes])

# --- Phase II: Sync ops inserted ONLY in Pass 7 on list[UOp] ---

@dataclass(frozen=True)
class CbOp:
  kind: str                       # "reserve" | "push" | "wait" | "pop"
  cb_id: int
  pages: int
  role: str                       # producer ("brisc"|"trisc2") or consumer ("trisc0"|"ncrisc")

@dataclass(frozen=True)
class SemOp:
  kind: str                       # "init" | "wait_space" | "post" | "wait_data" | "get"
  sem_id: int                     # 0 = math_pack
  max_val: int                    # 2 (double-buffered Dst) or 1 (single-buffered)
  toggle_dst: bool = False        # toggle dst_offset = (iter & 1) * 256
  role: str                       # "trisc1" or "trisc2"

@dataclass(frozen=True)
class StallOp:
  stall: str                      # "sync" | "math" | "sfpu" | "pack" | "unpack"
  wait: str                       # "math|sfpu" | "math" | "sfpu" | ...
  role: str                       # "trisc0" | "trisc1" | "trisc2"

@dataclass(frozen=True)
class NocWait:
  tid: int
  acked: bool                     # False for writes if only outgoing drain needed, True for reads
  role: str                       # "brisc" or "ncrisc"
```

---

## 4. Pass-by-Pass Specification

### Pass 1: Kernel Classification
Inspect the Layer 1 kernel `SINK` (from `rangeify.py`, with N-D `INDEX(RESHAPE(PARAM, max_sh), *idxs)` intact):
- **Pure RV32/NoC kernel** iff:
  - No float `REDUCE` (or only integer/boolean ops, or pure gather/scatter/copy like `Embedding` and `KV-cache write`), OR
  - Output total elements `<= 16` with pure integer/scalar logic (e.g. `argmax` final reduction on a single core if desired, though `argmax` can also use SFPU).
  - *Action:* Bypass Tensix passes (Passes 3–5, 7); lower directly to `brisc` (`NocRead`/`NocWrite` + RV32 loops) with `ROLE_PC[trisc0..2] = 0` (and `ncrisc = 0` if single-core copy).
- **Tensix kernel:** everything with float compute (`MVMUL`, `ELW*`, `SFPU`, `REDUCE`). Runs Passes 2–10.

### Pass 2: Sharding + Face Tiling + Uniform `PADTO`
Input: Layer 1 `SINK` with logical ranges `r0, r1, ...` and N-D `INDEX(RESHAPE(buf, shape), *idxs)`.

1. **Identify storage roles for each `PARAM` / L1 `ALLOC`:**
   - Weight buffer (`is_weight`): 2D+ read-only `PARAM` whose last two axes are `(N, K)` consumed by a matmul (`REDUCE(ADD, MUL(act, w))`) where `K` is the reduced axis and `N` is an output parallel axis. Physical face shape = `(16, 16)`.
   - Activation buffer (all other buffers, including outputs, residuals, L1 stages, KV cache): physical face shape = `(8, 16)`.
   - Scalar `(1,)` L1/DRAM buffers (like RMSNorm's `l1: fp32 (1,)`): single `8×16` slot (lane 0 or broadcast across all lanes).
2. **Split inner axes into `(outer_face, intra_face)` pairs (`PADTO`):**
   - For every matrix/vector axis mapped to the last dim `N` (cols): split `r_n ∈ [0, N)` into `f_n ∈ [0, ceil(N / 16))` and `i_n ∈ [0, 16)`, substituting `r_n -> f_n * 16 + i_n`. If `N % 16 != 0` (or symbolic like `start_pos + 1`), attach validity gate `f_n * 16 + i_n < N` (emitted as `WHERE(valid, val, identity)`: `0.0` for `ADD`/matmul, `-inf` for `MAX`).
   - For every matrix row axis `M`: split `r_m ∈ [0, M)` into `f_m ∈ [0, ceil(M / 8))` and `i_m ∈ [0, 8)`. For decode `M = 1`, `f_m = 0` and `i_m ∈ [0, 8)` with valid `i_m == 0` (rows `1..7` are harmless padding in the `8×16` face).
   - For matmul `K` reduction axis: split `r_k ∈ [0, K)` into `f_k ∈ [0, ceil(K / 16))` and `i_k ∈ [0, 16)`.
   - Run `sym` (`symbolic + div_and_mod_symbolic + pm_simplify_valid`) so every static-multiple gate (`7168 % 16 == 0`, `22016 % 16 == 0`, `128 % 16 == 0`) vanishes immediately!
3. **Register-block `MVMUL` output strips (`N_BLK`) and `K` bank-fill (`K_BLK`):**
   - For a matmul with `F_N = ceil(N / 16)` output column faces: pick `N_BLK = 8` if `F_N % 8 == 0` (or `N_BLK = 6` if `F_N % 6 == 0`, else `min(F_N, 8)` with tail mask). Split `f_n` into `(strip_n ∈ [0, ceil(F_N / N_BLK)), sub_n ∈ [0, N_BLK))`.
   - Pick `K_BLK = 4` (if `F_K % 4 == 0`, else `2` or `1`): unpack `4 × (8×16)` activation faces into `SrcB` and `4 × (16×16)` weight faces into `SrcA` per `dvalid` bank flip.
4. **Shard outer parallel work units `W` across `N_workers = min(W, num_workers)`:**
   - Collect outer parallel ranges (e.g. `strip_n` for matmul, `head_h` for fused multi-head attention, `(f_m, f_n)` for elementwise). Let `W` be their product.
   - Mint `wid = UOp.special(N_workers, "worker_id")`.
   - Split `W` into contiguous balanced blocks per worker:
     - `q, r = divmod(W, N_workers)`
     - If `r == 0` (exact split, e.g. `56` strips on `56` workers → `1` strip/core, or `448` faces on `112` workers → `4`/core): `work_idx = wid * q + local_i` for `local_i = UOp.range(q)`.
     - If `r != 0`: `start = wid * q + min(wid, r)`, `count = q + (wid < r)` (plain `WHERE`), `work_idx = start + local_i` for `local_i = UOp.range(count)`.
   - Guard unused cores at kernel entry if `N_workers < num_workers` (`if wid >= N_workers: ret`).

### Pass 3: Unified FPU Matching + SFPU Footprint Structuring (Still Abstract!)
Walk the tiled SSA DAG bottom-up inside the outer tile loops (above intra-face ranges `i_m, i_n, i_k, sub_n`):

1. **Match FPU idioms (closed over intra-face ranges `i_m, i_n, i_k`):**
   - **`MVMUL`:** `REDUCE(ADD, (f_k, i_k), CAST(MUL(a, b), fp32))` (or `MUL(CAST(a, fp32), CAST(b, fp32))`) where `a` depends on `(i_m, i_k)` (activation → `SrcB`) and `b` depends on `(i_n, i_k)` (weight → `SrcA`), and `a.dtype, b.dtype ∈ {bf16, bfp8, e4m3, bfp4, fp32}`.
     - Replace the inner `(i_k, i_m, i_n, sub_n)` contraction with `acc = UOp.ins(FpuOp("MVMUL", m_blocks, n_blocks, k_faces, fidelity), (tile_b, tile_a), dtypes.fp32)` inside the outer `f_k` reduction loop (producing an `m_blocks × n_blocks` tile-group value in `Space.DST` after closing `f_k`).
   - **`ELWADD` / `ELWSUB` / `ELWMUL`:** `ADD`/`SUB`/`MUL` on two `<= bf16` tile values (if NOT already inside an SFPU-only chain that must stay fp32!).
     - Replace with `UOp.ins(FpuOp("ELWADD"|"ELWSUB"|"ELWMUL", m_blocks, n_blocks), (tile_a, tile_b), dtypes.fp32)`.
2. **Keep SFPU math as plain core ALU `UOp`s in `Space.LREG` inside a `RANGE(fp)` loop:**
   - Do **not** wrap SFPU in `CALL(SINK)` and do **not** emit `SFP*` words yet.
   - Plain `UOp` ALU ops (`ADD`, `SUB`, `MUL`, `EXP2`, `LOG2`, `SIN`, `SQRT`, `RECIP`, `CMPLT`, `CMPEQ`, `WHERE`, `CAST`, `BITCAST`, bitwise ops) **are** the abstract SFPU IR — their space is `Space.LREG` (`role="trisc1"`).
   - Collapse the `(i_m ∈ [0, 8), i_n ∈ [0, 16))` intra-face axes of an `m_blocks × n_blocks` SFPU region into a structured footprint loop `fp = RANGE(4 * m_blocks * n_blocks, name="fp")` (each footprint = 32 SFPU lanes stepping `INCRWC dst+2`; optionally split into `RANGE(m_blocks * n_blocks)` × `RANGE(2, name="pair")` with `sub_row ∈ {0, 1}` when 2×-interleaving for `SFPLOADMACRO`).
   - For SFPU reductions over an inner face axis (e.g. RMSNorm `sum(x^2)` or softmax `max`): keep `REDUCE(op, (f_k, fp), lreg_expr)` in `Space.LREG` (accumulated in a loop-carried `LReg` in Pass 9), followed by `UOp.ins(SfpReduceLanes(op), (acc,), dtypes.fp32)` after the loop to fold the 32 lanes into a broadcast scalar.
   - **Why this works:**
     - `Dst` allocation (Pass 5) only sees `Space.DST` values (`FpuOp`, `UnpackOp(DST)`, `SfpStoreOp`, `PackOp`) — **never** `Space.LREG` intermediates.
     - FPU → SFPU (`MVMUL` → `silu` or `add(residual)`) connects in place through `Space.DST` with zero `PACR`/`UNPACR`.
     - Because `RANGE(fp)` remains a real `RANGE`/`END` around the `trisc1` ops all the way into Pass 9, `SFPLOADMACRO → REPLAY → MOP` can match and collapse it directly!

### Pass 4: Space Marking & Transfer Insertion (Mechanical Edge-Transition Table)
Every node in the tile DAG now has an output `Space` and required input `Space`s:

| Node | Required Input Space(s) | Output Space |
|---|---|---|
| `PARAM` (DRAM buffer) | — | `DRAM` |
| `ALLOC(..., space="l1")` | — | `L1` |
| `NocRead` | `(DRAM, byte_offset: GPR)` | `L1` (streaming CB) |
| `NocWrite` | `(L1, byte_offset: GPR)` | `DRAM` |
| `UnpackOp(SRCA/SRCB)` | `L1` | `SRCA` or `SRCB` |
| `UnpackOp(DST)` (`to_dest`) | `L1` | `DST` |
| `FpuOp(MVMUL/ELW*)` | `(SRCB, SRCA)` | `DST` |
| `SfpLoadOp` | `DST` | `LREG` |
| Core ALU `UOp`s (inside `RANGE(fp)`) / `SfpReduceLanes` | `LREG` | `LREG` |
| `SfpStoreOp` | `LREG` | `DST` |
| `PackOp` | `DST` | `L1` |

**One bottom-up rewrite pass** walks every edge `(producer -> consumer)` where `producer.space != consumer.expected_space` and inserts the exact chain from this table:

| Edge `producer -> consumer` | Inserted Transfer Chain |
|---|---|
| `DRAM -> L1` (read of DRAM `PARAM`) | Compute flat face byte offset `(batch_off + f_m * nc + f_n) * face_bytes` as pure integer UOps → `UOp.ins(NocRead(param_slot, None, nbytes), (byte_off,))` |
| `DRAM -> SRCB / SRCA` | `NocRead` (`DRAM -> L1`) → `UnpackOp(SRCB/SRCA)` (`L1 -> SRC*`) |
| `DRAM -> DST` / `DRAM -> LREG` (e.g. `fp32` SFPU input or residual add on SFPU) | `NocRead` (`DRAM -> L1`) → `UnpackOp(DST)` (`L1 -> DST`) → (`SfpLoadOp` if consumer is `LREG`) |
| `L1 -> SRCB / SRCA` (from kernel-local `ALLOC(space="l1")`) | `UnpackOp(SRCB/SRCA)` (**NO NoC op!**) |
| `L1 -> DST` / `L1 -> LREG` (from kernel-local `ALLOC(space="l1")`) | `UnpackOp(DST)` → (`SfpLoadOp` if `LREG`) (**NO NoC op!**) |
| `DST -> LREG` (`FpuOp` or `UnpackOp(DST)` → SFPU ALU op) | `SfpLoadOp` (stays in place in `Dst`; Pass 7 inserts `STALLWAIT(sync, math|sfpu)` if preceded by `FpuOp`) |
| `LREG -> LREG` (SFPU ALU → SFPU ALU) | **Nothing!** Stays in `L0..L7` (zero `Dst` traffic, zero `Dst` slot consumed!). |
| `LREG -> DST` (SFPU result feeding `PackOp` or another phase) | `SfpStoreOp` (inside `RANGE(fp)`, writing back to `Dst` slot) |
| `DST -> SRCB / SRCA` (SFPU `SfpStoreOp` → `FpuOp`, e.g. softmax `P -> P @ V`) | `PackOp` (`DST -> L1` `pages=1` CB) → `UnpackOp(SRCB/SRCA)` (`L1 -> SRC*`) (or `MOVD2A`/`MOVD2B` if single face) |
| `DST -> L1` (store to kernel-local `ALLOC(space="l1")`) | `PackOp` (`DST -> L1`, `untilize=False`) (**NO NoC op!**) |
| `DST -> DRAM` (store to DRAM output `PARAM`) | `PackOp` (`DST -> L1`, `untilize=is_host_out`) → `NocWrite(param_slot, None, nbytes)` (`L1 -> DRAM`) |

**Face byte-offset formula (replaces `FaceLayout`):**
- Given `INDEX(RESHAPE(param, shape), *coords)` tiled into `(batch_coords..., f_m, f_n)`:
  - `face_rows = 16 if is_weight else 8`
  - `mr = ceil(M / face_rows)`, `nc = ceil(N / 16)`
  - `face_bytes`: `face_rows * 16 * itemsize` for `bf16`/`fp32`/`e4m3`/`i32`; `272` (`16 + 256`) for `bfp8` `16×16`; `144` (`16 + 128`) for `bfp4` `16×16`.
  - `flat_face_idx = (batch_linear * mr + f_m) * nc + f_n`
  - `byte_offset = flat_face_idx * face_bytes` (pure integer `UOp`, simplified by `sym`!).
- Notice: if a contiguous `K_BLK = 4` strip of faces is read together (`f_n = k_outer * 4 + 0..3`), `NocRead` issues **one** transfer of `4 * face_bytes` at `flat_face_idx = ... + k_outer * 4`!

### Pass 5: Static Tile Resource Allocation (No `Dst` Spilling!)
Run three simple static allocators on the tile DAG (still structured, before linearization):

1. **CB Stream & L1 Allocator (`CB 0..31`):**
   - Every `NocRead` stream gets a streaming CB (`pages = DEPTH * BATCH`, default `DEPTH = 2`).
   - Every `NocWrite` stream gets an output CB (`pages = DEPTH * BATCH`).
   - Every kernel-local `ALLOC(..., space="l1")` (e.g. `l0`, `l1` from 3-tier fusion) gets a **`pages = 1` static CB** whose L1 address is assigned by `compiler/memory.py:plan_l1_memory`.
   - Every `UnpackOp(DST)` → `SfpLoadOp` pair gets a **0-byte phase-barrier CB** (`pages = 1`, `nbytes = 0`, matching `gdn_state.ttrv`) so `trisc0` and `trisc1` synchronize on `Dst` ownership!
   - Streaming CB ring buffers are laid out contiguously in L1 right after `code_end + static_l1_plan.peak_bytes` (64B-aligned), sized to fit `1.5 MB` L1.
2. **Hard-Budget `Dst` `8×16` Slot Assigner (`DST[0..31]` or `DST[0..63]`):**
   - Compute live intervals of **`Space.DST` tile-group values ONLY** (`FpuOp`, `UnpackOp(DST)`, `SfpStoreOp`, `PackOp` — never `Space.LREG` ALU ops!). Each value occupies `m_blocks * n_blocks` contiguous `8×16` slots.
   - Attempt interval coloring within `32` slots (`double_buf = True`, `sem math_pack max=2`).
   - If peak live slots `> 32`:
     1. First try shrinking `MVMUL` `N_BLK` (`8 -> 6`, or `4`).
     2. Otherwise allow `64` slots (`double_buf = False`, `sem math_pack max=1`).
     3. If still `> 64`: **never spill `Dst`** — demote an intermediate to a `pages=1` L1 CB (`PackOp` → `UnpackOp`).
   - Stamp concrete `dst_slot` onto every `FpuOp`, `SfpLoadOp`, `SfpStoreOp`, `UnpackOp(DST)`, and `PackOp`. (Reserve 1 spare `Dst` row if `trisc1`'s late `L0..L7` `regalloc` ever needs an `LReg` spill slot.)

---

### Pass 6: Joint Linearization (ONCE!)
Call the fixed `linearize_tile_graph(sink) -> list[UOp]` **once** on the unified tile DAG.
- Output is a single flat `list[UOp]` containing:
  - `Ops.RANGE` / `Ops.END` loop markers (strictly nested, never interleaved — including `RANGE(fp)` around `SfpLoadOp → ALU → SfpStoreOp` so `brisc`/`trisc0` ops never interleave into an SFPU body),
  - Pure integer address/index `UOp`s (untagged, backward-sliced per core in Pass 8),
  - Role-inherent tile ops (`NocRead[brisc]`, `UnpackOp[trisc0]`, `FpuOp[trisc1]`, `SfpLoadOp`/`SfpStoreOp`/`SfpReduceLanes` + `Space.LREG` ALU `[trisc1]`, `PackOp[trisc2]`, `NocWrite[ncrisc]`).
- **From this point onward, list order IS execution order. Zero `AFTER` tokens are needed.**

### Pass 7: Matched Intra-Core Sync Insertion (1 Linear Pass)
Walk the joint `list[UOp]` once, emitting matched producer/consumer sync pairs (`CbOp`, `SemOp`, `StallOp`, `NocWait`) at the exact same loop nesting depth:

1. **Streaming CBs (`brisc -> trisc0` and `trisc2 -> ncrisc`):**
   - Around each `NocRead(cb, ...)`:
     - Before: `CbOp("reserve", cb, batch, role="brisc")`
     - After: `NocWait(tid, acked=True, role="brisc")`, `CbOp("push", cb, batch, role="brisc")`
     - *(Note: for pipelined reads, `NocWait` + `CbPush` can be emitted right after `NocRead` for bring-up, then overlapped across 1 iteration later.)*
   - Around each `UnpackOp(cb, ...)` consuming a streaming CB:
     - Before: `CbOp("wait", cb, batch, role="trisc0")`
     - After: `CbOp("pop", cb, batch, role="trisc0")`
   - Around each `PackOp(cb, ...)` producing an output CB:
     - Before: `CbOp("reserve", cb, batch, role="trisc2")`
     - After: `CbOp("push", cb, batch, role="trisc2")`
   - Around each `NocWrite(cb, ...)` consuming an output CB:
     - Before: `CbOp("wait", cb, batch, role="ncrisc")`
     - After: `NocWait(tid, acked=False, role="ncrisc")` (with final `acked=True` before exit), `CbOp("pop", cb, batch, role="ncrisc")`
2. **Static `pages=1` L1 Stage CBs (e.g. RMSNorm `l0` read across all `N` strips):**
   - Producer (`trisc2` `PackOp` or `brisc` `NocRead` loop): wrap the **entire producing loop** with `CbOp("reserve", cb, 1)` before the loop and `CbOp("push", cb, 1)` after its `END`.
   - Consumer (`trisc0` `UnpackOp` inside a reusing loop): hoist `CbOp("wait", cb, 1)` **before** the reusing loop and `CbOp("pop", cb, 1)` **after** the reusing loop's `END`!
3. **`trisc0 -> trisc1` (`SrcA`/`SrcB` vs `Dst`):**
   - `UnpackOp(SRCA/SRCB)` ↔ `FpuOp`: hardware `dvalid` (`set_dvalid=1` on the last `UNPACR` of the bank fill; `FpuOp` clears `dvalid` on its last phase/use). No extra sync UOp needed!
   - `UnpackOp(DST)` ↔ `SfpLoadOp` / `FpuOp`: use the 0-byte phase-barrier CB (`trisc0` pushes `loaded_cb` after `UnpackOp(DST)`, `trisc1` waits `loaded_cb` before `RANGE(fp)` and pops after `END(fp)`).
4. **`trisc1` internal (`FpuOp <-> SFPU`):**
   - Whenever an `FpuOp` is followed by `RANGE(fp)` / `SfpLoadOp` on overlapping `Dst` slots: insert `StallOp("sync", "math|sfpu", role="trisc1")` before `RANGE(fp)`.
   - Whenever `SfpStoreOp` / `END(fp)` is followed by `FpuOp` on overlapping `Dst` slots: insert `StallOp("sync", "sfpu", role="trisc1")`.
5. **`trisc1 <-> trisc2` (`Dst` ownership via `sem math_pack`):**
   - Emit `SemOp("init", sem_id=0, max_val=2 if double_buf else 1, role="trisc1")` in prologue (or reuse `boot.c`'s `SEMINIT_ALL` if `max_val == 1`).
   - Before the first `trisc1` op writing a `Dst` group in an output iteration: `SemOp("wait_space", 0, max_val, toggle_dst=double_buf, role="trisc1")`.
   - After the last `trisc1` op on that `Dst` group: `StallOp("sync", "math|sfpu", role="trisc1")` + `SemOp("post", 0, max_val, role="trisc1")`.
   - Before `trisc2` `PackOp` on that `Dst` group: `SemOp("wait_data", 0, max_val, toggle_dst=double_buf, role="trisc2")`.
   - After `trisc2` `PackOp`: `StallOp("sync", "pack", role="trisc2")` + `SemOp("get", 0, max_val, role="trisc2")`.

### Pass 8: 5-Core Projection (`project_roles`)
Split the synced joint `list[UOp]` into 5 independent per-core `list[UOp]`s (`brisc`, `ncrisc`, `trisc0`, `trisc1`, `trisc2`):
1. Determine which `RANGE`/`END` pairs contain at least one op owned by role `r`.
2. For each role `r`, compute the **backward dependency closure** over pure untagged UOps starting from:
   - the operands of every op owned by `r`, and
   - the bound `src[0]` of every `RANGE` kept by `r`.
3. Emit into `buckets[r]` (preserving original list order):
   - every op owned by `r`,
   - every kept `RANGE` and its matching `END`,
   - every pure untagged UOp in `r`'s backward closure (so **only `brisc` gets read address math**, **only `ncrisc` gets write address math**, and **`trisc0/1/2` get zero DRAM address math**!).

---

### Pass 9: Late Per-Core Recipe Expansion & `StateTracker` Config Diffing
Now each core has its own clean `list[UOp]` (still with structured `RANGE`/`END` loops). Expand abstract tile/sync specs into concrete `RVOps`, `hw_isa.Tensix`, and `SfpSpec` instructions using the 3 hardware state trackers (Turn 15):

- **`TileStateTracker`** (shared `Space.CONFIG` `TENSIX_CFG` words, initialized to `boot.c:reset_tensix()` values): diffs `THCON_SEC0/1`, `ALU_FORMAT`, `fp32_dest_acc=1`, `PCK0` formats/strides, emitting minimal `RMWCIB0..3` / `TENSIX_CFG` `SW`s.
- **`TriscStateTracker` (×3)** (private `Space.THREAD`, initialized to `boot.c:reset_thread()` values): tracks `ADDR_MOD[0..7]`, `PACK_ADDR_MOD[0..3]`, `dst_offset`, `unpack_ctx_offset`, `RWC`/`ADC`, `MOP_CFG`, `REPLAY[0..32)`, `SFPCONFIG` `L11..L14`. Intersects to `UNKNOWN` at loop headers and `if/else` joins so a diff never elides a required write across control flow.
- **`NocStateTracker` (×2)** (private to `brisc`/`ncrisc`, initialized to `boot.c:noc_init_worker()` values): tracks per-`CMD_BUF` sticky fields (used if emitting inline NoC MMIO instead of `jal FN_NOC_*`).

**Per-core expansions:**
1. **`brisc` / `ncrisc`:**
   - `CbOp("reserve"|"wait"|"push"|"pop")` → overlay stream `LW`/`LHU`/`SW` on `OVERLAY_STREAMS + (8 + cb_id) * 0x1000` + `FENCE` + `BACKEDGE` poll loops (tracking local ring cursor in a virtual GPR).
   - `NocRead` / `NocWrite` → load `(buf_lo, buf_hi)` from L1 Arg Block `0x80 + 8 * param_slot`, set RV32 ABI arg regs, `JAL` to resident `FN_NOC_READ` / `FN_NOC_WRITE` (`0x70`/`0x74`).
   - `NocWait` → `JAL FN_NOC_WAIT` (`0x78`).
2. **`trisc0`:**
   - `CbOp("wait"|"pop")` → overlay stream poll + cursor advance (yielding L1 byte/16B-word address for `UNPACR`).
   - `UnpackOp` → `TileStateTracker` + `TriscStateTracker` diffs (`THCON_SEC0/1` format/strides, TF32 `row=64, face=1024` when `dst_dtype == tf32`, `Haloize_mode=1` when `transpose=True`) → `SETADC*` → `UNPACR` (with `set_dvalid=1` on last face of bank fill, or `UNPACR to_dest` for `Space.DST`).
3. **`trisc1`:**
   - `SemOp` → `SEMINIT` / `SEMWAIT(STALL_ON_MAX)` / `SEMPOST` + `SETC16(dst_offset)` toggle.
   - `StallOp` → `STALLWAIT`.
   - `FpuOp("MVMUL")` → `ZEROACC` on `dst_slot..dst_slot+m*n-1` (once before `K` loop) + `TileStateTracker`/`TriscStateTracker` diffs (`ALU_FORMAT`, `ADDR_MOD`s) + unrolled `MVMUL` schedule rotating across all `N_BLK` distinct `8×16` `Dst` blocks (hiding 6-cycle `Dst` RAW latency → 1.0 cyc/op) × `fidelity` phases `{0,1,2}`, clearing `dvalid` on the final phase.
   - `FpuOp("ELW*")` → `ELWADD`/`ELWSUB`/`ELWMUL` across `m_blocks × n_blocks` `8×16` blocks.
   - **SFPU (`SfpLoadOp` → `Space.LREG` ALU ops → `SfpStoreOp` / `SfpReduceLanes` inside `RANGE(fp)`):**
     1. Run `compiler/sfpu.py`'s decomposition + FMA rewrites (`pm_sfpu_decomp + pm_sfpu_fma`) on the `Space.LREG` UOps (`exp2`/`log2`/`sin`/`recip`/`rsqrt`/`sqrt` → `MULACC`/`SfpPrim`).
     2. Select `sfp_ins` (`SfpSpec`) with virtual `LReg`s:
        - `SfpLoadOp(dst_slot, sub_row)` → `sfp_ins(SFPLOAD, ..., addr=dst_slot*8 + sub_row, *vreg(choices))` — **key for future `SFPLOADMACRO`:** constrain `choices` to `(L0..L3)` when `(dst_row & 1) == 0` and `(L4..L7)` when `(dst_row & 1) == 1` so Blackhole's `(dst_row & 1) == (r // 4)` parity rule is satisfied automatically!
        - `MULACC`, `ADD`, `MUL`, `WHERE` (`SFPSETCC`/`SFPPUSHC`/`SFPCOMPC`/`SFPPOPC`), `SfpPrim` → `sfp_ins(...)` with `vreg(L0..L7)` (plus `L8..L14` constant tiering hoisted via `SFPCONFIG`).
        - `SfpStoreOp(dst_slot, sub_row)` → `sfp_ins(SFPSTORE, ..., addr=dst_slot*8 + sub_row)`.
        - Append `tt_ins(INCRWC(dst=2))` at the end of `RANGE(fp)` (or `INCRWC(dst=4)` for 2×-interleaved pairs).
        - `SfpReduceLanes` → `SFPSHFT2` + `SFPTRANSP` fold after the reduction loop.
     3. Run the **shared CFG-aware `regalloc`** ([compiler/isa/__init__.py:91](../compiler/isa/__init__.py#L91)) on `file="lreg"` (`L0..L7`, with loop-carried reduction accumulators naturally kept live across the `RANGE` backedge, and `spill`/`fill` borrowing 1 spare `Dst` row if needed).
4. **`trisc2`:**
   - `SemOp` → `SEMWAIT(STALL_ON_ZERO)` / `SEMGET` + `SETC16(dst_offset)` toggle.
   - `CbOp("reserve"|"push")` → overlay stream poll + cursor advance.
   - `PackOp` → `TileStateTracker`/`TriscStateTracker` diffs (`PCK0` format, `DstAccessMode=1` if `untilize`) → `SETADC*` → `2 * blocks` `PACR` words (`4×16` per `PACR`, `last=1` on final).
5. **Optional Late TRISC Compression Passes (strictly optional for v1, structurally guaranteed viable!):**
   - Because **both** FPU and SFPU have now expanded to concrete, register-allocated 32-bit `tt_ins` / `sfp_ins` words **while `RANGE`/`END` loops are still intact** (before Pass 10 lowers `RANGE`/`END` to RV32 branches), all three hardware compression passes drop directly onto each TRISC's `list[UOp]` in reverse pipeline order:
     1. **`SFPLOADMACRO`** (`trisc1` peephole): anchors on `SFPLOAD r, dst[off]` (whose `r` already respects `(dst_row & 1) == (r // 4)` parity!), fuses up to 1 op per sub-unit (`simple`, `mad`, `round`, `store`) within `0..7` delays, hoists `SFPCONFIG` templates to prologue, and replaces the chain with 1 `SFPLOADMACRO` word.
     2. **`REPLAY`** (per-TRISC, `trisc0`/`trisc1`/`trisc2`, 32-word budget): deduplicates contiguous runs of `2..32` constant Tensix words (FPU `MVMUL` strips, `UNPACR`/`PACR` runs, and SFPU / `SFPLOADMACRO` bodies alike), hoists `REPLAY(load=1)` to prologue, replaces each occurrence with 1 `REPLAY(run)` word.
     3. **`MOP` Template 1** (per-TRISC, `trisc0`/`trisc1`/`trisc2`): matches 1- or 2-level static-count `RANGE`/`END` nests (`1..1023`) whose body has shrunk to `<= 1` prologue word, `1–2` inner words (e.g. `REPLAY(run)` + `INCRWC`), and `<= 2` epilogue words; hoists `ttsync` + `MOP_CFG` `SW`s to prologue and replaces the entire loop nest with **1 `MOP` word**. Non-matching or dynamic (`start_pos`) loops stay plain RV32 loops.

### Pass 10: Per-Core RV32 Lowering & `BH01` Assembly
On each of the 5 per-core `list[UOp]`s (using `BlackholeRenderer.compile_core`):
1. Run `RV32` `isel` on remaining pure scalar/index `UOp`s (loop bounds, DRAM byte offsets, CB pointers, `SPECIAL("worker_id")`, runtime `PARAM` arg loads).
2. `pre_regalloc`: lower remaining `RANGE`/`END` → counter `LI 0`, `LABEL`, `BGE`/`BGEU`, `ADDI +1`, `JAL`; lower `IF` → branch + labels.
3. `regalloc`: CFG-aware graph coloring on `x6..x29` (spilling via `x30..x31` to `LOCAL_BASE`).
4. `post_regalloc`: expand `LI` → `LUI`+`ADDI`, drop no-op moves, strip structural markers, append `fw/park.c` exit epilogue.
5. `trisc1` only: `fix_sfpu_hazards_uops` (inserting `SFPNOP` on undetected SFPU RAW hazards, including loop wraparound).
6. Long-branch relaxation + `assemble` → 5 binary images → `pack_bundle` (`BH01`) → `Ops.PROGRAM`.

---

## 5. Worked Example: Nanbeige `down_proj + residual` (Kernel 8)

### Input: Real Layer 1 N-D Kernel from `rangeify.py`
```text
%0  = param 7168 slot=0 dtype=bf16           # out:      bf16 (1, 1, 7168)
%1  = reshape %0 [1 1 7168]
%2  = range 7168 axis=0                      # N = 7168 (448 faces of 16)
%3  = index %1 0 0 %2
%4  = param 7168 slot=1 dtype=bf16           # residual: bf16 (7168,)
%6  = load (index %4 %2)                     # bf16
%7  = param 22016 slot=2 dtype=bf16          # x:        bf16 (22016,)
%8  = range 22016 axis=1                     # K = 22016 (1376 faces of 16)
%10 = load (index %7 %8)                     # bf16
%11 = param 157810688 slot=3 dtype=bf16      # W:        bf16 (7168, 22016)
%12 = reshape %11 [7168 22016]
%14 = load (index %12 %2 %8)                 # bf16
%15 = mul %10 %14                            # bf16
%16 = cast %15 dtype=fp32                    # fp32
%17 = reduce %16 %8 op=add n=0               # fp32  <-- matmul dot product
%18 = cast %17 dtype=bf16                    # bf16
%19 = add %6 %18                             # bf16  <-- residual add
%20 = store %3 %19
%21 = end %20 %2
%22 = sink %21 name=''
```

### After Pass 1–2 (Classify → Shard + Face-Tile + `N_BLK=8`, `K_BLK=4`)
- **Classification:** Tensix kernel (`M=1`, `N=7168` → `448` faces = `56` strips of `N_BLK=8` → `N_workers = 56`, `1` strip per core; `K=22016` → `1376` faces = `344` chunks of `K_BLK=4`).
- `wid = SPECIAL("worker_id", 56)` (guard: `if wid >= 56: ret`).
- `strip_n = wid` (0..55); `sub_n ∈ [0, 8)`; `i_n ∈ [0, 16)`; `i_m ∈ [0, 8)` (decode row 0 valid).
- `k_blk = RANGE(344)` (outer K chunks of 4 faces); `sub_k ∈ [0, 4)`; `i_k ∈ [0, 16)`.
- Because `7168 % 128 == 0` and `22016 % 64 == 0`, `sym` proves all validity gates `True` and deletes them.

### After Pass 3 (Match FPU + Structure SFPU `RANGE(fp)` — Still Pure SSA!)
```text
# Inside wid ∈ [0, 56):
acc_k  = REDUCE_TILE(k_blk in 0..344):
           FpuOp("MVMUL", m=1, n=8, k=4, fidelity=3)(
             x_tile[k_blk],                      # 4 x (8x16) bf16 -> SrcB
             W_tile[wid, k_blk]                  # 8 x 4 x (16x16) bf16 -> SrcA
           )                                     # -> 8 x (8x16) fp32 in Dst
res_t  = LOAD_TILE(residual[wid])                # 8 x (8x16) bf16 -> Dst

# Residual add stays plain core ALU (ADD) in Space.LREG inside RANGE(fp = 4*8 = 32):
RANGE fp in 0..32:                               # (or 8 blocks x 2 pairs for 2x-interleaved SFPLOADMACRO)
  v_acc = SfpLoadOp(acc_k)                       # Space.DST -> Space.LREG
  v_res = SfpLoadOp(res_t)                       # Space.DST -> Space.LREG
  v_out = ADD(v_acc, v_res)                      # plain Ops.ADD in Space.LREG!
  out_t = SfpStoreOp(v_out)                      # Space.LREG -> Space.DST
END fp
STORE_TILE(out[wid], CAST(out_t, bf16))
```

### After Pass 4–5 (Spaces, Transfers, Static CB & `Dst` Allocation)
- **CBs:** `cb_x = 0` (`DEPTH=2`, `4 × 256 B = 1024 B/page`), `cb_w = 1` (`DEPTH=2`, `32 × 512 B = 16 KB/page`), `cb_res = 2` (`pages=1`, `8 × 256 B = 2 KB`), `cb_out = 3` (`pages=1`, `8 × 256 B = 2 KB`), `cb_res_loaded = 4` (0-byte phase barrier `trisc0 -> trisc1`).
- **`Dst` slots (`double_buf=True`, `32` slots/half):** `acc_k -> Dst[0..7]` (rows `0..63`), `res_t -> Dst[8..15]` (rows `64..127`), `out_t -> Dst[0..7]` (in-place!). Peak = `16 <= 32` slots → fits cleanly with zero spilling. (`v_acc`, `v_res`, `v_out` are `Space.LREG` — zero `Dst` slots consumed!)
- **Byte offsets (pure integer UOps, simplified by `sym`):**
  - `off_x   = k_blk * 1024` (`4 * 8 * 16 * 2`)
  - `off_w   = (wid * 8 * 1376 + k_blk * 4) * 512` (or per-`sub_n` row: `((wid * 8 + sub_n) * 1376 + k_blk * 4) * 512`, `2048 B` per `sub_n`)
  - `off_res = wid * 2048` (`8 * 8 * 16 * 2`)
  - `off_out = wid * 2048`

### After Pass 6–7 (Joint Linear Stream + Matched Sync Insertion)
```text
# Prologue (all cores check wid < 56)
[trisc1] SemOp(init, sem=0, max=2)
[trisc1] SemOp(wait_space, sem=0, max=2, toggle_dst=True)
[trisc1] ZEROACC(slots 0..7)                     # (expanded in Pass 9)

RANGE k_blk in 0..344:
  [brisc]  CbOp(reserve, cb=0, 1)
  [brisc]  NocRead(slot=2, cb=0, 1024B, off=k_blk*1024)
  [brisc]  NocWait(tid=0, acked=True)
  [brisc]  CbOp(push, cb=0, 1)
  [trisc0] CbOp(wait, cb=0, 1)
  [trisc0] UnpackOp(SRCB, cb=0, bf16, faces=4, rows=8)
  [trisc0] CbOp(pop, cb=0, 1)

  RANGE sub_n in 0..8:                           # (or unrolled 2x4)
    [brisc]  CbOp(reserve, cb=1, 1)
    [brisc]  NocRead(slot=3, cb=1, 2048B, off=((wid*8+sub_n)*1376 + k_blk*4)*512)
    [brisc]  NocWait(tid=0, acked=True)
    [brisc]  CbOp(push, cb=1, 1)
    [trisc0] CbOp(wait, cb=1, 1)
    [trisc0] UnpackOp(SRCA, cb=1, bf16, faces=4, rows=16)
    [trisc0] CbOp(pop, cb=1, 1)
    [trisc1] FpuOp(MVMUL, dst_slot=sub_n, k=4, fidelity=3)
  END sub_n
END k_blk

# Residual load + in-place SFPU add on Dst[0..7]
[brisc]  CbOp(reserve, cb=2, 1)
[brisc]  NocRead(slot=1, cb=2, 2048B, off=wid*2048)
[brisc]  NocWait(tid=0, acked=True)
[brisc]  CbOp(push, cb=2, 1)
[trisc0] CbOp(wait, cb=2, 1)
[trisc0] UnpackOp(DST, cb=2, bf16->fp32, faces=8, rows=8, dst_slot=8)
[trisc0] CbOp(pop, cb=2, 1)
[trisc0] CbOp(push, cb=4, 1)                     # 0-byte barrier: res_t is in Dst[8..15]

[trisc1] CbOp(wait, cb=4, 1)
[trisc1] StallOp(sync, math|sfpu)
RANGE fp in 0..32:                               # stays intact into Pass 9 -> MOP-ready!
  [trisc1] v0 = SfpLoadOp(dst_slot=0)
  [trisc1] v1 = SfpLoadOp(dst_slot=8)
  [trisc1] v2 = ADD(v0, v1)
  [trisc1] SfpStoreOp(dst_slot=0, v2)
END fp
[trisc1] CbOp(pop, cb=4, 1)
[trisc1] StallOp(sync, math|sfpu)
[trisc1] SemOp(post, sem=0, max=2)

# Pack Dst[0..7] -> L1 -> DRAM
[trisc2] SemOp(wait_data, sem=0, max=2, toggle_dst=True)
[trisc2] CbOp(reserve, cb=3, 1)
[trisc2] PackOp(cb=3, bf16, blocks=8, dst_slot=0, untilize=False)
[trisc2] StallOp(sync, pack)
[trisc2] SemOp(get, sem=0, max=2)
[trisc2] CbOp(push, cb=3, 1)

[ncrisc] CbOp(wait, cb=3, 1)
[ncrisc] NocWrite(slot=0, cb=3, 2048B, off=wid*2048)
[ncrisc] NocWait(tid=1, acked=True)
[ncrisc] CbOp(pop, cb=3, 1)
```

### After Pass 8–10 (5-Core Projection → Per-Core Recipe Expansion → `BH01`)
- **`brisc`**: keeps `k_blk` and `sub_n` loops + `off_x`, `off_w`, `off_res` RV32 integer math + CB reserve/push + `jal FN_NOC_READ`/`FN_NOC_WAIT`. Zero Tensix ops.
- **`trisc0`**: keeps `k_blk` and `sub_n` loops + CB wait/pop + `RMWCIB`/`SETC16` config diffs + `UNPACR`s. Zero DRAM address math!
- **`trisc1`**: keeps `k_blk`, `sub_n`, and `fp` loops; Pass 9 lowers `FpuOp` → `ZEROACC`/`MVMUL`, lowers `SfpLoadOp`/`ADD`/`SfpStoreOp` → `SFPLOAD(0)`/`SFPLOAD(64)`/`SFPADD`/`SFPSTORE(0)`/`INCRWC dst+2` + `L0..L7` `regalloc`, optionally compresses with `SFPLOADMACRO → REPLAY → MOP` while `RANGE(fp)` is still structured, then Pass 10 lowers remaining loops + `fix_sfpu_hazards_uops`. Zero DRAM address math!
- **`trisc2`**: **no `k_blk` or `fp` loop at all!** Just `SEMWAIT` → `CbOp(reserve)` → `16 × PACR` → `STALLWAIT` → `SEMGET` → `CbOp(push)`.
- **`ncrisc`**: **no `k_blk` or `fp` loop at all!** Just `CbOp(wait)` → `off_out = wid * 2048` → `jal FN_NOC_WRITE` → `jal FN_NOC_WAIT` → `CbOp(pop)`.

### Two Other Kernel Archetypes (for Completeness)
- **Multi-phase L1-staged kernel (Kernel 7: `RMSNorm + SwiGLU`):**
  - `l1: fp32 (1,)` (RMS scalar) and `l0: bf16 (7168,)` (normalized `xn`) are already marked `ALLOC(..., space="l1")` by `rangeify.py`.
  - Pass 4 lowers `l1` and `l0` directly to `pages=1` static L1 CBs (zero NoC traffic between RMSNorm and SwiGLU!).
  - Phase 1 computes `sum(x^2)` in `Space.LREG` (loop-carried `LReg` accumulator across `RANGE(k)` + `RANGE(fp)` → `SfpReduceLanes("add")` leaves RMS scalar in all 32 lanes) → `SfpStoreOp` + `PackOp` to `l1` CB (or stays directly in an `LReg`/`Dst` slot for Phase 2!).
  - Phase 2 computes `xn = (x * recip(rms)) * gamma` in `Space.LREG` → `SfpStoreOp` → `PackOp` to `l0` CB (`CbOp(push, cb_l0, 1)` once after loop).
  - Phase 3 (`gate_proj` + `up_proj` + `silu(gate) * up`) hoists `CbOp(wait, cb_l0, 1)` once before the `N` strip loop and `CbOp(pop, cb_l0, 1)` once after, running `MVMUL` (`gate`, `up`) → `StallOp` → `RANGE(fp)` `SfpLoadOp`/`silu * up`/`SfpStoreOp` in place on `Dst` → single `PackOp` → `NocWrite`.
- **Pure RV32/NoC kernel (Kernel 0: `Embedding` gather):**
  - Pass 1 classifies as pure RV32/NoC (`ROLE_PC[trisc0..2] = 0`, `ROLE_PC[ncrisc] = 0`).
  - `brisc` reads `tok` (`4 B` via `FN_NOC_READ` into L1 scratch), checks `0 <= tok < 166912`, shards the `448` output faces across `N_workers`, and loops `FN_NOC_READ(weight, tok_row_off + face_off)` → `FN_NOC_WRITE(out, face_off)` (or zeros L1 scratch if out-of-bounds).

---

## 6. Recommended Implementation Order (Incremental Bring-Up)

Do **not** try to write all 10 passes and immediately run 52-layer Nanbeige. Verify each milestone in order (both in the RV32 emulator `test/test_isa.py` and on silicon with `BH_HW=1`):

1. **Milestone 0 — Prerequisites:**
   - Fix `linearize()` in `compiler/uop.py`, fix `project_roles()` in `compiler/isa/tensix.py`, add `SPECIAL`/arg-block/`IF`/long-branch to `compiler/isa/rv32.py`, export `FN_NOC_*` + completion barrier in `fw/boot.c` + `fw/park.c`.
   - Port `compiler/sfpu.py` onto the dtype-free `UOp` core + `sfp_ins` (`SfpSpec`) + `8×16` `Dst` blocks + `reduce_lanes`, and re-enable `test_sfpu.py` & `test_sfpu_hw.py`.
2. **Milestone 1 — Pure RV32/NoC kernel end-to-end (`Embedding` gather):**
   - Pass 1 + Pass 8 + Pass 9 (`brisc` `FN_NOC_*`) + Pass 10 + `Device.run` runtime arg-block dispatch.
   - Verify `Tensor.embedding` matches NumPy on Blackhole silicon.
3. **Milestone 2 — Single-phase SFPU kernel end-to-end (`silu(x) * y`, `RMSNorm`, `RoPE`):**
   - Full Passes 2–10 for SFPU-only kernels (`NocRead` → `UnpackOp(DST)` → `RANGE(fp)` `[SfpLoadOp → ALU → SfpStoreOp]` → `PackOp` → `NocWrite`, with `StateTracker`s and CB/sem syncs).
   - Verify bit-exact / tolerance match against `test_rangeify.py` Python evaluator on silicon.
4. **Milestone 3 — FPU `MVMUL` + fused FPU→SFPU kernel (`down_proj + residual`):**
   - Add `FpuOp("MVMUL")` matching + `N_BLK=8` rotation + 3-phase fidelity + `FpuOp -> SfpLoadOp` in-place `Dst` handoff.
   - Verify against NumPy on silicon for both `bf16 @ bf16` and `fp32 (TF32) @ bf16` (checking 4-byte TF32 Src strides!).
5. **Milestone 4 — Multi-phase L1-staged kernels & dynamic `start_pos` (`RMSNorm + SwiGLU`, fused `Attention`, `argmax`):**
   - Static `pages=1` L1 stage CBs + `WHERE` → `SFPSETCC` tail/causal masking + runtime `Variable` `start_pos` from L1 arg block.
6. **Milestone 5 — Full 52-layer Nanbeige decode + resident dispatch + optional `SFPLOADMACRO → REPLAY → MOP` compression.**
