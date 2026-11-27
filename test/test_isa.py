import struct, unittest
from hw import isa as hw_isa
from compiler import (
  BlackholeRenderer, GroupOp, KernelArg, L0, L1, L2, L3, LCONST, LOCAL_BASE, Ops,
  ROLES, RV32Renderer, RVGroupOp, RVOps, SfpSpec, Tensor, TensixGroupOp, TensixOps,
  UOp, UPat, Variable, X, X0, dtypes, fix_sfpu_hazards_uops, line_rewrite,
  linearize, pack_bundle, render_uir, sfp_ins, split_roles, to_program, tt_ins, unpack_bundle,
)

# ---- Minimal RV32IM emulator to execute assembled UOp.ins binaries in unit tests ----

def _sext(val: int, bits: int) -> int:
  m = 1 << (bits - 1)
  return (val & (m - 1)) - (val & m)

def run_rv32(code: bytes, regs_init: dict[int, int] | None = None, mem: bytearray | None = None, max_steps: int = 50_000,
             on_call=None) -> tuple[list[int], bytearray]:
  r = [0] * 32
  if regs_init:
    for k, v in regs_init.items(): r[k] = v & 0xFFFFFFFF
  r[1] = 0xFFFFFFFC  # return sentinel in ra (x1)
  memory = bytearray(4096) if mem is None else mem
  pc = 0
  for _ in range(max_steps):
    if pc == 0xFFFFFFFC: break
    assert 0 <= pc < len(code) and pc % 4 == 0, f"bad pc {pc:#x}"
    w = struct.unpack_from("<I", code, pc)[0]
    opc = w & 0x7F
    rd = (w >> 7) & 0x1F
    f3 = (w >> 12) & 0x7
    rs1 = (w >> 15) & 0x1F
    rs2 = (w >> 20) & 0x1F
    f7 = (w >> 25) & 0x7F
    nxt = pc + 4
    if opc == 0x37:  # LUI
      r[rd] = w & 0xFFFFF000
    elif opc == 0x13:  # OP-IMM
      imm = _sext(w >> 20, 12)
      a = r[rs1]
      if f3 == 0: r[rd] = (a + imm) & 0xFFFFFFFF
      elif f3 == 2: r[rd] = int(_sext(a, 32) < imm)
      elif f3 == 3: r[rd] = int(a < (imm & 0xFFFFFFFF))
      elif f3 == 4: r[rd] = (a ^ (imm & 0xFFFFFFFF)) & 0xFFFFFFFF
      elif f3 == 6: r[rd] = (a | (imm & 0xFFFFFFFF)) & 0xFFFFFFFF
      elif f3 == 7: r[rd] = (a & (imm & 0xFFFFFFFF)) & 0xFFFFFFFF
      elif f3 == 1: r[rd] = (a << (rs2 & 0x1F)) & 0xFFFFFFFF
      elif f3 == 5: r[rd] = ((_sext(a, 32) >> (rs2 & 0x1F)) & 0xFFFFFFFF) if (f7 & 0x20) else (a >> (rs2 & 0x1F))
      else: raise AssertionError(f"unknown OP-IMM f3={f3}")
    elif opc == 0x33:  # OP (+ M ext)
      a, b = r[rs1], r[rs2]
      sa, sb = _sext(a, 32), _sext(b, 32)
      if f7 == 1:
        if f3 == 0: r[rd] = (sa * sb) & 0xFFFFFFFF
        elif f3 == 4: r[rd] = int(sa / sb) & 0xFFFFFFFF if sb else 0xFFFFFFFF
        elif f3 == 5: r[rd] = (a // b) & 0xFFFFFFFF if b else 0xFFFFFFFF
        elif f3 == 6: r[rd] = (sa - int(sa / sb) * sb) & 0xFFFFFFFF if sb else a
        elif f3 == 7: r[rd] = (a % b) & 0xFFFFFFFF if b else a
        else: raise AssertionError(f"unknown M f3={f3}")
      else:
        if f3 == 0: r[rd] = (a - b if f7 & 0x20 else a + b) & 0xFFFFFFFF
        elif f3 == 1: r[rd] = (a << (b & 0x1F)) & 0xFFFFFFFF
        elif f3 == 2: r[rd] = int(sa < sb)
        elif f3 == 3: r[rd] = int(a < b)
        elif f3 == 4: r[rd] = a ^ b
        elif f3 == 5: r[rd] = ((sa >> (b & 0x1F)) & 0xFFFFFFFF) if (f7 & 0x20) else (a >> (b & 0x1F))
        elif f3 == 6: r[rd] = a | b
        elif f3 == 7: r[rd] = a & b
    elif opc == 0x03:  # LOAD
      addr = (r[rs1] + _sext(w >> 20, 12)) & 0xFFFFFFFF
      if f3 == 2: r[rd] = struct.unpack_from("<I", memory, addr)[0]
      elif f3 == 0: r[rd] = _sext(memory[addr], 8) & 0xFFFFFFFF
      elif f3 == 1: r[rd] = _sext(struct.unpack_from("<H", memory, addr)[0], 16) & 0xFFFFFFFF
      elif f3 == 4: r[rd] = memory[addr]
      elif f3 == 5: r[rd] = struct.unpack_from("<H", memory, addr)[0]
      else: raise AssertionError(f"unknown LOAD f3={f3}")
    elif opc == 0x23:  # STORE
      imm = _sext(((w >> 25) << 5) | ((w >> 7) & 0x1F), 12)
      addr = (r[rs1] + imm) & 0xFFFFFFFF
      if f3 == 2: struct.pack_into("<I", memory, addr, r[rs2])
      elif f3 == 1: struct.pack_into("<H", memory, addr, r[rs2] & 0xFFFF)
      elif f3 == 0: memory[addr] = r[rs2] & 0xFF
      else: raise AssertionError(f"unknown STORE f3={f3}")
    elif opc == 0x63:  # BRANCH
      imm = _sext(((w >> 31) << 12) | (((w >> 7) & 1) << 11) | (((w >> 25) & 0x3F) << 5) | (((w >> 8) & 0xF) << 1), 13)
      a, b = r[rs1], r[rs2]
      sa, sb = _sext(a, 32), _sext(b, 32)
      taken = {0: a == b, 1: a != b, 4: sa < sb, 5: sa >= sb, 6: a < b, 7: a >= b}[f3]
      if taken: nxt = pc + imm
    elif opc == 0x6F:  # JAL
      imm = _sext(((w >> 31) << 20) | (((w >> 12) & 0xFF) << 12) | (((w >> 20) & 1) << 11) | (((w >> 21) & 0x3FF) << 1), 21)
      if rd: r[rd] = nxt
      nxt = pc + imm
    elif opc == 0x67:  # JALR
      imm = _sext(w >> 20, 12)
      t = (r[rs1] + imm) & ~1
      if rd: r[rd] = nxt
      if on_call is None or not on_call(t, r): nxt = t
    elif opc == 0x0F:  # FENCE
      pass
    else:
      raise AssertionError(f"unhandled RV32 opcode {opc:#x} at pc={pc:#x} word={w:#010x}")
    r[0] = 0
    pc = nxt
  else:
    raise RuntimeError("RV32 emulator exceeded max_steps")
  return r, memory


class TestMiniTinygradAndMixins(unittest.TestCase):
  def test_shared_mixin_on_uop_and_tensor(self):
    # UOp and Tensor share the exact same Mixin methods, while UOp preserves identity equality
    u_a = UOp.buffer("a", (4, 8), dtypes.fp32)
    u_b = UOp.buffer("b", (8, 6), dtypes.fp32)
    t_a, t_b = Tensor.from_uop(u_a), Tensor.from_uop(u_b)

    u_out = (u_a @ u_b).silu().softmax(-1)
    t_out = (t_a @ t_b).silu().softmax(-1)
    self.assertIs(u_out, t_out.uop)
    self.assertTrue(u_a == u_a)
    self.assertFalse(u_a == u_b)
    self.assertEqual((t_a == t_a).uop.op, Ops.CMPEQ)

  def test_tensor_assign_builds_store_after(self):
    # Slice assign, int+slice assign, and chained assigns all build STORE + AFTER automatically
    buf = Tensor.empty(2, 4, 3, dtype=dtypes.fp32)
    base = buf.uop
    p0 = Tensor([[[1.0, 2.0, 3.0]], [[4.0, 5.0, 6.0]]])
    p1 = Tensor([10.0, 11.0, 12.0])
    buf[:, 1:2, :].assign(p0)
    self.assertEqual(buf.uop.op, Ops.AFTER)
    self.assertEqual(buf.uop.src[1].op, Ops.STORE)
    self.assertIs(buf.uop.src[0], base)
    first = buf.uop
    buf[1, 3, :].assign(p1)
    self.assertEqual(buf.uop.op, Ops.AFTER)
    self.assertIs(buf.uop.src[0], first)  # chained assigns stack AFTERs on the same buffer
    self.assertEqual(buf.uop.src[1].src[1].shape, (3,))  # STORE(view, val)
    self.assertEqual(buf.shape, (2, 4, 3))

  def test_blackhole_group_ops_and_tensix_groups(self):
    self.assertTrue({TensixOps.MVMUL, TensixOps.ELWADD, TensixOps.MOVA2D, TensixOps.ZEROACC} <= TensixGroupOp.FPU)
    self.assertTrue({TensixOps.SFPMAD, TensixOps.SFPLOAD, TensixOps.SFPSTORE, TensixOps.SFPNOP} <= TensixGroupOp.SFPU)
    self.assertIn(TensixOps.UNPACR, TensixGroupOp.Trisc0)
    self.assertIn(TensixOps.MVMUL, TensixGroupOp.Trisc1)
    self.assertIn(TensixOps.SFPMAD, TensixGroupOp.Trisc1)
    self.assertIn(TensixOps.PACR, TensixGroupOp.Trisc2)


class TestRV32BottomLayer(unittest.TestCase):
  def test_rv32_loop_compile_and_execute(self):
    # Compile a scalar loop: for i in 0..8: dst[i] = src[i] * 3 + 7 (all in UOp -> UOp.ins -> RV32 bytes)
    src_ptr = X[10]
    dst_ptr = X[11]
    r = UOp.range(8, 0, "i")
    val = src_ptr.index(r).load() * 3 + 7
    st = dst_ptr.index(r).store(val)
    sink = UOp.sink(st.end(r), arg=KernelArg("scale_add", 1))

    ren = RV32Renderer(wgpr=X[12:28])
    prg = to_program(sink, ren)
    self.assertEqual(prg.op, Ops.PROGRAM)
    self.assertEqual(prg.src[1].op, Ops.LINEAR)
    self.assertEqual(prg.src[3].op, Ops.BINARY)
    code = prg.src[3].arg

    mem = bytearray(4096)
    src_vals = [10, -5, 0, 42, 100, -1, 7, 999]
    for i, v in enumerate(src_vals): struct.pack_into("<i", mem, 256 + 4 * i, v)
    run_rv32(code, {10: 256, 11: 512}, mem)
    got = [struct.unpack_from("<i", mem, 512 + 4 * i)[0] for i in range(8)]
    self.assertEqual(got, [v * 3 + 7 for v in src_vals])

  def test_rv32_spilling_under_register_pressure(self):
    # Force spills by restricting allocatable GPRs to 2 regs while keeping 4 values live simultaneously
    p = X[10]
    a = p.index(0).load()
    b = p.index(1).load()
    c = p.index(2).load()
    d = p.index(3).load()
    res = ((a + b) * (c + d)) + ((a - c) * (b - d))
    sink = UOp.sink(p.index(4).store(res), arg=KernelArg("spill_test", 1))

    ren = RV32Renderer(wgpr=(X[6], X[7]), scratch_regs=(X[30], X[31]), spill_base=LOCAL_BASE, spill_offset=0)
    prg = to_program(sink, ren)
    code = prg.src[3].arg

    mem = bytearray(4096)
    vals = [3, 5, 7, 11]
    for i, v in enumerate(vals): struct.pack_into("<i", mem, 512 + 4 * i, v)
    run_rv32(code, {3: 64, 10: 512}, mem)
    got = struct.unpack_from("<i", mem, 512 + 16)[0]
    want = ((3 + 5) * (7 + 11)) + ((3 - 7) * (5 - 11))
    self.assertEqual(got, want)

  def test_rv32_while_polling_backedge_loop(self):
    # Unbounded while loop: poll/increment counter in memory until counter == 5 (same shape as CB/NoC polling)
    p = X[10]
    lp = UOp.loop_range(0, "poll")
    cur = p.after(lp).index(0).load()
    nxt = cur + 1
    st = p.index(0).store(nxt)
    be = st.backedge(lp, nxt < 5)
    sink = UOp.sink(be, arg=KernelArg("poll_loop", 1))

    ren = RV32Renderer(wgpr=X[12:24])
    prg = to_program(sink, ren)
    mem = bytearray(4096)
    struct.pack_into("<i", mem, 256, 0)
    run_rv32(prg.src[3].arg, {10: 256}, mem)
    self.assertEqual(struct.unpack_from("<i", mem, 256)[0], 5)


class TestTensixAndBlackholeBottomLayer(unittest.TestCase):
  def test_tensix_uop_ins_repeated_ops_and_sfpu_hazards(self):
    # Repeated identical MOVA2D / PACR stay distinct in Ops.LINEAR (no hash-cons collapse)
    ren = BlackholeRenderer()
    mov = tt_ins(hw_isa.MOVA2D(addr_mod=1, rows=2, dst=0), role="trisc1")
    stream = [mov] * 8 + [tt_ins(hw_isa.SETRWC(release=1, mask=0xF), role="trisc1")]
    raw = ren.assemble(stream)
    words = struct.unpack(f"<{len(raw) // 4}I", raw)
    self.assertEqual(len(words), 9)
    for w in words[:8]:
      dec = hw_isa.decode(hw_isa.outline(w))
      self.assertEqual(dec.op, TensixOps.MOVA2D)
      self.assertEqual(dec.addr_mod, 1)

    # Register-level SFPU UOp.ins + automatic SFPNOP hazard insertion
    ld0 = sfp_ins(TensixOps.SFPLOAD, (), dtypes.fp32, L0, fmt=hw_isa.SfpuFormat.FP32, addr=0)
    ld1 = sfp_ins(TensixOps.SFPLOAD, (), dtypes.fp32, L1, fmt=hw_isa.SfpuFormat.FP32, addr=64)
    mad = sfp_ins(TensixOps.SFPMAD, (ld0, ld1, LCONST[1.0]), dtypes.fp32, L0)
    # SFPIADD reading L0 immediately after SFPMAD writing L0 is an undetected RAW hazard on Blackhole
    iadd = sfp_ins(TensixOps.SFPIADD, (L1,), dtypes.i32, L0, mod=4)
    st = sfp_ins(TensixOps.SFPSTORE, (iadd,), dtypes.void, fmt=hw_isa.SfpuFormat.FP32, addr=0)
    fixed = fix_sfpu_hazards_uops([ld0, ld1, mad, iadd, st], ren)
    self.assertEqual(len(fixed), 6)
    self.assertEqual(fixed[3].ins_op, hw_isa.SFPNOP())


if __name__ == "__main__":
  unittest.main()
