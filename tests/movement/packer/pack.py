"""Handwritten Blackhole row-major packer kernels used by movement tests."""

from asm import Asm
from fw.consts import TensixMMIO
from isa import R, Reg, Tensix as TT, is_reg
from tests.movement.unpacker.unpack import (
  BF16, F32, TILE_ELEMENTS, PackCfg, Sem, SemWait, Stall, Wait,
  _mop_loop_words, _set_pack_destination, _set_thread_cfg,
  configure_mop, configure_packer, pc_sync, run_mop, sem_get, sem_wait, stall,
)


PACK_ADDRESS_MODIFIER = 37
PACK_SINGLE_INTERFACE = 1


def _pacr(*, address_mode=0, last=False):
  return TT.TTPACR(
    0, 0, 0, address_mode, 0, 0, PACK_SINGLE_INTERFACE,
    0, 0, 0, 0, int(last),
  )


def initialize_prng(k: Asm, seed: int):
  """Seed Blackhole's PRNG and advance its SFPU initialization pipeline."""
  if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
    raise ValueError("PRNG seed must be a 32-bit unsigned integer")
  k.write(TensixMMIO.PRNG_SEED_SEED_VAL, seed)
  nop = TT.TTSFPNOP()
  configure_mop(k, _mop_loop_words(1, 600, loop=nop, last=nop))
  run_mop(k)
  stall(k, Stall.SFPU, Wait.SFPU)


def _configure_row_addressing(k: Asm):
  # Native pack-rows mode: one PACR interface emits one contiguous 16-value
  # register row. Address mode 0 advances Dst Y; mode 1 resets it on close.
  _set_thread_cfg(k, PACK_ADDRESS_MODIFIER + 0, 1)
  _set_thread_cfg(k, PACK_ADDRESS_MODIFIER + 1, 0x20)
  _set_thread_cfg(k, PACK_ADDRESS_MODIFIER + 2, 0)
  k.write(PackCfg.COUNTERS, 1 << 8)


def _set_dynamic_pack_x(k: Asm, element_count: Reg):
  word = k.reg()
  k.addi(word, element_count, -1)
  k.slli(word, word, 10)
  base = k.reg()
  k.li(base, TT.TTSETADCXX(4, 0, 0))
  k.or_(word, word, base)
  k.write(TensixMMIO.INSTRN_BUF_BASE, word)


def _configure_row_mop(k: Asm, rows: int | Reg, *, close: bool):
  normal = _pacr()
  final = _pacr(address_mode=1, last=True) if close else normal
  configure_mop(k, _mop_loop_words(1, rows, loop=normal, last=final))


def _set_dst_position(k: Asm, tile: int, element_offset: int):
  row = element_offset // 16
  k.emit(TT.TTSETADC(4, 0, 1, row & 15))
  k.emit(TT.TTSETADC(4, 0, 2, row >> 4))
  k.emit(TT.TTSETADC(4, 0, 3, tile))


def emit_pack_dst_to_cb(
  k: Asm,
  tile: int,
  output_address: int,
  element_count: Reg,
  *,
  dst_element_offset=0,
  output_format=BF16,
  relu_mode=0,
  relu_threshold=0,
  stochastic=False,
):
  """Pack runtime N values from FP32 Dst into a dense row-major L1 CB page.

  Dst offsets begin at a native 16-element register-row boundary. Runtime N
  may include an arbitrary 1..15 element tail. Repetition is always driven by
  MOP: one runtime loop for full rows and at most one single-iteration tail.
  """
  if not is_reg(element_count):
    raise TypeError("element_count must be a runtime register")
  if type(tile) is not int or not 0 <= tile < 8:
    raise ValueError("FP32 Dst tile must be in range 0..7")
  if (type(dst_element_offset) is not int or
      not 0 <= dst_element_offset < TILE_ELEMENTS):
    raise ValueError("Dst element offset must be in range 0..1023")
  if dst_element_offset % 16:
    raise ValueError("Dst element offset must begin on a 16-element row")
  if output_format not in (BF16, F32):
    raise ValueError("row pack supports BF16 and F32 output")
  if relu_mode not in (0, 1, 3):
    raise ValueError("packer ReLU mode must be 0, 1, or 3")
  if not 0 <= relu_threshold < 1 << 16:
    raise ValueError("packer ReLU threshold must be a 16-bit value")

  sem_wait(k, Sem.MATH_PACK, SemWait.ON_ZERO, Stall.TDMA)
  configure_packer(
    k, output_format, relu_mode=relu_mode, relu_threshold=relu_threshold,
    stochastic=stochastic,
  )
  _configure_row_addressing(k)
  _set_pack_destination(k, tile, output_address)
  _set_dst_position(k, tile, dst_element_offset)
  k.write(PackCfg.DESTINATION_OFFSET, 0)

  rows, tail = k.reg(2)
  k.srli(rows, element_count, 4)
  k.andi(tail, element_count, 15)
  no_rows = k._new_label("no_pack_rows")
  no_tail = k._new_label("no_pack_tail")
  close_rows = k._new_label("close_pack_rows")
  run_rows = k._new_label("run_pack_rows")

  k.beq(rows, R.ZERO, no_rows)
  k.beq(tail, R.ZERO, close_rows)
  k.emit(TT.TTSETADCXX(4, 15, 0))
  _configure_row_mop(k, rows, close=False)
  k.j(run_rows)
  k.label(close_rows)
  k.emit(TT.TTSETADCXX(4, 15, 0))
  _configure_row_mop(k, rows, close=True)
  k.label(run_rows)
  stall(k, Stall.CFG, Wait.PACK0)
  run_mop(k)
  k.label(no_rows)

  k.beq(tail, R.ZERO, no_tail)
  _set_dynamic_pack_x(k, tail)
  _configure_row_mop(k, 1, close=True)
  stall(k, Stall.CFG, Wait.PACK0)
  run_mop(k)
  k.label(no_tail)

  stall(k, Stall.SYNC, Wait.PACK0)
  pc_sync(k)
  sem_get(k, Sem.MATH_PACK)
