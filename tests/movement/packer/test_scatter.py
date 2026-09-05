"""Time 512 FP32 Dst values packed to dense BF16, then written to DRAM."""

from statistics import median
from struct import pack

from asm import Asm
from fw.consts import TensixL1, TensixMMIO
from isa import Tensix as TT
from tests.movement.packer.pack import _configure_row_addressing, _set_dst_position
from tests.movement.unpacker.unpack import (
  BF16, F32_TILE_BYTES, PackCfg, Sem, SemWait, Stall, Wait,
  _set_pack_destination, _set_thread_cfg, configure_packer,
  emit_unpack_to_dst, load_replay, pc_sync, publish_dst, sem_get, sem_post, sem_wait, stall,
)
from tests.profiler import Profiler


INPUT = TensixL1.DATA_BUFFER_SPACE_BASE
OUTPUT = INPUT + 8 * F32_TILE_BYTES
REPEATS = 32
SAMPLES = 5
STRIDES = (1, 2, 4, 8, 16, 21)
CASES = (("contiguous", 1, False, True, False),) + tuple(
  (f"{mode} stride {stride}", stride, True, drain, linear)
  for mode, drain, linear in (
    ("drained", True, False), ("queued", False, False),
    ("one counter", False, True),
  )
  for stride in STRIDES
)


def _images(slots, split, dram, *, drain=True, linear=False, reuse_output=False, interfaces=1):
  unpacker, math, packer = (Asm(role) for role in ("trisc0", "trisc1", "trisc2"))
  math.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  stall(math, Stall.SYNC, Wait.MATH)
  # Initialize only the tiles we use. Every setup handoff is consumed before
  # timing starts; neither unpack latency nor math ownership waits are timed.
  for tile in sorted({slot // 8 for slot in slots}):
    size = unpacker.reg()
    unpacker.li(size, F32_TILE_BYTES)
    emit_unpack_to_dst(unpacker, INPUT + tile * F32_TILE_BYTES, size, tile, 0)
    sem_wait(math, Sem.MATH_DONE, SemWait.ON_MAX, Stall.SYNC)
    sem_post(math, Sem.MATH_DONE)
    sem_wait(math, Sem.UNPACK_TO_DEST, SemWait.ON_ZERO, Stall.SYNC)
    sem_get(math, Sem.UNPACK_TO_DEST)
    publish_dst(math)
    sem_wait(packer, Sem.MATH_PACK, SemWait.ON_ZERO, Stall.TDMA)
    sem_get(packer, Sem.MATH_PACK)

  configure_packer(packer, BF16)
  _configure_row_addressing(packer)
  _set_thread_cfg(packer, 37, interfaces)
  packer.write(PackCfg.DESTINATION_OFFSET, 0)
  packer.emit(TT.TTSETADCXX(4, 15, 0))
  requests = 32 // interfaces
  normal = TT.TTPACR(ReadIntfSel=(1 << interfaces) - 1)
  final = TT.TTPACR(ReadIntfSel=(1 << interfaces) - 1, AddrMode=1, Last=1)
  load_replay(packer, 0, [normal] * (requests - 1) + [final])
  if reuse_output:
    _set_pack_destination(packer, 0, OUTPUT)
  pc_sync(packer)

  def pack_once():
    if not reuse_output:
      _set_pack_destination(packer, 0, OUTPUT)
    if split:
      if linear:
        packer.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
      for index, slot in enumerate(slots):
        if index and drain:
          # Conservative boundary drain before replacing the input counters.
          stall(packer, Stall.SYNC, Wait.PACK0)
        if linear:
          # Y can address all 512 logical FP32 rows; Z and W stay zero.
          packer.emit(TT.TTSETADC(4, 0, 1, slot * 8))
        else:
          _set_dst_position(packer, slot // 8, slot % 8 * 128)
        segment = 8 // interfaces
        packer.emit(TT.TTREPLAY(index * segment, segment, 0, 0))
    else:
      _set_dst_position(packer, 0, 0)
      packer.emit(TT.TTREPLAY(0, requests, 0, 0))
    stall(packer, Stall.SYNC, Wait.PACK0)
    pc_sync(packer)

  pack_once()  # warm the configured path
  profile = Profiler(packer)
  profile.record("pack batch")
  for _ in packer.range(REPEATS):
    pack_once()
  profile.record("pack batch")

  # Same one-packet, acknowledged 1024-byte DRAM write for all placements.
  niu, tid = 0xFFB20000, 1
  coordinate = packer.reg()
  packer.read(coordinate, niu + 0x148)
  packer.slli(coordinate, coordinate, 20)
  packer.srli(coordinate, coordinate, 20)
  packer.wait(niu + 0x40, 0)
  for index, value in enumerate((
    OUTPUT, 0, coordinate, dram.address, 0, dram.coordinate,
    tid << 10, (1 << 1) | (1 << 4) | (1 << 7) | (1 << 13),
    1024, 0, 0, 0, 0, 0, 0,
  )):
    packer.write(niu + index * 4, value)
  profile.record("DRAM write")
  packer.write(niu + 0x40, 1)
  packer.wait(niu + 0x40, 0)
  packer.wait(niu + 0x280 + tid * 4, 0)
  packer.wait(niu + 0x240 + tid * 4, 0)
  profile.record("DRAM write")
  images = {k.role: k.lower() for k in (unpacker, math, packer)}
  return images, profile


def _run_cases(bh, cases, *, reuse_output=False, interfaces=1):
  dram = bh.dram_buffer(1024)
  # Unique BF16-exact values across the entire Dst expose address mistakes,
  # including wrong tiles, order, repeated blocks, and high/low-half aliasing.
  words = tuple(0x3F00 + index for index in range(8192))
  source = pack("<8192I", *(word << 16 for word in words))
  results = []
  for name, stride, split, drain, linear in cases:
    slots = tuple(index * stride for index in range(4))
    expected = pack("<512H", *(words[slot * 128 + i] for slot in slots for i in range(128)))
    images, profile = _images(slots, split, dram, drain=drain, linear=linear,
                             reuse_output=reuse_output, interfaces=interfaces)
    samples, writes = [], []
    for _ in range(SAMPLES):
      bh.launch(images, l1={INPUT: source, OUTPUT: b"\xA5" * 1088}, profiler=profile)
      assert bh.read(dram) == expected
      assert bh.read_l1(bh.core, OUTPUT + 1024, 64) == b"\xA5" * 64
      samples.append(profile.last["pack batch"] / REPEATS)
      writes.append(profile.last["DRAM write"])
    results.append((name, slots, median(samples), min(samples), max(samples), median(writes)))
  print(f"\n512 elements, FP32 Dst -> BF16 L1 -> DRAM; {interfaces} read interface(s), "
        f"reuse output={reuse_output}; cycles per pack")
  print("case                 slots                 median     min     max  DRAM median")
  for name, slots, mid, low, high, write in results:
    print(f"{name:20} {str(slots):21} {mid:8.1f} {low:7.1f} {high:7.1f} {write:12.0f}")


def test_pack_contiguous_vs_scattered_dst_to_dram(bh):
  _run_cases(bh, CASES)


def test_pack_reused_output_address_to_dram(bh):
  cases = (("fixed contiguous", 1, False, False, True),) + tuple(
    (f"fixed output stride {stride}", stride, True, False, True)
    for stride in STRIDES
  )
  _run_cases(bh, cases, reuse_output=True)


def test_pack_four_read_interfaces_to_dram(bh):
  cases = (("4 interfaces contiguous", 1, False, False, True),) + tuple(
    (f"4 interfaces stride {stride}", stride, True, False, True)
    for stride in STRIDES
  )
  _run_cases(bh, cases, reuse_output=True, interfaces=4)
