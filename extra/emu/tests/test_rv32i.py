from emu.core import BRISC, NCRISC, TRISC0, TRISC1, TRISC2
from emu.memory import Memory
from emu import memory as M
from emu import dsl


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

def test_x0_immutable():
  core = run([dsl.ADDI(dsl.zero, dsl.zero, 99)])
  assert core.regs[0] == 0

def test_ldm_isolation():
  shared = Memory()
  a, b = BRISC(l1=shared, pc=0x100), TRISC0(l1=shared, pc=0x100)
  a.ldm.write32(0, 0xAAAA); b.ldm.write32(0, 0xBBBB)
  assert a.mem.read32(0xFFB00000) == 0xAAAA
  assert b.mem.read32(0xFFB00000) == 0xBBBB
  a.mem.write32(0x1000, 0xDEAD)
  assert b.mem.read32(0x1000) == 0xDEAD

def test_ldm_slow_path_read():
  shared = Memory()
  cores = [BRISC(l1=shared), NCRISC(l1=shared),
      TRISC0(l1=shared), TRISC1(l1=shared), TRISC2(l1=shared)]
  _attach_slow_ldm(cores)

  # Each core writes a marker to its own LDM (via own-LDM registration)
  for i, c in enumerate(cores):
    c.ldm.write32(0, 0xAA00 + i)

  # Every core can read every other core's LDM via slow path
  slow_bases = [M.LDM_SLOW_BRISC, M.LDM_SLOW_NCRISC,
         M.LDM_SLOW_TRISC0, M.LDM_SLOW_TRISC1, M.LDM_SLOW_TRISC2]
  for reader in cores:
    for j, base in enumerate(slow_bases):
      assert reader.mem.read32(base) == 0xAA00 + j

def test_ldm_slow_path_write():
  shared = Memory()
  brisc  = BRISC(l1=shared)
  ncrisc = NCRISC(l1=shared)
  trisc0 = TRISC0(l1=shared)
  trisc1 = TRISC1(l1=shared)
  trisc2 = TRISC2(l1=shared)
  _attach_slow_ldm([brisc, ncrisc, trisc0, trisc1, trisc2])
  # NCRISC writes to BRISC's LDM via slow path
  ncrisc.mem.write32(M.LDM_SLOW_BRISC + 0x100, 0xDEAD)
  # BRISC sees it via fast path
  assert brisc.mem.read32(M.LDM_BASE + 0x100) == 0xDEAD

def test_ldm_slow_path_padding():
  shared = Memory()
  brisc  = BRISC(l1=shared)
  ncrisc = NCRISC(l1=shared)
  trisc0 = TRISC0(l1=shared)
  trisc1 = TRISC1(l1=shared)
  trisc2 = TRISC2(l1=shared)
  fallback = _attach_slow_ldm([brisc, ncrisc, trisc0, trisc1, trisc2])
  # TRISC0 has 4K LDM — upper 4K of its 8K slot is unmapped padding
  brisc.mem.write32(M.LDM_SLOW_TRISC0 + 0x1000, 0xBAD)
  assert trisc0.ldm.read32(0x1000) == 0  # not in TRISC0's LDM
  assert fallback.read32(M.LDM_SLOW_TRISC0 + 0x1000) == 0xBAD

# -- address map routing ---------------------------------------------------

def test_router_dispatches_ranges():
  core = BRISC(pc=0x100)
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

def test_router_default_fallback():
  core = BRISC(pc=0x100)
  core.mem.write32(0xDEADBEE0, 0xCAFEBABE)
  assert core.mem.read32(0xDEADBEE0) == 0xCAFEBABE
  # Standalone default is a plain Memory — verify it received the write.
  assert core.mem.default.read32(0xDEADBEE0) == 0xCAFEBABE


def test_router_per_core_dispatch():
  from emu.core import TRISC0, TRISC1, TRISC2
  shared = Memory()
  brisc  = BRISC(l1=shared)
  trisc0 = TRISC0(l1=shared)
  trisc1 = TRISC1(l1=shared)
  trisc2 = TRISC2(l1=shared)
  log = []

  class _RoleLogger:
    def __init__(self, role): self.role = role
    def read8(self, addr):  return 0
    def read16(self, addr): return 0
    def read32(self, addr): return 0
    def write8(self, addr, val):  pass
    def write16(self, addr, val): pass
    def write32(self, addr, val): log.append((self.role, addr, val))

  for c in [brisc, trisc0, trisc1, trisc2]:
    c.mem.register(M.INSTRN_BUF_T0, M.INSTRN_BUF_END, _RoleLogger(c.ROLE))

  brisc.mem.write32(M.INSTRN_BUF_T1, 0xDEAD)
  trisc0.mem.write32(M.INSTRN_BUF_T0, 0xBEEF)
  trisc2.mem.write32(M.INSTRN_BUF_T0, 0xCAFE)
  assert log == [
    ('brisc',  M.INSTRN_BUF_T1, 0xDEAD),
    ('trisc0', M.INSTRN_BUF_T0, 0xBEEF),
    ('trisc2', M.INSTRN_BUF_T0, 0xCAFE),
  ]
