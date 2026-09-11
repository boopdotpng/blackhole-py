"""Scattered pack formats/order/tails and a wrapping two-page CB.

Logical slots hold 128 elements (two physical units for FP32, one for BF16).
Native PACRs gather full blocks without intermediate drains. Exact tails use
one final bounded L1 copy because PACR may pad its last output word.
"""
from statistics import median
from struct import pack

import pytest

from asm import Asm
from fw.consts import TensixL1, TensixMMIO
from isa import R, Tensix as TT
from tests.movement import noc
from tests.movement.packer.pack import _configure_row_addressing
from tests.movement.unpacker import unpack as u
from tests.operation_pocs.runtime.ops import cb_action
from tests.operation_pocs.transport.ops import copy_bytes
from tests.operation_pocs.transport.test_source import seed_source
from tests.profiler import Profiler


BASE = TensixL1.DATA_BUFFER_SPACE_BASE
INPUT, OUTPUT, SCRATCH, OBSERVE = BASE, BASE + 0x10000, BASE + 0x15000, BASE + 0x18000
ARCHIVE, READY, COUNTERS = BASE + 0x22000, BASE + 0x30000, BASE + 0x30010
PAGE_BYTES = 8192
GUARD = b'\xa5' * 64


def source_words(fp32):
  # Unique, finite, exactly BF16-representable values, including both signs.
  return [((0x1800 + i) | (0x8000 if i % 3 == 0 else 0)) << 16
          for i in range(8192 if fp32 else 16384)]


def encode(words, fmt):
  return pack(f'<{len(words)}I', *words) if fmt == u.F32 else pack(f'<{len(words)}H', *(w >> 16 for w in words))


def initialize_dst(loader, math, fp32):
  if fp32:
    size = loader.reg(); loader.li(size, 32768)
    u.emit_unpack_to_dst(loader, INPUT, size, 0, 0)
    u.sem_post(math, u.Sem.MATH_DONE)
    u.sem_wait(math, u.Sem.UNPACK_TO_DEST, u.SemWait.ON_ZERO, u.Stall.SYNC)
    u.sem_get(math, u.Sem.UNPACK_TO_DEST)
    u.configure_fp32_dst(math, 0)
  else:
    # Sixteen different full source banks populate all native BF16 Dst slots.
    # Runtime loops keep the fixture within the firmware text partitions.
    for tile in loader.range(16):
      address, offset = loader.reg(2)
      loader.slli(offset, tile, 11); loader.li(address, INPUT); loader.add(address, address, offset)
      u.stall(loader, u.Stall.UNPACK, u.Wait.SRCA_CLR)
      seed_source(loader, u.UnpackTarget.SRCA, address, publish=True)
    u._set_thread_cfg(math, 1, 0)
    u._rmw_cfg_byte(math, u.CFG_BASE + 4, 3, 0x20, 0)
    for reg in (12, 28, 47): u._set_thread_cfg(math, reg, 0)
    math.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    for _ in math.range(16):
      u.stall(math, u.Stall.MATH, u.Wait.SRCA_VLD)
      for row in range(0, 64, 8):
        math.emit(TT.TTMOVA2D(0, row, 0, 2, 0))
        math.emit(TT.TTINCRWC(0, 8, 0, 0))
      u.stall(math, u.Stall.SYNC, u.Wait.MATH)
      math.emit(TT.TTCLEARDVALID(1, 0))
      u.pc_sync(math)
  u.publish_dst(math)


def configure(k, fp32, output_format, interfaces):
  u.configure_packer(k, output_format)
  # Dst storage width and packed output format are independent.
  source_format = output_format if fp32 else u.BF16
  source_bytes = 4 if source_format == u.F32 else 2
  u._rmw_cfg_byte(k, u.PackCfg.ALU_FORMAT, 3, 0x1E, source_format << 1)
  k.write(u.PackCfg.DATA_FORMAT, 1 | output_format << 4 | source_format << 8)
  k.write(u.PackCfg.DESTINATION_READ, int(fp32))
  k.write(u.PackCfg.ADDRESS_XY, 16 * source_bytes << 16)
  k.write(u.PackCfg.ADDRESS_ZW, 256 * source_bytes | 1024 * source_bytes << 16)
  _configure_row_addressing(k)
  u._set_thread_cfg(k, 37, interfaces)
  k.write(u.PackCfg.DESTINATION_OFFSET, 0)
  u.load_replay(k, 0, [TT.TTPACR(ReadIntfSel=(1 << interfaces) - 1)] * (8 // interfaces))


def scatter(k, slots, tail, interfaces, destination, *, slot_shift=None, capacity=64):
  u._set_pack_destination(k, 0, destination)
  k.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 5))
  k.emit(TT.TTSETADCXX(4, 15, 0))
  for index, slot in enumerate(slots):
    if slot_shift is None:
      k.emit(TT.TTSETADC(4, 0, 1, slot * 8))
    else:
      # A different logical slot shift on every CB publication catches stale pages.
      row, word, base = k.reg(3)
      k.addi(row, slot_shift, slot); k.andi(row, row, capacity - 1)
      k.slli(row, row, 3)
      k.li(base, TT.TTSETADC(4, 0, 1, 0)); k.or_(word, base, row)
      k.write(TensixMMIO.INSTRN_BUF_BASE, word)
    n = tail if index == len(slots) - 1 else 128
    if n == 128:
      if index != len(slots) - 1:
        k.emit(TT.TTREPLAY(0, 8 // interfaces, 0, 0))
      else:
        if 8 // interfaces > 1: k.emit(TT.TTREPLAY(0, 8 // interfaces - 1, 0, 0))
        k.emit(TT.TTPACR(ReadIntfSel=(1 << interfaces) - 1, AddrMode=1, Last=1))
    else:
      # Single-interface final block gives exact logical N; final L1 padding is
      # confined to caller-owned scratch, then copied with an exact byte count.
      u._set_thread_cfg(k, 37, 1)
      rows, remainder = divmod(n, 16)
      for row in range(rows):
        final = row == rows - 1 and not remainder
        k.emit(TT.TTPACR(ReadIntfSel=1, AddrMode=int(final), Last=int(final)))
      if remainder:
        k.emit(TT.TTSETADCXX(4, remainder - 1, 0))
        k.emit(TT.TTPACR(ReadIntfSel=1, AddrMode=1, Last=1))
      u._set_thread_cfg(k, 37, interfaces)
  u.stall(k, u.Stall.SYNC, u.Wait.PACK0)
  u.pc_sync(k)


def observe_all(k, fp32):
  configure(k, fp32, u.F32 if fp32 else u.BF16, 1)
  u._set_pack_destination(k, 0, OBSERVE)
  k.emit(TT.TTSETADCXY(4, 0, 0, 0, 0, 0xF))
  k.emit(TT.TTSETADCZW(4, 0, 0, 0, 0, 0xF))
  k.emit(TT.TTSETADCXX(4, 15, 0))
  normal = TT.TTPACR(ReadIntfSel=1)
  final = TT.TTPACR(ReadIntfSel=1, AddrMode=1, Last=1)
  # MOP's inner count cannot represent 1024; keep the stream open between halves.
  for last in ((True,) if fp32 else (False, True)):
    u.configure_mop(k, u._mop_loop_words(1, 512, loop=normal, last=final if last else normal))
    u.run_mop(k)
  u.stall(k, u.Stall.SYNC, u.Wait.PACK0); u.pc_sync(k)


def images(fp32, output_format, slots, tail=128, interfaces=1, output_offset=64):
  loader, math, packer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2'))
  initialize_dst(loader, math, fp32)
  u.sem_wait(packer, u.Sem.MATH_PACK, u.SemWait.ON_ZERO, u.Stall.TDMA)
  configure(packer, fp32, output_format, interfaces)
  p = Profiler(packer)
  p.record('scatter pack')
  scatter(packer, slots, tail, interfaces, SCRATCH if tail != 128 else OUTPUT + output_offset)
  p.record('scatter pack')
  if tail != 128:
    n = packer.reg(); packer.li(n, ((len(slots) - 1) * 128 + tail) * (4 if output_format == u.F32 else 2))
    copy_bytes(packer, SCRATCH, OUTPUT + output_offset, n)
  observe_all(packer, fp32)
  u.sem_get(packer, u.Sem.MATH_PACK)
  return {k.role: k.lower() for k in (loader, math, packer)}, p


def expected(words, slots, tail=128):
  return [w for index, slot in enumerate(slots)
          for w in words[slot * 128:slot * 128 + (tail if index == len(slots) - 1 else 128)]]


@pytest.mark.parametrize('fp32', (True, False), ids=('fp32-dst', 'bf16-dst'))
@pytest.mark.parametrize('output_format', (u.BF16, u.F32), ids=('bf16-out', 'fp32-out'))
@pytest.mark.parametrize('interfaces', (1, 4))
@pytest.mark.parametrize('order', ('contiguous', 'reverse', 'irregular', 'eight', 'repeat'))
def test_scatter_pack_formats_and_order(bh, fp32, output_format, interfaces, order):
  last = 63 if fp32 else 127
  slots = {'contiguous': (0, 1, 2, 3), 'reverse': (last, last-1, last-2, last-3),
           'irregular': (last, 0, 17, 4), 'eight': (last, 0, 17, 4, 31, 8, 55, 2),
           'repeat': (last, 0, last, 17)}[order]
  check_pack(bh, fp32, output_format, slots, 128, interfaces, 64)


@pytest.mark.parametrize('fp32', (True, False), ids=('fp32-dst', 'bf16-dst'))
@pytest.mark.parametrize('output_format', (u.BF16, u.F32), ids=('bf16-out', 'fp32-out'))
@pytest.mark.parametrize('tail,offset', ((1, 17), (17, 66), (127, 79)))
def test_scatter_pack_exact_tail(bh, fp32, output_format, tail, offset):
  check_pack(bh, fp32, output_format, (63 if fp32 else 127, 0, 17, 4), tail, 4, offset)


def check_pack(bh, fp32, output_format, slots, tail, interfaces, offset):
  code, p = images(fp32, output_format, slots, tail, interfaces, offset)
  words = source_words(fp32)
  source = encode(words, u.F32 if fp32 else u.BF16)
  payload = encode(expected(words, slots, tail), output_format)
  samples = []
  for sample in range(4):
    bh.launch(code, l1={INPUT: source, OUTPUT: GUARD * 80, SCRATCH-64: GUARD * 82,
                       OBSERVE: GUARD * 513}, profiler=p)
    assert bh.read_l1(bh.core, OUTPUT, 5120) == b'\xa5' * offset + payload + b'\xa5' * (5120-offset-len(payload))
    assert bh.read_l1(bh.core, OBSERVE, len(source)) == source
    assert bh.read_l1(bh.core, OBSERVE + len(source), 64) == GUARD
    assert bh.read_l1(bh.core, SCRATCH-64, 64) == GUARD
    assert bh.read_l1(bh.core, SCRATCH+5120, 64) == GUARD
    if sample: samples.append(p.last['scatter pack'])
  print('SCATTER_PACK', fp32, output_format, interfaces, slots, tail, 'cycles', samples, 'median', median(samples))


def copy_dynamic(k, source, destination, size):
  """Fixture copy with register addresses; source/destination remain unchanged."""
  src, dst, value = k.reg(3)
  k.mv(src, source); k.mv(dst, destination)
  for _ in k.range(size):
    k.lbu(value, src); k.sb(value, dst)
    k.addi(src, src, 1); k.addi(dst, dst, 1)
  k.fence()


def ring_images(fp32, output_format, tail, *, pages=6):
  loader, math, packer, consumer = (Asm(role) for role in ('trisc0', 'trisc1', 'trisc2', 'ncrisc'))
  initialize_dst(loader, math, fp32)
  u.sem_wait(packer, u.Sem.MATH_PACK, u.SemWait.ON_ZERO, u.Stall.TDMA)
  config = noc.InterleavedConfig((0,), OUTPUT, depth=2, page_bytes=PAGE_BYTES, sync_slot=29)
  # Wrap both physical pages and 16-bit credit counters in this one launch.
  packer.write(noc._cb_counter(config, True), 65534)
  packer.write(noc._cb_counter(config, False), 65534)
  configure(packer, fp32, output_format, 4)
  packer.write(READY, 1); packer.fence()
  consumer.wait(READY, 1)
  slots = (63 if fp32 else 127, 0, 17, 4)
  size = (384 + tail) * (4 if output_format == u.F32 else 2)
  p = Profiler(packer)
  for page in packer.range(pages):
    cb_action(packer, config, 'reserve')
    p.record('last page pack')
    scatter(packer, slots, tail, 4, SCRATCH, slot_shift=page, capacity=64 if fp32 else 128)
    p.record('last page pack')
    offset, destination, source = packer.reg(3)
    packer.andi(offset, page, 1); packer.slli(offset, offset, 13)
    packer.li(destination, OUTPUT + 64); packer.add(destination, destination, offset)
    packer.li(source, SCRATCH)
    copy_dynamic(packer, source, destination, size)
    cb_action(packer, config, 'publish')
  for page in consumer.range(pages):
    cb_action(consumer, config, 'wait')
    # Delay each reader after acquiring a page, so producer reuse faces pressure.
    delay = consumer.reg(); consumer.li(delay, 1024)
    loop = consumer._new_label('slow_consumer'); consumer.label(loop)
    consumer.addi(delay, delay, -1); consumer.bne(delay, R.ZERO, loop)
    offset, source, destination = consumer.reg(3)
    consumer.andi(offset, page, 1); consumer.slli(offset, offset, 13)
    consumer.li(source, OUTPUT); consumer.add(source, source, offset)
    consumer.slli(offset, page, 13)
    consumer.li(destination, ARCHIVE); consumer.add(destination, destination, offset)
    copy_dynamic(consumer, source, destination, PAGE_BYTES)
    cb_action(consumer, config, 'release')
  cb_action(packer, config, 'reserve', count=2)  # Both pages have been consumed.
  for i, received in enumerate((True, False)):
    value = packer.reg(); packer.read(value, noc._cb_counter(config, received), bytes=2)
    packer.write(COUNTERS + i * 4, value)
  observe_all(packer, fp32)
  u.sem_get(packer, u.Sem.MATH_PACK)
  return {k.role: k.lower() for k in (loader, math, packer, consumer)}, p, slots


@pytest.mark.parametrize('fp32', (True, False), ids=('fp32-dst', 'bf16-dst'))
@pytest.mark.parametrize('output_format', (u.BF16, u.F32), ids=('bf16-out', 'fp32-out'))
@pytest.mark.parametrize('tail', (128, 73), ids=('full', 'tail'))
def test_scatter_pack_wrapping_cb(bh, fp32, output_format, tail):
  code, p, slots = ring_images(fp32, output_format, tail)
  words = source_words(fp32)
  source = encode(words, u.F32 if fp32 else u.BF16)
  samples = []
  for sample in range(4):
    bh.launch(code, l1={INPUT: source, OUTPUT: GUARD * (2 * PAGE_BYTES // 64),
                       SCRATCH-64: GUARD * 82, OBSERVE: GUARD * 513,
                       ARCHIVE: GUARD * (6 * PAGE_BYTES // 64 + 1), READY: bytes(32)}, profiler=p)
    for page in range(6):
      shifted = tuple((slot + page) % (64 if fp32 else 128) for slot in slots)
      payload = encode(expected(words, shifted, tail), output_format)
      want = GUARD + payload + b'\xa5' * (PAGE_BYTES - 64 - len(payload))
      assert bh.read_l1(bh.core, ARCHIVE + page * PAGE_BYTES, PAGE_BYTES) == want
    assert bh.read_l1(bh.core, ARCHIVE + 6 * PAGE_BYTES, 64) == GUARD
    assert bh.read_l1(bh.core, COUNTERS, 8) == pack('<2I', 4, 4)
    assert bh.read_l1(bh.core, OBSERVE, len(source)) == source
    assert bh.read_l1(bh.core, OBSERVE + len(source), 64) == GUARD
    assert bh.read_l1(bh.core, SCRATCH-64, 64) == GUARD
    assert bh.read_l1(bh.core, SCRATCH+5120, 64) == GUARD
    if sample: samples.append(p.last['last page pack'])
  print('SCATTER_CB', fp32, output_format, tail, 'six pages', 'last page cycles', samples)


def test_scatter_pack_images_fit_worker_text():
  for fp32 in (True, False):
    for tail in (128, 127):
      code, _ = images(fp32, u.F32, (63 if fp32 else 127, 0, 17, 4, 31, 8, 55, 2), tail, 4, 64)
      ring, _, _ = ring_images(fp32, u.F32, tail)
      for streams in (code, ring):
        assert all(len(image) <= TensixL1.WORKER_TEXT_SIZE[role] for role, image in streams.items())
