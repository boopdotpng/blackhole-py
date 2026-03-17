#!/usr/bin/env python3
"""Minimal reproducer for the packer L1 accumulation Float16 hardware bug.

The bug requires BOTH:
  1. FPU matmul instruction (matmul_block) producing values in DST
  2. Packer L1 accumulation (pack_reconfig_l1_acc(1)) writing Float16
  3. Multiple subblocks packed per L1 acc cycle (in1_num_subblocks > 1)

copy_tile + L1 acc alone does NOT trigger the bug. Single-subblock matmul +
L1 acc also does NOT trigger it. The corruption only appears when multiple
subblocks are packed sequentially to different CB24 positions with L1 acc
enabled — i.e., the matmul inner loop with in1_num_subblocks >= 2.

The NaN pattern is completely deterministic: every core gets exactly 1 NaN
at the same face/position (face=(0,1), intra=(0,2)), always 0xffff.
Float16_b (bfloat16) is unaffected.

Usage:
  PYTHONPATH=. TT_USB=1 uv run examples/l1_acc_bug.py         # Float16 (triggers bug)
  PYTHONPATH=. TT_USB=1 F16=0 uv run examples/l1_acc_bug.py   # Float16_b (clean)
  PYTHONPATH=. TT_USB=1 uv run examples/l1_acc_bug.py 16      # custom block count
"""
import os, sys
import numpy as np

from hw import *
from dispatch import *
from device import Device, Dtype
from dram import tilize, untilize

NUM_BLOCKS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
USE_F16 = os.environ.get("F16", "1") != "0"
IO_DTYPE = Dtype.Float16 if USE_F16 else Dtype.Float16_b
MAX_CORES = int(os.environ.get("CORES", "10")) or None  # 0 = use all
NO_L1_ACC = os.environ.get("NO_L1_ACC", "") == "1"

# Matmul parameters — match matmul_peak's structure
SBH = 8           # out_subblock_h
SBW = 1           # out_subblock_w
BW = 4            # in0_block_w (K tiles per block)
PCM = 8           # per_core_m (= in0_num_subblocks * SBH = 1*8)
PCN = 6           # per_core_n (= in1_num_subblocks * SBW = 6*1)
IN0_NUM_SB = PCM // SBH  # 1
IN1_NUM_SB = PCN // SBW  # 6
IN0_SB_TILES = SBH * BW  # 32
OUT_SB_TILES = SBH * SBW  # 8
OUT_BLOCK_TILES = PCM * PCN  # 48

# -- kernel sources --

READER = f"""\
#include <cstdint>
#define A(n) get_arg_val<uint32_t>(n)

void kernel_main() {{
  const uint32_t num_blocks = A(0);
  constexpr uint32_t in0_block_num_tiles = {PCM * BW};
  const InterleavedAddrGenFast<true> a_dram = {{
    .bank_base_address = A(1),
    .page_size = get_tile_size(tt::CBIndex::c_0),
    .data_format = get_dataformat(tt::CBIndex::c_0),
  }};
  for (uint32_t b = 0; b < num_blocks; b++) {{
    cb_reserve_back(tt::CBIndex::c_0, in0_block_num_tiles);
    uint32_t l1 = get_write_ptr(tt::CBIndex::c_0);
    for (uint32_t t = 0; t < in0_block_num_tiles; t++) {{
      noc_async_read_tile(b * in0_block_num_tiles + t, a_dram, l1);
      l1 += get_tile_size(tt::CBIndex::c_0);
    }}
    noc_async_read_barrier();
    cb_push_back(tt::CBIndex::c_0, in0_block_num_tiles);
  }}
}}
"""

WRITER = f"""\
#include <cstdint>
#define A(n) get_arg_val<uint32_t>(n)

void kernel_main() {{
  const uint32_t num_blocks = A(0);
  constexpr uint32_t in1_block_num_tiles = {PCN * BW};
  constexpr uint32_t out_tiles = {OUT_BLOCK_TILES};
  constexpr uint32_t sb_h = {SBH};
  constexpr uint32_t sb_w = {SBW};
  constexpr uint32_t sb_tiles = {OUT_SB_TILES};
  constexpr uint32_t in1_num_sb = {IN1_NUM_SB};
  constexpr uint32_t in0_num_sb = {IN0_NUM_SB};
  const InterleavedAddrGenFast<true> b_dram = {{
    .bank_base_address = A(1),
    .page_size = get_tile_size(tt::CBIndex::c_1),
    .data_format = get_dataformat(tt::CBIndex::c_1),
  }};
  const InterleavedAddrGenFast<true> c_dram = {{
    .bank_base_address = A(2),
    .page_size = get_tile_size(tt::CBIndex::c_16),
    .data_format = get_dataformat(tt::CBIndex::c_16),
  }};
  // Feed B tiles each block
  for (uint32_t b = 0; b < num_blocks; b++) {{
    cb_reserve_back(tt::CBIndex::c_1, in1_block_num_tiles);
    uint32_t l1 = get_write_ptr(tt::CBIndex::c_1);
    for (uint32_t t = 0; t < in1_block_num_tiles; t++) {{
      noc_async_read_tile(t, b_dram, l1);
      l1 += get_tile_size(tt::CBIndex::c_1);
    }}
    noc_async_read_barrier();
    cb_push_back(tt::CBIndex::c_1, in1_block_num_tiles);
  }}
  // Write output: iterate subblocks, write each subblock's tiles
  const uint32_t out_base = A(3);
  uint32_t sbh_start = out_base;
  for (uint32_t in0_sb = 0; in0_sb < in0_num_sb; in0_sb++) {{
    uint32_t sbw_start = sbh_start;
    for (uint32_t in1_sb = 0; in1_sb < in1_num_sb; in1_sb++) {{
      cb_wait_front(tt::CBIndex::c_16, sb_tiles);
      uint32_t l1_addr = get_read_ptr(tt::CBIndex::c_16);
      uint32_t row_id = sbw_start;
      for (uint32_t h = 0; h < sb_h; h++) {{
        uint32_t tile_id = row_id;
        for (uint32_t w = 0; w < sb_w; w++) {{
          noc_async_write_tile(tile_id, c_dram, l1_addr);
          l1_addr += get_tile_size(tt::CBIndex::c_16);
          tile_id += 1;
        }}
        row_id += {PCN};
      }}
      noc_async_write_barrier();
      cb_pop_front(tt::CBIndex::c_16, sb_tiles);
      sbw_start += sb_w;
    }}
    sbh_start += sb_h * {PCN};
  }}
}}
"""

def _make_compute(use_l1_acc: bool) -> str:
  if use_l1_acc:
    l1_acc_define = "#define PACKER_L1_ACC 1"
    l1_acc_config = (
      "          if (block == 0) { PACK((llk_pack_reconfig_l1_acc(0))); }\n"
      "          else if (block == 1) { PACK((llk_pack_reconfig_l1_acc(1))); }")
    reload_enable = (
      f"    if (num_blocks > 2 && block < num_blocks - 2) {{\n"
      f"      cb_wait_front(tt::CBIndex::c_24, {OUT_BLOCK_TILES});\n"
      f"      cb_pop_front(tt::CBIndex::c_24, {OUT_BLOCK_TILES});\n"
      f"    }}\n"
      f"    if (num_blocks >= 2 && block == num_blocks - 2) enable_reload = true;")
  else:
    l1_acc_define = "// NO L1 ACC — reload every block"
    l1_acc_config = "          PACK((llk_pack_reconfig_l1_acc(0)));"
    # No CB24 pop needed — each subblock's reload(8) + pack(8) cycle
    # naturally keeps the read/write pointers synchronized.
    reload_enable = "    if (block == 0) enable_reload = true;"

  # Build C++ source — use % substitution to avoid f-string brace escaping hell
  tmpl = """\
#include <cstdint>
%(l1_acc_define)s
#include "compute_kernel_api/common.h"
#include "compute_kernel_api/matmul.h"
#include "compute_kernel_api/tile_move_copy.h"

namespace NAMESPACE {
void MAIN {
  const uint32_t num_blocks = get_arg_val<uint32_t>(0);
  constexpr uint32_t in0_block_w = %(BW)d;
  constexpr uint32_t out_subblock_h = %(SBH)d;
  constexpr uint32_t out_subblock_w = %(SBW)d;
  constexpr uint32_t out_subblock_num_tiles = %(OUT_SB_TILES)d;
  constexpr uint32_t out_block_num_tiles = %(OUT_BLOCK_TILES)d;
  constexpr uint32_t in0_block_num_tiles = %(in0_block_num_tiles)d;
  constexpr uint32_t in1_block_num_tiles = %(in1_block_num_tiles)d;
  constexpr uint32_t in0_num_subblocks = %(IN0_NUM_SB)d;
  constexpr uint32_t in1_num_subblocks = %(IN1_NUM_SB)d;
  constexpr uint32_t in0_subblock_num_tiles = %(IN0_SB_TILES)d;
  constexpr uint32_t in1_per_core_w = %(PCN)d;
  constexpr uint32_t transpose = 0;

  mm_block_init(tt::CBIndex::c_0, tt::CBIndex::c_1, tt::CBIndex::c_16,
    transpose, out_subblock_w, out_subblock_h, in0_block_w);

  bool enable_reload = false;
  uint32_t out_num_tiles_to_wait = out_subblock_num_tiles;

  for (uint32_t block = 0; block < num_blocks; block++) {
    const bool last_out = (block == (num_blocks - 1));

    cb_wait_front(tt::CBIndex::c_0, in0_block_num_tiles);
    cb_wait_front(tt::CBIndex::c_1, in1_block_num_tiles);

    int in0_index_subblock_offset = 0;
    for (uint32_t in0_sb = 0; in0_sb < in0_num_subblocks; in0_sb++) {
      int in1_index_subblock_offset = 0;
      for (uint32_t in1_sb = 0; in1_sb < in1_num_subblocks; in1_sb++) {
        tile_regs_acquire();
        if (enable_reload) {
          copy_tile_to_dst_init_short(tt::CBIndex::c_24);
          cb_wait_front(tt::CBIndex::c_24, out_subblock_num_tiles);
          #pragma GCC unroll 0
          for (uint32_t i = 0; i < out_subblock_num_tiles; i++) { copy_tile(tt::CBIndex::c_24, i, i); }
          cb_pop_front(tt::CBIndex::c_24, out_subblock_num_tiles);
          mm_block_init_short(tt::CBIndex::c_0, tt::CBIndex::c_1,
            transpose, out_subblock_w, out_subblock_h, in0_block_w);
        }

        #pragma GCC unroll 0
        for (uint32_t inner = 0; inner < in0_block_w; inner++) {
          const uint32_t in0_tile_index = (uint32_t)(in0_index_subblock_offset + (int)inner);
          const uint32_t in1_tile_index = (uint32_t)(in1_index_subblock_offset + (int)(inner * in1_per_core_w));
          matmul_block(tt::CBIndex::c_0, tt::CBIndex::c_1,
            in0_tile_index, in1_tile_index, 0, transpose, out_subblock_w, out_subblock_h, in0_block_w);
        }

        tile_regs_commit();

        if (last_out) {
          cb_reserve_back(tt::CBIndex::c_16, out_subblock_num_tiles);
          tile_regs_wait();
          PACK((llk_pack_reconfig_l1_acc(0)));
          #pragma GCC unroll 0
          for (uint32_t i = 0; i < out_subblock_num_tiles; i++) { pack_tile(i, tt::CBIndex::c_16); }
          tile_regs_release();
          cb_push_back(tt::CBIndex::c_16, out_subblock_num_tiles);
        } else {
          if (block == 0) {
            cb_reserve_back(tt::CBIndex::c_16, out_num_tiles_to_wait);
            out_num_tiles_to_wait += out_subblock_num_tiles;
          }
          cb_reserve_back(tt::CBIndex::c_24, out_subblock_num_tiles);
          tile_regs_wait();
%(l1_acc_config)s
          #pragma GCC unroll 0
          for (uint32_t i = 0; i < out_subblock_num_tiles; i++) { pack_tile(i, tt::CBIndex::c_24); }
          tile_regs_release();
          cb_push_back(tt::CBIndex::c_24, out_subblock_num_tiles);
        }
        in1_index_subblock_offset += out_subblock_w;
      }
      in0_index_subblock_offset += in0_subblock_num_tiles;
    }

%(reload_enable)s

    cb_pop_front(tt::CBIndex::c_0, in0_block_num_tiles);
    cb_pop_front(tt::CBIndex::c_1, in1_block_num_tiles);
  }
}
}  // namespace NAMESPACE
"""
  return tmpl % dict(
    l1_acc_define=l1_acc_define, l1_acc_config=l1_acc_config, reload_enable=reload_enable,
    BW=BW, SBH=SBH, SBW=SBW, OUT_SB_TILES=OUT_SB_TILES, OUT_BLOCK_TILES=OUT_BLOCK_TILES,
    in0_block_num_tiles=PCM * BW, in1_block_num_tiles=PCN * BW,
    IN0_NUM_SB=IN0_NUM_SB, IN1_NUM_SB=IN1_NUM_SB, IN0_SB_TILES=IN0_SB_TILES, PCN=PCN,
  )

# -- host helpers --

def _to_tile_bytes(arr: np.ndarray, dtype: Dtype) -> bytes:
  tile = arr.astype(np.float16).flatten()
  if dtype == Dtype.Float16:
    return tile.tobytes()
  u32 = tile.astype(np.float32).view(np.uint32)
  return (u32 >> 16).astype(np.uint16).tobytes()

def _from_raw(data: bytes, dtype: Dtype) -> np.ndarray:
  if dtype == Dtype.Float16:
    return np.frombuffer(data, dtype=np.float16).astype(np.float32)
  u16 = np.frombuffer(data, dtype=np.uint16)
  return (u16.astype(np.uint32) << 16).view(np.float32).flatten()

def _f16_parts(raw):
  """Decompose float16 raw uint16 → (sign, exponent, mantissa)."""
  return (raw >> 15) & 1, (raw >> 10) & 0x1f, raw & 0x3ff

def _partial_at(a_data, b_data, block, m, n, row, col):
  """Float16 matmul partial for one block at one output position."""
  v = np.float16(0.0)
  for k in range(BW):
    v = np.float16(float(v) + float(np.float16(np.dot(
      a_data[block * PCM * BW + m * BW + k, row, :].astype(np.float32),
      b_data[n + k * PCN, :, col].astype(np.float32)))))
  return v

def _accum_through(a_data, b_data, last_block, m, n, row, col):
  """Accumulated float16 value after blocks 0..last_block at one position."""
  acc = np.float16(0.0)
  for b in range(last_block + 1):
    p = _partial_at(a_data, b_data, b, m, n, row, col)
    acc = p if b == 0 else np.float16(float(acc) + float(p))
  return acc

def _analyze_corruption(device, a_data, b_data, num_blocks, io_dtype, no_l1_acc,
                        values, out_tiles_per_core, a_buf, b_buf):
  """Sweep block counts to find the exact L1 acc cycle that introduces NaN."""
  elements_per_tile = 32 * 32
  nan_pos = []
  for t in range(out_tiles_per_core):
    start = t * elements_per_tile
    bad = np.where(~np.isfinite(values[start : start + elements_per_tile]))[0]
    for e in bad:
      nan_pos.append((t, e))
  if not nan_pos or num_blocks < 3:
    return

  print(f"\n{'='*72}")
  print("Sweeping block counts to find corruption onset...")
  sweep_c = device.dram.alloc(out_tiles_per_core, io_dtype, name="C_sweep")

  for tile_idx, elem_idx in nan_pos[:3]:
    m, n = tile_idx // PCN, tile_idx % PCN
    face = elem_idx // 256
    abs_r = (face // 2) * 16 + (elem_idx % 256) // 16
    abs_c = (face % 2) * 16 + (elem_idx % 256) % 16
    flat = tile_idx * elements_per_tile + elem_idx

    print(f"\n  tile {tile_idx} (m={m},n={n}) at ({abs_r},{abs_c}):")
    first_nan_k = None
    for k in range(3, num_blocks + 1):
      sp = Program(
        cores=1, reader_kernel=READER,
        compute_kernel=_make_compute(use_l1_acc=not no_l1_acc),
        writer_kernel=WRITER,
        cbs=[
          CBConfig(index=0, dtype=io_dtype, tiles=2 * PCM * BW),
          CBConfig(index=1, dtype=io_dtype, tiles=2 * PCN * BW),
          CBConfig(index=16, dtype=io_dtype, tiles=out_tiles_per_core),
          CBConfig(index=24, dtype=io_dtype, tiles=out_tiles_per_core),
        ],
        reader_args=[k, a_buf.addr],
        writer_args=lambda ci, xy, nn, _k=k: [_k, b_buf.addr, sweep_c.addr, 0],
        compute_args=[k], name="sweep",
      )
      device.queue(sp)
      device.run()
      rb = device.dram.read(sweep_c)
      vk = _from_raw(rb, io_dtype)
      rk = np.frombuffer(rb, dtype=np.uint16)
      v, r = float(vk[flat]), int(rk[flat])
      _, e, _ = _f16_parts(r)
      is_nan = not np.isfinite(v)
      mark = " *** NaN ***" if is_nan else ""
      print(f"    blocks={k:2d} ({k-2:2d} L1 acc): 0x{r:04x} e={e:2d} {v:+.6f}{mark}")
      if is_nan and first_nan_k is None:
        first_nan_k = k

    if first_nan_k is None:
      continue

    # blocks=K-1 was clean, blocks=K has NaN → the NEW L1 acc cycle at block K-2 is the culprit
    # (blocks 1..K-3 are identical between both runs and proven clean)
    crit = first_nan_k - 2
    l1v = _accum_through(a_data, b_data, crit - 1, m, n, abs_r, abs_c)
    dv = _partial_at(a_data, b_data, crit, m, n, abs_r, abs_c)
    ev = np.float16(float(l1v) + float(dv))
    lr, dr, er = int(l1v.view(np.uint16)), int(dv.view(np.uint16)), int(ev.view(np.uint16))
    ls, le, lm = _f16_parts(lr)
    ds, de, dm = _f16_parts(dr)
    es, ee, em = _f16_parts(er)

    print(f"\n  Critical L1 acc at block {crit}:")
    print(f"    L1_prev: 0x{lr:04x} ({float(l1v):+.6f})")
    print(f"      sign={ls} exp={le:2d} (0b{le:05b}) mant=0x{lm:03x} (0b{lm:010b})")
    print(f"    DST:     0x{dr:04x} ({float(dv):+.6f})")
    print(f"      sign={ds} exp={de:2d} (0b{de:05b}) mant=0x{dm:03x} (0b{dm:010b})")
    print(f"    Expected:0x{er:04x} ({float(ev):+.6f})")
    print(f"      sign={es} exp={ee:2d} (0b{ee:05b}) mant=0x{em:03x} (0b{em:010b})")
    print(f"    Hardware: 0xffff (NaN)")
    print(f"    |exp_diff| = {abs(le - de)}")

    # Compare with previous (clean) L1 acc cycle
    if crit >= 2:
      l1p = _accum_through(a_data, b_data, crit - 2, m, n, abs_r, abs_c)
      dp = _partial_at(a_data, b_data, crit - 1, m, n, abs_r, abs_c)
      ep = np.float16(float(l1p) + float(dp))
      lrp, drp, erp = int(l1p.view(np.uint16)), int(dp.view(np.uint16)), int(ep.view(np.uint16))
      _, lep, _ = _f16_parts(lrp)
      _, dep, _ = _f16_parts(drp)
      print(f"\n  Previous (clean) L1 acc at block {crit-1}:")
      print(f"    L1_prev: 0x{lrp:04x} ({float(l1p):+.6f}) exp={lep}")
      print(f"    DST:     0x{drp:04x} ({float(dp):+.6f}) exp={dep}")
      print(f"    Result:  0x{erp:04x} ({float(ep):+.6f}) |exp_diff|={abs(lep-dep)}")

    # Full numpy trace for context
    print(f"\n  Full numpy trace:")
    print(f"  {'blk':>3} {'mode':>7} {'accum':>10} {'partial':>10} {'result':>10}  {'Ae':>3} {'Pe':>3} {'Re':>3}")
    acc = np.float16(0.0)
    for b in range(num_blocks):
      p = _partial_at(a_data, b_data, b, m, n, abs_r, abs_c)
      is_first, is_last = (b == 0), (b == num_blocks - 1)
      r = p if is_first else np.float16(float(acc) + float(p))
      ar, pr, rr = int(acc.view(np.uint16)), int(p.view(np.uint16)), int(r.view(np.uint16))
      _, ae, _ = _f16_parts(ar)
      _, pe, _ = _f16_parts(pr)
      _, re, _ = _f16_parts(rr)
      mode = "L1_ACC" if not is_first and not is_last else ("FIRST" if is_first else "RELOAD")
      mark = " <<<" if b == crit else ""
      print(f"  {b:3d} {mode:>7} 0x{ar:04x} 0x{pr:04x} 0x{rr:04x}   {ae:2d}  {pe:2d}  {re:2d}{mark}")
      acc = r

def main():
  device = Device()
  try:
    num_cores = min(len(device.cores), MAX_CORES) if MAX_CORES else len(device.cores)
    fmt_name = "Float16 (IEEE)" if USE_F16 else "Float16_b (bfloat16)"
    l1_acc_cycles = max(0, NUM_BLOCKS - 2)
    out_tiles_per_core = PCM * PCN
    out_tiles = num_cores * out_tiles_per_core
    num_a_tiles = PCM * BW * NUM_BLOCKS
    num_b_tiles = PCN * BW
    print(f"L1 acc matmul bug repro: {num_cores} cores, {NUM_BLOCKS} K-blocks, {fmt_name}")
    print(f"  per_core: {PCM}m x {PCN}n = {out_tiles_per_core} tiles, "
          f"subblock {SBH}h x {SBW}w, in0_block_w={BW}")
    print(f"  in0_num_sb={IN0_NUM_SB}, in1_num_sb={IN1_NUM_SB}, "
          f"{IN0_NUM_SB * IN1_NUM_SB} subblocks/block")
    acc_mode = "RELOAD (no L1 acc)" if NO_L1_ACC else "L1 ACC"
    print(f"  {out_tiles} total output tiles, {l1_acc_cycles} L1 acc cycles each, mode={acc_mode}")

    seed = int(os.environ.get("SEED", "42"))
    rng = np.random.default_rng(seed)
    print(f"  seed={seed}")

    # A: PCM * BW tiles per block, NUM_BLOCKS blocks
    a_data = rng.uniform(-0.5, 0.5, size=(num_a_tiles, 32, 32)).astype(np.float16)
    a_bytes = b""
    for t in range(num_a_tiles):
      a_bytes += tilize(_to_tile_bytes(a_data[t], IO_DTYPE), IO_DTYPE.bpe, (32, 32))
    a_buf = device.dram.alloc(num_a_tiles, IO_DTYPE, name="A")
    device.dram.write(a_buf, a_bytes)

    # B: PCN * BW tiles (reused every block)
    b_data = rng.uniform(-0.5, 0.5, size=(num_b_tiles, 32, 32)).astype(np.float16)
    b_bytes = b""
    for t in range(num_b_tiles):
      b_bytes += tilize(_to_tile_bytes(b_data[t], IO_DTYPE), IO_DTYPE.bpe, (32, 32))
    b_buf = device.dram.alloc(num_b_tiles, IO_DTYPE, name="B")
    device.dram.write(b_buf, b_bytes)

    # Output
    c_buf = device.dram.alloc(out_tiles, IO_DTYPE, name="C")

    prog = Program(
      cores=num_cores,
      reader_kernel=READER,
      compute_kernel=_make_compute(use_l1_acc=not NO_L1_ACC),
      writer_kernel=WRITER,
      cbs=[
        CBConfig(index=0, dtype=IO_DTYPE, tiles=2 * PCM * BW),
        CBConfig(index=1, dtype=IO_DTYPE, tiles=2 * PCN * BW),
        CBConfig(index=16, dtype=IO_DTYPE, tiles=out_tiles_per_core),
        CBConfig(index=24, dtype=IO_DTYPE, tiles=out_tiles_per_core),
      ],
      reader_args=[NUM_BLOCKS, a_buf.addr],
      writer_args=lambda ci, xy, n: [NUM_BLOCKS, b_buf.addr, c_buf.addr,
                                      ci * out_tiles_per_core],
      compute_args=[NUM_BLOCKS],
      name="l1_acc_matmul_repro",
    )

    device.queue(prog)
    device.run()

    # Read back and analyze
    result = device.dram.read(c_buf)
    values = _from_raw(result, IO_DTYPE)

    nan_mask = ~np.isfinite(values)
    nan_count = int(nan_mask.sum())

    if nan_count > 0:
      print(f"\n*** BUG REPRODUCED: {nan_count} NaN values "
            f"out of {len(values)} elements ({out_tiles} tiles) ***")
      elements_per_tile = 32 * 32
      raw_u16 = np.frombuffer(result, dtype=np.uint16)
      bad_tiles = 0
      for t in range(out_tiles):
        start = t * elements_per_tile
        tile_vals = values[start : start + elements_per_tile]
        tile_raw = raw_u16[start : start + elements_per_tile]
        tile_nans = ~np.isfinite(tile_vals)
        if tile_nans.any():
          bad_tiles += 1
          positions = np.where(tile_nans)[0]
          for pos in positions[:3]:
            face = pos // 256
            intra = pos % 256
            face_r, face_c = face // 2, face % 2
            row_in_face, col_in_face = intra // 16, intra % 16
            print(f"  tile {t:3d}  face=({face_r},{face_c})  "
                  f"intra=({row_in_face},{col_in_face})  "
                  f"raw=0x{tile_raw[pos]:04x}")
      print(f"  {bad_tiles} tiles affected out of {out_tiles}")
      _analyze_corruption(device, a_data, b_data, NUM_BLOCKS, IO_DTYPE, NO_L1_ACC,
                          values, out_tiles_per_core, a_buf, b_buf)
    else:
      print(f"\nNo NaN values found.")

  finally:
    device.close()

if __name__ == "__main__":
  main()
