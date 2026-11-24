import gc, math, unittest
import numpy as np
import hw
from hw import isa
from compiler import (
  Fidelity, Grid, Kernel, Ops, PatternMatcher, Space, UOp, UPat, VerifyError,
  alloc, argmax, barrier, dram_buf, dtypes, end, evaluate, graph_rewrite,
  host_buf, if_uop, lane_id, load, mop, mvmul, noc_mcast, noc_read, noc_write,
  pack, pretty, range_uop, reduce, reduce_row, replay, simplify, special,
  special_axes, store, substitute, unpack, verify,
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

    cid = special("core_id", 119)
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
    cid = special("core_id", 119)
    r = range_uop(10, axis=0, name="i")
    x = r + 1
    y = x * x
    self.assertIs(substitute(r, {r: cid}), cid)
    self.assertIs(substitute(y, {r: cid}), (cid + 1) * (cid + 1))

  def test_upat_and_graph_rewrite(self):
    a = unpack(noc_read(dram_buf("a", (32, 32), dtypes.bf16), 0), Space.DST, dtypes.fp32)
    expr = (a + a) * 2.0
    pm = PatternMatcher([
      (UPat(Ops.ADD, space=Space.DST, src=(UPat.var("x"), UPat.var("x"))), lambda x: x * 2.0),
      (UPat(Ops.MUL, src=[UPat(Ops.MUL, src=[UPat.var("x"), UPat.const("c1")]), UPat.const("c2")]),
       lambda x, c1, c2: x * (c1.arg * c2.arg)),
    ])
    self.assertIs(graph_rewrite(expr, pm), a * 4.0)

    cx, cy = special("core_x", 12), special("core_y", 10)
    pm_bu = PatternMatcher([
      (UPat.any(UPat(Ops.SPECIAL, arg="core_x"), UPat(Ops.SPECIAL, arg="core_y")).named("c"),
       lambda c: UOp.const(dtypes.i32, 7)),
    ])
    self.assertIs(simplify(graph_rewrite(cx + cy, pm_bu, bottom_up=True)), UOp.const(dtypes.i32, 14))

  def test_rewrite_cycle_detection(self):
    cid = special("core_id", 119)
    pm_cycle = PatternMatcher([(UPat(Ops.NEG, src=(UPat.var("x"),)), lambda x: -(-x))])
    with self.assertRaises(RuntimeError):
      graph_rewrite(-cid, pm_cycle, limit=200)


class TestLayer1OpsAndVerify(unittest.TestCase):
  def test_simplify_identities_and_float_safety(self):
    cid = special("core_id", 119)
    cx, cy = special("core_x", 12), special("core_y", 10)
    self.assertIs(simplify((cid + 0) * 1 // 1), cid)
    self.assertIs(simplify(cid * 0), UOp.const(dtypes.i32, 0))
    self.assertIs(simplify(cid - cid), UOp.const(dtypes.i32, 0))
    self.assertIs(simplify(-(-cid)), cid)
    self.assertIs(simplify((cid < cid).where(cx, cy)), cy)

    a = unpack(noc_read(dram_buf("a", (32, 32), dtypes.fp32), 0), Space.DST, dtypes.fp32)
    self.assertEqual(simplify(a * 0.0).op, Ops.MUL)
    self.assertIs(simplify(a * 1.0 + 0.0), a)

  def test_special_axes_multicast_detection(self):
    cx, cy = special("core_x", 12), special("core_y", 10)
    col_only = cx * 16 + range_uop(16, axis=0)
    row_only = cy * 16 + range_uop(16, axis=0)
    self.assertEqual(special_axes(col_only), {"core_x"})
    self.assertEqual(special_axes(row_only), {"core_y"})

  def test_fpu_detection_and_fidelity_auto_and_override(self):
    bf16_b = dram_buf("b16", (32, 32), dtypes.bf16)
    bfp8_b = dram_buf("b8",  (32, 32), dtypes.bfp8)
    e4m3_b = dram_buf("e4",  (32, 32), dtypes.e4m3)
    fp32_b = dram_buf("f32", (32, 32), dtypes.fp32)

    sa_16 = unpack(noc_read(bf16_b, 0), Space.SRCA)
    sb_16 = unpack(noc_read(bf16_b, 0), Space.SRCB)
    sa_8  = unpack(noc_read(bfp8_b, 0), Space.SRCA)
    sb_8  = unpack(noc_read(bfp8_b, 0), Space.SRCB)
    sa_e4 = unpack(noc_read(e4m3_b, 0), Space.SRCA)
    sa_32 = unpack(noc_read(fp32_b, 0), Space.SRCA, allow_tf32=True)

    # Auto-populated fidelity on MVMUL and FPU elementwise ops
    self.assertEqual(mvmul(sb_8, sa_8).fidelity, Fidelity.LOFI)
    self.assertEqual(mvmul(sb_8, sa_e4).fidelity, Fidelity.LOFI)
    self.assertEqual(mvmul(sb_16, sa_8).fidelity, Fidelity.HIFI2)
    self.assertEqual(mvmul(sb_16, sa_16).fidelity, Fidelity.HIFI2)
    self.assertEqual(mvmul(sb_16, sa_32).fidelity, Fidelity.HIFI4)

    # Mixed-dtype FPU elementwise + override
    elw_mixed = sa_8 * sb_16
    self.assertTrue(elw_mixed.is_fpu)
    self.assertEqual(elw_mixed.dtype, dtypes.bf16)
    self.assertEqual(elw_mixed.fidelity, Fidelity.HIFI2)
    self.assertEqual(elw_mixed.with_fidelity(Fidelity.HIFI4).fidelity, Fidelity.HIFI4)
    self.assertEqual(mvmul(sb_16, sa_16, fidelity=Fidelity.HIFI4).fidelity, Fidelity.HIFI4)
    self.assertEqual(mvmul(sb_16, sa_16).with_fidelity(Fidelity.HIFI3).fidelity, Fidelity.HIFI3)

    # Non-FPU ops report is_fpu=False and reject with_fidelity()
    dst_x = unpack(noc_read(bf16_b, 0), Space.DST, dtypes.fp32)
    sfpu_op = dst_x * 2.0
    self.assertFalse(sfpu_op.is_fpu)
    self.assertIsNone(sfpu_op.fidelity)
    with self.assertRaises(ValueError):
      sfpu_op.with_fidelity(Fidelity.HIFI2)

  def test_replay_and_mop_escape_hatch(self):
    a_buf = dram_buf("a", (32, 32), dtypes.bf16)
    b_buf = dram_buf("b", (32, 32), dtypes.bf16)
    out_buf = dram_buf("out", (32, 32), dtypes.bf16)
    k = Kernel("replay_test", grid=119)
    r = k.range(4, "k")
    sa = unpack(noc_read(a_buf, r), Space.SRCA)
    sb = unpack(noc_read(b_buf, r), Space.SRCB)
    w = isa.MVMUL(addr_mode=0)
    rep1 = replay([w, w, w, w], sb, sa, r, name="mm4")
    rep2 = replay([w, w, w, w], sb, sa, r, name="mm4")
    self.assertIs(rep1, rep2)
    self.assertEqual(len(rep1.arg.insns), 4)
    self.assertEqual(rep1.src, (sb, sa, r))

    m = mop([0] * hw.MOP_CFG_WORDS, rep1, name="mm_mop")
    acc = reduce(m, r, op=Ops.ADD, space=Space.DST)
    k.emit(noc_write(out_buf, 0, pack(acc, dtypes.bf16)))
    sink = k.build()
    self.assertIn("REPLAY", pretty(sink))
    self.assertIn("MOP", pretty(sink))

    with self.assertRaises(VerifyError):
      verify(UOp.sink(replay([w] * 33)))
    with self.assertRaises(VerifyError):
      verify(UOp.sink(mop([0, 1, 2])))

  def test_verify_catches_hardware_violations(self):
    a_f32 = dram_buf("a", (32, 32), dtypes.fp32)
    a_bf16 = dram_buf("b", (32, 32), dtypes.bf16)
    out = dram_buf("out", (32, 32), dtypes.bf16)

    # 1. FP32 unpack to SRCA/SRCB rejected unless allow_tf32=True
    with self.assertRaises(VerifyError):
      verify(UOp.sink(unpack(noc_read(a_f32, 0), Space.SRCA)))
    verify(UOp.sink(unpack(noc_read(a_f32, 0), Space.SRCA, allow_tf32=True)))
    verify(UOp.sink(unpack(noc_read(a_f32, 0), Space.DST)))

    # 2. Unclosed RANGE leaking into SINK
    r = range_uop(8, axis=0, name="leaked")
    with self.assertRaises(VerifyError):
      verify(UOp.sink(noc_write(out, r, noc_read(a_bf16, r))))

    # 3. MVMUL operand space order (must be SRCB, SRCA)
    sa = unpack(noc_read(a_bf16, 0), Space.SRCA)
    sb = unpack(noc_read(a_bf16, 0), Space.SRCB)
    with self.assertRaises(VerifyError):
      verify(UOp.sink(mvmul(sa, sb)))
    verify(UOp.sink(mvmul(sb, sa)))

    # 4. FPU elementwise allowed on SRCA/SRCB (+, -, *, max), SFPU-only (exp2) rejected on SRCA
    verify(UOp.sink(sa + sb))
    with self.assertRaises(VerifyError):
      verify(UOp.sink(sa.exp2()))

    # 5. ALU directly on L1 without unpack rejected
    with self.assertRaises(VerifyError):
      verify(UOp.sink(noc_read(a_bf16, 0) + 1.0))

    # 6. PACK from non-DST rejected
    with self.assertRaises(VerifyError):
      verify(UOp.sink(pack(sa, dtypes.bf16)))

    # 7. L1 REDUCE over PACK requires l1_acc=True
    rk = range_uop(4, axis=1, name="k")
    p_no_acc = pack(unpack(noc_read(a_bf16, rk), Space.DST, dtypes.fp32), dtypes.fp32, l1_acc=False)
    with self.assertRaises(VerifyError):
      verify(UOp.sink(reduce(p_no_acc, rk, op=Ops.ADD, space=Space.L1)))
    p_acc = pack(unpack(noc_read(a_bf16, rk), Space.DST, dtypes.fp32), dtypes.fp32, l1_acc=True)
    verify(UOp.sink(reduce(p_acc, rk, op=Ops.ADD, space=Space.L1)))


class TestLayer1Evaluation(unittest.TestCase):
  def test_slice1_silu_mul_full_p100a_grid(self):
    # Slice 1 target kernel using gated noc_read / noc_write (no if_uop needed!)
    num_tiles = 300
    k = Kernel("silu_mul", grid=119)
    tiles_per_core = math.ceil(num_tiles / k.grid.cores)

    a_buf = dram_buf("a", (num_tiles, 32, 32), dtypes.bf16)
    b_buf = dram_buf("b", (num_tiles, 32, 32), dtypes.bf16)
    out_buf = dram_buf("out", (num_tiles, 32, 32), dtypes.bf16)

    r = k.range(tiles_per_core, "t")
    tile_idx = k.core_id + r * k.grid.cores
    valid = tile_idx < num_tiles
    a_dst = unpack(noc_read(a_buf, tile_idx, gate=valid, depth=2, cap=2), Space.DST, dtypes.fp32)
    b_dst = unpack(noc_read(b_buf, tile_idx, gate=valid, depth=2, cap=2), Space.DST, dtypes.fp32)
    y_dst = a_dst.silu() * b_dst
    k.emit(end(noc_write(out_buf, tile_idx, pack(y_dst, dtypes.bf16), gate=valid), r))
    sink = k.build()

    rng = np.random.default_rng(0)
    a_np = rng.standard_normal((num_tiles, 32, 32)).astype(np.float32)
    b_np = rng.standard_normal((num_tiles, 32, 32)).astype(np.float32)
    out_np = np.zeros_like(a_np)
    evaluate(sink, {"a": a_np, "b": b_np, "out": out_np})

    expected = (a_np / (1.0 + np.exp(-a_np))) * b_np
    np.testing.assert_allclose(out_np, expected, rtol=2e-2, atol=2e-2)

  def test_matmul_2d_multicast(self):
    R, C_cols = 2, 3
    grid = Grid(cores=R * C_cols, rows=R)
    MT, NT, KT = 4, 6, 4
    m_per, n_per = MT // R, NT // C_cols

    A = dram_buf("A", (MT * KT, 32, 32), dtypes.bf16)
    B = dram_buf("B", (KT * NT, 32, 32), dtypes.bf16)
    O = dram_buf("O", (MT * NT, 32, 32), dtypes.bf16)

    k = Kernel("matmul_2d_mcast", grid=grid)
    rm, rn, rk = k.range(m_per, "m"), k.range(n_per, "n"), k.range(KT, "k")

    mt = k.core_y * m_per + rm
    nt = k.core_x * n_per + rn
    a_l1 = noc_mcast(noc_read(A, mt * KT + rk), rect="row", sender=rk % grid.cols)
    b_l1 = noc_mcast(noc_read(B, rk * NT + nt), rect="col", sender=rk % grid.rows)

    acc = reduce(mvmul(unpack(a_l1, Space.SRCB), unpack(b_l1, Space.SRCA)), rk, op=Ops.ADD, space=Space.DST)
    k.emit(end(noc_write(O, mt * NT + nt, pack(acc, dtypes.bf16)), rm, rn))
    sink = k.build()

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
    X = dram_buf("X", (4, 32, 32), dtypes.fp32)
    Y = dram_buf("Y", (2, 32, 32), dtypes.fp32)
    tok = host_buf("tokens", (2,), dtypes.i32)

    k = Kernel("multi_stage", grid=2)
    rk = k.range(2, "k")
    x_dst = unpack(noc_read(X, k.core_id * 2 + rk), Space.DST, dtypes.fp32)
    summed_l1 = reduce(pack(x_dst, dtypes.fp32, l1_acc=True), rk, op=Ops.ADD, space=Space.L1)
    s_dst = unpack(summed_l1, Space.DST, dtypes.fp32)
    row_max = reduce_row(s_dst, Ops.MAX)
    masked = (lane_id() < 16).where(s_dst - row_max, 0.0)

    acc_slot = alloc("state", Space.DST, dtypes.fp32)
    st_acc = store(acc_slot, masked)
    final_dst = load(acc_slot).after(st_acc)
    k.emit(noc_write(Y, k.core_id, pack(final_dst, dtypes.fp32)))

    k.emit(barrier("all"))
    k.emit(if_uop(k.core_id.eq(0), noc_write(tok, 0, UOp.const(dtypes.i32, 777))))
    sink = k.build()

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
    A = dram_buf("A", (1, 32, 32), dtypes.bf16)
    B = dram_buf("B", (1, 32, 32), dtypes.bf16)
    OUT = dram_buf("OUT", (1, 32, 32), dtypes.fp32)
    IDX = dram_buf("IDX", (1, 32, 32), dtypes.i32)

    k = Kernel("fpu_elw_and_argmax", grid=1)
    sa = unpack(noc_read(A, 0), Space.SRCA)
    sb = unpack(noc_read(B, 0), Space.SRCB)
    # Plain Python + on SRCA/SRCB -> FPU ELWADD into DST!
    added = (sa + sb).cast(dtypes.fp32)
    a_dst = unpack(noc_read(A, 0), Space.DST, dtypes.fp32)
    y = (added - a_dst).gelu()
    idx = argmax(y)
    k.emit(noc_write(OUT, 0, pack(y, dtypes.fp32)), noc_write(IDX, 0, pack(idx, dtypes.i32)))
    sink = k.build()

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


if __name__ == "__main__":
  unittest.main()
