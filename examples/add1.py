import argparse, struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import KernelBuilder
from program import Buffer, DType, Dram, KernelBundle, Param, Program
from ttk.cb import CB
from ttk.sfpu import SfpuFormat
from ttk.sync import Barrier

CORE, TILE_BYTES = (1, 2), 2048
INPUT_CB_ADDR = 0x37000
OUTPUT_CB_ADDR = INPUT_CB_ADDR + TILE_BYTES
INIT_BARRIER_ADDR = 0x36F10

def lower_add1(src: Buffer, dst: Buffer, *, core=CORE, read_coord=0, write_coord=0) -> Program:
  src_param, dst_param = Param("src", src), Param("dst", dst)

  def build(k: KernelBuilder):
    input_reader_cb, input_unpack_cb = CB(k.brisc, input_cb_config), CB(k.trisc0, input_cb_config)
    output_pack_cb, output_writer_cb = CB(k.trisc2, output_cb_config), CB(k.ncrisc, output_cb_config)
    k.unpack.init(input_unpack_cb)
    k.math.initialize()
    add_one = k.math.sfpu.install(k.math.sfpu.add_immediate_program(1, format=SfpuFormat.BF16))
    k.pack.init(output_pack_cb)
    Barrier(k.trisc0, init_barrier, 0).wait()
    Barrier(k.trisc1, init_barrier, 1).wait()
    Barrier(k.trisc2, init_barrier, 2).wait()

    input_reader_cb.reserve_back()
    noc = k.brisc.noc(0).initialize_from_firmware()
    write_ptr = k.brisc.reg(); input_reader_cb.write_ptr(write_ptr)
    with noc.read_batch() as reads:
      reads.issue(k.brisc.param(src_param), read_coord, write_ptr, TILE_BYTES)
    input_reader_cb.push_back()

    input_unpack_cb.wait_front()
    k.unpack.to_src_a()
    k.unpack.wait()
    input_unpack_cb.pop_front()

    k.math.copy_src_a_to_dst()
    k.math.sfpu.run_tile(add_one)
    k.math.publish_dst()

    k.pack.acquire_dst()
    output_pack_cb.reserve_back()
    k.pack.to_cb()
    output_pack_cb.push_back()

    output_writer_cb.wait_front()
    noc = k.ncrisc.noc(1).initialize_from_firmware()
    read_ptr = k.ncrisc.reg(); output_writer_cb.read_ptr(read_ptr)
    with noc.write_ack_batch() as writes:
      writes.issue(read_ptr, k.ncrisc.param(dst_param), write_coord, TILE_BYTES)
    output_writer_cb.pop_front()

  bundle = KernelBundle((core,), params=(src_param, dst_param))
  input_cb_config = bundle.cb(DType.BF16, 1, INPUT_CB_ADDR)
  output_cb_config = bundle.cb(DType.BF16, 1, OUTPUT_CB_ADDR)
  init_barrier = bundle.barrier(3, INIT_BARRIER_ADDR)
  return bundle.lower(build)

def _bf16(value): return struct.unpack("<I", struct.pack("<f", float(value)))[0] >> 16
def _fp32(value): return struct.unpack("<f", struct.pack("<I", value << 16))[0]

def input_and_reference():
  source_words = tuple(_bf16((x % 257 - 128) / 8) for x in range(1024))
  result_words = tuple(_bf16(_fp32(x) + 1) for x in source_words)
  encode = lambda words: struct.pack(f"<{len(words)}H", *words)
  return encode(source_words), encode(result_words)

def show(program: Program):
  print(f"cores: {program.cores}"); print(f"CBs:   {program.cbs}")
  print(f"params: {[(param.name, hex(program.param_addr(param)), hex(param.initial.addr)) for param in program.params.values()]}")
  for core in program.cores:
    for role, image in program.kernels[core].items(): print(f"{core} {role:7s}: {len(image):4d} bytes")

def run_hardware():
  from device import Device
  from ttk.dram import endpoint_coords

  device = Device()
  try:
    device.init_device()
    src = device.dram.buffer("src", DType.BF16, (32, 32), (32, 32))
    dst = device.dram.buffer("dst", DType.BF16, (32, 32), (32, 32))
    read_coord, write_coord = (endpoint_coords(device.pcie.harvested_dram_bank, x)[0] for x in range(2))
    program = lower_add1(src, dst, read_coord=read_coord, write_coord=write_coord)
    source, expected = input_and_reference()
    device.write(src, source)
    device.run(program)
    actual = device.read(dst)
    if actual != expected:
      mismatch = next(i for i, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
      raise AssertionError(f"add1 mismatch at byte {mismatch}: {actual[mismatch]:02x} != {expected[mismatch]:02x}")
    print("PASS add1: one 32x32 BF16 tile"); show(program)
  finally: device.close()

def main():
  parser = argparse.ArgumentParser(); parser.add_argument("--run", action="store_true")
  if parser.parse_args().run: return run_hardware()
  dram = Dram()
  src = dram.buffer("src", DType.BF16, (32, 32), (32, 32))
  dst = dram.buffer("dst", DType.BF16, (32, 32), (32, 32)); show(lower_add1(src, dst))

if __name__ == "__main__": main()
