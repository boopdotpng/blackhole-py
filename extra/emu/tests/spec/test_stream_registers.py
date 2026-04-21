"""Spec tests for ../specs/stream-registers.md.

Covers: address space constants, CB-to-stream mapping, tiles_acked/received
register R/W, stream isolation, dispatch address, and sparse backing behavior.
"""

import pytest

from emu import memory as M
from emu.memory import (
    STREAM_BASE, STREAM_STRIDE, STREAM_END,
    STREAM_TILES_ACKED, STREAM_TILES_RECEIVED, STREAM_SYNC_REG,
    STREAM_DISPATCH_REG, STREAM_DISPATCH_ID,
    DISPATCH_MESSAGE_ADDR,
    cb_stream_id, cb_tiles_received_addr, cb_tiles_acked_addr,
)
from emu.tests._helpers import mini_device

from .conftest import spec


# ===========================================================================
# Address space constants
# ===========================================================================

@spec("STREG.ADDR.BASE")
def test_stream_base():
    assert STREAM_BASE == 0xFFB40000


@spec("STREG.ADDR.BASE")
def test_stream_stride():
    assert STREAM_STRIDE == 0x1000


@spec("STREG.ADDR.BASE")
def test_stream_end():
    assert STREAM_END == 0xFFB7FFFF


@spec("STREG.ADDR.FORMULA")
@pytest.mark.parametrize("stream_id,reg_id,expected", [
    (0,  0,  0xFFB40000),
    (0,  8,  0xFFB40020),
    (0,  10, 0xFFB40028),
    (0,  31, 0xFFB4007C),
    (5,  10, 0xFFB45028),
    (48, 270, 0xFFB70438),
])
def test_stream_reg_addr_formula(stream_id, reg_id, expected):
    """STREAM_REG_ADDR = 0xFFB40000 + stream_id*0x1000 + reg_id*4."""
    assert STREAM_BASE + stream_id * STREAM_STRIDE + reg_id * 4 == expected


# ===========================================================================
# Register index constants
# ===========================================================================

@spec("STREG.CB.TILES_ACKED_REG")
def test_tiles_acked_offset():
    assert STREAM_TILES_ACKED == 0x020


@spec("STREG.CB.TILES_RECEIVED_REG")
def test_tiles_received_offset():
    assert STREAM_TILES_RECEIVED == 0x028


@spec("STREG.SYNC.STREAM0_REG31")
def test_sync_reg_offset():
    assert STREAM_SYNC_REG == 0x07C


@spec("STREG.DISPATCH.ADDR")
def test_dispatch_message_addr():
    assert DISPATCH_MESSAGE_ADDR == 0xFFB70438


@spec("STREG.DISPATCH.STREAM_ID")
def test_dispatch_stream_id():
    assert STREAM_DISPATCH_ID == 48
    assert STREAM_DISPATCH_REG == 270 * 4


# ===========================================================================
# Read/write through tile's address bus
# ===========================================================================

@spec("STREG.CB.WRITE_VISIBLE")
def test_stream_reg_write_read_same_core():
    """Write and read tiles_received through the same core's bus."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    cb = 5
    recv_addr = STREAM_BASE + cb * STREAM_STRIDE + STREAM_TILES_RECEIVED
    tile.brisc.mem.write32(recv_addr, 42)
    assert tile.brisc.mem.read32(recv_addr) == 42


@spec("STREG.CB.WRITE_VISIBLE")
def test_stream_reg_write_visible_across_cores():
    """Write from NCRISC is visible to TRISC0."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    addr = STREAM_BASE + 3 * STREAM_STRIDE + STREAM_TILES_RECEIVED
    tile.ncrisc.mem.write32(addr, 7)
    assert tile.trisc0.mem.read32(addr) == 7


@spec("STREG.CB.ISOLATION_FROM_L1")
def test_stream_reg_isolated_from_l1():
    """Write to stream reg does not modify L1; write to L1 does not affect stream reg."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    addr = cb_tiles_received_addr(7)
    # Write through the bus → lands in stream_regs
    tile.brisc.mem.write32(addr, 0xBEEF)
    assert tile.stream_regs.read32(addr) == 0xBEEF
    # Not in raw L1
    assert tile.l1.read32(addr) == 0


# ===========================================================================
# Sparse backing store
# ===========================================================================

@spec("STREG.IMPL.SPARSE")
def test_unwritten_stream_reg_reads_zero():
    """Unwritten stream registers return 0."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    # Read a never-written stream register
    addr = STREAM_BASE + 10 * STREAM_STRIDE + STREAM_TILES_ACKED
    assert tile.brisc.mem.read32(addr) == 0


@spec("STREG.IMPL.SPARSE")
def test_stream_reg_write_persist():
    """Written stream registers retain their value."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    addr = STREAM_BASE + 2 * STREAM_STRIDE + STREAM_TILES_ACKED
    tile.brisc.mem.write32(addr, 99)
    assert tile.brisc.mem.read32(addr) == 99
    tile.brisc.mem.write32(addr, 100)
    assert tile.brisc.mem.read32(addr) == 100


# ===========================================================================
# Sync register (stream 0, reg 31)
# ===========================================================================

@spec("STREG.SYNC.STREAM0_REG31")
def test_sync_register_read_write():
    """Stream 0, reg 31 (+0x07C) is a general-purpose sync register."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    sync_addr = STREAM_BASE + 0 * STREAM_STRIDE + STREAM_SYNC_REG
    tile.brisc.mem.write32(sync_addr, 0xDEAD)
    assert tile.brisc.mem.read32(sync_addr) == 0xDEAD
    # Also visible from NCRISC
    assert tile.ncrisc.mem.read32(sync_addr) == 0xDEAD


# ===========================================================================
# Dispatch register (stream 48, reg 270)
# ===========================================================================

@spec("STREG.DISPATCH.ADDR", "STREG.DISPATCH.STREAM_ID")
def test_dispatch_register_write_sink():
    """Stream 48, reg 270 accepts writes without error."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    tile.brisc.mem.write32(DISPATCH_MESSAGE_ADDR, 0x1)
    # No assertion beyond "no exception"; it's a write sink for slow dispatch
