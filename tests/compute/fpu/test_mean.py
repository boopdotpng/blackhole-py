"""Raw arange(1024) mean: SrcA/SrcB FPU reductions versus an FP32 SFPU sum.

Input is materialized FP32 in L1, not a constant-folded arange expression.
FPU paths unpack to TF32 (exact for these integers), accumulate into FP32,
and finish in SFPU without narrowing partial sums through source registers.
"""
from statistics import median
from struct import pack, unpack

import pytest

from asm import Asm
from fw.consts import TensixL1
from isa import Tensix as TT
from tests.movement.packer.pack import emit_pack_dst_to_cb
from tests.movement.unpacker.unpack import (
  F32, UnpackCfg, UnpackTarget, Sem, SemWait, Stall, Wait,
  _engine_cfg, _mop_loop_words, _set_thread_cfg, _unpacr,
  configure_unpacker, configure_fp32_dst, configure_mop, load_replay,
  run_mop, pc_sync, publish_dst, sem_get, sem_post, sem_wait, stall, UNPACK_CONFIG_SYNC,
)
from tests.profiler import Profiler

INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
WEIGHTS = INPUT + 4096
OUTPUT = WEIGHTS + 4096
SAMPLES = 7
PATHS = ("srcA-gapool", "srcA-mvmul", "srcB-mvmul", "srcA-gapool-scaled", "srcA-mvmul-scaled", "srcB-mvmul-scaled", "sfpu")


def _emit(k, *words):
  for word in words:
    k.emit(word)


def _add(k, a, b, dest):
  k.emit(TT.TTSFPADD(a, 10, b, dest, 0))


def _reduce_l0(k, *, horizontal=True, vertical=True):
  # Reduce only the dimensions containing nonzero partials. Full FP32 input
  # needs both steps; A column sums need horizontal, B row sums need vertical.
  for distance in ((4, 2, 1) if horizontal else ()):
    k.emit(TT.TTSFPMOV(0, 0, 1, 0))
    for _ in range(distance):
      k.emit(TT.TTSFPSHFT2(0, 1, 1, 3))
    _add(k, 0, 1, 0)
  if not vertical:
    return
  for reg in (1, 2, 3):
    k.emit(TT.TTSFPMOV(0, 0, reg, 0))
  k.emit(TT.TTSFPTRANSP(0, 0, 0, 0))
  for reg in (1, 2, 3):
    _add(k, 0, reg, 0)


def _images(path):
  loader, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  fpu = path != "sfpu"
  data_b = path.startswith("srcB")
  if fpu:
    for engine, target in ((0, UnpackTarget.SRCA), (1, UnpackTarget.SRCB)):
      address = INPUT if engine == int(data_b) else WEIGHTS
      configure_unpacker(loader, engine, address, F32, target, commit=False)
      # Format 4 = TF32. The BF16 control deliberately discards input bits.
      bf16 = path.endswith("bf16")
      loader.write(_engine_cfg(UnpackCfg.OPTIONS, engine), 0x20 | (5 if bf16 else 4))
      if bf16:
        loader.write(_engine_cfg(UnpackCfg.ADDRESS_XY1, engine), 2 | 32 << 16)
        loader.write(_engine_cfg(UnpackCfg.ADDRESS_ZW1, engine), 512)
        loader.write(_engine_cfg(UnpackCfg.ADDRESS_ZW1, engine) + 4, 2048)
    observed = loader.reg()
    loader.read(observed, _engine_cfg(UnpackCfg.BASE, 0))
    loader.write(UNPACK_CONFIG_SYNC, 0)
    _emit(loader, TT.TTSETADCXX(3, 1023, 0), TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    configure_mop(loader, _mop_loop_words(1, 1, start=_unpacr(0),
                  loop=_unpacr(1), last=_unpacr(1), outer_last=_unpacr(1)))
  else:
    configure_unpacker(loader, 0, INPUT, F32, UnpackTarget.DST)
    _emit(loader, TT.TTSETADCXX(1, 255, 0), TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    load_replay(loader, 0, (_unpacr(0, to_dst=True), TT.TTSTALLWAIT(Stall.UNPACK, Wait.UNPACK0)))
    replay = TT.TTREPLAY(0, 2, 0, 0)
    configure_mop(loader, _mop_loop_words(1, 4, loop=replay, last=replay))
  pc_sync(loader)
  sem_post(loader, Sem.UNPACK_TO_DEST)  # Configuration ready, no data yet.
  sem_wait(loader, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.UNPACK)
  sem_get(loader, Sem.MATH_DONE)
  if fpu:
    stall(loader, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
  run_mop(loader)
  stall(loader, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
  sem_get(loader, Sem.UNPACK_SYNC)
  pc_sync(loader)
  sem_post(loader, Sem.UNPACK_TO_DEST)

  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  configure_fp32_dst(math, 0)
  _set_thread_cfg(math, 11, 0)
  # Mode 0 steps along data, mode 1 wraps data and advances fidelity,
  # mode 2 wraps data and resets fidelity, mode 3 leaves all counters alone.
  step, blocks, phase_step = (8, 8, 2) if data_b else (16, 4, 1)
  for mode, delta, fidelity in ((0, step, 0), (1, step, phase_step << 13),
                                 (2, step, 1 << 15), (3, 0, 0)):
    _set_thread_cfg(math, 12 + mode, (delta << 8) if data_b else delta)
    _set_thread_cfg(math, 28 + mode, fidelity)
    _set_thread_cfg(math, 47 + mode, 0)
  _emit(math, TT.TTSETRWC(0, 0, 0, 0, 0, 0xF), TT.TTSFPENCC(0, 0, 0, 2))
  if fpu:
    def ins(mod):
      return TT.TTGAPOOL(0, 0, mod, 0, 0) if "gapool" in path else TT.TTMVMUL(0, 0, mod, 0)
    words = tuple(ins(0 if i < blocks-1 else last) for last in (1, 2) for i in range(blocks))
    load_replay(math, 0, words)
  stall(math, Stall.SYNC, Wait.MATH | Wait.SFPU)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  pc_sync(math)
  profile = Profiler(math)
  profile.record("empty")
  profile.record("empty")
  profile.record("L1 to L1")
  sem_post(math, Sem.MATH_DONE)
  sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.UNPACK_TO_DEST)
  if fpu:
    stall(math, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
  pc_sync(math)
  profile.record("reduction")
  if fpu:
    math.emit(TT.TTREPLAY(0, len(words), 0, 0))
    stall(math, Stall.SFPU, Wait.MATH)
  # A path: only row 0 contains 16 column sums. B path: only column 0
  # contains eight row sums. Remaining positions are explicitly zero.
  positions = ((0, 4) if data_b else (0, 2)) if fpu else tuple(range(0, 64, 2))
  math.emit(TT.TTSFPLOAD(0, 3, 3, 0))
  for position in positions[1:]:
    math.emit(TT.TTSFPLOAD(1, 3, 3, position))
    _add(math, 0, 1, 0)
  _reduce_l0(math, horizontal=not data_b, vertical=data_b or not fpu)
  # 1/1024 is exactly representable. No general division or reciprocal needed.
  if not path.endswith("scaled"):
    math.emit(TT.TTSFPMULI(0x3A80, 0, 0))
  math.emit(TT.TTSFPSTORE(0, 3, 3, 0))
  stall(math, Stall.SYNC, Wait.SFPU)
  pc_sync(math)
  profile.record("reduction")
  if fpu:
    math.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  publish_dst(math)
  sem_wait(math, Sem.MATH_DONE, SemWait.ON_ZERO, Stall.SYNC)
  sem_get(math, Sem.MATH_DONE)
  profile.record("L1 to L1")

  count = packer.reg()
  packer.li(count, 16)
  emit_pack_dst_to_cb(packer, 0, OUTPUT, count, output_format=F32)
  sem_post(packer, Sem.MATH_DONE)
  return {k.role: k.lower() for k in (loader, math, packer)}, profile


@pytest.mark.parametrize("path", PATHS)
def test_arange1024_mean(bh, path):
  images, profile = _images(path)
  # Row-major stream of four consecutive 16x16 chunks. A input reduces
  # columns; B input reduces rows. Do not transpose/reorder input on the host.
  weights = [float(i % 16 == 0) for i in range(1024)] if path.startswith("srcB") else [float(i < 16) for i in range(1024)]
  if path.endswith("scaled"):
    weights = [x / 1024 for x in weights]
  timings = []
  def run(values, *, timed=False):
    bh.launch(images, l1={INPUT: pack("<1024f", *values), WEIGHTS: pack("<1024f", *weights),
                        OUTPUT: b"\xA5" * 128}, profiler=profile if timed else None)
    result = unpack("<f", bh.read_l1(bh.core, OUTPUT, 4))[0]
    assert result == sum(values) / 1024, (path, result, sum(values)/1024)
    assert bh.read_l1(bh.core, OUTPUT+64, 64) == b"\xA5" * 64
  for _ in range(SAMPLES):
    run(list(range(1024)), timed=True)
    timings.append(dict(profile.last))
  # Non-arange inputs reject accidental formula evaluation, incomplete
  # coverage, and dependence on monotonic values. Sparse inputs exercise
  # every 128-element source block and both SFPU lane parities.
  run([((i*173+31) % 1024)-512 for i in range(1024)])
  for slot in range(8):
    for offset in (0, 1, 126, 127):
      values = [0.] * 1024
      values[slot*128 + offset] = 1024.
      run(values)
  print(f"{path}: arange mean=511.5, permuted signed mean=-0.5; " + "; ".join(
    f"{label} median={median(t[label] for t in timings)}, min={min(t[label] for t in timings)}, max={max(t[label] for t in timings)} cycles"
    for label in ("reduction", "L1 to L1", "empty")))


def test_mean_bf16_precision_control(bh):
  """FP32 accumulation cannot restore the bits discarded on input."""
  images, _ = _images("srcA-gapool-bf16")
  bh.launch(images, l1={INPUT: pack("<1024f", *range(1024)),
                      WEIGHTS: pack("<1024f", *([1.]*16 + [0.]*1008)),
                      OUTPUT: b"\xA5" * 128})
  result = unpack("<f", bh.read_l1(bh.core, OUTPUT, 4))[0]
  bits = unpack("<1024I", pack("<1024f", *range(1024)))
  truncated = unpack("<1024f", pack("<1024I", *(x & 0xFFFF0000 for x in bits)))
  assert result == sum(truncated) / 1024 == 510.625
  assert bh.read_l1(bh.core, OUTPUT+64, 64) == b"\xA5" * 64
  print("BF16 input truncation + FP32 Dst: mean=510.625; exact input mean=511.5")
