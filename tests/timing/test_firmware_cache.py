"""Read the startup CSR on hardware; catch accidentally disabled fusion."""
import struct

import pytest

from asm import Asm
from firmware.consts import TensixL1, TensixMMIO
from ttko.isa import R


@pytest.mark.parametrize('role', ('trisc0', 'trisc1', 'trisc2'))
def test_firmware_instruction_fusion(bh, role):
  k = Asm(role)
  value = k.reg()
  address = TensixL1.DATA_BUFFER_SPACE_BASE
  k.csrrs(value, R.ZERO, 0x7c0)
  k.write(address, value)
  k.fence()
  bh.launch({role: k.lower()}, l1={address: bytes(4)})
  cfg0, = struct.unpack('<I', bh.read_l1(bh.core, address, 4))
  print(f'{role}: cfg0={cfg0:#010x}, fusion={not bool(cfg0 & (1 << 18))}, '
        f'CSR permits prefetch={not bool(cfg0 & (1 << 2))}')
  assert not cfg0 & (1 << 18), 'firmware disabled .ttinsn fusion'
  assert not cfg0 & (1 << 2), 'firmware disabled instruction prefetch'


@pytest.mark.parametrize('all_workers', (False, True))
def test_worker_instruction_caches(bh, all_workers):
  roles = ('brisc', 'ncrisc', 'trisc0', 'trisc1', 'trisc2')
  address = TensixL1.DATA_BUFFER_SPACE_BASE
  images = {}
  for i, role in enumerate(roles):
    k = Asm(role)
    value = k.reg()
    k.csrrs(value, R.ZERO, 0x7c0)
    k.write(address + 4*i, value)
    if role == 'brisc':
      k.read(value, TensixMMIO.CFG_BASE + 208*4)
      k.write(address + 20, value)
    k.fence()
    images[role] = k.lower()
  cores = bh.device.cores if all_workers else (bh.core,)
  bh.launch_many(images, cores=cores)
  states = set()
  for core in cores:
    values = struct.unpack('<6I', bh.read_l1(core, address, 24))
    states.add(values)
    assert all(not v & (1 << 18) for v in values[2:5]), core
    assert all(not v & (1 << 2) for v in values[:5]), core
    assert values[5] & 0x1f == 0x1f, (core, 'backend prefetch disabled')
    assert (values[5] >> 5) & 0xff, (core, 'no prefetch requests allowed')
  print(f'{len(cores)} workers: CSR / prefetch states='
        f'{[tuple(hex(v) for v in state) for state in sorted(states)]}')
