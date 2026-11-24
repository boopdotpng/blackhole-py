import gc, math, unittest
import numpy as np
import hw
from hw import isa
from compiler import (
  Fidelity, KernelArg, Ops, PatternMatcher, Space, UOp, UPat, VerifyError, dtypes, evaluate, graph_rewrite,
  lower_reduce_to_loop, pretty, simplify, special_axes, substitute, verify,
)

class TestUOpCore(unittest.TestCase):
  def test_hash_consing_and_arg_distinction(self):
    c_i = UOp.const(dtypes.i32, 1)
    c_f = UOp.const(dtypes.fp32, 1.0)
    c_b = UOp.const(dtypes.bool, True)
    self.assertIs(c_i, UOp.const(dtypes.i32, 1))
    self.assertIsNot(c_i, c_f)
    self.assertIsNot(c_i, c_b)
    self.assertNotIn("e5m2", dtypes._by_name)

    pos0 = UOp.const(dtypes.fp32, 0.0)
    neg0 = UOp.const(dtypes.fp32, -0.0)
    self.assertIsNot(pos0, neg0)
    self.assertIs(neg0, UOp.const(dtypes.fp32, -0.0))

    nan1 = UOp.const(dtypes.fp32, float("nan"))
    nan2 = UOp.const(dtypes.fp32, float("nan"))
    self.assertIs(nan1, nan2)

    cid = UOp.special(119, "core_id")
    self.assertIs(cid + 1, cid + 1)
    self.assertEqual(hash(cid + 1), hash(cid + 1))
    with self.assertRaises(AttributeError):
      cid.arg = "other"

  def test_weakref_eviction(self):
    u = UOp.const(dtypes.i32, 987654321)
    uid = id(u)
    del u
    gc.collect()
    u2 = UOp.const(dtypes.i32, 987654321)
    self.assertEqual(u2.arg, 987654321)
    self.assertIsInstance(uid, int)

  def test_substitute_and_diamond(self):
    cid = UOp.special(119, "core_id")
    r = UOp.range(10, axis=0, name="i")
    x = r + 1
    y = x * x
    self.assertIs(substitute(r, {r: cid}), cid)
    self.assertIs(substitute(y, {r: cid}), (cid + 1) * (cid + 1))

  def test_upat_and_graph_rewrite(self):
    a = UOp.buffer("a", (32, 32), dtypes.bf16).noc_read(0).unpack(Space.DST, dtypes.fp32)
    expr = (a + a) * 2.0
    pm = PatternMatcher([
      (UPat(Ops.ADD, space=Space.DST, src=(UPat.var("x"), UPat.var("x"))), lambda x: x * 2.0),
      (UPat(Ops.MUL, src=[UPat(Ops.MUL, src=[UPat.var("x"), UPat.const("c1")]), UPat.const("c2")]),
       lambda x, c1, c2: x * (c1.arg * c2.arg)),
    ])
    self.assertIs(graph_rewrite(expr, pm), a * 4.0)

    cx, cy = UOp.special(12, "core_x"), UOp.special(10, "core_y")
    pm_bu = PatternMatcher([
      (UPat.any(UPat(Ops.SPECIAL, arg="core_x"), UPat(Ops.SPECIAL, arg="core_y")).named("c"),
       lambda c: UOp.const(dtypes.i32, 7)),
    ])
    self.assertIs(simplify(graph_rewrite(cx + cy, pm_bu, bottom_up=True)), UOp.const(dtypes.i32, 14))

  def test_rewrite_cycle_detection(self):
    cid = UOp.special(119, "core_id")
    pm_cycle = PatternMatcher([(UPat(Ops.NEG, src=(UPat.var("x"),)), lambda x: -(-x))])
    with self.assertRaises(RuntimeError):
      graph_rewrite(-cid, pm_cycle, limit=200)

class TestLayer1OpsAndVerify(unittest.TestCase):
  def test_simplify_identities_and_float_safety(self):
    cid = UOp.special(119, "core_id")
    cx, cy = UOp.special(12, "core_x"), UOp.special(10, "core_y")
    self.assertIs(simplify((cid + 0) * 1 // 1), cid)
    self.assertIs(simplify(cid * 0), UOp.const(dtypes.i32, 0))
    self.assertIs(simplify(cid - cid), UOp.const(dtypes.i32, 0))
    self.assertIs(simplify(-(-cid)), cid)
    self.assertIs(simplify((cid < cid).where(cx, cy)), cy)

    a = UOp.buffer("a", (32, 32), dtypes.fp32).noc_read(0).unpack(Space.DST, dtypes.fp32)
    self.assertEqual(simplify(a * 0.0).op, Ops.MUL)
    self.assertIs(simplify(a * 1.0 + 0.0), a)

  def test_special_axes_multicast_detection(self):
    cx, cy = UOp.special(12, "core_x"), UOp.special(10, "core_y")
    col_only = cx * 16 + UOp.range(16, axis=0)
    row_only = cy * 16 + UOp.range(16, axis=0)
    self.assertEqual(special_axes(col_only), {"core_x"})
    self.assertEqual(special_axes(row_only), {"core_y"})

  def test_fpu_detection_and_fidelity_auto_and_override(self):
    bf16_b = UOp.buffer("b16", (32, 32), dtypes.bf16)
    bfp8_b = UOp.buffer("b8", (32, 32), dtypes.bfp8)
    e4m3_b = UOp.buffer("e4", (32, 32), dtypes.e4m3)
    fp32_b = UOp.buffer("f32", (32, 32), dtypes.fp32)

    sa_16 = bf16_b.noc_read(0).unpack(Space.SRCA)
    sb_16 = bf16_b.noc_read(0).unpack(Space.SRCB)
    sa_8  = bfp8_b.noc_read(0).unpack(Space.SRCA)
    sb_8  = bfp8_b.noc_read(0).unpack(Space.SRCB)
    sa_e4 = e4m3_b.noc_read(0).unpack(Space.SRCA)
    sa_32 = fp32_b.noc_read(0).unpack(Space.SRCA, allow_tf32=True)

    # Auto-populated fidelity on MVMUL and FPU elementwise ops
    self.assertEqual(sb_8.mvmul(sa_8).fidelity, Fidelity.LOFI)
    self.assertEqual(sb_8.mvmul(sa_e4).fidelity, Fidelity.LOFI)
    self.assertEqual(sb_16.mvmul(sa_8).fidelity, Fidelity.HIFI2)
    self.assertEqual(sb_16.mvmul(sa_16).fidelity, Fidelity.HIFI2)
    self.assertEqual(sb_16.mvmul(sa_32).fidelity, Fidelity.HIFI4)

    # Mixed-dtype FPU elementwise + override
    elw_mixed = sa_8 * sb_16
    self.assertTrue(elw_mixed.is_fpu)
    self.assertEqual(elw_mixed.dtype, dtypes.bf16)
    self.assertEqual(elw_mixed.fidelity, Fidelity.HIFI2)
    self.assertEqual(elw_mixed.with_fidelity(Fidelity.HIFI4).fidelity, Fidelity.HIFI4)
    self.assertEqual(sb_16.mvmul(sa_16, fidelity=Fidelity.HIFI4).fidelity, Fidelity.HIFI4)
    self.assertEqual(sb_16.mvmul(sa_16).with_fidelity(Fidelity.HIFI3).fidelity, Fidelity.HIFI3)

    # Non-FPU ops report is_fpu=False and reject with_fidelity()
    dst_x = bf16_b.noc_read(0).unpack(Space.DST, dtypes.fp32)
    sfpu_op = dst_x * 2.0
    self.assertFalse(sfpu_op.is_fpu)
    self.assertIsNone(sfpu_op.fidelity)
    with self.assertRaises(ValueError):
      sfpu_op.with_fidelity(Fidelity.HIFI2)

  def test_replay_and_mop_escape_hatch(self):
    a_buf = UOp.buffer("a", (32, 32), dtypes.bf16)
    b_buf = UOp.buffer("b", (32, 32), dtypes.bf16)
    out_buf = UOp.buffer("out", (32, 32), dtypes.bf16)
    r = UOp.range(4, 0, "k")
    sa = a_buf.noc_read(r).unpack(Space.SRCA)
    sb = b_buf.noc_read(r).unpack(Space.SRCB)
    w = isa.MVMUL()
    rep1 = UOp.replay([w, w, w, w], sb, sa, r, name="mm4")
    rep2 = UOp.replay([w, w, w, w], sb, sa, r, name="mm4")
    self.assertIs(rep1, rep2)
    self.assertEqual(len(rep1.arg.insns), 4)
    self.assertEqual(rep1.src, (sb, sa, r))

    m = UOp.mop([0] * isa.MOP_CFG_WORDS, rep1, name="mm_mop")
    acc = m.reduce(r, op=Ops.ADD, space=Space.DST)
    sink = UOp.sink(out_buf.noc_write(0, acc.pack(dtypes.bf16)), arg=KernelArg("replay_test", 119))
    verify(sink)
    self.assertIn("REPLAY", pretty(sink))
    self.assertIn("MOP", pretty(sink))

    with self.assertRaises(VerifyError):
      verify(UOp.sink(UOp.replay([w] * 33)))
    with self.assertRaises(VerifyError):
      verify(UOp.sink(UOp.mop([0, 1, 2])))

  def test_verify_catches_hardware_violations(self):
    a_f32 = UOp.buffer("a", (32, 32), dtypes.fp32)
    a_bf16 = UOp.buffer("b", (32, 32), dtypes.bf16)
    out = UOp.buffer("out", (32, 32), dtypes.bf16)

    # 1. FP32 unpack to SRCA/SRCB rejected unless allow_tf32=True
    with self.assertRaises(VerifyError):
      verify(UOp.sink(a_f32.noc_read(0).unpack(Space.SRCA)))
    verify(UOp.sink(a_f32.noc_read(0).unpack(Space.SRCA, allow_tf32=True)))
    verify(UOp.sink(a_f32.noc_read(0).unpack(Space.DST)))

    # 2. Unclosed RANGE leaking into SINK
    r = UOp.range(8, axis=0, name="leaked")
    with self.assertRaises(VerifyError):
      verify(UOp.sink(out.noc_write(r, a_bf16.noc_read(r))))

    # 3. MVMUL operand space order (must be SRCB, SRCA)
    sa = a_bf16.noc_read(0).unpack(Space.SRCA)
    sb = a_bf16.noc_read(0).unpack(Space.SRCB)
    with self.assertRaises(VerifyError):
      verify(UOp.sink(sa.mvmul(sb)))
    verify(UOp.sink(sb.mvmul(sa)))

    # 4. FPU elementwise allowed on SRCA/SRCB (+, -, *, max), SFPU-only (exp2) rejected on SRCA
    verify(UOp.sink(sa + sb))
    with self.assertRaises(VerifyError):
      verify(UOp.sink(sa.exp2()))

    # 5. ALU directly on L1 without unpack rejected
    with self.assertRaises(VerifyError):
      verify(UOp.sink(a_bf16.noc_read(0) + 1.0))

    # 6. PACK from non-DST rejected
    with self.assertRaises(VerifyError):
      verify(UOp.sink(sa.pack(dtypes.bf16)))

    # 7. L1 REDUCE over PACK requires l1_acc=True
    rk = UOp.range(4, axis=1, name="k")
    p_no_acc = a_bf16.noc_read(rk).unpack(Space.DST, dtypes.fp32).pack(dtypes.fp32, l1_acc=False)
    with self.assertRaises(VerifyError):
      verify(UOp.sink(p_no_acc.reduce(rk, op=Ops.ADD, space=Space.L1)))
    p_acc = a_bf16.noc_read(rk).unpack(Space.DST, dtypes.fp32).pack(dtypes.fp32, l1_acc=True)
    verify(UOp.sink(p_acc.reduce(rk, op=Ops.ADD, space=Space.L1)))

class TestLayer1Evaluation(unittest.TestCase):
  def test_slice1_silu_mul_full_p100a_grid(self):
    # Gated noc_read / noc_write
    num_tiles = 300
    cores = 119
    tiles_per_core = math.ceil(num_tiles / cores)

    a_buf = UOp.buffer("a", (num_tiles, 32, 32), dtypes.bf16)
    b_buf = UOp.buffer("b", (num_tiles, 32, 32), dtypes.bf16)
    out_buf = UOp.buffer("out", (num_tiles, 32, 32), dtypes.bf16)

    r = UOp.range(tiles_per_core, 0, "t")
    tile_idx = UOp.special(cores, "core_id") + r * cores
    valid = tile_idx < num_tiles
    a_dst = a_buf.noc_read(tile_idx, gate=valid, depth=2, cap=2).unpack(Space.DST, dtypes.fp32)
    b_dst = b_buf.noc_read(tile_idx, gate=valid, depth=2, cap=2).unpack(Space.DST, dtypes.fp32)
    y_dst = a_dst.silu() * b_dst
    sink = UOp.sink(out_buf.noc_write(tile_idx, y_dst.pack(dtypes.bf16), gate=valid).end(r), arg=KernelArg("silu_mul", cores))

    rng = np.random.default_rng(0)
    a_np = rng.standard_normal((num_tiles, 32, 32)).astype(np.float32)
    b_np = rng.standard_normal((num_tiles, 32, 32)).astype(np.float32)
    out_np = np.zeros_like(a_np)
    evaluate(sink, {"a": a_np, "b": b_np, "out": out_np})

    expected = (a_np / (1.0 + np.exp(-a_np))) * b_np
    np.testing.assert_allclose(out_np, expected, rtol=2e-2, atol=2e-2)

  def test_matmul_2d_multicast(self):
    rows, cols = hw.WORKER_ROWS, 2
    MT, NT, KT = 10, 4, 4
    m_per, n_per = MT // rows, NT // cols

    A = UOp.buffer("A", (MT * KT, 32, 32), dtypes.bf16)
    B = UOp.buffer("B", (KT * NT, 32, 32), dtypes.bf16)
    O = UOp.buffer("O", (MT * NT, 32, 32), dtypes.bf16)

    rm, rn, rk = UOp.range(m_per, 0, "m"), UOp.range(n_per, 1, "n"), UOp.range(KT, 2, "k")
    mt = UOp.special(rows, "core_y") * m_per + rm
    nt = UOp.special(cols, "core_x") * n_per + rn
    a_l1 = A.noc_read(mt * KT + rk).noc_mcast(rect="row", sender=rk % cols)
    b_l1 = B.noc_read(rk * NT + nt).noc_mcast(rect="col", sender=rk % rows)

    acc = a_l1.unpack(Space.SRCB).mvmul(b_l1.unpack(Space.SRCA)).reduce(rk, op=Ops.ADD, space=Space.DST)
    sink = UOp.sink(O.noc_write(mt * NT + nt, acc.pack(dtypes.bf16)).end(rm, rn), arg=KernelArg("matmul_2d_mcast", rows * cols))

    rng = np.random.default_rng(1)
    a_tiles = rng.standard_normal((MT, KT, 32, 32)).astype(np.float32) * 0.2
    b_tiles = rng.standard_normal((KT, NT, 32, 32)).astype(np.float32) * 0.2
    o_tiles = np.zeros((MT, NT, 32, 32), dtype=np.float32)
    evaluate(sink, {"A": a_tiles.reshape(-1, 32, 32), "B": b_tiles.reshape(-1, 32, 32), "O": o_tiles.reshape(-1, 32, 32)})

    a_mat = a_tiles.transpose(0, 2, 1, 3).reshape(MT * 32, KT * 32)
    b_mat = b_tiles.transpose(0, 2, 1, 3).reshape(KT * 32, NT * 32)
    o_mat = o_tiles.transpose(0, 2, 1, 3).reshape(MT * 32, NT * 32)
    np.testing.assert_allclose(o_mat, a_mat @ b_mat, rtol=3e-2, atol=3e-2)

  def test_l1_acc_dst_alloc_sfpu_row_ops_if_and_host_stream(self):
    X = UOp.buffer("X", (4, 32, 32), dtypes.fp32)
    Y = UOp.buffer("Y", (2, 32, 32), dtypes.fp32)
    tok = UOp.buffer("tokens", (2,), dtypes.i32, Space.HOST)

    cid = UOp.special(2, "core_id")
    rk = UOp.range(2, 0, "k")
    x_dst = X.noc_read(cid * 2 + rk).unpack(Space.DST, dtypes.fp32)
    summed_l1 = x_dst.pack(dtypes.fp32, l1_acc=True).reduce(rk, op=Ops.ADD, space=Space.L1)
    s_dst = summed_l1.unpack(Space.DST, dtypes.fp32)
    row_max = s_dst.reduce_row(Ops.MAX)
    masked = (UOp.lane_id() < 16).where(s_dst - row_max, 0.0)

    acc_slot = UOp.alloc("state", Space.DST, dtypes.fp32)
    st_acc = acc_slot.store(masked)
    final_dst = acc_slot.load().after(st_acc)
    sink = UOp.sink(Y.noc_write(cid, final_dst.pack(dtypes.fp32)), UOp.barrier("all"),
                    cid.eq(0).if_(tok.noc_write(0, UOp.const(dtypes.i32, 777))), arg=KernelArg("multi_stage", 2))

    rng = np.random.default_rng(2)
    x_np = rng.standard_normal((4, 32, 32)).astype(np.float32)
    y_np = np.zeros((2, 32, 32), dtype=np.float32)
    tok_np = np.zeros((2,), dtype=np.int32)
    evaluate(sink, {"X": x_np, "Y": y_np, "tokens": tok_np})

    for cid in range(2):
      s = x_np[cid * 2] + x_np[cid * 2 + 1]
      ref = np.where(np.arange(32)[:, None] % 4 < 2, s - s.max(axis=-1, keepdims=True), 0.0)
      np.testing.assert_allclose(y_np[cid], ref, rtol=1e-5, atol=1e-5)
    np.testing.assert_array_equal(tok_np, np.array([777, 0], dtype=np.int32))

  def test_fpu_elw_via_python_ops_and_argmax(self):
    A = UOp.buffer("A", (1, 32, 32), dtypes.bf16)
    B = UOp.buffer("B", (1, 32, 32), dtypes.bf16)
    OUT = UOp.buffer("OUT", (1, 32, 32), dtypes.fp32)
    IDX = UOp.buffer("IDX", (1, 32, 32), dtypes.i32)

    sa = A.noc_read(0).unpack(Space.SRCA)
    sb = B.noc_read(0).unpack(Space.SRCB)
    # Plain Python + on SRCA/SRCB -> FPU ELWADD into DST
    added = (sa + sb).cast(dtypes.fp32)
    a_dst = A.noc_read(0).unpack(Space.DST, dtypes.fp32)
    y = (added - a_dst).gelu()
    idx = y.argmax()
    sink = UOp.sink(OUT.noc_write(0, y.pack(dtypes.fp32)), IDX.noc_write(0, idx.pack(dtypes.i32)),
                    arg=KernelArg("fpu_elw_and_argmax", 1))

    rng = np.random.default_rng(3)
    a_np = rng.standard_normal((1, 32, 32)).astype(np.float32)
    b_np = rng.standard_normal((1, 32, 32)).astype(np.float32)
    out_np = np.zeros((1, 32, 32), dtype=np.float32)
    idx_np = np.zeros((1, 32, 32), dtype=np.int32)
    evaluate(sink, {"A": a_np, "B": b_np, "OUT": out_np, "IDX": idx_np})

    c = math.sqrt(2.0 / math.pi)
    ref = 0.5 * b_np * (1.0 + np.tanh(c * (b_np + 0.044715 * (b_np ** 3))))
    np.testing.assert_allclose(out_np, ref, rtol=2e-2, atol=2e-2)
    np.testing.assert_array_equal(idx_np[0, :, 0], np.argmax(out_np[0], axis=-1))

  def test_loop_carry_coupled_state_and_lreg_decode_rmsnorm(self):
    # 1. Coupled multi-tile carried Dst state (online softmax-like max + rescaled sum over 3 tiles)
    X = UOp.buffer("X", (3, 32, 32), dtypes.fp32)
    M_OUT = UOp.buffer("M", (1, 32, 32), dtypes.fp32)
    L_OUT = UOp.buffer("L", (1, 32, 32), dtypes.fp32)
    r = UOp.range(3, 0, "t")
    xt = X.noc_read(r).unpack(Space.DST, dtypes.fp32)
    m_fin, l_fin = r.loop((UOp.const(dtypes.fp32, -math.inf), UOp.const(dtypes.fp32, 0.0)), lambda m, l: (
        (m_new := m.maximum(xt)),
        l * (m - m_new).exp() + (xt - m_new).exp(),
      ), spaces=(Space.DST, Space.DST))
    sink = UOp.sink(M_OUT.noc_write(0, m_fin.pack(dtypes.fp32)), L_OUT.noc_write(0, l_fin.pack(dtypes.fp32)),
                    arg=KernelArg("coupled_carry", 1))

    rng = np.random.default_rng(11)
    x_np = rng.uniform(-2.0, 2.0, (3, 32, 32)).astype(np.float32)
    m_np, l_np = np.zeros((1, 32, 32), dtype=np.float32), np.zeros((1, 32, 32), dtype=np.float32)
    evaluate(sink, {"X": x_np, "M": m_np, "L": l_np})
    ref_m = np.max(x_np, axis=0)
    ref_l = np.sum(np.exp(x_np - ref_m), axis=0)
    np.testing.assert_allclose(m_np[0], ref_m, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(l_np[0], ref_l, rtol=1e-5, atol=1e-5)

    # 2. Decode RMSNorm with Space.LREG reduction + lower_reduce_to_loop + reduce_lanes
    G = UOp.buffer("G", (1, 32, 32), dtypes.fp32)
    Y = UOp.buffer("Y", (1, 32, 32), dtypes.fp32)
    rt = UOp.range(3, 0, "t")
    x_tile = X.noc_read(rt).unpack(Space.DST, dtypes.fp32)
    acc_lreg = (x_tile * x_tile).reduce(rt, op=Ops.ADD, space=Space.LREG)
    inv_rms = (acc_lreg.reduce_lanes(Ops.ADD, "all") * (1.0 / (3 * 1024)) + 1e-5).rsqrt()
    self.assertEqual(inv_rms.space, Space.LREG)
    x0 = X.noc_read(0).unpack(Space.DST, dtypes.fp32)
    g0 = G.noc_read(0).unpack(Space.DST, dtypes.fp32)
    sink_red = UOp.sink(Y.noc_write(0, (x0 * inv_rms * g0).pack(dtypes.fp32)), arg=KernelArg("decode_rmsnorm", 1))
    sink_loop = lower_reduce_to_loop(sink_red)
    verify(sink_loop)
    self.assertNotIn(Ops.REDUCE, {u.op for u in sink_loop.toposort()})
    self.assertIn(Ops.LOOP, {u.op for u in sink_loop.toposort()})

    g_np = rng.uniform(0.5, 1.5, (1, 32, 32)).astype(np.float32)
    ref_rms = x_np[0] / np.sqrt(np.mean(x_np ** 2) + 1e-5) * g_np[0]
    for s in (sink_red, sink_loop):
      y_np = np.zeros((1, 32, 32), dtype=np.float32)
      evaluate(s, {"X": x_np, "G": g_np, "Y": y_np})
      np.testing.assert_allclose(y_np[0], ref_rms, rtol=1e-5, atol=1e-5)

    # 3. Verify catches CARRY init depending on its own RANGE and leaked CARRY
    bad_r = UOp.range(4, axis=9)
    with self.assertRaises(VerifyError):
      verify(UOp.sink((bad_r + 1).carry(bad_r, space=Space.SCALAR)))

if __name__ == "__main__":
  unittest.main()
