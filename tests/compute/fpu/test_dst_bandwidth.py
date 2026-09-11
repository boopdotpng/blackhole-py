"""Dst payload throughput, not a measurement of physical bus width.

Card 1: pytest -q -s this_file --bh-hardware --bh-device=1 --bh-core=2
Each timed iteration replays 32 instructions. Setup and result packing are
outside the interval; completion is drained inside it. Tile sweep holds the
number of operations fixed, spreading the addresses across 1/2/4 tiles.
"""
from statistics import median

import numpy as np
import pytest

from asm import Asm
from isa import R, Tensix as TT
from tests.profiler import Profiler
from tests.compute.fpu import test_rmsnorm_llama3 as rms
from tests.compute.fpu.test_rmsnorm_reduce import _constant, _read_intervals, _bf16_round, _from_bf16
from tests.movement.unpacker.unpack import (
  CFG_BASE, Stall, Wait, configure_fp32_dst, configure_unpack_pair,
  configure_mop, _mop_loop_words, _unpacr, _set_thread_cfg, _rmw_cfg_byte,
  load_replay, run_mop, stall, pc_sync, publish_dst,
  sem_get, Sem,
)

READY = rms.SCALE + 20000


def _repeat(k, words, repeats):
  load_replay(k, 0, words)
  play = TT.TTREPLAY(0, len(words), 0, 0)
  configure_mop(k, _mop_loop_words(1, repeats, loop=play, last=play, outer_last=play))


def _images(role, op, tiles, repeats):
  kernels = {role: Asm(role) for role in ('trisc0', 'trisc1', 'trisc2')}
  u, w, p = kernels['trisc0'], kernels[role], kernels['trisc2']
  configure_unpack_pair(u, rms.INPUT, rms.GAMMA)
  u.emit(TT.TTSETADCXX(3, 1023, 0))
  configure_mop(u, _mop_loop_words(1, 1, start=_unpacr(0), loop=_unpacr(1),
                                  last=_unpacr(1), outer_last=_unpacr(1)))
  run_mop(u)
  stall(u, Stall.SYNC, Wait.UNPACK0 | Wait.UNPACK1)
  sem_get(u, Sem.UNPACK_SYNC)
  pc_sync(u)
  if u is not w:
    u.write(READY, 1)
    u.fence()
    w.wait(READY, 1, bytes=4)
  configure_fp32_dst(w, 0)
  _rmw_cfg_byte(w, CFG_BASE + 4, 3, 0x40, 0x40)
  for register in (15, 31, 50):
    _set_thread_cfg(w, register, 0)
  w.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xf))
  w.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(w, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
  for tile in range(4):
    for row in range(0, 64, 8):
      w.emit(TT.TTMOVA2D(0, row, 3, 2, tile*64+row))
  stall(w, Stall.SFPU, Wait.MATH)
  w.emit(TT.TTSFPENCC(0, 0, 0, 2))
  w.emit(TT.TTSFPCONFIG(0, 15, 1))
  _constant(w, 0, 2)
  words = []
  for j in range(32):
    tile = j % tiles
    row = 2*(j // tiles)
    if op == 'load':
      words.append(TT.TTSFPLOAD(j % 4, 3, 3, tile*64+row))
    elif op == 'store':
      words.append(TT.TTSFPSTORE(0, 3, 3, tile*64+row))
    elif op == 'mova':
      row = 8*((j // tiles) % 8)
      words.append(TT.TTMOVA2D(0, row, 3, 2, tile*64+row))
    else:
      raise ValueError(op)
  _repeat(w, words, repeats)
  stall(w, Stall.SYNC, Wait.MATH | Wait.SFPU)
  pc_sync(w)
  profile = Profiler(w)
  profile.record('body')
  run_mop(w)
  stall(w, Stall.SYNC, Wait.MATH | Wait.SFPU)
  pc_sync(w)
  profile.record('body')
  w.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xf))
  if op == 'load':
    # ZEROACC invalidates Dst; a partial SFPU store does not clear the
    # untouched lanes of its row. Initialize the other vector explicitly.
    _constant(w, 6, 0)
    w.emit(TT.TTSFPSTORE(6, 3, 3, 258))
    w.emit(TT.TTSFPSTORE(0, 3, 3, 256))
  publish_dst(w)
  rms._pack_output(p, 1, 4 if op == 'load' else 0)
  profile._validate()
  return {role: k.lower() for role, k in kernels.items()}, profile


@pytest.mark.parametrize('role', ('trisc0', 'trisc1', 'trisc2'))
@pytest.mark.parametrize('op', ('mova', 'load', 'store'))
@pytest.mark.parametrize('tiles', (1, 2, 4))
def test_dst_payload_throughput(bh, role, op, tiles):
  xb = _bf16_round(np.arange(1024)/1024 + 1)
  x = _from_bf16(xb)
  points = []
  for repeats in (32, 128, 256):
    images, profile = _images(role, op, tiles, repeats)
    samples = []
    for sample in range(8):
      bh.launch(images, l1={rms.INPUT: xb.tobytes(), rms.GAMMA: xb.tobytes(),
                           READY: bytes(32), rms.OUTPUT: b'\xa5'*2112})
      y = _from_bf16(np.frombuffer(bh.read_l1(bh.core, rms.OUTPUT, 2048), dtype='<u2'))
      if op == 'load':
        # Last load into L0 is instruction 28; preserve that vector after timing.
        row = 2*(28 // tiles)
        start = (row & ~3)*16 + bool(row & 2)
        np.testing.assert_array_equal(y[:64:2], x[start:start+64:2])
        np.testing.assert_array_equal(y[1:64:2], 0)
      elif op == 'store':
        expected = x.copy()
        expected[:1024//tiles] = 2
        np.testing.assert_array_equal(y, expected)
      else:
        np.testing.assert_array_equal(y, x)
      assert bh.read_l1(bh.core, rms.OUTPUT+2048, 64) == b'\xa5'*64
      if sample:
        samples.append(_read_intervals(bh, profile.l1_address, ('body',))['body'])
    points.append(median(samples))
  slopes = [(b-a)/(32*(rb-ra)) for a,b,ra,rb in
            zip(points, points[1:], (32,128), (128,256))]
  payload = 512 if op == 'mova' else 128
  print(f'{role} {op} tiles={tiles}: cycles={points}; cycles/op={slopes}; '
        f'FP32-Dst payload bytes/cycle={[payload/s for s in slopes]}')


def _contention_images(schedule, fpu_op, sfpu_op, advance, repeats, *, batch_size=None):
  u, f, s = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  # Unpack once, preserve x in Dst0, write independent FPU results to Dst1.
  rms._unpack_reused(u, 0)
  from tests.compute.fpu.test_rmsnorm_reduce import _await_sources
  configure_fp32_dst(f, 0)
  _rmw_cfg_byte(f, CFG_BASE+4, 3, 0x40, 0x40)
  f.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  _await_sources(f)
  for register in (12, 15, 28, 31, 47, 50):
    _set_thread_cfg(f, register, 8 if advance and register == 12 else 0)
  for row in range(0, 64, 8):
    f.emit(TT.TTMOVA2D(0, row, 3, 2, row))
  stall(f, Stall.SFPU, Wait.MATH)
  f.emit(TT.TTSFPENCC(0, 0, 0, 2))
  f.emit(TT.TTSFPCONFIG(0, 15, 1))
  _constant(f, 0, 2 if sfpu_op == 'store' else 1)
  _constant(f, 7, 0)
  stall(f, Stall.SYNC, Wait.MATH | Wait.SFPU)
  pc_sync(f)
  fwords, swords = [], []
  width = 32 if batch_size is not None else 16
  for j in range(width):
    row = (j % 8)*8
    if fpu_op == 'mova':
      fwords.append(TT.TTMOVA2D(0, row, 0 if advance else 3, 2, 64+row))
    else:
      # LoFi ones*ones is exact; repeated additions exercise Dst RMW.
      fwords.append(TT.TTELWMUL(0, 0, 0, 0 if advance else 3, 64+row))
    swords.append(TT.TTSFPLOAD(j % 4, 3, 3, j*2) if sfpu_op == 'load' else
                  TT.TTSFPSTORE(0, 3, 3, j*2) if sfpu_op == 'store' else
                  TT.TTSFPMAD(0, 0, 7, 7, 0))
  def loop(k, words):
    counter = k.reg()
    k.li(counter, repeats)
    label = k._new_label('repeat')
    k.label(label)
    for word in words:
      k.emit(word)
    k.addi(counter, counter, -1)
    k.bne(counter, R.ZERO, label)
  profile = Profiler(f)
  if schedule == 'split':
    for register in (0, 1, 15, 31, 50):
      _set_thread_cfg(s, register, 0)
    s.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xf))
    pc_sync(s)
    s.write(READY+16, 1)
    s.fence()
    f.wait(READY+16, 1, bytes=4)
  profile.record('work')
  if schedule == 'split':
    f.write(READY, 1)
    f.fence()
    s.wait(READY, 1, bytes=4)
    loop(s, swords)
    stall(s, Stall.SYNC, Wait.SFPU)
    pc_sync(s)
    s.write(READY+32, 1)
    s.fence()
    loop(f, fwords)
  elif schedule == 'interleaved':
    loop(f, [word for pair in zip(fwords, swords) for word in pair])
  elif schedule == 'grouped':
    if batch_size not in (1, 2, 4, 8, 16, 32):
      raise ValueError(batch_size)
    words = []
    for start in range(0, width, batch_size):
      words.extend(fwords[start:start+batch_size])
      words.extend(swords[start:start+batch_size])
    loop(f, words)
  elif schedule == 'batched':
    loop(f, fwords)
    loop(f, swords)
  elif schedule == 'fpu':
    loop(f, fwords)
  elif schedule == 'sfpu':
    loop(f, swords)
  else:
    raise ValueError(schedule)
  stall(f, Stall.SYNC, Wait.MATH | Wait.SFPU)
  pc_sync(f)
  if schedule == 'split':
    f.wait(READY+32, 1, bytes=4)
  profile.record('work')
  if sfpu_op in ('load', 'mad') and schedule != 'fpu':
    f.emit(TT.TTSFPSTORE(7 if sfpu_op == 'mad' else 0, 3, 3, 256))
  f.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xf))
  publish_dst(f)
  # Pack all five tiles for independent movement/arithmetic checks.
  rms._pack_output(s, 5, 0)
  profile._validate()
  return {k.role: k.lower() for k in (u, f, s)}, profile


@pytest.mark.parametrize('fpu_op', ('mova', 'elwmul'))
@pytest.mark.parametrize('sfpu_op', ('load', 'store', 'mad'))
@pytest.mark.parametrize('advance', (False, True), ids=('stationary', 'increment'))
def test_dst_contention(bh, fpu_op, sfpu_op, advance):
  xb = _bf16_round(np.ones(1024))
  for schedule in ('fpu', 'sfpu', 'batched', 'interleaved', 'split'):
    points = []
    for repeats in (32, 128, 256):
      images, profile = _contention_images(schedule, fpu_op, sfpu_op, advance, repeats)
      samples = []
      for sample in range(6):
        bh.launch(images, l1={rms.INPUT: xb.tobytes(), rms.GAMMA: xb.tobytes(),
                             READY: bytes(64), rms.OUTPUT: b'\xa5'*(10240+64)})
        y = _from_bf16(np.frombuffer(bh.read_l1(bh.core, rms.OUTPUT, 10240), dtype='<u2'))
        np.testing.assert_array_equal(y[:512], 2 if sfpu_op == 'store' and schedule != 'fpu' else 1)
        np.testing.assert_array_equal(y[512:1024], 1)
        expected = 0 if schedule == 'sfpu' else 1 if fpu_op == 'mova' else 2*repeats
        np.testing.assert_array_equal(y[1024:2048], expected)
        if sfpu_op in ('load', 'mad') and schedule != 'fpu':
          np.testing.assert_array_equal(y[4096:4160:2], 1 if sfpu_op == 'load' else 16*repeats)
        assert bh.read_l1(bh.core, rms.OUTPUT+10240, 64) == b'\xa5'*64
        if sample:
          samples.append(_read_intervals(bh, profile.l1_address, ('work',))['work'])
      points.append(median(samples))
    slopes = [(b-a)/(16*(rb-ra)) for a,b,ra,rb in
              zip(points, points[1:], (32,128), (128,256))]
    print(f'{fpu_op}+{sfpu_op} advance={advance} {schedule}: cycles={points}; '
          f'cycles/pair-or-single={slopes}')


def test_dst_switch_frequency(bh):
  """Same 32 FPU + 32 load instructions/iteration, different grouping only.

  Counters stay stationary; addresses use immediate offsets. FPU writes Dst1,
  SFPU reads Dst0. The grouped loop has identical size/control at every batch
  size. The fully batched control uses two loops, with only one engine switch.
  """
  groups = (1, 2, 4, 8, 16, 32, 'all')
  counts = (32, 128, 256)
  xb = _bf16_round(np.ones(1024))
  points = {group: [] for group in groups}
  for repeats in counts:
    variants = {group: _contention_images(
      'batched' if group == 'all' else 'grouped', 'elwmul', 'load', False,
      repeats, batch_size=32 if group == 'all' else group) for group in groups}
    samples = {group: [] for group in groups}
    for sample in range(22):
      for group in groups[::1 if sample % 2 == 0 else -1]:
        images, profile = variants[group]
        bh.launch(images, l1={rms.INPUT: xb.tobytes(), rms.GAMMA: xb.tobytes(),
                             READY: bytes(64), rms.OUTPUT: b'\xa5'*(10240+64)})
        y = _from_bf16(np.frombuffer(bh.read_l1(bh.core, rms.OUTPUT, 10240), dtype='<u2'))
        np.testing.assert_array_equal(y[:1024], 1)
        np.testing.assert_array_equal(y[1024:2048], 4*repeats)
        np.testing.assert_array_equal(y[4096:4160:2], 1)
        np.testing.assert_array_equal(y[4097:4160:2], 0)
        assert bh.read_l1(bh.core, rms.OUTPUT+10240, 64) == b'\xa5'*64
        if sample >= 2:
          samples[group].append(_read_intervals(bh, profile.l1_address, ('work',))['work'])
    for group in groups:
      points[group].append(median(samples[group]))
  slopes = {group: [(b-a)/(32*(rb-ra)) for a,b,ra,rb in
                    zip(values, values[1:], counts, counts[1:])]
            for group, values in points.items()}
  for group in groups:
    overhead = ([((s-base)*group/2) for s,base in zip(slopes[group], slopes['all'])]
                if group != 'all' else [])
    print(f'switch batch={group}: cycles={points[group]}; cycles/pair={slopes[group]}; '
          f'excess cycles/switch={overhead}')
