"""Batch-one BF16 RMSNorm: HiFi4 x*gamma and macro FP32 square sums.

Port of blackhole-py/tests/compute/fpu/test_rmsnorm_hybrid.py. With half_sync=True,
TRISC1 issues
FPU products in lower-half Dst; TRISC2 squares upper-half scratch under
semaphore ownership, then packs after TRISC1 normalizes the products.
TRISC0 prefetches the next pair into the alternate source banks.
half_sync=False retains the queued Dst-0 scratch baseline.
Optional elwmul_mop=True issues each HiFi4 tile through a 4x8 math MOP.
Explicit ELWMUL remains the default: measured MOP setup/dispatch costs more
than it saves for these short vectors (see boop-docs measurements/rmsnorm/elwmul-vs-mop.md).
fidelity=3 omits the low*low BF16 product phase; HiFi4 remains the default.
"""
from ttko.isa import Tensix as TT
from firmware.consts import TensixMMIO
from program import DType
from ttko.cb import CB
from ttko.mop import LoopTemplate
from ttko.sync import Sem, SemWait, Stall, Wait, sem_get, sem_post, sem_wait, stall, sync
from ttko.unpack import UnpackTarget, _BASE, _unpacr

# Diagnostic ablation: identical-sized streams distinguish macro state from
# instruction placement. Production callers leave this unset.
BOUNDARY_MODE = None
REPLAY_PREFIX = 0
BOUNDARY_PADDING = 0


def _elwmul_template(dst_row, fidelity=4):
  """Three/four phases over eight blocks, with a reset after each phase.

  MOP last is the final outer/inner iteration; outer_last ends other inner
  loops. Modifier 0 advances Dst by eight, 1 resets Dst and advances fidelity,
  and 2 resets both. Source rows advance modulo 64 in all three modifiers.
  """
  return LoopTemplate(outer=fidelity, inner=8,
    loop=TT.TTELWMUL(0, 0, 0, 0, dst_row),
    outer_last=TT.TTELWMUL(0, 0, 0, 1, dst_row),
    last=TT.TTELWMUL(0, 0, 0, 2, dst_row))


def _run_elwmul_mop(mop, dst_row, *, initialize, fidelity=4):
  """Reuse the template between tiles; only three destination operands change.

  The caller must not use another math MOP between these invocations.
  """
  template = _elwmul_template(dst_row, fidelity)
  if initialize:
    mop.configure(template)
  else:
    words = template.words()
    mop.write_words(words, (5, 7, 8))  # loop, last outer, last inner
    mop.state.config = words
  mop.run()


def _square_tile(k, scratch_base):
  for row in range(0, 64, 2):
    reg = (row // 2) % 4
    k.emit(TT.TTSFPLOADMACRO((reg << 2) | reg, 3, 3, scratch_base + row))
  for _ in range(3):
    k.emit(TT.TTSFPNOP())


def emit_rmsnorm(p, x, weight, output_cb, *, tiles, finalize, read_noc=0, port=None,
                 elwmul_mop=False, fidelity=4, half_sync=False, profile=None):
  """Emit RMSNorm; half_sync=True overlaps FPU/SFPU on opposite Dst halves.

  The default retains the queued baseline. The overlap option uses RISC-V
  tile loops for square accumulation and packing to keep TRISC2 code compact.
  TRISC2 consumes scratch tile 7
  under semaphore ownership; products stay in lower-half tiles 0..tiles-1.
  One scratch section suffices: FPU products overlap SFPU square accumulation,
  and the next scratch copy waits until its previous consumer has finished.
  """
  if tiles not in (2, 4):
    raise ValueError("decode RMSNorm supports 2048 or 4096 elements")
  if fidelity not in (3, 4):
    raise ValueError('RMSNorm supports HiFi3 or HiFi4')
  if x.dtype != DType.BF16 or weight.dtype != DType.BF16:
    raise ValueError("decode RMSNorm requires BF16")
  if x.tilized != weight.tilized:
    raise ValueError("RMSNorm operands must have the same element order")
  operands = p.cb(DType.BF16, depth=2*tiles)
  for buffer in (x, weight):
    p.brisc.noc_at(read_noc, port).read_tiles_into_cb(buffer, tuple(range(tiles)), operands)
  input_bases = (operands.addr, operands.addr + tiles*operands.tile_size)
  u, m, s = p.trisc0, p.trisc1, p.trisc2
  scratch_base = 7*64 if half_sync else 0
  product_first = 0 if half_sync else 1
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
    if elwmul_mop and mod < 3:
      phase |= 8 if mod == 0 else 1 << 11
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
  # The input CB is filled once per launch at fixed bases, so the unpacker
  # can be configured while the reader is still in flight; only the data
  # itself waits for the producer credit.
  for address, target in zip(input_bases, (UnpackTarget.SRCA, UnpackTarget.SRCB)):
    p.unpack._configure_l1(DType.BF16, target, address, 256,
                           commit=False, configure_mop=False)
  p.unpack._commit_config(_BASE[0])
  u.emit(TT.TTSETADCXX(3, 1023, 0))
  p.unpack._mop.configure(LoopTemplate(
    outer=1, inner=1, start=_unpacr(0), loop=_unpacr(1),
    last=_unpacr(1), outer_last=_unpacr(1)))
  CB.wait_front(u, operands, 2*tiles)
  if profile is not None:
    sync(u)
    profile.kernel = u
    profile.record('L1 to L1')
  if half_sync:
    m.emit(TT.TTSEMINIT(1, 0, (1 << Sem.FPU_SFPU) | (1 << Sem.UNPACK_OPERAND_SYNC)))
    for register in (1, 15, 31, 50): s.emit(TT.TTSETC16(register, 0))
    s.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xf))
    # Scratch stays at one address; retain the wait/release on every iteration.
    for _ in s.range(tiles):
      sem_wait(s, Sem.FPU_SFPU, SemWait.STALL_ON_ZERO, Stall.SFPU | Stall.SYNC)
      _square_tile(s, scratch_base)
      stall(s, Stall.SYNC, Wait.SFPU)
      sem_get(s, Sem.FPU_SFPU)
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
    if half_sync:
      sem_wait(m, Sem.FPU_SFPU, SemWait.STALL_ON_MAX, Stall.MATH | Stall.SYNC)
    for row in range(0, 64, 8):
      m.emit(TT.TTMOVA2D(0, row, 3, 2, scratch_base + row))
    stall(m, Stall.SFPU, Wait.MATH)
    if profile is not None and tile == 0:
      sync(m)
      profile.kernel = m
      profile.record('compute')
    if half_sync:
      stall(m, Stall.SYNC, Wait.MATH)
      sem_post(m, Sem.FPU_SFPU)
    m.emit(TT.TTSETRWC(0, 0, 0, 0, 0, 0xF))
    if elwmul_mop:
      _run_elwmul_mop(p.fpu._mop, (tile+product_first)*64, initialize=tile == 0, fidelity=fidelity)
    else:
      for phase in range(fidelity):
        for slot in range(8):
          mod = 0 if slot < 7 else (1 if phase < fidelity-1 else 2)
          m.emit(TT.TTELWMUL(0, 0, 0, mod, (tile+product_first)*64 + slot*8))
    if not half_sync:
      _square_tile(m, scratch_base)
    stall(m, Stall.SYNC, Wait.MATH if half_sync else Wait.MATH | Wait.SFPU)
    m.emit(TT.TTSETRWC(3, 0, 0, 0, 0, 0xF))
  if half_sync:
    sem_post(s, Sem.UNPACK_OPERAND_SYNC)
    sem_wait(m, Sem.UNPACK_OPERAND_SYNC, SemWait.STALL_ON_ZERO, Stall.SFPU | Stall.SYNC)
    sem_get(m, Sem.UNPACK_OPERAND_SYNC)
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
      row = (tile+product_first)*64 + vector*2
      m.emit(TT.TTSFPLOADMACRO(reg & 3, 3, 3, row | (reg >> 2)))
  for _ in range(4):
    m.emit(TT.TTSFPNOP())
  if profile is not None:
    stall(m, Stall.SYNC, Wait.MATH | Wait.SFPU)
    sync(m)
    profile.kernel = m
    profile.record('compute')
    profile.record('pack')
  p.sfpu.publish()
  # Match the raw kernel's BF16 gasket rounding from FP32 Dst. Sending
  # FP32 directly to the packer instead truncates and nearly doubles error.
  sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
  p.pack._configure(output_cb, False, False)
  p.pack._rmw_cfg_byte(TensixMMIO.CFG_BASE + 4, 0, 0x07, 0)
  p.trisc2.write(TensixMMIO.CFG_BASE + 0x48, 1)
  if half_sync:
    # Products start at tile zero. Pack accepts a RISC-V register as its source
    # tile, and each iteration retains CB reservation/publication and drains.
    for tile in s.range(tiles):
      p.pack._move_acquired(output_cb, tile, False, configure=False)
  else:
    for tile in range(product_first, product_first+tiles):
      p.pack._move_acquired(output_cb, tile, False, configure=False)
  p.pack._release_dst()
  if profile is not None:
    sync(s)
    profile.kernel = s
    profile.record('pack')
    profile.record('L1 to L1')
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
