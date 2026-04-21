from emu.core import BRISC
from emu import dsl
from emu.rvir import *

def run(k, n=1000, pc=0x100):
  core = BRISC(pc=pc)
  core.load(pc, k)
  core.run(n)
  return core

def run_full(k, n=1000, pc=0x100):
  """Load both text and .data (data goes at k._data_base)."""
  core = BRISC(pc=pc)
  text, data = k.assemble_full()
  for i, w in enumerate(text):
    core.mem.write32(pc + i*4, w)
  for i in range(0, len(data), 4):
    core.mem.write32(k._data_base + i, int.from_bytes(data[i:i+4], 'little'))
  core.run(n)
  return core

# =============================================================================
# li — 32-bit immediate loading
# =============================================================================
def test_li_small_positive():
  k = Kernel()
  k.li(a0, 42)
  assert len(k) == 1
  core = run(k)
  assert core.regs[a0] == 42

def test_li_small_negative():
  k = Kernel()
  k.li(a0, -1)
  assert len(k) == 1
  core = run(k)
  assert core.regs[a0] == 0xFFFFFFFF

def test_li_large():
  k = Kernel()
  k.li(a0, 0xFFE40000)
  assert len(k) == 1  # upper bits only, no lower
  core = run(k)
  assert core.regs[a0] == 0xFFE40000

def test_li_needs_both():
  k = Kernel()
  k.li(a0, 0x12345678)
  assert len(k) == 2  # LUI + ADDI
  core = run(k)
  assert core.regs[a0] == 0x12345678

def test_li_sign_extension_edge():
  k = Kernel()
  k.li(a0, 0xDEADBEEF)
  core = run(k)
  assert core.regs[a0] == 0xDEADBEEF

def test_li_zero():
  k = Kernel()
  k.li(a0, 0)
  assert len(k) == 1
  core = run(k)
  assert core.regs[a0] == 0

def test_li_max_unsigned():
  k = Kernel()
  k.li(a0, 0xFFFFFFFF)
  assert len(k) == 1  # ADDI(rd, zero, -1)
  core = run(k)
  assert core.regs[a0] == 0xFFFFFFFF

def test_li_0x800():
  k = Kernel()
  k.li(a0, 0x800)
  core = run(k)
  assert core.regs[a0] == 0x800

def test_li_negative_2048():
  k = Kernel()
  k.li(a0, -2048)
  assert len(k) == 1
  core = run(k)
  assert core.regs[a0] == 0xFFFFF800

# =============================================================================
# Labels and branches
# =============================================================================
def test_label_backward_branch():
  k = Kernel()
  k.li(a0, 3)
  k.li(a1, 0)
  k.label("loop")
  k.emit(ADD(a1, a1, a0))
  k.emit(ADDI(a0, a0, -1))
  k.bnez(a0, "loop")
  core = run(k)
  assert core.regs[a1] == 6  # 3 + 2 + 1

def test_label_forward_branch():
  k = Kernel()
  k.li(a0, 0)
  k.beqz(a0, "skip")
  k.li(a0, 99)  # should be skipped
  k.label("skip")
  k.li(a1, 42)
  core = run(k)
  assert core.regs[a0] == 0
  assert core.regs[a1] == 42

def test_j_forward():
  k = Kernel()
  k.j("target")
  k.li(a0, 99)  # skipped
  k.label("target")
  k.li(a0, 42)
  core = run(k)
  assert core.regs[a0] == 42

def test_call_and_ret():
  k = Kernel()
  k.call("myfunc")
  k.j("done")

  k.label("myfunc")
  k.li(a0, 77)
  k.ret()

  k.label("done")
  core = run(k)
  assert core.regs[a0] == 77

def test_all_branch_types():
  # blt: 5 < 10 → should branch
  k = Kernel()
  k.li(a0, 5)
  k.li(a1, 10)
  k.li(a2, 0)
  k.blt(a0, a1, "taken")
  k.li(a2, 1)  # not taken
  k.label("taken")
  core = run(k)
  assert core.regs[a2] == 0  # branch was taken, skipped li

  # bge: 10 >= 5 → should branch
  k = Kernel()
  k.li(a0, 10)
  k.li(a1, 5)
  k.li(a2, 0)
  k.bge(a0, a1, "taken2")
  k.li(a2, 1)
  k.label("taken2")
  core = run(k)
  assert core.regs[a2] == 0

def test_bltz_bgez():
  k = Kernel()
  k.li(a0, -5)
  k.li(a1, 0)
  k.bltz(a0, "neg")
  k.li(a1, 99)
  k.label("neg")
  core = run(k)
  assert core.regs[a1] == 0  # branch taken

# =============================================================================
# Fixup — general deferred resolution
# =============================================================================
def test_fixup_basic():
  k = Kernel()
  k.label("start")
  k.li(a0, 0)
  k.li(a1, 0)
  # fixup: encode the byte distance from here to "start" into a2
  k.fixup(
    lambda pc, L: int(ADDI(a2, zero, pc - L["start"])),
    desc="distance to start")
  core = run(k)
  # start is at pc=0x100, the fixup is the 3rd instruction at 0x108
  assert core.regs[a2] == 8  # 0x108 - 0x100

# =============================================================================
# __getattr__ fallthrough to dsl
# =============================================================================
def test_getattr_add():
  k = Kernel()
  k.li(a0, 10)
  k.li(a1, 20)
  k.add(a2, a0, a1)
  core = run(k)
  assert core.regs[a2] == 30

def test_getattr_lw_sw():
  k = Kernel()
  k.li(a0, 0x42)
  k.li(a1, 0x1000)
  k.sw(a1, a0, 0)
  k.lw(a2, a1, 0)
  core = run(k)
  assert core.regs[a2] == 0x42

def test_getattr_mv():
  k = Kernel()
  k.li(a0, 99)
  k.mv(a1, a0)
  core = run(k)
  assert core.regs[a1] == 99

def test_getattr_slli():
  k = Kernel()
  k.li(a0, 1)
  k.slli(a1, a0, 4)
  core = run(k)
  assert core.regs[a1] == 16

def test_getattr_nop():
  k = Kernel()
  k.nop()
  assert len(k) == 1

def test_getattr_ret():
  k = Kernel()
  k.ret()
  assert len(k) == 1

def test_getattr_mulhu():
  k = Kernel()
  k.li(a0, 0x80000000)
  k.li(a1, 4)
  k.mulhu(a2, a0, a1)
  core = run(k)
  assert core.regs[a2] == 2  # (0x80000000 * 4) >> 32

def test_getattr_sh2add():
  k = Kernel()
  k.li(a0, 3)
  k.li(a1, 100)
  k.sh2add(a2, a0, a1)  # a2 = 100 + (3 << 2) = 112
  core = run(k)
  assert core.regs[a2] == 112

def test_getattr_invalid():
  k = Kernel()
  try:
    k.nonexistent_instruction()
    assert False, "should have raised"
  except AttributeError:
    pass

# =============================================================================
# Tensix instruction encoding
# =============================================================================
def test_tt_nop():
  k = Kernel()
  k.tt(TT_NOP())
  words = k.assemble()
  assert len(words) == 1
  # TT_NOP = opcode 0x02, params 0 → raw = 0x02000000
  # TTINSN rotates left 2: (0x02000000 << 2) | (0x02000000 >> 30) = 0x08000000
  assert words[0] == 0x08000000

def test_tensix_op_rejects_extra_args():
  try:
    TT_ATGETM(0, 1)
    assert False, "should have rejected extra positional arg"
  except TypeError:
    pass

  try:
    TT_ATGETM(mutex_index=0, extra=1)
    assert False, "should have rejected unexpected keyword arg"
  except TypeError:
    pass

  try:
    TT_ATGETM(0, mutex_index=1)
    assert False, "should have rejected duplicate arg"
  except TypeError:
    pass

def test_emit_auto_wraps_tensix():
  k = Kernel()
  k.emit(TT_NOP())
  words = k.assemble()
  assert words[0] == 0x08000000

def test_getattr_tensix():
  k = Kernel()
  k.tt_nop()
  words = k.assemble()
  assert words[0] == 0x08000000

def test_tt_seminit():
  k = Kernel()
  k.tt(TT_SEMINIT(max_value=2, init_value=0, sem_sel=2))
  words = k.assemble()
  # verify it assembles to a single word
  assert len(words) == 1
  # decode it back through TTINSN inverse: rotate right 2
  w = words[0]
  raw = ((w >> 2) | (w << 30)) & 0xFFFFFFFF
  assert (raw >> 24) == 0xA3  # SEMINIT opcode

# =============================================================================
# countdown loop
# =============================================================================
def test_countdown():
  k = Kernel()
  k.li(a1, 0)
  with k.countdown(a0, 5):
    k.add(a1, a1, a0)
  core = run(k)
  assert core.regs[a1] == 15

def test_countdown_zero_trip():
  k = Kernel()
  k.li(a1, 0)
  with k.countdown(a0, 0):
    k.addi(a1, a1, 1)
  core = run(k)
  assert core.regs[a1] == 0

def test_countdown_zero_trip_from_register():
  k = Kernel()
  k.li(a0, 0)
  k.li(a1, 0)
  with k.countdown(a0, count=None):
    k.addi(a1, a1, 1)
  core = run(k)
  assert core.regs[a1] == 0

def test_countdown_from_register():
  k = Kernel()
  k.li(a0, 4)
  k.li(a1, 0)
  k.mv(a2, a0)
  with k.countdown(a2, count=None):
    k.add(a1, a1, a2)
  core = run(k)
  assert core.regs[a1] == 10  # 4+3+2+1

def test_countdown_break():
  k = Kernel()
  k.li(a1, 0)
  with k.countdown(a0, 10) as L:
    k.add(a1, a1, a0)
    # break when a0 reaches 7 (after add, before decrement)
    k.li(t0, 7)
    k.beq(a0, t0, L.brk)
  core = run(k)
  # iter 1: a0=10, a1=10, beq not taken, a0→9
  # iter 2: a0=9,  a1=19, beq not taken, a0→8
  # iter 3: a0=8,  a1=27, beq not taken, a0→7
  # iter 4: a0=7,  a1=34, beq TAKEN → break
  assert core.regs[a1] == 10 + 9 + 8 + 7

# =============================================================================
# countup loop
# =============================================================================
def test_countup():
  k = Kernel()
  k.li(a1, 0)
  k.li(a2, 4)  # limit
  with k.countup(a0, limit=a2):
    k.add(a1, a1, a0)
  core = run(k)
  assert core.regs[a1] == 6  # 0+1+2+3

def test_countup_with_start():
  k = Kernel()
  k.li(a1, 0)
  k.li(a2, 5)
  with k.countup(a0, limit=a2, start=2):
    k.add(a1, a1, a0)
  core = run(k)
  assert core.regs[a1] == 9  # 2+3+4

def test_countup_zero_trip():
  k = Kernel()
  k.li(a1, 0)
  k.li(a2, 5)
  with k.countup(a0, limit=a2, start=5):
    k.addi(a1, a1, 1)
  core = run(k)
  assert core.regs[a1] == 0

# =============================================================================
# while_true loop
# =============================================================================
def test_while_true():
  k = Kernel()
  k.li(a0, 5)
  k.li(a1, 0)
  with k.while_true() as L:
    k.beqz(a0, L.brk)       # check BEFORE add
    k.add(a1, a1, a0)
    k.addi(a0, a0, -1)
  core = run(k)
  assert core.regs[a1] == 15  # 5+4+3+2+1

# =============================================================================
# func — prologue/epilogue
# =============================================================================
def test_func_saves_and_restores():
  k = Kernel()
  # Set up known values in s0, s1
  k.li(s0, 0xAAAA)
  k.li(s1, 0xBBBB)
  k.li(sp, 0x2000)  # stack pointer
  k.call("myfunc")
  k.j("end")

  with k.func("myfunc", saves=[s0, s1]):
    # trash s0, s1 inside the function
    k.li(s0, 0x1111)
    k.li(s1, 0x2222)
    k.li(a0, 42)  # return value in a0

  k.label("end")
  core = run(k)
  # s0, s1 should be restored
  assert core.regs[s0] == 0xAAAA
  assert core.regs[s1] == 0xBBBB
  # a0 should have the value set inside the function
  assert core.regs[a0] == 42

def test_func_frame_alignment():
  k = Kernel()
  k.li(sp, 0x2000)
  # 3 regs (ra + s0 + s1) = 12 bytes → aligned to 16
  with k.func(saves=[s0, s1]):
    # sp inside should be 0x2000 - 16 = 0x1FF0
    k.mv(a0, sp)
  core = run(k, n=50)
  assert core.regs[a0] == 0x2000 - 16

def test_func_with_name():
  k = Kernel()
  k.li(sp, 0x2000)
  k.call("add_ten")
  k.j("end")

  with k.func("add_ten"):
    k.addi(a0, a0, 10)

  k.label("end")
  k.li(a0, 5)
  k.call("add_ten")
  k.j("done")
  k.label("done")

  # This is tricky — the function gets called twice.
  # First call: a0=0 → a0=10, then we jump to end, set a0=5, call again → a0=15
  core = run(k, n=50)
  assert core.regs[a0] == 15

# =============================================================================
# sw_imm convenience
# =============================================================================
def test_sw_imm():
  k = Kernel()
  k.li(a0, 0x1000)
  k.sw_imm(0xDEAD, a0, 0)
  k.lw(a1, a0, 0)
  core = run(k)
  assert core.regs[a1] == 0xDEAD

# =============================================================================
# emit chaining
# =============================================================================
def test_emit_chaining():
  k = Kernel()
  k.emit(ADDI(a0, zero, 1), ADDI(a1, zero, 2), ADD(a2, a0, a1))
  core = run(k)
  assert core.regs[a2] == 3

# =============================================================================
# iteration / core.load compatibility
# =============================================================================
def test_iter_yields_ints():
  k = Kernel()
  k.li(a0, 42)
  words = list(k)
  assert all(isinstance(w, int) for w in words)
  assert len(words) == 1

def test_core_load_direct():
  core = BRISC(pc=0x100)
  k = Kernel()
  k.li(a0, 77)
  core.load(0x100, k)
  core.run(5)
  assert core.regs[a0] == 77

# =============================================================================
# base address support
# =============================================================================
def test_base_address():
  k = Kernel(base=0x6290)
  k.li(a0, 0)
  k.beqz(a0, "skip")
  k.li(a0, 99)
  k.label("skip")
  k.li(a1, 42)
  # assemble and verify branch offset is correct
  words = k.assemble()
  core = BRISC(pc=0x6290)
  core.load(0x6290, k)
  core.run(10)
  assert core.regs[a0] == 0
  assert core.regs[a1] == 42

# =============================================================================
# word (raw data)
# =============================================================================
def test_word():
  k = Kernel()
  k.word(0xDEADBEEF)
  words = k.assemble()
  assert words[0] == 0xDEADBEEF

# =============================================================================
# error cases
# =============================================================================
def test_duplicate_label_raises():
  k = Kernel()
  k.label("foo")
  k.nop()
  k.label("foo")
  try:
    k.assemble()
    assert False, "should have raised"
  except ValueError as e:
    assert "duplicate" in str(e)

def test_missing_label_raises():
  k = Kernel()
  k.j("nowhere")
  try:
    k.assemble()
    assert False, "should have raised"
  except KeyError:
    pass

# =============================================================================
# Integration: realistic kernel-like sequence
# =============================================================================
def test_integration_dram_bank_calc():
  k = Kernel()
  tile_id = 20
  magic = 0x92492493  # ceil(2^34 / 7)

  k.li(s7, tile_id)
  k.li(s3, magic)
  k.mulhu(a5, s7, s3)
  k.srli(a5, a5, 2)        # a5 = tile_id / 7
  k.slli(a4, a5, 3)
  k.sub(a4, a4, a5)         # a4 = quotient * 7
  k.sub(a4, s7, a4)         # a4 = tile_id % 7

  core = run(k)
  assert core.regs[a5] == 20 // 7  # 2
  assert core.regs[a4] == 20 % 7   # 6

def test_integration_memcpy_loop():
  k = Kernel()
  src, dst = 0x1000, 0x2000
  k.li(s0, src)
  k.li(s1, dst)
  with k.countdown(s2, 4):
    k.lw(t0, s0, 0)
    k.sw(s1, t0, 0)
    k.addi(s0, s0, 4)
    k.addi(s1, s1, 4)

  core = BRISC(pc=0x100)
  # write source data
  for i in range(4):
    core.mem.write32(src + i*4, 0xA0 + i)
  core.load(0x100, k)
  core.run(1000)
  # verify copy
  for i in range(4):
    assert core.mem.read32(dst + i*4) == 0xA0 + i

def test_integration_nested_loops():
  k = Kernel()
  k.li(a0, 0)
  with k.countdown(s0, 3):     # outer: 3 iterations
    with k.countdown(s1, 4):   # inner: 4 iterations
      k.addi(a0, a0, 1)
  core = run(k)
  assert core.regs[a0] == 12  # 3 * 4

# =============================================================================
# la — load absolute address of label (text or data)
# =============================================================================
def test_la_text_label():
  k = Kernel(base=0x100)
  k.la(a0, "target")
  k.j("end")
  k.label("target")
  k.li(a1, 1)
  k.label("end")
  core = run(k)
  # la=2 insns, j=1 insn, so "target" label is at 0x100 + 3*4 = 0x10C
  assert core.regs[a0] == 0x10C

def test_la_data_label():
  k = Kernel(base=0x100)
  k.la(a0, "mydata")
  k.data_label("mydata")
  k.data_word(0xDEADBEEF)
  core = run(k, n=5)
  assert core.regs[a0] == LDM_BASE

def test_la_loads_data_value():
  k = Kernel(base=0x100)
  k.la(a0, "mydata")
  k.lw(a1, a0, 0)
  k.data_label("mydata")
  k.data_word(0xCAFEBABE)
  core = run_full(k)
  assert core.regs[a1] == 0xCAFEBABE

# =============================================================================
# data section basics
# =============================================================================
def test_data_words_layout():
  k = Kernel()
  k.data_words(0x11111111, 0x22222222, 0x33333333)
  data = k.data()
  assert data == bytes.fromhex('11111111') + bytes.fromhex('22222222') + bytes.fromhex('33333333')

def test_data_bytes_padding():
  k = Kernel()
  k.data_bytes(b'abc')
  assert k.data() == b'abc\x00'

def test_data_label_resolves_to_ldm_addr():
  k = Kernel()
  k.data_word(0)
  k.data_label("here")
  k.data_word(0)
  labels = k._resolve_labels()
  assert labels["here"] == LDM_BASE + 4

def test_assemble_full_returns_both():
  k = Kernel()
  k.li(a0, 1)
  k.data_word(0xAA)
  text, data = k.assemble_full()
  assert len(text) == 1
  assert data == bytes.fromhex('AA000000')

# =============================================================================
# if_ / else_
# =============================================================================
def test_if_eqz_taken():
  k = Kernel()
  k.li(a0, 0)
  k.li(a1, 0)
  with k.if_('eqz', a0):
    k.li(a1, 42)
  core = run(k)
  assert core.regs[a1] == 42

def test_if_eqz_not_taken():
  k = Kernel()
  k.li(a0, 1)
  k.li(a1, 0)
  with k.if_('eqz', a0):
    k.li(a1, 42)
  core = run(k)
  assert core.regs[a1] == 0

def test_if_else_then_branch():
  k = Kernel()
  k.li(a0, 5)
  k.li(a1, 0)
  with k.if_('eq', a0, zero) as c:
    k.li(a1, 1)
    with c.else_():
      k.li(a1, 2)
  core = run(k)
  assert core.regs[a1] == 2

def test_if_else_else_branch():
  k = Kernel()
  k.li(a0, 0)
  k.li(a1, 0)
  with k.if_('eq', a0, zero) as c:
    k.li(a1, 1)
    with c.else_():
      k.li(a1, 2)
  core = run(k)
  assert core.regs[a1] == 1

def test_if_lt_vs_ge():
  k = Kernel()
  k.li(a0, 3)
  k.li(a1, 10)
  k.li(a2, 0)
  with k.if_('lt', a0, a1) as c:
    k.li(a2, 100)
    with c.else_():
      k.li(a2, 200)
  core = run(k)
  assert core.regs[a2] == 100

def test_if_nez_skips_body():
  k = Kernel()
  k.li(a0, 0)
  k.li(a1, 99)
  with k.if_('nez', a0):
    k.li(a1, 0)
  core = run(k)
  assert core.regs[a1] == 99

def test_if_nested():
  k = Kernel()
  k.li(a0, 1)
  k.li(a1, 1)
  k.li(a2, 0)
  with k.if_('nez', a0):
    with k.if_('nez', a1):
      k.li(a2, 42)
  core = run(k)
  assert core.regs[a2] == 42

def test_if_double_else_raises():
  k = Kernel()
  k.li(a0, 0)
  try:
    with k.if_('eqz', a0) as c:
      with c.else_():
        pass
      with c.else_():
        pass
    assert False, "should have raised"
  except RuntimeError as e:
    assert "else_" in str(e)

def test_if_unknown_cond():
  k = Kernel()
  try:
    with k.if_('bogus', a0):
      pass
    assert False
  except ValueError:
    pass

# =============================================================================
# jumptable
# =============================================================================
def test_jumptable_basic():
  k = Kernel(base=0x100)
  k.li(a0, 2)            # cmd
  with k.jumptable(a0, n=3) as jt:
    with jt.case(0):
      k.li(a1, 100)
      k.j("done")
    with jt.case(1):
      k.li(a1, 200)
      k.j("done")
    with jt.case(2):
      k.li(a1, 300)
      k.j("done")
  k.label("done")
  core = run_full(k)
  assert core.regs[a1] == 300

def test_jumptable_case_0():
  k = Kernel(base=0x100)
  k.li(a0, 0)
  with k.jumptable(a0, n=3) as jt:
    with jt.case(0):
      k.li(a1, 111)
      k.j("done")
    with jt.case(1):
      k.li(a1, 222)
      k.j("done")
    with jt.case(2):
      k.li(a1, 333)
      k.j("done")
  k.label("done")
  core = run_full(k)
  assert core.regs[a1] == 111

def test_jumptable_bias():
  k = Kernel(base=0x100)
  k.li(a0, 8)            # biased by 7 → idx 1
  with k.jumptable(a0, n=3, bias=7) as jt:
    with jt.case(0):
      k.li(a1, 10)
      k.j("done")
    with jt.case(1):
      k.li(a1, 20)
      k.j("done")
    with jt.case(2):
      k.li(a1, 30)
      k.j("done")
  k.label("done")
  core = run_full(k)
  assert core.regs[a1] == 20

def test_jumptable_default():
  k = Kernel(base=0x100)
  k.li(a0, 3)            # unfilled slot → default
  with k.jumptable(a0, n=5, default="bad") as jt:
    with jt.case(0):
      k.li(a1, 1)
      k.j("done")
    with jt.case(2):
      k.li(a1, 2)
      k.j("done")
  k.j("done")
  k.label("bad")
  k.li(a1, 999)
  k.label("done")
  core = run_full(k)
  assert core.regs[a1] == 999

def test_jumptable_multi_case():
  k = Kernel(base=0x100)
  k.li(a0, 2)
  with k.jumptable(a0, n=4) as jt:
    with jt.case(0, 1, 2):     # shared body
      k.li(a1, 7)
      k.j("done")
    with jt.case(3):
      k.li(a1, 8)
      k.j("done")
  k.label("done")
  core = run_full(k)
  assert core.regs[a1] == 7

def test_jumptable_missing_slot_raises():
  k = Kernel(base=0x100)
  k.li(a0, 0)
  try:
    with k.jumptable(a0, n=3) as jt:
      with jt.case(0):
        k.j("done")
    assert False, "should have raised"
  except ValueError as e:
    assert "not emitted" in str(e)

def test_jumptable_duplicate_case():
  k = Kernel(base=0x100)
  k.li(a0, 0)
  try:
    with k.jumptable(a0, n=2) as jt:
      with jt.case(0): k.nop()
      with jt.case(0): k.nop()
    assert False
  except ValueError as e:
    assert "duplicate" in str(e)
