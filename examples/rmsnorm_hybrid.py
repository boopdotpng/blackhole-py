"""Batch-one BF16 RMSNorm: HiFi4 x*gamma and macro FP32 square sums.

Port of blackhole-py/tests/compute/fpu/test_rmsnorm_hybrid.py. Math stays on
TRISC1; TRISC0 prefetches the next pair into the alternate source banks.
Dst 0 is scratch and Dst 1..tiles hold products, then normalized output.
"""
import os
from ttko.isa import Tensix as TT
from fw.consts import TensixMMIO
from ttko.program import DType
from ttko.cb import CB
from ttko.mop import LoopTemplate
from ttko.sync import Sem, SemWait, Stall, Wait, sem_get, sem_post, sem_wait, stall, sync
from ttko.unpack import UnpackTarget, _BASE, _unpacr

# Diagnostic ablation: identical-sized streams distinguish macro state from
# instruction placement. Production callers leave this unset.
BOUNDARY_MODE = None
REPLAY_PREFIX = 0
BOUNDARY_PADDING = 0


def enabled():
  """Keep the faster measured decode default until the boundary regression is fixed."""
  mode = os.environ.get('LLAMA_RMSNORM', 'reference')
  if mode not in ('reference', 'hybrid'):
    raise ValueError('LLAMA_RMSNORM must be reference or hybrid')
  return mode == 'hybrid'


def emit_rmsnorm(p, x, weight, output_cb, *, tiles, finalize, read_noc=0):
  if tiles not in (2, 4):
    raise ValueError("decode RMSNorm supports 2048 or 4096 elements")
  if x.dtype != DType.BF16 or weight.dtype != DType.BF16:
    raise ValueError("decode RMSNorm requires BF16")
  if x.tilized != weight.tilized:
    raise ValueError("RMSNorm operands must have the same element order")
  operands = p.cb(DType.BF16, depth=2*tiles)
  for buffer in (x, weight):
    p.brisc.noc_at(read_noc).read_tiles_into_cb(buffer, tuple(range(tiles)), operands)
  input_bases = (operands.addr, operands.addr + tiles*operands.tile_size)
  u, m = p.trisc0, p.trisc1
  sem_wait(m, Sem.MATH_PACK, SemWait.STALL_ON_MAX,
           Stall.SYNC | Stall.MATH | Stall.SFPU)
  p.fpu._configure_dst(0)
  p.fpu._rmw_cfg_byte(TensixMMIO.CFG_BASE + 4, 3, 0x40, 0x40)
  m.emit(TT.TTZEROACC(3, 1, 0, 1, 0))
  m.emit(TT.TTSFPENCC(0, 0, 0, 2))
  m.emit(TT.TTSFPCONFIG(0, 15, 1))
  m.emit(TT.TTSFPNOP())
  for mod, step, phase in ((0, 0x808, 0), (1, 0x808, 1 << 13),
                           (2, 0x808, 1 << 15), (3, 0, 0)):
    for register, value in ((12+mod, step), (28+mod, phase), (47+mod, 0)):
      m.emit(TT.TTSETC16(register, value))
  for reg in range(4):
    m.emit(TT.TTSFPMAD(reg, reg, reg ^ 2, 12+reg, 0))
    m.emit(TT.TTSFPCONFIG((0x84+reg) << 8, 4+reg, 1))
  m.emit(TT.TTSFPCONFIG(3, 8, 1))
  for reg in (2, 3):
    m.emit(TT.TTSFPLOADI(reg, 8, 0))
    m.emit(TT.TTSFPLOADI(reg, 10, 0))
  sem_post(m, Sem.MATH_DONE)
  sem_wait(u, Sem.MATH_DONE, SemWait.STALL_ON_ZERO, Stall.UNPACK | Stall.SYNC)
  sem_get(u, Sem.MATH_DONE)
  # The input CB is filled once per launch; its fixed bases are safe to use
  # after the producer credit. No host-generated constants or extra NoC reads.
  CB.wait_front(u, operands, 2*tiles)
  for address, target in zip(input_bases, (UnpackTarget.SRCA, UnpackTarget.SRCB)):
    p.unpack._configure_l1(DType.BF16, target, address, 256,
                           commit=False, configure_mop=False)
  p.unpack._commit_config(_BASE[0])
  u.emit(TT.TTSETADCXX(3, 1023, 0))
  p.unpack._mop.configure(LoopTemplate(
    outer=1, inner=1, start=_unpacr(0), loop=_unpacr(1),
    last=_unpacr(1), outer_last=_unpacr(1)))
  for tile in range(tiles):
    if tile:
      for engine, address in enumerate(input_bases):
        base = ((address + tile*operands.tile_size) >> 4)-1
        u.write(int(_BASE[engine]), base)
        u.write(int(_BASE[engine])+4, base)
    u.emit(TT.TTSETADCZW(3, 0, 0, 0, 0, 0xF))
    stall(u, Stall.UNPACK, Wait.SRCA_CLR | Wait.SRCB_CLR)
    p.unpack._mop.run()
    stall(u, Stall.UNPACK, Wait.UNPACK0 | Wait.UNPACK1)
    sem_get(u, Sem.UNPACK_SYNC)
    sync(u)
    sem_wait(u, Sem.UNPACK_TO_DEST, SemWait.STALL_ON_MAX, Stall.SYNC)
    sem_post(u, Sem.UNPACK_TO_DEST)

    sem_wait(m, Sem.UNPACK_TO_DEST, SemWait.STALL_ON_ZERO, Stall.SYNC)
    sem_get(m, Sem.UNPACK_TO_DEST)
    stall(m, Stall.MATH, Wait.SRCA_VLD | Wait.SRCB_VLD)
    for row in range(0, 64, 8):
      m.emit(TT.TTMOVA2D(0, row, 3, 2, row))
    stall(m, Stall.SFPU, Wait.MATH)
    m.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    for phase in range(4):
      for slot in range(8):
        mod = 0 if slot < 7 else (1 if phase < 3 else 2)
        m.emit(TT.TTELWMUL(0, 0, 0, mod, (tile+1)*64 + slot*8))
    for row in range(0, 64, 2):
      reg = (row // 2) % 4
      m.emit(TT.TTSFPLOADMACRO((reg << 2) | reg, 3, 3, row))
    for _ in range(3):
      m.emit(TT.TTSFPNOP())
    stall(m, Stall.SYNC, Wait.MATH | Wait.SFPU)
    m.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  CB.pop_front(u, operands, 2*tiles)
  m.emit(TT.TTSFPADD(10, 2, 3, 7, 0))
  m.emit(TT.TTSFPNOP())
  # Reuse macro 0: multiply by L0 at t+1 and store FP32 at t+3.
  m.emit(TT.TTSFPMUL(0, 0, 9, 12, 0))
  m.emit(TT.TTSFPLOADI(0, 8, 0x1300))
  m.emit(TT.TTSFPLOADI(0, 10, 0x8400))
  m.emit(TT.TTSFPCONFIG(0, 4, 0))
  m.emit(TT.TTSFPCONFIG(3, 8, 1))
  # The shared finalizer consumes partial sums in L0.
  m.emit(TT.TTSFPMOV(0, 7, 0, 0))
  for word in finalize.words:
    m.emit(word)
  stall(m, Stall.SFPU, Wait.MATH)
  for tile in range(tiles):
    for vector in range(32):
      reg = 1 + vector % 4
      row = (tile+1)*64 + vector*2
      m.emit(TT.TTSFPLOADMACRO(reg & 3, 3, 3, row | (reg >> 2)))
  for _ in range(4):
    m.emit(TT.TTSFPNOP())
  p.sfpu.publish()
  # Match the raw kernel's BF16 gasket rounding from FP32 Dst. Sending
  # FP32 directly to the packer instead truncates and nearly doubles error.
  sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
  p.pack._configure(output_cb, False, False)
  p.pack._rmw_cfg_byte(TensixMMIO.CFG_BASE + 4, 0, 0x07, 0)
  p.trisc2.write(TensixMMIO.CFG_BASE + 0x48, 1)
  for tile in range(1, tiles+1):
    p.pack._move_acquired(output_cb, tile, False, configure=False)
  p.pack._release_dst()
  if BOUNDARY_MODE is not None:
    words = (TT.TTSFPCONFIG(0, 15, 1), TT.TTSFPNOP(),
             TT.TTSFPMUL(0, 0, 9, 12, 0),
             TT.TTSFPCONFIG(0x8400, 4, 1), TT.TTSFPCONFIG(0x0f00, 8, 1))
    for word in words:
      m.emit(word if BOUNDARY_MODE == 'restore' else TT.TTSFPNOP())
  if REPLAY_PREFIX:
    p.sfpu._mop.state.replay.used.update(range(REPLAY_PREFIX))
  for _ in range(BOUNDARY_PADDING):
    m.emit(TT.TTNOP())
