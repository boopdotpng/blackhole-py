"""Unpacker probes (k_unpack.c on TRISC0, k_unpack_math.c on TRISC1, k_unpack_pack.c on TRISC2, k_unpack_noc.c on
BRISC/NCRISC or a second tile). See UNPACK.md for the case groups, hypotheses and risks.

  python3 sims/probes/run.py --device 1 --output sims/results/<date>-unpack-card1.jsonl unpack [-k verify]
  python3 sims/probes/unpack.py --check     # host-only: encodings vs ttrv.isa, every image compiles, data models

Formats in scope (user decision 2026-11-18): bf16, fp8 (e4m3 only), bfp8, bfp4 in L1; plus fp32 -> SrcA (attention
state merge, llama3_attention.ttrv:472), labelled fmt='fp32-srca'. bf16 with transpose (attention.ttrv:449).

Timing: a sample is t1 - t0 on TRISC0 around `count` ops then a drain; for each count in COUNTS there are REPS
samples, the first a warmup. slope = (median(c2) - median(c0)) / (c2 - c0) cycles per op.
"""
import hashlib, struct, subprocess, sys, tempfile
from pathlib import Path
from statistics import median

import numpy as np

HERE = Path(__file__).resolve().parent
TILE = (1, 2)             # the unpacking tile
PEER = (2, 2)             # remote NoC traffic generator
SRC_A, SRC_B, PACK_OUT, NOC_BUF, U_FLAGS = 0x80000, 0x100000, 0x160000, 0x170000, 0x48000
REGION_A, REGION_B = 0x100000 - SRC_A, 0x160000 - SRC_B
COUNTS, REPS = (8, 24, 56), 8
TILE_COUNTS = (2, 6, 14)
MODE = dict(raw=1, extra=2, move=3, lat=4, full=5)
MATH = dict(consume=1, lat=2, full=3)
KIND = dict(release=0, mova2d=1, movb2d=2, elwmul=3, mvmul=4)
PAT = dict(pair_face=1, a_face=2, b_face=3, a_tile=4, b_tile=5, ba_tile=6)
PAT_EVENTS = dict(pair_face=(4, 3), a_face=(4, 1), b_face=(4, 2), a_tile=(1, 1), b_tile=(1, 2), ba_tile=(1, 3))
EXTRA = ['none', 'setadczw', 'setadcxx_zw', 'rmwcib4', 'stall_cfg', 'stall_done', 'risc_base', 'credit', 'wrcfg',
         'setc16', 'nop_wake']
# fmt name: (in code, out code, L1 bytes per datum excluding BFP exponents)
FMT = {'bf16': (5, 5, 2), 'fp8': (10, 10, 1), 'bfp8': (6, 6, 1), 'bfp4': (7, 7, 0.5), 'fp32-srca': (0, 5, 4)}
SITES = {1: 'start/consumer flag', 2: 'packer start / ready', 3: 'UNPACK_SYNC credit', 4: 'armed', 5: 'released'}


def is_bfp(f): return f in ('bfp8', 'bfp4')


def block_bytes(fmt, n):
  """L1 bytes of one unpack block of n datums (BFP: exponent section first, 16 B per 256 datums rounded up)."""
  if is_bfp(fmt): return -(-n // 256) * 16 + int(n * FMT[fmt][2])
  return int(n * FMT[fmt][2])


# ---------------------------------------------------------------- data and reference models

def _rng(seed): return np.random.default_rng(seed)


def make_data(fmt, n, seed=1):
  """A block of n datums in L1 layout and the bf16 / f32 bit patterns the pipeline should produce."""
  r = _rng(seed)
  if fmt == 'bf16':
    v = (0x3C00 + r.integers(0, 0x0800, n)).astype(np.uint16) | (r.integers(0, 2, n).astype(np.uint16) << 15)
    return v.tobytes(), v
  if fmt == 'fp32-srca':
    v = (0x3C000000 + r.integers(0, 0x08000000, n, dtype=np.int64)).astype(np.uint32)
    v |= r.integers(0, 2, n).astype(np.uint32) << 31
    return v.tobytes(), (v >> 16).astype(np.uint16)          # unpacker truncates fp32 -> bf16
  if fmt == 'fp8':
    exp = r.integers(1, 15, n)                                 # normals only, no NaN (exp 15, man 7)
    b = (r.integers(0, 2, n) << 7 | exp << 3 | r.integers(0, 8, n)).astype(np.uint8)
    return b.tobytes(), e4m3_to_f32(b)
  mag_bits = 7 if fmt == 'bfp8' else 3
  exps, codes = [], []
  for _ in range(n // 16):
    exps.append(int(r.integers(118, 136)))
    g = [int(r.integers(1, 1 << mag_bits)) | int(r.integers(0, 2)) << mag_bits for _ in range(16)]
    k = int(r.integers(0, 16))
    g[k] = (g[k] & 1 << mag_bits) | int(r.integers(1 << (mag_bits - 1), 1 << mag_bits))
    codes += g
  ebytes = bytes(exps).ljust(-(-n // 256) * 16, b'\0')
  mant = bytes(codes) if fmt == 'bfp8' else bytes(codes[i] | codes[i + 1] << 4 for i in range(0, n, 2))
  return ebytes + mant, np.array([bfp_to_bf16(fmt, c, exps[i // 16]) for i, c in enumerate(codes)], np.uint16)


def e4m3_to_f32(b):
  """ISA FormatConversion (Exponent4b) to FP16, then exact FP16 -> FP32 (the packer widens 16-bit Dst)."""
  b = np.asarray(b, np.uint16)
  sign, exp, man = b >> 7 & 1, b >> 3 & 15, b & 7
  pad = np.where((exp == 15) & (man == 7), 0x7F, 0)
  h = (sign << 15) | (np.where(exp > 0, exp + 8, 0) << 10) | (man << 7) | pad
  return h.astype(np.uint16).view(np.float16).astype(np.float32).view(np.uint32)


def bfp_to_bf16(fmt, code, exp):
  """ISA BFP8ToBF16 (BFP4: the nibble shifted into the top of a BFP8 datum)."""
  d = code if fmt == 'bfp8' else code << 4
  sign, mag = d >> 7 & 1, (d << 1) & 0xFF
  if mag == 0: return 0xFF80 if sign else 0
  lz = 8 - mag.bit_length()
  mag, exp = (mag << lz) & 0xFF, (exp - lz) & 0xFF
  return sign << 15 | exp << 7 | (mag & 0x7E)


def transpose_faces(v):
  return np.asarray(v).reshape(-1, 16, 16).transpose(0, 2, 1).reshape(-1)


def stream_data(fmt, ops, n, seed=1):
  """Back-to-back blocks for raw streaming. BFP raw blocks are one big block of `ops` faces (ZDim = ops):
  [ceil(ops * n / 256) * 16 B exponents][mantissas], which is what Z stepping through one descriptor reads."""
  return make_data(fmt, n * ops, seed)[0]


# ---------------------------------------------------------------- builds

def _hdr_tag():
  return hashlib.sha256(b''.join((HERE / f).read_bytes() for f in ('unpack.h', 'probe.h'))).hexdigest()[:12]


def build_all(case):
  """{role: image} for the case (fw.compile does not hash sims/probes headers: UNPACK_TAG forces a rebuild)."""
  from tile import build
  tag = dict(UNPACK_TAG=f'0x{_hdr_tag()[:8]}')
  imgs = {'trisc0': build('k_unpack.c', 'trisc0', MODE=MODE[case['mode']], **tag)}
  if case.get('math'): imgs['trisc1'] = build('k_unpack_math.c', 'trisc1', MATH=MATH[case['math']], **tag)
  if case.get('pack'): imgs['trisc2'] = build('k_unpack_pack.c', 'trisc2', PACK=dict(verify=1, loop=2)[case['pack']], **tag)
  if case.get('noc_local'): imgs['brisc'] = build('k_unpack_noc.c', 'brisc', **tag)
  if case.get('noc_local2'): imgs['ncrisc'] = build('k_unpack_noc.c', 'ncrisc', **tag)
  return imgs


# ---------------------------------------------------------------- case table

def _cfg(sel, dvalid=0, transpose=0, direct=0, throttle=None, wstart=0, wpack=0, pat=0, extra=0, step=1):
  c = sel | dvalid << 2 | transpose << 3 | direct << 4 | wstart << 8 | wpack << 9 | pat << 12 | extra << 16 | step << 20
  if throttle is not None: c |= 1 << 5 | throttle << 6
  return c


def _case(id, group, **kw):
  kw.setdefault('tiles', [TILE])
  return dict(id=f'{group}-{id}', group=group, **kw)


def _cases():
  U = {'a': 1, 'b': 2, 'ab': 3}
  # issue: per-instruction cost with negligible data (one 16-datum row)
  for unit in ('a', 'b', 'ab'):
    for issue in ('mop', 'direct'):
      for op in ('unpacr', 'nop'):
        if unit == 'ab' and op == 'nop': continue
        yield _case(f'{op}-{unit}-{issue}', 'issue', mode='raw', fmt='bf16', unit=unit, n=16, issue=issue, op=op)
  # size: throughput per format and datums per UNPACR, one unpacker, MOP, no dvalid, L1 walking forward
  for fmt, ns in (('bf16', (16, 64, 128, 256, 512, 1024)), ('fp8', (16, 64, 128, 256, 512, 1024)),
                  ('bfp8', (128, 256)), ('bfp4', (128, 256)), ('fp32-srca', (16, 64, 256, 512, 1024))):
    for unit in (('a',) if fmt == 'fp32-srca' else ('a', 'b')):
      for n in ns:
        yield _case(f'{fmt}-{unit}-n{n}', 'size', mode='raw', fmt=fmt, unit=unit, n=n)
  for n in (256, 1024):
    yield _case(f'bf16-a-n{n}-transpose', 'size', mode='raw', fmt='bf16', unit='a', n=n, transpose=1)
  yield _case('bf16-a-n1024-nostep', 'size', mode='raw', fmt='bf16', unit='a', n=1024, step=0)
  # throttle override (RISKY: word 70 bit 3): x1/x2/x4 alone, then the A x B interference table
  for fmt in ('bf16', 'fp8'):
    for unit in (('a', 'b') if fmt == 'bf16' else ('a',)):
      for t in range(3):
        yield _case(f'{fmt}-{unit}-n1024-x{1 << t}', 'throttle', mode='raw', fmt=fmt, unit=unit, n=1024, throttle=(t, t))
  for ta in range(3):
    for tb in range(3):
      yield _case(f'bf16-ab-n1024-a{1 << ta}x-b{1 << tb}x', 'throttle', mode='raw', fmt='bf16', unit='ab', n=1024,
                  throttle=(ta, tb))
  # dual: both unpackers, A and B UNPACRs interleaved (llama pair), vs size-group singles
  for fmt, ns in (('bf16', (16, 256, 1024)), ('fp8', (256, 1024)), ('bfp8', (256,)), ('bfp4', (256,))):
    for n in ns:
      yield _case(f'{fmt}-n{n}', 'dual', mode='raw', fmt=fmt, unit='ab', n=n)
  # place: B's source = A's + offset (same / different L1 banks; both walk forward with the same stride)
  for n in (256, 1024):
    for off in (0, 16, 32, 48, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 0x10000):
      yield _case(f'bf16-n{n}-off{off:#x}', 'place', mode='raw', fmt='bf16', unit='ab', n=n, base_b=SRC_A + off)
  # align: source base offset from a 64 KiB boundary
  for fmt, n, offs in (('bf16', 256, (0, 16, 32, 48, 64, 128, 256, 512)), ('bf16', 1024, (0, 16, 32, 48, 64, 128, 256, 512)),
                       ('fp8', 1024, (0, 16, 32, 64))):
    for off in offs:
      yield _case(f'{fmt}-a-n{n}-off{off}', 'align', mode='raw', fmt=fmt, unit='a', n=n, base_a=SRC_A + off)
  # extra: per-op cost of the config / sync instructions llama emits around an UNPACR (pushed one by one)
  for n in (16, 256):
    for x in EXTRA:
      yield _case(f'{x}-a-n{n}', 'extra', mode='extra', fmt='bf16', unit='a', n=n, extra=x)
  for x in ('none', 'rmwcib4', 'credit'):
    yield _case(f'{x}-b-n256', 'extra', mode='extra', fmt='bf16', unit='b', n=256, extra=x)
  # move: the ttrv `unpack.move` lowering per tile, as the llama kernels use it, no dvalid (no consumer)
  for pat, fmt, tr in (('pair_face', 'bf16', 0), ('pair_face', 'fp8', 0), ('a_face', 'bf16', 0), ('a_tile', 'bf16', 0),
                       ('a_tile', 'fp32-srca', 0), ('a_tile', 'bfp8', 0), ('a_tile', 'bfp4', 0), ('ba_tile', 'bf16', 1),
                       ('ba_tile', 'bf16', 0), ('b_tile', 'bf16', 0), ('b_tile', 'bfp8', 0), ('b_tile', 'bfp4', 0)):
    yield _case(f'{pat}-{fmt}{"-transpose" if tr else ""}', 'move', mode='move', fmt=fmt, pat=pat, transpose=tr)
  # pipe: SetDatValid + a T1 consumer as fast as it can go; steady unpack + math rate
  for pat, fmt, tr, kinds in (('pair_face', 'bf16', 0, ('release', 'elwmul')), ('pair_face', 'fp8', 0, ('release', 'elwmul')),
                              ('a_face', 'bf16', 0, ('release', 'mova2d')), ('a_tile', 'bf16', 0, ('release', 'mova2d')),
                              ('a_tile', 'fp32-srca', 0, ('release', 'mova2d')), ('a_tile', 'bfp8', 0, ('release',)),
                              ('a_tile', 'bfp4', 0, ('release',)), ('ba_tile', 'bf16', 1, ('release', 'mvmul')),
                              ('ba_tile', 'bf16', 0, ('mvmul',))):
    for k in kinds:
      yield _case(f'move-{pat}-{fmt}{"-transpose" if tr else ""}-{k}', 'pipe', mode='move', fmt=fmt, pat=pat,
                  transpose=tr, dvalid=1, math='consume', kind=k)
  for unit, n, kinds in (('ab', 256, ('release', 'elwmul', 'mvmul')), ('a', 256, ('release', 'mova2d')), ('a', 1024, ('release',))):
    for k in kinds:
      yield _case(f'raw-{unit}-n{n}-bf16-{k}', 'pipe', mode='raw', fmt='bf16', unit=unit, n=n, dvalid=1, math='consume', kind=k)
  yield _case('raw-ab-n256-fp8-elwmul', 'pipe', mode='raw', fmt='fp8', unit='ab', n=256, dvalid=1, math='consume', kind='elwmul')
  # handoff: dvalid -> math latency, and the stall while both banks are full
  for fmt, unit, n in (('bf16', 'a', 16), ('bf16', 'a', 256), ('bf16', 'a', 1024), ('bf16', 'b', 16), ('bf16', 'b', 256),
                       ('bf16', 'b', 1024), ('fp8', 'a', 1024)):
    yield _case(f'lat-{fmt}-{unit}-n{n}', 'handoff', mode='lat', fmt=fmt, unit=unit, n=n, math='lat', delay=400)
  for n, delay in ((256, 200), (256, 1000), (256, 5000), (1024, 1000)):
    yield _case(f'full-bf16-a-n{n}-d{delay}', 'handoff', mode='full', fmt='bf16', unit='a', n=n, math='full', delay=delay)
  # contention: the same unpack workload while other L1 clients run
  work = [('rawA-bf16-n1024', dict(mode='raw', fmt='bf16', unit='a', n=1024)),
          ('rawAB-bf16-n256', dict(mode='raw', fmt='bf16', unit='ab', n=256)),
          ('rawA-fp8-n1024', dict(mode='raw', fmt='fp8', unit='a', n=1024)),
          ('move-pair_face-bf16', dict(mode='move', fmt='bf16', pat='pair_face'))]
  traffic = [('none', {}), ('self8k', dict(noc_local=(0, 8192))), ('self8k-2noc', dict(noc_local=(0, 8192), noc_local2=(1, 8192))),
             ('wr_in8k', dict(noc_remote=('wr_in', 0, 8192), tiles=[TILE, PEER])),
             ('rd_out8k', dict(noc_remote=('rd_out', 0, 8192), tiles=[TILE, PEER])),
             ('pack', dict(pack='loop')), ('pack-self8k', dict(pack='loop', noc_local=(0, 8192)))]
  for wn, w in work:
    for tn, t in traffic:
      yield _case(f'{wn}-{tn}', 'contention', **w, **t)
  for size in (512, 2048):
    yield _case(f'rawA-bf16-n1024-self{size}', 'contention', mode='raw', fmt='bf16', unit='a', n=1024, noc_local=(0, size))
  # verify: data lands correctly (unpack -> T1 MOVA2D/MOVB2D -> Dst -> T2 pack -> host compare), once per format
  for fmt, pats in (('bf16', ('a_face', 'b_face', 'a_tile', 'b_tile')), ('fp8', ('a_face', 'b_face', 'a_tile', 'b_tile')),
                    ('bfp8', ('a_tile', 'b_tile')), ('bfp4', ('a_tile', 'b_tile')), ('fp32-srca', ('a_face', 'a_tile'))):
    for pat in pats:
      yield _case(f'{fmt}-{pat}', 'verify', mode='move', fmt=fmt, pat=pat, verify=True)
  yield _case('bf16-a_tile-transpose', 'verify', mode='move', fmt='bf16', pat='a_tile', transpose=1, verify=True)
  for t in range(3):
    yield _case(f'bf16-a_tile-x{1 << t}', 'verify', mode='move', fmt='bf16', pat='a_tile', throttle=(t, t), verify=True)


CASES = list(_cases())
assert len({c['id'] for c in CASES}) == len(CASES)


# ---------------------------------------------------------------- run

def _unit_sel(case):
  if case['mode'] == 'move': return {'pair_face': 3, 'a_face': 1, 'b_face': 2, 'a_tile': 1, 'b_tile': 2, 'ba_tile': 3}[case['pat']]
  return {'a': 1, 'b': 2, 'ab': 3}[case['unit']]


def plan(case):
  """Everything a launch needs: per-role params, L1 contents, and how to read the result."""
  fmt, mode = case['fmt'], case['mode']
  fin, fout, _ = FMT[fmt]
  sel = _unit_sel(case)
  verify = case.get('verify')
  counts = (1,) if verify else TILE_COUNTS if mode == 'move' else COUNTS
  reps = 1 if verify else REPS
  n = 1024 if mode == 'move' and case.get('pat', '').endswith('tile') else 256 if mode == 'move' else case['n']
  if mode in ('lat', 'full'): counts = ()
  throttle = case.get('throttle')
  cfg = _cfg(sel, dvalid=case.get('dvalid', 1 if verify or mode in ('lat', 'full') else 0), transpose=case.get('transpose', 0),
             direct=case.get('issue') == 'direct' or mode == 'extra', throttle=None, wstart=bool(case.get('noc_local') or case.get('noc_remote')),
             wpack=case.get('pack') == 'loop', pat=PAT.get(case.get('pat'), 1 if case.get('op') == 'nop' else 0),
             extra=EXTRA.index(case.get('extra', 'none')), step=0 if mode == 'extra' else case.get('step', 1))
  if throttle is not None: cfg |= 1 << 5 | throttle[0] << 6  # override bit + A's mode; B's mode is P_THB
  fmtw = fin | fout << 4 | fin << 8 | fout << 12
  l1 = {U_FLAGS: bytes(64)}
  maxc = max(counts) if counts else 3
  base_a, base_b = case.get('base_a', SRC_A), case.get('base_b', SRC_B)
  if mode == 'move':
    tile_bytes = block_bytes(fmt, 1024)
    stride = tile_bytes
    if verify:
      data, expect = make_data(fmt, 1024, seed=7)
      if case.get('transpose'): expect = transpose_faces(expect)
      l1[base_a if sel & 1 else base_b] = data
      l1[PACK_OUT] = b'\xa5' * 4096
    else:
      if sel & 1: l1[base_a] = make_data(fmt, 1024 * maxc, 3)[0] if not is_bfp(fmt) else b''.join(make_data(fmt, 1024, 3 + t)[0] for t in range(maxc))
      if sel & 2: l1[base_b] = make_data(fmt, 1024 * maxc, 5)[0] if not is_bfp(fmt) else b''.join(make_data(fmt, 1024, 5 + t)[0] for t in range(maxc))
    sa = sb = stride
  else:
    per = block_bytes(fmt, n) if not is_bfp(fmt) else 0
    if sel & 1: l1[base_a] = stream_data(fmt, maxc, n, 3)
    if sel & 2:
      if sel & 1 and base_a <= base_b < base_a + 0x40000:  # placement sweep: one buffer covers both streams
        l1[base_a] = stream_data(fmt, maxc + -(-(base_b - base_a) // max(per, 16)) + 1, n, 3)
      else: l1[base_b] = stream_data(fmt, maxc, n, 5)
    sa = sb = per
  for a, d in l1.items():
    if a >= SRC_A and a < PACK_OUT:
      lim = 0x100000 if a < 0x100000 else 0x160000
      if a + len(d) > lim: raise ValueError(f"{case['id']}: source overruns its region ({a:#x}+{len(d):#x})")
  zdim = maxc if is_bfp(fmt) and mode != 'move' else 1
  t0p = [cfg, fmtw, n, base_a, base_b, sum(c << 8 * i for i, c in enumerate(counts)), reps, zdim, sa, sb,
         case.get('delay', 0)]
  t0p.append(throttle[1] if throttle is not None else 0)  # P_THB
  params = {'trisc0': t0p}
  # T1
  if case.get('math') == 'consume':
    per_op, mask = PAT_EVENTS[case['pat']] if mode == 'move' else (1, sel)
    events = per_op * sum(counts) * reps
    kind = case['kind']
    rows = 64 if mode == 'move' and case['pat'].endswith('tile') else 16
    if mode == 'raw': rows = max(8, n // 16)
    params['trisc1'] = [KIND[kind], mask, events, rows, 16 if mode == 'move' else 4, 0, 0, 1, 0, 0]
  elif verify:
    case = dict(case, math='consume', pack='verify')
    per_op, mask = PAT_EVENTS[case['pat']]
    kind = 'mova2d' if mask == 1 else 'movb2d'
    rows = 64 if case['pat'].endswith('tile') else 16
    fp8 = fmt == 'fp8'
    params['trisc1'] = [KIND[kind], mask, per_op, rows, 0, 0 if fp8 else 1, 1, 0, 0, 0]
    w70 = 8 if throttle is not None else 0
    params['trisc2'] = [0, 1, 0, PACK_OUT, w70, 0] if fp8 else [5, 5, 1, PACK_OUT, w70, 0]
  elif case.get('math') == 'lat':
    params['trisc1'] = [0, sel, 0, 0, 0, 0, 0, 0, REPS, 0]
  elif case.get('math') == 'full':
    params['trisc1'] = [0, 1, 0, 0, 0, 0, 0, 0, REPS, case['delay']]
  if case.get('pack') == 'loop':
    params['trisc2'] = [5, 5, 1, PACK_OUT, 8 if throttle is not None else 0, 100000]
  jobs_extra = []
  if case.get('noc_local'):
    noc, size = case['noc_local']
    params['brisc'] = [0, noc, size, 0, NOC_BUF + 0x8000, 200000, NOC_BUF, 0]
  if case.get('noc_local2'):
    noc, size = case['noc_local2']
    params['ncrisc'] = [0, noc, size, 0, NOC_BUF + 0xC000, 200000, NOC_BUF + 0x4000, 0]
  if case.get('noc_remote'):
    kind, noc, size = case['noc_remote']
    jobs_extra.append((PEER, [1 if kind == 'wr_in' else 2, noc, size, TILE[0] | TILE[1] << 6, NOC_BUF, 20000, NOC_BUF, 0]))
  return dict(case=case, params=params, l1=l1, counts=counts, reps=reps, expect=expect if verify else None,
              jobs_extra=jobs_extra)


def _slope(counts, samples):
  meds = [median(s[1:]) for s in samples]
  out = dict(counts=list(counts), medians=meds, samples=samples)
  if len(counts) >= 2:
    out['slope'] = (meds[-1] - meds[0]) / (counts[-1] - counts[0])
    out['slopes'] = [(b - a) / (cb - ca) for a, b, ca, cb in zip(meds, meds[1:], counts, counts[1:])]
    out['intercept'] = meds[0] - out['slope'] * counts[0]
    out['median'] = out['slope']
  return out


def run(card, case, timeout):
  from tile import build
  p = plan(case)
  case = p['case']
  imgs = build_all(case)
  jobs = [(TILE, imgs, p['params'], p['l1'])]
  for tile, params in p['jobs_extra']:
    jobs.append((tile, build('k_unpack_noc.c', 'brisc', UNPACK_TAG=f'0x{_hdr_tag()[:8]}'), params, {}))
  card.run(jobs, max(timeout, 0.5), SITES)
  rec = {}
  if case['mode'] in ('lat', 'full'):
    w = card.log(TILE, 2 * REPS, 'trisc0')
    m = card.log(TILE, REPS, 'trisc1')
    t0, t1 = w[0::2], w[1::2]
    s32 = lambda x: (x & 0xFFFFFFFF) - (1 << 32) if x & 0x80000000 else x
    if case['mode'] == 'lat':
      unp = [s32(b - a) for a, b in zip(t0, t1)][1:]
      seen = [s32(c - a) for a, c in zip(t0, m)][1:]
      rec = dict(unpack_done=unp, math_seen=seen, unpack_done_median=median(unp), math_seen_median=median(seen),
                 median=median(seen))
    else:
      stall = [s32(b - a) for a, b in zip(t0, t1)][1:]
      after = [s32(b - r) for b, r in zip(t1, m)][1:]
      rec = dict(stall=stall, after_release=after, stall_median=median(stall), after_release_median=median(after),
                 median=median(after))
    return rec
  if case.get('verify'):
    exp = p['expect']
    if case['fmt'] == 'fp8':
      got = np.frombuffer(card.iface.read(TILE, PACK_OUT, 4096), np.uint32)
    else:
      got = np.frombuffer(card.iface.read(TILE, PACK_OUT, 2048), np.uint16)
    bad = np.nonzero(got != exp)[0]
    rec = dict(ok=not len(bad), mismatches=int(len(bad)), first_bad=[[int(i), int(got[i]), int(exp[i])] for i in bad[:8]])
    if len(bad): raise RuntimeError(f"{case['id']}: {len(bad)} of {len(exp)} datums differ, first {rec['first_bad']}")
    return rec
  ncount = len(p['counts']) * p['reps']
  w = card.log(TILE, ncount, 'trisc0')
  samples = [list(w[i * p['reps']:(i + 1) * p['reps']]) for i in range(len(p['counts']))]
  rec = _slope(p['counts'], samples)
  aux = card.aux(TILE, 2, 'trisc0')
  rec['generator_stopped_early'] = aux[0]
  rec['packer_stopped_early'] = aux[1]
  if case.get('math'): rec['math_log'] = list(card.log(TILE, 2, 'trisc1'))
  if case.get('noc_local'): rec['noc_log'] = list(card.log(TILE, 4, 'brisc'))
  if case.get('pack') == 'loop': rec['pack_log'] = list(card.log(TILE, 3, 'trisc2'))
  if case.get('noc_remote'): rec['peer_log'] = list(card.log(PEER, 4, 'brisc'))
  return rec


# ---------------------------------------------------------------- host-only checks

ENC = {  # macro expression: (ttrv.isa name, fields)
  'UNPACR(0, 1, 1)': ('UNPACR', dict(Unpack_block_selection=0, AddrMode=1, OvrdThreadId=1, SetDatValid=1, Last=1)),
  'UNPACR(1, 0x11, 0)': ('UNPACR', dict(Unpack_block_selection=1, AddrMode=0x11, OvrdThreadId=1, Last=1)),
  'UNPACR_NOP_NOP(1)': ('UNPACR_NOP', dict(Unpacker_Select=1, Unpack_Pop=2)),
  'UNPACR_NOP_DVALID(1)': ('UNPACR_NOP', dict(Unpacker_Select=1, Set_Dvalid=1, Unpack_Pop=1)),
  'SETADCXX(2, 255, 3)': ('SETADCXX', dict(CntSetMask=2, x_end2=255, x_start=3)),
  'SETADCXY(4, 1, 2, 3, 4, 11)': ('SETADCXY', dict(CntSetMask=4, Ch1_Y=1, Ch1_X=2, Ch0_Y=3, Ch0_X=4, BitMask=11)),
  'SETADCZW(3, 1, 2, 3, 4, 15)': ('SETADCZW', dict(CntSetMask=3, Ch1_W=1, Ch1_Z=2, Ch0_W=3, Ch0_Z=4, BitMask=15)),
  'SETADC(4, 0, 3, 5)': ('SETADC', dict(CntSetMask=4, ChannelIndex=0, DimensionIndex=3, Value=5)),
  'STALLWAIT(B_UNPACK, C_TRISC_CFG | C_SRCA_CLR)': ('STALLWAIT', dict(stall_res=8, wait_res=1024 | 32)),
  'SEMINIT(2, 0, 32)': ('SEMINIT', dict(max_value=2, init_value=0, sem_sel=32)),
  'SEMPOST(2)': ('SEMPOST', dict(sem_sel=2)), 'SEMGET(32)': ('SEMGET', dict(sem_sel=32)),
  'RMWCIB(2, 0x40, 0x40, 71)': ('RMWCIB2', dict(Mask=0x40, Data=0x40, CfgRegAddr=71)),
  'RMWCIB(0, 0x07, 0, 1)': ('RMWCIB0', dict(Mask=7, Data=0, CfgRegAddr=1)),
  'WRCFG(4, 0, 76)': ('WRCFG', dict(GprAddress=4, wr128b=0, CfgReg=76)),
  'MOP1': ('MOP', dict(mop_type=1)),
  'SETRWC(3, 0, 0, 0, 0, 3)': ('SETRWC', dict(clear_ab_vld=3, BitMask=3)),
  'SETRWC(2, 2, 0, 0, 0, 2)': ('SETRWC', dict(clear_ab_vld=2, rwc_cr=2, BitMask=2)),
  'MOVA2D(0, 0, 2, 2, 0)': ('MOVA2D', dict(addr_mode=2, instr_mod=2)),
  'MOVB2D(0, 0, 2, 4, 0)': ('MOVB2D', dict(addr_mode=2, movb2d_instr_mod=4)),
  'ELWMUL(3, 0, 0, 3, 0)': ('ELWMUL', dict(clear_dvalid=3, addr_mode=3)),
  'MVMUL(3, 0, 0, 0)': ('MVMUL', dict(clear_dvalid=3)),
  'T_PACR(0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1)': ('PACR', dict(AddrMode=1, Last=1)),
  'T_PACR(0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0)': ('PACR', dict(AddrMode=2)),
  'SETC16(5, 4)': ('SETC16', dict(setc16_reg=5, setc16_value=4)),
  'TT_NOP': ('NOP', {}),
}


def check_encodings():
  """Compile unpack.h for the host and compare each macro with ttrv.isa. Also cross-checks llama words."""
  sys.path.insert(0, str(HERE.parents[1]))
  from ttrv import isa
  # probe.h / hw.h hold RISC-V asm: stand in for them so only unpack.h's own code is compiled for the host
  prelude = ('#define PROBE_H\n#include <stdio.h>\ntypedef unsigned u32;\ntypedef unsigned char u8;\n'
             '#define INLINE static inline\n#define TENSIX_CFG 0xFFEF0000u\n#define REGFILE 0xFFE00000u\n'
             '#define BUDGET 1u\n#define RES_SITE 0u\n#define SETC16(i, v) (0xB2000000u | (i) << 16 | (v))\n'
             'static u32 read32(u32 a){return a;}\nstatic void write32(u32 a, u32 v){(void)a;(void)v;}\n'
             'static void tensix_push(u32 w){(void)w;}\nstatic u32 now(void){return 0;}\n'
             'static void probe_fail(u32 s){(void)s;}\n#define WAIT_UNTIL(c, s) do {} while (0)\n')
  src = prelude + '#include "unpack.h"\nint main(void){\n' + ''.join(
    f'printf("%u\\n", (unsigned)({e}));\n' for e in ENC) + 'return 0;}\n'
  root = HERE.parents[1]
  with tempfile.TemporaryDirectory() as d:
    (Path(d) / 'c.c').write_text(src)
    subprocess.run(['cc', '-std=gnu11', '-w', f'-I{HERE}', '-o', f'{d}/c', f'{d}/c.c'], check=True)
    got = [int(x) for x in subprocess.run([f'{d}/c'], capture_output=True, text=True, check=True).stdout.split()]
  bad = [(e, hex(g), hex(isa.tensix(n, **f))) for (e, (n, f)), g in zip(ENC.items(), got) if g != isa.tensix(n, **f)]
  # words seen in the exported llama kernels
  assert isa.tensix('UNPACR', Unpack_block_selection=0, AddrMode=1, OvrdThreadId=1, SetDatValid=1, Last=1) == 0x420080c1
  assert isa.tensix('UNPACR_NOP', Unpacker_Select=1, Set_Dvalid=1, Unpack_Pop=1) == 0x43800101
  return bad


def check_models():
  """Reference models against hand-worked values."""
  assert bfp_to_bf16('bfp8', 0x40, 127) == 0x3F80          # 0.5 * 2 = 1.0 (mag 0x80 -> hidden bit at top)
  assert bfp_to_bf16('bfp8', 0xC0, 127) == 0xBF80
  assert bfp_to_bf16('bfp4', 0x4, 127) == 0x3F80
  assert int(e4m3_to_f32(np.array([0x38], np.uint8))[0]) == 0x3F800000  # e4m3 1.0
  assert int(e4m3_to_f32(np.array([0x7E], np.uint8))[0]) == struct.unpack('<I', struct.pack('<f', 448.0))[0]
  for f in FMT:
    d, e = make_data(f, 1024, 1)
    assert len(d) == block_bytes(f, 1024) and len(e) == 1024, f


def check_all():
  from tile import build
  bad = check_encodings()
  check_models()
  tag = dict(UNPACK_TAG=f'0x{_hdr_tag()[:8]}')
  sizes = {}
  for m in MODE: sizes[f'k_unpack MODE={m}'] = len(build('k_unpack.c', 'trisc0', MODE=MODE[m], **tag))
  for m in MATH: sizes[f'k_unpack_math MATH={m}'] = len(build('k_unpack_math.c', 'trisc1', MATH=MATH[m], **tag))
  for m, v in (('verify', 1), ('loop', 2)): sizes[f'k_unpack_pack PACK={m}'] = len(build('k_unpack_pack.c', 'trisc2', PACK=v, **tag))
  for r in ('brisc', 'ncrisc'): sizes[f'k_unpack_noc {r}'] = len(build('k_unpack_noc.c', r, **tag))
  for c in CASES: plan(c)
  return bad, sizes


if __name__ == '__main__':
  sys.path.insert(0, str(HERE))
  if '--check' in sys.argv:
    bad, sizes = check_all()
    for k, v in sizes.items(): print(f'{k:32s} {v:5d} B')
    print(f'{len(CASES)} cases; encodings: {"OK" if not bad else bad}')
    sys.exit(1 if bad else 0)
