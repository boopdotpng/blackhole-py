import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asm import Cond
from program import Buffer, DType, Dram, Program
from ttk.rms import token_apply_rms_weight, token_square_accumulate
from ttk.sfpu import LReg


ROWS = 32
HIDDEN = 2048
SOURCE_TILES = HIDDEN // 32
TOKEN_TILES = HIDDEN // 1024
EPSILON = 1e-5
P100_WORKERS = tuple(
  (x, y) for x in (*range(1, 8), *range(10, 15)) for y in range(2, 12)
  if (x, y) not in ((14, 2), (14, 3))
)


def rmsnorm(x: Buffer, weight: Buffer, out: Buffer, *, cores=P100_WORKERS[:ROWS]) -> Program:
  """Run one independent 2048-element token on each worker core.

  DRAM remains in normal 32x32 matrix-tiled layout. Each BRISC gathers its
  token's row from 64 source pages into two dense local tiles; NCRISC scatters
  those two result tiles back into the same logical row.
  """
  for name, buffer in (("x", x), ("weight", weight), ("out", out)):
    if buffer.dtype is not DType.BF16: raise ValueError(f"RMSNorm {name} must be BF16")
    if buffer.shape != (ROWS, HIDDEN): raise ValueError(f"RMSNorm {name} must have shape {(ROWS, HIDDEN)}")
    if buffer.padded_shape != buffer.shape: raise ValueError(f"RMSNorm {name} must not have extra padding")
  cores = tuple(cores)
  if len(cores) != ROWS: raise ValueError(f"RMSNorm requires one core for each of its {ROWS} tokens")

  p = Program(cores, buffers=(x, weight, out))
  reduce_cb = p.cb(DType.BF16, TOKEN_TILES, name="reduce_input")
  norm_cb = p.cb(DType.BF16, TOKEN_TILES, name="norm_input")
  weight_cb = p.cb(DType.BF16, TOKEN_TILES, name="weight")
  output_cb = p.cb(DType.BF16, TOKEN_TILES, name="output")
  scale_cb = p.cb(DType.F32, 1, name="scale")
  scale_ready = p.scratch(4, name="scale_ready")
  output_pack_ready = p.scratch(4, name="output_pack_ready")
  p.initialize_scratch(scale_ready); p.initialize_scratch(output_pack_ready)

  reduce_reader, reduce_unpack = p.brisc.init_cb(reduce_cb), p.trisc0.init_cb(reduce_cb)
  norm_reader, norm_unpack = p.brisc.init_cb(norm_cb), p.trisc0.init_cb(norm_cb)
  weight_reader, weight_unpack = p.brisc.init_cb(weight_cb), p.trisc0.init_cb(weight_cb)
  output_pack, output_writer = p.trisc2.init_cb(output_cb), p.ncrisc.init_cb(output_cb)
  scale_pack = p.trisc2.init_cb(scale_cb)

  # All cores run the same image. The runtime token index selects one source
  # row and also staggers page order so workers do not march through one DRAM
  # bank in lockstep.
  token = p.brisc.arg(0)
  noc = p.brisc.noc(0).initialize_from_firmware()
  def gather(buffer, cb):
    cb.reserve_back(TOKEN_TILES)
    for step in p.brisc.range(SOURCE_TILES):
      with p.brisc.scope():
        chunk, local_page, local_row = p.brisc.reg(3, exclude=(step, token))
        p.brisc.add(chunk, step, token); p.brisc.andi(chunk, chunk, SOURCE_TILES - 1)
        p.brisc.srli(local_page, chunk, 5); p.brisc.andi(local_row, chunk, 31)
        noc.read_dram_tile_rows(
          buffer, chunk, cb, token, local_row, 1, cb_page=local_page,
        )
    cb.push_back(TOKEN_TILES)

  gather(x, reduce_reader)
  gather(x, norm_reader)
  gather(weight, weight_reader)

  p.unpack.init(reduce_unpack)
  for _ in p.trisc0.range(TOKEN_TILES):
    reduce_unpack.wait_front()
    p.unpack.wait_source_clear().wait_config_idle().configure_source(reduce_unpack).commit_config().to_src_a().wait()
    reduce_unpack.pop_front()
  for _ in p.trisc0.range(TOKEN_TILES):
    norm_unpack.wait_front()
    p.unpack.wait_source_clear().wait_config_idle().configure_source(norm_unpack).commit_config().to_src_a().wait()
    norm_unpack.pop_front()
    weight_unpack.wait_front()
    p.unpack.wait_source_clear().wait_config_idle().configure_source(weight_unpack).commit_config().to_src_a().wait()
    weight_unpack.pop_front()

  p.math.initialize()
  square = p.math.sfpu.install(token_square_accumulate())
  apply = p.math.sfpu.install(token_apply_rms_weight(weight_base=64), replay_range=(16, 32))
  p.math.acquire_dst()
  with p.math.sfpu.tile(): p.math.sfpu.load_float(LReg.L7, 0.0)
  for _ in p.trisc1.range(TOKEN_TILES):
    p.math.copy_src_a_to_dst()
    p.math.sfpu.run_tile(square)
  with p.math.sfpu.tile():
    p.math.sfpu.sum_32(LReg.L7, LReg.L0)
    p.math.sfpu.load_float(LReg.L4, 1.0 / HIDDEN)
    p.math.sfpu.multiply(LReg.L0, LReg.L4, LReg.L0)
    p.math.sfpu.load_float(LReg.L4, EPSILON)
    p.math.sfpu.add(LReg.L0, LReg.L4, LReg.L0)
    p.math.sfpu.rsqrt_positive(LReg.L0, LReg.L0, scratch=range(1, 8))
    # MOVA2D's second local tile is observed through both BF16 halves at this
    # offset, so fold the matching factor into the scalar before gamma.
    p.math.sfpu.load_float(LReg.L4, 0.5)
    p.math.sfpu.multiply(LReg.L0, LReg.L4, LReg.L0)
    p.math.sfpu.store_dst(LReg.L0, 0, format=3)
  p.math.publish_dst()
  p.trisc1.wait32(scale_ready, 1)
  p.trisc1.wait32(output_pack_ready, 1)
  p.math.acquire_dst()
  p.math.sfpu.load_float_from_l1(LReg.L0, scale_cb.addr)
  for tile in p.trisc1.range(TOKEN_TILES):
    p.math.clear_dst()
    p.math.copy_src_a_to_dst(0)
    p.math.copy_src_a_to_dst(64)
    p.math.set_destination_offset(0)
    p.math.sfpu.run_tile(apply)
    p.math.publish_dst()
    with p.trisc1.if_(Cond(tile, "!=", TOKEN_TILES - 1)): p.math.acquire_dst()

  p.pack.init(scale_pack, fp32_dest=True)
  p.pack.acquire_dst(); scale_pack.reserve_back(); p.pack.to_cb()
  scale_pack.push_back(); p.pack.release_dst()
  p.trisc2.write32(scale_ready, 1); p.trisc2.fence()
  p.pack.init(output_pack)
  p.trisc2.write32(output_pack_ready, 1); p.trisc2.fence()
  for _ in p.trisc2.range(TOKEN_TILES):
    p.pack.acquire_dst(); output_pack.reserve_back(); p.pack.to_cb()
    output_pack.push_back(); p.pack.release_dst()

  token = p.ncrisc.arg(0)
  noc = p.ncrisc.noc(1).initialize_from_firmware()
  output_writer.wait_front(TOKEN_TILES)
  for step in p.ncrisc.range(SOURCE_TILES):
    with p.ncrisc.scope():
      chunk, local_page, local_row = p.ncrisc.reg(3, exclude=(step, token))
      p.ncrisc.add(chunk, step, token); p.ncrisc.andi(chunk, chunk, SOURCE_TILES - 1)
      p.ncrisc.srli(local_page, chunk, 5); p.ncrisc.andi(local_row, chunk, 31)
      noc.write_dram_tile_rows(
        out, chunk, output_writer, token, 1,
        source_row=local_row, cb_page=local_page,
      )
  output_writer.pop_front(TOKEN_TILES)

  p.set_runtime_args({core: (index,) for index, core in enumerate(cores)})
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
    program = rmsnorm(x, weight, out, cores=device.pcie.cores[:ROWS])
    values = rng.normal(0, 0.25, shape).astype(np.float32)
    gamma = rng.normal(1, 0.1, HIDDEN).astype(np.float32)
    tiled_gamma = np.broadcast_to(gamma, shape).copy()
    x_data, weight_data = x.from_numpy(values), weight.from_numpy(tiled_gamma)
    xf, wf = x.to_numpy(x_data), weight.to_numpy(weight_data)
    squares = xf.copy(); np.square(squares, out=squares)
    scale = np.sum(squares, axis=1, dtype=np.float32) / np.float32(HIDDEN)
    scale = np.reciprocal(np.sqrt(scale + np.float32(EPSILON), dtype=np.float32), dtype=np.float32)
    expected = out.to_numpy(out.from_numpy(xf * scale[:, None] * wf))
    device.write(x, x_data); device.write(weight, weight_data)
    timings = device.run(program)
    actual = out.to_numpy(device.read(out))
    error = np.abs(actual - expected)
    if not np.isfinite(actual).all() or float(error.max()) > 0.05:
      row, col = np.unravel_index(int(error.argmax()), error.shape)
      raise AssertionError(
        f"RMSNorm mismatch at ({row}, {col}): actual={actual[row, col]} "
        f"expected={expected[row, col]} max_abs={error.max()}"
      )
    samples = [timings[-1].us]
    for _ in range(repeats - 1): samples.append(device.run(program)[0].us)
    print(f"PASS rmsnorm: cores={len(program.cores)} max_abs={error.max():.6g} mean_abs={error.mean():.6g}")
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
  print(f"cores: {len(program.cores)}"); print(f"CBs: {program.cbs}")
  for role, image in program.kernels[program.cores[0]].items(): print(f"{role:7s}: {len(image):4d} bytes")


if __name__ == "__main__": main()
