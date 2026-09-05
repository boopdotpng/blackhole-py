"""Observe all eight loaded vectors, with independently stored hardware lane IDs."""
from struct import pack, unpack

from asm import Asm
from fw.consts import TensixL1
from isa import Tensix as TT
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, Sem, SemWait, Stall, Wait, _set_thread_cfg, configure_fp32_dst,
  emit_unpack_to_dst, pc_sync, publish_dst, sem_get, sem_post, sem_wait, stall,
)

INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
OUTPUT = INPUT + 4096


def test_arange256_sfpu_lanes(bh):
  loader, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  size = loader.reg()
  loader.li(size, 256 * 4)
  emit_unpack_to_dst(loader, INPUT, size, 0, 0)

  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(math, Stall.SYNC, Wait.MATH)
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  configure_fp32_dst(math, 0)
  for register in (12, 28, 47):
    _set_thread_cfg(math, register, 0)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  math.emit(TT.TTSFPENCC(0, 0, 0, 2))  # Disable predication: all lanes active.
  for reg in range(8):
    math.emit(TT.TTSFPLOAD(reg, 3, 0, reg * 2))
  # All eight LRegs now hold the input. Store each in its own four-row window.
  for reg in range(8):
    math.emit(TT.TTSFPSTORE(reg, 3, 0, 32 + reg * 4))
  # L15 contains lane*2. Store raw integer tags beside each vector's values,
  # so readback identifies actual lanes rather than assuming the store mapping.
  math.emit(TT.TTSFPMOV(0, 15, 0, 0))
  for reg in range(8):
    math.emit(TT.TTSFPSTORE(0, 4, 0, 34 + reg * 4))
  stall(math, Stall.SYNC, Wait.SFPU)
  pc_sync(math)
  publish_dst(math)

  count = packer.reg()
  packer.li(count, 512)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, dst_element_offset=512, output_format=F32)
  bh.launch({k.role: k.lower() for k in (loader, math, packer)},
            l1={INPUT: pack("<256f", *range(256)), OUTPUT: b"\xA5" * 2112})
  raw = bh.read_l1(bh.core, OUTPUT, 2048)
  floats, words = unpack("<512f", raw), unpack("<512I", raw)
  vectors = []
  for reg in range(8):
    base = reg * 64
    tags = words[base+1:base+64:2]
    assert sorted(tags) == list(range(0, 64, 2))
    values = dict(zip(tags, floats[base:base+64:2]))
    vector = [values[lane * 2] for lane in range(32)]
    expected = [(reg // 2) * 64 + (lane // 8) * 16 + (lane % 8) * 2 + reg % 2 for lane in range(32)]
    assert vector == expected
    vectors.append(vector)
    print(f"l{reg}: {[int(x) for x in vector]}")
  assert sorted(x for vector in vectors for x in vector) == list(range(256))
  assert bh.read_l1(bh.core, OUTPUT+2048, 64) == b"\xA5" * 64
