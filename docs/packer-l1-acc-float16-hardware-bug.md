# Packer L1 Accumulation: IEEE Float16 Hardware Bug

The packer's L1 accumulation path (`PACKER_L1_ACC`) produces **NaN values when operating on IEEE Float16 (A-exponent) data**. This is a hardware-level bug on Blackhole P100A, confirmed deterministic and reproducible. Float16_b (B-exponent / bfloat16) and Float32 L1 accumulation work correctly.

## Summary

| Format | L1 Accumulation | Status |
|--------|----------------|--------|
| Float16_b (bfloat16) | Read-add-write in L1 | **Works** |
| Float32 | Read-add-write in L1 | **Works** |
| Float16 (IEEE half) | Read-add-write in L1 | **Broken — produces NaN** |

## What PACKER_L1_ACC Does

When `llk_pack_reconfig_l1_acc(1)` is called, the packer hardware performs a fused read-add-write cycle instead of a simple write:

1. **Read** existing tile data from the L1 CB write address
2. **Add** the DST register value to it
3. **Write** the sum back to L1

This is used in matmul to accumulate partial sums across K-dimension blocks without the overhead of a full unpack→copy_tile→DST reload cycle. The hardware sets `Pack_L1_Acc=1` and `Disable_pack_zero_flags=1` in the THCON packer section config registers.

```
Standard pack:     DST ──────────────────────> L1 (write)
L1 accumulation:   DST ──┐                 ┌─> L1 (write)
                         ADD ◄── L1 (read) ─┘
```

## The Bug

When the packer's L1 accumulation operates on **IEEE Float16 (A-exponent, 5-bit exponent, 10-bit mantissa)** tiles, it produces corrupted values. The corrupted values are always NaN with specific bit patterns:

| Raw value | IEEE Float16 interpretation |
|-----------|----------------------------|
| `0x7fff` | +NaN (exp=0x1f, mantissa=0x3ff) |
| `0xffff` | -NaN (exp=0x1f, mantissa=0x3ff) |

These are all-ones patterns in the sign+exponent+mantissa fields.

### Trigger conditions

The bug requires **all three** of these conditions:

1. **FPU matmul instruction** (`matmul_block`) producing values in DST
2. **Packer L1 accumulation** (`pack_reconfig_l1_acc(1)`) writing IEEE Float16
3. **Multiple subblocks** packed per L1 acc cycle (`in1_num_subblocks >= 2`)

What does **not** trigger the bug (even with Float16 + L1 acc enabled):

| Scenario | Result |
|----------|--------|
| `copy_tile` + L1 acc (no matmul) | Clean |
| Matmul + L1 acc with 1 subblock (in1_num_subblocks=1) | Clean |
| Matmul + L1 acc with Float16_b | Clean |
| Matmul + multiple subblocks + reload (no L1 acc) | Clean |

The minimal repro uses the matmul inner loop from `matmul_peak` with subblock 8h×1w, `in0_block_w=4`, `in1_num_subblocks=6`.

### It is data-dependent

The corrupted position is **not fixed** — it depends on the input data. Different random seeds produce NaN at different tiles and intra-tile positions:

| Seed | Tile | Face | Intra-tile position | Raw |
|------|------|------|---------------------|-----|
| 42 | 20 | (0,1) | (0,2) | 0xffff |
| 1 | 44 | (1,0) | (0,7) | 0x7fff |
| 256 | 16 | (0,0) | (13,15) | 0x7fff |
| 256 | 39 | (1,0) | (1,13) | 0x7fff |
| 9999 | 42 | (0,0) | (7,1) | 0x7fff |

However, for a **given input**, the corruption is completely deterministic — same position, same value on every run.

Not every block count triggers the bug either. With the minimal repro kernel (10 cores, subblock 8h×1w, `in0_block_w=4`):

| Blocks | L1 acc cycles | NaN per core |
|--------|---------------|-------------|
| 3–6 | 1–4 | 0 |
| **7** | **5** | **1** |
| 8–24 | 6–22 | 0 |
| **25** | **23** | **2** |
| 26–27 | 24–25 | 0 |
| **28** | **26** | **1** |
| 29–30 | 27–28 | 0 |
| **31–32** | **29–30** | **1** |
| 48, 64 | 46, 62 | 0 |

The pattern is irregular — specific block counts produce NaN because the accumulated partial sum at the affected element hits a bad bit pattern in the A-exponent adder.

### Software simulation produces correct values

Tracing the accumulation block-by-block in Python float16 for the corrupted position shows **completely mundane, well-behaved values**:

```
blocks=7, position (m=3,n=1,r=28,c=10):
  block 0: L1 = -0.627  (0xb904)
  block 1: L1 = +0.015  (0x2380)   ← L1 acc: -0.627 + 0.642
  block 2: L1 = -0.301  (0xb4d0)
  block 3: L1 = +0.418  (0x36b0)
  block 4: L1 = +0.797  (0x3a60)
  block 5: L1 = +0.910  (0x3b48)   ← hardware produces 0x7fff (NaN) here
  block 6: L1 = +1.667  (0x3eab)   ← final (reload, no L1 acc)
```

No overflow, no denorm, no edge case. The packer hardware produces all-ones NaN from ordinary small floats.

### Reproduction data (blackhole-py matmul_peak, `F16=1 TT_USB=1`)

5120×4096×5632 matmul, inputs uniform in [-0.5, 0.5], subblock 8h×1w:

| K | in0_block_w | num_blocks | L1 acc cycles | Bad tiles |
|---|-------------|-----------|---------------|-----------|
| 128 | 4 | 1 | 0 | 0 |
| 256 | 4 | 2 | 0 | 0 |
| 512 | 4 | 4 | 2 | 25 |
| 1024 | 4 | 8 | 6 | 34 |
| 2048 | 4 | 16 | 14 | 60 |
| 4096 | 4 | 32 | 30 | 97 |

`num_blocks=1` has zero L1 acc cycles (only one block, packs directly to output). `num_blocks=2` has zero L1 acc cycles (block 0 writes to intermediate CB, block 1 reloads and writes to output — no accumulation). L1 accumulation engages starting at `num_blocks=3` (block 1 calls `llk_pack_reconfig_l1_acc(1)`).

## Proof It Is Not a Compiler Bug

Disassembling the compiled RISC-V kernels for Float16 vs Float16_b shows:

| RISC core | Instructions | Difference |
|-----------|-------------|------------|
| trisc0 (unpack) | 534 | 3 immediate values (format descriptor constants) |
| trisc1 (math/FPU) | 507 | **Zero** — byte-for-byte identical |
| trisc2 (pack) | 434 | 2 immediate values (THCON packer config constants) |

The **opcodes, loop structure, register allocation, and branch targets are identical**. The only differences are literal constants written to hardware config registers that tell the packer which exponent format to use:

```
                        bf16              f16
                        ────              ───
trisc2 pack config:     0xb61e1a01        0xb61e0201     ← THCON section register
trisc2 format desc:     1361 (0x551)      273 (0x111)    ← exponent type encoding
```

The compiler generates the same code. The hardware produces different results.

## Proof It Is the L1 Acc Hardware Path

Running the **same matmul, same data, same Float16 format** with two different accumulation strategies:

| Mode | How it works | Result |
|------|-------------|--------|
| L1 acc ON | `pack_reconfig_l1_acc(1)` — packer does `L1 = DST + L1` in hardware | **10 NaN** |
| L1 acc OFF (reload) | `pack_reconfig_l1_acc(0)` — unpack CB24→DST, matmul adds to DST, pack overwrites CB24 | **Clean** |

The mathematical result is identical. The only difference is whether the addition happens in the packer's hardware adder (L1 acc) or in the DST registers via the unpack+matmul path (reload). The packer's A-exponent adder is broken.

## Why Float16_b Works

Float16_b (bfloat16) uses B-exponent (8-bit exponent, 7-bit mantissa) — the same exponent format as Float32 and the FPU's internal representation. The packer's L1 accumulation hardware appears to be designed and tested for B-exponent formats.

IEEE Float16 uses A-exponent (5-bit exponent, 10-bit mantissa). The L1 accumulation read-add-write cycle mishandles the A-exponent bit layout during the addition step, producing all-ones NaN for specific input value combinations.

## How tt-metal Avoids This

tt-metal **never uses IEEE Float16 for the intermediate/partials CB** when L1 accumulation is active. From every matmul program factory:

```cpp
// matmul_multicore_reuse_mcast_2d_program_factory.cpp:87-90
tt::DataFormat interm0_data_format = packer_l1_acc_en
    ? (fp32_dest_acc_en ? tt::DataFormat::Float32 : tt::DataFormat::Float16_b)
    : (fp32_dest_acc_en ? tt::DataFormat::Float32 : output_data_format);
```

When `packer_l1_acc_en=true`, the intermediate CB is **always Float16_b or Float32**, never Float16. This sidesteps the hardware bug entirely.

## Workarounds

| Approach | Complexity | Performance impact |
|----------|-----------|-------------------|
| **Disable L1 acc for Float16**: use standard spill-reload (unpack→copy_tile→DST each block) | Medium — requires alternate compute kernel path | ~10-15% slower (extra unpack/copy per block) |
| **Add pack_src/pack_dst splitting to compiler**: match tt-metal's format header generation | High — changes to `compiler.py` header generation | None (matches tt-metal behavior) |
| **Restrict Float16 to small K**: only allow `num_blocks ≤ 2` for Float16 matmul | Low — planner constraint | Limits use cases |
| **Use Float16_b internally**: convert F16↔BF16 in dataflow kernels | Medium — format conversion in readers/writers | Small (NOC-bound anyway) |

## Minimal Reproducer

`blackhole-py/examples/l1_acc_bug.py` — standalone repro with configurable parameters:

```bash
# Reproduce (10 cores, 7 blocks, Float16) — produces 10 NaN
PYTHONPATH=. TT_USB=1 uv run examples/l1_acc_bug.py

# Verify Float16_b is clean with same kernel
PYTHONPATH=. TT_USB=1 F16=0 uv run examples/l1_acc_bug.py

# Verify reload path (no L1 acc) is clean with same data
PYTHONPATH=. TT_USB=1 NO_L1_ACC=1 uv run examples/l1_acc_bug.py

# Stress test (120 cores, 32 blocks)
PYTHONPATH=. TT_USB=1 CORES=0 uv run examples/l1_acc_bug.py 32

# Different random data
PYTHONPATH=. TT_USB=1 SEED=256 uv run examples/l1_acc_bug.py 32
```

When NaN is detected, the script automatically sweeps block counts (3..N) to pinpoint the exact L1 ACC cycle that first introduces corruption, then prints the critical (L1_prev, DST) operand pair with full bit-level decomposition.

## Related: F32_ACC DST Overflow (Fixed)

A separate issue discovered during the same investigation: when `FP32_DEST_ACC_EN=1`, the DST register file capacity halves (16→8 tiles). With `DST_SYNC_MODE=0` (half-sync), each acquire/release cycle only gets 4 tiles. An 8-tile subblock overflows DST, causing register aliasing and completely garbled output (PCC ≈ 0.5).

**Fix**: set `dst_full_sync=True` when `f32_acc=True` — gives the full 8-tile DST per cycle. Confirmed working in blackhole-py.
