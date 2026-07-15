import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from program import Buffer, DType, Dram, Program
from ttk.matmul import Matmul, TILE, plan_matmul, plan_output_chunks


P100_CORES = tuple(
  (x, y)
  for x in (*range(1, 8), *range(10, 15))
  for y in range(2, 12)
  if (x, y) not in ((14, 2), (14, 3))
)


def matmul(a: Buffer, b: Buffer, output: Buffer, cores=P100_CORES, *,
           plan=None, m_tile_offset=0, n_tile_offset=0, hifi=False) -> Program:
  if any(buffer.dtype is not DType.BF16 for buffer in (a, b, output)):
    raise ValueError("matmul requires BF16 buffers")
  if len(a.shape) != 2 or len(b.shape) != 2 or len(output.shape) != 2:
    raise ValueError("matmul requires rank-2 buffers")
  m, k = a.shape; bk, n = b.shape
  if k != bk:
    raise ValueError(f"incompatible matmul inputs: {a.shape} @ {b.shape}")

  plan = plan or plan_matmul(m, k, n, cores)
  if m_tile_offset * TILE + output.shape[0] > m or n_tile_offset * TILE + output.shape[1] > n:
    raise ValueError("matmul output chunk lies outside its inputs")
  if a.padded_shape[1] != plan.kt * TILE or b.padded_shape[0] != plan.kt * TILE:
    raise ValueError(f"matmul requires K padded to {plan.kt * TILE}")
  if output.padded_shape != (plan.mt * TILE, plan.nt * TILE):
    raise ValueError(f"matmul output requires padded shape {(plan.mt * TILE, plan.nt * TILE)}")

  p = Program(plan.cores, buffers=(a, b, output))
  a_cb = p.cb(DType.BF16, 2 * plan.a_block_pages, name="A")
  b_cb = p.cb(DType.BF16, 2 * plan.b_block_pages, name="B")
  output_cb = p.cb(DType.BF16, plan.output_tiles, name="output")
  kernel = Matmul(
    p, plan, a, b, output, a_cb, b_cb, output_cb,
    m_tile_offset=m_tile_offset, n_tile_offset=n_tile_offset, hifi=hifi,
  )

  kernel.read_a()
  kernel.read_b_and_write_output()
  kernel.unpack()
  kernel.multiply()
  kernel.pack()
  p.set_runtime_args(kernel.runtime_args())
  return p


def show(program: Program):
  print(f"cores: {len(program.cores)}")
  print(f"CBs:   {program.cbs}")
  for role, image in program.kernels[program.cores[0]].items():
    print(f"{role:7s}: {len(image):4d} bytes")


def _quality(actual, expected):
  import numpy as np
  actual = actual.astype(np.float32, copy=False).reshape(-1)
  expected = expected.astype(np.float32, copy=False).reshape(-1)
  rel_l2 = float(np.linalg.norm(actual - expected) / (np.linalg.norm(expected) + 1e-12))
  pcc = float(np.corrcoef(actual, expected)[0, 1]) if np.std(expected) else 1.0
  return pcc, rel_l2


def run_hardware(m=384, n=384, k=384, *, runs=5, hifi=False):
  import numpy as np
  from device import Device

  device = Device()
  try:
    device.init_device()
    chunks = plan_output_chunks(m, k, n, device.pcie.cores)
    kp = chunks[0].plan.kt * TILE
    mp, npad = ((value + TILE - 1) // TILE * TILE for value in (m, n))
    a = device.dram.buffer("A", DType.BF16, (m, k), (mp, kp))
    b = device.dram.buffer("B", DType.BF16, (k, n), (kp, npad))
    outputs, programs = [], []
    for index, chunk in enumerate(chunks):
      output = device.dram.buffer(
        f"output{index}", DType.BF16, (chunk.m, chunk.n),
        (chunk.plan.mt * TILE, chunk.plan.nt * TILE),
      )
      outputs.append(output)
      programs.append(matmul(
        a, b, output, device.pcie.cores, plan=chunk.plan,
        m_tile_offset=chunk.m0 // TILE, n_tile_offset=chunk.n0 // TILE, hifi=hifi,
      ))

    rng = np.random.default_rng(0)
    a_values = rng.uniform(-0.25, 0.25, size=(m, k)).astype(np.float32)
    b_values = rng.uniform(-0.25, 0.25, size=(k, n)).astype(np.float32)
    a_bytes, b_bytes = a.from_numpy(a_values), b.from_numpy(b_values)
    a_reference, b_reference = a.to_numpy(a_bytes), b.to_numpy(b_bytes)
    device.write(a, a_bytes); device.write(b, b_bytes)

    timings = []
    for _ in range(runs):
      results = device.run(programs)
      timings.append(sum(result.us for result in results[-len(programs):]))
    actual = np.empty((m, n), dtype=np.float32)
    for chunk, output in zip(chunks, outputs):
      actual[chunk.m0:chunk.m0 + chunk.m, chunk.n0:chunk.n0 + chunk.n] = output.to_numpy(device.read(output))
    if m * n * k <= 1_000_000_000:
      pcc, rel_l2 = _quality(actual, a_reference @ b_reference)
    else:
      sample_rng = np.random.default_rng(1)
      rows = sample_rng.integers(0, m, size=64); cols = sample_rng.integers(0, n, size=64)
      expected = np.array([a_reference[row] @ b_reference[:, col] for row, col in zip(rows, cols)])
      pcc, rel_l2 = _quality(actual[rows, cols], expected)
    average = sum(timings) / len(timings)
    tflops = 2.0 * m * k * n / (average * 1.0e6)
    if not np.all(np.isfinite(actual)) or pcc < 0.995 or rel_l2 > 0.10:
      if k <= 1024:
        width = chunks[0].plan.block_w * TILE
        for start in range(0, kp, width):
          end = min(start + width, k)
          if start < end:
            spcc, sl2 = _quality(actual, a_reference[:, start:end] @ b_reference[start:end])
            print(f"  diagnostic K[{start}:{end}]: PCC={spcc:.6f}, rel_l2={sl2:.6f}")
        for label, sliced in (
          ("first", a_reference[:, :min(width, k)] @ b_reference[:min(width, k)]),
          ("last", a_reference[:, max(0, k - width):k] @ b_reference[max(0, k - width):k]),
        ):
          for tm in range((m + 31) // 32):
            for tn in range((n + 31) // 32):
              tile = np.s_[tm * 32:min((tm + 1) * 32, m), tn * 32:min((tn + 1) * 32, n)]
              tpcc, tl2 = _quality(actual[tile], sliced[tile])
              print(f"  diagnostic {label} tile[{tm},{tn}]: PCC={tpcc:.6f}, rel_l2={tl2:.6f}")
      raise AssertionError(
        f"matmul validation failed: {average:.2f} us, {tflops:.2f} TFLOP/s, "
        f"PCC={pcc:.6f}, rel_l2={rel_l2:.6f}"
      )

    print("PASS matmul_peak")
    print(f"  shape: {m}x{k}x{n} (inputs padded {mp}x{kp}x{npad})")
    print(f"  chunks: {len(chunks)}; cores/chunk: {[len(program.cores) for program in programs]}")
    print(f"  fidelity: {'HiFi2' if hifi else 'LoFi'}")
    print(f"  kernel_avg: {average:,.2f} us over {runs} runs")
    print(f"  throughput: {tflops:.2f} TFLOP/s")
    print(f"  validation: PCC={pcc:.6f}, rel_l2={rel_l2:.6f}")
  finally:
    device.close()


def main():
  parser = argparse.ArgumentParser(description="Readable peak BF16 matmul for Blackhole")
  parser.add_argument("M", type=int, nargs="?", default=384)
  parser.add_argument("N", type=int, nargs="?", default=384)
  parser.add_argument("K", type=int, nargs="?", default=384)
  parser.add_argument("--run", action="store_true", help="run and validate on hardware")
  parser.add_argument("--runs", type=int, default=5)
  parser.add_argument("--hifi", action="store_true", help="use two math fidelity phases")
  args = parser.parse_args()
  if min(args.M, args.N, args.K, args.runs) <= 0: parser.error("dimensions and --runs must be positive")
  if args.run: return run_hardware(args.M, args.N, args.K, runs=args.runs, hifi=args.hifi)

  chunks = plan_output_chunks(args.M, args.K, args.N, P100_CORES)
  if len(chunks) != 1:
    print(f"shape requires {len(chunks)} independently scheduled output chunks")
    for index, chunk in enumerate(chunks):
      print(f"  {index}: origin=({chunk.m0},{chunk.n0}) shape={chunk.m}x{chunk.n} cores={len(chunk.plan.cores)}")
    return
  plan = chunks[0].plan
  mp, kp, npad = plan.mt * TILE, plan.kt * TILE, plan.nt * TILE
  dram = Dram()
  a = dram.buffer("A", DType.BF16, (args.M, args.K), (mp, kp))
  b = dram.buffer("B", DType.BF16, (args.K, args.N), (kp, npad))
  output = dram.buffer("output", DType.BF16, (args.M, args.N), (mp, npad))
  show(matmul(a, b, output, hifi=args.hifi))


if __name__ == "__main__": main()
