"""REPLAY and MOP expander behavior, observed through scalar GPR counters.

Every replayed / expanded slot is an ADDDMAREG that adds 1 to its own TDMA GPR
(40..48 of the issuing TRISC), so the GPRs count how often each slot ran.

Claims:
- REPLAY load_mode=1 records `len` following instructions into slots
  [start, start+len); with execute_while_loading=0 they do not run, with 1
  they run once while being recorded.
- REPLAY load_mode=0 plays the range back; each playback runs every recorded
  instruction once, in any slot range including the top of the 32-slot buffer.
- MOP template 1 (loop): outer x inner iterations; the final inner iteration of
  a non-final outer pass issues word 8 instead of the loop body, and the final
  inner iteration of the last outer pass issues word 7; a non-NOP word 6
  alternates with word 5 and doubles the inner count; start / end0 / end1 run
  once per outer pass (end1 only when end0 is non-NOP).
- MOP template 0 (mask): count+1 iterations, LSB-first zmask bit 0 -> a0
  (+a1..a3 if flags&2, +b if flags&1), bit 1 -> skip_a0 (+skip_b if flags&1);
  mask bits 16..31 come from MOP_CFG issued immediately before.
- A REPLAY word inside a MOP slot expands to the recorded range.
Ordering rules used (from ../blackhole-py-rewrite/config.py): mop_sync before
writing MOP config; MOP_CFG(mask>>16) immediately before a template-0 MOP.
"""
from struct import unpack

import pytest

from asm import Asm
from firmware.consts import TensixMMIO
from ttko.isa import Tensix as TT
from ttko.mop import LoopTemplate, MaskTemplate, Mop, Replay
from tests.movement.unpacker.unpack import Stall, Wait, pc_sync, stall

OUTPUT = 0x60000
GPR0 = 40
NOP = TT.TTNOP()


def inc(i): return TT.TTADDDMAREG(1, GPR0 + i, 1, GPR0 + i)  # gpr[i] += 1


def run(bh, body):
  k = Asm('trisc0')
  for i in range(9): k.write(TensixMMIO.REGFILE_BASE + 4 * (GPR0 + i), 0)
  pc_sync(k)
  body(k)
  stall(k, Stall.SYNC, Wait.THCON)
  pc_sync(k)
  v = k.reg()
  for i in range(9):
    k.read(v, TensixMMIO.REGFILE_BASE + 4 * (GPR0 + i))
    k.write(OUTPUT + 4 * i, v)
  bh.launch({'trisc0': k.lower()}, l1={OUTPUT: b'\xa5' * 36})
  return unpack('<9I', bh.read_l1(bh.core, OUTPUT, 36))


@pytest.mark.parametrize('start', [0, 29])
@pytest.mark.parametrize('execute', [0, 1])
@pytest.mark.parametrize('plays', [0, 1, 3])
def test_replay(bh, start, execute, plays):
  words = (inc(0), inc(1), inc(1))
  def body(k):
    k.emit(TT.TTREPLAY(start, len(words), execute, 1))
    for w in words: k.emit(w)
    for _ in range(plays): k.emit(TT.TTREPLAY(start, len(words), 0, 0))
  runs = execute + plays
  assert run(bh, body) == (runs, 2 * runs, 0, 0, 0, 0, 0, 0, 0)


def model_loop(words):
  """MOPExpander.md ExpandTemplate1: how often each word index is issued."""
  outer, inner, start, end0, end1, loop, alt, _, _ = words
  counts, op = [0] * 9, 5
  flip = alt != NOP
  inner *= 2 if flip else 1
  for j in range(outer):
    if start != NOP: counts[2] += 1
    for i in range(inner):
      counts[op if i != inner - 1 else 8 if j != outer - 1 else 7] += 1
      if flip: op = 11 - op
    if end0 != NOP:
      counts[3] += 1
      if end1 != NOP: counts[4] += 1
  return counts


def model_mask(words, mask, count):
  _, flags, *_ = words
  counts = [0] * 9
  for _ in range(count):
    if mask & 1 == 0:
      counts[3] += 1
      if flags & 2: counts[4] += 1; counts[5] += 1; counts[6] += 1
      if flags & 1: counts[2] += 1
    else:
      counts[7] += 1
      if flags & 1: counts[8] += 1
    mask >>= 1
  return counts


def per_gpr(words, counts):
  out = [0] * 9
  for w, n in zip(words, counts):
    if type(w) is not int and w != NOP and n: out[(int(w) >> 12 & 0x7ff) - GPR0] += n
  return tuple(out)


@pytest.mark.parametrize('outer,inner', [(1, 1), (3, 4)])
@pytest.mark.parametrize('alt', [False, True])
def test_loop_template(bh, outer, inner, alt):
  t = LoopTemplate(outer, inner, inc(3), start=inc(0), end0=inc(1), end1=inc(2),
                   alternate=inc(4) if alt else NOP, last=inc(5), outer_last=inc(6))
  got = run(bh, lambda k: Mop(k, 0).configure(t).run())
  assert got == per_gpr(t.values(), model_loop(t.values()))


@pytest.mark.parametrize('has_b,has_a123', [(0, 0), (1, 1)])
@pytest.mark.parametrize('mask', [0b100101, 0x10001])
def test_mask_template(bh, has_b, has_a123, mask):
  t = MaskTemplate(inc(1), inc(5), b=inc(0) if has_b else None,
                   a1=inc(2) if has_a123 else None, a2=inc(3) if has_a123 else None,
                   a3=inc(4) if has_a123 else None, skip_b=inc(6) if has_b else None)
  count = 18 if mask >> 16 else 6
  got = run(bh, lambda k: Mop(k, 0).configure(t).run(count, mask))
  assert got == per_gpr(t.values(), model_mask(t.values(), mask, count))


def test_replay_in_mop_slot(bh):
  r = Replay(4, (inc(0), inc(1)))
  t = LoopTemplate(2, 3, r, last=r)
  got = run(bh, lambda k: Mop(k, 0).configure(t).run())
  # 2 outer x 3 inner; word 8 (outer_last) is NOP, so 5 replays of the 2-word range.
  assert got == (5, 5, 0, 0, 0, 0, 0, 0, 0)
