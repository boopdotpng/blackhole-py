"""Blackhole semaphore mask/saturation and mutex exclusion contracts."""
from struct import pack, unpack

import pytest

from asm import Asm
from ttko.isa import R, Tensix as TT
from tests.movement.unpacker.unpack import PC_SEMAPHORE_BASE, Stall, pc_sync

OUTPUT = 0x60000
BOUNDARIES = ((0, 0), (0, 15), (1, 0), (1, 1), (7, 7), (7, 14), (15, 14), (15, 15))


# Walking bits select each semaphore; a few multi-bit masks cover combined selection.
# Every TRISC uses the same semaphore unit, so other roles get one all-mask smoke case.
MASKS = (0, 1, 2, 4, 8, 16, 32, 64, 128, 0x03, 0x55, 0xaa, 0xff)
SEMAPHORE_CASES = [pytest.param('trisc1', m, id=f'trisc1-mask{m:02x}') for m in MASKS]
SEMAPHORE_CASES += [pytest.param(r, 0xff, id=f'{r}-maskff') for r in ('trisc0', 'trisc2')]


@pytest.mark.parametrize('role,mask', SEMAPHORE_CASES)
@pytest.mark.parametrize('operation', ('init', 'post', 'get'))
def test_semaphore_masks_saturation(bh, role, mask, operation):
  k = Asm(role)
  value = k.reg()
  expected = []
  for maximum, initial in BOUNDARIES:
    for index in range(8): k.emit(TT.TTSEMINIT(15, index + 2, 1 << index))
    k.emit(TT.TTSEMINIT(maximum, initial, mask))
    if operation == 'post': k.emit(TT.TTSEMPOST(mask))
    if operation == 'get': k.emit(TT.TTSEMGET(mask))
    pc_sync(k)
    for index in range(8):
      k.read(value, PC_SEMAPHORE_BASE + index * 4)
      k.write(OUTPUT + len(expected) * 4, value)
      wanted = index + 2
      if mask & (1 << index):
        wanted = initial
        if operation == 'post': wanted = min(15, initial + 1)
        if operation == 'get': wanted = max(0, initial - 1)
      expected.append(wanted)
  k.emit(TT.TTSEMINIT(15, 0, 255))
  pc_sync(k)
  size = len(expected) * 4
  bh.launch({role: k.lower()}, l1={OUTPUT: b'\xa5' * (size + 64)})
  actual = unpack(f'<{len(expected)}I', bh.read_l1(bh.core, OUTPUT, size))
  assert actual == tuple(expected)
  assert bh.read_l1(bh.core, OUTPUT + size, 64) == b'\xa5' * 64


@pytest.mark.parametrize('mask', (1, 128, 3, 85, 170, 255))
@pytest.mark.parametrize('condition,initial', ((1, 0), (2, 2), (3, 0), (3, 2)))
@pytest.mark.parametrize('roles', (('trisc0', 'trisc1'), ('trisc1', 'trisc2'), ('trisc2', 'trisc0')))
def test_semaphore_wait_all_conditions(bh, mask, condition, initial, roles):
  waiter, peer = (Asm(role) for role in roles)
  start, proof, observed = OUTPUT, OUTPUT + 4, OUTPUT + 8
  waiter.emit(TT.TTSEMINIT(2, initial, mask))
  pc_sync(waiter)
  waiter.write(start, 1)
  waiter.fence()
  waiter.emit(TT.TTSEMWAIT(Stall.SYNC, mask, condition))
  waiter.emit(TT.TTSEMPOST(0))  # A consumer of the blocked Sync resource.
  pc_sync(waiter)
  value = waiter.reg()
  waiter.read(value, proof)
  waiter.write(observed, value)
  peer.wait(start, 1)
  first = mask & -mask if mask & (mask - 1) else 0
  peer.emit(TT.TTSEMINIT(2, 1, first))
  pc_sync(peer)
  delay = peer.reg()
  peer.li(delay, 2048)
  label = peer._new_label('partial_release')
  peer.label(label)
  peer.addi(delay, delay, -1)
  peer.bne(delay, R.ZERO, label)
  peer.write(proof, 0x1234abcd)
  peer.fence()
  peer.emit(TT.TTSEMINIT(2, 1, mask))
  pc_sync(peer)
  bh.launch({k.role: k.lower() for k in (waiter, peer)}, l1={OUTPUT: bytes(12) + b'\xa5' * 64})
  assert bh.read_l1(bh.core, observed, 4) == pack('<I', 0x1234abcd)
  assert bh.read_l1(bh.core, OUTPUT + 12, 64) == b'\xa5' * 64


@pytest.mark.parametrize('mutex', (0, 2, 3, 4))  # Other Blackhole indices hang indefinitely.
@pytest.mark.parametrize('roles', (('trisc0', 'trisc1'), ('trisc1', 'trisc2'),
                                 ('trisc2', 'trisc0'), ('trisc0', 'trisc1', 'trisc2')))
@pytest.mark.parametrize('reacquire', (False, True))
def test_mutex_exclusion(bh, mutex, roles, reacquire):
  kernels = []
  for role in roles:
    k = Asm(role)
    iteration, value = k.reg(2)
    k.li(iteration, 37)
    loop = k._new_label('critical_section')
    k.label(loop)
    k.emit(TT.TTATGETM(mutex))
    if reacquire: k.emit(TT.TTATGETM(mutex))
    pc_sync(k)
    k.read(value, OUTPUT)
    k.addi(value, value, 1)
    k.write(OUTPUT, value)
    k.fence()
    k.emit(TT.TTATRELM(mutex))
    pc_sync(k)
    k.addi(iteration, iteration, -1)
    k.bne(iteration, R.ZERO, loop)
    kernels.append(k)
  bh.launch({k.role: k.lower() for k in kernels}, l1={OUTPUT: bytes(4) + b'\xa5' * 64})
  assert bh.read_l1(bh.core, OUTPUT, 4) == pack('<I', len(roles) * 37)
  assert bh.read_l1(bh.core, OUTPUT + 4, 64) == b'\xa5' * 64
