#!/usr/bin/env python3
"""One BF16 tile of add1 through the real unpack/FPU/SFPU/pack pipeline."""
import argparse, struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import KernelBuilder
from program import Buffer, DType, DramAllocator, KernelBundle, Param, Program
from ttk.cb import TileBuffer
from ttk.math import Math
from ttk.pack import Pack
from ttk.sfpu import SfpuFormat
from ttk.sync import Barrier
from ttk.tile import tilize, untilize
from ttk.unpack import Unpack


CORE, TILE_BYTES = (1, 2), 2048
INPUT_CB_ADDR, INPUT_CB_FLAG = 0x37000, 0x36F00
OUTPUT_CB_ADDR, OUTPUT_CB_FLAG = INPUT_CB_ADDR + TILE_BYTES, INPUT_CB_FLAG + 4
INIT_BARRIER_ADDR = INPUT_CB_FLAG + 0x10


def lower_add1(src: Buffer, dst: Buffer, *, core=CORE, read_coord=0, write_coord=0) -> Program:
  if src.layout != "tile" or dst.layout != "tile": raise ValueError("add1 requires tile-layout buffers")
  if src.dtype != DType.BF16 or dst.dtype != DType.BF16: raise ValueError("add1 requires BF16")
  if src.tiles != 1 or dst.tiles != 1: raise ValueError("add1 currently handles one tile")
  src_param, dst_param = Param("src", src), Param("dst", dst)

  def build_reader(k: KernelBuilder):
    input_cb = TileBuffer(k, input_cb_config)
    noc = k.noc(0).initialize_from_firmware()
    with noc.read_batch() as reads:
      reads.issue(k.param(src_param), read_coord, input_cb.addr, TILE_BYTES)
    input_cb.publish()

  def build_unpack(k: KernelBuilder):
    input_cb = TileBuffer(k, input_cb_config)
    unpack = Unpack(k).init(input_cb)
    Barrier(k, init_barrier, 0).wait()
    input_cb.wait()
    unpack.to_src_a()
    unpack.wait()

  def build_math(k: KernelBuilder):
    math = Math(k).initialize()
    add_one = math.sfpu.install(math.sfpu.add_immediate_program(1, format=SfpuFormat.BF16))
    Barrier(k, init_barrier, 1).wait()
    math.copy_src_a_to_dst()
    math.sfpu.run_tile(add_one)
    math.publish_dst()

  def build_pack(k: KernelBuilder):
    output_cb = TileBuffer(k, output_cb_config)
    pack = Pack(k).init(output_cb)
    Barrier(k, init_barrier, 2).wait()
    pack.acquire_dst()
    pack.to_cb()
    output_cb.publish()

  def build_writer(k: KernelBuilder):
    output_cb = TileBuffer(k, output_cb_config)
    output_cb.wait()
    noc = k.noc(1).initialize_from_firmware()
    with noc.write_ack_batch() as writes:
      writes.issue(output_cb.addr, k.param(dst_param), write_coord, TILE_BYTES)

  bundle = KernelBundle((core,), params=(src_param, dst_param),
    brisc=build_reader, trisc0=build_unpack, trisc1=build_math,
    trisc2=build_pack, ncrisc=build_writer)
  input_cb_config = bundle.cb(DType.BF16, 1, INPUT_CB_ADDR, flag_addr=INPUT_CB_FLAG)
  output_cb_config = bundle.cb(DType.BF16, 1, OUTPUT_CB_ADDR, flag_addr=OUTPUT_CB_FLAG)
  init_barrier = bundle.barrier(3, INIT_BARRIER_ADDR)
  return bundle.lower()


def _bf16(value): return struct.unpack("<I", struct.pack("<f", float(value)))[0] >> 16
def _fp32(value): return struct.unpack("<f", struct.pack("<I", value << 16))[0]


def input_and_reference():
  source_words = tuple(_bf16((x % 257 - 128) / 8) for x in range(1024))
  result_words = tuple(_bf16(_fp32(x) + 1) for x in source_words)
  encode = lambda words: struct.pack(f"<{len(words)}H", *words)
  return encode(source_words), encode(result_words)


def show(program: Program):
  print(f"cores: {program.cores}"); print(f"CBs:   {program.cbs}")
  print(f"params: {[(param.name, hex(program.param_addr(param)), hex(param.initial.addr)) for param in program.params]}")
  for core in program.cores:
    for role, image in program.kernels[core].items(): print(f"{core} {role:7s}: {len(image):4d} bytes")


def run_hardware():
  from device import Device
  from ttk.dram import endpoint_coords

  device = Device()
  try:
    device.upload_fw()
    src = device.dram.alloc("src", DType.BF16, (32, 32), (32, 32), layout="tile")
    dst = device.dram.alloc("dst", DType.BF16, (32, 32), (32, 32), layout="tile")
    read_coord, write_coord = (endpoint_coords(device.pcie.harvested_dram_bank, x)[0] for x in range(2))
    program = lower_add1(src, dst, read_coord=read_coord, write_coord=write_coord)
    source, expected = input_and_reference()
    device.write(src, tilize(source, DType.BF16.itemsize))
    device.queue(program); device.run()
    actual = untilize(device.read(dst), DType.BF16.itemsize)
    if actual != expected:
      mismatch = next(i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
      raise AssertionError(f"add1 mismatch at byte {mismatch}: {actual[mismatch]:02x} != {expected[mismatch]:02x}")
    print("PASS add1: one 32x32 BF16 tile"); show(program)
  finally: device.close()


def main():
  parser = argparse.ArgumentParser(); parser.add_argument("--run", action="store_true")
  if parser.parse_args().run: return run_hardware()
  dram = DramAllocator()
  src = dram.alloc("src", DType.BF16, (32, 32), (32, 32), layout="tile")
  dst = dram.alloc("dst", DType.BF16, (32, 32), (32, 32), layout="tile"); show(lower_add1(src, dst))


if __name__ == "__main__": main()
