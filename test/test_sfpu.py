import math, unittest
import numpy as np
from hw import isa
from compiler import (
  KernelArg, Ops, SfpuCompileError, Space, UOp, compile_sfpu, compile_sfpu_loop, disasm_sfpu, dtypes,
  evaluate, fix_sfpu_hazards, lower_sfpu_uops, sfpu_hazards, sfpu_prim, verify, verify_sfpu_words,
)

def _eval_sfpu_expr(fn, inputs_np: dict[str, np.ndarray], *, precision=dtypes.fp32, out_dt=dtypes.fp32):
  bufs = {name: UOp.buffer(name, (1, 32, 32), dtypes.fp32 if arr.dtype == np.float32 else dtypes.i32)
          for name, arr in inputs_np.items()}
  dst_vars = {name: b.noc_read(0).unpack(Space.DST, b.dtype) for name, b in bufs.items()}
  out_buf = UOp.buffer("out", (1, 32, 32), out_dt)
  y = fn(**dst_vars)
  sink = UOp.sink(out_buf.noc_write(0, y.pack(out_dt)), arg=KernelArg("sfpu_eval", 1))
  lowered = lower_sfpu_uops(sink, precision=precision)
  verify(lowered)
  # Ensure high-level transcendentals & DIV were actually eliminated from Space.DST
  for u in lowered.toposort():
    if u.space is Space.DST:
      assert u.op not in (Ops.EXP2, Ops.LOG2, Ops.SIN, Ops.SQRT, Ops.RSQRT, Ops.RECIP, Ops.DIV), \
        f"unlowered SFPU op {u.op.name}"
  out_np = np.zeros((1, 32, 32), dtype=np.float32 if out_dt.is_float else np.int32)
  data = {**{k_: v.reshape(1, 32, 32) for k_, v in inputs_np.items()}, "out": out_np}
  evaluate(lowered, data)
  return out_np[0], lowered

class TestSfpuHazardModel(unittest.TestCase):
  def test_measured_undetected_hazards_and_safe_pairs(self):
    mad_l0 = isa.SFPMAD(a=1, b=2, c=3)  # 2-cycle write to L0

    # Every undetected RAW hazard measured on Blackhole A0 card 1
    bad_consumers = [
      ("IADD reg VD",       isa.SFPIADD(src=1, mode=4)),
      ("SHFT reg VD",       isa.SFPSHFT(src=1)),
      ("AND USE_VB",        isa.SFPAND(src=1, dest=2, mode=1)),
      ("OR USE_VB",         isa.SFPOR(src=1, dest=2, mode=1)),
      ("SETEXP non-imm VD", isa.SFPSETEXP(src=1, mode=2)),
      ("SETMAN non-imm VD", isa.SFPSETMAN(src=1)),
      ("SETSGN non-imm VD", isa.SFPSETSGN(src=1)),
      ("ARECIP mode 1 VB",  isa.SFPARECIP(src=1, dest=2, mode=1)),
      ("SWAP mode 1 VD",    isa.SFPSWAP(src=1, mode=1)),
      ("SHFT2 mode 3 VC",   isa.SFPSHFT2(dest=1, mode=3)),
      ("SHFT2 mode 6 VB",   isa.SFPSHFT2(src=1, dest=2, mode=6)),
      ("CONFIG non-imm L0", isa.SFPCONFIG(target=12)),
      ("LOADI LOWER L0",    isa.SFPLOADI(mode=isa.LoadImm.LOWER, imm=0x1234)),
      ("LOAD LO16_ONLY L0", isa.SFPLOAD(format=isa.SfpuFormat.LO16_ONLY)),
    ]
    for label, cons in bad_consumers:
      with self.subTest(label=label):
        hz = sfpu_hazards([mad_l0, cons])
        self.assertEqual(len(hz), 1, f"expected hazard for {label}")
        self.assertEqual(hz[0][1][0], "stale")
        fixed = fix_sfpu_hazards([mad_l0, cons])
        self.assertEqual(len(fixed), 3)
        self.assertEqual(fixed[1], isa.SFPNOP())
        self.assertEqual(sfpu_hazards(fixed), [])

    # Safe pairs (hardware stalls or no dependency) must NOT get spurious SFPNOPs
    safe_pairs = [
      ("MAD -> MAD",          [mad_l0, isa.SFPMAD(b=1, c=2, dest=3)]),
      ("MAD -> SHFT imm",     [mad_l0, isa.SFPSHFT(imm=3, dest=1, mode=5)]),
      ("MAD -> SWAP mode 0",  [mad_l0, isa.SFPSWAP(dest=1)]),
      ("MAD -> LOADI FLOATB", [mad_l0, isa.SFPLOADI(mode=isa.LoadImm.FLOATB, imm=0x3F80)]),
      ("LOADI FLOATB->LOWER", [isa.SFPLOADI(mode=isa.LoadImm.FLOATB, imm=0x3F80), isa.SFPLOADI(mode=isa.LoadImm.LOWER, imm=0x1234)]),
      ("SWAP -> ADD",         [isa.SFPSWAP(src=1, mode=1), isa.SFPADD(a=10, c=1, dest=2)]),
      ("SHFT2 -> ADD",        [isa.SFPSHFT2(src=1, mode=3), isa.SFPADD(a=10, c=1, dest=2)]),
    ]
    for label, stream in safe_pairs:
      with self.subTest(label=label):
        self.assertEqual(sfpu_hazards(stream), [], f"unexpected hazard for {label}")
        self.assertEqual(fix_sfpu_hazards(stream), stream)

  def test_verify_rejects_backdoor_and_illegal_writes(self):
    # VD >= 12 on non-CONFIG/LOADMACRO becomes a silent backdoor template write
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPSTORE(lreg=12, format=isa.SfpuFormat.FP32)])
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPTRANSP(dest=12)])
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPGT(dest=12, mode=1)])
    # Writing read-only L9/L10 fails
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPMOV(dest=9)])
    # Storing L9 (0.0) or L10 (1.0) is safe (VD < 12)
    verify_sfpu_words([isa.SFPSTORE(lreg=9, format=isa.SfpuFormat.FP32)])

  def test_loop_wraparound_hazard_detection_and_fix(self):
    # Body starts with IADD reg reading L0 and ends with MAD writing L0: safe once, stale on 2nd iteration
    body = [isa.SFPIADD(src=1, mode=4), isa.SFPMAD(a=1, b=2, c=3)]
    self.assertEqual(sfpu_hazards(body), [])
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words(body, is_loop=True)
    fixed = fix_sfpu_hazards(body, is_loop=True)
    self.assertEqual(fixed[-1], isa.SFPNOP())
    verify_sfpu_words(fixed, is_loop=True)

class TestSfpuDecompositions(unittest.TestCase):
  def test_exp2_and_exp_bf16_and_fp32(self):
    xs = np.linspace(-10.0, 10.0, 1024, dtype=np.float32).reshape(32, 32)
    xs[0, 0], xs[0, 1], xs[0, 2], xs[0, 3] = -150.0, -126.5, 0.0, 100.0
    out_f32, _ = _eval_sfpu_expr(lambda x: x.exp2(), {"x": xs}, precision=dtypes.fp32)
    ref = np.exp2(xs)
    np.testing.assert_allclose(out_f32, ref, rtol=2e-6, atol=1e-35)
    self.assertEqual(out_f32[0, 0], 0.0)
    self.assertEqual(out_f32[0, 1], 0.0)

    out_bf16, _ = _eval_sfpu_expr(lambda x: x.exp(), {"x": np.linspace(-6.0, 6.0, 1024, dtype=np.float32).reshape(32, 32)},
                                  precision=dtypes.bf16, out_dt=dtypes.bf16)
    ref_e = np.exp(np.linspace(-6.0, 6.0, 1024, dtype=np.float32).reshape(32, 32))
    np.testing.assert_allclose(out_bf16, ref_e, rtol=1.5e-2, atol=1e-4)

  def test_recip_rsqrt_sqrt_log2_sin(self):
    rng = np.random.default_rng(42)
    pos = np.exp(rng.uniform(-6.0, 6.0, (32, 32))).astype(np.float32)
    signed = np.where(rng.random((32, 32)) < 0.5, -pos, pos).astype(np.float32)

    out_rcp, _ = _eval_sfpu_expr(lambda x: x.recip(), {"x": signed}, precision=dtypes.fp32)
    np.testing.assert_allclose(out_rcp, 1.0 / signed, rtol=2e-6, atol=0.0)

    out_rsq, _ = _eval_sfpu_expr(lambda x: x.rsqrt(), {"x": pos}, precision=dtypes.fp32)
    np.testing.assert_allclose(out_rsq, 1.0 / np.sqrt(pos), rtol=2e-6, atol=0.0)

    pos0 = pos.copy()
    pos0[0, 0] = 0.0
    out_sq, _ = _eval_sfpu_expr(lambda x: x.sqrt(), {"x": pos0}, precision=dtypes.fp32)
    np.testing.assert_allclose(out_sq, np.sqrt(pos0), rtol=2e-6, atol=0.0)
    self.assertEqual(out_sq[0, 0], 0.0)

    out_log2, _ = _eval_sfpu_expr(lambda x: x.log2(), {"x": pos}, precision=dtypes.fp32)
    np.testing.assert_allclose(out_log2, np.log2(pos), rtol=2e-5, atol=2e-5)

    angles = rng.uniform(-5000.0, 5000.0, (32, 32)).astype(np.float32)
    out_sin, _ = _eval_sfpu_expr(lambda x: x.sin(), {"x": angles}, precision=dtypes.fp32)
    np.testing.assert_allclose(out_sin, np.sin(angles.astype(np.float64)), rtol=2e-6, atol=2e-6)

  def test_exp2_magic_rounding_survives_rewrites(self):
    # Ensure (x + 12582912.0) - 12582912.0 is NOT folded away by simplify / lower_sfpu_uops
    xs = np.array([[0.3, -0.3, 1.7, -1.7] * 8] * 32, dtype=np.float32)
    out_f32, lowered = _eval_sfpu_expr(lambda x: x.exp2(), {"x": xs}, precision=dtypes.fp32)
    np.testing.assert_allclose(out_f32, np.exp2(xs), rtol=1e-6, atol=0.0)
    consts = {u.arg for u in lowered.toposort() if u.op is Ops.CONST}
    self.assertIn(12582912.0, consts)

  def test_silu_mul_and_gelu_and_tanh(self):
    rng = np.random.default_rng(7)
    a = rng.standard_normal((32, 32)).astype(np.float32) * 3.0
    b = rng.standard_normal((32, 32)).astype(np.float32)
    a[0, 0], a[0, 1] = -100.0, 100.0  # extreme clamp check (no NaN/Inf)

    out_silu_f32, lowered = _eval_sfpu_expr(lambda a, b: a.silu() * b, {"a": a, "b": b}, precision=dtypes.fp32)
    ref_silu = (a / (1.0 + np.exp(-np.clip(a, -80.0, 80.0)))) * b
    np.testing.assert_allclose(out_silu_f32, ref_silu, rtol=3e-5, atol=1e-5)
    self.assertTrue(np.all(np.isfinite(out_silu_f32)))
    # Verify MULACC fusion happened
    self.assertIn(Ops.MULACC, {u.op for u in lowered.toposort()})

    out_silu_bf16, _ = _eval_sfpu_expr(lambda a, b: a.silu() * b, {"a": a, "b": b}, precision=dtypes.bf16, out_dt=dtypes.bf16)
    np.testing.assert_allclose(out_silu_bf16, ref_silu, rtol=2e-2, atol=2e-2)

    a_mild = rng.standard_normal((32, 32)).astype(np.float32) * 2.0
    out_gelu, _ = _eval_sfpu_expr(lambda x: x.gelu(), {"x": a_mild}, precision=dtypes.fp32)
    c = math.sqrt(2.0 / math.pi)
    ref_gelu = 0.5 * a_mild * (1.0 + np.tanh(c * (a_mild + 0.044715 * a_mild ** 3)))
    np.testing.assert_allclose(out_gelu, ref_gelu, rtol=2e-4, atol=1e-4)

class TestSfpuCompiler(unittest.TestCase):
  def _make_dst(self, name: str, dt=dtypes.fp32) -> UOp:
    return UOp.buffer(name, (1, 32, 32), dt).noc_read(0).unpack(Space.DST, dt)

  def _check_compiled(self, comp, max_regs: int, addr_mode: int = 0):
    self.assertGreaterEqual(len(comp.passes), 1)
    for p in comp.passes:
      self.assertLessEqual(p.peak_regs, max_regs)
      all_words = p.prologue + p.body + p.epilogue
      verify_sfpu_words(all_words)
      # Every word must decode cleanly through hw.isa
      for w in all_words:
        self.assertIsNotNone(isa.decode(w))
      # Every L11..L14 read in body must have been explicitly programmed via SFPCONFIG in prologue
      cfg_written = {(w >> 4) & 15 for w in p.prologue if (w >> 24) == 0x91}
      for w in p.body:
        info = sfpu_hazards([w])
        self.assertEqual(info, [])
        dec = isa.decode(w)
        assert dec is not None
        for k, v in dec.fields().items():
          if k in ("lreg", "a", "b", "c", "src", "dest") and 12 <= v <= 14:
            self.assertIn(v, cfg_written, f"L{v} read in body without SFPCONFIG init in prologue")
      if addr_mode:
        stores = [isa.decode(w) for w in p.body if (w >> 24) == 0x72]
        self.assertTrue(stores)
        self.assertEqual(stores[-1].addr_mod, addr_mode)

  def test_slice1_silu_mul_compilation_and_l11_usage(self):
    a = self._make_dst("a")
    b = self._make_dst("b")
    y = a.silu() * b

    # BF16 precision, full 8 regs (L11 available as 4th constant -> fits in 1 pass)
    comp_bf16 = compile_sfpu(y, {a: 0, b: 1}, precision=dtypes.bf16, output_tiles={y: 0}, addr_mode=6)
    self._check_compiled(comp_bf16, max_regs=8, addr_mode=6)
    self.assertEqual(comp_bf16.output_tiles[lower_sfpu_uops(y, precision=dtypes.bf16)], 0)
    self.assertLessEqual(comp_bf16.dst_tiles, 4)

    # FP32 precision with preserve_l11=True (must never program L11 with non-(-1.0))
    comp_f32_keep11 = compile_sfpu(y, {a: 0, b: 1}, precision=dtypes.fp32, output_tiles={y: 0}, preserve_l11=True)
    self._check_compiled(comp_f32_keep11, max_regs=8)
    for p in comp_f32_keep11.passes:
      self.assertFalse(p.l11_used)

    # Tight 4-reg budget (for 2x even/odd interleaving): forces clean Dst pass splitting
    comp_4reg = compile_sfpu(y, {a: 0, b: 1}, precision=dtypes.fp32, max_regs=4, output_tiles={y: 0})
    self._check_compiled(comp_4reg, max_regs=4)
    self.assertGreaterEqual(len(comp_4reg.passes), 2)
    self.assertIn("SFPMAD", "\n".join(disasm_sfpu(p.body) for p in comp_4reg.passes))

  def test_deep_register_pressure_forces_dst_spills(self):
    # 6-way independent expression tree needing >8 simultaneous live temps if unsplit
    a = self._make_dst("a")
    b = self._make_dst("b")
    # Build a balanced tree of height 4 (Ershov number = 5) with multi-reg ops inside each leaf
    def leaf(x, k):
      return (x + float(k) * 0.13).exp2() * (x + float(k) * 0.27 + 1.0).recip()
    t0 = leaf(a, 1) + leaf(b, 2)
    t1 = leaf(a + 0.5, 3) + leaf(b - 0.5, 4)
    t2 = leaf(a * 0.7, 5) + leaf(b * 1.3, 6)
    y = (t0 * t1 + t2) * (t0 - t2)

    comp = compile_sfpu(y, {a: 0, b: 1}, precision=dtypes.fp32, max_regs=8, dst_budget=8, output_tiles={y: 0})
    self._check_compiled(comp, max_regs=8)
    self.assertGreaterEqual(len(comp.passes), 2)
    self.assertLessEqual(comp.dst_tiles, 8)

  def test_where_and_predication_lowering(self):
    a = self._make_dst("a")
    b = self._make_dst("b")
    c = self._make_dst("c")

    # 1. Direct single-use comparison WHERE -> SFPENCC + SFPGT/SFPLE + SFPMOV (no mask reg)
    w_lt = (a < b).where(a + 1.0, b)
    comp_lt = compile_sfpu(w_lt, {a: 0, b: 1}, output_tiles={w_lt: 0})
    self._check_compiled(comp_lt, max_regs=8)
    ops_lt = [isa.decode(w).name for w in comp_lt.passes[0].body]
    self.assertIn("SFPENCC", ops_lt)
    self.assertIn("SFPGT", ops_lt)

    w_ge = (a >= b).where(a, b)
    comp_ge = compile_sfpu(w_ge, {a: 0, b: 1}, output_tiles={w_ge: 0})
    self._check_compiled(comp_ge, max_regs=8)
    ops_ge = [isa.decode(w).name for w in comp_ge.passes[0].body]
    self.assertIn("SFPLE", ops_ge)

    # 2. Composed boolean mask with b == 0.0 -> 3-address SFPAND fast path (zero SFPENCC)
    mask = (a < b) & (b < c)
    w_zero = mask.where(a, 0.0)
    comp_and = compile_sfpu(w_zero, {a: 0, b: 1, c: 2}, output_tiles={w_zero: 0})
    self._check_compiled(comp_and, max_regs=8)
    ops_and = [isa.decode(w).name for w in comp_and.passes[0].body]
    self.assertIn("SFPAND", ops_and)
    self.assertNotIn("SFPENCC", ops_and)

    # 3. Equality check -> SFPSETCC
    w_eq = a.eq(b).where(c, a)
    comp_eq = compile_sfpu(w_eq, {a: 0, b: 1, c: 2}, output_tiles={w_eq: 0})
    self._check_compiled(comp_eq, max_regs=8)
    ops_eq = [isa.decode(w).name for w in comp_eq.passes[0].body]
    self.assertIn("SFPSETCC", ops_eq)

    # 4. Integer UOp.lane_id() < 16 comparison -> uses L15 (LANE_X2) and nonnegative sign-magnitude keys
    w_lane = (UOp.lane_id() < 16).where(a, 0.0)
    comp_lane = compile_sfpu(w_lane, {a: 0}, output_tiles={w_lane: 0})
    self._check_compiled(comp_lane, max_regs=8)
    ops_lane = [isa.decode(w).name for w in comp_lane.passes[0].body]
    self.assertIn("SFPSHFT", ops_lane)
    self.assertIn("SFPGT", ops_lane)

    # 5. Integer / boolean output stores with SfpuFormat.INT32 (never FP32 which flushes small ints)
    mask_out = a < b
    comp_mask = compile_sfpu(mask_out, {a: 0, b: 1}, output_tiles={mask_out: 0})
    self._check_compiled(comp_mask, max_regs=8)
    stores = [isa.decode(w) for w in comp_mask.passes[-1].body if (w >> 24) == 0x72]
    self.assertEqual(stores[-1].format, isa.SfpuFormat.INT32)

  def test_transpose_requires_explicit_register_group(self):
    a = self._make_dst("a")
    with self.assertRaisesRegex(SfpuCompileError, "four explicit register inputs"):
      compile_sfpu(sfpu_prim("TRANSP", dtypes.fp32, a + 1), {a: 0})

  def test_resident_product_is_a_load(self):
    a, b = self._make_dst("a"), self._make_dst("b")
    product = a * b
    comp = compile_sfpu(product + 2, {product: 0})
    ops = [isa.decode(w).name for w in comp.passes[0].body]
    self.assertEqual(ops.count("SFPLOAD"), 1)
    self.assertNotIn("SFPMAD", ops)

  def test_integer_immediates_skip_constant_setup(self):
    a = self._make_dst("a", dtypes.i32)
    for root in (UOp.const(dtypes.i32, 1999) + a, a - 2048):
      p, = compile_sfpu(root, {a: 0}).passes
      self.assertFalse(p.prologue)
      self.assertEqual([isa.decode(w).name for w in p.body], ["SFPLOAD", "SFPIADD", "SFPSTORE"])

  def test_output_tile_contract(self):
    a, b = self._make_dst("a"), self._make_dst("b")
    for slots in ([1, 1], [-1, 0], [0, 8]):
      with self.subTest(slots=slots), self.assertRaises(ValueError):
        compile_sfpu([a, b], {a: 0, b: 1}, output_tiles=slots)
    with self.assertRaises(ValueError):
      compile_sfpu(a, {a: 1}, dst_budget=1)

  def test_dst_no_store_before_load_aliasing_and_const_and_dup_roots(self):
    a = self._make_dst("a")
    b = self._make_dst("b")

    # Bug #1 regression: two inputs (tiles 0, 1), early output depends only on `a`, second depends on `b`.
    # Must NEVER store over tile 1 before loading `b` from tile 1
    out0 = a + 1.0
    out1 = b + 2.0
    comp = compile_sfpu([out0, out1], {a: 0, b: 1}, output_tiles=[1, 0])
    self._check_compiled(comp, max_regs=8)
    self.assertEqual(comp.root_tiles, (1, 0))
    for p in comp.passes:
      written: set[int] = set()
      for w in p.body:
        if (w >> 24) == 0x72: written.add((w & 0x3FF) // 64)
        elif (w >> 24) == 0x70: self.assertNotIn((w & 0x3FF) // 64, written)

    # Bug #6c: root simplifying to a CONST must materialize cleanly instead of KeyError
    c_root = UOp.const(dtypes.fp32, 3.5)
    comp_c = compile_sfpu(c_root, {a: 0}, output_tiles=[2])
    self._check_compiled(comp_c, max_regs=8)
    self.assertEqual(comp_c.root_tiles, (2,))
    self.assertEqual(len(comp_c.passes), 1)

    # Bug #6d: two roots that CSE to the same UOp but target two different Dst tiles
    r0 = a + b
    r1 = a + b
    comp_dup = compile_sfpu([r0, r1], {a: 0, b: 1}, output_tiles=[2, 3])
    self._check_compiled(comp_dup, max_regs=8)
    self.assertEqual(comp_dup.root_tiles, (2, 3))
    stored_tiles = {(w & 0x3FF) // 64 for p in comp_dup.passes for w in p.body if (w >> 24) == 0x72}
    self.assertTrue({2, 3} <= stored_tiles)

  def test_pinned_lreg_accumulator_and_decode_rmsnorm(self):
    r = UOp.range(4, axis=0, name="t")
    x = self._make_dst("x")
    gamma = self._make_dst("gamma")

    # Stage 1: LReg accumulator loop: l0 += x * x (2-word body, zero SFPSTOREs, SFPLOAD steps addr_mode=6)
    acc = (x * x).reduce(r, op=Ops.ADD, space=Space.LREG)
    sq_loop = compile_sfpu_loop(acc, {x: 0}, addr_mode=6)
    self.assertEqual(len(sq_loop.init_passes), 1)
    self.assertEqual(sq_loop.init_passes[0].footprints, 1)
    self.assertEqual(sq_loop.reg_carries[acc], 0)
    self.assertEqual(len(sq_loop.body_passes), 1)
    sq_pass = sq_loop.body_passes[0]
    self.assertEqual(sq_pass.footprints, 32)
    sq_ops = [isa.decode(w).name for w in sq_pass.body]
    self.assertEqual(sq_ops, ["SFPLOAD", "SFPMAD"])
    self.assertEqual(isa.decode(sq_pass.body[0]).addr_mod, 6)
    self.assertEqual(isa.decode(sq_pass.body[1]).dest, 0)
    verify_sfpu_words(sq_pass.body, is_loop=True)

    # Stage 2: 1-shot LReg reduce_lanes + rsqrt (runs ONCE, stays in L0, zero Dst traffic)
    inv_rms = (acc.reduce_lanes(Ops.ADD, "all") * (1.0 / 4096.0) + 1e-5).rsqrt()
    rms_comp = compile_sfpu(inv_rms, reg_inputs=sq_loop.reg_carries, reg_outputs={inv_rms: 0})
    self.assertEqual(len(rms_comp.passes), 1)
    rms_pass = rms_comp.passes[0]
    self.assertEqual(rms_pass.footprints, 1)
    rms_ops = [isa.decode(w).name for w in rms_pass.body]
    self.assertNotIn("SFPLOAD", rms_ops)
    self.assertNotIn("SFPSTORE", rms_ops)
    self.assertIn("SFPSHFT2", rms_ops)
    self.assertIn("SFPTRANSP", rms_ops)
    verify_sfpu_words(rms_pass.prologue + rms_pass.body)

    # Stage 3: rms_apply with read-only pinned L0 across 32 footprints (L0 never overwritten)
    out = x * inv_rms * gamma
    apply_comp = compile_sfpu(out, {x: 0, gamma: 1}, reg_inputs={inv_rms: 0}, output_tiles={out: 0}, addr_mode=6)
    self._check_compiled(apply_comp, max_regs=8, addr_mode=6)
    apply_pass = apply_comp.passes[0]
    self.assertEqual(apply_pass.footprints, 32)
    self.assertEqual([isa.decode(w).name for w in apply_pass.body].count("SFPLOAD"), 2)

  def test_pinned_lreg_survives_multi_pass_body(self):
    # A spilled body splits into several passes; only the last reads the carried L0, but none may clobber it.
    from compiler.sfpu import _verify_compiled_pass
    r = UOp.range(2, axis=0, name="t")
    x, y = self._make_dst("x"), self._make_dst("y")
    lp = compile_sfpu_loop((x.exp() * y).reduce(r, op=Ops.ADD, space=Space.LREG), {x: 0, y: 1}, addr_mode=6, max_regs=4)
    self.assertEqual(lp.reg_carries[next(iter(lp.reg_carries))], 0)
    self.assertGreater(len(lp.body_passes), 1)
    for p in lp.body_passes[:-1]:
      _verify_compiled_pass(p.prologue, p.body, p.epilogue, footprints=p.footprints, pinned_ro={0})
      if any(isa.decode(w).name == "SFPCONFIG" for w in p.prologue):
        self.assertEqual(isa.decode(p.prologue[0]).name, "SFPMOV")
        self.assertEqual(isa.decode(p.prologue[0]).src, 0)
        self.assertEqual(isa.decode(p.prologue[-1]).dest, 0)

    # Duplicate-output copy passes must not use a pinned register as scratch either
    s = UOp.const(dtypes.fp32, 2.0).carry(UOp.range(1, axis=9), space=Space.LREG)
    out = x * s
    comp = compile_sfpu([out, out], {x: 0}, reg_inputs={s: 0}, output_tiles=[1, 2], addr_mode=6)
    self.assertGreater(len(comp.passes), 1)
    for p in comp.passes:
      _verify_compiled_pass(p.prologue, p.body, p.epilogue, footprints=p.footprints, pinned_ro={0})

  def test_dst_accumulator_single_and_dual_in_place_loop(self):
    r = UOp.range(4, axis=0, name="t")
    x = self._make_dst("x")

    # Single Dst accumulator: Dst[1] += x * x updated in-place in 1 pass with 0 scratch tiles
    acc_dst = (x * x).reduce(r, op=Ops.ADD, space=Space.DST)
    lp1 = compile_sfpu_loop(acc_dst, {x: 0}, addr_mode=6)
    self.assertEqual(lp1.dst_carries[acc_dst], 1)
    self.assertEqual(lp1.dst_tiles, 2)
    self.assertEqual(len(lp1.body_passes), 1)
    self._check_compiled(type("C", (), {"passes": lp1.body_passes})(), max_regs=8, addr_mode=6)

    # Dual coupled Dst accumulators: sum + max both updated in-place in 1 pass with 0 scratch tiles
    s_out, m_out = r.loop((UOp.const(dtypes.fp32, 0.0), UOp.const(dtypes.fp32, -math.inf)), lambda s, m: (s + x, m.maximum(x)), spaces=(Space.DST, Space.DST))
    lp2 = compile_sfpu_loop(s_out, {x: 0}, addr_mode=6)
    self.assertEqual(lp2.dst_carries[s_out], 1)
    self.assertEqual(lp2.dst_carries[m_out], 2)
    self.assertEqual(lp2.dst_tiles, 3)
    self.assertEqual(len(lp2.body_passes), 1)
    self._check_compiled(type("C", (), {"passes": lp2.body_passes})(), max_regs=8, addr_mode=6)

  def test_prologue_preserves_live_in_l0_and_reg_output_swap(self):
    x = self._make_dst("x")
    scale = UOp.const(dtypes.fp32, 1.0).carry(UOp.range(1, axis=5), space=Space.LREG)
    y = x.sin() * scale
    comp = compile_sfpu(y, {x: 0}, reg_inputs={scale: 0}, output_tiles={y: 0}, addr_mode=6)
    self._check_compiled(comp, max_regs=8, addr_mode=6)
    # Prologue programs L12..L14 via L0, so it must save L0 before and restore L0 after
    pro_ops = [isa.decode(w).name for w in comp.passes[0].prologue]
    self.assertIn("SFPCONFIG", pro_ops)
    self.assertEqual(pro_ops[0], "SFPMOV")
    self.assertEqual(pro_ops[-1], "SFPMOV")
    self.assertEqual(isa.decode(comp.passes[0].prologue[0]).src, 0)
    self.assertEqual(isa.decode(comp.passes[0].prologue[-1]).dest, 0)

    # Register output swap cycle (L0 <-> L1) uses 1-insn SFPSWAP(mod=0)
    a = UOp.const(dtypes.fp32, 1.0).carry(UOp.range(1, axis=6), space=Space.LREG)
    b = UOp.const(dtypes.fp32, 2.0).carry(UOp.range(1, axis=7), space=Space.LREG)
    swap_comp = compile_sfpu([b, a], reg_inputs={a: 0, b: 1}, reg_outputs={b: 0, a: 1})
    self.assertEqual(swap_comp.passes[0].footprints, 1)
    self.assertEqual([isa.decode(w).name for w in swap_comp.passes[0].body], ["SFPSWAP"])

if __name__ == "__main__":
  unittest.main()
