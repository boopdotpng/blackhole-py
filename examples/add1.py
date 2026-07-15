import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from program import Buffer, DType, Dram, Program
from ttk.sfpu import SfpuFormat

def add1(src: Buffer, dst: Buffer, *, core=(1, 2)) -> Program:
  if src.dtype != DType.BF16 or dst.dtype != DType.BF16: raise ValueError("add1 requires BF16 buffers")
  if src.pages != dst.pages: raise ValueError("add1 input and output must have the same tile count")
  p = Program((core,), buffers=(src, dst))
  depth = min(16, src.pages)
  input_cb = p.cb(src.dtype, depth, name="input")
  output_cb = p.cb(dst.dtype, depth, name="output")

  input_reader = p.brisc.init_cb(input_cb)
  input_unpack = p.trisc0.init_cb(input_cb)
  output_pack = p.trisc2.init_cb(output_cb)
  output_writer = p.ncrisc.init_cb(output_cb)

  p.unpack.init(input_unpack)
  p.math.initialize()
  add_one = p.math.sfpu.install(p.math.sfpu.add_immediate_program(1, format=SfpuFormat.BF16))
  p.pack.init(output_pack)

  noc = p.brisc.noc(0).initialize_from_firmware()
  for tile in p.brisc.range(src.pages):
    input_reader.reserve_back()
    with noc.read_batch() as reads:
      reads.issue_dram(src, tile, input_reader)
    input_reader.push_back()

  for _ in p.trisc0.range(src.pages):
    input_unpack.wait_front()
    p.unpack.wait_config_idle()
    p.unpack.configure_source(input_unpack)
    p.unpack.commit_config()
    p.unpack.to_src_a()
    p.unpack.wait()
    input_unpack.pop_front()

  for _ in p.trisc1.range(src.pages):
    p.math.acquire_dst()
    p.math.copy_src_a_to_dst()
    p.math.sfpu.run_tile(add_one)
    p.math.publish_dst()

  for _ in p.trisc2.range(src.pages):
    p.pack.acquire_dst()
    output_pack.reserve_back()
    p.pack.to_cb()
    output_pack.push_back()
    p.pack.release_dst()

  noc = p.ncrisc.noc(1).initialize_from_firmware()
  for tile in p.ncrisc.range(dst.pages):
    output_writer.wait_front()
    with noc.write_ack_batch() as writes:
      writes.issue_dram(dst, tile, output_writer)
    output_writer.pop_front()
  return p

def show(program: Program):
  print(f"cores: {program.cores}"); print(f"CBs:   {program.cbs}")
  print(f"params: {[(buffer.name, hex(program.param_addr(buffer)), hex(buffer.addr)) for buffer in program.params.values()]}")
  for core in program.cores:
    for role, image in program.kernels[core].items(): print(f"{core} {role:7s}: {len(image):4d} bytes")

def run_hardware(tiles=1):
  import numpy as np
  from device import Device

  device = Device()
  try:
    device.init_device()
    shape = (32, 32 * tiles)
    src = device.dram.buffer("src", DType.BF16, shape, shape)
    dst = device.dram.buffer("dst", DType.BF16, shape, shape)
    program = add1(src, dst)
    values = ((np.arange(1024 * tiles, dtype=np.float32) % 257) - 128).reshape(shape) / 8
    source = src.from_numpy(values)
    expected = dst.from_numpy(src.to_numpy(source) + 1)
    device.write(src, source)
    device.run(program)
    actual = device.read(dst)
    if actual != expected:
      mismatch = next(i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
      raise AssertionError(f"add1 mismatch at byte {mismatch}: {actual[mismatch]:02x} != {expected[mismatch]:02x}")
    print(f"PASS add1: {tiles} BF16 tile{'s' if tiles != 1 else ''}"); show(program)
  finally: device.close()

def main():
  parser = argparse.ArgumentParser(); parser.add_argument("--run", action="store_true"); parser.add_argument("--tiles", type=int, default=1)
  args = parser.parse_args()
  if args.tiles <= 0: parser.error("--tiles must be positive")
  if args.run: return run_hardware(args.tiles)
  dram = Dram()
  shape = (32, 32 * args.tiles)
  src = dram.buffer("src", DType.BF16, shape, shape)
  dst = dram.buffer("dst", DType.BF16, shape, shape); show(add1(src, dst))

if __name__ == "__main__": main()
