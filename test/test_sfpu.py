import math, unittest
import numpy as np
from hw import isa
from compiler import (
  Kernel, Ops, SfpuCompileError, SfpuPrim, Space, UOp,
  compile_sfpu, disasm_sfpu, dram_buf, dtypes, end, evaluate, fix_sfpu_hazards,
  lane_id, lower_sfpu_uops, noc_read, noc_write, pack, sfpu_hazards, sfpu_prim,
  sfpu_slope, unpack, verify, verify_sfpu_words,
)


def _eval_sfpu_expr(fn, inputs_np: dict[str, np.ndarray], *, precision=dtypes.fp32, out_dt=dtypes.fp32):
  """Build a single-tile Layer 1 kernel, run Pass A lower_sfpu_uops, verify, and evaluate against NumPy."""
  k = Kernel("sfpu_eval", grid=1)
  bufs = {name: dram_buf(name, (1, 32, 32), dtypes.fp32 if arr.dtype == np.float32 else dtypes.i32)
          for name, arr in inputs_np.items()}
  dst_vars = {name: unpack(noc_read(b, 0), Space.DST, b.dtype) for name, b in bufs.items()}
  out_buf = dram_buf("out", (1, 32, 32), out_dt)
  y = fn(**dst_vars)
  k.emit(noc_write(out_buf, 0, pack(y, out_dt)))
  sink = k.build()
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
    mad_l0 = isa.SFPMAD(1, 2, 3, 0, 0)  # 2-cycle write to L0

    # Every undetected RAW hazard measured on Blackhole A0 card 1
    bad_consumers = [
      ("IADD reg VD",       isa.SFPIADD(0, 1, 0, 4)),
      ("SHFT reg VD",       isa.SFPSHFT(0, 1, 0, 0)),
      ("AND USE_VB",        isa.SFPAND(0, 1, 2, 1)),
      ("OR USE_VB",         isa.SFPOR(0, 1, 2, 1)),
      ("SETEXP non-imm VD", isa.SFPSETEXP(0, 1, 0, 2)),
      ("SETMAN non-imm VD", isa.SFPSETMAN(0, 1, 0, 0)),
      ("SETSGN non-imm VD", isa.SFPSETSGN(0, 1, 0, 0)),
      ("ARECIP mode 1 VB",  isa.SFPARECIP(0, 1, 2, 1)),
      ("SWAP mode 1 VD",    isa.SFPSWAP(0, 1, 0, 1)),
      ("SHFT2 mode 3 VC",   isa.SFPSHFT2(0, 0, 1, 3)),
      ("SHFT2 mode 6 VB",   isa.SFPSHFT2(0, 1, 2, 6)),
      ("CONFIG non-imm L0", isa.SFPCONFIG(0, 12, 0)),
      ("LOADI LOWER L0",    isa.SFPLOADI(0, isa.LoadImm.LOWER, 0x1234)),
      ("LOAD LO16_ONLY L0", isa.SFPLOAD(0, isa.SfpuFormat.LO16_ONLY, 0, 0)),
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
      ("MAD -> MAD",          [mad_l0, isa.SFPMAD(0, 1, 2, 3, 0)]),
      ("MAD -> SHFT imm",     [mad_l0, isa.SFPSHFT(3, 0, 1, 5)]),
      ("MAD -> SWAP mode 0",  [mad_l0, isa.SFPSWAP(0, 0, 1, 0)]),
      ("MAD -> LOADI FLOATB", [mad_l0, isa.SFPLOADI(0, isa.LoadImm.FLOATB, 0x3F80)]),
      ("LOADI FLOATB->LOWER", [isa.SFPLOADI(0, isa.LoadImm.FLOATB, 0x3F80), isa.SFPLOADI(0, isa.LoadImm.LOWER, 0x1234)]),
      ("SWAP -> ADD",         [isa.SFPSWAP(0, 1, 0, 1), isa.SFPADD(10, 0, 1, 2, 0)]),
      ("SHFT2 -> ADD",        [isa.SFPSHFT2(0, 1, 0, 3), isa.SFPADD(10, 0, 1, 2, 0)]),
    ]
    for label, stream in safe_pairs:
      with self.subTest(label=label):
        self.assertEqual(sfpu_hazards(stream), [], f"unexpected hazard for {label}")
        self.assertEqual(fix_sfpu_hazards(stream), stream)

  def test_verify_rejects_backdoor_and_illegal_writes(self):
    # VD >= 12 on non-CONFIG/LOADMACRO becomes a silent backdoor template write!
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPSTORE(12, isa.SfpuFormat.FP32, 0, 0)])
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPTRANSP(0, 0, 12, 0)])
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPGT(0, 0, 12, 1)])
    # Writing read-only L9/L10 fails
    with self.assertRaises(SfpuCompileError):
      verify_sfpu_words([isa.SFPMOV(0, 0, 9, 0)])
    # Storing L9 (0.0) or L10 (1.0) is safe (VD < 12)
    verify_sfpu_words([isa.SFPSTORE(9, isa.SfpuFormat.FP32, 0, 0)])

  def test_loop_wraparound_hazard_detection_and_fix(self):
    # Body starts with IADD reg reading L0 and ends with MAD writing L0: safe once, stale on 2nd iteration!
    body = [isa.SFPIADD(0, 1, 0, 4), isa.SFPMAD(1, 2, 3, 0, 0)]
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
    a[0, 0], a[0, 1] = -100.0, 100.0  # extreme clamp check (no NaN/Inf!)

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
    return unpack(noc_read(dram_buf(name, (1, 32, 32), dt), 0), Space.DST, dt)

  def _check_compiled(self, comp, max_regs: int, addr_mode: int = 0):
    self.assertGreaterEqual(len(comp.passes), 1)
    for p in comp.passes:
      self.assertLessEqual(p.peak_regs, max_regs)
      all_words = p.prologue + p.body + p.epilogue
      verify_sfpu_words(all_words)
      # Every word must decode cleanly through hw.isa
      for w in all_words:
        self.assertIsNotNone(isa.tensix_decode(w))
      # Every L11..L14 read in body must have been explicitly programmed via SFPCONFIG in prologue
      cfg_written = {(w >> 4) & 15 for w in p.prologue if (w >> 24) == 0x91}
      for w in p.body:
        info = sfpu_hazards([w])
        self.assertEqual(info, [])
        dec = isa.tensix_decode(w)
        assert dec is not None
        for k, v in dec[1].items():
          if k.startswith("lreg_") and 12 <= v <= 14:
            self.assertIn(v, cfg_written, f"L{v} read in body without SFPCONFIG init in prologue")
      if addr_mode:
        stores = [isa.tensix_decode(w) for w in p.body if (w >> 24) == 0x72]
        self.assertTrue(stores)
        self.assertEqual(stores[-1][1]["sfpu_addr_mode"], addr_mode)

  def test_slice1_silu_mul_compilation_and_l11_usage(self):
    a = self._make_dst("a")
    b = self._make_dst("b")
    y = a.silu() * b

    # BF16 precision, full 8 regs (L11 available as 4th constant -> fits in 1 pass!)
    comp_bf16 = compile_sfpu(y, {a: 0, b: 1}, precision=dtypes.bf16, output_tiles={y: 0}, addr_mode=6)
    self._check_compiled(comp_bf16, max_regs=8, addr_mode=6)
    self.assertEqual(comp_bf16.output_tiles[lower_sfpu_uops(y, precision=dtypes.bf16)], 0)
    self.assertLessEqual(comp_bf16.dst_tiles, 4)

    # FP32 precision with preserve_l11=True (must never program L11 with non-(-1.0))
    comp_f32_keep11 = compile_sfpu(y, {a: 0, b: 1}, precision=dtypes.fp32, output_tiles={y: 0}, preserve_l11=True)
    self._check_compiled(comp_f32_keep11, max_regs=8)
    for p in comp_f32_keep11.passes:
      self.assertFalse(p.l11_used)

    # Tight 4-reg budget (for 2x even/odd interleaving): forces clean Dst pass splitting!
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

    # 1. Direct single-use comparison WHERE -> SFPENCC + SFPGT/SFPLE + SFPMOV (no mask reg!)
    w_lt = (a < b).where(a + 1.0, b)
    comp_lt = compile_sfpu(w_lt, {a: 0, b: 1}, output_tiles={w_lt: 0})
    self._check_compiled(comp_lt, max_regs=8)
    ops_lt = [isa.tensix_decode(w)[0] for w in comp_lt.passes[0].body]
    self.assertIn("SFPENCC", ops_lt)
    self.assertIn("SFPGT", ops_lt)

    w_ge = (a >= b).where(a, b)
    comp_ge = compile_sfpu(w_ge, {a: 0, b: 1}, output_tiles={w_ge: 0})
    self._check_compiled(comp_ge, max_regs=8)
    ops_ge = [isa.tensix_decode(w)[0] for w in comp_ge.passes[0].body]
    self.assertIn("SFPLE", ops_ge)

    # 2. Composed boolean mask with b == 0.0 -> 3-address SFPAND fast path (zero SFPENCC!)
    mask = (a < b) & (b < c)
    w_zero = mask.where(a, 0.0)
    comp_and = compile_sfpu(w_zero, {a: 0, b: 1, c: 2}, output_tiles={w_zero: 0})
    self._check_compiled(comp_and, max_regs=8)
    ops_and = [isa.tensix_decode(w)[0] for w in comp_and.passes[0].body]
    self.assertIn("SFPAND", ops_and)
    self.assertNotIn("SFPENCC", ops_and)

    # 3. Equality check -> SFPSETCC
    w_eq = a.eq(b).where(c, a)
    comp_eq = compile_sfpu(w_eq, {a: 0, b: 1, c: 2}, output_tiles={w_eq: 0})
    self._check_compiled(comp_eq, max_regs=8)
    ops_eq = [isa.tensix_decode(w)[0] for w in comp_eq.passes[0].body]
    self.assertIn("SFPSETCC", ops_eq)

    # 4. Integer lane_id() < 16 comparison -> uses L15 (LANE_X2) + SFPCAST(mod=3) + SFPGT
    w_lane = (lane_id() < 16).where(a, 0.0)
    comp_lane = compile_sfpu(w_lane, {a: 0}, output_tiles={w_lane: 0})
    self._check_compiled(comp_lane, max_regs=8)
    ops_lane = [isa.tensix_decode(w)[0] for w in comp_lane.passes[0].body]
    self.assertIn("SFPSHFT", ops_lane)
    self.assertIn("SFPCAST", ops_lane)

    # 5. Integer / boolean output stores with SfpuFormat.INT32 (never FP32 which flushes small ints!)
    mask_out = a < b
    comp_mask = compile_sfpu(mask_out, {a: 0, b: 1}, output_tiles={mask_out: 0})
    self._check_compiled(comp_mask, max_regs=8)
    stores = [isa.tensix_decode(w)[1] for w in comp_mask.passes[-1].body if (w >> 24) == 0x72]
    self.assertEqual(stores[-1]["instr_mod0"], isa.SfpuFormat.INT32)

  def test_transp_clobber_barrier(self):
    # SFPTRANSP permutes all of L0..L7; live values across it must be spilled into separate passes with VD=0.
    a = self._make_dst("a")
    b = self._make_dst("b")
    t = sfpu_prim("TRANSP", dtypes.fp32, a + 1.0)
    y = t + (b * 2.0)
    comp = compile_sfpu(y, {a: 0, b: 1}, output_tiles={y: 0})
    self._check_compiled(comp, max_regs=8)
    all_body = [w for p in comp.passes for w in p.body]
    transps = [isa.tensix_decode(w)[1] for w in all_body if (w >> 24) == 0x8C]
    self.assertEqual(len(transps), 1)
    self.assertEqual(transps[0]["lreg_dest"], 0)

  def test_dst_no_store_before_load_aliasing_and_const_and_dup_roots(self):
    a = self._make_dst("a")
    b = self._make_dst("b")

    # Bug #1 regression: two inputs (tiles 0, 1), early output depends only on `a`, second depends on `b`.
    # Must NEVER store over tile 1 before loading `b` from tile 1!
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


if __name__ == "__main__":
  unittest.main()
