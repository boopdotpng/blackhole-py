"""All Blackhole push/pop modifiers and conditional-stack truth tables.

Includes depth-eight peek/mutate behavior fixed relative to Wormhole. Undefined
push overflow and ordinary pop underflow are deliberately excluded.
"""
from itertools import product
from struct import unpack

import pytest

from asm import Asm
from ttko.isa import Tensix as TT
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, Stall, Wait, _set_thread_cfg, configure_fp32_dst, pc_sync, publish_dst, stall,
)

OUTPUT = 0x60000
STATES = list(product((False, True), repeat=2))  # use flags, flag value


def boolean(mode, a, b):
  return (None, b, not b, a and b, a or b, a and not b, a or not b,
          not a and b, not a or b, not a and not b, not a or not b, a != b, a == b)[mode]


def model(op, mode, current, stack):
  use, flag = current
  if op == 'SFPENCC':
    immediate, modifier = mode
    if modifier & 2: use = bool(immediate & 1)
    elif modifier & 1: use = not use
    flag = bool(immediate & 2) if modifier & 8 else True
  elif op == 'SFPPUSHC':
    if mode == 0: stack.append(current)
    else:
      if mode <= 12: top = (use, boolean(mode, stack[-1][1], flag))
      elif mode == 13:
        flag = not flag
        top = (use, flag)
      else: top = (True, mode == 14)
      stack[-1] = top
  elif op == 'SFPPOPC':
    top_use, top_flag = stack[-1] if stack else (False, False)
    if mode == 0:
      use, flag = stack.pop()
    elif mode <= 12: use, flag = top_use, boolean(mode, flag, top_flag)
    elif mode == 13: flag = not flag
    else: use, flag = True, mode == 14
  elif op == 'SFPCOMPC':
    top_use, top_flag = stack[-1] if stack else (True, True)
    flag = top_flag and not flag if use and top_use else False
  elif op in ('SFPGT', 'SFPLE'):
    modifier, comparison = mode
    if op == 'SFPLE': comparison = not comparison
    if (not use or flag) and modifier & 1: flag = comparison
    if stack and modifier & 2:
      top_use, top_flag = stack[-1]
      stack[-1] = (top_use, top_flag or comparison if modifier & 4 else top_flag and comparison)
  else: raise AssertionError(op)
  return bool(use), bool(flag)


CASES = [(op, mode, depth) for op in ('SFPPUSHC', 'SFPPOPC') for mode in range(16)
         for depth in (0, 1, 7, 8)
         if not (op == 'SFPPUSHC' and (depth == 8 and mode == 0 or depth == 0 and mode != 0))
         and not (op == 'SFPPOPC' and depth == 0 and mode == 0)]
CASES += [('SFPCOMPC', 0, depth) for depth in (0, 1, 7, 8)]
CASES += [('SFPENCC', (imm, mod), 0) for imm in range(4) for mod in (0, 1, 2, 3, 8, 9, 10, 11)]
CASES += [(op, (mod, comparison), depth) for op in ('SFPGT', 'SFPLE')
          for mod in range(16) for comparison in (False, True) for depth in (0, 1, 8)]


# SFPENCC never touches the stack, so its saved top state is not varied.
STACK_CASES = [(*case, current, top) for case in CASES for current, top in product(STATES, repeat=2)
               if case[0] != 'SFPENCC' or top == STATES[0]]


@pytest.mark.parametrize('op,mode,depth,current,top', STACK_CASES)
def test_predicate_stack(bh, op, mode, depth, current, top):
  a, p = Asm('trisc1'), Asm('trisc2')
  a.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(a, Stall.SYNC, Wait.MATH)
  configure_fp32_dst(a, 0)
  for register in (12, 28, 47): _set_thread_cfg(a, register, 0)
  a.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  expected = []

  def set_state(state):
    a.emit(TT.TTSFPENCC(int(state[0]) + 2 * int(state[1]), 0, 0, 10))

  # Capture the actual post-instruction state before any reinitialization.
  # Each position reruns the full scenario so all 32 lanes are independently read.
  stack = [(bool(i & 1), bool(i & 2)) for i in range(depth)]
  if stack: stack[-1] = top
  after_stack = stack.copy()
  after = model(op, mode, current, after_stack)
  states = [after] + list(reversed(after_stack))
  for position in range(4):
    for state in stack:
      set_state(state)
      a.emit(TT.TTSFPPUSHC(0, 0, 0, 0))
    a.emit(TT.TTSFPENCC(0, 0, 0, 2))
    a.emit(TT.TTSFPLOADI(4, 0, 0x3f80))
    a.emit(TT.TTSFPLOADI(5, 0, 0x3f80))
    if op in ('SFPGT', 'SFPLE'):
      a.emit(TT.TTSFPLOADI(0, 2, 0))
      a.emit(TT.TTSFPLOADI(1, 2, int(mode[1])))
    set_state(current)
    if op == 'SFPENCC': a.emit(TT.TTSFPENCC(mode[0], 0, 0, mode[1]))
    elif op in ('SFPGT', 'SFPLE'): a.emit(getattr(TT, 'TT' + op)(0, 0, 1, mode[0]))
    else: a.emit(getattr(TT, 'TT' + op)(0, 0, 0, mode))
    for index, state in enumerate(states):
      if index:
        a.emit(TT.TTSFPENCC(0, 0, 0, 2))
        a.emit(TT.TTSFPLOADI(4, 0, 0x3f80))
        a.emit(TT.TTSFPLOADI(5, 0, 0x3f80))
        a.emit(TT.TTSFPPOPC(0, 0, 0, 0))
      a.emit(TT.TTSFPLOADI(4, 0, 0x4000))
      a.emit(TT.TTSFPPOPC(0, 0, 0, 13))
      a.emit(TT.TTSFPLOADI(5, 0, 0x4000))
      a.emit(TT.TTSFPENCC(0, 0, 0, 2))
      a.emit(TT.TTSFPSTORE(4, 3, 0, index * 16 + position * 2))
      a.emit(TT.TTSFPSTORE(5, 3, 0, index * 16 + 8 + position * 2))
  for use, flag in states:
    expected.extend([2. if not use or flag else 1.] * 128)
    expected.extend([2. if not use or not flag else 1.] * 128)
  stall(a, Stall.SYNC, Wait.SFPU)
  pc_sync(a)
  publish_dst(a)
  n = p.reg()
  p.li(n, len(expected) + 128)
  emit_pack_dst_to_cb(p, 0, OUTPUT, n, output_format=F32)
  expected.extend([0.] * 128)
  size = len(expected) * 4
  bh.launch({k.role: k.lower() for k in (a, p)}, l1={OUTPUT: b'\xa5' * (size + 64)})
  actual = unpack(f'<{len(expected)}f', bh.read_l1(bh.core, OUTPUT, size))
  assert actual == tuple(expected)
  assert bh.read_l1(bh.core, OUTPUT + size, 64) == b'\xa5' * 64
