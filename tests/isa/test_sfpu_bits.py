"""Bit-exact hardware oracles from the ISA functional models.

Integer results travel as two normal FP32 mantissas, so unpack/pack conversion
cannot hide integer, NaN-payload, signed-zero, or denormal differences.
"""
from struct import unpack

import pytest

from asm import Asm
from ttko.isa import Tensix as TT
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, Stall, Wait, _set_thread_cfg, configure_fp32_dst, pc_sync,
  publish_dst, stall,
)

OUTPUT = 0x60000
MASK32 = 0xffffffff
VALUES = (0, 1, 0x7fffff, 0x800000, 0x3f800000, 0x7fffffff,
          0x80000000, 0xffffffff, 0x7f800000, 0xff800000,
          0x7fc12345, 0xffc12345)


def imm(a, reg, value):
  a.emit(TT.TTSFPLOADI(reg, 0, (value >> 16) & 0xffff))
  a.emit(TT.TTSFPLOADI(reg, 10, value & 0xffff))


def oracle(op, mode, immediate, c, b, flag):
  """Return (raw uint32 result, lane flag); independent of assembler encoding."""
  result = c
  if op == 'SFPABS':
    result = (c & 0x7fffffff if c <= 0xff800000 else c) if mode else (-c if c >> 31 else c)
  elif op == 'SFPAND': result = (0xa55a1234 if mode & 1 else b) & c
  elif op == 'SFPOR': result = (0xa55a1234 if mode & 1 else b) | c
  elif op == 'SFPXOR': result = b ^ c
  elif op == 'SFPNOT': result = ~c
  elif op == 'SFPMOV': result = c ^ (0x80000000 if mode == 1 else 0)
  elif op == 'SFPSETCC':
    result = b
    if mode & 8: flag = False
    elif mode & 1: flag = bool(immediate)
    else: flag = {0: bool(c >> 31), 2: c != 0, 4: not bool(c >> 31), 6: c == 0}[mode]
  elif op == 'SFPSETSGN': result = (c & 0x7fffffff) | ((immediate if mode & 1 else b >> 31) << 31)
  elif op == 'SFPSETEXP':
    exponent = immediate if mode & 1 else ((b >> 23) & 255 if mode & 2 else b & 255)
    result = (c & 0x807fffff) | (exponent << 23)
  elif op == 'SFPSETMAN': result = (c & 0xff800000) | (immediate << 11 if mode else b & 0x7fffff)
  elif op == 'SFPEXMAN': result = (c & 0x7fffff) | (0 if mode else 1 << 23)
  elif op == 'SFPDIVP2':
    exponent = (c >> 23) & 255
    exponent = ((exponent + immediate) & 255 if exponent != 255 else 255) if mode else immediate
    result = (c & 0x807fffff) | (exponent << 23)
  elif op == 'SFPCAST':
    result = -c if c >> 31 else c
    if mode == 3: result |= c & 0x80000000
  elif op == 'SFPMUL24':
    a = b if mode & 4 and mode & 8 else c
    product = (a & 0x7fffff) * (0xa55a1234 & 0x7fffff)
    result = product >> 23 if mode & 1 else product & 0x7fffff
  elif op == 'SFPEXEXP':
    result = ((c >> 23) & 255) - (0 if mode & 1 else 127)
    if mode & 2: flag = result < 0
    if mode & 8: flag = not flag
  elif op == 'SFPLZ':
    value = c & (0x7fffffff if mode & 4 else MASK32)
    result = 32 - value.bit_length()
    if mode & 2: flag = value != 0
    if mode & 8: flag = not flag
  elif op == 'SFPSHFT':
    shift = immediate if mode else c - (1 << 32 if c >> 31 else 0)
    result = b << (shift & 31) if shift >= 0 else b >> (-shift & 31)
  elif op == 'SFPIADD':
    result = c + immediate if mode & 1 else c - b if mode & 2 else c + b
    result &= MASK32
    if not mode & 4: flag = bool(result >> 31)
    if mode & 8: flag = not flag
  elif op in ('SFPGT', 'SFPLE'):
    # Total ordering of sign-magnitude encodings, including -0 and NaNs.
    key = lambda x: -(x & 0x7fffffff) - 1 if x >> 31 else x
    comparison = key(b) > key(c)
    if op == 'SFPLE': comparison = not comparison
    result = (MASK32 if comparison else 0) if mode & 8 else b
    if mode & 1: flag = comparison
  elif op == 'SFPLOADI':
    if mode == 0: result = immediate << 16
    elif mode == 1:
      result = ((immediate >> 15) << 31) | ((((immediate >> 10) & 31) + 112) << 23) | ((immediate & 1023) << 13)
    elif mode == 2: result = immediate
    elif mode == 4: result = immediate - (65536 if immediate & 32768 else 0)
    elif mode == 8: result = (b & 65535) | (immediate << 16)
    elif mode == 10: result = (b & 0xffff0000) | immediate
  else: raise AssertionError(op)
  return result & MASK32, flag


CASES = []
def cases(op, modes, immediates=(0,)):
  CASES.extend(pytest.param(op, m, i, id=f'{op}-mod{m}-imm{i}') for m in modes for i in immediates)

cases('SFPABS', (0, 1))
for op in ('SFPAND', 'SFPOR', 'SFPXOR', 'SFPNOT'): cases(op, (0,))
for op in ('SFPAND', 'SFPOR'): cases(op, (1,), (2,))
for op in ('SFPGT', 'SFPLE'): cases(op, (0, 1, 8, 9))
cases('SFPMOV', (0, 1, 2))
cases('SFPSETCC', range(16), (0, 1))
cases('SFPSETSGN', (0,))
cases('SFPSETSGN', (1,), (0, 1))
cases('SFPSETEXP', (0, 2))
cases('SFPSETEXP', (1, 3), (0, 127, 255))
cases('SFPSETMAN', (0,))
cases('SFPSETMAN', (1,), (0, 1, 2048, 4095))
cases('SFPEXMAN', (0, 1))
cases('SFPDIVP2', (0, 1), (0, 1, 127, 128, 255))
cases('SFPCAST', (2, 3))
cases('SFPMUL24', (0, 1, 4, 5, 8, 9, 12, 13))
cases('SFPEXEXP', (0, 1, 2, 3, 8, 9, 10, 11))
cases('SFPLZ', (0, 2, 4, 6, 8, 10, 12, 14))
cases('SFPSHFT', (0,))
cases('SFPSHFT', (1,), (-2048, -33, -32, -31, -1, 0, 1, 31, 32, 33, 2047))
cases('SFPIADD', (0, 2, 4, 6, 8, 10, 12, 14))
cases('SFPIADD', (1, 3, 5, 7, 9, 11, 13, 15), (-2048, -1, 0, 2047))
cases('SFPLOADI', (0, 1, 2, 4, 8, 10), (0, 1, 0x7fff, 0x8000, 0xffff))


# Masking and register aliasing are orthogonal to each operation's datapath:
# cross them fully for the integer add cases, and run every other case once.
BIT_CASES = [pytest.param(*case.values, alias, mask, id=f'{case.id}-{"alias" if alias else "distinct"}-{mask}')
             for case in CASES for alias in (False, True) for mask in ('all', 'none', 'upper16')
             if case.values[0] == 'SFPIADD' or (not alias and mask == 'all')]


@pytest.mark.parametrize('op,mode,immediate,alias,mask', BIT_CASES)
def test_sfpu_bits(bh, op, mode, immediate, alias, mask):
  math, packer = Asm('trisc1'), Asm('trisc2')
  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(math, Stall.SYNC, Wait.MATH)
  configure_fp32_dst(math, 0)
  for register in (12, 28, 47): _set_thread_cfg(math, register, 0)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  dest = 0 if alias else 1
  expected = []
  for index, c in enumerate(VALUES):
    b = c if alias else VALUES[(index + 5) % len(VALUES)]
    result_words, flags = [], []
    for element in range(128):
      enabled = mask == 'all' or mask == 'upper16' and (element % 64) // 2 >= 16
      result, flag = oracle(op, mode, immediate, c, b, enabled) if enabled else (b, enabled)
      if op == 'SFPMOV' and mode == 2: result = c
      result_words.append(result)
      flags.append(int(flag))
    # Three adjacent 128-element slots: low half, high half, observed flags.
    expected.extend([0x3f800000 | (x & 65535) for x in result_words])
    expected.extend([0x3f800000 | (x >> 16) for x in result_words])
    expected.extend([0x3f800000 | x for x in flags])
    for position in range(4):
      math.emit(TT.TTSFPENCC(0, 0, 0, 2))
      imm(math, 0, c)
      if not alias: imm(math, dest, b)
      imm(math, 2, 0xa55a1234)
      if op == 'SFPMUL24': imm(math, 7, dest if mode & 8 else 0)
      imm(math, 4, 0)
      math.emit(TT.TTSFPENCC(1 if mask == 'none' else 3, 0, 0, 10))
      if mask == 'upper16': math.emit(TT.TTSFPIADD((-32) & 4095, 15, 5, 9))
      if op == 'SFPLOADI': math.emit(TT.TTSFPLOADI(dest, mode, immediate))
      elif op == 'SFPCAST': math.emit(TT.TTSFPCAST(0, dest, mode))
      elif op == 'SFPMUL24': math.emit(TT.TTSFPMUL24(3 if mode & 4 else 0, 2, 9, 3 if mode & 8 else dest, mode))
      else: math.emit(getattr(TT, 'TT' + op)(immediate & 4095, 0, dest, mode))
      # Observe condition flags before disabling predication for transport.
      math.emit(TT.TTSFPLOADI(4, 2, 1))
      math.emit(TT.TTSFPENCC(0, 0, 0, 2))
      imm(math, 5, 65535)
      imm(math, 7, 0x3f800000)
      for half in range(2):
        math.emit(TT.TTSFPMOV(0, dest, 6, 0))
        if half: math.emit(TT.TTSFPSHFT((-16) & 4095, 0, 6, 1))
        math.emit(TT.TTSFPAND(0, 5, 6, 0))
        math.emit(TT.TTSFPOR(0, 7, 6, 0))
        math.emit(TT.TTSFPSTORE(6, 3, 0, index * 24 + half * 8 + position * 2))
      math.emit(TT.TTSFPOR(0, 7, 4, 0))
      math.emit(TT.TTSFPSTORE(4, 3, 0, index * 24 + 16 + position * 2))
  stall(math, Stall.SYNC, Wait.SFPU)
  pc_sync(math)
  publish_dst(math)
  count = packer.reg()
  count_value = len(expected) + 128
  packer.li(count, count_value)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=F32)
  size = count_value * 4
  bh.launch({k.role: k.lower() for k in (math, packer)}, l1={OUTPUT: b'\xa5' * (size + 64)})
  actual = unpack(f'<{count_value}I', bh.read_l1(bh.core, OUTPUT, size))
  expected.extend([0] * 128)
  for offset, (got, want) in enumerate(zip(actual, expected, strict=True)):
    assert got == want, f'{op} mode={mode} imm={immediate} word={offset}: {got:#010x} != {want:#010x}'
  assert bh.read_l1(bh.core, OUTPUT + size, 64) == b'\xa5' * 64
