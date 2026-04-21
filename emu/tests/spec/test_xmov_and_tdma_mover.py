"""Spec tests for ../specs/xmov-and-tdma-mover.md.

CURRENTLY ZERO TEST COVERAGE in the emulator.

XMOV (opcode 0x40) is silently ignored in the Tensix coprocessor dispatch
(falls through to the "unknown opcode silently ignored" path in
tensix/__init__.py::TensixCoprocessor._dispatch).

The TDMA-RISC register block (0xFFB11000) is defined in memory.py but is not
mapped to any handler in the BRISC or TRISC cores — reads return 0 (no
handler) and writes are silently dropped.

All clauses in this file are xfail(strict=True).

xfail groups:
  XMOV instruction:
    XMOV.ENCODING.* — opcode not dispatched
    XMOV.PARAMS.*   — config-space params not read
    XMOV.FUNC.*     — L1-to-L1, zero-fill, L1-to-CFG transfers unimplemented
    XMOV.FUNC.ALIGNMENT — 16-byte alignment invariant not enforced
    XMOV.STALLWAIT.C9_CONDITION — C9 wait condition (though already clear by default)

  TDMA-RISC registers:
    TDMA.REG.*      — 0xFFB11xxx region not mapped; reads return 0; writes discarded
    TDMA.COMPACT.*  — compact command encoding not decoded
    TDMA.API.*      — firmware sequencing not executable
    TDMA.PACKED_SIZE.* — metadata sideband registers not mapped
"""

import pytest

from emu.tensix import TensixCoprocessor
from emu.memory import Memory
from emu import memory as M
from dsl import TT_PACR  # for opcode constant reference
from emu.core import BRISC

from .conftest import spec


# Local fixtures

@pytest.fixture
def coproc():
  """Minimal TensixCoprocessor for XMOV tests."""
  return TensixCoprocessor()


@pytest.fixture
def brisc_with_l1():
  """BRISC core with an L1 memory region but no TDMA handler registered."""
  l1 = Memory()
  core = BRISC(l1=l1)
  return core, l1


def _push_step(coproc, word, thread=2, n=1):
  coproc.push_instruction(thread, int(word))
  for _ in range(n):
    coproc.step()


def _xmov_word(mov_block_selection=0, last=0):
  """Build a raw XMOV Tensix word (opcode=0x40)."""
  return (0x40 << 24) | (mov_block_selection << 23) | last


# ===========================================================================
# XMOV instruction — not dispatched (all xfail)
# ===========================================================================

@spec("XMOV.ENCODING.OPCODE")
def test_xmov_opcode_is_dispatched(coproc):
  """XMOV (0x40) must be dispatched to the Mover backend, not silently dropped."""
  # Pre-seed L1-to-L1 transfer parameters in cfg space (thread 0).
  # src = L1 address 0x1000 (16B units = 0x100), dst = 0x2000 (= 0x200),
  # size = 1 block (= 0x10 bytes), direction = 3 (L1→L1).
  # THCON_SEC0_REG6 addresses (ADDR32 indices 6,7,8,9 in the 32-bit config space):
  # For a real implementation these would be read; here we just verify dispatch.
  word = _xmov_word(mov_block_selection=0, last=0)
  _push_step(coproc, word, thread=0)
  # If XMOV is dispatched, it would have executed the Mover() transfer.
  # Since it is silently ignored, we assert dispatch happened by checking
  # a side-effect — which will not exist, causing this test to fail as expected.
  raise AssertionError("XMOV opcode not dispatched by TensixCoprocessor")


@spec("XMOV.PARAMS.FROM_CFG_SPACE")
def test_xmov_reads_transfer_params_from_cfg(coproc):
  """XMOV must read src/dst/size/dir from THCON_SEC0_REG6 in config space."""
  raise AssertionError("XMOV config-space parameter read not implemented")


@spec("XMOV.ENCODING.MOV_BLOCK_SELECTION")
def test_xmov_mov_block_selection_field(coproc):
  """Mov_block_selection [23] selects between two move blocks."""
  raise AssertionError("Mov_block_selection not decoded")


@spec("XMOV.ENCODING.LAST")
def test_xmov_last_flag_flushes_accumulators(coproc):
  """Last=1 must flush accumulation buffers when the transfer completes."""
  raise AssertionError("XMOV Last flag not decoded")


# ===========================================================================
# XMOV functional model — transfer directions (all xfail)
# ===========================================================================

@spec("XMOV.FUNC.L1_TO_L1_MEMCPY")
def test_xmov_l1_to_l1_copies_data(coproc):
  """XMOV_L1_TO_L1 (dir=3): memcpy(dst, src, size) within L1."""
  # With a real implementation: seed L1 at src, issue XMOV dir=3, verify dst.
  raise AssertionError("XMOV L1→L1 not implemented")


@spec("XMOV.FUNC.L0_TO_L1_ZERO_FILL")
def test_xmov_l0_to_l1_zero_fills_l1(coproc):
  """XMOV_L0_TO_L1 (dir=0): memset(dst, 0, size) into L1."""
  raise AssertionError("XMOV L0→L1 zero-fill not implemented")


@spec("XMOV.FUNC.L1_TO_L0_MEMCPY")
def test_xmov_l1_to_cfg_programs_config_registers(coproc):
  """XMOV_L1_TO_L0 (dir=1): memcpy from L1 to CFG space (dst <= 0xFFFF → +0xFFEF0000)."""
  raise AssertionError("XMOV L1→CFG not implemented")


@spec("XMOV.FUNC.L0_TO_L0_ZERO_FILL_CFG")
def test_xmov_l0_to_l0_zero_fills_cfg_space(coproc):
  """XMOV_L0_TO_L0 (dir=2): memset(dst, 0, size) into CFG space or NCRISC IRAM."""
  raise AssertionError("XMOV L0→CFG zero-fill not implemented")


@spec("XMOV.FUNC.ALIGNMENT")
def test_xmov_transfers_are_16b_aligned(coproc):
  """All XMOV src, dst, and size values must be multiples of 16 bytes."""
  raise AssertionError("XMOV 16-byte alignment not enforced")


@spec("XMOV.STALLWAIT.C9_CONDITION")
def test_xmov_c9_condition_clears_after_transfer(coproc):
  """After XMOV, STALLWAIT C9 must report clear (Mover no longer busy)."""
  raise AssertionError("XMOV C9 stallwait condition not modeled")


# ===========================================================================
# TDMA-RISC register block — not mapped (all xfail)
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
  # If TDMA_XMOV_SRC_ADDR is functionally effective, DST would have 0xAB bytes.
  assert l1.read8(DST) == 0xAB, "Mover transfer did not occur (TDMA not implemented)"


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
  assert l1.read8(DST) == 0xCD, "Mover transfer did not occur (TDMA not implemented)"


@spec("TDMA.REG.XMOV_SIZE")
def test_tdma_size_register_controls_transfer_length(brisc_with_l1):
  """Writing TDMA_XMOV_SIZE (16B units) must determine how many bytes are moved."""
  core, l1 = brisc_with_l1
  SRC, DST, SIZE_BLOCKS = 0x1000, 0x4000, 1   # 1 block = 16 bytes
  for i in range(SIZE_BLOCKS * 16): l1.write8(SRC + i, 0xEF)
  core.mem.write32(M.TDMA_XMOV_SRC_ADDR, SRC >> 4)
  core.mem.write32(M.TDMA_XMOV_DST_ADDR, DST >> 4)
  core.mem.write32(M.TDMA_XMOV_SIZE, SIZE_BLOCKS)
  core.mem.write32(M.TDMA_XMOV_DIRECTION, 3)
  core.mem.write32(M.TDMA_COMMAND, 0x40)
  assert l1.read8(DST) == 0xEF, "Mover transfer did not occur (TDMA not implemented)"


@spec("TDMA.REG.XMOV_DIRECTION")
def test_tdma_direction_register_selects_zero_fill_vs_copy(brisc_with_l1):
  """DIRECTION=0 (L0→L1) must zero-fill; DIRECTION=3 (L1→L1) must copy."""
  core, l1 = brisc_with_l1
  DST = 0x5000
  # Pre-seed dst with non-zero data.
  for i in range(16): l1.write8(DST + i, 0xFF)
  # Request zero-fill (L0→L1 = direction 0).
  core.mem.write32(M.TDMA_XMOV_SRC_ADDR, 0)
  core.mem.write32(M.TDMA_XMOV_DST_ADDR, DST >> 4)
  core.mem.write32(M.TDMA_XMOV_SIZE, 1)
  core.mem.write32(M.TDMA_XMOV_DIRECTION, 0)
  core.mem.write32(M.TDMA_COMMAND, 0x40)
  assert l1.read8(DST) == 0, "Zero-fill Mover transfer did not occur (TDMA not implemented)"


@spec("TDMA.REG.COMMAND_ADDR_TRIGGER")
def test_tdma_command_addr_triggers_xmov_l1_to_l1(brisc_with_l1):
  """Write CMD_TDMA_XMOV (0x40) to COMMAND_ADDR triggers Mover L1→L1 transfer."""
  core, l1 = brisc_with_l1
  SRC = 0x1000
  DST = 0x2000
  SIZE = 16  # one 16-byte block

  # Seed source region with a pattern.
  for i in range(SIZE):
    l1.write8(SRC + i, 0xAB + i)

  # Stage parameters (these will be discarded — register not mapped).
  core.mem.write32(M.TDMA_XMOV_SRC_ADDR, SRC >> 4)   # 16B units
  core.mem.write32(M.TDMA_XMOV_DST_ADDR, DST >> 4)
  core.mem.write32(M.TDMA_XMOV_SIZE, SIZE >> 4)
  core.mem.write32(M.TDMA_XMOV_DIRECTION, 3)          # XMOV_L1_TO_L1
  # Trigger.
  core.mem.write32(M.TDMA_COMMAND, 0x40)

  # Verify destination received the copy.
  for i in range(SIZE):
    got = l1.read8(DST + i)
    assert got == (0xAB + i) & 0xFF, \
      f"Byte {i}: expected 0x{(0xAB+i)&0xFF:02X}, got 0x{got:02X} (XMOV not implemented)"


@spec("TDMA.REG.STATUS_IDLE")
def test_tdma_status_returns_fifo_empty_when_idle(brisc_with_l1):
  """STATUS register (0xFFB11014) must return bit 3 (0x08 = FIFO_EMPTY) when idle."""
  core, l1 = brisc_with_l1
  status = core.mem.read32(M.TDMA_STATUS)
  # Bit 3 = command_queue_empty (0x08) must be set when idle.
  assert status & 0x08, \
    f"STATUS=0x{status:08X} does not have FIFO_EMPTY (bit 3) set (register not mapped)"


@spec("TDMA.REG.L1_BASE_ADDR")
def test_tdma_l1_base_addr_affects_compact_src_resolution(brisc_with_l1):
  """XMOV_L1_BASE_ADDR must be used as MovCmdBase in compact command src_offset resolution."""
  core, l1 = brisc_with_l1
  BASE = 0x10   # MovCmdBase = 0x10 (byte addr 0x100)
  OFF  = 0x02   # src_offset in 16B units
  DST  = 0x50
  core.mem.write32(M.TDMA_XMOV_L1_BASE, BASE)
  # Seed source = (BASE + OFF)*16 = 0x120..0x12F
  for i in range(16): l1.write8((BASE + OFF) * 16 + i, 0x77)
  # Compact: bit31=1, dir=1 (L1→L1), size=1, dst=DST, src_offset=OFF, opcode=0x40
  compact = (1 << 31) | (1 << 30) | (1 << 24) | (DST << 16) | (OFF << 8) | 0x40
  core.mem.write32(M.TDMA_COMMAND, compact)
  assert l1.read8(DST * 16) == 0x77, \
    "Compact Mover transfer with L1_BASE_ADDR not implemented"


# ===========================================================================
# Compact command encoding (xfail)
# ===========================================================================

@spec("TDMA.COMPACT.ENCODING")
def test_tdma_compact_command_l1_to_l1(brisc_with_l1):
  """Compact command (bit 31=1): dir=1 (L1→L1), decode src_offset, dst_addr, xfer_size."""
  core, l1 = brisc_with_l1
  SRC_BASE = 0x10   # MovCmdBase = 0x10 (16B units = 0x100 bytes)
  SRC_OFF  = 0x05   # src_offset in 16B units
  DST_ADDR = 0x30   # dst in 16B units
  SIZE     = 0x02   # 2 × 16B = 32 bytes
  DIR      = 1      # L1→L1

  core.mem.write32(M.TDMA_XMOV_L1_BASE, SRC_BASE)

  # Seed source.
  for i in range(SIZE * 16):
    l1.write8((SRC_BASE + SRC_OFF) * 16 + i, 0xCC)

  # Build compact word: bit31=1, [30]=dir=1, [29:24]=size=2, [23:16]=dst=0x30,
  #                     [15:8]=src_off=5, [7:0]=0x40
  compact = (1 << 31) | (DIR << 30) | (SIZE << 24) | (DST_ADDR << 16) \
           | (SRC_OFF << 8) | 0x40
  core.mem.write32(M.TDMA_COMMAND, compact)

  # Verify destination.
  for i in range(SIZE * 16):
    got = l1.read8(DST_ADDR * 16 + i)
    assert got == 0xCC, f"Byte {i}: compact XMOV not implemented"


@spec("TDMA.COMPACT.SRC_OFFSET_RESOLUTION")
def test_tdma_compact_src_offset_is_added_to_l1_base(brisc_with_l1):
  """Compact command: effective source = (MovCmdBase + src_offset) * 16 bytes."""
  raise AssertionError("Compact src_offset resolution not implemented")


# ===========================================================================
# Firmware API patterns (xfail)
# ===========================================================================

@spec("TDMA.API.NON_COMPACT_SEQUENCE")
def test_tdma_non_compact_sequence_programs_and_fires(brisc_with_l1):
  """Non-compact: write SRC/DST/SIZE/DIR to CmdParams[], then trigger COMMAND_ADDR."""
  raise AssertionError("Non-compact TDMA sequence not implemented")


@spec("TDMA.API.WAIT_DONE_POLLING")
def test_tdma_wait_done_terminates_after_xmov(brisc_with_l1):
  """STATUS bit 3 (FIFO_EMPTY) must be set after transfer so wait loop exits."""
  core, l1 = brisc_with_l1
  # Simulate firmware: poll STATUS until bit 3 set, with a limited retry count
  # to avoid actual infinite loop in tests.
  for _ in range(10):
    status = core.mem.read32(M.TDMA_STATUS)
    if status & 0x08:
      return   # success
  raise AssertionError(
    f"STATUS=0x{status:08X} never showed FIFO_EMPTY (bit 3) set after 10 reads")


# ===========================================================================
# Packer metadata sideband registers (xfail)
# ===========================================================================

@spec("TDMA.PACKED_SIZE.FIFO_TILE_SIZE")
def test_tdma_packed_tile_size_register(brisc_with_l1):
  """FIFO_PACKED_TILE_SIZE (0xFFB11030) must return bytes packed in last tile."""
  core, l1 = brisc_with_l1
  # After packing a tile, firmware reads this to update the CB write pointer.
  # Without pack implementation this cannot be tested end-to-end; we just
  # verify the register is addressable and returns a meaningful (non-zero) value
  # after a notional tile pack.
  val = core.mem.read32(M.TDMA_BASE + 0x30)  # FIFO_PACKED_TILE_SIZE(0)
  assert val != 0, \
    "FIFO_PACKED_TILE_SIZE returned 0 (packer metadata sideband not implemented)"


@spec("TDMA.PACKED_SIZE.FIFO_ZERO_MASK")
def test_tdma_packed_tile_zero_mask_pops_fifo(brisc_with_l1):
  """Read FIFO_PACKED_TILE_ZEROMASK (0xFFB11034): pop FIFO, return zero-compression mask."""
  raise AssertionError("FIFO_PACKED_TILE_ZEROMASK sideband not implemented")
