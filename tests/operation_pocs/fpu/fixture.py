"""Broad fixture-only initialization and observation; never part of the emitter."""
from asm import Asm
from firmware.consts import TensixL1
from ttko.isa import Tensix as TT
from tests.operation_pocs.fpu.observation import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  BF16, CFG_BASE, _rmw_cfg_byte, F32, F32_TILE_BYTES, Sem, SemWait, Stall, Wait, UNPACKER0, UNPACKER1,
  _mop_loop_words, _set_thread_cfg, _unpacr, configure_fp32_dst,
  configure_mop, configure_unpack_pair,
  emit_unpack_to_dst, load_replay, pc_sync, publish_dst, run_mop, sem_get, sem_post, sem_wait, stall,
)
from tests.profiler import Profiler


from tests.operation_pocs.fpu.emit import prepare, execute

INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
INPUT_A = INPUT + 4096
INPUT_B = INPUT_A + 2048
OUTPUT = INPUT_B + 2048
REPEATS = 16

def images(op, a, b, dst, broadcast=0, accumulate=True, fidelity=2, observe=None, fp32=True, repeats=REPEATS, output_tile=None):
  loader, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  size = loader.reg()
  loader.li(size, F32_TILE_BYTES)
  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(math, Stall.SYNC, Wait.MATH)
  # Poison every FP32 allocation before the operation, including distant tiles.
  for tile in range(8):
    emit_unpack_to_dst(loader, INPUT, size, tile, 0)
    sem_wait(math, Sem.MATH_DONE, SemWait.ON_MAX, Stall.SYNC)
    sem_post(math, Sem.MATH_DONE)
    sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
    sem_get(math, Sem.UNPACK_TO_DEST)

  # Load a complete bank in one UNPACR per source, with one bank handoff.
  # Unused slots hold distractors; input placement is outside the timer.
  configure_unpack_pair(loader, INPUT_A, INPUT_B)
  loader.emit(TT.TTSETADCXX(3, 1023, 0))
  stall(loader, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
  configure_mop(loader, _mop_loop_words(
    1, 1, start=_unpacr(UNPACKER0), loop=_unpacr(UNPACKER1),
    last=_unpacr(UNPACKER1), outer_last=_unpacr(UNPACKER1),
  ))
  run_mop(loader)
  stall(loader, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
  sem_get(loader, Sem.UNPACK_SYNC)
  pc_sync(loader)

  configure_fp32_dst(math, 0)
  stall(math, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
  pc_sync(math)
  if not fp32:
    # Broad BF16 fixture: copy known source A into the full observation tile.
    _rmw_cfg_byte(math, CFG_BASE + 4, 3, 0x20, 0)
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    for reg in (12, 28, 47): _set_thread_cfg(math, reg, 0)
    for slot in range(128): math.emit(TT.TTMOVA2D(0, (slot%8)*8, 0, 2, slot*8))
    stall(math, Stall.SYNC, Wait.MATH)
    pc_sync(math)
  profile = Profiler(math)
  profile.record("control")
  profile.record("control")
  profile.record("complete")
  prepare(math, op, a, b, dst, broadcast=broadcast, accumulate=accumulate, fidelity=fidelity, repeats=repeats, fp32=fp32)
  pc_sync(math)
  profile.record("operation")
  execute(math)
  profile.record("operation")
  profile.record("complete")
  # Observation-only source snapshot uses this initialized Dst tile as scratch.
  if observe:
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    _set_thread_cfg(math, 12, 0)
    _set_thread_cfg(math, 28, 0)
    for slot in range(8):
      if observe == 'a': math.emit(TT.TTMOVA2D(0, slot*8, 0, 2, (dst//8)*64+slot*8))
      else:
        for row in (0, 4): math.emit(TT.TTMOVB2D(0, slot*8+row, 0, 4, (dst//8)*64+slot*8+row))
    stall(math, Stall.SYNC, Wait.MATH)
    pc_sync(math)
  math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  publish_dst(math)
  count = packer.reg()
  packer.li(count, 1024)
  emit_pack_dst_to_cb(packer, dst//8 if output_tile is None else output_tile, OUTPUT, count, output_format=F32 if fp32 else BF16)
  return {k.role: k.lower() for k in (loader, math, packer)}, profile
