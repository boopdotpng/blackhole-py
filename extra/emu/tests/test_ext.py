from emu.core import BRISC
from emu import dsl

def run(insns, n=None, pc=0x100):
  core = BRISC(pc=pc)
  core.load(pc, insns)
  core.run(n or len(insns))
  return core

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

def test_divu():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 42), dsl.ADDI(dsl.a1, dsl.zero, 5),
    dsl.DIVU(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 8

def test_divu_by_zero():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 42),
    dsl.DIVU(dsl.a1, dsl.a0, dsl.zero),
  ])
  assert core.regs[dsl.a1] == 0xFFFFFFFF

def test_remu():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 42), dsl.ADDI(dsl.a1, dsl.zero, 5),
    dsl.REMU(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 2

def test_remu_by_zero():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 42),
    dsl.REMU(dsl.a1, dsl.a0, dsl.zero),
  ])
  assert core.regs[dsl.a1] == 42

# -- Zba -----------------------------------------------------------------------

def test_sh1add():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 5), dsl.ADDI(dsl.a1, dsl.zero, 100),
    dsl.SH1ADD(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 5 * 2 + 100

def test_sh2add():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 5), dsl.ADDI(dsl.a1, dsl.zero, 100),
    dsl.SH2ADD(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 5 * 4 + 100

def test_sh3add():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 5), dsl.ADDI(dsl.a1, dsl.zero, 100),
    dsl.SH3ADD(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 5 * 8 + 100

def test_sh2add_address_calc():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 3),       # index
    dsl.LUI(dsl.a1, 0x1000),              # base = 0x1000
    dsl.SH2ADD(dsl.a2, dsl.a0, dsl.a1),  # addr = index*4 + base
  ])
  assert core.regs[dsl.a2] == 0x1000 + 3 * 4

# -- Zbb -----------------------------------------------------------------------

def test_zext_h():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -1),       # 0xFFFFFFFF
    dsl.ZEXT_H(dsl.a1, dsl.a0),
  ])
  assert core.regs[dsl.a1] == 0xFFFF

def test_zext_h_noop_small():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 0x42),
    dsl.ZEXT_H(dsl.a1, dsl.a0),
  ])
  assert core.regs[dsl.a1] == 0x42

def test_sext_b():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 0x80),     # 128 as byte = -128
    dsl.SEXT_B(dsl.a1, dsl.a0),
  ])
  assert core.regs[dsl.a1] == 0xFFFFFF80

def test_sext_b_positive():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 0x42),
    dsl.SEXT_B(dsl.a1, dsl.a0),
  ])
  assert core.regs[dsl.a1] == 0x42

def test_sext_h():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -256),     # 0xFFFFFF00, lower 16 = 0xFF00
    dsl.SEXT_H(dsl.a1, dsl.a0),
  ])
  # lower 16 bits = 0xFF00 → sign-extend → 0xFFFFFF00
  assert core.regs[dsl.a1] == 0xFFFFFF00

def test_ctz():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 8),        # 0b1000 → 3 trailing zeros
    dsl.CTZ(dsl.a1, dsl.a0),
  ])
  assert core.regs[dsl.a1] == 3

def test_ctz_one():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 1),
    dsl.CTZ(dsl.a1, dsl.a0),
  ])
  assert core.regs[dsl.a1] == 0

def test_ctz_zero():
  core = run([dsl.CTZ(dsl.a0, dsl.zero)])
  assert core.regs[dsl.a0] == 32

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

def test_mulh():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -1),       # 0xFFFFFFFF = -1
    dsl.ADDI(dsl.a1, dsl.zero, -1),
    dsl.MULH(dsl.a2, dsl.a0, dsl.a1),
  ])
  # (-1) * (-1) = 1 → upper 32 bits = 0
  assert core.regs[dsl.a2] == 0

def test_mulh_negative():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -1),       # -1
    dsl.ADDI(dsl.a1, dsl.zero, 2),
    dsl.MULH(dsl.a2, dsl.a0, dsl.a1),
  ])
  # (-1) * 2 = -2 → upper 32 bits = -1 = 0xFFFFFFFF
  assert core.regs[dsl.a2] == 0xFFFFFFFF

def test_mulhsu():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -1),       # signed -1
    dsl.ADDI(dsl.a1, dsl.zero, 2),         # unsigned 2
    dsl.MULHSU(dsl.a2, dsl.a0, dsl.a1),
  ])
  # (-1) * 2 = -2 → upper 32 bits = -1 = 0xFFFFFFFF
  assert core.regs[dsl.a2] == 0xFFFFFFFF

def test_mulhsu_positive():
  core = run([
    dsl.LUI(dsl.a0, 0x10000000), dsl.ADDI(dsl.a1, dsl.zero, 16),
    dsl.MULHSU(dsl.a2, dsl.a0, dsl.a1),
  ])
  # 0x10000000 * 16 = 0x1_0000_0000 → upper 32 = 1
  assert core.regs[dsl.a2] == 1

def test_div():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -7),       # -7
    dsl.ADDI(dsl.a1, dsl.zero, 2),
    dsl.DIV(dsl.a2, dsl.a0, dsl.a1),
  ])
  # -7 / 2 = -3 (truncate toward zero)
  assert core.regs[dsl.a2] == (-3) & 0xFFFFFFFF

def test_div_by_zero():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 42),
    dsl.DIV(dsl.a1, dsl.a0, dsl.zero),
  ])
  assert core.regs[dsl.a1] == 0xFFFFFFFF

def test_div_overflow():
  core = run([
    dsl.LUI(dsl.a0, 0x80000000),          # -2^31
    dsl.ADDI(dsl.a1, dsl.zero, -1),
    dsl.DIV(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 0x80000000

def test_rem():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -7),       # -7
    dsl.ADDI(dsl.a1, dsl.zero, 2),
    dsl.REM(dsl.a2, dsl.a0, dsl.a1),
  ])
  # -7 % 2 = -1 (sign follows dividend)
  assert core.regs[dsl.a2] == (-1) & 0xFFFFFFFF

def test_rem_by_zero():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, 42),
    dsl.REM(dsl.a1, dsl.a0, dsl.zero),
  ])
  assert core.regs[dsl.a1] == 42

def test_rem_overflow():
  core = run([
    dsl.LUI(dsl.a0, 0x80000000),
    dsl.ADDI(dsl.a1, dsl.zero, -1),
    dsl.REM(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 0

# -- Zbb: MAX, CLZ, CPOP, ANDN, ORN, XNOR, ROL, ROR, RORI, REV8, ORC.B -----

def test_max():
  core = run([
    dsl.ADDI(dsl.a0, dsl.zero, -1),       # -1 signed
    dsl.ADDI(dsl.a1, dsl.zero, 1),
    dsl.MAX(dsl.a2, dsl.a0, dsl.a1),
  ])
  assert core.regs[dsl.a2] == 1

def test_clz():
  core = run([dsl.ADDI(dsl.a0, dsl.zero, 1), dsl.CLZ(dsl.a1, dsl.a0)])
  assert core.regs[dsl.a1] == 31

def test_clz_zero():
  core = run([dsl.CLZ(dsl.a0, dsl.zero)])
  assert core.regs[dsl.a0] == 32

def test_clz_high_bit():
  core = run([dsl.LUI(dsl.a0, 0x80000000), dsl.CLZ(dsl.a1, dsl.a0)])
  assert core.regs[dsl.a1] == 0

def test_cpop():
  core = run([dsl.ADDI(dsl.a0, dsl.zero, 0xFF), dsl.CPOP(dsl.a1, dsl.a0)])
  assert core.regs[dsl.a1] == 8

def test_cpop_zero():
  core = run([dsl.CPOP(dsl.a0, dsl.zero)])
  assert core.regs[dsl.a0] == 0

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
