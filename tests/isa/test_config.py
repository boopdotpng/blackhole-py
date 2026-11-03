"""Configuration-unit instructions: WRCFG, RDCFG, RMWCIB0-3, CFGSHIFTMASK, SETC16.

Scratch words: Config 88..91 (THCON_SEC0_REG6, the unused mover block) and
SCRATCH_SEC0..2 (209..211); both are zeroed again at the end of each kernel.
RISC addresses: bank b word w at CFG_BASE + 0x380*b + 4*w, dual write at
CFG_BASE + 0x700, ThreadConfig[t][r] at 0xFFEF0A80 + 272*t + 4*r.

Claims:
- WRCFG copies GPR[r] (or the aligned 4-GPR group, Is128Bit) to Config word
  w (or the aligned 4-word group) of the bank chosen by the thread's
  CFG_STATE_ID; the other bank is untouched. RDCFG returns that bank's word.
  One NOP sits between WRCFG and RDCFG; SETC16(CFG_STATE_ID) needs nothing
  extra before the next WRCFG/RDCFG of the same thread.
- RMWCIBn replaces only the masked bits of byte n; data bits outside the mask
  are ignored; only the current bank is written.
- CFGSHIFTMASK follows the ISA functional model for all 8 ALU modes, both
  mask modes, and scratch selection (index 3 = current thread's SCRATCH_SEC).
- SETC16 writes the issuing thread's ThreadConfig and is readable by that
  TRISC through the RISC ThreadConfig mapping (not write-only on Blackhole);
  bits without a field (41[7:6]) read back 0.
"""
from struct import unpack

import pytest

from asm import Asm
from firmware.consts import TensixMMIO
from ttko.isa import Tensix as TT
from tests.isa.test_scalar import set_gpr
from tests.movement.unpacker.unpack import Stall, Wait, pc_sync, stall

OUTPUT = 0x60000
CFG = 0xFFEF0000
DUAL = CFG + 0x700
THREAD_CFG = 0xFFEF0A80
WORD, SCRATCH = 88, 209
GPR = 40
MASK32 = 0xffffffff


def addr(word, bank): return CFG + 0x380 * bank + 4 * word


def run(bh, role, body):
  """body(k, out) appends RISC-visible words to observe; returns them."""
  k = Asm(role)
  v = k.reg()
  outputs = []
  def out(address):
    k.read(v, address); k.write(OUTPUT + 4 * len(outputs), v); outputs.append(address)
  def gpr(index): out(TensixMMIO.REGFILE_BASE + 4 * index)
  body(k, out, gpr)
  for w in range(4): k.write(DUAL + 4 * (WORD + w), 0)
  for w in range(3): k.write(CFG + 4 * (SCRATCH + w), 0)
  pc_sync(k)
  size = 4 * len(outputs)
  bh.launch({role: k.lower()}, l1={OUTPUT: b'\xa5' * size})
  return unpack(f'<{len(outputs)}I', bh.read_l1(bh.core, OUTPUT, size))


def drain(k):
  stall(k, Stall.SYNC, Wait.THCON | Wait.CFGEXU)
  pc_sync(k)


@pytest.mark.parametrize('bank', [0, 1])
@pytest.mark.parametrize('wide', [0, 1])
def test_wrcfg_rdcfg(bh, wide, bank):
  preset = [[0x0b000000 | b << 20 | w for w in range(4)] for b in range(2)]
  values = [0xc0de0000 | w for w in range(4)]
  def body(k, out, gpr):
    for b in range(2):
      for w in range(4): k.write(addr(WORD + w, b), preset[b][w])
    for i, x in enumerate(values): set_gpr(k, GPR + i, x)
    pc_sync(k)
    k.emit(TT.TTSETC16(0, bank))
    # 32-bit: GPR41 -> word 90. 128-bit: unaligned operands round down to GPR40..43 -> 88..91.
    k.emit(TT.TTWRCFG(GPR + 1, wide, WORD + 2 if not wide else WORD + 1))
    k.emit(TT.TTNOP())
    for w in range(4): k.emit(TT.TTRDCFG(GPR + 4 + w, WORD + w))
    k.emit(TT.TTSETC16(0, 0))
    drain(k)
    for w in range(4): gpr(GPR + 4 + w)
    for b in range(2):
      for w in range(4): out(addr(WORD + w, b))
  want = [row[:] for row in preset]
  if wide: want[bank] = values[:]
  else: want[bank][2] = values[1]
  assert run(bh, 'trisc0', body) == (*want[bank], *want[0], *want[1])


@pytest.mark.parametrize('byte', range(4))
@pytest.mark.parametrize('mask,data', [(0xff, 0x5c), (0x0f, 0xa3), (0x00, 0xff)])
def test_rmwcib(bh, byte, mask, data):
  old = 0x11223344
  def body(k, out, gpr):
    k.write(DUAL + 4 * WORD, old)
    pc_sync(k)
    k.emit((TT.TTRMWCIB0, TT.TTRMWCIB1, TT.TTRMWCIB2, TT.TTRMWCIB3)[byte](mask, data, WORD))
    drain(k)
    out(addr(WORD, 0)); out(addr(WORD, 1))
  shift = 8 * byte
  new = (old & ~(mask << shift)) | ((data & mask) << shift)
  assert run(bh, 'trisc0', body) == (new & MASK32, old)


def shiftmask_model(cfg, scratch, op, keep_old, width, rot):
  rotr = lambda x: ((x >> rot) | (x << (32 - rot))) & MASK32 if rot else x
  mask = (2 << width) - 1
  s = rotr(scratch & mask)
  if not keep_old: cfg &= ~rotr(mask) & MASK32
  cfg = (cfg | s, cfg & s, cfg ^ s, cfg + s, cfg | ~s, cfg & ~s, cfg ^ ~s, cfg - s)[op]
  return cfg & MASK32


SHIFTMASK = [(op, 0, 0, 'trisc0') for op in range(8)]
SHIFTMASK += [(op, 1, 0, 'trisc0') for op in (0, 1, 3)]
SHIFTMASK += [(0, 0, 1, 'trisc0'), (0, 0, 2, 'trisc0'), (0, 0, 3, 'trisc0'), (0, 0, 3, 'trisc2')]


@pytest.mark.parametrize('op,keep_old,sel,role', SHIFTMASK)
def test_cfgshiftmask(bh, op, keep_old, sel, role):
  cfg, scratch, width, rot = 0x12345678, (0xf0f0a5c3, 0x0bad1dea, 0x600dcafe), 11, 4
  def body(k, out, gpr):
    k.write(DUAL + 4 * WORD, cfg)
    for i, x in enumerate(scratch): k.write(CFG + 4 * (SCRATCH + i), x)
    pc_sync(k)
    k.emit(TT.TTCFGSHIFTMASK(keep_old, op, width, rot, sel, WORD))
    drain(k)
    out(addr(WORD, 0)); out(addr(WORD, 1))
  index = sel if sel < 3 else int(role[-1])
  assert run(bh, role, body) == (shiftmask_model(cfg, scratch[index], op, keep_old, width, rot), cfg)


def test_setc16_thread_config(bh):
  # UNPACK_MISC_CFG (41); context-reset bits 4 / 12 stay clear. Bits 6-7 have no
  # field and read back 0 (hardware: 0x40e1 -> 0x4021).
  values = (0x0102, 0x2c0f, 0x40e1)
  images = {}
  for t, value in enumerate(values):
    k = Asm(f'trisc{t}')
    v = k.reg()
    k.emit(TT.TTSETC16(41, value))
    pc_sync(k)
    k.read(v, THREAD_CFG + 272 * t + 4 * 41); k.write(OUTPUT + 4 * t, v)
    k.emit(TT.TTSETC16(41, 0))
    pc_sync(k)
    images[k.role] = k.lower()
  bh.launch(images, l1={OUTPUT: b'\xa5' * 12})
  got = unpack('<3I', bh.read_l1(bh.core, OUTPUT, 12))
  assert [g & 0xffff for g in got] == [v & ~0xc0 for v in values]
