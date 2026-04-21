"""Spec tests for ../specs/circular-buffers.md.

Covers: CB count, L1 config layout, sequential allocation, overflow/range
errors, CB-to-stream mapping constants, stream register isolation, and
remote NOC atomic updates to tiles_received.
"""

import pytest

from emu.device import Device
from emu.memory import (
    NUM_CBS, CB_CONFIG_WORDS, CB_CONFIG_BYTES, CB_L1_CONFIG_BASE,
    KERNEL_CONFIG_BASE, DATA_BUFFER_SPACE_BASE, L1_SIZE,
    STREAM_BASE, STREAM_STRIDE, STREAM_TILES_ACKED, STREAM_TILES_RECEIVED,
    DISPATCH_MESSAGE_ADDR,
    cb_stream_id, cb_tiles_received_addr, cb_tiles_acked_addr,
    NIU_CMD_BUF_STRIDE, NIU_TARG_ADDR_LO, NIU_TARG_ADDR_MID,
    NIU_TARG_ADDR_HI, NIU_RET_ADDR_LO, NIU_AT_LEN_BE, NIU_AT_DATA,
    NIU_CTRL, NIU_CMD_CTRL,
    NOC_CTRL_AT, NOC0_BASE,
)
from emu.noc import AT_INCR_GET
from emu.tests._helpers import mini_device

from .conftest import spec


# ===========================================================================
# CB count
# ===========================================================================

@spec("CB.COUNT.64")
def test_num_cbs():
    """NUM_CBS == 64."""
    assert NUM_CBS == 64


# ===========================================================================
# L1 config layout constants
# ===========================================================================

@spec("CB.CONFIG.WORDS_PER_SLOT")
def test_cb_config_words():
    """CB_CONFIG_WORDS == 4 (16 bytes per slot)."""
    assert CB_CONFIG_WORDS == 4
    assert CB_CONFIG_BYTES == 16


@spec("CB.CONFIG.BASE_ADDR")
def test_cb_config_base_addr():
    """CB_L1_CONFIG_BASE == KERNEL_CONFIG_BASE == 0x86B0."""
    assert CB_L1_CONFIG_BASE == KERNEL_CONFIG_BASE
    assert CB_L1_CONFIG_BASE == 0x86B0


@spec("CB.CONFIG.NO_DATAFORMAT")
def test_cb_config_no_dataformat():
    """Only 4 words written; no 5th word for dataformat."""
    dev = mini_device()
    dev.configure_cbs({0: (1, 512)})
    tile = dev.tiles[(1, 2)]
    base = CB_L1_CONFIG_BASE
    # Words 0-3 are set; word 4 should be 0 (no format stored)
    assert tile.l1.read32(base + 16) == 0  # no 5th word


# ===========================================================================
# CB config word semantics
# ===========================================================================

@spec("CB.CONFIG.WORD0_ADDR")
def test_cb_config_word0_is_address():
    """Word 0 is cb_address (FIFO start address in L1)."""
    dev = mini_device()
    dev.configure_cbs({0: (2, 2048)})
    tile = dev.tiles[(1, 2)]
    base = CB_L1_CONFIG_BASE
    assert tile.l1.read32(base + 0) == DATA_BUFFER_SPACE_BASE


@spec("CB.CONFIG.WORD1_SIZE")
def test_cb_config_word1_is_size():
    """Word 1 is cb_size = num_pages * page_size."""
    dev = mini_device()
    dev.configure_cbs({0: (3, 1024)})
    tile = dev.tiles[(1, 2)]
    base = CB_L1_CONFIG_BASE
    assert tile.l1.read32(base + 4) == 3 * 1024


@spec("CB.CONFIG.WORD2_NUM_PAGES")
def test_cb_config_word2_is_num_pages():
    """Word 2 is num_pages."""
    dev = mini_device()
    dev.configure_cbs({0: (5, 512)})
    tile = dev.tiles[(1, 2)]
    base = CB_L1_CONFIG_BASE
    assert tile.l1.read32(base + 8) == 5


@spec("CB.CONFIG.WORD3_PAGE_SIZE")
def test_cb_config_word3_is_page_size():
    """Word 3 is page_size."""
    dev = mini_device()
    dev.configure_cbs({0: (1, 4096)})
    tile = dev.tiles[(1, 2)]
    base = CB_L1_CONFIG_BASE
    assert tile.l1.read32(base + 12) == 4096


# ===========================================================================
# Sequential allocation
# ===========================================================================

@spec("CB.ALLOC.SEQUENTIAL")
def test_cb_allocation_sequential():
    """CBs are allocated sequentially from DATA_BUFFER_SPACE_BASE."""
    dev = mini_device()
    dev.configure_cbs({
        0: (2, 2048),   # occupies DATA_BUFFER_SPACE_BASE .. +4096-1
        1: (4, 1024),   # starts right after
    })
    tile = dev.tiles[(1, 2)]
    base1 = CB_L1_CONFIG_BASE + 1 * CB_CONFIG_BYTES
    addr1 = tile.l1.read32(base1 + 0)
    assert addr1 == DATA_BUFFER_SPACE_BASE + 2 * 2048


@spec("CB.ALLOC.ALL_TILES")
def test_configure_cbs_writes_all_tiles():
    """configure_cbs writes identical config to every tile."""
    dev = Device(tensix_x=(1, 2), tensix_y=(2,))
    dev.configure_cbs({0: (1, 512)})
    for tile in dev.tiles.values():
        base = CB_L1_CONFIG_BASE
        assert tile.l1.read32(base + 0) == DATA_BUFFER_SPACE_BASE
        assert tile.l1.read32(base + 4) == 512
        assert tile.l1.read32(base + 8) == 1
        assert tile.l1.read32(base + 12) == 512


# ===========================================================================
# Error cases
# ===========================================================================

@spec("CB.ALLOC.OVERFLOW_RAISES")
def test_cb_overflow_raises():
    """Configuring a CB that overflows L1 raises ValueError."""
    dev = mini_device()
    available = L1_SIZE - DATA_BUFFER_SPACE_BASE
    with pytest.raises(ValueError):
        dev.configure_cbs({0: (1, available + 1)})


@spec("CB.ALLOC.INDEX_RANGE")
def test_cb_bad_index_raises():
    """CB index out of range 0..63 raises ValueError."""
    dev = mini_device()
    with pytest.raises(ValueError):
        dev.configure_cbs({64: (1, 512)})

    with pytest.raises(ValueError):
        dev.configure_cbs({-1: (1, 512)})


# ===========================================================================
# CB-to-stream mapping
# ===========================================================================

@spec("CB.STREAM.CB_N_IS_STREAM_N")
def test_cb_stream_id_identity():
    """CB N maps directly to stream N (OPERAND_START_STREAM=0)."""
    assert cb_stream_id(0) == 0
    assert cb_stream_id(5) == 5
    assert cb_stream_id(63) == 63


@spec("CB.STREAM.TILES_RECEIVED_ADDR")
def test_cb_tiles_received_addr():
    """tiles_received address for CB 0 is 0xFFB40028."""
    assert cb_tiles_received_addr(0) == 0xFFB40028


@spec("CB.STREAM.TILES_ACKED_ADDR")
def test_cb_tiles_acked_addr():
    """tiles_acked address for CB 0 is 0xFFB40020."""
    assert cb_tiles_acked_addr(0) == 0xFFB40020


# ===========================================================================
# Stream register isolation from L1
# ===========================================================================

@spec("STREG.CB.ISOLATION_FROM_L1", "CB.STREAM.CB_N_IS_STREAM_N")
def test_stream_reg_isolated_from_l1():
    """Writing a stream register must not touch L1, and vice versa."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    addr = cb_tiles_received_addr(3)
    # Write through BRISC's address bus (hits stream_regs via bus registration)
    tile.brisc.mem.write32(addr, 0xDEADBEEF)
    # Must appear in stream_regs
    assert tile.stream_regs.read32(addr) == 0xDEADBEEF
    # Must NOT appear in raw L1
    assert tile.l1.read32(addr) == 0


@spec("STREG.CB.WRITE_VISIBLE")
def test_stream_reg_write_visible_across_cores():
    """Write to stream reg from BRISC is visible from TRISC0 at the same address."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    recv_addr = cb_tiles_received_addr(5)
    tile.brisc.mem.write32(recv_addr, 42)
    assert tile.trisc0.mem.read32(recv_addr) == 42


# ===========================================================================
# CB synchronization pattern
# ===========================================================================

@spec("CB.STREAM.TILES_RECEIVED_ADDR", "CB.STREAM.TILES_ACKED_ADDR")
def test_cb_sync_pattern():
    """CB sync: (received - acked) gives tiles available to consumer."""
    dev = mini_device()
    tile = dev.tiles[(1, 2)]
    cb = 0
    acked_addr = cb_tiles_acked_addr(cb)
    recv_addr  = cb_tiles_received_addr(cb)

    # Initial state
    assert tile.brisc.mem.read32(recv_addr) == 0
    assert tile.trisc0.mem.read32(acked_addr) == 0

    # Producer pushes 3 tiles
    tile.ncrisc.mem.write32(recv_addr, 3)
    received = tile.trisc0.mem.read32(recv_addr)
    acked    = tile.trisc0.mem.read32(acked_addr)
    assert received - acked == 3

    # Consumer pops 2 tiles
    tile.trisc0.mem.write32(acked_addr, acked + 2)
    received = tile.ncrisc.mem.read32(recv_addr)
    acked    = tile.ncrisc.mem.read32(acked_addr)
    assert received - acked == 1


# ===========================================================================
# Remote NOC atomic → stream registers
# ===========================================================================

@spec("STREG.CB.REMOTE_ATOMIC")
def test_remote_noc_atomic_lands_in_stream_regs():
    """NOC INCR_GET targeting tiles_received lands in StreamRegisters, not L1."""
    dev = Device(tensix_x=(1, 2), tensix_y=(2,))
    tile_a = dev.tiles[(1, 2)]
    tile_b = dev.tiles[(2, 2)]
    cb = 2
    recv_addr = cb_tiles_received_addr(cb)

    bus = tile_a.brisc.mem
    buf = NOC0_BASE + 0 * NIU_CMD_BUF_STRIDE
    bus.write32(buf + NIU_TARG_ADDR_LO,  recv_addr)
    bus.write32(buf + NIU_TARG_ADDR_MID, 0)
    bus.write32(buf + NIU_TARG_ADDR_HI,  (2 << 6) | 2)
    bus.write32(buf + NIU_RET_ADDR_LO,   0x1000)
    bus.write32(buf + NIU_AT_LEN_BE,     (AT_INCR_GET << 12) | (1 << 6))
    bus.write32(buf + NIU_AT_DATA,       1)
    bus.write32(buf + NIU_CTRL,          NOC_CTRL_AT)
    bus.write32(buf + NIU_CMD_CTRL,      1)

    # Landed in stream_regs
    assert tile_b.stream_regs.read32(recv_addr) == 1
    # NOT in L1
    assert tile_b.l1.read32(recv_addr) == 0


# ===========================================================================
# Dispatch message address
# ===========================================================================

@spec("STREG.DISPATCH.ADDR")
def test_dispatch_message_addr():
    """DISPATCH_MESSAGE_ADDR == 0xFFB70438 (stream 48, reg 270)."""
    assert DISPATCH_MESSAGE_ADDR == 0xFFB70438


# ===========================================================================
# Tile header not used
# ===========================================================================

@spec("CB.TILE_HDR.NOT_USED")
def test_tile_header_not_used_in_cb_config():
    """CB config stores only 4 words: no tile header accounting."""
    dev = mini_device()
    dev.configure_cbs({0: (1, 1024)})
    tile = dev.tiles[(1, 2)]
    base = CB_L1_CONFIG_BASE
    # page_size = 1024 (pure data, no 16-byte header)
    assert tile.l1.read32(base + 12) == 1024
    # size = 1 * 1024
    assert tile.l1.read32(base + 4) == 1024
