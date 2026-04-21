"""Spec tests for ../specs/ldm-layouts.md.

Each test is pinned to one or more clauses from
../clauses/ldm-layouts.md via the @spec() marker.

Helper _attach_slow_ldm mirrors the one in test_riscv.py; duplicated here
so spec tests are self-contained (conftest.py must not be modified).
"""

import pytest

from emu.core import BRISC, NCRISC, TRISC0, TRISC1, TRISC2
from emu.memory import Memory
from emu import memory as M

from .conftest import spec


# Local helper — mirrors test_riscv._attach_slow_ldm

def _attach_slow_ldm(cores):
    """Register each core's LDM at its slow-path address in all cores' routers."""
    fallback = Memory()
    slot_bases = [M.LDM_SLOW_BRISC, M.LDM_SLOW_NCRISC,
                  M.LDM_SLOW_TRISC0, M.LDM_SLOW_TRISC1, M.LDM_SLOW_TRISC2]
    for c in cores:
        c.mem.default = fallback
        for peer, base in zip(cores, slot_bases):
            c.mem.register(base, base + peer.LDM_SIZE - 1, peer.ldm, offset=base)
    return fallback


# ===========================================================================
# LDM isolation
# ===========================================================================

@spec("LDM.ISOLATION.PER_CORE")
def test_brisc_and_trisc0_ldm_are_independent():
    """BRISC write to 0xFFB00000 must not affect TRISC0's LDM at 0xFFB00000."""
    shared = Memory()
    brisc  = BRISC(l1=shared)
    trisc0 = TRISC0(l1=shared)
    brisc.ldm.write32(0, 0xAAAA)
    trisc0.ldm.write32(0, 0xBBBB)
    assert brisc.mem.read32(M.LDM_BASE)  == 0xAAAA
    assert trisc0.mem.read32(M.LDM_BASE) == 0xBBBB


@spec("LDM.ISOLATION.PER_CORE")
@pytest.mark.parametrize("cls_a,cls_b", [
    (BRISC,  NCRISC),
    (TRISC0, TRISC1),
    (TRISC1, TRISC2),
    (BRISC,  TRISC2),
])
def test_ldm_isolation_between_core_pairs(cls_a, cls_b):
    """No two different cores share the same LDM Memory object."""
    shared = Memory()
    a = cls_a(l1=shared)
    b = cls_b(l1=shared)
    assert a.ldm is not b.ldm


# ===========================================================================
# LDM sizes
# ===========================================================================

@spec("LDM.SIZE.BRISC_8K")
def test_brisc_ldm_size():
    assert BRISC.LDM_SIZE == 0x2000


@spec("LDM.SIZE.NCRISC_8K")
def test_ncrisc_ldm_size():
    assert NCRISC.LDM_SIZE == 0x2000


@spec("LDM.SIZE.TRISC0_4K")
def test_trisc0_ldm_size():
    assert TRISC0.LDM_SIZE == 0x1000


@spec("LDM.SIZE.TRISC1_4K")
def test_trisc1_ldm_size():
    assert TRISC1.LDM_SIZE == 0x1000


@spec("LDM.SIZE.TRISC2_4K")
def test_trisc2_ldm_size():
    assert TRISC2.LDM_SIZE == 0x1000


# ===========================================================================
# L1 is shared
# ===========================================================================

@spec("LDM.L1.SHARED_ALL_CORES")
def test_l1_write_by_brisc_visible_to_trisc0():
    """Write to L1 by BRISC is immediately visible to TRISC0."""
    shared = Memory()
    brisc  = BRISC(l1=shared)
    trisc0 = TRISC0(l1=shared)
    brisc.mem.write32(0x1000, 0xDEADBEEF)
    assert trisc0.mem.read32(0x1000) == 0xDEADBEEF


@spec("LDM.L1.SHARED_ALL_CORES")
def test_l1_write_by_ncrisc_visible_to_all():
    """Write to L1 by NCRISC is visible to all other cores."""
    shared = Memory()
    cores = [BRISC(l1=shared), NCRISC(l1=shared),
             TRISC0(l1=shared), TRISC1(l1=shared), TRISC2(l1=shared)]
    cores[1].mem.write32(0x4000, 0xCAFEBABE)
    for c in cores:
        assert c.mem.read32(0x4000) == 0xCAFEBABE


# ===========================================================================
# Slow-path addresses
# ===========================================================================

@spec("LDM.SLOW_PATH.BRISC_BASE")
def test_brisc_slow_path_base():
    assert M.LDM_SLOW_BRISC == 0xFFB14000


@spec("LDM.SLOW_PATH.NCRISC_BASE")
def test_ncrisc_slow_path_base():
    assert M.LDM_SLOW_NCRISC == 0xFFB16000


@spec("LDM.SLOW_PATH.TRISC0_BASE")
def test_trisc0_slow_path_base():
    assert M.LDM_SLOW_TRISC0 == 0xFFB18000


@spec("LDM.SLOW_PATH.TRISC1_BASE")
def test_trisc1_slow_path_base():
    assert M.LDM_SLOW_TRISC1 == 0xFFB1A000


@spec("LDM.SLOW_PATH.TRISC2_BASE")
def test_trisc2_slow_path_base():
    assert M.LDM_SLOW_TRISC2 == 0xFFB1C000


@spec("LDM.SLOW_PATH.WRITE_VISIBLE_FAST",
      "LDM.SLOW_PATH.BRISC_BASE")
def test_slow_path_write_visible_via_fast_path():
    """Write to BRISC slow-path address is visible via fast-path address."""
    shared = Memory()
    brisc  = BRISC(l1=shared)
    ncrisc = NCRISC(l1=shared)
    _attach_slow_ldm([brisc, ncrisc, TRISC0(l1=shared),
                      TRISC1(l1=shared), TRISC2(l1=shared)])
    # NCRISC writes to BRISC's LDM via slow path
    ncrisc.mem.write32(M.LDM_SLOW_BRISC + 0x100, 0xDEAD)
    # BRISC sees it via fast path
    assert brisc.mem.read32(M.LDM_BASE + 0x100) == 0xDEAD


@spec("LDM.SLOW_PATH.WRITE_VISIBLE_FAST")
def test_slow_path_read_all_cores():
    """Every core can read every other core's LDM via its slow-path address."""
    shared = Memory()
    cores = [BRISC(l1=shared), NCRISC(l1=shared),
             TRISC0(l1=shared), TRISC1(l1=shared), TRISC2(l1=shared)]
    _attach_slow_ldm(cores)
    # Each core writes a marker to its own LDM
    for i, c in enumerate(cores):
        c.ldm.write32(0, 0xAA00 + i)
    slow_bases = [M.LDM_SLOW_BRISC, M.LDM_SLOW_NCRISC,
                  M.LDM_SLOW_TRISC0, M.LDM_SLOW_TRISC1, M.LDM_SLOW_TRISC2]
    # Any core can read any other core's marker via slow path
    for reader in cores:
        for j, base in enumerate(slow_bases):
            assert reader.mem.read32(base) == 0xAA00 + j


@spec("LDM.SLOW_PATH.TRISC_PADDING")
def test_trisc_slow_path_upper_half_is_padding():
    """TRISC0 slow-path upper 4 KiB (offset >= 0x1000) is not TRISC0's LDM."""
    shared = Memory()
    brisc  = BRISC(l1=shared)
    trisc0 = TRISC0(l1=shared)
    fallback = _attach_slow_ldm([brisc, NCRISC(l1=shared), trisc0,
                                  TRISC1(l1=shared), TRISC2(l1=shared)])
    # Write to upper half of TRISC0's 8K slot via BRISC
    brisc.mem.write32(M.LDM_SLOW_TRISC0 + 0x1000, 0xBAD)
    # TRISC0's actual LDM is only 4K — offset 0x1000 is NOT inside it
    assert trisc0.ldm.read32(0x1000) == 0   # LDM untouched
    # The write landed in the fallback (padding)
    assert fallback.read32(M.LDM_SLOW_TRISC0 + 0x1000) == 0xBAD
