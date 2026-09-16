"""Allocation-independent, predicated raw implementations of SFPURegister math.

Inputs/results in explicit LRegs. No Dst or source allocation side effects.
Call drain() before a RISC consumer or timestamp; subsequent SFPU dependencies
are automatically interlocked on Blackhole. L9=0 and L10=1 are architectural.
"""
from math import factorial
from struct import pack, unpack
from ttko.isa import Tensix as TT
from tests.movement.unpacker.unpack import stall, pc_sync, Stall, Wait

OPS = ('add', 'sub', 'mul', 'mad', 'neg', 'abs', 'exp', 'reciprocal')


def constant(k, reg, value):
  bits = unpack('<I', pack('<f', value))[0]
  k.emit(TT.TTSFPLOADI(reg, 8, bits >> 16))
  k.emit(TT.TTSFPLOADI(reg, 10, bits & 65535))


def drain(k):
  stall(k, Stall.SYNC, Wait.SFPU)
  pc_sync(k)


def arithmetic(k, op, dst, other=1, addend=2, *, mode='refined', scratch=(3,4,5,6)):
  """In-place public operation. scratch disjoint from all live input LRegs.

  Basic operations use no scratch. reciprocal native uses none, refined uses
  first 3 scratch; exp native uses first scratch, polynomial uses first 3.
  All instructions respect incoming predication and preserve predicate state.
  """
  if op not in OPS or not 0 <= dst < 8: raise ValueError('invalid operation/destination')
  if not all(0 <= r < 16 for r in (other, addend)): raise ValueError('invalid source')
  if op == 'add': k.emit(TT.TTSFPADD(10, dst, other, dst, 0))
  elif op == 'sub': k.emit(TT.TTSFPADD(10, dst, other, dst, 2))
  elif op == 'mul': k.emit(TT.TTSFPMUL(dst, other, 9, dst, 0))
  elif op == 'mad': k.emit(TT.TTSFPMAD(dst, other, addend, dst, 0))
  elif op == 'neg': k.emit(TT.TTSFPMOV(0, dst, dst, 1))
  elif op == 'abs': k.emit(TT.TTSFPABS(0, dst, dst, 1))
  else:
    if mode not in ('native', 'refined'): raise ValueError('invalid numerical mode')
    if len(scratch) < 3 or len(set(scratch)) != len(scratch) or any(r == dst or not 0 <= r < 8 for r in scratch):
      raise ValueError('scratch must contain distinct writable registers disjoint from dst')
    x, tmp, c = scratch[:3]
    if op == 'reciprocal':
      if mode == 'native': k.emit(TT.TTSFPARECIP(0, dst, dst, 0))
      else:
        k.emit(TT.TTSFPMOV(0, dst, x, 0))
        k.emit(TT.TTSFPARECIP(0, dst, dst, 0))
        constant(k, c, 2.)
        for _ in range(2):
          k.emit(TT.TTSFPMAD(x, dst, c, tmp, 1))  # 2-x*y
          k.emit(TT.TTSFPMUL(dst, tmp, 9, dst, 0))
    elif mode == 'native':
      k.emit(TT.TTSFPMOV(0, dst, x, 0))
      k.emit(TT.TTSFPARECIP(0, dst, dst, 2))
      k.emit(TT.TTSFPARECIP(x, dst, dst, 1))  # negative input => 1/abs(exp(|x|))
    else:
      # exp(x) = exp(x/256)^256. Degree-8 Taylor on [-0.344,0.344].
      k.emit(TT.TTSFPMOV(0, dst, x, 0))
      k.emit(TT.TTSFPMULI(0x3b80, x, 0))
      constant(k, dst, 1/factorial(8))
      for degree in range(7, -1, -1):
        constant(k, c, 1/factorial(degree))
        k.emit(TT.TTSFPMAD(dst, x, c, dst, 0))
      for _ in range(8): k.emit(TT.TTSFPMUL(dst, dst, 9, dst, 0))
