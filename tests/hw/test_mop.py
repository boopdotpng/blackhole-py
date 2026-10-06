"""Hardware probe: MOP expander template semantics (config.MopLoop / config.MopMask).

Every MOP slot holds an ADDDMAREG that adds 1 to its own TDMA GPR, so the GPRs count how often each slot ran.
Run from blackhole-py, see test_contexts.py.
"""
import sys, pathlib
from struct import unpack
import pytest
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from config import MopLoop, MopMask, Thread

from asm import Asm
from firmware.consts import TensixL1, TensixMMIO
from ttko.isa import Tensix as TT
from tests.movement.unpacker.unpack import Stall, Wait, mop_sync, pc_sync, stall

OUT = TensixL1.DATA_BUFFER_SPACE_BASE
GPR0 = 40  # counters live in TDMA GPRs 40..48 of thread 0
NOP = TT.TTNOP()
MOP_CFG = 0xFFB80000

def inc(i): return TT.TTADDDMAREG(1, GPR0 + i, 1, GPR0 + i)  # gpr[i] += 1

def _kernel(cfg, mop_word, mop_cfg_word=None):
  k = Asm("trisc0")
  for i in range(9): k.write(TensixMMIO.REGFILE_BASE + 4 * (GPR0 + i), 0)
  mop_sync(k)
  for (_, _, addr), (value, _) in cfg.writes().items(): k.write(addr, value)
  if mop_cfg_word is not None: k.emit(mop_cfg_word)
  k.emit(mop_word)
  stall(k, Stall.SYNC, Wait.THCON)
  pc_sync(k)
  v = k.reg()
  for i in range(9):
    k.read(v, TensixMMIO.REGFILE_BASE + 4 * (GPR0 + i)); k.write(OUT + 4 * i, v)
  return {"trisc0": k.lower()}

def _run(bh, cfg, mop_word, mop_cfg_word=None):
  bh.launch(_kernel(cfg, mop_word, mop_cfg_word), l1={OUT: bytes(36)})
  return unpack("<9I", bh.read_l1(bh.core, OUT, 36))

def model_template1(words):
  """MOPExpander.md ExpandTemplate1 (Blackhole), returning how often each word index is emitted."""
  outer, inner, start, end0, end1, loop, loop1, last0, last1 = words
  counts = [0] * 9
  inner &= 1023; outer &= 1023
  flip = loop1 != NOP
  if flip: inner *= 2
  op = 5
  for j in range(outer):
    if start != NOP: counts[2] += 1
    for i in range(inner):
      counts[op if i != inner - 1 else 8 if j != outer - 1 else 7] += 1
      if flip: op = 11 - op  # 5 <-> 6
    if end0 != NOP:
      counts[3] += 1
      if end1 != NOP: counts[4] += 1
  return counts

def model_template0(words, mask, count1):
  _, flags, b, a0, a1, a2, a3, skip_a0, skip_b = words
  counts = [0] * 9
  for _ in range(count1 + 1):
    if mask & 1 == 0:
      counts[3] += 1
      if flags & 2: counts[4] += 1; counts[5] += 1; counts[6] += 1
      if flags & 1: counts[2] += 1
    else:
      counts[7] += 1
      if flags & 1: counts[8] += 1
    mask >>= 1
  return counts

def slot_counts(words, counts):
  """Map 'word index ran n times' onto the GPR each word increments."""
  out = [0] * 9
  for w, n in zip(words, counts):
    if w != NOP and n: out[(int(w) >> 12 & 0x7FF) - GPR0] += n
  return tuple(out)

@pytest.mark.parametrize("alt", [False, True])
def test_loop_template(bh, alt):
  cfg = MopLoop(thread=Thread.UNPACK, outer_count=3, inner_count=4, start=inc(0), end_0=inc(1), end_1=inc(2),
                body=inc(3), body_alt=inc(4) if alt else NOP, last_body=inc(5), outer_last_body=inc(6))
  w = {k[2]: v for k, (v, _) in cfg.writes().items()}
  words = [w[MOP_CFG + 4 * i] for i in range(9)]
  got = _run(bh, cfg, TT.TTMOP(1, 0, 0))
  want = slot_counts(words, model_template1(words))
  print("loop", "alt" if alt else "plain", "hw", got[:7], "model", want[:7])
  assert got == want

@pytest.mark.parametrize("has_b,has_a123", [(0, 0), (1, 0), (0, 1), (1, 1)])
def test_mask_template(bh, has_b, has_a123):
  mask, count = 0b100101, 6  # LSB first: skip, run, skip, run, run, skip
  cfg = MopMask(thread=Thread.UNPACK, has_b=bool(has_b), has_a123=bool(has_a123), b=inc(0), a0=inc(1), a1=inc(2), a2=inc(3),
                a3=inc(4), skip_a0=inc(5), skip_b=inc(6))
  w = {k[2]: v for k, (v, _) in cfg.writes().items()}
  words = [w.get(MOP_CFG + 4 * i, 0) for i in range(9)]
  got = _run(bh, cfg, TT.TTMOP(0, count - 1, mask & 0xFFFF), TT.TTMOP_CFG(mask >> 16))
  want = slot_counts(words, model_template0(words, mask, count - 1))
  print("mask", has_b, has_a123, "hw", got[:7], "model", want[:7])
  assert got == want
