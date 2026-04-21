"""Spec tests for ../specs/address-space.md.

Each test is pinned to one or more clauses from
../clauses/address-space.md via the @spec() marker.
"""

import pytest

from emu.core import BRISC, NCRISC, TRISC0, TRISC1, TRISC2
from emu.memory import Memory
from emu import memory as M
from emu import dsl

from .conftest import spec


# Local helper

def _attach_slow_ldm(cores):
    fallback = Memory()
    slot_bases = [M.LDM_SLOW_BRISC, M.LDM_SLOW_NCRISC,
                  M.LDM_SLOW_TRISC0, M.LDM_SLOW_TRISC1, M.LDM_SLOW_TRISC2]
    for c in cores:
        c.mem.default = fallback
        for peer, base in zip(cores, slot_bases):
            c.mem.register(base, base + peer.LDM_SIZE - 1, peer.ldm, offset=base)
    return fallback


# ===========================================================================
# Router basics
# ===========================================================================

@spec("ADDR.ROUTER.FIRST_MATCH_WINS")
def test_first_registered_range_shadows_later():
    """First registered range wins over a later overlapping one."""
    from emu.memory import Memory
    from emu.router import Router

    first  = Memory()
    second = Memory()
    r = Router(default=Memory())
    r.register(0x1000, 0x1FFF, first,  offset=0x1000)
    r.register(0x1000, 0x1FFF, second, offset=0x1000)
    r.write32(0x1000, 0xAAAA)
    # first was registered first — write should go to it
    assert first.read32(0)  == 0xAAAA
    assert second.read32(0) == 0


@spec("ADDR.ROUTER.DEFAULT_FALLBACK")
def test_unmapped_address_goes_to_default():
    """Access to unmapped address goes to router.default."""
    core = BRISC()
    core.mem.write32(0xDEADBEE0, 0xCAFEBABE)
    assert core.mem.default.read32(0xDEADBEE0) == 0xCAFEBABE


# ===========================================================================
# L1 address range
# ===========================================================================

@spec("ADDR.L1.RANGE")
def test_l1_range_constants():
    """L1_BASE, L1_END, L1_SIZE match spec values."""
    assert M.L1_BASE == 0x00000000
    assert M.L1_END  == 0x0017FFFF
    assert M.L1_SIZE == 0x00180000


@spec("ADDR.L1.SHARED_ALL_CORES")
def test_l1_is_shared_between_cores():
    """Write to L1 by one core is immediately visible to another."""
    shared = Memory()
    brisc  = BRISC(l1=shared)
    trisc1 = TRISC1(l1=shared)
    brisc.mem.write32(0x5000, 0x12345678)
    assert trisc1.mem.read32(0x5000) == 0x12345678


# ===========================================================================
# LDM fast path
# ===========================================================================

@spec("ADDR.LDM.FAST_PATH_BASE")
def test_ldm_base_address():
    assert M.LDM_BASE == 0xFFB00000


@spec("ADDR.LDM.FAST_PATH_PER_CORE")
def test_ldm_fast_path_is_per_core():
    """Two different cores writing the same LDM address go to different banks."""
    shared = Memory()
    brisc  = BRISC(l1=shared)
    trisc0 = TRISC0(l1=shared)
    brisc.mem.write32(M.LDM_BASE, 0xAAAA)
    trisc0.mem.write32(M.LDM_BASE, 0xBBBB)
    assert brisc.mem.read32(M.LDM_BASE)  == 0xAAAA
    assert trisc0.mem.read32(M.LDM_BASE) == 0xBBBB


# ===========================================================================
# LDM slow path addresses
# ===========================================================================

@spec("ADDR.LDM.SLOW_PATH_BRISC")
def test_ldm_slow_brisc_address():
    assert M.LDM_SLOW_BRISC == 0xFFB14000


@spec("ADDR.LDM.SLOW_PATH_NCRISC")
def test_ldm_slow_ncrisc_address():
    assert M.LDM_SLOW_NCRISC == 0xFFB16000


@spec("ADDR.LDM.SLOW_PATH_TRISC0")
def test_ldm_slow_trisc0_address():
    assert M.LDM_SLOW_TRISC0 == 0xFFB18000


@spec("ADDR.LDM.SLOW_PATH_TRISC1")
def test_ldm_slow_trisc1_address():
    assert M.LDM_SLOW_TRISC1 == 0xFFB1A000


@spec("ADDR.LDM.SLOW_PATH_TRISC2")
def test_ldm_slow_trisc2_address():
    assert M.LDM_SLOW_TRISC2 == 0xFFB1C000


# ===========================================================================
# NIU registers
# ===========================================================================

@spec("ADDR.NIU.NOC0_BASE")
def test_noc0_base_and_size():
    assert M.NOC0_BASE == 0xFFB20000
    assert M.NOC_SIZE  == 0x10000


@spec("ADDR.NIU.NOC1_BASE")
def test_noc1_base():
    assert M.NOC1_BASE == 0xFFB30000


@spec("ADDR.NIU.NOC0_BASE",
      "ADDR.NIU.NOC1_BASE")
def test_noc_registers_routed_away_from_l1():
    """Writes to NOC0_BASE do not land in L1."""
    core = BRISC()
    backing = Memory()
    core.mem.register(M.NOC0_BASE, M.NOC0_BASE + M.NOC_SIZE - 1,
                      backing, offset=M.NOC0_BASE)
    core.mem.write32(M.NOC0_BASE + M.NIU_ID_LOGICAL, 0x42)
    assert backing.read32(M.NIU_ID_LOGICAL) == 0x42
    # L1 at the same offset is untouched
    assert core.l1.read32(M.NOC0_BASE + M.NIU_ID_LOGICAL) == 0


# ===========================================================================
# Debug/control register addresses
# ===========================================================================

@spec("ADDR.DEBUG.SOFT_RESET_ADDR")
def test_soft_reset_address():
    assert M.SOFT_RESET_0 == 0xFFB121B0


@spec("ADDR.DEBUG.WALL_CLOCK_ADDR")
def test_wall_clock_addresses():
    assert M.WALL_CLOCK_L == 0xFFB121F0
    assert M.WALL_CLOCK_H == 0xFFB121F8


# ===========================================================================
# Instruction buffer FIFO address
# ===========================================================================

@spec("ADDR.INSTRN_BUF.T0_BASE")
def test_instrn_buf_t0_base():
    assert M.INSTRN_BUF_T0 == 0xFFE40000


# ===========================================================================
# Tensix config base
# ===========================================================================

@spec("ADDR.TENSIX_CFG.BASE")
def test_tensix_cfg_base():
    assert M.TENSIX_CFG_BASE == 0xFFEF0000


# ===========================================================================
# L1 mailbox layout
# ===========================================================================

@spec("ADDR.MAILBOX.BASE")
def test_mailbox_layout_constants():
    assert M.MAILBOX_BASE == 0x000060
    assert M.GO_MESSAGES  == 0x000370


@spec("ADDR.MAILBOX.SUBORDINATE_SYNC")
def test_subordinate_sync_address():
    assert M.SUBORDINATE_SYNC == 0x000068


# ===========================================================================
# Router dispatch — single instruction
# ===========================================================================

@spec("ADDR.ROUTER.FIRST_MATCH_WINS",
      "ADDR.NIU.NOC0_BASE")
def test_risc_store_routes_to_noc0_not_l1():
    """SW to NOC0_BASE range routes to the NIU handler, not L1."""
    core = BRISC(pc=0x100)
    core.in_reset = False
    backing = Memory()
    core.mem.register(M.NOC0_BASE, M.NOC0_BASE + M.NOC_SIZE - 1,
                      backing, offset=M.NOC0_BASE)
    core.load(0x100, [
        dsl.LUI(dsl.t0, M.NOC0_BASE),
        dsl.ADDI(dsl.t1, dsl.zero, 0x42),
        dsl.SW(dsl.t0, dsl.t1, M.NIU_ID_LOGICAL),
    ])
    core.run(3)
    assert backing.read32(M.NIU_ID_LOGICAL) == 0x42
    assert core.l1.read32(M.NOC0_BASE + M.NIU_ID_LOGICAL) == 0
