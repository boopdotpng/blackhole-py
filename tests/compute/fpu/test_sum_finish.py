"""Compare SFPU and FPU scalar finishes for 1024 values already in SrcA.

Run: python3 -m pytest tests/compute/fpu/test_sum_finish.py --bh-hardware --bh-core=1 -s -q
All paths share TF32 input, two first-stage fidelity phases and FP32 Dst.
The FPU finishes deliberately expose the precision loss on Dst -> Src transfers.
"""
from statistics import median
from struct import pack, unpack

import pytest

from asm import Asm
from isa import Tensix as TT
from tests.compute.fpu.test_mean import INPUT, WEIGHTS, OUTPUT, _add, _reduce_l0
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, UnpackCfg, UnpackTarget, Sem, SemWait, Stall, Wait,
  _engine_cfg, _mop_loop_words, _set_thread_cfg, _unpacr,
  configure_unpacker, configure_fp32_dst, configure_mop, load_replay,
  run_mop, pc_sync, publish_dst, sem_get, sem_post, sem_wait, stall,
  UNPACK_CONFIG_SYNC,
)
from tests.profiler import Profiler

FINISHES = ("sfpu", "fpu-transpose", "fpu-row")


def _finish(k, finish, op):
  if finish == "sfpu":
    stall(k, Stall.SFPU, Wait.MATH)
    k.emit(TT.TTSFPLOAD(0, 3, 3, 0))
    k.emit(TT.TTSFPLOAD(1, 3, 3, 2))
    _add(k, 0, 1, 0)
    _reduce_l0(k, vertical=False)
    k.emit(TT.TTSFPSTORE(0, 3, 3, 0))
    return

  # Transpose: partial row -> scratch B -> transpose -> A column (LLK style).
  # Row dot: partial row -> B[0], preloaded B[16:32] column of ones -> A.
  k.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  k.emit(TT.TTMOVD2B(0, 16 if finish == "fpu-transpose" else 0, 3, 0, 0))
  k.emit(TT.TTGATESRCRST(1, 1))
  if finish == "fpu-transpose":
    k.emit(TT.TTTRNSPSRCB())
    k.emit(TT.TTGATESRCRST(1, 1))
  for row in range(0, 16, 4):
    k.emit(TT.TTMOVB2A(row, 3, 2, 16 + row))
  k.emit(TT.TTGATESRCRST(1, 1))
  # First-stage row has been copied; clear the accumulation before reusing it.
  k.emit(TT.TTZEROACC(3, 1, 0, 3, 0))
  phase_mode = 4 if finish == "fpu-transpose" else 5
  k.emit(op(0, 0, phase_mode, 0, 0) if op == TT.TTGAPOOL else op(0, 0, phase_mode, 0))
  k.emit(op(0, 0, 6, 0, 0) if op == TT.TTGAPOOL else op(0, 0, 6, 0))


def _images(first, finish, *, split=False):
  loader, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  for engine, target in ((0, UnpackTarget.SRCA), (1, UnpackTarget.SRCB)):
    configure_unpacker(loader, engine, INPUT if engine == 0 else WEIGHTS,
                       F32, target, commit=False)
    loader.write(_engine_cfg(UnpackCfg.OPTIONS, engine), 0x24)  # TF32
  observed = loader.reg()
  loader.read(observed, _engine_cfg(UnpackCfg.BASE, 0))
  loader.write(UNPACK_CONFIG_SYNC, 0)
  loader.emit(TT.TTSETADCXX(3, 1023, 0))
  loader.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
  configure_mop(loader, _mop_loop_words(1, 1, start=_unpacr(0),
                loop=_unpacr(1), last=_unpacr(1), outer_last=_unpacr(1)))
  pc_sync(loader)
  sem_post(loader, Sem.UNPACK_TO_DEST)
  sem_wait(loader, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(loader, Sem.MATH_DONE)
  stall(loader, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
  run_mop(loader)
  stall(loader, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
  sem_get(loader, Sem.UNPACK_SYNC)
  pc_sync(loader)
  sem_post(loader, Sem.UNPACK_TO_DEST)

  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  configure_fp32_dst(math, 0)
  _set_thread_cfg(math, 11, 0)
  for mode, delta, fidelity in ((0, 16, 0), (1, 16, 1 << 13),
      (2, 16, 1 << 15), (3, 0, 0), (4, 0, 1 << 13),
      (5, 0, 2 << 13), (6, 0, 1 << 15)):
    _set_thread_cfg(math, 12 + mode, delta)
    _set_thread_cfg(math, 28 + mode, fidelity)
    _set_thread_cfg(math, 47 + mode, 0)
  math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
  math.emit(TT.TTSFPENCC(0, 0, 0, 2))
  # Establish a known lane configuration, including enabling Dst/source moves.
  math.emit(TT.TTSFPLOADI(0, 2, 0))
  math.emit(TT.TTSFPCONFIG(0, 15, 0))
  math.emit(TT.TTSFPNOP())
  op = TT.TTGAPOOL if first == "gapool" else TT.TTMVMUL
  def instruction(mode):
    return op(0, 0, mode, 0, 0) if first == "gapool" else op(0, 0, mode, 0)
  words = tuple(instruction(0 if i < 3 else last) for last in (1, 2) for i in range(4))
  load_replay(math, 0, words)
  stall(math, Stall.SYNC, Wait.MATH | Wait.SFPU)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  pc_sync(math)
  profile = Profiler(math)
  profile.record("empty")
  profile.record("empty")
  if not split: profile.record("L1 to L1")
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  stall(math, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
  math.emit(TT.TTGATESRCRST(1, 1))
  pc_sync(math)
  profile.record("reduction")
  math.emit(TT.TTREPLAY(0, len(words), 0, 0))
  if split:
    stall(math, Stall.SYNC, Wait.MATH)
    pc_sync(math)
    profile.record("finish")
  _finish(math, finish, op)
  stall(math, Stall.SYNC, Wait.MATH | Wait.SFPU)
  pc_sync(math)
  if split: profile.record("finish")
  profile.record("reduction")
  math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  publish_dst(math)
  sem_wait(math, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.MATH_DONE)
  if not split: profile.record("L1 to L1")
  count = packer.reg()
  packer.li(count, 16)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=F32)
  sem_post(packer, Sem.MATH_DONE)
  return {k.role: k.lower() for k in (loader, math, packer)}, profile


def _run(bh, images, finish, values, profile=None):
  weights = [1.] * 16 + [0.] * 1008
  if finish == "fpu-row":
    for row in range(16, 32): weights[row * 16] = 1.
  bh.launch(images, l1={INPUT: pack("<1024f", *values),
                       WEIGHTS: pack("<1024f", *weights),
                       OUTPUT: b"\xA5" * 128}, profiler=profile)
  result = unpack("<f", bh.read_l1(bh.core, OUTPUT, 4))[0]
  assert bh.read_l1(bh.core, OUTPUT + 64, 64) == b"\xA5" * 64
  return result


@pytest.mark.parametrize("first", ("gapool", "mvmul"))
@pytest.mark.parametrize("finish", FINISHES)
def test_sum_finish_cycles(bh, first, finish):
  values = list(range(1024))  # Exact in all paths, including partial transfers.
  for split in (False, True):
    images, profile = _images(first, finish, split=split)
    assert _run(bh, images, finish, values) == sum(values)  # unmeasured warmup
    samples = []
    for _ in range(11):
      assert _run(bh, images, finish, values, profile) == sum(values)
      samples.append(dict(profile.last))
    print(f"SUM {first}/{finish} split={split}: " + "; ".join(
      f"{label} median={median(s[label] for s in samples)}, "
      f"min={min(s[label] for s in samples)}, max={max(s[label] for s in samples)}"
      for label in profile.last))
  # Exact small signed integers and sparse values catch bad axes/bank selection.
  for values in ([1.] * 1024, [float(i % 17 - 8) for i in range(1024)]):
    assert _run(bh, images, finish, values) == sum(values)
  for index in (0, 1, 15, 16, 255, 256, 511, 512, 767, 768, 1022, 1023):
    values = [0.] * 1024
    values[index] = 1024.
    assert _run(bh, images, finish, values) == 1024.


@pytest.mark.parametrize("finish", FINISHES)
def test_sum_finish_precision(bh, finish):
  images, _ = _images("gapool", finish)
  # Every input is exactly representable by the first-stage TF32 multiplier.
  # The sum in column zero needs extra bits, lost only on the FPU round trip.
  values = [1.] * 1024
  values[0] += 1 / 512
  expected = sum(values) if finish == "sfpu" else 1024.
  actual = _run(bh, images, finish, values)
  assert actual == expected, (finish, actual, expected)
  print(f"PRECISION {finish}: exact={sum(values)}, actual={actual}")
  # Cancellation makes the loss of that small contribution conspicuous.
  values = [0.] * 1024
  for row in range(64):
    values[row * 16] = 1.
    values[row * 16 + 1] = -1.
  values[0] += 1 / 512
  expected = 1 / 512 if finish == "sfpu" else 0.
  actual = _run(bh, images, finish, values)
  assert actual == expected, (finish, actual, expected)
  print(f"CANCELLATION {finish}: exact={sum(values)}, actual={actual}")
