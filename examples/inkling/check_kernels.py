"""Check each Inkling device kernel against the torch reference ops on random inputs.

  python examples/inkling/check_kernels.py [names...]   # default: all
"""
import math
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from ttrv import Device  # noqa: E402
from reference import mix, rms  # noqa: E402

D, ROW = 2304, 3072
rng = np.random.default_rng(0)


def bf16(x):
  """float array -> BF16 bits (round to nearest even)."""
  u = np.asarray(x, np.float32).view(np.uint32).astype(np.uint64)
  return ((u + 0x7FFF + (u >> 16 & 1)) >> 16).astype(np.uint16)


def floats(bits):
  return (np.asarray(bits).astype(np.uint32) << 16).view(np.float32)


def unpack_x(bits, k):
  """Face-packed BF16 bits -> the first k floats."""
  return floats(np.asarray(bits).reshape(-1, 2, 16, 16).transpose(0, 2, 1, 3).reshape(-1))[:k]


def rows(*vs):
  """FP32 [len(vs), ROW], zero past D."""
  out = np.zeros((len(vs), ROW), np.float32)
  for i, v in enumerate(vs): out[i, :len(v)] = v
  return out


def report(name, got, want, tol):
  err = float(np.abs(got - want).max() / max(np.abs(want).max(), 1e-30))
  ok = err < tol and np.isfinite(got).all()
  print(f"{'PASS' if ok else 'FAIL'} {name}: max error {err:.2e} of max {np.abs(want).max():.3g}")
  return ok


def test_mix(dev):
  kernel = HERE / "mix.ttrv"
  ok = True
  for nb, nq, norm in ((0, 1, 1), (1, 1, 0), (3, 1, 1), (4, 3, 1), (1, 4, 0)):
    xs = [rng.standard_normal(D).astype(np.float32) * rng.uniform(0.5, 30) for _ in range(nb + 1)]
    qs = rng.standard_normal((nq, D)).astype(np.float32) * 3
    gamma = rng.standard_normal((nq, D)).astype(np.float32)
    blocks = dev.array(rows(*([np.zeros(D)] * 2 + xs[:nb])))  # rows 2.. hold the blocks
    cur = dev.array(rows(xs[nb])[0])
    queries, g = dev.array(rows(*qs)), dev.array(rows(*gamma))
    out, normed = dev.zeros(nq * ROW, "fp32"), dev.zeros(nq * ROW, "bf16")
    k = dev.kernel(kernel, NB=nb, B0=2, NQ=nq, NORM=norm, DENSE=1)
    args = dict(blocks=blocks, cur=cur, queries=queries, out=out)
    if norm: args |= dict(gamma=g, normed=normed)
    k(**args)
    want = mix([torch.from_numpy(x) for x in xs[:nb]], torch.from_numpy(xs[nb]), torch.from_numpy(qs)).numpy()
    got = out.numpy().reshape(nq, ROW)
    ok &= report(f"mix NB={nb} NQ={nq} dense", got[:, :D], want, 2e-3)
    ok &= float(np.abs(got[:, D:]).max()) == 0
    if norm:
      wn = (rms(torch.from_numpy(want)) * torch.from_numpy(gamma)).numpy()
      gn = np.stack([unpack_x(r, D) for r in normed.numpy().reshape(nq, ROW)])
      ok &= report(f"mix NB={nb} NQ={nq} normed", gn, wn, 1e-2)
  # The embedding path: BF16 cur, normed only.
  x = rng.standard_normal(D).astype(np.float32)
  gamma = rng.standard_normal(D).astype(np.float32)
  cur = dev.array(np.pad(bf16(x), (0, ROW - D)), "bf16")
  normed, dummy = dev.zeros(ROW, "bf16"), dev.zeros(ROW, "fp32")
  k = dev.kernel(kernel, NB=0, NORM=1, DENSE=0, CUR_BF16=1)
  k(blocks=dummy, cur=cur, queries=dummy, gamma=dev.array(rows(gamma)), normed=normed)
  want = (rms(rms(torch.from_numpy(floats(bf16(x))))) * torch.from_numpy(gamma)).numpy()
  ok &= report("mix bf16 cur normed", unpack_x(normed.numpy(), D), want, 1e-2)
  return ok


def test_moe(dev, layer=3):
  """Router, top-8, routed gate/up, SwiGLU, routed down on one real layer against reference.moe's math."""
  from helpers import safe_load
  from reference import DEFAULT, Experts, swiglu, tensor
  from projections import bf16_image, pack_x, upload_experts
  import json
  cfg = json.loads((DEFAULT / "config.json").read_text())["text_config"]
  T = safe_load(DEFAULT / "model-00001-of-00001.safetensors")
  wr = tensor(T[f"model.llm.layers.{layer}.mlp.gate.weight"])
  br = tensor(T[f"model.llm.layers.{layer}.mlp.gate.bias"])
  images = DEFAULT.parent / "bfp8"
  layout = json.loads((images / "layout.json").read_text())[str(layer)]
  path = images / f"layer{layer:02d}.safetensors"
  data = np.memmap(path, np.uint8, "r")
  tensors = safe_load(path)
  w13, l13 = upload_experts(dev, data, tensors, layout, "w13")
  w2, l2 = upload_experts(dev, data, tensors, layout, "w2")
  img, lr = bf16_image(wr.numpy())
  router_w = dev.empty(img.size, "bf16", tiles_per_page=8).copy_from(img)
  router = dev.kernel(HERE / "experts.ttrv", K=D, N=128, BITS=16, GROUP=8, OUT32=1, WORKERS=4)
  route = dev.kernel(HERE / "router.ttrv")
  gate_up = dev.kernel(HERE / "experts.ttrv", K=D, N=8 * 2 * 1152, GROUP=l13["GROUP"], SELECT=1, WORKERS=96)
  act = dev.kernel(HERE / "swiglu.ttrv")
  down = dev.kernel(HERE / "experts.ttrv", K=8 * 1152, N=D, GROUP=l2["GROUP"], SELECT=2, WORKERS=72)
  bias = dev.array(np.pad(br.numpy(), (0, 1024 - 128)).astype(np.float32))
  logits, select, score = dev.zeros(1024, "fp32"), dev.zeros(16, "fp32"), dev.zeros(16, "fp32")
  index = dev.array(np.arange(1024, dtype=np.float32))
  gu, a, y = dev.zeros(8 * 2304, "bf16"), dev.zeros(8 * 1152, "bf16"), dev.zeros(D, "bf16")
  E = Experts(T, layer)
  ok = True
  for trial in range(3):
    h = rms(torch.from_numpy(rng.standard_normal(D).astype(np.float32)))
    xb = dev.array(pack_x(h.numpy()), "bf16")
    router(x=xb, weights=router_w, output=logits)
    route(logits=logits, bias=bias, index=index, select=select, score=score)
    gate_up(x=xb, weights=w13, output=gu, select=select)
    act(gate_up=gu, score=score, output=a)
    down(x=a, weights=w2, output=y, select=select)
    hb = torch.from_numpy(floats(bf16(h.numpy())))
    scores = torch.sigmoid(wr @ hb)
    idx = torch.topk(scores + br, 8).indices
    got_idx = select.numpy()[:8].view(np.uint32) & 255
    same = sorted(idx.tolist()) == sorted(got_idx.tolist())
    ok &= report(f"moe router logits #{trial}", logits.numpy()[:128], (wr @ hb).numpy(), 1e-2)
    print(f"{'PASS' if same else 'FAIL'} moe top-8 #{trial}: ref {sorted(idx.tolist())} device {sorted(got_idx.tolist())}")
    ok &= same
    got_s, want_s = score.numpy()[:8], scores[torch.from_numpy(got_idx.astype(np.int64))].numpy()
    ok &= report(f"moe top-8 scores #{trial}", got_s, want_s, 1e-2)
    w = scores[idx] / scores[idx].sum() * cfg["route_scale"]
    want = sum(we * (E.weight("w2", e) @ swiglu(*E.weight("w13", e).matmul(hb).view(-1, 2).T, 4.0, 25.0))
               for we, e in zip(w, idx.tolist()))
    if trial == 0:
      order = got_idx.tolist()
      g = floats(gu.numpy()).reshape(8, 2, 1152)
      sv = score.numpy()[:8]
      wd = sv / sv.sum() * 8
      av = unpack_x(a.numpy(), 8 * 1152).reshape(8, 1152)
      for slot, e in enumerate(order[:3]):
        ref = (E.weight("w13", e) @ hb).view(-1, 2).T.numpy()
        report(f"  slot {slot} gate", g[slot, 0], ref[0], 3e-2)
        report(f"  slot {slot} up", g[slot, 1], ref[1], 3e-2)
        ra = (wd[slot] * swiglu(torch.from_numpy(g[slot, 0]), torch.from_numpy(g[slot, 1]), 4.0, 25.0)).numpy()
        report(f"  slot {slot} act", av[slot], ra, 3e-2)
      ys = sum((E.weight("w2", e) @ torch.from_numpy(av[slot])).numpy() for slot, e in enumerate(order))
      report("  down of device act", floats(y.numpy()), ys, 3e-2)
    ok &= report(f"moe output #{trial}", floats(y.numpy()), want.numpy(), 5e-2)
  return ok


def attention_weights(layer):
  """One layer's attention constants from the checkpoint (fp32 torch)."""
  from helpers import safe_load
  from reference import DEFAULT, tensor
  import json
  cfg = json.loads((DEFAULT / "config.json").read_text())["text_config"]
  T = safe_load(DEFAULT / "model-00001-of-00001.safetensors")
  W = lambda n: tensor(T[f"model.llm.layers.{layer}." + n])  # noqa: E731
  full = layer not in cfg["local_layer_ids"]
  L = {n: W("attn." + n) for n in ("q_l2_clip.scale", "rel_l2_clip.scale", "rel_logits_proj.proj")}
  if full:
    for n in "kv": L[n + "_static"] = W(f"attn.{n}_sconv.static_w")
  else:
    for n in "kv": L[n + "_conv"] = W(f"attn.{n}_sconv.weight")[:, 0]
  return cfg, full, L


def attention_reference(cfg, full, L, c, q_proj, k_proj, v_proj, pos):
  """reference.Inkling.attention from the projection outputs to the gated context (before the o projection)."""
  from reference import l2clip
  H, KV, HD = 24, 8, 128
  q, gate, r, sink = q_proj[:3072], q_proj[3072:6144], q_proj[6144:6528], q_proj[6528:6552]
  def conv(x, name, w):
    window = torch.cat([c[name], x[None]]); c[name] = window[1:]
    return ((window * w.T).sum(0) + x) / math.sqrt(5)
  def dconv(x, name, static, dyn):
    window = torch.cat([c[name], x[None]]); c[name] = window[1:]
    lags = window.flip(0)
    weights = static.T.reshape(KV, HD, 4) + dyn.view(KV, 1, 4)
    return ((lags.T.reshape(KV, HD, 4) * weights).sum(-1).reshape(-1) + x) / 3
  k, v = k_proj[:1024], v_proj[:1024]
  q = l2clip(q.view(H, HD) * L["q_l2_clip.scale"], cfg["qk_l2_clip_threshold"])
  if full: k, v = dconv(k, "kc", L["k_static"], k_proj[1024:1056]), dconv(v, "vc", L["v_static"], v_proj[1024:1056])
  else: k, v = conv(k, "kc", L["k_conv"]), conv(v, "vc", L["v_conv"])
  c["k"].append(l2clip(k.view(KV, HD), cfg["qk_l2_clip_threshold"]))
  c["v"].append(rms(v.view(KV, HD), eps=1e-6))
  r = l2clip(r.view(H, -1) * L["rel_l2_clip.scale"], cfg["rel_l2_clip_threshold"])
  rel = r @ L["rel_logits_proj.proj"]
  n = len(c["k"])
  first = max(0, n - 1024) if not full else 0
  K, V = torch.stack(c["k"][first:]), torch.stack(c["v"][first:])
  dist = (n - 1) - torch.arange(first, n)
  bias = torch.where(dist < rel.shape[1], rel[:, dist.clamp(max=rel.shape[1] - 1)], torch.zeros(()))
  scores = torch.einsum("khd,nkd->khn", q.view(KV, 3, HD), K).reshape(H, -1) / math.sqrt(HD) + bias
  p = torch.softmax(torch.cat([scores, sink[:, None]], 1), 1)[:, :-1]
  out = torch.einsum("khn,nkd->khd", p.view(KV, 3, -1), V).reshape(-1)
  return out * torch.sigmoid(gate)


def attention_device(dev, full, L, max_tokens):
  """Kernels and per-layer buffers for one layer's attention, as the model driver builds them."""
  from projections import bf16_bits
  sliding = not full
  k = {
    "qprep": dev.kernel(HERE / "qprep.ttrv"),
    "kvconv": dev.kernel(HERE / "kvconv.ttrv", DYNAMIC=int(full), NORM=1 / 3 if full else 1 / math.sqrt(5)),
    "rel": dev.kernel(HERE / "rel.ttrv"),
    "attn": dev.kernel(HERE / "attention.ttrv", SLIDING=int(sliding), MAX_TOKENS=max_tokens),
  }
  if full: lag = np.stack([L[n + "_static"].numpy() for n in "kv"])                      # [2][4 lags][1024]
  else: lag = np.stack([L[n + "_conv"].numpy()[:, ::-1].T for n in "kv"])                # tap 3 is lag 0
  P = L["rel_logits_proj.proj"].numpy()
  tiles = np.zeros((32, 32, 32), np.float32)
  tiles[:, :16, :] = P.reshape(16, 32, 32).transpose(1, 0, 2)                            # [tile][r][d]
  tiles = tiles.reshape(32, 2, 16, 2, 16).transpose(0, 1, 3, 2, 4).reshape(32, 1024)    # face layout
  b = {
    "q_scale": dev.array(bf16_bits(L["q_l2_clip.scale"].numpy().reshape(-1)), "bf16"),
    "r_scale": dev.array(np.pad(bf16_bits(L["rel_l2_clip.scale"].numpy().reshape(-1)), (0, 1024 - 384)), "bf16"),
    "lag": dev.array(bf16_bits(np.ascontiguousarray(lag).reshape(-1)), "bf16"),
    "proj_tiles": dev.array(bf16_bits(tiles.reshape(-1)), "bf16"),
    "history": dev.zeros(2 * 4 * 1024, "bf16"),
    "keys": dev.zeros(8 * max_tokens * 128, "bf16"), "values": dev.zeros(8 * max_tokens * 128, "bf16"),
    "q": dev.zeros(3072, "bf16"), "r": dev.zeros(1024, "bf16"), "rel": dev.zeros(24 * 1024, "bf16"),
    "k": dev.zeros(1024, "bf16"), "v": dev.zeros(1024, "bf16"), "ctx": dev.zeros(3072, "bf16"),
  }
  return k, b


def attention_run(k, b, q_proj, k_proj, v_proj, pos):
  k["qprep"](proj=q_proj, q_scale=b["q_scale"], r_scale=b["r_scale"], q_out=b["q"], r_out=b["r"])
  k["kvconv"](k_in=k_proj, v_in=v_proj, weights=b["lag"], history=b["history"], k_out=b["k"], v_out=b["v"], pos=pos)
  k["rel"](r_in=b["r"], proj_tiles=b["proj_tiles"], rel=b["rel"])
  k["attn"](q_in=b["q"], proj=q_proj, k_in=b["k"], v_in=b["v"], rel=b["rel"], key_cache=b["keys"],
            value_cache=b["values"], context=b["ctx"], start_pos=pos)


def test_attention(dev):
  ok = True
  for layer, steps, checks in ((6, 1100, (0, 1, 2, 31, 32, 33, 200, 1022, 1023, 1024, 1025, 1099)), (5, 300, (0, 1, 5, 64, 299))):
    cfg, full, L = attention_weights(layer)
    k, b = attention_device(dev, full, L, 2048)
    c = {"k": [], "v": [], "kc": torch.zeros(3, 1024), "vc": torch.zeros(3, 1024)}
    q_dev, k_dev, v_dev = dev.zeros(7168, "bf16"), dev.zeros(1056, "bf16"), dev.zeros(1056, "bf16")
    worst = 0
    for pos in range(steps):
      qp = floats(bf16(rng.standard_normal(7168).astype(np.float32) * 2))
      kp = floats(bf16(rng.standard_normal(1056).astype(np.float32) * 2))
      vp = floats(bf16(rng.standard_normal(1056).astype(np.float32) * 2))
      qp[6552:] = 0
      q_dev.copy_from(bf16(qp)); k_dev.copy_from(bf16(kp)); v_dev.copy_from(bf16(vp))
      attention_run(k, b, q_dev, k_dev, v_dev, pos)
      want = attention_reference(cfg, full, L, c, *(torch.from_numpy(a) for a in (qp, kp, vp)), pos).numpy()
      if pos in checks:
        got = unpack_x(b["ctx"].numpy(), 3072)
        err = float(np.abs(got - want).max() / np.abs(want).max())
        worst = max(worst, err)
    good = worst < 5e-2
    print(f"{'PASS' if good else 'FAIL'} attention layer {layer} ({'full' if full else 'sliding'}): "
          f"worst error {worst:.2e} over positions {checks}")
    ok &= good
  return ok


def test_gate(dev, layer=8):
  """Message gate: rms(h), rms(m) -> down -> [forget; gain] -> gate, against reference.message_gate."""
  from helpers import safe_load
  from reference import DEFAULT, tensor
  from projections import bf16_image
  T = safe_load(DEFAULT / "model-00001-of-00001.safetensors")
  down, forget, gain = (tensor(T[f"model.llm.layers.{layer}.controllers.k.{m}_weight"]) for m in ("down", "forget", "gain"))
  wd = np.zeros((64, 6144), np.float32)
  wd[:, :D], wd[:, 3072:3072 + D] = down[:, :D].numpy(), down[:, D:].numpy()
  wfg = np.zeros((2 * D, 512), np.float32)
  wfg[:D, :64], wfg[D:, :64] = forget.numpy(), gain.numpy()
  img_d, ld = bf16_image(wd)
  img_fg, lfg = bf16_image(wfg)
  bd = dev.empty(img_d.size, "bf16", tiles_per_page=8).copy_from(img_d)
  bfg = dev.empty(img_fg.size, "bf16", tiles_per_page=8).copy_from(img_fg)
  norm1 = dev.kernel(HERE / "mix.ttrv", NB=0, NQ=1, DENSE=0, NORM=1)
  kd = dev.kernel(HERE / "experts.ttrv", K=6144, N=64, BITS=16, GROUP=8, X2=1, PACK_OUT=1, WORKERS=2)
  kfg = dev.kernel(HERE / "experts.ttrv", K=512, N=2 * D, BITS=16, GROUP=8, WORKERS=96, OUT32=1)
  kg = dev.kernel(HERE / "gate.ttrv")
  ones = dev.array(rows(np.ones(D, np.float32)))
  ok = True
  for trial in range(2):
    h = rng.standard_normal(D).astype(np.float32) * 3
    m = rng.standard_normal(D).astype(np.float32)
    hb, mb = dev.array(rows(h)[0]), dev.array(rows(m)[0])
    xh, xm, g, fa, out = dev.zeros(ROW, "bf16"), dev.zeros(ROW, "bf16"), dev.zeros(512, "bf16"), dev.zeros(D + ROW, "fp32"), dev.zeros(ROW, "fp32")
    norm1(blocks=hb, cur=hb, queries=hb, gamma=ones, normed=xh)
    norm1(blocks=mb, cur=mb, queries=mb, gamma=ones, normed=xm)
    kd(x=xh, x2=xm, weights=bd, output=g)
    kfg(x=g, weights=bfg, output=fa)
    kg(h=hb, m=mb, fa=fa, out=out)
    ht, mt = torch.from_numpy(h), torch.from_numpy(m)
    gw = down @ torch.cat([rms(ht), rms(mt)])
    want = (1 - torch.tanh(forget @ gw)) * ht + torch.tanh(gain @ gw) * mt
    ok &= report(f"gate down #{trial}", unpack_x(g.numpy(), 64), gw.numpy(), 3e-2)
    ok &= report(f"gate out #{trial}", out.numpy()[:D], want.numpy(), 3e-2)
  return ok


def test_resconv(dev):
  kernel = dev.kernel(HERE / "resconv.ttrv")
  w = rng.standard_normal((D, 4)).astype(np.float32) * 0.5
  taps = np.zeros((4, ROW), np.float32)
  taps[:, :D] = w[:, ::-1].T
  tb = dev.array(bf16(taps.reshape(-1)), "bf16")
  hist = dev.zeros(4 * ROW, "bf16")
  out = dev.zeros(ROW, "fp32")
  cache = torch.zeros(3, D)
  ok = True
  for pos in range(6):
    y = floats(bf16(rng.standard_normal(D).astype(np.float32)))
    res = rng.standard_normal(D).astype(np.float32)
    kernel(y=dev.array(np.pad(bf16(y), (0, ROW - D)), "bf16"), taps=tb, history=hist, residual=dev.array(rows(res)[0]), out=out, pos=pos)
    window = torch.cat([cache, torch.from_numpy(y)[None]])
    cache = window[1:]
    want = torch.from_numpy(res) + ((window * torch.from_numpy(floats(bf16(w))).T).sum(0) + torch.from_numpy(y)) / math.sqrt(5)
    ok &= report(f"resconv pos {pos}", out.numpy()[:D], want.numpy(), 1e-3)
  return ok


TESTS = {"mix": test_mix, "moe": test_moe, "attention": test_attention, "gate": test_gate, "resconv": test_resconv}

if __name__ == "__main__":
  names = sys.argv[1:] or list(TESTS)
  dev = Device(0)
  try:
    results = {n: TESTS[n](dev) for n in names}
  finally:
    dev.close()
  print("ALL PASS" if all(results.values()) else f"FAILED: {[n for n, r in results.items() if not r]}")
