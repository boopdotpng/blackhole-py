"""Raw DRISC GDDR DMA round trips; run with --bh-device=1 on queue 1.

Uses the NOC1-preferred endpoint: the NOC0-preferred DRISC is reserved for
system firmware. No NIU mode switch is needed for bank-local DMA.
"""
import json
import struct
import time
from contextlib import contextmanager

import pytest

from asm import Asm
from pcie import TLBWindow
from ttko.isa import R

L1_TAG = 0x2000000000
RESET, RESET_PC = 0xFFB121B0, 0xFFB14000
CODE, MAIL, STAGE = 0x1000, 0x100, 0x8000
DMA_CTRL, DMA_STREAM = 0xFC001000, 0xFC000000
CLOCK = 0xFFB121F0


@contextmanager
def drisc_window(device, bank=0):
  core = device.pcie.dram_endpoints[bank][1]
  with TLBWindow(device.pcie.fd, core) as window:
    def read(address, size=4):
      window.target(address & -window.SIZE)
      return window.read(address % window.SIZE, size)
    def write(address, data):
      window.target(address & -window.SIZE)
      window.write(address % window.SIZE, data)
    def word(address):
      return int.from_bytes(read(address), 'little')
    reset, pc = word(RESET), word(RESET_PC)
    if not reset & 0x800:
      raise RuntimeError(f'DRISC {core} is already running')
    saved = read(L1_TAG, 128 * 1024)
    try:
      yield read, write, word
    finally:
      write(RESET, reset | 0x800)
      write(L1_TAG, saved)
      write(RESET_PC, pc)
      write(RESET, reset)


def dma_kernel(src, dst, size, stream, burst, depth, repeats):
  # Reuse only the scalar assembler encoding; this is standalone DRISC code,
  # not the Tensix BRISC firmware ABI.
  fw = Asm('brisc', firmware=True, physical_regs=True)
  fw.base = CODE
  fw.configure_csr()
  fw.read32(R.S0, DMA_CTRL + 4)
  fw.write32(MAIL + 28, R.S0)
  fw.li(R.T0, ~0xff00 & 0xffffffff)
  fw.and_(R.T0, R.S0, R.T0)
  fw.li(R.T1, burst << 8)
  fw.or_(R.T0, R.T0, R.T1)
  fw.write32(DMA_CTRL + 4, R.T0, tmp_addr=R.T2)
  base = DMA_STREAM + stream * 0x100
  def wait_mask(address, mask, ready=False):
    fw.li(R.S3, 1000000)
    loop = fw._new_label('poll'); done = fw._new_label('ready')
    fw.label(loop)
    fw.read32(R.T0, address)
    fw.li(R.T1, mask); fw.and_(R.T1, R.T0, R.T1)
    (fw.bne if ready else fw.beq)(R.T1, R.ZERO, done)
    fw.addi(R.S3, R.S3, -1); fw.bne(R.S3, R.ZERO, loop)
    fw.write32(MAIL + 20, R.T0, tmp_addr=R.T2)
    fw.li(R.S4, 0xdead); fw.j('restore')
    fw.label(done)
  for direction, offset in (('read', 4), ('write', 12)):
    fw.write32(MAIL + 24, offset)
    fw.read32(R.S1, CLOCK)
    fw.write32(MAIL + offset, R.S1)
    fw.li(R.S2, repeats)
    loop = fw._new_label('repeat'); fw.label(loop)
    for i in range(depth):
      wait_mask(DMA_CTRL + (0x10 if direction == 'read' else 0x14), 1, ready=True)
      if direction == 'read':
        regs = ((0x30, src + i*size), (0x34, 0), (0x38, STAGE + i*size),
                (0x50, 0x83000000 | size//16))
      else:
        regs = ((0x10, STAGE + i*size), (0x14, dst + i*size), (0x18, 0),
                (0x50, 0x10000000 | size//16))
      for register, value in regs: fw.write32(base + register, value)
    wait_mask(base, 0xff10 if direction == 'read' else 0xf00f0009)
    fw.addi(R.S2, R.S2, -1); fw.bne(R.S2, R.ZERO, loop)
    fw.read32(R.S1, CLOCK); fw.write32(MAIL + offset + 4, R.S1)
  fw.li(R.S4, 0xcafe)
  fw.label('restore'); fw.write32(DMA_CTRL + 4, R.S0)
  fw.read32(R.T1, DMA_CTRL + 4); fw.write32(MAIL + 32, R.T1)
  fw.fence(); fw.write32(MAIL, R.S4)
  fw.label('halt'); fw.j('halt')
  return fw.lower()


@pytest.mark.parametrize('stream', (0, 1))
@pytest.mark.parametrize('burst', (16, 255))
@pytest.mark.parametrize('size,depth', ((16, 1), (2048, 1), (2048, 4), (16384, 4)))
@pytest.mark.parametrize('bank', range(8))
def test_drisc_dma(bh, stream, burst, size, depth, bank):
  device = bh.device
  if bank >= len(device.pcie.dram_endpoints):
    pytest.skip('bank unavailable on this card')
  count = size * depth
  src = device.alloc_interleaved_dram(count + 64, page_size=2048, banks=1, bank_start=bank)
  dst = device.alloc_interleaved_dram(count + 64, page_size=2048, banks=1, bank_start=bank)
  pattern = bytes((i*131 + i//251 + stream*37) & 255 for i in range(count))
  device.write_dram(src, b'\xa5'*32 + pattern + b'\xa5'*32)
  device.write_dram(dst, b'\x5a'*(count+64))
  repeats = 32
  with drisc_window(device, bank) as (read, write, word):
    nius = [word(0xffb20100 + n*0x10000) for n in range(2)]
    write(L1_TAG + STAGE - 32, b'\x69'*(count+64))
    write(L1_TAG + MAIL, bytes(36))
    write(L1_TAG + CODE, dma_kernel(src.address+32, dst.address+32, size, stream, burst, depth, repeats))
    write(RESET_PC, CODE)
    write(RESET, word(RESET) & ~0x800)
    deadline = time.monotonic() + 2
    while word(L1_TAG + MAIL) == 0:
      if time.monotonic() > deadline:
        raise TimeoutError(f'DRISC DMA stream={stream}, size={size}, stage={word(L1_TAG+MAIL+24):#x}, stamps={read(L1_TAG+MAIL,32).hex()}')
    assert word(L1_TAG + MAIL) == 0xcafe, read(L1_TAG + MAIL, 36).hex()
    assert read(L1_TAG + STAGE - 32, count+64) == b'\x69'*32 + pattern + b'\x69'*32
    stamps = struct.unpack('<4I', read(L1_TAG + MAIL + 4, 16))
    assert word(L1_TAG + MAIL + 28) == word(L1_TAG + MAIL + 32)
    assert [word(0xffb20100 + n*0x10000) for n in range(2)] == nius
  assert device.read_dram(dst) == b'\x5a'*32 + pattern + b'\x5a'*32
  assert device.read_dram(src) == b'\xa5'*32 + pattern + b'\xa5'*32
  cycles = [(stamps[i+1]-stamps[i]) & 0xffffffff for i in (0,2)]
  print(json.dumps(dict(bank=bank, stream=stream, burst=burst, size=size, depth=depth,
                       bytes_per_direction=count*repeats, read_cycles=cycles[0], write_cycles=cycles[1])))
