"""Allocation-scoped raw SFPU movement. No fixture initialization or host oracle."""
from struct import pack, unpack

from ttko.isa import Tensix as TT
from tests.movement.unpacker.unpack import Stall, Wait, stall


def register(index, *, writable=False):
  if type(index) is not int or not 0 <= index < (8 if writable else 16):
    raise ValueError("register must be l0-l7 writable, or l0-l15 readable")
  return index


def address(allocation_start, position=0, block=0, blocks=1):
  """Physical 16-bit allocation units; each FP32 block consumes two units."""
  if (type(allocation_start) is not int or allocation_start % 2 or
      type(blocks) is not int or blocks < 1 or
      not 0 <= allocation_start <= 128 - 2 * blocks or
      type(block) is not int or not 0 <= block < blocks or
      type(position) is not int or not 0 <= position < 4):
    raise ValueError("invalid aligned FP32 allocation/block/position")
  return allocation_start * 4 + block * 8 + position * 2


def load(k, dst, allocation_start, *, position=0, block=0, blocks=1):
  k.emit(TT.TTSFPLOAD(register(dst, writable=True), 3, 0,
                      address(allocation_start, position, block, blocks)))


def store(k, src, allocation_start, *, position=0, block=0, blocks=1, raw=False,
          scratch=5):
  src = register(src)
  target = address(allocation_start, position, block, blocks)
  # l12-l15 stores have special backdoor semantics. Copy to declared scratch.
  if src >= 12:
    copy(k, scratch, src)
    src = scratch
  k.emit(TT.TTSFPSTORE(src, 4 if raw else 3, 0, target))


def loadi_bits(k, dst, bits):
  register(dst, writable=True)
  if type(bits) is not int or not 0 <= bits < 1 << 32:
    raise ValueError("immediate must be uint32 bits")
  k.emit(TT.TTSFPLOADI(dst, 0, bits >> 16))
  if bits & 65535:
    k.emit(TT.TTSFPLOADI(dst, 10, bits & 65535))


def loadi(k, dst, value):
  loadi_bits(k, dst, unpack('<I', pack('<f', float(value)))[0])


def copy(k, dst, src):
  k.emit(TT.TTSFPMOV(0, register(src), register(dst, writable=True), 0))


def predicate(k, mask=None, *, scratch=(6, 7)):
  """Replace predicate with compile-time uint32; clobber two explicit LRegs.

  Bit i controls physical lane i. None disables predication and restores flags.
  No Dst scratch; mask replacement works when the previous predicate is false.
  """
  if mask is not None and (type(mask) is not int or not 0 <= mask < 1 << 32):
    raise ValueError("predicate must be None or uint32")
  if len(scratch) != 2 or scratch[0] == scratch[1]:
    raise ValueError("predicate needs two distinct writable scratch registers")
  shift, bits = (register(x, writable=True) for x in scratch)
  k.emit(TT.TTSFPENCC(0, 0, 0, 2))
  if mask is None:
    return
  if mask in (0, 0xffffffff):
    k.emit(TT.TTSFPENCC(1 if mask == 0 else 3, 0, 0, 10))
    return
  k.emit(TT.TTSFPSHFT(0xfff, 15, shift, 5))  # Lane = L15 >> 1.
  k.emit(TT.TTSFPIADD(0, 9, shift, 6))       # -Lane, no flag update.
  loadi_bits(k, bits, mask)
  k.emit(TT.TTSFPSHFT(0, shift, bits, 0))   # mask >> Lane.
  k.emit(TT.TTSFPSHFT(31, bits, bits, 1))  # Desired bit into sign.
  k.emit(TT.TTSFPENCC(3, 0, 0, 10))
  k.emit(TT.TTSFPSETCC(0, bits, 0, 0))


def drain(k):
  stall(k, Stall.SYNC, Wait.SFPU)
