from emu.core import BRISC, NCRISC, TRISC0, TRISC1, TRISC2
from emu.memory import Memory
from emu import memory as M
from emu import dsl

def run(insns, n=None, pc=0x100):
    core = BRISC(pc=pc)
    core.load(pc, insns)
    core.run(n or len(insns))
    return core

def test_addi():
    core = run([dsl.ADDI(dsl.a0, dsl.zero, 42)])
    assert core.regs[dsl.a0] == 42

def test_addi_negative():
    core = run([dsl.ADDI(dsl.a0, dsl.zero, -1)])
    assert core.regs[dsl.a0] == 0xFFFFFFFF

def test_add_sub():
    core = run([
        dsl.ADDI(dsl.a0, dsl.zero, 10), dsl.ADDI(dsl.a1, dsl.zero, 3),
        dsl.ADD(dsl.a2, dsl.a0, dsl.a1), dsl.SUB(dsl.a3, dsl.a0, dsl.a1),
    ])
    assert core.regs[dsl.a2] == 13
    assert core.regs[dsl.a3] == 7

def test_logic():
    core = run([
        dsl.ADDI(dsl.a0, dsl.zero, 0xFF), dsl.ADDI(dsl.a1, dsl.zero, 0x0F),
        dsl.AND(dsl.a2, dsl.a0, dsl.a1), dsl.OR(dsl.a3, dsl.a0, dsl.a1),
        dsl.XOR(dsl.a4, dsl.a0, dsl.a1), dsl.ANDI(dsl.a5, dsl.a0, 0x33),
        dsl.ORI(dsl.a6, dsl.zero, 0x55), dsl.XORI(dsl.a7, dsl.a0, 0x0F),
    ])
    assert core.regs[dsl.a2] == 0x0F
    assert core.regs[dsl.a3] == 0xFF
    assert core.regs[dsl.a4] == 0xF0
    assert core.regs[dsl.a5] == 0x33
    assert core.regs[dsl.a6] == 0x55
    assert core.regs[dsl.a7] == 0xF0

def test_shifts():
    core = run([
        dsl.ADDI(dsl.a0, dsl.zero, 1), dsl.SLLI(dsl.a1, dsl.a0, 4),
        dsl.ADDI(dsl.a2, dsl.zero, -1),
        dsl.SRLI(dsl.a3, dsl.a2, 24), dsl.SRAI(dsl.a4, dsl.a2, 24),
        dsl.ADDI(dsl.t0, dsl.zero, 4),
        dsl.SLL(dsl.a5, dsl.a0, dsl.t0), dsl.SRL(dsl.a6, dsl.a2, dsl.t0),
    ])
    assert core.regs[dsl.a1] == 16
    assert core.regs[dsl.a3] == 0xFF
    assert core.regs[dsl.a4] == 0xFFFFFFFF
    assert core.regs[dsl.a5] == 16
    assert core.regs[dsl.a6] == 0x0FFFFFFF

def test_slt():
    core = run([
        dsl.ADDI(dsl.a0, dsl.zero, -1), dsl.ADDI(dsl.a1, dsl.zero, 1),
        dsl.SLT(dsl.a2, dsl.a0, dsl.a1),   # -1 < 1 signed
        dsl.SLTU(dsl.a3, dsl.a0, dsl.a1),  # 0xFFFFFFFF < 1 unsigned -> no
        dsl.SLTU(dsl.a4, dsl.a1, dsl.a0),  # 1 < 0xFFFFFFFF unsigned -> yes
    ])
    assert core.regs[dsl.a2] == 1
    assert core.regs[dsl.a3] == 0
    assert core.regs[dsl.a4] == 1

def test_lui_auipc():
    PC = 0x100
    core = run([dsl.LUI(dsl.a0, 0xABCDE000), dsl.AUIPC(dsl.a1, 0x00001000)], pc=PC)
    assert core.regs[dsl.a0] == 0xABCDE000
    assert core.regs[dsl.a1] == (PC + 4) + 0x1000

def test_lw_sw():
    core = run([
        dsl.ADDI(dsl.a0, dsl.zero, 0x42), dsl.LUI(dsl.a1, 0x1000),
        dsl.SW(dsl.a1, dsl.a0, 0), dsl.LW(dsl.a2, dsl.a1, 0),
    ])
    assert core.regs[dsl.a2] == 0x42

def test_lb_sb_lbu():
    core = BRISC(pc=0x100)
    core.l1.write8(0x2000, 0xFF)
    core.load(0x100, [
        dsl.LUI(dsl.t0, 0x2000),
        dsl.LBU(dsl.a0, dsl.t0, 0), dsl.LW(dsl.a1, dsl.t0, 0),
    ])
    core.run(3)
    assert core.regs[dsl.a0] == 0xFF
    assert core.regs[dsl.a1] == 0xFF

def test_sh_lh_lhu():
    core = BRISC(pc=0x100)
    core.load(0x100, [
        dsl.ADDI(dsl.a0, dsl.zero, -1), dsl.LUI(dsl.t0, 0x2000),
        dsl.SH(dsl.t0, dsl.a0, 0), dsl.LHU(dsl.a1, dsl.t0, 0),
    ])
    core.run(4)
    assert core.regs[dsl.a1] == 0xFFFF

def test_beq_taken():
    core = run([
        dsl.ADDI(dsl.a0, dsl.zero, 5), dsl.ADDI(dsl.a1, dsl.zero, 5),
        dsl.BEQ(dsl.a0, dsl.a1, 8),
        dsl.ADDI(dsl.a2, dsl.zero, 0xFF),  # skipped
        dsl.ADDI(dsl.a2, dsl.zero, 1),     # target
    ], n=4)
    assert core.regs[dsl.a2] == 1

def test_bne_not_taken():
    core = run([
        dsl.ADDI(dsl.a0, dsl.zero, 3), dsl.ADDI(dsl.a1, dsl.zero, 3),
        dsl.BNE(dsl.a0, dsl.a1, 8), dsl.ADDI(dsl.a2, dsl.zero, 42),
    ])
    assert core.regs[dsl.a2] == 42

def test_bne_loop():
    core = run([
        dsl.ADDI(dsl.a0, dsl.zero, 0), dsl.ADDI(dsl.a1, dsl.zero, 5),
        dsl.ADDI(dsl.a0, dsl.a0, 1),  # loop body
        dsl.BNE(dsl.a0, dsl.a1, -4),  # back to loop body
    ], n=12)
    assert core.regs[dsl.a0] == 5

def test_jal_jalr():
    PC = 0x100
    core = run([
        dsl.JAL(dsl.ra, 8),
        dsl.ADDI(dsl.a0, dsl.zero, 0xFF),  # skipped
        dsl.ADDI(dsl.a1, dsl.zero, 0x42),  # target
    ], n=2, pc=PC)
    assert core.regs[dsl.ra] == PC + 4
    assert core.regs[dsl.a0] == 0
    assert core.regs[dsl.a1] == 0x42
    # JALR
    core2 = BRISC(pc=0x100)
    core2.load(0x100, [dsl.ADDI(dsl.a0, dsl.zero, 0x200), dsl.JALR(dsl.ra, dsl.a0, 0)])
    core2.load(0x200, [dsl.ADDI(dsl.a1, dsl.zero, 7)])
    core2.run(3)
    assert core2.regs[dsl.ra] == 0x108
    assert core2.regs[dsl.a1] == 7

def test_x0_immutable():
    core = run([dsl.ADDI(dsl.zero, dsl.zero, 99)])
    assert core.regs[0] == 0

def test_ldm_isolation():
    shared = Memory()
    a, b = BRISC(l1=shared, pc=0x100), TRISC0(l1=shared, pc=0x100)
    a.ldm.write32(0, 0xAAAA); b.ldm.write32(0, 0xBBBB)
    assert a.read32(0xFFB00000) == 0xAAAA
    assert b.read32(0xFFB00000) == 0xBBBB
    a.write32(0x1000, 0xDEAD)
    assert b.read32(0x1000) == 0xDEAD

def test_ldm_slow_path_read():
    """Slow/cross-core LDM reads route to the target core's LDM."""
    shared = Memory()
    cores = [BRISC(l1=shared), NCRISC(l1=shared),
             TRISC0(l1=shared), TRISC1(l1=shared), TRISC2(l1=shared)]
    ldm_slots = [(c.ldm, c.LDM_SIZE) for c in cores]
    for c in cores:
        c.mem.slow_ldm = ldm_slots

    # Each core writes a marker to its own LDM (fast path)
    for i, c in enumerate(cores):
        c.ldm.write32(0, 0xAA00 + i)

    # Every core can read every other core's LDM via slow path
    slow_bases = [M.LDM_SLOW_BRISC, M.LDM_SLOW_NCRISC,
                  M.LDM_SLOW_TRISC0, M.LDM_SLOW_TRISC1, M.LDM_SLOW_TRISC2]
    for reader in cores:
        for j, base in enumerate(slow_bases):
            assert reader.read32(base) == 0xAA00 + j

def test_ldm_slow_path_write():
    """Writes via slow path land in the target core's LDM."""
    shared = Memory()
    brisc = BRISC(l1=shared)
    ncrisc = NCRISC(l1=shared)
    ldm_slots = [
        (brisc.ldm, BRISC.LDM_SIZE),
        (ncrisc.ldm, NCRISC.LDM_SIZE),
        (Memory(), 0x1000), (Memory(), 0x1000), (Memory(), 0x1000),
    ]
    for c in [brisc, ncrisc]:
        c.mem.slow_ldm = ldm_slots
    # NCRISC writes to BRISC's LDM via slow path
    ncrisc.write32(M.LDM_SLOW_BRISC + 0x100, 0xDEAD)
    # BRISC sees it via fast path
    assert brisc.read32(M.LDM_BASE + 0x100) == 0xDEAD

def test_ldm_slow_path_padding():
    """Access to padding above a TRISC slow-path slot falls to MMIO."""
    shared = Memory()
    brisc = BRISC(l1=shared)
    trisc0 = TRISC0(l1=shared)
    ldm_slots = [
        (brisc.ldm, BRISC.LDM_SIZE),
        (Memory(), 0x2000),
        (trisc0.ldm, TRISC0.LDM_SIZE),
        (Memory(), 0x1000), (Memory(), 0x1000),
    ]
    brisc.mem.slow_ldm = ldm_slots
    # TRISC0 has 4K LDM — upper 4K of its 8K slot is unmapped padding
    brisc.write32(M.LDM_SLOW_TRISC0 + 0x1000, 0xBAD)
    assert trisc0.ldm.read32(0x1000) == 0  # not in TRISC0's LDM
    assert brisc.mem.mmio.read32(M.LDM_SLOW_TRISC0 + 0x1000) == 0xBAD

# -- address map routing ---------------------------------------------------

def test_niu_regs_routed():
    """Stores to NIU register space land in the noc[] Memory, not L1."""
    core = BRISC(pc=0x100)
    core.load(0x100, [
        dsl.LUI(dsl.t0, M.NOC0_BASE),                   # t0 = 0xFFB20000
        dsl.ADDI(dsl.t1, dsl.zero, 0x42),
        dsl.SW(dsl.t0, dsl.t1, M.NIU_ID_LOGICAL),       # store 0x42 to NOC0 NOC_ID_LOGICAL
    ])
    core.run(3)
    assert core.mem.noc[0].read32(M.NIU_ID_LOGICAL) == 0x42
    assert core.l1.read32(M.NOC0_BASE + M.NIU_ID_LOGICAL) == 0  # not in L1

def test_tensix_cfg_routed():
    """Stores to Tensix config registers land in cfg Memory."""
    core = BRISC(pc=0x100)
    core.write32(M.TENSIX_CFG_BASE + 0x10, 0xBEEF)
    assert core.mem.cfg.read32(0x10) == 0xBEEF
    assert core.read32(M.TENSIX_CFG_BASE + 0x10) == 0xBEEF

def test_instrn_fifo_callback():
    """Writes to instruction FIFO addresses trigger the callback."""
    log = []
    core = BRISC(pc=0x100)
    core.mem.on_instrn_write = lambda thread, word: log.append((thread, word))
    core.write32(M.INSTRN_BUF_T0, 0xDEAD)
    core.write32(M.INSTRN_BUF_T1, 0xBEEF)
    core.write32(M.INSTRN_BUF_T2, 0xCAFE)
    assert log == [(0, 0xDEAD), (1, 0xBEEF), (2, 0xCAFE)]

def test_noc_cmd_ctrl_callback():
    """Writing 1 to NOC_CMD_CTRL fires the on_noc_cmd callback."""
    log = []
    core = BRISC(pc=0x100)
    core.mem.on_noc_cmd = lambda noc_id, buf: log.append((noc_id, buf))
    # NOC0 buf0 CMD_CTRL
    core.write32(M.NOC0_BASE + M.NIU_CMD_CTRL, 1)
    # NOC1 buf1 CMD_CTRL (buf1 is at +0x800)
    core.write32(M.NOC1_BASE + M.NIU_CMD_BUF_STRIDE + M.NIU_CMD_CTRL, 1)
    assert log == [(0, 0), (1, 1)]

def test_mmio_catch_all():
    """Reads/writes to unmapped MMIO don't crash, reads return stored values."""
    core = BRISC(pc=0x100)
    core.write32(M.SOFT_RESET_0, 0x47800)
    assert core.read32(M.SOFT_RESET_0) == 0x47800
