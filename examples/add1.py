import argparse

from isa import R, Tensix as TT
from program import Buffer, DType, Dram, Program
from ttk.math import AddressModifier, DestinationCounter, SourceCounter, set_dst_row_base
from ttk.mop import LoopTemplate
from ttk.sfpu import SfpuFormat
from ttk.tensix import (
  TensixSem, TensixSemWait, TensixStall, TensixWait,
)
from ttk.unpack import UnpackTarget

_COPY = TT.TTMOVA2D(0, 0, 2, 2, 0)
_COPY_MOP = LoopTemplate(
  outer=4, inner=2, loop=_COPY,
  end0=TT.TTSETRWC(3, 0, 0, 0, 0, 3),
  last=_COPY, outer_last=_COPY,
)

def _dram_page(k, noc_index: int, buffer: Buffer, page: R):
  coords = buffer.dram_coords[noc_index]
  base = k.param(buffer)
  address, coordinate, bank, banks, scale = k.reg(5, exclude=(page, base))
  k.li(banks, len(coords))
  k.remu(bank, page, banks)
  k.divu(address, page, banks)
  k.li(scale, buffer.page_size)
  k.mul(address, address, scale)
  k.add(address, address, base)

  selected = k._new_label("dram_bank_selected")
  invalid = k._new_label("dram_bank_invalid")
  labels = {index: k._new_label(f"dram_bank_{index}") for index in range(len(coords))}
  k.switch(bank, labels, invalid)
  for index, label in labels.items():
    k.label(label)
    k.li(coordinate, coords[index])
    k.j(selected)
  k.label(invalid)
  k.j(invalid)
  k.label(selected)
  return address, coordinate


def add1(src: Buffer, dst: Buffer, *, core=(1, 2), cores=None) -> Program:
  if src.dtype != DType.BF16 or dst.dtype != DType.BF16: raise ValueError("add1 requires BF16 buffers")
  if src.pages != dst.pages: raise ValueError("add1 input and output must have the same tile count")
  cores = (core,) if cores is None else tuple(cores)
  if src.pages < len(cores): raise ValueError("add1 requires at least one tile per core")
  p = Program(cores, buffers=(src, dst))
  tiles_per_core, extra = divmod(src.pages, len(cores))
  input_cb = p.cb(src.dtype, name="input")
  output_cb = p.cb(dst.dtype, name="output")

  AddressModifier(source_a=SourceCounter(increment=8),
                  destination=DestinationCounter(increment=8)).configure(p.fpu, 2)
  set_dst_row_base(p.fpu)
  p.fpu.mop.configure(_COPY_MOP)
  p.sfpu.configure()
  add_one = p.sfpu.install(p.sfpu.add_immediate_program(1, format=SfpuFormat.BF16))

  noc = p.brisc.noc(0)
  start, count = p.brisc.arg(0), p.brisc.arg(1)
  for tile in p.brisc.range(count):
    with p.brisc.scope():
      page = p.brisc.reg(exclude=(start, tile))
      p.brisc.add(page, start, tile)
      source, source_coordinate = _dram_page(p.brisc, noc.index, src, page)
      noc.read_into_cb(source, source_coordinate, input_cb)

  for _ in p.trisc0.range(p.trisc0.arg(1)):
    p.unpack.move(input_cb, UnpackTarget.SRCA)

  for _ in p.trisc1.range(p.trisc1.arg(1)):
    p.fpu.semaphore_wait(TensixSem.MATH_PACK, TensixSemWait.STALL_ON_MAX,
                         TensixStall.SYNC | TensixStall.MATH | TensixStall.SFPU)
    p.fpu.stall(TensixStall.MATH, TensixWait.SRCA_VLD)
    p.fpu.mop.run()
    p.sfpu.run_tile(add_one)
    p.fpu.stall(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU)
    p.fpu.semaphore_post(TensixSem.MATH_PACK)

  for _ in p.trisc2.range(p.trisc2.arg(1)):
    p.pack.move(0, output_cb)

  noc = p.ncrisc.noc(1)
  start, count = p.ncrisc.arg(0), p.ncrisc.arg(1)
  for tile in p.ncrisc.range(count):
    with p.ncrisc.scope():
      page = p.ncrisc.reg(exclude=(start, tile))
      p.ncrisc.add(page, start, tile)
      target, target_coordinate = _dram_page(p.ncrisc, noc.index, dst, page)
      noc.write_from_cb(output_cb, target, target_coordinate)
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
