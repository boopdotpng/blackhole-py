import pytest

from emu.core import BRISC, NCRISC, TRISC0, TRISC1, TRISC2
from emu.memory import Memory
from emu import memory as M
import dsl


def _attach_slow_ldm(cores):
  fallback = Memory()
  slot_bases = [M.LDM_SLOW_BRISC, M.LDM_SLOW_NCRISC,
         M.LDM_SLOW_TRISC0, M.LDM_SLOW_TRISC1, M.LDM_SLOW_TRISC2]
  for c in cores:
    c.mem.default = fallback
    for peer, base in zip(cores, slot_bases):
      c.mem.register(base, base + peer.LDM_SIZE - 1, peer.ldm, offset=base)
  return fallback

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

def test_shift_immediate_range_validation():
  for fn in [dsl.SLLI, dsl.SRLI, dsl.SRAI]:
    try:
      fn(dsl.a0, dsl.a1, 32)
      assert False, f"{fn.__name__} should have rejected shamt=32"
    except ValueError:
      pass

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

# ============================================================================
# RV32 extensions: M (multiply/divide), Zba (address generation), Zbb (bit manip)
# ============================================================================
# -- M extension ---------------------------------------------------------------

def test_mul():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 7), dsl.ADDI(dsl.a1, dsl.zero, 6),
    dsl.MUL(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 42

def test_mul_overflow():
  core = run([
    dsl.LUI(dsl.a0, 0x10000000), dsl.ADDI(dsl.a1, dsl.zero, 16),
    dsl.MUL(dsl.a2, dsl.a0, dsl.a1),
  ])
  # 0x10000000 * 16 = 0x1_0000_0000 → lower 32 bits = 0
  assert core.regs[dsl.a2] == 0

def test_mulhu():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 21),
    dsl.LUI(dsl.a1, 0x92493000),
    dsl.ADDI(dsl.a1, dsl.a1, -0x6D),  # a1 = 0x92492493 (magic for /7)
    dsl.MULHU(dsl.a2, dsl.a0, dsl.a1),
  ])
  # mulhu(21, 0x92492493) = (21 * 0x92492493) >> 32
  expected = (21 * 0x92492493) >> 32
  assert core.regs[dsl.a2] == expected

def test_mulhu_div7_pattern():
  magic = 0x92492493
  for n in [0, 1, 6, 7, 13, 14, 49, 100]:
    core = run([
      dsl.ADDI(dsl.a0, dsl.zero, n),
      dsl.LUI(dsl.a1, magic & 0xFFFFF000),
      dsl.ADDI(dsl.a1, dsl.a1, (magic & 0xFFF) - (0x1000 if magic & 0x800 else 0)),
      dsl.MULHU(dsl.a2, dsl.a0, dsl.a1),
      dsl.SRLI(dsl.a2, dsl.a2, 2),
    ])
    assert core.regs[dsl.a2] == n // 7, f"div7({n}) failed"

@pytest.mark.parametrize("insn,divisor,expected", [
  (dsl.DIVU, 5, 8),             # 42 / 5 = 8
  (dsl.DIVU, 0, 0xFFFFFFFF),    # divu by zero → all ones
  (dsl.REMU, 5, 2),             # 42 % 5 = 2
  (dsl.REMU, 0, 42),            # remu by zero → dividend
])
def test_divu_remu(insn, divisor, expected):
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 42), dsl.ADDI(dsl.a1, dsl.zero, divisor),
    insn(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == expected

# -- Zba -----------------------------------------------------------------------

@pytest.mark.parametrize("insn,shift", [
  (dsl.SH1ADD, 1), (dsl.SH2ADD, 2), (dsl.SH3ADD, 3),
])
def test_shNadd(insn, shift):
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 5), dsl.ADDI(dsl.a1, dsl.zero, 100),
    insn(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == (5 << shift) + 100

# -- Zbb -----------------------------------------------------------------------

@pytest.mark.parametrize("insn,imm,expected", [
  (dsl.ZEXT_H, -1,   0xFFFF),      # 0xFFFFFFFF → keep low 16
  (dsl.SEXT_B, 0x80, 0xFFFFFF80),  # byte 0x80 → -128 sign-extended
  (dsl.SEXT_H, -256, 0xFFFFFF00),  # lower 16 = 0xFF00 → sign-extended
])
def test_zext_sext(insn, imm, expected):
  core = run([dsl.ADDI(dsl.a0, dsl.zero, imm), insn(dsl.a1, dsl.a0)])
  assert core.regs[dsl.a1] == expected

@pytest.mark.parametrize("imm,expected", [(8, 3), (1, 0), (0, 32)])
def test_ctz(imm, expected):
  core = run([dsl.ADDI(dsl.a0, dsl.zero, imm), dsl.CTZ(dsl.a1, dsl.a0)])
  assert core.regs[dsl.a1] == expected

def test_min():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -1),       # 0xFFFFFFFF = -1 signed
    dsl.ADDI(dsl.a1, dsl.zero, 1),
    dsl.MIN(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 0xFFFFFFFF     # -1 < 1 signed

def test_minu():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -1),       # 0xFFFFFFFF
    dsl.ADDI(dsl.a1, dsl.zero, 1),
    dsl.MINU(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 1              # 1 < 0xFFFFFFFF unsigned

def test_maxu():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 10), dsl.ADDI(dsl.a1, dsl.zero, 20),
    dsl.MAXU(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 20

# -- M extension: MULH, MULHSU, DIV, REM -------------------------------------

@pytest.mark.parametrize("insn,a,b,expected", [
  (dsl.MULH,   -1, -1, 0),           # (-1)*(-1)=1 → hi=0
  (dsl.MULH,   -1,  2, 0xFFFFFFFF),  # (-1)*2=-2 → hi=-1
  (dsl.MULHSU, -1,  2, 0xFFFFFFFF),  # signed -1 × unsigned 2 → hi=-1
])
def test_mulh_variants(insn, a, b, expected):
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, a), dsl.ADDI(dsl.a1, dsl.zero, b),
    insn(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == expected

@pytest.mark.parametrize("insn,a,b,expected", [
  (dsl.DIV, -7,  2, (-3) & 0xFFFFFFFF),  # -7/2 trunc = -3
  (dsl.DIV, 42,  0, 0xFFFFFFFF),          # div by zero → all ones
  (dsl.REM, -7,  2, (-1) & 0xFFFFFFFF),  # -7%2 = -1 (sign of dividend)
  (dsl.REM, 42,  0, 42),                  # rem by zero → dividend
])
def test_div_rem(insn, a, b, expected):
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, a), dsl.ADDI(dsl.a1, dsl.zero, b),
    insn(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == expected

@pytest.mark.parametrize("insn,expected", [
  (dsl.DIV, 0x80000000),  # -2^31 / -1 → overflow, returns -2^31
  (dsl.REM, 0),           # -2^31 % -1 → 0
])
def test_div_rem_overflow(insn, expected):
  core = run([
    dsl.LUI(dsl.a0, 0x80000000), dsl.ADDI(dsl.a1, dsl.zero, -1),
    insn(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == expected

# -- Zbb: MAX, CLZ, CPOP, ANDN, ORN, XNOR, ROL, ROR, RORI, REV8, ORC.B -----

def test_max():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -1),       # -1 signed
    dsl.ADDI(dsl.a1, dsl.zero, 1),
    dsl.MAX(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 1

@pytest.mark.parametrize("setup,expected", [
  ([dsl.ADDI(dsl.a0, dsl.zero, 1)],   31),  # only bit 0
  ([],                                 32),  # zero
  ([dsl.LUI(dsl.a0, 0x80000000)],      0),  # high bit
])
def test_clz(setup, expected):
  core = run(setup + [dsl.CLZ(dsl.a1, dsl.a0)])
  assert core.regs[dsl.a1] == expected

@pytest.mark.parametrize("imm,expected", [(0xFF, 8), (0, 0)])
def test_cpop(imm, expected):
  core = run([dsl.ADDI(dsl.a0, dsl.zero, imm), dsl.CPOP(dsl.a1, dsl.a0)])
  assert core.regs[dsl.a1] == expected

def test_andn():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 0xFF),
    dsl.ADDI(dsl.a1, dsl.zero, 0x0F),
    dsl.ANDN(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 0xF0

def test_orn():
  core = run([
    dsl.ADDI(dsl.a1, dsl.zero, -1),       # ~(-1) = 0
    dsl.ORN(dsl.a2, dsl.zero, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 0              # 0 | ~0xFFFFFFFF = 0

def test_xnor():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 0xFF),
    dsl.ADDI(dsl.a1, dsl.zero, 0xFF),
    dsl.XNOR(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 0xFFFFFFFF     # ~(x ^ x) = all ones

def test_rol():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 1),
    dsl.ADDI(dsl.a1, dsl.zero, 4),
    dsl.ROL(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 16             # 1 rotated left 4 = 16

def test_ror():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 1),
    dsl.ADDI(dsl.a1, dsl.zero, 1),
    dsl.ROR(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 0x80000000     # bit 0 wraps to bit 31

def test_rori():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 1),
    dsl.RORI(dsl.a1, dsl.a0, 1),
  ])
  assert core.regs[dsl.a1] == 0x80000000

def test_rev8():
  core = run([
    dsl.LUI(dsl.a0, 0x12345000),
    dsl.ADDI(dsl.a0, dsl.a0, 0x678),       # a0 = 0x12345678
    dsl.REV8(dsl.a1, dsl.a0),
  ])
  assert core.regs[dsl.a1] == 0x78563412

def test_orc_b():
  core = run([
    dsl.LUI(dsl.a0, 0x00FF0000),
    dsl.ADDI(dsl.a0, dsl.a0, 0x01),        # a0 = 0x00FF0001
    dsl.ORC_B(dsl.a1, dsl.a0),
  ])
  # byte 0: 0x01 != 0 → 0xFF, byte 1: 0x00 → 0x00, byte 2: 0xFF → 0xFF, byte 3: 0x00 → 0x00
  assert core.regs[dsl.a1] == 0x00FF00FF

# -- integration: kernel snippet -----------------------------------------------

def test_add1_brisc_zext_mulhu_sequence():
  magic = 0x92492493
  tile = 21
  base = 0x2000
  idx = 3
  core = run([
    # set up: a5 = some 32-bit value, simulate add + zext.h
    dsl.LUI(dsl.a5, 0x000F0000),
    dsl.ADDI(dsl.a4, dsl.zero, 0x05),
    dsl.ADD(dsl.a5, dsl.a5, dsl.a4),
    dsl.ZEXT_H(dsl.a5, dsl.a5),           # keep lower 16 bits
    # mulhu divide-by-7 pattern
    dsl.ADDI(dsl.s7, dsl.zero, tile),
    dsl.LUI(dsl.s3, magic & 0xFFFFF000),
    dsl.ADDI(dsl.s3, dsl.s3, (magic & 0xFFF) - (0x1000 if magic & 0x800 else 0)),
    dsl.MULHU(dsl.a5, dsl.s7, dsl.s3),
    dsl.SRLI(dsl.a5, dsl.a5, 2),          # a5 = tile / 7
    # sh2add for bank table lookup
    dsl.ADDI(dsl.a4, dsl.zero, idx),
    dsl.LUI(dsl.s3, base & 0xFFFFF000),
    dsl.SH2ADD(dsl.a3, dsl.a4, dsl.s3),
  ])
  assert core.regs[dsl.a5] == tile // 7      # 21 // 7 = 3
  assert core.regs[dsl.a3] == base + idx * 4
