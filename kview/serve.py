#!/usr/bin/env python3
"""kview: a reader for the exported kernels under kernels/.

  python kview/serve.py [--port 8137] [--host 0.0.0.0] [--kernels kernels]

Decodes each <role>.bin on demand (nothing is read from the .S listings) and serves a small web UI. Standard library only.
"""
import argparse, json, re, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import decode

ROOT = HERE.parent
STATIC = HERE / "static"
ROLE_ORDER = ["brisc", "ncrisc", "trisc0", "trisc1", "trisc2"]
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml"}

class Library:
  def __init__(self, kernels):
    self.dir = Path(kernels).resolve()
    self.abi = decode.parse_abi(ROOT / "fw" / "abi.h")
    self.lock = threading.Lock()
    self.manifests, self.cache = {}, {}

  def models(self): return sorted(p.parent.name for p in self.dir.glob("*/manifest.json"))

  def manifest(self, model):
    path = self.dir / model / "manifest.json"
    stamp = path.stat().st_mtime_ns
    if self.manifests.get(model, (None,))[0] != stamp: self.manifests[model] = (stamp, json.loads(path.read_text()))
    return self.manifests[model][1]

  def buffers(self, m):
    seen, out = set(), []
    for b in [*m.get("buffers", {}).values(), *m.get("uploads", []), m.get("history")]:
      if not b or (b["name"], b["addr"]) in seen: continue
      seen.add((b["name"], b["addr"]))
      out.append(dict(name=b["name"], addr=b["addr"], size=b["size"], tile=b["tile"], kind=b.get("kind"), src=b.get("src")))
    return sorted(out, key=lambda b: (b["addr"], -b["size"]))

  def resolve(self, value, buffers):
    """What a launch-parameter word is: a DRAM buffer (low 3 bits = first bank), a Tensix instruction, or a number."""
    if isinstance(value, str): return dict(text=value, kind="dynamic", note="filled in by the host for every token")
    if value >> 24 == 0x71:
      d = decode.tt_decode(value)
      return dict(text=decode.hex8(value), kind="instr", note=f"{d['op']}: {d['gist']}")
    base = value & ~7
    best = None
    for b in buffers:
      span = max(-(-b["size"] // 8), b["tile"])  # bytes per DRAM bank
      if b["addr"] <= base < b["addr"] + span and (best is None or b["addr"] == base): best = b
    if best and value >= 4096:
      off = base - best["addr"]
      note = best["name"] + (f" + {decode.hx(off)}" if off else "") + (f", first bank {value & 7}" if value & 7 else "")
      if best.get("src"): note += f"  ({best['src']})"
      return dict(text=decode.hex8(value), kind="dram", note=note, buffer=best["name"])
    return dict(text=str(value) if value < 100000 else decode.hex8(value), kind="num", note="")

  def index(self):
    out = []
    for model in self.models():
      m = self.manifest(model)
      buffers = self.buffers(m)
      order = list(dict.fromkeys(name for name, _ in m["launches"])) + [n for n in m["programs"] if n not in {x for x, _ in m["launches"]}]
      programs = []
      for name in order:
        p = m["programs"][name]
        launches = [words for n, words in m["launches"] if n == name]
        uniform = []
        for i, pname in enumerate(p["uniform"]):
          values = [w[i] for w in launches if i < len(w)]
          distinct = list(dict.fromkeys(map(json.dumps, values)))
          uniform.append(dict(name=pname, addr=m["l1_param_base"] + 4 * i, kind="uniform", varies=len(distinct) > 1,
                              values=[self.resolve(json.loads(v), buffers) for v in distinct[:40]]))
        for a, b in zip(uniform, uniform[1:]):  # FP8 scales travel as two SFPLOADI words: low half, then high half
          if a["name"].endswith("_0") and b["name"] == a["name"][:-1] + "1":
            ia, ib = p["uniform"].index(a["name"]), p["uniform"].index(b["name"])
            pairs = [(w[ia], w[ib]) for w in launches if isinstance(w[ia], int) and isinstance(w[ib], int) and w[ia] >> 16 == 0x716A and w[ib] >> 16 == 0x7168]
            if pairs:
              floats = [decode.fnum(decode.f32((hi & 0xFFFF) << 16 | lo & 0xFFFF)) for lo, hi in pairs]
              a["combined"] = b["combined"] = dict(name=a["name"][:-2], values=floats)
        static = []
        for j, pname in enumerate(p["static"]):
          values = [c["params"][j] for c in p["per_core"]]
          static.append(dict(name=pname, addr=m["static_base"] + 0x40 * p["k"] + 4 * j, kind="per-core", per_core=values,
                             varies=len(set(values)) > 1, values=[self.resolve(v, buffers) for v in list(dict.fromkeys(values))[:3]]))
        kernels = []
        for r, role in enumerate(m["roles"]):
          for v, rel in enumerate(p["files"][role]):
            path = self.dir / model / rel
            cores = [c["core"] for c in p["per_core"] if c["variants"][r] == v]
            kernels.append(dict(role=role, file=Path(rel).stem, variant=v if len(p["files"][role]) > 1 else None,
                                size=path.stat().st_size if path.exists() else 0, cores=cores))
        programs.append(dict(name=name, k=p["k"], cores=p["cores"], params=uniform + static, kernels=kernels, launches=len(launches)))
      seq, runs = [n for n, _ in m["launches"]], []
      ref = {}
      try: ref = json.loads((self.dir / model / "reference.json").read_text())
      except (OSError, ValueError): pass
      out.append(dict(id=model, model=m.get("model", model), note=ref.get("note", ""), programs=programs, sequence=compress(seq),
                      layout={k: m[k] for k in ("static_base", "l1_param_base", "l1_data_base", "dram_top", "kv_block", "max_tokens") if k in m},
                      persistent=m.get("persistent", []), buffers=[b for b in buffers if b["kind"] == "buffer" or b["kind"] == "history"]))
    return dict(models=out, roles={r: decode.RISC_ROLE[r] for r in ROLE_ORDER}, abi={k: v for k, v in self.abi.items() if k.startswith(("FW_", "CODE_", "L1_", "DATA_", "SLOT_", "GO_", "LAUNCH", "SUBORD", "PARAM"))})

  def kernel(self, model, program, file):
    if not all(re.fullmatch(r"[\w.\-]+", x) for x in (model, program, file)): raise ValueError("bad kernel name")
    path = self.dir / model / program / f"{file}.bin"
    stamp = (path.stat().st_mtime_ns, (self.dir / model / "manifest.json").stat().st_mtime_ns)
    key = (model, program, file)
    with self.lock:
      hit = self.cache.get(key)
      if hit and hit[0] == stamp: return hit[1]
    ctx = decode.Context(file.split(".")[0], self.manifest(model), program, self.abi)
    result = decode.disassemble(path.read_bytes(), ctx)
    result.update(model=model, program=program, file=file, role=file.split(".")[0])
    with self.lock: self.cache[key] = (stamp, result)
    return result

  def search(self, model, query):
    """Rows of every kernel of a model whose text contains every word of the query."""
    words = [w for w in query.lower().split() if w]
    hits = []
    if not words: return hits
    m = self.manifest(model)
    for pname, p in m["programs"].items():
      for role in m["roles"]:
        for rel in p["files"][role]:
          file = Path(rel).stem
          for row in self.kernel(model, pname, file)["rows"]:
            text = row_text(row)
            low = text.lower()
            if all(w in low for w in words):
              hits.append(dict(program=pname, file=file, pc=row["pc"], text=text[:200]))
              if len(hits) >= 400: return hits
    return hits

def row_text(row):
  if row["kind"] == "tt": ops = ", ".join(f"{n}={v}" for n, v, _ in row["args"])
  else: ops = row.get("operands", "") + row.get("tlabel", "")
  ann = "; ".join(" ← ".join(str(x) for x in a[1:] if x != "") if a[0] == "store" else str(a[1]) for a in row["ann"])
  return f"{row['op']} {ops}" + (f"  # {ann}" if ann else "")

def compress(seq):
  """['a','b','c','b','c','d'] -> [['a'], 2, ['b','c'], ['d']] style run-length encoding of the launch order."""
  out, i = [], 0
  while i < len(seq):
    best = (1, 1)
    for period in range(1, 9):
      reps = 1
      while seq[i + reps * period: i + (reps + 1) * period] == seq[i:i + period]: reps += 1
      if reps > 1 and reps * period > best[0] * best[1]: best = (period, reps)
    period, reps = best
    out.append(dict(names=seq[i:i + period], times=reps))
    i += period * reps
  return out

class Handler(BaseHTTPRequestHandler):
  lib = None
  def log_message(self, *args): pass

  def send(self, body, mime="application/json", status=200):
    data = body if isinstance(body, bytes) else json.dumps(body, separators=(",", ":")).encode()
    self.send_response(status)
    self.send_header("Content-Type", mime)
    self.send_header("Content-Length", str(len(data)))
    self.send_header("Cache-Control", "no-store")
    self.end_headers()
    self.wfile.write(data)

  def do_GET(self):
    url = urlsplit(self.path)
    q = {k: v[0] for k, v in parse_qs(url.query).items()}
    try:
      if url.path == "/api/index": return self.send(self.lib.index())
      if url.path == "/api/isa": return self.send({v["name"]: {k: v[k] for k in ("title", "group", "summary", "notes", "constants", "manual", "fields")} for v in decode.ISA.values()})
      if url.path == "/api/kernel": return self.send(self.lib.kernel(q["model"], q["program"], q["file"]))
      if url.path == "/api/search": return self.send(self.lib.search(q["model"], q.get("q", "")))
      name = "index.html" if url.path in ("/", "") else url.path.lstrip("/")
      path = (STATIC / name).resolve()
      if STATIC not in path.parents or not path.is_file(): return self.send(dict(error="not found"), status=404)
      return self.send(path.read_bytes(), MIME.get(path.suffix, "application/octet-stream"))
    except (KeyError, ValueError, OSError) as e:
      return self.send(dict(error=f"{type(e).__name__}: {e}"), status=400)

def main():
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--port", type=int, default=8137)
  ap.add_argument("--host", default="0.0.0.0", help="address to listen on; 127.0.0.1 to keep it to this machine")
  ap.add_argument("--kernels", default=str(ROOT / "kernels"))
  args = ap.parse_args()
  Handler.lib = Library(args.kernels)
  models = Handler.lib.models()
  if not models: sys.exit(f"no */manifest.json under {args.kernels}")
  server = ThreadingHTTPServer((args.host, args.port), Handler)
  import socket
  shown = socket.gethostname() if args.host == "0.0.0.0" else args.host
  print(f"kview: {', '.join(models)}\n  http://{shown}:{args.port}" + ("  (listening on every interface)" if args.host == "0.0.0.0" else ""))
  try: server.serve_forever()
  except KeyboardInterrupt: pass

if __name__ == "__main__": main()
