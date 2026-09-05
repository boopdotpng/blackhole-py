"""Prepared FP32 L1-to-Dst latency; source paths convert through BF16."""
from statistics import median
from struct import pack

import pytest

from asm import Asm
from isa import Tensix as TT
from fw.consts import TensixL1
from tests.profiler import Profiler
from tests.movement.unpacker.unpack import (
  BF16, F32, UnpackCfg, _engine_cfg, UnpackTarget, Sem, SemWait, Stall, Wait, _set_thread_cfg,
  _unpacr, _mop_loop_words, configure_unpacker, configure_mop, run_mop,
  load_replay, stall, sem_wait, sem_get, sem_post, pc_sync, publish_dst,
  emit_pack_dst, finish_pack, configure_fp32_dst,
)

INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
OUTPUT = INPUT + 4096


def _images(path, elements):
  loader, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  direct = path == "direct"
  engine = int(path == "srcB")
  target = UnpackTarget.DST if direct else (UnpackTarget.SRCB if engine else UnpackTarget.SRCA)
  configure_unpacker(loader, engine, INPUT, F32, target)
  if not direct:
    # FP32 input converted to BF16 in source registers; test values are exact BF16.
    loader.write(_engine_cfg(UnpackCfg.OPTIONS, engine), 0x20 | BF16)
    loader.write(_engine_cfg(UnpackCfg.ADDRESS_XY1, engine), 2 | 32 << 16)
    loader.write(_engine_cfg(UnpackCfg.ADDRESS_ZW1, engine), 512)
    loader.write(_engine_cfg(UnpackCfg.ADDRESS_ZW1, engine) + 4, 2048)
  loader.emit(TT.TTSETADCXX(engine + 1, min(elements, 256) - 1 if direct else elements - 1, 0))
  loader.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  if direct:
    load_replay(loader, 0, (_unpacr(0, to_dst=True), TT.TTSTALLWAIT(Stall.UNPACK, Wait.UNPACK0)))
    replay = TT.TTREPLAY(0, 2, 0, 0)
    configure_mop(loader, _mop_loop_words(1, max(1, elements // 256), loop=replay, last=replay))
  else:
    configure_mop(loader, _mop_loop_words(1, 1, start=_unpacr(engine)))
  pc_sync(loader)

  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  configure_fp32_dst(math, 0)
  if not direct:
    step = 4 if engine else 8
    _set_thread_cfg(math, 14, step << 8 if engine else step)
    _set_thread_cfg(math, 30, step)
    _set_thread_cfg(math, 49, 0)
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    move = TT.TTMOVB2D(0, 0, 2, 4, 0) if engine else TT.TTMOVA2D(0, 0, 2, 2, 0)
    configure_mop(math, _mop_loop_words(1, elements // (step * 16), loop=move, last=move))
  stall(math, Stall.SYNC, Wait.MATH)
  pc_sync(math)
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  if not direct:
    stall(math, Stall.MATH, Wait.SRCB_VLD if engine else Wait.SRCA_VLD)
    run_mop(math)
    math.emit(TT.TTSETRWC(2 if engine else 1, 0, 0, 0, 0, 0xF))
  stall(math, Stall.SYNC, Wait.MATH)
  pc_sync(math)
  sem_post(math, Sem.MATH_DONE)
  # Keep pack out of the measured interval, including the acknowledgement.
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  publish_dst(math)

  sem_wait(loader, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(loader, Sem.MATH_DONE)
  pc_sync(loader)
  profile = Profiler(loader)
  profile.record("L1 to Dst ready")
  run_mop(loader)
  stall(loader, Stall.UNPACK, Wait.UNPACK1 if engine else Wait.UNPACK0)
  sem_get(loader, Sem.UNPACK_SYNC)
  sem_post(loader, Sem.UNPACK_TO_DEST)
  sem_wait(loader, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(loader, Sem.MATH_DONE)
  pc_sync(loader)
  profile.record("L1 to Dst ready")
  sem_post(loader, Sem.UNPACK_TO_DEST)

  emit_pack_dst(packer, 0, OUTPUT, F32)
  finish_pack(packer)
  return {k.role: k.lower() for k in (loader, math, packer)}, profile


@pytest.mark.parametrize("elements", (128, 1024))
@pytest.mark.parametrize("path", ("direct", "srcA", "srcB"))
def test_l1_to_dst_paths(bh, path, elements):
  images, profile = _images(path, elements)
  source = pack("<1024I", *((0x3C00 + i) << 16 for i in range(1024)))
  expected = source[:elements * 4] + bytes((1024-elements)*4)
  samples = []
  for _ in range(15):
    bh.launch(images, l1={INPUT: source, OUTPUT: b"\xA5" * 4160}, profiler=profile)
    assert bh.read_l1(bh.core, OUTPUT, 4096) == expected
    assert bh.read_l1(bh.core, OUTPUT+4096, 64) == b"\xA5" * 64
    samples.append(profile.last["L1 to Dst ready"])
  print(f"{path} {elements}: median={median(samples)}, min={min(samples)}, max={max(samples)} cycles")


@pytest.mark.parametrize("path", ("direct", "srcA", "srcB"))
def test_dst_path_precision(bh, path):
  images, profile = _images(path, 128)
  bits = [0x3F800001 + i * 1031 for i in range(1024)]
  expected = bits[:128] if path == "direct" else [x & 0xFFFF0000 for x in bits[:128]]
  bh.launch(images, l1={INPUT: pack("<1024I", *bits), OUTPUT: b"\xA5" * 4160}, profiler=profile)
  assert bh.read_l1(bh.core, OUTPUT, 4096) == pack("<1024I", *expected, *([0] * 896))
  assert bh.read_l1(bh.core, OUTPUT+4096, 64) == b"\xA5" * 64
