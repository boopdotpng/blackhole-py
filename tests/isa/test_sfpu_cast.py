"""SFPCAST sign-magnitude -> FP32: RNE ties and stochastic neighbor bounds."""
from struct import pack, unpack

import pytest

from asm import Asm
from ttko.isa import Tensix as TT
from tests.isa.test_sfpu_bits import imm
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, Stall, Wait, _set_thread_cfg, configure_fp32_dst, pc_sync, publish_dst, stall,
)

OUTPUT = 0x60000
MAGNITUDES = (0, 1, 2, 0x7fffff, 0xffffff, 0x1000000, 0x1000001,
              0x1000003, 0x1ffffff, 0x2000001, 0x3fffffff, 0x40000001, 0x7fffffff)


def bits(value):
  return unpack('<I', pack('<f', value))[0]


def allowed(magnitude, sign, mode):
  if not mode: return {bits(float(magnitude)) | (sign << 31)}
  shift = max(0, magnitude.bit_length() - 24)
  lower = (magnitude >> shift) << shift
  word = bits(float(lower)) | (sign << 31)
  return {word} if lower == magnitude else {word, word + 1}


@pytest.mark.parametrize('mode', (0, 1), ids=('nearest-even', 'stochastic'))
@pytest.mark.parametrize('sign', (0, 1), ids=('positive', 'negative'))
@pytest.mark.parametrize('alias', (False, True), ids=('distinct', 'alias'))
@pytest.mark.parametrize('mask', ('all', 'none', 'upper16'))
def test_cast_integer_to_float(bh, mode, sign, alias, mask):
  a, p = Asm('trisc1'), Asm('trisc2')
  a.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(a, Stall.SYNC, Wait.MATH)
  configure_fp32_dst(a, 0)
  for register in (12, 28, 47): _set_thread_cfg(a, register, 0)
  a.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 15))
  dest = 0 if alias else 1
  for index, magnitude in enumerate(MAGNITUDES):
    for position in range(4):
      a.emit(TT.TTSFPENCC(0, 0, 0, 2))
      imm(a, 0, magnitude | (sign << 31))
      if not alias: imm(a, 1, 0xa55a1234)
      a.emit(TT.TTSFPENCC(1 if mask == 'none' else 3, 0, 0, 10))
      if mask == 'upper16': a.emit(TT.TTSFPIADD((-32) & 4095, 15, 5, 9))
      a.emit(TT.TTSFPCAST(0, dest, mode))
      a.emit(TT.TTSFPENCC(0, 0, 0, 2))
      imm(a, 5, 65535)
      imm(a, 7, 0x3f800000)
      for half in range(2):
        a.emit(TT.TTSFPMOV(0, dest, 6, 0))
        if half: a.emit(TT.TTSFPSHFT((-16) & 4095, 0, 6, 1))
        a.emit(TT.TTSFPAND(0, 5, 6, 0))
        a.emit(TT.TTSFPOR(0, 7, 6, 0))
        a.emit(TT.TTSFPSTORE(6, 3, 0, index * 16 + half * 8 + position * 2))
  stall(a, Stall.SYNC, Wait.SFPU)
  pc_sync(a)
  publish_dst(a)
  count = len(MAGNITUDES) * 256 + 128
  n = p.reg()
  p.li(n, count)
  emit_pack_dst_to_cb(p, 0, OUTPUT, n, output_format=F32)
  bh.launch({k.role: k.lower() for k in (a, p)}, l1={OUTPUT: b'\xa5' * (count * 4 + 64)})
  words = unpack(f'<{count}I', bh.read_l1(bh.core, OUTPUT, count * 4))
  for index, magnitude in enumerate(MAGNITUDES):
    permitted = allowed(magnitude, sign, mode)
    unchanged = magnitude | (sign << 31) if alias else 0xa55a1234
    for element in range(128):
      lo, hi = words[index * 256 + element], words[index * 256 + 128 + element]
      assert lo & 0xffff0000 == hi & 0xffff0000 == 0x3f800000
      actual = (lo & 65535) | ((hi & 65535) << 16)
      enabled = mask == 'all' or mask == 'upper16' and (element % 64) // 2 >= 16
      assert actual in (permitted if enabled else {unchanged}), (magnitude, element, hex(actual), permitted)
  assert words[-128:] == (0,) * 128
  assert bh.read_l1(bh.core, OUTPUT + count * 4, 64) == b'\xa5' * 64
