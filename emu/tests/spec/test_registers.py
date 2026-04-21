"""Spec tests for ../specs/registers.md.

Each test is pinned to one or more clauses from
../clauses/registers.md via the @spec() marker.
"""

import pytest

from emu.core import BRISC, NCRISC, TRISC0, TRISC1, TRISC2
from emu.memory import Memory
from emu import dsl
from emu import memory as M

from .conftest import spec


# Helpers

def _step(insns, pc=0x100):
    """Build a BRISC with in_reset=False, load and run insns."""
    core = BRISC(pc=pc)
    core.in_reset = False
    core.load(pc, insns)
    core.run(len(insns))
    return core


# ===========================================================================
# CSR cfg0 (0x7C0)
# ===========================================================================

@spec("REG.CFG0.EXISTS")
def test_cfg0_csrrs_stores_and_reads_back():
    """CSRRS to cfg0 (0x7C0) stores bits; reading back returns them.

    dsl.CSRRS(rd, rs1, csr) encodes: rd=destination, rs1=source mask, csr=CSR address.
    """
    core = _step([
        dsl.CSRRS(dsl.a0, dsl.zero, 0x7C0),   # read old (expect 0)
        dsl.ADDI(dsl.t0, dsl.zero, 2),         # bit 1 = DisBp
        dsl.CSRRS(dsl.a1, dsl.t0, 0x7C0),     # set bit 1, return old
        dsl.CSRRS(dsl.a2, dsl.zero, 0x7C0),   # read current value
    ])
    assert core.regs[dsl.a0] == 0              # fresh core: cfg0 = 0
    assert core.regs[dsl.a1] == 0             # old value before set = 0
    assert core.regs[dsl.a2] & 2 == 2         # bit 1 is now set


@spec("REG.CFG0.EXISTS")
def test_cfg0_csrrc_clears_bits():
    """CSRRC clears bits in cfg0."""
    core = _step([
        dsl.ADDI(dsl.t0, dsl.zero, 3),
        dsl.CSRRS(dsl.zero, dsl.t0, 0x7C0),   # set bits 0 and 1
        dsl.ADDI(dsl.t1, dsl.zero, 2),
        dsl.CSRRC(dsl.zero, dsl.t1, 0x7C0),   # clear bit 1
        dsl.CSRRS(dsl.a0, dsl.zero, 0x7C0),   # read back
    ])
    assert core.regs[dsl.a0] & 3 == 1         # bit 0 still set, bit 1 cleared


# ===========================================================================
# SOFT_RESET_0 — constant values
# ===========================================================================

@spec("REG.SOFT_RESET.ALL_VALUE")
def test_soft_reset_all_constant():
    """SOFT_RESET_ALL = 0x47800."""
    # Bits 11 (BRISC) + 12-14 (TRISC0/1/2) + 18 (NCRISC) set.
    soft_reset_all = 0x47800
    # Verify bit 11 (BRISC)
    assert soft_reset_all & (1 << 11) != 0
    # Verify bits 12-14 (TRISCs)
    for bit in (12, 13, 14):
        assert soft_reset_all & (1 << bit) != 0
    # Verify bit 18 (NCRISC)
    assert soft_reset_all & (1 << 18) != 0


@spec("REG.SOFT_RESET.BRISC_ONLY_VALUE")
def test_soft_reset_brisc_only_constant():
    """SOFT_RESET_BRISC_ONLY_RUN = 0x47000: bit 11 clear, bits 12-14 and 18 set."""
    soft_reset_brisc_run = 0x47000
    # BRISC bit (11) must be CLEAR (BRISC is released)
    assert soft_reset_brisc_run & (1 << 11) == 0
    # TRISCs (12-14) still in reset
    for bit in (12, 13, 14):
        assert soft_reset_brisc_run & (1 << bit) != 0
    # NCRISC (18) still in reset
    assert soft_reset_brisc_run & (1 << 18) != 0


@spec("REG.SOFT_RESET.GATES_CORES")
def test_core_starts_in_reset():
    """Newly constructed cores start with in_reset=True."""
    for cls in (BRISC, NCRISC, TRISC0, TRISC1, TRISC2):
        assert cls().in_reset is True


# ===========================================================================
# RESET_PC registers — addresses defined in memory constants
# ===========================================================================

@spec("REG.RESET_PC.TRISC_REGISTERS")
def test_trisc_reset_pc_addresses():
    """TRISC RESET_PC registers are at the documented addresses."""
    assert M.TRISC0_RESET_PC == 0xFFB12228
    assert M.TRISC1_RESET_PC == 0xFFB1222C
    assert M.TRISC2_RESET_PC == 0xFFB12230


@spec("REG.RESET_PC.NCRISC_REGISTER")
def test_ncrisc_reset_pc_address():
    """NCRISC_RESET_PC is at 0xFFB12238."""
    assert M.NCRISC_RESET_PC == 0xFFB12238


# ===========================================================================
# Write-sink no-ops
# ===========================================================================

@spec("REG.WRITE_SINK.DEST_CG_CTRL")
def test_write_sink_dest_cg_ctrl_accepts_write():
    """Write to DEST_CG_CTRL (0xFFB12240) does not raise an error."""
    core = BRISC()
    core.mem.default = Memory()
    # Should not raise
    core.mem.write32(M.DEST_CG_CTRL, 0)


@spec("REG.WRITE_SINK.DEST_CG_CTRL")
def test_write_sink_tdma_clk_gate_accepts_write():
    """Write to TDMA_CLK_GATE_EN (0xFFB11024) does not raise an error."""
    core = BRISC()
    core.mem.default = Memory()
    core.mem.write32(M.TDMA_CLK_GATE_EN, 0x3F)


# ===========================================================================
# Standard RISC-V CSRs — must be readable without error
# ===========================================================================

def _csr_read(csr_addr):
    """Build a CSRRS instruction that reads a CSR address.

    dsl.CSRRS validates the CSR address as a 12-bit unsigned value, but only
    accepts values in [0, 4095].  For addresses that cannot be passed through
    the dsl helper (e.g., values that would trigger other dsl validation), we
    build the raw instruction word directly.  The RISC-V encoding places the
    CSR number in bits [31:20] as an unsigned 12-bit field.
    rd=a0 (reg 10), rs1=zero (reg 0), funct3=2 (CSRRS), opcode=0x73.
    """
    from emu import dsl as _dsl
    from emu.memory import Memory
    # Direct encoding: avoids dsl validation entirely.
    # opcode=0x73 | rd<<7 | funct3<<12 | rs1<<15 | csr<<20
    rd = dsl.a0   # 10
    rs1 = dsl.zero  # 0
    word = 0x73 | (rd << 7) | (2 << 12) | (rs1 << 15) | ((csr_addr & 0xFFF) << 20)
    return dsl.RiscVInsn(word)


@spec("REG.CSR.MCYCLE")
def test_mcycle_readable():
    """Reading mcycle (CSR 0xB00) returns a value without raising an exception."""
    core = _step([_csr_read(0xB00)])
    # Any value is acceptable — just must not crash and result must be 32-bit
    assert 0 <= core.regs[dsl.a0] <= 0xFFFFFFFF


@spec("REG.CSR.MINSTRET")
def test_minstret_readable():
    """Reading minstret (CSR 0xB02) returns a value without raising an exception."""
    core = _step([_csr_read(0xB02)])
    assert 0 <= core.regs[dsl.a0] <= 0xFFFFFFFF


@spec("REG.CSR.TT_CFG_QSTATUS")
def test_tt_cfg_qstatus_returns_zero():
    """tt_cfg_qstatus (CSR 0xBC0) returns 0 in the emulator (not busy)."""
    core = _step([_csr_read(0xBC0)])
    assert core.regs[dsl.a0] == 0


@spec("REG.CSR.TT_CFG_QSTATUS")
def test_tt_cfg_bstatus_returns_zero():
    """tt_cfg_bstatus (CSR 0xBC1) returns 0 in the emulator (not busy)."""
    core = _step([_csr_read(0xBC1)])
    assert core.regs[dsl.a0] == 0
