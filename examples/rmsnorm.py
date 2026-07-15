import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Cond
from program import Buffer, DType, Dram, Program
from ttk.rms import apply_rms, finalize_rms, row_square_sum
from ttk.sync import RiscBarrier


ROWS = 32
HIDDEN = 2048
TILES = HIDDEN // 32
EPSILON = 1e-5
READ_BATCH = 8


def rmsnorm(x: Buffer, weight: Buffer, out: Buffer, *, core=(1, 2)) -> Program:
  for name, buffer in (("x", x), ("weight", weight), ("out", out)):
    if buffer.dtype is not DType.BF16: raise ValueError(f"RMSNorm {name} must be BF16")
    if buffer.shape != (ROWS, HIDDEN): raise ValueError(f"RMSNorm {name} must have shape {(ROWS, HIDDEN)}")
    if buffer.padded_shape != buffer.shape: raise ValueError(f"RMSNorm {name} must not have extra padding")
  p = Program((core,), buffers=(x, weight, out))
  reduce_cb = p.cb(DType.BF16, 8, name="reduce_input")
  norm_input_cb = p.cb(DType.BF16, 8, name="norm_input")
  weight_cb = p.cb(DType.BF16, TILES, name="weight")
  norm_cb = p.cb(DType.BF16, TILES, name="normalized")
  out_cb = p.cb(DType.BF16, 2, name="out")
  barrier = RiscBarrier(p.l1(2 * 3 * 4, name="phase_barrier"), 3)
  p.launch = (barrier.reset(p.cores, phases=2),)

  reduce_reader, reduce_unpack = p.brisc.init_cb(reduce_cb), p.trisc0.init_cb(reduce_cb)
  norm_reader, norm_input_unpack = p.brisc.init_cb(norm_input_cb), p.trisc0.init_cb(norm_input_cb)
  weight_reader, weight_unpack = p.brisc.init_cb(weight_cb), p.trisc0.init_cb(weight_cb)
  norm_pack, norm_unpack = p.trisc2.init_cb(norm_cb), p.trisc0.init_cb(norm_cb)
  out_pack, out_writer = p.trisc2.init_cb(out_cb), p.ncrisc.init_cb(out_cb)
  reduce_first = row_square_sum(accumulate=False)
  reduce_more = row_square_sum(accumulate=True)
  finish = finalize_rms(width=HIDDEN, epsilon=EPSILON)
  apply = apply_rms()

  noc = p.brisc.noc(0).initialize_from_firmware()
  def read_tiles(buffer, cb, reads):
    for block in p.brisc.range(TILES // READ_BATCH):
      cb.reserve_back(READ_BATCH)
      with reads.batch(READ_BATCH):
        for lane in p.brisc.range(READ_BATCH):
          with p.brisc.scope():
            tile = p.brisc.reg(exclude=(block, lane))
            p.brisc.slli(tile, block, 3); p.brisc.add(tile, tile, lane)
            src, src_coord = noc.dram_page(buffer, tile)
            dst = p.brisc.reg(); cb.write_ptr(dst, lane)
            reads.issue(src, src_coord, dst)
      cb.push_back(READ_BATCH)

  with noc.read_stream(x.page_size) as reads:
    read_tiles(x, reduce_reader, reads)
    read_tiles(x, norm_reader, reads)
    read_tiles(weight, weight_reader, reads)

  # Materialize normalized BF16 tiles before changing the Tensix pipeline to
  # the final HiFi2 row-broadcast multiply. Reduction and rsqrt stay FP32.
  p.unpack.init(reduce_unpack)
  for cb in (reduce_unpack, norm_input_unpack):
    for _ in p.trisc0.range(TILES):
      cb.wait_front()
      p.unpack.wait_source_clear().wait_config_idle().configure_source(cb).commit_config().to_src_a().wait()
      cb.pop_front()
  p.unpack.wait_source_clear()
  barrier.arrive(p.trisc0, 0, 1)
  p.unpack.init_row_broadcast(norm_unpack, weight_unpack)
  barrier.arrive(p.trisc0, 0, 2)
  for _ in p.trisc0.range(TILES):
    norm_unpack.wait_front(); weight_unpack.wait_front()
    p.unpack.wait_config_idle().configure_row_broadcast(norm_unpack, weight_unpack).commit_config().row_broadcast().wait_both()
    norm_unpack.pop_front(); weight_unpack.pop_front()

  p.math.initialize()
  p.math.acquire_dst()
  p.math.copy_src_a_to_dst(); p.math.sfpu.run(reduce_first)
  for _ in p.trisc1.range(TILES - 1):
    p.math.copy_src_a_to_dst(); p.math.sfpu.run(reduce_more)
  p.math.set_destination_offset(0); p.math.sfpu.run(finish)
  for tile in p.trisc1.range(TILES):
    p.math.copy_src_a_to_dst(0)
    p.math.set_destination_offset(0); p.math.sfpu.run(apply)
    p.math.publish_dst()
    with p.trisc1.if_(Cond(tile, "!=", TILES - 1)): p.math.acquire_dst()
  p.math.acquire_dst(); barrier.arrive(p.trisc1, 1, 1)
  p.math.configure_row_broadcast_mul_hifi2(); barrier.arrive(p.trisc1, 1, 2)
  for tile in p.trisc1.range(TILES):
    p.math.row_broadcast_mul_hifi2(); p.math.publish_dst()
    with p.trisc1.if_(Cond(tile, "!=", TILES - 1)): p.math.acquire_dst()

  p.pack.init(norm_pack)
  for _ in p.trisc2.range(TILES):
    p.pack.acquire_dst(); norm_pack.reserve_back(); p.pack.to_cb()
    norm_pack.push_back(); p.pack.release_dst()
  barrier.arrive(p.trisc2, 2, 1)
  p.pack.init(out_pack)
  barrier.arrive(p.trisc2, 2, 2)
  for _ in p.trisc2.range(TILES):
    p.pack.acquire_dst(); out_pack.reserve_back(); p.pack.to_cb()
    out_pack.push_back(); p.pack.release_dst()

  noc = p.ncrisc.noc(1).initialize_from_firmware()
  for tile in p.ncrisc.range(TILES):
    out_writer.wait_front()
    with noc.write_ack_batch() as writes: writes.issue_dram(out, tile, out_writer)
    out_writer.pop_front()
  return p


def run_hardware(repeats=20):
  import numpy as np
  from device import Device

  rng = np.random.default_rng(0)
  device = Device()
  try:
    device.init_device()
    shape = (ROWS, HIDDEN)
    x = device.dram.buffer("x", DType.BF16, shape, shape)
    weight = device.dram.buffer("weight", DType.BF16, shape, shape)
    out = device.dram.buffer("out", DType.BF16, shape, shape)
    program = rmsnorm(x, weight, out)
    values = rng.normal(0, 0.25, shape).astype(np.float32)
    gamma = rng.normal(1, 0.1, HIDDEN).astype(np.float32)
    tiled_gamma = np.broadcast_to(gamma, shape).copy()
    x_data, weight_data = x.from_numpy(values), weight.from_numpy(tiled_gamma)
    xf, wf = x.to_numpy(x_data), weight.to_numpy(weight_data)
    squares = xf.copy(); np.square(squares, out=squares)
    scale = np.sum(squares, axis=1, dtype=np.float32) / np.float32(HIDDEN)
    scale = np.reciprocal(np.sqrt(scale + np.float32(EPSILON), dtype=np.float32), dtype=np.float32)
    normalized = out.to_numpy(out.from_numpy(xf * scale[:, None]))
    expected = out.to_numpy(out.from_numpy(normalized * wf))
    device.write(x, x_data); device.write(weight, weight_data)
    timings = device.run(program)
    actual = out.to_numpy(device.read(out))
    error = np.abs(actual - expected)
    if not np.isfinite(actual).all() or float(error.max()) > 0.05:
      row, col = np.unravel_index(int(error.argmax()), error.shape)
      raise AssertionError(f"RMSNorm mismatch at ({row}, {col}): actual={actual[row, col]} expected={expected[row, col]} max_abs={error.max()}")
    samples = [timings[-1].us]
    for _ in range(repeats - 1): samples.append(device.run(program)[0].us)
    print(f"PASS rmsnorm: max_abs={error.max():.6g} mean_abs={error.mean():.6g}")
    print(f"latency_us min={min(samples):.3f} median={float(np.median(samples)):.3f} samples={samples}")
  finally: device.close()


def main():
  parser = argparse.ArgumentParser(); parser.add_argument("--run", action="store_true"); parser.add_argument("--repeats", type=int, default=20)
  args = parser.parse_args()
  if args.repeats <= 0: parser.error("--repeats must be positive")
  if args.run: return run_hardware(args.repeats)
  dram = Dram(); shape = (ROWS, HIDDEN)
  buffers = tuple(dram.buffer(name, DType.BF16, shape, shape) for name in ("x", "weight", "out"))
  program = rmsnorm(*buffers)
  print(f"cores: {program.cores}"); print(f"CBs: {program.cbs}")
  for role, image in program.kernels[program.cores[0]].items(): print(f"{role:7s}: {len(image):4d} bytes")


if __name__ == "__main__": main()
