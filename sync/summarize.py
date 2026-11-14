"""Tables from sync/results/*.json: per-kernel time vs. the DRAM streaming bound, and the ablation deltas.

  python sync/summarize.py > sync/results.md
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PEAK = 506e9  # B/s: lm (1.05 GB BF16 LM head, one launch) measured 506 GB/s; treat as achievable streaming rate

# bytes of weights read per launch, from the Llama 3 shapes
SHAPES = {"1b": dict(d=2048, ff=8192, kv=8 * 64, L=16, vocab=128256, w=2, lm=2),
          "8b-bf16": dict(d=4096, ff=14336, kv=8 * 128, L=32, vocab=128256, w=2, lm=2),
          "8b-fp8": dict(d=4096, ff=14336, kv=8 * 128, L=32, vocab=128256, w=1, lm=2)}

def weight_bytes(model):
  s = SHAPES[model]
  d, ff, kv, w = s["d"], s["ff"], s["kv"], s["w"]
  return dict(qkv=(d + 2 * kv) * d * w, o=d * d * w, gate=2 * ff * d * w, down=d * ff * w, lm=s["vocab"] * d * s["lm"])

def load():
  return {(r["model"], r["variant"]): r for r in map(lambda p: json.loads(p.read_text()), sorted((HERE / "results").glob("*.json")))}

def main():
  res = load()
  for model in ("8b-fp8", "8b-bf16", "1b"):
    base = res.get((model, "base"))
    if not base: continue
    wb, L = weight_bytes(model), SHAPES[model]["L"]
    print(f"\n### {model}: {base['period_us'] / 1e3:.2f} ms/token\n")
    print("| kernel | us/launch | streaming bound | excess | compute-only (`nodram`) | per-tile syncs off (`nodram+t0semfix+t1nosync`) |")
    print("|---|---:|---:|---:|---:|---:|")
    nd, nds = res.get((model, "nodram")), res.get((model, "nodram+t0semfix+t1nosync"))
    total_excess = 0
    for k in ("qkv", "o", "gate", "down", "lm"):
      t = base["kernels"][k]["us_per_launch"]
      bound = wb[k] / PEAK * 1e6
      n = base["kernels"][k]["launches_per_token"]
      total_excess += (t - bound) * n
      f = lambda r: f"{r['kernels'][k]['us_per_launch']:.1f}" if r else "–"
      print(f"| {k} | {t:.1f} | {bound:.1f} | {t - bound:+.1f} | {f(nd)} | {f(nds)} |")
    for k in ("attention", "attention_merge", "embedding", "argmax"):
      v = base["kernels"][k]
      total_excess += v["us_per_token"]
      print(f"| {k} | {v['us_per_launch']:.1f} | ~0 | {v['us_per_launch']:+.1f} | | |")
    print(f"\nTime not explained by streaming weights at {PEAK / 1e9:.0f} GB/s: "
          f"{total_excess / 1e3:.2f} ms/token ({total_excess / base['period_us']:.0%}).")
  print("\n### All runs\n")
  print("| model | variant | ms/token | tokens match | gate | down | qkv | o | lm |")
  print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
  for (model, variant), r in sorted(res.items()):
    ks = r["kernels"]
    print(f"| {model} | `{variant}` | {r['period_us'] / 1e3:.2f} | {r['tokens_match']} | "
          + " | ".join(f"{ks[k]['us_per_launch']:.1f}" for k in ("gate", "down", "qkv", "o", "lm")) + " |")

if __name__ == "__main__": main()
