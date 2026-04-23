"""Spec tests for ../specs/xmov-and-tdma-mover.md.

Covers the XMOV Tensix instruction (opcode 0x40) and the TDMA-RISC MMIO
register block (0xFFB11000) that share the Mover DMA engine.

The packer-metadata sideband registers (0xFFB11030 / 0xFFB11034) live in the
same block but are driven by the Packer functional model, which does not
exist yet — those clauses remain xfail and will be picked up alongside the
pack/unpack rewrite.
"""

import pytest

from emu.tensix import TensixCoprocessor, TDMA
from emu.memory import Memory
from emu import memory as M
from emu.core import BRISC

from .conftest import spec


# Local fixtures

@pytest.fixture
def coproc():
  """TensixCoprocessor with L1 attached so XMOV transfers can hit memory."""
  c = TensixCoprocessor()
  c.attach_l1(Memory())
  return c


@pytest.fixture
def brisc_with_l1():
  """BRISC with L1 + TDMA handler wired at 0xFFB11000, matching device.py."""
  l1 = Memory()
  core = BRISC(l1=l1)
  cop = TensixCoprocessor()
  cop.attach_l1(l1)
  tdma = TDMA(mover=cop.mover)
  core.mem.register(M.TDMA_BASE, M.TDMA_END, tdma, offset=M.TDMA_BASE)
  return core, l1


def _push_step(coproc, word, thread=0, n=1):
  coproc.push_instruction(thread, int(word))
  for _ in range(n):
    coproc.step()


def _xmov_word(mov_block_selection=0, last=0):
  """Build a raw XMOV Tensix word (opcode=0x40)."""
  return (0x40 << 24) | (mov_block_selection << 23) | last


def _seed_xmov_cfg(cop, thread, src_16b, dst_16b, size_16b, direction):
  """Write XMOV's transfer parameters into the per-state config bank that
  the config state id for `thread` points at.  THCON_SEC0_REG6 ADDR32
  mapping: 88=src, 89=dst, 90=(size[29:0] | dir[31:30])."""
  cfg = cop.config_unit
  sid = cfg._state_id(thread)
  cfg.cfg[sid][88] = src_16b
  cfg.cfg[sid][89] = dst_16b
  cfg.cfg[sid][90] = (size_16b & 0xFFFF) | ((direction & 0x3) << 30)


# ===========================================================================
# XMOV instruction dispatch + parameter source
# ===========================================================================

@spec("XMOV.ENCODING.OPCODE")
def test_xmov_opcode_is_dispatched(coproc):
  """XMOV (0x40) must execute a Mover transfer, not fall through as a no-op."""
  SRC, DST, SIZE = 0x1000, 0x2000, 16
  for i in range(SIZE): coproc.mover.l1.write8(SRC + i, 0xA5)
  _seed_xmov_cfg(coproc, thread=0, src_16b=SRC >> 4, dst_16b=DST >> 4,
                 size_16b=SIZE >> 4, direction=3)  # L1→L1
  _push_step(coproc, _xmov_word(), thread=0)
  assert coproc.mover.l1.read8(DST) == 0xA5


@spec("XMOV.PARAMS.FROM_CFG_SPACE")
def test_xmov_reads_transfer_params_from_cfg(coproc):
  """XMOV must read src/dst/size/dir from THCON_SEC0_REG6 in config space,
  not from the instruction word itself."""
  SRC, DST, SIZE = 0x1000, 0x4000, 32
  for i in range(SIZE): coproc.mover.l1.write8(SRC + i, (i + 1) & 0xFF)
  _seed_xmov_cfg(coproc, thread=1, src_16b=SRC >> 4, dst_16b=DST >> 4,
                 size_16b=SIZE >> 4, direction=3)
  _push_step(coproc, _xmov_word(), thread=1)
  for i in range(SIZE):
    assert coproc.mover.l1.read8(DST + i) == (i + 1) & 0xFF


@spec("XMOV.ENCODING.MOV_BLOCK_SELECTION")
def test_xmov_mov_block_selection_field(coproc):
  """Mov_block_selection [23] picks between two physical move blocks in real
  hardware; the functional emulator has a single Mover, so both selections
  must execute the transfer equivalently."""
  for sel in (0, 1):
    l1 = Memory()
    coproc.attach_l1(l1)
    SRC, DST = 0x100, 0x200
    for i in range(16): l1.write8(SRC + i, 0xB0 | sel)
    _seed_xmov_cfg(coproc, thread=2, src_16b=SRC >> 4, dst_16b=DST >> 4,
                   size_16b=1, direction=3)
    _push_step(coproc, _xmov_word(mov_block_selection=sel), thread=2)
    assert l1.read8(DST) == 0xB0 | sel


@spec("XMOV.ENCODING.LAST")
def test_xmov_last_flag_flushes_accumulators(coproc):
  """Last=1 triggers accumulator flush in real hardware.  The functional
  emulator has no accumulators to flush; what we verify is that the Last bit
  is decoded and does not cause the transfer to be skipped or duplicated."""
  SRC, DST, SIZE = 0x1000, 0x2000, 16
  for i in range(SIZE): coproc.mover.l1.write8(SRC + i, 0x5A)
  _seed_xmov_cfg(coproc, thread=0, src_16b=SRC >> 4, dst_16b=DST >> 4,
                 size_16b=SIZE >> 4, direction=3)
  _push_step(coproc, _xmov_word(last=1), thread=0)
  for i in range(SIZE):
    assert coproc.mover.l1.read8(DST + i) == 0x5A


# ===========================================================================
# XMOV functional model — all four directions
# ===========================================================================

@spec("XMOV.FUNC.L1_TO_L1_MEMCPY")
def test_xmov_l1_to_l1_copies_data(coproc):
  """XMOV_L1_TO_L1 (dir=3): memcpy(dst, src, size) within L1."""
  SRC, DST, SIZE = 0x3000, 0x5000, 48
  for i in range(SIZE): coproc.mover.l1.write8(SRC + i, (0x80 + i) & 0xFF)
  _seed_xmov_cfg(coproc, thread=0, src_16b=SRC >> 4, dst_16b=DST >> 4,
                 size_16b=SIZE >> 4, direction=3)
  _push_step(coproc, _xmov_word(), thread=0)
  for i in range(SIZE):
    assert coproc.mover.l1.read8(DST + i) == (0x80 + i) & 0xFF


@spec("XMOV.FUNC.L0_TO_L1_ZERO_FILL")
def test_xmov_l0_to_l1_zero_fills_l1(coproc):
  """XMOV_L0_TO_L1 (dir=0): memset(dst, 0, size) into L1.  The 'L0' source
  label is a hardware misnomer for "zero fill" — no actual read occurs."""
  DST, SIZE = 0x4000, 32
  # Pre-seed dst with non-zero so we can observe the zero-fill.
  for i in range(SIZE): coproc.mover.l1.write8(DST + i, 0xFF)
  _seed_xmov_cfg(coproc, thread=0, src_16b=0, dst_16b=DST >> 4,
                 size_16b=SIZE >> 4, direction=0)
  _push_step(coproc, _xmov_word(), thread=0)
  for i in range(SIZE):
    assert coproc.mover.l1.read8(DST + i) == 0


@spec("XMOV.FUNC.L1_TO_L0_MEMCPY")
def test_xmov_l1_to_cfg_programs_config_registers(coproc):
  """XMOV_L1_TO_L0 (dir=1): memcpy from L1 to CFG space.  dst ≤ 0xFFFF is
  rebased to TENSIX_CFG_BASE (0xFFEF0000)."""
  SRC, CFG_OFF, SIZE = 0x2000, 0x100, 16
  for i in range(SIZE): coproc.mover.l1.write8(SRC + i, 0xC3)
  _seed_xmov_cfg(coproc, thread=0, src_16b=SRC >> 4, dst_16b=CFG_OFF >> 4,
                 size_16b=SIZE >> 4, direction=1)
  _push_step(coproc, _xmov_word(), thread=0)
  # CFG Memory is the coprocessor's .cfg — reads use the rebased address.
  for i in range(SIZE):
    assert coproc.cfg.read8(CFG_OFF + i) == 0xC3


@spec("XMOV.FUNC.L0_TO_L0_ZERO_FILL_CFG")
def test_xmov_l0_to_l0_zero_fills_cfg_space(coproc):
  """XMOV_L0_TO_L0 (dir=2): memset(dst, 0, size) into CFG space."""
  CFG_OFF, SIZE = 0x200, 32
  # Pre-seed cfg with non-zero so the zero-fill is observable.
  for i in range(SIZE): coproc.cfg.write8(CFG_OFF + i, 0xAA)
  _seed_xmov_cfg(coproc, thread=0, src_16b=0, dst_16b=CFG_OFF >> 4,
                 size_16b=SIZE >> 4, direction=2)
  _push_step(coproc, _xmov_word(), thread=0)
  for i in range(SIZE):
    assert coproc.cfg.read8(CFG_OFF + i) == 0


@spec("XMOV.FUNC.ALIGNMENT")
def test_xmov_transfers_are_16b_aligned(coproc):
  """All XMOV src, dst, and size values are in 16B units — unaligned byte
  values cannot arise through the normal issue path.  The Mover refuses to
  execute undefined unaligned transfers."""
  with pytest.raises(ValueError, match="16B alignment"):
    coproc.mover.transfer(dst=0x10, src=0x8, count=16, direction=3)
  with pytest.raises(ValueError, match="16B alignment"):
    coproc.mover.transfer(dst=0x10, src=0x20, count=15, direction=3)


@spec("XMOV.STALLWAIT.C9_CONDITION")
def test_xmov_c9_condition_clears_after_transfer(coproc):
  """STALLWAIT C9 (bit 0x200) waits for Mover outstanding requests.  The
  emulator completes transfers synchronously, so C9 is always clear — a
  STALLWAIT with cond_mask=C9 must release (wait_gate.opcode→None) rather
  than hang after the 1-cycle latch expires."""
  from dsl import TT_STALLWAIT
  from emu.tensix import STALL_XMOV, COND_XMOV
  SRC, DST = 0x1000, 0x2000
  for i in range(16): coproc.mover.l1.write8(SRC + i, 0x77)
  _seed_xmov_cfg(coproc, thread=0, src_16b=SRC >> 4, dst_16b=DST >> 4,
                 size_16b=1, direction=3)
  stallwait = int(TT_STALLWAIT(STALL_XMOV, COND_XMOV))
  nop = 0x02 << 24
  coproc.push_instruction(0, _xmov_word())
  coproc.push_instruction(0, stallwait)
  # Two NOPs: the first is consumed by the 1-cycle hold latch (lost),
  # the second reaches _evaluate which returns False for C9 (synchronous
  # Mover) and releases the gate.
  coproc.push_instruction(0, nop)
  coproc.push_instruction(0, nop)
  for _ in range(5):
    coproc.step()
  assert coproc.mover.l1.read8(DST) == 0x77
  assert coproc.threads[0].wait_gate.opcode is None


# ===========================================================================
# TDMA-RISC register block — MMIO-triggered transfers
# ===========================================================================

@spec("TDMA.REG.XMOV_SRC_ADDR")
def test_tdma_src_addr_register_has_functional_effect(brisc_with_l1):
  """Writing TDMA_XMOV_SRC_ADDR must affect the source of the next Mover transfer."""
  core, l1 = brisc_with_l1
  SRC, DST, SIZE = 0x1000, 0x2000, 16
  for i in range(SIZE): l1.write8(SRC + i, 0xAB)
  core.mem.write32(M.TDMA_XMOV_SRC_ADDR, SRC >> 4)
  core.mem.write32(M.TDMA_XMOV_DST_ADDR, DST >> 4)
  core.mem.write32(M.TDMA_XMOV_SIZE, SIZE >> 4)
  core.mem.write32(M.TDMA_XMOV_DIRECTION, 3)  # L1→L1
  core.mem.write32(M.TDMA_COMMAND, 0x40)
  assert l1.read8(DST) == 0xAB


@spec("TDMA.REG.XMOV_DST_ADDR")
def test_tdma_dst_addr_register_has_functional_effect(brisc_with_l1):
  """Writing TDMA_XMOV_DST_ADDR must determine where Mover writes data."""
  core, l1 = brisc_with_l1
  SRC, DST, SIZE = 0x1000, 0x3000, 16
  for i in range(SIZE): l1.write8(SRC + i, 0xCD)
  core.mem.write32(M.TDMA_XMOV_SRC_ADDR, SRC >> 4)
  core.mem.write32(M.TDMA_XMOV_DST_ADDR, DST >> 4)
  core.mem.write32(M.TDMA_XMOV_SIZE, SIZE >> 4)
  core.mem.write32(M.TDMA_XMOV_DIRECTION, 3)
  core.mem.write32(M.TDMA_COMMAND, 0x40)
  assert l1.read8(DST) == 0xCD


@spec("TDMA.REG.XMOV_SIZE")
def test_tdma_size_register_controls_transfer_length(brisc_with_l1):
  """Writing TDMA_XMOV_SIZE (16B units) must determine how many bytes are moved."""
  core, l1 = brisc_with_l1
  SRC, DST, SIZE_BLOCKS = 0x1000, 0x4000, 3
  for i in range(SIZE_BLOCKS * 16): l1.write8(SRC + i, 0xEF)
  # Pre-seed just past the end so we can confirm it is NOT overwritten.
  l1.write8(DST + SIZE_BLOCKS * 16, 0x12)
  core.mem.write32(M.TDMA_XMOV_SRC_ADDR, SRC >> 4)
  core.mem.write32(M.TDMA_XMOV_DST_ADDR, DST >> 4)
  core.mem.write32(M.TDMA_XMOV_SIZE, SIZE_BLOCKS)
  core.mem.write32(M.TDMA_XMOV_DIRECTION, 3)
  core.mem.write32(M.TDMA_COMMAND, 0x40)
  for i in range(SIZE_BLOCKS * 16):
    assert l1.read8(DST + i) == 0xEF
  assert l1.read8(DST + SIZE_BLOCKS * 16) == 0x12


@spec("TDMA.REG.XMOV_DIRECTION")
def test_tdma_direction_register_selects_zero_fill_vs_copy(brisc_with_l1):
  """DIRECTION=0 (L0→L1) must zero-fill; DIRECTION=3 (L1→L1) must copy."""
  core, l1 = brisc_with_l1
  DST = 0x5000
  for i in range(16): l1.write8(DST + i, 0xFF)
  core.mem.write32(M.TDMA_XMOV_SRC_ADDR, 0)
  core.mem.write32(M.TDMA_XMOV_DST_ADDR, DST >> 4)
  core.mem.write32(M.TDMA_XMOV_SIZE, 1)
  core.mem.write32(M.TDMA_XMOV_DIRECTION, 0)
  core.mem.write32(M.TDMA_COMMAND, 0x40)
  for i in range(16):
    assert l1.read8(DST + i) == 0


@spec("TDMA.REG.COMMAND_ADDR_TRIGGER")
def test_tdma_command_addr_triggers_xmov_l1_to_l1(brisc_with_l1):
  """Writing CMD_TDMA_XMOV (0x40) to COMMAND_ADDR triggers the Mover transfer."""
  core, l1 = brisc_with_l1
  SRC, DST, SIZE = 0x1000, 0x2000, 16
  for i in range(SIZE): l1.write8(SRC + i, 0xAB + i)
  core.mem.write32(M.TDMA_XMOV_SRC_ADDR, SRC >> 4)
  core.mem.write32(M.TDMA_XMOV_DST_ADDR, DST >> 4)
  core.mem.write32(M.TDMA_XMOV_SIZE, SIZE >> 4)
  core.mem.write32(M.TDMA_XMOV_DIRECTION, 3)
  core.mem.write32(M.TDMA_COMMAND, 0x40)
  for i in range(SIZE):
    assert l1.read8(DST + i) == (0xAB + i) & 0xFF


@spec("TDMA.REG.STATUS_IDLE")
def test_tdma_status_returns_fifo_empty_when_idle(brisc_with_l1):
  """STATUS register returns bit 3 (0x08, FIFO_EMPTY) when idle."""
  core, _ = brisc_with_l1
  status = core.mem.read32(M.TDMA_STATUS)
  assert status & 0x08


@spec("TDMA.REG.L1_BASE_ADDR")
def test_tdma_l1_base_addr_affects_compact_src_resolution(brisc_with_l1):
  """XMOV_L1_BASE_ADDR is MovCmdBase for compact command src_offset resolution."""
  core, l1 = brisc_with_l1
  BASE = 0x10   # MovCmdBase = 0x10 (byte addr 0x100)
  OFF  = 0x02   # src_offset in 16B units
  DST  = 0x50   # dst in 16B units
  core.mem.write32(M.TDMA_XMOV_L1_BASE, BASE)
  for i in range(16): l1.write8((BASE + OFF) * 16 + i, 0x77)
  # Compact: bit31=1, dir=1 (L1→L1), size=1, dst=DST, src_offset=OFF, opcode=0x40
  compact = (1 << 31) | (1 << 30) | (1 << 24) | (DST << 16) | (OFF << 8) | 0x40
  core.mem.write32(M.TDMA_COMMAND, compact)
  assert l1.read8(DST * 16) == 0x77


# ===========================================================================
# Compact command encoding
# ===========================================================================

@spec("TDMA.COMPACT.ENCODING")
def test_tdma_compact_command_l1_to_l1(brisc_with_l1):
  """Compact command (bit31=1): dir=1 (L1→L1), decode src_offset/dst/size."""
  core, l1 = brisc_with_l1
  SRC_BASE, SRC_OFF, DST_ADDR, SIZE, DIR = 0x10, 0x05, 0x30, 0x02, 1
  core.mem.write32(M.TDMA_XMOV_L1_BASE, SRC_BASE)
  for i in range(SIZE * 16):
    l1.write8((SRC_BASE + SRC_OFF) * 16 + i, 0xCC)
  compact = (1 << 31) | (DIR << 30) | (SIZE << 24) | (DST_ADDR << 16) \
           | (SRC_OFF << 8) | 0x40
  core.mem.write32(M.TDMA_COMMAND, compact)
  for i in range(SIZE * 16):
    assert l1.read8(DST_ADDR * 16 + i) == 0xCC


@spec("TDMA.COMPACT.SRC_OFFSET_RESOLUTION")
def test_tdma_compact_src_offset_is_added_to_l1_base(brisc_with_l1):
  """Compact source is (MovCmdBase + src_offset) * 16 bytes — confirm the
  addition by varying the base with a fixed offset and observing different
  source regions each time."""
  core, l1 = brisc_with_l1
  OFF, DST, SIZE = 0x04, 0x60, 1
  DIR = 1  # compact dir=1 → L1→L1
  for base, marker in [(0x10, 0xA1), (0x20, 0xB2)]:
    # Seed a distinct marker at each candidate source.
    for i in range(16): l1.write8((base + OFF) * 16 + i, marker)
    core.mem.write32(M.TDMA_XMOV_L1_BASE, base)
    compact = (1 << 31) | (DIR << 30) | (SIZE << 24) | (DST << 16) \
             | (OFF << 8) | 0x40
    core.mem.write32(M.TDMA_COMMAND, compact)
    assert l1.read8(DST * 16) == marker


# ===========================================================================
# Firmware API patterns
# ===========================================================================

@spec("TDMA.API.NON_COMPACT_SEQUENCE")
def test_tdma_non_compact_sequence_programs_and_fires(brisc_with_l1):
  """Full firmware sequence: write SRC/DST/SIZE/DIR then COMMAND.  This is
  the sequence emitted by tdma_xmov() in tt-metal's tdma_xmov.c."""
  core, l1 = brisc_with_l1
  SRC, DST, SIZE = 0x7000, 0x8000, 64
  for i in range(SIZE): l1.write8(SRC + i, (0xE0 + i) & 0xFF)
  mover_number = 1
  core.mem.write32(M.TDMA_XMOV_SRC_ADDR, SRC >> 4)
  core.mem.write32(M.TDMA_XMOV_DST_ADDR, DST >> 4)
  core.mem.write32(M.TDMA_XMOV_SIZE, SIZE >> 4)
  core.mem.write32(M.TDMA_XMOV_DIRECTION, 3)
  core.mem.write32(M.TDMA_COMMAND, 0x40 | (mover_number << 8))
  for i in range(SIZE):
    assert l1.read8(DST + i) == (0xE0 + i) & 0xFF


@spec("TDMA.API.WAIT_DONE_POLLING")
def test_tdma_wait_done_terminates_after_xmov(brisc_with_l1):
  """wait_tdma_movers_done()'s polling loop must terminate — STATUS reports
  FIFO_EMPTY (0x08) at all times in the synchronous emulator."""
  core, _ = brisc_with_l1
  for _ in range(10):
    status = core.mem.read32(M.TDMA_STATUS)
    if status & 0x08:
      return
  raise AssertionError(
    f"STATUS=0x{status:08X} never showed FIFO_EMPTY after 10 reads")


# ===========================================================================
# Packer metadata sideband registers — deferred to PR 2 (pack/unpack rewrite)
# ===========================================================================

@spec("TDMA.PACKED_SIZE.FIFO_TILE_SIZE")
@pytest.mark.xfail(strict=True, reason="Packer metadata sideband: depends on "
                                       "real Packer functional model (PR 2)")
def test_tdma_packed_tile_size_register(brisc_with_l1):
  """FIFO_PACKED_TILE_SIZE (0xFFB11030) must return bytes packed in last tile."""
  core, _ = brisc_with_l1
  val = core.mem.read32(M.TDMA_BASE + 0x30)
  assert val != 0


@spec("TDMA.PACKED_SIZE.FIFO_ZERO_MASK")
@pytest.mark.xfail(strict=True, reason="Packer metadata sideband: depends on "
                                       "real Packer functional model (PR 2)")
def test_tdma_packed_tile_zero_mask_pops_fifo(brisc_with_l1):
  """Read FIFO_PACKED_TILE_ZEROMASK (0xFFB11034): pop FIFO, return zero-mask."""
  core, _ = brisc_with_l1
  val = core.mem.read32(M.TDMA_BASE + 0x34)
  assert val != 0
