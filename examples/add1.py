#!/usr/bin/env python3
"""Element-wise add-1 on every tile: validates SFPU scalar broadcast path."""
import os, struct, random
import numpy as np

from device import Device
from program import Dtype, Program
from examples.kernel_bins import kernel_from_ptloads

def _bf16(x: float) -> int: return struct.unpack("<I", struct.pack("<f", x))[0] >> 16
def _f32(x: int) -> float: return struct.unpack("<f", struct.pack("<I", (x & 0xFFFF) << 16))[0]
def _bf16_rtne(x: float) -> int:
  bits = struct.unpack("<I", struct.pack("<f", x))[0]
  low = bits & 0xFFFF
  hi = bits >> 16
  if low > 0x8000 or (low == 0x8000 and (hi & 1)):
    hi += 1
  return hi & 0xFFFF

def _format_bf16_words(data: bytes, count: int = 16) -> str:
  return " ".join(
    f"{int.from_bytes(data[i : i + 2], 'little'):04x}"
    for i in range(0, min(len(data), count * 2), 2)
  )

def _seed_src_tensor(num_tiles: int, pattern: str) -> bytes:
  if pattern == "ordered":
    return b"".join(
      _bf16(float(i)).to_bytes(2, "little")
      for i in range(num_tiles * 32 * 32)
    )
  rng = random.Random(42)
  return b"".join(
    _bf16(rng.random()).to_bytes(2, "little")
    for _ in range(num_tiles * 32 * 32)
  )

def _expected_add1(src: bytes, *, rtne: bool) -> bytes:
  conv = _bf16_rtne if rtne else _bf16
  out = bytearray(len(src))
  for i in range(0, len(src), 2):
    x = int.from_bytes(src[i : i + 2], "little")
    y = conv(_f32(x) + 1.0)
    out[i : i + 2] = y.to_bytes(2, "little")
  return bytes(out)

def _first_mismatch(got: bytes, exp: bytes) -> int | None:
  return next((i for i, (g, e) in enumerate(zip(got, exp)) if g != e), None)

def main():
  device = Device()
  try:
    num_cores = len(device.cores)
    tiles_per_core = int(os.environ.get("TILES", "4"))
    input_pattern = os.environ.get("INPUT_PATTERN", "ordered")
    print_n = int(os.environ.get("PRINT_N", "16"))
    n_tiles = num_cores * tiles_per_core

    src_rm = _seed_src_tensor(n_tiles, input_pattern)

    src_buf = device.alloc_write(src_rm, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="src")
    dst_buf = device.dram.alloc(n_tiles, dtype=Dtype.Float16_b, shape=(n_tiles, 32, 32), name="dst")

    target_cores = sorted(device.cores, key=lambda xy: (xy[1], xy[0]))[:num_cores]
    core_index = {xy: i for i, xy in enumerate(target_cores)}

    def reader_args(x, y):
      return [src_buf.addr, core_index[(x, y)] * tiles_per_core, tiles_per_core]

    def writer_args(x, y):
      return [dst_buf.addr, core_index[(x, y)] * tiles_per_core, tiles_per_core]

    def compute_args(_x, _y):
      return [tiles_per_core]

    prog = Program(
      num_cores=num_cores,
      brisc=kernel_from_ptloads("add1_reader_brisc.kernel", reader_args),
      ncrisc=kernel_from_ptloads("add1_writer_ncrisc.kernel", writer_args),
      trisc0=kernel_from_ptloads("add1_compute_trisc0.kernel", compute_args),
      trisc1=kernel_from_ptloads("add1_compute_trisc1.kernel", compute_args),
      trisc2=kernel_from_ptloads("add1_compute_trisc2.kernel", compute_args),
      cbs=[(0, Dtype.Float16_b.tile_size, 2), (16, Dtype.Float16_b.tile_size, 2)],
    )
    prog.name = "add1"
    device.queue(prog)
    device.run()
    out = device.dram_read(dst_buf)
    trunc = _expected_add1(src_rm, rtne=False)
    rtne = _expected_add1(src_rm, rtne=True)
    trunc_mismatch = _first_mismatch(out, trunc)
    rtne_mismatch = _first_mismatch(out, rtne)

    print(f"add1 input pattern: {input_pattern}")
    print(f"output first {print_n}: {_format_bf16_words(out, print_n)}")
    print(f"trunc  first {print_n}: {_format_bf16_words(trunc, print_n)}")
    print(f"rtne   first {print_n}: {_format_bf16_words(rtne, print_n)}")
    if trunc_mismatch is None:
      print(f"PASS trunc  {n_tiles} tiles across {num_cores} cores")
    else:
      print(
        f"trunc mismatch byte={trunc_mismatch} "
        f"got={out[trunc_mismatch:trunc_mismatch + 32].hex()} "
        f"exp={trunc[trunc_mismatch:trunc_mismatch + 32].hex()}"
      )
    if rtne_mismatch is None:
      print(f"PASS rtne   {n_tiles} tiles across {num_cores} cores")
    else:
      print(
        f"rtne mismatch byte={rtne_mismatch} "
        f"got={out[rtne_mismatch:rtne_mismatch + 32].hex()} "
        f"exp={rtne[rtne_mismatch:rtne_mismatch + 32].hex()}"
      )

  finally:
    device.close()

if __name__ == "__main__":
  main()
