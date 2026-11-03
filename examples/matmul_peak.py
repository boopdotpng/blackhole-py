"""Row-major BF16 / FP8 matmul. Timing includes native unpack tilization."""
import os
from contextlib import contextmanager
from dataclasses import dataclass
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
from examples.matmul_peak_kernel import kernel as k, asm, epilogue


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


def build(plan, endpoints, a=0, b=0, c=0, *, output_noc="split"):
  """Build for padded row-major A/B inputs and face-major output tiles."""
  cb_configs = []
  address = k.CB_STORAGE_BASE
  n_split = plan.n_passes if plan.pass_axis == 'n' else 1
  sizes = (k.input_page_bytes(plan.in0_block_w), k.input_page_bytes(plan.per_core_n // n_split))
  for index, pages in ((0, plan.cb0_pages), (1, plan.cb1_pages),
                       (16, plan.cb16_pages), (24, plan.cb24_pages)):
    # FP32 partials accumulate in place in the output storage: CB24 aliases CB16.
    if index == 24:
      cb_address = cb_configs[-1][1]
    else:
      cb_address = address
      address += pages * (sizes[index] if index < 2 else k.TILE_BYTES)
    cb_configs.append((index, cb_address, pages * (sizes[index] if index < 2 else k.TILE_BYTES), pages))
  if k.INPUT_DTYPE == k.DType.BF16:
    for index, pages in ((2, plan.in0_block_num_tiles), (3, plan.in1_block_num_tiles)):
      cb_configs.append((index, address, pages * k.INPUT_TILE_BYTES, pages))
      address += pages * k.INPUT_TILE_BYTES
  # CB17 aliases CB16: each subblock's BF16 rows reuse its own FP32 tiles'
  # storage, which the epilogue has already copied into Dst.
  out16 = next(c for c in cb_configs if c[0] == 16)
  subblocks = plan.out_block_num_tiles // plan.out_subblock_num_tiles
  cb_configs.append((epilogue.OUT_CB, out16[1], subblocks * epilogue.page_bytes(plan), subblocks))
  if address > k.CB_STORAGE_END:
    raise ValueError('matmul buffers overlap launch tables')
  asm.CONTEXT = {'cbs': cb_configs, 'endpoints': endpoints, 'address': k.CODE_BASE, 'fp8': k.INPUT_DTYPE == k.DType.FP8}
  if plan.n_passes > 1 and plan.pass_axis == 'm':
    from dataclasses import replace
    plan = replace(plan, per_core_m=plan.per_core_m // plan.n_passes,
                   in0_num_subblocks=plan.in0_num_subblocks // plan.n_passes,
                   in0_block_num_tiles=plan.in0_block_num_tiles // plan.n_passes,
                   out_block_num_tiles=plan.out_block_num_tiles // plan.n_passes)
  elif plan.n_passes > 1:
    from dataclasses import replace
    plan = replace(plan, per_core_n=plan.per_core_n // plan.n_passes,
                   in1_num_subblocks=plan.in1_num_subblocks // plan.n_passes,
                   in1_block_num_tiles=plan.in1_block_num_tiles // plan.n_passes,
                   in1_per_core_w=plan.in1_per_core_w // plan.n_passes,
                   out_block_num_tiles=plan.out_block_num_tiles // plan.n_passes)
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
  if asm.CONTEXT['address'] > k.CB_STORAGE_BASE:
    raise ValueError(f'matmul code overlaps circular buffers ({asm.CONTEXT["address"]:#x})')
  if output_noc not in ('split', '0', '1'):
    raise ValueError('unsupported output NoC')
  program = GridProgram(sources, rows=plan.rows, cols=plan.cols)
  topology = struct.pack('<128I', *(plan.rows + (0,)*(64-len(plan.rows)) + plan.cols + (0,)*(64-len(plan.cols))))
  commands = program.commands(params=(a, b, c, len(endpoints), 2 if output_noc == 'split' else int(output_noc)),
                              l1={asm.GRID_BASE: topology, asm.SEM_BASE: bytes(128)})
  return program, commands, sources


def read_profile(window, cores, *, per_core=False):
  starts, ends = [], []
  durations = {name: [] for name, _ in k.PROFILE_NAMES}
  counters = {name: [] for name, _ in k.PROFILE_COUNTERS}
  for core in cores:
    window.target(0, core)
    starts.append(struct.unpack('<Q', window.read(k.PROFILE_BRISC, 8))[0])
    ends.append(max(struct.unpack('<Q', window.read(address + 8, 8))[0]
                    for address in (k.PROFILE_BRISC, k.PROFILE_NCRISC)))
    for name, address in k.PROFILE_NAMES:
      begin, end = struct.unpack('<QQ', window.read(address, 16))
      durations[name].append((end - begin) / 1350)
      if name.startswith('trisc'):
        csr = int.from_bytes(window.read(address + 16, 4), 'little')
        if csr & (1 << 18):
          raise AssertionError(f'instruction fusion disabled on {core}/{name}')
    if k.PROFILE_LEVEL:
      words = struct.unpack('<%dI' % len(k.PROFILE_COUNTERS),
                            window.read(k.PROFILE_COUNTER_BASE, 4 * len(k.PROFILE_COUNTERS)))
      for (name, _), value in zip(k.PROFILE_COUNTERS, words):
        counters[name].append(value / 1350)
  if per_core:
    return durations
  return (max(ends) - min(starts)) / 1350, {name: max(values) for name, values in durations.items()}, counters


def print_counters(counters, cores, plan):
  """Stall/phase accumulators in us: max, mean over all cores, and mean over
  cores that are neither A senders (grid column 0) nor B senders (grid row 0)."""
  interior = [i for i, (x, y) in enumerate(cores) if x != plan.cols[0] and y != plan.rows[0]]
  print(f'{"counter":28s} {"max":>9s} {"mean":>9s} {"interior":>9s}')
  for name, values in counters.items():
    if not values:
      continue
    inner = [values[i] for i in interior] or values
    print(f'{name:28s} {max(values):9.1f} {sum(values)/len(values):9.1f} {sum(inner)/len(inner):9.1f}')


def dump_timeout(device, cores):
  with TLBWindow(device.pcie.fd, cores[0]) as window:
    for core in cores[:4]:
      window.target(0, core)
      for address, size in ((0x68, 4), (0x370, 4), (asm.SEM_BASE, 64),
                            (k.SYNC_TRISC_START, 32), (k.DEBUG_TRISC0, 144), (k.DEBUG_NCRISC_OUTPUT, 16)):
        words = struct.unpack('<' + 'I'*(size//4), window.read(address, size))
        print(core, hex(address), [hex(v) for v in words], flush=True)


@dataclass(frozen=True)
class Region:
  plan: object
  m0: int          # first logical output row
  m: int           # logical output rows
  n0: int          # first logical output column
  n: int           # logical output columns
  overrides: dict  # kernel-module settings that differ from the default


@contextmanager
def region_globals(overrides):
  saved = {name: getattr(k, name) for name in overrides}
  for name, value in overrides.items(): setattr(k, name, value)
  try:
    yield
  finally:
    for name, value in saved.items(): setattr(k, name, value)


def _bands(cores):
  """Split workers into row bands whose rows share one column set. On a
  Blackhole with a partial column this is two rectangles covering every core."""
  rows = {}
  for x, y in cores: rows.setdefault(y, set()).add(x)
  bands = []
  for y in sorted(rows):
    if bands and bands[-1][1] == rows[y] and bands[-1][0][-1] == y - 1:
      bands[-1][0].append(y)
    else:
      bands.append(([y], rows[y]))
  return [[(x, y) for y in ys for x in sorted(xs)] for ys, xs in bands]


def plan_regions(m, inner, n, cores, *, all_cores=True):
  """Cover every worker: each row band computes its own output rows and
  receives A along its rows; B is read once per band. M is split so every
  core's output extent (and so its work) is as even as possible."""
  primary = k.plan_matmul(m, inner, n, cores)
  single = [Region(primary, 0, m, 0, n, {})]
  bands = _bands(cores)
  if not all_cores or len(bands) != 2:
    return single
  best = None
  for m0 in range(8, m, 8):
    try:
      plans = [k.plan_matmul(rows, inner, n, band) for rows, band in ((m0, bands[0]), (m - m0, bands[1]))]
    except ValueError:
      continue
    if any(len(p.cores()) != len(band) for p, band in zip(plans, bands)):
      continue
    cost = max(p.m_extent * p.n_extent for p in plans)
    if best is None or cost < best[0]:
      best = (cost, plans, m0)
  if best is None or best[0] >= primary.m_extent * primary.n_extent:
    return single
  _, (top, bottom), m0 = best
  return [Region(top, 0, m0, 0, n, {}), Region(bottom, m0, m - m0, 0, n, {})]


def run(m, n, inner, *, runs=5, device_index=0, execute=False, profile=False, dtype='bf16', fidelity=None, writer_wave_rows=0, block_k=0, subblock=None, output_noc="split", full_validation=False, all_cores=True):
  """Row-major BF16 or FP8 (E4M3) inputs, always FP32 accumulation.

  FP8 is exact at one fidelity phase (its 4-bit significand fits the
  multiplier). BF16 is exact at HiFi4; the default HiFi2 drops the lowest
  mantissa bit of one operand for twice the math rate.
  """
  if dtype not in ('bf16', 'fp8') or output_noc not in ('0', '1', 'split'):
    raise ValueError('unsupported dtype or output NoC')
  fidelity = fidelity or (2 if dtype == 'bf16' else 1)
  if fidelity not in (1, 2, 3, 4) or (dtype == 'fp8' and fidelity != 1):
    raise ValueError('fidelity is 1..4 for BF16; FP8 is exact at 1')
  if min(m, n, inner, runs) <= 0:
    raise ValueError('dimensions and runs must be positive')
  # FP32 Dst holds four tiles per half, and the per-core FP32 partial block
  # (pcm*pcn*4096 B) stays resident in L1 for packer L1 accumulation.
  subblock = subblock or (1, 4)
  h, w = subblock
  if h not in (1, 2) or w not in (1, 2, 4) or h > w or h*w > 4:
    raise ValueError('FP32 double buffering: subblock H <= W, at most 4 tiles, H in (1, 2)')
  if block_k < 0 or writer_wave_rows < 0:
    raise ValueError('block-k and writer-wave-rows must be nonnegative')
  # Tuning knobs. N passes split the per-core output (the ttnn output-block
  # split) so a longer K block fits next to the resident FP32 partials.
  k.N_PASSES = int(os.environ.get("MATMUL_N_PASSES", "1"))
  k.PASS_AXIS = os.environ.get("MATMUL_PASS_AXIS", "n")
  k.OVERLAP_BLOCKS = int(os.environ.get("MATMUL_OVERLAP_BLOCKS", "0"))
  k.INPUT_BUFFER_FACTOR = int(os.environ.get("MATMUL_A_BUFFERS", "2"))
  # BF16 prepares each K block in a serialized phase, so a longer K block is
  # worth more than double-buffered B staging (5000^3: K block 1 -> 2 measured
  # 54 -> 132 TFLOP/s).
  k.B_BUFFER_FACTOR = int(os.environ.get("MATMUL_B_BUFFERS", "1" if dtype == 'bf16' else "2"))
  if k.N_PASSES > 1 and writer_wave_rows:
    raise ValueError('passes currently require no writer waves')
  k.ROW_MOP = dtype == 'fp8'
  k.FAST_READS = True
  k.WRITER_WAVE_ROWS = writer_wave_rows
  k.SUPPORTED_IN0_BLOCK_WS = (block_k,) if block_k else tuple(range(1, 11 if dtype == 'fp8' else 7))
  if not block_k and dtype == 'fp8':
    k.SUPPORTED_IN0_BLOCK_WS = (2, 4, 6, 8, 10)  # odd FP8 K blocks take the slow, unaligned row-read path
  k.SUPPORTED_OUT_SUBBLOCK_H, k.SUPPORTED_OUT_SUBBLOCK_W = subblock
  k.INPUT_DTYPE = k.DType.FP8 if dtype == 'fp8' else k.DType.BF16
  k.INPUT_TILE_BYTES = k.INPUT_DTYPE.tile_size
  k.FIDELITY = fidelity
  k.OUTPUT_DTYPE = k.DType.F32
  k.TILE_BYTES = k.OUTPUT_DTYPE.tile_size
  device = Device(device_index) if execute else None
  programs = []
  try:
    if device:
      device.boot()
    cores = device.cores if device else P100_WORKER_CORES
    endpoints = device.pcie.dram_endpoints if device else P100_DRAM_ENDPOINTS
    regions = plan_regions(m, inner, n, list(cores), all_cores=all_cores)
    plan = regions[0].plan
    print(f'{dtype} {m}x{inner}x{n}, fp32 accumulation, fidelity {fidelity}, '
          f'{sum(len(r.plan.cores()) for r in regions)} cores', flush=True)
    for region in regions:
      p = region.plan
      print(f'  region M[{region.m0}:{region.m0 + region.m}] N[{region.n0}:{region.n0 + region.n}]: grid {len(p.rows)}x{len(p.cols)}, '
            f'per core {p.m_extent}x{p.n_extent} ({p.per_core_m}x{p.per_core_n} tiles), '
            f'K block {p.in0_block_w}, subblock {p.out_subblock_h}x{p.out_subblock_w}', flush=True)
    if not device:
      for region in regions:
        with region_globals(region.overrides):
          program, _, sources = build(region.plan, endpoints, output_noc=output_noc)
        print('Kernel bytes:', {name: len(image) for name, (_, image) in sources.items()})
      return
    a_ref, b_ref = k.make_inputs(m, inner, n)
    a_storage, b_storage = a_ref, b_ref
    if dtype == 'fp8':
      a_storage, b_storage = (fp8_encode(values) for values in (a_ref, b_ref))
      # Decode only for CPU validation; upload the padded encoded bytes in row-major order.
      a_ref, b_ref = (fp8_decode(words) for words in (a_storage, b_storage))
    commands, outputs = [], []
    for region in regions:
      p, m0, mr, n0, nr = region.plan, region.m0, region.m, region.n0, region.n
      mp, kp, npad = p.mt*32, p.kt*32, p.nt*32
      buffers = []
      for operand, (values, shape) in enumerate(((a_storage[m0:m0+mr], (mp, kp)), (b_storage[:, n0:n0+nr], (kp, npad)))):
        shape = (shape[0], k.input_dram_columns(shape[1]))
        padded = np.zeros(shape, dtype=np.uint8 if dtype == 'fp8' else np.float32)
        if operand == 0:
          for i in range(len(p.rows)):
            start = i * p.m_extent
            count = min(p.m_extent, max(0, mr - start))
            padded[i*p.per_core_m*32:i*p.per_core_m*32+count, :inner] = values[start:start+count]
        else:
          for i in range(len(p.cols)):
            start = i * p.n_extent
            count = min(p.n_extent, max(0, nr - start))
            padded[:inner, i*p.per_core_n*32:i*p.per_core_n*32+count] = values[:, start:start+count]
        buffer = device.alloc_interleaved_dram(padded.size * (1 if dtype == "fp8" else 2), page_size=k.INPUT_TILE_BYTES)
        data = (padded.tobytes() if dtype == 'fp8' else
                (padded.view(np.uint32) >> 16).astype('<u2').tobytes())
        device.write_dram(buffer, data)
        buffers.append(buffer)
      # Row-major BF16, rows padded to whole 2048-byte pages.
      output = device.alloc_interleaved_dram(mp*epilogue.output_columns(p)*2, page_size=2048)
      device.write_dram(output, b'\xa5' * output.size)
      outputs.append(output)
      with region_globals(region.overrides):
        try:
          program, region_commands, _ = build(p, endpoints, buffers[0].address, buffers[1].address, output.address, output_noc=output_noc)
        except ValueError as error:
          # The unrolled fast reader can outgrow the code region for some
          # plans; the generic reader is smaller.
          if 'overlaps circular buffers' not in str(error) or not k.FAST_READS: raise
          print('fast reader does not fit this plan; using the generic reader')
          k.FAST_READS = False
          program, region_commands, _ = build(p, endpoints, buffers[0].address, buffers[1].address, output.address, output_noc=output_noc)
      programs.append(program)
      commands.extend(region_commands[:-1])  # every region starts under one RUN
    all_cores = tuple(core for program in programs for core in program.cores)
    device.cq.submit((*commands, Run(all_cores)), timeout=10)  # Upload and warm up.
    timings = []
    with TLBWindow(device.pcie.fd, all_cores[0]) as window:
      for _ in range(runs):
        device.cq.submit((McastWrite(rectangles(all_cores), asm.SEM_BASE, bytes(128)),
                          McastWrite(rectangles(all_cores), k.PROFILE_COUNTER_BASE, bytes(k.PROFILE_COUNTER_BYTES)),
                          Run(all_cores)), timeout=10)
        elapsed, durations, counters = read_profile(window, all_cores)
        timings.append(elapsed)
    dense = np.empty((m,n),dtype='<u2')
    for region, output in zip(regions, outputs):
      p, m0, mr, n0, nr = region.plan, region.m0, region.m, region.n0, region.n
      mp, npad = p.mt*32, p.nt*32
      columns = epilogue.output_columns(p)
      physical = np.frombuffer(device.read_dram(output), dtype='<u2')[:mp*columns].reshape(mp, columns)
      for i in range(len(p.rows)):
        r = i*p.m_extent
        h = min(p.m_extent,max(0,mr-r))
        for j in range(len(p.cols)):
          c = j*p.n_extent
          w = min(p.n_extent,max(0,nr-c))
          dense[m0+r:m0+r+h,n0+c:n0+c+w] = physical[i*p.per_core_m*32:i*p.per_core_m*32+h,
                                              j*p.per_core_n*32:j*p.per_core_n*32+w]
    pcc, error = k.validate(a_ref, b_ref, dense.tobytes(), m, n, m, n, full=full_validation)
    throughput = [k.tflops(m, n, inner, elapsed) for elapsed in timings]
    print(f'{runs} runs: TFLOP/s mean {sum(throughput)/len(throughput):.2f}, '
          f'min {min(throughput):.2f}, max {max(throughput):.2f}')
    if profile:
      print(f'PASS: PCC={pcc:.6f}, rel_l2={error:.6f}')
      print('Last run, maximum duration per role (us):', {name: round(value, 2) for name, value in durations.items()})
      if len(programs) > 1:
        with TLBWindow(device.pcie.fd, all_cores[0]) as window:
          for index, program in enumerate(programs):
            region_durations = read_profile(window, program.cores, per_core=True)
            print(f'  region {index} max (us):', {name: round(max(values), 1) for name, values in region_durations.items()})
      if k.PROFILE_LEVEL:
        print(f'Last run, accumulated counters (us, profile level {k.PROFILE_LEVEL}):')
        print_counters(counters, list(all_cores), plan)
  except TimeoutError:
    if programs:
      dump_timeout(device, [core for program in programs for core in program.cores])
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
  parser.add_argument('--full-validation', action='store_true',
                      help='compare every output element against the CPU reference')
  parser.add_argument('--writer-wave-rows', type=int, default=0)
  parser.add_argument('--block-k', type=int, default=0)
  parser.add_argument('--output-noc', choices=('0','1','split'), default='split')
  parser.add_argument('--subblock', type=int, nargs=2)
  parser.add_argument('--fidelity', type=int, choices=(1, 2, 3, 4),
                      help='BF16 fidelity phases (default 2; 4 is exact). FP8 always uses 1, which is exact')
  parser.add_argument('--dtype', choices=('bf16', 'fp8'), default='bf16')
  parser.add_argument('--grid-only', action='store_true', help='use only the largest rectangular core grid')
  args = parser.parse_args()
  if min(args.M, args.N, args.K, args.runs) <= 0:
    parser.error('dimensions and runs must be positive')
  run(args.M, args.N, args.K, runs=args.runs, device_index=args.device,
      execute=args.run, profile=args.profile, dtype=args.dtype, writer_wave_rows=args.writer_wave_rows, block_k=args.block_k, subblock=tuple(args.subblock) if args.subblock else None, output_noc=args.output_noc, fidelity=args.fidelity,
      full_validation=args.full_validation, all_cores=not args.grid_only)


if __name__ == '__main__':
  main()
