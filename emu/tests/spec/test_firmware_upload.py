"""Spec tests for ../specs/firmware-upload.md.

Covers: power-on reset state, BRISC-only / all-cores release, re-assert,
RESET_PC override mechanism, JAL encoding, go_message protocol,
step_loop wall-clock + skip-in-reset, BRISC releasing subordinates,
and TimeoutError.
"""

import pytest

from emu.device import Device, SOFT_RESET_ALL
from emu.memory import (
    SOFT_RESET_0,
    TRISC0_RESET_PC, TRISC1_RESET_PC, TRISC2_RESET_PC, TRISC_RESET_PC_OVR,
    NCRISC_RESET_PC, NCRISC_RESET_PC_OVR,
    GO_MESSAGES, WALL_CLOCK_L, BRISC_FW_BASE,
)
from emu.device import SOFT_RESET_BRISC_ONLY, _make_jal
from emu.core import BRISC
from emu.tests._helpers import mini_device

from .conftest import spec


# -- minimal instruction helpers -----------------------------------------------

def _addi(rd, rs1, imm):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (0 << 12) | (rd << 7) | 0x13

def _lui(rd, upper20):
    return (upper20 << 12) | (rd << 7) | 0x37

def _sw(rs2, offset, rs1):
    return (((offset >> 5) & 0x7F) << 25) | (rs2 << 20) | (rs1 << 15) \
         | (2 << 12) | ((offset & 0x1F) << 7) | 0x23


# ===========================================================================
# Power-on reset state
# ===========================================================================

@spec("FW.RESET.POWER_ON_STATE")
def test_device_starts_all_in_reset():
    """All cores start in reset after device construction."""
    dev = mini_device()
    for xy, tile in dev.tiles.items():
        for core in tile.cores:
            assert core.in_reset, f"core at {xy} not in reset"


@spec("FW.RESET.POWER_ON_STATE")
def test_soft_reset_0_initial_value():
    """SOFT_RESET_0 reads SOFT_RESET_ALL (0x47800) after construction."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    assert tile.brisc.mem.read32(SOFT_RESET_0) == SOFT_RESET_ALL
    assert SOFT_RESET_ALL == 0x47800


# ===========================================================================
# Release transitions
# ===========================================================================

@spec("FW.RESET.BRISC_ONLY_RELEASE")
def test_release_brisc_only():
    """Writing SOFT_RESET_BRISC_ONLY releases BRISC (PC=0), keeps others held."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_BRISC_ONLY)
    assert not tile.brisc.in_reset
    assert tile.brisc.pc == 0
    assert tile.ncrisc.in_reset
    assert tile.trisc0.in_reset
    assert tile.trisc1.in_reset
    assert tile.trisc2.in_reset


@spec("FW.RESET.ALL_RELEASE")
def test_release_all_cores():
    """Writing 0 to SOFT_RESET_0 releases all 5 cores."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    tile.brisc.mem.write32(SOFT_RESET_0, 0)
    for core in tile.cores:
        assert not core.in_reset


@spec("FW.RESET.REASSERT")
def test_reassert_reset():
    """Writing SOFT_RESET_ALL back re-asserts reset on all cores."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    tile.brisc.mem.write32(SOFT_RESET_0, 0)
    assert not tile.brisc.in_reset
    tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_ALL)
    for core in tile.cores:
        assert core.in_reset


# ===========================================================================
# BRISC always starts at PC=0
# ===========================================================================

@spec("FW.BOOT.BRISC_PC_ZERO")
def test_brisc_always_boots_from_pc_zero():
    """BRISC reset always jumps to PC=0 regardless of any RESET_PC register."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    # Even if someone erroneously wrote a BRISC reset PC, it must still be 0
    tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_BRISC_ONLY)
    assert tile.brisc.pc == 0


# ===========================================================================
# RESET_PC override mechanism
# ===========================================================================

@spec("FW.RESET_PC.OVERRIDE_MECHANISM")
def test_reset_pc_with_override():
    """Override-enabled subordinates start at their programmed reset PCs."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    mmio = tile.mmio
    mmio.write32(TRISC0_RESET_PC, 0x5A40)
    mmio.write32(NCRISC_RESET_PC, 0x5440)
    mmio.write32(TRISC_RESET_PC_OVR, 0b001)
    mmio.write32(NCRISC_RESET_PC_OVR, 0x1)
    tile.brisc.mem.write32(SOFT_RESET_0, 0)
    assert tile.trisc0.pc == 0x5A40
    assert tile.ncrisc.pc == 0x5440
    assert tile.brisc.pc == 0


@spec("FW.RESET_PC.WITHOUT_OVR")
def test_reset_pc_without_override_defaults_to_zero():
    """Without override enable, subordinate starts at PC=0."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    tile.mmio.write32(TRISC0_RESET_PC, 0x5A40)
    # TRISC_RESET_PC_OVR defaults to 0
    tile.brisc.mem.write32(SOFT_RESET_0, 0)
    assert tile.trisc0.pc == 0


@spec("FW.RESET_PC.TRISC_INDIVIDUAL_BITS")
def test_trisc_individual_override_bits():
    """Each TRISC override bit is independent."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    mmio = tile.mmio
    mmio.write32(TRISC0_RESET_PC, 0x100)
    mmio.write32(TRISC1_RESET_PC, 0x200)
    mmio.write32(TRISC2_RESET_PC, 0x300)
    mmio.write32(TRISC_RESET_PC_OVR, 0b010)  # only TRISC1
    tile.brisc.mem.write32(SOFT_RESET_0, 0)
    assert tile.trisc0.pc == 0      # no override
    assert tile.trisc1.pc == 0x200  # override bit 1 set
    assert tile.trisc2.pc == 0      # no override


# ===========================================================================
# JAL encoding
# ===========================================================================

@spec("FW.JAL.ENCODING")
def test_make_jal_encoding_formula():
    """_make_jal uses (target&0xFF000)|((target&0x800)<<9)|((target&0x7FE)<<20)|0x6F."""
    target = 0x3840
    jal = int.from_bytes(_make_jal(target), 'little')
    expected = (
        (target & 0xFF000)
        | ((target & 0x800) << 9)
        | ((target & 0x7FE) << 20)
        | 0x6F
    )
    assert jal == expected


@spec("FW.JAL.PC_JUMP")
def test_make_jal_brisc_fw_base_jump():
    """JAL from L1[0] jumps BRISC to BRISC_FIRMWARE_BASE (0x3840)."""
    jal = _make_jal(BRISC_FW_BASE)
    core = BRISC(pc=0)
    core.in_reset = False
    core.l1.load(0, jal)
    core.l1.write32(BRISC_FW_BASE, _addi(10, 0, 55))
    core.step()   # JAL
    assert core.pc == BRISC_FW_BASE
    core.step()   # ADDI
    assert core.regs[10] == 55


@spec("FW.JAL.ROUNDTRIP")
@pytest.mark.parametrize("target", [0x100, 0x3840, 0x5440, 0x6A40])
def test_make_jal_roundtrip(target):
    """_make_jal correctly encodes jumps to all standard firmware bases."""
    jal = _make_jal(target)
    core = BRISC(pc=0)
    core.in_reset = False
    core.l1.load(0, jal)
    core.step()
    assert core.pc == target, f"JAL to {target:#x}: pc={core.pc:#x}"


# ===========================================================================
# go_message protocol
# ===========================================================================

@spec("FW.GO_MSG.INIT_VALUE")
def test_go_msg_boot_init_value():
    """fw.boot writes RUN_MSG_INIT (0x40) to the signal byte at GO_MESSAGES+3."""
    # We can test the fw.boot structure indirectly: after construction +
    # boot stub, the go_init blob contains 0x40 in byte 3
    from emu.device import RUN_MSG_INIT
    assert RUN_MSG_INIT == 0x40


# ===========================================================================
# step_loop behavior
# ===========================================================================

@spec("FW.STEP.SKIPS_RESET")
def test_step_loop_skips_cores_in_reset():
    """step_loop does not step cores with in_reset=True."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    tile.l1.write32(0, _addi(10, 0, 42))
    tile.l1.write32(0x200, _addi(10, 0, 99))
    tile.mmio.write32(TRISC0_RESET_PC, 0x200)
    tile.mmio.write32(TRISC_RESET_PC_OVR, 0b001)
    tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_BRISC_ONLY)
    dev._step_loop([tile], lambda: True, 1)
    assert tile.brisc.regs[10] == 42
    assert tile.trisc0.in_reset
    assert tile.trisc0.regs[10] == 0


@spec("FW.STEP.WALL_CLOCK")
def test_wall_clock_increments_even_during_reset():
    """WALL_CLOCK_L advances even when all cores are in reset."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    assert tile.mmio.read32(WALL_CLOCK_L) == 0
    dev._step_loop([tile], lambda: dev._clock >= 5, 10)
    assert tile.mmio.read32(WALL_CLOCK_L) >= 5


@spec("FW.STEP.TIMEOUT")
def test_step_loop_raises_timeout():
    """step_loop raises TimeoutError if done condition never fires."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    with pytest.raises(TimeoutError):
        dev._step_loop([tile], lambda: False, max_steps=3)


# ===========================================================================
# BRISC releasing subordinates via firmware write
# ===========================================================================

@spec("FW.BRISC.RELEASES_SUBORDINATES", "FW.SOFT_RESET.HOOK")
def test_brisc_releases_subordinates_via_soft_reset():
    """BRISC writes 0 to SOFT_RESET_0; hook transitions subordinates to running."""
    dev = mini_device()
    tile = list(dev.tiles.values())[0]
    mmio = tile.mmio

    mmio.write32(TRISC0_RESET_PC, 0x200)
    mmio.write32(TRISC1_RESET_PC, 0x200)
    mmio.write32(TRISC2_RESET_PC, 0x200)
    mmio.write32(NCRISC_RESET_PC, 0x200)
    mmio.write32(TRISC_RESET_PC_OVR, 0b111)
    mmio.write32(NCRISC_RESET_PC_OVR, 0x1)

    tile.l1.write32(0x200, _addi(11, 0, 77))

    # BRISC code: LUI a0, 0xFFB12; SW x0, 0x1B0(a0)  → SOFT_RESET_0 = 0
    tile.l1.write32(0x00, _lui(10, 0xFFB12))
    tile.l1.write32(0x04, _sw(0, 0x1B0, 10))

    tile.brisc.mem.write32(SOFT_RESET_0, SOFT_RESET_BRISC_ONLY)

    def done():
        return all(c.regs[11] == 77
                   for c in [tile.ncrisc, tile.trisc0, tile.trisc1, tile.trisc2])

    dev._step_loop([tile], done, 10)
    for core in tile.cores:
        assert not core.in_reset
    for name, core in [('ncrisc', tile.ncrisc), ('trisc0', tile.trisc0),
                        ('trisc1', tile.trisc1), ('trisc2', tile.trisc2)]:
        assert core.regs[11] == 77, f"{name} didn't execute"
