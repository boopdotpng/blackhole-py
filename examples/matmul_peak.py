"""Multicast BF16 HiFi2 / FP8 matmul with 8x16 edge arithmetic."""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from cq import McastWrite, Run, rectangles
from device import Device
from program import GridProgram
from pcie import P100_WORKER_CORES, P100_DRAM_ENDPOINTS, TLBWindow
from examples.matmul_peak_kernel import kernel as k, asm


def fp8_decode(codes):
  codes = np.asarray(codes, dtype=np.uint8)
  exponent = (codes >> 3) & 15
  mantissa = codes & 7
  magnitude = np.where(exponent == 0, mantissa * 2.**-9,
                       (1 + mantissa / 8) * np.exp2(exponent.astype(np.int32) - 7))
  magnitude = np.where((codes & 127) == 127, np.nan, magnitude)
  return np.where(codes & 128, -magnitude, magnitude).astype(np.float32)


def fp8_encode(values):
  """E4M3FN RNE, saturating at 448; subnormal results flush to signed zero."""
  values = np.asarray(values, dtype=np.float32)
  if not np.all(np.isfinite(values)):
    raise ValueError('FP8 input must be finite')
  levels = fp8_decode(np.arange(127, dtype=np.uint8))
  magnitude = np.abs(values)
  hi = np.minimum(np.searchsorted(levels, magnitude), 126)
  lo = np.maximum(hi - 1, 0)
  down, up = magnitude - levels[lo], levels[hi] - magnitude
  codes = np.where((down < up) | ((down == up) & ((lo & 1) == 0)), lo, hi)
  # The hardware tests document nonstandard E4M3 subnormal expansion.
  # Flush these encodings explicitly so the reference and device agree.
  codes = np.where(codes < 8, 0, codes)
  return (codes | (np.signbit(values).astype(np.uint8) << 7)).astype(np.uint8)


def tile_bytes(values, dtype="bf16"):
  """Row-major float32 -> BF16 or FP8 storage tiles with four 16x16 faces."""
  m, n = values.shape
  words = (fp8_encode(values) if dtype == 'fp8' else
           (np.ascontiguousarray(values, dtype=np.float32).view(np.uint32) >> 16).astype('<u2'))
  return words.reshape(m//32, 2, 16, n//32, 2, 16).transpose(0, 3, 1, 4, 2, 5).tobytes()


def matrix_bytes(data, m, n):
  """Physical 16-bit tiles -> row-major 16-bit bytes (BF16 or FP16)."""
  words = np.frombuffer(data, dtype='<u2').reshape(m//32, n//32, 2, 2, 16, 16)
  return words.transpose(0, 2, 4, 1, 3, 5).copy().tobytes()


def build(plan, endpoints, a=0, b=0, c=0, *, output_noc="split"):
  cb_configs = []
  address = k.CB_STORAGE_BASE
  for index, pages in ((0, plan.cb0_pages), (1, plan.cb1_pages),
                       (16, plan.cb16_pages), (24, plan.cb24_pages)):
    # Final output and accumulated partials intentionally share storage.
    if index == 24:
      cb_address = cb_configs[-1][1]
    else:
      cb_address = address
      address += pages * (k.INPUT_TILE_BYTES if index < 2 else 2048)
    cb_configs.append((index, cb_address, pages * (k.INPUT_TILE_BYTES if index < 2 else 2048), pages))
  if address > k.DEBUG_NCRISC_OUTPUT:
    raise ValueError('matmul buffers overlap diagnostics')
  asm.CONTEXT = {'cbs': cb_configs, 'endpoints': endpoints, 'address': 0x12000, 'fp8': k.INPUT_DTYPE == k.DType.FP8}
  sources = {}
  constructors = (
    ('brisc', lambda: k.matmul_reader(plan)),
    ('ncrisc', lambda: k.matmul_writer(plan)),
    *((f'trisc{i}', lambda i=i: getattr(k, f'matmul_trisc{i}')(plan)) for i in range(3)),
  )
  for name, constructor in constructors:
    kernel = constructor()
    image = kernel.lower()
    sources[name] = (kernel.base, image)
    asm.CONTEXT['address'] = (kernel.base + len(image) + 63) & -64
  if asm.CONTEXT['address'] > asm.ARG_BASE:
    raise ValueError('matmul code overlaps argument tables')
  if output_noc not in ('split', '0', '1'):
    raise ValueError('unsupported output NoC')
  program = GridProgram(sources, rows=plan.rows, cols=plan.cols)
  topology = struct.pack('<128I', *(plan.rows + (0,)*(64-len(plan.rows)) + plan.cols + (0,)*(64-len(plan.cols))))
  commands = program.commands(params=(a, b, c, len(endpoints), 2 if output_noc == 'split' else int(output_noc)),
                              l1={asm.GRID_BASE: topology, asm.SEM_BASE: bytes(128)})
  return program, commands, sources


def read_profile(window, cores):
  starts, ends = [], []
  durations = {name: [] for name, _ in k.PROFILE_NAMES}
  for core in cores:
    window.target(0, core)
    starts.append(struct.unpack('<Q', window.read(k.PROFILE_BRISC, 8))[0])
    ends.append(struct.unpack('<Q', window.read(k.PROFILE_NCRISC + 8, 8))[0])
    for name, address in k.PROFILE_NAMES:
      begin, end = struct.unpack('<QQ', window.read(address, 16))
      durations[name].append((end - begin) / 1350)
      if name.startswith('trisc'):
        csr = int.from_bytes(window.read(address + 16, 4), 'little')
        if csr & (1 << 18):
          raise AssertionError(f'instruction fusion disabled on {core}/{name}')
  return (max(ends) - min(starts)) / 1350, {name: max(values) for name, values in durations.items()}


def dump_timeout(device, cores):
  with TLBWindow(device.pcie.fd, cores[0]) as window:
    for core in cores[:4]:
      window.target(0, core)
      for address, size in ((0x68, 4), (0x370, 4), (asm.SEM_BASE, 64),
                            (k.SYNC_TRISC_START, 32), (k.DEBUG_TRISC0, 144)):
        words = struct.unpack('<' + 'I'*(size//4), window.read(address, size))
        print(core, hex(address), [hex(v) for v in words], flush=True)


def run(m, n, inner, *, runs=5, device_index=0, execute=False, profile=False, dtype='bf16', writer_wave_rows=0, block_k=0, subblock=(2,4), output_noc="split"):
  if min(m, n, inner, runs) <= 0:
    raise ValueError('dimensions and runs must be positive')
  if dtype not in ('bf16', 'fp8') or output_noc not in ('0', '1', 'split'):
    raise ValueError('unsupported dtype or output NoC')
  h, w = subblock
  if h not in (1, 2) or w not in (1, 2, 4, 8) or h > w or h*w > 8:
    raise ValueError('subblock must have H <= W and at most 8 tiles, H in (1, 2)')
  if block_k < 0 or writer_wave_rows < 0:
    raise ValueError('block-k and writer-wave-rows must be nonnegative')
  k.WRITER_WAVE_ROWS = writer_wave_rows
  k.SUPPORTED_IN0_BLOCK_WS = (block_k,) if block_k else tuple(range(1, 11 if dtype == 'fp8' else 7))
  k.SUPPORTED_OUT_SUBBLOCK_H, k.SUPPORTED_OUT_SUBBLOCK_W = subblock
  k.INPUT_DTYPE = k.DType.FP8 if dtype == 'fp8' else k.DType.BF16
  k.INPUT_TILE_BYTES = k.INPUT_DTYPE.tile_size
  k.OUTPUT_DTYPE = k.DType.F16 if dtype == "fp8" else k.DType.BF16
  device = Device(device_index) if execute else None
  program = None
  try:
    if device:
      device.boot()
    cores = device.cores if device else P100_WORKER_CORES
    endpoints = device.pcie.dram_endpoints if device else P100_DRAM_ENDPOINTS
    plan = k.plan_matmul(m, inner, n, list(cores))
    mp, kp, npad = plan.mt*32, plan.kt*32, plan.nt*32
    print(f'{dtype.upper()} {m}x{inner}x{n}; compute padding {plan.m_extent*len(plan.rows)}x{plan.k_extent}x{plan.n_extent*len(plan.cols)}; '
          f'{len(plan.rows)}x{len(plan.cols)} cores, {plan.out_subblock_h}x{plan.out_subblock_w} output subblocks, K block {plan.in0_block_w}', flush=True)
    if not device:
      program, _, sources = build(plan, endpoints, output_noc=output_noc)
      print('Kernel bytes:', {name: len(image) for name, (_, image) in sources.items()})
      print(f'grid {program.global_size}, {len(sources)} shared controller images, {len(program.binary)} bundle bytes, output NoC {output_noc}')
      return
    a_ref, b_ref = k.make_inputs(m, inner, n)
    if dtype == 'fp8':
      a_ref, b_ref = (fp8_decode(fp8_encode(values)) for values in (a_ref, b_ref))
    buffers = []
    for operand, (values, shape) in enumerate(((a_ref, (mp, kp)), (b_ref, (kp, npad)))):
      padded = np.zeros(shape, dtype=np.float32)
      if operand == 0:
        for i in range(len(plan.rows)):
          start = i * plan.m_extent
          count = min(plan.m_extent, max(0, m - start))
          padded[i*plan.per_core_m*32:i*plan.per_core_m*32+count, :inner] = values[start:start+count]
      else:
        for i in range(len(plan.cols)):
          start = i * plan.n_extent
          count = min(plan.n_extent, max(0, n - start))
          padded[:inner, i*plan.per_core_n*32:i*plan.per_core_n*32+count] = values[:, start:start+count]
      buffer = device.alloc_interleaved_dram(padded.size * (1 if dtype == "fp8" else 2), page_size=k.INPUT_TILE_BYTES)
      device.write_dram(buffer, tile_bytes(padded, dtype))
      buffers.append(buffer)
    output = device.alloc_interleaved_dram(mp*npad*2, page_size=2048)
    program, commands, _ = build(plan, endpoints, buffers[0].address, buffers[1].address, output.address, output_noc=output_noc)
    device.cq.submit(commands, timeout=10)  # Upload and warm up.
    timings = []
    with TLBWindow(device.pcie.fd, program.cores[0]) as window:
      for _ in range(runs):
        device.cq.submit((McastWrite(rectangles(program.cores), asm.SEM_BASE, bytes(128)),
                          Run(program.cores)), timeout=10)
        elapsed, durations = read_profile(window, program.cores)
        timings.append(elapsed)
    raw = device.read_dram(output)
    physical = np.frombuffer(matrix_bytes(raw, mp, npad), dtype='<u2').reshape(mp,npad)
    dense = np.empty((m,n),dtype='<u2')
    for i in range(len(plan.rows)):
      r = i*plan.m_extent
      h = min(plan.m_extent,max(0,m-r))
      for j in range(len(plan.cols)):
        c = j*plan.n_extent
        w = min(plan.n_extent,max(0,n-c))
        dense[r:r+h,c:c+w] = physical[i*plan.per_core_m*32:i*plan.per_core_m*32+h,
                                      j*plan.per_core_n*32:j*plan.per_core_n*32+w]
    pcc, error = k.validate(a_ref, b_ref, dense.tobytes(), m, n, m, n)
    average = sum(timings)/len(timings)
    print(f'PASS: PCC={pcc:.6f}, rel_l2={error:.6f}; fusion enabled on every TRISC')
    print(f'{runs} runs: mean {average:.2f} us, min {min(timings):.2f}, max {max(timings):.2f}')
    print(f'Logical {k.tflops(m, n, inner, average):.2f} TFLOP/s; '
          f'padded {k.tflops(plan.m_extent*len(plan.rows), plan.n_extent*len(plan.cols), plan.k_extent, average):.2f} TFLOP/s')
    if profile:
      print('Last run, maximum duration per role (us):', {name: round(value, 2) for name, value in durations.items()})
  except TimeoutError:
    if program:
      dump_timeout(device, program.cores)
    raise
  finally:
    if device:
      device.close()


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  for dim in ('M', 'N', 'K'):
    parser.add_argument(dim, nargs='?', type=int, default=5000)
  parser.add_argument('--run', action='store_true')
  parser.add_argument('--runs', type=int, default=5)
  parser.add_argument('--device', type=int, default=0)
  parser.add_argument('--profile', action='store_true')
  parser.add_argument('--writer-wave-rows', type=int, default=0)
  parser.add_argument('--block-k', type=int, default=0)
  parser.add_argument('--output-noc', choices=('0','1','split'), default='split')
  parser.add_argument('--subblock', type=int, nargs=2, default=(2,4))
  parser.add_argument('--dtype', choices=('bf16', 'fp8'), default='bf16')
  args = parser.parse_args()
  if min(args.M, args.N, args.K, args.runs) <= 0:
    parser.error('dimensions and runs must be positive')
  run(args.M, args.N, args.K, runs=args.runs, device_index=args.device,
      execute=args.run, profile=args.profile, dtype=args.dtype, writer_wave_rows=args.writer_wave_rows, block_k=args.block_k, subblock=tuple(args.subblock), output_noc=args.output_noc)


if __name__ == '__main__':
  main()
