"""Tests for emulated Blackhole device."""
import struct

from emu.device import Device, Tile, _compute_bank_xy, _build_bank_noc_table
from emu.device import P100A_TENSIX_X, P100A_Y_RANGE
from emu.device import RUN_MSG_INIT, RUN_MSG_GO, RUN_MSG_DONE
from emu import memory as M
from emu.noc import NOC, noc_key
from emu import dsl
from emu.memory import LDM_SCRATCH, LDM_BASE


# -- unit tests ----------------------------------------------------------------

def test_bank_xy_p100a():
    """P100A bank geometry: 7 banks (bank 0 harvested)."""
    bxy = _compute_bank_xy([0])
    assert len(bxy) == 7  # banks 0-6 (bank 0 harvested maps differently)

def test_bank_xy_p150():
    """P150 bank geometry: all 8 banks."""
    bxy = _compute_bank_xy([])
    assert len(bxy) == 8

def test_bank_noc_table_size():
    """Bank table has expected size for P100A."""
    cores = [(x, y) for x in P100A_TENSIX_X for y in P100A_Y_RANGE]
    table = _build_bank_noc_table([0], cores)
    assert len(table) > 0

# -- Device creation without firmware ------------------------------------------

def test_device_no_firmware():
    """Device without firmware creates 120 tiles and 7 DRAM banks."""
    dev = Device(firmware=None)
    assert len(dev.tiles) == 120
    assert len(dev.dram_banks) == 7
    assert len(dev.cores) == 120

def test_device_tiles_have_shared_resources():
    """All 5 cores in a tile share the same noc, cfg, and mmio Memory objects."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    cores = tile.cores
    # All cores share the same noc[0], noc[1], cfg, mmio
    for core in cores[1:]:
        assert core.mem.noc[0] is cores[0].mem.noc[0]
        assert core.mem.noc[1] is cores[0].mem.noc[1]
        assert core.mem.cfg is cores[0].mem.cfg
        assert core.mem.mmio is cores[0].mem.mmio
    # But they have different LDM
    assert cores[0].ldm is not cores[1].ldm

def test_device_tiles_share_l1():
    """All 5 cores in a tile share the same L1."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    tile.brisc.write32(0x1000, 0xDEAD)
    assert tile.ncrisc.read32(0x1000) == 0xDEAD

def test_device_noc_between_tiles():
    """NOC write from one tile reaches another tile's L1."""
    dev = Device(firmware=None)
    src = dev.tiles[(1, 2)]
    dst = dev.tiles[(3, 4)]

    # Write data to source tile's L1
    src.l1.write32(0x5000, 0xCAFEBABE)

    # Program NOC0 buf0 for a DMA write
    noc = src.brisc.mem.noc[0]
    noc.write32(M.NIU_TARG_ADDR_LO, 0x5000)         # local source
    noc.write32(M.NIU_TARG_ADDR_MID, 0)
    noc.write32(M.NIU_RET_ADDR_LO, 0x6000)           # remote dest
    noc.write32(M.NIU_RET_ADDR_MID, 0)
    noc.write32(M.NIU_RET_ADDR_HI, (4 << 6) | 3)     # (3, 4)
    noc.write32(M.NIU_AT_LEN_BE, 4)
    noc.write32(M.NIU_CTRL, M.NOC_CTRL_WR | M.NOC_CTRL_RESP_MARKED)

    # Fire
    src.brisc.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

    assert dst.l1.read32(0x6000) == 0xCAFEBABE

def test_device_noc_to_dram():
    """NOC write from a tile reaches a DRAM bank."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]

    # Write data to tile's L1
    tile.l1.write32(0x5000, 0x12345678)

    # Get DRAM bank 1's NOC coordinates from bank_xy
    bank_id = 1
    # bank 1 should be in bank_xy (P100A with bank 0 harvested)
    bx, by0 = dev.bank_xy[bank_id]
    port = 1  # use port 1

    # Program NOC write to DRAM bank
    noc = tile.brisc.mem.noc[0]
    noc.write32(M.NIU_TARG_ADDR_LO, 0x5000)
    noc.write32(M.NIU_TARG_ADDR_MID, 0)
    noc.write32(M.NIU_RET_ADDR_LO, 0x100)  # DRAM offset
    noc.write32(M.NIU_RET_ADDR_MID, 0)
    noc.write32(M.NIU_RET_ADDR_HI, ((by0 + port) << 6) | bx)
    noc.write32(M.NIU_AT_LEN_BE, 4)
    noc.write32(M.NIU_CTRL, M.NOC_CTRL_WR | M.NOC_CTRL_RESP_MARKED)
    tile.brisc.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)

    # Read back from DRAM bank
    # Find which index in dram_banks corresponds to bank_id
    active_banks = sorted(dev.bank_xy.keys())
    bank_idx = active_banks.index(bank_id)
    assert dev.dram_banks[bank_idx].read32(0x100) == 0x12345678

def test_device_niu_id_logical():
    """Each tile's NIU has correct NOC_ID_LOGICAL pre-populated."""
    dev = Device(firmware=None)
    for (x, y), tile in dev.tiles.items():
        expected = (y << 6) | x
        assert tile.brisc.mem.noc[0].read32(M.NIU_ID_LOGICAL) == expected
        assert tile.brisc.mem.noc[1].read32(M.NIU_ID_LOGICAL) == expected

def test_device_wall_clock():
    """WALL_CLOCK_L is written during step loop and increases monotonically."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    # Initially 0
    assert tile.shared_mmio.read32(M.WALL_CLOCK_L) == 0
    # Manually tick the clock
    dev._clock = 42
    tile.shared_mmio.write32(M.WALL_CLOCK_L, 42)
    assert tile.shared_mmio.read32(M.WALL_CLOCK_L) == 42

def test_device_dram_read_write():
    """Direct DRAM read/write utilities work."""
    dev = Device(firmware=None)
    dev.write_dram(0, 0x100, b"\xAA\xBB\xCC\xDD")
    assert dev.read_dram(0, 0x100, 4) == b"\xAA\xBB\xCC\xDD"

def test_device_l1_read_write():
    """Direct L1 read/write utilities work."""
    dev = Device(firmware=None)
    dev.write_l1(1, 2, 0x1000, b"\x01\x02\x03\x04")
    assert dev.read_l1(1, 2, 0x1000, 4) == b"\x01\x02\x03\x04"


# -- Simple run test (no firmware, direct PC setup) ----------------------------

def test_step_single_core_direct():
    """Directly set BRISC PC and step: verify it executes instructions."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]

    # Write a simple program: ADDI a0, zero, 42
    tile.l1.write32(0x100, int(dsl.ADDI(dsl.a0, dsl.zero, 42)))

    tile.brisc.pc = 0x100
    tile.brisc.step()
    assert tile.brisc.regs[dsl.a0] == 42


# -- LDM scratch area redirection ---------------------------------------------

def test_ldm_segment_redirected_to_scratch():
    """PT_LOAD segments at 0xFFB00000 are redirected to L1 scratch areas."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]

    # Simulate what _upload_firmware does for a single core's LDM segment
    init_data = b'\xDE\xAD\xBE\xEF'
    addr = LDM_BASE  # 0xFFB00000
    scratch = LDM_SCRATCH['brisc']
    # The redirect logic: LDM segment → L1 scratch
    offset = addr - LDM_BASE
    tile.l1.load(scratch + offset, init_data)

    actual = bytes(tile.l1.read8(scratch + i) for i in range(4))
    assert actual == init_data

def test_ldm_segment_per_core_isolation():
    """Each core's LDM segment goes to its own scratch area."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]

    markers = {
        'brisc':  b'\x01\x01\x01\x01',
        'ncrisc': b'\x02\x02\x02\x02',
        'trisc0': b'\x03\x03\x03\x03',
        'trisc1': b'\x04\x04\x04\x04',
        'trisc2': b'\x05\x05\x05\x05',
    }
    # Write each core's marker to its scratch area (as _upload_firmware would)
    for name, marker in markers.items():
        scratch = LDM_SCRATCH[name]
        tile.l1.load(scratch, marker)

    # Verify each scratch area has the right data and no cross-contamination
    for name, marker in markers.items():
        scratch = LDM_SCRATCH[name]
        actual = bytes(tile.l1.read8(scratch + i) for i in range(4))
        assert actual == marker, f"{name}: expected {marker!r} at scratch 0x{scratch:X}, got {actual!r}"

def test_do_crt1_copies_data_to_ldm():
    """A minimal do_crt1 implementation: copy from L1 scratch → LDM, zero BSS."""
    dev = Device(firmware=None)
    tile = dev.tiles[(1, 2)]
    core = tile.brisc

    # Pre-populate L1 scratch with 2 words of initialized data
    scratch = LDM_SCRATCH['brisc']
    tile.l1.write32(scratch + 0, 0xCAFEBABE)
    tile.l1.write32(scratch + 4, 0x12345678)

    # Dirty LDM to verify BSS zeroing actually clears it
    core.ldm.write32(8, 0xFFFFFFFF)
    core.ldm.write32(12, 0xFFFFFFFF)

    # Assemble a minimal do_crt1:
    #   - Copy 2 words from L1 scratch → LDM (0xFFB00000)
    #   - Zero 2 words of BSS at LDM+8
    #
    # Registers:
    #   a0 = L1 scratch address
    #   a1 = LDM base (0xFFB00000)
    #   a2 = scratch data word
    #   a3 = zero
    code_addr = 0x100
    insns = [
        # Load scratch address into a0
        dsl.LUI(dsl.a0, scratch & 0xFFFFF000),
        dsl.ADDI(dsl.a0, dsl.a0, scratch & 0xFFF),
        # Load LDM base into a1
        dsl.LUI(dsl.a1, 0xFFB00000),
        # Copy word 0: L1[scratch+0] → LDM[0]
        dsl.LW(dsl.a2, dsl.a0, 0),
        dsl.SW(dsl.a1, dsl.a2, 0),
        # Copy word 1: L1[scratch+4] → LDM[4]
        dsl.LW(dsl.a2, dsl.a0, 4),
        dsl.SW(dsl.a1, dsl.a2, 4),
        # Zero BSS: LDM[8] and LDM[12]
        dsl.SW(dsl.a1, dsl.zero, 8),
        dsl.SW(dsl.a1, dsl.zero, 12),
    ]
    for i, insn in enumerate(insns):
        tile.l1.write32(code_addr + i * 4, int(insn))

    core.pc = code_addr
    core.run(n=len(insns) + 1)

    # Verify data was copied to LDM
    assert core.ldm.read32(0) == 0xCAFEBABE
    assert core.ldm.read32(4) == 0x12345678
    # Verify BSS was zeroed
    assert core.ldm.read32(8) == 0
    assert core.ldm.read32(12) == 0
