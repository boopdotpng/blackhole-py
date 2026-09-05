"""Handwritten Blackhole unpack/move/pack pipelines used by unpacker tests.

The input and output buffers are ordinary row-major L1 byte streams.  The
unpacker is deliberately left in non-tileize mode: consecutive 16x16 chunks
are copied into consecutive Src/Dst faces and the packer writes the same face
order back to L1.  Every repeated Tensix sequence is issued through MOP; the
direct-to-Dst sequence additionally retains the required per-fragment UNPACK0
drain by putting ``UNPACR; STALLWAIT`` in Replay.
"""

from enum import IntEnum

from asm import Asm
from fw.consts import TensixMMIO
from isa import R, Reg, Tensix as TT, is_reg


BF16 = 5
F32 = 0
TILE_ELEMENTS = 32 * 32
FACE_ELEMENTS = 16 * 16
BF16_TILE_BYTES = TILE_ELEMENTS * 2
F32_TILE_BYTES = TILE_ELEMENTS * 4

MOP_CFG = 0xFFB80000
UNPACK_CONFIG_SYNC = 0xFFE80034
PC_SEMAPHORE_BASE = TensixMMIO.PC_BUF_SYNC - 4 + 8 * 4


class Stall(IntEnum):
  TDMA, SYNC, PACK, UNPACK, XMOV, THCON, MATH, CFG, SFPU = (
    1 << bit for bit in range(9)
  )


class Wait(IntEnum):
  THCON, UNPACK0, UNPACK1, PACK0, MATH, SRCA_CLR, SRCB_CLR, SRCA_VLD, SRCB_VLD, XMOV, TRISC_CFG, SFPU, CFGEXU = (
    1 << bit for bit in range(13)
  )


class SemWait(IntEnum):
  ON_ZERO = 1
  ON_MAX = 2


class Sem(IntEnum):
  MATH_PACK = 1
  UNPACK_TO_DEST = 2
  UNPACK_SYNC = 5
  MATH_DONE = 7


class UnpackTarget(IntEnum):
  SRCA = 0
  SRCB = 1
  DST = 2


CFG_BASE = TensixMMIO.CFG_BASE


class UnpackCfg(IntEnum):
  ADDRESS_XY0 = CFG_BASE + 0xB0
  ADDRESS_ZW0 = CFG_BASE + 0xB4
  ADDRESS_XY1 = CFG_BASE + 0xE0
  ADDRESS_ZW1 = CFG_BASE + 0xE4
  TILE_DESCRIPTOR = CFG_BASE + 0x100
  OPTIONS = CFG_BASE + 0x120
  BASE = CFG_BASE + 0x130
  DESTINATION = CFG_BASE + 0x150
  X_DIMENSION = CFG_BASE + 0x158
  OFFSET = CFG_BASE + 0x170


class PackCfg(IntEnum):
  ALU_FORMAT = CFG_BASE + 4
  ACCUMULATION = CFG_BASE + 8
  ADDRESS_XY = CFG_BASE + 0x30
  ADDRESS_ZW = CFG_BASE + 0x34
  DESTINATION_READ = CFG_BASE + 0x48
  TILE_ROW_MAPPING = CFG_BASE + 0x50
  TILE_ROW_MAPPING1 = CFG_BASE + 0x54
  EDGE = CFG_BASE + 0x60
  EDGE1 = CFG_BASE + 0x64
  COUNTERS = CFG_BASE + 0x70
  SECTION_SIZES = CFG_BASE + 0x110
  L1_DESTINATION = CFG_BASE + 0x114
  DATA_FORMAT = CFG_BASE + 0x118
  DESTINATION_OFFSET = CFG_BASE + 0x2D0


UNPACKER0, UNPACKER1 = range(2)
SRCA_SET = 5
UNPACK_MISC_CONFIG = 41

ADDR_BASE0 = (CFG_BASE + 48 * 4, CFG_BASE + 60 * 4)
ADDR_BASE1 = (CFG_BASE + 49 * 4, CFG_BASE + 61 * 4)
ADDR_MISC = (CFG_BASE + 50 * 4, CFG_BASE + 62 * 4)
NOP_CLEAR = (CFG_BASE + 53 * 4, CFG_BASE + 63 * 4)
PACK_ADDRESS_MODIFIER = 37


def _engine_cfg(register: UnpackCfg, engine: int):
  # The two low address-counter blocks are interleaved; the THCON section-0
  # and section-1 descriptor/config blocks are 0xc0 bytes apart.
  interleaved = register in (
    UnpackCfg.ADDRESS_XY0, UnpackCfg.ADDRESS_ZW0,
    UnpackCfg.ADDRESS_XY1, UnpackCfg.ADDRESS_ZW1,
  )
  return int(register) + engine * (8 if interleaved else 0xC0)


def stall(k: Asm, resources: int, conditions: int):
  k.emit(TT.TTSTALLWAIT(int(resources), int(conditions)))


def sem_wait(k: Asm, semaphore: Sem, condition: SemWait, resources: int):
  k.emit(TT.TTSEMWAIT(int(resources), 1 << semaphore, int(condition)))


def sem_get(k: Asm, semaphore: Sem):
  k.emit(TT.TTSEMGET(1 << semaphore))


def sem_post(k: Asm, semaphore: Sem):
  k.emit(TT.TTSEMPOST(1 << semaphore))


def _pc_sync(k: Asm, address: int):
  pointer, observed = k.reg(2)
  k.li(pointer, address)
  k.sw(R.ZERO, pointer)
  k.lw(observed, pointer)
  k.and_(R.ZERO, R.ZERO, observed)


def mop_sync(k: Asm):
  _pc_sync(k, TensixMMIO.PC_BUF_MOP_SYNC)


def pc_sync(k: Asm):
  _pc_sync(k, TensixMMIO.PC_BUF_SYNC)


def _mop_loop_words(outer, inner, *, start=TT.TTNOP(), loop=TT.TTNOP(),
                    end0=TT.TTNOP(), end1=TT.TTNOP(),
                    alternate=TT.TTNOP(), last=TT.TTNOP(),
                    outer_last=TT.TTNOP()):
  return (outer, inner, start, end0, end1, loop, alternate, last, outer_last)


def configure_mop(k: Asm, words):
  """Program one nine-word MOP template after draining its previous user."""
  words = tuple(words)
  if len(words) != 9:
    raise ValueError("a MOP template has exactly nine words")
  mop_sync(k)
  for index, word in enumerate(words):
    k.write(MOP_CFG + index * 4, word)


def run_mop(k: Asm):
  k.emit(TT.TTMOP(1, 0, 0))


def load_replay(k: Asm, start: int, words):
  words = tuple(words)
  if not words or start < 0 or start + len(words) > 32:
    raise ValueError("Replay occupies one to 32 valid slots")
  k.emit(TT.TTREPLAY(start, len(words), 0, 1))
  for word in words:
    k.emit(word)


def _unpacr(engine: int, *, to_dst=False):
  return TT.TTUNPACR(
    engine, 0x11 if to_dst else 1, 0, 0, 0, 1,
    int(not to_dst), 0, 0, 0, 0, 0, 1,
  )


def _srcb_dvalid():
  return TT.TTUNPACR_NOP(1, 0, 0, 1, 0, 0, 0, 0, 1)


def _wait_unpack_config(k: Asm):
  pointer, value = k.reg(2)
  again, ready = k._new_label("unpack_cfg"), k._new_label("unpack_cfg_ready")
  k.li(pointer, UNPACK_CONFIG_SYNC)
  k.label(again)
  k.lw(value, pointer)
  k.andi(value, value, 0xFE)
  k.beq(value, R.ZERO, ready)
  k.fence()
  k.j(again)
  k.label(ready)


def _set_unpack_base(k: Asm, engine: int, address: int | Reg):
  if is_reg(address):
    base = k.reg()
    k.srli(base, address, 4)
    k.addi(base, base, -1)
  else:
    if address < 16 or address % 16:
      raise ValueError("unpack source must be a positive 16-byte-aligned L1 address")
    base = (address >> 4) - 1
  k.write(_engine_cfg(UnpackCfg.BASE, engine), base)
  k.write(_engine_cfg(UnpackCfg.BASE, engine) + 4, base)


def configure_unpacker(k: Asm, engine: int, address: int | Reg, input_format: int,
                       target: UnpackTarget, *, dst_tile=0,
                       dst_element_offset=0, commit=True):
  """Configure one unpacker for an unmodified, non-tileized L1 stream."""
  if engine not in (UNPACKER0, UNPACKER1):
    raise ValueError("unpacker engine must be zero or one")
  if target is UnpackTarget.DST and engine != UNPACKER0:
    raise ValueError("only unpacker zero can write Dst")
  if input_format not in (BF16, F32):
    raise ValueError("the unpacker proof supports BF16 and F32")
  if type(dst_tile) is not int or not 0 <= dst_tile < 8:
    raise ValueError("FP32 Dst tile must be in range 0..7")
  if type(dst_element_offset) is not int or not 0 <= dst_element_offset < TILE_ELEMENTS:
    raise ValueError("Dst element offset must be in range 0..1023")

  _wait_unpack_config(k)
  k.emit(TT.TTSETC16(0, 0))

  descriptor_x = 0 if engine == UNPACKER0 else FACE_ELEMENTS
  descriptor = (
    input_format | 0x10 | descriptor_x << 16,
    1 | 4 << 16,
    0,
    0,
  )
  direct = target is UnpackTarget.DST
  options = (0x20 | input_format, 0x03 | (0x30 if direct else 0), 0, 0)
  for register, words in (
    (_engine_cfg(UnpackCfg.TILE_DESCRIPTOR, engine), descriptor),
    (_engine_cfg(UnpackCfg.OPTIONS, engine), options),
  ):
    for index, word in enumerate(words):
      k.write(register + index * 4, word)

  item_size = 2 if input_format == BF16 else 4
  for register, value in (
    (_engine_cfg(UnpackCfg.ADDRESS_XY0, engine), 0),
    (_engine_cfg(UnpackCfg.ADDRESS_ZW0, engine), 0),
    (_engine_cfg(UnpackCfg.ADDRESS_XY1, engine), item_size | 16 * item_size << 16),
    (_engine_cfg(UnpackCfg.ADDRESS_ZW1, engine), FACE_ELEMENTS * item_size),
    (ADDR_BASE0[engine], 0),
    (ADDR_BASE1[engine], 0),
    (ADDR_MISC[engine], 0x100 if engine == UNPACKER0 else 0),
    (NOP_CLEAR[engine], 0),
  ):
    k.write(register, value)

  destination = 64 if engine == UNPACKER0 else 0
  if direct:
    # Dst addresses are bytes, with the first 64 bytes reserved by THCON.
    # Dst's THCON address is a register-row selector, not a linear SRAM byte
    # address.  A 32x32 FP32 tile advances by 64 register rows * 16.
    destination += dst_tile * 64 * 16 + dst_element_offset
  for register, value in (
    (_engine_cfg(UnpackCfg.DESTINATION, engine), destination | destination << 16),
    (_engine_cfg(UnpackCfg.X_DIMENSION, engine), FACE_ELEMENTS | FACE_ELEMENTS << 16),
    (_engine_cfg(UnpackCfg.OFFSET, engine), 0),
    (_engine_cfg(UnpackCfg.OFFSET, engine) + 4, 0),
  ):
    k.write(register, value)

  _set_unpack_base(k, engine, address)
  k.emit(TT.TTSETC16(UNPACK_MISC_CONFIG, 0))
  if engine == UNPACKER0:
    k.emit(TT.TTSETC16(SRCA_SET, 0 if direct else 4))
  if commit:
    observed = k.reg()
    k.read(observed, _engine_cfg(UnpackCfg.BASE, engine))
    k.write(UNPACK_CONFIG_SYNC, 0)


def _set_dynamic_adc_x(k: Asm, engine: int, element_count: Reg):
  """Issue SETADCXX with a runtime x-end through the Tensix MMIO FIFO."""
  word = k.reg()
  k.addi(word, element_count, -1)
  k.slli(word, word, 10)
  base = k.reg()
  k.li(base, TT.TTSETADCXX(engine + 1, 0, 0))
  k.or_(word, word, base)
  k.write(TensixMMIO.INSTRN_BUF_BASE, word)


def _program_runtime_outer_mop(k: Asm, outer: Reg, replay_start: int,
                               replay_length: int):
  play = TT.TTREPLAY(replay_start, replay_length, 0, 0)
  configure_mop(k, _mop_loop_words(outer, 1, start=play))


def emit_unpack_to_dst(k: Asm, address: int | Reg, byte_count: Reg,
                       dst_tile: int, dst_element_offset: int, *,
                       pack_stochastic=False):
  """Copy a runtime number of F32 bytes directly to one FP32 Dst tile.

  At most two MOP invocations are emitted: one runtime-count loop for complete
  256-element fragments and one for the final fragment.  The source operation
  never expands into one instruction per element.
  """
  if not is_reg(byte_count):
    raise TypeError("byte_count must be a runtime register")
  if dst_element_offset < 0 or dst_element_offset >= TILE_ELEMENTS:
    raise ValueError("Dst element offset must be in range 0..1023")
  if dst_element_offset % 16:
    raise ValueError("direct-to-Dst offset must begin on a 16-element row")

  configure_unpacker(
    k, UNPACKER0, address, F32, UnpackTarget.DST,
    dst_tile=dst_tile, dst_element_offset=dst_element_offset,
  )
  configure_stochastic_rounding(k, stochastic=pack_stochastic)
  load_replay(k, 0, (
    _unpacr(UNPACKER0, to_dst=True),
    TT.TTSTALLWAIT(Stall.UNPACK, Wait.UNPACK0),
  ))
  k.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  sem_wait(k, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(k, Sem.MATH_DONE)
  sem_wait(k, Sem.UNPACK_TO_DEST, SemWait.ON_MAX, Stall.UNPACK)
  stall(k, Stall.UNPACK, Wait.TRISC_CFG | Wait.PACK0)

  elements, full, tail = k.reg(3)
  k.srli(elements, byte_count, 2)
  k.srli(full, elements, 8)
  k.andi(tail, elements, FACE_ELEMENTS - 1)
  no_full, after_full = k._new_label("no_full_faces"), k._new_label("after_full_faces")
  k.beq(full, R.ZERO, no_full)
  k.emit(TT.TTSETADCXX(1, FACE_ELEMENTS - 1, 0))
  _program_runtime_outer_mop(k, full, 0, 2)
  run_mop(k)
  k.j(after_full)
  k.label(no_full)
  k.label(after_full)

  no_tail = k._new_label("no_tail")
  k.beq(tail, R.ZERO, no_tail)
  _set_dynamic_adc_x(k, UNPACKER0, tail)
  one = k.reg()
  k.li(one, 1)
  _program_runtime_outer_mop(k, one, 0, 2)
  run_mop(k)
  k.label(no_tail)

  stall(k, Stall.UNPACK, Wait.THCON | Wait.UNPACK0)
  sem_get(k, Sem.UNPACK_SYNC)
  pc_sync(k)
  k.emit(TT.TTSETC16(SRCA_SET, 4))
  sem_post(k, Sem.UNPACK_TO_DEST)


def emit_unpack_to_src(k: Asm, address: int, target: UnpackTarget):
  if target not in (UnpackTarget.SRCA, UnpackTarget.SRCB):
    raise ValueError("source target must be SrcA or SrcB")
  engine = UNPACKER0 if target is UnpackTarget.SRCA else UNPACKER1
  configure_unpacker(k, engine, address, BF16, target)
  k.emit(TT.TTSETADCXX(engine + 1, FACE_ELEMENTS - 1, 0))
  k.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  stall(k, Stall.UNPACK, Wait.SRCA_CLR if engine == 0 else Wait.SRCB_CLR)
  if engine == UNPACKER0:
    configure_mop(k, _mop_loop_words(
      4, 1, start=_unpacr(engine), loop=_srcb_dvalid(),
      last=_srcb_dvalid(), outer_last=_srcb_dvalid(),
    ))
  else:
    configure_mop(k, _mop_loop_words(4, 1, start=_unpacr(engine)))
  stall(k, Stall.UNPACK, Wait.TRISC_CFG)
  run_mop(k)
  stall(k, Stall.UNPACK, Wait.UNPACK0 if engine == 0 else Wait.UNPACK1)
  sem_get(k, Sem.UNPACK_SYNC)
  pc_sync(k)


def configure_unpack_pair(k: Asm, address_a: int, address_b: int):
  configure_unpacker(
    k, UNPACKER0, address_a, BF16, UnpackTarget.SRCA, commit=False,
  )
  configure_unpacker(
    k, UNPACKER1, address_b, BF16, UnpackTarget.SRCB, commit=False,
  )
  observed = k.reg()
  k.read(observed, _engine_cfg(UnpackCfg.BASE, UNPACKER0))
  k.write(UNPACK_CONFIG_SYNC, 0)
  k.emit(TT.TTSETADCXX(1, FACE_ELEMENTS - 1, 0))
  k.emit(TT.TTSETADCXX(2, FACE_ELEMENTS - 1, 0))
  k.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))


def emit_unpack_pair(k: Asm, address_a: int, address_b: int):
  configure_unpack_pair(k, address_a, address_b)
  stall(k, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
  configure_mop(k, _mop_loop_words(
    4, 1, start=_unpacr(UNPACKER0), loop=_unpacr(UNPACKER1),
    last=_unpacr(UNPACKER1), outer_last=_unpacr(UNPACKER1),
  ))
  stall(k, Stall.UNPACK, Wait.TRISC_CFG)
  run_mop(k)
  stall(k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
  sem_get(k, Sem.UNPACK_SYNC)
  pc_sync(k)


def _rmw_cfg_byte(k: Asm, register: int, byte: int, mask: int, data: int):
  op = (TT.TTRMWCIB0, TT.TTRMWCIB1, TT.TTRMWCIB2, TT.TTRMWCIB3)[byte]
  k.emit(op(mask, data & mask, (register - CFG_BASE) >> 2))


def _set_thread_cfg(k: Asm, register: int, value: int):
  k.emit(TT.TTSETC16(register, value))


def configure_stochastic_rounding(k: Asm, *, stochastic: bool):
  """Program gasket/packer rounding after unpack configuration is complete."""
  # Match cfg_reg_rmw_tensix<1, 0, 0x7> from the LLK.  TTSETC16's operand is
  # not the cfg word index on Blackhole, so it silently leaves these bits clear.
  _rmw_cfg_byte(k, PackCfg.ALU_FORMAT, 0, 0x07,
                0x06 if stochastic else 0)


def configure_fp32_dst(k: Asm, tile: int):
  _set_thread_cfg(k, 0, 0)
  _set_thread_cfg(k, 1, tile * 64)
  stall(k, Stall.CFG, Wait.MATH | Wait.SFPU)
  _rmw_cfg_byte(k, CFG_BASE + 4, 3, 0x20, 0x20)


def _configure_copy_mop(k: Asm, bank: UnpackTarget, release: int):
  if bank is UnpackTarget.SRCA:
    # MOVA2D consumes eight register rows per issue.
    move = TT.TTMOVA2D(0, 0, 2, 2, 0)
    inner = 2
    end = TT.TTSETRWC(release, 0, 0, 0, 0, 3)
  else:
    # MOVB2D has no non-broadcast eight-row mode.  Mode 2 is the eight-row
    # broadcast form; use its four-row copy mode and advance SrcB/Dst by four.
    move = TT.TTMOVB2D(0, 0, 2, 4, 0)
    inner = 4
    end = TT.TTSETRWC(release, 2, 0, 0, 0, 2)
  configure_mop(k, _mop_loop_words(
    4, inner, loop=move, end0=end,
    last=move, outer_last=move,
  ))


def emit_copy_src_to_dst(k: Asm, bank: UnpackTarget, tile: int, *, release=3,
                         wait_for_dst=True):
  if bank not in (UnpackTarget.SRCA, UnpackTarget.SRCB):
    raise ValueError("copy source must be SrcA or SrcB")
  if wait_for_dst:
    sem_wait(k, Sem.MATH_PACK, SemWait.ON_MAX, Stall.SYNC | Stall.MATH | Stall.SFPU)
  configure_fp32_dst(k, tile)
  source_step = 8 if bank is UnpackTarget.SRCA else 4 << 8
  destination_step = 8 if bank is UnpackTarget.SRCA else 4
  for register, value in (
    (CFG_BASE + (12 + 2) * 4, source_step),
    (CFG_BASE + (28 + 2) * 4, destination_step),
    (CFG_BASE + (47 + 2) * 4, 0),
  ):
    _set_thread_cfg(k, (register - CFG_BASE) >> 2, value)
  k.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  stall(k, Stall.MATH, Wait.SRCA_VLD if bank is UnpackTarget.SRCA else Wait.SRCB_VLD)
  _configure_copy_mop(k, bank, release)
  run_mop(k)
  k.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))


def publish_dst(k: Asm):
  stall(k, Stall.SYNC, Wait.MATH | Wait.SFPU)
  sem_post(k, Sem.MATH_PACK)


def emit_direct_dst_math_handshake(k: Asm, tile: int):
  """Math side of the two-sided direct-to-Dst ownership protocol."""
  # Establish deterministic untouched bytes for partial-copy checks.
  k.emit(TT.TTZEROACC(3, 1, 0, 1, tile * 4))
  stall(k, Stall.SYNC, Wait.MATH)
  sem_wait(k, Sem.MATH_DONE, SemWait.ON_MAX, Stall.SYNC)
  sem_post(k, Sem.MATH_DONE)
  sem_wait(k, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(k, Sem.UNPACK_TO_DEST)
  publish_dst(k)


def _set_dma_reg16(k: Asm, half_register: int, value: int | Reg):
  if not is_reg(value):
    value_reg = k.reg()
    k.li(value_reg, value)
    value = value_reg
  instruction, mask, base = k.reg(3)
  k.slli(instruction, value, 8)
  k.li(mask, 0x00FFFF00)
  k.and_(instruction, instruction, mask)
  k.li(base, TT.TTSETDMAREG(0, 0, 0, half_register))
  k.or_(instruction, instruction, base)
  k.write(TensixMMIO.INSTRN_BUF_BASE, instruction)


def configure_packer(k: Asm, output_format: int, *, relu_mode=0,
                     relu_threshold=0, stochastic=False):
  if output_format not in (BF16, F32):
    raise ValueError("the packer proof supports BF16 and F32")
  if relu_mode not in (0, 1, 3):
    raise ValueError("packer ReLU mode must be 0, 1, or 3")
  if not 0 <= relu_threshold < 1 << 16:
    raise ValueError("packer ReLU threshold must be a 16-bit value")
  pack_source_format = output_format
  _set_thread_cfg(k, 0, 0)
  _rmw_cfg_byte(
    k, PackCfg.ALU_FORMAT, 3, 0x1E, pack_source_format << 1,
  )
  _rmw_cfg_byte(k, PackCfg.ALU_FORMAT, 0, 0x07,
                0x06 if stochastic else 0)
  relu = relu_mode << 2 | relu_threshold << 6
  for byte, mask in enumerate((0xFC, 0xFF, 0x3F)):
    _rmw_cfg_byte(k, PackCfg.ACCUMULATION, byte, mask, relu >> (byte * 8))
  for register, value in (
    (PackCfg.SECTION_SIZES, 0x00040000),
    (PackCfg.DATA_FORMAT,
     1 | output_format << 4 | pack_source_format << 8),
    (PackCfg.DESTINATION_READ, 1),
    (PackCfg.ADDRESS_XY,
     16 * (2 if pack_source_format == BF16 else 4) << 16),
    (PackCfg.ADDRESS_ZW,
     FACE_ELEMENTS * (2 if pack_source_format == BF16 else 4) |
     TILE_ELEMENTS * (2 if pack_source_format == BF16 else 4) << 16),
    (PackCfg.COUNTERS, 0x1000),
    (PackCfg.EDGE, 0xFFFF),
    (PackCfg.EDGE1, 0),
    (PackCfg.TILE_ROW_MAPPING, 0),
    (PackCfg.TILE_ROW_MAPPING1, 0),
  ):
    k.write(int(register), value)
  tile_bytes = BF16_TILE_BYTES if output_format == BF16 else F32_TILE_BYTES
  k.write(TensixMMIO.REGFILE_BASE + 16 * 4, tile_bytes >> 4)
  k.write(TensixMMIO.REGFILE_BASE + 52 * 4, 0x40000)
  for section, value in enumerate((0x0104, 0x2820, 0x1120)):
    _set_thread_cfg(k, PACK_ADDRESS_MODIFIER + section, value)
  k.emit(TT.TTSETADCXY(4, 0, 0, 0, 0, 0xB))
  k.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 0xF))
  pack = TT.TTPACR()
  configure_mop(k, _mop_loop_words(
    4, 4, loop=pack,
    last=TT.TTPACR(0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1),
    outer_last=TT.TTPACR(0, 0, 0, 2),
  ))
  pc_sync(k)


def _set_pack_destination(k: Asm, tile: int, output_address: int):
  if output_address % 16:
    raise ValueError("pack output must be 16-byte aligned")
  k.emit(TT.TTSETADC(4, 0, 3, tile))
  address = (output_address >> 4) - 1
  _set_dma_reg16(k, 24, address)
  high, valid = k.reg(2)
  k.li(high, address)
  k.srli(high, high, 16)
  k.li(valid, 0x8000)
  k.or_(valid, valid, high)
  _set_dma_reg16(k, 25, valid)
  stall(k, Stall.CFG, Wait.THCON | Wait.PACK0)
  k.emit(TT.TTWRCFG(12, 0, (int(PackCfg.L1_DESTINATION) - CFG_BASE) >> 2))
  _set_dma_reg16(k, 25, high)
  k.emit(TT.TTDMANOP())


def emit_pack_dst(k: Asm, tile: int, output_address: int, output_format: int,
                  *, configure=True, wait_for_dst=True):
  if wait_for_dst:
    sem_wait(k, Sem.MATH_PACK, SemWait.ON_ZERO, Stall.TDMA)
  if configure:
    configure_packer(k, output_format)
  _set_pack_destination(k, tile, output_address)
  k.emit(TT.TTSETADCXX(4, 15, 0))
  k.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
  k.write(PackCfg.DESTINATION_OFFSET, 0)
  stall(k, Stall.CFG, Wait.PACK0)
  run_mop(k)
  stall(k, Stall.SYNC, Wait.PACK0)
  pc_sync(k)


def finish_pack(k: Asm):
  sem_get(k, Sem.MATH_PACK)


def clear_sources(k: Asm):
  k.emit(TT.TTZEROSRC(0, 0, 1, 3))
  stall(k, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
