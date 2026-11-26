import json, math, struct, tempfile, unittest
from pathlib import Path
import numpy as np
from compiler import (
  Ops, Space, Tensor, UOp, Variable, VerifyError, dtypes, eval_tensor, get_state_dict, load_state_dict,
  pretty, safe_load, simplify_tensor, verify, verify_tensor,
)

class TestLayer0Ops(unittest.TestCase):
  def test_movement_ops_and_simplify(self):
    rng = np.random.default_rng(0)
    x_np = rng.standard_normal((2, 3, 4)).astype(np.float32)
    x = Tensor(x_np)

    np.testing.assert_allclose(x.reshape(6, 4).numpy(), x_np.reshape(6, 4))
    np.testing.assert_allclose(x.view(2, -1).numpy(), x_np.reshape(2, 12))
    np.testing.assert_allclose(x.permute(2, 0, 1).numpy(), x_np.transpose(2, 0, 1))
    np.testing.assert_allclose(x.transpose(1, 2).numpy(), x_np.swapaxes(1, 2))
    np.testing.assert_allclose(x.T.numpy(), x_np.T)
    np.testing.assert_allclose(x.mT.numpy(), np.swapaxes(x_np, -2, -1))
    np.testing.assert_allclose(x.flip(1).numpy(), np.flip(x_np, axis=1))
    np.testing.assert_allclose(x.flip(0, 2).numpy(), np.flip(x_np, axis=(0, 2)))
    np.testing.assert_allclose(x.shrink((None, (1, 3), (0, 2))).numpy(), x_np[:, 1:3, 0:2])
    np.testing.assert_allclose(x.pad(((0, 1), (1, 0), (0, 2))).numpy(), np.pad(x_np, ((0, 1), (1, 0), (0, 2))))
    np.testing.assert_allclose(x.pad((1, 2, 0, 1), value=-3.0).numpy(),
                               np.pad(x_np, ((0, 0), (0, 1), (1, 2)), constant_values=-3.0))

    # Squeeze / unsqueeze / repeat / roll / unfold / split / chunk / cat / stack
    np.testing.assert_allclose(x.unsqueeze(1).squeeze(1).numpy(), x_np)
    np.testing.assert_allclose(x.repeat(2, 1, 3).numpy(), np.tile(x_np, (2, 1, 3)))
    np.testing.assert_allclose(x.repeat_interleave(2, dim=1).numpy(), np.repeat(x_np, 2, axis=1))
    np.testing.assert_allclose(x.roll(1, dims=2).numpy(), np.roll(x_np, 1, axis=2))
    a, b = x.split([1, 2], dim=1)
    np.testing.assert_allclose(Tensor.cat([a, b], dim=1).numpy(), x_np)
    np.testing.assert_allclose(a.cat(b, dim=1).numpy(), x_np)
    np.testing.assert_allclose(Tensor.stack([x, x * 2.0], dim=0).numpy(), np.stack([x_np, x_np * 2.0], axis=0))
    np.testing.assert_allclose(x.stack(x * 2.0, dim=0).numpy(), np.stack([x_np, x_np * 2.0], axis=0))
    c0, c1 = x.chunk(2, dim=2)
    np.testing.assert_allclose(c0.cat(c1, dim=2).numpy(), x_np)

    # Unfold sliding window
    seq = Tensor.arange(6, dtype=dtypes.fp32)
    np.testing.assert_allclose(seq.unfold(0, 3, 1).numpy(), np.array([[0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5]], np.float32))

    # Simplifier folds nested movement ops
    folded = simplify_tensor(x.reshape(6, 4).reshape(24).reshape(2, 3, 4))
    self.assertIs(folded.uop, x.uop)
    folded_perm = simplify_tensor(x.permute(1, 2, 0).permute(2, 0, 1))
    self.assertIs(folded_perm.uop, x.uop)
    folded_flip = simplify_tensor(x.flip(1).flip(1))
    self.assertIs(folded_flip.uop, x.uop)

  def test_slicing_indexing_gather_scatter_and_assign(self):
    x_np = np.arange(24, dtype=np.float32).reshape(4, 6)
    x = Tensor(x_np)

    np.testing.assert_allclose(x[1].numpy(), x_np[1])
    np.testing.assert_allclose(x[:, 0::2].numpy(), x_np[:, 0::2])
    np.testing.assert_allclose(x[:, 1::2].numpy(), x_np[:, 1::2])
    np.testing.assert_allclose(x[::-1, ::-2].numpy(), x_np[::-1, ::-2])
    np.testing.assert_allclose(x[None, ..., -1].numpy(), x_np[None, ..., -1])

    idx = Tensor([3, 0, 2], dtype=dtypes.i32)
    np.testing.assert_allclose(x[idx].numpy(), x_np[[3, 0, 2]])
    np.testing.assert_allclose(x[:, idx].numpy(), x_np[:, [3, 0, 2]])

    # Multi-axis tensor indexing
    ri = Tensor([0, 2, 3], dtype=dtypes.i32)
    ci = Tensor([1, 4, 5], dtype=dtypes.i32)
    np.testing.assert_allclose(x[ri, ci].numpy(), x_np[[0, 2, 3], [1, 4, 5]])

    # gather (take_along_axis)
    g_idx = Tensor(np.array([[5, 0], [3, 2], [1, 4], [2, 2]], dtype=np.int32))
    np.testing.assert_allclose(x.gather(1, g_idx).numpy(), np.take_along_axis(x_np, g_idx.numpy(), axis=1))

    # In-place slice and dynamic-index assignment (KV cache / ring buffer pattern)
    cache = Tensor.zeros(5, 4, dtype=dtypes.fp32)
    row0 = Tensor([1.0, 2.0, 3.0, 4.0])
    row2 = Tensor([5.0, 6.0, 7.0, 8.0])
    cache[0] = row0
    pos = Tensor.buffer("pos", (), dtypes.i32)
    cache[pos] = row2
    got = cache.numpy({"pos": np.array(2, dtype=np.int32)})
    ref = np.zeros((5, 4), dtype=np.float32)
    ref[0] = [1, 2, 3, 4]
    ref[2] = [5, 6, 7, 8]
    np.testing.assert_allclose(got, ref)

  def test_elementwise_reductions_contractions_and_bf16(self):
    rng = np.random.default_rng(1)
    a_np = rng.standard_normal((16, 32)).astype(np.float32)
    b_np = rng.standard_normal((32, 24)).astype(np.float32)
    a, b = Tensor(a_np), Tensor(b_np)

    # Canonical contraction graph uses REDUCE_AXIS(ADD, MUL(...))
    mm = a @ b
    ops = {u.op for u in mm.uop.toposort()}
    self.assertIn(Ops.REDUCE_AXIS, ops)
    self.assertIn(Ops.MUL, ops)
    np.testing.assert_allclose(mm.numpy(), a_np @ b_np, rtol=1e-5, atol=1e-5)

    # Mixed quantized dtype contraction (bf16 @ bfp8 -> fp32 acc) preserves input dtypes in graph
    a_sym = Tensor.buffer("a", (32, 64), dtypes.bf16)
    w_sym = Tensor.buffer("w", (64, 32), dtypes.bfp8)
    y_sym = a_sym.matmul(w_sym, dtype=dtypes.fp32)
    self.assertEqual(y_sym.dtype, dtypes.fp32)
    self.assertEqual(y_sym.shape, (32, 32))
    self.assertIn("REDUCE_AXIS", y_sym.pretty())

    # Reductions, argmax, argmin, topk, softmax, softplus, activations
    v_np = rng.standard_normal((4, 12)).astype(np.float32)
    v = Tensor(v_np)
    np.testing.assert_allclose(v.sum(-1).numpy(), v_np.sum(-1), rtol=1e-5)
    np.testing.assert_allclose(v.max(-1).numpy(), v_np.max(-1))
    np.testing.assert_allclose(v.min(-1).numpy(), v_np.min(-1))
    np.testing.assert_allclose(v.mean(-1).numpy(), v_np.mean(-1), rtol=1e-5)
    np.testing.assert_allclose(v.var(-1).numpy(), v_np.var(-1, ddof=1), rtol=1e-5)
    np.testing.assert_array_equal(v.argmax(-1).numpy(), np.argmax(v_np, axis=-1))
    np.testing.assert_array_equal(v.argmin(-1).numpy(), np.argmin(v_np, axis=-1))
    np.testing.assert_array_equal(v.argmax().numpy(), np.argmax(v_np))

    tk = v.topk(3, dim=-1)
    ref_idx = np.argsort(-v_np, axis=-1, kind="stable")[:, :3]
    np.testing.assert_array_equal(tk.indices.numpy(), ref_idx)
    np.testing.assert_allclose(tk.values.numpy(), np.take_along_axis(v_np, ref_idx, axis=-1))

    np.testing.assert_allclose(v.softmax(-1).numpy(),
                               np.exp(v_np - v_np.max(-1, keepdims=True)) / np.exp(v_np - v_np.max(-1, keepdims=True)).sum(-1, keepdims=True),
                               rtol=1e-5, atol=1e-6)
    np.testing.assert_allclose(v.softplus().numpy(), np.log1p(np.exp(-np.abs(v_np))) + np.maximum(v_np, 0), rtol=1e-5, atol=1e-6)
    np.testing.assert_allclose(v.silu().numpy(), v_np / (1.0 + np.exp(-v_np)), rtol=1e-5, atol=1e-6)
    np.testing.assert_allclose(v.tanh().numpy(), np.tanh(v_np), rtol=1e-5, atol=1e-5)

    # BF16 where keeps BF16 when scalar is on the left
    scores_bf16 = Tensor(v_np, dtype=dtypes.bf16)
    masked = (Tensor.arange(12) > 5).where(-math.inf, scores_bf16)
    self.assertEqual(masked.dtype, dtypes.bf16)

  def test_layer_boundary_verification(self):
    # Layer 1 verify rejects Layer 0 tensor graphs
    t = Tensor.buffer("x", (32, 32), dtypes.bf16) + 1.0
    verify_tensor(t)
    with self.assertRaises(VerifyError):
      verify(UOp.sink(t.uop))

    # Layer 0 verify_tensor rejects Layer 1 hardware UOps
    l1 = UOp.buffer("a", (32, 32), dtypes.bf16).noc_read(0).unpack(Space.DST, dtypes.fp32)
    with self.assertRaises(VerifyError):
      verify_tensor(l1)

    # Layer 1 verify rejects MAX on SRCA/SRCB (Blackhole FPU has no ELWMAX)
    sa = UOp.buffer("a", (32, 32), dtypes.bf16).noc_read(0).unpack(Space.SRCA)
    sb = UOp.buffer("b", (32, 32), dtypes.bf16).noc_read(0).unpack(Space.SRCB)
    with self.assertRaises(VerifyError):
      verify(UOp.sink(sa.maximum(sb)))

class TestLayer0Models(unittest.TestCase):
  def test_llama_nanbeige_decode_block(self):
    rng = np.random.default_rng(10)
    V, D, H, KV, HD, MLP, T = 32, 16, 4, 2, 4, 24, 6
    embed_np = rng.standard_normal((V, D)).astype(np.float32)
    w_rms = rng.uniform(0.8, 1.2, (D,)).astype(np.float32)
    wq = rng.standard_normal((H * HD, D)).astype(np.float32) * 0.2
    wk = rng.standard_normal((KV * HD, D)).astype(np.float32) * 0.2
    wv = rng.standard_normal((KV * HD, D)).astype(np.float32) * 0.2
    wo = rng.standard_normal((D, H * HD)).astype(np.float32) * 0.2
    w_gate = rng.standard_normal((MLP, D)).astype(np.float32) * 0.2
    w_up = rng.standard_normal((MLP, D)).astype(np.float32) * 0.2
    w_down = rng.standard_normal((D, MLP)).astype(np.float32) * 0.2
    w_lm = rng.standard_normal((V, D)).astype(np.float32) * 0.2

    angles = np.arange(T, dtype=np.float32)[:, None] * (10000.0 ** (-np.arange(0, HD, 2, dtype=np.float32) / HD))
    cos_np, sin_np = np.cos(angles).astype(np.float32), np.sin(angles).astype(np.float32)

    def apply_rope_t(x: Tensor, c: Tensor, s: Tensor) -> Tensor:
      x1, x2 = x.chunk(2, dim=-1)
      return (x1 * c - x2 * s).cat(x1 * s + x2 * c, dim=-1)

    def apply_rope_np(x, c, s):
      x1, x2 = np.split(x, 2, axis=-1)
      return np.concatenate([x1 * c - x2 * s, x1 * s + x2 * c], axis=-1)

    # Run 3 sequential decode steps updating KV cache
    k_cache = Tensor.zeros(T, KV, HD)
    v_cache = Tensor.zeros(T, KV, HD)
    k_ref = np.zeros((T, KV, HD), dtype=np.float32)
    v_ref = np.zeros((T, KV, HD), dtype=np.float32)

    embed_t, rms_t = Tensor(embed_np), Tensor(w_rms)
    wq_t, wk_t, wv_t, wo_t = Tensor(wq), Tensor(wk), Tensor(wv), Tensor(wo)
    wg_t, wu_t, wd_t, lm_t = Tensor(w_gate), Tensor(w_up), Tensor(w_down), Tensor(w_lm)
    cos_t, sin_t = Tensor(cos_np), Tensor(sin_np)

    for pos, tok in enumerate([3, 17, 5]):
      x = embed_t[Tensor(tok, dtype=dtypes.i32)]
      h = x.rms_norm(rms_t, eps=1e-5)
      q = apply_rope_t(h.linear(wq_t).reshape(H, HD), cos_t[pos], sin_t[pos])
      k = apply_rope_t(h.linear(wk_t).reshape(KV, HD), cos_t[pos], sin_t[pos])
      v = h.linear(wv_t).reshape(KV, HD)
      k_cache[pos] = k
      v_cache[pos] = v

      # GQA SDPA over 0..pos
      q4 = q.reshape(1, H, 1, HD)
      k4 = k_cache[:pos + 1].permute(1, 0, 2).unsqueeze(0)
      v4 = v_cache[:pos + 1].permute(1, 0, 2).unsqueeze(0)
      attn = q4.scaled_dot_product_attention(k4, v4, enable_gqa=True).reshape(H * HD)
      x = x + attn.linear(wo_t)
      hm = x.rms_norm(rms_t, eps=1e-5)
      x = x + (hm.linear(wg_t).silu() * hm.linear(wu_t)).linear(wd_t)
      logits = x.linear(lm_t)
      nxt = logits.argmax()

      # NumPy reference
      xr = embed_np[tok]
      hr = xr / np.sqrt(np.mean(xr ** 2) + 1e-5) * w_rms
      qr = apply_rope_np((wq @ hr).reshape(H, HD), cos_np[pos], sin_np[pos])
      kr = apply_rope_np((wk @ hr).reshape(KV, HD), cos_np[pos], sin_np[pos])
      vr = (wv @ hr).reshape(KV, HD)
      k_ref[pos], v_ref[pos] = kr, vr
      k_rep = np.repeat(k_ref[:pos + 1].transpose(1, 0, 2), H // KV, axis=0)
      v_rep = np.repeat(v_ref[:pos + 1].transpose(1, 0, 2), H // KV, axis=0)
      sc = np.einsum("hd,htd->ht", qr, k_rep) / math.sqrt(HD)
      p = np.exp(sc - sc.max(-1, keepdims=True))
      p = p / p.sum(-1, keepdims=True)
      ar = np.einsum("ht,htd->hd", p, v_rep).reshape(-1)
      xr = xr + wo @ ar
      hmr = xr / np.sqrt(np.mean(xr ** 2) + 1e-5) * w_rms
      g, u = w_gate @ hmr, w_up @ hmr
      xr = xr + w_down @ ((g / (1.0 + np.exp(-g))) * u)
      ref_logits = w_lm @ xr

      np.testing.assert_allclose(logits.numpy(), ref_logits, rtol=1e-4, atol=1e-4)
      self.assertEqual(int(nxt.item()), int(np.argmax(ref_logits)))

  def test_qwen38_gdn_block(self):
    # Matches examples/qwen38_check.py: causal 4-tap conv + SiLU, L2 norm, softplus decay,
    # GDN delta-rule state recurrence, gated RMSNorm.
    rng = np.random.default_rng(20)
    VH, KH, D = 6, 2, 8
    C = KH * D * 2 + VH * D  # q, k, v channels
    taps_np = rng.standard_normal((4, C)).astype(np.float32) * 0.4
    expa_np = (0.05 + rng.random(VH) * 1.5).astype(np.float32)
    dtb_np = rng.standard_normal(VH).astype(np.float32) * 0.5
    gamma_np = (1.0 + rng.standard_normal(D) * 0.1).astype(np.float32)

    hist = Tensor.zeros(3, C)
    S = Tensor.zeros(VH, D, D)
    taps, expa, dtb, gamma = Tensor(taps_np), Tensor(expa_np), Tensor(dtb_np), Tensor(gamma_np)

    hist_ref = np.zeros((3, C), dtype=np.float32)
    S_ref = np.zeros((VH, D, D), dtype=np.float32)

    for _ in range(4):
      raw_np = rng.standard_normal(C).astype(np.float32) * 0.5
      a_np = rng.standard_normal(VH).astype(np.float32)
      b_np = rng.standard_normal(VH).astype(np.float32)
      z_np = rng.standard_normal((VH, D)).astype(np.float32)

      raw, a_t, b_t, z_t = Tensor(raw_np), Tensor(a_np), Tensor(b_np), Tensor(z_np)
      window = Tensor.cat([hist, raw[None]], dim=0)
      hist.assign(window[1:])
      conv = (window * taps).sum(0).silu()

      qk_w = KH * D
      q = conv[:qk_w].reshape(KH, D)
      k = conv[qk_w:2 * qk_w].reshape(KH, D)
      v = conv[2 * qk_w:].reshape(VH, D)
      q = (q * (q.square().sum(-1, keepdim=True) + 1e-6).rsqrt() * (1.0 / math.sqrt(D))).repeat_interleave(VH // KH, dim=0)
      k = (k * (k.square().sum(-1, keepdim=True) + 1e-6).rsqrt()).repeat_interleave(VH // KH, dim=0)

      decay = (-expa * (a_t + dtb).softplus()).exp()            # [VH]
      beta = b_t.sigmoid()                                      # [VH]
      pred = (k.unsqueeze(1) @ S).squeeze(1)                    # [VH, D]
      delta = beta.unsqueeze(-1) * (v - decay.unsqueeze(-1) * pred)
      S.assign(decay.reshape(VH, 1, 1) * S + k.unsqueeze(2) * delta.unsqueeze(1))
      y = (q.unsqueeze(1) @ S).squeeze(1)                       # [VH, D]
      out = y.rms_norm(gamma, eps=1e-6) * z_t.silu()

      # NumPy reference
      win_r = np.concatenate([hist_ref, raw_np[None]], axis=0)
      hist_ref = win_r[1:]
      c_r = (win_r * taps_np).sum(0)
      c_r = c_r / (1.0 + np.exp(-c_r))
      qr = c_r[:qk_w].reshape(KH, D)
      kr = c_r[qk_w:2 * qk_w].reshape(KH, D)
      vr = c_r[2 * qk_w:].reshape(VH, D)
      qr = np.repeat(qr / np.sqrt((qr ** 2).sum(-1, keepdims=True) + 1e-6) / math.sqrt(D), VH // KH, axis=0)
      kr = np.repeat(kr / np.sqrt((kr ** 2).sum(-1, keepdims=True) + 1e-6), VH // KH, axis=0)
      sp = np.maximum(a_np + dtb_np, 0) + np.log1p(np.exp(-np.abs(a_np + dtb_np)))
      dec_r = np.exp(-expa_np * sp)
      bet_r = 1.0 / (1.0 + np.exp(-b_np))
      for h in range(VH):
        del_r = bet_r[h] * (vr[h] - dec_r[h] * (kr[h] @ S_ref[h]))
        S_ref[h] = dec_r[h] * S_ref[h] + np.outer(kr[h], del_r)
      yr = np.einsum("hd,hde->he", qr, S_ref)
      out_r = yr / np.sqrt((yr ** 2).mean(-1, keepdims=True) + 1e-6) * gamma_np * (z_np / (1.0 + np.exp(-z_np)))

      np.testing.assert_allclose(out.numpy(), out_r, rtol=1e-4, atol=1e-4)
      np.testing.assert_allclose(S.numpy(), S_ref, rtol=1e-4, atol=1e-4)

  def test_inkling_attention_dconv_mix_and_moe(self):
    # Exercises Inkling-specific ops from examples/inkling/reference.py:
    # block attention residual mix, l2clip, dynamic dconv with flip(0), relative-bias attention
    # with sink logits and einsum, sigmoid top-k MoE router, softcapped interleaved SwiGLU.
    rng = np.random.default_rng(30)
    D, H, KV, HD, EXT, N, E, K_EXP, MLP = 16, 4, 2, 4, 5, 4, 8, 2, 12
    group = H // KV

    def l2clip_t(x: Tensor, thr: float) -> Tensor:
      norm = x.square().sum(-1, keepdim=True).sqrt()
      return x * (thr / (norm + 1e-6)).clamp(max_=1.0)

    def l2clip_np(x, thr):
      norm = np.linalg.norm(x, axis=-1, keepdims=True)
      return x * np.minimum(thr / (norm + 1e-6), 1.0)

    # 1. Block attention residual mix
    b0_np, cur_np = rng.standard_normal((D,)).astype(np.float32), rng.standard_normal((D,)).astype(np.float32)
    q_mix_np = rng.standard_normal((2, D)).astype(np.float32) * 0.3
    s_t = Tensor.stack([Tensor(b0_np), Tensor(cur_np)], dim=0).rms_norm(eps=1e-6)
    p_t = (Tensor(q_mix_np).view(-1, D) @ s_t.T * (1.0 / math.sqrt(D))).softmax(-1)
    mix_t = p_t @ s_t

    s_r = np.stack([b0_np, cur_np], axis=0)
    s_r = s_r / np.sqrt((s_r ** 2).mean(-1, keepdims=True) + 1e-6)
    sc_r = (q_mix_np @ s_r.T) / math.sqrt(D)
    p_r = np.exp(sc_r - sc_r.max(-1, keepdims=True)); p_r /= p_r.sum(-1, keepdims=True)
    np.testing.assert_allclose(mix_t.numpy(), p_r @ s_r, rtol=1e-5, atol=1e-5)

    # 2. Dynamic depthwise conv with flip(0)
    hist_np = rng.standard_normal((3, KV * HD)).astype(np.float32)
    x_np = rng.standard_normal((KV * HD,)).astype(np.float32)
    static_np = rng.standard_normal((4, KV * HD)).astype(np.float32) * 0.2
    dyn_np = rng.standard_normal((KV * 4,)).astype(np.float32) * 0.2
    win = Tensor.cat([Tensor(hist_np), Tensor(x_np)[None]], dim=0)
    lags = win.flip(0)
    w_dconv = Tensor(static_np).T.reshape(KV, HD, 4) + Tensor(dyn_np).view(KV, 1, 4)
    dconv_t = ((lags.T.reshape(KV, HD, 4) * w_dconv).sum(-1).reshape(-1) + Tensor(x_np)) * (1.0 / math.sqrt(9.0))

    win_r = np.concatenate([hist_np, x_np[None]], axis=0)
    w_r = static_np.T.reshape(KV, HD, 4) + dyn_np.reshape(KV, 1, 4)
    dconv_r = ((np.flip(win_r, axis=0).T.reshape(KV, HD, 4) * w_r).sum(-1).reshape(-1) + x_np) / math.sqrt(9.0)
    np.testing.assert_allclose(dconv_t.numpy(), dconv_r, rtol=1e-5, atol=1e-5)

    # 3. Relative-bias attention with sink logits & einsum
    q_np = rng.standard_normal((H, HD)).astype(np.float32)
    K_np = rng.standard_normal((N, KV, HD)).astype(np.float32)
    V_np = rng.standard_normal((N, KV, HD)).astype(np.float32)
    rel_np = rng.standard_normal((H, EXT)).astype(np.float32) * 0.3
    sink_np = rng.standard_normal((H,)).astype(np.float32) * 0.5
    q_c = l2clip_t(Tensor(q_np), 1.5)
    dist = (N - 1) - Tensor.arange(0, N, dtype=dtypes.i32)
    rel_t = Tensor(rel_np)
    bias = (dist < EXT).where(rel_t[:, dist.clamp(max_=EXT - 1)], 0.0)
    scores = Tensor.einsum("khd,nkd->khn", q_c.view(KV, group, HD), Tensor(K_np)).reshape(H, N) * (1.0 / math.sqrt(HD)) + bias
    p_attn = Tensor.cat([scores, Tensor(sink_np)[:, None]], dim=1).softmax(1)[:, :-1]
    out_attn = Tensor.einsum("khn,nkd->khd", p_attn.view(KV, group, N), Tensor(V_np)).reshape(-1)

    q_cr = l2clip_np(q_np, 1.5)
    dist_r = (N - 1) - np.arange(0, N)
    bias_r = np.where(dist_r < EXT, rel_np[:, np.minimum(dist_r, EXT - 1)], 0.0)
    sc_a = np.einsum("khd,nkd->khn", q_cr.reshape(KV, group, HD), K_np).reshape(H, N) / math.sqrt(HD) + bias_r
    cat_a = np.concatenate([sc_a, sink_np[:, None]], axis=1)
    pa_r = np.exp(cat_a - cat_a.max(1, keepdims=True)); pa_r = (pa_r / pa_r.sum(1, keepdims=True))[:, :-1]
    out_ar = np.einsum("khn,nkd->khd", pa_r.reshape(KV, group, N), V_np).reshape(-1)
    np.testing.assert_allclose(out_attn.numpy(), out_ar, rtol=1e-5, atol=1e-5)

    # 4. Sigmoid top-k MoE router + softcapped interleaved SwiGLU
    h_np = rng.standard_normal((D,)).astype(np.float32)
    w_router_np = rng.standard_normal((E, D)).astype(np.float32) * 0.4
    b_router_np = rng.standard_normal((E,)).astype(np.float32) * 0.1
    w13_np = rng.standard_normal((E, 2 * MLP, D)).astype(np.float32) * 0.2
    w2_np = rng.standard_normal((E, D, MLP)).astype(np.float32) * 0.2
    gc, uc, route_scale = 7.0, 7.0, 2.5

    h_t = Tensor(h_np)
    r_scores = (Tensor(w_router_np) @ h_t).sigmoid()
    idx = (r_scores + Tensor(b_router_np)).topk(K_EXP).indices
    w_moe = r_scores[idx]
    w_moe = w_moe / (w_moe.sum() + 1e-20) * route_scale
    # Gather selected expert weights and evaluate batched softcapped SwiGLU in one graph
    gu = (Tensor(w13_np)[idx] @ h_t.unsqueeze(-1)).squeeze(-1)  # [K_EXP, 2*MLP]
    g, u = gu[:, 0::2], gu[:, 1::2]
    act = (g / gc).tanh() * gc * g.sigmoid() * (u / uc).tanh() * uc
    ey = (Tensor(w2_np)[idx] @ act.unsqueeze(-1)).squeeze(-1)   # [K_EXP, D]
    moe_out = (w_moe.unsqueeze(-1) * ey).sum(0)

    rs_r = 1.0 / (1.0 + np.exp(-(w_router_np @ h_np)))
    idx_r = np.argsort(-(rs_r + b_router_np), kind="stable")[:K_EXP]
    wm_r = rs_r[idx_r]; wm_r = wm_r / (wm_r.sum() + 1e-20) * route_scale
    gu_r = w13_np[idx_r] @ h_np
    gr, ur = gu_r[:, 0::2], gu_r[:, 1::2]
    act_r = np.tanh(gr / gc) * gc * (1.0 / (1.0 + np.exp(-gr))) * np.tanh(ur / uc) * uc
    moe_r = (wm_r[:, None] * np.einsum("kdm,km->kd", w2_np[idx_r], act_r)).sum(0)
    np.testing.assert_allclose(moe_out.numpy(), moe_r, rtol=1e-4, atol=1e-4)

  def test_disk_bytes_safetensors_and_state_dict(self):
    # bytes / bytearray / Path / from_disk / data()
    raw = bytes(range(16))
    self.assertEqual(bytes(Tensor(raw).data()), raw)

    # Build a real .safetensors file with BF16, F32, I32, and F8_E4M3 tensors and load lazily
    w_f32 = np.array([[1.5, -2.0], [0.25, 4.0]], dtype=np.float32)
    w_bf16_f32 = np.array([0.5, -1.5, 3.0, 2.0], dtype=np.float32)
    w_bf16_u16 = (w_bf16_f32.view(np.uint32) >> 16).astype("<u2")
    w_i32 = np.array([7, -3, 42], dtype="<i4")
    # E4M3FN byte 0x38 = 1.0 (exp=7, man=0), 0x40 = 2.0 (exp=8, man=0), 0xB8 = -1.0
    w_e4m3 = np.array([0x38, 0x40, 0xB8], dtype=np.uint8)

    blobs = [
      ("lin.weight", "F32", [2, 2], w_f32.astype("<f4").tobytes()),
      ("norm.weight", "BF16", [4], w_bf16_u16.tobytes()),
      ("ids", "I32", [3], w_i32.tobytes()),
      ("scale", "F8_E4M3", [3], w_e4m3.tobytes()),
    ]
    header, off, body = {}, 0, bytearray()
    for name, dt, sh, b in blobs:
      header[name] = {"dtype": dt, "shape": sh, "data_offsets": [off, off + len(b)]}
      body.extend(b)
      off += len(b)
    hdr_bytes = json.dumps(header).encode("utf-8")

    with tempfile.TemporaryDirectory() as td:
      p = Path(td) / "model.safetensors"
      p.write_bytes(struct.pack("<Q", len(hdr_bytes)) + hdr_bytes + bytes(body))

      # Tensor(Path) lazy u8 disk view + slice .data()
      disk_t = Tensor(p)
      self.assertEqual(disk_t.dtype, dtypes.u8)
      self.assertEqual(int.from_bytes(disk_t[0:8].data(), "little"), len(hdr_bytes))

      # safe_load + get_state_dict + load_state_dict
      sd = safe_load(p)
      self.assertEqual(sd["lin.weight"].dtype, dtypes.fp32)
      self.assertEqual(sd["norm.weight"].dtype, dtypes.bf16)
      self.assertEqual(sd["ids"].dtype, dtypes.i32)
      self.assertEqual(sd["scale"].dtype, dtypes.e4m3)

      from types import SimpleNamespace
      class _Mod:
        def __init__(self):
          self.lin = SimpleNamespace(weight=Tensor.empty(2, 2, dtype=dtypes.fp32))
          self.norm = SimpleNamespace(weight=Tensor.empty(4, dtype=dtypes.bf16))

      mod = _Mod()
      self.assertEqual(set(get_state_dict(mod).keys()), {"lin.weight", "norm.weight"})
      loaded = load_state_dict(mod, sd, strict=False)
      self.assertEqual(set(loaded), {"lin.weight", "norm.weight"})
      np.testing.assert_allclose(mod.lin.weight.numpy(), w_f32)
      np.testing.assert_allclose(mod.norm.weight.numpy(), w_bf16_f32)
      np.testing.assert_array_equal(sd["ids"].numpy(), w_i32)
      np.testing.assert_allclose(sd["scale"].numpy(), np.array([1.0, 2.0, -1.0], dtype=np.float32))

  def test_frontend_pm_and_llama3_graph(self):
    # Frontend PMs: stack -> shrink eliminates dead zero-padded branch; lossless bf16->fp32->bf16 folds;
    # float div by const -> mul by reciprocal; size-1 reduce strips.
    a = Tensor.buffer("a", (2, 4), dtypes.bf16)
    b = Tensor.buffer("b", (2, 4), dtypes.bf16)
    stacked_slice = simplify_tensor(Tensor.stack(a, b, dim=0)[0])
    self.assertIs(stacked_slice.uop, a.uop)

    roundtrip = simplify_tensor(a.float().bfloat16())
    self.assertIs(roundtrip.uop, a.uop)

    div_const = simplify_tensor(a.float() / 4.0)
    self.assertEqual(div_const.uop.op, Ops.MUL)

    # Tensor.assign builds STORE + AFTER automatically (matches llama3 KV cache pattern)
    buf = Tensor.zeros(2, 4, 3, dtype=dtypes.bf16).realize()
    patch = Tensor(np.arange(6, dtype=np.float32).reshape(2, 1, 3), dtype=dtypes.bf16)
    buf[:, 2:3, :].assign(patch)
    self.assertEqual(buf.uop.op, Ops.AFTER)
    self.assertEqual(buf.uop.src[1].op, Ops.STORE)
    got = buf.numpy()
    ref = np.zeros((2, 4, 3), dtype=np.float32)
    ref[:, 2:3, :] = np.arange(6, dtype=np.float32).reshape(2, 1, 3)
    np.testing.assert_allclose(got, ref)

    # Full Llama 3.2 1B model from examples/llama3.py builds and simplifies cleanly
    from examples.llama3 import Model
    m = Model(layers=2)
    prefill = simplify_tensor(m(Tensor([[128000, 15339, 11]], dtype=dtypes.i32), start_pos=0))
    tok = Tensor.buffer("tok", (1, 1), dtypes.i32)
    m.reset_cache()
    decode6 = simplify_tensor(m(tok, start_pos=6))
    m.reset_cache()
    decode17 = simplify_tensor(m(tok, start_pos=17))
    u6, v6 = decode6.unbind_all()
    u17, v17 = decode17.unbind_all()
    verify_tensor(prefill)
    verify_tensor(u6)
    self.assertIs(u6.uop, u17.uop)
    self.assertEqual([v.arg.name for v in u6.variables()], ["start_pos"])
    self.assertEqual(list(v6.values()), [6])
    self.assertEqual(list(v17.values()), [17])
    self.assertEqual(prefill.shape, ())
    self.assertEqual(u6.shape, ())
    self.assertEqual(prefill.dtype, dtypes.i32)
    self.assertEqual(u6.dtype, dtypes.i32)

  def test_symbolic_variable_bind_unbind_and_eval(self):
    # Build ONE symbolic KV-attention decode graph parameterized by Variable("pos", 1, 7)
    rng = np.random.default_rng(99)
    T, H, D = 8, 2, 4
    pos = Variable("pos", 1, T - 1)
    cos_np = np.cos(np.arange(T, dtype=np.float32)[:, None] * 0.25 + np.arange(D, dtype=np.float32)[None, :] * 0.1).astype(np.float32)
    kv_np = rng.standard_normal((2, H, T, D)).astype(np.float32) * 0.3

    cos_t = Tensor(cos_np)
    kv_buf = Tensor.buffer("kv", (2, H, T, D), dtypes.fp32)
    q_buf = Tensor.buffer("q", (H, 1, D), dtypes.fp32)
    new_kv = Tensor.buffer("new_kv", (2, H, 1, D), dtypes.fp32)

    # RoPE-like scale at [pos:pos+1] (cancels to concrete length 1), write KV at pos, attend over [:pos+1]
    q_rot = q_buf * cos_t[pos:pos + 1].reshape(1, 1, D)
    kv_buf[:, :, pos:pos + 1, :].assign(new_kv)
    k = kv_buf[0, :, :pos + 1, :]
    v = kv_buf[1, :, :pos + 1, :]
    self.assertEqual(k.max_shape, (H, T, D))
    scores = (q_rot @ k.mT) * (1.0 / math.sqrt(D))
    out = simplify_tensor(scores.softmax(-1) @ v)
    self.assertEqual(out.shape, (H, 1, D))
    self.assertEqual([v.arg.name for v in out.variables()], ["pos"])

    # Unbound eval without var_vals raises clearly
    with self.assertRaises(ValueError):
      out.numpy({"kv": kv_np, "q": np.zeros((H, 1, D), np.float32), "new_kv": np.zeros((2, H, 1, D), np.float32)})

    # Evaluate the SAME graph at multiple runtime positions via var_vals
    for p in (1, 3, 6):
      q_np = rng.standard_normal((H, 1, D)).astype(np.float32)
      nkv_np = rng.standard_normal((2, H, 1, D)).astype(np.float32)
      got = out.numpy({"kv": kv_np, "q": q_np, "new_kv": nkv_np}, var_vals={"pos": p})

      kv_r = kv_np.copy()
      kv_r[:, :, p:p + 1, :] = nkv_np
      qr = q_np * cos_np[p:p + 1][None, :, :]
      sc = (qr @ kv_r[0, :, :p + 1, :].swapaxes(-1, -2)) / math.sqrt(D)
      pr = np.exp(sc - sc.max(-1, keepdims=True)); pr /= pr.sum(-1, keepdims=True)
      ref = pr @ kv_r[1, :, :p + 1, :]
      np.testing.assert_allclose(got, ref, rtol=1e-5, atol=1e-5)

    # Also verify bound Variable works directly with .numpy()
    p_bound = pos.bind(4)
    slc_bound = cos_t[p_bound:p_bound + 1]
    np.testing.assert_allclose(slc_bound.numpy(), cos_np[4:5], rtol=1e-6)
    with self.assertRaises(ValueError):
      pos.bind(T)  # out of [1, T - 1] range

if __name__ == "__main__":
  unittest.main()
