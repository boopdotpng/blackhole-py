"""Scalar GPR behavior specified by Blackhole LLK instructions/assembly.yaml.

Every case checks the result and all 64 GPRs, including source preservation.
"""
from struct import unpack

import pytest

from asm import Asm
from firmware.consts import TensixMMIO
from ttko.isa import Tensix as TT
from tests.movement.unpacker.unpack import pc_sync, stall, Stall, Wait

OUTPUT = 0x60000
MASK32 = 0xffffffff
VALUES = (0, 1, 31, 32, 63, 0xffff, 0x10000, 0x7fffffff, 0x80000000, 0xffffffff)
OPERATIONS = [('ADDDMAREG', 0), ('SUBDMAREG', 0), ('MULDMAREG', 0)]
OPERATIONS += [('BITWOPDMAREG', m) for m in range(3)]
OPERATIONS += [('SHIFTDMAREG', m) for m in range(2)]
OPERATIONS += [('CMPDMAREG', m) for m in range(3)]


def set_gpr(k, index, value):
  for half in range(2):
    word = (value >> (16 * half)) & 65535
    k.emit(TT.TTSETDMAREG(word >> 14, word & 16383, 0, index * 2 + half))


def result(op, mode, a, b):
  if op == 'ADDDMAREG': return (a + b) & MASK32
  if op == 'SUBDMAREG': return (a - b) & MASK32
  if op == 'MULDMAREG': return (a & 65535) * (b & 65535)
  if op == 'BITWOPDMAREG': return (a & b, a | b, a ^ b)[mode]
  if op == 'SHIFTDMAREG': return ((a << (b & 31)) & MASK32) if mode == 0 else a >> (b & 31)
  if op == 'CMPDMAREG': return int((a > b, a < b, a == b)[mode])
  raise AssertionError(op)


# All TRISCs share one scalar ALU: run the full matrix on TRISC1 and one
# smoke case per operation on the other threads.
SCALAR_CASES = [pytest.param(op, mode, imm, regs, alias, role, id=f'{op}-{mode}-{"imm" if imm else "reg"}-{regs[0]}-{alias}-{role}')
                for op, mode in OPERATIONS for imm in (False, True)
                for regs in ((0, 1, 2), (31, 32, 63), (61, 62, 63)) for alias in ('none', 'left', 'right')
                for role in ('trisc0', 'trisc1', 'trisc2')
                if role == 'trisc1' or (not imm and regs == (0, 1, 2) and alias == 'none')]


@pytest.mark.parametrize('op,mode,immediate,registers,alias,role', SCALAR_CASES)
def test_scalar_gpr(bh, op, mode, immediate, registers, alias, role):
  k = Asm(role)
  left, right, dest = registers
  if alias == 'left': dest = left
  if alias == 'right': dest = right
  state = [(0xa5000000 | i * 0x10101) for i in range(64)]
  for index, word in enumerate(state): set_gpr(k, index, word)
  expected = []
  observed = k.reg()
  # Equal operands exercise comparisons; asymmetric operands establish order.
  pairs = [(a, b) for a in VALUES for b in (a, VALUES[(VALUES.index(a) + 3) % len(VALUES)])]
  for a, b in pairs:
    if immediate: b &= 31 if op == 'SHIFTDMAREG' else 63
    set_gpr(k, left, a)
    state[left] = a
    if not immediate:
      set_gpr(k, right, b)
      state[right] = b
    args = [int(immediate)]
    if op in ('BITWOPDMAREG', 'SHIFTDMAREG', 'CMPDMAREG'): args.append(mode)
    args.extend((dest, b if immediate else right, left))
    k.emit(getattr(TT, 'TT' + op)(*args))
    stall(k, Stall.SYNC, Wait.THCON)
    pc_sync(k)
    k.read(observed, TensixMMIO.REGFILE_BASE + dest * 4)
    k.write(OUTPUT + len(expected) * 4, observed)
    state[dest] = result(op, mode, a, b)
    expected.append(state[dest])
  for index in range(64):
    k.read(observed, TensixMMIO.REGFILE_BASE + index * 4)
    k.write(OUTPUT + len(expected) * 4, observed)
    expected.append(state[index])
  size = len(expected) * 4
  bh.launch({role: k.lower()}, l1={OUTPUT: b'\xa5' * (size + 64)})
  actual = unpack(f'<{len(expected)}I', bh.read_l1(bh.core, OUTPUT, size))
  assert actual == tuple(expected)
  assert bh.read_l1(bh.core, OUTPUT + size, 64) == b'\xa5' * 64
