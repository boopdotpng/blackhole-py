"""Spec tests for ../specs/niu.md.

Covers: NIU address layout, command buffer fire/clear, NOC_ID_LOGICAL
pre-population, unicast/multicast coordinate encoding, read/write/inline-write
transactions, and status counter behavior.

Each test is pinned to one or more clauses from ../clauses/niu.md.
Tests that exercise clauses where the emulator diverges from spec are marked
xfail(strict=True).
"""

import struct
import pytest

from emu import memory as M
from emu.memory import Memory
from emu.noc import NOC, noc_key

from .conftest import spec


# ===========================================================================
# Fixtures
# ===========================================================================

def _make_network_tile(x, y, network):
    """Build a minimal (no full Device) tile: L1 + NOC0 + NOC1."""
    l1 = Memory()
    network[noc_key(x, y)] = l1
    noc0 = NOC(0, l1, network, x, y)
    noc1 = NOC(1, l1, network, x, y)
    noc0.pre_populate()
    noc1.pre_populate()
    return l1, noc0, noc1


@pytest.fixture
def three_tile_network():
    """Source (1,2), target A (3,4), target B (4,4) on the same network."""
    net = {}
    src_l1, src_noc0, src_noc1 = _make_network_tile(1, 2, net)
    dst_l1, dst_noc0, dst_noc1 = _make_network_tile(3, 4, net)
    dst2_l1, dst2_noc0, dst2_noc1 = _make_network_tile(4, 4, net)
    return dict(
        network=net,
        src_l1=src_l1, src_noc0=src_noc0, src_noc1=src_noc1,
        src_xy=(1, 2),
        dst_l1=dst_l1, dst_noc0=dst_noc0, dst_noc1=dst_noc1,
        dst_xy=(3, 4),
        dst2_l1=dst2_l1, dst2_noc0=dst2_noc0, dst2_noc1=dst2_noc1,
        dst2_xy=(4, 4),
    )


# ===========================================================================
# Address space — NIU base addresses
# ===========================================================================

@spec("NIU.ADDR.NOC0_BASE")
def test_noc0_base_address():
    assert M.NOC0_BASE == 0xFFB20000


@spec("NIU.ADDR.NOC1_BASE")
def test_noc1_base_address():
    assert M.NOC1_BASE == 0xFFB30000


# ===========================================================================
# Command buffer stride and fire/clear
# ===========================================================================

@spec("NIU.CMDBUF.STRIDE")
def test_cmd_buf_stride():
    """4 command buffers at stride 0x800."""
    assert M.NIU_CMD_BUF_STRIDE == 0x800


@spec("NIU.CMDBUF.FIRE")
def test_cmd_ctrl_fire_clears(two_tile_network):
    """Writing 1 to CMD_CTRL fires and then clears CMD_CTRL to 0."""
    net = two_tile_network
    noc = net['src_noc0']
    # Program a trivial inline write to avoid KeyError in fire path
    buf = 0
    base = buf * M.NIU_CMD_BUF_STRIDE
    noc.regs.write32(base + M.NIU_TARG_ADDR_LO, 0x1000)
    noc.regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_TARG_ADDR_HI,
                     (net['dst_xy'][1] << 6) | net['dst_xy'][0])
    noc.regs.write32(base + M.NIU_AT_DATA, 0xDEAD)
    noc.regs.write32(base + M.NIU_CTRL, M.NOC_CTRL_WR | M.NOC_CTRL_WR_INLINE)
    # Fire
    noc.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)
    # CMD_CTRL must be 0 after completion
    assert noc.regs.read32(base + M.NIU_CMD_CTRL) == 0


@spec("NIU.CMDBUF.AVAIL")
def test_cmd_buf_avail_pre_populated(two_tile_network):
    """pre_populate sets CMD_BUF_AVAIL to 0x1F1F1F1F."""
    net = two_tile_network
    assert net['src_noc0'].regs.read32(M.NIU_CMD_BUF_AVAIL) == 0x1F1F1F1F


# ===========================================================================
# NOC_ID_LOGICAL and NODE_ID pre-population
# ===========================================================================

@spec("NIU.CFG.NOC_ID_LOGICAL")
def test_noc_id_logical_pre_populated(two_tile_network):
    """NOC_ID_LOGICAL == (y<<6)|x for source tile (1,2)."""
    net = two_tile_network
    x, y = net['src_xy']
    expected = (y << 6) | x
    assert net['src_noc0'].regs.read32(M.NIU_ID_LOGICAL) == expected
    assert net['src_noc1'].regs.read32(M.NIU_ID_LOGICAL) == expected


@spec("NIU.CFG.NODE_ID")
def test_node_id_pre_populated(two_tile_network):
    """NOC_NODE_ID in buf 0 == (y<<6)|x."""
    net = two_tile_network
    x, y = net['src_xy']
    expected = (y << 6) | x
    assert net['src_noc0'].regs.read32(M.NIU_NODE_ID) == expected


# ===========================================================================
# Coordinate encoding
# ===========================================================================

@spec("NIU.XY.UNICAST_ENCODING")
@pytest.mark.parametrize("x,y", [(0, 0), (1, 2), (7, 11), (63, 63)])
def test_unicast_xy_encoding(x, y):
    """_unicast_xy decodes x=[5:0], y=[11:6] from packed register."""
    raw = (y << 6) | x
    gx, gy = NOC._unicast_xy(raw)
    assert gx == x
    assert gy == y


@spec("NIU.XY.MCAST_ENCODING")
def test_mcast_rect_encoding():
    """_mcast_rect decodes (sx,sy,ex,ey) from multicast coordinate register."""
    sx, sy, ex, ey = 2, 3, 5, 7
    raw = (sy << 18) | (sx << 12) | (ey << 6) | ex
    got_sx, got_sy, got_ex, got_ey = NOC._mcast_rect(raw)
    assert got_sx == sx
    assert got_sy == sy
    assert got_ex == ex
    assert got_ey == ey


# ===========================================================================
# Read transaction
# ===========================================================================

def _fire_read(noc, buf, targ_x, targ_y, targ_addr, ret_addr, length):
    """Program and fire a DMA read via noc.regs directly."""
    base = buf * M.NIU_CMD_BUF_STRIDE
    noc.regs.write32(base + M.NIU_TARG_ADDR_LO, targ_addr)
    noc.regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_TARG_ADDR_HI, (targ_y << 6) | targ_x)
    noc.regs.write32(base + M.NIU_RET_ADDR_LO, ret_addr)
    noc.regs.write32(base + M.NIU_RET_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_AT_LEN_BE, length)
    noc.regs.write32(base + M.NIU_CTRL, 0)  # AT=0, WR=0
    noc.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)


@spec("NIU.TX.READ")
def test_unicast_read_transfers_bytes(two_tile_network):
    """DMA read copies bytes from remote tile L1 to local L1."""
    net = two_tile_network
    # Seed destination tile L1
    src_data = b'\xAA\xBB\xCC\xDD'
    for i, b in enumerate(src_data):
        net['dst_l1'].write8(0x8000 + i, b)
    # Fire read: dst → src
    _fire_read(net['src_noc0'], 1,
               net['dst_xy'][0], net['dst_xy'][1],
               0x8000, 0x9000, 4)
    result = bytes(net['src_l1'].read8(0x9000 + i) for i in range(4))
    assert result == src_data


@spec("NIU.COUNTER.RD_RESP", "NIU.COUNTER.RD_REQ")
def test_read_increments_counters(two_tile_network):
    """DMA read increments RD_RESP_RECEIVED and RD_REQ_SENT."""
    net = two_tile_network
    _fire_read(net['src_noc0'], 1,
               net['dst_xy'][0], net['dst_xy'][1],
               0x8000, 0x9000, 4)
    assert net['src_noc0'].regs.read32(M.NIU_MST_RD_RESP_RECEIVED) == 1
    assert net['src_noc0'].regs.read32(M.NIU_MST_RD_REQ_SENT) == 1


# ===========================================================================
# Write transaction
# ===========================================================================

def _fire_write(noc, buf, src_addr, dst_x, dst_y, dst_addr, length, resp=True):
    base = buf * M.NIU_CMD_BUF_STRIDE
    noc.regs.write32(base + M.NIU_TARG_ADDR_LO, src_addr)
    noc.regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_LO, dst_addr)
    noc.regs.write32(base + M.NIU_RET_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_HI, (dst_y << 6) | dst_x)
    noc.regs.write32(base + M.NIU_AT_LEN_BE, length)
    ctrl = M.NOC_CTRL_WR
    if resp:
        ctrl |= M.NOC_CTRL_RESP_MARKED
    noc.regs.write32(base + M.NIU_CTRL, ctrl)
    noc.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)


@spec("NIU.TX.WRITE")
def test_unicast_write_transfers_bytes(two_tile_network):
    """DMA write copies bytes from local L1 to remote tile L1."""
    net = two_tile_network
    src_data = b'\x11\x22\x33\x44'
    for i, b in enumerate(src_data):
        net['src_l1'].write8(0x5000 + i, b)
    _fire_write(net['src_noc0'], 0,
                0x5000, net['dst_xy'][0], net['dst_xy'][1], 0x6000, 4)
    result = bytes(net['dst_l1'].read8(0x6000 + i) for i in range(4))
    assert result == src_data


@spec("NIU.COUNTER.WR_ACK", "NIU.COUNTER.NONPOSTED_WR")
def test_nonposted_write_increments_ack_counter(two_tile_network):
    """Non-posted write (RESP_MARKED=1) increments WR_ACK_RECEIVED and NONPOSTED_WR_REQ_SENT."""
    net = two_tile_network
    net['src_l1'].write32(0x5000, 0x1234)
    _fire_write(net['src_noc0'], 0,
                0x5000, net['dst_xy'][0], net['dst_xy'][1], 0x6000, 4,
                resp=True)
    assert net['src_noc0'].regs.read32(M.NIU_MST_WR_ACK_RECEIVED) == 1
    assert net['src_noc0'].regs.read32(M.NIU_MST_NONPOSTED_WR_REQ_SENT) == 1


@spec("NIU.COUNTER.POSTED_WR")
def test_posted_write_increments_posted_counter(two_tile_network):
    """Posted write (RESP_MARKED=0) increments POSTED_WR_REQ_SENT, not WR_ACK."""
    net = two_tile_network
    net['src_l1'].write32(0x5000, 0xABCD)
    _fire_write(net['src_noc0'], 0,
                0x5000, net['dst_xy'][0], net['dst_xy'][1], 0x6000, 4,
                resp=False)
    assert net['src_noc0'].regs.read32(M.NIU_MST_POSTED_WR_REQ_SENT) == 1
    assert net['src_noc0'].regs.read32(M.NIU_MST_WR_ACK_RECEIVED) == 0


# ===========================================================================
# Inline write transaction
# ===========================================================================

def _fire_inline_write(noc, buf, targ_x, targ_y, targ_addr, data_word, resp=False):
    base = buf * M.NIU_CMD_BUF_STRIDE
    noc.regs.write32(base + M.NIU_TARG_ADDR_LO, targ_addr)
    noc.regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_TARG_ADDR_HI, (targ_y << 6) | targ_x)
    noc.regs.write32(base + M.NIU_AT_DATA, data_word)
    ctrl = M.NOC_CTRL_WR | M.NOC_CTRL_WR_INLINE
    if resp:
        ctrl |= M.NOC_CTRL_RESP_MARKED
    noc.regs.write32(base + M.NIU_CTRL, ctrl)
    noc.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)


@spec("NIU.TX.INLINE_WRITE")
def test_inline_write_sends_4_bytes(two_tile_network):
    """Inline write sends 4 bytes of NOC_AT_DATA to target address."""
    net = two_tile_network
    _fire_inline_write(net['src_noc0'], 2,
                       net['dst_xy'][0], net['dst_xy'][1],
                       0x7000, 0xDEADBEEF)
    assert net['dst_l1'].read32(0x7000) == 0xDEADBEEF


@spec("NIU.TX.INLINE_WRITE")
def test_inline_write_counter_posted(two_tile_network):
    """Inline write without RESP_MARKED increments POSTED_WR_REQ_SENT."""
    net = two_tile_network
    _fire_inline_write(net['src_noc0'], 2,
                       net['dst_xy'][0], net['dst_xy'][1],
                       0x7000, 0x1, resp=False)
    assert net['src_noc0'].regs.read32(M.NIU_MST_POSTED_WR_REQ_SENT) == 1


# ===========================================================================
# Multicast write
# ===========================================================================

@spec("NIU.MCAST.RECT_DELIVERY")
def test_mcast_write_reaches_all_tiles_in_rect(three_tile_network):
    """Multicast write delivers to all tiles in [sx..ex, sy..ey]."""
    net = three_tile_network
    # Both dst (3,4) and dst2 (4,4) should receive.
    # Rect: sx=3, sy=4, ex=4, ey=4 (contiguous x values only).
    # Data in src_l1
    net['src_l1'].write32(0x5000, 0xCAFEBABE)
    sx, sy, ex, ey = 3, 4, 4, 4
    xy = (sy << 18) | (sx << 12) | (ey << 6) | ex
    base = 0 * M.NIU_CMD_BUF_STRIDE
    noc = net['src_noc0']
    noc.regs.write32(base + M.NIU_TARG_ADDR_LO, 0x5000)
    noc.regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_LO, 0x6000)
    noc.regs.write32(base + M.NIU_RET_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_HI, xy)
    noc.regs.write32(base + M.NIU_AT_LEN_BE, 4)
    noc.regs.write32(base + M.NIU_CTRL,
                     M.NOC_CTRL_WR | M.NOC_CTRL_BRCST | M.NOC_CTRL_RESP_MARKED)
    noc.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)
    assert net['dst_l1'].read32(0x6000) == 0xCAFEBABE
    assert net['dst2_l1'].read32(0x6000) == 0xCAFEBABE


@spec("NIU.MCAST.SRC_INCLUDE")
def test_mcast_src_exclude_default(two_tile_network):
    """Multicast with BRCST_SRC_INCLUDE=0 excludes the sender from delivery."""
    net = two_tile_network
    # Use a rect that exactly covers src (1,2) and dst (3,4).
    # The emulator's _write_targets iterates the full rect; tiles not in network are silently skipped.
    # We test only that the SENDER does NOT receive.
    net['src_l1'].write32(0x5000, 0xABCD)
    net['src_l1'].write32(0xA000, 0xDEAD)  # sentinel

    # Rect covering exactly src (1,2): sx=1, sy=2, ex=1, ey=2
    sx, sy, ex, ey = 1, 2, 1, 2
    xy = (sy << 18) | (sx << 12) | (ey << 6) | ex
    base = 0 * M.NIU_CMD_BUF_STRIDE
    noc = net['src_noc0']
    noc.regs.write32(base + M.NIU_TARG_ADDR_LO, 0x5000)
    noc.regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_LO, 0xA000)
    noc.regs.write32(base + M.NIU_RET_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_HI, xy)
    noc.regs.write32(base + M.NIU_AT_LEN_BE, 4)
    # BRCST_SRC_INCLUDE=0 (default): sender excluded
    noc.regs.write32(base + M.NIU_CTRL,
                     M.NOC_CTRL_WR | M.NOC_CTRL_BRCST | M.NOC_CTRL_RESP_MARKED)
    noc.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)
    # Sender's L1 at 0xA000 must be unchanged (sentinel preserved)
    assert net['src_l1'].read32(0xA000) == 0xDEAD


@spec("NIU.MCAST.SRC_INCLUDE")
def test_mcast_src_include_loopback():
    """Multicast with BRCST_SRC_INCLUDE=1 also writes to the sender's L1."""
    # Use a local 2-tile compact network: src (1,2) and peer (1,3).
    # Rect sx=1,sy=2,ex=1,ey=3 covers exactly these two tiles with no gaps.
    net = {}
    src_l1, src_noc0, src_noc1 = _make_network_tile(1, 2, net)
    peer_l1, peer_noc0, peer_noc1 = _make_network_tile(1, 3, net)

    src_l1.write32(0x5000, 0x1111)
    sx, sy, ex, ey = 1, 2, 1, 3  # rect: x=1, y=2..3 (exactly sender + peer)
    xy = (sy << 18) | (sx << 12) | (ey << 6) | ex
    base = 0 * M.NIU_CMD_BUF_STRIDE
    noc = src_noc0
    noc.regs.write32(base + M.NIU_TARG_ADDR_LO, 0x5000)
    noc.regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_LO, 0xB000)
    noc.regs.write32(base + M.NIU_RET_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_HI, xy)
    noc.regs.write32(base + M.NIU_AT_LEN_BE, 4)
    noc.regs.write32(base + M.NIU_CTRL,
                     M.NOC_CTRL_WR | M.NOC_CTRL_BRCST | M.NOC_CTRL_RESP_MARKED
                     | M.NOC_CTRL_BRCST_SRC_INCLUDE)
    noc.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)
    # Sender's own L1 at 0xB000 should receive the write
    assert src_l1.read32(0xB000) == 0x1111
    # Peer also receives
    assert peer_l1.read32(0xB000) == 0x1111


@spec("NIU.MCAST.WR_ACK_PER_DEST")
def test_mcast_wr_ack_increments_per_destination(three_tile_network):
    """For a non-posted multicast, NIU_MST_WR_ACK_RECEIVED must bump by one
    per destination tile that ACKs (here: 2 tiles in the rect), while
    NIU_MST_NONPOSTED_WR_REQ_SENT bumps by 1 (one command issued).

    CURRENTLY FAILS — the emulator's _inc_write_counters bumps WR_ACK by
    a flat 1 regardless of multicast fan-out. This test documents the
    per-destination spec and will pass once counter accounting is fixed."""
    net = three_tile_network
    net['src_l1'].write32(0x5000, 0xCAFEBABE)
    # Rect covers dst (3,4) and dst2 (4,4) — two destination tiles.
    sx, sy, ex, ey = 3, 4, 4, 4
    xy = (sy << 18) | (sx << 12) | (ey << 6) | ex
    base = 0 * M.NIU_CMD_BUF_STRIDE
    noc = net['src_noc0']
    noc.regs.write32(base + M.NIU_TARG_ADDR_LO, 0x5000)
    noc.regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_LO, 0x6000)
    noc.regs.write32(base + M.NIU_RET_ADDR_MID, 0)
    noc.regs.write32(base + M.NIU_RET_ADDR_HI, xy)
    noc.regs.write32(base + M.NIU_AT_LEN_BE, 4)
    noc.regs.write32(base + M.NIU_CTRL,
                     M.NOC_CTRL_WR | M.NOC_CTRL_BRCST | M.NOC_CTRL_RESP_MARKED)
    noc.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)
    # Spec: one command sent → NONPOSTED_WR_REQ_SENT = 1; two destinations
    # ACKed → WR_ACK_RECEIVED = 2.
    assert noc.regs.read32(M.NIU_MST_NONPOSTED_WR_REQ_SENT) == 1
    assert noc.regs.read32(M.NIU_MST_WR_ACK_RECEIVED) == 2


@spec("NIU.MCAST.BRCST_XY_ROUTING_AXIS")
def test_mcast_brcst_xy_bit_does_not_change_delivery(three_tile_network):
    """Bit 16 (BRCST_XY) of NOC_CTRL selects X-first vs Y-first routing.
    It only affects packet-routing topology and congestion — not which
    tiles receive the write. Firing the same multicast twice, once with
    the bit clear and once set, must deliver identical data to the same
    set of tiles."""
    def _fire_mcast(net, brcst_xy_bit):
        sx, sy, ex, ey = 3, 4, 4, 4
        xy = (sy << 18) | (sx << 12) | (ey << 6) | ex
        base = 0 * M.NIU_CMD_BUF_STRIDE
        noc = net['src_noc0']
        # Wipe destinations to a known sentinel
        net['dst_l1'].write32(0x6000, 0xAAAAAAAA)
        net['dst2_l1'].write32(0x6000, 0xAAAAAAAA)
        net['src_l1'].write32(0x5000, 0xCAFEBABE)
        noc.regs.write32(base + M.NIU_TARG_ADDR_LO, 0x5000)
        noc.regs.write32(base + M.NIU_TARG_ADDR_MID, 0)
        noc.regs.write32(base + M.NIU_RET_ADDR_LO, 0x6000)
        noc.regs.write32(base + M.NIU_RET_ADDR_MID, 0)
        noc.regs.write32(base + M.NIU_RET_ADDR_HI, xy)
        noc.regs.write32(base + M.NIU_AT_LEN_BE, 4)
        ctrl = M.NOC_CTRL_WR | M.NOC_CTRL_BRCST | M.NOC_CTRL_RESP_MARKED
        if brcst_xy_bit:
            ctrl |= (1 << 16)   # BRCST_XY: Y-first routing
        noc.regs.write32(base + M.NIU_CTRL, ctrl)
        noc.write32(M.NOC0_BASE + base + M.NIU_CMD_CTRL, 1)
        return net['dst_l1'].read32(0x6000), net['dst2_l1'].read32(0x6000)

    # X-first (bit clear)
    net_a = three_tile_network
    a1, a2 = _fire_mcast(net_a, brcst_xy_bit=False)

    # Fresh network for Y-first (bit set)
    net_b = {}
    src_l1, src_noc0, src_noc1 = _make_network_tile(1, 2, net_b)
    dst_l1, dst_noc0, dst_noc1 = _make_network_tile(3, 4, net_b)
    dst2_l1, dst2_noc0, dst2_noc1 = _make_network_tile(4, 4, net_b)
    net_b_wrapped = dict(
        network=net_b,
        src_l1=src_l1, src_noc0=src_noc0,
        src_xy=(1, 2),
        dst_l1=dst_l1, dst_xy=(3, 4),
        dst2_l1=dst2_l1, dst2_xy=(4, 4),
    )
    b1, b2 = _fire_mcast(net_b_wrapped, brcst_xy_bit=True)

    # Delivery must be identical regardless of routing axis.
    assert a1 == b1 == 0xCAFEBABE
    assert a2 == b2 == 0xCAFEBABE
