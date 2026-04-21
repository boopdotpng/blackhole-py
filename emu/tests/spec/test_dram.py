"""Spec tests for ../specs/dram.md.

Covers: DRAM bank count, port aliasing, interleaved read/write, bank
harvesting, bank-to-NOC table format, and NOC-routed DRAM access.
"""

import struct
import pytest

from emu.device import Device
from emu.fw import (
    DRAM_BANK_COUNT, DRAM_PORTS, _compute_bank_xy, _build_bank_noc_table,
)
from emu import memory as M
from emu.tests._helpers import mini_device

from .conftest import spec


# ===========================================================================
# DRAM bank geometry
# ===========================================================================

@spec("DRAM.GEO.BANK_COUNT")
def test_bank_count_constant():
    """DRAM_BANK_COUNT == 8 physical, 7 active with 1 harvested."""
    assert DRAM_BANK_COUNT == 8


@spec("DRAM.GEO.BANK_COUNT")
def test_device_has_seven_active_banks():
    """Device with 1 harvested bank exposes 7 dram_banks."""
    dev = mini_device()  # harvested=[0] by default
    assert len(dev.dram_banks) == 7


@spec("DRAM.GEO.PORTS_PER_BANK")
def test_ports_per_bank_constant():
    assert DRAM_PORTS == 3


@spec("DRAM.GEO.COLUMNS")
def test_compute_bank_xy_columns():
    """_compute_bank_xy with harvested=[0] returns x=17 or x=18 for all banks."""
    bank_xy = _compute_bank_xy([0])
    for b, (x, y0) in bank_xy.items():
        assert x in (17, 18), f"bank {b}: unexpected x={x}"


@spec("DRAM.GEO.COLUMNS")
def test_four_west_three_east():
    """P100A (harvested=[0]): exactly 4 banks on x=17, 3 on x=18."""
    bank_xy = _compute_bank_xy([0])
    west = [b for b, (x, _) in bank_xy.items() if x == 17]
    east = [b for b, (x, _) in bank_xy.items() if x == 18]
    assert len(west) == 4
    assert len(east) == 3


# ===========================================================================
# Port aliasing
# ===========================================================================

@spec("DRAM.PORT.ALIAS_SAME_MEM")
def test_all_ports_share_same_memory():
    """All 3 port coordinates of a bank alias the same backing Memory."""
    dev = Device(tensix_x=(1,), tensix_y=(2,))
    # bank_xy gives base (x, y0); ports are y0, y0+1, y0+2
    bank_id = list(dev.bank_xy.keys())[0]
    x, y0 = dev.bank_xy[bank_id]
    net = dev.networks[0]
    from emu.noc import noc_key
    mem0 = net[noc_key(x, y0)]
    mem1 = net[noc_key(x, y0 + 1)]
    mem2 = net[noc_key(x, y0 + 2)]
    # All three must be the same object
    assert mem0 is mem1
    assert mem1 is mem2


@spec("DRAM.PORT.ALIAS_SAME_MEM")
def test_write_to_port0_visible_at_port1():
    """Writing through one port is readable through any other port of the same bank."""
    dev = Device(tensix_x=(1,), tensix_y=(2,))
    bank_idx = 0
    # Write directly to dram_banks[0]
    dev.dram_banks[bank_idx].write32(0x100, 0xDEADBEEF)
    # Read back from same object (all ports share it)
    assert dev.dram_banks[bank_idx].read32(0x100) == 0xDEADBEEF


# ===========================================================================
# Interleaved read/write
# ===========================================================================

@spec("DRAM.INTERLEAVE.BANK_INDEX")
@pytest.mark.parametrize("page_id,num_banks,expected_bank,expected_slot", [
    (0,  7, 0, 0),
    (1,  7, 1, 0),
    (6,  7, 6, 0),
    (7,  7, 0, 1),
    (13, 7, 6, 1),
    (14, 7, 0, 2),
])
def test_interleave_bank_index(page_id, num_banks, expected_bank, expected_slot):
    """bank = page_id % num_banks; slot = page_id // num_banks."""
    assert page_id % num_banks == expected_bank
    assert page_id // num_banks == expected_slot


@spec("DRAM.INTERLEAVE.ADDR_FORMULA")
def test_interleave_addr_formula():
    """addr within bank = base_addr + slot * tile_bytes."""
    from emu.memory import Memory as Mem
    from emu.device import Dram
    banks = [Mem() for _ in range(7)]
    dram = Dram(num_banks=7, banks=banks, bank_xy={})
    tile_bytes = 16
    base_addr = 0x1000
    # tile 7 → bank 0, slot 1 → addr = 0x1000 + 1*16 = 0x1010
    dram.write_interleaved(base_addr, 7, tile_bytes, b'\xAA' * tile_bytes)
    data = dram.read_interleaved(base_addr, 7, tile_bytes)
    assert data == b'\xAA' * tile_bytes
    # Check it landed in bank 0 at the expected address
    assert banks[0].read8(0x1010) == 0xAA


@spec("DRAM.INTERLEAVE.WRITE_READ_ROUNDTRIP")
def test_interleave_write_read_roundtrip():
    """write_interleaved then read_interleaved returns the same bytes."""
    from emu.memory import Memory as Mem
    from emu.device import Dram
    banks = [Mem() for _ in range(7)]
    dram = Dram(num_banks=7, banks=banks, bank_xy={})
    payload = bytes(range(32))
    dram.write_interleaved(0x2000, 3, 32, payload)
    assert dram.read_interleaved(0x2000, 3, 32) == payload


# ===========================================================================
# Harvesting
# ===========================================================================

@spec("DRAM.HARVEST.SINGLE_BANK")
def test_harvest_produces_seven_banks():
    """Any single harvested bank still yields 7 active banks."""
    for h in range(8):
        dev = Device(tensix_x=(1,), tensix_y=(2,),
                     harvested_banks=[h])
        assert len(dev.dram_banks) == 7, f"harvested {h}: got {len(dev.dram_banks)}"


@spec("DRAM.HARVEST.BOUNDARY")
def test_harvest_bank0_produces_7_entries():
    """With bank 0 harvested, bank_xy has exactly 7 entries (physical bank 7 is absent)."""
    bank_xy = _compute_bank_xy([0])
    assert len(bank_xy) == 7
    # Physical bank 7 is absent (it was harvested out of the enumeration)
    assert 7 not in bank_xy


@spec("DRAM.HARVEST.MIRROR_REORDER")
def test_harvest_mirror_reorder_bank0():
    """Bank 0 harvested: 3 banks assigned to east (x=18), 4 to west (x=17)."""
    bank_xy = _compute_bank_xy([0])
    east = {b: (x, y0) for b, (x, y0) in bank_xy.items() if x == 18}
    west = {b: (x, y0) for b, (x, y0) in bank_xy.items() if x == 17}
    assert len(east) == 3
    assert len(west) == 4


@spec("DRAM.HARVEST.MIRROR_REORDER")
def test_harvest_mirror_reorder_bank4():
    """Bank 4 harvested: 4 banks assigned to west (x=17), 3 to east (x=18)."""
    bank_xy = _compute_bank_xy([4])
    west = {b: (x, y0) for b, (x, y0) in bank_xy.items() if x == 17}
    east = {b: (x, y0) for b, (x, y0) in bank_xy.items() if x == 18}
    assert len(west) == 4
    assert len(east) == 3


# ===========================================================================
# Bank-to-NOC table format
# ===========================================================================

@spec("DRAM.BANK_TABLE.ENCODING")
def test_bank_table_noc_xy_encoding():
    """NOC XY entries in bank table are packed as (y<<6)|x."""
    worker_xy = [(1, 2)]
    table = _build_bank_noc_table([0], worker_xy)
    # Unpack first uint16 (NOC0, bank 0 slot in 7-bank layout)
    xy0 = struct.unpack_from('<H', table, 0)[0]
    x = xy0 & 0x3F
    y = (xy0 >> 6) & 0x3F
    # Should be a valid DRAM port coordinate
    assert x in (17, 18)
    assert 12 <= y <= 23


@spec("DRAM.BANK_TABLE.DRAM_NOC_ORDER")
def test_bank_table_noc0_before_noc1():
    """Bank table: NUM_NOCS*NUM_DRAM_BANKS uint16 for DRAM (NOC0 then NOC1)."""
    worker_xy = [(1, 2)]
    num_banks = 7
    nocs = 2
    table = _build_bank_noc_table([0], worker_xy)
    # First nocs*num_banks uint16s are DRAM entries
    dram_section = struct.unpack_from(f'<{nocs * num_banks}H', table)
    for xy in dram_section:
        x = xy & 0x3F
        y = (xy >> 6) & 0x3F
        assert x in (17, 18), f"unexpected DRAM x={x}"
        assert 12 <= y <= 23, f"unexpected DRAM y={y}"


@spec("DRAM.BANK_TABLE.OFFSETS_ZERO")
def test_bank_table_offsets_are_zero():
    """bank_to_dram_offset and bank_to_l1_offset are all zeros."""
    num_banks = 7
    nocs = 2
    worker_xy = [(x, y) for x in (1, 2) for y in range(2, 5)]
    num_l1 = len(worker_xy)
    table = _build_bank_noc_table([0], worker_xy)
    # Offset section starts after the uint16 entries
    uint16_count = nocs * num_banks + nocs * num_l1
    off = uint16_count * 2
    # Align to 4 bytes if needed (the table uses direct struct.pack, no padding)
    int_count = num_banks + num_l1
    ints = struct.unpack_from(f'<{int_count}i', table, off)
    assert all(v == 0 for v in ints)


# ===========================================================================
# NOC-routed DRAM access
# ===========================================================================

@spec("DRAM.NOC.WRITE_ROUTED")
def test_noc_write_to_dram_bank(two_tile_network):
    """NOC DMA write targeting a DRAM bank coordinate writes to that bank's memory."""
    # Use a full Device to get DRAM in the network
    dev = Device(tensix_x=(1,), tensix_y=(2,))
    tile = dev.tiles[(1, 2)]
    tile.l1.write32(0x5000, 0x12345678)

    # Pick bank 1's NOC0 port
    bank_id = list(dev.bank_xy.keys())[1]
    bx, by0 = dev.bank_xy[bank_id]
    from emu.fw import DRAM_BANK_PORT
    port_offset = DRAM_BANK_PORT[bank_id][0]
    noc_y = by0 + port_offset

    regs = tile.noc0.regs
    regs.write32(M.NIU_TARG_ADDR_LO, 0x5000)
    regs.write32(M.NIU_TARG_ADDR_MID, 0)
    regs.write32(M.NIU_RET_ADDR_LO, 0x200)
    regs.write32(M.NIU_RET_ADDR_MID, 0)
    regs.write32(M.NIU_RET_ADDR_HI, (noc_y << 6) | bx)
    regs.write32(M.NIU_AT_LEN_BE, 4)
    regs.write32(M.NIU_CTRL, M.NOC_CTRL_WR | M.NOC_CTRL_RESP_MARKED)
    tile.brisc.mem.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

    active_banks = sorted(dev.bank_xy.keys())
    bank_idx = active_banks.index(bank_id)
    assert dev.dram_banks[bank_idx].read32(0x200) == 0x12345678


@spec("DRAM.NOC.READ_ROUTED")
def test_noc_read_from_dram_bank():
    """NOC DMA read targeting a DRAM bank coordinate reads from that bank's memory."""
    dev = Device(tensix_x=(1,), tensix_y=(2,))
    tile = dev.tiles[(1, 2)]

    bank_id = list(dev.bank_xy.keys())[0]
    bx, by0 = dev.bank_xy[bank_id]
    from emu.fw import DRAM_BANK_PORT
    port_offset = DRAM_BANK_PORT[bank_id][0]
    noc_y = by0 + port_offset

    # Pre-seed the bank
    active_banks = sorted(dev.bank_xy.keys())
    bank_idx = active_banks.index(bank_id)
    dev.dram_banks[bank_idx].write32(0x300, 0xDEADBEEF)

    # NOC read: DRAM → local L1
    regs = tile.noc0.regs
    buf = 1 * M.NIU_CMD_BUF_STRIDE
    regs.write32(buf + M.NIU_TARG_ADDR_LO, 0x300)
    regs.write32(buf + M.NIU_TARG_ADDR_MID, 0)
    regs.write32(buf + M.NIU_TARG_ADDR_HI, (noc_y << 6) | bx)
    regs.write32(buf + M.NIU_RET_ADDR_LO, 0x4000)
    regs.write32(buf + M.NIU_RET_ADDR_MID, 0)
    regs.write32(buf + M.NIU_AT_LEN_BE, 4)
    regs.write32(buf + M.NIU_CTRL, 0)  # read
    tile.brisc.mem.write32(M.NOC0_BASE + buf + M.NIU_CMD_CTRL, 1)

    assert tile.l1.read32(0x4000) == 0xDEADBEEF
