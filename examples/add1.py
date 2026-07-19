import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from program import Buffer, DType, Dram, Program
from ttk.sfpu import SfpuFormat
from ttk.unpack import UnpackTarget

def add1(src: Buffer, dst: Buffer, *, core=(1, 2), cores=None) -> Program:
  cores = (core,) if cores is None else tuple(cores)
  p = Program(cores, buffers=(src, dst))
  tiles_per_core, extra = divmod(src.pages, len(cores))
  input_cb = p.cb(src.dtype)
  output_cb = p.cb(dst.dtype)

  dst_tile = p.dst.tile()

  noc = p.brisc.noc(0)
  start, count = p.brisc.arg(0), p.brisc.arg(1)
  for tile in p.brisc.range(count):
    with p.brisc.scope():
      page = p.brisc.reg(exclude=(start, tile))
      p.brisc.add(page, start, tile)
      noc.read_into_cb(src, page, input_cb)

  for _ in p.trisc0.range(p.trisc0.arg(1)):
    p.unpack.move(input_cb, UnpackTarget.SRCA)

  for _ in p.trisc1.range(p.trisc1.arg(1)):
    with p.fpu.tile(dst_tile):
      p.fpu.copy_a(dst_tile)
      p.sfpu.add_scalar(dst_tile, 1, format=SfpuFormat.BF16)

  for _ in p.trisc2.range(p.trisc2.arg(1)):
    p.pack.move(dst_tile, output_cb)

  noc = p.ncrisc.noc(1)
  start, count = p.ncrisc.arg(0), p.ncrisc.arg(1)
  for tile in p.ncrisc.range(count):
    with p.ncrisc.scope():
      page = p.ncrisc.reg(exclude=(start, tile))
      p.ncrisc.add(page, start, tile)
      noc.write_from_cb(output_cb, dst, page)
  args, start = {}, 0
  for index, worker in enumerate(cores):
    count = tiles_per_core + int(index < extra)
    args[worker] = (start, count)
    start += count
  p.set_runtime_args(args)
  return p

def show(program: Program):
  print(f"cores: {len(program.cores)} ({program.cores[0]}..{program.cores[-1]})"); print(f"CBs:   {program.cbs}")
  print(f"params: {[(buffer.name, hex(program.param_addr(buffer)), hex(buffer.addr)) for buffer in program.params.values()]}")
  core = program.cores[0]
  for role, image in program.kernels[core].items(): print(f"{role:7s}: {len(image):4d} bytes")

def run_hardware(tiles=1, *, all_cores=False):
  import numpy as np
  from device import Device

  device = Device()
  try:
    device.init_device()
    cores = tuple(device.pcie.cores) if all_cores else None
    total_tiles = tiles * len(cores) if cores is not None else tiles
    shape = (32, 32 * total_tiles)
    src = device.dram.buffer("src", DType.BF16, shape, shape)
    dst = device.dram.buffer("dst", DType.BF16, shape, shape)
    program = add1(src, dst, cores=cores)
    values = ((np.arange(1024 * total_tiles, dtype=np.float32) % 257) - 128).reshape(shape) / 8
    source = src.from_numpy(values)
    expected = dst.from_numpy(src.to_numpy(source) + 1)
    device.write(src, source)
    timestamps = device.run(program)
    kernel_us = timestamps[-1].us
    actual = device.read(dst)
    if actual != expected:
      mismatch = next(i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
      raise AssertionError(f"add1 mismatch at byte {mismatch}: {actual[mismatch]:02x} != {expected[mismatch]:02x}")
    print(
      f"PASS add1: {len(program.cores)} core{'s' if len(program.cores) != 1 else ''} "
      f"x {tiles} BF16 tile{'s' if tiles != 1 else ''}/core = {total_tiles} tiles"
    )
    traffic = total_tiles * (src.page_size + dst.page_size)
    print(f"kernel: {kernel_us:.3f} us, DRAM traffic: {traffic / kernel_us / 1e3:.3f} GB/s")
    show(program)
  finally: device.close()

def main():
  parser = argparse.ArgumentParser(); parser.add_argument("--run", action="store_true")
  parser.add_argument("--tiles", type=int, default=1, help="tiles, or tiles per core with --all-cores")
  parser.add_argument("--all-cores", action="store_true")
  args = parser.parse_args()
  if args.tiles <= 0: parser.error("--tiles must be positive")
  if args.all_cores and not args.run: parser.error("--all-cores requires --run")
  if args.run: return run_hardware(args.tiles, all_cores=args.all_cores)
  dram = Dram()
  shape = (32, 32 * args.tiles)
  src = dram.buffer("src", DType.BF16, shape, shape)
  dst = dram.buffer("dst", DType.BF16, shape, shape); show(add1(src, dst))

if __name__ == "__main__": main()
