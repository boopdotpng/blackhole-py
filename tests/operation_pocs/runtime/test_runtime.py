"""Measured independent external operations, guarded byte-exact oracles."""
import json
from statistics import median
from struct import pack, unpack

import pytest

from asm import Asm
from fw.consts import TensixL1
from tests.movement import noc
from tests.profiler import Profiler
from tests.operation_pocs.runtime.ops import Transfer, read_from, write_to, cb_action

BASE = TensixL1.DATA_BUFFER_SPACE_BASE
GUARD = bytes([0xAD]) * 64


def report(request, bh, operation, samples, controls, K=1, **case):
  print('RUNTIME_RESULT ' + json.dumps(dict(
    operation=operation, card=request.config.getoption('--bh-device'),
    core=bh.core, K=K, samples=samples, control=controls,
    minimum=min(samples), median=median(samples), maximum=max(samples),
    cycles_per_operation=[x / K for x in samples], warmup=1, **case), sort_keys=True))


@pytest.mark.parametrize('direction', ['read', 'write'])
@pytest.mark.parametrize('noc_index', [0, 1])
@pytest.mark.parametrize('element_bytes,elements,placement,stride', [
  (2, 128, 0, 0), (4, 128, 0x4000, 0), (2, 256, 0x8000, 512),
  (4, 256, 0xC000, 1024),
])
def test_external(bh, request, direction, noc_index, element_bytes, elements, placement, stride):
  block_bytes = 128 * element_bytes
  size = elements * element_bytes
  offset = 64
  extent = offset + (elements // 128 - 1) * (stride or block_bytes) + block_bytes + 64
  original = bytes((i * 37 + i // 7 + 13) & 255 for i in range(extent))
  payload = bytes((i * 73 + i // 11 + 19) & 255 for i in range(size))
  bank = 0 if placement == 0 else len(bh.device.pcie.dram_endpoints) - 1
  external = bh.dram_buffer(extent, bank=bank, initial=original)
  neighbor = bh.dram_buffer(256, bank=bank, initial=GUARD * 4)
  address = BASE + placement + 64
  spec = Transfer(bh.dram_coordinates(noc_index, banks=1, bank_start=bank)[0],
                  address, elements, element_bytes, offset, stride, noc_index)
  expected = bytearray(original)
  if direction == 'read':
    payload = b''.join(original[offset + b * (stride or block_bytes):
                                 offset + b * (stride or block_bytes) + block_bytes]
                       for b in range(elements // 128))
  else:
    for b in range(elements // 128):
      start = offset + b * (stride or block_bytes)
      expected[start:start + block_bytes] = payload[b * block_bytes:(b + 1) * block_bytes]
  for serial in (True, False):
    k = Asm('brisc' if direction == 'read' else 'ncrisc')
    p = Profiler(k)
    external_address = k.reg()
    k.read(external_address, TensixL1.PARAM_BASE)
    p.record('empty'); p.record('empty')
    p.record(direction)
    (read_from if direction == 'read' else write_to)(k, spec, external_address, serial=serial)
    p.record(direction)
    images = {k.role: k.lower()}
    samples, controls = [], []
    for sample in range(8):
      bh.write(external, original)
      initial = bytes([0xD3]) * size if direction == 'read' else payload
      bh.launch(images, params=(external.address,),
                l1={address - 64: GUARD + initial + GUARD}, profiler=p)
      assert bh.read_l1(bh.core, address - 64, size + 128) == GUARD + payload + GUARD
      assert bh.read(external) == bytes(expected)
      assert bh.read(neighbor) == GUARD * 4
      if sample:
        samples.append(p.last[direction]); controls.append(p.last['empty'])
    report(request, bh, direction, samples, controls, noc=noc_index,
           element_bytes=element_bytes, N=elements, l1_address=address,
           bank=bank, coordinate=spec.coordinate, offset_bytes=offset,
           stride_bytes=stride, mode='serial-baseline' if serial else 'batched',
           image_bytes=len(images[k.role]))


@pytest.mark.parametrize('action', ['reserve', 'publish', 'wait', 'release'])
@pytest.mark.parametrize('slot,initial', [(0, 0), (31, 65535)])
def test_cb_primitive(bh, request, action, slot, initial):
  config = noc.InterleavedConfig((0,), BASE + 0x10000, 32, 256, sync_slot=slot)
  k = Asm('brisc'); p = Profiler(k)
  received = initial + (16 if action in ('wait', 'release') else 0)
  acked = initial
  received &= 65535
  k.write(noc._cb_counter(config, True), received)
  k.write(noc._cb_counter(config, False), acked)
  other = noc.InterleavedConfig((0,), BASE + 0x11000, 2, 256, sync_slot=1)
  k.write(noc._cb_counter(other, True), 123)
  k.write(noc._cb_counter(other, False), 122)
  k.fence()
  p.record('empty'); p.record('empty')
  p.record(action)
  for _ in range(16): cb_action(k, config, action)
  p.record(action)
  for i, addr in enumerate((noc._cb_counter(config, True), noc._cb_counter(config, False),
                            noc._cb_counter(other, True), noc._cb_counter(other, False))):
    value = k.reg(); k.read(value, addr); k.write(BASE + 0x12000 + i * 4, value)
  image = k.lower()
  expected = ((received + 16 * (action == 'publish')) & 65535,
              (acked + 16 * (action == 'release')) & 65535, 123, 122)
  samples, controls = [], []
  for sample in range(8):
    bh.launch({'brisc': image}, profiler=p,
              l1={BASE + 0x12000 - 64: GUARD + bytes(16) + GUARD})
    observed = bh.read_l1(bh.core, BASE + 0x12000 - 64, 144)
    assert observed == GUARD + pack('<4I', *expected) + GUARD
    if sample:
      samples.append(p.last[action]); controls.append(p.last['empty'])
  report(request, bh, 'cb_' + action, samples, controls, slot=slot,
         initial_counter=initial, depth=32, count=1, K=16, mode='uncontended',
         image_bytes=len(image))


@pytest.mark.parametrize('action', ['post', 'get', 'wait_ready', 'wait_space'])
@pytest.mark.parametrize('semaphore', [1, 2, 5, 7])
def test_semaphore_primitive(bh, request, action, semaphore):
  from isa import Tensix as TT
  from tests.movement.unpacker.unpack import pc_sync, PC_SEMAPHORE_BASE
  from tests.operation_pocs.runtime.ops import semaphore_action
  k = Asm('trisc1'); p = Profiler(k)
  initial = 7 if action in ('get', 'wait_ready') else 0
  # Only selected handoff semaphore is owned; sentinel in unused semaphore 0.
  k.emit(TT.TTSEMINIT(15, initial, 1 << semaphore))
  k.emit(TT.TTSEMINIT(15, 9, 1))
  pc_sync(k)
  p.record('empty'); p.record('empty')
  p.record(action)
  for _ in range(7): semaphore_action(k, semaphore, action)
  p.record(action)
  for i, slot in enumerate((semaphore, 0)):
    value = k.reg(); k.read(value, PC_SEMAPHORE_BASE + slot * 4)
    k.write(BASE + 0x13000 + i * 4, value)
  expected = initial + (7 if action == 'post' else -7 if action == 'get' else 0)
  samples, controls = [], []
  image = k.lower()
  for sample in range(8):
    bh.launch({'trisc1': image}, profiler=p,
              l1={BASE + 0x13000 - 64: GUARD + bytes(8) + GUARD})
    assert bh.read_l1(bh.core, BASE + 0x13000 - 64, 136) == GUARD + pack('<2I', expected, 9) + GUARD
    if sample:
      samples.append(p.last[action]); controls.append(p.last['empty'])
  report(request, bh, 'semaphore_' + action, samples, controls, K=7,
         semaphore=semaphore, initial=initial, mode='uncontended', image_bytes=len(image))


@pytest.mark.parametrize('action', ['reserve', 'wait'])
def test_cb_blocking(bh, request, action):
  from isa import R
  config = noc.InterleavedConfig((0,), BASE + 0x10000, 2, 256, sync_slot=31)
  start, proof, observed = BASE + 0x14000, BASE + 0x14004, BASE + 0x14008
  k, peer = Asm('brisc'), Asm('ncrisc')
  p = Profiler(k)
  k.write(noc._cb_counter(config, True), 2 if action == 'reserve' else 0)
  k.write(noc._cb_counter(config, False), 0); k.fence()
  peer.wait(start, 1)
  delay = peer.reg(); peer.li(delay, 1024)
  again = peer._new_label('fixture_delay'); peer.label(again)
  peer.addi(delay, delay, -1); peer.bne(delay, R.ZERO, again)
  peer.write(proof, 0x12345678); peer.fence()
  cb_action(peer, config, 'release' if action == 'reserve' else 'publish')
  p.record('empty'); p.record('empty')
  p.record(action)
  k.write(start, 1); k.fence()
  cb_action(k, config, action)
  p.record(action)
  value = k.reg(); k.read(value, proof); k.write(observed, value)
  images = {'brisc': k.lower(), 'ncrisc': peer.lower()}
  samples, controls = [], []
  for sample in range(8):
    bh.launch(images, profiler=p, l1={start: bytes(12)})
    assert unpack('<I', bh.read_l1(bh.core, observed, 4))[0] == 0x12345678
    if sample:
      samples.append(p.last[action]); controls.append(p.last['empty'])
  report(request, bh, 'cb_' + action, samples, controls,
         mode='intentional-peer-wait', delay_iterations=1024, slot=31)


@pytest.mark.parametrize('action', ['wait_ready', 'wait_space'])
def test_semaphore_blocking(bh, request, action):
  from isa import R, Tensix as TT
  from tests.movement.unpacker.unpack import pc_sync, PC_SEMAPHORE_BASE
  from tests.operation_pocs.runtime.ops import semaphore_action
  start, proof, observed = BASE + 0x15000, BASE + 0x15004, BASE + 0x15008
  k, peer = Asm('trisc1'), Asm('trisc0')
  p = Profiler(k)
  k.emit(TT.TTSEMINIT(1, 0 if action == 'wait_ready' else 1, 1 << 2)); pc_sync(k)
  peer.wait(start, 1)
  delay = peer.reg(); peer.li(delay, 1024)
  again = peer._new_label('fixture_delay'); peer.label(again)
  peer.addi(delay, delay, -1); peer.bne(delay, R.ZERO, again)
  peer.write(proof, 0x76543210); peer.fence()
  semaphore_action(peer, 2, 'post' if action == 'wait_ready' else 'get')
  p.record('empty'); p.record('empty')
  p.record(action)
  k.write(start, 1); k.fence()
  semaphore_action(k, 2, action)
  p.record(action)
  value = k.reg(); k.read(value, proof); k.write(observed, value)
  images = {'trisc1': k.lower(), 'trisc0': peer.lower()}
  samples, controls = [], []
  for sample in range(8):
    bh.launch(images, profiler=p, l1={start: bytes(12)})
    assert unpack('<I', bh.read_l1(bh.core, observed, 4))[0] == 0x76543210
    if sample:
      samples.append(p.last[action]); controls.append(p.last['empty'])
  report(request, bh, 'semaphore_' + action, samples, controls,
         mode='intentional-peer-wait', delay_iterations=1024, semaphore=2)


@pytest.mark.parametrize('action', ['publish', 'wait_valid', 'release', 'wait_free'])
@pytest.mark.parametrize('bank', [0, 1])
def test_source_flags(bh, request, action, bank):
  from tests.movement.unpacker.unpack import configure_unpacker, UnpackTarget, BF16, pc_sync
  from tests.operation_pocs.runtime.ops import source_flag
  k = Asm('trisc0'); p = Profiler(k)
  # Flag-only NOPs never consume data-unpack configuration; committing here
  # leaks a config credit and blocks the third launch's configuration wait.
  configure_unpacker(k, bank, BASE + 0x16000, BF16,
                     UnpackTarget.SRCA if bank == 0 else UnpackTarget.SRCB, commit=False)
  pc_sync(k)
  for _ in range(8):
    p.accumulate('empty'); p.accumulate('empty')
  # Repeated complete bank cycles are fixture sequencing. Only the named
  # primitive and its completion fence are inside accumulated intervals.
  for cycle in range(8):
    for step_index, step in enumerate(('wait_free', 'publish', 'wait_valid', 'release')):
      k.write(BASE + 0x17004, cycle * 4 + step_index)
      if step == action: p.accumulate(action)
      source_flag(k, bank, step)
      if step == action: p.accumulate(action)
  k.write(BASE + 0x17000, 0x1234ABCD)
  image = k.lower()
  samples, controls = [], []
  for sample in range(8):
    try:
      bh.launch({'trisc0': image}, profiler=p,
                l1={BASE + 0x16000: GUARD * 4, BASE + 0x17000: bytes(8)})
    except TimeoutError:
      print('SOURCE_STAGE', sample, int.from_bytes(bh.read_l1(bh.core, BASE + 0x17004, 4), 'little'))
      raise
    assert bh.read_l1(bh.core, BASE + 0x17000, 4) == pack('<I', 0x1234ABCD)
    assert bh.read_l1(bh.core, BASE + 0x16000, 256) == GUARD * 4
    if sample:
      samples.append(p.last[action]); controls.append(p.last['empty'])
  report(request, bh, 'source_' + action, samples, controls, K=8,
         source_bank='A' if bank == 0 else 'B', mode='uncontended-accumulated',
         image_bytes=len(image))


@pytest.mark.parametrize('action', ['wait_valid'])
@pytest.mark.parametrize('bank', [0, 1])
def test_source_flag_blocking(bh, request, action, bank):
  from isa import R
  from tests.movement.unpacker.unpack import configure_unpacker, UnpackTarget, BF16, pc_sync
  from tests.operation_pocs.runtime.ops import source_flag
  start, proof, observed = BASE + 0x18000, BASE + 0x18004, BASE + 0x18008
  k, peer = Asm('trisc0'), Asm('trisc1')
  p = Profiler(k)
  configure_unpacker(k, bank, BASE + 0x16000, BF16,
                     UnpackTarget.SRCA if bank == 0 else UnpackTarget.SRCB, commit=False)
  pc_sync(k)
  peer.wait(start, 1)
  delay = peer.reg(); peer.li(delay, 1024)
  again = peer._new_label('fixture_delay'); peer.label(again)
  peer.addi(delay, delay, -1); peer.bne(delay, R.ZERO, again)
  peer.write(proof, 0xABCDEF12); peer.fence()
  source_flag(peer, bank, 'publish')
  p.record('empty'); p.record('empty')
  p.record(action)
  k.write(start, 1); k.fence()
  source_flag(k, bank, action)
  p.record(action)
  value = k.reg(); k.read(value, proof); k.write(observed, value)
  # Return the acquired bank; advance both selectors once.
  source_flag(k, bank, 'release')
  images = {'trisc0': k.lower(), 'trisc1': peer.lower()}
  samples, controls = [], []
  for sample in range(8):
    bh.launch(images, profiler=p, l1={start: bytes(12)})
    assert unpack('<I', bh.read_l1(bh.core, observed, 4))[0] == 0xABCDEF12
    if sample:
      samples.append(p.last[action]); controls.append(p.last['empty'])
  report(request, bh, 'source_' + action, samples, controls,
         source_bank='A' if bank == 0 else 'B', mode='intentional-peer-wait',
         delay_iterations=1024)
