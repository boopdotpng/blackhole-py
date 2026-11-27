# Chip-Wide 2D Multicast Matmul Specification (`blackhole-py`)

This document specifies how to add **2D SUMMA-style NoC multicast matmuls** (`NocMcastRead` + multi-block `BM × BN` FPU tiling) to `blackhole-py` so compute-bound matmuls (`M ≥ 16`, prefill / batched GEMM) approach peak Blackhole TFLOP/s **without** `Tensor.custom_kernel()` and **without** breaking epilogue fusion (SwiGLU, residual add, casts) or the existing 1D decode path.

All file paths, header offsets, ABI conventions, and hardware bitfields below match the current `blackhole-py` codebase and verified silicon recipes in `blackhole-py-archive/examples/prefill/summa_projection.ttrv`, `blackhole-py-archive/ttrv/noc.py`, and `blackhole-py-archive/ttrv/hw.py`.

---

## 0. Scope & Hard Invariants

1. **Keep the 1D decode path intact.** When `mf == 1` (`M ≤ 8`), matmul is weight-DRAM-bandwidth bound and must keep using the existing 1D `N`-sharded path in `compiler/blackhole/lower.py`.
2. **No `Tensor.custom_kernel()`.** 2D multicast must lower through the same tile pipeline (`lower_kernel` → `linearize` → `insert_syncs` → `split_roles` → `compile_core`), keeping `UnpackOp`, `FpuOp`, SFPU epilogues, `PackOp`, and `NocWrite` agnostic to whether L1 slabs came from `NocRead` or `NocMcastRead`.
3. **Blackhole NoC deadlock rules (non-negotiable):**
   - **All DRAM reads stay on NoC0 (`niu = 0`, BRISC).** Never issue DRAM reads on NoC1 (vertical DRAM-column link contention per `boop-docs/notes/noc_findings.md`).
   - **Row multicasts (`A`, invariant across `worker_x`) run on NoC0 (`niu = 0`, BRISC).**
   - **Column multicasts (`W`, invariant across `worker_y`) run on NoC1 (`niu = 1`, NCRISC)** after BRISC reads from DRAM on NoC0 and bumps a local L1 `staged` counter.
   - **Credit atomics (`FN_NOC_INC`) run on NoC1 (`niu = 1`, NCRISC)** using `ATOMIC_BUF` on `STATIC_VC(1)`, separate from multicast `MCAST_BUF` on `STATIC_VC(4)`.
   - **Every multicast rectangle must be 1D (`y0 == y1` or `x0 == x1`) and MUST contain its sender (`include_sender = 1`, `CTRL_BRCST_SRC_INCLUDE`).** Never multicast to a rect excluding the sender or overlap 2D rects from multiple senders.
   - **Flag ordering:** Send each 4-byte readiness flag (`slab + 1`) on the **exact same NIU, command buffer (`MCAST_BUF`), rect, and `STATIC_VC(4)`** immediately after the slab data mcast, from a **16-byte aligned** source address (`src % 16 == dst % 16 == 0`).
   - **Monotonic sequence numbers only:** Never clear a readiness flag or credit counter mid-launch. Use `flag[slot] = slab + 1` (consumer spins `flag[slot] > slab`) and monotonically increasing `cred[slot]` (sender spins `cred[slot] >= expected`). Only send credits when `slab + NSLOT < total_slabs`, so every sender waits for all credits it will ever receive before exiting; zero control words once on kernel exit (or in `fw/boot.c` before `GO_FLAG`).
   - **Uniform trip count across the grid:** Every worker in the `grows × gcols` grid must execute the **exact same `(OM, ON, SLABS)` loop bounds** so no worker exits early and starves credits. Out-of-bounds boundary tiles clamp DRAM read offsets to `0` and skip `NocWrite`.

---

## 1. Firmware & Device Primitives (`fw/`, `device.py`)

### 1.1 `fw/hw.h`
Add the missing NoC multicast control bits (verified in `blackhole-py-archive/ttrv/hw.py`) and two free jump-table trampoline slots (`0x7C` and `0x38` are currently unused):

```c
#define FN_NOC_MCAST           0x7C   // jal x0 trampoline to kernel_noc_mcast
#define FN_NOC_INC             0x38   // jal x0 trampoline to kernel_noc_inc

#define CTRL_BRCST_PACKET      (1u << 5)
#define CTRL_BRCST_SRC_INCLUDE (1u << 17)
```

Reserve a small fixed L1 control-block clear or zero it inside the kernel prologue before signaling sync — **prefer zeroing a fixed 1 KiB mcast control region `[MCAST_CTRL_BASE, MCAST_CTRL_BASE + 0x400)` in `fw/boot.c` on BRISC before `GO_FLAG = 1`**:

```c
#define MCAST_CTRL_BASE        0x1EC00  // 1 KiB (64 x 16B aligned slots), zeroed by boot before GO_FLAG
```

*(Check: `NOC_READ_SCRATCH` is `0x1F000..0x1FFFF`, `CODE_BASE` ends well before `0x1E000`, and CB staging starts at `0x20000`. Verify `code_end <= MCAST_CTRL_BASE` in `runtime.py`.)*

### 1.2 `fw/noc.h` & `fw/noc.c`
Add logical-to-physical coordinate translation matching `fw/boot.c:168-172` and `device.py:209`:

```c
static u32 worker_coord(u32 wx, u32 wy) {
  u32 x = wx + (wx >= 7 ? 3 : 1);   // skips physical x = 8, 9 (DRAM/ETH gap)
  u32 y = wy + 2;
  return (y << 6) | x;
}
```

Add two helpers to `fw/noc.c` (and declare in `fw/noc.h`):

1. **`noc_mcast(u32 niu, u32 local, u32 remote, u32 rect_packed, u32 size, u32 tid, u32 include_sender)`**
   - `rect_packed = (x0 & 63) | ((y0 & 63) << 6) | ((x1 & 63) << 12) | ((y1 & 63) << 18)` in **logical** worker coordinates (`0 <= x0 <= x1 < cols`, `0 <= y0 <= y1 < 10`).
   - Translate corners:
     ```c
     u32 c0 = worker_coord(rect_packed & 63, (rect_packed >> 6) & 63);
     u32 c1 = worker_coord((rect_packed >> 12) & 63, (rect_packed >> 18) & 63);
     // CRITICAL: NoC0 takes (start << 12) | end; NoC1 takes (end << 12) | start.
     u32 ret_coord = (niu == 0) ? ((c0 << 12) | c1) : ((c1 << 12) | c0);
     ```
   - Use `volatile u32 *c = CMD_BUF(niu, MCAST_BUF);`
   - Control word:
     ```c
     u32 ctrl = CTRL_WRITE | CTRL_BRCST_PACKET | STATIC_VC(4)
              | (include_sender ? CTRL_BRCST_SRC_INCLUDE : 0);
     ```
   - Chunk loop `for (u32 done = 0; done < size; done += NOC_MAX_BURST)`:
     - Pace outgoing: `while (read32(OUTGOING(niu, tid)) > 128) {}`
     - `wait_idle(c);`
     - `c[TARG_LO] = local + done; c[TARG_MID] = 0; c[TARG_COORD] = noc_coord(niu);`
     - `c[RET_LO] = remote + done; c[RET_MID] = 0; c[RET_COORD] = ret_coord;`
     - `c[PACKET_TAG] = tid << 10;`
     - `c[CTRL] = ctrl;`
     - `c[AT_LEN_BE] = MIN(size - done, NOC_MAX_BURST);`
     - `c[AT_LEN_BE_1] = 0; c[AT_DATA] = 0; c[BRCST_EXCLUDE] = 0;`
     - `send(c);`
   - Note: `noc_mcast` returns asynchronously (caller waits via `FN_NOC_WAIT(niu, tid, acked=0)` after sending both the data slab and its 4-byte flag!).

2. **`noc_inc_worker(u32 niu, u32 remote, u32 target_xy_packed, u32 tid)`**
   - `target_xy_packed = (wx & 63) | ((wy & 63) << 6)` in logical worker coordinates.
   - `u32 coord = worker_coord(target_xy_packed & 63, (target_xy_packed >> 6) & 63);`
   - Uses `CMD_BUF(niu, ATOMIC_BUF)`:
     ```c
     volatile u32 *c = CMD_BUF(niu, ATOMIC_BUF);
     wait_idle(c);
     c[TARG_LO] = remote; c[TARG_MID] = 0; c[TARG_COORD] = coord;
     c[PACKET_TAG] = tid << 10;
     c[CTRL] = 1u | STATIC_VC(1);   // posted atomic inc on VC 1
     c[AT_LEN_BE] = (1u << 12) | (31u << 2);
     c[AT_LEN_BE_1] = 0; c[AT_DATA] = 1; c[BRCST_EXCLUDE] = 0;
     send(c);
     ```

### 1.3 `fw/boot.c` & `fw/park.c`
- In `fw/boot.c` (BRISC):
  - Add `kernel_noc_mcast` and `kernel_noc_inc` wrappers (RV32 ABI `a0..a6`, exact same convention as `kernel_noc_read`).
  - Install jump trampolines:
    ```c
    install_jump(FN_NOC_MCAST, (u32)kernel_noc_mcast);
    install_jump(FN_NOC_INC, (u32)kernel_noc_inc);
    ```
  - Zero `[MCAST_CTRL_BASE, MCAST_CTRL_BASE + 0x400)` before `write32(GO_FLAG, 1);`.
  - Update `kernel_noc_wait(u32 niu, u32 tid, u32 acked)` to also wait `CMD_BUF(niu, MCAST_BUF)[CMD_CTRL] == 0` and `CMD_BUF(niu, ATOMIC_BUF)[CMD_CTRL] == 0`.
- In `fw/park.c` (`ROLE < ROLE_TRISC0`):
  - Also wait `CMD_BUF(ROLE, MCAST_BUF)[CMD_CTRL] == 0` and `CMD_BUF(ROLE, ATOMIC_BUF)[CMD_CTRL] == 0` before signaling completion.

### 1.4 `device.py` & `compiler/blackhole/runtime.py`
- On P150 (`self.cols == 14`), `self.dma_core` sits at `(16, 11)` (logical `x = 13, y = 9`), so the largest clean full-height 2D rectangle is:
  - **`grid_rows = 10`** (`wy ∈ 0..9`)
  - **`grid_cols = self.cols - 1`** (`13` on P150 → 130 cores; `11` on P100a → 110 cores).
- Add a helper on `Device`:
  ```python
  def worker_grid(self, gcols: int, grows: int) -> list[tuple[int, int]]:
    assert 1 <= gcols <= self.cols - 1 and 1 <= grows <= 10
    return [(x, y) for wx in range(gcols) for x in (wx + (3 if wx >= 7 else 1),)
            for wy in range(grows) for y in (wy + 2,)]
  ```
- Extend `LoweredKernel` in `compiler/blackhole/lower.py`:
  ```python
  @dataclass(frozen=True)
  class LoweredKernel:
    program: UOp
    workers: int
    face_rows: tuple[int, ...]
    grid: tuple[int, int] | None = None   # (gcols, grows) when 2D-sharded
  ```
- In `compiler/blackhole/runtime.py`:
  - Pass `grid_shape=(device.cols - 1, 10)` into `lower_kernel`.
  - When launching: `cores = device.worker_grid(*lowered.grid) if lowered.grid else device.workers[:lowered.workers]`.

---

## 2. Multi-Block `BM × BN` FPU Tiling & Slab Sizing

Multicast only delivers high TFLOP/s if each core reuses each received `A` and `W` slab across a **2D register tile in `Dst`** and feeds the FPU without 6-cycle `Dst` RAW stalls.

### 2.1 Tile Geometry per Core
For a 2D matmul `C[M, N] = A[M, K] @ W[N, K]^T` (`mf = ceil(M / 8)`, `nf = ceil(N / 16)`, `kf = ceil(K / 16)`):

1. **Choose `BM × BN` face block per core (all held in FP32 `Dst` simultaneously):**
   - For single-reduction matmul (`len(reductions) == 1`):
     - `BM = 4 if mf >= 4 else (2 if mf >= 2 else 1)` (`BM * 8` activation rows, up to `32` rows = 4 faces in `SrcB`).
     - `BN = 4 if nf >= 4 else (2 if nf >= 2 else 1)` (`BN * 16` weight cols, up to `64` cols = 4 faces in `SrcA`).
     - Total `Dst` slots used = `BM * BN ≤ 16` (128 Dst rows out of 512 — fits with huge margin, zero `Pack_L1_Acc` needed!).
   - For fused dual-reduction matmul (e.g., SwiGLU `gate` + `up`, `len(reductions) == 2`):
     - Cap `BM * BN ≤ 16` per reduction (`≤ 32` total `Dst` slots = 256 rows; `gate` in `0..BM*BN-1`, `up` in `BM*BN..2*BM*BN-1`).
2. **Choose 2D worker grid `(gcols, grows)`:**
   - Total block rows `M_BLKS = ceil(mf / BM)`, total block cols `N_BLKS = ceil(nf / BN)`.
   - `grows = min(M_BLKS, max_grid_rows)` (up to `10`).
   - `gcols = min(N_BLKS, max_grid_cols)` (up to `13` on P150).
   - Outer block loops per worker (identical trip counts across all workers!):
     - `OM = ceil(M_BLKS / grows)`
     - `ON = ceil(N_BLKS / gcols)`
     - Worker `(wx, wy)` at outer step `(om, on)` computes:
       - `m_blk = wy + om * grows` (faces `m_blk * BM + r` for `r ∈ 0..BM-1`)
       - `n_blk = wx + on * gcols` (faces `n_blk * BN + c` for `c ∈ 0..BN-1`)
3. **Choose `K`-slab size `SK` and ring depth `NSLOT = 2`:**
   - Pick the largest `SK ∈ (16, 8, 4)` that divides `kf` AND keeps both ring buffers inside L1 (`<= 0x140000`) AND keeps each slab `<= 64 KiB` (if `kf % 4 != 0`, fall back to `SK = 1` or pad tail).
   - **Why `SK % 4 == 0` matters:**
     - `4` BFP4 weight faces = `576 B` (`% 64 == 0`)
     - `4` BFP8 weight faces = `1088 B` (`% 64 == 0`)
     - `4` BF16 weight faces = `2048 B` (`% 64 == 0`)
     - Every DRAM read for `W` and `A` hits the **fast zero-copy congruent NoC0 path** (`((lo + off) ^ local) & 63 == 0`)!
   - `SLABS = kf // SK`.

### 2.2 Multi-Face `SrcB` / `SrcA` Bank Fill + `BM × BN` `MVMUL` (`recipes.py`)
To hit near-peak FPU throughput per core (1 `dvalid` flip per `k_local` step instead of `BM * BN` flips):

- **Activation unpack (`TRISC0`, `UnpackOp(Space.SRCB, faces=BM, rows=8)`):**
  - Unpack all `BM` faces (`r = 0..BM-1`) at `k_local` into `SrcB` rows `0, 8, 16, 24` (`BM * 8 <= 32` rows, fits easily in 64-row `SrcB`!).
  - Flip `set_dvalid=1` only on the last face (`r == BM - 1`).
  - *(Note: `A` slab layout in L1 is `[r in 0..BM-1][k_local in 0..SK-1][face_bytes(a, 8)]`, so face `(r, k_local)` is at `slot_base + (r * SK + k_local) * a_face_bytes`.)*
- **Weight unpack (`TRISC0`, `UnpackOp(Space.SRCA, faces=BN, rows=16)`):**
  - Unpack all `BN` faces (`c = 0..BN-1`) at `k_local` into `SrcA` rows `0, 16, 32, 48` (`BN * 16 <= 64` rows, fills `SrcA`!).
  - Flip `set_dvalid=1` only on the last face (`c == BN - 1`).
  - *(Note: `W` slab layout in L1 is `[c in 0..BN-1][k_local in 0..SK-1][face_bytes(w, 16)]`, so face `(c, k_local)` is at `slot_base + (c * SK + k_local) * w_face_bytes`.)*
- **FPU (`TRISC1`, `FpuOp("MVMUL", m_blocks=BM, n_blocks=BN, k_faces=1, fidelity=phases, dst_slot=base_slot, accumulate=True)`):**
  - Configure 3 `ADDR_MOD` slots once in `prologue`/setup:
    - `am_c`: `srca += 16, srcb += 0, dst += 0, fidelity += 0` (step to next weight face `c`, explicit `dst` imm on `MVMUL`)
    - `am_r`: `srca = 0, srcb += 8, dst += 0, fidelity += 0` (reset `SrcA` to 0, step to next activation face `r`)
    - `am_p`: `srca = 0, srcb = 0, dst += 0, fidelity += 1` (reset `SrcA`/`SrcB` to 0, advance fidelity phase)
  - Wait `STALLWAIT(MATH, SRCA_VLD | SRCB_VLD)`, reset RWC once, then emit:
    ```python
    for phase in range(spec.fidelity):
      for r in range(spec.m_blocks):
        for c in range(spec.n_blocks):
          last_c = (c == spec.n_blocks - 1)
          last_rc = last_c and (r == spec.m_blocks - 1)
          last_all = last_rc and (phase == spec.fidelity - 1)
          am = am_p if last_rc else (am_r if last_c else am_c)
          dst_row = (spec.dst_slot + r * spec.n_blocks + c) * 8
          self.tt(isa.MVMUL(dst=dst_row, addr_mod=am, release=3 if last_all else 0))
    ```
  - **Why this is huge:** With `BM = 4, BN = 4`, each `(r, c)` writes a distinct `Dst` slot (`0..15`), completely hiding the 6-cycle `Dst` accumulate RAW latency (`16 > 6`), and only flips `dvalid` once per `k_local`! *(Verify `MVMUL` with `BM × BN` in isolation in Stage 2 before turning on multicast!)*

---

## 3. Compiler IR & Invariance-Detected `NocMcastRead`

### 3.1 New Specs (`compiler/blackhole/specs.py`)
Add two abstract specs (no raw machine instructions in the DAG):

```python
@dataclass(frozen=True)
class NocMcastRead:
  param_slot: int
  cb_id: int              # ring buffer base in cb_addrs[cb_id]
  axis: str               # "x" (row mcast, NoC0/BRISC) or "y" (col mcast, NoC1/NCRISC)
  gcols: int
  grows: int
  blocks: int             # BM (for A) or BN (for W) contiguous K-strips read per slab
  strip_bytes: int        # SK * face_bytes per block (DRAM read size per strip)
  strip_stride: int       # kf * face_bytes (DRAM stride between adjacent blocks r or c)
  nslots: int = 2
  slot_stride: int = 0    # 64B-aligned byte stride between ring slots (>= blocks * strip_bytes)
  ctrl_id: int = 0        # index into MCAST_CTRL_BASE control block (0 for A, 1 for W, 2 for W2...)
  total_slabs: int = 1    # total slabs executed across OM * ON * SLABS (identical on all cores)
  tid_read: int = 0       # BRISC DRAM read tid
  tid_mcast: int = 2      # mcast tid (2 on NoC0 for A, 3 on NoC1 for W)
  rotate_sender: bool = True
  role: str = "brisc"     # DRAM read always on brisc; axis=="y" also emits ncrisc mcast op

@dataclass(frozen=True)
class NocMcastForward:    # NCRISC half of axis=="y" (wait staged -> NoC1 col mcast + flag)
  cb_id: int
  gcols: int
  grows: int
  nbytes: int             # blocks * strip_bytes
  nslots: int
  slot_stride: int
  ctrl_id: int
  total_slabs: int
  tid_mcast: int = 3
  rotate_sender: bool = True
  role: str = "ncrisc"

@dataclass(frozen=True)
class McastWait:          # TRISC0 waits for flag[slot] > slab_seq
  ctrl_id: int
  nslots: int
  role: str = "trisc0"

@dataclass(frozen=True)
class McastRelease:       # TRISC0 bumps consumed = slab_seq + 1; NCRISC sends FN_NOC_INC credits
  axis: str
  gcols: int
  grows: int
  nslots: int
  ctrl_id: int
  total_slabs: int
  rotate_sender: bool = True
  tid_inc: int = 4
  role: str = "ncrisc"
```

### 3.2 Automatic Invariance Detection (Pass 2 / Pass 4)
Create `compiler/blackhole/mcast.py` called from `compiler/blackhole/lower.py` when a 2D matmul qualifies:
- **Trigger condition:** `mf >= 2 and nf >= 2` (or `gcols > 1 or grows > 1` after computing `(gcols, grows)` from `BM, BN`; allow `BH_MCAST=0` env var override to disable for A/B benchmarking against 1D!).
- Mint `wx = UOp.special(gcols, "worker_x")` and `wy = UOp.special(grows, "worker_y")`.
- For each matmul operand's DRAM base offset expression (at `(om, on, slab)`):
  - Collect `{u.arg for u in offset.toposort() if u.op is Ops.SPECIAL}`:
    - `{"worker_y"}` (invariant in `worker_x`) and `gcols > 1` → **Row multicast (`axis="x"`)** on NoC0.
    - `{"worker_x"}` (invariant in `worker_y`) and `grows > 1` → **Column multicast (`axis="y"`)** on NoC1 (with BRISC DRAM read on NoC0).
    - Otherwise → ordinary per-core `NocRead`.
- **Linear slab sequence index `slab_seq`:**
  - Across the nested loops `for om in 0..OM: for on in 0..ON: for s in 0..SLABS:`, define the monotonic 0-based counter:
    - `slab_seq = ((om * ON + on) * SLABS + s)`
    - `total_slabs = OM * ON * SLABS`
    - `slot = slab_seq % NSLOT` (`slab_seq & 1` for `NSLOT = 2`).
  - Sender selection:
    - For `axis="x"` (`A`): `sender_x(seq) = (seq % gcols) if rotate_sender else 0`.
    - For `axis="y"` (`W`): `sender_y(seq) = (seq % grows) if rotate_sender else 0`.
  - Expected credit count before sender refills `slot` at `seq >= NSLOT`:
    - How many times has *this specific worker* already sent into `slot` before `seq`?
      - With `rotate_sender = False` (fixed sender `0`): `sends_before = seq // NSLOT` (so wait `cred[slot] >= (seq // NSLOT) * rect_len`).
      - With `rotate_sender = True`: track a per-slot local L1 counter `acnt[slot]` (initialized to 0 by `MCAST_CTRL_BASE` zeroing): whenever `seq >= NSLOT` and `me == sender(seq)`, wait `cred[slot] >= acnt[slot] + rect_len`, then set `acnt[slot] += rect_len`! **Use this local `acnt[slot]` counter — it works identically for BOTH fixed and rotating senders with zero division!**

### 3.3 L1 Control Block Layout (`MCAST_CTRL_BASE = 0x1EC00`)
Each multicast stream `ctrl_id ∈ {0, 1, 2}` gets `256` bytes (`0x100`, all 16-byte aligned, zeroed by `fw/boot.c` before `GO_FLAG`):

| Offset from `base = MCAST_CTRL_BASE + ctrl_id * 0x100` | Contents (16B stride per slot, `NSLOT = 2`) |
|---|---|
| `+0x00`, `+0x10` | `flag[0]`, `flag[1]` — written via mcast with `slab_seq + 1`; `TRISC0` spins `flag[slot] > slab_seq` |
| `+0x20`, `+0x30` | `flag_src[0]`, `flag_src[1]` — 16B-aligned local source word for 4-byte flag mcast (`src % 16 == dst % 16 == 0`) |
| `+0x40`, `+0x50` | `cred[0]`, `cred[1]` — incremented by receivers via `FN_NOC_INC`; sender spins `cred[slot] >= acnt[slot] + rect_len` |
| `+0x60`, `+0x70` | `acnt[0]`, `acnt[1]` — sender's local credit watermark per slot |
| `+0x80` | `staged` — BRISC writes `slab_seq + 1` after DRAM read (`axis="y"` only); NCRISC spins `staged > slab_seq` |
| `+0x90` | `consumed` — TRISC0 writes `slab_seq + 1` after unpacking slab; NCRISC spins `consumed > slab_seq` before sending credits |

### 3.4 Exact 5-Core Expansion (`recipes.py`)
For each slab iteration `slab_seq` (`slot = slab_seq & 1`):

1. **BRISC (`NocMcastRead`):**
   - Compute `is_sender = (wx == sender_x(slab_seq))` (for `axis="x"`) or `(wy == sender_y(slab_seq))` (for `axis="y"`).
   - If `is_sender`:
     - If `slab_seq >= NSLOT`:
       - `need = acnt[slot] + rect_len`
       - Spin `while (cred[slot] < need) {}`; `fence`; `acnt[slot] = need`
     - `dst_l1 = cb_addrs[cb_id] + slot * slot_stride`
     - For `b in range(blocks)` (clamping DRAM offset to `0` if `blk_idx * blocks + b >= max_faces`):
       - `FN_NOC_READ(niu=0, ptr_lo, ptr_hi, dram_off + b * strip_stride, strip_bytes, dst_l1 + b * strip_bytes, tid_read)`
     - `FN_NOC_WAIT(niu=0, tid_read, acked=1)`
     - If `axis == "x"`:
       - `flag_src[slot] = slab_seq + 1; fence`
       - `rect = (0) | (wy << 6) | ((gcols - 1) << 12) | (wy << 18)`
       - `FN_NOC_MCAST(niu=0, dst_l1, dst_l1, rect, blocks * strip_bytes, tid_mcast, include_sender=1)`
       - `FN_NOC_MCAST(niu=0, &flag_src[slot], &flag[slot], rect, 4, tid_mcast, include_sender=1)`
       - `FN_NOC_WAIT(niu=0, tid_mcast, acked=0)`
     - Else (`axis == "y"`):
       - `fence; staged = slab_seq + 1; fence`
2. **NCRISC (`NocMcastForward` for `axis == "y"`):**
   - If `wy == sender_y(slab_seq)`:
     - Spin `while (staged <= slab_seq) {}`; `fence`
     - `dst_l1 = cb_addrs[cb_id] + slot * slot_stride`
     - `flag_src[slot] = slab_seq + 1; fence`
     - `rect = (wx) | (0 << 6) | (wx << 12) | ((grows - 1) << 18)`
     - `FN_NOC_MCAST(niu=1, dst_l1, dst_l1, rect, nbytes, tid_mcast, include_sender=1)`
     - `FN_NOC_MCAST(niu=1, &flag_src[slot], &flag[slot], rect, 4, tid_mcast, include_sender=1)`
     - `FN_NOC_WAIT(niu=1, tid_mcast, acked=0)`
3. **TRISC0 (`McastWait` + unpack loop + `consumed` bump):**
   - Spin `while (flag[slot] <= slab_seq) {}`; `fence` (for both `A` and `W` streams).
   - Unpack `SK` steps of `(BM` faces into `SrcB`, `BN` faces into `SrcA)` from `cb_addrs[cb_id] + slot * slot_stride`.
   - Wait unpack drain (`drain()`), then write `consumed = slab_seq + 1; fence` for each mcast stream.
4. **NCRISC (`McastRelease`, runs for EVERY worker including senders):**
   - Spin `while (consumed <= slab_seq) {}`; `fence`.
   - If `slab_seq + NSLOT < total_slabs`:
     - `next_seq = slab_seq + NSLOT`; `next_slot = next_seq & 1`
     - If `axis == "x"`: `target = (sender_x(next_seq)) | (wy << 6)`
     - If `axis == "y"`: `target = (wx) | (sender_y(next_seq) << 6)`
     - `FN_NOC_INC(niu=1, &cred[next_slot], target, tid_inc)`
     - `FN_NOC_WAIT(niu=1, tid_inc, acked=0)`
5. **TRISC2 + NCRISC output write (after `SLABS` loop closes):**
   - Pack all `BM * BN` `Dst` slots (`r = 0..BM-1`, `c = 0..BN-1`) into output CBs.
   - NCRISC writes each `(r, c)` face to DRAM **only if** `(m_blk * BM + r < mf) and (n_blk * BN + c < nf)` (guarding boundary tiles!).

> **Important ordering note for NCRISC:** Inside the `s` loop, NCRISC must **not** deadlock waiting for `consumed` of slab `s` before it has forwarded `W` of slab `s`! Always emit `NocMcastForward` (for `W` slab `s`) **before** `McastRelease` (waiting `consumed > s`) inside the same `s` loop body! Because `TRISC0` needs `W` slab `s` before it can bump `consumed = s + 1`, putting `NocMcastForward(s)` before `McastRelease(s)` guarantees strict forward progress with zero deadlocks.

---

## 4. Phased Implementation & Verification Plan

Implement in 4 incremental, hardware-verified stages (never debug multicast and multi-block FPU simultaneously):

### Stage 1: Firmware Mcast & Atomic Inc (`test/test_noc_mcast_hw.py`)
- Implement `noc_mcast`, `noc_inc_worker`, `FN_NOC_MCAST`, `FN_NOC_INC`, `MCAST_CTRL_BASE` zeroing in `fw/boot.c`, and `MCAST_BUF`/`ATOMIC_BUF` drain in `fw/park.c`.
- Verify on **both P150 cards** (`card 0` and `card 1`):
  1. Row mcast on NoC0 across all 13 columns (`wx = 0..12`, crossing the `x = 8, 9` gap) with `include_sender=1`, verifying both 4 KiB payload and ordered 4-byte flag arrive at every column.
  2. Column mcast on NoC1 across all 10 rows (`wy = 0..9`) with `include_sender=1`.
  3. Simultaneous NoC0 row mcast + NoC1 col mcast + NoC1 `FN_NOC_INC` credit return across all 130 cores for 16 consecutive ring iterations and 5 back-to-back launches (zero hangs, exact bytes).

### Stage 2: Multi-Block `BM × BN` `MVMUL` (No Mcast Yet)
- Extend `recipes.py` `UnpackOp(faces=BM/BN)` + `FpuOp(m_blocks=BM, n_blocks=BN)` to fill `SrcB` (`BM` faces) and `SrcA` (`BN` faces) once per `k` step and run `BM × BN` `MVMUL`s across `Dst` slots `0..BM*BN-1`.
- Test `(BM, BN) ∈ {(1, 1), (2, 2), (4, 4)}` on BF16, BFP8, and BFP4 weights on both P150 cards against NumPy exact integer & numerical tolerances.

### Stage 3: 2D Sharding + `NocMcastRead` Integration (`test/test_matmul_mcast.py`)
- Implement `compiler/blackhole/mcast.py`, `LoweredKernel.grid`, `Device.worker_grid`, and wire into `lower.py` / `pipeline.py` / `recipes.py` / `runtime.py`.
- Verify on **both P150 cards**:
  - Shapes covering exact multiples, non-multiples (boundary masking), and multiple outer `(OM, ON)` passes:
    - `(16, 256) @ (256, 256)` (BF16)
    - `(64, 1024) @ (1024, 1024)` (BF16, BFP8, BFP4)
    - `(128, 7168) @ (7168, 7168)` (real Nanbeige layer-0 `q_proj` BFP8)
    - `(128, 7168) @ (7168, 22016)` (real Nanbeige layer-0 `gate_proj` BFP4, tests `nf = 1376` non-divisible by `gcols = 13`!)
    - Fused SwiGLU `(64, 7168) → silu(gate) * up` with real BFP4 weights.
    - 10 consecutive launches back-to-back (verifies clean control-word reset).
  - Verify `BH_MCAST=0` vs `BH_MCAST=1` match within expected BF16/BFP tolerance.

### Stage 4: Benchmark & Full Regression Check
- Add `examples/benchmark_matmul_mcast.py` measuring warm launch time and achieved **TFLOP/s** (`2 * M * N * K / dt / 1e12`) for `M ∈ {64, 128, 256, 512, 1024}`, `K = 7168`, `N ∈ {7168, 22016}` (BF16, BFP8, BFP4), comparing `BH_MCAST=0` (1D) vs `BH_MCAST=1` (2D SUMMA) on Card 0 and saving JSON results under `test/results/matmul_mcast_2026-11-27.json`.
- Run the full regression suite (`python3 -m pytest -q`, `BH_HW=1 python3 -m pytest -q`, and `python3 examples/nanbeige.py --device 0 --tokens 8 --timing`) to confirm zero regressions in decode accuracy or speed.
