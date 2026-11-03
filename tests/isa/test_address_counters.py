"""Address counters: RWCs (SETRWC / INCRWC) and packer ADCs (SETADC*, INCADC*, ADDRCR*).

Neither counter set has a RISC-visible readback, so both are observed by effect.
Dst tile 0 is first tagged so every element holds 0x3f800000 | (row*16 + col).
Observed while writing this: after ZEROACC, an SFPSTORE that writes only the
even columns of rows r..r+3 makes the odd columns of those rows read back the
data left there by a previous kernel (ZEROACC clears per-row zero flags, not
data), so the RWC cases tag all of Dst before the store under test.

RWC claims (math thread, observed through the Dst row an SFPSTORE writes):
- SFPSTORE address = Imm + RWC.Dst; SETRWC sets Dst and Dst_Cr; INCRWC adds
  to Dst only (the counter exceeds the 4-bit field: 15 + 15 = 30); INCRWC with DstCr
  adds to Dst_Cr and copies it to Dst (carriage return); SETRWC with DstCr adds
  the value to Dst_Cr, with DstCtoCr adds it to Dst.
ADC claims (packer channel 0, observed through the Dst row one PACR packs,
row = 16*Z + Y, tile = W):
- SETADC / SETADCXY / SETADCZW set a counter (and its Cr); INCADCXY /
  INCADCZW add to the counter only; ADDRCRXY / ADDRCRZW add the increment to
  Cr and copy Cr into the counter, leaving the other dimension alone.
- SETADCXY aimed at the unpackers (U0|U1) leaves the packer ADC untouched, and
  the packer ADC written by TRISC0 is not the one TRISC2's PACR uses
  (ADCs are per thread).
- SETADCXX X0 start skips the first X0 columns of the row.
The RWC cases issue STALLWAIT(SFPU, MATH) between the RWC ops and SFPSTORE;
whether that stall is required was not tested.
Not covered: unpacker ADCs and the unpacker context counter wrap
(../blackhole-py-rewrite/tests/hw/test_unpacker1_contexts.py); that probe
needs the rewrite's config.apply machinery and is not ported here.
"""
from struct import unpack

import pytest

from asm import Asm
from ttko.isa import Tensix as TT
from tests.movement.packer.pack import _configure_row_addressing, _pacr, emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, PackCfg, Sem, SemWait, Stall, Wait, _set_pack_destination, _set_thread_cfg,
  configure_fp32_dst, configure_packer, pc_sync, publish_dst, sem_get, sem_post, sem_wait, stall,
)

OUTPUT = 0x60000
ONE = 0x3f800000
MARK = 1025  # RWC marker lanes: ONE | (1025 + 2L), above every tag


def math_prologue(k):
  k.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(k, Stall.SYNC, Wait.MATH)
  configure_fp32_dst(k, 0)
  for register in (12, 28, 47): _set_thread_cfg(k, register, 0)
  k.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  k.emit(TT.TTSFPLOADI(7, 0, ONE >> 16))
  k.emit(TT.TTSFPLOADI(7, 10, 0))


def store_tag(k, imm, base):
  """Lane L holds ONE | (2L + base); lands at row (A&~3)+L//8, col 2(L%8)+(A>>1&1)."""
  k.emit(TT.TTSFPIADD(base, 15, 1, 5))
  k.emit(TT.TTSFPOR(0, 7, 1, 0))
  k.emit(TT.TTSFPSTORE(1, 3, 0, imm))


def stored(address, base, words):
  for lane in range(32):
    row, col = (address & ~3) + lane // 8, 2 * (lane % 8) + (address >> 1 & 1)
    words[row * 16 + col] = ONE | (2 * lane + base)
  return words


def tag_dst(k):
  for address in range(0, 64, 2):  # element (r, c) = ONE | (16r + c)
    store_tag(k, address, 16 * (address & ~3) + (address >> 1 & 1))


def launch(bh, images, count):
  size = 4 * count
  bh.launch({k.role: k.lower() for k in images}, l1={OUTPUT: b'\xa5' * (size + 64)})
  return list(unpack(f'<{count}I', bh.read_l1(bh.core, OUTPUT, size)))


def SET(val, cr=0, mask=4): return TT.TTSETRWC(0, cr, val, 0, 0, mask)
def INC(val, cr=0): return TT.TTINCRWC(cr, val, 0, 0)

RWC = {
  'set8': ([SET(8)], 0, 8),
  'set8+imm16': ([SET(8)], 16, 24),
  'set8-inc4': ([SET(8), INC(4)], 0, 12),
  'inc-past-15': ([SET(15), INC(15)], 0, 30),
  'inc-then-cr': ([SET(8), INC(4), INC(0, cr=4)], 0, 8),
  'cr-inc': ([SET(8), INC(4), INC(4, cr=4)], 0, 12),
  'setrwc-dstcr': ([SET(4), INC(8), SET(4, cr=4)], 0, 8),
  'setrwc-dstctocr': ([SET(4), INC(8), SET(4, cr=8, mask=0)], 0, 16),
}


@pytest.mark.parametrize('case', list(RWC))
def test_rwc_dst(bh, case):
  ops, imm, address = RWC[case]
  math, packer = Asm('trisc1'), Asm('trisc2')
  math_prologue(math)
  tag_dst(math)  # ZEROACC alone is not enough: see the module docstring
  for op in ops: math.emit(op)
  stall(math, Stall.SFPU, Wait.MATH)
  store_tag(math, imm, MARK)
  stall(math, Stall.SYNC, Wait.SFPU)
  pc_sync(math)
  publish_dst(math)
  count = packer.reg()
  packer.li(count, 1024)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=F32)
  tags = [ONE | i for i in range(1024)]
  assert launch(bh, (math, packer), 1024) == stored(address, MARK, tags)


def XY(y): return TT.TTSETADCXY(4, 0, 0, y, 0, 2)
def ZW(z): return TT.TTSETADCZW(4, 0, 0, 0, z, 1)

ADC = {  # name: (ops, expected Dst row, first column)
  'baseline': ([], 0, 0),
  'setadc-y': ([TT.TTSETADC(4, 0, 1, 11)], 11, 0),
  'setadcxy': ([XY(5)], 5, 0),
  'incadcxy': ([XY(5), TT.TTINCADCXY(4, 0, 0, 3, 0)], 8, 0),
  'setadczw': ([ZW(2)], 32, 0),
  'incadczw': ([ZW(1), TT.TTINCADCZW(4, 0, 0, 0, 2)], 48, 0),
  'addrcrxy': ([XY(5), TT.TTINCADCXY(4, 0, 0, 3, 0), TT.TTADDRCRXY(4, 0, 0, 2, 0, 2)], 7, 0),
  'addrcrxy-0': ([XY(5), TT.TTINCADCXY(4, 0, 0, 3, 0), TT.TTADDRCRXY(4, 0, 0, 0, 0, 2)], 5, 0),
  'addrcrzw': ([ZW(1), TT.TTINCADCZW(4, 0, 0, 0, 2), TT.TTADDRCRZW(4, 0, 0, 0, 1, 1)], 32, 0),
  'addrcrxy-keeps-z': ([XY(5), ZW(1), TT.TTINCADCXY(4, 0, 0, 3, 0), TT.TTINCADCZW(4, 0, 0, 0, 2),
                        TT.TTADDRCRXY(4, 0, 0, 0, 0, 2)], 53, 0),
  'unpacker-only': ([TT.TTSETADCXY(3, 0, 0, 5, 0, 2)], 0, 0),
  'x-start': ([TT.TTSETADCXX(4, 15, 4)], 0, 4),
  'other-thread': ([], 0, 0),
}


@pytest.mark.parametrize('case', list(ADC))
def test_packer_adc(bh, case):
  ops, row, col = ADC[case]
  math, packer = Asm('trisc1'), Asm('trisc2')
  images = [math, packer]
  if case == 'other-thread':
    loader = Asm('trisc0')
    loader.emit(XY(7))
    stall(loader, Stall.SYNC, Wait.THCON)
    sem_post(loader, Sem.UNPACK_TO_DEST)
    sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
    sem_get(math, Sem.UNPACK_TO_DEST)
    images.append(loader)
  math_prologue(math)
  tag_dst(math)
  stall(math, Stall.SYNC, Wait.SFPU)
  pc_sync(math)
  publish_dst(math)

  sem_wait(packer, Sem.MATH_PACK, SemWait.ON_ZERO, Stall.TDMA)
  configure_packer(packer, F32)
  _configure_row_addressing(packer)
  _set_pack_destination(packer, 0, OUTPUT)
  packer.write(PackCfg.DESTINATION_OFFSET, 0)
  packer.emit(TT.TTSETADCXX(4, 15, 0))
  for dim in (1, 2): packer.emit(TT.TTSETADC(4, 0, dim, 0))
  for op in ops: packer.emit(op)
  stall(packer, Stall.CFG, Wait.PACK0)
  packer.emit(_pacr(address_mode=1, last=True))
  stall(packer, Stall.SYNC, Wait.PACK0)
  pc_sync(packer)
  sem_get(packer, Sem.MATH_PACK)
  got = launch(bh, images, 16)
  assert got[:16 - col] == [ONE | (16 * row + c) for c in range(col, 16)]
