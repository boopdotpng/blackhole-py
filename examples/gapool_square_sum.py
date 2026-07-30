"""Probe direct FPU GAPOOL of one BF16 page: ``(x * x).sum()``."""

import numpy as np

from device import Device
from isa import Tensix as TT
from program import DType, Program
from ttk.cb import CB
from ttk.check import check_buffer
from ttk.sfpu import LaneConfig, LReg, SfpuFormat
from ttk.sync import Stall, Wait, stall, sync


ELEMENTS = 1024


def _select_dst(sfpu, tile):
  sfpu._configure_dst(tile, LaneConfig())
  stall(sfpu.k, Stall.SFPU, Wait.MATH)


def _fill_dst(sfpu, value):
  bits = np.float32(value).view(np.uint32).item()
  sfpu._issue(TT.TTSFPLOADI(LReg.L0, 10, bits & 0xffff))
  sfpu._issue(TT.TTSFPLOADI(LReg.L0, 8, bits >> 16))
  for _ in range(2):
    sfpu._issue(TT.TTSFPSTORE(LReg.L0, SfpuFormat.FP32, 7, 0))
    sfpu._issue(TT.TTINCRWC(0, 2, 0, 0))
  sfpu._issue(TT.TTSETRWC(0, 0, 0, 0, 0, 4))
  stall(sfpu.k, Stall.SYNC, Wait.MATH | Wait.SFPU)


def square_sum(x, output) -> Program:
  """Return a one-core program that writes ``sum(float(x) ** 2)`` to output."""
  check_buffer("x", x, dtype=DType.BF16, shape=(ELEMENTS,), core_count=1)
  check_buffer("output", output, dtype=DType.F32, shape=(4,), cores=x.cores)
  p = Program(x.cores, x, output, fp32_dst=True)
  x_cb, output_cb = p.cb(DType.BF16, depth=1), p.cb(DType.F32, depth=1)
  mul_done = p.cb.internal("gapool_mul_done", DType.BF16)
  reduce_ready = p.cb.internal("gapool_reduce_ready", DType.BF16)

  p.brisc.noc.read_into_cb(x, 0, x_cb)
  # Follow the official fused mul-reduce schedule exactly: ordinary HiFi2
  # multiply first, then explicitly reuse its FP32 Dst tile as GAPOOL SrcA.
  CB.wait_front(p.trisc0, x_cb)
  p.unpack.move_l1_pair_pair(DType.BF16, x_cb.addr, DType.BF16, x_cb.addr)
  CB.pop_front(p.trisc0, x_cb)
  CB.wait_front(p.trisc0, mul_done)
  CB.pop_front(p.trisc0, mul_done)
  p.unpack.switch_to_mul_reduce()
  sync(p.trisc0)
  CB.reserve_back(p.trisc0, reduce_ready)
  CB.push_back(p.trisc0, reduce_ready)

  p.fpu.binary("mul", dst_tile=0)
  stall(p.trisc1, Stall.SYNC, Wait.MATH | Wait.SFPU)
  CB.reserve_back(p.trisc1, mul_done)
  CB.push_back(p.trisc1, mul_done)
  CB.wait_front(p.trisc1, reduce_ready)
  CB.pop_front(p.trisc1, reduce_ready)
  p.fpu.gapool_reduce_init()
  p.fpu.move_dst_tile_to_srca(dst_tile=0)
  _select_dst(p.sfpu, 0)
  _fill_dst(p.sfpu, 1.0)
  p.fpu.move_dst_tile_to_srcb(dst_tile=0)
  _select_dst(p.sfpu, 0)
  _fill_dst(p.sfpu, 0.0)
  p.fpu.gapool_reduce_column(dst_tile=0)
  p.fpu.gapool_reduce_scalar(dst_tile=0)
  p.fpu.publish()
  p.pack.move_scalar(output_cb, tile=0)

  CB.wait_front(p.ncrisc, output_cb)
  with p.ncrisc.scope():
    source = p.ncrisc.reg()
    CB.get_read_ptr(p.ncrisc, output_cb, source)
    target, coordinate = p.ncrisc.noc._dram_tile(output, 0)
    p.ncrisc.noc.write(source, target, coordinate, 16, posted=False)
  CB.pop_front(p.ncrisc, output_cb)
  return p


def run():
  host = np.linspace(-1.0, 1.0, ELEMENTS, dtype=np.float32)
  device = Device()
  try:
    device.init_device()
    core = (device.dram.cores[0],)
    x = device.dram.buffer("gapool_x", DType.BF16, (ELEMENTS,), cores=core)
    output = device.dram.buffer("gapool_sum", DType.F32, (4,), cores=core)
    x_data = x.from_numpy(host)
    stored = x.to_numpy(x_data)
    expected = np.sum(stored * stored, dtype=np.float32)
    device.write(x, x_data)
    device.run(square_sum(x, output), timeout=30.0)
    actual = output.to_numpy(device.read(output, timeout=30.0))
    error = np.abs(actual - expected)
    print(f"expected: {float(expected):.9g}")
    print(f"output:   {actual.tolist()}")
    print(f"closest:  output[{int(error.argmin())}], abs error {float(error.min()):.9g}")
    if not np.isfinite(actual).all() or float(error.min()) > 1e-3:
      raise AssertionError("direct GAPOOL square-sum failed")
  finally:
    device.close()


if __name__ == "__main__":
  run()
